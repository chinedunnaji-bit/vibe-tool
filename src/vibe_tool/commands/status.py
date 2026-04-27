import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from vibe_tool.config import VibeConfig

console = Console()


def _time_ago(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    except (ValueError, TypeError):
        return "unknown"


def _get_status_line(project: dict) -> str:
    """Try to read the Current state section from the project's CLAUDE.md."""
    claude_md = Path(project["path"]) / "CLAUDE.md"
    if not claude_md.exists():
        return ""
    try:
        content = claude_md.read_text()
        marker = "## Current state"
        idx = content.find(marker)
        if idx == -1:
            return ""
        after = content[idx + len(marker):].strip()
        for line in after.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                return line[:40]
        return ""
    except OSError:
        return ""


def _format_tests(tc: dict) -> str:
    total = tc.get("total", 0)
    if total == 0:
        return "no tests"
    passed = tc.get("pass", 0)
    failed = tc.get("fail", 0)
    mark = "[green]✓[/green]" if failed == 0 else "[red]✗[/red]"
    return f"{passed}/{total} {mark}"


@click.command()
def status():
    """Show all projects grouped by client with test health."""
    config_dir = os.environ.get("VIBE_CONFIG_DIR")
    config = VibeConfig(config_dir) if config_dir else VibeConfig()
    config.ensure_dirs()

    projects = config.load_projects()
    if not projects:
        console.print("No projects registered. Run [bold]vibe init[/bold] in a project directory.")
        return

    clients = config.load_clients()
    client_accounts = {c["name"]: c.get("account", "") for c in clients}

    # Group by client
    grouped = defaultdict(list)
    for p in projects:
        grouped[p["client"]].append(p)

    for client_name, client_projects in grouped.items():
        account = client_accounts.get(client_name, "")
        title = client_name.upper()
        if account:
            title += f" ({account})"

        table = Table(title=title, title_style="bold cyan")
        table.add_column("Project", style="white")
        table.add_column("Tests", justify="center")
        table.add_column("Stack", justify="center", style="dim")
        table.add_column("Last Active", justify="center")
        table.add_column("Status", style="dim")

        for p in client_projects:
            table.add_row(
                p["name"],
                _format_tests(p.get("testCount", {})),
                p.get("stack", ""),
                _time_ago(p.get("lastActive", "")),
                _get_status_line(p),
            )

        console.print(table)
        console.print()
