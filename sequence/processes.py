"""All available processes to include in a *Sequence* model."""
from compaction.landlab import Compact

from sequence.fluvial import Fluvial
from sequence.sea_level import SeaLevelTimeSeries
from sequence.sea_level import SinusoidalSeaLevel
from sequence.sediment_flexure import SedimentFlexure
from sequence.shoreline import ShorelineFinder
from sequence.submarine import SubmarineDiffuser
from sequence.subsidence import SubsidenceTimeSeries

__all__ = [
    "Compact",
    "Fluvial",
    "SeaLevelTimeSeries",
    "SinusoidalSeaLevel",
    "SedimentFlexure",
    "ShorelineFinder",
    "SubmarineDiffuser",
    "SubsidenceTimeSeries",
]
