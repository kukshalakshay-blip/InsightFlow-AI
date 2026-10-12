import pandas as pd

from app.services.dataset_signature import (
    generate_dataset_signature,
)


def test_identical_datasets_have_identical_signatures():
    df1 = pd.DataFrame({
        "sales": [100, 200, 300],
        "profit": [10, 20, 30],
    })

    df2 = df1.copy()

    assert generate_dataset_signature(
        df1,
        "sales.csv",
    ) == generate_dataset_signature(
        df2,
        "sales.csv",
    )


def test_changed_values_change_signature():
    df1 = pd.DataFrame({
        "sales": [100, 200, 300],
    })

    df2 = pd.DataFrame({
        "sales": [100, 200, 900],
    })

    assert generate_dataset_signature(
        df1,
        "sales.csv",
    ) != generate_dataset_signature(
        df2,
        "sales.csv",
    )


def test_changed_dataset_name_changes_signature():
    df = pd.DataFrame({
        "sales": [100, 200, 300],
    })

    assert generate_dataset_signature(
        df,
        "sales.csv",
    ) != generate_dataset_signature(
        df,
        "revenue.csv",
    )


def test_changed_column_names_change_signature():
    df1 = pd.DataFrame({
        "sales": [100, 200],
    })

    df2 = pd.DataFrame({
        "revenue": [100, 200],
    })

    assert generate_dataset_signature(
        df1,
    ) != generate_dataset_signature(
        df2,
    )


def test_changed_dtypes_change_signature():
    df1 = pd.DataFrame({
        "value": [1, 2, 3],
    })

    df2 = pd.DataFrame({
        "value": [1.0, 2.0, 3.0],
    })

    assert generate_dataset_signature(
        df1,
    ) != generate_dataset_signature(
        df2,
    )


def test_changed_row_order_changes_signature():
    df1 = pd.DataFrame({
        "sales": [100, 200, 300],
    })

    df2 = pd.DataFrame({
        "sales": [300, 200, 100],
    })

    assert generate_dataset_signature(
        df1,
    ) != generate_dataset_signature(
        df2,
    )


def test_changed_index_changes_signature():
    df1 = pd.DataFrame({
        "sales": [100, 200, 300],
    })

    df2 = df1.copy()
    df2.index = [10, 20, 30]

    assert generate_dataset_signature(
        df1,
    ) != generate_dataset_signature(
        df2,
    )


def test_empty_dataframes_have_stable_signatures():
    df1 = pd.DataFrame(columns=["sales", "profit"])
    df2 = df1.copy()

    assert generate_dataset_signature(
        df1,
    ) == generate_dataset_signature(
        df2,
    )


def test_empty_dataframes_with_different_columns_differ():
    df1 = pd.DataFrame(columns=["sales"])
    df2 = pd.DataFrame(columns=["profit"])

    assert generate_dataset_signature(
        df1,
    ) != generate_dataset_signature(
        df2,
    )