import numpy as np
import pandas as pd


def analyze_trend(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    frequency: str = "D",
) -> pd.DataFrame:
    """
    Prepare time-series data for trend analysis.

    Converts the x-axis column to datetime, removes invalid
    values, calculates the mean y-value for each date, and
    sorts the result chronologically.
    """

    trend_data = df[[x_column, y_column]].copy()

    trend_data[x_column] = pd.to_datetime(
        trend_data[x_column],
        errors="coerce",
        format="mixed",
    )

    trend_data = trend_data.dropna(
        subset=[x_column, y_column]
    )

    trend_data = (
        trend_data
        .set_index(x_column)
        .resample(frequency)[y_column]
        .mean()
        .reset_index()
    )

    return trend_data


def analyze_correlation(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
) -> float | None:
    """
    Calculate the Pearson correlation between two numerical
    columns.

    Return None when either column has insufficient variation
    or the correlation cannot be calculated.
    """

    x = df[x_column]
    y = df[y_column]

    # Correlation is undefined when either column is constant.
    if x.nunique(dropna=True) < 2:
        return None

    if y.nunique(dropna=True) < 2:
        return None

    correlation = x.corr(y)

    if pd.isna(correlation):
        return None

    return float(correlation)


def analyze_distribution(
    df: pd.DataFrame,
    column: str,
) -> dict:
    """
    Analyze the distribution of a numerical column.

    Calculates the mean, median, and percentage difference
    between them.
    """

    numeric_data = df[column].dropna()

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
    }


def detect_outliers(
    df: pd.DataFrame,
    column: str,
    multiplier: float = 1.5,
) -> dict:
    """
    Detect potential numerical outliers using the IQR method.

    Values below Q1 - multiplier * IQR or above
    Q3 + multiplier * IQR are flagged.

    Missing and non-finite values are excluded.

    The original DataFrame is never modified.

    Returns:
        A dictionary containing quartiles, boundaries,
        outlier values, counts, and outlier percentage.
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

    # An entirely missing column has no values to analyze.
    # Handle this before checking its dtype because pandas
    # may infer an object dtype for a column containing only None.
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

    # Convert to numeric values and exclude NaN, infinity,
    # and negative infinity from statistical calculations.
    numeric_data = series.dropna()
    numeric_data = numeric_data[
        np.isfinite(numeric_data)
    ]

    # The column may contain only non-finite values.
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

    # Values exactly on either boundary are not outliers.
    outliers = numeric_data[
        (numeric_data < lower_bound)
        | (numeric_data > upper_bound)
    ]

    outlier_count = int(len(outliers))
    valid_count = int(len(numeric_data))

    outlier_percentage = (
        outlier_count / valid_count * 100
        if valid_count > 0
        else 0.0
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
        "outlier_percentage": float(outlier_percentage),
    }