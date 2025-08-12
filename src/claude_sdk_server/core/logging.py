"""Logging configuration using loguru."""

import sys
from pathlib import Path
from loguru import logger

from .config import settings


def setup_logging() -> None:
    """Configure loguru logging."""
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stderr,
        format=settings.log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=settings.debug,
        diagnose=settings.debug
    )
    
    # File handler (if configured)
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.log_file,
            format=settings.log_format,
            level=settings.log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=settings.debug,
            diagnose=settings.debug
        )
    
    # Add custom levels
    logger.level("REQUEST", no=25, color="<blue>")
    logger.level("RESPONSE", no=26, color="<green>")
    
    logger.info(f"Logging initialized - Level: {settings.log_level}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")


def get_logger(name: str = None):
    """Get a logger instance."""
    if name:
        return logger.bind(name=name)
    return logger


# Initialize logging on import
setup_logging()

# Export configured logger
__all__ = ["logger", "get_logger", "setup_logging"]