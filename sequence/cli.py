import os
import pathlib
import sys
from io import StringIO

import click
import numpy as np
import yaml
from landlab.core import load_params

from .raster_model import load_model_params
from .sequence_model import SequenceModel


def _contents_of_input_file(infile, set):
    params = load_model_params(defaults=SequenceModel.DEFAULT_PARAMS, dotted_params=set)

    def as_csv(data, header=None):
        with StringIO() as fp:
            np.savetxt(fp, data, header=header, delimiter=",", fmt="%.1f")
            contents = fp.getvalue()
        return contents

    contents = {
        "config": yaml.dump(params, default_flow_style=False),
        "bathymetry": as_csv(
            [[0.0, 20.0], [100000.0, -80.0]], header="X [m], Elevation [m]"
        ),
        "sealevel": as_csv(
            [[0.0, 0.0], [200000, -10]], header="Time [y], Sea-Level Elevation [m]"
        ),
        "subsidence": as_csv(
            [[0.0, 0], [30000.0, 0], [35000.0, 0], [50000.0, 0], [100000.0, 0]],
            header="Time [y], Subsidence Rate [m / y]",
        ),
    }

    return contents[infile]


@click.group()
def sequence():
    pass


@sequence.command()
@click.option("--dry-run", is_flag=True, help="do not actually run the model")
@click.option(
    "-v", "--verbose", is_flag=True, help="Also emit status messages to stderr."
)
@click.option(
    "--with-citations", is_flag=True, help="print citations for components used"
)
@click.argument(
    "config_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
def run(config_file, with_citations, verbose, dry_run):
    config_file = pathlib.Path(config_file)
    rundir = config_file.parent.resolve()

    params = load_params(config_file)

    if verbose:
        click.secho(yaml.dump(params, default_flow_style=False), err=True)

    os.chdir(rundir)

    model = SequenceModel(**params)

    if with_citations:
        from landlab.core.model_component import registry

        click.secho("👇👇👇These are the citations to use👇👇👇", err=True)
        click.secho(registry.format_citations())
        click.secho("👆👆👆These are the citations to use👆👆👆", err=True)

    if not dry_run:
        try:
            with click.progressbar(
                length=int(model.clock.stop // model.clock.step),
                label=" ".join(["🚀", config_file.name]),
            ) as bar:
                while 1:
                    model.run_one_step()
                    bar.update(1)
        except StopIteration:
            pass

        click.secho("💥 Finished! 💥", err=True, fg="green")
        if "output" in params:
            click.secho(
                "Output written to {0}".format(rundir / params["output"]["filepath"]),
                fg="green",
            )
    else:
        click.secho("Nothing to do. 😴", fg="green")


@sequence.command()
@click.argument(
    "infile", type=click.Choice(["bathymetry", "config", "sealevel", "subsidence"])
)
@click.option(
    "--set", multiple=True, help="Set model parameters",
)
def show(infile, set):
    click.secho(_contents_of_input_file(infile, set), err=False)


@sequence.command()
@click.argument(
    "destination",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
@click.option(
    "--set", multiple=True, help="Set model parameters",
)
def setup(destination, set):
    folder = pathlib.Path(destination)

    files = [
        pathlib.Path(fname)
        for fname in ["bathymetry.csv", "config.yaml", "sealevel.csv", "subsidence.csv"]
    ]

    existing_files = [folder / name for name in files if (folder / name).exists()]
    if existing_files:
        for name in existing_files:
            click.secho(
                f"{name}: File exists. Either remove and then rerun or choose a different destination folder",
                err=True,
            )
    else:
        for fname in files:
            with open(folder / fname, "w") as fp:
                print(_contents_of_input_file(fname.stem, set), file=fp)
        click.secho(str(folder / "config.yaml"), err=False)

    sys.exit(len(existing_files))
