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

from app.services.recommendation_engine import (
    generate_business_recommendations,
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

visualization_recommendations = (
    recommend_visualizations(df)
)


# ==========================================================
# GENERATE DETERMINISTIC INSIGHTS
# ==========================================================

st.header("📊 Deterministic Insights")

st.caption(
    "Analytical findings calculated directly from your dataset."
)


if not visualization_recommendations:

    st.info(
        "No analytical recommendations were generated "
        "for this dataset."
    )

else:

    for index, recommendation in enumerate(
        visualization_recommendations,
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

        st.write(insight)


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


business_recommendations = (
    generate_business_recommendations(
        df,
        visualization_recommendations,
    )
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

analysis_context = build_analysis_context(
    df,
    visualization_recommendations,
)


# Add deterministic business recommendations to the context.
analysis_context["business_recommendations"] = [
    {
        "rule_id": item["rule_id"],
        "category": item["category"],
        "priority": item["priority"],
        "title": item["title"],
        "finding": item["finding"],
        "action": item["action"],
        "rationale": item["rationale"],
    }
    for item in business_recommendations
]


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
# RESET STALE AI RESULTS
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