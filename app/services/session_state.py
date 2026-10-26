def reset_stale_ai_analysis(
    session_state,
    dataset_signature: str,
) -> None:
    """
    Clear stored AI analysis when the dataset signature changes.
    """

    if (
        "ai_analysis" not in session_state
        or session_state.get("ai_analysis_signature")
        != dataset_signature
    ):
        session_state["ai_analysis"] = None
        session_state["ai_analysis_signature"] = (
            dataset_signature
        )


def reset_stale_pdf_report(
    session_state,
    dataset_signature: str,
) -> None:
    """Clear a cached PDF when it does not match the active dataset."""

    if session_state.get("generated_pdf_signature") != dataset_signature:
        for key in (
            "generated_pdf_report",
            "generated_pdf_name",
            "generated_pdf_shape",
            "generated_pdf_signature",
        ):
            session_state.pop(key, None)
