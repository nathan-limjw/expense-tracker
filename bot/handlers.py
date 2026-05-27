import httpx
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import settings
from bot.user_service import get_or_register_user


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user_id = str(update.effective_user.id)
    name = update.effective_user.first_name

    user_id = await get_or_register_user(telegram_user_id, name)

    await update.message.reply_text(
        f"Hey {name}! 👋 You're all set up.\n\n"
        f"Just send me any expense in plain text and I'll log it for you.\n\n"
        f"Example: _Grabbed lunch at hawker centre for $5.50_",
        parse_mode="Markdown",
    )


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
