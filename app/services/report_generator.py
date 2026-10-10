from datetime import datetime
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
)


# ==========================================================
# REPORT GENERATOR
# ==========================================================

def generate_pdf_report(
    dataset_name: str,
    profile: dict,
    deterministic_insights: list[dict],
    business_recommendations: list[dict],
    ai_analysis=None,
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
            "Business Intelligence & Data Analysis Report",
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

    story.append(
        Paragraph(
            f"<b>Dataset:</b> {dataset_name}",
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
    # 3. EXECUTIVE SUMMARY
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
                str(ai_analysis.executive_summary),
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
                    f"&bull; {finding}",
                    styles["BodyTextCustom"],
                )
            )

    # ======================================================
    # 4. DETERMINISTIC INSIGHTS
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
                    f"<b>{title}</b>",
                    styles["BodyTextCustom"],
                )
            )

            story.append(
                Paragraph(
                    text,
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
    # 5. BUSINESS RECOMMENDATIONS
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

            priority = recommendation.get(
                "priority",
                "medium",
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
                    f"<b>{index}. {title}</b> "
                    f"— {priority} PRIORITY",
                    styles["BodyTextCustom"],
                )
            )

            story.append(
                Paragraph(
                    f"<b>Finding:</b> {finding}",
                    styles["BodyTextCustom"],
                )
            )

            story.append(
                Paragraph(
                    f"<b>Recommended action:</b> {action}",
                    styles["BodyTextCustom"],
                )
            )

            story.append(
                Paragraph(
                    f"<b>Rationale:</b> {rationale}",
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
    # 6. AI RECOMMENDATIONS
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
                    f"&bull; {recommendation}",
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
                        f"&bull; {risk}",
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
    # 7. REPORT FOOTER
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

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()