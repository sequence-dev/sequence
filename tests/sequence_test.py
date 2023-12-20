from __future__ import annotations

import numpy as np
import pytest

from sequence.grid import SequenceModelGrid
from sequence.processes import ShorelineFinder
from sequence.sequence import Sequence


@pytest.fixture(scope="function")
def grid():
    grid = SequenceModelGrid(100, spacing=1000.0)
    grid.at_node["topographic__elevation"] = -0.001 * grid.x_of_node + 20.0
    return grid


@pytest.mark.parametrize("frac", [1.0 / 3.0, 1.0, 3.14159, 0.0])
@pytest.mark.parametrize("time_step", [1.0 / 3.0, 1.0, 3.14159])
def test_sequence_run_until(frac, time_step):
    grid = SequenceModelGrid(100, spacing=1000.0)
    grid.at_node["topographic__elevation"] = -0.001 * grid.x_of_node + 20.0
    seq = Sequence(grid, time_step=time_step)
    initial_layers = grid.at_layer.number_of_layers

    assert seq.time == pytest.approx(0.0)

    until = time_step * frac
    seq.run(until=until, progress_bar=False)
    assert seq.time == pytest.approx(until)

    expected = int(until // time_step)
    if until % time_step > 0:
        expected += 1

    assert grid.at_layer.number_of_layers - initial_layers == expected


@pytest.mark.parametrize("dt", [10.0, 1.0, 0.9, 200.0])
def test_sequence_run_until_with_dt(grid, dt):
    seq = Sequence(grid, time_step=100.0)
    initial_layers = grid.at_layer.number_of_layers

    assert seq.time == pytest.approx(0.0)

    until = 10.0
    seq.run(until=until, dt=dt, progress_bar=False)

    expected = int(until // dt)
    if until % dt > 0:
        expected += 1
    assert seq.time == pytest.approx(until)
    assert grid.at_layer.number_of_layers - initial_layers == expected


def test_sequence_x_of_shore_missing(grid):
    seq = Sequence(grid)

    assert "x_of_shore" not in grid.at_grid
    assert "x_of_shelf_edge" not in grid.at_grid

    assert grid.at_layer_grid.number_of_layers == 1
    assert np.isnan(grid.at_layer_grid["x_of_shore"][0])
    assert np.isnan(grid.at_layer_grid["x_of_shelf_edge"][0])

    seq.update()

    assert grid.at_layer_grid.number_of_layers == 2
    assert np.isnan(grid.at_layer_grid["x_of_shore"][-1])
    assert np.isnan(grid.at_layer_grid["x_of_shelf_edge"][-1])


def test_sequence_x_of_shore(grid):
    seq = Sequence(grid, components=[ShorelineFinder(grid)])

    assert "x_of_shore" in grid.at_row
    assert "x_of_shelf_edge" in grid.at_row

    assert grid.at_layer_grid.number_of_layers == 1
    assert np.all(grid.at_layer_row["x_of_shore"][-1, :] == pytest.approx(20000.0))
    assert np.all(grid.at_layer_row["x_of_shelf_edge"][-1, :] > 20000.0)

    seq.update()

    assert grid.at_layer_grid.number_of_layers == 2
    assert np.all(grid.at_layer_row["x_of_shore"][-1, :] == pytest.approx(20000.0))
    assert np.all(grid.at_layer_row["x_of_shelf_edge"][-1, :] > 20000.0)
