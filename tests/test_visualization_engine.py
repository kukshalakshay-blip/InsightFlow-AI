import pandas as pd
import pytest

from app.services.visualization_engine import (
    choose_best_measure,
    choose_time_frequency,
    is_suitable_for_scatter,
    recommend_visualizations,
    select_diverse_recommendations,
)


# =========================================================
# 1. Choosing a business measure
# =========================================================

def test_choose_sales_as_best_measure():
    df = pd.DataFrame({
        "quantity": [1, 2, 3],
        "profit": [10, 20, 30],
        "sales": [100, 200, 300],
    })

    result = choose_best_measure(
        df,
        ["quantity", "profit", "sales"],
    )

    assert result == "sales"


def test_choose_revenue_when_sales_is_unavailable():
    df = pd.DataFrame({
        "revenue": [100, 200, 300],
        "quantity": [1, 2, 3],
    })

    result = choose_best_measure(
        df,
        ["revenue", "quantity"],
    )

    assert result == "revenue"


def test_choose_first_measure_when_no_keyword_matches():
    df = pd.DataFrame({
        "temperature": [20, 25, 30],
        "height": [150, 160, 170],
    })

    result = choose_best_measure(
        df,
        ["temperature", "height"],
    )

    assert result == "temperature"


def test_choose_best_measure_returns_none_when_no_measures_exist():
    result = choose_best_measure(
        pd.DataFrame(),
        [],
    )

    assert result is None


# =========================================================
# 2. Scatter plot suitability
# =========================================================

@pytest.mark.parametrize(
    "semantic_type",
    ["numeric_measure", "count"],
)
def test_numeric_semantic_types_are_suitable_for_scatter(
    semantic_type,
):
    assert is_suitable_for_scatter(semantic_type) is True


@pytest.mark.parametrize(
    "semantic_type",
    [
        "categorical",
        "identifier",
        "datetime",
        "constant",
        "binary_category",
    ],
)
def test_non_measure_semantic_types_are_not_suitable_for_scatter(
    semantic_type,
):
    assert is_suitable_for_scatter(semantic_type) is False


# =========================================================
# 3. Choosing time frequency
# =========================================================

def test_daily_frequency_for_up_to_90_unique_dates():
    dates = pd.date_range(
        "2025-01-01",
        periods=30,
        freq="D",
    )

    df = pd.DataFrame({"date": dates})

    assert choose_time_frequency(df, "date") == "D"


def test_daily_frequency_at_90_unique_dates():
    dates = pd.date_range(
        "2025-01-01",
        periods=90,
        freq="D",
    )

    df = pd.DataFrame({"date": dates})

    assert choose_time_frequency(df, "date") == "D"


def test_weekly_frequency_above_90_unique_dates():
    dates = pd.date_range(
        "2024-01-01",
        periods=100,
        freq="D",
    )

    df = pd.DataFrame({"date": dates})

    assert choose_time_frequency(df, "date") == "W"


def test_month_end_frequency_above_365_unique_dates():
    dates = pd.date_range(
        "2020-01-01",
        periods=400,
        freq="D",
    )

    df = pd.DataFrame({"date": dates})

    assert choose_time_frequency(df, "date") == "ME"


def test_time_frequency_ignores_invalid_dates():
    df = pd.DataFrame({
        "date": [
            "2025-01-01",
            "2025-01-02",
            "not-a-date",
        ]
    })

    assert choose_time_frequency(df, "date") == "D"


# =========================================================
# 4. Selecting diverse recommendations
# =========================================================

def test_select_diverse_recommendations_respects_maximum():
    recommendations = [
        {"type": "bar", "score": 0.9},
        {"type": "line", "score": 0.8},
        {"type": "scatter", "score": 0.7},
    ]

    result = select_diverse_recommendations(
        recommendations,
        max_recommendations=2,
    )

    assert len(result) == 2


def test_select_diverse_recommendations_respects_chart_type_limits():
    recommendations = [
        {"type": "scatter", "score": 0.99},
        {"type": "scatter", "score": 0.98},
        {"type": "scatter", "score": 0.97},
        {"type": "scatter", "score": 0.96},
        {"type": "scatter", "score": 0.95},
    ]

    result = select_diverse_recommendations(
        recommendations,
        max_recommendations=10,
    )

    assert len(result) == 3


def test_select_diverse_recommendations_returns_empty_for_empty_input():
    assert select_diverse_recommendations([], 10) == []


def test_select_diverse_recommendations_with_zero_limit():
    result = select_diverse_recommendations(
        [{"type": "bar", "score": 0.9}],
        max_recommendations=0,
    )

    assert result == []


# =========================================================
# 5. Numeric and categorical visualizations
# =========================================================

def test_numeric_dataset_recommends_histograms():
    df = pd.DataFrame({
        "sales": [100, 200, 300, 400],
        "profit": [10, 20, 30, 40],
    })

    recommendations = recommend_visualizations(df)

    assert any(
        item["type"] == "histogram"
        for item in recommendations
    )


def test_categorical_dataset_recommends_bar_chart():
    df = pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "sales": [100, 200, 300, 400],
    })

    recommendations = recommend_visualizations(df)

    assert any(
        item["type"] == "bar"
        and item.get("column") == "region"
        for item in recommendations
    )


def test_numeric_relationship_recommends_scatter_plot():
    df = pd.DataFrame({
        "sales": [100, 200, 300, 400, 500],
        "profit": [10, 25, 30, 50, 70],
    })

    recommendations = recommend_visualizations(df)

    assert any(
        item["type"] == "scatter"
        for item in recommendations
    )


def test_date_and_measure_recommend_line_chart():
    df = pd.DataFrame({
        "order_date": pd.date_range(
            "2025-01-01",
            periods=10,
            freq="D",
        ),
        "sales": range(100, 110),
    })

    recommendations = recommend_visualizations(df)

    assert any(
        item["type"] == "line"
        and item.get("x") == "order_date"
        and item.get("y") == "sales"
        for item in recommendations
    )


# =========================================================
# 6. Empty and unusual datasets
# =========================================================

def test_empty_dataframe_returns_no_recommendations():
    df = pd.DataFrame()

    recommendations = recommend_visualizations(df)

    assert recommendations == []


def test_constant_numeric_columns_do_not_create_scatter_plots():
    df = pd.DataFrame({
        "sales": [100, 100, 100, 100],
        "profit": [10, 20, 30, 40],
    })

    recommendations = recommend_visualizations(df)

    assert not any(
        item["type"] == "scatter"
        and "sales" in [item.get("x"), item.get("y")]
        for item in recommendations
    )


def test_maximum_recommendations_is_respected():
    df = pd.DataFrame({
        "sales": [100, 200, 300, 400],
        "profit": [10, 20, 30, 40],
        "quantity": [1, 2, 3, 4],
        "discount": [0.1, 0.2, 0.3, 0.4],
    })

    recommendations = recommend_visualizations(
        df,
        max_recommendations=3,
    )

    assert len(recommendations) <= 3


def test_recommendations_are_sorted_by_score():
    df = pd.DataFrame({
        "sales": [100, 200, 300, 400],
        "profit": [10, 20, 30, 40],
        "region": ["North", "South", "East", "West"],
    })

    recommendations = recommend_visualizations(df)

    scores = [
        item["score"]
        for item in recommendations
    ]

    assert scores == sorted(scores, reverse=True)