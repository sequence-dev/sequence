"""Logger used for printing Sequence log messages."""
import contextlib
import logging
import sys
from typing import Any, Generator

import click

logger = logging.getLogger("sequence")

LOG_LEVEL_STYLES: dict[str, dict[str, Any]] = {
    "DEBUG": {"bold": True, "dim": True},
    "INFO": {"bold": True, "dim": True},
    "WARNING": {"bold": True, "fg": "bright_yellow"},
    "ERROR": {"bold": True, "fg": "red"},
    "CRITICAL": {"bold": True, "fg": "bright_red"},
}

MULTILINE_STYLES: dict[str, Any] = {"dim": True, "italic": True}


class LoggingHandler(logging.Handler):
    """Print Sequence log messages."""

    def emit(self, record: logging.LogRecord) -> None:
        """Print a log message.

        Parameters
        ----------
        record : LogRecord
            The log to print.
        """
        level_msg = click.style(
            f"[{record.levelname}]", **LOG_LEVEL_STYLES[record.levelname]
        )
        lines = record.getMessage().splitlines()
        if len(lines) == 0:
            lines = [""]
        print(f"{level_msg} {lines[0]}", file=sys.stderr)

        if len(lines) > 1:
            for line in lines[1:]:
                print(click.style(f"+ {line}", **MULTILINE_STYLES), file=sys.stderr)


@contextlib.contextmanager
def logging_handler() -> Generator[None, None, None]:
    """Change, temporarily, the current logger."""
    handler = LoggingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        yield
    finally:
        logger.removeHandler(handler)
