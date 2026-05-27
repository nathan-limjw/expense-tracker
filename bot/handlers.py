import httpx
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
        f"/report — generate your monthly financial report\n"
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


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user_id = str(update.effective_user.id)
    name = update.effective_user.first_name
    user_id = await get_or_register_user(telegram_user_id, name)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{settings.API_BASE_URL}/expenses/",
            params={"user_id": user_id},
        )

    if response.status_code == 404:
        await update.message.reply_text("No expenses logged yet!")
        return

    if response.status_code != 200:
        await update.message.reply_text("❌ Something went wrong, please try again.")
        return

    expenses = response.json()[-10:]
    lines = []
    for e in reversed(expenses):
        lines.append(
            f"• *{e['description']}* — ${e['amount']:.2f} ({e['category']}) {e['date'][:10]}"
        )

    await update.message.reply_text(
        "*Your last 10 expenses:*\n\n" + "\n".join(lines),
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

    category_lines = []
    for c in data["categories"]:
        if c["budget"]:
            category_lines.append(
                f"• *{c['category']}*: ${c['spent']:.2f} / ${c['budget']:.2f} ({c['variance_pct']:.1f}%)"
            )
        else:
            category_lines.append(
                f"• *{c['category']}*: ${c['spent']:.2f} (no budget set)"
            )

    budget_line = (
        f"${data['total_spent']:.2f} / ${data['monthly_budget']:.2f}"
        if data["monthly_budget"]
        else f"${data['total_spent']:.2f} (no overall budget set)"
    )

    reply = (
        f"📊 *Report for {data['month']}* (Day {data['current_day']}/{data['days_in_period']})\n\n"
        f"*Total Spent:* {budget_line}\n\n"
        f"*By Category:*\n" + "\n".join(category_lines) + "\n\n"
        f"*Summary:*\n{data['summary']}"
    )

    await update.message.reply_text(reply, parse_mode="Markdown")


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
