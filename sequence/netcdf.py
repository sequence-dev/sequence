"""Write a `SequenceModelGrid` to a NetCDF file."""
from __future__ import annotations

import contextlib
import os
import warnings
from collections import defaultdict
from collections.abc import Iterable
from collections.abc import Sequence
from os import PathLike
from typing import Any

import netCDF4 as nc
import numpy as np
from numpy.typing import NDArray

from sequence.grid import SequenceModelGrid

_NUMPY_TO_NETCDF_TYPE = {
    "float32": "f4",
    "float64": "f8",
    "int8": "i1",
    "int16": "i2",
    "int32": "i4",
    "int64": "i8",
    "uint8": "u1",
    "uint16": "u2",
    "uint32": "u4",
    "uint64": "u8",
    "bool": "i1",
}


def _netcdf_var_name(name: str, at: str) -> str:
    """Get the name a field will be stored as in a netCDF file."""
    return f"at_{at}:{name}"


def _netcdf_type(arr: NDArray) -> str:
    """Get the netCDF type string for a numpy array."""
    return _NUMPY_TO_NETCDF_TYPE[str(arr.dtype)]


def _create_grid_dimension(
    root: Any,
    grid: SequenceModelGrid,
    at: str = "node",
    ids: slice | Iterable[int] | None = None,
) -> Any:
    """Create grid dimensions for a netcdf file."""
    if ids is None:
        ids = slice(None)

    if at not in (
        "node",
        "link",
        "patch",
        "corner",
        "face",
        "cell",
        "grid",
        "row",
        "column",
    ):
        raise ValueError(f"unknown grid location {at}")

    if at not in root.dimensions:
        if at == "grid":
            number_of_elements = 1
        elif at == "row":
            number_of_elements = len(getattr(grid, f"y_of_{at}")[ids])
        elif at == "column":
            number_of_elements = len(getattr(grid, f"x_of_{at}")[ids])
        else:
            number_of_elements = len(getattr(grid, f"xy_of_{at}")[ids])
        root.createDimension(at, number_of_elements)

    return root


def _create_grid_coordinates(
    root: Any,
    grid: SequenceModelGrid,
    at: str = "node",
    ids: slice | Iterable[int] | None = None,
) -> Any:
    """Create x and y coordinates for a field location."""
    _create_grid_dimension(root, grid, at=at, ids=ids)

    if at != "grid":
        root.createVariable(f"x_of_{at}", "f8", (at,))
        root.createVariable(f"y_of_{at}", "f8", (at,))

        for coord in ("x", "y"):
            name = f"{coord}_of_{at}"
            if name not in root.variables:
                root.createVariable(name, "f8", (at,))

    return root


def _set_grid_coordinates(
    root: Any,
    grid: SequenceModelGrid,
    at: str = "node",
    ids: slice | Iterable[int] | None = None,
) -> None:
    """Set the values for the coordinates of a field location."""
    if ids is None:
        ids = slice(None)
        # ids = Ellipsis
    _create_grid_coordinates(root, grid, at=at, ids=ids)

    if at == "grid":
        return

    if at == "row":
        coords = getattr(grid, f"y_of_{at}")
        root.variables[f"y_of_{at}"][:] = coords[ids]
    elif at == "column":
        coords = getattr(grid, f"x_of_{at}")
        root.variables[f"x_of_{at}"][:] = coords[ids]
    else:
        coords = getattr(grid, f"xy_of_{at}")
        root.variables[f"x_of_{at}"][:] = coords[ids, 0]
        root.variables[f"y_of_{at}"][:] = coords[ids, 1]


def _create_field(
    root: Any,
    grid: SequenceModelGrid,
    at: str = "node",
    names: Iterable[str] | None = None,
) -> None:
    """Create variables at a field location(s)."""
    if names is None:
        names = grid[at]

    dimensions = [at]
    if "time" in root.dimensions:
        dimensions = ["time"] + dimensions

    for name in names:
        netcdf_name = _netcdf_var_name(name, at)
        if netcdf_name not in root.variables:
            root.createVariable(netcdf_name, _netcdf_type(grid[at][name]), dimensions)


def _set_field(
    root: Any,
    grid: SequenceModelGrid,
    at: str = "node",
    ids: slice | Iterable[int] | None = None,
    names: str | Iterable[str] | None = None,
) -> None:
    """Set values for variables at a field location(s)."""
    if isinstance(names, str):
        names = [names]
    names = set(names or grid[at])

    if missing := names - set(grid[at]):
        warnings.warn(
            f"missing field{'(s)' if len(missing) > 1 else ''} ({', '.join(missing)})",
            stacklevel=2,
        )
        names = names & set(grid[at])

    if at == "grid":
        with contextlib.suppress(KeyError):
            names.remove("x_of_shelf_edge")
        with contextlib.suppress(KeyError):
            names.remove("x_of_shore")

    _create_field(root, grid, at=at, names=names)

    if "time" in root.dimensions:
        n_times = len(root.dimensions["time"])
        for name in names:
            if grid[at][name].ndim > 0:
                values = grid[at][name][ids]
            else:
                values = grid[at][name]
            root.variables[_netcdf_var_name(name, at)][n_times - 1, :] = values
    else:
        for name in names:
            root.variables[_netcdf_var_name(name, at)][:] = grid[at][name][ids]


def _create_layers(
    root: Any, grid: SequenceModelGrid, names: Iterable[str] | None = None
) -> None:
    """Create variables at grid layers."""
    if names is None:
        names = []
    for name in names:
        netcdf_name = _netcdf_var_name(name, "layer")
        if netcdf_name not in root.variables:
            root.createVariable(
                netcdf_name,
                _netcdf_type(grid.event_layers[name]),
                ("layer", "row", "column"),
            )

    netcdf_name = _netcdf_var_name("thickness", "layer")
    if netcdf_name not in root.variables:
        root.createVariable(netcdf_name, "f8", ("layer", "row", "column"))


def _set_layers(
    root: Any,
    grid: SequenceModelGrid,
    names: Iterable[str] | None = None,
    ids: slice | Iterable[int] | None = None,
) -> None:
    """Set values for variables at a grid layers."""
    if isinstance(names, str):
        names = [names]
    names = names or grid.event_layers.tracking

    if "layer" not in root.dimensions:
        root.createDimension("layer", None)

    _create_layers(root, grid, names=names)

    n_layers = grid.event_layers.number_of_layers
    for name in names:
        layers = grid.event_layers[name][:, ids].reshape(
            (-1, grid.shape[0] - 2, grid.shape[1] - 2)
        )
        root.variables[_netcdf_var_name(name, "layer")][:n_layers, :, :] = layers

    dz = grid.event_layers.dz[:, ids].reshape(
        (-1, grid.shape[0] - 2, grid.shape[1] - 2)
    )
    root.variables[_netcdf_var_name("thickness", "layer")][:n_layers, :, :] = dz


def to_netcdf(
    grid: SequenceModelGrid,
    filepath: str | PathLike[str],
    mode: str = "w",
    format: str = "NETCDF4",
    time: float = 0.0,
    at: str | Sequence[str] | None = None,
    ids: dict[str, NDArray[np.integer]] | int | Iterable[int] | slice | None = None,
    names: None | (dict[str, Iterable[str] | None] | str | Iterable[str]) = None,
    with_layers: bool = True,
) -> None:
    """Write a grid and fields to a netCDF file.

    Parameters
    ----------
    grid: grid_like
        A landlab grid.
    filepath: str
        File to which to save the grid.
    mode: {'w', 'a'}, optional
        Write ('w') or append ('a') mode. If mode='w', any existing
        file at this location will be overwritten. If mode="a",
        existing variables will be appended as a new time slice.
    format: {'NETCDF4', 'NETCDF4_CLASSIC', 'NETCDF3_64BIT', 'NETCDF3_CLASSIC'}, optional
        File format for the resulting netCDF file.
    time: float, optional
        Time to use when adding data. This will be appended to the time
        variable.
    at: str or iterable or str, optional
        Field location(s) on the grid for fields to write. Locations can
        be 'node', 'link', 'patch', 'corner', 'face', 'patch'. The default
        is to write variables from all field locations.
    ids: array_like of int, optional
        Indices of elements to write.
    names: iterable or str, optional
        Names of fields to write to the netCDF file.
    with_layers : bool, optional
        Indicate if the NetCDF file should contain the grid's layers.
    """
    if with_layers and format != "NETCDF4":
        raise ValueError("Grid layers are only available with the NETCDF4 format.")
    if at is None:
        at = ["node", "link", "face", "cell", "grid"]

    if isinstance(at, str):
        at = [at]
    if isinstance(names, str):
        names = [names]
    if isinstance(ids, int):
        ids = [ids]
    elif ids is None:
        ids = slice(None)

    names_dict = defaultdict(list)
    if not isinstance(names, dict):
        for loc in at:
            if names is None:
                names_dict[loc] = list(grid[loc])
            else:
                names_dict[loc] = list(set(names) & set(grid[loc]))
    else:
        for loc, names_ in names.items():
            if names_ is None:
                names_dict[loc] = list(grid[loc])
            elif isinstance(names_, str):
                names_dict[loc] = [names_]
            else:
                names_dict[loc] = list(names_)

    with contextlib.suppress(ValueError):
        names_dict["grid"].remove("x_of_shore")
    with contextlib.suppress(ValueError):
        names_dict["grid"].remove("x_of_shelf_edge")
    names_dict["row"] = ["x_of_shore", "x_of_shelf_edge"]

    ids_dict: dict[str, slice | Iterable[int]] = defaultdict(lambda: slice(None))
    if not isinstance(ids, dict):
        for loc in at:
            ids_dict[loc] = ids
    else:
        for loc, ids_ in ids.items():
            if ids_ is None:
                ids_dict[loc] = slice(None)
            else:
                ids_dict[loc] = ids_

    if not os.path.isfile(filepath):
        mode = "w"
    root = nc.Dataset(filepath, mode, format=format)

    if mode == "w":
        root.createDimension("time", None)
        root.createVariable("time", "f8", ("time",))

        _set_grid_coordinates(root, grid, at="row", ids=ids_dict["row"])
        _set_grid_coordinates(root, grid, at="column", ids=ids_dict["column"])
        for loc in at:
            _set_grid_coordinates(root, grid, at=loc, ids=ids_dict[loc])

    n_times = len(root.dimensions["time"])
    root.variables["time"][n_times] = time

    for loc in at:
        _set_field(root, grid, at=loc, ids=ids_dict[loc], names=names_dict[loc])
    _set_field(
        root,
        grid,
        at="row",
        ids=ids_dict["row"],
        names=["x_of_shore", "x_of_shelf_edge"],
    )

    if with_layers:
        _set_layers(root, grid, names=None, ids=ids_dict.get("cell", None))

    root.close()
