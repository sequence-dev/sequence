#! /usr/bin/env python
import numpy as np
from landlab import Component
from scipy.interpolate import interp1d


class BathymetryReader(Component):

    _name = "Bathymetry"

    _input_var_names = ()

    _output_var_names = ("bedrock_surface__elevation",)

    _var_units = {"bedrock_surface__elevation": "m"}

    _var_mapping = {"bedrock_surface__elevation": "node"}

    _var_doc = {"bedrock_surface__elevation": "Surface elevation"}

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
        super(BathymetryReader, self).__init__(grid, **kwds)

        data = np.loadtxt(filepath, delimiter=",")
        self._bathymetry = interp1d(
            data[:, 0],
            data[:, 1],
            kind=kind,
            copy=True,
            assume_sorted=True,
            bounds_error=True,
        )

        if "bedrock_surface__elevation" not in self.grid.at_node:
            self.grid.add_zeros("bedrock_surface__elevation", at="node")

    @property
    def x(self):
        return self.grid.x_of_node[self.grid.nodes_at_bottom_edge]

    @property
    def z(self):
        return self.grid.at_node["bedrock_surface__elevation"][
            self.grid.nodes_at_bottom_edge
        ]

    def run_one_step(self, dt=None):
        z = self.grid.at_node["bedrock_surface__elevation"].reshape(self.grid.shape)
        z[:] = self._bathymetry(self.grid.x_of_node[self.grid.nodes_at_bottom_edge])
