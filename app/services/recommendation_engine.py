import pandas as pd

from app.services.analysis_engine import (
    analyze_correlation,
    analyze_trend,
    detect_outliers,
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
            if (
                column.lower() == "profit"
                and pd.api.types.is_numeric_dtype(df[column])
                and not pd.api.types.is_bool_dtype(df[column])
            )
        ),
        None,
    )

    consolidated_margin_columns = set()

    if profit_column is not None:

        profit_values = df[profit_column].dropna()
        negative_profit_count = int(
            (profit_values < 0).sum()
        )

        if negative_profit_count > 0:
            negative_profit_percentage = (
                negative_profit_count / len(profit_values)
            ) * 100

            # Identify margin columns with exactly the same
            # negative-value records as the profit column.
            matching_margin_columns = []

            profit_negative_mask = (
                df[profit_column]
                .lt(0)
                .fillna(False)
                .to_numpy(dtype=bool)
            )

            for column in df.columns:
                if (
                    "margin" not in column.lower()
                    or not pd.api.types.is_numeric_dtype(df[column])
                    or pd.api.types.is_bool_dtype(df[column])
                ):
                    continue

                margin_negative_mask = (
                    df[column]
                    .lt(0)
                    .fillna(False)
                    .to_numpy(dtype=bool)
                )

                if (
                    margin_negative_mask.shape == profit_negative_mask.shape
                    and (margin_negative_mask == profit_negative_mask).all()
                ):
                    matching_margin_columns.append(column)

            consolidated_margin_columns.update(
                matching_margin_columns
            )

            # Build one finding when both metrics flag
            # exactly the same records.
            if matching_margin_columns:
                margin_details = []

                for column in matching_margin_columns:
                    margin_values = df[column].dropna()

                    margin_count = int(
                        (margin_values < 0).sum()
                    )

                    margin_percentage = (
                        margin_count / len(margin_values)
                    ) * 100

                    margin_details.append(
                        f"{column}: {margin_count:,} negative records "
                        f"({margin_percentage:.2f}% of valid records)"
                    )

                title = (
                    "Investigate overlapping profitability losses"
                )

                finding = (
                    f"{negative_profit_count:,} records have negative "
                    f"profit ({negative_profit_percentage:.2f}% "
                    f"of valid profit records). The same records also "
                    f"have negative values in: "
                    f"{'; '.join(margin_details)}."
                )

            else:
                title = "Investigate loss-making records"

                finding = (
                    f"{negative_profit_count:,} records have "
                    f"negative profit "
                    f"({negative_profit_percentage:.2f}% "
                    f"of valid profit records)."
                )

            recommendations.append(
                {
                    "rule_id": "negative_profit",
                    "category": "profitability",
                    "priority": (
                        "high"
                        if negative_profit_percentage >= 10
                        else "medium"
                    ),
                    "title": title,
                    "finding": finding,
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
            and not pd.api.types.is_bool_dtype(df[column])
        )
    ]

    for column in margin_columns:

        if column in consolidated_margin_columns:
            continue

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
        if (
            pd.api.types.is_numeric_dtype(df[column])
            and not pd.api.types.is_bool_dtype(df[column])
        )
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
        if (
            column.lower() == "profit"
            or "profit_margin" in column.lower()
        )
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

        if x_column not in df.columns or y_column not in df.columns:
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
    # 7. DATA QUALITY: NUMERICAL OUTLIERS
    # ======================================================

    excluded_columns = {
        "id",
        "row_id",
        "postal_code",
        "zip_code",
        "order_year",
        "order_month",
        "order_quarter",
    }

    identifier_keywords = (
        "identifier",
        "customer_id",
        "product_id",
        "order_id",
        "account_number",
        "transaction_number",
        "phone",
    )

    outlier_findings = []

    for column in df.columns:

        column_name = str(column).lower().strip()

        if column_name in excluded_columns:
            continue

        if (
            column_name.endswith("_id")
            or column_name.startswith("id_")
            or any(
                keyword in column_name
                for keyword in identifier_keywords
            )
        ):
            continue

        if (
            not pd.api.types.is_numeric_dtype(df[column])
            or pd.api.types.is_bool_dtype(df[column])
        ):
            continue

        valid_values = df[column].dropna()

        if len(valid_values) < 10 or valid_values.nunique() < 2:
            continue

        result = detect_outliers(df, column)

        outlier_count = int(result["outlier_count"])
        outlier_percentage = float(result["outlier_percentage"])

        lower_bound = result["lower_bound"]
        upper_bound = result["upper_bound"]

        if outlier_count == 0 or outlier_percentage >= 25:
            continue

        low_count = int((valid_values < lower_bound).sum())
        high_count = int((valid_values > upper_bound).sum())

        outlier_findings.append({
            "column": column,
            "count": outlier_count,
            "percentage": outlier_percentage,
            "low_count": low_count,
            "high_count": high_count,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
        })

    # Rank by the proportion of valid records flagged.
    # This is a screening priority, not a measure of business loss.
    outlier_findings.sort(
        key=lambda item: (
            item["percentage"],
            item["count"],
        ),
        reverse=True,
    )

    # Keep individual recommendations for the strongest signals.
    # Summarize remaining columns to reduce repetitive output.
    individual_limit = 3

    for item in outlier_findings[:individual_limit]:

        column = item["column"]

        priority = (
            "medium"
            if item["percentage"] >= 5
            else "low"
        )

        recommendations.append({
            "rule_id": f"numerical_outliers:{column}",
            "category": "data_quality",
            "priority": priority,
            "title": f"Review statistically unusual values in {column}",
            "finding": (
                f"IQR outlier detection identified "
                f"{item['count']:,} outlier(s) in '{column}' "
                f"({item['percentage']:.2f}% of valid records): "
                f"{item['low_count']:,} below the lower bound "
                f"({item['lower_bound']:.4g}) and "
                f"{item['high_count']:,} above the upper bound "
                f"({item['upper_bound']:.4g})."
            ),
            "action": (
                f"Inspect the flagged records in '{column}' and "
                "compare them with relevant business context. "
                "Determine whether they are legitimate extremes, "
                "data-quality issues, or a distinct subgroup."
            ),
                    "rationale": (
            "IQR detection identifies statistical extremes, "
            "not necessarily errors or business-rule violations. "
            "Some observations may overlap with other business "
            "findings, so review related recommendations together."
        ),
        })

    remaining_findings = outlier_findings[individual_limit:]

    if remaining_findings:

        summary_details = "; ".join(
            (
                f"{item['column']}: {item['count']:,} records "
                f"({item['percentage']:.2f}%)"
            )
            for item in remaining_findings
        )

        recommendations.append({
            "rule_id": "numerical_outliers:summary",
            "category": "data_quality",
            "priority": "low",
            "title": "Review unusual values across additional measures",
            "finding": (
                f"IQR screening identified unusual values in "
                f"{len(remaining_findings)} additional columns: "
                f"{summary_details}."
            ),
            "action": (
                "Review these columns together and investigate "
                "the observations with the greatest relevance "
                "to the analysis."
            ),
            "rationale": (
                "Grouping additional outlier findings reduces "
                "repetition while preserving the evidence needed "
                "to decide which observations merit investigation."
            ),
        })
    # ======================================================
    # 8. DEDUPLICATE RECOMMENDATIONS
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
    # 9. PRIORITIZE RECOMMENDATIONS
    # ======================================================

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    # Secondary ordering reflects the type of finding,
    # not a claim that unlike statistical measures are comparable.
    rule_order = {
        "missing_data": 0,
        "duplicate_rows": 1,
        "negative_profit": 2,
        "negative_margin": 3,
        "discount_relationship": 4,
        "declining_sales": 5,
        "numerical_outliers": 6,
    }

    def recommendation_sort_key(item):
        rule_id = item.get("rule_id", "")
        rule_family = rule_id.split(":")[0]

        return (
            priority_order.get(item.get("priority"), 3),
            rule_order.get(rule_family, 99),
            rule_id,
        )

    unique_recommendations.sort(
        key=recommendation_sort_key
    )

    return unique_recommendations