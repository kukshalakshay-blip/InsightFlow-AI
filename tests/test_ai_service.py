import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.services.ai_service import (
    AIAnalysis,
    generate_ai_analysis,
    get_gemini_client,
)


# ==========================================================
# TEST DATA
# ==========================================================

VALID_ANALYSIS = {
    "executive_summary": (
        "Revenue increased during the reporting period."
    ),
    "key_findings": [
        "Revenue increased by 15%.",
        "Three regions contributed most of the revenue.",
        "Missing values were detected.",
    ],
    "recommendations": [
        "Investigate missing values.",
        "Compare regional performance.",
        "Monitor revenue trends.",
    ],
    "risks_or_anomalies": [
        "Some records contain missing values."
    ],
}


@pytest.fixture
def valid_json_response():
    return json.dumps(VALID_ANALYSIS)


@pytest.fixture
def mock_gemini_client():
    client = MagicMock()
    return client


@pytest.fixture
def mock_interaction():
    interaction = MagicMock()
    interaction.output_text = json.dumps(VALID_ANALYSIS)
    return interaction


# ==========================================================
# AI RESPONSE SCHEMA TESTS
# ==========================================================

def test_ai_analysis_accepts_valid_response():
    analysis = AIAnalysis.model_validate(VALID_ANALYSIS)

    assert isinstance(analysis, AIAnalysis)
    assert analysis.executive_summary == (
        "Revenue increased during the reporting period."
    )
    assert len(analysis.key_findings) == 3
    assert len(analysis.recommendations) == 3


def test_ai_analysis_rejects_missing_required_field():
    invalid_response = {
        "executive_summary": "Revenue increased.",
        "key_findings": ["Revenue increased."],
        "recommendations": ["Monitor revenue."],
        # risks_or_anomalies is missing
    }

    with pytest.raises(ValidationError):
        AIAnalysis.model_validate(invalid_response)


def test_ai_analysis_rejects_wrong_field_type():
    invalid_response = {
        **VALID_ANALYSIS,
        "key_findings": "This should be a list, not a string.",
    }

    with pytest.raises(ValidationError):
        AIAnalysis.model_validate(invalid_response)


def test_ai_analysis_accepts_empty_risks():
    response = {
        **VALID_ANALYSIS,
        "risks_or_anomalies": [],
    }

    analysis = AIAnalysis.model_validate(response)

    assert analysis.risks_or_anomalies == []


# ==========================================================
# GEMINI CLIENT TESTS
# ==========================================================

def test_missing_api_key_raises_value_error():
    with patch.dict("os.environ", {}, clear=True):
        with patch(
            "app.services.ai_service.genai.Client"
        ) as mock_client:
            with pytest.raises(
                ValueError,
                match="GEMINI_API_KEY is not configured",
            ):
                get_gemini_client()

            mock_client.assert_not_called()


def test_gemini_client_uses_environment_api_key():
    with patch.dict(
        "os.environ",
        {"GEMINI_API_KEY": "test-api-key"},
    ):
        with patch(
            "app.services.ai_service.genai.Client"
        ) as mock_client:
            get_gemini_client()

            mock_client.assert_called_once_with(
                api_key="test-api-key"
            )


# ==========================================================
# SUCCESSFUL AI ANALYSIS TESTS
# ==========================================================

def test_generate_ai_analysis_returns_valid_model(
    mock_gemini_client,
    mock_interaction,
):
    mock_gemini_client.interactions.create.return_value = (
        mock_interaction
    )

    with patch(
        "app.services.ai_service.get_gemini_client",
        return_value=mock_gemini_client,
    ):
        with patch(
            "app.services.ai_service.time.sleep"
        ) as mock_sleep:
            result = generate_ai_analysis(
                {"rows": 100, "columns": 5}
            )

    assert isinstance(result, AIAnalysis)
    assert result.executive_summary == (
        VALID_ANALYSIS["executive_summary"]
    )
    assert result.key_findings == VALID_ANALYSIS["key_findings"]

    mock_gemini_client.interactions.create.assert_called_once()
    mock_sleep.assert_not_called()


def test_generate_ai_analysis_uses_expected_model(
    mock_gemini_client,
    mock_interaction,
):
    mock_gemini_client.interactions.create.return_value = (
        mock_interaction
    )

    with patch(
        "app.services.ai_service.get_gemini_client",
        return_value=mock_gemini_client,
    ):
        with patch("app.services.ai_service.time.sleep"):
            generate_ai_analysis({"rows": 100})

    call_kwargs = (
        mock_gemini_client.interactions.create.call_args.kwargs
    )

    assert call_kwargs["model"] == "gemini-3.5-flash-lite"
    assert call_kwargs["stream"] is False
    assert call_kwargs["response_format"]["mime_type"] == (
        "application/json"
    )


def test_generate_ai_analysis_includes_context_in_prompt(
    mock_gemini_client,
    mock_interaction,
):
    mock_gemini_client.interactions.create.return_value = (
        mock_interaction
    )

    context = {
        "total_revenue": 150000,
        "growth_percentage": 15,
    }

    with patch(
        "app.services.ai_service.get_gemini_client",
        return_value=mock_gemini_client,
    ):
        with patch("app.services.ai_service.time.sleep"):
            generate_ai_analysis(context)

    call_kwargs = (
        mock_gemini_client.interactions.create.call_args.kwargs
    )

    assert "150000" in call_kwargs["input"]
    assert "15" in call_kwargs["input"]


# ==========================================================
# INVALID RESPONSE TESTS
# ==========================================================

def test_empty_ai_response_raises_value_error(
    mock_gemini_client,
):
    interaction = MagicMock()
    interaction.output_text = ""

    mock_gemini_client.interactions.create.return_value = (
        interaction
    )

    with patch(
        "app.services.ai_service.get_gemini_client",
        return_value=mock_gemini_client,
    ):
        with patch("app.services.ai_service.time.sleep"):
            with pytest.raises(
                ValueError,
                match="Gemini returned no output",
            ):
                generate_ai_analysis({"rows": 100})

    assert (
        mock_gemini_client.interactions.create.call_count
        == 4
    )


def test_malformed_json_eventually_raises_validation_error(
    mock_gemini_client,
):
    interaction = MagicMock()
    interaction.output_text = "{invalid json"

    mock_gemini_client.interactions.create.return_value = (
        interaction
    )

    with patch(
        "app.services.ai_service.get_gemini_client",
        return_value=mock_gemini_client,
    ):
        with patch("app.services.ai_service.time.sleep"):
            with pytest.raises(ValidationError):
                generate_ai_analysis({"rows": 100})

    assert (
        mock_gemini_client.interactions.create.call_count
        == 4
    )


# ==========================================================
# RETRY BEHAVIOR TESTS
# ==========================================================

def test_temporary_failure_then_success(
    mock_gemini_client,
    mock_interaction,
):
    mock_gemini_client.interactions.create.side_effect = [
        RuntimeError("Temporary service failure"),
        mock_interaction,
    ]

    with patch(
        "app.services.ai_service.get_gemini_client",
        return_value=mock_gemini_client,
    ):
        with patch(
            "app.services.ai_service.time.sleep"
        ) as mock_sleep:
            result = generate_ai_analysis(
                {"rows": 100}
            )

    assert isinstance(result, AIAnalysis)
    assert (
        mock_gemini_client.interactions.create.call_count
        == 2
    )
    mock_sleep.assert_called_once_with(1)


def test_retry_uses_exponential_backoff(
    mock_gemini_client,
):
    mock_gemini_client.interactions.create.side_effect = (
        RuntimeError("Temporary service failure")
    )

    with patch(
        "app.services.ai_service.get_gemini_client",
        return_value=mock_gemini_client,
    ):
        with patch(
            "app.services.ai_service.time.sleep"
        ) as mock_sleep:
            with pytest.raises(RuntimeError):
                generate_ai_analysis({"rows": 100})

    assert (
        mock_gemini_client.interactions.create.call_count
        == 4
    )

    assert [
        call.args[0]
        for call in mock_sleep.call_args_list
    ] == [1, 2, 4]


def test_final_attempt_raises_original_error(
    mock_gemini_client,
):
    original_error = RuntimeError(
        "Gemini service unavailable"
    )

    mock_gemini_client.interactions.create.side_effect = (
        original_error
    )

    with patch(
        "app.services.ai_service.get_gemini_client",
        return_value=mock_gemini_client,
    ):
        with patch("app.services.ai_service.time.sleep"):
            with pytest.raises(RuntimeError) as error_info:
                generate_ai_analysis({"rows": 100})

    assert error_info.value is original_error
    assert (
        mock_gemini_client.interactions.create.call_count
        == 4
    )