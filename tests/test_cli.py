import pytest
from click.testing import CliRunner

from sequence.cli import sequence


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(sequence, ["--help"])
    assert result.exit_code == 0

    result = runner.invoke(sequence, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


@pytest.mark.parametrize("subcommand", ("run", "show", "setup"))
def test_subcommand_help(subcommand):
    runner = CliRunner()
    result = runner.invoke(sequence, [subcommand, "--help"])
    assert result.exit_code == 0
