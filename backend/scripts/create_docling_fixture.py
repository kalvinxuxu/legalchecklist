"""Create a deterministic complex-layout PDF for local Docling acceptance tests."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(18 * mm, 10 * mm, "Docling complex-layout acceptance fixture")
    canvas.drawRightString(192 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def main() -> None:
    output = Path(__file__).resolve().parents[2] / "output" / "pdf" / "docling_complex_layout_fixture.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("FixtureTitle", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=10)
    heading = ParagraphStyle("FixtureHeading", parent=styles["Heading2"], spaceBefore=8, spaceAfter=5)
    body = ParagraphStyle("FixtureBody", parent=styles["BodyText"], leading=14, spaceAfter=6)
    small = ParagraphStyle("FixtureSmall", parent=styles["BodyText"], fontSize=8, leading=10)

    story = [
        Paragraph("MASTER SERVICE AGREEMENT", title),
        Paragraph("1. Scope and document hierarchy", heading),
        Paragraph(
            "This fixture intentionally combines headings, paragraphs, numbered obligations, a multi-column table, "
            "and a page break. The parser must preserve reading order and evidence locations across the document.", body,
        ),
        Paragraph("1.1 The parties shall maintain accurate records and notify each other of material changes.", body),
        Paragraph("1.2 Payment terms are governed by the schedule below and the signed order form.", body),
        Paragraph("2. Commercial schedule", heading),
    ]
    data = [
        [Paragraph("Item", small), Paragraph("Deliverable", small), Paragraph("Quantity", small), Paragraph("Unit price", small), Paragraph("Review rule", small)],
        ["A-01", "Initial legal review", "1", "1200", "Five business days"],
        ["A-02", "Risk issue register", "1", "800", "Evidence required"],
        ["A-03", "Revision round", "2", "600", "Written comments"],
        ["A-04", "Final approval memo", "1", "500", "Partner sign-off"],
        ["A-05", "Archive package", "1", "300", "Checksum recorded"],
        ["TOTAL", "", "", "5900", "Tax excluded"],
    ]
    table = Table(data, colWidths=[23 * mm, 50 * mm, 24 * mm, 28 * mm, 55 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7f8c8d")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#f4f7fb")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d9eaf7")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([table, Spacer(1, 8), Paragraph("3. Obligations", heading)])
    story.extend([
        Paragraph("(a) The supplier shall preserve all source materials for seven years.", body),
        Paragraph("(b) The customer may request a correction when an evidence reference is incomplete.", body),
        Paragraph("(c) Any exception must be documented in the issue register before approval.", body),
        PageBreak(),
        Paragraph("4. Review protocol", heading),
        Paragraph(
            "The review protocol continues on this page to test page-level reading order. Each finding must include "
            "a source page, a block reference, and a short quoted span. A finding without evidence is not actionable.", body,
        ),
        Paragraph("4.1 Acceptance criteria", heading),
        Paragraph("1. All five commercial items remain associated with their labels.", body),
        Paragraph("2. The total amount remains 5900 before tax.", body),
        Paragraph("3. The footer is treated as page furniture and does not replace body reading order.", body),
        Paragraph("5. Signature and approval", heading),
        Paragraph("The parties confirm that this test document is complete and ready for parser acceptance.", body),
        Spacer(1, 20),
        Table([["Supplier signature: ____________________", "Customer signature: ____________________"]], colWidths=[88 * mm, 88 * mm], style=TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])),
    ])
    SimpleDocTemplate(
        str(output), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=18 * mm,
        title="Docling complex layout acceptance fixture",
    ).build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    print(output)


if __name__ == "__main__":
    main()
