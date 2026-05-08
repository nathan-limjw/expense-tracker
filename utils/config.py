import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/db/test.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_TEMPERATURE = os.getenv("MODEL_TEMPERATURE", "0")

CONFIDENCE_THRESHOLD = os.getenv("CONFIDENCE_THRESHOLD", "0.75")
