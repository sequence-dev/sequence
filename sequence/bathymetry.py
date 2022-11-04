"""Read bathymetry.

This module contains *Landlab* components to read bathymetry into a
`SequenceModelGrid`.
"""
import numpy as np
from landlab import Component
from scipy import interpolate


class BathymetryReader(Component):
    """Landlab component that reads bathymetry from a file."""

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
        grid: SequenceModelGrid
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
        """Return the x-coordinates of the grid."""
        return self.grid.x_of_node[self.grid.nodes_at_bottom_edge]

    @property
    def z(self):
        """Return the elevations along the grid."""
        return self.grid.at_node["topographic__elevation"][
            self.grid.nodes_at_bottom_edge
        ]

    def run_one_step(self, dt=None):
        """Update the grid's bathymetry.

        Parameters
        ----------
        dt : float, optional
            Time step to update the component by. Currently this
            value is unused.
        """
        z = self.grid.at_node["topographic__elevation"].reshape(self.grid.shape)
        z[:] = self._bathymetry(self.grid.x_of_node[self.grid.nodes_at_bottom_edge])


def _create_initial_profile(
    x,
    sl_plain=0.0008,
    init_shore=19750.0,
    hgt=15.0,
    alpha=1 / 2000.0,
    sl_sh=0.001,
    wavebase=60.0,
):

    # check shoreline is in array, else put in center of array
    if x[-1] < init_shore:
        init_shore = (x[0] + x[-1]) / 2

    z = np.empty_like(x)

    land = x < init_shore
    z[land] = (init_shore - x[land]) * sl_plain
    z[~land] = (init_shore - x[~land]) * sl_sh - hgt * (
        1 - np.exp((init_shore - x[~land]) * alpha)
    )

    return z
