from functools import partial

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.patches import Patch
from scipy.interpolate import interp1d

from .errors import MissingRequiredVariable


def _plot(
    elevation_at_layer,
    x_of_stack=None,
    x_of_shore_at_layer=None,
    x_of_shelf_edge_at_layer=None,
    color_water=(0.8, 1.0, 1.0),
    color_land=(0.8, 1.0, 0.8),
    color_shoreface=(0.8, 0.8, 0.0),
    color_shelf=(0.75, 0.5, 0.5),
    layer_line_width=0.5,
    layer_line_color="k",
    layer_start=0,
    layer_stop=-1,
    n_layers=5,
    title=None,
    x_label="Distance (m)",
    y_label="Elevation (m)",
    legend_location="lower left",
):
    if x_of_stack is None:
        x_of_stack = np.arange(elevation_at_layer.shape[1])

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
        fill_between_layers(
            x_of_stack,
            elevation_at_layer,
            lower=None,
            upper=stack_of_shore,
            fc=color_land,
        )

    if plot_shoreface:
        fill_between_layers(
            x_of_stack,
            elevation_at_layer,
            lower=stack_of_shore,
            upper=stack_of_shelf_edge,
            fc=color_shoreface,
        )

    if plot_shelf:
        fill_between_layers(
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


def plot_grid(grid, **kwds):
    elevation_at_layer = (
        grid.at_node["bedrock_surface__elevation"][grid.node_at_cell] + grid.at_layer.z
    )
    x_of_stack = grid.x_of_node[grid.node_at_cell]

    x_of_shore = grid.at_layer_grid["x_of_shore"].flatten()
    x_of_shelf_edge = grid.at_layer_grid["x_of_shelf_edge"].flatten()

    time_at_layer_grid = grid.at_layer_grid["age"].flatten()
    time_at_layer = grid.at_layer["age"]

    x_of_shore = interp1d(time_at_layer_grid, x_of_shore)(time_at_layer[:, 0])
    x_of_shelf_edge = interp1d(time_at_layer_grid, x_of_shelf_edge)(time_at_layer[:, 0])

    kwds.setdefault("title", f"time = {time_at_layer[-1, 0]} years")

    _plot(
        elevation_at_layer,
        x_of_stack=x_of_stack,
        x_of_shore_at_layer=x_of_shore,
        x_of_shelf_edge_at_layer=x_of_shelf_edge,
        **kwds,
    )


def plot_file(filename, **kwds):
    kwds.setdefault("title", f"{filename}")
    with xr.open_dataset(filename) as ds:
        try:
            thickness_at_layer = ds["at_layer:thickness"]
            x_of_shore = ds["at_grid:x_of_shore"].data.squeeze()
            x_of_shelf_edge = ds["at_grid:x_of_shelf_edge"].data.squeeze()
            bedrock = ds["at_node:bedrock_surface__elevation"].data.squeeze()
            time = ds["time"]
            time_at_layer = ds["at_layer:age"]
        except KeyError as err:
            raise MissingRequiredVariable(str(err))

        try:
            x_of_stack = ds["x_of_cell"].data.squeeze()
        except KeyError:
            x_of_stack = np.arange(ds.dims["cell"])

        elevation_at_layer = bedrock[-1, 1:-1] + np.cumsum(thickness_at_layer, axis=0)

    x_of_shore = interp1d(time, x_of_shore)(time_at_layer[:, 0])
    x_of_shelf_edge = interp1d(time, x_of_shelf_edge)(time_at_layer[:, 0])

    _plot(
        elevation_at_layer,
        x_of_stack=x_of_stack,
        x_of_shore_at_layer=x_of_shore,
        x_of_shelf_edge_at_layer=x_of_shelf_edge,
        **kwds,
    )


def _get_layers_to_plot(start, stop, num=-1):
    if num == 0:
        return None
    elif num < 0 or num > stop - start + 1:
        num = stop - start + 1
    step = int((stop - start + 1) / num)
    return slice(start, stop, step)


def fill_between_layers(x, y, lower=None, upper=None, fc=None):
    n_layers = len(y)

    if lower is None:
        lower = np.zeros(n_layers, dtype=int)

    if upper is None:
        upper = np.full(n_layers, len(x) - 1)

    for layer in range(n_layers - 1):
        xi, yi = outline_layer(
            x,
            y[layer],
            y[layer + 1],
            bottom_limits=(lower[layer], upper[layer]),
            top_limits=(lower[layer + 1], upper[layer + 1]),
        )
        plt.fill(xi, yi, fc=fc)


def outline_layer(
    x, y_of_bottom_layer, y_of_top_layer, bottom_limits=None, top_limits=None
):
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
    y_of_left = interp_between_layers(
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
    y_of_right = interp_between_layers(
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


def interp_between_layers(x, y_of_bottom, y_of_top, kind="linear"):
    x = np.asarray(x)
    y_of_top, y_of_bottom = np.asarray(y_of_top), np.asarray(y_of_bottom)

    assert len(y_of_top) == len(y_of_bottom) == len(x)

    if len(x) == 0:
        return np.array([], dtype=float)
    elif len(x) == 1:
        return y_of_bottom

    dy = (y_of_top - y_of_bottom) * interp1d((x[0], x[-1]), (0.0, 1.0), kind=kind)(x)

    return y_of_bottom + dy
