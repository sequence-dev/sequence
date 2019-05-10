#! /usr/bin/env python
import numpy as np

from landlab import Component


class ShorelineFinder(Component):

    _name = "Shoreline finder"

    _input_var_names = ("topographic__elevation", "sea_level__elevation")

    _output_var_names = (
        "x_of_shore",
    )

    _var_units = {
        "topographic__elevation": "m",
        "sea_level__elevation": "m",
        "x_of_shore": "m",
        "x_of_shelf_edge": "m",
    }

    _var_mapping = {
        "topographic__elevation": "node",
        "sea_level__elevation": "grid",
        "x_of_shore": "grid",
        "x_of_shelf_edge": "grid",
    }

    _var_doc = {
        "topographic__elevation": "Elevation of the land and sea floor",
        "sea_level__elevation": "Elevation of sea level",
        "x_of_shore": "Position of the shore line",
        "x_of_shelf_edge": "Position of the shelf edge",
    }

    def __init__(self, grid):
        super(ShorelineFinder, self).__init__(grid)

        self.grid.at_grid["x_of_shore"] = 0.0
        self.grid.at_grid["x_of_shelf_edge"] = 0.0

        x = self.grid.x_of_node[self.grid.node_at_cell]
        z = self.grid.at_node["topographic__elevation"][self.grid.node_at_cell]
        sea_level = self.grid.at_grid["sea_level__elevation"]

        x_of_shore = find_shoreline(x, z, sea_level=sea_level)
        x_of_shelf_edge = find_shelf_edge(self, x, z, x_of_shore, sea_level=sea_level)

    def update(self):
        x = self.grid.x_of_node[self.grid.node_at_cell]
        z = self.grid.at_node["topographic__elevation"][self.grid.node_at_cell]
        sea_level = self.grid.at_grid["sea_level__elevation"]

        x_of_shore = find_shoreline(x, z, sea_level=sea_level)
        x_of_shelf_edge = find_shelf_edge(self, x, z, x_of_shore, sea_level=sea_level)

        if x_of_shelf_edge <= x_of_shore:
            raise RuntimeError((x_of_shelf_edge, x_of_shore))

        self.grid.at_grid["x_of_shore"] = x_of_shore
        self.grid.at_grid["x_of_shelf_edge"] = x_of_shelf_edge

        #self.grid.at_cell["curvature"] = np.gradient(np.gradient(z, x), x)

    def run_one_step(self, dt=None):
        self.update()


def find_shelf_edge(self, x, z, x_of_shore, sea_level=0.0):
    """Find the x-coordinate of the shelf edge.

    The shelf edge is the location where the curvature of *sea-floor elevations*
    is a *minimum*.
    Revised: now maximum of deposit_thickness*wd

    Parameters
    ----------
    x : ndarray of float
        x-positions of the profile.
    z : ndarray of float
        Elevations of the profile.
    sea_level : float, optional
        Elevation of sea level.

    Examples
    --------
    >>> import numpy as np
    >>> from sequence.shoreline import find_shelf_edge

    >>> x = np.arange(50.)
    >>> z = - np.arctan(x / 5.0 - 5.0)
    >>> find_shelf_edge(x, z, sea_level=z.max())
    22.0
    """
    
  
    #curvature = np.gradient(np.gradient(z, x), x)
    dz = self.grid.at_node["sediment_deposit__thickness"][self.grid.node_at_cell].copy()
    sf = x_of_shore + 6000  #3 / self._alpha
    offshore = x > sf
    onshore = x <= sf
    dz[onshore] = 0.
    dz *= -z
    

    index_at_shelf_edge = np.argmax(dz[offshore])
    if x[index_at_shelf_edge] < x_of_shore:
        x[index_at_shelf_edge] = x_of_shore + 6000
    
    return x[index_at_shelf_edge]


def find_shoreline(x, z, sea_level=0.0, kind="cubic"):
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
    from scipy.interpolate import interp1d
    from scipy.optimize import bisect

    x = np.asarray(x)
    z = np.asarray(z)

    try:
        index_at_shore = find_shoreline_index(x, z, sea_level=sea_level)
    except ValueError:
        if z[0] < sea_level:
            x_of_shoreline = x[0]
        else:
            x_of_shoreline = x[-1]
    else:
        func = interp1d(x, z - sea_level, kind=kind)
        x_of_shoreline = bisect(func, x[index_at_shore - 1], x[index_at_shore])

    return x_of_shoreline


def find_shoreline_polyfit(x, z, sea_level=0.0):
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


def find_shoreline_index(x, z, sea_level=0.0):
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
    a `ValueError`.

    >>> find_shoreline_index(x, z, sea_level=100.)
    ...     # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ValueError: profile does not contain shoreline
    >>> find_shoreline_index(x, z, sea_level=-100.)
    Traceback (most recent call last):
    ...
    ValueError: profile does not contain shoreline
    """
    (below_water,) = np.where(z < sea_level)

    if len(below_water) == 0 or len(below_water) == len(x):
        raise ValueError("profile does not contain shoreline")
    else:
        return below_water[0]
