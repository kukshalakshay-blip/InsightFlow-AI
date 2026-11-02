import streamlit as st

from app.services.ai_service import (
    generate_ai_analysis,
)

from app.services.analysis_orchestrator import (
    run_deterministic_analysis,
)

from app.services.dataset_signature import (
    generate_dataset_signature,
)

from app.services.session_state import (
    reset_stale_ai_analysis,
)

# ==========================================================
# PAGE HEADER
# ==========================================================

st.title("💡 AI Insights")

st.markdown(
    """
Turn your dataset into **business-level insights** using
InsightFlow's analytical engine and AI analyst.
"""
)


# ==========================================================
# CHECK DATASET
# ==========================================================

if "dataset" not in st.session_state:

    st.warning(
        "No dataset is currently loaded."
    )

    st.info(
        "Go to **Data Upload** and upload a dataset first."
    )

    st.stop()


df = st.session_state["dataset"]


# ==========================================================
# GENERATE VISUALIZATION RECOMMENDATIONS
# ==========================================================

# Run the deterministic engines once. Both the page and AI context
# reuse this exact result instead of recomputing findings.
try:
    analysis_result = run_deterministic_analysis(df)
except Exception as error:
    st.error("Unable to prepare deterministic analysis for this dataset.")
    st.exception(error)
    st.stop()

visualization_recommendations = analysis_result.visualization_recommendations
business_recommendations = analysis_result.business_recommendations
analysis_context = analysis_result.analysis_context


# ==========================================================
# GENERATE DETERMINISTIC INSIGHTS
# ==========================================================

st.header("📊 Deterministic Insights")
st.caption("Analytical findings calculated directly from your dataset.")

if not analysis_result.deterministic_findings:
    st.info("No analytical recommendations were generated for this dataset.")
else:
    for index, finding in enumerate(analysis_result.deterministic_findings, start=1):
        chart_type = finding.recommendation.get("type", "Analysis")
        st.markdown(f"**{index}. {str(chart_type).title()}**")
        st.write(finding.text)


# ==========================================================
# BUSINESS RECOMMENDATIONS ENGINE
# ==========================================================

st.divider()

st.header("🎯 Business Recommendations")

st.caption(
    "Actionable suggestions generated from deterministic "
    "business rules. Each recommendation is linked to an "
    "observable pattern in your dataset."
)


# ==========================================================
# DISPLAY BUSINESS RECOMMENDATIONS
# ==========================================================

if not business_recommendations:

    st.success(
        "No business recommendation rules were triggered "
        "by the available data."
    )

else:

    # Summary metrics
    high_priority_count = sum(
        recommendation["priority"] == "high"
        for recommendation in business_recommendations
    )

    medium_priority_count = sum(
        recommendation["priority"] == "medium"
        for recommendation in business_recommendations
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    metric_col1.metric(
        "Total Recommendations",
        len(business_recommendations),
    )

    metric_col2.metric(
        "High Priority",
        high_priority_count,
    )

    metric_col3.metric(
        "Medium Priority",
        medium_priority_count,
    )

    st.markdown("### Recommended Actions")

    for index, recommendation in enumerate(
        business_recommendations,
        start=1,
    ):

        priority = recommendation["priority"].upper()

        priority_icon = {
            "HIGH": "🔴",
            "MEDIUM": "🟠",
            "LOW": "🟢",
        }.get(priority, "⚪")

        with st.container(border=True):

            st.markdown(
                f"### {index}. {recommendation['title']}"
            )

            st.caption(
                f"{priority_icon} {priority} PRIORITY"
                f"  ·  "
                f"{recommendation['category'].replace('_', ' ').title()}"
            )

            st.markdown("**Finding**")

            st.write(
                recommendation["finding"]
            )

            st.markdown("**Suggested action**")

            st.write(
                recommendation["action"]
            )

            st.markdown("**Why it matters**")

            st.write(
                recommendation["rationale"]
            )


# ==========================================================
# BUILD ANALYTICAL CONTEXT FOR GEMINI
# ==========================================================


# ==========================================================
# DATASET SIGNATURE
# ==========================================================

dataset_name = st.session_state.get(
    "dataset_name",
    "dataset",
)

dataset_signature = generate_dataset_signature(
    df,
    dataset_name,
)


# ==========================================================
# RESET STALE AI RESULTS
# ==========================================================


reset_stale_ai_analysis(
    st.session_state,
    dataset_signature,
)

# ==========================================================
# AI BUSINESS ANALYSIS
# ==========================================================

st.divider()

st.header("🧠 AI Business Analysis")

st.caption(
    "Gemini interprets InsightFlow's analytical findings "
    "and rule-based business recommendations."
)


# ==========================================================
# GENERATE AI ANALYSIS
# ==========================================================

if st.button(
    "✨ Generate AI Insights",
    type="primary",
):

    with st.spinner(
        "AI analyst is reviewing the dataset and "
        "business recommendations..."
    ):

        try:

            ai_result = generate_ai_analysis(
                analysis_context
            )

            st.session_state[
                "ai_analysis"
            ] = ai_result

        except Exception:

            st.error(
                "The AI analysis could not be generated "
                "right now. Your deterministic insights "
                "and business recommendations are still available."
            )


# ==========================================================
# DISPLAY AI ANALYSIS
# ==========================================================

ai_result = st.session_state.get(
    "ai_analysis"
)


if ai_result is not None:

    # ------------------------------------------------------
    # EXECUTIVE SUMMARY
    # ------------------------------------------------------

    st.subheader("Executive Summary")

    st.write(
        ai_result.executive_summary
    )

    # ------------------------------------------------------
    # KEY FINDINGS
    # ------------------------------------------------------

    st.subheader("🔎 Key Findings")

    for finding in ai_result.key_findings:

        st.markdown(
            f"- {finding}"
        )

    # ------------------------------------------------------
    # AI RECOMMENDATIONS
    # ------------------------------------------------------

    st.subheader("💡 AI Recommendations")

    for recommendation in ai_result.recommendations:

        st.markdown(
            f"- {recommendation}"
        )

    # ------------------------------------------------------
    # RISKS AND ANOMALIES
    # ------------------------------------------------------

    st.subheader("⚠️ Risks / Anomalies")

    if ai_result.risks_or_anomalies:

        for risk in ai_result.risks_or_anomalies:

            st.markdown(
                f"- {risk}"
            )

    else:

        st.success(
            "No significant risks or anomalies were "
            "identified from the available analytical facts."
        )