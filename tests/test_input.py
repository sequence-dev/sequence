import pathlib

import pytest

from sequence.input_reader import load_config


def test_load_config(datadir):
    config = {}
    for fmt in ("yaml", "toml"):
        config[fmt] = load_config(datadir / f"sequence.{fmt}", fmt=fmt)
    assert config["yaml"] == config["toml"]


@pytest.mark.parametrize("fmt", ("yaml", "toml"))
def test_guess_format(datadir, fmt):
    filepath = datadir / f"sequence.{fmt}"
    actual = load_config(filepath, fmt=None)
    expected = load_config(filepath, fmt=fmt)
    assert actual == expected


def test_bad_format(tmpdir, datadir):
    with pytest.raises(ValueError):
        load_config(datadir / "sequence.yaml", fmt="foo")

    with tmpdir.as_cwd():
        p = pathlib.Path("sequence.foo")
        p.symlink_to(datadir / "sequence.yaml")
        with pytest.raises(ValueError):
            load_config(p)


def test_missing_file(tmpdir):
    with tmpdir.as_cwd():
        with pytest.raises(OSError):
            load_config("not-a-file.toml")


@pytest.mark.parametrize("fmt", ("yaml", "toml"))
def test_no_extension(tmpdir, datadir, fmt):
    with tmpdir.as_cwd():
        p = pathlib.Path("sequence")
        p.symlink_to(datadir / f"sequence.{fmt}")
        with pytest.raises(ValueError):
            load_config(p, fmt=None)
        actual = load_config(p, fmt=fmt)
        expected = load_config(datadir / f"sequence.{fmt}")

        assert actual == expected
