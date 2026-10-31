import numpy as np
import pandas as pd
import pytest

from app.services.data_validator import ValidationResult, validate_dataset


def test_valid_dataset_passes_validation():
    df = pd.DataFrame({"sales": [100, 200, 300], "profit": [20, 40, 60]})
    result = validate_dataset(df)
    assert result.is_valid is True
    assert result.errors == []
    assert result.warnings == []


def test_empty_dataframe_is_invalid():
    result = validate_dataset(pd.DataFrame())
    assert result.is_valid is False
    assert "The dataset contains no rows." in result.errors
    assert "The dataset contains no columns." in result.errors


def test_dataset_with_columns_but_no_rows_is_invalid():
    result = validate_dataset(pd.DataFrame(columns=["sales", "profit"]))
    assert result.is_valid is False
    assert "The dataset contains no rows." in result.errors


def test_dataset_with_rows_but_no_columns_is_invalid():
    result = validate_dataset(pd.DataFrame(index=range(3)))
    assert result.is_valid is False
    assert "The dataset contains no columns." in result.errors


def test_duplicate_column_names_are_detected():
    df = pd.DataFrame([[1, 2], [3, 4]], columns=["sales", "sales"])
    result = validate_dataset(df)
    assert result.is_valid is False
    assert any("Duplicate column names" in error for error in result.errors)


def test_blank_column_names_are_rejected():
    result = validate_dataset(pd.DataFrame([[1, 2]], columns=["sales", "  "]))
    assert not result.is_valid
    assert any("Blank or whitespace-only" in error for error in result.errors)


def test_missing_values_below_20_percent_do_not_trigger_warning():
    df = pd.DataFrame({"sales": [100, 200, 300, 400, 500],
                       "profit": [10, 20, None, 40, 50]})
    result = validate_dataset(df)
    assert not any("missing" in warning.lower() for warning in result.warnings)


def test_missing_values_at_20_percent_trigger_warning():
    result = validate_dataset(pd.DataFrame({"sales": [100, 200, 300, 400, None]}))
    assert any("20%" in warning for warning in result.warnings)


def test_missing_values_at_50_percent_trigger_warning():
    result = validate_dataset(pd.DataFrame({"sales": [100, None]}))
    assert any("50%" in warning for warning in result.warnings)


def test_missing_values_above_50_percent_trigger_highest_warning():
    result = validate_dataset(pd.DataFrame({"x": [None, None, 1]}))
    assert any("50%" in warning for warning in result.warnings)


def test_duplicate_rows_are_reported_as_warning():
    df = pd.DataFrame({"sales": [100, 200, 100], "profit": [20, 40, 20]})
    result = validate_dataset(df)
    assert result.is_valid is True
    assert "1 duplicate rows detected." in result.warnings


def test_dataset_without_duplicate_rows_has_no_duplicate_warning():
    df = pd.DataFrame({"sales": [100, 200, 300], "profit": [20, 40, 60]})
    result = validate_dataset(df)
    assert not any("duplicate rows" in warning.lower() for warning in result.warnings)


def test_multiple_validation_errors_are_reported():
    result = validate_dataset(pd.DataFrame(columns=["sales", "sales"]))
    assert not result.is_valid
    assert "The dataset contains no rows." in result.errors
    assert any("Duplicate column names" in error for error in result.errors)


def test_all_missing_column_is_reported():
    df = pd.DataFrame({"sales": [1, 2, 3], "empty": [None, None, None]})
    result = validate_dataset(df)
    assert any("only missing values" in warning for warning in result.warnings)


def test_positive_infinity_is_reported():
    result = validate_dataset(pd.DataFrame({"sales": [1.0, np.inf, 3.0]}))
    assert any("Infinite numeric values" in warning for warning in result.warnings)
    assert "+inf: 1" in next(w for w in result.warnings if "Infinite" in w)


def test_negative_infinity_is_reported():
    result = validate_dataset(pd.DataFrame({"sales": [1.0, -np.inf, 3.0]}))
    assert "-inf: 1" in next(w for w in result.warnings if "Infinite" in w)


def test_positive_and_negative_infinity_counts_are_reported():
    result = validate_dataset(pd.DataFrame({"sales": [np.inf, -np.inf, 3.0]}))
    warning = next(w for w in result.warnings if "Infinite" in w)
    assert "(+inf: 1, -inf: 1)" in warning


def test_missing_numeric_values_are_not_counted_as_infinity():
    result = validate_dataset(pd.DataFrame({"sales": [1.0, np.nan, 3.0]}))
    assert not any("Infinite" in warning for warning in result.warnings)


def test_boolean_columns_are_not_treated_as_numeric_infinity_columns():
    result = validate_dataset(pd.DataFrame({"flag": [True, False, True]}))
    assert not any("Infinite" in warning for warning in result.warnings)


def test_constant_column_is_reported():
    result = validate_dataset(pd.DataFrame({"sales": [5, 5, 5]}))
    assert any("Constant columns" in warning for warning in result.warnings)


def test_non_constant_column_is_not_reported_as_constant():
    result = validate_dataset(pd.DataFrame({"sales": [5, 6, 5]}))
    assert not any("Constant columns" in warning for warning in result.warnings)


def test_duplicate_column_labels_do_not_crash_missing_checks():
    df = pd.DataFrame([[1, None], [2, 3]], columns=["x", "x"])
    result = validate_dataset(df)
    assert isinstance(result, ValidationResult)
    assert not result.is_valid


def test_pandas_string_dtype_is_supported():
    df = pd.DataFrame({"region": pd.Series(["North", "South"], dtype="string")})
    result = validate_dataset(df)
    assert result.is_valid
    assert result.errors == []


def test_categorical_dtype_is_supported():
    df = pd.DataFrame({"region": pd.Series(["North", "South"], dtype="category")})
    result = validate_dataset(df)
    assert result.is_valid


def test_datetime_dtype_is_supported():
    df = pd.DataFrame({"date": pd.to_datetime(["2025-01-01", "2025-01-02"])})
    result = validate_dataset(df)
    assert result.is_valid


def test_non_dataframe_input_raises_clear_type_error():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        validate_dataset([{"sales": 10}])


def test_warning_conditions_do_not_make_dataset_invalid():
    df = pd.DataFrame({"sales": [1.0, np.inf, 1.0], "notes": [None, None, "x"]})
    result = validate_dataset(df)
    assert result.is_valid is True
    assert result.warnings
