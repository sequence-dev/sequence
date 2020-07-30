import pytest

from sequence.input_reader import TimeVaryingConfig


@pytest.mark.parametrize("fmt", ("yaml", "toml"))
def test_from_file(datadir, fmt):
    config = TimeVaryingConfig.from_file(datadir / f"config.{fmt}")

    assert config.as_dict() == {"foo": {"bar": "baz"}, "constant": {"pi": 3.14}}


@pytest.mark.parametrize("fmt", ("yaml", "toml"))
def test_from_file_basic(datadir, fmt):
    config = TimeVaryingConfig.from_file(datadir / f"config-basic.{fmt}")

    assert config.as_dict() == {"foo": {"bar": "baz"}, "constant": {"pi": 3.14}}


@pytest.mark.parametrize("src_fmt", ("yaml", "toml"))
@pytest.mark.parametrize("dst_fmt", ("yaml", "toml"))
def test_dump(tmpdir, datadir, src_fmt, dst_fmt):
    with tmpdir.as_cwd():
        config = TimeVaryingConfig.from_file(datadir / f"config.{src_fmt}")
        with open(f"config.{dst_fmt}", "w") as fp:
            fp.write(config.dump(fmt=dst_fmt))
        actual = TimeVaryingConfig.from_file(f"config.{dst_fmt}")
        assert actual.as_dict() == config.as_dict()

