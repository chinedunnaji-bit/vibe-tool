import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli
from vibe_tool.config import VibeConfig


def test_status_no_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "No projects" in result.output


def test_status_shows_projects_grouped_by_client(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))

    config = VibeConfig(vibe_dir)
    config.ensure_dirs()
    config.add_client("acme", "claude-1")
    config.add_client("beta-inc", "claude-2")
    config.add_project("marketplace", "/tmp/marketplace", "acme", "web", "next")
    config.add_project("fitness-api", "/tmp/fitness", "beta-inc", "api", "fastapi")
    config.update_project_tests("marketplace", passed=24, failed=0, total=24)
    config.update_project_tests("fitness-api", passed=18, failed=2, total=20)

    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "acme" in result.output.lower() or "ACME" in result.output
    assert "marketplace" in result.output
    assert "fitness-api" in result.output
    assert "24" in result.output
