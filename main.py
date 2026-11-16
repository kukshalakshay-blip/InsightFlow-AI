import streamlit as st

from app.assets.styles import load_custom_css
from app.assets.ui_components import render_sidebar_status

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="InsightFlow AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Theme is loaded ONCE here; pages do not need to call load_custom_css().
load_custom_css()

# --------------------------------------------------
# Pages
# --------------------------------------------------
home = st.Page("app/pages/home.py", title="Home", icon="🏠", default=True)
upload = st.Page("app/pages/upload.py", title="Data Upload", icon="📤")
profile = st.Page("app/pages/profile.py", title="Profile", icon="👤")
visualization = st.Page("app/pages/visualization.py", title="Visualizations", icon="📊")
insights = st.Page("app/pages/insights.py", title="AI Insights", icon="💡")
reports = st.Page("app/pages/reports.py", title="Reports", icon="📄")

pg = st.navigation(
    {
        "Workspace": [home, upload, profile, visualization],
        "Intelligence": [insights, reports],
    }
)

pg.run()

# Rendered AFTER pg.run() so it reflects a dataset uploaded during this run.
render_sidebar_status()