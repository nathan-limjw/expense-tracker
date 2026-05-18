from langchain_aws import ChatBedrockConverse
from langchain_ollama import ChatOllama

from utils.config import settings


def get_llm():
    if settings.APP_ENV == "prod":
        return ChatBedrockConverse(
            model=settings.BEDROCK_MODEL_ID,
            region_name=settings.AWS_REGION,
            temperature=settings.MODEL_TEMPERATURE,
        )
    else:
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.MODEL_TEMPERATURE,
        )
