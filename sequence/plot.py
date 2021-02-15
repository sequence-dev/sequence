import pathlib
from functools import partial
from itertools import tee

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.patches import Patch


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def plot_strat(
    filename,
    color_water=(0.8, 1.0, 1.0),
    color_land=(0.8, 1.0, 0.8),
    color_shoreface=(0.8, 0.8, 0.0),
    color_shelf=(0.75, 0.5, 0.5),
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
    filename = pathlib.Path(filename)

    legend_item = partial(Patch, edgecolor="k", linewidth=0.5)

    with xr.open_dataset(filename) as ds:
        n_times = ds.dims["time"]

        thickness_at_layer = ds["at_layer:thickness"][:n_times]
        x_of_shore = ds["at_grid:x_of_shore"].data.squeeze()
        x_of_shelf_edge = ds["at_grid:x_of_shelf_edge"].data.squeeze()
        x_of_stack = ds["x_of_cell"].data.squeeze()
        bedrock = ds["at_node:bedrock_surface__elevation"].data.squeeze()

        elevation_at_layer = bedrock[-1, 1:-1] + np.cumsum(thickness_at_layer, axis=0)

    if n_layers:
        layer_step = int(len(elevation_at_layer) / n_layers)
        plt.plot(
            x_of_stack,
            elevation_at_layer[layer_start:layer_stop:layer_step].T,
            color=layer_line_color,
            linewidth=layer_line_width,
        )

    water = x_of_stack > x_of_shore[-1]
    x_water = x_of_stack[water]
    y_water = elevation_at_layer[-1, water]

    plt.fill_between(
        x_water, y_water, np.full_like(x_water, y_water[0]), fc=color_water
    )
    plt.plot([x_water[0], x_water[-1]], [y_water[0], y_water[0]], color="k")

    stack_of_shore = np.searchsorted(x_of_stack, x_of_shore)
    land_top = x_of_stack <= x_of_shore[-1]
    land_bottom = x_of_stack <= x_of_shore[0]
    plt.fill(
        np.r_[x_of_shore, x_of_stack[land_top][::-1], x_of_stack[land_bottom]],
        np.r_[
            elevation_at_layer.data[np.arange(n_times), stack_of_shore],
            elevation_at_layer[-1, land_top][::-1],
            elevation_at_layer[0, land_bottom],
        ],
        fc=color_land,
    )

    stack_of_shelf_edge = np.searchsorted(x_of_stack, x_of_shelf_edge)
    shoreface_top = (x_of_stack > x_of_shore[-1]) & (x_of_stack <= x_of_shelf_edge[-1])
    shoreface_bottom = (x_of_stack > x_of_shore[0]) & (x_of_stack <= x_of_shelf_edge[0])
    plt.fill(
        np.r_[
            x_of_shelf_edge,
            x_of_stack[shoreface_top][::-1],
            x_of_shore[::-1],
            x_of_stack[shoreface_bottom],
        ],
        np.r_[
            elevation_at_layer.data[np.arange(n_times), stack_of_shelf_edge],
            elevation_at_layer[-1, shoreface_top][::-1],
            elevation_at_layer.data[np.arange(n_times), stack_of_shore][::-1],
            elevation_at_layer[0, shoreface_bottom],
        ],
        fc=color_shoreface,
    )

    shelf_top = x_of_stack > x_of_shelf_edge[-1]
    shelf_bottom = x_of_stack > x_of_shelf_edge[0]
    plt.fill(
        np.r_[
            x_of_stack[shelf_top][::-1],
            x_of_shelf_edge[::-1],
            x_of_stack[shelf_bottom],
        ],
        np.r_[
            elevation_at_layer[-1, shelf_top][::-1],
            elevation_at_layer.data[np.arange(n_times), stack_of_shelf_edge][::-1],
            elevation_at_layer[0, shelf_bottom],
        ],
        fc=color_shelf,
    )

    if legend_location:
        legend = [
            legend_item(label="Land", fc=color_land),
            legend_item(label="Shoreface", fc=color_shoreface),
            legend_item(label="Shelf", fc=color_shelf),
        ]

        plt.legend(handles=legend, loc=legend_location)

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title.format(filename=filename.name))
    plt.xlim((x_of_stack[0], x_of_stack[-1]))

    plt.show()
