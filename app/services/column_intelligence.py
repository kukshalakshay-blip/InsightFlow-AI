import pandas as pd


def looks_like_datetime(series: pd.Series) -> bool:
    """
    Determine whether a column contains datetime-like values.

    Numeric and boolean columns are excluded because numbers
    can sometimes be incorrectly interpreted as timestamps.
    """

    if series.empty:
        return False

    # Numeric columns should not be treated as dates.
    if pd.api.types.is_numeric_dtype(series):
        return False

    # Boolean columns should not be treated as dates.
    if pd.api.types.is_bool_dtype(series):
        return False

    converted = pd.to_datetime(
        series,
        errors="coerce",
        format="mixed",
    )

    valid_ratio = converted.notna().mean()

    return valid_ratio >= 0.80


def looks_like_year(series: pd.Series) -> bool:
    """
    Determine whether a numerical column represents years.
    """

    if series.empty:
        return False

    numeric_series = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric_series.empty:
        return False

    valid_years = numeric_series.between(
        1900,
        2100,
    )

    return valid_years.mean() >= 0.90


def looks_like_month(
    column_name: str,
    series: pd.Series,
) -> bool:
    """
    Determine whether a column represents calendar months.
    """

    name = column_name.lower().strip()

    month_keywords = {
    "month",
    "order_month",
    "month_number",
    "month_num",
}

    if name not in month_keywords:
        return False

    numeric_series = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric_series.empty:
        return False

    return (
        numeric_series.between(1, 12).mean()
        >= 0.90
    )


def looks_like_quarter(
    column_name: str,
    series: pd.Series,
) -> bool:
    """
    Determine whether a column represents calendar quarters.
    """

    name = column_name.lower().strip()

    quarter_keywords = {
        "quarter",
        "order_quarter",
        "fiscal_quarter",
    }

    if name not in quarter_keywords:
        return False

    numeric_series = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric_series.empty:
        return False

    return (
        numeric_series.between(1, 4).mean()
        >= 0.90
    )


def looks_like_identifier(
    column_name: str,
    series: pd.Series,
) -> bool:
    """
    Determine whether a column is likely an identifier.
    """

    name = column_name.lower().strip()

    identifier_keywords = {
        "id",
        "identifier",
        "row_id",
        "order_id",
        "customer_id",
        "product_id",
        "user_id",
        "account_id",
        "transaction_id",
    }

    if name in identifier_keywords:
        return True

    if name.endswith("_id"):
        return True

    if name.endswith("id") and len(name) > 2:
        return True

    return False


def looks_like_geographic_code(
    column_name: str,
    series: pd.Series,
) -> bool:
    """
    Determine whether a column represents a geographic code.
    """

    name = column_name.lower().strip()

    geographic_keywords = {
        "postcode",
        "postal_code",
        "postalcode",
        "zip",
        "zipcode",
        "zip_code",
    }

    return name in geographic_keywords


def looks_like_count(
    column_name: str,
    series: pd.Series,
) -> bool:
    """
    Determine whether a numerical column represents a count.
    """

    name = column_name.lower()

    count_keywords = {
        "count",
        "number",
        "num",
        "quantity",
        "qty",
        "rooms",
        "bedroom",
        "bedrooms",
        "bathroom",
        "bathrooms",
        "car",
        "cars",
    }

    keyword_match = any(
        keyword in name
        for keyword in count_keywords
    )

    if not keyword_match:
        return False

    numeric_series = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric_series.empty:
        return False

    return bool(
        (numeric_series >= 0).all()
        and (numeric_series % 1 == 0).all()
    )


def is_constant(series: pd.Series) -> bool:
    """
    Determine whether a column contains only one
    unique value.
    """

    return series.nunique(
        dropna=True
    ) <= 1


def is_binary_category(series: pd.Series) -> bool:
    """
    Determine whether a column contains exactly
    two unique values.
    """

    return series.nunique(
        dropna=True
    ) == 2


def is_high_cardinality(
    series: pd.Series,
) -> bool:
    """
    Determine whether a categorical column contains
    many unique values relative to the dataset size.
    """

    unique_count = series.nunique(
        dropna=True
    )

    row_count = len(series)

    if row_count == 0:
        return False

    threshold = max(
        50,
        row_count * 0.05,
    )

    return unique_count > threshold


def classify_column(
    column_name: str,
    series: pd.Series,
) -> str:
    """
    Classify a column according to its semantic role.
    """

    # ----------------------------------------------
    # 1. Constant columns
    # ----------------------------------------------

    if is_constant(series):
        return "constant"

    # ----------------------------------------------
    # 2. Geographic codes
    # ----------------------------------------------

    if looks_like_geographic_code(
        column_name,
        series,
    ):
        return "geographic_code"

    # ----------------------------------------------
    # 3. Identifiers
    # ----------------------------------------------

    if looks_like_identifier(
        column_name,
        series,
    ):
        return "identifier"

    # ----------------------------------------------
    # 4. Boolean columns
    # ----------------------------------------------

    if pd.api.types.is_bool_dtype(series):
        return "binary_category"

    # ----------------------------------------------
    # 5. Binary categorical columns
    # ----------------------------------------------

    if is_binary_category(series):

        if not pd.api.types.is_numeric_dtype(series):
            return "binary_category"

    # ----------------------------------------------
    # 6. Datetime columns
    # ----------------------------------------------

    if looks_like_datetime(series):
        return "datetime"

    # ----------------------------------------------
    # 7. Year columns
    # ----------------------------------------------

    if looks_like_year(series):
        return "year"

    # ----------------------------------------------
    # 8. Month columns
    # ----------------------------------------------

    if looks_like_month(
        column_name,
        series,
    ):
        return "temporal_component"

    # ----------------------------------------------
    # 9. Quarter columns
    # ----------------------------------------------

    if looks_like_quarter(
        column_name,
        series,
    ):
        return "temporal_component"

    # ----------------------------------------------
    # 10. Numeric counts
    # ----------------------------------------------

    if looks_like_count(
        column_name,
        series,
    ):
        return "count"

    # ----------------------------------------------
    # 11. Numeric measurements
    # ----------------------------------------------

    if pd.api.types.is_numeric_dtype(series):
        return "numeric_measure"

    # ----------------------------------------------
    # 12. String / categorical columns
    # ----------------------------------------------

    if pd.api.types.is_string_dtype(series):

        if is_high_cardinality(series):
            return "high_cardinality_categorical"

        return "categorical"

    # ----------------------------------------------
    # 13. Pandas categorical dtype
    # ----------------------------------------------

    if isinstance(
        series.dtype,
        pd.CategoricalDtype,
    ):

        if is_high_cardinality(series):
            return "high_cardinality_categorical"

        return "categorical"

    # ----------------------------------------------
    # 14. Unknown
    # ----------------------------------------------

    return "unknown"


def analyze_columns(
    df: pd.DataFrame,
) -> list[dict]:
    """
    Analyze every column in a dataset and return
    semantic information about each column.
    """

    results = []

    for column in df.columns:

        series = df[column]

        results.append(
            {
                "column": column,
                "dtype": str(series.dtype),
                "semantic_type": classify_column(
                    column,
                    series,
                ),
                "unique_count": int(
                    series.nunique(
                        dropna=True
                    )
                ),
                "missing_percentage": float(
                    series.isna().mean() * 100
                ),
            }
        )

    return results