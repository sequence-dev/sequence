#! /usr/bin/env python
import numpy as np


def interp_shoreline_point(x, z, sea_level=0., kind="cubic"):
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


def find_shoreline(x, z, sea_level=0.):
    try:
        index_at_shore = find_shoreline_index(x, z, sea_level=sea_level)
    except ValueError:
        if z[0] < sea_level:
            index_at_shore = 0
        else:
            index_at_shore = len(x)-1
   

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
        
    i = np.argmin(np.abs(root_sea-x[index_at_shore]))
    x_sea = root_sea[i]
    x_sea = np.clip(x_sea,x[index_at_shore-1],x[index_at_shore]) 
        
    i = np.argmin(np.abs(root_land-x[index_at_shore]))
    x_land = root_land[i]
    x_land = np.clip(x_land,x[index_at_shore-1],x[index_at_shore])
    
    if np.isreal(x_land) and np.isreal(x_sea):
        x_of_shoreline = (x_sea+x_land)/2
    elif np.isreal(x_land) and not np.isreal(x_sea):
        x_of_shoreline = np.real(x_land)
    elif not np.isreal(x_land) and np.isreal(x_sea):
        x_of_shoreline = np.real(x_sea)
    else:
        x_of_shoreline = (np.real(x_land) + np.real(x_sea))/2
            
    # print (index_at_shore,z[index_at_shore - 3:index_at_shore+3] - sea_level, x[index_at_shore], x_land,  x_sea, x_of_shoreline)
    
    #x_of_shoreline = x_of_shoreline + 250.
        
    return x_of_shoreline


def insert_shoreline_point(x, z, sea_level=0.):
    from bisect import bisect

    (x_shore, z_shore) = interp_shoreline_point(x, z, sea_level=sea_level)
    index = bisect(x, x_shore)

    return np.insert(x, index, x_shore), np.insert(z, index, z_shore)


def find_shoreline_index(x, z, sea_level=0.):
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
