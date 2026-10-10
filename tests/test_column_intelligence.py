import pandas as pd
import pytest

from app.services.column_intelligence import (
    analyze_columns,
    classify_column,
    is_binary_category,
    is_constant,
    is_high_cardinality,
    looks_like_count,
    looks_like_datetime,
    looks_like_geographic_code,
    looks_like_identifier,
    looks_like_month,
    looks_like_quarter,
    looks_like_year,
)


# =========================================================
# 1. Date detection
# =========================================================

def test_detects_datetime_column():
    series = pd.Series([
        "2025-01-15",
        "2025-02-15",
        "2025-03-15",
    ])

    assert bool(looks_like_datetime(series)) is True


def test_numeric_values_are_not_treated_as_dates():
    series = pd.Series([20240101, 20240201, 20240301])

    assert bool(looks_like_datetime(series)) is False


def test_empty_series_is_not_datetime():
    series = pd.Series([], dtype="object")

    assert bool(looks_like_datetime(series)) is False


def test_datetime_detection_handles_invalid_values():
    series = pd.Series([
        "2025-01-15",
        "2025-02-15",
        "not-a-date",
        "2025-04-15",
        "2025-05-15",
    ])

    assert bool(looks_like_datetime(series)) is True


# =========================================================
# 2. Year detection
# =========================================================

def test_detects_year_column():
    series = pd.Series([2020, 2021, 2022, 2023])

    assert bool(looks_like_year(series)) is True


def test_ordinary_measurements_are_not_years():
    series = pd.Series([10, 20, 30, 40])

    assert bool(looks_like_year(series)) is False


def test_year_detection_ignores_missing_values():
    series = pd.Series([2020, 2021, None, 2023])

    assert bool(looks_like_year(series)) is True


# =========================================================
# 3. Month and quarter detection
# =========================================================

def test_detects_month_number():
    series = pd.Series([1, 2, 3, 4, 5, 6])

    assert bool(looks_like_month("Month", series)) is True


def test_month_detection_rejects_invalid_month_numbers():
    series = pd.Series([1, 2, 3, 13])

    assert bool(looks_like_month("month", series)) is False


def test_month_detection_requires_recognized_column_name():
    series = pd.Series([1, 2, 3, 4])

    assert bool(looks_like_month("sales", series)) is False


def test_detects_quarter_number():
    series = pd.Series([1, 2, 3, 4])

    assert bool(looks_like_quarter("quarter", series)) is True


def test_quarter_detection_rejects_invalid_values():
    series = pd.Series([1, 2, 3, 5])

    assert bool(looks_like_quarter("quarter", series)) is False


# =========================================================
# 4. Identifier detection
# =========================================================

@pytest.mark.parametrize(
    "column_name",
    [
        "id",
        "customer_id",
        "order_id",
        "transaction_id",
        "product_id",
        "user_id",
        "Customer_ID",
    ],
)
def test_recognizes_identifier_names(column_name):
    series = pd.Series([101, 102, 103])

    assert looks_like_identifier(column_name, series) is True


def test_recognizes_id_suffix():
    series = pd.Series([101, 102, 103])

    assert looks_like_identifier("invoiceid", series) is True


def test_does_not_misclassify_ordinary_column_as_identifier():
    series = pd.Series([100, 200, 300])

    assert looks_like_identifier("sales", series) is False


# =========================================================
# 5. Geographic codes
# =========================================================

@pytest.mark.parametrize(
    "column_name",
    [
        "postcode",
        "postal_code",
        "postalcode",
        "zip",
        "zipcode",
        "zip_code",
    ],
)
def test_recognizes_geographic_code_names(column_name):
    series = pd.Series(["248001", "248002", "248003"])

    assert looks_like_geographic_code(column_name, series) is True


def test_ordinary_column_is_not_geographic_code():
    series = pd.Series([100, 200, 300])

    assert looks_like_geographic_code("sales", series) is False


# =========================================================
# 6. Count detection
# =========================================================

@pytest.mark.parametrize(
    "column_name",
    [
        "count",
        "quantity",
        "qty",
        "rooms",
        "bedrooms",
        "bathrooms",
        "cars",
        "customer_count",
    ],
)
def test_recognizes_nonnegative_integer_counts(column_name):
    series = pd.Series([1, 2, 3, 4])

    assert looks_like_count(column_name, series) is True


def test_count_detection_rejects_negative_values():
    series = pd.Series([1, 2, -1, 4])

    assert looks_like_count("quantity", series) is False


def test_count_detection_rejects_fractional_values():
    series = pd.Series([1, 2, 3.5, 4])

    assert looks_like_count("quantity", series) is False


def test_count_detection_rejects_non_count_column_names():
    series = pd.Series([1, 2, 3])

    assert looks_like_count("sales", series) is False


# =========================================================
# 7. General column characteristics
# =========================================================

def test_detects_constant_column():
    series = pd.Series(["North", "North", None, "North"])

    assert is_constant(series) is True


def test_empty_series_is_constant():
    series = pd.Series([], dtype="object")

    assert is_constant(series) is True


def test_detects_binary_category():
    series = pd.Series(["Yes", "No", "Yes", "No"])

    assert is_binary_category(series) is True


def test_missing_values_do_not_create_extra_categories():
    series = pd.Series(["Yes", "No", None])

    assert is_binary_category(series) is True


def test_detects_high_cardinality_column():
    series = pd.Series(range(1000))

    assert is_high_cardinality(series) is True


def test_empty_series_is_not_high_cardinality():
    series = pd.Series([], dtype="object")

    assert is_high_cardinality(series) is False


# =========================================================
# 8. Semantic classification
# =========================================================

@pytest.mark.parametrize(
    ("column_name", "values", "expected"),
    [
        ("Order_ID", [101, 102, 103], "identifier"),
        ("Postal_Code", ["248001", "248002", "248003"], "geographic_code"),
        ("Order_Date", ["2025-01-15", "2025-02-15", "2025-03-15"], "datetime"),
        ("Year", [2020, 2021, 2022], "year"),
        ("Month", [1, 2, 3], "temporal_component"),
        ("Quarter", [1, 2, 3], "temporal_component"),
        ("Quantity", [1, 2, 3], "count"),
        ("Sales", [100.5, 200.5, 300.5], "numeric_measure"),
        ("Region", ["North", "South", "West"], "categorical"),
        ("Status", ["Open", "Closed", "Open"], "binary_category"),
    ],
)
def test_classifies_columns_correctly(column_name, values, expected):
    series = pd.Series(values)

    assert classify_column(column_name, series) == expected


def test_constant_column_takes_priority():
    series = pd.Series([100, 100, 100])

    assert classify_column("sales", series) == "constant"


def test_boolean_column_is_binary_category():
    series = pd.Series([True, False, True])

    assert classify_column("is_profitable", series) == "binary_category"


# =========================================================
# 9. Full dataset analysis
# =========================================================

def test_analyze_columns_returns_expected_information():
    df = pd.DataFrame({
        "Sales": [100, 200, 300],
        "Region": ["North", "South", "North"],
        "Order_Date": [
            "2025-01-01",
            "2025-02-01",
            "2025-03-01",
        ],
    })

    results = analyze_columns(df)

    assert len(results) == 3

    sales_result = next(
        item for item in results
        if item["column"] == "Sales"
    )

    assert sales_result["semantic_type"] == "numeric_measure"
    assert sales_result["unique_count"] == 3
    assert sales_result["missing_percentage"] == pytest.approx(0.0)


def test_analyze_columns_reports_missing_percentage():
    df = pd.DataFrame({
        "Sales": [100, None, 300, 400],
    })

    results = analyze_columns(df)

    assert results[0]["missing_percentage"] == pytest.approx(25.0)


def test_analyze_empty_dataframe():
    df = pd.DataFrame()

    assert analyze_columns(df) == []