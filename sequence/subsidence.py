"""Subside a `SequenceModelGrid`."""
import os
from collections.abc import Callable
from typing import Union

import numpy as np
from landlab import Component
from numpy.typing import NDArray
from scipy import interpolate

from sequence._grid import SequenceModelGrid


class SubsidenceTimeSeries(Component):
    """A *Landlab* component that subsides a grid."""

    _name = "Subsider"

    _time_units = "y"

    _info = {
        "bedrock_surface__increment_of_elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "Change in elevation due to subsidence",
        }
    }

    def __init__(
        self, grid: SequenceModelGrid, filepath: os.PathLike, kind: str = "linear"
    ):
        """Create a grid subsider from a time-series file.

        Parameters
        ----------
        grid: SequenceModelGrid
            A landlab grid.
        filepath: os.PathLike
            Name of csv-formatted subsidence file.
        kind: str, optional
            Kind of interpolation as a string (one of 'linear',
            'nearest', 'zero', 'slinear', 'quadratic', 'cubic').
            Default is 'linear'.
        """
        if "bedrock_surface__increment_of_elevation" not in grid.at_node:
            grid.add_zeros("bedrock_surface__increment_of_elevation", at="node")

        super().__init__(grid)

        self._filepath = filepath
        self._kind = kind

        data = np.loadtxt(filepath, delimiter=",", comments="#")
        self._subsidence = SubsidenceTimeSeries._subsidence_interpolator(
            data, kind=self._kind
        )

        self._dz_dt = self._calc_subsidence_rate()

        self._time = 0.0

    @property
    def subsidence_rate(self) -> NDArray:
        """Return the current subsidence rate."""
        return self._dz_dt

    @staticmethod
    def _subsidence_interpolator(
        data: NDArray, kind: str = "linear"
    ) -> Callable[[Union[float, NDArray]], NDArray]:
        return interpolate.interp1d(
            data[:, 0],
            data[:, 1],
            kind=kind,
            copy=True,
            assume_sorted=True,
            bounds_error=True,
        )

    def _calc_subsidence_rate(self) -> NDArray:
        return self._subsidence(self.grid.x_of_node[self.grid.nodes_at_bottom_edge])

    @property
    def time(self) -> float:
        """Return the current component time."""
        return self._time

    @property
    def filepath(self) -> str:
        """Return the path to the current subsidence file."""
        return str(self._filepath)

    @filepath.setter
    def filepath(self, new_path: os.PathLike) -> None:
        self._filepath = new_path
        self._subsidence = SubsidenceTimeSeries._subsidence_interpolator(
            np.loadtxt(self._filepath, delimiter=",", comments="#"), kind=self._kind
        )

        self._dz_dt = self._calc_subsidence_rate()

    def run_one_step(self, dt: float) -> None:
        """Update the component by a time step.

        Parameters
        ----------
        dt : float
            The time step to update the component by.
        """
        self.grid.get_profile("bedrock_surface__increment_of_elevation")[:] += (
            self.subsidence_rate * dt
        )

        self._time += dt
