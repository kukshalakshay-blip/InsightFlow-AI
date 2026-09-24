import re

import pandas as pd


def looks_like_datetime(series: pd.Series) -> bool:
    """
    Check whether a column appears to contain datetime values.
    """

    if not pd.api.types.is_string_dtype(series):
        return False

    non_null_values = series.dropna()

    if len(non_null_values) == 0:
        return False

    parsed_values = pd.to_datetime(
        non_null_values,
        errors="coerce",
        format="mixed",
    )

    valid_ratio = parsed_values.notna().mean()

    return valid_ratio >= 0.80


def looks_like_year(series: pd.Series) -> bool:
    """
    Check whether numeric values look like calendar years.
    """

    non_null_values = series.dropna()

    if len(non_null_values) == 0:
        return False

    return non_null_values.between(
        1900,
        2100,
    ).mean() >= 0.90


def looks_like_count(
    column_name: str,
    series: pd.Series,
) -> bool:
    """
    Check whether a numeric column likely represents a count.
    """

    column_name_lower = column_name.lower().strip()

    count_keywords = [
        "count",
        "number",
        "num_",
        "quantity",
        "qty",
        "rooms",
        "bedroom",
        "bathroom",
        "car",
    ]

    has_count_keyword = any(
        keyword in column_name_lower
        for keyword in count_keywords
    )

    if not has_count_keyword:
        return False

    non_null_values = series.dropna()

    if len(non_null_values) == 0:
        return False

    return bool(
        (non_null_values >= 0).all()
        and
        (non_null_values % 1 == 0).mean() >= 0.95
    )


def looks_like_geographic_code(
    column_name: str,
    series: pd.Series,
) -> bool:
    """
    Check whether a numeric column likely represents
    a geographic or postal code.
    """

    column_name_lower = column_name.lower().strip()

    geographic_keywords = [
        "postcode",
        "postal",
        "zip",
        "zipcode",
        "zip_code",
    ]

    return any(
        keyword in column_name_lower
        for keyword in geographic_keywords
    )



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
    # Geographic columns
    # --------------------------------------------------

    latitude_names = [
        "latitude",
        "lattitude",
        "lat",
    ]

    longitude_names = [
        "longitude",
        "longtitude",
        "long",
        "lng",
    ]

    if any(
        name in column_name_lower
        for name in latitude_names
    ):
        return "geographic_latitude"

    if any(
        name in column_name_lower
        for name in longitude_names
    ):
        return "geographic_longitude"

    # --------------------------------------------------
    # Datetime columns
    # --------------------------------------------------

    datetime_keywords = [
        "date",
        "time",
        "timestamp",
        "created_at",
        "updated_at",
    ]

    looks_like_date_name = any(
        keyword in column_name_lower
        for keyword in datetime_keywords
    )

    if looks_like_date_name:
        if looks_like_datetime(series):
            return "datetime"

    

    # --------------------------------------------------
    # Numeric columns
    # --------------------------------------------------

    if pd.api.types.is_numeric_dtype(series):

        if looks_like_geographic_code(
            column_name,
            series,
        ):
            return "geographic_code"

        if looks_like_year(series):
            return "year"

        if looks_like_count(
            column_name,
            series,
        ):
            return "count"

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