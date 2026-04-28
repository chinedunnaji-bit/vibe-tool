import os
import stat
from pathlib import Path

import click
from rich.console import Console

from vibe_tool.config import VibeConfig
from vibe_tool.detect import detect_project
from vibe_tool.errors import HEADER as ERRORS_HEADER
from vibe_tool.indexer import scan_project, render_index
from vibe_tool.prompts import install_templates
from vibe_tool.templates import (
    get_git_hook_pre_commit,
    get_git_hook_pre_push,
    get_github_actions_ci,
    get_project_claude_md,
)

console = Console()


@click.command()
def init():
    """Scaffold a new project with tests, hooks, CI, and context."""
    config_dir = os.environ.get("VIBE_CONFIG_DIR")
    config = VibeConfig(config_dir) if config_dir else VibeConfig()
    config.ensure_dirs()

    project_dir = Path.cwd()
    project_name = project_dir.name

    # 1. Select client
    clients = config.load_clients()
    if not clients:
        console.print("[red]No clients configured.[/red] Run [bold]vibe setup[/bold] first.")
        raise SystemExit(1)

    if len(clients) == 1:
        selected_client = clients[0]["name"]
        console.print(f"Using client: [bold]{selected_client}[/bold]")
    else:
        console.print("\n[bold]Select client:[/bold]")
        for i, c in enumerate(clients, 1):
            label = f"{c['name']}"
            if c.get("account"):
                label += f" ({c['account']})"
            console.print(f"  {i}. {label}")
        client_idx = click.prompt("Choice", type=int) - 1
        selected_client = clients[client_idx]["name"]

    # 2. Auto-detect project type and stack
    detected = detect_project(project_dir)
    project_type = detected["project_type"]
    stack = detected["stack"]

    if stack != "other":
        console.print(f"\nDetected: [bold]{detected['label']}[/bold]")
    else:
        console.print("\n[dim]No framework detected — using generic defaults[/dim]")

    # 3. Create project CLAUDE.md
    claude_md = project_dir / "CLAUDE.md"
    claude_md.write_text(get_project_claude_md(project_name, project_type, stack))
    console.print("[green]Created[/green] CLAUDE.md")

    # 4. Install git hooks
    hooks_dir = project_dir / ".git" / "hooks"
    if hooks_dir.parent.exists():
        hooks_dir.mkdir(parents=True, exist_ok=True)

        pre_commit = hooks_dir / "pre-commit"
        pre_commit.write_text(get_git_hook_pre_commit(project_type, stack))
        pre_commit.chmod(pre_commit.stat().st_mode | stat.S_IEXEC)

        pre_push = hooks_dir / "pre-push"
        pre_push.write_text(get_git_hook_pre_push(project_type, stack))
        pre_push.chmod(pre_push.stat().st_mode | stat.S_IEXEC)

        console.print("[green]Installed[/green] git hooks")
    else:
        console.print("[yellow]Warning:[/yellow] not a git repo — skipped git hooks")

    # 5. Create CI pipeline
    ci_dir = project_dir / ".github" / "workflows"
    ci_dir.mkdir(parents=True, exist_ok=True)
    ci_file = ci_dir / "ci.yml"
    ci_file.write_text(get_github_actions_ci(project_type, stack))
    console.print("[green]Created[/green] CI pipeline")

    # 6. Register project
    config.add_project(
        name=project_name,
        path=str(project_dir),
        client=selected_client,
        project_type=project_type,
        stack=stack,
    )
    console.print("[green]Registered[/green] project")

    # 7. Create .vibe/ directory with context intelligence
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)

    # 8. Run codebase index
    scanned = scan_project(project_dir)
    if scanned:
        md = render_index(scanned, project_dir)
        (vibe_dir / "codebase.md").write_text(md)
        console.print(f"[green]Indexed[/green] {len(scanned)} source files")
    else:
        console.print("[dim]No source files to index yet[/dim]")

    # 9. Create empty error memory
    errors_file = vibe_dir / "errors.md"
    if not errors_file.exists():
        errors_file.write_text(ERRORS_HEADER)
    console.print("[green]Created[/green] error memory")

    # 10. Install prompt templates
    install_templates(vibe_dir / "prompts")
    console.print("[green]Installed[/green] prompt templates")

    # 11. Add session-context.md to .gitignore
    gitignore = project_dir / ".gitignore"
    gitignore_content = gitignore.read_text() if gitignore.exists() else ""
    if ".vibe/session-context.md" not in gitignore_content:
        with open(gitignore, "a") as f:
            if gitignore_content and not gitignore_content.endswith("\n"):
                f.write("\n")
            f.write("# Vibe tool ephemeral context\n.vibe/session-context.md\n.vibe/.session-start-sha\n")
    console.print("[green]Updated[/green] .gitignore")

    console.print(f"\n[bold green]Project initialized.[/bold green] Open Claude Code and start building.")
