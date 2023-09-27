# Plotting output

<!-- start-plotting -->

The *Sequence* program provides a command-line utility for generating a quick
plot of *Sequence* output from a NetCDF file named *sequence.nc*. As an
example,

```bash
sequence plot
```

If you would like to change some aspects of the generated plot, you can add
a *sequence.plot* section to your *sequence.toml* file. For example, here
is a *sequence.plot* section,

```toml
[sequence.plot]
color_water = [0.8, 1.0, 1.0]
color_land = [0.8, 1.0, 0.8]
color_shoreface = [0.8, 0.8, 0.0]
color_shelf = [0.75, 0.5, 0.5]
layer_line_color = "k"
layer_line_width = 0.5
title = "{filename}"
x_label = "Distance (m)"
y_label = "Elevation (m)"
legend_location = "upper right"
layer_start=0
layer_stop = -1
n_layers = 5
```

The *color\_* parameters give colors of various pieces of the plot as
fractions of \[*red*, *green*, *blue*\]. Some other parameters, which may
not be obvious,

- *layer_start*: the first layer to plot
- *layer_stop*: the last layer to plot (a value of -1 means stop at the last layer)
- *n_layers*: the number of layers to plot.

<!-- end-plotting -->
