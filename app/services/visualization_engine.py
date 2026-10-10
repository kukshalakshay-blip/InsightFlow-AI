import pandas as pd

from app.services.column_intelligence import analyze_columns


# =========================================================
# 1. Choosing the Best Business Measure
# =========================================================

def choose_best_measure(
    df: pd.DataFrame,
    measure_columns: list[str],
) -> str | None:
    """
    Select the most relevant numeric measure for business charts.

    Priority:
    1. Sales
    2. Revenue
    3. Profit
    4. Amount
    5. Value
    6. Quantity

    If no priority keyword matches, return the first available
    measure. Return None when no measures exist.
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


# =========================================================
# 2. Scatter Plot Suitability
# =========================================================

def is_suitable_for_scatter(
    semantic_type: str,
) -> bool:
    """
    Determine whether a column is suitable for a scatter plot.

    Scatter plots are suitable for numeric measures and counts.
    """

    return semantic_type in {
        "numeric_measure",
        "count",
    }


# =========================================================
# 3. Selecting Diverse Visualization Recommendations
# =========================================================

def select_diverse_recommendations(
    recommendations: list[dict],
    max_recommendations: int,
) -> list[dict]:
    """
    Select diverse visualizations while respecting:
    - The maximum number of recommendations.
    - The maximum number of charts of each type.
    """

    # Fix: return immediately for zero or negative limits.
    if max_recommendations <= 0:
        return []

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

        # Skip a chart type that has reached its limit.
        if current_count >= limit:
            continue

        selected.append(recommendation)

        type_counts[chart_type] = current_count + 1

        # Stop when the requested maximum is reached.
        if len(selected) >= max_recommendations:
            break

    return selected


# =========================================================
# 4. Choosing Time-Series Frequency
# =========================================================

def choose_time_frequency(
    df: pd.DataFrame,
    date_column: str,
) -> str:
    """
    Choose an appropriate frequency for time-series charts.

    Rules:
    - Up to 90 unique dates: Daily.
    - 91 to 365 unique dates: Weekly.
    - More than 365 unique dates: Month-end.

    Returns pandas frequency aliases:
    D  = Daily
    W  = Weekly
    ME = Month-end
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


# =========================================================
# 5. Recommending Visualizations
# =========================================================

def recommend_visualizations(
    df: pd.DataFrame,
    max_recommendations: int = 10,
) -> list[dict]:
    """
    Recommend appropriate visualizations for a dataset.

    Supported recommendations:
    - Histograms for numeric columns.
    - Bar charts for categorical columns.
    - Scatter plots for numeric relationships.
    - Line charts for date-based trends.
    - Maps when latitude and longitude columns are detected.

    Recommendations are scored, sorted, and diversified.
    """

    # Fix: enforce the limit at the public function level too.
    if max_recommendations <= 0:
        return []

    recommendations = []

    # Analyze the semantic meaning of dataset columns.
    column_information = analyze_columns(df)

    # -----------------------------------------------------
    # Identify columns by semantic type
    # -----------------------------------------------------

    numeric_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] in {
            "numeric_measure",
            "count",
        }
    ]

    measure_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] == "numeric_measure"
    ]

    categorical_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] == "categorical"
    ]

    datetime_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] == "datetime"
    ]

    latitude_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] == "geographic_latitude"
    ]

    longitude_columns = [
        item["column"]
        for item in column_information
        if item["semantic_type"] == "geographic_longitude"
    ]

    # Select the primary business measure.
    best_measure = choose_best_measure(
        df,
        measure_columns,
    )

    # -----------------------------------------------------
    # A. Histogram Recommendations
    # -----------------------------------------------------

    for column in numeric_columns:
        recommendations.append({
            "type": "histogram",
            "column": column,
            "score": 0.60,
            "reason": (
                f"Explore the distribution of '{column}' "
                "to understand its spread and frequency."
            ),
        })

    # -----------------------------------------------------
    # B. Bar Chart Recommendations
    # -----------------------------------------------------

    if best_measure is not None:

        for column in categorical_columns:
            unique_count = df[column].nunique(
                dropna=True,
            )

            # Avoid categories with too many distinct values.
            if 2 <= unique_count <= 20:

                score = 0.70

                # Prefer simpler categories for readability.
                if unique_count <= 10:
                    score += 0.10

                recommendations.append({
                    "type": "bar",
                    "column": column,
                    "x": column,
                    "y": best_measure,
                    "score": score,
                    "reason": (
                        f"Compare '{best_measure}' across "
                        f"the categories of '{column}'."
                    ),
                })

    # -----------------------------------------------------
    # C. Scatter Plot Recommendations
    # -----------------------------------------------------

    scatter_columns = [
        item["column"]
        for item in column_information
        if is_suitable_for_scatter(
            item["semantic_type"],
        )
    ]

    if len(scatter_columns) >= 2:

        correlation_matrix = df[
            scatter_columns
        ].corr(numeric_only=True)

        for i, column_x in enumerate(scatter_columns):

            for column_y in scatter_columns[i + 1:]:

                # Skip pairs that are absent from the
                # computed correlation matrix.
                if (
                    column_x not in correlation_matrix.columns
                    or column_y not in correlation_matrix.columns
                ):
                    continue

                correlation = correlation_matrix.at[
                    column_x,
                    column_y,
                ]

                # Correlation may be undefined.
                if pd.isna(correlation):
                    continue

                if not isinstance(correlation, (int, float)):
                    continue

                correlation_value = float(correlation)
                score = (
                    0.50
                    + abs(correlation_value) * 0.50
                )

                recommendations.append({
                    "type": "scatter",
                    "x": column_x,
                    "y": column_y,
                    "score": score,
                    "reason": (
                        f"Explore the relationship between "
                        f"'{column_x}' and '{column_y}'. "
                        f"Correlation: {correlation_value:.2f}."
                    ),
                })

    # -----------------------------------------------------
    # D. Time-Series Line Chart Recommendations
    # -----------------------------------------------------

    for date_column in datetime_columns:

        frequency = choose_time_frequency(
            df,
            date_column,
        )

        for measure_column in measure_columns:

            recommendations.append({
                "type": "line",
                "x": date_column,
                "y": measure_column,
                "frequency": frequency,
                "score": 0.85,
                "reason": (
                    f"Track '{measure_column}' over time "
                    f"using '{date_column}'."
                ),
            })

    # -----------------------------------------------------
    # E. Geographic Map Recommendations
    # -----------------------------------------------------

    if latitude_columns and longitude_columns:

        recommendations.append({
            "type": "map",
            "latitude": latitude_columns[0],
            "longitude": longitude_columns[0],
            "score": 0.90,
            "reason": (
                "Explore the geographic distribution "
                "of the available coordinates."
            ),
        })

    # -----------------------------------------------------
    # F. Sort Recommendations by Score
    # -----------------------------------------------------

    recommendations.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # -----------------------------------------------------
    # G. Return Diverse Recommendations
    # -----------------------------------------------------

    return select_diverse_recommendations(
        recommendations,
        max_recommendations=max_recommendations,
    )