import streamlit as st

from app.services.ai_service import (
    generate_ai_analysis,
)

from app.services.insight_engine import (
    build_analysis_context,
    generate_insight,
)

from app.services.visualization_engine import (
    recommend_visualizations,
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

recommendations = recommend_visualizations(
    df
)


# ==========================================================
# BUILD ANALYTICAL CONTEXT
# ==========================================================

analysis_context = build_analysis_context(
    df,
    recommendations,
)


# ==========================================================
# DETERMINISTIC INSIGHTS
# ==========================================================

st.header("📊 Deterministic Insights")

st.caption(
    "These insights are generated directly from "
    "statistical analysis of your dataset."
)


if not recommendations:

    st.info(
        "No analytical recommendations were generated "
        "for this dataset."
    )

else:

    for index, recommendation in enumerate(
        recommendations,
        start=1,
    ):

        insight = generate_insight(
            df,
            recommendation,
        )

        st.markdown(
            f"**{index}. "
            f"{recommendation['type'].title()}**"
        )

        st.write(
            insight
        )


# ==========================================================
# AI ANALYSIS
# ==========================================================

st.divider()

st.header("🧠 AI Business Analysis")

st.caption(
    "Gemini interprets the analytical facts generated "
    "by InsightFlow."
)


# ==========================================================
# DATASET SIGNATURE
# ==========================================================

dataset_name = st.session_state.get(
    "dataset_name",
    "dataset",
)

dataset_signature = (
    dataset_name,
    len(df),
    len(df.columns),
    tuple(df.columns),
)


# ==========================================================
# INITIALIZE AI CACHE
# ==========================================================

if (
    "ai_analysis" not in st.session_state
    or st.session_state.get(
        "ai_analysis_signature"
    ) != dataset_signature
):

    st.session_state["ai_analysis"] = None

    st.session_state[
        "ai_analysis_signature"
    ] = dataset_signature


# ==========================================================
# GENERATE AI ANALYSIS
# ==========================================================

if st.button(
    "✨ Generate AI Insights",
    type="primary",
):

    with st.spinner(
        "AI analyst is reviewing the dataset..."
    ):

        try:

            ai_result = generate_ai_analysis(
                analysis_context
            )

            # Store result for future Streamlit reruns.
            st.session_state[
                "ai_analysis"
            ] = ai_result

        except Exception as error:

            st.error(
                "The AI analysis could not be generated "
                "right now."
            )

            st.caption(
                f"Technical detail: {error}"
            )


# ==========================================================
# DISPLAY CACHED AI ANALYSIS
# ==========================================================

ai_result = st.session_state.get(
    "ai_analysis"
)


if ai_result is not None:

    # ------------------------------------------------------
    # Executive Summary
    # ------------------------------------------------------

    st.subheader(
        "Executive Summary"
    )

    st.write(
        ai_result.executive_summary
    )

    # ------------------------------------------------------
    # Key Findings
    # ------------------------------------------------------

    st.subheader(
        "🔎 Key Findings"
    )

    for finding in (
        ai_result.key_findings
    ):

        st.markdown(
            f"- {finding}"
        )

    # ------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------

    st.subheader(
        "🎯 Recommendations"
    )

    for recommendation in (
        ai_result.recommendations
    ):

        st.markdown(
            f"- {recommendation}"
        )

    # ------------------------------------------------------
    # Risks / Anomalies
    # ------------------------------------------------------

    st.subheader(
        "⚠️ Risks / Anomalies"
    )

    if ai_result.risks_or_anomalies:

        for risk in (
            ai_result.risks_or_anomalies
        ):

            st.markdown(
                f"- {risk}"
            )

    else:

        st.success(
            "No significant risks or anomalies "
            "were identified from the available "
            "analytical facts."
        )