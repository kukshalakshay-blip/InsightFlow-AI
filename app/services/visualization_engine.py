"""Deterministic, intelligence-aware visualization planning for InsightFlow."""
from __future__ import annotations

from numbers import Real
from typing import Any
import pandas as pd

from app.services.column_intelligence import analyze_columns

MEASURE_PRIORITY = ("price", "sales", "revenue", "profit", "amount", "value", "score", "rate", "cost", "quantity", "score", "salary", "income")

def _as_dict(value: Any) -> dict:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value if isinstance(value, dict) else {}

def _understanding_maps(understanding: Any) -> tuple[str, dict[str, dict]]:
    payload = _as_dict(understanding)
    domain = str(payload.get("domain", "general")).lower()
    mappings = {}
    for item in payload.get("column_meanings", []) or []:
        if isinstance(item, dict) and item.get("column"):
            mappings[str(item["column"])] = item
    return domain, mappings

def choose_best_measure(df: pd.DataFrame, measure_columns: list[str]) -> str | None:
    for keyword in MEASURE_PRIORITY:
        for column in measure_columns:
            if keyword in column.lower():
                return column
    return measure_columns[0] if measure_columns else None

def select_diverse_recommendations(recommendations: list[dict], max_recommendations: int) -> list[dict]:
    if max_recommendations <= 0:
        return []
    # Strict limits mapped to fully supported renderer types: scatter, histogram, bar, line, box, map
    type_limits = {"scatter": 3, "line": 2, "bar": 3, "histogram": 2, "box": 2, "map": 1}
    selected, counts = [], {}
    seen_signatures = set()
    for index, recommendation in enumerate(recommendations):
        chart_type = recommendation["type"]
        signature = (chart_type, recommendation.get("x"), recommendation.get("y"),
                     recommendation.get("column"), recommendation.get("latitude"),
                     recommendation.get("longitude"))
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
        if ai_role and item["semantic_type"] not in {
            "geographic_latitude", "geographic_longitude", "geographic_code",
            "datetime", "year", "temporal_component", "identifier", "constant",
        }:
            item["semantic_type"] = ai_role
        item["semantic_role"] = mapping.get("semantic_role", "")
    return info

def recommend_visualizations(
    df: pd.DataFrame,
    max_recommendations: int = 10,
    understanding: Any = None,
) -> list[dict]:
    if max_recommendations <= 0 or not isinstance(df, pd.DataFrame) or df.empty:
        return []

    domain, _ = _understanding_maps(understanding)
    columns = _semantic_columns(df, understanding)
    by_type = lambda *types: [x["column"] for x in columns if x["semantic_type"] in types]
    measures = by_type("numeric_measure", "count")
    best_measure = choose_best_measure(df, measures)
    numeric_distribution = by_type("numeric_measure", "count")
    categories = by_type("categorical", "binary_category", "ordinal_category")
    dates = by_type("datetime")
    lats, lons = by_type("geographic_latitude"), by_type("geographic_longitude")

    recs: list[dict] = []

    # 1. Distribution Histograms
    for column in numeric_distribution[:3]:
        if df[column].nunique(dropna=True) > 1:
            recs.append({
                "type": "histogram", "column": column, "score": 0.65,
                "reason": f"Examine the statistical spread and distribution of {column}.",
                "title": f"Distribution of {column}"
            })

    # 2. Box Plots for Outlier & Spread Comparisons across Categories
    for category in categories:
        cardinality = int(df[category].nunique(dropna=True))
        if 2 <= cardinality <= 15 and best_measure:
            recs.append({
                "type": "box", "x": category, "y": best_measure, "score": 0.85,
                "reason": f"Compare variance, median benchmarks, and outliers of {best_measure} across {category}.",
                "title": f"Distribution Spread of {best_measure} by {category}"
            })
            break

    # 3. Category Comparisons (Bar Charts)
    for category in categories[:2]:
        cardinality = int(df[category].nunique(dropna=True))
        if not 2 <= cardinality <= 25:
            continue
        if best_measure is None:
            recs.append({
                "type": "bar", "x": category, "column": category, "aggregation": "count", "score": 0.70,
                "reason": f"Show record frequency distribution across {category}.",
                "title": f"Records by {category}"
            })
        else:
            recs.append({
                "type": "bar", "x": category, "column": category, "y": best_measure, "value_column": best_measure,
                "aggregation": "sum", "score": 0.80,
                "reason": f"Compare total {best_measure} across different {category} groups.",
                "title": f"Total {best_measure} by {category}"
            })

    # 4. Scatter Correlations for Key Drivers
    if len(measures) >= 2:
        corr = df[measures].corr(numeric_only=True)
        for i, x in enumerate(measures):
            for y in measures[i + 1:]:
                val = corr.at[x, y] if x in corr.columns and y in corr.columns else 0.0
                if not isinstance(val, Real):
                    continue
                correlation = float(val)
                if pd.isna(correlation) or abs(correlation) < 0.25:
                    continue
                recs.append({
                    "type": "scatter", "x": x, "y": y, "score": 0.60 + abs(correlation) * 0.40,
                    "reason": f"Analyze direct driver relationship between {x} and {y}.",
                    "title": f"{y} vs {x} Relationship"
                })

    # 5. Temporal Trends (Line charts for trajectory)
    for date_column in dates:
        frequency = choose_time_frequency(df, date_column)
        for measure in measures[:2]:
            recs.append({
                "type": "line", "x": date_column, "y": measure, "frequency": frequency, "aggregation": "mean",
                "score": 0.90, "reason": f"Track periodic trajectory and average movement of {measure} over {date_column}.",
                "title": f"{measure} Trend Over Time"
            })

    if lats and lons:
        recs.append({
            "type": "map", "latitude": lats[0], "longitude": lons[0], "score": 0.94,
            "reason": "Explore spatial clusters and geographic distribution patterns.",
            "title": "Geographic Cluster Spread"
        })

    recs.sort(key=lambda item: item["score"], reverse=True)
    return select_diverse_recommendations(recs, max_recommendations)