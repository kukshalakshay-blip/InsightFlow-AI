import pandas as pd
import pytest

from app.services.profiler import profile_dataset


def test_profile_reports_correct_dataset_dimensions():
    """The profiler should report the correct number of rows and columns."""

    df = pd.DataFrame({
        "sales": [100, 200, 300],
        "profit": [20, 40, 60],
    })

    profile = profile_dataset(df)

    assert profile["rows"] == 3
    assert profile["columns"] == 2


def test_profile_detects_numeric_and_categorical_columns():
    """Columns should be classified according to their data types."""

    df = pd.DataFrame({
        "sales": [100, 200, 300],
        "region": ["North", "South", "North"],
        "is_profitable": [True, False, True],
    })

    profile = profile_dataset(df)

    assert profile["numeric_columns"] == ["sales"]
    assert profile["categorical_columns"] == ["region", "is_profitable"]


def test_profile_counts_missing_cells():
    """Missing values should be counted across the entire dataset."""

    df = pd.DataFrame({
        "sales": [100, None, 300],
        "profit": [None, 40, 60],
    })

    profile = profile_dataset(df)

    assert profile["missing_cells"] == 2
    assert profile["missing_percentage"] == pytest.approx(33.3333333)


def test_profile_counts_duplicate_rows():
    """Repeated records should be counted correctly."""

    df = pd.DataFrame({
        "sales": [100, 200, 100],
        "profit": [20, 40, 20],
    })

    profile = profile_dataset(df)

    assert profile["duplicate_rows"] == 1


def test_profile_calculates_column_missing_statistics():
    """Each column should have its own missing-value statistics."""

    df = pd.DataFrame({
        "sales": [100, None, 300, 400],
        "profit": [20, 40, 60, 80],
    })

    profile = profile_dataset(df)

    sales_profile = profile["column_profiles"]["sales"]
    profit_profile = profile["column_profiles"]["profit"]

    assert sales_profile["missing_count"] == 1
    assert sales_profile["missing_percentage"] == pytest.approx(25.0)

    assert profit_profile["missing_count"] == 0
    assert profit_profile["missing_percentage"] == pytest.approx(0.0)


def test_profile_counts_unique_values_correctly():
    """Missing values should not count as unique values."""

    df = pd.DataFrame({
        "region": ["North", "South", "North", None],
    })

    profile = profile_dataset(df)
    region_profile = profile["column_profiles"]["region"]

    assert region_profile["unique_values"] == 2
    assert region_profile["unique_percentage"] == pytest.approx(50.0)


def test_profile_reports_column_data_types():
    """Each column profile should report its pandas data type."""

    df = pd.DataFrame({
        "sales": [100, 200, 300],
        "region": ["North", "South", "East"],
    })

    profile = profile_dataset(df)

    assert profile["column_profiles"]["sales"]["dtype"] == "int64"
    assert profile["column_profiles"]["region"]["dtype"] == str(
        df["region"].dtype
    )

def test_profile_handles_empty_dataframe():
    """An empty dataframe should not cause division-by-zero errors."""

    df = pd.DataFrame()

    profile = profile_dataset(df)

    assert profile["rows"] == 0
    assert profile["columns"] == 0
    assert profile["missing_cells"] == 0
    assert profile["missing_percentage"] == 0
    assert profile["duplicate_rows"] == 0
    assert profile["column_profiles"] == {}


def test_profile_handles_columns_without_rows():
    """Columns with no records should have zero unique percentage."""

    df = pd.DataFrame(columns=["sales", "region"])

    profile = profile_dataset(df)

    assert profile["rows"] == 0
    assert profile["columns"] == 2
    assert profile["column_profiles"]["sales"]["unique_percentage"] == 0
    assert profile["column_profiles"]["region"]["unique_percentage"] == 0