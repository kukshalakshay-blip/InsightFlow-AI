import hashlib
import json

import pandas as pd


def generate_dataset_signature(
    df: pd.DataFrame,
    dataset_name: str = "dataset",
) -> str:
    """
    Generate a signature representing a dataset's identity,
    schema, and contents.

    The signature changes when the dataset name, column names,
    data types, index, or cell values change.
    """

    schema = {
        "dataset_name": dataset_name,
        "columns": [str(column) for column in df.columns],
        "dtypes": [str(dtype) for dtype in df.dtypes],
        "shape": list(df.shape),
    }

    schema_bytes = json.dumps(
        schema,
        sort_keys=True,
        default=str,
    ).encode("utf-8")

    content_hash = pd.util.hash_pandas_object(
        df,
        index=True,
        categorize=True,
    ).to_numpy().tobytes()

    digest = hashlib.sha256()
    digest.update(schema_bytes)
    digest.update(content_hash)

    return digest.hexdigest()