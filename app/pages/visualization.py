import streamlit as st


st.title("Visualizations")

if "dataset" not in st.session_state:
    st.info("Upload a dataset to begin analysis.")
    st.stop()

df = st.session_state["dataset"]
dataset_name = st.session_state["dataset_name"]

st.success(f"Active dataset: {dataset_name}")

st.write("Shape:", df.shape)

st.dataframe(df.head(10))