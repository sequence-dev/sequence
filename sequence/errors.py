"""Errors used by *sequence*."""
from __future__ import annotations


class SequenceError(Exception):
    """All *sequence* errors should inherit from this class."""

    pass


class ShorelineError(SequenceError):
    """Raise this exception if there was an error locating the shoreline."""

    def __init__(self, msg: str):
        self._msg = str(msg)

    def __str__(self) -> str:
        """Return an error message in human-readable form."""
        return self._msg


class ShelfEdgeError(SequenceError):
    """Raise this exception is there was an errors locating the shelf edge."""

    def __init__(self, msg: str):
        self._msg = str(msg)

    def __str__(self) -> str:
        """Return an error message in human-readable form."""
        return self._msg


class OutputValidationError(SequenceError):
    """Raise this exception if there is something wrong with an output file."""

    pass


class InvalidRowError(OutputValidationError):
    """Raise this exception if a required variable is missing from an output file."""

    def __init__(self, row: int, n_rows: int):
        self._row = row
        self._n_rows = n_rows

    def __str__(self) -> str:
        """Return error message that includes the requested row."""
        return f"row {self._row!r} is out of bounds for output file with {self._n_rows} rows"


class MissingRequiredVariable(OutputValidationError):
    """Raise this exception if a required variable is missing from an output file."""

    def __init__(self, name: str):
        self._name = name

    def __str__(self) -> str:
        """Return error message that includes the name of the missing variable."""
        return f"requireed variable ({self._name!r}) is missing from output file"


class ParameterMismatchError(SequenceError):
    """Raise this exception if values from two configurations are mismatched."""

    def __init__(self, keys):
        self.keys = tuple(keys)

    def __str__(self):
        """Return an error message with the offending keys."""
        params = ", ".join([repr(key) for key in self.keys])
        return f"mismatch in parameter{'s' if len(self.keys) > 1 else ''}: {params}"
