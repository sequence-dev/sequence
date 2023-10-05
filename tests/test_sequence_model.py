import os
import shutil
from itertools import chain, combinations, permutations

import pytest
from landlab.core import load_params

from sequence.sequence_model import SequenceModel

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ALL_PROCESSES = [
    "sea_level",
    "subsidence",
    "compaction",
    "submarine_diffusion",
    "flexure",
]


# @pytest.mark.skip("test fails with a core dump from numpy")
def test_marmara(tmpdir, datadir):
    with tmpdir.as_cwd():
        for fname in datadir.iterdir():
            shutil.copy(str(datadir / fname), ".")
        params = load_params("marmara.yaml")
        grid = SequenceModel.load_grid(params["grid"], bathymetry=params["bathymetry"])
        processes = SequenceModel.load_processes(
            grid,
            processes=params.get("processes", ALL_PROCESSES),
            context=params,
        )
        model = SequenceModel(
            grid, clock=params["clock"], processes=processes, output=params["output"]
        )
        model.run()

        assert os.path.isfile("marmara.nc")


@pytest.mark.parametrize("processes", permutations(ALL_PROCESSES))
def test_component_ordering(tmpdir, datadir, processes):
    with tmpdir.as_cwd():
        for fname in datadir.iterdir():
            shutil.copy(str(datadir / fname), ".")
        with open("marmara.toml", "rb") as fp:
            params = tomllib.load(fp)["sequence"]
        grid = SequenceModel.load_grid(params["grid"], bathymetry=params["bathymetry"])
        processes = SequenceModel.load_processes(
            grid,
            processes=processes,
            context=params,
        )
        model = SequenceModel(
            grid, clock=params["clock"], processes=processes, output=params["output"]
        )
        model.run()

        assert os.path.isfile("marmara.nc")


@pytest.mark.parametrize(
    "processes",
    chain(
        combinations(ALL_PROCESSES, 0),
        combinations(ALL_PROCESSES, 1),
        combinations(ALL_PROCESSES, 2),
        combinations(ALL_PROCESSES, 3),
        combinations(ALL_PROCESSES, 4),
    ),
    ids=[
        "-".join(combo)
        for combo in chain(
            combinations(ALL_PROCESSES, 0),
            combinations(ALL_PROCESSES, 1),
            combinations(ALL_PROCESSES, 2),
            combinations(ALL_PROCESSES, 3),
            combinations(ALL_PROCESSES, 4),
        )
    ],
)
def test_component_combos(tmpdir, datadir, processes):

    with tmpdir.as_cwd():
        for fname in datadir.iterdir():
            shutil.copy(str(datadir / fname), ".")
        with open("marmara.toml", "rb") as fp:
            params = tomllib.load(fp)["sequence"]
        grid = SequenceModel.load_grid(params["grid"], bathymetry=params["bathymetry"])
        processes = SequenceModel.load_processes(
            grid,
            processes=processes,
            context=params,
        )
        model = SequenceModel(
            grid, clock=params["clock"], processes=processes, output=params["output"]
        )
        model.run()

        assert os.path.isfile("marmara.nc")
