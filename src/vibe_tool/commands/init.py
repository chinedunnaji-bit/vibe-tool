import os
import stat
from pathlib import Path

import click
from rich.console import Console

from vibe_tool.config import VibeConfig
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

PROJECT_TYPES = [
    ("web", "Web app"),
    ("mobile", "Mobile app"),
    ("api", "API / Backend"),
    ("cli", "CLI tool"),
    ("fullstack", "Full-stack (web + API)"),
    ("other", "Other"),
]

STACKS = {
    "web": [("next", "Next.js"), ("vite", "React + Vite"), ("svelte", "SvelteKit"), ("other", "Other")],
    "mobile": [("expo", "Expo / React Native"), ("other", "Other")],
    "api": [("express", "Express"), ("fastify", "Fastify"), ("hono", "Hono"), ("fastapi", "FastAPI (Python)"), ("flask", "Flask (Python)"), ("django", "Django (Python)"), ("other", "Other")],
    "cli": [("python", "Python (Click/Typer)"), ("node", "Node.js"), ("go", "Go"), ("rust", "Rust"), ("other", "Other")],
    "fullstack": [("next", "Next.js (full-stack)"), ("vite-express", "React + Express"), ("vite-fastapi", "React + FastAPI"), ("other", "Other")],
    "other": [("python", "Python"), ("node", "Node.js"), ("go", "Go"), ("rust", "Rust"), ("other", "Other")],
}


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

    console.print("\n[bold]Select client:[/bold]")
    for i, c in enumerate(clients, 1):
        label = f"{c['name']}"
        if c.get("account"):
            label += f" ({c['account']})"
        console.print(f"  {i}. {label}")

    client_idx = click.prompt("Choice", type=int) - 1
    selected_client = clients[client_idx]["name"]

    # 2. Select project type
    console.print("\n[bold]What are you building?[/bold]")
    for i, (_, label) in enumerate(PROJECT_TYPES, 1):
        console.print(f"  {i}. {label}")

    type_idx = click.prompt("Choice", type=int) - 1
    project_type = PROJECT_TYPES[type_idx][0]

    # 3. Select stack
    stack_options = STACKS[project_type]
    console.print("\n[bold]Select stack:[/bold]")
    for i, (_, label) in enumerate(stack_options, 1):
        console.print(f"  {i}. {label}")

    stack_idx = click.prompt("Choice", type=int) - 1
    stack = stack_options[stack_idx][0]

    # 4. Create project CLAUDE.md
    claude_md = project_dir / "CLAUDE.md"
    claude_md.write_text(get_project_claude_md(project_name, project_type, stack))
    console.print("[green]Created[/green] CLAUDE.md")

    # 5. Install git hooks
    hooks_dir = project_dir / ".git" / "hooks"
    if hooks_dir.parent.exists():
        hooks_dir.mkdir(parents=True, exist_ok=True)

        pre_commit = hooks_dir / "pre-commit"
        pre_commit.write_text(get_git_hook_pre_commit(project_type, stack))
        pre_commit.chmod(pre_commit.stat().st_mode | stat.S_IEXEC)

        pre_push = hooks_dir / "pre-push"
        pre_push.write_text(get_git_hook_pre_push(project_type, stack))
        pre_push.chmod(pre_push.stat().st_mode | stat.S_IEXEC)

        console.print("[green]Installed[/green] git hooks (pre-commit, pre-push)")
    else:
        console.print("[yellow]Warning:[/yellow] not a git repo — skipped git hooks")

    # 6. Create CI pipeline
    ci_dir = project_dir / ".github" / "workflows"
    ci_dir.mkdir(parents=True, exist_ok=True)
    ci_file = ci_dir / "ci.yml"
    ci_file.write_text(get_github_actions_ci(project_type, stack))
    console.print("[green]Created[/green] CI pipeline (.github/workflows/ci.yml)")

    # 7. Register project
    config.add_project(
        name=project_name,
        path=str(project_dir),
        client=selected_client,
        project_type=project_type,
        stack=stack,
    )
    console.print("[green]Registered[/green] project in vibe index")

    # 8. Create .vibe/ directory with v2 context intelligence
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)

    # 9. Run codebase index
    scanned = scan_project(project_dir)
    if scanned:
        md = render_index(scanned, project_dir)
        (vibe_dir / "codebase.md").write_text(md)
        console.print(f"[green]Indexed[/green] {len(scanned)} source files")
    else:
        console.print("[dim]No source files to index yet[/dim]")

    # 10. Create empty error memory
    errors_file = vibe_dir / "errors.md"
    if not errors_file.exists():
        errors_file.write_text(ERRORS_HEADER)
    console.print("[green]Created[/green] error memory (.vibe/errors.md)")

    # 11. Install prompt templates
    install_templates(vibe_dir / "prompts")
    console.print("[green]Installed[/green] prompt templates (.vibe/prompts/)")

    # 12. Add session-context.md to .gitignore
    gitignore = project_dir / ".gitignore"
    gitignore_content = gitignore.read_text() if gitignore.exists() else ""
    if ".vibe/session-context.md" not in gitignore_content:
        with open(gitignore, "a") as f:
            if gitignore_content and not gitignore_content.endswith("\n"):
                f.write("\n")
            f.write("# Vibe tool ephemeral context\n.vibe/session-context.md\n.vibe/.session-start-sha\n")
    console.print("[green]Updated[/green] .gitignore")

    console.print(f"\n[bold green]Project initialized.[/bold green] Open Claude Code and start building.")
