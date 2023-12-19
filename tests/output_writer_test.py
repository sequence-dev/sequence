import numpy as np
import xarray as xr
from pytest import approx
from pytest import raises

from sequence import SequenceModelGrid
from sequence.output_writer import OutputWriter


def test_no_fields(tmpdir):
    grid = SequenceModelGrid((1, 4), spacing=(1.0, 1.0))
    with tmpdir.as_cwd():
        writer = OutputWriter(grid, "test.nc")
        writer.run_one_step()
        ds = xr.open_dataset("test.nc")

    assert np.all(ds.x_of_node == approx(grid.x_of_node))
    assert np.all(ds.y_of_node == approx(grid.y_of_node))
    assert ds["time"] == approx([0.0])


def test_default_output_interval(tmpdir):
    grid = SequenceModelGrid((1, 4), spacing=(1.0, 1.0))
    with tmpdir.as_cwd():
        writer = OutputWriter(grid, "test.nc")
        for _ in range(4):
            writer.run_one_step()
        ds = xr.open_dataset("test.nc")

    assert np.all(ds.x_of_node == approx(grid.x_of_node))
    assert np.all(ds.y_of_node == approx(grid.y_of_node))
    assert np.all(ds["time"] == approx([0.0, 1.0, 2.0, 3.0]))


def test_output_interval(tmpdir):
    grid = SequenceModelGrid((1, 4), spacing=(1.0, 1.0))
    with tmpdir.as_cwd():
        writer = OutputWriter(grid, "test.nc", interval=2)
        for _ in range(3):
            writer.run_one_step()
        ds = xr.open_dataset("test.nc")

    assert np.all(ds.x_of_node == approx(grid.x_of_node))
    assert np.all(ds.y_of_node == approx(grid.y_of_node))
    assert np.all(ds["time"] == approx([0.0, 2.0]))


def test_default_clobber_is_false(tmpdir):
    grid = SequenceModelGrid((1, 4), spacing=(1.0, 1.0))
    with tmpdir.as_cwd():
        OutputWriter(grid, "test.nc").run_one_step()
        with raises(RuntimeError):
            OutputWriter(grid, "test.nc").run_one_step()


def test_clobber_keyword(tmpdir):
    grid = SequenceModelGrid((1, 4), spacing=(1.0, 1.0))
    with tmpdir.as_cwd():
        writer = OutputWriter(grid, "test.nc")
        for _ in range(10):
            writer.run_one_step()
        with xr.open_dataset("test.nc") as ds:
            assert len(ds["time"]) == 10

        with raises(RuntimeError):
            OutputWriter(grid, "test.nc", clobber=False).run_one_step()

        OutputWriter(grid, "test.nc", clobber=True).run_one_step()
        with xr.open_dataset("test.nc") as ds:
            assert len(ds["time"]) == 1


def test_default_is_all_rows(tmpdir):
    grid = SequenceModelGrid((1, 4), spacing=(1.0, 1.0))
    with tmpdir.as_cwd():
        OutputWriter(grid, "test.nc").run_one_step()
        with xr.open_dataset("test.nc") as ds:
            assert len(ds.x_of_node) == grid.number_of_nodes


def test_rows_keyword(tmpdir):
    grid = SequenceModelGrid((1, 4), spacing=(1.0, 1.0))
    with tmpdir.as_cwd():
        OutputWriter(grid, "test.nc", rows=(1,)).run_one_step()
        with xr.open_dataset("test.nc") as ds:
            assert np.all(ds.x_of_column == approx([0, 1]))
            assert np.all(ds.y_of_row == approx(0.0))

        # OutputWriter(grid, "test.nc", rows=((0, 2),), clobber=True).run_one_step()
        OutputWriter(grid, "test.nc", rows=(0, 2), clobber=True).run_one_step()
        with xr.open_dataset("test.nc") as ds:
            assert np.all(ds.x_of_column == approx([0, 1]))
            assert np.all(ds.y_of_row == approx([2, 1]))
