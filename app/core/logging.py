import logging
import logging.config
import sys

from app.config import Settings, get_settings

settings: Settings = get_settings()


def setup_logging():
    env: str = settings.ENV
    log_level: str = settings.LOG_LEVEL

    if env == "production":
        log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    else:
        log_format = "\033[36m%(asctime)s\033[0m | \033[32m%(levelname)-8s\033[0m | \033[33m%(name)s\033[0m | %(message)s"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
