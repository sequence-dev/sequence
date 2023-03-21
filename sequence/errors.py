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
        """Return error message that includes the name of the missing variable."""
        return f"{self._name!r}"


class ParameterMismatchError(SequenceError):
    """Raise this exception if values from two configurations are mismatched."""

    def __init__(self, keys):
        self.keys = tuple(keys)

    def __str__(self):
        """Return an error message with the offending keys."""
        params = ", ".join([repr(key) for key in self.keys])
        return f"mismatch in parameter{'s' if len(self.keys) > 1 else ''}: {params}"
