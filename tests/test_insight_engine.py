import numpy as np
import pandas as pd
import pytest

from app.services.insight_engine import (
    build_analysis_context,
    generate_insight,
)


# ==========================================================
# TEST DATA
# ==========================================================

@pytest.fixture
def sales_dataframe():
    """A small, realistic business dataset."""
    return pd.DataFrame({
        "date": pd.to_datetime([
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
            "2026-01-04",
            "2026-01-05",
        ]),
        "region": [
            "North",
            "South",
            "North",
            "East",
            "North",
        ],
        "sales": [100, 200, 300, 400, 500],
        "profit": [10, 20, 30, 40, 50],
        "discount": [1, 2, 3, 4, 5],
    })


# ==========================================================
# SCATTER PLOT INSIGHTS
# ==========================================================

def test_scatter_insight_detects_positive_relationship(
    sales_dataframe,
):
    recommendation = {
        "type": "scatter",
        "x": "sales",
        "y": "profit",
    }

    result = generate_insight(
        sales_dataframe,
        recommendation,
    )

    assert "positive relationship" in result
    assert "correlation: 1.00" in result


def test_scatter_insight_detects_negative_relationship():
    df = pd.DataFrame({
        "discount": [1, 2, 3, 4, 5],
        "profit": [50, 40, 30, 20, 10],
    })

    recommendation = {
        "type": "scatter",
        "x": "discount",
        "y": "profit",
    }

    result = generate_insight(df, recommendation)

    assert "negative relationship" in result
    assert "correlation: -1.00" in result


def test_scatter_insight_handles_constant_column():
    df = pd.DataFrame({
        "sales": [100, 100, 100, 100],
        "profit": [10, 20, 30, 40],
    })

    recommendation = {
        "type": "scatter",
        "x": "sales",
        "y": "profit",
    }

    result = generate_insight(df, recommendation)

    assert "No reliable relationship" in result


def test_scatter_insight_classifies_weak_relationship():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [1, 3, 2, 5, 4],
    })

    recommendation = {
        "type": "scatter",
        "x": "x",
        "y": "y",
    }

    result = generate_insight(df, recommendation)

    assert "relationship" in result
    assert "correlation:" in result


# ==========================================================
# HISTOGRAM INSIGHTS
# ==========================================================

def test_histogram_insight_calculates_mean_and_median():
    df = pd.DataFrame({
        "sales": [10, 20, 30, 40, 50],
    })

    recommendation = {
        "type": "histogram",
        "column": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "mean of 30.00" in result
    assert "median of 30.00" in result
    assert "relatively close" in result


def test_histogram_insight_handles_empty_numeric_data():
    df = pd.DataFrame({
        "sales": [np.nan, np.nan, np.nan],
    })

    recommendation = {
        "type": "histogram",
        "column": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "No valid numeric values" in result


def test_histogram_insight_detects_possible_skewness():
    df = pd.DataFrame({
        "sales": [1, 1, 1, 1, 100],
    })

    recommendation = {
        "type": "histogram",
        "column": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "may be skewed" in result


def test_histogram_insight_handles_zero_median():
    df = pd.DataFrame({
        "profit": [-10, 0, 10],
    })

    recommendation = {
        "type": "histogram",
        "column": "profit",
    }

    result = generate_insight(df, recommendation)

    assert "mean of 0.00" in result
    assert "median of 0.00" in result


# ==========================================================
# BAR CHART INSIGHTS
# ==========================================================

def test_bar_insight_identifies_top_category(
    sales_dataframe,
):
    recommendation = {
        "type": "bar",
        "column": "region",
    }

    result = generate_insight(
        sales_dataframe,
        recommendation,
    )

    assert "North" in result
    assert "60.0% of valid records" in result


def test_bar_insight_identifies_top_metric_category():
    df = pd.DataFrame({
        "region": ["North", "South", "North", "East"],
        "sales": [100, 200, 300, 50],
    })

    recommendation = {
        "type": "bar",
        "column": "region",
        "value_column": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "North" in result
    assert "400.00" in result
    assert "61.5%" in result


def test_bar_insight_handles_empty_categories():
    df = pd.DataFrame({
        "region": [None, None, None],
    })

    recommendation = {
        "type": "bar",
        "column": "region",
    }

    result = generate_insight(df, recommendation)

    assert "No categorical values" in result


def test_bar_insight_handles_zero_total_metric():
    df = pd.DataFrame({
        "region": ["North", "South"],
        "sales": [100, -100],
    })

    recommendation = {
        "type": "bar",
        "column": "region",
        "value_column": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "highest total sales" in result
    assert "100.00" in result


# ==========================================================
# LINE CHART INSIGHTS
# ==========================================================

def test_line_insight_detects_increasing_trend():
    df = pd.DataFrame({
        "date": [
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
        ],
        "sales": [100, 150, 200],
    })

    recommendation = {
        "type": "line",
        "x": "date",
        "y": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "increased by 100.0%" in result
    assert "100.00 to 200.00" in result


def test_line_insight_detects_decreasing_trend():
    df = pd.DataFrame({
        "date": [
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
        ],
        "sales": [300, 200, 100],
    })

    recommendation = {
        "type": "line",
        "x": "date",
        "y": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "decreased by 66.7%" in result


def test_line_insight_handles_insufficient_time_points():
    df = pd.DataFrame({
        "date": ["2026-01-01"],
        "sales": [100],
    })

    recommendation = {
        "type": "line",
        "x": "date",
        "y": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "Not enough time points" in result


def test_line_insight_handles_zero_initial_value():
    df = pd.DataFrame({
        "date": [
            "2026-01-01",
            "2026-01-02",
        ],
        "sales": [0, 100],
    })

    recommendation = {
        "type": "line",
        "x": "date",
        "y": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "changed from 0.00 to 100.00" in result


def test_line_insight_handles_invalid_dates():
    df = pd.DataFrame({
        "date": ["invalid", "also-invalid"],
        "sales": [100, 200],
    })

    recommendation = {
        "type": "line",
        "x": "date",
        "y": "sales",
    }

    result = generate_insight(df, recommendation)

    assert "No valid data" in result


# ==========================================================
# MAP INSIGHTS
# ==========================================================

def test_map_insight_calculates_geographic_span():
    df = pd.DataFrame({
        "latitude": [10.0, 15.0, 20.0],
        "longitude": [70.0, 75.0, 80.0],
    })

    recommendation = {
        "type": "map",
        "latitude": "latitude",
        "longitude": "longitude",
    }

    result = generate_insight(df, recommendation)

    assert "3 geographic records" in result
    assert "10.00° of latitude" in result
    assert "10.00° of longitude" in result


def test_map_insight_handles_missing_coordinates():
    df = pd.DataFrame({
        "latitude": [np.nan, np.nan],
        "longitude": [np.nan, np.nan],
    })

    recommendation = {
        "type": "map",
        "latitude": "latitude",
        "longitude": "longitude",
    }

    result = generate_insight(df, recommendation)

    assert "No valid geographic coordinates" in result


# ==========================================================
# UNKNOWN CHART TYPE
# ==========================================================

def test_unknown_chart_type_returns_fallback(sales_dataframe):
    recommendation = {
        "type": "unknown_chart",
    }

    result = generate_insight(
        sales_dataframe,
        recommendation,
    )

    assert "No analytical explanation is available" in result
    assert "unknown_chart" in result


# ==========================================================
# ANALYTICAL CONTEXT
# ==========================================================

def test_build_analysis_context_includes_dataset_metadata(
    sales_dataframe,
):
    context = build_analysis_context(
        sales_dataframe,
        [],
    )

    assert context["dataset"]["rows"] == 5
    assert context["dataset"]["columns"] == 5


def test_build_analysis_context_calculates_numeric_metrics(
    sales_dataframe,
):
    context = build_analysis_context(
        sales_dataframe,
        [],
    )

    assert context["metrics"]["sales"]["mean"] == pytest.approx(300)
    assert context["metrics"]["sales"]["median"] == pytest.approx(300)
    assert context["metrics"]["sales"]["min"] == pytest.approx(100)
    assert context["metrics"]["sales"]["max"] == pytest.approx(500)
    assert context["metrics"]["sales"]["total"] == pytest.approx(1500)


def test_build_analysis_context_excludes_non_finite_values():
    df = pd.DataFrame({
        "sales": [
            100.0,
            200.0,
            300.0,
            np.inf,
            -np.inf,
            np.nan,
        ]
    })

    context = build_analysis_context(
        df,
        [],
    )

    metrics = context["metrics"]["sales"]

    assert metrics["mean"] == pytest.approx(200)
    assert metrics["median"] == pytest.approx(200)
    assert metrics["min"] == pytest.approx(100)
    assert metrics["max"] == pytest.approx(300)
    assert metrics["total"] == pytest.approx(600)


def test_build_analysis_context_includes_deterministic_findings(
    sales_dataframe,
):
    recommendations = [
        {
            "type": "scatter",
            "x": "sales",
            "y": "profit",
            "score": 0.9,
            "reason": "Strong relationship",
        }
    ]

    context = build_analysis_context(
        sales_dataframe,
        recommendations,
    )

    assert len(context["deterministic_findings"]) == 1

    finding = context["deterministic_findings"][0]

    assert finding["type"] == "scatter"
    assert finding["reason"] == "Strong relationship"
    assert finding["score"] == 0.9
    assert "positive relationship" in finding["insight"]


def test_build_analysis_context_includes_recommendations(
    sales_dataframe,
):
    recommendation = {
        "type": "histogram",
        "column": "sales",
        "score": 0.8,
        "reason": "Numeric distribution",
    }

    context = build_analysis_context(
        sales_dataframe,
        [recommendation],
    )

    assert context["recommendations"] == [recommendation]


def test_build_analysis_context_skips_all_missing_numeric_columns():
    df = pd.DataFrame({
        "sales": [np.nan, np.nan, np.nan],
        "profit": [10, 20, 30],
    })

    context = build_analysis_context(df, [])

    assert "sales" not in context["metrics"]
    assert context["metrics"]["profit"]["mean"] == pytest.approx(20)


def test_build_analysis_context_handles_empty_dataframe():
    df = pd.DataFrame({
        "sales": pd.Series(dtype="float64"),
        "profit": pd.Series(dtype="float64"),
    })

    context = build_analysis_context(df, [])

    assert context["dataset"]["rows"] == 0
    assert context["dataset"]["columns"] == 2
    assert context["metrics"] == {}
    assert context["deterministic_findings"] == []
    assert context["recommendations"] == []