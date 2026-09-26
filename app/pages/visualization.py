import streamlit as st

from app.services.visualization_engine import (
    recommend_visualizations,
)

from app.services.chart_renderer import (
    render_chart,
)


st.title("Visualizations")

st.write(
    "Explore automatically recommended visualizations "
    "based on the structure and characteristics of your dataset."
)


# --------------------------------------------------
# Check whether a dataset exists
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


st.success(
    f"Active dataset: {dataset_name}"
)


st.divider()


# --------------------------------------------------
# Generate visualization recommendations
# --------------------------------------------------

recommendations = recommend_visualizations(
    df,
    max_recommendations=10,
)


st.subheader("Recommended Visualizations")

st.write(
    f"InsightFlow found {len(recommendations)} "
    "visualizations worth exploring."
)


# --------------------------------------------------
# Render recommendations
# --------------------------------------------------

for index, recommendation in enumerate(
    recommendations,
    start=1,
):

    chart_type = recommendation["type"]

    score = recommendation["score"]

    reason = recommendation["reason"]


    st.markdown(
        f"### {index}. "
        f"{chart_type.title()}"
    )

    st.caption(
        f"Recommendation score: {score:.2f}"
    )

    st.write(reason)


    try:

        figure = render_chart(
            df,
            recommendation,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )

    except Exception as error:

        st.error(
            f"Unable to render this visualization: "
            f"{error}"
        )


    st.divider()