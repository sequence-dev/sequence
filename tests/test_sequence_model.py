import os
import shutil

import pytest
from landlab.core import load_params

from sequence.sequence_model import SequenceModel


# @pytest.mark.skip("test fails with a core dump from numpy")
def test_marmara(tmpdir, datadir):
    with tmpdir.as_cwd():
        for fname in datadir.iterdir():
            shutil.copy(str(datadir / fname), ".")
        params = load_params("marmara.yaml")
        model = SequenceModel(**params)
        model.run()

        assert os.path.isfile("marmara.nc")
