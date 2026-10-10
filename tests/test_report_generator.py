from io import BytesIO

import pytest
from pypdf import PdfReader

from app.services.report_generator import generate_pdf_report


@pytest.fixture
def sample_profile():
    return {
        "rows": 1000,
        "columns": 8,
        "missing_cells": 25,
        "duplicate_rows": 10,
    }


@pytest.fixture
def sample_insights():
    return [
        {
            "title": "Revenue Trend",
            "text": "Revenue increased by 15% during the reporting period.",
        },
        {
            "title": "Data Quality",
            "text": "A small number of missing values were detected.",
        },
    ]


@pytest.fixture
def sample_recommendations():
    return [
        {
            "title": "Improve Data Quality",
            "priority": "high",
            "finding": "Some records contain missing values.",
            "action": "Investigate the source of missing data.",
            "rationale": "Reliable data improves analytical accuracy.",
        }
    ]


def extract_pdf_text(pdf_bytes):
    """Extract readable text from generated PDF bytes."""
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )


def test_generates_valid_pdf(sample_profile):
    pdf_bytes = generate_pdf_report(
        dataset_name="sales.csv",
        profile=sample_profile,
        deterministic_insights=[],
        business_recommendations=[],
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 100


def test_report_contains_dataset_name(sample_profile):
    pdf_bytes = generate_pdf_report(
        dataset_name="sales.csv",
        profile=sample_profile,
        deterministic_insights=[],
        business_recommendations=[],
    )

    text = extract_pdf_text(pdf_bytes)

    assert "sales.csv" in text


def test_report_contains_profile_statistics(sample_profile):
    pdf_bytes = generate_pdf_report(
        dataset_name="sales.csv",
        profile=sample_profile,
        deterministic_insights=[],
        business_recommendations=[],
    )

    text = extract_pdf_text(pdf_bytes)

    assert "1,000" in text
    assert "8" in text
    assert "25" in text
    assert "10" in text


def test_empty_insights_and_recommendations_are_supported(
    sample_profile,
):
    pdf_bytes = generate_pdf_report(
        dataset_name="empty_findings.csv",
        profile=sample_profile,
        deterministic_insights=[],
        business_recommendations=[],
    )

    text = extract_pdf_text(pdf_bytes)

    assert "No deterministic findings were available." in text
    assert "No business recommendations were generated." in text


def test_deterministic_insights_appear_in_report(
    sample_profile,
    sample_insights,
):
    pdf_bytes = generate_pdf_report(
        dataset_name="sales.csv",
        profile=sample_profile,
        deterministic_insights=sample_insights,
        business_recommendations=[],
    )

    text = extract_pdf_text(pdf_bytes)

    assert "Revenue Trend" in text
    assert "increased by 15%" in text
    assert "Data Quality" in text


def test_business_recommendations_appear_in_report(
    sample_profile,
    sample_recommendations,
):
    pdf_bytes = generate_pdf_report(
        dataset_name="sales.csv",
        profile=sample_profile,
        deterministic_insights=[],
        business_recommendations=sample_recommendations,
    )

    text = extract_pdf_text(pdf_bytes)

    assert "Improve Data Quality" in text
    assert "HIGH PRIORITY" in text
    assert "Investigate the source" in text
    assert "Reliable data improves" in text


def test_missing_profile_fields_use_defaults():
    pdf_bytes = generate_pdf_report(
        dataset_name="minimal.csv",
        profile={},
        deterministic_insights=[],
        business_recommendations=[],
    )

    text = extract_pdf_text(pdf_bytes)

    assert "minimal.csv" in text
    assert "Rows" in text
    assert "Columns" in text


def test_missing_recommendation_fields_use_defaults(
    sample_profile,
):
    pdf_bytes = generate_pdf_report(
        dataset_name="sales.csv",
        profile=sample_profile,
        deterministic_insights=[],
        business_recommendations=[{}],
    )

    text = extract_pdf_text(pdf_bytes)

    assert "Recommendation 1" in text
    assert "MEDIUM PRIORITY" in text


def test_special_characters_in_dataset_name(sample_profile):
    pdf_bytes = generate_pdf_report(
        dataset_name="Sales & Marketing <2026>.csv",
        profile=sample_profile,
        deterministic_insights=[],
        business_recommendations=[],
    )

    text = extract_pdf_text(pdf_bytes)

    assert "Sales & Marketing" in text


def test_special_characters_in_insight_text(sample_profile):
    pdf_bytes = generate_pdf_report(
        dataset_name="sales.csv",
        profile=sample_profile,
        deterministic_insights=[
            {
                "title": "Revenue & Profit",
                "text": "Revenue < target & profit > costs.",
            }
        ],
        business_recommendations=[],
    )

    text = extract_pdf_text(pdf_bytes)

    assert "Revenue & Profit" in text
    assert "Revenue < target & profit > costs." in text


def test_long_report_generates_multiple_pages(sample_profile):
    long_text = "Business analysis detail. " * 2500

    pdf_bytes = generate_pdf_report(
        dataset_name="large_report.csv",
        profile=sample_profile,
        deterministic_insights=[
            {
                "title": "Extended Analysis",
                "text": long_text,
            }
        ],
        business_recommendations=[],
    )

    reader = PdfReader(BytesIO(pdf_bytes))

    assert len(reader.pages) > 1