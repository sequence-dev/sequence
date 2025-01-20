"""Test the shoreline.find_shoreline function."""

from __future__ import annotations

import numpy as np
import pytest
from pytest import approx

from sequence.shoreline import find_shoreline


@pytest.fixture
def x():
    return np.arange(10.0)


def test_find_shoreline_fails_with_no_args():
    """Test find_shoreline fails with no arguments"""
    with pytest.raises(TypeError):
        find_shoreline()


def test_find_shoreline_fails_with_one_arg(x):
    """Test find_shoreline fails with one argument"""
    with pytest.raises(TypeError):
        find_shoreline(x)


def test_find_shoreline_with_default_keywords(x):
    """Test find_shoreline with the keyword defaults"""
    find_shoreline(x, 5.0 - x)


def test_find_shoreline_with_list_args(x):
    """Test find_shoreline with list arguments"""
    x_list = x.tolist()
    z_list = (5.0 - x).tolist()
    find_shoreline(x_list, z_list)


def test_find_shoreline_fails_with_different_len_args(x):
    """Test find_shoreline fails with arguments of different length"""
    new_x = np.arange(float(len(x) + 1))
    with pytest.raises(ValueError):
        find_shoreline(new_x, 5.0 - x)


def test_find_shoreline_fails_with_unknown_kind(x):
    """Test find_shoreline fails with unknown interpolation"""
    with pytest.raises(NotImplementedError):
        find_shoreline(x, 5.0 - x, kind="foobarbaz")


def test_find_shoreline_return_value(x):
    """Test find_shoreline return value"""
    r = find_shoreline(x, 5.0 - x)
    assert r == approx(5.0)


def test_find_shoreline_return_value_with_sea_level(x):
    """Test find_shoreline return value with sea level"""
    r = find_shoreline(x, 5.0 - x, sea_level=0.25)
    assert r == approx(4.75)


def test_find_shoreline_return_value_with_hi_sea_level(x):
    """Test find_shoreline return value with high sea level"""
    r = find_shoreline(x, 5.0 - x, sea_level=100.0)
    assert r == approx(x[0])


def test_find_shoreline_return_value_with_lo_sea_level(x):
    """Test find_shoreline return value with low sea level"""
    r = find_shoreline(x, 5.0 - x, sea_level=-100.0)
    assert r == approx(x[-1])


def test_find_shoreline_with_kind_linear(x):
    """Test find_shoreline with linear interpolation"""
    r = find_shoreline(x, 5.0 - x, kind="linear")
    assert r == approx(5.0)


def test_find_shoreline_with_kind_nearest(x):
    """Test find_shoreline with nearest interpolation"""
    r = find_shoreline(x, 5.0 - x, kind="nearest")
    assert r == approx(5.0)


def test_find_shoreline_with_kind_zero(x):
    """Test find_shoreline with zero interpolation"""
    r = find_shoreline(x, 5.0 - x, kind="zero")
    assert r == approx(5.0)


def test_find_shoreline_with_kind_slinear(x):
    """Test find_shoreline with slinear interpolation"""
    r = find_shoreline(x, 5.0 - x, kind="slinear")
    assert r == approx(5.0)


def test_find_shoreline_with_kind_quadratic(x):
    """Test find_shoreline with quadratic interpolation"""
    r = find_shoreline(x, 5.0 - x, kind="quadratic")
    assert r == approx(5.0)


def test_find_shoreline_with_kind_cubic(x):
    """Test find_shoreline with cubic interpolation"""
    r = find_shoreline(x, 5.0 - x, kind="cubic")
    assert r == approx(5.0)
