import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.config import load_config

config_values = load_config()

LOGS_FOLDER = config_values["LOGS_FOLDER"]

LOG_FILE = os.path.join(LOGS_FOLDER, "app.log")


def setup_logging():
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to prevent duplicate logs if called multiple times
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1024 * 1024 * 5, backupCount=2
    )  # 5MB per file, 2 backups

    # Create formatters and add it to handlers
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)

    # Add handlers to the root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Optional: Set a higher level for specific noisy loggers if needed
    # logging.getLogger('requests').setLevel(logging.WARNING)
    # logging.getLogger('urllib3').setLevel(logging.WARNING)

    # Setup checker errors logger
    CHECKER_ERRORS_LOG_FILE = os.path.join(LOGS_FOLDER, "checker_errors.log")
    checker_errors_logger = logging.getLogger("checker_errors_logger")
    checker_errors_logger.setLevel(logging.WARNING)
    checker_errors_handler = RotatingFileHandler(
        CHECKER_ERRORS_LOG_FILE, maxBytes=1024 * 1024 * 5, backupCount=2
    )
    checker_errors_handler.setFormatter(log_format)
    checker_errors_logger.addHandler(checker_errors_handler)
