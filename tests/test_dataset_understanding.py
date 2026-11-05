import json

import pandas as pd
import pytest
from pydantic import ValidationError

from app.intelligence.dataset_understanding import (
    DatasetUnderstanding,
    build_dataset_profile,
    infer_structural_role,
)


def test_profile_contains_schema_and_aggregates_only():
    frame = pd.DataFrame({
        "customer_email": ["alice@example.com", None, "bob@example.com"],
        "sales": [10.0, 20.0, 30.0],
    })
    serialized = json.dumps(build_dataset_profile(frame))
    profile = json.loads(serialized)
    assert profile["row_count"] == 3
    assert profile["column_count"] == 2
    assert profile["columns"][0]["missing_count"] == 1
    assert profile["columns"][1]["numeric_summary"]["median"] == 20
    assert "alice@example.com" not in serialized
    assert "bob@example.com" not in serialized


def test_profile_never_sends_category_labels():
    frame = pd.DataFrame({"city": ["Dehradun", "Delhi", "Mumbai", "Dehradun"]})
    profile = json.dumps(build_dataset_profile(frame))
    assert "Dehradun" not in profile
    assert "Delhi" not in profile
    assert "Mumbai" not in profile


def test_profile_rejects_empty_dataset():
    with pytest.raises(ValueError, match="at least one row"):
        build_dataset_profile(pd.DataFrame(columns=["a"]))


def test_profile_rejects_excessive_column_count():
    with pytest.raises(ValueError, match="maximum supported"):
        build_dataset_profile(pd.DataFrame([[1, 1, 1]], columns=["a", "b", "c"]), max_columns=2)


def test_binary_and_continuous_roles_are_distinguished():
    frame = pd.DataFrame({"active": [0, 1, 1, 0], "age": [21.2, 34.1, 44.0, 55.5]})
    assert infer_structural_role(frame["active"], "active") == "binary_categorical"
    assert infer_structural_role(frame["age"], "age") == "continuous"


def test_small_numeric_scale_is_not_automatically_continuous():
    series = pd.Series([1, 2, 3, 1, 2])
    assert infer_structural_role(series, "severity_level") == "ordinal_categorical"


def test_understanding_rejects_duplicate_column_mappings():
    payload = {
        "domain": "commerce", "dataset_kind": "sales records", "confidence": 0.9,
        "rationale": "Sales and product fields indicate commerce.",
        "column_meanings": [
            {"column": "sales", "semantic_role": "revenue", "description": "Sales amount", "confidence": 0.9},
            {"column": "sales", "semantic_role": "profit", "description": "Profit amount", "confidence": 0.5},
        ],
    }
    with pytest.raises(ValidationError, match="duplicate column"):
        DatasetUnderstanding.model_validate(payload)


def test_understanding_rejects_unknown_domain():
    payload = {
        "domain": "random_domain", "dataset_kind": "records", "confidence": 0.5,
        "rationale": "Unclear dataset.",
    }
    with pytest.raises(ValidationError):
        DatasetUnderstanding.model_validate(payload)
