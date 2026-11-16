"""Visualizations page. Place at: app/pages/visualization.py"""
import html

import streamlit as st

from app.assets.ui_components import (
    card,
    render_empty_state,
    render_header,
    render_metric_card,
    style_figure,
)
from app.services.chart_renderer import render_chart
from app.services.insight_engine import generate_insight
from app.services.visualization_engine import recommend_visualizations

render_header(
    title="Visualizations",
    subtitle="Automatically recommended charts based on the structure of your dataset.",
    badge="Auto-recommended",
)

# ----------------------------------------------------------------------
# Guard
# ----------------------------------------------------------------------
if "dataset" not in st.session_state:
    render_empty_state(
        icon="📊",
        title="No dataset loaded",
        message="Upload a CSV or Excel file and InsightFlow will recommend the best charts for it.",
        page="app/pages/upload.py",
        label="Go to Data Upload",
        cta_icon="📤",
    )
    st.stop()

df = st.session_state["dataset"]

# Use the AI profile only if it belongs to the active dataset.
active_signature = st.session_state.get("active_dataset_signature")
understanding = None
if st.session_state.get("dataset_understanding_signature") == active_signature:
    understanding = st.session_state.get("dataset_understanding")

recommendations = recommend_visualizations(
    df,
    max_recommendations=10,
    understanding=understanding,
)

# ----------------------------------------------------------------------
# Summary row
# ----------------------------------------------------------------------
c1, c2, c3 = st.columns(3)
with c1:
    render_metric_card("Rows", f"{df.shape[0]:,}")
with c2:
    render_metric_card("Columns", f"{df.shape[1]:,}")
with c3:
    render_metric_card("Charts recommended", f"{len(recommendations)}")

st.markdown("")

# ----------------------------------------------------------------------
# Chart cards
# ----------------------------------------------------------------------
for index, recommendation in enumerate(recommendations, start=1):
    chart_type = str(recommendation["type"]).title()
    score = recommendation["score"]
    reason = recommendation["reason"]
    insight = generate_insight(df, recommendation)

    with card(f"viz_{index}"):
        left, right = st.columns([1, 1.5], gap="large")

        with left:
            st.markdown(
                f'<span class="if-pill if-pill--ready">#{index} · {html.escape(chart_type)}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"#### {chart_type} analysis")
            st.caption(f"Recommendation score {score:.2f}")
            st.write(f"**Why this chart:** {reason}")
            st.info(f"**Insight:** {insight}")

        with right:
            try:
                figure = style_figure(render_chart(df, recommendation))
                st.plotly_chart(figure, use_container_width=True, theme=None)
            except Exception as error:
                st.error(f"Unable to render this visualization: {error}")

    st.markdown("")