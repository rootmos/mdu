import logging.config
import os

from . import whoami, env

default_level = "INFO"

def mk_logging_config(level):
    assert(__name__.startswith(whoami))

    aws_request_id = os.environ.get("AWS_REQUEST_ID")
    if not aws_request_id:
        fmt = "%(asctime)s:%(name)s:%(levelname)s %(message)s"
        stream = "ext://sys.stderr"
    else:
        fmt = f"{aws_request_id}:%(name)s:%(levelname)s %(message)s"
        stream = "ext://sys.stdout"

    return {
        "version": 1,
        "formatters": {
            "default": {
                "format": fmt,
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "message-only": {
                "format": "%(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level.upper(),
                "formatter": "default",
                "stream": stream,
            },
        },
        "loggers": {
            whoami: {
                "level": 1,
                "handlers": ["console"],
            },
        },
    }

def setup(level: str | None = None):
    level = level or env("LOG_LEVEL") or default_level
    logging.config.dictConfig(mk_logging_config(level))

    logger = logging.getLogger(whoami)
    [handler] = logger.handlers
    return logger, handler

def remove_default_logging():
    l = logging.getLogger()
    while l.hasHandlers():
        l.removeHandler(l.handlers[0])
