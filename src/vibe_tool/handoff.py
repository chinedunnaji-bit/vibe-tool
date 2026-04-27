import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def generate_handoff(project_dir: Path, start_sha: str | None = None) -> str:
    """Generate a session handoff note from git state."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Session Handoff", f"Last session: {now}", ""]

    # What was done — commits since session start
    if start_sha:
        log = _run_git(["log", f"{start_sha}..HEAD", "--oneline"], project_dir)
    else:
        log = _run_git(["log", "-5", "--oneline"], project_dir)

    lines.append("## What was done")
    if log:
        for commit_line in log.split("\n"):
            if commit_line.strip():
                # Strip the short SHA, keep the message
                parts = commit_line.strip().split(" ", 1)
                msg = parts[1] if len(parts) > 1 else parts[0]
                lines.append(f"- {msg}")
    else:
        lines.append("- No changes committed this session")
    lines.append("")

    # In progress — uncommitted changes
    status = _run_git(["status", "--short"], project_dir)
    uncommitted = []
    if status:
        for sline in status.split("\n"):
            sline = sline.strip()
            if sline:
                # Format: "M  file.txt" or "?? file.txt"
                parts = sline.split(None, 1)
                if len(parts) == 2:
                    uncommitted.append(parts[1])

    if uncommitted:
        lines.append("## In progress")
        for f in uncommitted:
            lines.append(f"- {f} (uncommitted)")
        lines.append("")

    # Files changed — from diff since start
    if start_sha:
        diff_stat = _run_git(["diff", "--name-status", f"{start_sha}..HEAD"], project_dir)
    else:
        diff_stat = _run_git(["diff", "--name-status", "HEAD~5..HEAD"], project_dir)

    lines.append("## Files changed")
    if diff_stat:
        for dline in diff_stat.split("\n"):
            dline = dline.strip()
            if not dline:
                continue
            parts = dline.split("\t")
            if len(parts) >= 2:
                status_code = parts[0]
                fname = parts[1]
                label = {"A": "Created", "M": "Modified", "D": "Deleted"}.get(status_code, "Changed")
                lines.append(f"- {label}: {fname}")
    elif not log:
        lines.append("- No files changed")
    lines.append("")

    # Next up placeholder
    lines.append("## Next up")
    lines.append("- [Determined by next session based on project CLAUDE.md]")
    lines.append("")

    return "\n".join(lines)


def write_handoff(project_dir: Path, start_sha: str | None = None):
    """Generate and write handoff to .vibe/handoff.md."""
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)
    md = generate_handoff(project_dir, start_sha)
    (vibe_dir / "handoff.md").write_text(md)
