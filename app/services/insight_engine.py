"""Universal, context-aware insight engine for InsightFlow supporting any domain."""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import cast

from app.services.analysis_engine import (
    analyze_correlation,
    analyze_distribution,
    analyze_trend,
)

def _finite_numeric(series: pd.Series) -> pd.Series:
    """Return finite numeric observations while preserving row indexes."""
    values = pd.to_numeric(series, errors="coerce")
    return values.replace([np.inf, -np.inf], np.nan).dropna()


def build_analysis_context(
    df: pd.DataFrame,
    recommendations: list[dict],
    deterministic_findings: list[dict] | None = None,
    understanding: dict | None = None,
) -> dict:
    """Build a structured analytical context enhanced by dataset understanding."""
    context = {
        "dataset": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "domain": understanding.get("domain", "general") if understanding else "general",
            "dataset_kind": understanding.get("dataset_kind", "Dataset") if understanding else "Dataset",
        },
        "metrics": {},
        "deterministic_findings": [],
        "recommendations": [],
    }

    numeric_columns = df.select_dtypes(include="number").columns
    for column in numeric_columns:
        series = _finite_numeric(df[column])
        if series.empty:
            continue
        context["metrics"][column] = {
            "mean": float(series.mean()),
            "median": float(series.median()),
            "min": float(series.min()),
            "max": float(series.max()),
            "total": float(series.sum()),
            "std": float(series.std()) if len(series) > 1 else None,
            "valid_count": int(len(series)),
        }

    if deterministic_findings is None:
        for recommendation in recommendations:
            insight = generate_insight(df, recommendation, understanding)
            context["deterministic_findings"].append(
                {
                    "type": recommendation.get("type"),
                    "reason": recommendation.get("reason"),
                    "score": recommendation.get("score"),
                    "insight": insight,
                }
            )
    else:
        context["deterministic_findings"] = [dict(item) for item in deterministic_findings]

    for recommendation in recommendations:
        context["recommendations"].append(recommendation)

    return context


def generate_insight(
    df: pd.DataFrame,
    recommendation: dict,
    understanding: dict | None = None,
) -> str:
    """Generate human-readable, context-aware analytical insights for any dataset domain."""
    chart_type = recommendation.get("type", "unknown")

    # ==================================================
    # 1. SCATTER PLOT
    # ==================================================
    if chart_type == "scatter":
        x_column = recommendation["x"]
        y_column = recommendation["y"]

        correlation = analyze_correlation(df, x_column, y_column)
        if correlation is None:
            return f"No reliable relationship could be calculated between {x_column} and {y_column}."

        abs_corr = abs(correlation)
        strength = "very strong" if abs_corr >= 0.8 else "strong" if abs_corr >= 0.6 else "moderate" if abs_corr >= 0.4 else "weak"
        direction = "positive" if correlation > 0 else "inverse"

        return (
            f"**Driver Analysis ({x_column} vs {y_column})**: {x_column} and {y_column} exhibit a "
            f"{strength} {direction} pattern. Changes in {x_column} closely mirror shifts in {y_column}, "
            f"highlighting a core behavioral link across records."
        )

    # ==================================================
    # 2. HISTOGRAM
    # ==================================================
    if chart_type == "histogram":
        column = recommendation["column"]
        distribution = analyze_distribution(df, column)

        mean = distribution.get("mean")
        median = distribution.get("median")
        if mean is None or median is None:
            return f"No valid numeric values available for {column}."

        return (
            f"**Distribution Profile ({column})**: Typical values for {column} center around an average "
            f"of {mean:,.2f} (median: {median:,.2f}). This spread provides a reliable baseline for identifying "
            f"normality versus extreme outliers in your dataset."
        )

    # ==================================================
    # 3. BAR CHART
    # ==================================================
    if chart_type == "bar":
        column = recommendation["column"]
        value_column = recommendation.get("value_column")

        if value_column is not None and value_column in df.columns:
            sub_df = df[[column, value_column]].copy()
            sub_df[value_column] = pd.to_numeric(sub_df[value_column], errors="coerce")
            grouped = sub_df.groupby(column)[value_column].sum().dropna().sort_values(ascending=False)

            if not grouped.empty:
                top_cat = grouped.index[0]
                top_val = grouped.iloc[0]
                total_val = grouped.sum()
                pct = (top_val / total_val) * 100 if total_val > 0 else 0
                return (
                    f"**Segment Leader ({column})**: **{top_cat}** dominates total {value_column} with "
                    f"{top_val:,.2f}, representing {pct:.1f}% of overall volume across all categories."
                )

        counts = df[column].value_counts(dropna=True)
        if not counts.empty:
            top_cat = counts.index[0]
            top_count = counts.iloc[0]
            pct = (top_count / len(df)) * 100
            return (
                f"**Frequency Concentration ({column})**: **{top_cat}** is the most prevalent category, "
                f"accounting for {pct:.1f}% ({top_count:,} records) of the entire dataset."
            )

    # ==================================================
    # 4. LINE CHART
    # ==================================================
    if chart_type == "line":
        x_column = recommendation["x"]
        y_column = recommendation["y"]
        frequency = recommendation.get("frequency", "D")

        chart_data = analyze_trend(df, x_column, y_column, frequency)
        if chart_data.empty or len(chart_data) < 2:
            return f"Insufficient temporal points to evaluate the trend of {y_column} over {x_column}."

        values = pd.to_numeric(chart_data[y_column], errors="coerce").dropna().to_numpy()
        if len(values) < 2:
            return f"Not enough valid data points to determine trajectory for {y_column}."

        first_val = values[0]
        last_val = values[-1]
        pct_change = ((last_val - first_val) / abs(first_val)) * 100 if first_val != 0 else 0
        direction = "grew" if pct_change > 0 else "declined" if pct_change < 0 else "remained stable"

        return (
            f"**Temporal Trajectory ({y_column} over {x_column})**: {y_column} {direction} by "
            f"{abs(pct_change):.1f}% from the initial period ({first_val:,.2f}) to the latest recorded "
            f"period ({last_val:,.2f}), revealing key momentum shifts over time."
        )

    # ==================================================
    # 5. BOX PLOT
    # ==================================================
    if chart_type == "box":
        x_col = recommendation.get("x")
        y_col = recommendation.get("y")
        return (
            f"**Variance & Spread ({y_col} across {x_col})**: Compares quartile distribution ranges, "
            f"median benchmarks, and potential outlier boundaries across different categories."
        )

    # ==================================================
    # 6. MAP
    # ==================================================
    if chart_type == "map":
        return "**Geographic Spread**: Visualizes spatial concentrations and regional distribution density across coordinates."

    return f"Analytical breakdown for {chart_type} analysis."