"""Tests for logger configuration helpers."""

import logging

from adibuild.utils import logger as logger_module


def test_get_logger_reuses_named_logger_without_duplicate_handlers():
    logger_module._global_logger = None
    logger_module._named_loggers.clear()

    logger_module.setup_logging(level=logging.DEBUG)

    first = logger_module.get_logger("adibuild.vivado")
    second = logger_module.get_logger("adibuild.vivado")

    assert first is second
    assert first.logger.propagate is False
    assert len(first.logger.handlers) == 1
