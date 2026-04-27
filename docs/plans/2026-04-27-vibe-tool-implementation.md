# Vibe Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI tool (`vibe`) that enforces automated quality gates and context continuity for Claude Code projects across multiple machines and accounts.

**Architecture:** Python package using Click for CLI, Rich for terminal UI, and subprocess for Git operations. Config stored in `~/.vibe/` as JSON. Templates for CLAUDE.md, git hooks, and CI pipelines stored as Python string constants.

**Tech Stack:** Python 3.11+, Click, Rich, pytest

---

### Task 1: Python Package Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/vibe_tool/__init__.py`
- Create: `src/vibe_tool/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

Create `tests/__init__.py`:
```python
```

Create `tests/test_cli.py`:
```python
from click.testing import CliRunner
from vibe_tool.cli import cli


def test_cli_shows_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "vibe" in result.output.lower()
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/chinedunnaji/Documents/workspace/VIbe-tool && python -m pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vibe_tool'`

**Step 3: Write minimal implementation**

Create `pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "vibe-tool"
version = "0.1.0"
description = "CLI tool for Claude Code productivity — quality gates and context continuity"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
    "rich>=13.0",
]

[project.scripts]
vibe = "vibe_tool.cli:cli"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Create `src/vibe_tool/__init__.py`:
```python
__version__ = "0.1.0"
```

Create `src/vibe_tool/cli.py`:
```python
import click


@click.group()
@click.version_option()
def cli():
    """Vibe — Claude Code productivity tool.

    Quality gates and context continuity across machines and accounts.
    """
    pass
```

**Step 4: Install package in dev mode and run test**

Run: `cd /Users/chinedunnaji/Documents/workspace/VIbe-tool && pip install -e ".[dev]" 2>/dev/null || pip install -e . && python -m pytest tests/test_cli.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: initialize Python package skeleton with CLI entry point"
```

---

### Task 2: Config Module

**Files:**
- Create: `src/vibe_tool/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing tests**

Create `tests/test_config.py`:
```python
import json
from pathlib import Path

from vibe_tool.config import VibeConfig


def test_init_creates_config_dir(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    assert (tmp_path / ".vibe").is_dir()


def test_load_clients_empty(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    assert config.load_clients() == []


def test_add_client(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    config.add_client("acme-corp", "claude-account1")
    clients = config.load_clients()
    assert len(clients) == 1
    assert clients[0]["name"] == "acme-corp"
    assert clients[0]["account"] == "claude-account1"


def test_add_duplicate_client_raises(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    config.add_client("acme-corp", "claude-account1")
    import pytest
    with pytest.raises(ValueError, match="already exists"):
        config.add_client("acme-corp", "claude-account2")


def test_load_projects_empty(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    assert config.load_projects() == []


def test_add_project(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    config.add_project(
        name="marketplace",
        path="/some/path",
        client="acme-corp",
        project_type="web",
        stack="next",
    )
    projects = config.load_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == "marketplace"
    assert projects[0]["client"] == "acme-corp"


def test_update_project_tests(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    config.add_project(
        name="marketplace",
        path="/some/path",
        client="acme-corp",
        project_type="web",
        stack="next",
    )
    config.update_project_tests("marketplace", passed=22, failed=2, total=24)
    projects = config.load_projects()
    assert projects[0]["testCount"] == {"pass": 22, "fail": 2, "total": 24}
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vibe_tool.config'`

**Step 3: Write implementation**

Create `src/vibe_tool/config.py`:
```python
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".vibe"


class VibeConfig:
    def __init__(self, config_dir: Path = DEFAULT_CONFIG_DIR):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.projects_file = self.config_dir / "projects.json"

    def ensure_dirs(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    def _write_json(self, path: Path, data: dict):
        path.write_text(json.dumps(data, indent=2) + "\n")

    # --- Clients ---

    def load_clients(self) -> list[dict]:
        data = self._read_json(self.config_file)
        return data.get("clients", [])

    def add_client(self, name: str, account: str = ""):
        data = self._read_json(self.config_file)
        clients = data.get("clients", [])
        if any(c["name"] == name for c in clients):
            raise ValueError(f"Client '{name}' already exists")
        clients.append({"name": name, "account": account})
        data["clients"] = clients
        self._write_json(self.config_file, data)

    # --- Projects ---

    def load_projects(self) -> list[dict]:
        data = self._read_json(self.projects_file)
        return data.get("projects", [])

    def add_project(self, name: str, path: str, client: str, project_type: str, stack: str):
        data = self._read_json(self.projects_file)
        projects = data.get("projects", [])
        now = datetime.now(timezone.utc).isoformat()
        projects.append({
            "name": name,
            "path": path,
            "client": client,
            "type": project_type,
            "stack": stack,
            "created": now[:10],
            "lastActive": now,
            "testCount": {"pass": 0, "fail": 0, "total": 0},
        })
        data["projects"] = projects
        self._write_json(self.projects_file, data)

    def update_project_tests(self, name: str, passed: int, failed: int, total: int):
        data = self._read_json(self.projects_file)
        projects = data.get("projects", [])
        for p in projects:
            if p["name"] == name:
                p["testCount"] = {"pass": passed, "fail": failed, "total": total}
                p["lastActive"] = datetime.now(timezone.utc).isoformat()
                break
        data["projects"] = projects
        self._write_json(self.projects_file, data)
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_config.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/config.py tests/test_config.py
git commit -m "feat: add config module for client and project management"
```

---

### Task 3: `vibe client add` and `vibe client list`

**Files:**
- Create: `src/vibe_tool/commands/client.py`
- Create: `src/vibe_tool/commands/__init__.py`
- Modify: `src/vibe_tool/cli.py`
- Create: `tests/test_client_cmd.py`

**Step 1: Write the failing tests**

Create `tests/test_client_cmd.py`:
```python
from click.testing import CliRunner
from vibe_tool.cli import cli


def test_client_add(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    runner = CliRunner()
    result = runner.invoke(cli, ["client", "add", "--name", "acme-corp", "--account", "claude-1"])
    assert result.exit_code == 0
    assert "acme-corp" in result.output


def test_client_list_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    runner = CliRunner()
    result = runner.invoke(cli, ["client", "list"])
    assert result.exit_code == 0
    assert "No clients" in result.output


def test_client_list_shows_added(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    runner = CliRunner()
    runner.invoke(cli, ["client", "add", "--name", "acme-corp", "--account", "claude-1"])
    result = runner.invoke(cli, ["client", "list"])
    assert result.exit_code == 0
    assert "acme-corp" in result.output
    assert "claude-1" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_client_cmd.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/commands/__init__.py`:
```python
```

Create `src/vibe_tool/commands/client.py`:
```python
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
```

Modify `src/vibe_tool/cli.py`:
```python
import click

from vibe_tool.commands.client import client


@click.group()
@click.version_option()
def cli():
    """Vibe — Claude Code productivity tool.

    Quality gates and context continuity across machines and accounts.
    """
    pass


cli.add_command(client)
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_client_cmd.py tests/test_cli.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/commands/ src/vibe_tool/cli.py tests/test_client_cmd.py
git commit -m "feat: add vibe client add/list commands"
```

---

### Task 4: Templates Module

**Files:**
- Create: `src/vibe_tool/templates.py`
- Create: `tests/test_templates.py`

**Step 1: Write the failing tests**

Create `tests/test_templates.py`:
```python
from vibe_tool.templates import (
    get_global_claude_md_addition,
    get_project_claude_md,
    get_git_hook_pre_commit,
    get_git_hook_pre_push,
    get_github_actions_ci,
)


def test_global_claude_md_contains_quality_rules():
    content = get_global_claude_md_addition()
    assert "Always write tests before implementation" in content
    assert "Never say" in content
    assert "TDD" in content or "test" in content.lower()


def test_project_claude_md_contains_placeholders():
    content = get_project_claude_md("my-app", "web", "next")
    assert "my-app" in content
    assert "## What this is" in content
    assert "## How to run" in content
    assert "## Current state" in content


def test_git_hook_pre_commit_is_executable_script():
    content = get_git_hook_pre_commit("web", "next")
    assert content.startswith("#!/")
    assert "lint" in content.lower() or "check" in content.lower()


def test_git_hook_pre_push_runs_tests():
    content = get_git_hook_pre_push("web", "next")
    assert content.startswith("#!/")
    assert "test" in content.lower()


def test_github_actions_web_next():
    content = get_github_actions_ci("web", "next")
    assert "npm" in content or "pnpm" in content
    assert "test" in content


def test_github_actions_api_python():
    content = get_github_actions_ci("api", "python")
    assert "pytest" in content
    assert "ruff" in content or "lint" in content
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_templates.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementation**

Create `src/vibe_tool/templates.py`:
```python
def get_global_claude_md_addition() -> str:
    return """\

## Mandatory Quality Rules (added by vibe-tool)

1. Always write tests before implementation (TDD). Write the test, run it to confirm it fails, then implement.
2. Always run the full test suite before claiming any task is complete.
3. Never say "done", "complete", or "finished" without pasting the actual test output as proof.
4. If any test fails, fix it before moving on. Do not ask the user to fix it.
5. After completing a feature, run the app/server and verify it works end-to-end.
6. When modifying existing code, run existing tests FIRST to establish a baseline, then make changes, then run tests again.
7. Update the project CLAUDE.md with any architectural decisions or changes after each milestone.
8. Update Claude Code memory after completing significant milestones.
9. Write behavioral tests — test what the code does, not how it does it. Test inputs and outputs, not internal implementation details.
10. If unsure about a requirement, ask — do not guess and ship.
"""


def get_project_claude_md(name: str, project_type: str, stack: str) -> str:
    commands = _get_commands_for_stack(project_type, stack)
    return f"""# {name}

## What this is
[Describe what this project does — updated after first session]

## Architecture
[Updated by Claude as the project evolves]

## How to run
- `{commands['dev']}` — start dev server
- `{commands['test']}` — run tests
- `{commands['lint']}` — lint

## Key decisions
[Updated by Claude as decisions are made]

## Current state
[Updated by Claude after each session]
"""


def _get_commands_for_stack(project_type: str, stack: str) -> dict:
    commands = {
        ("web", "next"): {"dev": "npm run dev", "test": "npm test", "lint": "npm run lint"},
        ("web", "vite"): {"dev": "npm run dev", "test": "npx vitest run", "lint": "npm run lint"},
        ("mobile", "react-native"): {"dev": "npx expo start", "test": "npm test", "lint": "npm run lint"},
        ("mobile", "expo"): {"dev": "npx expo start", "test": "npm test", "lint": "npm run lint"},
        ("api", "express"): {"dev": "npm run dev", "test": "npx vitest run", "lint": "npm run lint"},
        ("api", "fastify"): {"dev": "npm run dev", "test": "npx vitest run", "lint": "npm run lint"},
        ("api", "hono"): {"dev": "npm run dev", "test": "npx vitest run", "lint": "npm run lint"},
        ("api", "python"): {"dev": "uvicorn main:app --reload", "test": "pytest", "lint": "ruff check ."},
        ("api", "fastapi"): {"dev": "uvicorn main:app --reload", "test": "pytest", "lint": "ruff check ."},
        ("api", "flask"): {"dev": "flask run --reload", "test": "pytest", "lint": "ruff check ."},
    }
    return commands.get((project_type, stack), {"dev": "echo 'configure dev command'", "test": "echo 'configure test command'", "lint": "echo 'configure lint command'"})


def get_git_hook_pre_commit(project_type: str, stack: str) -> str:
    if stack in ("python", "fastapi", "flask"):
        return """#!/bin/sh
echo "Running lint checks..."
ruff check . || { echo "Lint failed. Fix errors before committing."; exit 1; }
echo "Lint passed."
"""
    return """#!/bin/sh
echo "Running lint checks..."
npm run lint 2>/dev/null || npx eslint . || { echo "Lint failed. Fix errors before committing."; exit 1; }
echo "Lint passed."
"""


def get_git_hook_pre_push(project_type: str, stack: str) -> str:
    if stack in ("python", "fastapi", "flask"):
        return """#!/bin/sh
echo "Running tests before push..."
pytest || { echo "Tests failed. Fix before pushing."; exit 1; }
echo "All tests passed."
"""
    return """#!/bin/sh
echo "Running tests before push..."
npm test 2>/dev/null || npx vitest run || { echo "Tests failed. Fix before pushing."; exit 1; }
echo "All tests passed."
"""


def get_github_actions_ci(project_type: str, stack: str) -> str:
    if stack in ("python", "fastapi", "flask"):
        return """name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]" 2>/dev/null || pip install -e .
      - name: Lint
        run: ruff check .
      - name: Test
        run: pytest -v
"""
    return f"""name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - name: Lint
        run: npm run lint
      - name: Test
        run: npm test
"""
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_templates.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/templates.py tests/test_templates.py
git commit -m "feat: add templates for CLAUDE.md, git hooks, and CI pipelines"
```

---

### Task 5: `vibe setup` Command

**Files:**
- Create: `src/vibe_tool/commands/setup.py`
- Create: `tests/test_setup_cmd.py`
- Modify: `src/vibe_tool/cli.py`

**Step 1: Write the failing tests**

Create `tests/test_setup_cmd.py`:
```python
import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def test_setup_creates_vibe_dir(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# Existing rules\n")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    result = runner.invoke(cli, ["setup"], input="acme-corp\nclaude-1\n")
    assert result.exit_code == 0
    assert vibe_dir.is_dir()


def test_setup_augments_claude_md(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# Existing rules\n")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    result = runner.invoke(cli, ["setup"], input="acme-corp\nclaude-1\n")
    assert result.exit_code == 0

    content = claude_dir.joinpath("CLAUDE.md").read_text()
    assert "Existing rules" in content
    assert "Mandatory Quality Rules" in content


def test_setup_does_not_duplicate_rules(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# Existing rules\n")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    runner.invoke(cli, ["setup"], input="acme-corp\nclaude-1\n")
    runner.invoke(cli, ["setup"], input="other\nclaude-2\n")

    content = claude_dir.joinpath("CLAUDE.md").read_text()
    assert content.count("Mandatory Quality Rules") == 1


def test_setup_adds_first_client(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    result = runner.invoke(cli, ["setup"], input="acme-corp\nclaude-1\n")
    assert result.exit_code == 0
    assert "acme-corp" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_setup_cmd.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/commands/setup.py`:
```python
import os
from pathlib import Path

import click
from rich.console import Console

from vibe_tool.config import VibeConfig
from vibe_tool.templates import get_global_claude_md_addition

console = Console()

MARKER = "Mandatory Quality Rules (added by vibe-tool)"


def get_claude_dir() -> Path:
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env) if env else Path.home() / ".claude"


@click.command()
def setup():
    """One-time machine setup: global CLAUDE.md rules, hooks, and config."""
    config_dir = os.environ.get("VIBE_CONFIG_DIR")
    config = VibeConfig(config_dir) if config_dir else VibeConfig()
    config.ensure_dirs()

    # Augment global CLAUDE.md
    claude_dir = get_claude_dir()
    claude_dir.mkdir(parents=True, exist_ok=True)
    claude_md = claude_dir / "CLAUDE.md"

    if claude_md.exists():
        existing = claude_md.read_text()
    else:
        existing = ""

    if MARKER not in existing:
        addition = get_global_claude_md_addition()
        claude_md.write_text(existing + addition)
        console.print("[green]Updated[/green] global CLAUDE.md with quality rules")
    else:
        console.print("Global CLAUDE.md already has quality rules — skipped")

    # Add first client
    clients = config.load_clients()
    if not clients:
        console.print("\n[bold]Let's add your first client.[/bold]")
        name = click.prompt("Client name")
        account = click.prompt("Claude account alias (optional, press Enter to skip)", default="")
        config.add_client(name, account)
        console.print(f"[green]Added client:[/green] {name}")
    else:
        console.print(f"Found {len(clients)} existing client(s) — skipped")

    console.print("\n[bold green]Setup complete.[/bold green]")
    console.print("Next: cd into a project and run [bold]vibe init[/bold]")
```

Update `src/vibe_tool/cli.py` to add the setup command:
```python
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
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_setup_cmd.py tests/test_cli.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/commands/setup.py src/vibe_tool/cli.py tests/test_setup_cmd.py
git commit -m "feat: add vibe setup command for one-time machine configuration"
```

---

### Task 6: `vibe init` Command

**Files:**
- Create: `src/vibe_tool/commands/init.py`
- Create: `tests/test_init_cmd.py`
- Modify: `src/vibe_tool/cli.py`

**Step 1: Write the failing tests**

Create `tests/test_init_cmd.py`:
```python
import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def _setup_env(tmp_path, monkeypatch):
    """Set up isolated vibe + claude config and a project directory."""
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    project_dir = tmp_path / "my-project"
    project_dir.mkdir()

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))
    monkeypatch.chdir(project_dir)

    # Pre-add a client
    from vibe_tool.config import VibeConfig
    config = VibeConfig(vibe_dir)
    config.ensure_dirs()
    config.add_client("acme-corp", "claude-1")

    # Init git in project dir
    os.system(f"cd {project_dir} && git init -q")

    return project_dir, vibe_dir


def test_init_creates_project_claude_md(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    # Select client 1, project type 1 (web), stack 1 (next)
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    assert (project_dir / "CLAUDE.md").exists()
    content = (project_dir / "CLAUDE.md").read_text()
    assert "## How to run" in content


def test_init_creates_git_hooks(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    pre_commit = project_dir / ".git" / "hooks" / "pre-commit"
    pre_push = project_dir / ".git" / "hooks" / "pre-push"
    assert pre_commit.exists()
    assert pre_push.exists()
    assert os.access(pre_commit, os.X_OK)


def test_init_creates_ci_pipeline(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    ci_file = project_dir / ".github" / "workflows" / "ci.yml"
    assert ci_file.exists()
    assert "test" in ci_file.read_text().lower()


def test_init_registers_project_in_index(tmp_path, monkeypatch):
    project_dir, vibe_dir = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0

    from vibe_tool.config import VibeConfig
    config = VibeConfig(vibe_dir)
    projects = config.load_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == "my-project"
    assert projects[0]["client"] == "acme-corp"


def test_init_python_api(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    # Select client 1, project type 3 (api), stack 4 (python/fastapi)
    result = runner.invoke(cli, ["init"], input="1\n3\n4\n")
    assert result.exit_code == 0
    content = (project_dir / "CLAUDE.md").read_text()
    assert "pytest" in content
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_init_cmd.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/commands/init.py`:
```python
import os
import stat
from pathlib import Path

import click
from rich.console import Console

from vibe_tool.config import VibeConfig
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
    ("api", "API"),
]

STACKS = {
    "web": [("next", "Next.js"), ("vite", "React + Vite")],
    "mobile": [("expo", "Expo / React Native")],
    "api": [("express", "Express"), ("fastify", "Fastify"), ("hono", "Hono"), ("fastapi", "FastAPI (Python)"), ("flask", "Flask (Python)")],
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

    # Normalize python stacks
    stack_key = stack
    if stack in ("fastapi", "flask"):
        stack_key = stack

    # 4. Create project CLAUDE.md
    claude_md = project_dir / "CLAUDE.md"
    claude_md.write_text(get_project_claude_md(project_name, project_type, stack_key))
    console.print("[green]Created[/green] CLAUDE.md")

    # 5. Install git hooks
    hooks_dir = project_dir / ".git" / "hooks"
    if hooks_dir.parent.exists():
        hooks_dir.mkdir(parents=True, exist_ok=True)

        pre_commit = hooks_dir / "pre-commit"
        pre_commit.write_text(get_git_hook_pre_commit(project_type, stack_key))
        pre_commit.chmod(pre_commit.stat().st_mode | stat.S_IEXEC)

        pre_push = hooks_dir / "pre-push"
        pre_push.write_text(get_git_hook_pre_push(project_type, stack_key))
        pre_push.chmod(pre_push.stat().st_mode | stat.S_IEXEC)

        console.print("[green]Installed[/green] git hooks (pre-commit, pre-push)")
    else:
        console.print("[yellow]Warning:[/yellow] not a git repo — skipped git hooks")

    # 6. Create CI pipeline
    ci_dir = project_dir / ".github" / "workflows"
    ci_dir.mkdir(parents=True, exist_ok=True)
    ci_file = ci_dir / "ci.yml"
    ci_file.write_text(get_github_actions_ci(project_type, stack_key))
    console.print("[green]Created[/green] CI pipeline (.github/workflows/ci.yml)")

    # 7. Register project
    config.add_project(
        name=project_name,
        path=str(project_dir),
        client=selected_client,
        project_type=project_type,
        stack=stack_key,
    )
    console.print(f"[green]Registered[/green] project in vibe index")

    console.print(f"\n[bold green]Project initialized.[/bold green] Open Claude Code and start building.")
```

Update `src/vibe_tool/cli.py`:
```python
import click

from vibe_tool.commands.client import client
from vibe_tool.commands.init import init
from vibe_tool.commands.setup import setup


@click.group()
@click.version_option()
def cli():
    """Vibe — Claude Code productivity tool.

    Quality gates and context continuity across machines and accounts.
    """
    pass


cli.add_command(client)
cli.add_command(init)
cli.add_command(setup)
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_init_cmd.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/commands/init.py src/vibe_tool/cli.py tests/test_init_cmd.py
git commit -m "feat: add vibe init command for project scaffolding"
```

---

### Task 7: `vibe status` Command

**Files:**
- Create: `src/vibe_tool/commands/status.py`
- Create: `tests/test_status_cmd.py`
- Modify: `src/vibe_tool/cli.py`

**Step 1: Write the failing tests**

Create `tests/test_status_cmd.py`:
```python
import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli
from vibe_tool.config import VibeConfig


def test_status_no_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "No projects" in result.output


def test_status_shows_projects_grouped_by_client(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))

    config = VibeConfig(vibe_dir)
    config.ensure_dirs()
    config.add_client("acme", "claude-1")
    config.add_client("beta-inc", "claude-2")
    config.add_project("marketplace", "/tmp/marketplace", "acme", "web", "next")
    config.add_project("fitness-api", "/tmp/fitness", "beta-inc", "api", "fastapi")
    config.update_project_tests("marketplace", passed=24, failed=0, total=24)
    config.update_project_tests("fitness-api", passed=18, failed=2, total=20)

    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "acme" in result.output.lower() or "ACME" in result.output
    assert "marketplace" in result.output
    assert "fitness-api" in result.output
    assert "24" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_status_cmd.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/commands/status.py`:
```python
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from vibe_tool.config import VibeConfig

console = Console()


def _time_ago(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    except (ValueError, TypeError):
        return "unknown"


def _get_status_line(project: dict) -> str:
    """Try to read the Current state section from the project's CLAUDE.md."""
    claude_md = Path(project["path"]) / "CLAUDE.md"
    if not claude_md.exists():
        return ""
    try:
        content = claude_md.read_text()
        marker = "## Current state"
        idx = content.find(marker)
        if idx == -1:
            return ""
        after = content[idx + len(marker):].strip()
        # Take first non-empty line
        for line in after.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                return line[:40]
        return ""
    except OSError:
        return ""


def _format_tests(tc: dict) -> str:
    total = tc.get("total", 0)
    if total == 0:
        return "no tests"
    passed = tc.get("pass", 0)
    failed = tc.get("fail", 0)
    mark = "[green]✓[/green]" if failed == 0 else "[red]✗[/red]"
    return f"{passed}/{total} {mark}"


@click.command()
def status():
    """Show all projects grouped by client with test health."""
    config_dir = os.environ.get("VIBE_CONFIG_DIR")
    config = VibeConfig(config_dir) if config_dir else VibeConfig()
    config.ensure_dirs()

    projects = config.load_projects()
    if not projects:
        console.print("No projects registered. Run [bold]vibe init[/bold] in a project directory.")
        return

    clients = config.load_clients()
    client_accounts = {c["name"]: c.get("account", "") for c in clients}

    # Group by client
    grouped = defaultdict(list)
    for p in projects:
        grouped[p["client"]].append(p)

    for client_name, client_projects in grouped.items():
        account = client_accounts.get(client_name, "")
        title = client_name.upper()
        if account:
            title += f" ({account})"

        table = Table(title=title, title_style="bold cyan")
        table.add_column("Project", style="white")
        table.add_column("Tests", justify="center")
        table.add_column("Stack", justify="center", style="dim")
        table.add_column("Last Active", justify="center")
        table.add_column("Status", style="dim")

        for p in client_projects:
            table.add_row(
                p["name"],
                _format_tests(p.get("testCount", {})),
                p.get("stack", ""),
                _time_ago(p.get("lastActive", "")),
                _get_status_line(p),
            )

        console.print(table)
        console.print()
```

Update `src/vibe_tool/cli.py`:
```python
import click

from vibe_tool.commands.client import client
from vibe_tool.commands.init import init
from vibe_tool.commands.setup import setup
from vibe_tool.commands.status import status


@click.group()
@click.version_option()
def cli():
    """Vibe — Claude Code productivity tool.

    Quality gates and context continuity across machines and accounts.
    """
    pass


cli.add_command(client)
cli.add_command(init)
cli.add_command(setup)
cli.add_command(status)
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_status_cmd.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/commands/status.py src/vibe_tool/cli.py tests/test_status_cmd.py
git commit -m "feat: add vibe status command with client-grouped project view"
```

---

### Task 8: `vibe sync` Command

**Files:**
- Create: `src/vibe_tool/commands/sync.py`
- Create: `tests/test_sync_cmd.py`
- Modify: `src/vibe_tool/cli.py`

**Step 1: Write the failing tests**

Create `tests/test_sync_cmd.py`:
```python
import os
import subprocess
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def _make_git_project(path: Path):
    """Create a minimal git project with a remote."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    # Create initial commit so we have a branch
    (path / "README.md").write_text("# test\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


def test_sync_commits_claude_context(tmp_path, monkeypatch):
    project_dir = tmp_path / "my-project"
    _make_git_project(project_dir)

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    monkeypatch.chdir(project_dir)

    # Create CLAUDE.md and .claude/ dir with content
    (project_dir / "CLAUDE.md").write_text("# My Project\n## Current state\nWIP\n")
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    (claude_dir / "memory.md").write_text("some memory\n")

    runner = CliRunner()
    result = runner.invoke(cli, ["sync", "push"])
    assert result.exit_code == 0

    # Verify files are committed
    log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=project_dir, capture_output=True, text=True
    )
    assert "vibe sync" in log.stdout.lower() or "context" in log.stdout.lower()


def test_sync_no_changes(tmp_path, monkeypatch):
    project_dir = tmp_path / "my-project"
    _make_git_project(project_dir)

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    monkeypatch.chdir(project_dir)

    runner = CliRunner()
    result = runner.invoke(cli, ["sync", "push"])
    assert result.exit_code == 0
    assert "nothing" in result.output.lower() or "No context" in result.output


def test_sync_not_a_git_repo(tmp_path, monkeypatch):
    project_dir = tmp_path / "not-git"
    project_dir.mkdir()

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    monkeypatch.chdir(project_dir)

    runner = CliRunner()
    result = runner.invoke(cli, ["sync"])
    assert result.exit_code != 0 or "not a git" in result.output.lower()
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_sync_cmd.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/commands/sync.py`:
```python
import os
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
```

Update `src/vibe_tool/cli.py`:
```python
import click

from vibe_tool.commands.client import client
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
cli.add_command(init)
cli.add_command(setup)
cli.add_command(status)
cli.add_command(sync)
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_sync_cmd.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/commands/sync.py src/vibe_tool/cli.py tests/test_sync_cmd.py
git commit -m "feat: add vibe sync command for cross-machine context sync"
```

---

### Task 9: Full Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration test**

Create `tests/test_integration.py`:
```python
"""End-to-end test: setup -> client add -> init -> status -> sync."""

import os
import subprocess
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def test_full_workflow(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# My rules\n")
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()

    # 1. Setup
    result = runner.invoke(cli, ["setup"], input="acme\nclaude-1\n")
    assert result.exit_code == 0
    assert "Setup complete" in result.output

    # Verify CLAUDE.md was augmented
    content = claude_dir.joinpath("CLAUDE.md").read_text()
    assert "Mandatory Quality Rules" in content

    # 2. Add another client
    result = runner.invoke(cli, ["client", "add", "--name", "beta-inc", "--account", "claude-2"])
    assert result.exit_code == 0

    # 3. Init project
    subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=project_dir, check=True)
    monkeypatch.chdir(project_dir)

    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / ".github" / "workflows" / "ci.yml").exists()

    # 4. Status
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "test-project" in result.output

    # 5. Sync push (after making initial commit)
    subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project_dir, check=True)
    # Modify CLAUDE.md to create something to sync
    (project_dir / "CLAUDE.md").write_text("# Updated\n## Current state\nDone\n")
    result = runner.invoke(cli, ["sync", "push"])
    assert result.exit_code == 0
    assert "Committed" in result.output
```

**Step 2: Run the integration test**

Run: `python -m pytest tests/test_integration.py -v`
Expected: All PASS

**Step 3: Run full test suite**

Run: `python -m pytest -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration test for full workflow"
```

---

### Task 10: README and Final Polish

**Files:**
- Create: `README.md`
- Modify: `pyproject.toml` (add dev dependencies)

**Step 1: Add dev dependencies to pyproject.toml**

Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = ["pytest>=7.0"]
```

**Step 2: Create README.md**

Create `README.md`:
```markdown
# vibe-tool

CLI tool for Claude Code productivity — automated quality gates and context continuity across machines and accounts.

## Install

```bash
pip install -e .
```

## Setup (one-time per machine)

```bash
vibe setup
```

This:
- Adds mandatory quality rules to your global `~/.claude/CLAUDE.md`
- Creates `~/.vibe/` config directory
- Prompts you to add your first client

## Usage

### Start a new project

```bash
cd my-new-project
git init
vibe init
```

### Check all projects

```bash
vibe status
```

### Sync context between machines

```bash
vibe sync        # pull then push
vibe sync push   # push only
vibe sync pull   # pull only
```

### Manage clients

```bash
vibe client add --name "my-client" --account "claude-account1"
vibe client list
```

## What it does

1. **Quality gates** — Every project gets tests, git hooks, and CI from day one. Claude Code is instructed to always write tests, always run them, and never claim "done" without proof.

2. **Context continuity** — Project CLAUDE.md and Claude Code memory are auto-maintained and synced across machines via Git. New sessions know everything — no re-explaining.

3. **Cross-project visibility** — `vibe status` shows all projects grouped by client with test health, last activity, and current state.
```

**Step 3: Run full test suite one final time**

Run: `python -m pytest -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add README.md pyproject.toml
git commit -m "docs: add README and dev dependencies"
```

---

## Execution Summary

| Task | Description | Tests |
|---|---|---|
| 1 | Package skeleton + CLI entry point | 1 |
| 2 | Config module (clients, projects) | 6 |
| 3 | `vibe client add/list` commands | 3 |
| 4 | Templates (CLAUDE.md, hooks, CI) | 6 |
| 5 | `vibe setup` command | 4 |
| 6 | `vibe init` command | 5 |
| 7 | `vibe status` command | 2 |
| 8 | `vibe sync` command | 3 |
| 9 | Full integration test | 1 |
| 10 | README + polish | 0 |
| **Total** | | **31 tests** |

**Dependency order:** 1 → 2 → 3, 4 (parallel) → 5 → 6 → 7, 8 (parallel) → 9 → 10
