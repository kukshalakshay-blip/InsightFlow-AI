from datetime import datetime
from io import BytesIO

import pytest
from pypdf import PdfReader
from PIL import Image

from app.services.report_generator import generate_pdf_report


@pytest.fixture
def sample_profile():
    return {"rows": 1000, "columns": 8, "missing_cells": 25, "duplicate_rows": 10}


@pytest.fixture
def sample_insights():
    return [
        {"title": "Revenue Trend", "text": "Revenue increased by 15% during the reporting period."},
        {"title": "Data Quality", "text": "A small number of missing values were detected."},
    ]


@pytest.fixture
def sample_recommendations():
    return [{
        "title": "Improve Data Quality", "priority": "high",
        "finding": "Some records contain missing values.",
        "action": "Investigate the source of missing data.",
        "rationale": "Reliable data improves analytical accuracy.",
    }]


def extract_pdf_text(pdf_bytes):
    return "\\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf_bytes)).pages)


def make_png_bytes():
    buffer = BytesIO()
    image = Image.new("RGB", (320, 180), color=(40, 90, 180))
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_generates_valid_pdf(sample_profile):
    pdf = generate_pdf_report("sales.csv", sample_profile, [], [])
    assert isinstance(pdf, bytes) and pdf.startswith(b"%PDF") and len(pdf) > 100


def test_report_contains_dataset_name(sample_profile):
    assert "sales.csv" in extract_pdf_text(generate_pdf_report("sales.csv", sample_profile, [], []))


def test_report_contains_profile_statistics(sample_profile):
    text = extract_pdf_text(generate_pdf_report("sales.csv", sample_profile, [], []))
    for value in ("1,000", "8", "25", "10"):
        assert value in text


def test_empty_insights_and_recommendations_are_supported(sample_profile):
    text = extract_pdf_text(generate_pdf_report("empty.csv", sample_profile, [], []))
    assert "No deterministic findings were available." in text
    assert "No business recommendations were generated." in text


def test_deterministic_insights_appear_in_report(sample_profile, sample_insights):
    text = extract_pdf_text(generate_pdf_report("sales.csv", sample_profile, sample_insights, []))
    assert all(x in text for x in ("Revenue Trend", "increased by 15%", "Data Quality"))


def test_business_recommendations_appear_in_report(sample_profile, sample_recommendations):
    text = extract_pdf_text(generate_pdf_report("sales.csv", sample_profile, [], sample_recommendations))
    assert all(x in text for x in ("Improve Data Quality", "HIGH PRIORITY",
                                   "Investigate the source", "Reliable data improves"))


def test_missing_profile_fields_use_defaults():
    text = extract_pdf_text(generate_pdf_report("minimal.csv", {}, [], []))
    assert "minimal.csv" in text and "Rows" in text and "Columns" in text


def test_missing_recommendation_fields_use_defaults(sample_profile):
    text = extract_pdf_text(generate_pdf_report("sales.csv", sample_profile, [], [{}]))
    assert "Recommendation 1" in text and "MEDIUM PRIORITY" in text


def test_special_characters_in_dataset_name(sample_profile):
    text = extract_pdf_text(generate_pdf_report("Sales & Marketing <2026>.csv", sample_profile, [], []))
    assert "Sales & Marketing" in text


def test_special_characters_in_insight_text(sample_profile):
    text = extract_pdf_text(generate_pdf_report(
        "sales.csv", sample_profile,
        [{"title": "Revenue & Profit", "text": "Revenue < target & profit > costs."}], []))
    assert "Revenue & Profit" in text
    assert "Revenue < target & profit > costs." in text


def test_long_report_generates_multiple_pages(sample_profile):
    long_text = "Business analysis detail. " * 2500
    pdf = generate_pdf_report("large.csv", sample_profile,
                              [{"title": "Extended Analysis", "text": long_text}], [])
    assert len(PdfReader(BytesIO(pdf)).pages) > 1


def test_html_like_text_is_rendered_literally(sample_profile):
    malicious = '<script>alert("test")</script>'
    text = extract_pdf_text(generate_pdf_report(
        "sales.csv", sample_profile, [{"title": "Markup Test", "text": malicious}], []))
    assert "Markup Test" in text and malicious in text


def test_multipage_report_contains_page_numbers(sample_profile):
    long_text = "Business analysis detail. " * 2500
    reader = PdfReader(BytesIO(generate_pdf_report(
        "large.csv", sample_profile, [{"title": "Extended", "text": long_text}], [])))
    assert len(reader.pages) > 1
    assert "Page 1" in reader.pages[0].extract_text()
    assert "Page 2" in reader.pages[1].extract_text()


def test_ai_analysis_accepts_mapping(sample_profile):
    ai = {"executive_summary": "Revenue performance was positive.",
          "key_findings": ["Revenue rose 15%."],
          "recommendations": ["Review the strongest segment."],
          "risks_or_anomalies": ["Some values require investigation."]}
    text = extract_pdf_text(generate_pdf_report("sales.csv", sample_profile, [], [], ai))
    assert all(x in text for x in ("Executive Summary", "Revenue performance",
                                   "AI Key Findings", "Review the strongest segment",
                                   "Risks & Anomalies"))


def test_ai_analysis_accepts_object(sample_profile):
    class AIResult:
        executive_summary = "Summary from model object."
        key_findings = ["Finding one."]
        recommendations = []
        risks_or_anomalies = []
    text = extract_pdf_text(generate_pdf_report("sales.csv", sample_profile, [], [], AIResult()))
    assert "Summary from model object." in text and "Finding one." in text


def test_partial_ai_analysis_is_supported(sample_profile):
    text = extract_pdf_text(generate_pdf_report(
        "sales.csv", sample_profile, [], [], {"executive_summary": "Partial summary."}))
    assert "Partial summary." in text


def test_chart_image_is_included(sample_profile):
    text = extract_pdf_text(generate_pdf_report(
        "sales.csv", sample_profile, [], [],
        chart_images=[{"title": "Monthly Revenue", "type": "bar", "image": make_png_bytes()}]))
    assert "Visual Analysis" in text and "Monthly Revenue" in text


def test_invalid_chart_is_skipped_without_failing_report(sample_profile):
    pdf = generate_pdf_report("sales.csv", sample_profile, [], [],
                              chart_images=[{"title": "Broken", "image": b"not-an-image"}])
    assert pdf.startswith(b"%PDF")
    assert "Analytical Findings" in extract_pdf_text(pdf)


def test_malformed_records_are_skipped(sample_profile):
    text = extract_pdf_text(generate_pdf_report("sales.csv", sample_profile, [None, "bad"], [None, {}]))
    assert "No deterministic findings were available." in text
    assert "Recommendation 1" in text


def test_non_finite_profile_values_are_safe():
    text = extract_pdf_text(generate_pdf_report(
        "sales.csv", {"rows": float("nan"), "columns": float("inf")}, [], []))
    assert "Rows" in text and "Columns" in text


def test_duplicate_extension_is_normalized(sample_profile):
    text = extract_pdf_text(generate_pdf_report("prices.csv.csv", sample_profile, [], []))
    assert "prices.csv" in text and "prices.csv.csv" not in text


def test_report_metadata_and_fixed_timestamp(sample_profile):
    pdf = generate_pdf_report(
        "sales.csv", sample_profile, [], [],
        report_metadata={"author": "Analyst Team", "subject": "Quarterly review",
                         "description": "Quarterly sales review."},
        generated_at=datetime(2026, 10, 31, 14, 30))
    reader = PdfReader(BytesIO(pdf))
    text = extract_pdf_text(pdf)
    assert reader.metadata.author == "Analyst Team"
    assert reader.metadata.subject == "Quarterly review"
    assert "Quarterly sales review." in text
    assert "31 October 2026, 14:30" in text


def test_profile_must_be_mapping():
    with pytest.raises(TypeError, match="profile must be a mapping"):
        generate_pdf_report("sales.csv", ["invalid"], [], [])


def test_generated_at_must_be_datetime(sample_profile):
    with pytest.raises(TypeError, match="generated_at must be a datetime"):
        generate_pdf_report("sales.csv", sample_profile, [], [], generated_at="today")


def test_unknown_priority_defaults_to_medium(sample_profile):
    text = extract_pdf_text(generate_pdf_report(
        "sales.csv", sample_profile, [], [{"title": "Review", "priority": "urgent-ish"}]))
    assert "MEDIUM PRIORITY" in text
