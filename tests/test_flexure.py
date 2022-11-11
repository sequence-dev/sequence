import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal

from sequence import SequenceModelGrid
from sequence.sediment_flexure import SedimentFlexure


@pytest.fixture()
def grid():
    grid = SequenceModelGrid(4, spacing=1.0)
    grid.add_empty("topographic__elevation", at="node")
    return grid


def test_properties(grid):
    flexure = SedimentFlexure(grid)
    assert flexure.sand_density == pytest.approx(2650.0)
    assert flexure.mud_density == pytest.approx(2720.0)
    assert flexure.water_density == pytest.approx(1030.0)

    flexure = SedimentFlexure(
        grid, sand_density=1234, mud_density=2468, water_density=1000
    )
    assert flexure.sand_density == pytest.approx(1234.0)
    assert flexure.mud_density == pytest.approx(2468.0)
    assert flexure.water_density == pytest.approx(1000.0)


@pytest.mark.parametrize("prop", ["sand_density", "mud_density", "water_density"])
def test_setters(grid, prop):
    flexure = SedimentFlexure(grid)
    setattr(flexure, prop, 1000.0)
    assert getattr(flexure, prop) == pytest.approx(1000.0)


@pytest.mark.parametrize("prop", ["sand_density", "mud_density", "water_density"])
def test_bad_densities(grid, prop):
    flexure = SedimentFlexure(grid)
    with pytest.raises(ValueError):
        setattr(flexure, prop, 0.0)
    with pytest.raises(ValueError):
        setattr(flexure, prop, -2.0)


@pytest.mark.parametrize("prop", ["sand_density", "mud_density"])
def test_update_bulk_density(grid, prop):
    flexure = SedimentFlexure(grid)

    initial_value = getattr(flexure, prop)
    setattr(flexure, prop, initial_value / 2.0)
    assert getattr(flexure, prop) < initial_value

    initial_value = getattr(flexure, prop)
    setattr(flexure, prop, initial_value * 2.0)
    assert getattr(flexure, prop) > initial_value

    initial_value = getattr(flexure, prop)
    setattr(flexure, prop, initial_value)
    assert getattr(flexure, prop) == pytest.approx(initial_value)


def test_flexure():
    grid = SequenceModelGrid(100)
    initial_elevation = grid.add_zeros("topographic__elevation", at="node").copy()

    grid.at_node["sediment_deposit__thickness"][:] = 1.0
    flexure = SedimentFlexure(grid)
    flexure.run_one_step()

    assert (
        grid.at_node["lithosphere_surface__increment_of_elevation"].reshape(grid.shape)[
            1, :
        ]
        > 0.0
    ).all()
    assert (grid.at_node["topographic__elevation"] == initial_elevation).all()


def test_all_dry():
    z = np.asarray([4.0, 3.0, 2.0, 1.0, 0.0])
    sediment_density = 1.0
    water_density = 0.5
    dz = np.full_like(z, 2.0)

    loading = SedimentFlexure._calc_loading(dz, z, sediment_density, water_density)

    assert_array_almost_equal(loading, dz * sediment_density)


def test_all_wet():
    z = np.asarray([-2.0, -3.0, -4.0, -5.0, -6.0])
    sediment_density = 1.0
    water_density = 0.5
    dz = np.full_like(z, 2.0)

    loading = SedimentFlexure._calc_loading(dz, z, sediment_density, water_density)

    assert_array_almost_equal(loading, dz * water_density)


def test_loading_wet_or_dry():
    z = np.asarray([2.0, 1.0, 0.0, -1.0, -2.0])
    sediment_density = 2000.0
    water_density = 1000.0
    dz = np.full_like(z, 0.5)

    loading = SedimentFlexure._calc_loading(dz, z, sediment_density, water_density)

    assert_array_almost_equal(
        loading, [0.5 * 2000.0, 0.5 * 2000, 0.5 * 2000, 0.5 * 1000, 0.5 * 1000]
    )


def test_loading_mixed():
    z = np.asarray([1.0, 0.0, -1.0, -2.0, -3.0])
    sediment_density = 1.0
    water_density = 0.5
    dz = np.full_like(z, 2.0)

    loading = SedimentFlexure._calc_loading(dz, z, sediment_density, water_density)

    assert_array_almost_equal(loading, [2.0, 2.0, 1.0 + 0.5, 1.0, 1.0])


def test_dry_erosion():
    z = np.asarray([4.0, 3.0, 2.0, 1.0, 0.0])
    sediment_density = 1.0
    water_density = 0.5
    dz = np.asarray([-1.0, -1.0, 1.0, 1.0, 1.0])

    loading = SedimentFlexure._calc_loading(dz, z, sediment_density, water_density)

    assert_array_almost_equal(loading, dz * sediment_density)


def test_wet_erosion():
    z = np.asarray([0.0, -1.0, -2.0, -3.0, -4.0])
    sediment_density = 1.0
    water_density = 0.5
    dz = np.asarray([-1.0, -1.0, 1.0, 1.0, 1.0])

    loading = SedimentFlexure._calc_loading(dz, z, sediment_density, water_density)

    assert_array_almost_equal(loading, dz * (sediment_density - water_density))


def test_mixed_erosion():
    z = np.asarray([3.0, 2.0, 1.0, 0.0, -1.0])
    sediment_density = 1.0
    water_density = 0.5
    dz = np.asarray([-2.0, -2.0, -2.0, 2.0, 2.0])

    loading = SedimentFlexure._calc_loading(dz, z, sediment_density, water_density)

    assert_array_almost_equal(loading, [-2.0, -2.0, -1.0 - 0.5, 2.0, 1.0 + 0.5])
