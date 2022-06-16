#! /usr/bin/env python
import numpy as np
from landlab import Component
from scipy import interpolate


class BathymetryReader(Component):

    _name = "Bathymetry"

    _unit_agnostic = True

    _info = {
        "topographic__elevation": {
            "dtype": "float",
            "intent": "out",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "Surface elevation",
        }
    }

    def __init__(self, grid, filepath=None, kind="linear", **kwds):
        """Generate a bathymetric profile from a file.

        Parameters
        ----------
        grid: RasterModelGrid
            A landlab grid.
        filepath: str
            Name of csv-formatted bathymetry file.
        kind: str, optional
            Kind of interpolation as a string (one of 'linear',
            'nearest', 'zero', 'slinear', 'quadratic', 'cubic').
            Default is 'linear'.
        """
        super().__init__(grid, **kwds)

        data = np.loadtxt(filepath, delimiter=",", comments="#")
        self._bathymetry = interpolate.interp1d(
            data[:, 0],
            data[:, 1],
            kind=kind,
            copy=True,
            assume_sorted=True,
            bounds_error=True,
        )

        if "topographic__elevation" not in self.grid.at_node:
            self.grid.add_zeros("topographic__elevation", at="node")

    @property
    def x(self):
        return self.grid.x_of_node[self.grid.nodes_at_bottom_edge]

    @property
    def z(self):
        return self.grid.at_node["topographic__elevation"][
            self.grid.nodes_at_bottom_edge
        ]

    def run_one_step(self, dt=None):
        z = self.grid.at_node["topographic__elevation"].reshape(self.grid.shape)
        z[:] = self._bathymetry(self.grid.x_of_node[self.grid.nodes_at_bottom_edge])
