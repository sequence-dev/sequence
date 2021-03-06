import os
import pathlib
import re
from functools import partial
from io import StringIO

import click
import numpy as np
import tomlkit as toml
import yaml

from .input_reader import TimeVaryingConfig
from .raster_model import load_model_params
from .sequence_model import SequenceModel

out = partial(click.secho, bold=True, err=True)
err = partial(click.secho, fg="red", err=True)


def _contents_of_input_file(infile, set):
    params = load_model_params(defaults=SequenceModel.DEFAULT_PARAMS, dotted_params=set)

    def as_csv(data, header=None):
        with StringIO() as fp:
            np.savetxt(fp, data, header=header, delimiter=",", fmt="%.1f")
            contents = fp.getvalue()
        return contents

    contents = {
        "sequence.yaml": yaml.dump(params, default_flow_style=False),
        "sequence.toml": toml.dumps(dict(sequence=dict(_time=0.0, **params))),
        "bathymetry.csv": as_csv(
            [[0.0, 20.0], [100000.0, -80.0]], header="X [m], Elevation [m]"
        ),
        "sealevel.csv": as_csv(
            [[0.0, 0.0], [200000, -10]], header="Time [y], Sea-Level Elevation [m]"
        ),
        "subsidence.csv": as_csv(
            [[0.0, 0], [30000.0, 0], [35000.0, 0], [50000.0, 0], [100000.0, 0]],
            header="Time [y], Subsidence Rate [m / y]",
        ),
    }
    for section, section_params in params.items():
        contents[f"sequence.{section}"] = yaml.dump(
            section_params, default_flow_style=False
        )

    return contents[infile]


def _time_from_filename(name):
    """Parse a time stamp from a file name.

    Parameters
    ----------
    name : str
        File name that contains a time stamp.

    Returns
    -------
    int
        Time stamp from the file name, or ``None`` if no time stamp exists.

    Examples
    --------
    >>> from sequence.cli import _time_from_filename
    >>> _time_from_filename("subsidence-0010.csv")
    10
    >>> _time_from_filename("subsidence.csv") is None
    True
    """
    name = pathlib.Path(name).name

    int_parts = [int(t) for t in re.split("([0-9]+)", name) if t.isdigit()]

    try:
        return int_parts[0]
    except IndexError:
        return None


def _find_config_files(pathname):
    """Find all of the time-varying config files for a simulation.

    Parameters
    ----------
    pathname : str
        Path to a folder that contains input files for a simulation.

    Returns
    -------
    list of tuple
        List of tuples of time stamp and file name.
    """
    pathname = pathlib.Path(pathname)

    toml_files = list(pathname.glob("sequence*.toml"))
    yaml_files = list(pathname.glob("sequence*.yaml"))

    config_files = toml_files if toml_files else yaml_files

    items = []
    for index, config_file in enumerate(config_files):
        time = _time_from_filename(config_file)
        if time is None:
            time = index
        items.append((time, str(config_file)))

    return zip(*sorted(items))


@click.group(chain=True)
@click.version_option()
@click.option(
    "--cd",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="chage to directory, then execute",
)
def sequence(cd) -> None:
    """The Steckler Sequence model.

    \b
    Examples:

      Create a folder with example input files,

        $ mkdir sequence-example && cd sequence-example
        $ sequence setup

      Run a simulation using the examples input files,

        $ sequence run
    """
    os.chdir(cd)


@sequence.command()
@click.option("--dry-run", is_flag=True, help="do not actually run the model")
@click.option(
    "-v", "--verbose", is_flag=True, help="Also emit status messages to stderr."
)
@click.option(
    "--with-citations", is_flag=True, help="print citations for components used"
)
def run(with_citations, verbose, dry_run):
    """Run a simulation."""
    run_dir = pathlib.Path.cwd()

    times, names = _find_config_files(".")
    params = TimeVaryingConfig.from_files(names, times=times)

    if verbose:
        out(params.dump())

    model = SequenceModel(**params.as_dict())

    if with_citations:
        from landlab.core.model_component import registry

        out("👇👇👇These are the citations to use👇👇👇")
        out(registry.format_citations())
        out("👆👆👆These are the citations to use👆👆👆")

    if not dry_run:
        try:
            with click.progressbar(
                length=int(model.clock.stop // model.clock.step),
                label=" ".join(["🚀", str(run_dir)]),
            ) as bar:
                while 1:
                    model.run_one_step()
                    model.set_params(params.update(1))
                    bar.update(1)
        except StopIteration:
            pass

        out("💥 Finished! 💥")
        out("Output written to {0}".format(run_dir))
    else:
        out("Nothing to do. 😴")


@sequence.command()
@click.argument(
    "infile",
    type=click.Choice(
        sorted(
            ["bathymetry.csv", "sequence.yaml", "sequence.toml", "sealevel.csv", "subsidence.csv"]
            # ["bathymetry.csv", "sequence.yaml", "sequence.output", "sealevel.csv", "subsidence.csv"]
            # + [f"sequence.{name}" for name in SequenceModel.DEFAULT_PARAMS]
        )
    ),
)
@click.option("--set", metavar="KEY=VALUE", multiple=True, help="Set model parameters")
def generate(infile, set):
    """Generate example input files."""
    print(_contents_of_input_file(infile, set))


@sequence.command()
@click.option("--set", multiple=True, help="Set model parameters")
def setup(set):
    """Setup a folder of input files for a simulation."""
    # folder = pathlib.Path(destination)
    folder = pathlib.Path.cwd()

    files = [
        pathlib.Path(fname)
        for fname in [
            "bathymetry.csv",
            "sequence.toml",
            "sealevel.csv",
            "subsidence.csv",
        ]
    ]

    existing_files = [name for name in files if name.exists()]
    if existing_files:
        for name in existing_files:
            err(
                f"{name}: File exists. Either remove and then rerun or choose a different destination folder"
            )
    else:
        for fname in files:
            with open(folder / fname, "w") as fp:
                print(_contents_of_input_file(str(fname), set), file=fp)
        print(str(folder))

    if existing_files:
        raise click.Abort()
