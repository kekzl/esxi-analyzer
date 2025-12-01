"""
Logging configuration for ESXi Analyzer.

This module sets up and manages logging throughout the application.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from .config import config


def setup_logger(
    name: str = "esxi_analyzer", log_file: str | None = None, level: str | None = None, console: bool = True
) -> logging.Logger:
    """
    Set up and configure logger for the application.

    Args:
        name: Logger name
        log_file: Path to log file. If None, uses config setting.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). If None, uses config.
        console: Whether to also log to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Get configuration
    if level is None:
        level = config.get_logging("level") or "INFO"
    if log_file is None:
        log_file = config.get_logging("log_file") or "esxi_analyzer.log"

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        try:
            max_bytes = config.get_logging("max_bytes") or 10485760  # 10MB
            backup_count = config.get_logging("backup_count") or 5

            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not set up file logging to {log_file}: {e}")

    return logger


# Global logger instance
logger = setup_logger()
