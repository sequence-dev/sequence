from __future__ import annotations

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal

from sequence.plot import _interp_between_layers
from sequence.plot import _outline_layer


def test_layer_interpolation_bottom_to_top():
    bottom, top = np.zeros(5), np.ones(5)
    yi = _interp_between_layers(np.arange(5), bottom, top)

    assert_array_almost_equal(yi, [0.0, 0.25, 0.5, 0.75, 1.0])


def test_layer_interpolation_top_to_bottom():
    bottom, top = np.zeros(5), np.ones(5)

    yi = _interp_between_layers([0.0, 1.0, 2.0, 3.0, 4.0], top, bottom)
    assert_array_almost_equal(yi, [1.0, 0.75, 0.5, 0.25, 0.0])


@pytest.mark.parametrize(
    "top_limits,bottom_limits,expected",
    (
        [(0, 2), (3, 6), [2, 1, 0, 1, 2, 3, 4, 5, 6, 5, 4, 3]],
        [(2, 4), (3, 6), [4, 3, 2, 3, 4, 5, 6, 5]],
        [(4, 5), (3, 6), [5, 4, 3, 4, 5, 6]],
        [(5, 7), (3, 6), [7, 6, 5, 4, 3, 4, 5, 6]],
        [(8, 9), (3, 6), [9, 8, 7, 6, 5, 4, 3, 4, 5, 6, 7, 8]],
        [(3, 6), (0, 2), [6, 5, 4, 3, 2, 1, 0, 1, 2, 3, 4, 5]],
        [(3, 6), (2, 4), [6, 5, 4, 3, 2, 3, 4, 5]],
        [(3, 6), (4, 5), [6, 5, 4, 3, 4, 5]],
        [(3, 6), (5, 7), [6, 5, 4, 3, 4, 5, 6, 7]],
        [(3, 6), (8, 9), [6, 5, 4, 3, 4, 5, 6, 7, 8, 9, 8, 7]],
    ),
)
def test_outline_layer_x(top_limits, bottom_limits, expected):
    x, bottom, top = np.arange(10.0), np.zeros(10), np.ones(10)
    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=bottom_limits, top_limits=top_limits
    )
    assert_array_almost_equal(x_of_patch, expected)


@pytest.mark.parametrize(
    "top_limits,bottom_limits,expected",
    (
        [
            (1, 3),
            (5, 8),
            [1, 1, 1, 0.75, 0.5, 0.25, 0, 0, 0, 0, 0.2, 0.4, 0.6, 0.8],
        ],
        [(1, 4), (3, 8), [1, 1, 1, 1, 0.5, 0, 0, 0, 0, 0, 0, 0.25, 0.5, 0.75]],
        [(3, 6), (1, 8), [1, 1, 1, 1, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0.5]],
        [(3, 9), (1, 5), [1, 1, 1, 1, 1, 1, 1, 0.5, 0, 0, 0, 0, 0, 0.25, 0.5, 0.75]],
        [(7, 9), (3, 5), [1, 1, 1, 0.75, 0.5, 0.25, 0, 0, 0, 0.25, 0.5, 0.75]],
    ),
)
def test_outline_layer_y(top_limits, bottom_limits, expected):
    x, bottom, top = np.arange(10.0), np.zeros(10), np.ones(10)
    _, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=bottom_limits, top_limits=top_limits
    )
    assert_array_almost_equal(y_of_patch, expected)


def test_outline_layer_without_sides():
    x, bottom, top = np.arange(10.0), np.zeros(10), np.ones(10)
    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=(1, 5), top_limits=(1, 5)
    )
    assert_array_almost_equal(x_of_patch, [5, 4, 3, 2, 1, 2, 3, 4])
    assert_array_almost_equal(y_of_patch, [1, 1, 1, 1, 0, 0, 0, 0])


def test_outline_layer_without_bottom():
    x, bottom, top = np.arange(10.0), np.zeros(10), np.ones(10)
    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=(5, 5), top_limits=(4, 6)
    )
    assert_array_almost_equal(x_of_patch, [6, 5, 4, 5])
    assert_array_almost_equal(y_of_patch, [1, 1, 1, 0])

    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=(5, 5), top_limits=(0, 3)
    )
    assert_array_almost_equal(x_of_patch, [3, 2, 1, 0, 1, 2, 3, 4, 5, 4])
    assert_array_almost_equal(y_of_patch, [1, 1, 1, 1, 0.8, 0.6, 0.4, 0.2, 0, 0.5])

    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=(5, 5), top_limits=(6, 9)
    )
    assert_array_almost_equal(x_of_patch, [9, 8, 7, 6, 5, 6, 7, 8])
    assert_array_almost_equal(y_of_patch, [1, 1, 1, 1, 0, 0.25, 0.5, 0.75])


def test_outline_layer_without_top():
    x, bottom, top = np.arange(10.0), np.zeros(10), np.ones(10)
    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=(4, 6), top_limits=(5, 5)
    )
    assert_array_almost_equal(x_of_patch, [5, 4, 5, 6])
    assert_array_almost_equal(y_of_patch, [1, 0, 0, 0])

    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=(0, 3), top_limits=(5, 5)
    )
    assert_array_almost_equal(x_of_patch, [5, 4, 3, 2, 1, 0, 1, 2, 3, 4])
    assert_array_almost_equal(y_of_patch, [1, 0.8, 0.6, 0.4, 0.2, 0, 0, 0, 0, 0.5])

    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=(6, 9), top_limits=(5, 5)
    )
    assert_array_almost_equal(x_of_patch, [5, 6, 7, 8, 9, 8, 7, 6])
    assert_array_almost_equal(y_of_patch, [1, 0, 0, 0, 0, 0.25, 0.5, 0.75])


def test_outline_layer_tiny():
    x, bottom, top = np.arange(10.0), np.zeros(10), np.ones(10)
    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=(4, 5), top_limits=(4, 5)
    )
    assert_array_almost_equal(x_of_patch, [5, 4])
    assert_array_almost_equal(y_of_patch, [1, 0])


@pytest.mark.parametrize("bottom_limits", [(0, None), (None, 9), (None, None), None])
@pytest.mark.parametrize("top_limits", [(0, None), (None, 9), (None, None), None])
def test_outline_layer_no_limits(bottom_limits, top_limits):
    x, bottom, top = np.arange(10.0), np.zeros(10), np.ones(10)
    x_expected, y_expected = _outline_layer(
        x, bottom, top, bottom_limits=(0, 9), top_limits=(0, 9)
    )
    x_of_patch, y_of_patch = _outline_layer(
        x, bottom, top, bottom_limits=bottom_limits, top_limits=top_limits
    )

    assert_array_almost_equal(x_of_patch, x_expected)
    assert_array_almost_equal(y_of_patch, y_expected)
