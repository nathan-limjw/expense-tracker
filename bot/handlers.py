from telegram import Update
from telegram.ext import ContextTypes

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

    await update.message.reply_text(
        f"Got it! Your user_id is `{user_id}`\n\nYou said: {text}",
        parse_mode="Markdown",
    )
