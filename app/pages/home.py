import streamlit as st

st.title("Welcome to Insightflow")

st.subheader(
    "Turn raw business data into decisions."
)

st.write(
     """
    InsightFlow AI is an intelligent analytics platform that helps analysts
    transform raw datasets into clean data, meaningful visualizations,
    business insights, and actionable recommendations.
    """
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Data Profiling",
        value="Automated"

    )

with col2:
    st.metric(
        label="AI Insights",
        value="Powered"

    )

with col3:
    st.metric(
        label="Reports",
        value="Exportable",
    )


st.divider()

st.markdown("### How InsightFlow works")

st.markdown(
    """
    **1. Upload** your CSV or Excel dataset.

    **2. Profile & clean** your data automatically.

    **3. Explore** trends, distributions, and KPIs.

    **4. Generate AI-powered** business insights.

    **5. Export** a professional analytics report.
    """
)



        