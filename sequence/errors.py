"""Errors used by *sequence*."""


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


class MissingRequiredVariable(SequenceError):
    """Raise this exception if a required variable is missing from an output file."""

    def __init__(self, name: str):
        self._name = name

    def __str_(self) -> str:
        """Return an error message in human-readable form, including the name of the missing variable."""
        return f"{self._name!r}"
