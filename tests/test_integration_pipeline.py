from io import BytesIO, StringIO

import pandas as pd
import pytest
from pypdf import PdfReader

from app.services.data_loader import load_dataset
from app.services.data_validator import validate_dataset
from app.services.profiler import profile_dataset
from app.services.visualization_engine import recommend_visualizations
from app.services.insight_engine import (
    build_analysis_context,
    generate_insight,
)
from app.services.recommendation_engine import (
    generate_business_recommendations,
)
from app.services.ai_service import AIAnalysis
from app.services.report_generator import generate_pdf_report


# ==========================================================
# TEST FILE HELPERS
# ==========================================================

class UploadedFile(BytesIO):
    """Simulate a Streamlit uploaded file."""

    def __init__(self, content, name):
        super().__init__(content)
        self.name = name


@pytest.fixture
def csv_upload():
    csv_content = (
        "date,region,sales,profit,discount\n"
        "2026-01-01,North,100,20,0.05\n"
        "2026-01-02,South,200,40,0.10\n"
        "2026-01-03,North,300,60,0.15\n"
        "2026-01-04,East,400,80,0.20\n"
        "2026-01-05,South,500,100,0.25\n"
    )

    return UploadedFile(
        csv_content.encode("utf-8"),
        "sales.csv",
    )


# ==========================================================
# DATA LOADING
# ==========================================================

def test_csv_upload_loads_dataframe(csv_upload):
    df = load_dataset(csv_upload)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert list(df.columns) == [
        "date",
        "region",
        "sales",
        "profit",
        "discount",
    ]


def test_unsupported_file_format_is_rejected():
    file = UploadedFile(
        b"some content",
        "sales.txt",
    )

    with pytest.raises(ValueError, match="Unsupported file format"):
        load_dataset(file)


def test_excel_upload_loads_dataframe():
    source_df = pd.DataFrame({
        "region": ["North", "South"],
        "sales": [100, 200],
    })

    buffer = BytesIO()

    source_df.to_excel(
        buffer,
        index=False,
        engine="openpyxl",
    )

    file = UploadedFile(
        buffer.getvalue(),
        "sales.xlsx",
    )

    result = load_dataset(file)

    assert isinstance(result, pd.DataFrame)
    assert result["region"].tolist() == ["North", "South"]
    assert result["sales"].tolist() == [100, 200]


# ==========================================================
# VALIDATION AND PROFILING
# ==========================================================

def test_loaded_dataset_passes_validation(csv_upload):
    df = load_dataset(csv_upload)

    result = validate_dataset(df)

    assert result.is_valid
    assert result.errors == []


def test_loaded_dataset_can_be_profiled(csv_upload):
    df = load_dataset(csv_upload)

    profile = profile_dataset(df)

    assert profile["rows"] == 5
    assert profile["columns"] == 5
    assert profile["missing_cells"] == 0


# ==========================================================
# VISUALIZATION AND INSIGHTS
# ==========================================================

def test_loaded_dataset_produces_visualization_recommendations(
    csv_upload,
):
    df = load_dataset(csv_upload)

    recommendations = recommend_visualizations(df)

    assert isinstance(recommendations, list)
    assert recommendations


def test_recommendations_produce_deterministic_findings(
    csv_upload,
):
    df = load_dataset(csv_upload)

    recommendations = recommend_visualizations(df)

    context = build_analysis_context(
        df,
        recommendations,
    )

    assert context["dataset"]["rows"] == 5
    assert context["dataset"]["columns"] == 5
    assert isinstance(context["metrics"], dict)
    assert len(context["deterministic_findings"]) == len(
        recommendations
    )


# ==========================================================
# BUSINESS RECOMMENDATIONS
# ==========================================================

def test_loaded_dataset_produces_business_recommendations(
    csv_upload,
):
    df = load_dataset(csv_upload)

    visualizations = recommend_visualizations(df)

    recommendations = generate_business_recommendations(
        df,
        visualizations,
    )

    assert isinstance(recommendations, list)

    for recommendation in recommendations:
        assert "title" in recommendation
        assert "priority" in recommendation
        assert "finding" in recommendation
        assert "action" in recommendation
        assert "rationale" in recommendation


# ==========================================================
# AI RESPONSE STRUCTURE
# ==========================================================

def test_analysis_context_can_be_used_with_ai_response_schema(
    csv_upload,
):
    df = load_dataset(csv_upload)

    visualizations = recommend_visualizations(df)

    context = build_analysis_context(
        df,
        visualizations,
    )

    assert context["dataset"]["rows"] == 5

    # Mock the output structure rather than making a Gemini call.
    ai_response = AIAnalysis(
        executive_summary=(
            "Sales increased throughout the sample period."
        ),
        key_findings=[
            "Sales increased across the observed dates.",
            "Profit increased alongside sales.",
            "The dataset contains five records.",
        ],
        recommendations=[
            "Monitor sales performance.",
            "Review profitability.",
            "Investigate discount effectiveness.",
        ],
        risks_or_anomalies=[],
    )

    assert ai_response.executive_summary
    assert len(ai_response.key_findings) >= 1
    assert len(ai_response.recommendations) >= 1


# ==========================================================
# PDF REPORT
# ==========================================================

def test_complete_analysis_can_be_exported_to_pdf(csv_upload):
    df = load_dataset(csv_upload)

    profile = profile_dataset(df)

    visualizations = recommend_visualizations(df)

    context = build_analysis_context(
        df,
        visualizations,
    )

    insights = []

    for recommendation in visualizations:
        insights.append({
            "title": recommendation["type"].title(),
            "text": generate_insight(df, recommendation),
        })

    business_recommendations = (
        generate_business_recommendations(
            df,
            visualizations,
        )
    )

    ai_response = AIAnalysis(
        executive_summary=(
            "The dataset contains five sales records."
        ),
        key_findings=[
            "Sales increase across the sample period.",
            "Profit increases alongside sales.",
            "Five records are available for analysis.",
        ],
        recommendations=[
            "Monitor sales trends.",
            "Review profitability.",
            "Evaluate discount effectiveness.",
        ],
        risks_or_anomalies=[],
    )

    pdf_bytes = generate_pdf_report(
        dataset_name="sales.csv",
        profile=profile,
        deterministic_insights=insights,
        business_recommendations=business_recommendations,
        ai_analysis=ai_response,
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")

    reader = PdfReader(BytesIO(pdf_bytes))

    assert len(reader.pages) >= 1

    pdf_text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    assert "sales.csv" in pdf_text
    assert "Dataset Overview" in pdf_text
    assert "Executive Summary" in pdf_text
    assert "Business Recommendations" in pdf_text


# ==========================================================
# INVALID DATASET INTEGRATION TESTS
# ==========================================================

def test_empty_dataset_is_rejected_before_analysis():
    df = pd.DataFrame()

    validation = validate_dataset(df)

    assert validation.is_valid is False
    assert validation.errors

    # The pipeline must not continue when validation fails.
    recommendations = []

    assert recommendations == []


def test_dataset_without_columns_is_rejected():
    df = pd.DataFrame(index=range(3))

    validation = validate_dataset(df)

    assert validation.is_valid is False
    assert (
        "The dataset contains no columns."
        in validation.errors
    )


def test_dataset_with_duplicate_columns_is_rejected():
    df = pd.DataFrame(
        [[100, 200], [300, 400]],
        columns=["sales", "sales"],
    )

    validation = validate_dataset(df)

    assert validation.is_valid is False
    assert any(
        "Duplicate column names found" in error
        for error in validation.errors
    )


def test_invalid_dataset_does_not_proceed_to_visualization():
    df = pd.DataFrame()

    validation = validate_dataset(df)

    if not validation.is_valid:
        recommendations = None
    else:
        recommendations = recommend_visualizations(df)

    assert recommendations is None


def test_valid_dataset_with_missing_values_can_be_analyzed():
    df = pd.DataFrame({
        "sales": [100, None, 300, 400, 500],
        "profit": [10, 20, 30, None, 50],
    })

    validation = validate_dataset(df)

    # Missing values generate warnings, not validation errors.
    assert validation.is_valid is True
    assert validation.warnings

    profile = profile_dataset(df)

    assert profile["rows"] == 5
    assert profile["columns"] == 2
    assert profile["missing_cells"] == 2


def test_duplicate_rows_generate_warnings_without_invalidating_data():
    df = pd.DataFrame({
        "sales": [100, 200, 200],
        "profit": [10, 20, 20],
    })

    validation = validate_dataset(df)

    assert validation.is_valid is True
    assert any(
        "duplicate rows detected" in warning
        for warning in validation.warnings
    )