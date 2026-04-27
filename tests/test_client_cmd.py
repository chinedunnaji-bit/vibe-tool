from click.testing import CliRunner
from vibe_tool.cli import cli


def test_client_add(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    runner = CliRunner()
    result = runner.invoke(cli, ["client", "add", "--name", "acme-corp", "--account", "claude-1"])
    assert result.exit_code == 0
    assert "acme-corp" in result.output


def test_client_list_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    runner = CliRunner()
    result = runner.invoke(cli, ["client", "list"])
    assert result.exit_code == 0
    assert "No clients" in result.output


def test_client_list_shows_added(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    runner = CliRunner()
    runner.invoke(cli, ["client", "add", "--name", "acme-corp", "--account", "claude-1"])
    result = runner.invoke(cli, ["client", "list"])
    assert result.exit_code == 0
    assert "acme-corp" in result.output
    assert "claude-1" in result.output
