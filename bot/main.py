from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot.config import settings
from bot.handlers import message_handler, start_handler


def main():
    app = ApplicationBuilder().token(settings.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot starting...")
    app.run_webhook(
        listen="0.0.0.0",
        port=8001,
        webhook_url=settings.WEBHOOK_URL,
        cert="/etc/nginx/ssl/bot.crt",
        key="/etc/nginx/ssl/bot.key",
    )
