import numpy as np
import pandas as pd
import pytest

from app.services.analysis_engine import (
    analyze_correlation,
    analyze_distribution,
    analyze_trend,
)


# ==========================================================
# TREND ANALYSIS
# ==========================================================

def test_analyze_trend_calculates_daily_mean():
    df = pd.DataFrame({
        "date": [
            "2026-01-01",
            "2026-01-01",
            "2026-01-02",
        ],
        "sales": [100, 200, 300],
    })

    result = analyze_trend(df, "date", "sales")

    assert len(result) == 2
    assert result.loc[0, "sales"] == pytest.approx(150)
    assert result.loc[1, "sales"] == pytest.approx(300)


def test_analyze_trend_sorts_dates_chronologically():
    df = pd.DataFrame({
        "date": [
            "2026-01-03",
            "2026-01-01",
            "2026-01-02",
        ],
        "sales": [300, 100, 200],
    })

    result = analyze_trend(df, "date", "sales")

    assert result["date"].is_monotonic_increasing
    assert result["sales"].tolist() == [100, 200, 300]


def test_analyze_trend_removes_invalid_dates():
    df = pd.DataFrame({
        "date": [
            "2026-01-01",
            "not-a-date",
            "2026-01-02",
        ],
        "sales": [100, 999, 200],
    })

    result = analyze_trend(df, "date", "sales")

    assert len(result) == 2
    assert result["sales"].tolist() == [100, 200]


def test_analyze_trend_preserves_missing_time_periods():
    df = pd.DataFrame({
        "date": [
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
        ],
        "sales": [100, np.nan, 300],
    })

    result = analyze_trend(df, "date", "sales")

    # Daily resampling preserves the complete timeline.
    assert len(result) == 3

    # Dates with valid observations retain their values.
    assert result.loc[0, "sales"] == pytest.approx(100)
    assert result.loc[2, "sales"] == pytest.approx(300)

    # The missing observation is not incorrectly replaced by zero.
    assert pd.isna(result.loc[1, "sales"])


def test_analyze_trend_supports_weekly_frequency():
    df = pd.DataFrame({
        "date": [
            "2026-01-05",
            "2026-01-06",
            "2026-01-12",
        ],
        "sales": [100, 200, 300],
    })

    result = analyze_trend(
        df,
        "date",
        "sales",
        frequency="W",
    )

    assert len(result) == 2
    assert result["sales"].tolist() == [150, 300]


def test_analyze_trend_returns_empty_result_for_invalid_dates():
    df = pd.DataFrame({
        "date": ["invalid", "also-invalid"],
        "sales": [100, 200],
    })

    result = analyze_trend(df, "date", "sales")

    assert result.empty
    assert "date" in result.columns
    assert "sales" in result.columns


def test_analyze_trend_handles_empty_dataframe():
    df = pd.DataFrame({
        "date": pd.Series(dtype="object"),
        "sales": pd.Series(dtype="float64"),
    })

    result = analyze_trend(df, "date", "sales")

    assert result.empty
    assert "date" in result.columns
    assert "sales" in result.columns


def test_analyze_trend_rejects_missing_column():
    df = pd.DataFrame({
        "date": ["2026-01-01"],
        "sales": [100],
    })

    with pytest.raises(KeyError):
        analyze_trend(df, "date", "profit")


# ==========================================================
# CORRELATION ANALYSIS
# ==========================================================

def test_analyze_correlation_detects_perfect_positive():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [2, 4, 6, 8, 10],
    })

    result = analyze_correlation(df, "x", "y")

    assert result == pytest.approx(1.0)


def test_analyze_correlation_detects_perfect_negative():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [10, 8, 6, 4, 2],
    })

    result = analyze_correlation(df, "x", "y")

    assert result == pytest.approx(-1.0)


def test_analyze_correlation_detects_no_linear_relationship():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [1, -1, 1, -1, 1],
    })

    result = analyze_correlation(df, "x", "y")

    assert result == pytest.approx(0.0)


def test_analyze_correlation_returns_none_for_constant_x():
    df = pd.DataFrame({
        "x": [5, 5, 5, 5],
        "y": [1, 2, 3, 4],
    })

    assert analyze_correlation(df, "x", "y") is None


def test_analyze_correlation_returns_none_for_constant_y():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4],
        "y": [5, 5, 5, 5],
    })

    assert analyze_correlation(df, "x", "y") is None


def test_analyze_correlation_handles_missing_values():
    df = pd.DataFrame({
        "x": [1, 2, np.nan, 4, 5],
        "y": [2, 4, 6, 8, 10],
    })

    result = analyze_correlation(df, "x", "y")

    assert result == pytest.approx(1.0)


def test_analyze_correlation_returns_none_when_insufficient_data():
    df = pd.DataFrame({
        "x": [1, np.nan, np.nan],
        "y": [2, 3, 4],
    })

    assert analyze_correlation(df, "x", "y") is None


def test_analyze_correlation_returns_float():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4],
        "y": [2, 3, 5, 8],
    })

    result = analyze_correlation(df, "x", "y")

    assert isinstance(result, float)


def test_analyze_correlation_rejects_missing_column():
    df = pd.DataFrame({
        "x": [1, 2, 3],
        "y": [2, 4, 6],
    })

    with pytest.raises(KeyError):
        analyze_correlation(df, "x", "profit")


# ==========================================================
# DISTRIBUTION ANALYSIS
# ==========================================================

def test_analyze_distribution_calculates_mean_and_median():
    df = pd.DataFrame({
        "sales": [10, 20, 30, 40, 50],
    })

    result = analyze_distribution(df, "sales")

    assert result["mean"] == pytest.approx(30.0)
    assert result["median"] == pytest.approx(30.0)
    assert result["difference_percentage"] == pytest.approx(0.0)


def test_analyze_distribution_calculates_percentage_difference():
    df = pd.DataFrame({
        "sales": [10, 20, 30],
    })

    result = analyze_distribution(df, "sales")

    assert result["mean"] == pytest.approx(20.0)
    assert result["median"] == pytest.approx(20.0)
    assert result["difference_percentage"] == pytest.approx(0.0)


def test_analyze_distribution_handles_zero_median():
    df = pd.DataFrame({
        "sales": [-10, 0, 10],
    })

    result = analyze_distribution(df, "sales")

    assert result["median"] == pytest.approx(0.0)
    assert result["difference_percentage"] is None


def test_analyze_distribution_handles_empty_column():
    df = pd.DataFrame({
        "sales": [np.nan, np.nan, np.nan],
    })

    result = analyze_distribution(df, "sales")

    assert result == {
        "mean": None,
        "median": None,
        "difference_percentage": None,
    }


def test_analyze_distribution_ignores_missing_values():
    df = pd.DataFrame({
        "sales": [10, 20, np.nan, 30],
    })

    result = analyze_distribution(df, "sales")

    assert result["mean"] == pytest.approx(20.0)
    assert result["median"] == pytest.approx(20.0)


def test_analyze_distribution_handles_negative_values():
    df = pd.DataFrame({
        "profit": [-10, -20, -30],
    })

    result = analyze_distribution(df, "profit")

    assert result["mean"] == pytest.approx(-20.0)
    assert result["median"] == pytest.approx(-20.0)
    assert result["difference_percentage"] == pytest.approx(0.0)


def test_analyze_distribution_rejects_missing_column():
    df = pd.DataFrame({
        "sales": [10, 20, 30],
    })

    with pytest.raises(KeyError):
        analyze_distribution(df, "profit")