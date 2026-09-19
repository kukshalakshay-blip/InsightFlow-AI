import pandas as pd


def profile_dataset(df: pd.DataFrame) -> dict:
    """
    Generate a high-level profile of a dataset.
    """

    total_cells = df.shape[0] * df.shape[1]
    missing_cells = int(df.isna().sum().sum())

    profile = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_cells": missing_cells,
        "missing_percentage": (
            (missing_cells / total_cells) * 100
            if total_cells > 0
            else 0
        ),
        "numeric_columns": df.select_dtypes(
            include="number"
        ).columns.tolist(),
        "categorical_columns": df.select_dtypes(
            include=["object", "category", "bool"]
        ).columns.tolist(),
    }

    column_profiles = {}

    for column in df.columns:
        series = df[column]

        column_profiles[column] = {
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_percentage": (
                float(series.isna().mean() * 100)
            ),
            "unique_values": int(series.nunique(dropna=True)),
            "unique_percentage": (
                float(
                    series.nunique(dropna=True)
                    / len(series)
                    * 100
                )
                if len(series) > 0
                else 0
            ),
        }

    profile["column_profiles"] = column_profiles

    return profile