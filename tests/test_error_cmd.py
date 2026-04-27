import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def test_error_add(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe-cfg"))

    runner = CliRunner()
    result = runner.invoke(cli, ["error", "add"],
        input="Module not found\nWhen importing\nBad path\nFix the path\n")
    assert result.exit_code == 0
    assert (project / ".vibe" / "errors.md").exists()


def test_error_list_empty(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe-cfg"))

    runner = CliRunner()
    result = runner.invoke(cli, ["error", "list"])
    assert result.exit_code == 0
    assert "No errors" in result.output


def test_error_list_shows_entries(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe-cfg"))

    runner = CliRunner()
    runner.invoke(cli, ["error", "add"],
        input="Test bug\nAlways\nBad code\nGood code\n")
    result = runner.invoke(cli, ["error", "list"])
    assert result.exit_code == 0
    assert "ERR-001" in result.output
    assert "Test bug" in result.output
