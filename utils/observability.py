from langfuse.langchain import CallbackHandler

from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def get_langfuse_callbacks(trace_name: str, user_id: str, metadata: dict = {}):
    if not settings.LANGFUSE_PUBLIC_KEY:
        logger.warning("LANGFUSE_PUBLIC_KEY not set, skipping tracing...")
        return []
    try:
        logger.info(f"Langfuse initialised for trace: {trace_name}")
        return [CallbackHandler(user_id=str(user_id))]
    except Exception as e:
        logger.warning(f"Langfuse init failed, skipping: {e}")
        return []
