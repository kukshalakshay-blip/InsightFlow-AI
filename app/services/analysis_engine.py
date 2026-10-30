import numpy as np
import pandas as pd
from typing import Literal, cast


# ============================================================
# SHARED DATA PREPARATION
# ============================================================

def _clean_numeric_data(series: pd.Series) -> pd.Series:
    """
    Convert a Series into valid finite numerical observations.

    - Converts numeric strings.
    - Removes missing values.
    - Removes positive and negative infinity.
    - Preserves original row indexes.
    """

    numeric_data = pd.to_numeric(
        series,
        errors="coerce",
    )

    numeric_data = numeric_data.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    return numeric_data.dropna()


# ============================================================
# 1. TREND ANALYSIS
# ============================================================

def analyze_trend(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    frequency: str = "D",
) -> pd.DataFrame:
    """
    Aggregate numerical values over time.

    Invalid dates and numerical observations are excluded.
    Missing time periods are preserved as NaN.
    """

    trend_data = df[
        [x_column, y_column]
    ].copy()

    trend_data[x_column] = pd.to_datetime(
        trend_data[x_column],
        errors="coerce",
        format="mixed",
    )

    trend_data[y_column] = pd.to_numeric(
        trend_data[y_column],
        errors="coerce",
    )

    trend_data[y_column] = trend_data[
        y_column
    ].replace(
        [np.inf, -np.inf],
        np.nan,
    )

    trend_data = trend_data.dropna(
        subset=[x_column, y_column]
    )

    if trend_data.empty:
        return pd.DataFrame(
            columns=[x_column, y_column]
        )

    trend_data = (
        trend_data
        .set_index(x_column)[y_column]
        .resample(frequency)
        .mean()
        .rename(y_column)
        .reset_index()
    )

    return trend_data


# ============================================================
# 2. CORRELATION ANALYSIS
# ============================================================

def analyze_correlation(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    method: str = "pearson",
) -> float | None:
    """
    Calculate correlation between two numerical columns.

    Supported methods:
    - Pearson: Linear relationships.
    - Spearman: Monotonic relationships.

    Missing and infinite paired observations are excluded.
    """

    supported_methods = {
        "pearson",
        "spearman",
    }

    method = method.lower()

    if method not in supported_methods:
        raise ValueError(
            f"Unsupported correlation method: {method}. "
            "Use 'pearson' or 'spearman'."
        )

    paired_data = pd.DataFrame({
        x_column: _clean_numeric_data(
            df[x_column]
        ),
        y_column: _clean_numeric_data(
            df[y_column]
        ),
    }).dropna()

    if len(paired_data) < 2:
        return None

    x = paired_data[x_column]
    y = paired_data[y_column]

    if x.nunique() < 2 or y.nunique() < 2:
        return None

    correlation = x.corr(
        y,
        method=cast(Literal["pearson", "spearman"], method),
    )

    if pd.isna(correlation):
        return None

    return float(correlation)


# ============================================================
# 3. DISTRIBUTION ANALYSIS
# ============================================================

def analyze_distribution(
    df: pd.DataFrame,
    column: str,
) -> dict:
    """
    Calculate descriptive statistics for a numerical column.

    Existing output keys are preserved for compatibility.
    """

    numeric_data = _clean_numeric_data(
        df[column]
    )

    if numeric_data.empty:
        return {
            "mean": None,
            "median": None,
            "difference_percentage": None,
        }

    mean = numeric_data.mean()
    median = numeric_data.median()

    if median == 0:
        difference_percentage = None
    else:
        difference_percentage = (
            abs(mean - median) / abs(median)
        ) * 100

    return {
        "mean": float(mean),
        "median": float(median),
        "difference_percentage": (
            float(difference_percentage)
            if difference_percentage is not None
            else None
        ),
        "std": (
            float(numeric_data.std())
            if len(numeric_data) > 1
            else None
        ),
        "variance": (
            float(numeric_data.var())
            if len(numeric_data) > 1
            else None
        ),
        "q1": float(numeric_data.quantile(0.25)),
        "q3": float(numeric_data.quantile(0.75)),
        "skewness": (
            float(cast(float, numeric_data.skew()))
            if len(numeric_data) >= 3
            and pd.notna(numeric_data.skew())
            else None
        ),
        "valid_count": int(len(numeric_data)),
    }


# ============================================================
# 4. OUTLIER DETECTION
# ============================================================

def detect_outliers(
    df: pd.DataFrame,
    column: str,
    multiplier: float = 1.5,
) -> dict:
    """
    Detect potential numerical outliers using IQR.

    Non-finite observations are excluded.
    Original DataFrame is never modified.
    """

    if not np.isfinite(multiplier) or multiplier <= 0:
        raise ValueError(
            "multiplier must be a finite number greater than zero."
        )

    if column not in df.columns:
        raise KeyError(
            f"Column '{column}' does not exist."
        )

    series = df[column]

    if series.isna().all():
        return {
            "column": column,
            "q1": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "outlier_values": [],
            "outlier_count": 0,
            "valid_count": 0,
            "outlier_percentage": 0.0,
        }

    if (
        not pd.api.types.is_numeric_dtype(series)
        or pd.api.types.is_bool_dtype(series)
    ):
        raise TypeError(
            f"Column '{column}' must contain numeric values, "
            "not Boolean or non-numeric values."
        )

    numeric_data = series.dropna()

    numeric_data = numeric_data[
        np.isfinite(numeric_data)
    ]

    if numeric_data.empty:
        return {
            "column": column,
            "q1": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "outlier_values": [],
            "outlier_count": 0,
            "valid_count": 0,
            "outlier_percentage": 0.0,
        }

    q1 = float(numeric_data.quantile(0.25))
    q3 = float(numeric_data.quantile(0.75))

    iqr = q3 - q1

    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    outliers = numeric_data[
        (numeric_data < lower_bound)
        | (numeric_data > upper_bound)
    ]

    outlier_count = int(len(outliers))
    valid_count = int(len(numeric_data))

    outlier_percentage = (
        outlier_count / valid_count * 100
    )

    return {
        "column": column,
        "q1": q1,
        "q3": q3,
        "iqr": float(iqr),
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
        "outlier_values": outliers.tolist(),
        "outlier_count": outlier_count,
        "valid_count": valid_count,
        "outlier_percentage": float(
            outlier_percentage
        ),
    }