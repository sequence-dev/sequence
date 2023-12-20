"""Components that adjust sea level.

This module contains *Landlab* components used for adjusting
a grid's sea level.
"""
from __future__ import annotations

from collections.abc import Callable
from os import PathLike

import numpy as np
from landlab import Component
from numpy.typing import NDArray
from scipy import interpolate

from sequence._grid import SequenceModelGrid


class SeaLevelTimeSeries(Component):
    """Modify sea level through a time series."""

    _name = "Sea Level Changer"

    _time_units = "y"

    _unit_agnostic = True

    _info = {
        "sea_level__elevation": {
            "dtype": "float",
            "intent": "out",
            "optional": False,
            "units": "m",
            "mapping": "grid",
            "doc": "Sea level elevation",
        },
        "sea_level__increment_of_elevation": {
            "dtype": "float",
            "intent": "out",
            "optional": False,
            "units": "m",
            "mapping": "grid",
            "doc": "Change in sea level elevation",
        },
    }

    def __init__(
        self,
        grid: SequenceModelGrid,
        filepath: str | PathLike[str],
        kind: str = "linear",
        start: float = 0.0,
    ):
        """Generate sea level values.

        Parameters
        ----------
        grid: SequenceModelGrid
            A landlab grid.
        filepath: str
            Name of csv-formatted sea-level file.
        kind: str, optional
            Kind of interpolation as a string (one of 'linear',
            'nearest', 'zero', 'slinear', 'quadratic', 'cubic').
            Default is 'linear'.
        start : float, optional
            Set the initial time for the component.
        """
        super().__init__(grid)

        self._filepath = filepath
        self._kind = kind

        self._sea_level = SeaLevelTimeSeries._sea_level_interpolator(
            np.loadtxt(self._filepath, delimiter=","), kind=self._kind
        )
        self._time = start

    @staticmethod
    def _sea_level_interpolator(
        data: NDArray[np.floating], kind: str = "linear"
    ) -> Callable[[float | NDArray], NDArray]:
        return interpolate.interp1d(
            data[:, 0],
            data[:, 1],
            kind=kind,
            copy=True,
            assume_sorted=True,
            bounds_error=True,
        )

    @property
    def filepath(self) -> str | PathLike[str]:
        """Return the path to the sea-level file."""
        return self._filepath

    @filepath.setter
    def filepath(self, new_path: str | PathLike[str]) -> None:
        self._filepath = new_path
        self._sea_level = SeaLevelTimeSeries._sea_level_interpolator(
            np.loadtxt(self._filepath, delimiter=","), kind=self._kind
        )

    @property
    def time(self) -> float:
        """Return the current component time."""
        return self._time

    @time.setter
    def time(self, new_time: float) -> None:
        self._time = new_time

    def run_one_step(self, dt: float) -> None:
        """Update the component by a time step.

        Parameters
        ----------
        dt : float
            The time step.
        """
        self._time += dt
        old_sea_level = self.grid.at_grid["sea_level__elevation"]
        new_sea_level = self._sea_level(self.time)
        self.grid.at_grid["sea_level__elevation"] = new_sea_level
        self.grid.at_grid["sea_level__increment_of_elevation"] = (
            new_sea_level - old_sea_level
        )


class SinusoidalSeaLevel(SeaLevelTimeSeries):
    """Adjust a grid's sea level using a sine curve."""

    def __init__(
        self,
        grid: SequenceModelGrid,
        wave_length: float = 1.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        mean: float = 0.0,
        start: float = 0.0,
        linear: float = 0.0,
    ):
        """Generate sea level values.

        Parameters
        ----------
        grid: SequenceModelGrid
            A landlab grid.
        wave_length : float, optional
            The wave length of the sea-level curve in [y].
        amplitude : float, optional
            The amplitude of the sea-level curve.
        phase : float, optional
            The phase shift of the sea-level curve [y].
        mean : float, optional
            Mean sea-level (disregarding any trend with time).
        start : float, optional
            The time of the component [y].
        linear : float, optional
            Linear trend of the sea-level curve with time [m / y].
        """
        wave_length /= 2.0 * np.pi
        super(SeaLevelTimeSeries, self).__init__(grid)

        self._sea_level = (
            lambda time: (
                np.sin((time - phase) / wave_length)
                + 0.3 * np.sin((2 * (time - phase)) / wave_length)
            )
            * amplitude
            + mean
            + linear * time
        )

        self._time = start
