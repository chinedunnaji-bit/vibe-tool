import os
import shutil
import subprocess
import sys
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


def _ensure_vibe_on_path():
    """Ensure the 'vibe' command is accessible on PATH."""
    # Find where pip installed the vibe script
    user_bin = Path.home() / "Library" / "Python" / f"{sys.version_info.major}.{sys.version_info.minor}" / "bin"
    if not user_bin.exists():
        user_bin = Path.home() / ".local" / "bin"  # Linux

    if not (user_bin / "vibe").exists():
        return  # can't find it, skip

    # Detect shell config file
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        rc_file = Path.home() / ".zshrc"
    elif "bash" in shell:
        rc_file = Path.home() / ".bashrc"
    else:
        rc_file = Path.home() / ".profile"

    rc_content = rc_file.read_text() if rc_file.exists() else ""

    if str(user_bin) in rc_content:
        return  # already added

    path_line = f'export PATH="$PATH:{user_bin}"'

    with open(rc_file, "a") as f:
        f.write(f'\n# Added by vibe-tool\n{path_line}\n')

    console.print(f"[green]Added[/green] {user_bin} to PATH in {rc_file.name}")
    console.print("[yellow]Restart your terminal[/yellow] (or run [bold]source ~/{rc_file.name}[/bold]) for `vibe` to work")


@click.command()
def setup():
    """One-time machine setup: global CLAUDE.md rules, hooks, and config."""
    config_dir = os.environ.get("VIBE_CONFIG_DIR")
    config = VibeConfig(config_dir) if config_dir else VibeConfig()
    config.ensure_dirs()

    # Ensure vibe is on PATH
    _ensure_vibe_on_path()

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
