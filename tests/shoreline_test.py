"""Test the shoreline.find_shoreline function."""
import numpy as np
import pytest
from pytest import approx

from sequence.shoreline import find_shoreline

# Test data: a linear shoreline profile.
x = np.arange(10.0)
z = 5.0 - x
sea_level = 0.25
expected_value = 5.0
expected_value_with_sea_level = 4.75
hi_value = 100.0
lo_value = -100.0


def test_find_shoreline_fails_with_no_args():
    """Test find_shoreline fails with no arguments"""
    with pytest.raises(TypeError):
        find_shoreline()


def test_find_shoreline_fails_with_one_arg():
    """Test find_shoreline fails with one argument"""
    with pytest.raises(TypeError):
        find_shoreline(x)


def test_find_shoreline_with_default_keywords():
    """Test find_shoreline with the keyword defaults"""
    find_shoreline(x, z)


def test_find_shoreline_with_list_args():
    """Test find_shoreline with list arguments"""
    x_list = x.tolist()
    z_list = z.tolist()
    find_shoreline(x_list, z_list)


def test_find_shoreline_fails_with_different_len_args():
    """Test find_shoreline fails with arguments of different length"""
    new_x = np.arange(float(len(x) + 1))
    with pytest.raises(ValueError):
        find_shoreline(new_x, z)


def test_find_shoreline_fails_with_unknown_kind():
    """Test find_shoreline fails with unknown interpolation"""
    with pytest.raises(NotImplementedError):
        find_shoreline(x, z, kind="foobarbaz")


def test_find_shoreline_return_value():
    """Test find_shoreline return value"""
    r = find_shoreline(x, z)
    assert r == approx(expected_value)


def test_find_shoreline_return_value_with_sea_level():
    """Test find_shoreline return value with sea level"""
    r = find_shoreline(x, z, sea_level=sea_level)
    assert r == approx(expected_value_with_sea_level)


def test_find_shoreline_return_value_with_hi_sea_level():
    """Test find_shoreline return value with high sea level"""
    r = find_shoreline(x, z, sea_level=hi_value)
    assert r == approx(x[0])


def test_find_shoreline_return_value_with_lo_sea_level():
    """Test find_shoreline return value with low sea level"""
    r = find_shoreline(x, z, sea_level=lo_value)
    assert r == approx(x[-1])


def test_find_shoreline_with_kind_linear():
    """Test find_shoreline with linear interpolation"""
    r = find_shoreline(x, z, kind="linear")
    assert r == approx(expected_value)


def test_find_shoreline_with_kind_nearest():
    """Test find_shoreline with nearest interpolation"""
    r = find_shoreline(x, z, kind="nearest")
    assert r == approx(expected_value)


def test_find_shoreline_with_kind_zero():
    """Test find_shoreline with zero interpolation"""
    r = find_shoreline(x, z, kind="zero")
    assert r == approx(expected_value)


def test_find_shoreline_with_kind_slinear():
    """Test find_shoreline with slinear interpolation"""
    r = find_shoreline(x, z, kind="slinear")
    assert r == approx(expected_value)


def test_find_shoreline_with_kind_quadratic():
    """Test find_shoreline with quadratic interpolation"""
    r = find_shoreline(x, z, kind="quadratic")
    assert r == approx(expected_value)


def test_find_shoreline_with_kind_cubic():
    """Test find_shoreline with cubic interpolation"""
    r = find_shoreline(x, z, kind="cubic")
    assert r == approx(expected_value)
