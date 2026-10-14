from datetime import datetime
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Image,
    KeepTogether,
)


# ==========================================================
# SAFE TEXT HANDLING
# ==========================================================

def _safe_text(value) -> str:
    """
    Escape dynamic text before inserting it into ReportLab paragraphs.

    This prevents HTML-like characters in dataset names, analytical
    findings, recommendations, and AI-generated content from being
    interpreted as ReportLab markup.
    """
    return escape(str(value), quote=False)


def _normalize_dataset_name(dataset_name: str) -> str:
    """Remove accidentally duplicated file extensions from a dataset name.

    Examples:
        ``sales.csv.csv`` -> ``sales.csv``
        ``prices.xlsx.xlsx`` -> ``prices.xlsx``

    Names with a single extension are returned unchanged.
    """
    name = str(dataset_name).strip()

    while True:
        suffix = name.rsplit(".", 1)
        if len(suffix) != 2 or not suffix[0] or not suffix[1]:
            return name

        extension = "." + suffix[1]
        stem = suffix[0]
        previous_extension = stem.rsplit(".", 1)

        if (
            len(previous_extension) == 2
            and previous_extension[1].lower() == suffix[1].lower()
        ):
            name = stem
        else:
            return name


# ==========================================================
# PAGE FOOTER
# ==========================================================

def _draw_page_footer(canvas, document):
    """Draw a consistent footer and page number on each PDF page."""

    canvas.saveState()

    page_width, _ = document.pagesize

    canvas.setStrokeColor(
        colors.HexColor("#CBD5E1")
    )
    canvas.setLineWidth(0.5)

    canvas.line(
        document.leftMargin,
        14 * mm,
        page_width - document.rightMargin,
        14 * mm,
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(
        colors.HexColor("#64748B")
    )

    canvas.drawString(
        document.leftMargin,
        9 * mm,
        "InsightFlow AI | Business Analysis Report",
    )

    canvas.drawRightString(
        page_width - document.rightMargin,
        9 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# ==========================================================
# REPORT GENERATOR
# ==========================================================

def generate_pdf_report(
    dataset_name: str,
    profile: dict,
    deterministic_insights: list[dict],
    business_recommendations: list[dict],
    ai_analysis=None,
    chart_images: list[dict] | None = None,
) -> bytes:
    """
    Generate a downloadable PDF business analysis report.

    Parameters
    ----------
    dataset_name:
        Name of the uploaded dataset.

    profile:
        Dataset statistics such as rows, columns,
        missing cells, and duplicate rows.

    deterministic_insights:
        List of dictionaries containing 'title' and 'text'.

    business_recommendations:
        Structured recommendations from the recommendation engine.

    ai_analysis:
        Optional AIAnalysis Pydantic model returned by Gemini.

    chart_images:
        Optional list of chart dictionaries. Each dictionary
        should contain:
            - title: Chart title
            - type: Chart type
            - image: PNG image bytes

    Returns
    -------
    bytes:
        PDF document bytes suitable for st.download_button().
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="InsightFlow Business Analysis Report",
        author="InsightFlow AI",
    )

    # ======================================================
    # STYLES
    # ======================================================

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=25,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2563EB"),
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=18,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#1D4ED8"),
            spaceBefore=14,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["BodyText"],
            fontSize=9,
            leading=14,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallMuted",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B"),
        )
    )

    story = []

    # ======================================================
    # 1. REPORT HEADER
    # ======================================================

    story.append(
        Spacer(1, 12 * mm)
    )

    story.append(
        Paragraph(
            "INSIGHTFLOW AI",
            styles["ReportTitle"],
        )
    )

    story.append(
        Paragraph(
            "Business Intelligence &amp; Data Analysis Report",
            styles["ReportSubtitle"],
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#DBEAFE"),
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            "Report Overview",
            styles["SectionHeading"],
        )
    )

    display_dataset_name = _normalize_dataset_name(dataset_name)

    story.append(
        Paragraph(
            f"<b>Dataset:</b> {_safe_text(display_dataset_name)}",
            styles["BodyTextCustom"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Generated:</b> "
            f"{datetime.now().strftime('%d %B %Y, %H:%M')}",
            styles["BodyTextCustom"],
        )
    )

    # ======================================================
    # 2. DATASET PROFILE
    # ======================================================

    story.append(
        Paragraph(
            "Dataset Overview",
            styles["SectionHeading"],
        )
    )

    profile_rows = [
        ["Metric", "Value"],
        [
            "Rows",
            f"{profile.get('rows', 0):,}",
        ],
        [
            "Columns",
            f"{profile.get('columns', 0):,}",
        ],
        [
            "Missing Cells",
            f"{profile.get('missing_cells', 0):,}",
        ],
        [
            "Duplicate Rows",
            f"{profile.get('duplicate_rows', 0):,}",
        ],
    ]

    profile_table = Table(
        profile_rows,
        colWidths=[75 * mm, 75 * mm],
        repeatRows=1,
    )

    profile_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1D4ED8"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    colors.HexColor("#F8FAFC"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    story.append(profile_table)

    # ======================================================
    # 3. VISUAL ANALYSIS
    # ======================================================

    if chart_images:

        valid_charts = [
            chart
            for chart in chart_images
            if isinstance(chart, dict)
            and isinstance(chart.get("image"), bytes)
            and chart["image"]
        ]

        if valid_charts:

            story.append(
                Paragraph(
                    "Visual Analysis",
                    styles["SectionHeading"],
                )
            )

            for index, chart in enumerate(
                valid_charts,
                start=1,
            ):

                chart_title = chart.get(
                    "title",
                    f"Visualization {index}",
                )

                try:
                    chart_image = Image(
                        BytesIO(chart["image"]),
                        width=165 * mm,
                        height=95 * mm,
                        kind="proportional",
                    )

                    chart_block = [
                        Paragraph(
                            _safe_text(chart_title),
                            styles["Heading3"],
                        ),
                        Spacer(1, 2 * mm),
                        chart_image,
                        Spacer(1, 5 * mm),
                    ]

                    story.append(
                        KeepTogether(chart_block)
                    )

                except Exception:
                    # Skip an invalid image without preventing
                    # the remaining report from being generated.
                    continue

    # ======================================================
    # 4. EXECUTIVE SUMMARY
    # ======================================================

    if ai_analysis is not None:

        story.append(
            Paragraph(
                "Executive Summary",
                styles["SectionHeading"],
            )
        )

        story.append(
            Paragraph(
                _safe_text(
                    ai_analysis.executive_summary
                ),
                styles["BodyTextCustom"],
            )
        )

        # --------------------------------------------------
        # AI KEY FINDINGS
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Key Findings",
                styles["SectionHeading"],
            )
        )

        for finding in ai_analysis.key_findings:

            story.append(
                Paragraph(
                    f"&bull; {_safe_text(finding)}",
                    styles["BodyTextCustom"],
                )
            )

    # ======================================================
    # 5. DETERMINISTIC INSIGHTS
    # ======================================================

    story.append(
        Paragraph(
            "Analytical Findings",
            styles["SectionHeading"],
        )
    )

    if deterministic_insights:

        for index, insight in enumerate(
            deterministic_insights,
            start=1,
        ):

            title = insight.get(
                "title",
                f"Finding {index}",
            )

            text = insight.get(
                "text",
                "",
            )

            story.append(
                Paragraph(
                    f"<b>{_safe_text(title)}</b>",
                    styles["BodyTextCustom"],
                )
            )

            story.append(
                Paragraph(
                    _safe_text(text),
                    styles["BodyTextCustom"],
                )
            )

    else:

        story.append(
            Paragraph(
                "No deterministic findings were available.",
                styles["BodyTextCustom"],
            )
        )

    # ======================================================
    # 6. BUSINESS RECOMMENDATIONS
    # ======================================================

    story.append(
        Paragraph(
            "Business Recommendations",
            styles["SectionHeading"],
        )
    )

    if business_recommendations:

        for index, recommendation in enumerate(
            business_recommendations,
            start=1,
        ):

            title = recommendation.get(
                "title",
                f"Recommendation {index}",
            )

            priority = str(
                recommendation.get(
                    "priority",
                    "medium",
                )
            ).upper()

            finding = recommendation.get(
                "finding",
                "",
            )

            action = recommendation.get(
                "action",
                "",
            )

            rationale = recommendation.get(
                "rationale",
                "",
            )

            story.append(
                Paragraph(
                    f"<b>{index}. {_safe_text(title)}</b> "
                    f"— {_safe_text(priority)} PRIORITY",
                    styles["BodyTextCustom"],
                )
            )

            story.append(
                Paragraph(
                    f"<b>Finding:</b> {_safe_text(finding)}",
                    styles["BodyTextCustom"],
                )
            )

            story.append(
                Paragraph(
                    f"<b>Recommended action:</b> "
                    f"{_safe_text(action)}",
                    styles["BodyTextCustom"],
                )
            )

            story.append(
                Paragraph(
                    f"<b>Rationale:</b> {_safe_text(rationale)}",
                    styles["BodyTextCustom"],
                )
            )

            story.append(
                Spacer(1, 3 * mm)
            )

    else:

        story.append(
            Paragraph(
                "No business recommendations were generated.",
                styles["BodyTextCustom"],
            )
        )

    # ======================================================
    # 7. AI RECOMMENDATIONS
    # ======================================================

    if ai_analysis is not None:

        story.append(
            Paragraph(
                "AI Recommendations",
                styles["SectionHeading"],
            )
        )

        for recommendation in ai_analysis.recommendations:

            story.append(
                Paragraph(
                    f"&bull; {_safe_text(recommendation)}",
                    styles["BodyTextCustom"],
                )
            )

        # --------------------------------------------------
        # RISKS AND ANOMALIES
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Risks &amp; Anomalies",
                styles["SectionHeading"],
            )
        )

        if ai_analysis.risks_or_anomalies:

            for risk in ai_analysis.risks_or_anomalies:

                story.append(
                    Paragraph(
                        f"&bull; {_safe_text(risk)}",
                        styles["BodyTextCustom"],
                    )
                )

        else:

            story.append(
                Paragraph(
                    "No risks or anomalies were identified "
                    "from the available analytical facts.",
                    styles["BodyTextCustom"],
                )
            )

    # ======================================================
    # 8. REPORT FOOTER CONTENT
    # ======================================================

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#CBD5E1"),
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        Paragraph(
            "Generated by InsightFlow AI. "
            "Recommendations are analytical suggestions "
            "and should be evaluated in their business context.",
            styles["SmallMuted"],
        )
    )

    # ======================================================
    # BUILD PDF
    # ======================================================

    document.build(
        story,
        onFirstPage=_draw_page_footer,
        onLaterPages=_draw_page_footer,
    )

    buffer.seek(0)

    return buffer.getvalue()