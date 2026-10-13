from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def load_dataset(file) -> pd.DataFrame:
    """Load a supported dataset while preserving duplicate CSV headers."""

    file_name = getattr(file, "name", "")

    if not file_name:
        raise ValueError("The uploaded file must have a filename.")

    extension = Path(file_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported file format. Please upload a CSV or Excel file."
        )

    if extension == ".csv":
        # Read the original header separately before pandas renames duplicates.
        file.seek(0)
        original_header = pd.read_csv(
            file,
            header=None,
            nrows=1,
            dtype=str,
        )

        # Load the complete dataset normally.
        file.seek(0)
        dataframe = pd.read_csv(file)

        # Restore original column names only when duplicates exist.
        if not original_header.empty:
            original_columns = original_header.iloc[0].tolist()

            if (
                len(original_columns) == len(dataframe.columns)
                and len(set(original_columns)) < len(original_columns)
            ):
                dataframe.columns = original_columns

        return dataframe

    # Excel loading remains unchanged.
    return pd.read_excel(file)