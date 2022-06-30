.. image:: https://raw.githubusercontent.com/sequence-dev/sequence/develop/docs/_static/sequence-logo-text-lowercase.png
  :target: https://sequence.readthedocs.io/en/develop/?badge=develop
  :alt: Sequence
  :align: center
  
.. raw:: html

  <h2 align="center">Sequence-stratigraphic modeling with Python</h2>

-----------

.. image:: https://github.com/sequence-dev/sequence/workflows/Build/Test%20CI/badge.svg


.. image:: https://github.com/sequence-dev/sequence/workflows/Flake8/badge.svg


.. image:: https://github.com/sequence-dev/sequence/workflows/Black/badge.svg


.. image:: https://github.com/sequence-dev/sequence/workflows/Documentation/badge.svg


.. image:: https://readthedocs.org/projects/sequence/badge/?version=develop
  :target: https://sequence.readthedocs.io/en/develop/?badge=develop
  :alt: Documentation Status

-----------

About
-----

*Sequence* is a modular 2D (i.e., profile) sequence stratigraphic model
that is written in Python and implemented within the Landlab framework.
Sequence represents time-averaged fluvial and marine sediment transport
via differential equations. The modular code includes components to deal
with sea level changes, sediment compaction, local or flexural isostasy,
and tectonic subsidence and uplift.

-----------

`Read the documentation on ReadTheDocs! <https://sequence.readthedocs.io/en/develop/>`_

-----------

Requirements
------------

*Sequence* requires Python 3.

Apart from Python, *Sequence* has a number of other requirements, all of which
can be obtained through either *pip* or *conda*, that will be automatically
installed when you install *Sequence*.

To see a full listing of the requirements, have a look at the project's
*requirements.txt* file.

If you are a developer of *Sequence* you will also want to install
additional dependencies for running *Sequence*'s tests to make sure
that things are working as they should. These dependencies are listed
in *requirements-testing.txt*.

Installation
------------

To install *Sequence*, first create a new environment in
which *Sequence* will be installed. This, although not necessary, will
isolate the installation so that there won't be conflicts with your
base *Python* installation. This can be done with *conda* as::

  $ conda create -n sequence python=3
  $ conda activate sequence

Stable Release
``````````````

*Sequence*, and its dependencies, can be installed either with *pip*
or *conda*. Using *pip*::

    $ pip install sequence-model

Using *conda*::

    $ conda install sequence-model -c conda-forge

From Source
```````````

After downloading the *Sequence* source code, run the following from
*Sequence*'s top-level folder (the one that contains *setup.py*) to
install *Sequence* into the current environment::

  $ pip install -e .


Usage
-----

*Sequence* is both a command-line program and a Python package that provides an
application programming interface.

The command-line program, *sequence*, provides several sub-commands for setting
up *sequence* input files, running *sequence*, and plotting output (you can use
the ``--help`` option to get help for the available subcommands). The four
subcommands are the following:

* `generate`: Generate example input files.
* `setup`: Setup a folder of input files for a simulation.
* `run`: Run a simulation.
* `plot`: Plot a sequence output file.

Example
```````

The following commands create an example set of input files, runs *sesquence*,
and then plots the output.

.. code:: bash

  $ mkdir example && cd example
  $ sequence setup
  $ sequence run
  $ sequence plot

.. image:: https://github.com/sequence-dev/sequence/raw/develop/docs/_static/sequence.png

The above can also be run through Python,

.. code:: python

  >>> from sequence import Sequence, SequenceModelGrid
  >>> grid = SequenceModelGrid(100, spacing=1000.0)
  >>> grid.at_node["topographic__elevation"] = -0.001 * grid.x_of_node + 20.0
  
  >>> sequence = Sequence()
  >>> sequence.run()
  >>> sequence.plot()

The ``Sequence`` class provides functionality not available to the command-line
program. For example, you are able to run a simulation through time while dynamically
changing parameters.

  >>> from sequence import Sequence, SequenceModelGrid  
  >>> grid = SequenceModelGrid(100, spacing=1000.0)
  >>> grid.at_node["topographic__elevation"] = -0.001 * grid.x_of_node + 20.0
  
  >>> process = default_process_queue()
  >>> sequence = Sequence(
  ...   grid,
  ...   components=[
  ...     process["sea_level"],
  ...     process["compaction"],
  ...     process["submarine_diffusion"],
  ...     process["fluvial"],
  ...     process["flexure"],
  ...     process["shoreline"],
  ...   ]
  ... )  
  
  >>> sequence.run(until=300000.0, dt=100.0)
  >>> sequence.submarine_diffusion.sediment_load *= 2.0
  >>> sequence.run(until=600000.0, dt=100.0)
  >>> sequence.plot()


Input Files
-----------

Sequence Parameter File
```````````````````````

The main *Sequence* input file is a *toml*-formatted (or, optionally, *yaml*)
text file that lists parameter values for the various components. Running
the following will print a sample *Sequence* parameter file::

  $ sequence generate sequence.toml

Following is the generated input file,

.. code:: toml

    [sequence]
    _time = 0.0

    [sequence.grid]
    shape = [3, 100]
    xy_spacing = 100.0
    xy_of_lower_left = [0.0, 0.0]

    [sequence.grid.bc]
    top = "closed"
    bottom = "closed"

    [sequence.clock]
    start = 0.0
    stop = 20000.0
    step = 100.0

    [sequence.output]
    interval = 10
    filepath = "sequence.nc"
    clobber = true
    rows = [1]
    fields = ["sediment_deposit__thickness"]

    [sequence.submarine_diffusion]
    plain_slope = 0.0008
    wave_base = 60.0
    shoreface_height = 15.0
    alpha = 0.0005
    shelf_slope = 0.001
    sediment_load = 3.0
    load_sealevel = 0.0
    basin_width = 500000.0

    [sequence.sea_level]
    amplitude = 10.0
    wave_length = 1000.0
    phase = 0.0
    linear = 0.0

    [sequence.subsidence]
    filepath = "subsidence.csv"

    [sequence.flexure]
    method = "flexure"
    rho_mantle = 3300.0
    isostasytime = 0

    [sequence.sediments]
    layers = 2
    sand = 1.0
    mud = 0.006
    sand_density = 2650.0
    mud_density = 2720.0
    sand_frac = 0.5
    hemipelagic = 0.0

    [sequence.bathymetry]
    filepath = "bathymetry.csv"
    kind = "linear"

    [sequence.compaction]
    c = 5e-08
    porosity_max = 0.5
    porosity_min = 0.01
    rho_grain = 2650.0
    rho_void = 1000.0


.. _The grid section:


The grid section
~~~~~~~~~~~~~~~~

You define the grid on which *Sequence* will run in the `sequence.grid` section.
An example gid section looks like,

.. code::

    [sequence.grid]
    shape = [3, 500]
    xy_spacing = 100.0
    xy_of_lower_left = [0.0, 0.0]

In this case we have a grid that, if we are looking down on it from above, consists
of three rows and 500 columns (the *shape* parameter). *Sequence* is a 1D model and
uses only the middle row of nodes so you will never want to change the number of
rows from a value of 3. You can play with the number of columns though—this is the
number of stacks of sediment you have along your profile.

The *xy_spacing* parameter is the width of each of your sediment stacks in meters.
Thus, the length of you domain is the product of the number of columns with
the spacing (that is, for this example, 500 * 100 m or 50 km).

The *xy_of_lower_left* parameter gives the position of the lower-left node of
you grid. In *Sequence*, this parameter is not used.

The output section
~~~~~~~~~~~~~~~~~~

You can define when and what *Sequence* will save to a NetCDF file while it is running.
Here is an example output section,

.. code::

    [sequence.output]
    interval = 10
    filepath = "sequence.nc"
    clobber = true
    rows = [1]
    fields = ["sediment_deposit__thickness"]

The *interval* parameter is the interval, in time steps (**not** years), that
*Sequence* will write data to a file. Other parameters, which you will
probably not want to change, are:

* *filepath*: the name of the output NetCDF file to which output is written.
* *clobber*: what *Sequence* should do if the output file exists. If `true`,
  an existing file will be overwritten, otherwise *Sequence* will raise an
  error.
* *rows*: as described in `The grid section`_ a *Sequence* grid consists
  of three rows. The *rows* parameter specifies which of these rows to
  write to the output file.
* *fields*: a list of names of quantities you would like *Sequence* to include
  in the NetCDF file. *Sequence* keeps track of many quantities, most of which
  you probably aren't interested in and so this parameter limits the number
  of quantities written as output.

.. _Time-varying parameters:

Time-varying parameters
~~~~~~~~~~~~~~~~~~~~~~~

Some parameters in the *sequence.toml* are able to vary with time. In the above
example all of the variables are help constant. To have a parameter change
at some time during the model simulation, you can add a new section, which will
be read at the given time. For example, if the following section is added
after the section from the previous example,

.. code:: toml

    [sequence]
    _time = 100

    [sequence.subsidence]
    filepath = "subsidence-100.csv"

at time 100, a new subsidence file will be read and used until the end of the
simulation.


Bathymetry File
```````````````

The *Sequence* bathymetry file defines initial sea-floor elevations in
a two-column CSV file. A sample bathymetry file can be obtained with::

  $ sequence generate bathymetry.csv
  # X [m], Elevation [m]
  0.0,20.0
  100000.0,-80.0

Elevations are linearly interpolated between the points given in the file
as necessary.

Sea-Level File
``````````````

The *Sequence* sea-level file defines sea-level elevations with simulation
time. It consists of two (comma separated) columns of time and sea-level
elevation, respectively. For a sample sea-level file::

  $ sequence generate sealevel.csv
  # Time [y], Sea-Level Elevation [m]
  0.0,0.0
  200000.0,-10.0

Subsidence File
```````````````

The *Sequence* subsidence file defines the subsidence rates of points along
the profile. It consists of two (comma separated) columns that give position
along the profile and subsidence rate, respectively. For a sample subsidence
file::

  $ sequence generate subsidence.csv
  # X [y], Subsidence Rate [m / y]
  0.0,0.0
  30000.0,0.0
  35000.0,0.0
  50000.0,0.0
  100000.0,0.0

.. note::

  Positive rates represent **uplift**.

If you would like your subsidence profile to change with time, see the
section above, `Time-varying parameters`_.

Output File
-----------

The output file of *Sequence* is a netcdf-formatted file that records the
generated stratigraphy. Output parameters are controlled through the
*output* section of the parameter file.

Examples
--------

To run a simulation using the sample input files described above, you first
need to create a set of sample files::

  $ mkdir example
  $ cd example && sequence setup
  example

You can now run the simulation (from within the *example* folder)::

  $ sequence run

Plotting output
---------------

The *Sequence* program provides a command-line utility for generating a quick
plot of *Sequence* output from a NetCDF file named *sequence.nc*. As an
example,

.. code::

    $ sequence plot

If you would like to change some aspects of the generated plot, you can add
a *sequence.plot* section to your *sequence.toml* file. For example, here
is a *sequence.plot* section,

.. code:: toml

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

The *color_* parameters give colors of various pieces of the plot as
fractions of [*red*, *green*, *blue*]. Some other parameters, which may
not be obvious,

* *layer_start*: the first layer to plot
* *layer_stop*: the last layer to plot (a value of -1 means stop at the last layer)
* *n_layers*: the number of layers to plot.

