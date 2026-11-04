"""InsightFlow landing page and guided entry point."""
import streamlit as st

st.title("InsightFlow AI")
st.subheader("From raw data to clear business decisions.")
st.markdown(
    "Upload a dataset, understand its quality, explore the patterns, "
    "and turn evidence into practical recommendations and reports."
)

st.divider()

if "dataset" in st.session_state:
    active_name = st.session_state.get("dataset_name", "Unnamed dataset")
    active_df = st.session_state["dataset"]
    st.success(f"Workspace ready · Active dataset: **{active_name}**")
    metric_columns = st.columns(3)
    metric_columns[0].metric("Rows", f"{len(active_df):,}")
    metric_columns[1].metric("Columns", f"{len(active_df.columns):,}")
    metric_columns[2].metric("Missing cells", f"{int(active_df.isna().sum().sum()):,}")
else:
    st.info("Your workspace is ready. Upload a CSV or Excel dataset to begin.")
    st.page_link(
        "app/pages/upload.py",
        label="Upload your first dataset",
        icon="📤",
        use_container_width=True,
    )

st.divider()
st.header("Your analysis workflow")

steps = [
    ("01 · Upload", "Bring in a CSV or Excel dataset and validate its structure."),
    ("02 · Profile", "Inspect dimensions, missing values, duplicates and column characteristics."),
    ("03 · Explore", "Review automatically recommended charts and data-driven findings."),
    ("04 · Interpret", "Generate business recommendations and optional Gemini analysis."),
    ("05 · Report", "Export a shareable PDF with findings and recommendations."),
]

for left, right in zip(st.columns(5), steps):
    with left:
        with st.container(border=True):
            st.markdown(f"**{right[0]}**")
            st.caption(right[1])

st.divider()
st.header("Workspace")
nav = st.columns(4)
nav[0].page_link("app/pages/upload.py", label="Data Upload", icon="📤", use_container_width=True)
nav[1].page_link("app/pages/profile.py", label="Dataset Profile", icon="🔎", use_container_width=True)
nav[2].page_link("app/pages/visualization.py", label="Visualizations", icon="📊", use_container_width=True)
nav[3].page_link("app/pages/insights.py", label="AI Insights", icon="💡", use_container_width=True)
