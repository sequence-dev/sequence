import pathlib

import pytest

from sequence.input_reader import load_config


def test_load_config_from_pathlike(datadir):
    config = {}
    for fmt in ("yaml", "toml"):
        config[fmt] = load_config(datadir / f"sequence.{fmt}", fmt=fmt)
    assert config["yaml"] == config["toml"]


def test_load_config_from_str(datadir):
    config = {}
    for fmt in ("yaml", "toml"):
        config[fmt] = load_config(str(datadir / f"sequence.{fmt}"), fmt=fmt)
    assert config["yaml"] == config["toml"]


def test_load_config_from_stream(datadir):
    config = {}
    for fmt in ("yaml", "toml"):
        with open(datadir / f"sequence.{fmt}") as fp:
            config[fmt] = load_config(fp, fmt=fmt)
    assert config["yaml"] == config["toml"]


def test_from_stream_without_format_keyword(datadir):
    with open(datadir / "sequence.toml") as fp:
        with pytest.raises(ValueError):
            load_config(fp)


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
