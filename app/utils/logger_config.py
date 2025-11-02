import sys
from loguru import logger
from app.models.models import config


def setup_logger(log_level: str, log_format: str):
    logger.remove()

    if log_format is None:
        log_format = "{time:YYYY-MM-DD HH:mm:ss, Europe/Rome}  | {level} | {name} | {function} | {line} | {message}"

    logger.add(sys.stdout, level=log_level, format=log_format, backtrace=True, diagnose=True)

    return logger


logger_index_txt = setup_logger(config.LOG_LEVEL, config.LOG_FORMAT)
