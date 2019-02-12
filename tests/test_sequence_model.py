import os
import shutil

from landlab.core import load_params
from sequence.sequence_model import SequenceModel


def test_marmara(tmpdir, datadir):
    files = [
        "marmara.yaml",
        "marmara_bathymetry.csv",
        "marmara_sea_level.csv",
        "marmara_subsidence.csv",
    ]
    with tmpdir.as_cwd():
        for fname in files:
            shutil.copy(str(datadir / fname), ".")
        params = load_params("marmara.yaml")
        model = SequenceModel(**params)
        model.run()

        assert os.path.isfile("marmara.nc")
