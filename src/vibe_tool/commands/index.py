import os
from pathlib import Path

import click
from rich.console import Console

from vibe_tool.indexer import scan_project, render_index

console = Console()


@click.command()
@click.option("--deep", is_flag=True, help="Use Claude for richer analysis (costs tokens)")
def index(deep: bool):
    """Generate codebase knowledge base in .vibe/codebase.md."""
    project_dir = Path.cwd()

    if deep:
        console.print("[yellow]--deep mode not yet implemented. Using pattern-based scan.[/yellow]")

    console.print("Scanning codebase...")
    scanned = scan_project(project_dir)

    if not scanned:
        console.print("[yellow]No source files found.[/yellow]")
        return

    # Ensure .vibe/ dir exists
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)

    # Write index
    md = render_index(scanned, project_dir)
    (vibe_dir / "codebase.md").write_text(md)

    console.print(f"[green]Indexed {len(scanned)} files[/green] → .vibe/codebase.md")
