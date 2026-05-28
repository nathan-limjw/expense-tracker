import base64
import io
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_report_pdf(data: dict, name: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=4,
        textColor=colors.HexColor("#16213e"),
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
        leading=14,
    )
    caption_style = ParagraphStyle(
        "Caption",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )

    elements = []

    # Title
    elements.append(Paragraph(f"💸 Expense Report — {data['month']}", title_style))
    elements.append(
        Paragraph(
            f"Generated for {name} | Day {data['current_day']} of {data['days_in_period']}",
            caption_style,
        )
    )
    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#cccccc"),
            spaceAfter=12,
        )
    )

    # Overview
    elements.append(Paragraph("Overview", heading_style))
    budget_line = (
        f"<b>Total Spent:</b> ${data['total_spent']:.2f} / ${data['monthly_budget']:.2f}"
        if data["monthly_budget"]
        else f"<b>Total Spent:</b> ${data['total_spent']:.2f} (no overall budget set)"
    )
    elements.append(Paragraph(budget_line, body_style))
    elements.append(Spacer(1, 8))

    # Category breakdown table
    elements.append(Paragraph("Spending by Category", heading_style))
    table_data = [["Category", "Spent", "Budget", "% Used"]]
    for c in data["categories"]:
        table_data.append(
            [
                c["category"],
                f"${c['spent']:.2f}",
                f"${c['budget']:.2f}" if c["budget"] else "—",
                f"{c['variance_pct']:.1f}%" if c["variance_pct"] else "—",
            ]
        )

    table = Table(table_data, colWidths=[5 * cm, 3 * cm, 3 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f5f5f5")],
                ),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Charts
    if data.get("chart_bytes"):
        elements.append(Paragraph("Charts", heading_style))

        pie_bytes = base64.b64decode(data["chart_bytes"]["pie"])
        pie_img = Image(io.BytesIO(pie_bytes), width=10 * cm, height=10 * cm)
        elements.append(pie_img)
        elements.append(Paragraph("Spending by Category", caption_style))
        elements.append(Spacer(1, 8))

        bar_bytes = base64.b64decode(data["chart_bytes"]["bar"])
        bar_img = Image(io.BytesIO(bar_bytes), width=14 * cm, height=8 * cm)
        elements.append(bar_img)
        elements.append(Paragraph("Spent vs Budget by Category", caption_style))
        elements.append(Spacer(1, 12))

    # Financial Summary
    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#cccccc"),
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    elements.append(Paragraph("Financial Summary", heading_style))
    elements.extend(
        _parse_markdown_to_elements(data["summary"], body_style, heading_style)
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def _parse_markdown_to_elements(text: str, body_style, heading_style) -> list:
    elements = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            elements.append(Spacer(1, 4))
        elif line.startswith("### "):
            elements.append(Paragraph(line[4:], heading_style))
        elif line.startswith("## "):
            elements.append(Paragraph(line[3:], heading_style))
        elif line.startswith("# "):
            elements.append(Paragraph(line[2:], heading_style))
        elif line.startswith("- ") or line.startswith("* "):
            content = _convert_inline_markdown(line[2:].strip())
            elements.append(Paragraph(f"• {content}", body_style))
        elif line[0].isdigit() and len(line) > 2 and line[1:3] in (". ", ") "):
            content = _convert_inline_markdown(line[3:].strip())
            elements.append(Paragraph(f"{line[0]}. {content}", body_style))
        else:
            elements.append(Paragraph(_convert_inline_markdown(line), body_style))
    return elements


def _convert_inline_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`(.*?)`", r'<font name="Courier">\1</font>', text)
    return text
