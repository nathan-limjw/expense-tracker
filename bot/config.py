import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    API_BASE_URL: str = "http://localhost:8000"
    WEBHOOK_URL: str

    model_config = SettingsConfigDict(
        env_file=".env" if os.getenv("APP_ENV", "dev") == "dev" else None,
        env_file_encoding="utc-8",
        extra="ignore",
    )


settings = BotSettings()
