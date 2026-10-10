import streamlit as st

from app.services.report_generator import (
    generate_pdf_report,
)

from app.services.insight_engine import (
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

st.title("📄 InsightFlow Reports")

st.markdown(
    """
Generate a downloadable **business analysis report** containing
dataset statistics, analytical findings, business recommendations,
and AI-generated insights.
"""
)

st.divider()


# ==========================================================
# CHECK DATASET
# ==========================================================

if "dataset" not in st.session_state:

    st.info(
        "Upload a dataset before generating a report."
    )

    st.page_link(
        "app/pages/upload.py",
        label="Go to Data Upload",
        icon="📤",
    )

    st.stop()


df = st.session_state["dataset"]

dataset_name = st.session_state.get(
    "dataset_name",
    "dataset",
)


# ==========================================================
# REPORT OVERVIEW
# ==========================================================

st.subheader("📊 Report Overview")

metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric(
    "Dataset Rows",
    f"{len(df):,}",
)

metric_col2.metric(
    "Dataset Columns",
    f"{len(df.columns):,}",
)

metric_col3.metric(
    "Missing Cells",
    f"{int(df.isna().sum().sum()):,}",
)


# ==========================================================
# PREPARE REPORT DATA
# ==========================================================

visualization_recommendations = (
    recommend_visualizations(df)
)


business_recommendations = (
    generate_business_recommendations(
        df,
        visualization_recommendations,
    )
)


# ==========================================================
# BUILD DETERMINISTIC INSIGHTS
# ==========================================================

deterministic_insights = []

for index, recommendation in enumerate(
    visualization_recommendations,
    start=1,
):

    insight_text = generate_insight(
        df,
        recommendation,
    )

    deterministic_insights.append(
        {
            "title": (
                f"{recommendation['type'].title()} "
                f"Finding {index}"
            ),
            "text": insight_text,
        }
    )


# ==========================================================
# GET CACHED AI ANALYSIS
# ==========================================================

ai_analysis = st.session_state.get(
    "ai_analysis"
)


# ==========================================================
# REPORT CONTENT SUMMARY
# ==========================================================

st.subheader("📋 Included in Your Report")

st.markdown(
    """
    - Dataset overview and data-quality statistics
    - Deterministic analytical findings
    - Prioritized business recommendations
    - AI executive summary and key findings, when available
    - AI recommendations and risks, when available
    """
)

if ai_analysis is None:

    st.warning(
        "AI analysis has not been generated for this session. "
        "You can still create a report, but it will not include "
        "the AI executive summary, AI findings, or AI recommendations."
    )

    st.caption(
        "To include AI analysis, visit AI Insights and select "
        "'Generate AI Insights' first."
    )

else:

    st.success(
        "Cached AI analysis is available and will be included "
        "in the PDF."
    )


# ==========================================================
# GENERATE PDF REPORT
# ==========================================================

st.divider()

st.subheader("📥 Generate Your Report")

st.write(
    f"Your report will be generated from the dataset "
    f"**{dataset_name}**."
)


if st.button(
    "📄 Generate PDF Report",
    type="primary",
    use_container_width=True,
):

    try:

        profile = {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "missing_cells": int(
                df.isna().sum().sum()
            ),
            "duplicate_rows": int(
                df.duplicated().sum()
            ),
        }

        with st.spinner(
            "Preparing your business analysis report..."
        ):

            pdf_bytes = generate_pdf_report(
                dataset_name=dataset_name,
                profile=profile,
                deterministic_insights=(
                    deterministic_insights
                ),
                business_recommendations=(
                    business_recommendations
                ),
                ai_analysis=ai_analysis,
            )

        # Cache the generated report for this session.
        st.session_state["generated_pdf_report"] = (
            pdf_bytes
        )

        st.session_state["generated_pdf_name"] = (
            dataset_name
        )

        st.success(
            "Your PDF report has been generated successfully!"
        )

    except Exception as error:

        st.error(
            "The PDF report could not be generated."
        )

        st.exception(error)


# ==========================================================
# DOWNLOAD GENERATED PDF
# ==========================================================

pdf_bytes = st.session_state.get(
    "generated_pdf_report"
)

pdf_dataset_name = st.session_state.get(
    "generated_pdf_name"
)


if (
    pdf_bytes is not None
    and pdf_dataset_name == dataset_name
):

    safe_filename = (
        str(dataset_name)
        .rsplit(".", 1)[0]
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    st.download_button(
        label="⬇️ Download Business Analysis PDF",
        data=pdf_bytes,
        file_name=f"InsightFlow_Report_{safe_filename}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.caption(
        "Your report is ready to download."
    )