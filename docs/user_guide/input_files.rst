Input Files
-----------

.. start-input-files

Sequence Parameter File
```````````````````````

The main *Sequence* input file is a *toml*-formatted (or, optionally, *yaml*)
text file that lists parameter values for the various components. Running
the following will print a sample *Sequence* parameter file:

.. code:: bash

  sequence generate sequence.toml

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

.. code:: toml

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

.. code:: toml

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
a two-column CSV file. A sample bathymetry file can be obtained with:

.. code:: bash

  sequence generate bathymetry.csv

.. code::

  # X [m], Elevation [m]
  0.0,20.0
  100000.0,-80.0

Elevations are linearly interpolated between the points given in the file
as necessary.

Sea-Level File
``````````````

The *Sequence* sea-level file defines sea-level elevations with simulation
time. It consists of two (comma separated) columns of time and sea-level
elevation, respectively. For a sample sea-level file:

.. code:: bash

  sequence generate sealevel.csv

.. code::

  # Time [y], Sea-Level Elevation [m]
  0.0,0.0
  200000.0,-10.0

Subsidence File
```````````````

The *Sequence* subsidence file defines the subsidence rates of points along
the profile. It consists of two (comma separated) columns that give position
along the profile and subsidence rate, respectively. For a sample subsidence
file:

.. code:: bash

  sequence generate subsidence.csv

.. code::

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

.. end-input-files
