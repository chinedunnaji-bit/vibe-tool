import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli
from vibe_tool.prompts import install_templates


def _setup(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    prompts_dir = project / ".vibe" / "prompts"
    install_templates(prompts_dir)
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe-cfg"))
    return project


def test_prompt_list(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["prompt", "list"])
    assert result.exit_code == 0
    assert "add-endpoint" in result.output
    assert "fix-bug" in result.output


def test_prompt_show(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["prompt", "show", "fix-bug"])
    assert result.exit_code == 0
    assert "bug" in result.output.lower()


def test_prompt_show_not_found(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["prompt", "show", "nonexistent"])
    assert result.exit_code != 0 or "not found" in result.output.lower()


def test_prompt_create(tmp_path, monkeypatch):
    project = _setup(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["prompt", "create", "deploy"],
        input="Deploy the app: [describe target]\n\nContext:\n- Check CI is green first\n")
    assert result.exit_code == 0
    assert (project / ".vibe" / "prompts" / "deploy.md").exists()
