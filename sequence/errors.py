class SequenceError(Exception):
    pass


class ShorelineError(SequenceError):
    def __init__(self, msg):
        self._msg = str(msg)

    def __str__(self):
        return self._msg


class ShelfEdgeError(SequenceError):
    def __init__(self, msg):
        self._msg = str(msg)

    def __str__(self):
        return self._msg


class MissingRequiredVariable(SequenceError):
    def __init__(self, name):
        self._name = name

    def __str_(self):
        return f"{self._name}"
