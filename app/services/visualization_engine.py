import pandas as pd

from app.services.column_intelligence import analyze_columns


def choose_best_measure(
    df: pd.DataFrame,
    measure_columns: list[str],
) -> str | None:
    """
    Choose the most useful business measure
    for categorical comparisons.
    """

    priority_keywords = [
        "sales",
        "revenue",
        "profit",
        "amount",
        "value",
        "quantity",
    ]

    for keyword in priority_keywords:

        for column in measure_columns:

            if keyword in column.lower():
                return column

    if measure_columns:
        return measure_columns[0]

    return None


def is_suitable_for_scatter(
    semantic_type: str,
) -> bool:
    """
    Determine whether a semantic column type
    is suitable for a scatter plot.
    """

    return semantic_type in {
        "numeric_measure",
        "count",
    }


def select_diverse_recommendations(
    recommendations: list[dict],
    max_recommendations: int,
) -> list[dict]:
    """
    Select high-scoring recommendations while
    preventing the final list from being dominated
    by one chart type.
    """

    type_limits = {
        "scatter": 3,
        "line": 2,
        "bar": 3,
        "histogram": 2,
        "map": 1,
    }

    selected = []
    type_counts = {}

    for recommendation in recommendations:

        chart_type = recommendation["type"]

        current_count = type_counts.get(
            chart_type,
            0,
        )

        limit = type_limits.get(
            chart_type,
            2,
        )

        if current_count >= limit:
            continue

        selected.append(recommendation)

        type_counts[chart_type] = (
            current_count + 1
        )

        if len(selected) >= max_recommendations:
            break

    return selected


def choose_time_frequency(
    df: pd.DataFrame,
    date_column: str,
) -> str:
    """
    Choose an appropriate time aggregation
    based on the number of unique dates.
    """

    unique_dates = (
        pd.to_datetime(
            df[date_column],
            errors="coerce",
        )
        .dropna()
        .nunique()
    )

    if unique_dates <= 90:
        return "D"

    if unique_dates <= 365:
        return "W"

    return "ME"


def recommend_visualizations(
    df: pd.DataFrame,
    max_recommendations: int = 10,
) -> list[dict]:
    """
    Recommend and rank useful visualizations based on
    semantic understanding of the dataset.
    """

    recommendations = []

    # ==================================================
    # 1. UNDERSTAND THE COLUMNS
    # ==================================================

    column_information = analyze_columns(df)

    # --------------------------------------------------
    # Numeric measurements
    # --------------------------------------------------

    numeric_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] in {
            "numeric_measure",
            "count",
        }
    ]

    # --------------------------------------------------
    # Pure measurements
    # Used for meaningful trends over time
    # --------------------------------------------------

    measure_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] == "numeric_measure"
    ]

    # --------------------------------------------------
    # Choose the best business measure
    # --------------------------------------------------

    best_measure = choose_best_measure(
        df,
        measure_columns,
    )

    # --------------------------------------------------
    # Categorical columns
    # --------------------------------------------------

    categorical_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] == "categorical"
    ]

    # --------------------------------------------------
    # Datetime columns
    # --------------------------------------------------

    datetime_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] == "datetime"
    ]

    # --------------------------------------------------
    # Geographic latitude
    # --------------------------------------------------

    latitude_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"]
        == "geographic_latitude"
    ]

    # --------------------------------------------------
    # Geographic longitude
    # --------------------------------------------------

    longitude_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"]
        == "geographic_longitude"
    ]

    # ==================================================
    # 2. NUMERIC DISTRIBUTIONS
    # ==================================================

    for column in numeric_columns:

        recommendations.append(
            {
                "type": "histogram",
                "column": column,
                "score": 0.60,
                "reason": (
                    f"Distribution of {column}"
                ),
            }
        )

    # ==================================================
    # 3. METRIC-AWARE CATEGORICAL COMPARISONS
    # ==================================================

    for column in categorical_columns:

        unique_count = df[column].nunique(
            dropna=True
        )

        if (
            2 <= unique_count <= 20
            and best_measure is not None
        ):

            score = 0.70

            if unique_count <= 10:
                score += 0.10

            recommendations.append(
                {
                    "type": "bar",
                    "column": column,
                    "value_column": best_measure,
                    "score": score,
                    "reason": (
                        f"{best_measure} by {column}"
                    ),
                }
            )

    # ==================================================
    # 4. NUMERIC VS NUMERIC
    # ==================================================

    if len(numeric_columns) >= 2:

        correlation_matrix = df[
            numeric_columns
        ].corr()

        correlation_values = (
            correlation_matrix.to_numpy(
                dtype=float
            )
        )

        for i in range(len(numeric_columns)):

            for j in range(
                i + 1,
                len(numeric_columns),
            ):

                x_column = numeric_columns[i]
                y_column = numeric_columns[j]

                x_type = next(
                    item["semantic_type"]
                    for item in column_information
                    if item["column"] == x_column
                )

                y_type = next(
                    item["semantic_type"]
                    for item in column_information
                    if item["column"] == y_column
                )

                if not (
                    is_suitable_for_scatter(x_type)
                    and is_suitable_for_scatter(y_type)
                ):
                    continue

                correlation = correlation_values[i, j]

                if pd.isna(correlation):
                    continue

                score = 0.50 + (
                    abs(correlation) * 0.50
                )

                recommendations.append(
                    {
                        "type": "scatter",
                        "x": x_column,
                        "y": y_column,
                        "score": float(score),
                        "reason": (
                            f"Relationship between "
                            f"{x_column} and "
                            f"{y_column}"
                        ),
                    }
                )

    # ==================================================
    # 5. DATETIME VS MEASUREMENT
    # ==================================================

    for date_column in datetime_columns:

        for numeric_column in measure_columns:

            recommendations.append(
                {
                    "type": "line",
                    "x": date_column,
                    "y": numeric_column,
                    "frequency": choose_time_frequency(
                        df,
                        date_column,
                    ),
                    "score": 0.85,
                    "reason": (
                        f"Trend of {numeric_column} "
                        f"over {date_column}"
                    ),
                }
            )

    # ==================================================
    # 6. GEOGRAPHIC MAP
    # ==================================================

    if latitude_columns and longitude_columns:

        latitude = latitude_columns[0]
        longitude = longitude_columns[0]

        recommendations.append(
            {
                "type": "map",
                "latitude": latitude,
                "longitude": longitude,
                "score": 0.90,
                "reason": (
                    f"Geographic distribution using "
                    f"{latitude} and {longitude}"
                ),
            }
        )

    # ==================================================
    # 7. RANK RECOMMENDATIONS
    # ==================================================

    recommendations.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # ==================================================
    # 8. SELECT DIVERSE RECOMMENDATIONS
    # ==================================================

    return select_diverse_recommendations(
        recommendations,
        max_recommendations,
    )