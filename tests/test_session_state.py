from app.services.session_state import (
    reset_stale_ai_analysis,
)


def test_first_load_initializes_ai_state():
    state = {}

    reset_stale_ai_analysis(state, "signature-a")

    assert state["ai_analysis"] is None
    assert state["ai_analysis_signature"] == "signature-a"


def test_changed_signature_clears_old_analysis():
    old_analysis = object()

    state = {
        "ai_analysis": old_analysis,
        "ai_analysis_signature": "signature-a",
    }

    reset_stale_ai_analysis(state, "signature-b")

    assert state["ai_analysis"] is None
    assert state["ai_analysis_signature"] == "signature-b"


def test_unchanged_signature_preserves_analysis():
    existing_analysis = object()

    state = {
        "ai_analysis": existing_analysis,
        "ai_analysis_signature": "signature-a",
    }

    reset_stale_ai_analysis(state, "signature-a")

    assert state["ai_analysis"] is existing_analysis


def test_missing_signature_clears_old_analysis():
    old_analysis = object()

    state = {
        "ai_analysis": old_analysis,
    }

    reset_stale_ai_analysis(state, "signature-a")

    assert state["ai_analysis"] is None
    assert state["ai_analysis_signature"] == "signature-a"


def test_changed_dataset_values_can_invalidate_analysis():
    state = {
        "ai_analysis": object(),
        "ai_analysis_signature": "old-data-signature",
    }

    reset_stale_ai_analysis(state, "new-data-signature")

    assert state["ai_analysis"] is None
    assert (
        state["ai_analysis_signature"]
        == "new-data-signature"
    )