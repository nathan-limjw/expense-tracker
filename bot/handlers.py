import io

import httpx
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
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import settings
from bot.user_service import get_or_register_user


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user_id = str(update.effective_user.id)
    name = update.effective_user.first_name

    await get_or_register_user(telegram_user_id, name)

    await update.message.reply_text(
        f"Hey {name}! 👋 You're all set up.\n\n"
        f"Just send me any expense in plain text and I'll log it for you.\n\n"
        f"*Commands:*\n"
        f"/history — view your last 10 expenses\n"
        f"/report — generate your monthly financial report with an AI summary and charts\n"
        f"/setcategorybudget — set a category budget e.g. `/setcategorybudget Food 200 2026-05`\n"
        f"/setmonthlybudget — set your monthly budget e.g. `/setmonthlybudget 1000`\n"
        f"/updatecategorybudget <category> <amount> <month> — update an existing category budget\n"
        f"/help — show this message again",
        parse_mode="Markdown",
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Commands:*\n"
        "/history — view your last 10 expenses\n"
        "/report — generate your monthly financial report\n"
        "/setcategorybudget — set a category budget e.g. `/setcategorybudget Food 200 2026-05`\n"
        "/setmonthlybudget — set your monthly budget e.g. `/setmonthlybudget 1000`\n"
        "/updatecategorybudget <category> <amount> <month> — update an existing category budget\n"
        "/help — show this message again\n\n"
        "Or just send any expense in plain text to log it!",
        parse_mode="Markdown",
    )


async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user_id = str(update.effective_user.id)
    name = update.effective_user.first_name
    user_id = await get_or_register_user(telegram_user_id, name)

    await update.message.reply_text(
        "⏳ Generating your report, this may take a few seconds..."
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.API_BASE_URL}/report/",
            json={"user_id": user_id, "month": ""},
        )

    if response.status_code != 200:
        await update.message.reply_text(
            "❌ Something went wrong generating your report."
        )
        return

    data = response.json()
    pdf_bytes = _generate_pdf(data, name)

    await update.message.reply_document(
        document=io.BytesIO(pdf_bytes),
        filename=f"report_{data['month']}.pdf",
        caption=f"📊 Your financial report for {data['month']}",
    )


def _generate_pdf(data: dict, name: str) -> bytes:
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
        "Body", parent=styles["Normal"], fontSize=10, spaceAfter=4, leading=14
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
            width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=12
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

        pie_bytes = data["chart_bytes"]["pie"]
        if isinstance(pie_bytes, list):
            pie_bytes = bytes(pie_bytes)
        pie_img = Image(io.BytesIO(pie_bytes), width=10 * cm, height=10 * cm)
        elements.append(pie_img)
        elements.append(Paragraph("Spending by Category", caption_style))
        elements.append(Spacer(1, 8))

        bar_bytes = data["chart_bytes"]["bar"]
        if isinstance(bar_bytes, list):
            bar_bytes = bytes(bar_bytes)
        bar_img = Image(io.BytesIO(bar_bytes), width=14 * cm, height=8 * cm)
        elements.append(bar_img)
        elements.append(Paragraph("Spent vs Budget by Category", caption_style))
        elements.append(Spacer(1, 12))

    # AI Summary
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
    for line in data["summary"].split("\n"):
        if line.strip():
            elements.append(Paragraph(line.strip(), body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


async def setcategorybudget_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user_id = str(update.effective_user.id)
    name = update.effective_user.first_name
    user_id = await get_or_register_user(telegram_user_id, name)

    args = context.args
    if not args or len(args) != 3:
        await update.message.reply_text(
            "Usage: `/setcategorybudget <category> <amount> <month>`\n"
            "Example: `/setcategorybudget Food 200 2026-05`\n\n"
            "Valid categories: Food, Transport, Shopping, Utilities, Entertainment, Others",
            parse_mode="Markdown",
        )
        return

    category, amount, month = args

    try:
        amount = float(amount)
    except ValueError:
        await update.message.reply_text(
            "❌ Amount must be a number e.g. `/setcategorybudget Food 200 2026-05`",
            parse_mode="Markdown",
        )
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.API_BASE_URL}/budgets/",
            json={
                "category": category,
                "month": month,
                "limit": amount,
                "user_id": user_id,
            },
        )

    if response.status_code == 200:
        await update.message.reply_text(
            f"✅ Budget set: *{category}* — ${amount:.2f} for {month}",
            parse_mode="Markdown",
        )
    elif response.status_code == 409:
        await update.message.reply_text(
            f"⚠️ Budget for {category} already exists for {month}. Use `/updatecategorybudget` to change it.",
            parse_mode="Markdown",
        )
    elif response.status_code == 422:
        await update.message.reply_text(
            f"❌ Invalid input: {response.json()['detail']}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("❌ Something went wrong, please try again.")


async def setmonthlybudget_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user_id = str(update.effective_user.id)
    name = update.effective_user.first_name
    user_id = await get_or_register_user(telegram_user_id, name)

    args = context.args
    if not args or len(args) != 1:
        await update.message.reply_text(
            "Usage: `/setmonthlybudget <amount>`\nExample: `/setmonthlybudget 1000`",
            parse_mode="Markdown",
        )
        return

    try:
        amount = float(args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Amount must be a number e.g. `/setmonthlybudget 1000`",
            parse_mode="Markdown",
        )
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.put(
            f"{settings.API_BASE_URL}/users/{user_id}",
            json={"monthly_budget": amount},
        )

    if response.status_code == 200:
        await update.message.reply_text(
            f"✅ Monthly budget updated to *${amount:.2f}*",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("❌ Something went wrong, please try again.")


async def updatecategorybudget_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    telegram_user_id = str(update.effective_user.id)
    name = update.effective_user.first_name
    user_id = await get_or_register_user(telegram_user_id, name)

    args = context.args
    if not args or len(args) != 3:
        await update.message.reply_text(
            "Usage: `/updatecategorybudget <category> <amount> <month>`\n"
            "Example: `/updatecategorybudget Food 300 2026-05`\n\n"
            "Valid categories: Food, Transport, Shopping, Utilities, Entertainment, Others",
            parse_mode="Markdown",
        )
        return

    category, amount, month = args

    try:
        amount = float(amount)
    except ValueError:
        await update.message.reply_text(
            "❌ Amount must be a number e.g. `/updatecategorybudget Food 300 2026-05`",
            parse_mode="Markdown",
        )
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.put(
            f"{settings.API_BASE_URL}/budgets/{user_id}",
            json={"category": category, "month": month, "limit": amount},
        )

    if response.status_code == 200:
        await update.message.reply_text(
            f"✅ Budget updated: *{category}* — ${amount:.2f} for {month}",
            parse_mode="Markdown",
        )
    elif response.status_code == 404:
        await update.message.reply_text(
            f"❌ No budget found for {category} in {month}. Use `/setbudget` to create one first.",
            parse_mode="Markdown",
        )
    elif response.status_code == 422:
        await update.message.reply_text(
            f"❌ Invalid input: {response.json()['detail']}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("❌ Something went wrong, please try again.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user_id = str(update.effective_user.id)
    name = update.effective_user.first_name
    text = update.message.text

    user_id = await get_or_register_user(telegram_user_id, name)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.API_BASE_URL}/expenses/",
            json={"description": text, "user_id": user_id},
        )

    if response.status_code == 200:
        data = response.json()
        expense = data["expense"]
        messages = data["messages"]

        reply = (
            f"✅ Logged!\n\n"
            f"*{expense['description']}*\n"
            f"💰 ${expense['amount']:.2f} — {expense['category']}\n"
            f"📅 {expense['date'][:10]}\n"
        )

        if messages:
            reply += "\n" + "\n".join(f"⚠️ {m}" for m in messages)

    elif response.status_code == 422:
        reply = f"❌ Couldn't log that: {response.json()['detail']}"
    else:
        reply = "❌ Something went wrong, please try again."

    await update.message.reply_text(reply, parse_mode="Markdown")
