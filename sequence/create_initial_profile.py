"""
Created on Tue Sep 13 11:18:10 2016

@author: michael
"""

import numpy as np


def create_initial_profile(
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
