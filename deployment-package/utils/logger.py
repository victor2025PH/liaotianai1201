import logging
import os
import config
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = config.LOGS_DIR
LOG_PATH = os.path.join(LOGS_DIR, "bot.log")


def setup_logger(name="tg_business_ai"):
    """
    统一日志系统，自动控制台+按天分文件
    """
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件日志，按天分割，最多保留30天
    file_handler = TimedRotatingFileHandler(
        LOG_PATH, when="midnight", backupCount=30, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def log_debug(msg, name="tg_business_ai"):
    logger = logging.getLogger(name)
    logger.debug(msg)


def log_info(msg, name="tg_business_ai"):
    logger = logging.getLogger(name)
    logger.info(msg)


def log_warning(msg, name="tg_business_ai"):
    logger = logging.getLogger(name)
    logger.warning(msg)


def log_error(msg, name="tg_business_ai"):
    logger = logging.getLogger(name)
    logger.error(msg)


def log_exception(msg, name="tg_business_ai"):
    logger = logging.getLogger(name)
    logger.exception(msg)


if __name__ == "__main__":
    logger = setup_logger()
    logger.info("日志系统初始化成功！")
    log_warning("测试警告日志")
    log_error("测试错误日志")
