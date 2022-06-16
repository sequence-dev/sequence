import os
from collections import defaultdict

import netCDF4 as nc

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


def _netcdf_var_name(name, at):
    """Get the name a field will be stored as in a netCDF file."""
    return f"at_{at}:{name}"


def _netcdf_type(arr):
    """Get the netCDF type string for a numpy array."""
    return _NUMPY_TO_NETCDF_TYPE[str(arr.dtype)]


def _create_grid_dimension(root, grid, at="node", ids=None):
    """Create grid dimensions for a netcdf file."""
    if ids is None:
        ids = Ellipsis

    if at not in ("node", "link", "patch", "corner", "face", "cell", "grid"):
        raise ValueError(f"unknown grid location {at}")

    if at not in root.dimensions:
        if at == "grid":
            number_of_elements = 1
        else:
            number_of_elements = len(getattr(grid, f"xy_of_{at}")[ids])
        root.createDimension(at, number_of_elements)

    return root


def _create_grid_coordinates(root, grid, at="node", ids=None):
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


def _set_grid_coordinates(root, grid, at="node", ids=None):

    """Set the values for the coordinates of a field location."""
    if ids is None:
        ids = Ellipsis
    _create_grid_coordinates(root, grid, at=at, ids=ids)

    if at == "grid":
        return

    coords = getattr(grid, f"xy_of_{at}")
    root.variables[f"x_of_{at}"][:] = coords[ids, 0]
    root.variables[f"y_of_{at}"][:] = coords[ids, 1]


def _create_field(root, grid, at="node", names=None):
    """Create variables at a field location(s)."""
    names = names or grid[at]
    dimensions = (at,)
    if "time" in root.dimensions:
        dimensions = ("time",) + dimensions

    for name in names:
        netcdf_name = _netcdf_var_name(name, at)
        if netcdf_name not in root.variables:
            root.createVariable(netcdf_name, _netcdf_type(grid[at][name]), dimensions)


def _set_field(root, grid, at="node", ids=None, names=None):
    """Set values for variables at a field location(s)."""
    if isinstance(names, str):
        names = [names]
    names = names or grid[at]

    _create_field(root, grid, at=at, names=names)

    if "time" in root.dimensions:
        n_times = len(root.dimensions["time"])
        for name in names:
            root.variables[_netcdf_var_name(name, at)][n_times - 1, :] = grid[at][name][
                ids
            ]
    else:
        for name in names:
            root.variables[_netcdf_var_name(name, at)][:] = grid[at][name][ids]


def _create_layers(root, grid, names=None):
    """Create variables at grid layers."""
    for name in names:
        netcdf_name = _netcdf_var_name(name, "layer")
        if netcdf_name not in root.variables:
            root.createVariable(
                netcdf_name, _netcdf_type(grid.event_layers[name]), ("layer", "cell")
            )

    netcdf_name = _netcdf_var_name("thickness", "layer")
    if netcdf_name not in root.variables:
        root.createVariable(netcdf_name, "f8", ("layer", "cell"))


def _set_layers(root, grid, names=None):
    """Set values for variables at a grid layers."""
    if isinstance(names, str):
        names = [names]
    names = names or grid.event_layers.tracking

    if "layer" not in root.dimensions:
        root.createDimension("layer", None)

    _create_layers(root, grid, names=names)

    n_layers = grid.event_layers.number_of_layers
    for name in names:
        root.variables[_netcdf_var_name(name, "layer")][
            :n_layers, :
        ] = grid.event_layers[name][:]
    root.variables[_netcdf_var_name("thickness", "layer")][
        :n_layers, :
    ] = grid.event_layers.dz[:]


def to_netcdf(
    grid,
    filepath,
    mode="w",
    format="NETCDF4",
    time=0.0,
    at=None,
    ids=None,
    names=None,
    with_layers=True,
):
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
    names: array_link or str, optional
        Names of fields to write to the netCDF file.
    """
    if with_layers and format != "NETCDF4":
        raise ValueError("Grid layers are only available with the NETCDF4 format.")

    at = at or {"node", "link", "face", "cell", "grid"}
    if isinstance(at, str):
        at = [at]

    if len(at) == 1:
        if not isinstance(names, dict):
            names = {at[0]: names}
        if not isinstance(ids, dict):
            ids = {at[0]: ids}

    names = defaultdict(lambda: None, names or {})
    ids = defaultdict(lambda: Ellipsis, ids or {})

    if not os.path.isfile(filepath):
        mode = "w"
    root = nc.Dataset(filepath, mode, format=format)

    if mode == "w":
        root.createDimension("time", None)
        root.createVariable("time", "f8", ("time",))

        for loc in at:
            _set_grid_coordinates(root, grid, at=loc, ids=ids[loc])

    n_times = len(root.dimensions["time"])
    root.variables["time"][n_times] = time

    for loc in at:
        _set_field(root, grid, at=loc, ids=ids[loc], names=names[loc])
    if with_layers:
        _set_layers(root, grid, names=None)

    root.close()
