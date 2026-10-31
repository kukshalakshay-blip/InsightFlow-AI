import numpy as np
import pandas as pd
import pytest

from app.services.profiler import profile_dataset


def test_profile_reports_correct_dataset_dimensions():
    df = pd.DataFrame({"sales": [100, 200, 300], "profit": [20, 40, 60]})
    profile = profile_dataset(df)
    assert profile["rows"] == 3
    assert profile["columns"] == 2


def test_profile_detects_numeric_and_categorical_columns():
    df = pd.DataFrame({
        "sales": [100, 200, 300],
        "region": ["North", "South", "North"],
        "is_profitable": [True, False, True],
    })
    profile = profile_dataset(df)
    assert profile["numeric_columns"] == ["sales"]
    assert profile["categorical_columns"] == ["region", "is_profitable"]


def test_profile_counts_missing_cells():
    df = pd.DataFrame({"sales": [100, None, 300], "profit": [None, 40, 60]})
    profile = profile_dataset(df)
    assert profile["missing_cells"] == 2
    assert profile["missing_percentage"] == pytest.approx(33.3333333)


def test_profile_counts_duplicate_rows():
    df = pd.DataFrame({"sales": [100, 200, 100], "profit": [20, 40, 20]})
    assert profile_dataset(df)["duplicate_rows"] == 1


def test_profile_calculates_column_missing_statistics():
    df = pd.DataFrame({"sales": [100, None, 300, 400], "profit": [20, 40, 60, 80]})
    profile = profile_dataset(df)
    assert profile["column_profiles"]["sales"]["missing_count"] == 1
    assert profile["column_profiles"]["sales"]["missing_percentage"] == 25
    assert profile["column_profiles"]["profit"]["missing_percentage"] == 0


def test_profile_counts_unique_values_correctly():
    df = pd.DataFrame({"region": ["North", "South", "North", None]})
    item = profile_dataset(df)["column_profiles"]["region"]
    assert item["unique_values"] == 2
    assert item["unique_percentage"] == 50


def test_profile_reports_column_data_types():
    df = pd.DataFrame({"sales": [100, 200, 300], "region": ["N", "S", "E"]})
    profile = profile_dataset(df)
    assert profile["column_profiles"]["sales"]["dtype"] == "int64"
    assert profile["column_profiles"]["region"]["dtype"] == str(df["region"].dtype)


def test_profile_handles_empty_dataframe():
    profile = profile_dataset(pd.DataFrame())
    assert profile["rows"] == profile["columns"] == 0
    assert profile["missing_cells"] == profile["missing_percentage"] == 0
    assert profile["duplicate_rows"] == 0
    assert profile["column_profiles"] == {}


def test_profile_handles_columns_without_rows():
    profile = profile_dataset(pd.DataFrame(columns=["sales", "region"]))
    assert profile["rows"] == 0
    assert profile["columns"] == 2
    assert profile["column_profiles"]["sales"]["unique_percentage"] == 0


def test_profile_supports_pandas_string_extension_dtype():
    df = pd.DataFrame({
        "region": pd.Series(["North", "South", "North"], dtype="string"),
        "sales": [100, 200, 300],
    })
    profile = profile_dataset(df)
    assert profile["categorical_columns"] == ["region"]
    assert profile["numeric_columns"] == ["sales"]


def test_numeric_statistics_are_reported():
    profile = profile_dataset(pd.DataFrame({"sales": [10, 20, 30, 40]}))
    stats = profile["column_profiles"]["sales"]["numeric_statistics"]
    assert stats["count"] == 4
    assert stats["mean"] == 25
    assert stats["median"] == 25
    assert stats["min"] == 10
    assert stats["q1"] == 17.5
    assert stats["q3"] == 32.5
    assert stats["max"] == 40


def test_non_finite_values_are_excluded_from_numeric_statistics():
    profile = profile_dataset(pd.DataFrame({"sales": [10.0, np.inf, -np.inf, np.nan, 20.0]}))
    item = profile["column_profiles"]["sales"]
    assert item["non_finite_count"] == 2
    assert item["finite_count"] == 2
    assert item["numeric_statistics"]["mean"] == 15


def test_numeric_statistics_return_none_for_all_invalid_values():
    profile = profile_dataset(pd.DataFrame({"x": [np.inf, -np.inf, np.nan]}))
    stats = profile["column_profiles"]["x"]["numeric_statistics"]
    assert stats["count"] == 0
    assert stats["mean"] is None
    assert stats["std"] is None


def test_boolean_columns_are_not_treated_as_numeric_measures():
    profile = profile_dataset(pd.DataFrame({"flag": [True, False, True]}))
    assert "flag" not in profile["numeric_columns"]
    assert "flag" in profile["categorical_columns"]


def test_datetime_columns_receive_date_range_profile():
    df = pd.DataFrame({"date": pd.to_datetime(["2025-01-02", "2025-01-01", None])})
    profile = profile_dataset(df)
    assert profile["datetime_columns"] == ["date"]
    stats = profile["column_profiles"]["date"]["datetime_statistics"]
    assert stats["min"].startswith("2025-01-01")
    assert stats["max"].startswith("2025-01-02")


def test_profile_reports_row_quality_and_memory():
    df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", "z"]})
    profile = profile_dataset(df)
    assert profile["rows_with_missing"] == 1
    assert profile["complete_rows"] == 2
    assert profile["memory_usage_bytes"] > 0


def test_categorical_profile_reports_top_values():
    profile = profile_dataset(pd.DataFrame({"region": ["N", "N", "S", "E", None]}))
    assert profile["column_profiles"]["region"]["top_values"][0] == {
        "value": "N", "count": 2
    }


def test_profile_rejects_non_dataframe_input():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        profile_dataset([1, 2, 3])


def test_profile_rejects_duplicate_column_names():
    df = pd.DataFrame([[1, 2]], columns=["value", "value"])
    with pytest.raises(ValueError, match="unique"):
        profile_dataset(df)


def test_non_numeric_object_columns_are_not_given_numeric_statistics():
    profile = profile_dataset(pd.DataFrame({"sales": ["10", "twenty", "30"]}))
    assert "numeric_statistics" not in profile["column_profiles"]["sales"]
