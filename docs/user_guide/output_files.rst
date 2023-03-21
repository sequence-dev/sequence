Output File
-----------

The output file of *Sequence* is a netcdf-formatted file that records the
generated stratigraphy. Output parameters are controlled through the
*output* section of the parameter file.

Examples
--------

To run a simulation using the sample input files described above, you first
need to create a set of sample files:

.. code:: bash

  mkdir example
  cd example && sequence setup
  example

You can now run the simulation (from within the *example* folder):

.. code:: bash

  sequence run
