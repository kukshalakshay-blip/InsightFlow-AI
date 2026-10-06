import pandas as pd

from app.services.analysis_engine import (
    analyze_correlation,
    analyze_distribution,
    analyze_trend,
)

def build_analysis_context(
    df: pd.DataFrame,
    recommendations: list[dict],
) -> dict:
    """
    Build a structured summary of the dataset that can
    later be passed to an AI model.
    """

    context = {
        "dataset": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
        },
        "metrics": {},
        "recommendations": [],
    }

    # ----------------------------------------------
    # Basic numeric metrics
    # ----------------------------------------------

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:

        series = df[column].dropna()

        if series.empty:
            continue

        context["metrics"][column] = {
            "mean": float(series.mean()),
            "median": float(series.median()),
            "min": float(series.min()),
            "max": float(series.max()),
            "total": float(series.sum()),
        }

    # ----------------------------------------------
    # Visualization recommendations
    # ----------------------------------------------

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

    chart_type = recommendation["type"]

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
        difference_percentage = distribution[
            "difference_percentage"
        ]

        if mean is None or median is None:
            return (
                f"No valid numeric values were available "
                f"for {column}."
            )

        if difference_percentage is None:
            return (
                f"The distribution of {column} has a "
                f"mean of {mean:,.2f} and a median of "
                f"{median:,.2f}."
            )

        if difference_percentage >= 20:
            distribution_note = (
                "The substantial difference between the "
                "mean and median suggests that the "
                "distribution may be skewed."
            )

        elif difference_percentage >= 10:
            distribution_note = (
                "The mean and median differ noticeably, "
                "indicating some asymmetry in the "
                "distribution."
            )

        else:
            distribution_note = (
                "The mean and median are relatively close, "
                "suggesting a more balanced distribution."
            )

        return (
            f"The distribution of {column} has a mean of "
            f"{mean:,.2f} and a median of "
            f"{median:,.2f}. "
            f"{distribution_note}"
        )

    # ==================================================
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

            grouped_data = (
                df.groupby(column)[value_column]
                .sum()
                .sort_values(
                    ascending=False
                )
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

        chart_data = analyze_trend(
            df,
            x_column,
            y_column,
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

        first_value = chart_data[y_column].iloc[0]
        last_value = chart_data[y_column].iloc[-1]

        if first_value == 0:
            return (
                f"{y_column} changed from "
                f"{first_value:,.2f} to "
                f"{last_value:,.2f} over the observed period."
            )

        percentage_change = (
            (last_value - first_value)
            / abs(first_value)
        ) * 100

        if percentage_change > 0:
            direction = "increased"

        elif percentage_change < 0:
            direction = "decreased"

        else:
            direction = "remained stable"

        return (
            f"Average {y_column} {direction} by "
            f"{abs(percentage_change):.1f}% "
            f"over the observed period, changing from "
            f"{first_value:,.2f} to {last_value:,.2f}."
        )

    # ==================================================
    # 5. MAP
    # ==================================================

    if chart_type == "map":

        latitude = recommendation["latitude"]
        longitude = recommendation["longitude"]

        geographic_data = df[
            [latitude, longitude]
        ].dropna(
            subset=[latitude, longitude]
        )

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