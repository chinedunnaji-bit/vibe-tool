import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def _make_project(tmp_path, monkeypatch):
    project = tmp_path / "my-project"
    project.mkdir()
    src = project / "src"
    src.mkdir()
    (src / "app.ts").write_text("export function hello() { return 'hi'; }\n")
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    return project


def test_index_creates_codebase_md(tmp_path, monkeypatch):
    project = _make_project(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["index"])
    assert result.exit_code == 0
    assert (project / ".vibe" / "codebase.md").exists()


def test_index_content_has_file_map(tmp_path, monkeypatch):
    project = _make_project(tmp_path, monkeypatch)
    runner = CliRunner()
    runner.invoke(cli, ["index"])
    content = (project / ".vibe" / "codebase.md").read_text()
    assert "## File Map" in content
    assert "app.ts" in content
