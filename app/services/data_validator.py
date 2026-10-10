from dataclasses import dataclass

import pandas as pd


@dataclass
class ValidationResult:
    """Result of dataset validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


def validate_dataset(df: pd.DataFrame) -> ValidationResult:
    """Validate a dataset's structure and report potential data-quality issues."""

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Check the basic dataset structure
    if df.empty:
        errors.append("The dataset contains no rows.")

    if df.shape[1] == 0:
        errors.append("The dataset contains no columns.")

    if df.columns.empty:
        errors.append("The dataset has no column names.")

    # 2. Detect duplicate column names
    if df.columns.duplicated().any():
        duplicated_columns = (
            df.columns[df.columns.duplicated()]
            .astype(str)
            .tolist()
        )

        errors.append(
            f"Duplicate column names found: {duplicated_columns}"
        )

    # 3. Check missing values
    total_cells = df.shape[0] * df.shape[1]

    if total_cells > 0:
        missing_cells = int(df.isna().sum().sum())
        missing_ratio = missing_cells / total_cells

        if missing_ratio >= 0.50:
            warnings.append(
                "More than 50% of the dataset values are missing."
            )
        elif missing_ratio >= 0.20:
            warnings.append(
                "More than 20% of the dataset values are missing."
            )

    # 4. Detect duplicate rows
    duplicate_rows = int(df.duplicated().sum())

    if duplicate_rows > 0:
        warnings.append(
            f"{duplicate_rows:,} duplicate rows detected."
        )

    # 5. Return the validation result
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )