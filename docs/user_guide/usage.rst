Usage
-----

.. start-usage

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

  mkdir example && cd example
  sequence setup
  sequence run
  sequence plot

.. image:: https://github.com/sequence-dev/sequence/raw/develop/docs/_static/sequence.png

The above can also be run through Python,

.. code:: pycon

  >>> from sequence import Sequence, SequenceModelGrid
  >>> grid = SequenceModelGrid(100, spacing=1000.0)
  >>> grid.at_node["topographic__elevation"] = -0.001 * grid.x_of_node + 20.0

  >>> sequence = Sequence()
  >>> sequence.run()
  >>> sequence.plot()

The ``Sequence`` class provides functionality not available to the command-line
program. For example, you are able to run a simulation through time while dynamically
changing parameters.

.. code:: pycon

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

.. end-usage
