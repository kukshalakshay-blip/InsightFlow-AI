import pandas as pd
import pytest

from app.services.recommendation_engine import (
    generate_business_recommendations,
)


# =========================================================
# Helpers
# =========================================================

def get_recommendations(
    df,
    visualizations=None,
):
    """Generate recommendations with optional visualizations."""

    if visualizations is None:
        visualizations = []

    return generate_business_recommendations(
        df,
        visualizations,
    )


def get_recommendations_by_rule(
    recommendations,
    rule_id,
):
    """Return recommendations matching a particular rule ID."""

    return [
        recommendation
        for recommendation in recommendations
        if recommendation["rule_id"] == rule_id
    ]


# =========================================================
# 1. Basic Behavior
# =========================================================

def test_clean_dataset_returns_no_recommendations():
    df = pd.DataFrame({
        "sales": [100, 200, 300, 400],
        "profit": [20, 40, 60, 80],
        "region": ["North", "South", "East", "West"],
    })

    recommendations = get_recommendations(df)

    assert recommendations == []


def test_empty_dataframe_returns_no_recommendations():
    df = pd.DataFrame()

    recommendations = get_recommendations(df)

    assert recommendations == []


def test_recommendations_have_required_fields():
    df = pd.DataFrame({
        "sales": [100, None, 300],
        "profit": [20, 30, 40],
    })

    recommendations = get_recommendations(df)

    assert recommendations

    required_fields = {
        "rule_id",
        "category",
        "priority",
        "title",
        "finding",
        "action",
        "rationale",
    }

    for recommendation in recommendations:
        assert required_fields.issubset(
            recommendation.keys()
        )


# =========================================================
# 2. Missing Data
# =========================================================

def test_missing_data_generates_recommendation():
    df = pd.DataFrame({
        "sales": [100, None, 300, 400],
        "profit": [10, 20, None, 40],
    })

    recommendations = get_recommendations(df)

    matches = get_recommendations_by_rule(
        recommendations,
        "missing_data",
    )

    assert len(matches) == 1


def test_missing_data_finding_reports_correct_count():
    df = pd.DataFrame({
        "sales": [100, None, 300, 400],
        "profit": [10, 20, None, 40],
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "missing_data",
    )[0]

    assert "2 missing cells" in recommendation["finding"]
    assert "25.00%" in recommendation["finding"]


def test_missing_data_has_medium_priority_below_five_percent():
    df = pd.DataFrame({
        "sales": [100] * 100 + [None],
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "missing_data",
    )[0]

    assert recommendation["priority"] == "medium"


def test_missing_data_has_high_priority_at_five_percent():
    df = pd.DataFrame({
        "sales": [100] * 19 + [None],
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "missing_data",
    )[0]

    assert recommendation["priority"] == "high"


def test_complete_dataset_has_no_missing_data_recommendation():
    df = pd.DataFrame({
        "sales": [100, 200, 300],
        "profit": [10, 20, 30],
    })

    recommendations = get_recommendations(df)

    assert not get_recommendations_by_rule(
        recommendations,
        "missing_data",
    )


# =========================================================
# 3. Duplicate Rows
# =========================================================

def test_duplicate_rows_generate_recommendation():
    df = pd.DataFrame({
        "order_id": [1, 2, 2, 3],
        "sales": [100, 200, 200, 300],
    })

    recommendations = get_recommendations(df)

    matches = get_recommendations_by_rule(
        recommendations,
        "duplicate_rows",
    )

    assert len(matches) == 1


def test_duplicate_rows_finding_reports_correct_count():
    df = pd.DataFrame({
        "order_id": [1, 2, 2, 3],
        "sales": [100, 200, 200, 300],
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "duplicate_rows",
    )[0]

    assert "1 duplicate rows" in recommendation["finding"]
    assert "25.00%" in recommendation["finding"]


def test_duplicate_rows_have_medium_priority_below_five_percent():
    df = pd.DataFrame({
        "value": list(range(100)) + [0],
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "duplicate_rows",
    )[0]

    assert recommendation["priority"] == "medium"


def test_duplicate_rows_have_high_priority_at_five_percent():
    df = pd.DataFrame({
        "value": list(range(19)) + [0],
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "duplicate_rows",
    )[0]

    assert recommendation["priority"] == "high"


def test_dataset_without_duplicates_has_no_duplicate_recommendation():
    df = pd.DataFrame({
        "order_id": [1, 2, 3],
        "sales": [100, 200, 300],
    })

    recommendations = get_recommendations(df)

    assert not get_recommendations_by_rule(
        recommendations,
        "duplicate_rows",
    )


# =========================================================
# 4. Negative Profit
# =========================================================

def test_negative_profit_generates_recommendation():
    df = pd.DataFrame({
        "profit": [10, -5, 20, -10, 30],
    })

    recommendations = get_recommendations(df)

    matches = get_recommendations_by_rule(
        recommendations,
        "negative_profit",
    )

    assert len(matches) == 1


def test_negative_profit_finding_reports_correct_count():
    df = pd.DataFrame({
        "profit": [10, -5, 20, -10, 30],
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "negative_profit",
    )[0]

    assert "2 records have negative profit" in recommendation["finding"]
    assert "40.00%" in recommendation["finding"]


def test_negative_profit_has_high_priority_at_ten_percent():
    df = pd.DataFrame({
        "profit": [-10] + [100] * 9,
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "negative_profit",
    )[0]

    assert recommendation["priority"] == "high"


def test_negative_profit_has_medium_priority_below_ten_percent():
    df = pd.DataFrame({
        "profit": [-10] + [100] * 19,
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "negative_profit",
    )[0]

    assert recommendation["priority"] == "medium"


def test_profit_column_with_no_losses_generates_no_recommendation():
    df = pd.DataFrame({
        "profit": [10, 20, 30],
    })

    recommendations = get_recommendations(df)

    assert not get_recommendations_by_rule(
        recommendations,
        "negative_profit",
    )


def test_profit_column_with_only_missing_values_is_ignored():
    df = pd.DataFrame({
        "profit": [None, None, None],
    })

    recommendations = get_recommendations(df)

    assert not get_recommendations_by_rule(
        recommendations,
        "negative_profit",
    )


def test_non_numeric_profit_column_is_ignored():
    df = pd.DataFrame({
        "profit": ["loss", "profit", "loss"],
    })

    recommendations = get_recommendations(df)

    assert not get_recommendations_by_rule(
        recommendations,
        "negative_profit",
    )


# =========================================================
# 5. Negative Profit Margins
# =========================================================

def test_negative_profit_margin_generates_recommendation():
    df = pd.DataFrame({
        "profit_margin": [0.2, -0.1, 0.3, -0.2],
    })

    recommendations = get_recommendations(df)

    matches = get_recommendations_by_rule(
        recommendations,
        "negative_margin:profit_margin",
    )

    assert len(matches) == 1


def test_multiple_margin_columns_are_checked():
    df = pd.DataFrame({
        "profit_margin": [0.2, -0.1, 0.3],
        "gross_margin": [0.3, -0.2, 0.4],
    })

    recommendations = get_recommendations(df)

    margin_recommendations = [
        recommendation
        for recommendation in recommendations
        if recommendation["rule_id"].startswith(
            "negative_margin:"
        )
    ]

    assert len(margin_recommendations) == 2


def test_margin_without_negative_values_generates_no_recommendation():
    df = pd.DataFrame({
        "profit_margin": [0.1, 0.2, 0.3],
    })

    recommendations = get_recommendations(df)

    assert not any(
        recommendation["rule_id"].startswith(
            "negative_margin:"
        )
        for recommendation in recommendations
    )


def test_non_numeric_margin_column_is_ignored():
    df = pd.DataFrame({
        "profit_margin": ["positive", "negative"],
    })

    recommendations = get_recommendations(df)

    assert not any(
        recommendation["rule_id"].startswith(
            "negative_margin:"
        )
        for recommendation in recommendations
    )


# =========================================================
# 6. Discount and Profitability Relationships
# =========================================================

def test_strong_negative_discount_profit_correlation_generates_recommendation():
    df = pd.DataFrame({
        "discount": [1, 2, 3, 4, 5],
        "profit": [50, 40, 30, 20, 10],
    })

    recommendations = get_recommendations(df)

    matches = [
        recommendation
        for recommendation in recommendations
        if recommendation["rule_id"]
        == "discount_relationship:discount:profit"
    ]

    assert len(matches) == 1


def test_weak_discount_profit_correlation_generates_no_recommendation():
    df = pd.DataFrame({
        "discount": [1, 2, 3, 4, 5],
        "profit": [10, 40, 20, 50, 30],
    })

    recommendations = get_recommendations(df)

    assert not any(
        recommendation["rule_id"].startswith(
            "discount_relationship:"
        )
        for recommendation in recommendations
    )


def test_discount_relationship_does_not_claim_causation():
    df = pd.DataFrame({
        "discount": [1, 2, 3, 4, 5],
        "profit": [50, 40, 30, 20, 10],
    })

    recommendations = get_recommendations(df)

    recommendation = get_recommendations_by_rule(
        recommendations,
        "discount_relationship:discount:profit",
    )[0]

    assert "does not establish causation" in (
        recommendation["rationale"]
    )


def test_discount_relationship_handles_constant_profit_values():
    df = pd.DataFrame({
        "discount": [1, 2, 3, 4],
        "profit": [20, 20, 20, 20],
    })

    recommendations = get_recommendations(df)

    assert not any(
        recommendation["rule_id"].startswith(
            "discount_relationship:"
        )
        for recommendation in recommendations
    )


# =========================================================
# 7. Declining Sales Trends
# =========================================================

def test_declining_sales_generates_recommendation():
    dates = pd.date_range(
        "2025-01-01",
        periods=10,
        freq="D",
    )

    df = pd.DataFrame({
        "order_date": dates,
        "sales": [100] * 9 + [70],
    })

    visualizations = [{
        "type": "line",
        "x": "order_date",
        "y": "sales",
        "frequency": "D",
    }]

    recommendations = get_recommendations(
        df,
        visualizations,
    )

    matches = get_recommendations_by_rule(
        recommendations,
        "declining_sales:order_date:sales",
    )

    assert len(matches) == 1


def test_declining_sales_finding_reports_percentage():
    dates = pd.date_range(
        "2025-01-01",
        periods=5,
        freq="D",
    )

    df = pd.DataFrame({
        "order_date": dates,
        "sales": [100, 100, 100, 100, 70],
    })

    visualizations = [{
        "type": "line",
        "x": "order_date",
        "y": "sales",
        "frequency": "D",
    }]

    recommendations = get_recommendations(
        df,
        visualizations,
    )

    recommendation = get_recommendations_by_rule(
        recommendations,
        "declining_sales:order_date:sales",
    )[0]

    assert "30.0%" in recommendation["finding"]


def test_small_sales_decline_generates_no_recommendation():
    dates = pd.date_range(
        "2025-01-01",
        periods=5,
        freq="D",
    )

    df = pd.DataFrame({
        "order_date": dates,
        "sales": [100, 100, 100, 100, 90],
    })

    visualizations = [{
        "type": "line",
        "x": "order_date",
        "y": "sales",
        "frequency": "D",
    }]

    recommendations = get_recommendations(
        df,
        visualizations,
    )

    assert not get_recommendations_by_rule(
        recommendations,
        "declining_sales:order_date:sales",
    )


def test_line_chart_for_unrelated_metric_is_ignored():
    dates = pd.date_range(
        "2025-01-01",
        periods=5,
        freq="D",
    )

    df = pd.DataFrame({
        "order_date": dates,
        "temperature": [100, 90, 80, 70, 60],
    })

    visualizations = [{
        "type": "line",
        "x": "order_date",
        "y": "temperature",
        "frequency": "D",
    }]

    recommendations = get_recommendations(
        df,
        visualizations,
    )

    assert not any(
        recommendation["rule_id"].startswith(
            "declining_sales:"
        )
        for recommendation in recommendations
    )


def test_non_line_visualization_does_not_trigger_sales_trend_rule():
    dates = pd.date_range(
        "2025-01-01",
        periods=5,
        freq="D",
    )

    df = pd.DataFrame({
        "order_date": dates,
        "sales": [100, 90, 80, 70, 60],
    })

    visualizations = [{
        "type": "bar",
        "x": "order_date",
        "y": "sales",
    }]

    recommendations = get_recommendations(
        df,
        visualizations,
    )

    assert not get_recommendations_by_rule(
        recommendations,
        "declining_sales:order_date:sales",
    )


# =========================================================
# 8. Deduplication and Priority Ordering
# =========================================================

def test_recommendations_are_sorted_by_priority():
    df = pd.DataFrame({
        "sales": [100, None, 300, 400],
        "profit": [-10, 20, 30, 40],
    })

    recommendations = get_recommendations(df)

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    priorities = [
        priority_order[item["priority"]]
        for item in recommendations
    ]

    assert priorities == sorted(priorities)


def test_recommendation_rule_ids_are_unique():
    df = pd.DataFrame({
        "sales": [100, None, 300, 400],
        "profit": [-10, -20, 30, 40],
        "profit_margin": [-0.1, -0.2, 0.3, 0.4],
        "discount": [1, 2, 3, 4],
    })

    recommendations = get_recommendations(df)

    rule_ids = [
        recommendation["rule_id"]
        for recommendation in recommendations
    ]

    assert len(rule_ids) == len(set(rule_ids))


def test_high_priority_recommendations_appear_before_medium():
    df = pd.DataFrame({
        "sales": [None] + [100] * 19,
        "profit": [-10] + [100] * 19,
    })

    recommendations = get_recommendations(df)

    priorities = [
        recommendation["priority"]
        for recommendation in recommendations
    ]

    if "high" in priorities and "medium" in priorities:
        first_medium = priorities.index("medium")

        assert all(
            priority == "high"
            for priority in priorities[:first_medium]
        )


# =========================================================
# 9. Input Edge Cases
# =========================================================

def test_dataset_with_zero_rows_and_columns_returns_empty_list():
    df = pd.DataFrame()

    assert get_recommendations(df) == []


def test_dataset_with_rows_but_no_numeric_columns():
    df = pd.DataFrame({
        "region": ["North", "South", "East"],
        "status": ["Open", "Closed", "Open"],
    })

    recommendations = get_recommendations(df)

    assert isinstance(recommendations, list)


def test_missing_values_and_negative_profit_are_both_reported():
    df = pd.DataFrame({
        "sales": [100, None, 300, 400],
        "profit": [-10, 20, -30, 40],
    })

    recommendations = get_recommendations(df)

    rule_ids = {
        recommendation["rule_id"]
        for recommendation in recommendations
    }

    assert "missing_data" in rule_ids
    assert "negative_profit" in rule_ids