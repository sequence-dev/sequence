(tutorials-section)=
# Quickstart

Running a *Sequence* simulation involves three steps: setup,
execution, visualization. Each of the  steps correspond to
a separate subcommand to the ``sequence`` program. The
the *Sequence* command line interface [reference](sequence-commands-ref)
gives a complete list of options for each of thes subcommands.


## Set up a new simulation

For a full description of all the *Sequence* input files, please
have a look at the [input file reference](sequence-input-files-ref).

Input files include a primary input file (``sequence.toml``) where
you can set input parameter for each of *Sequence*'s process components
(sea level, subsidence, compaction, etc.), a sea-level file (``sea_level.csv``),
and a subsidence file (``subsidence.csv``).

To get started, we'll create a set of input files with some default
settings. This can be done with the ``setup`` subcommand.

```bash
mkdir my-example && cd my-example
sequence setup
```

Your previously empty folder now contains the above files. Feel
free to open any of them up with a text editor and have a look.


## Run the simulation

Once you have created all of your input files, you are ready to run the
model. This is done with the ``run`` subcommand by executing the
following command from within the folder that contains your input files.

```bash
sequence run
```

## Plot the output

Once the run has completed, the will be a new file, ``sequence.nc``
that contains all of the output. This file contains, among other
things, layer thicknesses, layer compositions, and shoreline positions.
You can use the ``plot`` subcommand to create a simple plot of the
output.

```bash
sequence plot sequence.nc
```
