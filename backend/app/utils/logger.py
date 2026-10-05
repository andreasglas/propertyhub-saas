import logging
from logging.config import dictConfig

import structlog


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {"handlers": ["console"], "level": "INFO"},
        }
    )
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))


def get_logger(name: str):
    return structlog.get_logger(name)
