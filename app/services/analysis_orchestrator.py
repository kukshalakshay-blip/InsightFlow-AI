"""Coordinate deterministic analysis for InsightFlow pages.

This module deliberately contains no Streamlit or Gemini dependency.
It composes the existing analysis engines and returns reusable results.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.services.insight_engine import build_analysis_context, generate_insight
from app.services.recommendation_engine import generate_business_recommendations
from app.services.visualization_engine import recommend_visualizations


@dataclass(frozen=True)
class DeterministicFinding:
    """A visualization recommendation paired with its computed explanation."""

    recommendation: dict[str, Any]
    text: str


@dataclass
class AnalysisResult:
    """Shared deterministic output consumed by Insights and Reports."""

    dataset_summary: dict[str, int]
    visualization_recommendations: list[dict[str, Any]]
    deterministic_findings: list[DeterministicFinding]
    business_recommendations: list[dict[str, Any]]
    analysis_context: dict[str, Any]


def run_deterministic_analysis(df: pd.DataFrame) -> AnalysisResult:
    """Run each deterministic engine once and assemble a reusable result.

    A failed individual finding is intentionally allowed to propagate here:
    callers can display a single preparation error rather than silently
    creating an incomplete AI context that disagrees with the UI.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")
    if df.empty:
        # Empty datasets are valid inputs for the existing engines, so don't
        # reject them here; the downstream engines decide their output.
        pass

    visualizations = recommend_visualizations(df)
    findings = [
        DeterministicFinding(
            recommendation=recommendation,
            text=str(generate_insight(df, recommendation)),
        )
        for recommendation in visualizations
    ]
    business = generate_business_recommendations(df, visualizations)

    context_findings = [
        {
            "type": item.recommendation.get("type"),
            "reason": item.recommendation.get("reason"),
            "score": item.recommendation.get("score"),
            "insight": item.text,
        }
        for item in findings
    ]
    context = build_analysis_context(
        df,
        visualizations,
        deterministic_findings=context_findings,
    )
    context["business_recommendations"] = [
        {
            "rule_id": item.get("rule_id"),
            "category": item.get("category"),
            "priority": item.get("priority"),
            "title": item.get("title"),
            "observed_finding": item.get("finding"),
            "suggested_action": item.get("action"),
            "rationale": item.get("rationale"),
        }
        for item in business
    ]

    return AnalysisResult(
        dataset_summary={
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "missing_cells": int(df.isna().sum().sum()),
        },
        visualization_recommendations=visualizations,
        deterministic_findings=findings,
        business_recommendations=business,
        analysis_context=context,
    )
