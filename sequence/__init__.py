"""A sequence-stratigraphic model of a 1D profile written with *Landlab*."""
from ._grid import SequenceModelGrid
from ._version import __version__
from .sequence import Sequence
from .sequence_model import SequenceModel

__all__ = [
    "__version__",
    "Sequence",
    "SequenceModel",
    "SequenceModelGrid",
]
