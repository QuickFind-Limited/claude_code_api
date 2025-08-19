"""
Tests for the logging configuration module.

These tests verify that the logging configuration works correctly
and provides the expected functionality.
"""

import os
import tempfile
from unittest.mock import patch

import pytest
from claude_sdk_server.utils.logging_config import (
    LoggingConfig,
    get_log_context,
    get_logger,
    setup_logging,
)


class TestLoggingConfig:
    """Test cases for LoggingConfig class."""

    def test_get_log_level_default(self):
        """Test that default log level is INFO."""
        config = LoggingConfig()
        assert config.log_level == "INFO"

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_get_log_level_from_env(self):
        """Test that log level is read from environment variable."""
        config = LoggingConfig()
        assert config.log_level == "DEBUG"

    def test_ensure_log_dir_creation(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                config = LoggingConfig()
                assert config.log_dir.exists()
                assert config.log_dir.name == "logs"
            finally:
                os.chdir(original_cwd)

    def test_console_format_structure(self):
        """Test that console format has expected structure."""
        config = LoggingConfig()
        format_str = config._get_console_format()

        # Check that format contains expected elements
        assert "{time:" in format_str
        assert "{level:" in format_str
        assert "{name}" in format_str
        assert "{function}" in format_str
        assert "{line}" in format_str
        assert "{message}" in format_str

    def test_file_format_structure(self):
        """Test that file format has expected structure."""
        config = LoggingConfig()
        format_str = config._get_file_format()

        # Check that format contains expected elements
        assert "{time:" in format_str
        assert "{level:" in format_str
        assert "{name}" in format_str
        assert "{function}" in format_str
        assert "{line}" in format_str
        assert "{process.id}" in format_str
        assert "{thread.id}" in format_str
        assert "{message}" in format_str

    def test_reasoning_format_structure(self):
        """Test that reasoning format has expected structure."""
        config = LoggingConfig()
        format_str = config._get_reasoning_format()

        # Check that format contains expected elements
        assert "{time:" in format_str
        assert "REASONING" in format_str
        assert "{name}" in format_str
        assert "{message}" in format_str

    def test_is_reasoning_log_detection(self):
        """Test reasoning log detection."""
        config = LoggingConfig()

        # Test with reasoning keywords
        reasoning_record = {"message": "thinking: about this problem", "extra": {}}
        assert config._is_reasoning_log(reasoning_record) is True

        # Test with explicit log type
        explicit_record = {
            "message": "some message",
            "extra": {"log_type": "reasoning"},
        }
        assert config._is_reasoning_log(explicit_record) is True

        # Test with emoji indicators
        emoji_record = {"message": "🤔 pondering this decision", "extra": {}}
        assert config._is_reasoning_log(emoji_record) is True

        # Test normal log
        normal_record = {"message": "regular log message", "extra": {}}
        assert config._is_reasoning_log(normal_record) is False


class TestGetLogger:
    """Test cases for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")
        assert logger is not None

        # Test that logger has standard methods
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")

    def test_get_logger_custom_methods(self):
        """Test that logger has custom methods."""
        logger = get_logger("test_module")

        # Test custom methods exist
        assert hasattr(logger, "reasoning")
        assert hasattr(logger, "analysis")
        assert hasattr(logger, "decision")
        assert hasattr(logger, "thought")
        assert hasattr(logger, "context")
        assert hasattr(logger, "performance")
        assert hasattr(logger, "structured")

    def test_get_logger_without_name(self):
        """Test that get_logger works without explicit name."""
        logger = get_logger()
        assert logger is not None

    def test_get_logger_with_explicit_name(self):
        """Test that get_logger works with explicit name."""
        logger = get_logger("explicit_test_module")
        assert logger is not None


class TestLogContext:
    """Test cases for log context functionality."""

    def test_get_log_context(self):
        """Test get_log_context function."""
        context = get_log_context(operation="test", user_id="123")

        assert "timestamp" in context
        assert "context" in context
        assert context["context"]["operation"] == "test"
        assert context["context"]["user_id"] == "123"

    def test_get_log_context_empty(self):
        """Test get_log_context with no parameters."""
        context = get_log_context()

        assert "timestamp" in context
        assert "context" in context
        assert context["context"] == {}


class TestSetupLogging:
    """Test cases for setup_logging function."""

    def test_setup_logging_idempotent(self):
        """Test that setup_logging can be called multiple times safely."""
        # This should not raise an exception
        setup_logging()
        setup_logging()
        setup_logging()

    def test_setup_logging_creates_config(self):
        """Test that setup_logging initializes the configuration."""
        # Clear any existing config
        import claude_sdk_server.utils.logging_config as log_module

        log_module._logging_config = None

        # Setup logging
        setup_logging()

        # Verify config was created
        assert log_module._logging_config is not None
        assert isinstance(log_module._logging_config, LoggingConfig)


if __name__ == "__main__":
    pytest.main([__file__])
