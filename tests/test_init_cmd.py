import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def _setup_env(tmp_path, monkeypatch):
    """Set up isolated vibe + claude config and a project directory."""
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    project_dir = tmp_path / "my-project"
    project_dir.mkdir()

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))
    monkeypatch.chdir(project_dir)

    # Pre-add a client
    from vibe_tool.config import VibeConfig
    config = VibeConfig(vibe_dir)
    config.ensure_dirs()
    config.add_client("acme-corp", "claude-1")

    # Init git in project dir
    os.system(f"cd {project_dir} && git init -q")

    return project_dir, vibe_dir


def test_init_creates_project_claude_md(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    # Select client 1, project type 1 (web), stack 1 (next)
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    assert (project_dir / "CLAUDE.md").exists()
    content = (project_dir / "CLAUDE.md").read_text()
    assert "## How to run" in content


def test_init_creates_git_hooks(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    pre_commit = project_dir / ".git" / "hooks" / "pre-commit"
    pre_push = project_dir / ".git" / "hooks" / "pre-push"
    assert pre_commit.exists()
    assert pre_push.exists()
    assert os.access(pre_commit, os.X_OK)


def test_init_creates_ci_pipeline(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    ci_file = project_dir / ".github" / "workflows" / "ci.yml"
    assert ci_file.exists()
    assert "test" in ci_file.read_text().lower()


def test_init_registers_project_in_index(tmp_path, monkeypatch):
    project_dir, vibe_dir = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0

    from vibe_tool.config import VibeConfig
    config = VibeConfig(vibe_dir)
    projects = config.load_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == "my-project"
    assert projects[0]["client"] == "acme-corp"


def test_init_python_api(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    # Select client 1, project type 3 (api), stack 4 (python/fastapi)
    result = runner.invoke(cli, ["init"], input="1\n3\n4\n")
    assert result.exit_code == 0
    content = (project_dir / "CLAUDE.md").read_text()
    assert "pytest" in content


def test_init_creates_vibe_directory(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    assert (project_dir / ".vibe").is_dir()


def test_init_runs_index(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    # Add a source file so index has something to scan
    (project_dir / "src").mkdir()
    (project_dir / "src" / "app.ts").write_text("export function hello() {}\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    assert (project_dir / ".vibe" / "codebase.md").exists()


def test_init_creates_error_memory(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    assert (project_dir / ".vibe" / "errors.md").exists()
    content = (project_dir / ".vibe" / "errors.md").read_text()
    assert "Error Memory" in content


def test_init_installs_prompt_templates(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    prompts = project_dir / ".vibe" / "prompts"
    assert prompts.is_dir()
    assert (prompts / "fix-bug.md").exists()


def test_init_adds_session_context_to_gitignore(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    gitignore = project_dir / ".gitignore"
    assert gitignore.exists()
    assert "session-context.md" in gitignore.read_text()
