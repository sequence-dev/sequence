"""Test the shoreline.find_shoreline function."""

from __future__ import annotations

import numpy as np
import pytest
from pytest import approx

from sequence.shoreline import find_shoreline


def test_find_shoreline_with_default_keywords():
    """Test find_shoreline with the keyword defaults"""
    x = np.arange(10.0)
    expected = find_shoreline(x, 5.0 - x, sea_level=0.0, kind="cubic")
    actual = find_shoreline(x, 5.0 - x)

    assert actual == expected


def test_find_shoreline_with_list_args():
    """Test find_shoreline with list arguments"""
    x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    z = [5, 4, 3, 2, 1, 0, -1, -2, -3, -4]
    find_shoreline(x, z)


def test_find_shoreline_fails_with_unknown_kind():
    """Test find_shoreline fails with unknown interpolation"""
    with pytest.raises(NotImplementedError):
        find_shoreline([0, 1, 2, 3, 4, 5, 6], [5, 4, 3, 2, 1, 0, -1], kind="foobarbaz")


def test_find_shoreline_return_value():
    """Test find_shoreline return value"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [5, 4, 3, 2, 1, 0, -1, -2, -3, -4]
    )
    assert x_of_shore == approx(5.0)


def test_find_shoreline_return_value_with_sea_level():
    """Test find_shoreline return value with sea level"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [5, 4, 3, 2, 1, 0, -1, -2, -3, -4],
        sea_level=0.25,
    )
    assert x_of_shore == approx(4.75)


def test_find_shoreline_return_value_with_hi_sea_level():
    """Test find_shoreline return value with high sea level"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [5, 4, 3, 2, 1, 0, -1, -2, -3, -4],
        sea_level=100,
    )
    assert x_of_shore == approx(0.0)


def test_find_shoreline_return_value_with_lo_sea_level():
    """Test find_shoreline return value with low sea level"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [5, 4, 3, 2, 1, 0, -1, -2, -3, -4],
        sea_level=-100,
    )
    assert x_of_shore == approx(9.0)


def test_find_shoreline_with_kind_linear():
    """Test find_shoreline with linear interpolation"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [5, 4, 3, 2, 1, 0, -1, -2, -3, -4],
        kind="linear",
    )
    assert x_of_shore == approx(5.0)


def test_find_shoreline_with_kind_nearest():
    """Test find_shoreline with nearest interpolation"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [5, 4, 3, 2, 1, 0, -1, -2, -3, -4],
        kind="linear",
    )
    assert x_of_shore == approx(5.0)


def test_find_shoreline_with_kind_zero():
    """Test find_shoreline with zero interpolation"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [5, 4, 3, 2, 1, 0, -1, -2, -3, -4],
        kind="zero",
    )
    assert x_of_shore == approx(5.0)


def test_find_shoreline_with_kind_slinear():
    """Test find_shoreline with slinear interpolation"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [5, 4, 3, 2, 1, 0, -1, -2, -3, -4],
        kind="slinear",
    )
    assert x_of_shore == approx(5.0)


def test_find_shoreline_with_kind_quadratic():
    """Test find_shoreline with quadratic interpolation"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [5, 4, 3, 2, 1, 0, -1, -2, -3, -4],
        kind="quadratic",
    )
    assert x_of_shore == approx(5.0)


def test_find_shoreline_with_kind_cubic():
    """Test find_shoreline with cubic interpolation"""
    x_of_shore = find_shoreline(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [5, 4, 3, 2, 1, 0, -1, -2, -3, -4],
        kind="cubic",
    )
    assert x_of_shore == approx(5.0)
