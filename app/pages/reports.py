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

from app.services.chart_export_service import (
    generate_chart_images,
)


# ==========================================================
# PAGE HEADER
# ==========================================================

st.title("📄 InsightFlow Reports")

st.markdown(
    """
Generate a downloadable **business analysis report** containing:

- Dataset statistics and data-quality metrics
- Automatically generated visualizations
- Analytical findings
- Prioritized business recommendations
- AI-generated executive summaries and insights, when available
"""
)

st.divider()


# ==========================================================
# CHECK DATASET
# ==========================================================

if "dataset" not in st.session_state:

    # Clear any previously generated report.
    st.session_state.pop(
        "generated_pdf_report",
        None,
    )

    st.session_state.pop(
        "generated_pdf_name",
        None,
    )

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
# INVALIDATE STALE REPORTS
# ==========================================================

# A report generated for a previous dataset must not be
# offered as the report for the current dataset.

report_dataset_name = st.session_state.get(
    "generated_pdf_name"
)

report_dataset_shape = st.session_state.get(
    "generated_pdf_shape"
)

current_dataset_shape = (
    int(df.shape[0]),
    int(df.shape[1]),
)

if (
    report_dataset_name != dataset_name
    or report_dataset_shape != current_dataset_shape
):

    st.session_state.pop(
        "generated_pdf_report",
        None,
    )

    st.session_state.pop(
        "generated_pdf_name",
        None,
    )

    st.session_state.pop(
        "generated_pdf_shape",
        None,
)


# ==========================================================
# REPORT OVERVIEW
# ==========================================================

st.subheader("📊 Report Overview")

metric_col1, metric_col2, metric_col3 = st.columns(3)

with metric_col1:
    st.metric(
        "Dataset Rows",
        f"{len(df):,}",
    )

with metric_col2:
    st.metric(
        "Dataset Columns",
        f"{len(df.columns):,}",
    )

with metric_col3:
    st.metric(
        "Missing Cells",
        f"{int(df.isna().sum().sum()):,}",
    )


# ==========================================================
# PREPARE REPORT DATA
# ==========================================================

try:

    visualization_recommendations = (
        recommend_visualizations(df)
    )

    business_recommendations = (
        generate_business_recommendations(
            df,
            visualization_recommendations,
        )
    )

except Exception as error:

    st.error(
        "Unable to prepare the analytical findings "
        "for this dataset."
    )

    st.exception(error)

    st.stop()


# ==========================================================
# BUILD DETERMINISTIC INSIGHTS
# ==========================================================

deterministic_insights = []

for index, recommendation in enumerate(
    visualization_recommendations,
    start=1,
):

    try:

        insight_text = generate_insight(
            df,
            recommendation,
        )

        deterministic_insights.append(
            {
                "title": (
                    f"{recommendation.get('type', 'Analysis').title()} "
                    f"Finding {index}"
                ),
                "text": str(insight_text),
            }
        )

    except Exception as error:

        # Preserve the rest of the report if one finding fails.
        st.warning(
            f"Finding {index} could not be generated: {error}"
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
    f"""
    - Dataset overview and data-quality statistics
    - Analytical findings: {len(deterministic_insights)}
    - Business recommendations: {len(business_recommendations)}
    - Automatically generated charts, when export succeeds
    - AI executive summary and key findings, when available
    - AI recommendations and risks, when available
    """
)

if ai_analysis is None:

    st.warning(
        "AI analysis has not been generated for this session. "
        "You can still create a report without the AI sections."
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

    # Remove the previous report before generating a new one.
    st.session_state.pop(
        "generated_pdf_report",
        None,
    )

    st.session_state.pop(
        "generated_pdf_name",
        None,
    )

    st.session_state.pop(
        "generated_pdf_shape",
        None,
    )

    try:

        # --------------------------------------------------
        # DATASET PROFILE
        # --------------------------------------------------

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

        # --------------------------------------------------
        # EXPORT CHARTS
        # --------------------------------------------------

        chart_images = []

        if visualization_recommendations:

            with st.spinner(
                "Generating chart images for your report..."
            ):

                try:

                    chart_images = generate_chart_images(
                        df,
                        max_charts=3,
                    )

                    if chart_images:

                        st.success(
                            f"Prepared {len(chart_images)} "
                            "chart image(s) for the report."
                        )

                    else:

                        st.warning(
                            "No chart images were available. "
                            "The PDF will still include the "
                            "analytical findings and recommendations."
                        )

                except Exception as chart_error:

                    # Chart export should not prevent PDF creation.
                    st.warning(
                        "Chart export failed. Continuing without "
                        "embedded charts."
                    )

                    st.caption(
                        f"Chart export details: {chart_error}"
                    )

        # --------------------------------------------------
        # BUILD PDF
        # --------------------------------------------------

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
                chart_images=chart_images,
            )

        # --------------------------------------------------
        # VALIDATE GENERATED PDF
        # --------------------------------------------------

        if (
            not isinstance(pdf_bytes, bytes)
            or not pdf_bytes.startswith(b"%PDF")
        ):

            raise ValueError(
                "The report generator did not return "
                "a valid PDF document."
            )

        # --------------------------------------------------
        # CACHE GENERATED REPORT
        # --------------------------------------------------

        st.session_state["generated_pdf_report"] = (
            pdf_bytes
        )

        st.session_state["generated_pdf_name"] = (
            dataset_name
        )

        st.session_state["generated_pdf_shape"] = (
            int(df.shape[0]),
            int(df.shape[1]),
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

pdf_dataset_shape = st.session_state.get(
    "generated_pdf_shape"
)

current_dataset_shape = (
    int(df.shape[0]),
    int(df.shape[1]),
)


if (
    pdf_bytes is not None
    and pdf_dataset_name == dataset_name
    and pdf_dataset_shape == current_dataset_shape
):

    # Create a filesystem-safe download filename.
    safe_filename = (
        str(dataset_name)
        .rsplit(".", 1)[0]
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    st.divider()

    st.download_button(
        label="⬇️ Download Business Analysis PDF",
        data=pdf_bytes,
        file_name=(
            f"InsightFlow_Report_{safe_filename}.pdf"
        ),
        mime="application/pdf",
        use_container_width=True,
    )

    st.caption(
        "Your report is ready to download."
    )