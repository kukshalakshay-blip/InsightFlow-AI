"""Helpers for invalidating dataset-specific Streamlit session artifacts."""


def reset_stale_ai_analysis(session_state, dataset_signature: str) -> None:
    if session_state.get("ai_analysis_signature") != dataset_signature:
        session_state["ai_analysis"] = None
        session_state["ai_analysis_signature"] = dataset_signature


def reset_stale_pdf_report(session_state, dataset_signature: str) -> None:
    if session_state.get("generated_pdf_signature") != dataset_signature:
        for key in (
            "generated_pdf_report", "generated_pdf_name", "generated_pdf_shape",
            "generated_pdf_signature",
        ):
            session_state.pop(key, None)


def reset_stale_dataset_understanding(session_state, dataset_signature: str) -> None:
    """Clear a cached semantic profile when it belongs to another dataset."""
    if session_state.get("dataset_understanding_signature") != dataset_signature:
        for key in (
            "dataset_understanding", "dataset_understanding_signature",
            "dataset_understanding_error", "dataset_understanding_attempted_signature",
        ):
            session_state.pop(key, None)
