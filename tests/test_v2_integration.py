"""End-to-end v2 test: init with v2 features, index, error memory, prompts, handoff, pre-loader."""

import os
import subprocess
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli
from vibe_tool.config import VibeConfig
from vibe_tool.handoff import generate_handoff
from vibe_tool.preloader import generate_session_context


def _setup(tmp_path, monkeypatch):
    vibe_cfg = tmp_path / ".vibe-cfg"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# rules\n")
    project = tmp_path / "test-project"
    project.mkdir()

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_cfg))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    # Setup
    runner = CliRunner()
    runner.invoke(cli, ["setup"], input="acme\nclaude-1\n")

    # Init git
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=project, check=True)

    # Add source files
    src = project / "src"
    src.mkdir()
    (src / "app.ts").write_text("""
import { db } from './db';
export function startServer(port: number) { }
export function healthCheck() { return 'ok'; }
""")
    (src / "db.ts").write_text("""
export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    email: varchar('email'),
});
""")

    # .env files for pre-loader test
    (project / ".env.example").write_text("DATABASE_URL=\nAPI_KEY=\n")
    (project / ".env").write_text("DATABASE_URL=postgres://localhost\n")

    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)

    monkeypatch.chdir(project)
    return project, runner


def test_full_v2_workflow(tmp_path, monkeypatch):
    project, runner = _setup(tmp_path, monkeypatch)

    # 1. Init project (should create .vibe/ with all v2 features)
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0

    # Verify .vibe/ structure
    vibe_dir = project / ".vibe"
    assert vibe_dir.is_dir()
    assert (vibe_dir / "codebase.md").exists()
    assert (vibe_dir / "errors.md").exists()
    assert (vibe_dir / "prompts" / "fix-bug.md").exists()

    # 2. Verify codebase index content
    index_content = (vibe_dir / "codebase.md").read_text()
    assert "app.ts" in index_content
    assert "startServer" in index_content
    assert "users" in index_content  # table from db.ts

    # 3. Re-run index to verify idempotency
    result = runner.invoke(cli, ["index"])
    assert result.exit_code == 0
    assert "Indexed" in result.output

    # 4. Add an error
    result = runner.invoke(cli, ["error", "add"],
        input="Port in use\nStarting server\nPort 3000 already bound\nKill process on port 3000\n")
    assert result.exit_code == 0

    # Verify error was recorded
    result = runner.invoke(cli, ["error", "list"])
    assert "ERR-001" in result.output
    assert "Port in use" in result.output

    # 5. List prompt templates
    result = runner.invoke(cli, ["prompt", "list"])
    assert result.exit_code == 0
    assert "fix-bug" in result.output
    assert "add-endpoint" in result.output

    # 6. Show a template
    result = runner.invoke(cli, ["prompt", "show", "fix-bug"])
    assert "errors.md" in result.output

    # 7. Generate session context (pre-loader)
    md = generate_session_context(project)
    assert "## Git State" in md
    assert "## Environment Notes" in md
    assert "API_KEY" in md  # missing from .env

    # 8. Make a change and generate handoff
    start_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True
    ).stdout.strip()

    (project / "src" / "new-feature.ts").write_text("export function newThing() {}\n")
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "--no-verify", "-m", "feat: add new feature"], cwd=project, check=True)

    handoff = generate_handoff(project, start_sha)
    assert "## What was done" in handoff
    assert "new feature" in handoff
    assert "new-feature.ts" in handoff

    # 9. Verify .gitignore has session-context.md
    gitignore = (project / ".gitignore").read_text()
    assert "session-context.md" in gitignore
