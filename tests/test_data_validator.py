import pandas as pd

from app.services.data_validator import validate_dataset


def test_valid_dataset_passes_validation():
    df = pd.DataFrame({
        "sales": [100, 200, 300],
        "profit": [20, 40, 60],
    })

    result = validate_dataset(df)

    assert result.is_valid is True
    assert result.errors == []
    assert result.warnings == []


def test_empty_dataframe_is_invalid():
    df = pd.DataFrame()

    result = validate_dataset(df)

    assert result.is_valid is False
    assert "The dataset contains no rows." in result.errors
    assert "The dataset contains no columns." in result.errors


def test_dataset_with_columns_but_no_rows_is_invalid():
    df = pd.DataFrame(columns=["sales", "profit"])

    result = validate_dataset(df)

    assert result.is_valid is False
    assert "The dataset contains no rows." in result.errors


def test_dataset_with_rows_but_no_columns_is_invalid():
    df = pd.DataFrame(index=range(3))

    result = validate_dataset(df)

    assert result.is_valid is False
    assert "The dataset contains no columns." in result.errors


def test_duplicate_column_names_are_detected():
    df = pd.DataFrame(
        [[100, 200], [300, 400]],
        columns=["sales", "sales"],
    )

    result = validate_dataset(df)

    assert result.is_valid is False
    assert any("Duplicate column names" in error for error in result.errors)


def test_missing_values_below_20_percent_do_not_trigger_warning():
    df = pd.DataFrame({
        "sales": [100, 200, 300, 400, 500],
        "profit": [10, 20, None, 40, 50],
    })

    result = validate_dataset(df)

    assert not any("missing" in warning.lower() for warning in result.warnings)


def test_missing_values_at_20_percent_trigger_warning():
    df = pd.DataFrame({
        "sales": [100, 200, 300, 400, None],
    })

    result = validate_dataset(df)

    assert any("20%" in warning for warning in result.warnings)


def test_missing_values_at_50_percent_trigger_warning():
    df = pd.DataFrame({
        "sales": [100, None],
    })

    result = validate_dataset(df)

    assert any("50%" in warning for warning in result.warnings)


def test_duplicate_rows_are_reported_as_warning():
    df = pd.DataFrame({
        "sales": [100, 200, 100],
        "profit": [20, 40, 20],
    })

    result = validate_dataset(df)

    assert result.is_valid is True
    assert "1 duplicate rows detected." in result.warnings


def test_dataset_without_duplicate_rows_has_no_duplicate_warning():
    df = pd.DataFrame({
        "sales": [100, 200, 300],
        "profit": [20, 40, 60],
    })

    result = validate_dataset(df)

    assert not any("duplicate rows" in warning.lower() for warning in result.warnings)


def test_multiple_validation_errors_are_reported():
    df = pd.DataFrame(columns=["sales", "sales"])

    result = validate_dataset(df)

    assert result.is_valid is False
    assert "The dataset contains no rows." in result.errors
    assert any("Duplicate column names" in error for error in result.errors)