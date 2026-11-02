import json
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from app.services import ai_service
from app.services.ai_service import (
    AIAnalysis,
    _build_prompt,
    _serialize_analysis_context,
    generate_ai_analysis,
    get_gemini_client,
)


VALID_ANALYSIS = {
    "executive_summary": "Revenue increased in the observed period.",
    "key_findings": ["Revenue increased by 12%."],
    "recommendations": ["Review the strongest-performing segment."],
    "risks_or_anomalies": [],
}


def _mock_client(output_text):
    client = Mock()
    client.interactions.create.return_value = SimpleNamespace(
        output_text=output_text
    )
    return client


def test_ai_analysis_accepts_valid_response():
    result = AIAnalysis.model_validate(VALID_ANALYSIS)
    assert result.executive_summary.startswith("Revenue")
    assert result.key_findings == ["Revenue increased by 12%."]


def test_ai_analysis_allows_fewer_than_three_items():
    result = AIAnalysis.model_validate({
        "executive_summary": "Only one conclusion is supported.",
        "key_findings": ["One supported finding."],
        "recommendations": [],
        "risks_or_anomalies": [],
    })
    assert len(result.key_findings) == 1
    assert result.recommendations == []


def test_ai_analysis_defaults_optional_lists():
    result = AIAnalysis.model_validate({
        "executive_summary": "Summary."
    })
    assert result.key_findings == []
    assert result.recommendations == []
    assert result.risks_or_anomalies == []


@pytest.mark.parametrize("bad_summary", ["", "   ", None, 123])
def test_ai_analysis_rejects_invalid_executive_summary(bad_summary):
    payload = {**VALID_ANALYSIS, "executive_summary": bad_summary}
    with pytest.raises(ValidationError):
        AIAnalysis.model_validate(payload)


def test_ai_analysis_rejects_more_than_five_findings():
    payload = {
        **VALID_ANALYSIS,
        "key_findings": [f"Finding {index}" for index in range(6)],
    }
    with pytest.raises(ValidationError):
        AIAnalysis.model_validate(payload)


def test_ai_analysis_rejects_blank_list_items():
    payload = {**VALID_ANALYSIS, "key_findings": ["   "]}
    with pytest.raises(ValidationError):
        AIAnalysis.model_validate(payload)


def test_ai_analysis_rejects_unexpected_fields():
    payload = {**VALID_ANALYSIS, "unsupported": "extra"}
    with pytest.raises(ValidationError):
        AIAnalysis.model_validate(payload)


def test_ai_analysis_strips_whitespace():
    payload = {**VALID_ANALYSIS, "executive_summary": "  Summary.  "}
    result = AIAnalysis.model_validate(payload)
    assert result.executive_summary == "Summary."


def test_get_gemini_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        get_gemini_client()


def test_get_gemini_client_uses_timeout_and_key(monkeypatch):
    constructor = Mock(return_value="client")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ai_service.genai, "Client", constructor)

    result = get_gemini_client()

    assert result == "client"
    constructor.assert_called_once_with(
        api_key="test-key",
        http_options={"timeout": ai_service.REQUEST_TIMEOUT_MS},
    )


def test_context_serializes_numpy_pandas_and_dates():
    context = {
        "count": np.int64(4),
        "ratio": np.float64(0.25),
        "missing": np.float64(np.nan),
        "date": pd.Timestamp("2026-11-02"),
        "array": np.array([1, 2, 3]),
    }

    result = json.loads(_serialize_analysis_context(context))

    assert result["count"] == 4
    assert result["ratio"] == 0.25
    assert result["missing"] is None
    assert result["date"] == "2026-11-02T00:00:00"
    assert result["array"] == [1, 2, 3]


def test_context_serializes_nested_mapping_and_tuples():
    context = {"nested": {"values": (1, 2, 3)}}
    assert json.loads(_serialize_analysis_context(context)) == {
        "nested": {"values": [1, 2, 3]}
    }


def test_context_rejects_non_dictionary():
    with pytest.raises(TypeError, match="dictionary"):
        _serialize_analysis_context([1, 2, 3])


def test_context_rejects_unsupported_objects():
    with pytest.raises(TypeError, match="Unsupported value"):
        _serialize_analysis_context({"bad": object()})


def test_context_rejects_oversized_payload(monkeypatch):
    monkeypatch.setattr(ai_service, "MAX_CONTEXT_CHARS", 10)
    with pytest.raises(ValueError, match="too large"):
        _serialize_analysis_context({"text": "this is too long"})


def test_prompt_uses_json_context_and_evidence_rules():
    prompt = _build_prompt('{"rows":100}')
    assert '{"rows":100}' in prompt
    assert "Never invent numbers" in prompt
    assert "Do not claim causation" in prompt
    assert "rule-based business recommendations" in prompt


def test_generate_ai_analysis_returns_valid_model(monkeypatch):
    client = _mock_client(json.dumps(VALID_ANALYSIS))
    monkeypatch.setattr(ai_service, "get_gemini_client", lambda: client)

    result = generate_ai_analysis({"rows": 100})

    assert isinstance(result, AIAnalysis)
    assert result.executive_summary == VALID_ANALYSIS["executive_summary"]


def test_generate_ai_analysis_uses_model_structured_output_and_context(monkeypatch):
    client = _mock_client(json.dumps(VALID_ANALYSIS))
    monkeypatch.setattr(ai_service, "get_gemini_client", lambda: client)
    context = {"rows": 100, "metric": np.int64(7)}

    generate_ai_analysis(context)

    kwargs = client.interactions.create.call_args.kwargs
    assert kwargs["model"] == ai_service.MODEL_NAME
    assert kwargs["stream"] is False
    assert kwargs["response_format"]["mime_type"] == "application/json"
    assert kwargs["response_format"]["schema"] == AIAnalysis.model_json_schema()
    assert '"rows":100' in kwargs["input"]
    assert '"metric":7' in kwargs["input"]


def test_generate_ai_analysis_rejects_empty_response(monkeypatch):
    client = _mock_client("  ")
    monkeypatch.setattr(ai_service, "get_gemini_client", lambda: client)

    with pytest.raises(ValueError, match="empty"):
        generate_ai_analysis({"rows": 100})


def test_generate_ai_analysis_rejects_malformed_json_without_app_retry(monkeypatch):
    client = _mock_client("{not-json")
    monkeypatch.setattr(ai_service, "get_gemini_client", lambda: client)

    with pytest.raises(ValidationError):
        generate_ai_analysis({"rows": 100})

    assert client.interactions.create.call_count == 1


def test_generate_ai_analysis_propagates_api_error_without_second_retry(monkeypatch):
    client = Mock()
    client.interactions.create.side_effect = RuntimeError("simulated API failure")
    monkeypatch.setattr(ai_service, "get_gemini_client", lambda: client)

    with pytest.raises(RuntimeError, match="simulated API failure"):
        generate_ai_analysis({"rows": 100})

    # The SDK is the sole owner of its configured transport retry behavior.
    assert client.interactions.create.call_count == 1


def test_invalid_context_fails_before_client_creation(monkeypatch):
    client_factory = Mock()
    monkeypatch.setattr(ai_service, "get_gemini_client", client_factory)

    with pytest.raises(TypeError):
        generate_ai_analysis({"bad": object()})

    client_factory.assert_not_called()
