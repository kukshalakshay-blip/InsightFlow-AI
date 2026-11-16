"""InsightFlow landing page. Place at: app/pages/home.py"""
import streamlit as st

from app.assets.ui_components import (
    render_hero,
    render_ticker,
    render_metric_card,
    render_step_card,
)

has_data = "dataset" in st.session_state
has_ai = st.session_state.get("ai_analysis") is not None
has_report = st.session_state.get("generated_pdf_report") is not None

# ----------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------
render_hero(
    eyebrow="AI-powered analytics",
    title="From raw data to",
    highlight="clear business decisions.",
    body=(
        "Upload a dataset, understand its quality, explore the patterns, "
        "and turn evidence into practical recommendations and reports."
    ),
)

render_ticker()

cta = st.columns([1, 1, 2])
if has_data:
    cta[0].page_link("app/pages/visualization.py", label="Explore charts", icon="📊", use_container_width=True)
    cta[1].page_link("app/pages/insights.py", label="AI insights", icon="💡", use_container_width=True)
else:
    cta[0].page_link("app/pages/upload.py", label="Upload dataset", icon="📤", use_container_width=True)

# ----------------------------------------------------------------------
# Live workspace stats (real values only)
# ----------------------------------------------------------------------
st.markdown("### Workspace overview")

if has_data:
    df = st.session_state["dataset"]
    rows, cols = len(df), len(df.columns)
    missing = int(df.isna().sum().sum())
    total_cells = max(rows * cols, 1)
    completeness = 100 * (1 - missing / total_cells)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Rows", f"{rows:,}")
    with c2:
        render_metric_card("Columns", f"{cols:,}")
    with c3:
        render_metric_card(
            "Missing cells", f"{missing:,}",
            delta=f"{100 - completeness:.1f}% of cells",
            trend="down" if missing else "flat",
        )
    with c4:
        render_metric_card(
            "Completeness", f"{completeness:.1f}%",
            delta="Clean" if missing == 0 else "Has gaps",
            trend="up" if missing == 0 else "flat",
        )
else:
    st.caption("Upload a CSV or Excel file to see live statistics here.")

# ----------------------------------------------------------------------
# Workflow with progress
# ----------------------------------------------------------------------
st.markdown("### Your analysis workflow")


def _status(done: bool, needs_data: bool = True) -> str:
    if done:
        return "done"
    return "ready" if (has_data or not needs_data) else "locked"


steps = [
    ("01", "Upload", "Bring in a CSV or Excel dataset and validate its structure.",
     "done" if has_data else "next"),
    ("02", "Profile", "Inspect dimensions, missing values, duplicates and column types.",
     _status(False)),
    ("03", "Explore", "Review recommended charts and data-driven findings.",
     _status(False)),
    ("04", "Interpret", "Generate business recommendations and Gemini analysis.",
     _status(has_ai)),
    ("05", "Report", "Export a shareable PDF with findings and recommendations.",
     _status(has_report)),
]

for column, (num, title, desc, status) in zip(st.columns(5, gap="small"), steps):
    with column:
        render_step_card(num, title, desc, status)

# ----------------------------------------------------------------------
# Quick navigation (Reports was missing before)
# ----------------------------------------------------------------------
st.markdown("### Jump to")
nav = st.columns(5)
nav[0].page_link("app/pages/upload.py", label="Data Upload", icon="📤", use_container_width=True)
nav[1].page_link("app/pages/profile.py", label="Profile", icon="🔎", use_container_width=True)
nav[2].page_link("app/pages/visualization.py", label="Visualizations", icon="📊", use_container_width=True)
nav[3].page_link("app/pages/insights.py", label="AI Insights", icon="💡", use_container_width=True)
nav[4].page_link("app/pages/reports.py", label="Reports", icon="📄", use_container_width=True)