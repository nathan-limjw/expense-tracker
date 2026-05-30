import json
import logging

from utils.config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        standard_fields = logging.LogRecord.__dict__.keys()
        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry)


def get_logger(name: str):
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        logger.propagate = False

    return logger
