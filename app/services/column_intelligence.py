import re

import pandas as pd


def classify_column(
    column_name: str,
    series: pd.Series,
) -> str:
    """
    Assign a basic semantic type to a column.
    """

    column_name_lower = column_name.lower().strip()

    # --------------------------------------------------
    # Identifier detection
    # --------------------------------------------------

    identifier_patterns = [
        r"^id$",
        r".*_id$",
        r".*-id$",
        r".* id$",
        r"^uuid$",
        r".*_uuid$",
        r".*-uuid$",
        r".* uuid$",
        r"^identifier$",
        r".*_identifier$",
        r".*-identifier$",
        r".* identifier$",
        r".*_key$",
        r".*-key$",
        r".* key$",
        r".*_code$",
        r".*-code$",
        r".* code$",
    ]

    for pattern in identifier_patterns:
        if re.match(pattern, column_name_lower):
            return "identifier"

    # --------------------------------------------------
    # Numeric columns
    # --------------------------------------------------

    if pd.api.types.is_numeric_dtype(series):
        return "numeric_measure"

    # --------------------------------------------------
    # Categorical columns
    # --------------------------------------------------

    if isinstance(series.dtype, pd.CategoricalDtype):
        return "categorical"

    if pd.api.types.is_bool_dtype(series):
        return "categorical"

    if pd.api.types.is_string_dtype(series):
        return "categorical"

    # --------------------------------------------------
    # Fallback
    # --------------------------------------------------

    return "unknown"


def analyze_columns(
    df: pd.DataFrame,
) -> list[dict]:
    """
    Analyze dataset columns and assign basic semantic categories.
    """

    column_information = []

    for column in df.columns:
        series = df[column]

        dtype = str(series.dtype)

        unique_count = int(
            series.nunique(dropna=True)
        )

        missing_percentage = float(
            series.isna().mean() * 100
        )

        semantic_type = classify_column(
            column,
            series,
        )

        column_information.append(
            {
                "column": column,
                "dtype": dtype,
                "semantic_type": semantic_type,
                "unique_count": unique_count,
                "missing_percentage": missing_percentage,
            }
        )

    return column_information