import pandas as pd


def analyze_trend(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    frequency: str = "D",
) -> pd.DataFrame:
    """
    Prepare time-series data for trend analysis.

    Converts the x-axis column to datetime,
    removes invalid values, calculates the
    mean y-value for each date, and sorts
    the result chronologically.
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
    Calculate the Pearson correlation between two
    numerical columns.
    """

    correlation = df[x_column].corr(
        df[y_column]
    )

    if pd.isna(correlation):
        return None

    return float(correlation)

def analyze_distribution(
    df: pd.DataFrame,
    column: str,
) -> dict:
    """
    Analyze the distribution of a numerical column.

    Calculates the mean, median, and the percentage
    difference between them.
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
            abs(mean - median)
            / abs(median)
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