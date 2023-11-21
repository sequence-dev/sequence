import pytest

from sequence import SequenceModelGrid


def test_init():
    n_cols = 500
    spacing = 10.0
    grid = SequenceModelGrid(n_cols, spacing=spacing)
    assert grid.shape == (3, n_cols)
    assert grid.spacing == (1.0, spacing)


def test_from_dict():
    expected = SequenceModelGrid(500, spacing=5.0)

    actual = SequenceModelGrid.from_dict({"n_cols": 500, "spacing": 5.0})
    assert actual.shape == expected.shape
    assert actual.spacing == expected.spacing


def test_from_dict_old_style():
    expected = SequenceModelGrid(500, spacing=5.0)

    actual = SequenceModelGrid.from_dict({"shape": (1, 500), "xy_spacing": (5.0, 1.0)})
    assert actual.shape == expected.shape
    assert actual.spacing == expected.spacing

    actual = SequenceModelGrid.from_dict({"shape": 500, "xy_spacing": 5.0})
    assert actual.shape == expected.shape
    assert actual.spacing == expected.spacing


def test_fields():
    grid = SequenceModelGrid(500, spacing=5.0)
    assert list(grid.at_node) == ["sediment_deposit__thickness"]
    assert list(grid.at_grid) == ["sea_level__elevation"]

    assert grid.at_node["sediment_deposit__thickness"] == pytest.approx(0.0)
    assert grid.at_grid["sea_level__elevation"] == pytest.approx(0.0)


def test_boundary_conditions():
    grid = SequenceModelGrid(500, spacing=5.0)

    status_at_node = grid.status_at_node.reshape(grid.shape)
    assert all(status_at_node[0] == grid.BC_NODE_IS_CLOSED)
    assert all(status_at_node[2] == grid.BC_NODE_IS_CLOSED)


def test_from_toml(tmpdir):
    expected = SequenceModelGrid(500, spacing=5.0)

    with tmpdir.as_cwd():
        with open("grid.toml", "w") as fp:
            print("[sequence.grid]", file=fp)
            print("n_cols = 500", file=fp)
            print("spacing = 5.0", file=fp)
        actual = SequenceModelGrid.from_toml("grid.toml")
    assert actual.shape == expected.shape
    assert actual.spacing == expected.spacing
