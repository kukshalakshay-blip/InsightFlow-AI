import pandas as pd

from app.services.analysis_engine import (
    analyze_correlation,
    analyze_trend,
)


# ==========================================================
# RECOMMENDATION ENGINE
# ==========================================================

def generate_business_recommendations(
    df: pd.DataFrame,
    visualization_recommendations: list[dict],
) -> list[dict]:
    """
    Generate deterministic business recommendations
    from a dataset and its analytical findings.

    Each recommendation contains:
    - rule_id
    - category
    - priority
    - title
    - finding
    - action
    - rationale
    """

    recommendations = []

    # ======================================================
    # 1. DATA QUALITY: MISSING VALUES
    # ======================================================

    total_cells = df.size

    missing_cells = int(
        df.isna().sum().sum()
    )

    if total_cells > 0 and missing_cells > 0:

        missing_percentage = (
            missing_cells / total_cells
        ) * 100

        priority = (
            "high"
            if missing_percentage >= 5
            else "medium"
        )

        recommendations.append(
            {
                "rule_id": "missing_data",
                "category": "data_quality",
                "priority": priority,
                "title": "Investigate missing data",
                "finding": (
                    f"The dataset contains {missing_cells:,} "
                    f"missing cells "
                    f"({missing_percentage:.2f}% "
                    f"of all cells)."
                ),
                "action": (
                    "Identify the affected columns and determine "
                    "whether to correct, impute, or exclude "
                    "the affected values."
                ),
                "rationale": (
                    "Missing values can reduce the reliability "
                    "of statistical analysis and business decisions."
                ),
            }
        )

    # ======================================================
    # 2. DATA QUALITY: DUPLICATE ROWS
    # ======================================================

    duplicate_count = int(
        df.duplicated().sum()
    )

    if duplicate_count > 0:

        duplicate_percentage = (
            duplicate_count / len(df)
        ) * 100

        recommendations.append(
            {
                "rule_id": "duplicate_rows",
                "category": "data_quality",
                "priority": (
                    "high"
                    if duplicate_percentage >= 5
                    else "medium"
                ),
                "title": "Review duplicate records",
                "finding": (
                    f"The dataset contains {duplicate_count:,} "
                    f"duplicate rows "
                    f"({duplicate_percentage:.2f}% "
                    f"of all records)."
                ),
                "action": (
                    "Inspect duplicate rows and determine "
                    "whether they represent accidental duplication "
                    "or legitimate repeated events."
                ),
                "rationale": (
                    "Unintended duplicates can inflate aggregate "
                    "metrics and distort analytical results."
                ),
            }
        )

    # ======================================================
    # 3. PROFITABILITY: NEGATIVE PROFIT
    # ======================================================

    profit_column = next(
        (
            column
            for column in df.columns
            if column.lower() == "profit"
            and pd.api.types.is_numeric_dtype(df[column])
        ),
        None,
    )

    if profit_column is not None:

        profit_values = df[profit_column].dropna()

        if not profit_values.empty:

            negative_profit_count = int(
                (profit_values < 0).sum()
            )

            if negative_profit_count > 0:

                negative_profit_percentage = (
                    negative_profit_count
                    / len(profit_values)
                ) * 100

                recommendations.append(
                    {
                        "rule_id": "negative_profit",
                        "category": "profitability",
                        "priority": (
                            "high"
                            if negative_profit_percentage >= 10
                            else "medium"
                        ),
                        "title": "Investigate loss-making records",
                        "finding": (
                            f"{negative_profit_count:,} records have "
                            f"negative profit "
                            f"({negative_profit_percentage:.2f}% "
                            f"of valid profit records)."
                        ),
                        "action": (
                            "Investigate loss-making records by "
                            "product, customer segment, region, "
                            "and discount level where available."
                        ),
                        "rationale": (
                            "Understanding where losses occur can "
                            "help identify opportunities for further "
                            "profitability analysis."
                        ),
                    }
                )

    # ======================================================
    # 4. PROFITABILITY: NEGATIVE PROFIT MARGIN
    # ======================================================

    margin_columns = [
        column
        for column in df.columns
        if (
            "margin" in column.lower()
            and pd.api.types.is_numeric_dtype(df[column])
        )
    ]

    for column in margin_columns:

        margin_values = df[column].dropna()

        if margin_values.empty:
            continue

        negative_margin_count = int(
            (margin_values < 0).sum()
        )

        if negative_margin_count == 0:
            continue

        negative_margin_percentage = (
            negative_margin_count
            / len(margin_values)
        ) * 100

        recommendations.append(
            {
                "rule_id": f"negative_margin:{column}",
                "category": "profitability",
                "priority": (
                    "high"
                    if negative_margin_percentage >= 10
                    else "medium"
                ),
                "title": (
                    f"Investigate negative values in {column}"
                ),
                "finding": (
                    f"{negative_margin_count:,} records have "
                    f"negative values in {column} "
                    f"({negative_margin_percentage:.2f}% "
                    f"of valid records)."
                ),
                "action": (
                    "Compare negative-margin records across "
                    "relevant products, customer segments, "
                    "regions, and discount levels where available."
                ),
                "rationale": (
                    "Negative margin values identify records "
                    "that warrant further investigation into "
                    "profitability."
                ),
            }
        )

    # ======================================================
    # 5. PROFITABILITY: DISCOUNT RELATIONSHIPS
    # ======================================================

    numeric_columns = [
        column
        for column in df.columns
        if pd.api.types.is_numeric_dtype(df[column])
    ]

    discount_columns = [
        column
        for column in numeric_columns
        if "discount" in column.lower()
    ]

    # Restrict this rule to continuous profitability measures.
    # Exclude binary indicators such as is_profitable.
    profitability_columns = [
        column
        for column in numeric_columns
        if column.lower() == "profit"
        or "profit_margin" in column.lower()
    ]

    for discount_column in discount_columns:

        for metric_column in profitability_columns:

            if discount_column == metric_column:
                continue

            correlation = analyze_correlation(
                df,
                discount_column,
                metric_column,
            )

            if correlation is None:
                continue

            if correlation > -0.60:
                continue

            recommendations.append(
                {
                    "rule_id": (
                        f"discount_relationship:"
                        f"{discount_column}:{metric_column}"
                    ),
                    "category": "profitability",
                    "priority": "high",
                    "title": (
                        "Investigate discount-related "
                        "profitability patterns"
                    ),
                    "finding": (
                        f"{discount_column} and {metric_column} "
                        f"have a strong negative correlation "
                        f"({correlation:.2f})."
                    ),
                    "action": (
                        "Compare discount levels and profitability "
                        "across product categories, customer "
                        "segments, and regions before changing "
                        "discount policies."
                    ),
                    "rationale": (
                        "The association warrants investigation, "
                        "but correlation alone does not establish "
                        "causation."
                    ),
                }
            )

    # ======================================================
    # 6. SALES PERFORMANCE: DECLINING TRENDS
    # ======================================================

    for visualization in visualization_recommendations:

        if visualization.get("type") != "line":
            continue

        x_column = visualization.get("x")
        y_column = visualization.get("y")

        if not x_column or not y_column:
            continue

        metric_name = y_column.lower()

        if not any(
            keyword in metric_name
            for keyword in ("sales", "revenue")
        ):
            continue

        frequency = visualization.get(
            "frequency",
            "D",
        )

        trend_data = analyze_trend(
            df,
            x_column,
            y_column,
            frequency,
        )

        if len(trend_data) < 2:
            continue

        first_value = trend_data[y_column].iloc[0]
        last_value = trend_data[y_column].iloc[-1]

        if pd.isna(first_value) or pd.isna(last_value):
            continue

        if first_value <= 0:
            continue

        percentage_change = (
            (last_value - first_value)
            / abs(first_value)
        ) * 100

        if percentage_change > -20:
            continue

        recommendations.append(
            {
                "rule_id": (
                    f"declining_sales:{x_column}:{y_column}"
                ),
                "category": "sales_performance",
                "priority": "high",
                "title": "Investigate declining sales",
                "finding": (
                    f"Average {y_column} declined by "
                    f"{abs(percentage_change):.1f}% between "
                    f"the first and last observed time periods."
                ),
                "action": (
                    "Examine sales across time periods, customer "
                    "segments, product categories, and regions "
                    "to determine where the decline is concentrated."
                ),
                "rationale": (
                    "A substantial decline in the observed trend "
                    "warrants investigation, but the trend alone "
                    "does not explain its cause."
                ),
            }
        )

    # ======================================================
    # 7. DEDUPLICATE RECOMMENDATIONS
    # ======================================================

    unique_recommendations = []
    seen_rule_ids = set()

    for recommendation in recommendations:

        rule_id = recommendation["rule_id"]

        if rule_id in seen_rule_ids:
            continue

        seen_rule_ids.add(rule_id)

        unique_recommendations.append(
            recommendation
        )

    # ======================================================
    # 8. PRIORITIZE RECOMMENDATIONS
    # ======================================================

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    unique_recommendations.sort(
        key=lambda item: priority_order.get(
            item["priority"],
            3,
        )
    )

    return unique_recommendations