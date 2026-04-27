import os
import subprocess
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def _make_git_project(path: Path):
    """Create a minimal git project with a remote."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    # Create initial commit so we have a branch
    (path / "README.md").write_text("# test\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


def test_sync_commits_claude_context(tmp_path, monkeypatch):
    project_dir = tmp_path / "my-project"
    _make_git_project(project_dir)

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    monkeypatch.chdir(project_dir)

    # Create CLAUDE.md and .claude/ dir with content
    (project_dir / "CLAUDE.md").write_text("# My Project\n## Current state\nWIP\n")
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    (claude_dir / "memory.md").write_text("some memory\n")

    runner = CliRunner()
    result = runner.invoke(cli, ["sync", "push"])
    assert result.exit_code == 0

    # Verify files are committed
    log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=project_dir, capture_output=True, text=True
    )
    assert "vibe sync" in log.stdout.lower() or "context" in log.stdout.lower()


def test_sync_no_changes(tmp_path, monkeypatch):
    project_dir = tmp_path / "my-project"
    _make_git_project(project_dir)

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    monkeypatch.chdir(project_dir)

    runner = CliRunner()
    result = runner.invoke(cli, ["sync", "push"])
    assert result.exit_code == 0
    assert "nothing" in result.output.lower() or "No context" in result.output


def test_sync_not_a_git_repo(tmp_path, monkeypatch):
    project_dir = tmp_path / "not-git"
    project_dir.mkdir()

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    monkeypatch.chdir(project_dir)

    runner = CliRunner()
    result = runner.invoke(cli, ["sync"])
    assert result.exit_code != 0 or "not a git" in result.output.lower()


def test_sync_includes_vibe_directory(tmp_path, monkeypatch):
    project_dir = tmp_path / "my-project"
    _make_git_project(project_dir)

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    monkeypatch.chdir(project_dir)

    # Create .vibe/ with context files
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir()
    (vibe_dir / "codebase.md").write_text("# Index\n")
    (vibe_dir / "errors.md").write_text("# Errors\n")
    (vibe_dir / "handoff.md").write_text("# Handoff\n")

    runner = CliRunner()
    result = runner.invoke(cli, ["sync", "push"])
    assert result.exit_code == 0
    assert "Committed" in result.output

    # Verify .vibe files are committed
    log = subprocess.run(
        ["git", "show", "--stat", "HEAD"],
        cwd=project_dir, capture_output=True, text=True
    )
    assert ".vibe/" in log.stdout
