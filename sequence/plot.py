import pathlib
from functools import partial
from itertools import tee

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.patches import Patch
from scipy.interpolate import interp1d


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def plot_strat(
    filename,
    color_water=(0.8, 1.0, 1.0),
    color_land=(0.8, 1.0, 0.8, 0.5),
    color_shoreface=(0.8, 0.8, 0.0, 0.5),
    color_shelf=(0.75, 0.5, 0.5, 0.5),
    layer_line_width=0.5,
    layer_line_color="k",
    layer_start=0,
    layer_stop=-1,
    n_layers=5,
    title="{filename}",
    x_label="Distance (m)",
    y_label="Elevation (m)",
    legend_location="lower left",
):
    plot_land = bool(color_land)
    plot_shoreface = bool(color_shoreface)
    plot_shelf = bool(color_shelf)

    filename = pathlib.Path(filename)

    legend_item = partial(Patch, edgecolor="k", linewidth=0.5)

    with xr.open_dataset(filename) as ds:
        n_times = ds.dims["time"]

        thickness_at_layer = ds["at_layer:thickness"][:n_times]
        x_of_shore = ds["at_grid:x_of_shore"].data.squeeze()
        x_of_shelf_edge = ds["at_grid:x_of_shelf_edge"].data.squeeze()
        # x_of_stack = ds["x_of_cell"].data.squeeze()
        bedrock = ds["at_node:bedrock_surface__elevation"].data.squeeze()
        try:
            x_of_stack = ds["x_of_cell"].data.squeeze()
        except KeyError:
            x_of_stack = np.arange(ds.dims["cell"])
            # (
            #     np.arange(ds.dims["cell"]) * ds["xy_spacing"][0]
            #     + ds["xy_of_lower_left"][0]
            # )

        elevation_at_layer = bedrock[-1, 1:-1] + np.cumsum(thickness_at_layer, axis=0)

    if n_layers:
        # layer_step = int(len(elevation_at_layer) / (n_layers + 1))
        if layer_stop < 0:
            layer_stop = len(elevation_at_layer) + layer_stop
        if n_layers >= 0:
            if n_layers > layer_stop - layer_start:
                layer_step = layer_stop - layer_start - 1
            else:
                layer_step = int((layer_stop - layer_start) / (n_layers + 1))
        else:
            layer_step = 1
        plt.plot(
            x_of_stack,
            elevation_at_layer[layer_start:layer_stop:layer_step].T,
            color=layer_line_color,
            linewidth=layer_line_width,
        )

    water = x_of_stack > x_of_shore[-1]
    x_water = x_of_stack[water]
    y_water = elevation_at_layer[-1, water]

    if color_water:
        plt.fill_between(
            x_water, y_water, np.full_like(x_water, y_water[0]), fc=color_water
        )
    plt.plot([x_water[0], x_water[-1]], [y_water[0], y_water[0]], color="k")

    # stack_of_shore = np.searchsorted(x_of_stack, x_of_shore)

    if plot_land:
        fill_layers(
            x_of_stack,
            elevation_at_layer,
            lower=None,
            upper=x_of_shore,
            fc=color_land,
        )

    stack_of_shelf_edge = np.searchsorted(x_of_stack, x_of_shelf_edge)

    if plot_shoreface:
        fill_layers(
            x_of_stack,
            elevation_at_layer,
            lower=x_of_shore,
            upper=x_of_shelf_edge,
            fc=color_shoreface,
        )

    if plot_shelf:
        fill_layers(
            x_of_stack,
            elevation_at_layer,
            lower=x_of_shelf_edge,
            upper=None,
            fc=color_shelf,
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
    plt.title(title.format(filename=filename.name))
    plt.xlim((x_of_stack[0], x_of_stack[-1]))

    plt.show()


def fill_layers(x, y, lower=None, upper=None, fc=None):
    n_layers = len(y)

    if lower is None:
        lower = np.full(n_layers, x[0])

    if upper is None:
        upper = np.full(n_layers, x[-1])

    for layer in range(n_layers - 1):
        # for layer in range(1):
        top = (x > lower[layer + 1]) & (x < upper[layer + 1])
        bottom = (x > lower[layer]) & (x < upper[layer])

        xi, yi = outline_layer(
            x,
            y[layer],
            y[layer + 1],
            bottom_limits=(lower[layer], upper[layer]),
            top_limits=(lower[layer + 1], upper[layer + 1]),
        )
        plt.fill(xi, yi, fc=fc)  # , ec="k")

        # plt.plot(x[bottom], y[layer][bottom], linewidth=3)
        # plt.plot(x[top], y[layer + 1][top], linewidth=3)


def outline_layer(
    x, y_of_bottom_layer, y_of_top_layer, bottom_limits=None, top_limits=None
):
    #     bottom_limits = (None, None) if bottom_limits is None else bottom_limits
    #     top_limits = (None, None) if top_limits is None else top_limits
    #
    #     bottom_limits[0] = x[0] if bottom_limits is None else bottom_limits[0]
    #     bottom_limits[1] = x[1] if bottom_limits is None else bottom_limits[1]
    #     bottom_limits[0] = x[0] if bottom_limits is None else bottom_limits[0]
    #     bottom_limits[1] = x[1] if bottom_limits is None else bottom_limits[1]

    if bottom_limits is None:
        bottom_limits = (x[0], x[1])
    if top_limits is None:
        top_limits = (x[0], x[1])

    is_top = (x >= top_limits[0]) & (x <= top_limits[1])
    x_of_top = x[is_top]
    y_of_top = y_of_top_layer[is_top]

    is_bottom = (x >= bottom_limits[0]) & (x <= bottom_limits[1])
    x_of_bottom = x[is_bottom]
    y_of_bottom = y_of_bottom_layer[is_bottom]

    is_left = (x > min(x_of_top[0], x_of_bottom[0])) & (
        x < max(x_of_top[0], x_of_bottom[0])
    )
    x_of_left = x[is_left]
    reverse = top_limits[0] > bottom_limits[0]
    y_of_left = interp_between_layers(
        x_of_left, y_of_top_layer[is_left], y_of_bottom_layer[is_left], reverse=reverse
    )

    is_right = (x > min(x_of_top[-1], x_of_bottom[-1])) & (
        x < max(x_of_top[-1], x_of_bottom[-1])
    )
    x_of_right = x[is_right]
    reverse = top_limits[1] < bottom_limits[1]
    y_of_right = interp_between_layers(
        x_of_right,
        y_of_bottom_layer[is_right],
        y_of_top_layer[is_right],
        reverse=reverse,
    )

    if top_limits[0] > bottom_limits[0]:
        x_of_left = x_of_left[::-1]
        y_of_left = y_of_left[::-1]
    if top_limits[-1] < bottom_limits[-1]:
        x_of_right = x_of_right[::-1]
        y_of_right = y_of_right[::-1]

    return (
        np.r_[x_of_top[::-1], x_of_left, x_of_bottom, x_of_right],
        np.r_[y_of_top[::-1], y_of_left, y_of_bottom, y_of_right],
    )


def interp_between_layers(x, y_of_bottom, y_of_top, kind="linear", reverse=False):
    x = np.asarray(x)
    y_of_top, y_of_bottom = np.asarray(y_of_top), np.asarray(y_of_bottom)

    assert len(y_of_top) == len(y_of_bottom) == len(x)

    if len(x) == 0:
        return np.array([], dtype=float)
    elif len(x) == 1:
        return (y_of_top + y_of_bottom) * 0.5

    if reverse:
        dy = (y_of_top - y_of_bottom) * interp1d((x[0], x[-1]), (1.0, 0.0), kind=kind)(
            x
        )
    else:
        dy = (y_of_top - y_of_bottom) * interp1d((x[0], x[-1]), (0.0, 1.0), kind=kind)(
            x
        )

    return y_of_bottom + dy
