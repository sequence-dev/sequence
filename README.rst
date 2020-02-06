========
sequence
========


.. image:: https://img.shields.io/travis/sequence-dev/sequence.svg
        :target: https://travis-ci.org/sequence-dev/sequence

.. image:: https://readthedocs.org/projects/sequence/badge/?version=latest
        :target: https://sequence.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/sequence-dev/sequence/shield.svg
     :target: https://pyup.io/repos/github/sequence-dev/sequence/
     :alt: Updates



Python version of the Steckler Sequence model


Requirements
------------

*Sequence* has a number of requirements, all of which can be installed with
either *pip* or *conda*, the main one being *Python 3*. The rest are listed
in *requirements.txt*.

If you are a developer of *Sequence* you will also want to install
additional dependencies for running *Sequence*'s tests to make sure
that things are working as they should. These dependencies are listed
in *requirements-testing.txt*.

Installation Instructions
-------------------------

To install *Sequence* from source, first create a new environment in
which *Sequence* will be installed. This, although not necessary, will
isolate the installation so that there won't be conflicts with your
base *Python* installation. This can be done with *conda* as::

  $ conda create -n sequence python=3
  $ conda activate sequence

To install *Sequence* into this environment::

  $ pip install -e .

Input Files
-----------

Parameter File
++++++++++++++

The main *Sequence* input file is a yaml-formatted text file that lists
parameter values for the various components. Running the following will
print an sample *Sequence* parameter file::

  $ sequence-sample params

Bathymetry File
+++++++++++++++

The *Sequence* bathymetry file defines initial sea-floor elevations in
a two-column CSV file. A sample bathymetry file can be obtained with::

  $ sequence show bathymetry
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

  $ sequence show sealevel
  # Time [y], Sea-Level Elevation [m]
  0.0,0.0
  200000.0,-10.0

Subsidence File
+++++++++++++++

The *Sequence* subsidence file defines the subsidence rates of points along
the profile. It consists of two (comma separated) columns that give position
along the profile and subsidence rate, respectively. For a sample subsidence
file::

  $ sequence show subsidence
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
generated stratigraphy. Output parameters is controlled through the
*output* section of the parameter file.

Examples
--------

To run a simulation using the sample input files described above, you first
need to create a set of sample files::

  $ sequence setup example
  example/sequence.yaml

You can now run the simulation::

  $ sequence example/sequence.yaml
