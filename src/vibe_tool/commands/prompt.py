from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from vibe_tool.prompts import list_templates, load_template

console = Console()


@click.group()
def prompt():
    """Manage prompt templates."""
    pass


@prompt.command("list")
def list_prompts():
    """List available prompt templates."""
    prompts_dir = Path.cwd() / ".vibe" / "prompts"
    templates = list_templates(prompts_dir)
    if not templates:
        console.print("No templates found. Run [bold]vibe init[/bold] to install defaults.")
        return

    table = Table(title="Prompt Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="dim")

    for t in templates:
        table.add_row(t["name"], t["description"][:60])

    console.print(table)
    console.print("\nUse [bold]vibe prompt show <name>[/bold] to view a template")


@prompt.command()
@click.argument("name")
def show(name: str):
    """Print a prompt template."""
    prompts_dir = Path.cwd() / ".vibe" / "prompts"
    content = load_template(prompts_dir, name)
    if content is None:
        console.print(f"[red]Template '{name}' not found.[/red]")
        raise SystemExit(1)
    console.print(content)


@prompt.command()
@click.argument("name")
def copy(name: str):
    """Copy a prompt template to clipboard."""
    prompts_dir = Path.cwd() / ".vibe" / "prompts"
    content = load_template(prompts_dir, name)
    if content is None:
        console.print(f"[red]Template '{name}' not found.[/red]")
        raise SystemExit(1)

    try:
        import subprocess
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(content.encode())
        console.print(f"[green]Copied '{name}' to clipboard.[/green]")
    except FileNotFoundError:
        try:
            process = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            process.communicate(content.encode())
            console.print(f"[green]Copied '{name}' to clipboard.[/green]")
        except FileNotFoundError:
            console.print(content)
            console.print("\n[yellow]Clipboard not available — printed template above.[/yellow]")


@prompt.command()
@click.argument("name")
def create(name: str):
    """Create a custom prompt template."""
    prompts_dir = Path.cwd() / ".vibe" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    target = prompts_dir / f"{name}.md"
    if target.exists():
        console.print(f"[red]Template '{name}' already exists.[/red]")
        raise SystemExit(1)

    console.print(f"Enter template content (press Ctrl+D or Ctrl+Z when done):")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    content = "\n".join(lines) + "\n"
    target.write_text(content)
    console.print(f"[green]Created[/green] .vibe/prompts/{name}.md")
