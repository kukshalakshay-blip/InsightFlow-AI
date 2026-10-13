import pandas as pd
from streamlit.testing.v1 import AppTest


from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

UPLOAD_PAGE = PROJECT_ROOT / "app" / "pages" / "upload.py"


def test_upload_page_renders_without_uploaded_file():
    app = AppTest.from_file(UPLOAD_PAGE).run()

    assert not app.exception
    assert any(
        "Data Upload" in title.value
        for title in app.title
    )


def test_upload_page_displays_upload_instructions():
    app = AppTest.from_file(UPLOAD_PAGE).run()

    assert not app.exception

    displayed_text = [
        element.value
        for element in app.markdown
    ]

    assert any(
        "Upload a CSV or Excel dataset"
        in text
        for text in displayed_text
    )


def test_upload_page_contains_file_uploader():
    app = AppTest.from_file(UPLOAD_PAGE).run()

    assert not app.exception
    assert len(app.get("file_uploader")) == 1


def test_invalid_dataset_validation_does_not_replace_existing_state():
    """
    Verify the intended state-preservation policy at the
    validation-service level.

    This does not simulate an actual Streamlit file upload.
    """

    from app.services.data_validator import validate_dataset

    existing_dataset = pd.DataFrame({
        "sales": [100, 200],
    })

    invalid_dataset = pd.DataFrame()

    state = {
        "dataset": existing_dataset,
        "dataset_name": "previous.csv",
    }

    validation = validate_dataset(invalid_dataset)

    assert not validation.is_valid

    # Validation itself must not mutate existing session state.
    assert state["dataset_name"] == "previous.csv"
    pd.testing.assert_frame_equal(
        state["dataset"],
        existing_dataset,
    )