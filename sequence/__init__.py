"""A sequence-stratigraphic model of a 1D profile written with *Landlab*."""
from sequence._grid import SequenceModelGrid
from sequence._version import __version__
from sequence.sequence import Sequence
from sequence.sequence_model import SequenceModel

__all__ = [
    "__version__",
    "Sequence",
    "SequenceModel",
    "SequenceModelGrid",
]
