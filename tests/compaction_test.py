from __future__ import annotations

from numpy.testing import assert_array_almost_equal
from pytest import approx

from sequence.grid import SequenceModelGrid
from sequence.processes import Compact
from sequence.sequence import Sequence


def test_layers_compact():
    grid = SequenceModelGrid(5)
    grid.add_zeros("bedrock_surface__elevation", at="node")
    grid.add_zeros("topographic__elevation", at="node")

    compaction = Compact(
        grid,
        c=5e-08,
        porosity_max=0.5,
        porosity_min=0.01,
        rho_grain=2650.0,
        rho_void=1000.0,
    )
    sequence = Sequence(grid, time_step=100.0, components=[compaction])
    assert grid.event_layers.number_of_layers == 0
    for _ in range(n_layers := 15):
        sequence.add_layer(100.0)
    assert grid.event_layers.number_of_layers == 15
    assert grid.at_node["topographic__elevation"][grid.node_at_cell] == approx(
        n_layers * 100.0
    )

    sequence.run(progress_bar=False)

    assert (grid.event_layers["porosity"][: n_layers - 1, :] < 0.5).all()
    assert grid.event_layers["porosity"][n_layers - 1, :] == approx(0.5)

    assert (grid.event_layers.dz[: n_layers - 1, :] < 100.0).all()
    assert grid.event_layers.dz[n_layers - 1, :] == approx(100.0)


def test_layers_compact_only_once():
    grid = SequenceModelGrid(5)
    grid.add_zeros("bedrock_surface__elevation", at="node")
    grid.add_zeros("topographic__elevation", at="node")

    compaction = Compact(
        grid,
        c=5e-08,
        porosity_max=0.5,
        porosity_min=0.01,
        rho_grain=2650.0,
        rho_void=1000.0,
    )
    sequence = Sequence(grid, time_step=100.0, components=[compaction])
    assert grid.event_layers.number_of_layers == 0
    for _ in range(15):
        sequence.add_layer(100.0)

    sequence.run(progress_bar=False)
    assert sequence.time == approx(100.0)

    thickness_of_layers = grid.event_layers.thickness.copy()

    sequence.run(until=4000.0, progress_bar=False)
    assert sequence.time == approx(4000.0)

    assert_array_almost_equal(grid.event_layers.thickness, thickness_of_layers)
