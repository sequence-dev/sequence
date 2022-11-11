"""The command line interface for *Sequence*."""
import os
import pathlib
import re
from io import StringIO
from os import PathLike
from typing import Any, Iterable, Iterator, Optional, Union

import numpy as np
import rich_click as click
import tomlkit as toml
import yaml
from landlab.core import load_params
from numpy.typing import ArrayLike
from tqdm import tqdm

from .errors import MissingRequiredVariable
from .input_reader import TimeVaryingConfig
from .plot import plot_file
from .sequence_model import SequenceModel

click.rich_click.ERRORS_SUGGESTION = (
    "Try running the '--help' flag for more information."
)
click.rich_click.ERRORS_EPILOGUE = (
    "To find out more, visit https://github.com/sequence-dev/sequence"
)
click.rich_click.STYLE_ERRORS_SUGGESTION = "yellow italic"
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = False
click.rich_click.SHOW_METAVARS_COLUMN = True
click.rich_click.USE_MARKDOWN = True

# out = partial(click.secho, bold=True, file=sys.stderr)
# err = partial(click.secho, fg="red", file=sys.stderr)


def _out(message: Optional[str] = None, nl: bool = True, **styles: Any) -> None:
    if message is not None:
        if "bold" not in styles:
            styles["bold"] = True
        message = click.style(message, **styles)
    click.echo(message, nl=nl, err=True)


def _err(message: Optional[str] = None, nl: bool = True, **styles: Any) -> None:
    if message is not None:
        if "fg" not in styles:
            styles["fg"] = "red"
        message = click.style(message, **styles)
    click.echo(message, nl=nl, err=True)


def out(message: Optional[str] = None, nl: bool = True, **styles: Any) -> None:
    """Print a user info message."""
    _out(message, nl=nl, **styles)


def err(message: Optional[str] = None, nl: bool = True, **styles: Any) -> None:
    """Print a user error message."""
    _err(message, nl=nl, **styles)


def _contents_of_input_file(infile: Union[str, PathLike[str]], set: str) -> str:
    params = _load_model_params(
        defaults=SequenceModel.DEFAULT_PARAMS, dotted_params=set
    )

    def as_csv(data: ArrayLike, header: str = "") -> str:
        with StringIO() as fp:
            np.savetxt(fp, data, header=header, delimiter=",", fmt="%.1f")
            contents = fp.getvalue()
        return contents

    contents = {
        "sequence.yaml": yaml.dump(params, default_flow_style=False),
        "sequence.toml": toml.dumps(
            dict(
                sequence=dict(
                    _time=0.0, processes=SequenceModel.ALL_PROCESSES, **params
                )
            )
        ),
        "bathymetry.csv": as_csv(
            [[0.0, 20.0], [100000.0, -80.0]], header="X [m], Elevation [m]"
        ),
        "sealevel.csv": as_csv(
            [[0.0, 0.0], [200000.0, -10.0]], header="Time [y], Sea-Level Elevation [m]"
        ),
        "subsidence.csv": as_csv(
            [
                [0.0, 0.0],
                [30000.0, 0.0],
                [35000.0, 0.0],
                [50000.0, 0.0],
                [100000.0, 0.0],
            ],
            header="X [x], Subsidence Rate [m / y]",
        ),
    }
    for section, section_params in params.items():
        contents[f"sequence.{section}"] = yaml.dump(
            section_params, default_flow_style=False
        )

    return contents[str(infile)]


def _time_from_filename(name: Union[str, PathLike[str]]) -> Union[int, None]:
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


def _find_config_files(
    pathname: Union[str, PathLike[str]]
) -> tuple[list[int], list[str]]:
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

    config_files = sorted(toml_files if toml_files else yaml_files)

    times: list[int] = []
    names: list[str] = []
    for index, config_file in enumerate(config_files):
        time = _time_from_filename(config_file)
        if time is None:
            time = index
        times.append(time)
        names.append(str(config_file))

    names = [name for _, name in sorted(zip(times, names))]
    times.sort()

    return times, names


@click.group(chain=True)
@click.version_option(package_name="sequence-model")
@click.option(
    "--cd",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="chage to directory, then execute",
)
@click.option(
    "-s",
    "--silent",
    is_flag=True,
    help="Suppress status status messages, including the progress bar.",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Also emit status messages to stderr."
)
def sequence(cd: str, silent: bool, verbose: bool) -> None:
    """# Sequence.

    Sequence is a modular 2D (i.e., profile) sequence stratigraphic model
    that is written in Python and implemented within the Landlab framework.
    Sequence represents time-averaged fluvial and marine sediment transport
    via differential equations. The modular code includes components to deal
    with sea level changes, sediment compaction, local or flexural isostasy,
    and tectonic subsidence and uplift.
    """
    os.chdir(cd)


@sequence.command()
@click.option("--dry-run", is_flag=True, help="do not actually run the model")
@click.option(
    "--with-citations", is_flag=True, help="print citations for components used"
)
@click.pass_context
def run(ctx: Any, with_citations: bool, dry_run: bool) -> None:
    """Run a simulation.

    ## Examples

    Create a folder with example input files,
    ```bash
    $ mkdir sequence-example && cd sequence-example
    $ sequence setup
    ```
    Run a simulation using the examples input files,
    ```bash
    $ sequence run
    ```
    """
    verbose = ctx.parent.params["verbose"]
    silent = ctx.parent.params["silent"]

    run_dir = pathlib.Path.cwd()

    times, names = _find_config_files(".")
    if len(times) == 0:
        err("[ERROR] unable to find a configuration file.")
        raise click.Abort()

    if not silent:
        out(f"[INFO] config_files: {', '.join(repr(name) for name in names)}")
    params = TimeVaryingConfig.from_files(names, times=times)

    model_params = params.as_dict()
    model_params.pop("plot", None)

    grid = SequenceModel.load_grid(
        model_params["grid"], bathymetry=model_params["bathymetry"]
    )
    processes = model_params.get("processes", SequenceModel.ALL_PROCESSES)
    model = SequenceModel(
        grid,
        clock=model_params["clock"],
        output=model_params["output"],
        processes=SequenceModel.load_processes(grid, processes, model_params),
    )

    if verbose or not silent:
        for name in model.components:
            out(f"[INFO] ✅ enabled: {name}")
        for name in set(SequenceModel.ALL_PROCESSES) - set(model.components):
            out(f"[INFO] ❌ disabled {name}")

    if not silent and verbose:
        out(params.dump())

    if not silent and len(processes) == 0:
        out("[WARN] ⚠️  ALL PROCESSES HAVE BEEN DISABLED! ⚠️")

    if not silent and with_citations:
        from landlab.core.model_component import registry

        out("👇👇👇These are the citations to use👇👇👇")
        out(registry.format_citations())
        out("👆👆👆These are the citations to use👆👆👆")

    if not dry_run:
        progressbar = tqdm(
            total=int(model.clock.stop // model.clock.step),
            desc=" ".join(["🚀", str(run_dir)]),
            disable=True if silent else None,
        )

        try:
            with progressbar as bar:
                while 1:
                    model.run_one_step()
                    model.set_params(params.update(1))
                    bar.update(1)
        except StopIteration:
            pass

        if verbose or not silent:
            out("💥 Finished! 💥")
            out(f"Output written to {run_dir}")
    else:
        if verbose or not silent:
            out("Nothing to do. 😴")
    print(run_dir)


@sequence.command()
@click.argument(
    "infile",
    type=click.Choice(
        sorted(
            [
                "bathymetry.csv",
                "sequence.yaml",
                "sequence.toml",
                "sealevel.csv",
                "subsidence.csv",
            ]
            # ["bathymetry.csv", "sequence.yaml", "sequence.output", "sealevel.csv", "subsidence.csv"]
            # + [f"sequence.{name}" for name in SequenceModel.DEFAULT_PARAMS]
        )
    ),
)
@click.option("--set", metavar="KEY=VALUE", multiple=True, help="Set model parameters")
def generate(infile: str, set: str) -> None:
    """Generate example input files."""
    print(_contents_of_input_file(infile, set))


@sequence.command()
@click.option("--set", multiple=True, help="Set model parameters")
def setup(set: str) -> None:
    """Create a folder of input files for a simulation."""
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


@sequence.command()
@click.option("--set", multiple=True, help="Set model parameters")
@click.option(
    "-v", "--verbose", is_flag=True, help="Also emit status messages to stderr."
)
def plot(set: str, verbose: bool) -> None:
    """Plot a Sequence output file."""
    folder = pathlib.Path.cwd()

    if (folder / "sequence.toml").exists():
        config = (
            TimeVaryingConfig.from_file(folder / "sequence.toml")
            .as_dict()
            .get("plot", dict())
        )
    else:
        config = {}
    config.update(**_load_params_from_strings(set))

    if verbose:
        out(toml.dumps(dict(sequence=dict(plot=config))))

    try:
        plot_file(folder / "sequence.nc", **config)
    except MissingRequiredVariable as error:
        err(
            f"{folder / 'sequence.nc'}: output file is missing a required variable ({error})"
        )
        raise click.Abort()


def _load_params_from_strings(values: Iterable[str]) -> dict[str, Any]:
    params = {}
    for param in values:
        dotted_name, value = param.split("=")
        params.update(_dots_to_dict(dotted_name, yaml.safe_load(value)))

    return params


def _dots_to_dict(name: str, value: Any) -> dict[str, Any]:
    base: dict[str, Any] = {}
    level = base
    names = name.split(".")
    for k in names[:-1]:
        level[k] = {}
        level = level[k]
    level[names[-1]] = value
    return base


def _dict_to_dots(d: dict) -> list[str]:
    dots: list[str] = []
    for names in _walk_dict(d):
        dots.append(".".join(names[:-1]) + "=" + str(names[-1]))
    return dots


def _load_model_params(
    param_file: Optional[str] = None,
    defaults: Optional[dict] = None,
    dotted_params: Iterable[str] = (),
) -> dict[str, Any]:
    params = defaults or {}

    if param_file:
        params_from_file = load_params(param_file)
        dotted_params = _dict_to_dots(params_from_file) + list(dotted_params)

    params_from_cl = _load_params_from_strings(dotted_params)
    for group in params.keys():
        params[group].update(params_from_cl.get(group, {}))

    return params


def _walk_dict(indict: Union[dict, Any], prev: Optional[list] = None) -> Iterator[Any]:
    prev = prev[:] if prev else []

    if isinstance(indict, dict):
        for key, value in indict.items():
            if isinstance(value, dict):
                yield from _walk_dict(value, [key] + prev)
            elif isinstance(value, list) or isinstance(value, tuple):
                yield prev + [key, value]
            else:
                yield prev + [key, value]
    else:
        yield indict
