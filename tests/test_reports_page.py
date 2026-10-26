import runpy
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.services.dataset_signature import generate_dataset_signature


REPORTS_PAGE = "app/pages/reports.py"


@pytest.fixture
def dataset():
    return pd.DataFrame(
        {
            "product": ["A", "B", "C"],
            "sales": [100, 200, 150],
        }
    )


@pytest.fixture
def page_mocks():
    """Mock Streamlit UI and external report-generation services."""
    patches = [
        patch("streamlit.title"),
        patch("streamlit.markdown"),
        patch("streamlit.divider"),
        patch("streamlit.subheader"),
        patch("streamlit.columns", return_value=[MagicMock() for _ in range(3)]),
        patch("streamlit.metric"),
        patch("streamlit.info"),
        patch("streamlit.warning"),
        patch("streamlit.success"),
        patch("streamlit.caption"),
        patch("streamlit.write"),
        patch("streamlit.page_link"),
        patch("streamlit.spinner"),
        patch("streamlit.error"),
        patch("streamlit.exception"),
        patch("streamlit.stop", side_effect=RuntimeError("STREAMLIT_STOP")),
        patch("streamlit.button", return_value=False),
        patch("streamlit.download_button"),
        patch(
            "app.services.visualization_engine.recommend_visualizations",
            return_value=[],
        ),
        patch(
            "app.services.recommendation_engine.generate_business_recommendations",
            return_value=[],
        ),
        patch(
            "app.services.insight_engine.generate_insight",
            return_value="Test insight",
        ),
        patch(
            "app.services.chart_export_service.generate_chart_images",
            return_value=[],
        ),
        patch(
    "app.services.report_generator.generate_pdf_report",
    return_value=b"%PDF-1.4 test",
    name="pdf_generator",
),
    ]

    started = []
    try:
        for item in patches:
            started.append(item.start())
        yield started
    finally:
        for item in reversed(patches):
            item.stop()


def run_page(state):
    """Execute the page using the supplied mocked session state."""
    with patch("streamlit.session_state", state):
        runpy.run_path(REPORTS_PAGE)


def test_no_dataset_clears_cached_pdf(page_mocks):
    state = {
        "generated_pdf_report": b"%PDF-old",
        "generated_pdf_name": "old.csv",
        "generated_pdf_shape": (3, 2),
        "generated_pdf_signature": "old-signature",
    }

    with pytest.raises(RuntimeError, match="STREAMLIT_STOP"):
        run_page(state)

    assert "generated_pdf_report" not in state
    assert "generated_pdf_name" not in state
    assert "generated_pdf_shape" not in state
    assert "generated_pdf_signature" not in state


def test_stale_pdf_is_not_offered_for_download(dataset, page_mocks):
    state = {
        "dataset": dataset,
        "dataset_name": "sales.csv",
        "generated_pdf_report": b"%PDF-old",
        "generated_pdf_name": "sales.csv",
        "generated_pdf_shape": (3, 2),
        "generated_pdf_signature": "incorrect-signature",
    }

    download_button = page_mocks[17]

    run_page(state)

    download_button.assert_not_called()
    assert "generated_pdf_report" not in state


def test_stale_ai_analysis_is_not_included(dataset, page_mocks):
    state = {
        "dataset": dataset,
        "dataset_name": "sales.csv",
        "ai_analysis": {"executive_summary": "Old dataset analysis"},
        "ai_analysis_signature": "incorrect-signature",
    }

    run_page(state)

    assert state["ai_analysis"] is None
    assert (
        state["ai_analysis_signature"]
        == generate_dataset_signature(dataset, "sales.csv")
    )


def test_current_pdf_is_offered_for_download(dataset, page_mocks):
    signature = generate_dataset_signature(dataset, "sales.csv")
    pdf = b"%PDF-1.4 valid test PDF"

    state = {
        "dataset": dataset,
        "dataset_name": "sales.csv",
        "generated_pdf_report": pdf,
        "generated_pdf_name": "sales.csv",
        "generated_pdf_shape": (3, 2),
        "generated_pdf_signature": signature,
    }

    download_button = page_mocks[17]

    run_page(state)

    download_button.assert_called_once()
    assert download_button.call_args.kwargs["data"] == pdf



def test_generate_button_caches_pdf_with_current_signature(
    dataset, page_mocks
):
    state = {
        "dataset": dataset,
        "dataset_name": "sales.csv",
    }

    expected_pdf = b"%PDF-1.4 generated"
    expected_signature = generate_dataset_signature(dataset, "sales.csv")

    with (
        patch("streamlit.session_state", state),
        patch("streamlit.button", return_value=True),
        patch(
            "app.services.report_generator.generate_pdf_report",
            return_value=expected_pdf,
        ) as pdf_generator,
    ):
        runpy.run_path(REPORTS_PAGE)

    pdf_generator.assert_called_once()

    assert state["generated_pdf_report"] == expected_pdf
    assert state["generated_pdf_name"] == "sales.csv"
    assert state["generated_pdf_shape"] == (3, 2)
    assert state["generated_pdf_signature"] == expected_signature


