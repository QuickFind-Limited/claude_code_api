"""
Comprehensive logging configuration module for claude_sdk_server.

This module provides structured, clean logging using loguru with:
- Environment-based configuration
- Custom formatters for different log types
- Special handling for reasoning/thinking blocks
- Contextual information (timestamps, modules, line numbers)
- Multiple log levels with appropriate formatting
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


class LoggingConfig:
    """Centralized logging configuration for the application."""

    # Color codes for different log levels
    COLORS = {
        "TRACE": "\033[36m",  # Cyan
        "DEBUG": "\033[34m",  # Blue
        "INFO": "\033[32m",  # Green
        "SUCCESS": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self):
        self.log_level = self._get_log_level()
        self.log_dir = self._ensure_log_dir()
        self._configure_logger()

    def _get_log_level(self) -> str:
        """Get log level from environment variable with fallback to INFO."""
        return os.getenv("LOG_LEVEL", "INFO").upper()

    def _ensure_log_dir(self) -> Path:
        """Ensure log directory exists and return its path."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        return log_dir

    def _get_console_format(self) -> str:
        """Get console log format with colors and structure."""
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    def _get_file_format(self) -> str:
        """Get file log format without colors but with full context."""
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{process.id}:{thread.id} | "
            "{message}"
        )

    def _get_reasoning_format(self) -> str:
        """Get special format for reasoning/thinking logs."""
        return (
            "<blue>{time:HH:mm:ss}</blue> | "
            "<yellow>REASONING</yellow> | "
            "<green>{name}</green> | "
            "<white>{message}</white>"
        )

    def _configure_logger(self) -> None:
        """Configure loguru logger with custom settings."""
        # Remove default handler
        logger.remove()

        # Add console handler with colors and formatting
        logger.add(
            sys.stdout,
            format=self._get_console_format(),
            level=self.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
            filter=self._general_filter,
            enqueue=True,  # Thread-safe logging
        )

        # Add file handler for all logs
        logger.add(
            self.log_dir / "app.log",
            format=self._get_file_format(),
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            compression="gz",
            backtrace=True,
            diagnose=True,
            filter=self._general_filter,
            enqueue=True,
        )

        # Add separate error file handler
        logger.add(
            self.log_dir / "errors.log",
            format=self._get_file_format(),
            level="ERROR",
            rotation="5 MB",
            retention="14 days",
            compression="gz",
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )

        # Add reasoning/thinking handler with special formatting
        logger.add(
            sys.stdout,
            format=self._get_reasoning_format(),
            level="DEBUG",
            colorize=True,
            filter=self._reasoning_filter,
            enqueue=True,
        )

        # Add reasoning file handler
        logger.add(
            self.log_dir / "reasoning.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | REASONING | {name} | {message}",
            level="DEBUG",
            rotation="5 MB",
            retention="3 days",
            filter=self._reasoning_filter,
            enqueue=True,
        )

    def _general_filter(self, record: Dict[str, Any]) -> bool:
        """Filter out reasoning logs from general handlers."""
        return not self._is_reasoning_log(record)

    def _reasoning_filter(self, record: Dict[str, Any]) -> bool:
        """Filter to only include reasoning logs."""
        return self._is_reasoning_log(record)

    def _is_reasoning_log(self, record: Dict[str, Any]) -> bool:
        """Check if a log record is a reasoning/thinking log."""
        message = record.get("message", "").lower()
        extra = record.get("extra", {})

        # Check for reasoning indicators
        reasoning_keywords = [
            "thinking:",
            "reasoning:",
            "analysis:",
            "consideration:",
            "thought:",
            "reflection:",
            "decision:",
            "evaluation:",
        ]

        return (
            extra.get("log_type") == "reasoning"
            or any(keyword in message for keyword in reasoning_keywords)
            or message.startswith(("🤔", "💭", "🧠", "⚡"))
        )


# Global logging configuration instance
_logging_config: Optional[LoggingConfig] = None


def setup_logging() -> None:
    """Initialize the logging configuration."""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()


def get_logger(name: Optional[str] = None) -> Any:
    """
    Get a configured logger instance.

    Args:
        name: Optional name for the logger. If None, uses the calling module's name.

    Returns:
        Configured loguru logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
        >>> logger.reasoning("Analyzing user request for optimal response")
    """
    # Ensure logging is configured
    setup_logging()

    if name is None:
        # Auto-detect caller module name
        import inspect

        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            name = caller_frame.f_globals.get("__name__", "unknown")
        finally:
            del frame

    # Create a logger with custom methods
    custom_logger = logger.bind(name=name)

    # Add custom methods for different log types
    def reasoning(message: str, **kwargs) -> None:
        """Log reasoning/thinking messages with special formatting."""
        custom_logger.bind(log_type="reasoning").debug(f"💭 {message}", **kwargs)

    def analysis(message: str, **kwargs) -> None:
        """Log analysis messages."""
        custom_logger.bind(log_type="reasoning").debug(
            f"🔍 Analysis: {message}", **kwargs
        )

    def decision(message: str, **kwargs) -> None:
        """Log decision messages."""
        custom_logger.bind(log_type="reasoning").info(
            f"⚡ Decision: {message}", **kwargs
        )

    def thought(message: str, **kwargs) -> None:
        """Log thought processes."""
        custom_logger.bind(log_type="reasoning").debug(
            f"🧠 Thought: {message}", **kwargs
        )

    def context(message: str, context_data: Optional[Dict] = None, **kwargs) -> None:
        """Log with additional context data."""
        if context_data:
            custom_logger.bind(context=context_data).info(message, **kwargs)
        else:
            custom_logger.info(message, **kwargs)

    def performance(operation: str, duration: float, **kwargs) -> None:
        """Log performance metrics."""
        custom_logger.bind(operation=operation, duration=duration).info(
            f"⏱️  {operation} completed in {duration:.3f}s", **kwargs
        )

    def structured(event: str, **data) -> None:
        """Log structured data."""
        custom_logger.bind(**data).info(f"📊 {event}", **data)

    # Bind custom methods to the logger
    custom_logger.reasoning = reasoning
    custom_logger.analysis = analysis
    custom_logger.decision = decision
    custom_logger.thought = thought
    custom_logger.context = context
    custom_logger.performance = performance
    custom_logger.structured = structured

    return custom_logger


def configure_logging_for_module(
    module_name: str, level: Optional[str] = None, extra_handlers: Optional[list] = None
) -> Any:
    """
    Configure logging for a specific module with custom settings.

    Args:
        module_name: Name of the module
        level: Optional custom log level for this module
        extra_handlers: Optional list of additional handlers

    Returns:
        Configured logger for the module
    """
    logger_instance = get_logger(module_name)

    if level:
        # Create a filtered logger for specific level
        logger.add(
            sys.stdout,
            format=f"<cyan>{module_name}</cyan> | "
            + "<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
            level=level,
            filter=lambda record: record["name"] == module_name,
            colorize=True,
        )

    if extra_handlers:
        for handler in extra_handlers:
            logger.add(**handler)

    return logger_instance


def log_function_entry_exit(func):
    """
    Decorator to log function entry and exit with parameters and results.

    Usage:
        @log_function_entry_exit
        def my_function(param1, param2):
            return param1 + param2
    """

    def wrapper(*args, **kwargs):
        func_logger = get_logger(func.__module__)
        func_name = func.__qualname__

        # Log entry
        func_logger.debug(f"🚀 Entering {func_name} with args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            # Log successful exit
            func_logger.debug(
                f"✅ Exiting {func_name} with result type: {type(result).__name__}"
            )
            return result
        except Exception as e:
            # Log error exit
            func_logger.error(f"❌ {func_name} failed with error: {e}")
            raise

    return wrapper


def get_log_context(**context_data) -> Dict[str, Any]:
    """
    Create a log context dictionary for structured logging.

    Args:
        **context_data: Key-value pairs for context

    Returns:
        Dictionary with context data for logging
    """
    return {"timestamp": logger._datetime.now().isoformat(), "context": context_data}


# Initialize logging when module is imported
setup_logging()
