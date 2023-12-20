"""Find the shoreline of a `SequenceModelGrid`.

This module contains methods for calculating a grid's shoreline and
shelf edge.
"""
from __future__ import annotations

import bisect

import numpy as np
from landlab import Component
from numpy.typing import NDArray
from scipy import interpolate

from sequence._grid import SequenceModelGrid
from sequence.errors import ShelfEdgeError
from sequence.errors import ShorelineError


class ShorelineFinder(Component):
    """Find a grid's shoreline."""

    _name = "Shoreline finder"

    _unit_agnostic = True

    _info = {
        "topographic__elevation": {
            "dtype": "float",
            "intent": "in",
            "optional": False,
            "units": "m",
            "mapping": "node",
            "doc": "Elevation of the land and sea floor",
        },
        "sea_level__elevation": {
            "dtype": "float",
            "intent": "in",
            "optional": False,
            "units": "m",
            "mapping": "grid",
            "doc": "Elevation of sea level",
        },
        "x_of_shore": {
            "dtype": "float",
            "intent": "out",
            "optional": False,
            "units": "m",
            "mapping": "row",
            "doc": "Position of the shore line",
        },
        "x_of_shelf_edge": {
            "dtype": "float",
            "intent": "out",
            "optional": False,
            "units": "m",
            "mapping": "row",
            "doc": "Position of the shelf edge",
        },
    }

    def __init__(self, grid: SequenceModelGrid, alpha: float = 0.0005):
        """Create a shoreline finder.

        Parameters
        ----------
        grid : SequenceModelGrid
            A Sequence grid.
        alpha : float, optional
            Parameter used to find the shoreline when
            interpolating between nodes.
        """
        super().__init__(grid)

        self._alpha = alpha
        self.grid.at_row["x_of_shore"] = np.zeros(self.grid.shape[0] - 2)
        self.grid.at_row["x_of_shelf_edge"] = np.zeros(self.grid.shape[0] - 2)

        x = self.grid.x_of_column
        z = self.grid.get_profile("topographic__elevation")
        dz = self.grid.get_profile("sediment_deposit__thickness")
        sea_level = self.grid.at_grid["sea_level__elevation"]

        x_of_shores = np.empty(z.shape[0], dtype=float)
        x_of_shelf_edges = np.empty(z.shape[0], dtype=float)

        for row in range(z.shape[0]):
            x_of_shore = find_shoreline(x, z[row], sea_level=sea_level)
            try:
                x_of_shelf_edge = find_shelf_edge(
                    x, dz[row], x_of_shore=x_of_shore, alpha=self._alpha
                )
            except ShelfEdgeError:
                x_of_shelf_edge = np.nan

            x_of_shores[row] = x_of_shore
            x_of_shelf_edges[row] = x_of_shelf_edge

        self.grid.at_row["x_of_shore"][:] = x_of_shores
        self.grid.at_row["x_of_shelf_edge"][:] = x_of_shelf_edges

    @property
    def alpha(self) -> float:
        """Return the *alpha* parameter used to calculate the shoreline."""
        return self._alpha

    def update(self) -> None:
        """Update the component one time step to find the new shoreline."""
        x = self.grid.x_of_column
        z = self.grid.get_profile("topographic__elevation")
        dz = self.grid.get_profile("sediment_deposit__thickness")
        sea_level = self.grid.at_grid["sea_level__elevation"]

        x_of_shores = np.empty(z.shape[0], dtype=float)
        x_of_shelf_edges = np.empty(z.shape[0], dtype=float)

        for row in range(z.shape[0]):
            x_of_shore = find_shoreline(x, z[row], sea_level=sea_level)
            try:
                x_of_shelf_edge = find_shelf_edge(
                    x, dz[row], x_of_shore=x_of_shore, alpha=self._alpha
                )
            except ShelfEdgeError:
                x_of_shelf_edge = np.nan
            else:
                assert x_of_shelf_edge > x_of_shore

            x_of_shores[row] = x_of_shore
            x_of_shelf_edges[row] = x_of_shelf_edge

        self.grid.at_row["x_of_shore"][:] = x_of_shores
        self.grid.at_row["x_of_shelf_edge"][:] = x_of_shelf_edges

    def run_one_step(self, dt: float | None = None) -> None:
        """Update the component on time step.

        Parameters
        ----------
        dt : float, optional
            The time step to update the component by. Since this component
            is not time-varying, this value is ignored.
        """
        self.update()


def find_shelf_edge_by_curvature(
    x: NDArray[np.floating], z: NDArray[np.floating], sea_level: float = 0.0
) -> float:
    """Find the x-coordinate of the shelf edge.

    The shelf edge is the location where the curvature of *sea-floor elevations*
    is a *minimum*.

    Parameters
    ----------
    x : ndarray of float
        x-positions of the profile.
    z : ndarray of float
        Elevations of the profile.
    sea_level : float, optional
        Elevation of sea level.

    Returns
    -------
    float
        The x-coordinate of the shelf edge.

    Examples
    --------
    >>> import numpy as np
    >>> from sequence.shoreline import find_shelf_edge_by_curvature

    >>> x = np.arange(50.)
    >>> z = - np.arctan(x / 5.0 - 5.0)
    >>> find_shelf_edge_by_curvature(x, z, sea_level=z.max())
    22.0
    """
    curvature = np.gradient(np.gradient(z, x), x)
    return x[np.argmin(curvature)]


def find_shelf_edge(
    x: NDArray[np.floating],
    dz: NDArray[np.floating],
    x_of_shore: NDArray[np.floating] | float = 0.0,
    alpha: float = 0.0005,
) -> float:
    """Find the shelf edge based on deposit thickness.

    Parameters
    ----------
    x : ndarray of float
        x-positions of the profile.
    dz : ndarray of float
        Deposit thickness.
    x_of_shore : float, optional
        The x-position of the shoreline.
    alpha : float, optional
        Constant used in interpolating the precise location of the
        shoreline.

    Returns
    -------
    float
        The x-coordinate of the shelf edge.

    Raises
    ------
    ShelfEdgeError
        If the data do not contain the shelf edge.

    Examples
    --------
    >>> import numpy as np
    >>> from sequence.shoreline import find_shelf_edge

    Create a depositional profile where the maximum deposition is at *x=1.0*.

    >>> x = np.arange(50.) / 5.0
    >>> deposit = x * np.exp(-x)
    >>> find_shelf_edge(x, deposit, x_of_shore=0.0, alpha=1e3)
    1.0
    """
    ind_of_shore = bisect.bisect(x, x_of_shore + 3.0 / alpha)
    if ind_of_shore >= len(dz):
        raise ShelfEdgeError("shelf edge is not contained in the data")

    return x[np.argmax(dz[ind_of_shore:]) + ind_of_shore]


def find_shoreline(
    x: NDArray[np.floating],
    z: NDArray[np.floating],
    sea_level: float = 0.0,
    kind: str = "cubic",
) -> NDArray[np.floating] | float:
    """Find the shoreline of a profile.

    Parameters
    ----------
    x : array of float
        X-positions of profile.
    z : array of float
        Elevations along the profile.
    sea_level : float, optional
        Elevation of sea level.
    kind : str, optional
        Interpolation method used to find shoreline. Values are the same
        as those used for `scipy.interpolate.interp1d`. Default is `'cubic'`.

    Returns
    -------
    float
        X-position of the shoreline.

    Examples
    --------
    >>> from sequence.shoreline import find_shoreline
    >>> import numpy as np

    Create a linearly-dipping profile.

    >>> x = np.arange(10.)
    >>> z = - x + 5.
    >>> z
    array([ 5.,  4.,  3.,  2.,  1.,  0., -1., -2., -3., -4.])

    Find the shoreline.

    >>> find_shoreline(x, z, kind='linear')
    5.0
    >>> find_shoreline(x, z, sea_level=.25, kind='linear')
    4.75

    If sea level is higher/lower than the max/min elevation, return
    the first/last *x* value.

    >>> find_shoreline(x, z, sea_level=100., kind='linear')
    0.0
    >>> find_shoreline(x, z, sea_level=-100., kind='linear')
    9.0
    """
    from scipy.optimize import bisect

    x, z = np.asarray(x), np.asarray(z)

    z = np.atleast_2d(z)
    n_rows = z.shape[0]

    x_of_shorelines = np.empty(n_rows, dtype=float)
    for row in range(n_rows):
        try:
            index_at_shore = find_shoreline_index(x, z[row], sea_level=sea_level)
        except ShorelineError:
            if z[row, 0] < sea_level:
                x_of_shoreline = x[0]
            else:
                x_of_shoreline = x[-1]
        else:
            func = interpolate.interp1d(x, z[row] - sea_level, kind=kind)
            x_of_shoreline = bisect(func, x[index_at_shore - 1], x[index_at_shore])
        x_of_shorelines[row] = x_of_shoreline

    if n_rows == 1:
        return x_of_shorelines.item()
    else:
        return x_of_shorelines


def _find_shoreline_polyfit(
    x: NDArray[np.floating], z: NDArray[np.floating], sea_level: float = 0.0
) -> float:
    try:
        index_at_shore = find_shoreline_index(x, z, sea_level=sea_level)
    except ValueError:
        if z[0] < sea_level:
            index_at_shore = 0
        else:
            index_at_shore = len(x) - 1

    p_land = np.polyfit(
        x[index_at_shore - 3 : index_at_shore],
        z[index_at_shore - 3 : index_at_shore],
        2,
    )
    p_sea = np.polyfit(
        x[index_at_shore : index_at_shore + 3],
        z[index_at_shore : index_at_shore + 3],
        2,
    )

    root_land = np.roots(p_land)
    root_sea = np.roots(p_sea)

    i = np.argmin(np.abs(root_sea - x[index_at_shore]))
    x_sea = root_sea[i]
    x_sea = np.clip(x_sea, x[index_at_shore - 1], x[index_at_shore])

    i = np.argmin(np.abs(root_land - x[index_at_shore]))
    x_land = root_land[i]
    x_land = np.clip(x_land, x[index_at_shore - 1], x[index_at_shore])

    if np.isreal(x_land) and np.isreal(x_sea):
        x_of_shoreline = (x_sea + x_land) / 2
    elif np.isreal(x_land) and not np.isreal(x_sea):
        x_of_shoreline = np.real(x_land)
    elif not np.isreal(x_land) and np.isreal(x_sea):
        x_of_shoreline = np.real(x_sea)
    else:
        x_of_shoreline = (np.real(x_land) + np.real(x_sea)) / 2

    return x_of_shoreline


def find_shoreline_index(
    x: NDArray[np.floating], z: NDArray[np.floating], sea_level: float = 0.0
) -> NDArray[np.integer] | int:
    """Find the landward-index of the shoreline.

    Parameters
    ----------
    x : array of float
        X-positions of profile.
    z : array of float
        Elevations along the profile.
    sea_level : float, optional
        Elevation of sea level.

    Returns
    -------
    int
        Index into *z* landward of the shoreline.

    Raises
    ------
    ValueError
        If the profile does not contain a shoreline.

    Examples
    --------
    >>> from sequence.shoreline import find_shoreline_index
    >>> import numpy as np

    Create a linearly-dipping profile.

    >>> x = np.arange(10.)
    >>> z = - x + 5.
    >>> z
    array([ 5.,  4.,  3.,  2.,  1.,  0., -1., -2., -3., -4.])

    Find the shoreline.

    >>> find_shoreline_index(x, z)
    6
    >>> find_shoreline_index(x, z, sea_level=.25)
    5

    If sea level is higher/lower than the max/min elevation, raise
    a `ShorelineError`.

    >>> find_shoreline_index(x, z, sea_level=100.)
    Traceback (most recent call last):
    sequence.errors.ShorelineError: No shoreline found. The profile is all below sea level
    >>> find_shoreline_index(x, z, sea_level=-100.)
    Traceback (most recent call last):
    sequence.errors.ShorelineError: No shoreline found. The profile is all above sea level
    """
    z = np.atleast_2d(z)
    n_rows = z.shape[0]

    index_of_shoreline = np.full(n_rows, -1)
    for row in range(n_rows):
        (below_water,) = np.where(z[row] < sea_level)

        if len(below_water) == 0 or len(below_water) == len(x):
            raise ShorelineError(
                "No shoreline found. The profile is all {} sea level".format(
                    "above" if len(below_water) == 0 else "below"
                )
            )
            # return None
        else:
            index_of_shoreline[row] = below_water[0]
            # return below_water[0]

    if n_rows == 1:
        return index_of_shoreline.item()
    else:
        return index_of_shoreline
