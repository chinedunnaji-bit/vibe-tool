"""End-to-end test: setup -> client add -> init -> status -> sync."""

import os
import subprocess
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def test_full_workflow(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# My rules\n")
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()

    # 1. Setup
    result = runner.invoke(cli, ["setup"], input="acme\nclaude-1\n")
    assert result.exit_code == 0
    assert "Setup complete" in result.output

    # Verify CLAUDE.md was augmented
    content = claude_dir.joinpath("CLAUDE.md").read_text()
    assert "Mandatory Quality Rules" in content

    # 2. Add another client
    result = runner.invoke(cli, ["client", "add", "--name", "beta-inc", "--account", "claude-2"])
    assert result.exit_code == 0

    # 3. Init project
    subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=project_dir, check=True)
    monkeypatch.chdir(project_dir)

    result = runner.invoke(cli, ["init"], input="1\n")
    assert result.exit_code == 0
    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / ".github" / "workflows" / "ci.yml").exists()

    # 4. Status
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "test-project" in result.output

    # 5. Sync push (after making initial commit)
    subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
    subprocess.run(["git", "commit", "-q", "--no-verify", "-m", "init"], cwd=project_dir, check=True)
    # Modify CLAUDE.md to create something to sync
    (project_dir / "CLAUDE.md").write_text("# Updated\n## Current state\nDone\n")
    result = runner.invoke(cli, ["sync", "push"])
    assert result.exit_code == 0
    assert "Committed" in result.output
