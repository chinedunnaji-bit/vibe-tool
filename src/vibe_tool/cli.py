import click


@click.group()
@click.version_option()
def cli():
    """Vibe — Claude Code productivity tool.

    Quality gates and context continuity across machines and accounts.
    """
    pass
