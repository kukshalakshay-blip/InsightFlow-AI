from __future__ import annotations

import csv
from pathlib import Path
from typing import BinaryIO, TextIO

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet"}


def _get_file_name(file: object) -> str:
    """Return a safe filename from a path-like object or uploaded file."""
    name = getattr(file, "name", None)
    if not name and isinstance(file, (str, Path)):
        name = str(file)
    if not name:
        raise ValueError("The uploaded file must have a filename.")
    return str(name)


def _rewind(file: object) -> None:
    """Rewind file-like uploads before each read when possible."""
    seek = getattr(file, "seek", None)
    if callable(seek):
        seek(0)


def _read_csv_preserving_headers(file: object) -> pd.DataFrame:
    """Read CSV data while preserving duplicate and blank source headers."""
    _rewind(file)

    # Read the header separately so pandas' automatic duplicate-name
    # mangling (e.g. sales -> sales.1) does not hide source-level duplicates.
    try:
        header = pd.read_csv(file, header=None, nrows=1, dtype=str, encoding="utf-8-sig")
        _rewind(file)
        dataframe = pd.read_csv(file, encoding="utf-8-sig")
    except UnicodeDecodeError:
        _rewind(file)
        try:
            header = pd.read_csv(file, header=None, nrows=1, dtype=str, encoding="latin-1")
            _rewind(file)
            dataframe = pd.read_csv(file, encoding="latin-1")
        except Exception as exc:
            raise ValueError(f"Unable to decode CSV file: {exc}") from exc
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The uploaded file is empty.") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(f"Unable to parse CSV file: {exc}") from exc

    if header.empty:
        raise ValueError("The uploaded CSV file does not contain a header row.")

    original_columns = ["" if pd.isna(value) else str(value) for value in header.iloc[0].tolist()]
    if len(original_columns) == len(dataframe.columns):
        dataframe.columns = original_columns

    return dataframe


def load_dataset(file) -> pd.DataFrame:
    """Load CSV, Excel, JSON, or Parquet data into a pandas DataFrame.

    The input may be a Streamlit UploadedFile, a file-like object with a
    ``name`` attribute, or a filesystem path. Duplicate CSV headers are
    deliberately preserved so the validator can report them accurately.
    """
    file_name = _get_file_name(file)
    extension = Path(file_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file format '{extension or '[no extension]'}'. "
            f"Supported formats: {supported}."
        )

    try:
        if extension == ".csv":
            dataframe = _read_csv_preserving_headers(file)
        elif extension in {".xlsx", ".xls"}:
            _rewind(file)
            dataframe = pd.read_excel(file)
        elif extension == ".json":
            _rewind(file)
            dataframe = pd.read_json(file)
        else:  # .parquet
            _rewind(file)
            try:
                dataframe = pd.read_parquet(file)
            except ImportError as exc:
                raise ValueError(
                    "Parquet support requires an optional engine such as "
                    "'pyarrow' or 'fastparquet'. Install one to load this file."
                ) from exc
    except ValueError:
        raise
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise ValueError(f"Unable to read '{file_name}': {exc}") from exc
    except ImportError:
        raise
    except Exception as exc:
        raise ValueError(f"Unable to load '{file_name}': {exc}") from exc

    if not isinstance(dataframe, pd.DataFrame):
        raise ValueError(f"File '{file_name}' did not produce a tabular dataset.")

    return dataframe
