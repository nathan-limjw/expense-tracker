import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "dev"

    DATABASE_URL: str = "sqlite:///./app/db/test.db"
    LOG_LEVEL: str = "DEBUG"

    # Ollama (dev only)
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"

    # Bedrock (prod only)
    AWS_REGION: str = "ap-southeast-1"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # Shared Configs
    MODEL_TEMPERATURE: float = 0.0
    CONFIDENCE_THRESHOLD: float = 0.75

    model_config = SettingsConfigDict(
        env_file=".env" if os.getenv("APP_ENV", "dev") == "dev" else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
