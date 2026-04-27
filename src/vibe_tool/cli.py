import click

from vibe_tool.commands.client import client
from vibe_tool.commands.setup import setup


@click.group()
@click.version_option()
def cli():
    """Vibe — Claude Code productivity tool.

    Quality gates and context continuity across machines and accounts.
    """
    pass


cli.add_command(client)
cli.add_command(setup)
