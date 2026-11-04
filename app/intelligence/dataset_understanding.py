"""LLM-assisted dataset understanding for InsightFlow.

The model classifies the dataset and assigns semantic roles to columns. It does
not execute analysis or calculate facts; downstream Python engines remain the
source of truth for all measurements and findings.
"""
from __future__ import annotations

import json
import logging
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.settings import get_settings
from app.services.ai_service import get_gemini_client

logger = logging.getLogger(__name__)

DomainName = Literal[
    "commerce", "finance", "healthcare", "marketing", "customer_analytics",
    "operations", "education", "real_estate", "logistics", "social_sciences",
    "technology", "general", "uncertain",
]


class ColumnMeaning(BaseModel):
    """Meaning inferred for one existing dataset column."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    column: str = Field(min_length=1, max_length=256)
    semantic_role: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=300)
    confidence: float = Field(ge=0.0, le=1.0)


class DatasetUnderstanding(BaseModel):
    """Validated domain assessment returned by the model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    domain: DomainName
    subdomain: str = Field(default="", max_length=120)
    dataset_kind: str = Field(min_length=1, max_length=160)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1, max_length=600)
    column_meanings: list[ColumnMeaning] = Field(default_factory=list, max_length=200)
    analysis_priorities: list[str] = Field(default_factory=list, max_length=12)
    limitations: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("analysis_priorities", "limitations")
    @classmethod
    def clean_string_lists(cls, values: list[str]) -> list[str]:
        return [value.strip()[:160] for value in values if isinstance(value, str) and value.strip()]

    @model_validator(mode="after")
    def reject_duplicate_column_mappings(self) -> "DatasetUnderstanding":
        names = [item.column for item in self.column_meanings]
        if len(names) != len(set(names)):
            raise ValueError("column_meanings contains duplicate column names")
        return self


def build_dataset_profile(df: pd.DataFrame, max_columns: int = 200) -> dict:
    """Build a privacy-conscious metadata profile without sending row samples.

    Only schema, aggregate statistics and bounded category summaries are sent
    to the model. Raw records and representative cell values are never sent.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if df.empty or len(df.columns) == 0:
        raise ValueError("Upload a dataset with at least one row and one column")
    if len(df.columns) > max_columns:
        raise ValueError(f"Dataset has {len(df.columns)} columns; maximum supported for AI understanding is {max_columns}")

    columns = []
    for name in df.columns:
        series = df[name]
        item = {
            "name": str(name)[:256],
            "dtype": str(series.dtype),
            "rows": int(len(series)),
            "missing_count": int(series.isna().sum()),
            "missing_pct": round(float(series.isna().mean() * 100), 2),
            "unique_count": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
            if not values.empty:
                item["numeric_summary"] = {
                    "min": _safe_number(values.min()),
                    "median": _safe_number(values.median()),
                    "max": _safe_number(values.max()),
                }
        columns.append(item)

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": columns,
        "privacy_note": "No raw row samples or individual cell values are included.",
    }


def _safe_number(value: int | float | np.number) -> int | float | None:
    number = float(value)
    if not np.isfinite(number):
        return None
    return int(number) if number.is_integer() else round(number, 6)


def understand_dataset(df: pd.DataFrame) -> DatasetUnderstanding:
    """Ask Gemini to classify a dataset and map its columns semantically."""
    profile = build_dataset_profile(df)
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not configured. Add it to your .env file to enable dataset understanding.")

    prompt = f"""You are the dataset-understanding component of InsightFlow, an AI data analyst.

Infer the most likely domain and subdomain from the supplied schema and aggregate metadata.
Map each supplied column to a concise semantic role (examples: revenue, profit, transaction_date,
patient_age, blood_pressure_systolic, customer_identifier, product_category, target_label).
Choose analysis priorities that are appropriate to this dataset, not a generic checklist.

Rules:
- Use only the supplied metadata. Do not invent column names or claim facts not present.
- Return a mapping only for columns that exist in the supplied schema.
- Treat identifiers, binary flags, ordinal categories, dates, measures and target labels distinctly.
- Do not infer causation, diagnoses, creditworthiness, or other high-impact conclusions.
- If evidence is weak, use domain='uncertain' or 'general', lower confidence, and explain limitations.
- Domain must be one of the allowed schema values.
- Do not include raw data values; none were supplied.

DATASET PROFILE (JSON):
{json.dumps(profile, ensure_ascii=False, separators=(',', ':'))}"""

    client = get_gemini_client()
    response = client.interactions.create(
        model=settings.gemini_model,
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": DatasetUnderstanding.model_json_schema(),
        },
        stream=False,
    )
    output = getattr(response, "output_text", None)
    if not isinstance(output, str) or not output.strip():
        raise ValueError("Gemini returned an empty dataset-understanding response")

    result = DatasetUnderstanding.model_validate_json(output)
    valid_columns = {str(column) for column in df.columns}
    unknown = [item.column for item in result.column_meanings if item.column not in valid_columns]
    if unknown:
        raise ValueError(f"Gemini mapped columns that do not exist in the dataset: {unknown}")

    logger.info(
        "Dataset understood: domain=%s confidence=%.2f columns_mapped=%d",
        result.domain, result.confidence, len(result.column_meanings),
    )
    return result
