import streamlit as st

from app.services.profiler import profile_dataset


st.title("Dataset Profile")

st.write(
    "Understand the structure, quality, and characteristics "
    "of your dataset."
)


# --------------------------------------------------
# Check whether a dataset is available
# --------------------------------------------------

if "dataset" not in st.session_state:

    st.info(
        "No dataset is currently loaded. "
        "Go to Data Upload and upload a dataset first."
    )

    st.stop()


# --------------------------------------------------
# Retrieve active dataset
# --------------------------------------------------

df = st.session_state["dataset"]
dataset_name = st.session_state.get(
    "dataset_name",
    "Unnamed dataset",
)


# --------------------------------------------------
# Generate profile
# --------------------------------------------------

profile = profile_dataset(df)


# --------------------------------------------------
# Dataset information
# --------------------------------------------------

st.success(
    f"Active dataset: {dataset_name}"
)

st.divider()


# --------------------------------------------------
# Overview metrics
# --------------------------------------------------

st.subheader("Dataset Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Rows",
        f"{profile['rows']:,}",
    )

with col2:
    st.metric(
        "Columns",
        f"{profile['columns']:,}",
    )

with col3:
    st.metric(
        "Missing Cells",
        f"{profile['missing_cells']:,}",
    )

with col4:
    st.metric(
        "Duplicate Rows",
        f"{profile['duplicate_rows']:,}",
    )


st.divider()


# --------------------------------------------------
# Data quality
# --------------------------------------------------

st.subheader("Data Quality")

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Missing Data",
        f"{profile['missing_percentage']:.2f}%",
    )

with col2:

    st.metric(
        "Duplicate Rows",
        f"{profile['duplicate_rows']:,}",
    )


st.divider()


# --------------------------------------------------
# Column types
# --------------------------------------------------

st.subheader("Column Classification")

col1, col2 = st.columns(2)

with col1:

    st.write("### Numeric Columns")

    if profile["numeric_columns"]:
        for column in profile["numeric_columns"]:
            st.write(f"- {column}")
    else:
        st.caption("No numeric columns found.")


with col2:

    st.write("### Categorical Columns")

    if profile["categorical_columns"]:
        for column in profile["categorical_columns"]:
            st.write(f"- {column}")
    else:
        st.caption("No categorical columns found.")


st.divider()


# --------------------------------------------------
# Column-level profiling
# --------------------------------------------------

st.subheader("Column Profile")

column_profiles = profile["column_profiles"]


profile_rows = []

for column, details in column_profiles.items():

    profile_rows.append(
        {
            "Column": column,
            "Data Type": details["dtype"],
            "Missing": details["missing_count"],
            "Missing %": round(
                details["missing_percentage"],
                2,
            ),
            "Unique Values": details["unique_values"],
            "Unique %": round(
                details["unique_percentage"],
                2,
            ),
        }
    )


st.dataframe(
    profile_rows,
    use_container_width=True,
    hide_index=True,
)