"""Logging utilities for the varman package.

This module provides logging functionality for the varman package,
with configuration from the config module.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from varman.config import get_config


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the specified module.

    Args:
        name: The name of the module.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured yet
    if not logger.handlers:
        config = get_config()
        
        # Get log level from config
        log_level_str = config.get_log_level()
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Get log file path from config
        log_file = config.get_log_file()
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Get max size and backup count from config
        max_size = config.get("logging", "max_size", 10 * 1024 * 1024)  # Default: 10 MB
        backup_count = config.get("logging", "backup_count", 3)  # Default: 3 backups
        
        # Create file handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count
        )
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Optionally add console handler if specified in config
        console_logging = config.get("logging", "console", False)
        if console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    return logger