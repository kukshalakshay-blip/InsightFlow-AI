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


def test_stale_pdf_report_is_cleared_when_dataset_signature_changes():
    from app.services.session_state import reset_stale_pdf_report

    state = {
        "generated_pdf_report": b"%PDF-old",
        "generated_pdf_name": "sales.csv",
        "generated_pdf_shape": (100, 8),
        "generated_pdf_signature": "old-signature",
    }

    reset_stale_pdf_report(state, "new-signature")

    assert "generated_pdf_report" not in state
    assert "generated_pdf_name" not in state
    assert "generated_pdf_shape" not in state
    assert "generated_pdf_signature" not in state


def test_current_pdf_report_is_preserved_when_signature_matches():
    from app.services.session_state import reset_stale_pdf_report

    pdf_bytes = b"%PDF-current"
    state = {
        "generated_pdf_report": pdf_bytes,
        "generated_pdf_name": "sales.csv",
        "generated_pdf_shape": (100, 8),
        "generated_pdf_signature": "current-signature",
    }

    reset_stale_pdf_report(state, "current-signature")

    assert state["generated_pdf_report"] is pdf_bytes
    assert state["generated_pdf_signature"] == "current-signature"


def test_pdf_without_signature_is_treated_as_stale():
    from app.services.session_state import reset_stale_pdf_report

    state = {"generated_pdf_report": b"%PDF-legacy"}

    reset_stale_pdf_report(state, "current-signature")

    assert "generated_pdf_report" not in state
