import pandas as pd

from app.services.column_intelligence import analyze_columns


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
    # 3. CATEGORICAL DISTRIBUTIONS
    # ==================================================

    for column in categorical_columns:

        unique_count = df[column].nunique(
            dropna=True
        )

        if 2 <= unique_count <= 20:

            score = 0.70

            if unique_count <= 10:
                score += 0.10

            recommendations.append(
                {
                    "type": "bar",
                    "column": column,
                    "score": score,
                    "reason": (
                        f"Category frequency for "
                        f"{column}"
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

                correlation = (
                    correlation_values[i, j]
                )

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
    # 8. RETURN TOP RECOMMENDATIONS
    # ==================================================

    return recommendations[
        :max_recommendations
    ]