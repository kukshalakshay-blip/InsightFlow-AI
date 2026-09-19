import streamlit as st

from app.services.data_loader import load_dataset
from app.services.data_validator import validate_dataset

st.title("Data Upload")

st.write(
    "Upload a CSV or Excel dataset to begin your analysis."
)


uploaded_file = st.file_uploader(
    "Choose a dataset",
    type=["csv", "xlsx", "xls"],
)


if uploaded_file is not None:

    try:
        df = load_dataset(uploaded_file)
        validation = validate_dataset(df)

        if not validation.is_valid:
            for error in validation.errors:
                st.error(error)

            st.stop()

        for warning in validation.warnings:
            st.warning(warning)

        st.session_state["dataset"] = df
        st.session_state["dataset_name"] = uploaded_file.name

        st.success(
            f"Successfully loaded {uploaded_file.name}"
        )

        st.divider()

        st.subheader("Dataset Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Rows",
                f"{df.shape[0]:,}",
            )

        with col2:
            st.metric(
                "Columns",
                f"{df.shape[1]:,}",
            )

        with col3:
            st.metric(
                "Missing Values",
                f"{df.isna().sum().sum():,}",
            )

        st.divider()

        st.subheader("Data Preview")

        st.dataframe(
            df.head(100),
            use_container_width=True,
        )

    except Exception as error:

        st.error(
            f"Unable to load the dataset: {error}"
        )