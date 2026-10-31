"""Deterministic PDF report generation for InsightFlow."""
from __future__ import annotations

import logging
import math
import os
import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, Image, KeepTogether, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

logger = logging.getLogger(__name__)
PAGE_WIDTH, _ = A4
LEFT, RIGHT = 18 * mm, 18 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT - RIGHT
PRIMARY = colors.HexColor("#1D4ED8")
DARK = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#CBD5E1")
PALE = colors.HexColor("#F1F5F9")
_FONT_NAMES = None


def _fonts():
    global _FONT_NAMES
    if _FONT_NAMES:
        return _FONT_NAMES
    candidates = [
        (os.getenv("INSIGHTFLOW_FONT_REGULAR"), os.getenv("INSIGHTFLOW_FONT_BOLD")),
        (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
    ]
    for regular, bold in candidates:
        if regular and bold and Path(regular).is_file() and Path(bold).is_file():
            try:
                pdfmetrics.registerFont(TTFont("IFUnicode", regular))
                pdfmetrics.registerFont(TTFont("IFUnicode-Bold", bold))
                _FONT_NAMES = ("IFUnicode", "IFUnicode-Bold")
                return _FONT_NAMES
            except Exception:
                logger.warning("Unicode font registration failed.", exc_info=True)
    _FONT_NAMES = ("Helvetica", "Helvetica-Bold")
    return _FONT_NAMES


def _get(obj: Any, key: str, default=None):
    return obj.get(key, default) if isinstance(obj, Mapping) else getattr(obj, key, default)


def _safe(value: Any) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=False).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br/>")


def _dataset_name(value: Any) -> str:
    name = str(value or "Unnamed dataset").strip()
    while True:
        match = re.match(r"^(.*)(\.[^.]+)$", name)
        if not match:
            return name
        stem, ext = match.groups()
        previous = re.match(r"^(.*)(\.[^.]+)$", stem)
        if previous and previous.group(2).lower() == ext.lower():
            name = stem
        else:
            return name


def _number(value: Any) -> str:
    if value is None:
        return "0"
    if isinstance(value, bool):
        return str(value)
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return _safe(value)
    if not math.isfinite(number):
        return "—"
    return f"{int(number):,}" if number.is_integer() else f"{number:,.2f}".rstrip("0").rstrip(".")


def _records(value: Any) -> list:
    if value is None or isinstance(value, (str, bytes, Mapping)):
        return []
    if isinstance(value, Sequence):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return []


def _styles():
    regular, bold = _fonts()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="IFTitle", parent=styles["Title"], fontName=bold,
        fontSize=24, leading=29, alignment=TA_CENTER, textColor=PRIMARY, spaceAfter=5,
        splitLongWords=1))
    styles.add(ParagraphStyle(name="IFSubtitle", parent=styles["Normal"], fontName=regular,
        fontSize=9, leading=13, alignment=TA_CENTER, textColor=MUTED, spaceAfter=12))
    styles.add(ParagraphStyle(name="IFSection", parent=styles["Heading2"], fontName=bold,
        fontSize=13, leading=17, textColor=PRIMARY, spaceBefore=12, spaceAfter=6,
        keepWithNext=True))
    styles.add(ParagraphStyle(name="IFBody", parent=styles["BodyText"], fontName=regular,
        fontSize=8.8, leading=13, textColor=DARK, spaceAfter=5, splitLongWords=1))
    styles.add(ParagraphStyle(name="IFSmall", parent=styles["Normal"], fontName=regular,
        fontSize=7.5, leading=10, textColor=MUTED))
    styles.add(ParagraphStyle(name="IFChartTitle", parent=styles["Heading3"], fontName=bold,
        fontSize=9.5, leading=12, textColor=DARK, spaceAfter=4, keepWithNext=True))
    return styles, regular, bold


def _page(canvas, document):
    canvas.saveState()
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    if document.page > 1:
        canvas.drawString(LEFT, A4[1] - 12 * mm, "INSIGHTFLOW AI")
        canvas.setStrokeColor(BORDER)
        canvas.line(LEFT, A4[1] - 15 * mm, A4[0] - RIGHT, A4[1] - 15 * mm)
    canvas.setStrokeColor(BORDER)
    canvas.line(LEFT, 14 * mm, A4[0] - RIGHT, 14 * mm)
    canvas.drawString(LEFT, 9 * mm, "InsightFlow AI | Business Analysis Report")
    canvas.drawRightString(A4[0] - RIGHT, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def _section(story, title, styles):
    story.append(Paragraph(_safe(title), styles["IFSection"]))


def _profile_table(profile, styles, bold):
    rows = [[Paragraph("<b>Metric</b>", styles["IFBody"]),
             Paragraph("<b>Value</b>", styles["IFBody"])]]
    for label, key in (("Rows", "rows"), ("Columns", "columns"),
                       ("Missing Cells", "missing_cells"), ("Duplicate Rows", "duplicate_rows")):
        rows.append([Paragraph(label, styles["IFBody"]),
                     Paragraph(_safe(_number(profile.get(key, 0))), styles["IFBody"])])
    table = Table(rows, colWidths=[CONTENT_WIDTH * .68, CONTENT_WIDTH * .32], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), bold),
        ("BACKGROUND", (0, 1), (-1, -1), PALE),
        ("GRID", (0, 0), (-1, -1), .4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _charts(charts, styles):
    output = []
    for index, chart in enumerate(_records(charts), 1):
        if not isinstance(chart, Mapping):
            continue
        raw = chart.get("image")
        if not isinstance(raw, (bytes, bytearray)) or not raw:
            continue
        try:
            stream = BytesIO(bytes(raw))
            width, height = ImageReader(stream).getSize()
            if width <= 0 or height <= 0:
                raise ValueError("Invalid image dimensions.")
            scale = min(CONTENT_WIDTH / width, (90 * mm) / height)
            output.append(KeepTogether([
                Paragraph(_safe(chart.get("title") or f"Visualization {index}"),
                          styles["IFChartTitle"]),
                Image(stream, width=width * scale, height=height * scale),
                Spacer(1, 5 * mm),
            ]))
        except Exception:
            logger.warning("Skipping invalid chart image %s.", index, exc_info=True)
    return output


def _ai_content(ai, story, styles):
    if ai is None:
        return
    sections = [
        ("Executive Summary", "executive_summary", False),
        ("AI Key Findings", "key_findings", True),
        ("AI Recommendations", "recommendations", True),
        ("Risks & Anomalies", "risks_or_anomalies", True),
    ]
    for title, key, is_list in sections:
        value = _get(ai, key)
        if not value:
            continue
        _section(story, title, styles)
        items = _records(value) if is_list else [value]
        for item in items:
            if item is not None and str(item).strip():
                prefix = "&bull; " if is_list else ""
                story.append(Paragraph(prefix + _safe(item), styles["IFBody"]))


def generate_pdf_report(
    dataset_name: str,
    profile: dict,
    deterministic_insights: list[dict],
    business_recommendations: list[dict],
    ai_analysis=None,
    chart_images: list[dict] | None = None,
    *,
    report_metadata: Mapping[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> bytes:
    """Generate a downloadable multi-page PDF; original positional API is retained."""
    if profile is None:
        profile = {}
    if not isinstance(profile, Mapping):
        raise TypeError("profile must be a mapping.")
    metadata = report_metadata if isinstance(report_metadata, Mapping) else {}
    dataset_name = _dataset_name(dataset_name)
    timestamp = generated_at or datetime.now()
    if not isinstance(timestamp, datetime):
        raise TypeError("generated_at must be a datetime instance.")

    styles, regular, bold = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=RIGHT, leftMargin=LEFT,
        topMargin=22 * mm, bottomMargin=20 * mm,
        title=f"InsightFlow Report - {dataset_name}",
        author=str(metadata.get("author") or "InsightFlow AI"),
        subject=str(metadata.get("subject") or "Business analysis report"))
    story = [
        Spacer(1, 5 * mm),
        Paragraph("INSIGHTFLOW AI", styles["IFTitle"]),
        Paragraph("BUSINESS INTELLIGENCE &amp; DATA ANALYSIS REPORT", styles["IFSubtitle"]),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DBEAFE")),
        Spacer(1, 5 * mm),
    ]

    _section(story, "Report Overview", styles)
    story.append(Paragraph(f"<b>Dataset:</b> {_safe(dataset_name)}", styles["IFBody"]))
    story.append(Paragraph(f"<b>Generated:</b> {timestamp.strftime('%d %B %Y, %H:%M')}",
                           styles["IFBody"]))
    if metadata.get("description"):
        story.append(Paragraph(f"<b>Description:</b> {_safe(metadata['description'])}",
                               styles["IFBody"]))

    _section(story, "Dataset Overview", styles)
    story.append(_profile_table(profile, styles, bold))

    chart_items = _charts(chart_images, styles)
    if chart_items:
        _section(story, "Visual Analysis", styles)
        story.extend(chart_items)

    _ai_content(ai_analysis, story, styles)

    _section(story, "Analytical Findings", styles)
    insights = [x for x in _records(deterministic_insights) if isinstance(x, Mapping)]
    if not insights:
        story.append(Paragraph("No deterministic findings were available.", styles["IFBody"]))
    for index, item in enumerate(insights, 1):
        title = item.get("title") or f"Finding {index}"
        story.append(Paragraph(f"<b>{index}. {_safe(title)}</b>", styles["IFBody"]))
        if item.get("text"):
            story.append(Paragraph(_safe(item["text"]), styles["IFBody"]))

    _section(story, "Business Recommendations", styles)
    recommendations = [x for x in _records(business_recommendations) if isinstance(x, Mapping)]
    if not recommendations:
        story.append(Paragraph("No business recommendations were generated.", styles["IFBody"]))
    priority_colors = {"LOW": "#15803D", "MEDIUM": "#B45309",
                       "HIGH": "#B91C1C", "CRITICAL": "#B91C1C"}
    for index, item in enumerate(recommendations, 1):
        title = item.get("title") or f"Recommendation {index}"
        priority = str(item.get("priority") or "medium").strip().upper()
        if priority not in priority_colors:
            priority = "MEDIUM"
        story.append(Paragraph(
            f"<b>{index}. {_safe(title)}</b> "
            f"<font color='{priority_colors[priority]}'><b>— {priority} PRIORITY</b></font>",
            styles["IFBody"]))
        for label, key in (("Finding", "finding"), ("Recommended action", "action"),
                           ("Rationale", "rationale")):
            if item.get(key) is not None and str(item[key]).strip():
                story.append(Paragraph(f"<b>{label}:</b> {_safe(item[key])}", styles["IFBody"]))
        story.append(Spacer(1, 2 * mm))

    story.extend([
        Spacer(1, 6 * mm),
        HRFlowable(width="100%", thickness=.5, color=BORDER),
        Spacer(1, 3 * mm),
        Paragraph("Generated by InsightFlow AI. Recommendations are analytical suggestions "
                  "and should be evaluated in their business context.", styles["IFSmall"]),
    ])
    doc.build(story, onFirstPage=_page, onLaterPages=_page)
    return buffer.getvalue()
