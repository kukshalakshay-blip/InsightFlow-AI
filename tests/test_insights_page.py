"""Streamlit smoke tests for the Insights page's primary states."""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSIGHTS_PAGE = PROJECT_ROOT / "app" / "pages" / "insights.py"


def test_insights_page_guides_user_when_no_dataset_is_loaded():
    app = AppTest.from_file(INSIGHTS_PAGE).run()

    assert not app.exception
    assert any("No dataset is currently loaded" in item.value for item in app.warning)


def test_insights_page_renders_deterministic_analysis_without_gemini_key():
    app = AppTest.from_file(INSIGHTS_PAGE)
    app.session_state["dataset"] = pd.DataFrame(
        {
            "segment": ["A", "A", "B", "B", "C", "C"],
            "revenue": [100, 120, 180, 200, 250, 275],
            "profit": [10, 15, 25, 30, 40, 45],
        }
    )
    app.session_state["dataset_name"] = "sample.csv"
    app.run()

    assert not app.exception
    rendered_titles = [item.value for item in app.header]
    assert "📊 Deterministic Insights" in rendered_titles
    assert "🎯 Business Recommendations" in rendered_titles
    assert "🧠 AI Business Analysis" in rendered_titles
