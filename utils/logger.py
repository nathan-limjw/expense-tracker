import logging
import os

from utils.config import LOG_LEVEL


def get_logger(name: str):
    log_level = os.getenv(LOG_LEVEL, "DEBUG")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        )
        logger.addHandler(handler)

    return logger
