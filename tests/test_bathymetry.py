import os

import numpy as np
import pytest
from pytest import approx, raises

from landlab import RasterModelGrid
from sequence.bathymetry import BathymetryReader


@pytest.fixture(scope="session")
def bathy_file(tmpdir_factory):
    lines = ["# x (m), z (m)", "0., 10.", "2., 0.", "4., -5."]
    file_ = tmpdir_factory.mktemp("data").join("bathy.csv")
    file_.write(os.linesep.join(lines))
    return str(file_)


def test_reading_from_file(bathy_file):
    expected = np.array(
        [
            [10.0, 9.0, 8.0, 7.0, 6.0],
            [10.0, 9.0, 8.0, 7.0, 6.0],
            [10.0, 9.0, 8.0, 7.0, 6.0],
        ]
    )

    grid = RasterModelGrid((3, 5), xy_spacing=0.2)
    bathy = BathymetryReader(grid, filepath=bathy_file)
    bathy.run_one_step()

    actual = bathy.grid.at_node["topographic__elevation"].reshape(grid.shape)
    assert actual == approx(expected)


def test_output_is_topography(bathy_file):
    grid = RasterModelGrid((3, 5), xy_spacing=0.2)

    assert "topographic__elevation" not in grid.at_node
    BathymetryReader(grid, filepath=bathy_file).run_one_step()
    assert "topographic__elevation" in grid.at_node


def test_field_already_exists(bathy_file):
    expected = np.array(
        [
            [10.0, 9.0, 8.0, 7.0, 6.0],
            [10.0, 9.0, 8.0, 7.0, 6.0],
            [10.0, 9.0, 8.0, 7.0, 6.0],
        ]
    )

    grid = RasterModelGrid((3, 5), xy_spacing=0.2)
    grid.add_zeros("topographic__elevation", at="node")
    bathy = BathymetryReader(grid, filepath=bathy_file)
    bathy.run_one_step()

    actual = bathy.grid.at_node["topographic__elevation"].reshape(grid.shape)
    assert actual == approx(expected)


def test_no_extrapolate(bathy_file):
    grid = RasterModelGrid((3, 5), xy_spacing=2.0)
    bathy = BathymetryReader(grid, filepath=bathy_file)
    with raises(ValueError):
        bathy.run_one_step()

    grid = RasterModelGrid((3, 5), xy_spacing=-1.0)
    bathy = BathymetryReader(grid, filepath=bathy_file)
    with raises(ValueError):
        bathy.run_one_step()


def test_kind_is_nearest(bathy_file):
    expected = np.full((3, 5), 10.0)

    grid = RasterModelGrid((3, 5), xy_spacing=0.2)
    bathy = BathymetryReader(grid, filepath=bathy_file, kind="nearest")
    bathy.run_one_step()

    actual = bathy.grid.at_node["topographic__elevation"].reshape(grid.shape)
    assert actual == approx(expected)


def test_kind_is_previous(bathy_file):
    expected = np.array(
        [
            [10.0, 10.0, 10.0, 10.0, 0.0],
            [10.0, 10.0, 10.0, 10.0, 0.0],
            [10.0, 10.0, 10.0, 10.0, 0.0],
        ]
    )

    grid = RasterModelGrid((3, 5), xy_spacing=0.5)
    bathy = BathymetryReader(grid, filepath=bathy_file, kind="previous")
    bathy.run_one_step()

    actual = bathy.grid.at_node["topographic__elevation"].reshape(grid.shape)
    assert actual == approx(expected)


def test_kind_is_next(bathy_file):
    expected = np.array(
        [
            [10.0, 0.0, 0.0, 0.0, 0.0],
            [10.0, 0.0, 0.0, 0.0, 0.0],
            [10.0, 0.0, 0.0, 0.0, 0.0],
        ]
    )

    grid = RasterModelGrid((3, 5), xy_spacing=0.5)
    bathy = BathymetryReader(grid, filepath=bathy_file, kind="next")
    bathy.run_one_step()

    actual = bathy.grid.at_node["topographic__elevation"].reshape(grid.shape)
    assert actual == approx(expected)
