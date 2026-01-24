"""Logging configuration and utilities using rich library."""

import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


class BuildLogger:
    """Enhanced logger for build operations with rich console output."""

    def __init__(self, name: str, log_file: Path | None = None, level: int = logging.INFO):
        """
        Initialize BuildLogger.

        Args:
            name: Logger name
            log_file: Optional path to log file
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []  # Clear existing handlers

        # Rich console for colored output
        self.console = Console(stderr=True)

        # Rich handler for console output
        rich_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        rich_handler.setLevel(level)
        rich_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
        rich_handler.setFormatter(rich_formatter)
        self.logger.addHandler(rich_handler)

        # File handler if log file specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(msg, *args, **kwargs)

    def set_level(self, level: int):
        """Set logging level."""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(level)


# Global logger instance
_global_logger: BuildLogger | None = None


def setup_logging(
    name: str = "adibuild",
    log_file: Path | None = None,
    level: int = logging.INFO,
) -> BuildLogger:
    """
    Setup global logging configuration.

    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level

    Returns:
        BuildLogger instance
    """
    global _global_logger
    _global_logger = BuildLogger(name, log_file, level)
    return _global_logger


def get_logger(name: str | None = None) -> BuildLogger:
    """
    Get logger instance.

    Args:
        name: Optional logger name (uses global logger if None)

    Returns:
        BuildLogger instance
    """
    global _global_logger
    if name and name != "adibuild":
        # Create new logger for specific component
        return BuildLogger(name)
    if _global_logger is None:
        _global_logger = setup_logging()
    return _global_logger
