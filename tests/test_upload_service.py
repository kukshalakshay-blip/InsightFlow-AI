from io import BytesIO

import pandas as pd
import pytest

from app.services.upload_service import process_uploaded_dataset


# ==========================================================
# TEST FILE HELPER
# ==========================================================

def create_csv_file(
    content: str,
    filename: str = "test.csv",
) -> BytesIO:
    """Create a file-like CSV object for testing."""

    file = BytesIO(content.encode("utf-8"))
    file.name = filename

    return file


# ==========================================================
# SUCCESSFUL UPLOADS
# ==========================================================

def test_valid_csv_upload_succeeds():
    uploaded_file = create_csv_file(
        "sales,profit\n100,20\n200,40\n"
    )

    result = process_uploaded_dataset(uploaded_file)

    assert result.is_successful
    assert isinstance(result.dataframe, pd.DataFrame)
    assert result.dataframe.shape == (2, 2)
    assert result.validation is not None
    assert result.validation.is_valid
    assert result.error is None


def test_valid_csv_preserves_column_names():
    uploaded_file = create_csv_file(
        "customer_id,total_sales\n1,100\n2,200\n"
    )

    result = process_uploaded_dataset(uploaded_file)

    assert result.is_successful
    assert result.dataframe is not None
    assert list(result.dataframe.columns) == [
        "customer_id",
        "total_sales",
    ]


def test_valid_csv_preserves_numeric_values():
    uploaded_file = create_csv_file(
        "quantity,revenue\n2,150.5\n4,300.0\n"
    )

    result = process_uploaded_dataset(uploaded_file)

    assert result.is_successful
    assert result.dataframe is not None
    assert result.dataframe["quantity"].tolist() == [2, 4]
    assert result.dataframe["revenue"].tolist() == [
        150.5,
        300.0,
    ]


# ==========================================================
# VALIDATION FAILURES
# ==========================================================

def test_empty_csv_is_rejected():
    uploaded_file = create_csv_file(
        "sales,profit\n"
    )

    result = process_uploaded_dataset(uploaded_file)

    assert not result.is_successful
    assert result.dataframe is None
    assert result.validation is not None
    assert not result.validation.is_valid
    assert result.validation.errors


def test_duplicate_column_names_are_rejected():
    uploaded_file = create_csv_file(
        "sales,sales\n100,200\n"
    )

    result = process_uploaded_dataset(uploaded_file)

    assert not result.is_successful
    assert result.dataframe is None
    assert result.validation is not None
    assert not result.validation.is_valid


# ==========================================================
# VALIDATION WARNINGS
# ==========================================================

def test_missing_values_produce_warnings_without_rejection():
    uploaded_file = create_csv_file(
        "sales,profit\n100,\n200,40\n"
    )

    result = process_uploaded_dataset(uploaded_file)

    assert result.is_successful
    assert result.validation is not None
    assert result.validation.is_valid
    assert result.validation.warnings


def test_duplicate_rows_produce_warning_without_rejection():
    uploaded_file = create_csv_file(
        "sales,profit\n100,20\n100,20\n"
    )

    result = process_uploaded_dataset(uploaded_file)

    assert result.is_successful
    assert result.validation is not None
    assert result.validation.is_valid

    assert any(
        "duplicate rows" in warning.lower()
        for warning in result.validation.warnings
    )


# ==========================================================
# FILE FORMAT AND LOADING ERRORS
# ==========================================================

def test_unsupported_file_format_returns_error():
    uploaded_file = create_csv_file(
        "sales\n100\n",
        filename="test.txt",
    )

    result = process_uploaded_dataset(uploaded_file)

    assert not result.is_successful
    assert result.dataframe is None
    assert result.validation is None
    assert result.error is not None
    assert "Unsupported file format" in result.error


def test_malformed_csv_returns_loading_error():
    uploaded_file = create_csv_file(
        'sales,profit\n100,"unterminated\n'
    )

    result = process_uploaded_dataset(uploaded_file)

    assert not result.is_successful
    assert result.dataframe is None
    assert result.validation is None
    assert result.error is not None


def test_missing_filename_returns_loading_error():
    uploaded_file = BytesIO(
        b"sales,profit\n100,20\n"
    )

    result = process_uploaded_dataset(uploaded_file)

    assert not result.is_successful
    assert result.dataframe is None
    assert result.validation is None
    assert result.error is not None