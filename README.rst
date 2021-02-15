sequence: Sequence-stratigraphic modeling with Python
=====================================================

.. image:: https://github.com/sequence-dev/sequence/workflows/Build/Test%20CI/badge.svg

.. image:: https://github.com/sequence-dev/sequence/workflows/Flake8/badge.svg

.. image:: https://github.com/sequence-dev/sequence/workflows/Black/badge.svg

.. image:: https://github.com/sequence-dev/sequence/workflows/Documentation/badge.svg

.. image:: https://readthedocs.org/projects/sequence/badge/?version=develop
  :target: https://sequence.readthedocs.io/en/develop/?badge=develop
  :alt: Documentation Status


About
-----

*Sequence* is a modular 2D (i.e., profile) sequence stratigraphic model
that is written in Python and implemented within the Landlab framework.
Sequence represents time-averaged fluvial and marine sediment transport
via differential equations. The modular code includes components to deal
with sea level changes, sediment compaction, local or flexural isostasy,
and tectonic subsidence and uplift.

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
++++++++++++++

*Sequence*, and its dependencies, can be installed either with *pip*
or *conda*. Using *pip*::

    $ pip install sequence

Using *conda*::

    $ conda install sequence -c conda-forge

From Source
+++++++++++

After downloading the *Sequence* source code, run the following from
*Sequence*'s top-level folder (the one that contains *setup.py*) to
install *Sequence* into the current environment::

  $ pip install -e .

Input Files
-----------

Sequence Parameter File
+++++++++++++++++++++++

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
+++++++++++++++

The *Sequence* bathymetry file defines initial sea-floor elevations in
a two-column CSV file. A sample bathymetry file can be obtained with::

  $ sequence generate bathymetry.csv
  # X [m], Elevation [m]
  0.0,20.0
  100000.0,-80.0

Elevations are linearly interpolated between the points given in the file
as necessary.

Sea-Level File
++++++++++++++

The *Sequence* sea-level file defines sea-level elevations with simulation
time. It consists of two (comma separated) columns of time and sea-level
elevation, respectively. For a sample sea-level file::

  $ sequence generate sealevel.csv
  # Time [y], Sea-Level Elevation [m]
  0.0,0.0
  200000.0,-10.0

Subsidence File
+++++++++++++++

The *Sequence* subsidence file defines the subsidence rates of points along
the profile. It consists of two (comma separated) columns that give position
along the profile and subsidence rate, respectively. For a sample subsidence
file::

  $ sequence generate subsidence.csv
  # Time [y], Subsidence Rate [m / y]
  0.0,0.0
  30000.0,0.0
  35000.0,0.0
  50000.0,0.0
  100000.0,0.0

Note that positive rates represent uplift.

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
