from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ValidationResult:
    """Result of dataset validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


def validate_dataset(df: pd.DataFrame) -> ValidationResult:
    """Validate dataset structure and screen for common data-quality risks.

    Structural defects are errors. Potential quality issues are warnings:
    they do not automatically make an otherwise usable dataset invalid.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    errors: list[str] = []
    warnings: list[str] = []

    rows, columns = df.shape

    # 1. Structural checks
    if rows == 0:
        errors.append("The dataset contains no rows.")
    if columns == 0:
        errors.append("The dataset contains no columns.")
    if df.columns.empty:
        errors.append("The dataset has no column names.")

    duplicate_mask = df.columns.duplicated(keep="first")
    if duplicate_mask.any():
        duplicated_columns = (
            df.columns[duplicate_mask].map(str).tolist()
        )
        errors.append(
            f"Duplicate column names found: {duplicated_columns}"
        )

    blank_columns = [
        position
        for position, name in enumerate(df.columns)
        if not str(name).strip()
    ]
    if blank_columns:
        errors.append(
            f"Blank or whitespace-only column names found at positions: "
            f"{blank_columns}"
        )

    if rows == 0 or columns == 0:
        return ValidationResult(
            is_valid=not errors,
            errors=errors,
            warnings=warnings,
        )

    # 2. Missing-data checks
    total_cells = rows * columns
    missing_by_position = [
        int(df.iloc[:, position].isna().sum())
        for position in range(columns)
    ]
    missing_cells = sum(missing_by_position)
    missing_ratio = missing_cells / total_cells

    if missing_ratio >= 0.50:
        warnings.append(
            "More than 50% of the dataset values are missing."
        )
    elif missing_ratio >= 0.20:
        warnings.append(
            "More than 20% of the dataset values are missing."
        )

    all_missing_columns = [
        str(df.columns[position])
        for position, count in enumerate(missing_by_position)
        if count == rows
    ]
    if all_missing_columns:
        warnings.append(
            "Columns containing only missing values: "
            f"{all_missing_columns}"
        )

    # 3. Duplicate-row checks
    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows:
        warnings.append(
            f"{duplicate_rows:,} duplicate rows detected."
        )

    # 4. Non-finite numeric values
    non_finite_details = []
    for position, column in enumerate(df.columns):
        series = df.iloc[:, position]
        if (
            pd.api.types.is_numeric_dtype(series.dtype)
            and not pd.api.types.is_bool_dtype(series.dtype)
        ):
            numeric_values = pd.to_numeric(series, errors="coerce")
            values = numeric_values.to_numpy(dtype="float64", na_value=np.nan)
            positive_infinity = int(np.isposinf(values).sum())
            negative_infinity = int(np.isneginf(values).sum())
            total_infinity = positive_infinity + negative_infinity
            if total_infinity:
                non_finite_details.append(
                    f"{str(column)}: {total_infinity} "
                    f"(+inf: {positive_infinity}, -inf: {negative_infinity})"
                )

    if non_finite_details:
        warnings.append(
            "Infinite numeric values detected: "
            + "; ".join(non_finite_details)
            + "."
        )

    # 5. Constant and high-missingness columns
    constant_columns = []
    for position, column in enumerate(df.columns):
        series = df.iloc[:, position]
        valid = series.dropna()
        if not valid.empty and valid.nunique(dropna=True) == 1:
            constant_columns.append(str(column))

    if constant_columns:
        warnings.append(
            f"Constant columns detected: {constant_columns}"
        )

    # 6. Return a stable, backward-compatible result shape.
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
