from click.testing import CliRunner
from vibe_tool.cli import cli


def test_cli_shows_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "vibe" in result.output.lower()
