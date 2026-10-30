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
) -> dict:
    """
    Build a structured analytical context for the AI layer.

    The AI receives:
    - dataset information
    - important numerical metrics
    - deterministic analytical findings
    - visualization recommendations

    This keeps the AI focused on interpreting facts that
    InsightFlow has already calculated.
    """

    context = {
        "dataset": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
        },
        "metrics": {},
        "deterministic_findings": [],
        "recommendations": [],
    }

    # ======================================================
    # 1. BASIC NUMERIC METRICS
    # ======================================================

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

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
            "q1": float(series.quantile(0.25)),
            "q3": float(series.quantile(0.75)),
            "skewness": (
                float(cast(float, series.skew()))
                if len(series) >= 3 and pd.notna(series.skew())
                else None
            ),
            "valid_count": int(len(series)),
        }

    # ======================================================
    # 2. DETERMINISTIC ANALYTICAL FINDINGS
    # ======================================================

    for recommendation in recommendations:

        insight = generate_insight(
            df,
            recommendation,
        )

        context["deterministic_findings"].append(
            {
                "type": recommendation.get(
                    "type"
                ),
                "reason": recommendation.get(
                    "reason"
                ),
                "score": recommendation.get(
                    "score"
                ),
                "insight": insight,
            }
        )

    # ======================================================
    # 3. VISUALIZATION RECOMMENDATIONS
    # ======================================================

    for recommendation in recommendations:

        context["recommendations"].append(
            recommendation
        )

    return context

def generate_insight(
    df: pd.DataFrame,
    recommendation: dict,
) -> str:
    """
    Generate a deterministic analytical explanation
    for a visualization recommendation.
    """

    chart_type = recommendation.get("type", "unknown")

    # ==================================================
    # 1. SCATTER PLOT
    # ==================================================

    if chart_type == "scatter":

        x_column = recommendation["x"]
        y_column = recommendation["y"]

        correlation = analyze_correlation(
            df,
            x_column,
            y_column,
            method=recommendation.get("method", "pearson"),
        )

        if correlation is None:
            return (
                f"No reliable relationship could be "
                f"calculated between {x_column} and "
                f"{y_column}."
            )

        absolute_correlation = abs(correlation)

        if absolute_correlation >= 0.80:
            strength = "very strong"

        elif absolute_correlation >= 0.60:
            strength = "strong"

        elif absolute_correlation >= 0.40:
            strength = "moderate"

        elif absolute_correlation >= 0.20:
            strength = "weak"

        else:
            strength = "very weak"

        if correlation > 0:
            direction = "positive"

        elif correlation < 0:
            direction = "negative"

        else:
            direction = "neutral"

        return (
            f"{x_column} and {y_column} show a "
            f"{strength} {direction} relationship "
            f"(correlation: {correlation:.2f})."
        )

    # ==================================================
    # 2. HISTOGRAM
    # ==================================================

    if chart_type == "histogram":

        column = recommendation["column"]

        distribution = analyze_distribution(
            df,
            column,
        )

        mean = distribution["mean"]
        median = distribution["median"]
        skewness = distribution.get("skewness")

        if mean is None or median is None:
            return (
                f"No valid numeric values were available "
                f"for {column}."
            )

        if skewness is None:
            distribution_note = "Skewness could not be determined."
        elif skewness >= 1:
            distribution_note = "The values may be skewed to the right, showing substantial right skew."
        elif skewness >= 0.5:
            distribution_note = "The values may be skewed to the right, showing moderate right skew."
        elif skewness <= -1:
            distribution_note = "The values may be skewed to the left, showing substantial left skew."
        elif skewness <= -0.5:
            distribution_note = "The values may be skewed to the left, showing moderate left skew."
        else:
            distribution_note = "The mean and median are relatively close, indicating relatively low skewness."

        return (
            f"The distribution of {column} has a mean of "
            f"{mean:,.2f} and a median of {median:,.2f}. "
            f"{distribution_note}"
        )

    # 3. BAR CHART
    # ==================================================

    if chart_type == "bar":

        column = recommendation["column"]

        # --------------------------------------------------
        # Metric-based bar chart
        # --------------------------------------------------

        value_column = recommendation.get(
            "value_column"
        )

        if value_column is not None:

            if value_column not in df.columns or column not in df.columns:
                return (
                    f"No valid values were available to compare "
                    f"{value_column} across {column}."
                )

            metric_data = df[[column, value_column]].copy()
            metric_data[value_column] = pd.to_numeric(
                metric_data[value_column], errors="coerce"
            )
            metric_data[value_column] = metric_data[value_column].replace(
                [np.inf, -np.inf], np.nan
            )
            metric_data = metric_data.dropna(
                subset=[column, value_column]
            )

            grouped_data = (
                metric_data.groupby(column)[value_column]
                .sum(min_count=1)
                .dropna()
                .sort_values(ascending=False)
            )

            if grouped_data.empty:
                return (
                    f"No valid values were available "
                    f"to compare {value_column} "
                    f"across {column}."
                )

            top_category = grouped_data.index[0]
            top_value = grouped_data.iloc[0]

            total_value = grouped_data.sum()

            if total_value == 0:
                return (
                    f"{top_category} has the highest "
                    f"total {value_column}, with a value "
                    f"of {top_value:,.2f}."
                )

            percentage = (
                top_value / total_value
            ) * 100

            return (
                f"{top_category} has the highest total "
                f"{value_column}, with a value of "
                f"{top_value:,.2f}, representing "
                f"{percentage:.1f}% of the total "
                f"{value_column}."
            )

        # --------------------------------------------------
        # Fallback: category frequency
        # --------------------------------------------------

        counts = df[column].value_counts(
            dropna=True
        )

        if counts.empty:
            return (
                f"No categorical values were available "
                f"for {column}."
            )

        top_category = counts.index[0]
        top_count = counts.iloc[0]

        total_count = counts.sum()

        top_percentage = (
            top_count / total_count
        ) * 100

        if top_percentage >= 50:
            distribution_note = (
                "This category represents more than "
                "half of the valid records."
            )

        elif top_percentage >= 30:
            distribution_note = (
                "This category represents a substantial "
                "share of the valid records."
            )

        else:
            distribution_note = (
                "No single category dominates the "
                "distribution."
            )

        return (
            f"{top_category} is the most common category "
            f"in {column}, accounting for "
            f"{top_percentage:.1f}% of valid records "
            f"({top_count:,} records). "
            f"{distribution_note}"
        )

    # ==================================================
    # 4. LINE CHART
    # ==================================================

    if chart_type == "line":

        x_column = recommendation["x"]
        y_column = recommendation["y"]

        frequency = recommendation.get(
            "frequency",
            "D",
        )

        chart_data = analyze_trend(
            df,
            x_column,
            y_column,
            frequency,
        )

        if chart_data.empty:
            return (
                f"No valid data was available to analyze "
                f"{y_column} over {x_column}."
            )

        if len(chart_data) < 2:
            return (
                f"Not enough time points are available to "
                f"analyze the trend of {y_column}."
            )

        values = pd.to_numeric(
            chart_data[y_column], errors="coerce"
        ).to_numpy(dtype=float)

        valid_mask = np.isfinite(values)
        valid_values = values[valid_mask]
        valid_periods = np.arange(len(values), dtype=float)[valid_mask]

        if len(valid_values) < 2:
            return (
                f"Not enough valid time points are available to "
                f"analyze the trend of {y_column}."
            )

        first_value = valid_values[0]
        last_value = valid_values[-1]

        # --------------------------------------------------
        # 1. Calculate endpoint change
        # --------------------------------------------------

        if first_value == 0:
            endpoint_change_text = (
                f"changed from {first_value:,.2f} "
                f"to {last_value:,.2f}"
            )
        else:
            endpoint_change = (
                (last_value - first_value)
                / abs(first_value)
            ) * 100

            if endpoint_change > 0:
                endpoint_direction = "increased"
            elif endpoint_change < 0:
                endpoint_direction = "decreased"
            else:
                endpoint_direction = "remained unchanged"

            endpoint_change_text = (
                f"{endpoint_direction} by "
                f"{abs(endpoint_change):.1f}%, "
                f"from {first_value:,.2f} "
                f"to {last_value:,.2f}"
            )

                # --------------------------------------------------
        # 2. Estimate the overall linear trend
        # --------------------------------------------------

        slope, intercept = np.polyfit(
            valid_periods,
            valid_values,
            1,
        )

        fitted_values = intercept + slope * valid_periods

        residual_sum_squares = np.sum(
            (valid_values - fitted_values) ** 2
        )

        total_sum_squares = np.sum(
            (valid_values - np.mean(valid_values)) ** 2
        )

        if total_sum_squares > 0:
            r_squared = 1 - (
                residual_sum_squares / total_sum_squares
            )
            r_squared = float(np.clip(r_squared, 0, 1))
        else:
            r_squared = None

                # --------------------------------------------------
        # 3. Describe trend direction and fit strength
        # --------------------------------------------------

        if slope > 0:
            trend_direction = "upward"
        elif slope < 0:
            trend_direction = "downward"
        else:
            trend_direction = "flat"

        if r_squared is None:
            trend_summary = (
                "The values are constant, so the linear "
                "model's explanatory strength is undefined."
            )

        else:
            if r_squared >= 0.70:
                fit_strength = "strong"
            elif r_squared >= 0.40:
                fit_strength = "moderate"
            else:
                fit_strength = "weak"

            trend_summary = (
                f"The fitted linear trend is {trend_direction}, "
                f"with a {fit_strength} linear fit "
                f"(R² = {r_squared:.2f}). "
                f"The model explains approximately "
                f"{r_squared * 100:.1f}% of the observed variation."
            )

        return (
            f"{y_column} {endpoint_change_text} between "
            f"the first and last observed periods. "
            f"{trend_summary}"
        )
    # ==================================================
    # 5. MAP
    # ==================================================

    if chart_type == "map":

        latitude = recommendation["latitude"]
        longitude = recommendation["longitude"]

        if latitude not in df.columns or longitude not in df.columns:
            return (
                f"No valid geographic coordinates were "
                f"available using {latitude} and {longitude}."
            )

        geographic_data = df[[latitude, longitude]].copy()
        geographic_data[latitude] = pd.to_numeric(
            geographic_data[latitude], errors="coerce"
        )
        geographic_data[longitude] = pd.to_numeric(
            geographic_data[longitude], errors="coerce"
        )
        geographic_data = geographic_data.replace(
            [np.inf, -np.inf], np.nan
        ).dropna(subset=[latitude, longitude])
        geographic_data = geographic_data[
            geographic_data[latitude].between(-90, 90)
            & geographic_data[longitude].between(-180, 180)
        ]

        if geographic_data.empty:
            return (
                f"No valid geographic coordinates were "
                f"available using {latitude} and {longitude}."
            )

        minimum_latitude = geographic_data[latitude].min()
        maximum_latitude = geographic_data[latitude].max()

        minimum_longitude = geographic_data[longitude].min()
        maximum_longitude = geographic_data[longitude].max()

        latitude_range = (
            maximum_latitude - minimum_latitude
        )

        longitude_range = (
            maximum_longitude - minimum_longitude
        )

        record_count = len(geographic_data)

        return (
            f"The dataset contains {record_count:,} "
            f"geographic records spanning approximately "
            f"{latitude_range:.2f}° of latitude and "
            f"{longitude_range:.2f}° of longitude."
        )

    # ==================================================
    # 6. UNKNOWN CHART TYPE
    # ==================================================

    return (
        "No analytical explanation is available "
        f"for chart type: {chart_type}."
    )