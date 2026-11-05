"""Dataset upload page with rerun-safe processing and AI understanding."""
from __future__ import annotations

import hashlib
from io import BytesIO

import pandas as pd
import streamlit as st

from app.core.settings import settings
from app.intelligence.dataset_understanding import understand_dataset
from app.services.upload_service import process_uploaded_dataset

MAX_UPLOAD_MB = settings.max_upload_mb
SUPPORTED_TYPES = ["csv", "xlsx", "xls"]


def _clear_dataset_derived_state() -> None:
    """Invalidate all analysis, report, and intelligence artifacts on replacement."""
    for key in (
        "ai_analysis", "ai_analysis_signature", "generated_pdf_report",
        "generated_pdf_name", "generated_pdf_shape", "generated_pdf_signature",
        "analysis_result", "dataset_understanding", "dataset_understanding_signature",
        "dataset_understanding_error", "dataset_understanding_attempted_signature",
    ):
        st.session_state.pop(key, None)


def _run_dataset_understanding(df: pd.DataFrame, signature: str) -> None:
    """Run once per dataset signature; cache both success and failure for rerun safety."""
    st.session_state["dataset_understanding_attempted_signature"] = signature
    try:
        with st.spinner("Understanding dataset domain and column semantics..."):
            understanding = understand_dataset(df)
        st.session_state["dataset_understanding"] = understanding.model_dump()
        st.session_state["dataset_understanding_signature"] = signature
        st.session_state["dataset_understanding_error"] = None
    except Exception as exc:  # AI failure must never block deterministic analysis.
        st.session_state["dataset_understanding"] = None
        st.session_state["dataset_understanding_signature"] = None
        st.session_state["dataset_understanding_error"] = str(exc)[:500]


def _render_dataset_understanding(signature: str) -> None:
    """Render the cached intelligence profile, with an explicit retry on failure."""
    profile = st.session_state.get("dataset_understanding")
    error = st.session_state.get("dataset_understanding_error")
    if profile and st.session_state.get("dataset_understanding_signature") == signature:
        with st.expander("AI Dataset Understanding", expanded=True):
            st.markdown(f"**Domain:** `{profile['domain']}`")
            if profile.get("subdomain"):
                st.markdown(f"**Subdomain:** {profile['subdomain']}")
            left, right = st.columns(2)
            left.metric("Understanding confidence", f"{profile['confidence']:.0%}")
            right.metric("Dataset type", profile["dataset_kind"])
            st.write(profile["rationale"])
            meanings = profile.get("column_meanings", [])
            if meanings:
                st.markdown("**Column semantics**")
                st.dataframe(pd.DataFrame(meanings), use_container_width=True, hide_index=True)
            if profile.get("analysis_priorities"):
                st.markdown("**Suggested analysis priorities**")
                for priority in profile["analysis_priorities"]:
                    st.markdown(f"- {priority}")
            if profile.get("limitations"):
                st.markdown("**Interpretation limitations**")
                for limitation in profile["limitations"]:
                    st.caption(f"• {limitation}")
    elif error:
        st.warning("AI dataset understanding is unavailable. Your dataset and standard analysis remain available.")
        with st.expander("Understanding status"):
            st.caption(error)
            if st.button("Retry AI understanding", key="retry_dataset_understanding"):
                _run_dataset_understanding(st.session_state["dataset"], signature)
                st.rerun()


st.title("Data Upload")
st.markdown("Upload a CSV or Excel dataset to begin your analysis.")
st.caption(f"Supported formats: CSV, XLSX and XLS · Maximum file size: {MAX_UPLOAD_MB} MB")

uploaded_file = st.file_uploader(
    "Choose a dataset", type=SUPPORTED_TYPES,
    help="Your dataset is processed in this Streamlit session. It is not saved to a database.",
)

if uploaded_file is None:
    if "dataset" in st.session_state:
        st.success(f"Active dataset: {st.session_state.get('dataset_name', 'Unnamed dataset')}")
        st.caption("Your currently loaded dataset remains available until you replace it or restart the session.")
        active_signature = st.session_state.get("active_dataset_signature")
        if active_signature and st.session_state.get("dataset_understanding_attempted_signature") != active_signature:
            _run_dataset_understanding(st.session_state["dataset"], active_signature)
        if active_signature:
            _render_dataset_understanding(active_signature)
    else:
        st.info("Choose a CSV or Excel file to start analysing your data.")
    st.stop()

file_bytes = uploaded_file.getvalue()
file_signature = hashlib.sha256(uploaded_file.name.encode("utf-8") + b"\0" + file_bytes).hexdigest()
if len(file_bytes) > MAX_UPLOAD_MB * 1024 * 1024:
    st.error(f"File exceeds the {MAX_UPLOAD_MB} MB upload limit.")
    st.stop()

if st.session_state.get("processed_upload_signature") != file_signature:
    upload_buffer = BytesIO(file_bytes)
    upload_buffer.name = uploaded_file.name
    with st.spinner("Loading and validating your dataset..."):
        result = process_uploaded_dataset(upload_buffer)
    st.session_state["processed_upload_signature"] = file_signature
    st.session_state["processed_upload_result"] = result
else:
    result = st.session_state["processed_upload_result"]

if result.error:
    st.error(f"Unable to load the dataset: {result.error}")
    st.info("Your previously loaded valid dataset, if any, has been preserved.")
    st.stop()
if result.validation is not None and not result.validation.is_valid:
    st.error("The uploaded dataset failed validation.")
    for error in result.validation.errors:
        st.error(error)
    st.info("Your previously loaded valid dataset, if any, has been preserved.")
    st.stop()

if result.is_successful and result.dataframe is not None:
    df = result.dataframe
    previous_signature = st.session_state.get("active_dataset_signature")
    if previous_signature != file_signature:
        _clear_dataset_derived_state()
    st.session_state["dataset"] = df
    st.session_state["dataset_name"] = uploaded_file.name
    st.session_state["active_dataset_signature"] = file_signature

    st.success(f"Successfully loaded {uploaded_file.name}")
    st.divider()
    st.subheader("Dataset Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", f"{df.shape[0]:,}")
    col2.metric("Columns", f"{df.shape[1]:,}")
    col3.metric("Missing Values", f"{int(df.isna().sum().sum()):,}")

    if result.validation is not None:
        for warning in result.validation.warnings:
            st.warning(warning)

    # A failed Gemini call is cached too, so normal Streamlit reruns do not
    # repeatedly spend API calls. The user can retry explicitly from the UI.
    if st.session_state.get("dataset_understanding_attempted_signature") != file_signature:
        _run_dataset_understanding(df, file_signature)
    _render_dataset_understanding(file_signature)

    st.divider()
    st.subheader("Data Preview")
    st.dataframe(df.head(100), use_container_width=True, hide_index=True)
    st.caption(f"Previewing the first {min(len(df), 100):,} of {len(df):,} rows.")
