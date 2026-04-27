import os

import click
from rich.console import Console
from rich.table import Table

from vibe_tool.config import VibeConfig

console = Console()


def get_config() -> VibeConfig:
    config_dir = os.environ.get("VIBE_CONFIG_DIR")
    config = VibeConfig(config_dir) if config_dir else VibeConfig()
    config.ensure_dirs()
    return config


@click.group()
def client():
    """Manage clients and accounts."""
    pass


@client.command()
@click.option("--name", prompt="Client name", help="Name for this client")
@click.option("--account", default="", help="Claude account alias (optional)")
def add(name: str, account: str):
    """Register a new client."""
    config = get_config()
    try:
        config.add_client(name, account)
        console.print(f"[green]Added client:[/green] {name}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@client.command("list")
def list_clients():
    """List all configured clients."""
    config = get_config()
    clients = config.load_clients()
    if not clients:
        console.print("No clients configured. Run [bold]vibe client add[/bold] to add one.")
        return
    table = Table(title="Clients")
    table.add_column("Name", style="cyan")
    table.add_column("Account", style="green")
    for c in clients:
        table.add_row(c["name"], c.get("account", ""))
    console.print(table)
