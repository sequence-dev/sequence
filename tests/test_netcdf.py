import numpy as np
import xarray as xr
from landlab import RasterModelGrid
from pytest import approx

from sequence.netcdf import to_netcdf


def pytest_generate_tests(metafunc):
    if "format" in metafunc.fixturenames:
        metafunc.parametrize(
            "format", ("NETCDF4", "NETCDF4_CLASSIC", "NETCDF3_64BIT", "NETCDF3_CLASSIC")
        )


def test_no_fields(tmpdir):
    grid = RasterModelGrid((3, 4))
    with tmpdir.as_cwd():
        to_netcdf(grid, "test.nc")
        ds = xr.open_dataset("test.nc")
    assert np.all(ds.x_of_node == approx(grid.x_of_node))
    assert np.all(ds.y_of_node == approx(grid.y_of_node))
    assert ds["time"] == approx([0.0])


def test_with_node_fields(tmpdir):
    grid = RasterModelGrid((3, 4))
    grid.at_node["z"] = np.arange(12)
    with tmpdir.as_cwd():
        to_netcdf(grid, "test.nc")
        ds = xr.open_dataset("test.nc")
    assert np.all(ds["at_node:z"] == grid.at_node["z"][None, :])
    assert ds["time"] == approx([0.0])


def test_append(tmpdir):
    grid = RasterModelGrid((3, 4))
    grid.at_node["z"] = np.arange(12)
    with tmpdir.as_cwd():
        to_netcdf(grid, "test.nc")
        grid.at_node["z"] *= 10
        to_netcdf(grid, "test.nc", mode="a", time=1.0)
        ds = xr.open_dataset("test.nc")
    assert ds["at_node:z"].shape == (2, 12)
    assert np.all(ds["time"] == approx([0.0, 1.0]))


def test_float_var(tmpdir):
    grid = RasterModelGrid((3, 4))
    grid.at_node["int_var"] = np.arange(12, dtype=int)
    grid.at_node["float_var"] = np.arange(12, dtype=float)
    with tmpdir.as_cwd():
        to_netcdf(grid, "test.nc")
        ds = xr.open_dataset("test.nc")
    assert np.all(ds["at_node:int_var"] == grid.at_node["int_var"][None, :])
    assert np.all(ds["at_node:float_var"] == approx(grid.at_node["float_var"][None, :]))


def test_with_names(tmpdir):
    grid = RasterModelGrid((3, 4))
    grid.at_node["var0"] = np.arange(12)
    grid.at_node["var1"] = np.arange(12)
    with tmpdir.as_cwd():
        # to_netcdf(grid, "test.nc", names=("var0",))
        to_netcdf(grid, "test.nc", names={"node": ("var0",)})
        ds = xr.open_dataset("test.nc")
    assert "at_node:var0" in ds.variables
    assert "at_node:var1" not in ds.variables


def test_with_nodes(tmpdir):
    grid = RasterModelGrid((3, 4))
    grid.at_node["z"] = np.arange(12)
    # nodes = grid.nodes[1, :]
    nodes = grid.nodes[(1,)]
    with tmpdir.as_cwd():
        # to_netcdf(grid, "test.nc", nodes=nodes)
        to_netcdf(grid, "test.nc", ids={"node": nodes})
        ds = xr.open_dataset("test.nc")
    assert np.all(ds["at_node:z"] == [[4, 5, 6, 7]])


def test_without_layers(tmpdir):
    grid = RasterModelGrid((3, 4))
    with tmpdir.as_cwd():
        to_netcdf(grid, "test.nc")
        ds = xr.open_dataset("test.nc")
    assert np.all(ds["at_layer:thickness"] == [approx([0.0, 0.0])])


def test_with_layers(tmpdir):
    grid = RasterModelGrid((3, 4))
    grid.event_layers.add(10.0, age=0.0, water_depth=np.arange(2))
    with tmpdir.as_cwd():
        to_netcdf(grid, "test.nc")
        ds = xr.open_dataset("test.nc")
    assert ds.dims["layer"] == 1
    assert np.all(ds["at_layer:thickness"] == np.array([[10.0, 10.0]]))
    assert np.all(ds["at_layer:age"] == np.array([[0.0, 0.0]]))
    assert np.all(ds["at_layer:water_depth"] == np.array([[0.0, 1.0]]))


def test_formats(tmpdir, format):
    grid = RasterModelGrid((3, 4))
    grid.at_node["z"] = np.arange(12.0)
    with tmpdir.as_cwd():
        to_netcdf(grid, "test.nc", with_layers=False, format=format)
        ds = xr.open_dataset("test.nc")
    assert np.all(ds["at_node:z"] == approx(grid.at_node["z"][None, :]))
    assert ds["time"] == approx([0.0])


def test_one_location(tmpdir):
    grid = RasterModelGrid((3, 4))
    grid.at_node["var0"] = np.arange(12.0)
    grid.at_node["var1"] = np.arange(12.0) * 10.0
    with tmpdir.as_cwd():
        to_netcdf(grid, "test.nc", with_layers=False, at="node", names="var0")
        ds = xr.open_dataset("test.nc")
    assert np.all(ds["at_node:var0"] == approx(grid.at_node["var0"][None, :]))
    assert ds["time"] == approx([0.0])
