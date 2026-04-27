from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from vibe_tool.errors import add_error, load_errors

console = Console()


@click.group()
def error():
    """Manage error memory."""
    pass


@error.command()
def add():
    """Record a new error and its solution."""
    project_dir = Path.cwd()
    errors_file = project_dir / ".vibe" / "errors.md"

    title = click.prompt("Error title (short)")
    when = click.prompt("When does it happen")
    cause = click.prompt("Root cause")
    fix = click.prompt("Fix / solution")

    add_error(errors_file, title=title, when=when, cause=cause, fix=fix)
    console.print(f"[green]Added[/green] error to .vibe/errors.md")


@error.command("list")
def list_errors():
    """List all recorded errors."""
    project_dir = Path.cwd()
    errors_file = project_dir / ".vibe" / "errors.md"

    entries = load_errors(errors_file)
    if not entries:
        console.print("No errors recorded. Use [bold]vibe error add[/bold] to record one.")
        return

    table = Table(title="Error Memory")
    table.add_column("ID", style="red")
    table.add_column("Title", style="white")
    table.add_column("Fix", style="green")
    table.add_column("Date", style="dim")

    for e in entries:
        table.add_row(e["id"], e["title"], e["fix"][:50], e["date"])

    console.print(table)
