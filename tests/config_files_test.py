import pathlib

import pytest

from sequence.cli import _find_config_files


@pytest.mark.parametrize("path", [".", pathlib.Path(".")])
@pytest.mark.parametrize("ext", ["toml", "yaml"])
def test_with_one_file(tmpdir, path, ext):
    with tmpdir.as_cwd():
        pathlib.Path(f"sequence.{ext}").touch()
        times, names = _find_config_files(path)

    assert times == [0]
    assert names == [f"sequence.{ext}"]


@pytest.mark.parametrize("path", [".", pathlib.Path(".")])
@pytest.mark.parametrize("ext", ["toml", "yaml"])
def test_with_multiple_files_no_timestamp(tmpdir, path, ext):
    files = [f"sequence-a.{ext}", f"sequence-b.{ext}", f"sequence-c.{ext}"]
    with tmpdir.as_cwd():
        for name in files:
            pathlib.Path(name).touch()
        times, names = _find_config_files(path)

    assert times == [0, 1, 2]
    assert names == files


@pytest.mark.parametrize("path", [".", pathlib.Path(".")])
@pytest.mark.parametrize("ext", ["toml", "yaml"])
def test_with_multiple_files_with_timestamp(tmpdir, path, ext):
    files = [
        f"sequence-1.{ext}",
        f"sequence-2.{ext}",
        f"sequence-003.{ext}",
        f"sequence-10.{ext}",
    ]
    with tmpdir.as_cwd():
        for name in files:
            pathlib.Path(name).touch()
        times, names = _find_config_files(path)

    assert times == [1, 2, 3, 10]
    assert names == files


@pytest.mark.parametrize("path", [".", pathlib.Path(".")])
def test_with_multiple_files_mixed_format(tmpdir, path):
    toml_files = [
        "sequence-1.toml",
        "sequence-003.toml",
        "sequence-10.toml",
    ]
    yaml_files = [
        "sequence-2.yaml",
    ]
    with tmpdir.as_cwd():
        for name in toml_files + yaml_files:
            pathlib.Path(name).touch()
        times, names = _find_config_files(path)

    assert times == [1, 3, 10]
    assert names == toml_files
