# utils/logger.py
# Centralised logging for Hinata.

import os
import logging
import sys

from config import Config


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(f"hinata.{name}")

    if not logger.handlers:
        logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))

        # Console handler with colors
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s │ %(name)-25s │ %(levelname)-7s │ %(message)s",
            datefmt="%H:%M:%S",
        )
        console.setFormatter(formatter)
        logger.addHandler(console)

        # File handler (optional)
        log_dir = os.path.join(Config.DATA_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "hinata.log"),
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
