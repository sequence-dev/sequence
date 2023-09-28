# Modifing the Sea-Level Curve

In this tutorial, we'll modify the default simulation to use a new
sea-level curve.

## Setup

As before, we create a new folder to hold our input files and create
a set of default files.

```bash
mkdir sealevel-example && cd sealevel-example
sequence setup
```

If we look at the default sea level section of the main input file,
we see that it defines a sinusoidal curve,

```{literalinclude} /generated/_sequence.toml
:language: toml
:start-at: "[sequence.sea_level]"
:end-before: "[sequence.subsidence]"
```

To change *Sequence* to instead read sea level values from a file,
we replace this section with the following,

```toml
[sequence.sea_level]
filepath = sealevel.csv
```

With this configuration, *Sequence* will read sea level values from this
file every time setup (interpolating between points, as necessary).

```{literalinclude} /generated/_sealevel.csv
:language: python
```

```{note}
If this sea-level curve is not defined for all values in your simulation
as defined in `[sequence.clock]` section of you main input file,
*Sequence* will extrapolate using the nearest value of the defined curve.

:::{literalinclude} /generated/_sequence.toml
:language: toml
:start-at: "[sequence.clock]"
:end-at: "step = 100.0"
```
:::

