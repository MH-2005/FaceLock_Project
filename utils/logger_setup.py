import logging
from logging.handlers import RotatingFileHandler
import os
import sys

def setup_logging():
    log_dir = "../logs"
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            print(f"Error creating log directory {log_dir}: {e}")
            sys.exit(1)

    logger = logging.getLogger("FaceLockLogger")

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s'
    )

    log_file_path = os.path.join(log_dir, "app.log")
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=2 * 1024 * 1024,  # 2 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    logger.info("="*50)
    logger.info("Logger initialized successfully.")
    logger.info("="*50)

    return logger