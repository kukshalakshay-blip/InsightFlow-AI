"""Dataset profiling utilities for InsightFlow."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _finite_numeric_values(series: pd.Series) -> pd.Series:
    """Return numeric, finite observations without mutating the source."""
    values = pd.to_numeric(series, errors="coerce")
    values = values.replace([np.inf, -np.inf], np.nan).dropna()
    return values


def _column_semantic_type(column: object, series: pd.Series) -> str:
    """Use InsightFlow's semantic classifier when available."""
    try:
        from app.services.column_intelligence import classify_column

        result = classify_column(str(column), series)
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            return str(result.get("semantic_type", "unknown"))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass
    return "unknown"


def profile_dataset(df: pd.DataFrame) -> dict:
    """
    Generate a structural, quality, semantic and statistical dataset profile.

    Existing top-level keys are retained for backward compatibility.
    Numeric statistics exclude NaN and positive/negative infinity.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("profile_dataset expects a pandas DataFrame.")

    if not df.columns.is_unique:
        raise ValueError("DataFrame column names must be unique for profiling.")

    rows, columns = df.shape
    total_cells = rows * columns
    missing_by_column = df.isna().sum()
    missing_cells = int(missing_by_column.sum())
    rows_with_missing = int(df.isna().any(axis=1).sum()) if rows else 0

    numeric_columns = [
        col for col in df.select_dtypes(include="number").columns
        if not pd.api.types.is_bool_dtype(df[col])
    ]
    categorical_columns = df.select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()
    datetime_columns = df.select_dtypes(
        include=["datetime", "datetimetz"]
    ).columns.tolist()

    profile = {
        "rows": int(rows),
        "columns": int(columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_percentage": (
            float(df.duplicated().mean() * 100) if rows else 0.0
        ),
        "missing_cells": missing_cells,
        "missing_percentage": (
            float(missing_cells / total_cells * 100) if total_cells else 0.0
        ),
        "rows_with_missing": rows_with_missing,
        "complete_rows": int(rows - rows_with_missing),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "datetime_columns": datetime_columns,
        "memory_usage_bytes": int(
            df.memory_usage(index=True, deep=True).sum()
        ),
        "column_profiles": {},
    }

    column_profiles = {}
    for column in df.columns:
        series = df[column]
        missing_count = int(series.isna().sum())
        valid_count = int(series.notna().sum())
        unique_count = int(series.nunique(dropna=True))
        item = {
            "dtype": str(series.dtype),
            "semantic_type": _column_semantic_type(column, series),
            "missing_count": missing_count,
            "missing_percentage": (
                float(missing_count / rows * 100) if rows else 0.0
            ),
            "valid_count": valid_count,
            "unique_values": unique_count,
            "unique_percentage": (
                float(unique_count / rows * 100) if rows else 0.0
            ),
            "cardinality": unique_count,
            "cardinality_ratio": (
                float(unique_count / valid_count) if valid_count else 0.0
            ),
        }

        if column in numeric_columns:
            values = _finite_numeric_values(series)
            non_finite_count = int(
                (pd.to_numeric(series, errors="coerce").isin([np.inf, -np.inf])).sum()
            )
            item["non_finite_count"] = non_finite_count
            item["finite_count"] = int(len(values))
            item["numeric_statistics"] = {
                "count": int(len(values)),
                "mean": float(values.mean()) if len(values) else None,
                "median": float(values.median()) if len(values) else None,
                "std": float(values.std()) if len(values) > 1 else None,
                "min": float(values.min()) if len(values) else None,
                "q1": float(values.quantile(0.25)) if len(values) else None,
                "q3": float(values.quantile(0.75)) if len(values) else None,
                "max": float(values.max()) if len(values) else None,
                "skewness": (
                    float(values.skew())
                    if len(values) >= 3 and pd.notna(values.skew())
                    else None
                ),
                "zero_count": int((values == 0).sum()),
                "negative_count": int((values < 0).sum()),
            }

        elif column in categorical_columns:
            counts = series.value_counts(dropna=True).head(5)
            item["top_values"] = [
                {"value": str(value), "count": int(count)}
                for value, count in counts.items()
            ]

        elif column in datetime_columns:
            dates = pd.to_datetime(series, errors="coerce").dropna()
            item["datetime_statistics"] = {
                "min": dates.min().isoformat() if len(dates) else None,
                "max": dates.max().isoformat() if len(dates) else None,
                "valid_count": int(len(dates)),
            }

        column_profiles[column] = item

    profile["column_profiles"] = column_profiles
    return profile
