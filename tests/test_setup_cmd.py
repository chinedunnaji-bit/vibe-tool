import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def test_setup_creates_vibe_dir(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# Existing rules\n")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    result = runner.invoke(cli, ["setup"], input="acme-corp\nclaude-1\n")
    assert result.exit_code == 0
    assert vibe_dir.is_dir()


def test_setup_augments_claude_md(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# Existing rules\n")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    result = runner.invoke(cli, ["setup"], input="acme-corp\nclaude-1\n")
    assert result.exit_code == 0

    content = claude_dir.joinpath("CLAUDE.md").read_text()
    assert "Existing rules" in content
    assert "Mandatory Quality Rules" in content


def test_setup_does_not_duplicate_rules(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# Existing rules\n")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    runner.invoke(cli, ["setup"], input="acme-corp\nclaude-1\n")
    runner.invoke(cli, ["setup"], input="other\nclaude-2\n")

    content = claude_dir.joinpath("CLAUDE.md").read_text()
    assert content.count("Mandatory Quality Rules") == 1


def test_setup_adds_first_client(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    result = runner.invoke(cli, ["setup"], input="acme-corp\nclaude-1\n")
    assert result.exit_code == 0
    assert "acme-corp" in result.output


def test_setup_adds_context_loading_rules(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# Existing\n")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    result = runner.invoke(cli, ["setup"], input="acme\nclaude-1\n")
    assert result.exit_code == 0

    content = claude_dir.joinpath("CLAUDE.md").read_text()
    assert ".vibe/" in content
    assert "codebase.md" in content
