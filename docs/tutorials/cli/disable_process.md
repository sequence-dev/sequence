# Disabling Processes

Depending on the simulation you want to run, you may wish to
turn certain processes on or off. For example, in your particular
case maybe a processes contributes little to the final outcome
but yet takes a significant portion amount of time to run, which
increases your model's overall run time.

The ``[sesquence]`` section of the *sequence.toml* input file
controls the processes that are active for a given situation.

```{literalinclude} ../../generated/_sequence.toml
:start-at: "[sequence]"
:end-before: "[sequence.grid]"
```

The ``processes`` key is a list of named processes that are active
and also the order they are run in for each time step. To disable
the *compaction*, for example, you only need to remove it from the
list.

```toml
[sequence]
_time = 0.0
processes = ["sea_level", "subsidence", "submarine_diffusion", "fluvial", "flexure"]
```
