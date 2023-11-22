import os
import shutil

from landlab.core import load_params

from sequence.sequence_model import SequenceModel


# @pytest.mark.skip("test fails with a core dump from numpy")
def test_marmara(tmpdir, datadir):
    with tmpdir.as_cwd():
        for fname in datadir.iterdir():
            shutil.copy(str(datadir / fname), ".")
        params = load_params("marmara.yaml")
        grid = SequenceModel.load_grid(params["grid"], bathymetry=params["bathymetry"])
        processes = SequenceModel.load_processes(
            grid,
            processes=params.get(
                "processes",
                [
                    "sea_level",
                    "subsidence",
                    "compaction",
                    "submarine_diffusion",
                    "fluvial",
                    "flexure",
                ],
            ),
            context=params,
        )
        model = SequenceModel(
            grid, clock=params["clock"], processes=processes, output=params["output"]
        )
        model.run()

        assert os.path.isfile("marmara.nc")
