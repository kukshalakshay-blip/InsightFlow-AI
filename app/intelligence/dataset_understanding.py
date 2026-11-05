"""Privacy-conscious, LLM-assisted dataset and column understanding.

The LLM classifies metadata only. It does not receive records or category labels,
and it never calculates analytical findings.

Gemini receives a simplified JSON schema. Pydantic performs strict local
validation after the response is received.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Literal

import numpy as np
import pandas as pd

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.settings import get_settings
from app.services.ai_service import get_gemini_client


logger = logging.getLogger(__name__)


# =========================================================
# 1. Supported semantic categories
# =========================================================

DomainName = Literal[
    "commerce",
    "finance",
    "healthcare",
    "marketing",
    "customer_analytics",
    "operations",
    "education",
    "real_estate",
    "logistics",
    "social_sciences",
    "technology",
    "general",
    "uncertain",
]

DataRole = Literal[
    "continuous",
    "binary_categorical",
    "ordinal_categorical",
    "nominal_categorical",
    "datetime",
    "identifier",
    "text",
    "target",
    "unknown",
]


# =========================================================
# 2. Pydantic response models
# =========================================================

class ColumnMeaning(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    column: str = Field(min_length=1, max_length=256)

    semantic_role: str = Field(
        min_length=1,
        max_length=80,
    )

    description: str = Field(
        min_length=1,
        max_length=300,
    )

    data_role: DataRole = "unknown"

    unit: str = Field(
        default="",
        max_length=80,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class DatasetUnderstanding(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    domain: DomainName

    subdomain: str = Field(
        default="",
        max_length=120,
    )

    dataset_kind: str = Field(
        min_length=1,
        max_length=160,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    rationale: str = Field(
        min_length=1,
        max_length=600,
    )

    column_meanings: list[ColumnMeaning] = Field(
        default_factory=list,
        max_length=200,
    )

    analysis_priorities: list[str] = Field(
        default_factory=list,
        max_length=12,
    )

    limitations: list[str] = Field(
        default_factory=list,
        max_length=8,
    )

    @model_validator(mode="after")
    def reject_duplicate_column_mappings(self):
        names = [
            item.column
            for item in self.column_meanings
        ]

        if len(names) != len(set(names)):
            raise ValueError(
                "column_meanings contains duplicate column names"
            )

        return self


# =========================================================
# 3. Simplified Gemini response schema
# =========================================================

def get_gemini_response_schema() -> dict:
    """Return a deliberately simple schema for Gemini.

    Complex validation constraints are handled locally by Pydantic.

    Do not replace this with DatasetUnderstanding.model_json_schema().
    That was the cause of Gemini's schema-complexity HTTP 400 error.
    """

    column_schema = {
        "type": "object",
        "properties": {
            "column": {
                "type": "string"
            },
            "semantic_role": {
                "type": "string"
            },
            "description": {
                "type": "string"
            },
            "data_role": {
                "type": "string"
            },
            "unit": {
                "type": "string"
            },
            "confidence": {
                "type": "number"
            },
        },
        "required": [
            "column",
            "semantic_role",
            "description",
            "data_role",
            "unit",
            "confidence",
        ],
    }

    return {
        "type": "object",
        "properties": {
            "domain": {
                "type": "string"
            },
            "subdomain": {
                "type": "string"
            },
            "dataset_kind": {
                "type": "string"
            },
            "confidence": {
                "type": "number"
            },
            "rationale": {
                "type": "string"
            },
            "column_meanings": {
                "type": "array",
                "items": column_schema,
            },
            "analysis_priorities": {
                "type": "array",
                "items": {
                    "type": "string"
                },
            },
            "limitations": {
                "type": "array",
                "items": {
                    "type": "string"
                },
            },
        },
        "required": [
            "domain",
            "subdomain",
            "dataset_kind",
            "confidence",
            "rationale",
            "column_meanings",
            "analysis_priorities",
            "limitations",
        ],
    }


# =========================================================
# 4. Safe numerical conversion
# =========================================================

def _safe_number(value):
    """Convert NumPy/Pandas numerical values into JSON-safe numbers."""

    if pd.isna(value):
        return None

    value = value.item() if hasattr(value, "item") else value

    if not np.isfinite(value):
        return None

    if isinstance(value, (int, np.integer)):
        return int(value)

    return float(value)


# =========================================================
# 5. Structural column classification
# =========================================================

def infer_structural_role(
    series: pd.Series,
    column_name: str,
) -> str:
    """Infer a conservative structural role from dtype and column name."""

    name = column_name.lower()

    # Datetime detection
    if (
        pd.api.types.is_datetime64_any_dtype(series)
        or re.search(
            r"(^|_)(date|time|timestamp)(_|$)",
            name,
        )
    ):
        return "datetime"

    # Identifier detection
    if re.search(
        r"(^|_)(id|uuid|key|email|phone|mobile)(_|$)",
        name,
    ):
        return "identifier"

    # Boolean detection
    if pd.api.types.is_bool_dtype(series):
        return "binary_categorical"

    non_null = series.dropna()
    unique = int(non_null.nunique())

    # Numeric classification
    if pd.api.types.is_numeric_dtype(series):

        if unique <= 2:
            return "binary_categorical"

        # Explicit ordinal naming
        if re.search(
            r"(rating|grade|level|severity|rank|class|score|stage|tier)",
            name,
        ):
            return "ordinal_categorical"

        # Low-cardinality integer codes
        if (
            unique <= 10
            and pd.api.types.is_integer_dtype(series)
        ):
            return "nominal_categorical"

        return "continuous"

    # Non-numeric classification
    if unique <= 20:
        return "nominal_categorical"

    return "text"


# =========================================================
# 6. Dataset profiling
# =========================================================

def build_dataset_profile(
    df: pd.DataFrame,
    max_columns: int = 200,
) -> dict:
    """Build a privacy-conscious metadata profile.

    Raw rows, individual cell values and category labels
    are never sent to Gemini.
    """

    if not isinstance(df, pd.DataFrame):
        raise ValueError(
            "Input must be a Pandas DataFrame."
        )

    if df.empty or len(df.index) == 0:
        raise ValueError(
            "Dataset must contain at least one row."
        )

    if len(df.columns) == 0:
        raise ValueError(
            "Dataset must contain at least one column."
        )

    if len(df.columns) > max_columns:
        raise ValueError(
            f"Dataset exceeds maximum supported "
            f"column count ({max_columns})."
        )

    if not df.columns.is_unique:
        raise ValueError(
            "Dataset contains duplicate column names. "
            "Rename duplicate columns before analysis."
        )

    columns = []
    row_count = len(df)

    for name in df.columns:

        series = df[name]

        missing = int(series.isna().sum())

        role = infer_structural_role(
            series,
            str(name),
        )

        item = {
            "name": str(name)[:256],
            "dtype": str(series.dtype)[:80],
            "structural_role_hint": role,
            "row_count": row_count,
            "missing_count": missing,
            "missing_pct": round(
                missing / row_count * 100,
                3,
            ),
            "unique_count": int(
                series.nunique(dropna=True)
            ),
        }

        # Numerical aggregates for continuous variables only
        if (
            pd.api.types.is_numeric_dtype(series)
            and role == "continuous"
        ):

            numeric = pd.to_numeric(
                series,
                errors="coerce",
            ).dropna()

            if not numeric.empty:

                q = numeric.quantile(
                    [0.25, 0.5, 0.75]
                )

                item["numeric_summary"] = {
                    "min": _safe_number(numeric.min()),
                    "q1": _safe_number(q.loc[0.25]),
                    "median": _safe_number(q.loc[0.5]),
                    "q3": _safe_number(q.loc[0.75]),
                    "max": _safe_number(numeric.max()),
                    "mean": _safe_number(numeric.mean()),
                    "std": _safe_number(numeric.std()),
                }

        # Never send category labels or individual text values.
        columns.append(item)

    return {
        "row_count": row_count,
        "column_count": len(df.columns),
        "duplicate_row_count": int(
            df.duplicated().sum()
        ),
        "columns": columns,
        "privacy_note": (
            "Metadata and aggregate statistics only; "
            "no rows, cell values, or category labels are included."
        ),
    }


# =========================================================
# 7. Gemini dataset understanding
# =========================================================

def understand_dataset(
    df: pd.DataFrame,
) -> DatasetUnderstanding:
    """Understand a dataset using Gemini and validate its response locally."""

    # Step 1: Build metadata profile
    profile = build_dataset_profile(df)

    # Step 2: Load settings
    settings = get_settings()

    if not settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Add it to your local .env file."
        )

    # Step 3: Prepare instructions
    prompt = f"""
You are the dataset-understanding component of InsightFlow AI.

Your task is to classify the dataset domain and subdomain,
infer its kind, map columns to semantic roles, and suggest
analytical priorities.

Use only the supplied metadata.

RULES:

1. Do not invent facts, units, meanings or target variables.

2. Distinguish structural data_role from semantic_role.

3. Use only these data_role values:

   continuous
   binary_categorical
   ordinal_categorical
   nominal_categorical
   datetime
   identifier
   text
   target
   unknown

4. Treat structural_role_hint as evidence, not absolute truth.

5. Set unit to an empty string if it cannot be inferred confidently.

6. For uncertain domain or column meaning, lower confidence
   and explain the uncertainty in limitations.

7. Do not propose medical diagnoses or causal claims
   for healthcare datasets.

8. Return column mappings only for column names present
   in the supplied profile.

9. Do not assume that a column is a prediction target
   merely because it is numeric.

10. Keep explanations concise and evidence-based.

11. Include every dataset column in column_meanings
    when its meaning can be reasonably inferred.
    Otherwise use unknown.

12. Do not return raw records, category labels or
    individual cell values.

DATASET PROFILE:

{json.dumps(profile, ensure_ascii=False, allow_nan=False)}
"""

    # Step 4: Get existing Gemini client
    client = get_gemini_client()

    # Step 5: Request structured JSON using simplified schema
    response = client.interactions.create(
        model=settings.gemini_model,
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": get_gemini_response_schema(),
        },
        stream=False,
    )

    # Step 6: Validate response presence
    output_text = getattr(
        response,
        "output_text",
        None,
    )

    if not output_text:
        raise ValueError(
            "Gemini returned an empty dataset understanding response."
        )

    # Step 7: Strict local Pydantic validation
    result = DatasetUnderstanding.model_validate_json(
        output_text
    )

    # Step 8: Validate mapped column names
    valid_columns = {
        str(column)
        for column in df.columns
    }

    unknown = [
        item.column
        for item in result.column_meanings
        if item.column not in valid_columns
    ]

    if unknown:
        raise ValueError(
            f"AI returned mappings for unknown columns: {unknown}"
        )

    # Step 9: Log successful understanding
    logger.info(
        "Dataset understood: domain=%s confidence=%.2f",
        result.domain,
        result.confidence,
    )

    return result
