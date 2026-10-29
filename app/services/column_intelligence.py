import pandas as pd


# =========================================================
# 1. Datetime detection
# =========================================================

def looks_like_datetime(series: pd.Series) -> bool:
    """Determine whether a column contains datetime-like values."""

    if series.empty:
        return False

    if (
        pd.api.types.is_numeric_dtype(series)
        or pd.api.types.is_bool_dtype(series)
    ):
        return False

    converted = pd.to_datetime(
        series,
        errors="coerce",
        format="mixed",
    )

    return bool(converted.notna().mean() >= 0.80)


# =========================================================
# 2. Year detection
# =========================================================

def looks_like_year(series: pd.Series) -> bool:
    """Determine whether a numerical column represents years."""

    if series.empty:
        return False

    numeric_series = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric_series.empty:
        return False

    return bool(
        numeric_series.between(1900, 2100).mean() >= 0.90
    )


# =========================================================
# 3. Month and quarter detection
# =========================================================

def looks_like_month(
    column_name: str,
    series: pd.Series,
) -> bool:
    """Identify numerical calendar-month columns."""

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

    return bool(
        numeric_series.between(1, 12).mean() >= 0.90
    )


def looks_like_quarter(
    column_name: str,
    series: pd.Series,
) -> bool:
    """Identify numerical calendar-quarter columns."""

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

    return bool(
        numeric_series.between(1, 4).mean() >= 0.90
    )


# =========================================================
# 4. Identifier detection
# =========================================================

def looks_like_identifier(
    column_name: str,
    series: pd.Series,
) -> bool:
    """Determine whether a column is likely an identifier."""

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


# =========================================================
# 5. Geographic-code detection
# =========================================================

def looks_like_geographic_code(
    column_name: str,
    series: pd.Series,
) -> bool:
    """Identify columns containing postal or ZIP codes."""

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


# =========================================================
# 6. Latitude and longitude detection
# =========================================================

def _coordinate_values_are_valid(
    series: pd.Series,
    minimum: float,
    maximum: float,
) -> bool:
    """Validate numeric coordinates while allowing missing values."""

    if series.empty:
        return False

    numeric_series = pd.to_numeric(
        series,
        errors="coerce",
    )

    # Non-missing source values must be numeric.
    invalid_values = series.notna() & numeric_series.isna()

    if invalid_values.any():
        return False

    valid_values = numeric_series.dropna()

    if valid_values.empty:
        return False

    return bool(
        valid_values.between(minimum, maximum).all()
    )


def looks_like_latitude(
    column_name: str,
    series: pd.Series,
) -> bool:
    """Identify latitude columns with valid geographic ranges."""

    name = column_name.lower().strip()

    latitude_names = {
        "latitude",
        "lat",
        "geo_latitude",
        "geo_lat",
        "y_latitude",
    }

    if name not in latitude_names:
        return False

    return _coordinate_values_are_valid(
        series,
        minimum=-90,
        maximum=90,
    )


def looks_like_longitude(
    column_name: str,
    series: pd.Series,
) -> bool:
    """Identify longitude columns with valid geographic ranges."""

    name = column_name.lower().strip()

    longitude_names = {
        "longitude",
        "lon",
        "lng",
        "geo_longitude",
        "geo_lon",
        "y_longitude",
    }

    if name not in longitude_names:
        return False

    return _coordinate_values_are_valid(
        series,
        minimum=-180,
        maximum=180,
    )


# =========================================================
# 7. Count detection
# =========================================================

def looks_like_count(
    column_name: str,
    series: pd.Series,
) -> bool:
    """Determine whether a numerical column represents a count."""

    name = column_name.lower().strip()

    # Entity numbers are not necessarily counts.
    if name.endswith("_number"):
        return False

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

    name_tokens = set(
        name.replace("-", "_").split("_")
    )

    if not name_tokens.intersection(count_keywords):
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


# =========================================================
# 8. General column characteristics
# =========================================================

def is_constant(series: pd.Series) -> bool:
    """Determine whether a column has at most one non-missing value."""

    return series.nunique(dropna=True) <= 1


def is_binary_category(series: pd.Series) -> bool:
    """Determine whether a column contains exactly two unique values."""

    return series.nunique(dropna=True) == 2


def is_high_cardinality(series: pd.Series) -> bool:
    """Identify columns with many unique values relative to row count."""

    unique_count = series.nunique(dropna=True)
    row_count = len(series)

    if row_count == 0:
        return False

    threshold = max(50, row_count * 0.05)

    return unique_count > threshold


# =========================================================
# 9. Semantic column classification
# =========================================================

def classify_column(
    column_name: str,
    series: pd.Series,
) -> str:
    """Classify a column according to its semantic role."""

    # 1. Constant columns
    if is_constant(series):
        return "constant"

    # 2. Geographic coordinate columns
    if looks_like_latitude(column_name, series):
        return "geographic_latitude"

    if looks_like_longitude(column_name, series):
        return "geographic_longitude"

    # 3. Geographic codes
    if looks_like_geographic_code(column_name, series):
        return "geographic_code"

    # 4. Identifiers
    if looks_like_identifier(column_name, series):
        return "identifier"

    # 5. Boolean columns
    if pd.api.types.is_bool_dtype(series):
        return "binary_category"

    # 6. Binary categorical columns
    if is_binary_category(series):
        if not pd.api.types.is_numeric_dtype(series):
            return "binary_category"

    # 7. Datetime columns
    if looks_like_datetime(series):
        return "datetime"

    # 8. Year columns
    if looks_like_year(series):
        return "year"

    # 9. Month columns
    if looks_like_month(column_name, series):
        return "temporal_component"

    # 10. Quarter columns
    if looks_like_quarter(column_name, series):
        return "temporal_component"

    # 11. Numeric counts
    if looks_like_count(column_name, series):
        return "count"

    # 12. Numeric measurements
    if pd.api.types.is_numeric_dtype(series):
        return "numeric_measure"

    # 13. String and categorical columns
    if (
        pd.api.types.is_string_dtype(series)
        or isinstance(series.dtype, pd.CategoricalDtype)
        or pd.api.types.is_object_dtype(series)
    ):
        if is_high_cardinality(series):
            return "high_cardinality_categorical"

        return "categorical"

    return "unknown"


# =========================================================
# 10. Analyze a complete dataset
# =========================================================

def analyze_columns(
    df: pd.DataFrame,
) -> list[dict]:
    """Return semantic information for every dataset column."""

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
                    series.nunique(dropna=True)
                ),
                "missing_percentage": float(
                    series.isna().mean() * 100
                ),
            }
        )

    return results