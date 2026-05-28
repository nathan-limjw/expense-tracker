from langfuse.langchain import CallbackHandler

from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def get_langfuse_callbacks(trace_name: str, user_id: str, metadata: dict = {}):
    if not settings.LANGFUSE_PUBLIC_KEY:
        return []
    try:
        return [
            CallbackHandler(
                trace_name=trace_name,
                user_id=str(user_id),
                tags=[settings.APP_ENV],
                metadata=metadata,
            )
        ]
    except Exception as e:
        logger.warning(f"Langfuse init failed, skipping: {e}")
        return []
