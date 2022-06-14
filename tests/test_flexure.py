import pytest
from landlab import RasterModelGrid

from sequence.sediment_flexure import SedimentFlexure


@pytest.fixture()
def grid():
    grid = RasterModelGrid((3, 4))
    grid.add_empty("sediment_deposit__thickness", at="node")
    grid.add_empty("topographic__elevation", at="node")
    grid.add_empty("bedrock_surface__elevation", at="node")
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
    grid = RasterModelGrid((3, 4))
    grid.add_empty("sediment_deposit__thickness", at="node")
    grid.add_zeros("topographic__elevation", at="node")
    grid.add_zeros("bedrock_surface__elevation", at="node")

    grid.at_node["sediment_deposit__thickness"][:] = 1.0
    flexure = SedimentFlexure(grid)
    flexure.run_one_step()

    assert (
        grid.at_node["topographic__elevation"].reshape(grid.shape)[1, 1:-1] < 0.0
    ).all()
    assert (
        grid.at_node["bedrock_surface__elevation"].reshape(grid.shape)[1, 1:-1] < 0.0
    ).all()
