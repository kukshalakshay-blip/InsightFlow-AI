"""Gemini-backed business interpretation for InsightFlow.

Deterministic InsightFlow engines remain the source of analytical facts.
This module only translates their prepared context into business language.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from collections.abc import Mapping
from datetime import date, datetime
from typing import Annotated, Any

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

load_dotenv()

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("INSIGHTFLOW_GEMINI_MODEL", "gemini-3.5-flash-lite")
REQUEST_TIMEOUT_MS = 30_000
MAX_CONTEXT_CHARS = 100_000
MAX_LIST_ITEMS = 5

NonEmptyText = Annotated[str, Field(min_length=1, max_length=2_000)]
FindingText = Annotated[str, Field(min_length=1, max_length=1_000)]


class AIAnalysis(BaseModel):
    """Validated, display-ready AI interpretation of deterministic findings."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    executive_summary: NonEmptyText = Field(
        description="A concise executive summary grounded only in supplied evidence."
    )
    key_findings: list[FindingText] = Field(
        default_factory=list,
        max_length=MAX_LIST_ITEMS,
        description="Up to five evidence-supported findings; fewer are acceptable."
    )
    recommendations: list[FindingText] = Field(
        default_factory=list,
        max_length=MAX_LIST_ITEMS,
        description="Up to five practical recommendations supported by the context."
    )
    risks_or_anomalies: list[FindingText] = Field(
        default_factory=list,
        max_length=MAX_LIST_ITEMS,
        description="Evidence-supported risks or anomalies; empty when none are supported."
    )

    @field_validator(
        "key_findings",
        "recommendations",
        "risks_or_anomalies",
        mode="before",
    )
    @classmethod
    def normalize_missing_lists(cls, value: Any) -> Any:
        # Some model responses may explicitly return null for an optional list.
        return [] if value is None else value


def get_gemini_client():
    """Create a Gemini client using the configured API key and request timeout."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    return genai.Client(
        api_key=api_key,
        http_options={"timeout": REQUEST_TIMEOUT_MS},
    )


def _to_json_safe(value: Any) -> Any:
    """Convert common Pandas/NumPy/date values into strict JSON-compatible data."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None

    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()

    if isinstance(value, np.ndarray):
        return [_to_json_safe(item) for item in value.tolist()]

    if isinstance(value, np.generic):
        return _to_json_safe(value.item())

    if isinstance(value, Mapping):
        return {str(key): _to_json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]

    if isinstance(value, float) and not math.isfinite(value):
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    # Pandas extension scalars can expose isna() without being JSON-native.
    try:
        missing = pd.isna(value)
        if isinstance(missing, (bool, np.bool_)) and missing:
            return None
    except (TypeError, ValueError):
        pass

    raise TypeError(
        f"Unsupported value in AI analysis context: {type(value).__name__}"
    )


def _serialize_analysis_context(analysis_context: dict) -> str:
    """Validate and serialize context as compact, standards-compliant JSON."""
    if not isinstance(analysis_context, dict):
        raise TypeError("analysis_context must be a dictionary.")

    safe_context = _to_json_safe(analysis_context)
    serialized = json.dumps(
        safe_context,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )

    if len(serialized) > MAX_CONTEXT_CHARS:
        raise ValueError(
            f"AI analysis context is too large ({len(serialized):,} characters). "
            f"Maximum allowed size is {MAX_CONTEXT_CHARS:,} characters."
        )

    return serialized


def _build_prompt(serialized_context: str) -> str:
    """Build a stable prompt that separates evidence from interpretation."""
    return f"""
You are InsightFlow's business intelligence analyst.

Your task is to interpret the supplied, already-computed analytical context.
The deterministic analysis and rule-based recommendations are the source of truth.
Do not independently invent, recalculate, or infer dataset facts.

STRICT EVIDENCE RULES
1. Use only facts explicitly present in the supplied context.
2. Never invent numbers, percentages, trends, segments, causes, or sample sizes.
3. Do not claim causation from correlation or association.
4. Do not describe an outlier as an error unless the context establishes that.
5. Distinguish observed findings from interpretations and hypotheses.
6. Preserve the numerical meaning and direction of every reported statistic.
7. Acknowledge missing, conflicting, or insufficient evidence.
8. Treat rule-based business recommendations as suggestions, not proof.
9. Do not claim that a recommended action has already been taken.
10. Prefer concise, specific, decision-useful business language.
11. Return fewer findings or recommendations when evidence is limited.
12. Do not pad the response merely to reach a target number of items.
13. If no risks or anomalies are supported, return an empty list.
14. Prioritize findings explicitly marked as important or high priority.

OUTPUT REQUIREMENTS
- Produce one concise executive summary.
- Include up to five important key findings.
- Include up to five practical recommendations.
- Include supported risks or anomalies, or an empty list.
- Every item must be traceable to the supplied context.
- Return only data matching the provided JSON response schema.

ANALYSIS CONTEXT (JSON)
{serialized_context}
""".strip()


def generate_ai_analysis(analysis_context: dict) -> AIAnalysis:
    """Generate a structured AI interpretation of InsightFlow's analysis context.

    The Google GenAI SDK owns transient transport/API retries. This service does
    not add a second retry loop, avoiding multiplied request attempts.
    """
    serialized_context = _serialize_analysis_context(analysis_context)
    prompt = _build_prompt(serialized_context)

    client = get_gemini_client()
    started_at = time.perf_counter()

    try:
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": AIAnalysis.model_json_schema(),
            },
            stream=False,
        )

        output_text = getattr(interaction, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise ValueError("Gemini returned an empty AI analysis response.")

        result = AIAnalysis.model_validate_json(output_text)
        elapsed_ms = (time.perf_counter() - started_at) * 1_000
        logger.info(
            "AI analysis completed: model=%s duration_ms=%.1f "
            "findings=%d recommendations=%d",
            MODEL_NAME,
            elapsed_ms,
            len(result.key_findings),
            len(result.recommendations),
        )
        return result

    except ValidationError:
        logger.warning(
            "Gemini returned a response that failed AIAnalysis validation.",
            exc_info=True,
        )
        raise
    except Exception:
        elapsed_ms = (time.perf_counter() - started_at) * 1_000
        logger.exception(
            "AI analysis request failed: model=%s duration_ms=%.1f",
            MODEL_NAME,
            elapsed_ms,
        )
        raise
