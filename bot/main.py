from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot.config import settings
from bot.handlers import (
    help_handler,
    history_handler,
    message_handler,
    report_handler,
    setbudget_handler,
    start_handler,
)


def create_app():
    application = ApplicationBuilder().token(settings.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("history", history_handler))
    application.add_handler(CommandHandler("report", report_handler))
    application.add_handler(CommandHandler("setbudget", setbudget_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )
    return application


telegram_app = create_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    with open("/etc/nginx/ssl/bot.crt", "rb") as cert_file:
        await telegram_app.bot.set_webhook(
            url=settings.WEBHOOK_URL,
            certificate=cert_file,
        )
    print(f"Webhook set to {settings.WEBHOOK_URL}")
    await telegram_app.start()
    yield
    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
