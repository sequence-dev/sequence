"""Subside a `SequenceModelGrid`."""
import os

import numpy as np
from landlab import Component
from scipy import interpolate


class SubsidenceTimeSeries(Component):
    """A *Landlab* component that subsides a grid."""

    _name = "Subsider"

    _time_units = "y"

    _info = {
        "bedrock_surface__increment_of_elevation": {
            "dtype": "float",
            "intent": "out",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "Increment of elevation",
        },
        "bedrock_surface__elevation": {
            "dtype": "float",
            "intent": "inout",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "Surface elevation",
        },
    }

    def __init__(self, grid, filepath: os.PathLike, kind: str = "linear"):
        """Create a grid subsider from a time-series file.

        Parameters
        ----------
        grid: :class:`~sequence.grid.SequenceModelGrid`
            A landlab grid.
        filepath: os.PathLike
            Name of csv-formatted subsidence file.
        kind: str, optional
            Kind of interpolation as a string (one of 'linear',
            'nearest', 'zero', 'slinear', 'quadratic', 'cubic').
            Default is 'linear'.
        """
        if "bedrock_surface__elevation" not in grid.at_node:
            grid.add_empty("bedrock_surface__elevation", at="node")

        super().__init__(grid)

        self._filepath = filepath
        self._kind = kind

        data = np.loadtxt(filepath, delimiter=",", comments="#")
        subsidence = SubsidenceTimeSeries._subsidence_interpolator(
            data, kind=self._kind
        )
        if "bedrock_surface__increment_of_elevation" not in grid.at_node:
            self.grid.add_empty("bedrock_surface__increment_of_elevation", at="node")

        inc = self.grid.at_node["bedrock_surface__increment_of_elevation"].reshape(
            self.grid.shape
        )
        inc[:] = subsidence(self.grid.x_of_node[self.grid.nodes_at_bottom_edge])

        self._dz = inc.copy()
        self._time = 0.0

    @staticmethod
    def _subsidence_interpolator(data, kind="linear"):
        return interpolate.interp1d(
            data[:, 0],
            data[:, 1],
            kind=kind,
            copy=True,
            assume_sorted=True,
            bounds_error=True,
        )

    @property
    def time(self) -> float:
        """Return the current component time."""
        return self._time

    @property
    def filepath(self) -> str:
        """Return the path to the current subsidence file."""
        return str(self._filepath)

    @filepath.setter
    def filepath(self, new_path: os.PathLike):
        self._filepath = new_path
        subsidence = SubsidenceTimeSeries._subsidence_interpolator(
            np.loadtxt(self._filepath, delimiter=",", comments="#"), kind=self._kind
        )
        inc = self.grid.at_node["bedrock_surface__increment_of_elevation"].reshape(
            self.grid.shape
        )
        inc[:] = subsidence(self.grid.x_of_node[self.grid.nodes_at_bottom_edge])
        self._dz = inc.copy()

    def run_one_step(self, dt: float) -> None:
        """Update the component by a time step.

        Parameters
        ----------
        dt : float
            The time step to update the component by.
        """
        dz = self.grid.at_node["bedrock_surface__increment_of_elevation"]
        z = self.grid.at_node["bedrock_surface__elevation"]
        z_top = self.grid.at_node["topographic__elevation"]

        dz = dz.reshape(self.grid.shape)
        z = z.reshape(self.grid.shape)
        z_top = z_top.reshape(self.grid.shape)

        dz[:] = self._dz * dt
        z[:] += dz
        z_top[:] += dz

        self._time += dt
