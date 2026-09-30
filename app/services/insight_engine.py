import pandas as pd


def generate_insight(
    df: pd.DataFrame,
    recommendation: dict,
) -> str:
    """
    Generate a deterministic analytical explanation
    for a visualization recommendation.
    """

    chart_type = recommendation["type"]

    # --------------------------------------------------
    # Scatter plot
    # --------------------------------------------------

    if chart_type == "scatter":

        x_column = recommendation["x"]
        y_column = recommendation["y"]

        correlation = df[x_column].corr(
            df[y_column]
        )

        if pd.isna(correlation):
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

    # --------------------------------------------------
    # Histogram
    # --------------------------------------------------

    # --------------------------------------------------
    # Histogram
    # --------------------------------------------------

    if chart_type == "histogram":

        column = recommendation["column"]

        numeric_data = df[column].dropna()

        if numeric_data.empty:
            return (
                f"No valid numeric values were available "
                f"for {column}."
            )

        mean = numeric_data.mean()
        median = numeric_data.median()

        if median == 0:
            return (
                f"The distribution of {column} has a "
                f"mean of {mean:,.2f} and a median of "
                f"{median:,.2f}."
            )

        mean_median_difference = (
            abs(mean - median)
            / abs(median)
        ) * 100

        if mean_median_difference >= 20:
            distribution_note = (
                "The substantial difference between the "
                "mean and median suggests that the "
                "distribution may be skewed."
            )

        elif mean_median_difference >= 10:
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

    # --------------------------------------------------
    # Bar chart
    # --------------------------------------------------

    if chart_type == "bar":

        column = recommendation["column"]

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

        return (
            f"{top_category} is the most common "
            f"category in {column}, with "
            f"{top_count:,} records."
        )

    # --------------------------------------------------
    # Line chart
    # --------------------------------------------------

    if chart_type == "line":

        x_column = recommendation["x"]
        y_column = recommendation["y"]

        chart_data = df[
            [x_column, y_column]
        ].copy()

        chart_data[x_column] = pd.to_datetime(
            chart_data[x_column],
            errors="coerce",
            format="mixed",
        )

        chart_data = chart_data.dropna(
            subset=[x_column, y_column]
        )

        if chart_data.empty:
            return (
                f"No valid data was available to analyze "
                f"{y_column} over {x_column}."
            )

        chart_data = (
            chart_data
            .groupby(
                x_column,
                as_index=False,
            )[y_column]
            .mean()
            .sort_values(x_column)
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
            f"{first_value:,.2f} to "
            f"{last_value:,.2f}."
        )

    # --------------------------------------------------
    # Map
    # --------------------------------------------------

    if chart_type == "map":

        latitude = recommendation["latitude"]
        longitude = recommendation["longitude"]

        geographic_data = df[
            [latitude, longitude]
        ].copy()

        geographic_data = geographic_data.dropna(
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

    # --------------------------------------------------
    # Unknown chart type
    # --------------------------------------------------

    return (
        "No analytical explanation is available "
        f"for chart type: {chart_type}."
    )