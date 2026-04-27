import re
from datetime import datetime, timezone
from pathlib import Path

HEADER = "# Error Memory\nErrors encountered and their solutions. Read this before debugging.\n"


def get_next_id(errors_file: Path) -> str:
    """Get the next ERR-NNN id."""
    entries = load_errors(errors_file)
    if not entries:
        return "ERR-001"
    last_num = max(int(e["id"].split("-")[1]) for e in entries)
    return f"ERR-{last_num + 1:03d}"


def load_errors(errors_file: Path) -> list[dict]:
    """Parse error entries from the errors.md file."""
    if not errors_file.exists():
        return []

    content = errors_file.read_text()
    entries = []

    for match in re.finditer(
        r'## (ERR-\d+): (.+?)\n'
        r'\*\*When:\*\* (.+?)\n'
        r'\*\*Cause:\*\* (.+?)\n'
        r'\*\*Fix:\*\* (.+?)\n'
        r'\*\*Date:\*\* (.+?)(?:\n|$)',
        content,
    ):
        entries.append({
            "id": match.group(1),
            "title": match.group(2),
            "when": match.group(3),
            "cause": match.group(4),
            "fix": match.group(5),
            "date": match.group(6),
        })

    return entries


def add_error(errors_file: Path, title: str, when: str, cause: str, fix: str):
    """Append a new error entry to errors.md."""
    err_id = get_next_id(errors_file)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    entry = f"\n## {err_id}: {title}\n**When:** {when}\n**Cause:** {cause}\n**Fix:** {fix}\n**Date:** {date}\n"

    if not errors_file.exists():
        errors_file.parent.mkdir(parents=True, exist_ok=True)
        errors_file.write_text(HEADER + entry)
    else:
        with open(errors_file, "a") as f:
            f.write(entry)


def render_errors_md(errors_file: Path) -> str:
    """Return the full errors.md content."""
    if not errors_file.exists():
        return HEADER
    return errors_file.read_text()
