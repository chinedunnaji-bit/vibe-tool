import subprocess
from pathlib import Path
from vibe_tool.preloader import generate_session_context


def _make_git_project(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=project, check=True)
    (project / "README.md").write_text("# test\n")
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)
    return project


def test_session_context_includes_git_state(tmp_path):
    project = _make_git_project(tmp_path)
    md = generate_session_context(project)
    assert "## Git State" in md
    assert "Branch:" in md


def test_session_context_includes_recent_commits(tmp_path):
    project = _make_git_project(tmp_path)
    md = generate_session_context(project)
    assert "## Recent Commits" in md
    assert "init" in md


def test_session_context_shows_uncommitted(tmp_path):
    project = _make_git_project(tmp_path)
    (project / "new_file.txt").write_text("wip\n")
    md = generate_session_context(project)
    assert "new_file.txt" in md


def test_session_context_env_check(tmp_path):
    project = _make_git_project(tmp_path)
    (project / ".env.example").write_text("DATABASE_URL=\nSTRIPE_KEY=\n")
    (project / ".env").write_text("DATABASE_URL=postgres://localhost\n")
    md = generate_session_context(project)
    assert "## Environment Notes" in md
    assert "STRIPE_KEY" in md  # missing from .env


def test_session_context_no_env_files(tmp_path):
    project = _make_git_project(tmp_path)
    md = generate_session_context(project)
    # Should not crash, just skip env section
    assert "## Git State" in md
