import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/db/test.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
