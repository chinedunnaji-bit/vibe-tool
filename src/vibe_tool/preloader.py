import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _parse_env_file(path: Path) -> set[str]:
    """Extract variable names from a .env file."""
    keys = set()
    if not path.exists():
        return keys
    for line in path.read_text().split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            keys.add(line.split("=", 1)[0].strip())
    return keys


def generate_session_context(project_dir: Path) -> str:
    """Generate ephemeral session context from current repo state."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Session Context (auto-generated, do not edit)",
        f"Generated: {now}",
        "",
    ]

    # Git state
    branch = _run_git(["branch", "--show-current"], project_dir) or "unknown"
    ahead = _run_git(["rev-list", "--count", "HEAD", "--not", "--remotes"], project_dir) or "0"

    lines.append("## Git State")
    lines.append(f"Branch: {branch} ({ahead} commits ahead of remote)")

    # Uncommitted changes
    status = _run_git(["status", "--short"], project_dir)
    if status:
        lines.append("Uncommitted changes:")
        for sline in status.split("\n"):
            sline = sline.strip()
            if sline:
                lines.append(f"  - {sline}")
    else:
        lines.append("Working tree clean")
    lines.append("")

    # Recent commits
    log = _run_git(["log", "--oneline", "-5", "--format=%s (%ar)"], project_dir)
    lines.append("## Recent Commits (last 5)")
    if log:
        for commit in log.split("\n"):
            if commit.strip():
                lines.append(f"- {commit.strip()}")
    else:
        lines.append("- No commits yet")
    lines.append("")

    # Test health — read from cached results if available
    lines.append("## Test Health")
    lines.append("[Run `vibe status` for test counts]")
    lines.append("")

    # Environment check
    env_example = project_dir / ".env.example"
    env_file = project_dir / ".env"

    if env_example.exists():
        expected = _parse_env_file(env_example)
        actual = _parse_env_file(env_file)
        missing = expected - actual

        lines.append("## Environment Notes")
        if env_file.exists():
            lines.append(f".env has: {', '.join(sorted(actual)) if actual else 'empty'}")
        else:
            lines.append(".env file not found")

        if missing:
            lines.append(f".env missing: {', '.join(sorted(missing))}")
        elif env_file.exists():
            lines.append("All expected env vars are set")
        lines.append("")

    return "\n".join(lines)


def write_session_context(project_dir: Path):
    """Generate and write session context to .vibe/session-context.md."""
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)
    md = generate_session_context(project_dir)
    (vibe_dir / "session-context.md").write_text(md)


def record_session_start(project_dir: Path):
    """Record the current HEAD SHA for handoff comparison."""
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_dir, capture_output=True, text=True
    )
    if result.returncode == 0:
        (vibe_dir / ".session-start-sha").write_text(result.stdout.strip())
