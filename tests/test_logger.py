"""Tests for the logger module."""

import pytest
import logging
from unittest.mock import patch, Mock
import os

from ai.utils.logger import get_logger, setup_logging


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_basic(self):
        """Test basic logger creation."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_hierarchy(self):
        """Test logger hierarchy."""
        parent = get_logger("ai")
        child = get_logger("ai.backends")

        assert child.parent == parent

    def test_get_logger_same_instance(self):
        """Test that same name returns same instance."""
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")

        assert logger1 is logger2


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_default(self):
        """Test default logging setup."""
        with patch("logging.basicConfig") as mock_config:
            setup_logging()

            mock_config.assert_called_once()
            call_args = mock_config.call_args

            # Check default level
            assert call_args[1]["level"] == logging.INFO

            # Check format
            assert "%(asctime)s" in call_args[1]["format"]
            assert "%(name)s" in call_args[1]["format"]
            assert "%(levelname)s" in call_args[1]["format"]
            assert "%(message)s" in call_args[1]["format"]

    def test_setup_logging_custom_level(self):
        """Test custom logging level."""
        with patch("logging.basicConfig") as mock_config:
            setup_logging(level=logging.DEBUG)

            call_args = mock_config.call_args
            assert call_args[1]["level"] == logging.DEBUG

    def test_setup_logging_from_env_debug(self):
        """Test setting log level from DEBUG environment variable."""
        with patch.dict(os.environ, {"DEBUG": "true"}):
            with patch("logging.basicConfig") as mock_config:
                setup_logging()

                call_args = mock_config.call_args
                assert call_args[1]["level"] == logging.DEBUG

    def test_setup_logging_from_env_log_level(self):
        """Test setting log level from LOG_LEVEL environment variable."""
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]

        for env_value, expected_level in test_cases:
            with patch.dict(os.environ, {"LOG_LEVEL": env_value}):
                with patch("logging.basicConfig") as mock_config:
                    setup_logging()

                    call_args = mock_config.call_args
                    assert call_args[1]["level"] == expected_level

    def test_setup_logging_invalid_env_level(self):
        """Test invalid LOG_LEVEL falls back to default."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            with patch("logging.basicConfig") as mock_config:
                setup_logging()

                call_args = mock_config.call_args
                assert call_args[1]["level"] == logging.INFO

    def test_setup_logging_custom_format(self):
        """Test custom log format."""
        custom_format = "%(levelname)s: %(message)s"

        with patch("logging.basicConfig") as mock_config:
            setup_logging(format=custom_format)

            call_args = mock_config.call_args
            assert call_args[1]["format"] == custom_format

    def test_setup_logging_with_handlers(self):
        """Test setup with custom handlers."""
        handler = Mock(spec=logging.Handler)

        with patch("logging.basicConfig") as mock_config:
            setup_logging(handlers=[handler])

            call_args = mock_config.call_args
            assert call_args[1]["handlers"] == [handler]


class TestLoggingIntegration:
    """Test logging integration."""

    def test_logger_output(self, capsys):
        """Test actual logger output."""
        # Create a new logger with a stream handler for testing
        import io
        from logging import StreamHandler

        # Create a string buffer to capture output
        log_capture = io.StringIO()
        handler = StreamHandler(log_capture)
        handler.setFormatter(
            logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        )

        # Create a test logger
        logger = logging.getLogger("test.output.unique")
        logger.handlers = []  # Clear any existing handlers
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # Log at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Check output
        output = log_capture.getvalue()
        assert "Debug message" in output
        assert "Info message" in output
        assert "Warning message" in output
        assert "Error message" in output
        assert "test.output.unique" in output

    def test_logger_filtering_by_level(self, capsys):
        """Test that log level filtering works."""
        import io
        from logging import StreamHandler

        # Create a string buffer to capture output
        log_capture = io.StringIO()
        handler = StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(message)s"))

        # Create a test logger
        logger = logging.getLogger("test.filter.unique")
        logger.handlers = []  # Clear any existing handlers
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        logger.debug("Should not appear")
        logger.info("Should not appear")
        logger.warning("Should appear")
        logger.error("Should appear")

        output = log_capture.getvalue()
        assert "Should not appear" not in output
        assert "Should appear" in output


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_debug_env_variations(self):
        """Test various DEBUG environment variable values."""
        true_values = ["true", "True", "TRUE", "1", "yes", "on"]
        false_values = ["false", "False", "FALSE", "0", "no", "off", ""]

        for value in true_values:
            with patch.dict(os.environ, {"DEBUG": value}):
                with patch("logging.basicConfig") as mock_config:
                    setup_logging()
                    call_args = mock_config.call_args
                    assert call_args[1]["level"] == logging.DEBUG

        for value in false_values:
            with patch.dict(os.environ, {"DEBUG": value}):
                with patch("logging.basicConfig") as mock_config:
                    setup_logging()
                    call_args = mock_config.call_args
                    assert call_args[1]["level"] == logging.INFO

    def test_env_precedence(self):
        """Test that LOG_LEVEL takes precedence over DEBUG."""
        with patch.dict(os.environ, {"DEBUG": "true", "LOG_LEVEL": "ERROR"}):
            with patch("logging.basicConfig") as mock_config:
                setup_logging()

                call_args = mock_config.call_args
                assert call_args[1]["level"] == logging.ERROR
