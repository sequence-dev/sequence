"""Plot the layers of a `SequenceModelGrid`."""
from __future__ import annotations

from functools import partial
from os import PathLike
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.patches import Patch
from numpy.typing import NDArray
from scipy.interpolate import interp1d

from sequence.errors import InvalidRowError
from sequence.errors import MissingRequiredVariable
from sequence.grid import SequenceModelGrid


def plot_layers(
    elevation_at_layer: NDArray[np.floating],
    x_of_stack: NDArray[np.floating] | None = None,
    x_of_shore_at_layer: NDArray[np.floating] | None = None,
    x_of_shelf_edge_at_layer: NDArray[np.floating] | None = None,
    color_water: tuple[float, float, float] | str = (0.8, 1.0, 1.0),
    color_land: tuple[float, float, float] | str = (0.8, 1.0, 0.8),
    color_shoreface: tuple[float, float, float] | str = (0.8, 0.8, 0.0),
    color_shelf: tuple[float, float, float] | str = (0.75, 0.5, 0.5),
    layer_line_width: float = 0.5,
    layer_line_color: tuple[float, float, float] | str = "k",
    layer_start: int = 0,
    layer_stop: int = -1,
    n_layers: int = 5,
    title: str = "",
    x_label: str = "Distance (m)",
    y_label: str = "Elevation (m)",
    legend_location: str = "lower left",
) -> None:
    """Create a plot of sediment layers along a profile.

    Parameters
    ----------
    elevation_at_layer : array-like
        Elevations along each layer to plot.
    x_of_stack : array-like, optional
        X-coordinate of each stack. If not provided, use the stack index.
    x_of_shore_at_layer : array-like, optional
        The x-position of the shoreline at each layer.
    x_of_shelf_edge_at_layer : array-like, optional
        The x-position of the shelf edge at each layer.
    color_water : color, optional
        A `matplotlib.colors` color to use for water.
    color_land : color, optional
        A `matplotlib.colors` color to use for land.
    color_shoreface : color, optional
        A `matplotlib.colors` color to use for the shoreface.
    color_shelf : color, optional
        A `matplotlib.colors` color to use for the shelf.
    layer_line_width : float, optional
        Width of the line to use for outlining layers.
    layer_line_color : color, optional
        A `matplotlib.colors` color to use for layer outlines.
    layer_start : int, optional
        The first layer to plot.
    layer_stop : int, optional
        The last layer to plot.
    n_layers : int, optional
        The number of layers to plot.
    title : str, optional
        The title to use for the plot.
    x_label : str, optional
        The label to use for the x-axis.
    y_label : str, optional
        The label to use for the y-axis.
    legend_location : str, optional
        The location of the legend. Valid values are those accepted by the *loc*
        keyword use in :func:`matplotlib.pyplot.legend`.


    See Also
    --------
    :func:`plot_file` : Plot a `SequenceModelGrid`'s layers from a file.
    :func:`plot_grid` : Plot a `SequenceModelGrid`'s layers.
    """
    if x_of_stack is None:
        x_of_stack = np.arange(elevation_at_layer.shape[1], dtype=float)

    if x_of_shore_at_layer is None:
        x_of_shore_at_layer = np.zeros(len(elevation_at_layer))

    if x_of_shelf_edge_at_layer is None:
        x_of_shelf_edge_at_layer = np.zeros(len(elevation_at_layer))

    plot_land = bool(color_land)
    plot_shoreface = bool(color_shoreface)
    plot_shelf = bool(color_shelf)

    legend_item = partial(Patch, edgecolor="k", linewidth=0.5)

    stack_of_shore = np.searchsorted(x_of_stack, x_of_shore_at_layer)
    stack_of_shelf_edge = np.searchsorted(x_of_stack, x_of_shelf_edge_at_layer)

    water = x_of_stack > x_of_shore_at_layer[-1]
    x_water = x_of_stack[water]
    y_water = elevation_at_layer[-1, water]

    if layer_stop < 0:
        layer_stop = len(elevation_at_layer) + layer_stop + 1
    layers_to_plot = _get_layers_to_plot(layer_start, layer_stop, num=n_layers)

    if np.any(water):
        if color_water:
            plt.fill_between(
                x_water, y_water, np.full_like(x_water, y_water[0]), fc=color_water
            )
        plt.plot([x_water[0], x_water[-1]], [y_water[0], y_water[0]], color="k")

    if plot_land:
        _fill_between_layers(
            x_of_stack,
            elevation_at_layer,
            lower=None,
            upper=stack_of_shore,
            fc=color_land,
        )

    if plot_shoreface:
        _fill_between_layers(
            x_of_stack,
            elevation_at_layer,
            lower=stack_of_shore,
            upper=stack_of_shelf_edge,
            fc=color_shoreface,
        )

    if plot_shelf:
        _fill_between_layers(
            x_of_stack,
            elevation_at_layer,
            lower=stack_of_shelf_edge,
            upper=None,
            fc=color_shelf,
        )

    if layers_to_plot:
        plt.plot(
            x_of_stack,
            elevation_at_layer[layers_to_plot].T,
            color=layer_line_color,
            linewidth=layer_line_width,
        )
    plt.plot(
        x_of_stack,
        elevation_at_layer[-1],
        color=layer_line_color,
        linewidth=layer_line_width,
    )

    if legend_location:
        items = [
            ("Land", color_land),
            ("Shoreface", color_shoreface),
            ("Shelf", color_shelf),
        ]
        legend = [legend_item(label=label, fc=color) for label, color in items if color]
        legend and plt.legend(handles=legend, loc=legend_location)

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    if title:
        plt.title(title)
    plt.xlim((x_of_stack[0], x_of_stack[-1]))

    plt.show()


def plot_grid(grid: SequenceModelGrid, row: int | None = None, **kwds: Any) -> None:
    """Plot a :class:`~SequenceModelGrid`.

    Parameters
    ----------
    grid : SequenceModelGrid
        The grid to plot.
    row : int, optional
        The row of the grid to plot. If not provided, plot the middle row.
    **kwds: dict, optional
        Additional keyword arguments that are passed along to :func:`~plot_layers`.

    See Also
    --------
    :func:`plot_layers` : Plot layers from a 2D array of elevations.
    :func:`plot_file` : Plot a `SequenceModelGrid`'s layers from a file.
    """
    if row is None:
        row = (grid.number_of_rows - 2) // 2

    elevation_at_layer = (
        grid.get_profile("bedrock_surface__elevation")[row, 1:-1] + grid.at_layer.z
    )

    x_of_stack = grid.x_of_column[1:-1]

    x_of_shore = grid.at_layer_row["x_of_shore"]
    x_of_shelf_edge = grid.at_layer_row["x_of_shelf_edge"]

    time_at_layer_grid = grid.at_layer_grid["age"].flatten()
    time_at_layer = grid.at_layer["age"]

    x_of_shore = interp1d(time_at_layer_grid, x_of_shore[:, row].squeeze())(
        time_at_layer[:, 0]
    )
    x_of_shelf_edge = interp1d(time_at_layer_grid, x_of_shelf_edge[:, row].squeeze())(
        time_at_layer[:, 0]
    )

    kwds.setdefault("title", f"time = {time_at_layer[-1, 0]} years")

    plot_layers(
        elevation_at_layer,
        x_of_stack=x_of_stack,
        x_of_shore_at_layer=x_of_shore,
        x_of_shelf_edge_at_layer=x_of_shelf_edge,
        **kwds,
    )


def plot_file(filename: str | PathLike, row: int | None = None, **kwds: Any) -> None:
    """Plot a `SequenceModelGrid` from a *Sequence* output file.

    Parameters
    ----------
    filename : path-like
        Path to the file to plot.
    row : int, optional
        Row to plot. If not provided, plot the middle row.
    **kwds: dict, optional
        Additional keyword arguments that are passed along to :func:`~plot_layers`.

    See Also
    --------
    :func:`plot_layers` : Plot layers from a 2D array of elevations.
    :func:`plot_grid` : Plot a `SequenceModelGrid`'s layers.
    """
    kwds.setdefault("title", f"{filename}")
    with xr.open_dataset(filename) as ds:
        if "row" not in ds.dims:
            raise MissingRequiredVariable("row")

        if row is None:
            row = ds.dims["row"] // 2
        elif (row >= ds.dims["row"]) or (row < -ds.dims["row"]):
            raise InvalidRowError(row, ds.dims["row"])

        try:
            thickness_at_layer = ds["at_layer:thickness"][:, row, :]
            x_of_shore = ds["at_row:x_of_shore"].data
            x_of_shelf_edge = ds["at_row:x_of_shelf_edge"].data
            bedrock = (
                ds["at_node:bedrock_surface__elevation"]
                .data.reshape((-1, ds.dims["row"] + 2, ds.dims["column"] + 2))
                .squeeze()
            )
            time = ds["time"]
            time_at_layer = ds["at_layer:age"].data.reshape(
                (-1, ds.dims["row"], ds.dims["column"])
            )
        except KeyError as err:
            raise MissingRequiredVariable(str(err)) from err

        try:
            x_of_stack = (
                ds["x_of_cell"]
                .data.reshape((ds.dims["row"], ds.dims["column"]))[row, :]
                .squeeze()
            )
        except KeyError:
            x_of_stack = np.arange(ds.dims["cell"])

        elevation_at_layer = bedrock[-1, row, 1:-1] + np.cumsum(
            thickness_at_layer, axis=0
        )

    x_of_shore = interp1d(time, x_of_shore[:, row])(time_at_layer[:, row, 0])
    x_of_shelf_edge = interp1d(time, x_of_shelf_edge[:, row])(time_at_layer[:, row, 0])

    plot_layers(
        elevation_at_layer,
        x_of_stack=x_of_stack,
        x_of_shore_at_layer=x_of_shore,
        x_of_shelf_edge_at_layer=x_of_shelf_edge,
        **kwds,
    )


def _get_layers_to_plot(start: int, stop: int, num: int = -1) -> slice | None:
    if num == 0:
        return None
    elif num < 0 or num > stop - start + 1:
        num = stop - start + 1
    step = int((stop - start + 1) / num)
    return slice(start, stop, step)


def _fill_between_layers(
    x: NDArray,
    y: NDArray,
    lower: NDArray[np.integer] | None = None,
    upper: NDArray[np.integer] | None = None,
    fc: tuple[float, float, float] | str | None = None,
) -> None:
    n_layers = len(y)

    if lower is None:
        lower = np.zeros(n_layers, dtype=int)

    if upper is None:
        upper = np.full(n_layers, len(x) - 1)

    for layer in range(n_layers - 1):
        xi, yi = _outline_layer(
            x,
            y[layer],
            y[layer + 1],
            bottom_limits=(lower[layer], upper[layer]),
            top_limits=(lower[layer + 1], upper[layer + 1]),
        )
        plt.fill(xi, yi, fc=fc)


def _outline_layer(
    x: NDArray,
    y_of_bottom_layer: NDArray,
    y_of_top_layer: NDArray,
    bottom_limits: tuple[float | None, float | None] | None = None,
    top_limits: tuple[float | None, float | None] | None = None,
) -> tuple[NDArray, NDArray]:
    if bottom_limits is None:
        bottom_limits = (None, None)
    if top_limits is None:
        top_limits = (None, None)

    bottom_limits = (
        bottom_limits[0] if bottom_limits[0] is not None else 0,
        bottom_limits[1] if bottom_limits[1] is not None else len(x) - 1,
    )
    top_limits = (
        top_limits[0] if top_limits[0] is not None else 0,
        top_limits[1] if top_limits[1] is not None else len(x) - 1,
    )

    is_top = slice(top_limits[1], top_limits[0], -1)
    x_of_top = x[is_top]
    y_of_top = y_of_top_layer[is_top]

    is_bottom = slice(bottom_limits[0], bottom_limits[1])
    x_of_bottom = x[is_bottom]
    y_of_bottom = y_of_bottom_layer[is_bottom]

    if top_limits[0] > bottom_limits[0]:
        step = -1
        is_left = slice(bottom_limits[0], top_limits[0] + 1)
    else:
        step = 1
        is_left = slice(top_limits[0], bottom_limits[0] + 1)

    x_of_left = x[is_left]
    y_of_left = _interp_between_layers(
        x_of_left[::step],
        y_of_top_layer[is_left][::step],
        y_of_bottom_layer[is_left][::step],
    )
    x_of_left = x_of_left[::step][:-1]
    y_of_left = y_of_left[:-1]

    if bottom_limits[1] > top_limits[1]:
        step = -1
        is_right = slice(top_limits[1], bottom_limits[1] + 1)
    else:
        step = 1
        is_right = slice(bottom_limits[1], top_limits[1] + 1)
    x_of_right = x[is_right]
    y_of_right = _interp_between_layers(
        x_of_right[::step],
        y_of_bottom_layer[is_right][::step],
        y_of_top_layer[is_right][::step],
    )
    x_of_right = x_of_right[::step][:-1]
    y_of_right = y_of_right[:-1]

    return (
        np.r_[x_of_top, x_of_left, x_of_bottom, x_of_right],
        np.r_[y_of_top, y_of_left, y_of_bottom, y_of_right],
    )


def _interp_between_layers(
    x: NDArray[np.floating],
    y_of_bottom: NDArray[np.floating],
    y_of_top: NDArray[np.floating],
    kind: str = "linear",
) -> NDArray[np.floating]:
    x = np.asarray(x)
    y_of_top, y_of_bottom = np.asarray(y_of_top), np.asarray(y_of_bottom)

    assert len(y_of_top) == len(y_of_bottom) == len(x)

    if len(x) == 0:
        return np.array([], dtype=float)
    elif len(x) == 1:
        return y_of_bottom

    dy = (y_of_top - y_of_bottom) * interp1d((x[0], x[-1]), (0.0, 1.0), kind=kind)(x)

    return y_of_bottom + dy
