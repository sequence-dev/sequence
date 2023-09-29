(sequence-input-files-ref)=
# Input Files

<!-- start-input-files -->


(the-parameter-file)=

## Sequence Parameter File

The main *Sequence* input file is a *toml*-formatted (or, optionally, *yaml*)
text file that lists parameter values for the various components. Running
the following will print a sample *Sequence* parameter file:

```bash
sequence generate sequence.toml
```

Following is the generated input file,

```{literalinclude} /generated/_sequence.toml
:language: toml
```

### The sequence section

This is the base section for the *Sequence* model. For a description of the
*\_time* parameter, see the [Time-varying parameters](time-varying-parameters) section.

The *processes* parameter specifies what processes are to be run in the
simulation. Each of the processes in this list should also have a corresponding
section in the file. This list also defines the order in which *Sequence* will
run the processes within each time step.

```toml
_time = 0.0
processes = [
    "sea_level",
    "subsidence",
    "compaction",
    "submarine_diffusion",
    "fluvial",
    "flexure",
]
```

(the-grid-section)=

### The grid section

You define the grid on which *Sequence* will run in the `sequence.grid` section.
An example grid section looks like,

```toml
[sequence.grid]
n_cols = 100
spacing = 1000.0
```

In this case we have a grid that represents a 1D profile that consists of
500 columns (i.e. vertical stacks) of sediment (the *n_cols* parameter).

The *spacing* parameter is the width of each of your sediment stacks in meters.
Thus, the length of you domain is the product of the number of columns with
the spacing (that is, for this example, 500 * 100 m or 50 km).

(the-output-section)=

### The output section

You can define when and what *Sequence* will save to a NetCDF file while it is running.
Here is an example output section,

```toml
[sequence.output]
interval = 10
filepath = "sequence.nc"
clobber = true
rows = [1]
fields = ["sediment_deposit__thickness"]
```

The *interval* parameter is the interval, in time steps (**not** years), that
*Sequence* will write data to a file. Other parameters, which you will
probably not want to change, are:

- *filepath*: the name of the output NetCDF file to which output is written.
- *clobber*: what *Sequence* should do if the output file exists. If `true`,
  an existing file will be overwritten, otherwise *Sequence* will raise an
  error.
- *rows*: as described in [The grid section](the-grid-section) a *Sequence* grid consists
  of three rows. The *rows* parameter specifies which of these rows to
  write to the output file.
- *fields*: a list of names of quantities you would like *Sequence* to include
  in the NetCDF file. *Sequence* keeps track of many quantities, most of which
  you probably aren't interested in and so this parameter limits the number
  of quantities written as output.

(time-varying-parameters)=

### Time-varying parameters

Some parameters in the *sequence.toml* are able to vary with time. In the above
example all of the variables are help constant. To have a parameter change
at some time during the model simulation, you can add a new section, which will
be read at the given time. For example, if the following section is added
after the section from the previous example,

```toml
[sequence]
_time = 100

[sequence.subsidence]
filepath = "subsidence-100.csv"
```

at time 100, a new subsidence file will be read and used until the end of the
simulation.

## Bathymetry File

The *Sequence* bathymetry file defines initial sea-floor elevations in
a two-column CSV file. A sample bathymetry file can be obtained with:

```bash
sequence generate bathymetry.csv
```

```{literalinclude} /generated/_bathymetry.csv
:language: python
```

Elevations are linearly interpolated between the points given in the file
as necessary.

## Sea-Level File

The *Sequence* sea-level file defines sea-level elevations with simulation
time. It consists of two (comma separated) columns of time and sea-level
elevation, respectively. For a sample sea-level file:

```bash
sequence generate sealevel.csv
```

```{literalinclude} /generated/_sealevel.csv
:language: python
```

## Subsidence File

The *Sequence* subsidence file defines the subsidence rates of points along
the profile. It consists of two (comma separated) columns that give position
along the profile and subsidence rate, respectively. For a sample subsidence
file:

```bash
sequence generate subsidence.csv
```

```{literalinclude} /generated/_subsidence.csv
:language: python
```

:::{note}
Positive rates represent **uplift**.
:::

If you would like your subsidence profile to change with time, see the
section above, [Time-varying parameters](time-varying-parameters).

<!-- end-input-files -->
