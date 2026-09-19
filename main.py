import streamlit as st


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="InsightFlow AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# Page definitions
# --------------------------------------------------

home = st.Page(
    "app/pages/home.py",
    title="Home",
    icon="🏠",
    default=True,
)

upload = st.Page(
    "app/pages/upload.py",
    title="Data Upload",
    icon="📤",
)

profile = st.Page(
    "app/pages/profile.py",
    title="Profile",
    icon="👤",
)

visualization = st.Page(
    "app/pages/visualization.py",
    title="Visualizations",
    icon="📊",
)

insights = st.Page(
    "app/pages/insights.py",
    title="AI Insights",
    icon="💡",
)

reports = st.Page(
    "app/pages/reports.py",
    title="Reports",
    icon="📄",
)


# --------------------------------------------------
# Navigation
# --------------------------------------------------

pg = st.navigation(
    {
        "Workspace": [
            home,
            upload,
            profile,
            visualization,
        ],
        "Intelligence": [
            insights,
            reports,
        ],
    }
)


# --------------------------------------------------
# Run selected page
# --------------------------------------------------

pg.run()