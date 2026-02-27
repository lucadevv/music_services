"""Logging configuration for the application."""
import logging
import sys
from typing import Optional
from app.core.config import get_settings

settings = get_settings()


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return the root logger for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). 
               Defaults to INFO, or DEBUG if not production.
        format_string: Custom format string for log messages.
    
    Returns:
        Configured logger instance.
    """
    if level is None:
        level = "DEBUG" if settings.VERSION.endswith("-dev") else "INFO"
    
    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        )
    
    # Create formatter
    formatter = logging.Formatter(
        fmt=format_string,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the logger (usually __name__).
    
    Returns:
        Logger instance configured for the module.
    """
    return logging.getLogger(name)
