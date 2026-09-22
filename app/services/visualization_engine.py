import pandas as pd


def recommend_visualizations(
    df: pd.DataFrame,
    max_recommendations: int = 10,
) -> list[dict]:
    """
    Recommend and rank useful visualizations based on dataset structure.

    The function is dataset-agnostic and works with different combinations
    of numeric and categorical columns.
    """

    recommendations = []

    # --------------------------------------------------
    # Detect column types
    # --------------------------------------------------

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    # --------------------------------------------------
    # Single numeric columns
    # --------------------------------------------------

    for column in numeric_columns:
        recommendations.append(
            {
                "type": "histogram",
                "column": column,
                "score": 0.60,
                "reason": f"Distribution of {column}",
            }
        )

    # --------------------------------------------------
    # Categorical columns
    # --------------------------------------------------

    for column in categorical_columns:
        unique_count = df[column].nunique(dropna=True)

        # Avoid charts for extremely high-cardinality columns
        if 2 <= unique_count <= 20:
            score = 0.70

            # Fewer categories generally produce clearer charts
            if unique_count <= 10:
                score += 0.10

            recommendations.append(
                {
                    "type": "bar",
                    "column": column,
                    "score": score,
                    "reason": f"Category frequency for {column}",
                }
            )

    # --------------------------------------------------
    # Numeric vs numeric relationships
    # --------------------------------------------------

    if len(numeric_columns) >= 2:
        correlation_matrix = df[numeric_columns].corr()

        # Convert correlation matrix into a numeric NumPy array.
        # This avoids Pandas Scalar typing issues with Pylance.
        correlation_values = correlation_matrix.to_numpy(
            dtype=float
        )

        for i in range(len(numeric_columns)):
            for j in range(i + 1, len(numeric_columns)):

                x_column = numeric_columns[i]
                y_column = numeric_columns[j]

                correlation = correlation_values[i, j]

                # Skip relationships where correlation
                # could not be calculated.
                if pd.isna(correlation):
                    continue

                # Stronger correlation = higher recommendation score.
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
                            f"{x_column} and {y_column}"
                        ),
                    }
                )

    # --------------------------------------------------
    # Rank recommendations
    # --------------------------------------------------

    recommendations.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # --------------------------------------------------
    # Limit recommendations
    # --------------------------------------------------

    return recommendations[:max_recommendations]