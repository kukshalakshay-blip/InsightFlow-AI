import pandas as pd

from app.services.analysis_orchestrator import run_deterministic_analysis
from app.services.insight_engine import build_analysis_context


def sample_dataframe():
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=6, freq="D"),
            "region": ["North", "South", "North", "East", "South", "North"],
            "sales": [100, 180, 240, 160, 300, 360],
            "profit": [10, 25, 30, 18, 42, 55],
        }
    )


def test_orchestrator_returns_shared_deterministic_outputs():
    result = run_deterministic_analysis(sample_dataframe())

    assert result.dataset_summary == {
        "rows": 6,
        "columns": 4,
        "missing_cells": 0,
    }
    assert isinstance(result.visualization_recommendations, list)
    assert isinstance(result.deterministic_findings, list)
    assert isinstance(result.business_recommendations, list)
    assert result.analysis_context["dataset"]["rows"] == 6
    assert len(result.analysis_context["deterministic_findings"]) == len(
        result.deterministic_findings
    )


def test_precomputed_findings_are_reused_by_context_builder(monkeypatch):
    df = sample_dataframe()
    precomputed = [
        {
            "type": "bar",
            "reason": "precomputed",
            "score": 0.9,
            "insight": "This was computed once.",
        }
    ]

    def should_not_run(*args, **kwargs):
        raise AssertionError("generate_insight should not run for precomputed findings")

    monkeypatch.setattr(
        "app.services.insight_engine.generate_insight",
        should_not_run,
    )
    context = build_analysis_context(
        df,
        [{"type": "bar", "reason": "test", "score": 0.9}],
        deterministic_findings=precomputed,
    )

    assert context["deterministic_findings"] == precomputed


def test_context_builder_preserves_legacy_call_signature():
    df = sample_dataframe()
    context = build_analysis_context(df, [])

    assert context["dataset"] == {"rows": 6, "columns": 4}
    assert context["deterministic_findings"] == []


def test_orchestrator_rejects_non_dataframe_input():
    import pytest

    with pytest.raises(TypeError, match="pandas DataFrame"):
        run_deterministic_analysis([1, 2, 3])
