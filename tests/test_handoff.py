import subprocess
from pathlib import Path
from vibe_tool.handoff import generate_handoff


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


def test_handoff_with_commits(tmp_path):
    project = _make_git_project(tmp_path)
    # Record start SHA
    start_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True
    ).stdout.strip()

    # Make changes
    (project / "src").mkdir()
    (project / "src" / "app.ts").write_text("export function hello() {}\n")
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feat: add hello function"], cwd=project, check=True)

    md = generate_handoff(project, start_sha)
    assert "## What was done" in md
    assert "hello" in md.lower() or "feat:" in md
    assert "## Files changed" in md
    assert "app.ts" in md


def test_handoff_with_uncommitted_changes(tmp_path):
    project = _make_git_project(tmp_path)
    start_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True
    ).stdout.strip()

    # Uncommitted changes
    (project / "wip.ts").write_text("// work in progress\n")

    md = generate_handoff(project, start_sha)
    assert "## In progress" in md
    assert "wip.ts" in md


def test_handoff_no_changes(tmp_path):
    project = _make_git_project(tmp_path)
    start_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True
    ).stdout.strip()

    md = generate_handoff(project, start_sha)
    assert "No changes" in md or "## What was done" in md
