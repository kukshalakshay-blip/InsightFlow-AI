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