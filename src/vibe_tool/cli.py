import click

from vibe_tool.commands.client import client
from vibe_tool.commands.error import error
from vibe_tool.commands.index import index
from vibe_tool.commands.init import init
from vibe_tool.commands.setup import setup
from vibe_tool.commands.status import status
from vibe_tool.commands.sync import sync


@click.group()
@click.version_option()
def cli():
    """Vibe — Claude Code productivity tool.

    Quality gates and context continuity across machines and accounts.
    """
    pass


cli.add_command(client)
cli.add_command(error)
cli.add_command(index)
cli.add_command(init)
cli.add_command(setup)
cli.add_command(status)
cli.add_command(sync)
