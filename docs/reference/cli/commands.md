(sequence-commands-ref)=
# Commands

The command-line program, *sequence*, provides several sub-commands for setting
up *sequence* input files, running *sequence*, and plotting output (you can use
the `--help` option to get help for the available subcommands). The four
subcommands are the following:

- [generate](#sequence-generate): Generate example input files.
- [setup](#sequence-setup): Setup a folder of input files for a simulation.
- [run](#sequence-run): Run a simulation.
- [plot](#sequence-plot): Plot a sequence output file.


```{eval-rst}
.. click:: sequence.cli:sequence
	:prog: sequence
	:nested: full
```
