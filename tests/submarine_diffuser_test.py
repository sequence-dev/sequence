from __future__ import annotations

from random import random

import pytest
from landlab import RasterModelGrid

from sequence.submarine import SubmarineDiffuser


@pytest.mark.parametrize(
    "param",
    (
        "plain_slope",
        "wave_base",
        "shoreface_height",
        "alpha",
        "shelf_slope",
        "sediment_load",
    ),
)
def test_setters(param):
    grid = RasterModelGrid((3, 5))
    grid.add_zeros("topographic__elevation", at="node")
    grid.at_grid["sea_level__elevation"] = 0.0

    expected = random()
    diffuser = SubmarineDiffuser(grid, **{param: expected})

    assert getattr(diffuser, param) == pytest.approx(expected)

    expected = random()
    setattr(diffuser, param, expected)
    assert getattr(diffuser, param) == pytest.approx(expected)
