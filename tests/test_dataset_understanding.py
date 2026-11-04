import json

import pandas as pd
import pytest
from pydantic import ValidationError

from app.intelligence.dataset_understanding import (
    DatasetUnderstanding,
    build_dataset_profile,
)


def test_profile_contains_schema_and_aggregates_only():
    frame = pd.DataFrame({
        "customer_email": ["alice@example.com", None, "bob@example.com"],
        "sales": [10.0, 20.0, 30.0],
    })
    profile = build_dataset_profile(frame)
    serialized = json.dumps(profile)

    assert profile["row_count"] == 3
    assert profile["column_count"] == 2
    assert profile["columns"][0]["missing_count"] == 1
    assert profile["columns"][1]["numeric_summary"]["median"] == 20
    assert "alice@example.com" not in serialized
    assert "bob@example.com" not in serialized


def test_profile_rejects_empty_dataset():
    with pytest.raises(ValueError, match="at least one row"):
        build_dataset_profile(pd.DataFrame(columns=["a"]))


def test_profile_rejects_excessive_column_count():
    frame = pd.DataFrame([[1] * 3], columns=["a", "b", "c"])
    with pytest.raises(ValueError, match="maximum supported"):
        build_dataset_profile(frame, max_columns=2)


def test_understanding_rejects_duplicate_column_mappings():
    payload = {
        "domain": "commerce",
        "dataset_kind": "sales records",
        "confidence": 0.9,
        "rationale": "Sales and product fields indicate commerce.",
        "column_meanings": [
            {"column": "sales", "semantic_role": "revenue", "description": "Sales amount", "confidence": 0.9},
            {"column": "sales", "semantic_role": "profit", "description": "Profit amount", "confidence": 0.5},
        ],
    }
    with pytest.raises(ValidationError, match="duplicate column"):
        DatasetUnderstanding.model_validate(payload)
