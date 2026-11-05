"""Deterministic, intelligence-aware visualization planning for InsightFlow."""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.column_intelligence import analyze_columns


MEASURE_PRIORITY = ("sales", "revenue", "profit", "amount", "value", "price", "quantity")


def _as_dict(value: Any) -> dict:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value if isinstance(value, dict) else {}


def _understanding_maps(understanding: Any) -> tuple[str, dict[str, dict]]:
    """Extract validated domain and column roles from the saved AI profile."""
    payload = _as_dict(understanding)
    domain = str(payload.get("domain", "general")).lower()
    mappings = {}
    for item in payload.get("column_meanings", []) or []:
        if isinstance(item, dict) and item.get("column"):
            mappings[str(item["column"])] = item
    return domain, mappings


def choose_best_measure(df: pd.DataFrame, measure_columns: list[str]) -> str | None:
    """Select a likely measure using familiar business naming priorities."""
    del df  # retained for backwards-compatible public signature
    for keyword in MEASURE_PRIORITY:
        for column in measure_columns:
            if keyword in column.lower():
                return column
    return measure_columns[0] if measure_columns else None


def is_suitable_for_scatter(semantic_type: str) -> bool:
    return semantic_type in {"numeric_measure", "count"}


def select_diverse_recommendations(
    recommendations: list[dict], max_recommendations: int
) -> list[dict]:
    if max_recommendations <= 0:
        return []
    type_limits = {"scatter": 3, "line": 2, "bar": 3, "histogram": 2,
                   "map": 1, "box": 3}
    selected, counts = [], {}
    seen_signatures = set()
    for index, recommendation in enumerate(recommendations):
        chart_type = recommendation["type"]
        signature = (chart_type, recommendation.get("x"), recommendation.get("y"),
                     recommendation.get("column"), recommendation.get("latitude"),
                     recommendation.get("longitude"))
        # Generic recommendations without column metadata are distinct entries;
        # retain the legacy selector contract for caller-supplied lists.
        if not any(value is not None for value in signature[1:]):
            signature = (*signature, index)
        if signature in seen_signatures:
            continue
        if counts.get(chart_type, 0) >= type_limits.get(chart_type, 2):
            continue
        selected.append(recommendation)
        seen_signatures.add(signature)
        counts[chart_type] = counts.get(chart_type, 0) + 1
        if len(selected) >= max_recommendations:
            break
    return selected


def choose_time_frequency(df: pd.DataFrame, date_column: str) -> str:
    valid_dates = pd.to_datetime(df[date_column], errors="coerce").dropna()
    if valid_dates.empty:
        return "D"
    span = (valid_dates.max().normalize() - valid_dates.min().normalize()).days + 1
    if span <= 90:
        return "D"
    if span <= 365:
        return "W"
    return "ME"


def _semantic_columns(df: pd.DataFrame, understanding: Any) -> list[dict]:
    """Merge deterministic structural typing with optional AI semantic roles.

    Deterministic typing remains the fallback and protects against malformed or
    stale LLM mappings. AI data_role is used only when its column exists.
    """
    info = analyze_columns(df)
    _, mappings = _understanding_maps(understanding)
    role_map = {
        "continuous": "numeric_measure",
        "binary_categorical": "binary_category",
        "ordinal_categorical": "ordinal_category",
        "nominal_categorical": "categorical",
        "datetime": "datetime",
        "identifier": "identifier",
        "text": "high_cardinality_categorical",
        "target": "target",
        "unknown": "unknown",
    }
    for item in info:
        mapping = mappings.get(item["column"])
        if not mapping:
            continue
        ai_role = role_map.get(str(mapping.get("data_role", "unknown")))
        # Preserve stronger deterministic special cases (coordinates, dates,
        # identifiers, years, counts). AI resolves ordinary numeric/category ambiguity.
        if ai_role and item["semantic_type"] not in {
            "geographic_latitude", "geographic_longitude", "geographic_code",
            "datetime", "year", "temporal_component", "identifier", "constant",
        }:
            item["semantic_type"] = ai_role
        item["semantic_role"] = mapping.get("semantic_role", "")
        item["semantic_confidence"] = mapping.get("confidence", 0.0)
        item["unit"] = mapping.get("unit", "")
    return info


def recommend_visualizations(
    df: pd.DataFrame,
    max_recommendations: int = 10,
    understanding: Any = None,
) -> list[dict]:
    """Plan a diverse set of statistically suitable charts for a dataset.

    ``understanding`` is optional to preserve existing callers. It accepts the
    DatasetUnderstanding model or its ``model_dump()`` dictionary.
    """
    if max_recommendations <= 0 or not isinstance(df, pd.DataFrame) or df.empty:
        return []

    domain, _ = _understanding_maps(understanding)
    columns = _semantic_columns(df, understanding)
    by_type = lambda *types: [x["column"] for x in columns if x["semantic_type"] in types]
    measures = by_type("numeric_measure", "count")
    # Counts are valid business measures, but prefer true continuous measures.
    continuous_measures = by_type("numeric_measure")
    measure_pool = continuous_measures or measures
    best_measure = choose_best_measure(df, measure_pool)
    numeric_distribution = by_type("numeric_measure", "count")
    categories = by_type("categorical", "binary_category", "ordinal_category")
    dates = by_type("datetime")
    lats, lons = by_type("geographic_latitude"), by_type("geographic_longitude")

    recs: list[dict] = []

    # Distribution charts exclude binary/ordinal codes and identifiers.
    for column in numeric_distribution:
        if df[column].nunique(dropna=True) > 1:
            recs.append({"type": "histogram", "column": column, "score": 0.62,
                         "reason": f"Examine the distribution and spread of {column}.",
                         "title": f"Distribution of {column}"})

    # Category comparisons: healthcare benefits from distribution comparisons
    # (box plots); other domains default to aggregate bar charts.
    for category in categories:
        cardinality = int(df[category].nunique(dropna=True))
        if not 2 <= cardinality <= 20:
            continue
        if best_measure is None:
            recs.append({"type": "bar", "x": category, "column": category,
                         "aggregation": "count", "score": 0.70,
                         "reason": f"Show the number of records in each {category} group.",
                         "title": f"Records by {category}"})
        elif domain == "healthcare" and df[best_measure].nunique(dropna=True) > 2:
            recs.append({"type": "box", "x": category, "y": best_measure,
                         "score": 0.82 if cardinality <= 6 else 0.72,
                         "reason": f"Compare the distribution of {best_measure} across {category} groups.",
                         "title": f"{best_measure} by {category}"})
        else:
            aggregation = "mean" if domain in {"healthcare", "social_sciences"} else "sum"
            recs.append({"type": "bar", "x": category, "column": category,
                         "y": best_measure, "value_column": best_measure,
                         "aggregation": aggregation,
                         "score": 0.78 if cardinality <= 10 else 0.70,
                         "reason": f"Compare {aggregation} {best_measure} across {category} groups.",
                         "title": f"{aggregation.title()} {best_measure} by {category}"})

    # Scatter is limited to continuous/count measures, never binary/ordinal codes.
    scatter_columns = by_type("numeric_measure", "count")
    if len(scatter_columns) >= 2:
        corr = df[scatter_columns].corr(numeric_only=True)
        for i, x in enumerate(scatter_columns):
            for y in scatter_columns[i + 1:]:
                value = corr.at[x, y]
                if pd.isna(value):
                    continue
                # Require a non-trivial association to avoid chart spam.
                if abs(float(value)) < 0.25:
                    continue
                recs.append({"type": "scatter", "x": x, "y": y,
                             "score": 0.50 + abs(float(value)) * 0.45,
                             "reason": f"Explore the relationship between {x} and {y} (Pearson r={value:.2f}).",
                             "title": f"{y} vs {x}"})

    # Time-series: aggregation is explicit and selected by domain/measure semantics.
    for date_column in dates:
        frequency = choose_time_frequency(df, date_column)
        for measure in measure_pool:
            aggregation = "sum"
            if domain in {"healthcare", "social_sciences"}:
                aggregation = "mean"
            elif any(token in measure.lower() for token in ("price", "rate", "return", "temperature", "score", "index")):
                aggregation = "mean"
            recs.append({"type": "line", "x": date_column, "y": measure,
                         "frequency": frequency, "aggregation": aggregation,
                         "score": 0.86, "reason": f"Track {aggregation} {measure} over time.",
                         "title": f"{aggregation.title()} {measure} over time"})

    if lats and lons:
        recs.append({"type": "map", "latitude": lats[0], "longitude": lons[0],
                     "score": 0.90, "reason": "Explore the geographic distribution of records.",
                     "title": "Geographic Distribution"})

    recs.sort(key=lambda item: item["score"], reverse=True)
    return select_diverse_recommendations(recs, max_recommendations)
