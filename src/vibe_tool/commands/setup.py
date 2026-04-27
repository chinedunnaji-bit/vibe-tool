import os
from pathlib import Path

import click
from rich.console import Console

from vibe_tool.config import VibeConfig
from vibe_tool.templates import get_global_claude_md_addition

console = Console()

MARKER = "Mandatory Quality Rules (added by vibe-tool)"


def get_claude_dir() -> Path:
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env) if env else Path.home() / ".claude"


@click.command()
def setup():
    """One-time machine setup: global CLAUDE.md rules, hooks, and config."""
    config_dir = os.environ.get("VIBE_CONFIG_DIR")
    config = VibeConfig(config_dir) if config_dir else VibeConfig()
    config.ensure_dirs()

    # Augment global CLAUDE.md
    claude_dir = get_claude_dir()
    claude_dir.mkdir(parents=True, exist_ok=True)
    claude_md = claude_dir / "CLAUDE.md"

    if claude_md.exists():
        existing = claude_md.read_text()
    else:
        existing = ""

    if MARKER not in existing:
        addition = get_global_claude_md_addition()
        claude_md.write_text(existing + addition)
        console.print("[green]Updated[/green] global CLAUDE.md with quality rules")
    else:
        console.print("Global CLAUDE.md already has quality rules — skipped")

    # Add first client
    clients = config.load_clients()
    if not clients:
        console.print("\n[bold]Let's add your first client.[/bold]")
        name = click.prompt("Client name")
        account = click.prompt("Claude account alias (optional, press Enter to skip)", default="")
        config.add_client(name, account)
        console.print(f"[green]Added client:[/green] {name}")
    else:
        console.print(f"Found {len(clients)} existing client(s) — skipped")

    console.print("\n[bold green]Setup complete.[/bold green]")
    console.print("Next: cd into a project and run [bold]vibe init[/bold]")
