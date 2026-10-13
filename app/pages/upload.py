import streamlit as st

from app.services.upload_service import process_uploaded_dataset


st.title("Data Upload")

st.write(
    "Upload a CSV or Excel dataset to begin your analysis."
)


uploaded_file = st.file_uploader(
    "Choose a dataset",
    type=["csv", "xlsx", "xls"],
)


if uploaded_file is not None:

    # Step 1: Process the uploaded file through our upload service.
    result = process_uploaded_dataset(uploaded_file)

    # Step 2: Handle file-loading errors.
    if result.error:
        st.error(
            f"Unable to load the dataset: {result.error}"
        )

    # Step 3: Handle validation errors.
    elif (
        result.validation is not None
        and not result.validation.is_valid
    ):
        st.error(
            "The uploaded dataset failed validation."
        )

        for error in result.validation.errors:
            st.error(error)

    # Step 4: Display the dataset if processing succeeds.
    elif result.is_successful and (df := result.dataframe) is not None:

        # Display warnings without rejecting the dataset.
        if result.validation is not None:
            for warning in result.validation.warnings:
                st.warning(warning)

        # Store the dataset for use by other application pages.
        st.session_state["dataset"] = df
        st.session_state["dataset_name"] = uploaded_file.name

        st.success(
            f"Successfully loaded {uploaded_file.name}"
        )

        # Dataset overview.
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
            missing_values = int(df.isna().sum().sum())

            st.metric(
                "Missing Values",
                f"{missing_values:,}",
            )

        # Dataset preview.
        st.divider()

        st.subheader("Data Preview")

        st.dataframe(
            df.head(100),
            use_container_width=True,
        )