import subprocess
from pathlib import Path

import click
from rich.console import Console

console = Console()

CONTEXT_FILES = ["CLAUDE.md", ".claude"]


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _is_git_repo(path: Path) -> bool:
    result = _run_git(["rev-parse", "--is-inside-work-tree"], path)
    return result.returncode == 0


def _has_remote(path: Path) -> bool:
    result = _run_git(["remote"], path)
    return result.returncode == 0 and result.stdout.strip() != ""


def _sync_push(project_dir: Path):
    # Stage context files
    staged = False
    for name in CONTEXT_FILES:
        target = project_dir / name
        if target.exists():
            result = _run_git(["add", name], project_dir)
            if result.returncode == 0:
                staged = True

    if not staged:
        console.print("No context files found to sync.")
        return

    # Check if there are staged changes
    diff = _run_git(["diff", "--cached", "--quiet"], project_dir)
    if diff.returncode == 0:
        console.print("No context changes to commit.")
        return

    # Commit
    _run_git(["commit", "-m", "chore: vibe sync context update"], project_dir)
    console.print("[green]Committed[/green] context changes")

    # Push if remote exists
    if _has_remote(project_dir):
        result = _run_git(["push"], project_dir)
        if result.returncode == 0:
            console.print("[green]Pushed[/green] to remote")
        else:
            console.print(f"[yellow]Push failed:[/yellow] {result.stderr.strip()}")
    else:
        console.print("[dim]No remote configured — skipped push[/dim]")


def _sync_pull(project_dir: Path):
    if not _has_remote(project_dir):
        console.print("[dim]No remote configured — skipped pull[/dim]")
        return

    result = _run_git(["pull", "--rebase"], project_dir)
    if result.returncode == 0:
        console.print("[green]Pulled[/green] latest from remote")
    else:
        console.print(f"[yellow]Pull failed:[/yellow] {result.stderr.strip()}")


@click.command()
@click.argument("direction", default="both", type=click.Choice(["push", "pull", "both"]))
def sync(direction: str):
    """Sync project context (CLAUDE.md, .claude/) via Git.

    DIRECTION: push, pull, or both (default: both)
    """
    project_dir = Path.cwd()

    if not _is_git_repo(project_dir):
        console.print("[red]Error:[/red] Not a git repository.")
        raise SystemExit(1)

    if direction in ("pull", "both"):
        _sync_pull(project_dir)

    if direction in ("push", "both"):
        _sync_push(project_dir)

    console.print("[bold green]Sync complete.[/bold green]")
