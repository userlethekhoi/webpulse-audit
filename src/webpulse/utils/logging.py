"""Logging utility configuration for the WebPulse auditing framework.

This module configures structured, level-based console logging, adhering to
terminal color guidelines (including the NO_COLOR standard) and verbosity targets.
"""

import logging
import os
import sys

# Color mapping for log levels using standard ANSI escape sequences
COLOR_CODES = {
    logging.DEBUG: "\033[36m",  # Cyan
    logging.INFO: "\033[32m",  # Green
    logging.WARNING: "\033[33m",  # Yellow
    logging.ERROR: "\033[31m",  # Red
    logging.CRITICAL: "\033[1;31m",  # Bold Red
}
RESET_CODE = "\033[0m"


class WebPulseConsoleFormatter(logging.Formatter):
    """Custom log formatter supporting conditional ANSI color rendering."""

    def __init__(self, use_color: bool = True) -> None:
        """Initialize the formatter.

        Args:
            use_color: If True, uses ANSI color escape sequences in output.
        """
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record.

        Args:
            record: The LogRecord instance to format.

        Returns:
            The formatted log message string.
        """
        level_name = record.levelname
        message = record.getMessage()

        # Apply coloring if color output is enabled
        if self.use_color and record.levelno in COLOR_CODES:
            colored_level = f"{COLOR_CODES[record.levelno]}[{level_name}]{RESET_CODE}"
            log_line = f"{colored_level} {message}"
        else:
            log_line = f"[{level_name}] {message}"

        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"

        return log_line


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger for the WebPulse CLI application.

    Args:
        level: The minimum logging level to output.
    """
    root_logger = logging.getLogger("webpulse")
    root_logger.setLevel(level)

    # Clean existing handlers to prevent duplicate logging
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Enforce NO_COLOR spec: https://no-color.org/
    no_color = "NO_COLOR" in os.environ
    is_tty = sys.stdout.isatty()
    use_color = is_tty and not no_color

    formatter = WebPulseConsoleFormatter(use_color=use_color)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
