import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def load_dataset(file) -> pd.DataFrame:
    """
    Load a CSV or Excel file into a Pandas DataFrame.
    """

    file_name = file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(file)

    if file_name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)

    raise ValueError(
        "Unsupported file format. Please upload a CSV or Excel file."
    )