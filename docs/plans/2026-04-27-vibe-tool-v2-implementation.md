# Vibe Tool v2 — Context Intelligence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 5 context intelligence features to the existing vibe-tool CLI: codebase indexing, session handoff, session pre-loader, error memory, and prompt templates.

**Architecture:** New modules under `src/vibe_tool/` for parsing, handoff generation, error tracking, and templates. New CLI commands registered via Click. Existing commands (init, setup, sync) updated to integrate v2 features. All context files live in `.vibe/` per-project directory.

**Tech Stack:** Python 3.11+, Click, Rich, regex-based code parsing, subprocess for Git

**Existing codebase:** `src/vibe_tool/` with cli.py, config.py, templates.py, and commands/ (client.py, setup.py, init.py, status.py, sync.py). Tests in `tests/`.

---

### Task 1: Codebase Parser — JS/TS Extraction

**Files:**
- Create: `src/vibe_tool/parser.py`
- Create: `tests/test_parser.py`

**Step 1: Write the failing tests**

Create `tests/test_parser.py`:
```python
from vibe_tool.parser import parse_js_file, parse_python_file, generate_file_description


def test_parse_js_export_functions():
    code = """
import { db } from '../db/schema';

export function getUser(id: string): User {
    return db.query(id);
}

export const deleteUser = async (id: string) => {
    await db.delete(id);
};

export class UserService {
    constructor(private db: DB) {}
}
"""
    result = parse_js_file(code, "src/services/user.ts")
    assert any("getUser" in e for e in result["exports"])
    assert any("deleteUser" in e for e in result["exports"])
    assert any("UserService" in e for e in result["exports"])
    assert any("db/schema" in d for d in result["dependencies"])


def test_parse_js_api_routes():
    code = """
import express from 'express';
const router = express.Router();

router.get('/users', listUsers);
router.post('/users', createUser);
router.get('/users/:id', getUser);
app.delete('/users/:id', deleteUser);
"""
    result = parse_js_file(code, "src/api/routes/users.ts")
    assert any("GET /users" in r for r in result["routes"])
    assert any("POST /users" in r for r in result["routes"])
    assert any("DELETE /users/:id" in r for r in result["routes"])


def test_parse_js_schema():
    code = """
export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    email: varchar('email', { length: 255 }),
    createdAt: timestamp('created_at').defaultNow(),
});

export const products = pgTable('products', {
    id: serial('id').primaryKey(),
    title: varchar('title'),
    price: integer('price'),
});
"""
    result = parse_js_file(code, "src/db/schema.ts")
    assert any("users" in t for t in result["tables"])
    assert any("products" in t for t in result["tables"])


def test_parse_python_functions():
    code = """
import os
from pathlib import Path
from fastapi import FastAPI

app = FastAPI()

def helper_internal():
    pass

class UserService:
    def get(self, id):
        pass

@app.get("/users")
def list_users():
    return []

@app.post("/users")
async def create_user(data: UserCreate):
    pass
"""
    result = parse_python_file(code, "src/main.py")
    assert any("helper_internal" in e for e in result["exports"])
    assert any("UserService" in e for e in result["exports"])
    assert any("GET /users" in r for r in result["routes"])
    assert any("POST /users" in r for r in result["routes"])
    assert any("pathlib" in d or "Path" in d for d in result["dependencies"])


def test_parse_python_models():
    code = """
from sqlalchemy import Column, Integer, String
from .base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    title = Column(String)
"""
    result = parse_python_file(code, "src/models.py")
    assert any("users" in t for t in result["tables"])
    assert any("products" in t for t in result["tables"])


def test_generate_file_description():
    parsed = {
        "exports": ["getUser(id: string)", "deleteUser(id: string)", "UserService"],
        "routes": [],
        "dependencies": ["../db/schema"],
        "tables": [],
    }
    desc = generate_file_description(parsed)
    assert "getUser" in desc
    assert "3" in desc or "exports" in desc.lower()
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/chinedunnaji/Documents/workspace/VIbe-tool && python -m pytest tests/test_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vibe_tool.parser'`

**Step 3: Write implementation**

Create `src/vibe_tool/parser.py`:
```python
import re


def parse_js_file(code: str, filepath: str) -> dict:
    """Extract exports, routes, dependencies, and tables from JS/TS code."""
    exports = []
    routes = []
    dependencies = []
    tables = []

    for line in code.split("\n"):
        line_stripped = line.strip()

        # Exports: export function/const/class
        m = re.match(r'export\s+(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', line_stripped)
        if m:
            exports.append(f"{m.group(1)}({m.group(2).strip()})")
            continue

        m = re.match(r'export\s+const\s+(\w+)\s*=', line_stripped)
        if m:
            exports.append(m.group(1))
            continue

        m = re.match(r'export\s+class\s+(\w+)', line_stripped)
        if m:
            exports.append(m.group(1))
            continue

        m = re.match(r'export\s+default\s+(?:class|function)\s+(\w+)', line_stripped)
        if m:
            exports.append(f"{m.group(1)} (default)")
            continue

        # Routes: app.get/post/... or router.get/post/...
        m = re.match(r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', line_stripped)
        if m:
            method = m.group(1).upper()
            path = m.group(2)
            routes.append(f"{method} {path}")
            continue

        # Dependencies: import ... from '...'
        m = re.match(r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', line_stripped)
        if m:
            dependencies.append(m.group(1))
            continue

        # Tables: pgTable, createTable, etc.
        m = re.match(r'export\s+const\s+(\w+)\s*=\s*(?:pgTable|mysqlTable|sqliteTable|createTable)\s*\(\s*[\'"](\w+)[\'"]', line_stripped)
        if m:
            table_name = m.group(2)
            # Extract column names from nearby lines
            tables.append(f"table {table_name}")

    # Multi-line table detection: look for pgTable patterns
    for m in re.finditer(r'(?:pgTable|mysqlTable|sqliteTable)\s*\(\s*[\'"](\w+)[\'"]', code):
        table_name = m.group(1)
        entry = f"table {table_name}"
        if entry not in tables:
            tables.append(entry)

    return {"exports": exports, "routes": routes, "dependencies": dependencies, "tables": tables}


def parse_python_file(code: str, filepath: str) -> dict:
    """Extract functions, classes, routes, dependencies, and tables from Python code."""
    exports = []
    routes = []
    dependencies = []
    tables = []

    lines = code.split("\n")
    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Top-level functions (not indented)
        if line_stripped.startswith("def ") and not line.startswith(" ") and not line.startswith("\t"):
            m = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', line_stripped)
            if m:
                exports.append(f"{m.group(1)}({m.group(2).strip()})")

        # Top-level async functions
        if line_stripped.startswith("async def ") and not line.startswith(" ") and not line.startswith("\t"):
            m = re.match(r'async\s+def\s+(\w+)\s*\(([^)]*)\)', line_stripped)
            if m:
                exports.append(f"{m.group(1)}({m.group(2).strip()})")

        # Classes
        if line_stripped.startswith("class ") and not line.startswith(" ") and not line.startswith("\t"):
            m = re.match(r'class\s+(\w+)', line_stripped)
            if m:
                exports.append(m.group(1))

        # Routes: @app.get/post/... or @router.get/post/...
        m = re.match(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', line_stripped)
        if m:
            method = m.group(1).upper()
            path = m.group(2)
            routes.append(f"{method} {path}")

        # Flask routes: @app.route
        m = re.match(r'@(?:app|blueprint|bp)\.route\s*\(\s*[\'"]([^\'"]+)[\'"]', line_stripped)
        if m:
            routes.append(f"ROUTE {m.group(1)}")

        # Dependencies: from X import / import X
        m = re.match(r'from\s+([\w.]+)\s+import', line_stripped)
        if m:
            dependencies.append(m.group(1))
            continue
        m = re.match(r'import\s+([\w.]+)', line_stripped)
        if m:
            dependencies.append(m.group(1))

        # Tables: __tablename__
        m = re.match(r"__tablename__\s*=\s*['\"](\w+)['\"]", line_stripped)
        if m:
            tables.append(f"table {m.group(1)}")

    return {"exports": exports, "routes": routes, "dependencies": dependencies, "tables": tables}


def generate_file_description(parsed: dict) -> str:
    """Generate a one-line description from parsed file data."""
    parts = []
    if parsed["routes"]:
        parts.append(f"{len(parsed['routes'])} route(s): {', '.join(parsed['routes'][:3])}")
    if parsed["tables"]:
        parts.append(f"tables: {', '.join(parsed['tables'])}")
    if parsed["exports"] and not parsed["routes"]:
        names = [e.split("(")[0] for e in parsed["exports"][:4]]
        parts.append(f"{len(parsed['exports'])} exports: {', '.join(names)}")
    if not parts:
        return "no public exports detected"
    return "; ".join(parts)
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_parser.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/parser.py tests/test_parser.py
git commit -m "feat: add codebase parser for JS/TS and Python extraction"
```

---

### Task 2: `vibe index` Command

**Files:**
- Create: `src/vibe_tool/indexer.py`
- Create: `src/vibe_tool/commands/index.py`
- Create: `tests/test_indexer.py`
- Create: `tests/test_index_cmd.py`
- Modify: `src/vibe_tool/cli.py:1-24`

**Step 1: Write the failing tests**

Create `tests/test_indexer.py`:
```python
from pathlib import Path
from vibe_tool.indexer import scan_project, render_index


def _create_project(tmp_path):
    """Create a minimal JS project for testing."""
    src = tmp_path / "src"
    src.mkdir()

    (src / "index.ts").write_text("""
import { db } from './db';
export function main() { console.log('hello'); }
""")

    (src / "db.ts").write_text("""
export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    email: varchar('email'),
});
""")

    routes = src / "api"
    routes.mkdir()
    (routes / "auth.ts").write_text("""
import { db } from '../db';
router.post('/login', loginHandler);
router.post('/signup', signupHandler);
export function loginHandler(req, res) {}
export function signupHandler(req, res) {}
""")

    # Non-source files should be ignored
    (tmp_path / "package.json").write_text('{"name": "test"}')
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("junk")

    return tmp_path


def test_scan_project_finds_source_files(tmp_path):
    project = _create_project(tmp_path)
    result = scan_project(project)
    paths = [r["path"] for r in result]
    assert any("index.ts" in p for p in paths)
    assert any("auth.ts" in p for p in paths)
    # node_modules should be excluded
    assert not any("node_modules" in p for p in paths)


def test_scan_project_extracts_exports(tmp_path):
    project = _create_project(tmp_path)
    result = scan_project(project)
    auth = next(r for r in result if "auth.ts" in r["path"])
    assert any("loginHandler" in e for e in auth["parsed"]["exports"])


def test_render_index_produces_markdown(tmp_path):
    project = _create_project(tmp_path)
    scanned = scan_project(project)
    md = render_index(scanned, project)
    assert "## File Map" in md
    assert "## Exports" in md
    assert "auth.ts" in md
    assert "loginHandler" in md


def test_render_index_includes_dependencies(tmp_path):
    project = _create_project(tmp_path)
    scanned = scan_project(project)
    md = render_index(scanned, project)
    assert "## Dependencies" in md
```

Create `tests/test_index_cmd.py`:
```python
import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def _make_project(tmp_path, monkeypatch):
    project = tmp_path / "my-project"
    project.mkdir()
    src = project / "src"
    src.mkdir()
    (src / "app.ts").write_text("export function hello() { return 'hi'; }\n")
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    return project


def test_index_creates_codebase_md(tmp_path, monkeypatch):
    project = _make_project(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["index"])
    assert result.exit_code == 0
    assert (project / ".vibe" / "codebase.md").exists()


def test_index_content_has_file_map(tmp_path, monkeypatch):
    project = _make_project(tmp_path, monkeypatch)
    runner = CliRunner()
    runner.invoke(cli, ["index"])
    content = (project / ".vibe" / "codebase.md").read_text()
    assert "## File Map" in content
    assert "app.ts" in content
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_indexer.py tests/test_index_cmd.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/indexer.py`:
```python
import os
from datetime import datetime, timezone
from pathlib import Path

from vibe_tool.parser import parse_js_file, parse_python_file, generate_file_description

SOURCE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".py", ".mjs"}

IGNORE_DIRS = {
    "node_modules", ".git", ".vibe", "__pycache__", ".next", ".expo",
    "dist", "build", ".venv", "venv", "env", ".tox", ".mypy_cache",
    ".pytest_cache", "coverage", ".nyc_output",
}


def scan_project(project_dir: Path) -> list[dict]:
    """Walk the project and parse all source files."""
    results = []

    for root, dirs, files in os.walk(project_dir):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        for fname in sorted(files):
            fpath = Path(root) / fname
            ext = fpath.suffix

            if ext not in SOURCE_EXTENSIONS:
                continue

            rel_path = str(fpath.relative_to(project_dir))

            try:
                code = fpath.read_text(errors="replace")
            except OSError:
                continue

            if ext in (".py",):
                parsed = parse_python_file(code, rel_path)
            else:
                parsed = parse_js_file(code, rel_path)

            results.append({
                "path": rel_path,
                "parsed": parsed,
                "description": generate_file_description(parsed),
            })

    return results


def render_index(scanned: list[dict], project_dir: Path) -> str:
    """Render the scanned results into a markdown index."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Codebase Index (auto-generated by vibe index)",
        f"Last updated: {now}",
        "",
    ]

    # File Map
    lines.append("## File Map")
    for entry in scanned:
        lines.append(f"{entry['path']} — {entry['description']}")
    lines.append("")

    # Exports (only files with exports or routes)
    has_exports = [e for e in scanned if e["parsed"]["exports"] or e["parsed"]["routes"] or e["parsed"]["tables"]]
    if has_exports:
        lines.append("## Exports")
        for entry in has_exports:
            lines.append(f"### {entry['path']}")
            for route in entry["parsed"]["routes"]:
                lines.append(f"  {route}")
            for table in entry["parsed"]["tables"]:
                lines.append(f"  {table}")
            for export in entry["parsed"]["exports"]:
                lines.append(f"  {export}")
            lines.append("")

    # Dependencies
    has_deps = [e for e in scanned if e["parsed"]["dependencies"]]
    if has_deps:
        lines.append("## Dependencies")
        for entry in has_deps:
            deps = ", ".join(entry["parsed"]["dependencies"])
            lines.append(f"{entry['path']} → {deps}")
        lines.append("")

    # Patterns section placeholder
    lines.append("## Patterns")
    lines.append("[Run `vibe index --deep` for Claude-generated pattern analysis]")
    lines.append("")

    return "\n".join(lines)
```

Create `src/vibe_tool/commands/index.py`:
```python
import os
from pathlib import Path

import click
from rich.console import Console

from vibe_tool.indexer import scan_project, render_index

console = Console()


@click.command()
@click.option("--deep", is_flag=True, help="Use Claude for richer analysis (costs tokens)")
def index(deep: bool):
    """Generate codebase knowledge base in .vibe/codebase.md."""
    project_dir = Path.cwd()

    if deep:
        console.print("[yellow]--deep mode not yet implemented. Using pattern-based scan.[/yellow]")

    console.print("Scanning codebase...")
    scanned = scan_project(project_dir)

    if not scanned:
        console.print("[yellow]No source files found.[/yellow]")
        return

    # Ensure .vibe/ dir exists
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)

    # Write index
    md = render_index(scanned, project_dir)
    (vibe_dir / "codebase.md").write_text(md)

    console.print(f"[green]Indexed {len(scanned)} files[/green] → .vibe/codebase.md")
```

**Step 4: Update CLI — add to `src/vibe_tool/cli.py`:**

```python
import click

from vibe_tool.commands.client import client
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
cli.add_command(index)
cli.add_command(init)
cli.add_command(setup)
cli.add_command(status)
cli.add_command(sync)
```

**Step 5: Run tests**

Run: `python -m pytest tests/test_indexer.py tests/test_index_cmd.py tests/test_cli.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/vibe_tool/indexer.py src/vibe_tool/commands/index.py src/vibe_tool/cli.py tests/test_indexer.py tests/test_index_cmd.py
git commit -m "feat: add vibe index command for codebase knowledge base generation"
```

---

### Task 3: Session Handoff Generator

**Files:**
- Create: `src/vibe_tool/handoff.py`
- Create: `tests/test_handoff.py`

**Step 1: Write the failing tests**

Create `tests/test_handoff.py`:
```python
import subprocess
from pathlib import Path
from vibe_tool.handoff import generate_handoff


def _make_git_project(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=project, check=True)
    (project / "README.md").write_text("# test\n")
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)
    return project


def test_handoff_with_commits(tmp_path):
    project = _make_git_project(tmp_path)
    # Record start SHA
    start_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True
    ).stdout.strip()

    # Make changes
    (project / "src").mkdir()
    (project / "src" / "app.ts").write_text("export function hello() {}\n")
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feat: add hello function"], cwd=project, check=True)

    md = generate_handoff(project, start_sha)
    assert "## What was done" in md
    assert "hello" in md.lower() or "feat:" in md
    assert "## Files changed" in md
    assert "app.ts" in md


def test_handoff_with_uncommitted_changes(tmp_path):
    project = _make_git_project(tmp_path)
    start_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True
    ).stdout.strip()

    # Uncommitted changes
    (project / "wip.ts").write_text("// work in progress\n")

    md = generate_handoff(project, start_sha)
    assert "## In progress" in md
    assert "wip.ts" in md


def test_handoff_no_changes(tmp_path):
    project = _make_git_project(tmp_path)
    start_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True
    ).stdout.strip()

    md = generate_handoff(project, start_sha)
    assert "No changes" in md or "## What was done" in md
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_handoff.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/handoff.py`:
```python
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def generate_handoff(project_dir: Path, start_sha: str | None = None) -> str:
    """Generate a session handoff note from git state."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Session Handoff", f"Last session: {now}", ""]

    # What was done — commits since session start
    if start_sha:
        log = _run_git(["log", f"{start_sha}..HEAD", "--oneline"], project_dir)
    else:
        log = _run_git(["log", "-5", "--oneline"], project_dir)

    lines.append("## What was done")
    if log:
        for commit_line in log.split("\n"):
            if commit_line.strip():
                # Strip the short SHA, keep the message
                parts = commit_line.strip().split(" ", 1)
                msg = parts[1] if len(parts) > 1 else parts[0]
                lines.append(f"- {msg}")
    else:
        lines.append("- No changes committed this session")
    lines.append("")

    # In progress — uncommitted changes
    status = _run_git(["status", "--short"], project_dir)
    uncommitted = []
    if status:
        for sline in status.split("\n"):
            sline = sline.strip()
            if sline:
                # Format: "M  file.txt" or "?? file.txt"
                parts = sline.split(None, 1)
                if len(parts) == 2:
                    uncommitted.append(parts[1])

    if uncommitted:
        lines.append("## In progress")
        for f in uncommitted:
            lines.append(f"- {f} (uncommitted)")
        lines.append("")

    # Files changed — from diff since start
    if start_sha:
        diff_stat = _run_git(["diff", "--stat", "--name-status", f"{start_sha}..HEAD"], project_dir)
    else:
        diff_stat = _run_git(["diff", "--stat", "--name-status", "HEAD~5..HEAD"], project_dir)

    lines.append("## Files changed")
    if diff_stat:
        for dline in diff_stat.split("\n"):
            dline = dline.strip()
            if not dline:
                continue
            parts = dline.split("\t")
            if len(parts) >= 2:
                status_code = parts[0]
                fname = parts[1]
                label = {"A": "Created", "M": "Modified", "D": "Deleted"}.get(status_code, "Changed")
                lines.append(f"- {label}: {fname}")
    elif not log:
        lines.append("- No files changed")
    lines.append("")

    # Next up placeholder
    lines.append("## Next up")
    lines.append("- [Determined by next session based on project CLAUDE.md]")
    lines.append("")

    return "\n".join(lines)


def write_handoff(project_dir: Path, start_sha: str | None = None):
    """Generate and write handoff to .vibe/handoff.md."""
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)
    md = generate_handoff(project_dir, start_sha)
    (vibe_dir / "handoff.md").write_text(md)
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_handoff.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/handoff.py tests/test_handoff.py
git commit -m "feat: add session handoff generator using git state"
```

---

### Task 4: Session Pre-loader Generator

**Files:**
- Create: `src/vibe_tool/preloader.py`
- Create: `tests/test_preloader.py`

**Step 1: Write the failing tests**

Create `tests/test_preloader.py`:
```python
import subprocess
from pathlib import Path
from vibe_tool.preloader import generate_session_context


def _make_git_project(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=project, check=True)
    (project / "README.md").write_text("# test\n")
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)
    return project


def test_session_context_includes_git_state(tmp_path):
    project = _make_git_project(tmp_path)
    md = generate_session_context(project)
    assert "## Git State" in md
    assert "Branch:" in md


def test_session_context_includes_recent_commits(tmp_path):
    project = _make_git_project(tmp_path)
    md = generate_session_context(project)
    assert "## Recent Commits" in md
    assert "init" in md


def test_session_context_shows_uncommitted(tmp_path):
    project = _make_git_project(tmp_path)
    (project / "new_file.txt").write_text("wip\n")
    md = generate_session_context(project)
    assert "new_file.txt" in md


def test_session_context_env_check(tmp_path):
    project = _make_git_project(tmp_path)
    (project / ".env.example").write_text("DATABASE_URL=\nSTRIPE_KEY=\n")
    (project / ".env").write_text("DATABASE_URL=postgres://localhost\n")
    md = generate_session_context(project)
    assert "## Environment Notes" in md
    assert "STRIPE_KEY" in md  # missing from .env


def test_session_context_no_env_files(tmp_path):
    project = _make_git_project(tmp_path)
    md = generate_session_context(project)
    # Should not crash, just skip env section
    assert "## Git State" in md
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_preloader.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/preloader.py`:
```python
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _parse_env_file(path: Path) -> set[str]:
    """Extract variable names from a .env file."""
    keys = set()
    if not path.exists():
        return keys
    for line in path.read_text().split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            keys.add(line.split("=", 1)[0].strip())
    return keys


def generate_session_context(project_dir: Path) -> str:
    """Generate ephemeral session context from current repo state."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Session Context (auto-generated, do not edit)",
        f"Generated: {now}",
        "",
    ]

    # Git state
    branch = _run_git(["branch", "--show-current"], project_dir) or "unknown"
    ahead = _run_git(["rev-list", "--count", "HEAD", "--not", "--remotes"], project_dir) or "0"

    lines.append("## Git State")
    lines.append(f"Branch: {branch} ({ahead} commits ahead of remote)")

    # Uncommitted changes
    status = _run_git(["status", "--short"], project_dir)
    if status:
        lines.append("Uncommitted changes:")
        for sline in status.split("\n"):
            sline = sline.strip()
            if sline:
                lines.append(f"  - {sline}")
    else:
        lines.append("Working tree clean")
    lines.append("")

    # Recent commits
    log = _run_git(["log", "--oneline", "-5", "--format=%s (%ar)"], project_dir)
    lines.append("## Recent Commits (last 5)")
    if log:
        for commit in log.split("\n"):
            if commit.strip():
                lines.append(f"- {commit.strip()}")
    else:
        lines.append("- No commits yet")
    lines.append("")

    # Test health — read from cached results if available
    vibe_dir = project_dir / ".vibe"
    lines.append("## Test Health")
    lines.append("[Run `vibe status` for test counts]")
    lines.append("")

    # Environment check
    env_example = project_dir / ".env.example"
    env_file = project_dir / ".env"

    if env_example.exists():
        expected = _parse_env_file(env_example)
        actual = _parse_env_file(env_file)
        missing = expected - actual

        lines.append("## Environment Notes")
        if env_file.exists():
            lines.append(f".env has: {', '.join(sorted(actual)) if actual else 'empty'}")
        else:
            lines.append(".env file not found")

        if missing:
            lines.append(f".env missing: {', '.join(sorted(missing))}")
        elif env_file.exists():
            lines.append("All expected env vars are set")
        lines.append("")

    return "\n".join(lines)


def write_session_context(project_dir: Path):
    """Generate and write session context to .vibe/session-context.md."""
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)
    md = generate_session_context(project_dir)
    (vibe_dir / "session-context.md").write_text(md)


def record_session_start(project_dir: Path):
    """Record the current HEAD SHA for handoff comparison."""
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir(exist_ok=True)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_dir, capture_output=True, text=True
    )
    if result.returncode == 0:
        (vibe_dir / ".session-start-sha").write_text(result.stdout.strip())
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_preloader.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/preloader.py tests/test_preloader.py
git commit -m "feat: add session pre-loader for temporal context generation"
```

---

### Task 5: Error Memory Module and Commands

**Files:**
- Create: `src/vibe_tool/errors.py`
- Create: `src/vibe_tool/commands/error.py`
- Create: `tests/test_errors.py`
- Create: `tests/test_error_cmd.py`
- Modify: `src/vibe_tool/cli.py`

**Step 1: Write the failing tests**

Create `tests/test_errors.py`:
```python
from pathlib import Path
from vibe_tool.errors import load_errors, add_error, render_errors_md, get_next_id


def test_load_errors_empty(tmp_path):
    errors_file = tmp_path / "errors.md"
    assert load_errors(errors_file) == []


def test_add_and_load_error(tmp_path):
    errors_file = tmp_path / "errors.md"
    add_error(errors_file, title="Module not found", when="importing @/lib", cause="tsconfig paths missing", fix="Add baseUrl to tsconfig")
    entries = load_errors(errors_file)
    assert len(entries) == 1
    assert entries[0]["id"] == "ERR-001"
    assert entries[0]["title"] == "Module not found"


def test_add_multiple_errors_increments_id(tmp_path):
    errors_file = tmp_path / "errors.md"
    add_error(errors_file, title="First", when="w1", cause="c1", fix="f1")
    add_error(errors_file, title="Second", when="w2", cause="c2", fix="f2")
    entries = load_errors(errors_file)
    assert len(entries) == 2
    assert entries[0]["id"] == "ERR-001"
    assert entries[1]["id"] == "ERR-002"


def test_get_next_id_empty(tmp_path):
    errors_file = tmp_path / "errors.md"
    assert get_next_id(errors_file) == "ERR-001"


def test_get_next_id_after_entries(tmp_path):
    errors_file = tmp_path / "errors.md"
    add_error(errors_file, title="First", when="w", cause="c", fix="f")
    assert get_next_id(errors_file) == "ERR-002"


def test_render_errors_md(tmp_path):
    errors_file = tmp_path / "errors.md"
    add_error(errors_file, title="Test error", when="testing", cause="bad config", fix="fix config")
    content = errors_file.read_text()
    assert "# Error Memory" in content
    assert "ERR-001" in content
    assert "Test error" in content
    assert "**When:**" in content
    assert "**Fix:**" in content
```

Create `tests/test_error_cmd.py`:
```python
import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli


def test_error_add(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe-cfg"))

    runner = CliRunner()
    result = runner.invoke(cli, ["error", "add"],
        input="Module not found\nWhen importing\nBad path\nFix the path\n")
    assert result.exit_code == 0
    assert (project / ".vibe" / "errors.md").exists()


def test_error_list_empty(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe-cfg"))

    runner = CliRunner()
    result = runner.invoke(cli, ["error", "list"])
    assert result.exit_code == 0
    assert "No errors" in result.output


def test_error_list_shows_entries(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe-cfg"))

    runner = CliRunner()
    runner.invoke(cli, ["error", "add"],
        input="Test bug\nAlways\nBad code\nGood code\n")
    result = runner.invoke(cli, ["error", "list"])
    assert result.exit_code == 0
    assert "ERR-001" in result.output
    assert "Test bug" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_errors.py tests/test_error_cmd.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/errors.py`:
```python
import re
from datetime import datetime, timezone
from pathlib import Path

HEADER = "# Error Memory\nErrors encountered and their solutions. Read this before debugging.\n"


def get_next_id(errors_file: Path) -> str:
    """Get the next ERR-NNN id."""
    entries = load_errors(errors_file)
    if not entries:
        return "ERR-001"
    last_num = max(int(e["id"].split("-")[1]) for e in entries)
    return f"ERR-{last_num + 1:03d}"


def load_errors(errors_file: Path) -> list[dict]:
    """Parse error entries from the errors.md file."""
    if not errors_file.exists():
        return []

    content = errors_file.read_text()
    entries = []

    for match in re.finditer(
        r'## (ERR-\d+): (.+?)\n'
        r'\*\*When:\*\* (.+?)\n'
        r'\*\*Cause:\*\* (.+?)\n'
        r'\*\*Fix:\*\* (.+?)\n'
        r'\*\*Date:\*\* (.+?)(?:\n|$)',
        content,
    ):
        entries.append({
            "id": match.group(1),
            "title": match.group(2),
            "when": match.group(3),
            "cause": match.group(4),
            "fix": match.group(5),
            "date": match.group(6),
        })

    return entries


def add_error(errors_file: Path, title: str, when: str, cause: str, fix: str):
    """Append a new error entry to errors.md."""
    err_id = get_next_id(errors_file)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    entry = f"\n## {err_id}: {title}\n**When:** {when}\n**Cause:** {cause}\n**Fix:** {fix}\n**Date:** {date}\n"

    if not errors_file.exists():
        errors_file.parent.mkdir(parents=True, exist_ok=True)
        errors_file.write_text(HEADER + entry)
    else:
        with open(errors_file, "a") as f:
            f.write(entry)


def render_errors_md(errors_file: Path) -> str:
    """Return the full errors.md content."""
    if not errors_file.exists():
        return HEADER
    return errors_file.read_text()
```

Create `src/vibe_tool/commands/error.py`:
```python
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
```

**Step 4: Update `src/vibe_tool/cli.py`:**

```python
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
```

**Step 5: Run tests**

Run: `python -m pytest tests/test_errors.py tests/test_error_cmd.py tests/test_cli.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/vibe_tool/errors.py src/vibe_tool/commands/error.py src/vibe_tool/cli.py tests/test_errors.py tests/test_error_cmd.py
git commit -m "feat: add error memory module and vibe error add/list commands"
```

---

### Task 6: Prompt Templates Module and Commands

**Files:**
- Create: `src/vibe_tool/prompts.py`
- Create: `src/vibe_tool/commands/prompt.py`
- Create: `tests/test_prompts.py`
- Create: `tests/test_prompt_cmd.py`
- Modify: `src/vibe_tool/cli.py`

**Step 1: Write the failing tests**

Create `tests/test_prompts.py`:
```python
from pathlib import Path
from vibe_tool.prompts import get_default_templates, install_templates, list_templates, load_template


def test_get_default_templates_returns_dict():
    templates = get_default_templates()
    assert "add-endpoint" in templates
    assert "add-page" in templates
    assert "fix-bug" in templates
    assert "add-feature" in templates
    assert "refactor" in templates


def test_install_templates(tmp_path):
    prompts_dir = tmp_path / ".vibe" / "prompts"
    install_templates(prompts_dir)
    assert prompts_dir.exists()
    assert (prompts_dir / "add-endpoint.md").exists()
    assert (prompts_dir / "fix-bug.md").exists()


def test_list_templates(tmp_path):
    prompts_dir = tmp_path / ".vibe" / "prompts"
    install_templates(prompts_dir)
    templates = list_templates(prompts_dir)
    names = [t["name"] for t in templates]
    assert "add-endpoint" in names
    assert "fix-bug" in names


def test_load_template(tmp_path):
    prompts_dir = tmp_path / ".vibe" / "prompts"
    install_templates(prompts_dir)
    content = load_template(prompts_dir, "fix-bug")
    assert "bug" in content.lower()
    assert ".vibe/errors.md" in content


def test_load_template_not_found(tmp_path):
    prompts_dir = tmp_path / ".vibe" / "prompts"
    prompts_dir.mkdir(parents=True)
    content = load_template(prompts_dir, "nonexistent")
    assert content is None
```

Create `tests/test_prompt_cmd.py`:
```python
import os
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli
from vibe_tool.prompts import install_templates


def _setup(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    prompts_dir = project / ".vibe" / "prompts"
    install_templates(prompts_dir)
    monkeypatch.chdir(project)
    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe-cfg"))
    return project


def test_prompt_list(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["prompt", "list"])
    assert result.exit_code == 0
    assert "add-endpoint" in result.output
    assert "fix-bug" in result.output


def test_prompt_show(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["prompt", "show", "fix-bug"])
    assert result.exit_code == 0
    assert "bug" in result.output.lower()


def test_prompt_show_not_found(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["prompt", "show", "nonexistent"])
    assert result.exit_code != 0 or "not found" in result.output.lower()


def test_prompt_create(tmp_path, monkeypatch):
    project = _setup(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["prompt", "create", "deploy"],
        input="Deploy the app: [describe target]\n\nContext:\n- Check CI is green first\n")
    assert result.exit_code == 0
    assert (project / ".vibe" / "prompts" / "deploy.md").exists()
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_prompts.py tests/test_prompt_cmd.py -v`
Expected: FAIL

**Step 3: Write implementation**

Create `src/vibe_tool/prompts.py`:
```python
from pathlib import Path


def get_default_templates() -> dict[str, str]:
    """Return the default prompt templates."""
    return {
        "add-endpoint": (
            "Add a new API endpoint: [describe what it does]\n"
            "\n"
            "Context for Claude:\n"
            "- Check .vibe/codebase.md for existing routes and patterns\n"
            "- Follow the route pattern in the existing API routes directory\n"
            "- Use the validation middleware (see codebase index for location)\n"
            "- Add tests matching existing test patterns\n"
            "- Update .vibe/codebase.md Exports section when done\n"
        ),
        "add-page": (
            "Add a new page: [describe what the page does]\n"
            "\n"
            "Context for Claude:\n"
            "- Check .vibe/codebase.md for existing components and pages\n"
            "- Follow the existing page structure and layout patterns\n"
            "- Reuse existing components before creating new ones\n"
            "- Add E2E test for the new page\n"
            "- Update .vibe/codebase.md File Map when done\n"
        ),
        "fix-bug": (
            "Fix this bug: [describe what's broken]\n"
            "\n"
            "Context for Claude:\n"
            "- Read .vibe/errors.md first — this may be a known issue\n"
            "- Write a failing test that reproduces the bug BEFORE fixing it\n"
            "- Run existing tests to make sure the fix doesn't break anything else\n"
            "- If this was non-obvious, add it to .vibe/errors.md\n"
        ),
        "add-feature": (
            "Add this feature: [describe what it does]\n"
            "\n"
            "Context for Claude:\n"
            "- Read .vibe/codebase.md to understand existing architecture\n"
            "- Follow existing patterns for similar functionality\n"
            "- Write tests first (TDD)\n"
            "- Update .vibe/codebase.md when done\n"
        ),
        "refactor": (
            "Refactor: [describe what to restructure]\n"
            "\n"
            "Context for Claude:\n"
            "- Run all tests FIRST to establish a green baseline\n"
            "- Make structural changes WITHOUT changing behavior\n"
            "- Run tests after each change to verify nothing broke\n"
            "- Update .vibe/codebase.md if file locations or exports changed\n"
        ),
    }


def install_templates(prompts_dir: Path):
    """Write default templates to the prompts directory."""
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for name, content in get_default_templates().items():
        (prompts_dir / f"{name}.md").write_text(content)


def list_templates(prompts_dir: Path) -> list[dict]:
    """List available templates with their first line as description."""
    if not prompts_dir.exists():
        return []
    templates = []
    for f in sorted(prompts_dir.glob("*.md")):
        first_line = f.read_text().split("\n")[0].strip()
        templates.append({"name": f.stem, "description": first_line})
    return templates


def load_template(prompts_dir: Path, name: str) -> str | None:
    """Load a template by name. Returns None if not found."""
    path = prompts_dir / f"{name}.md"
    if not path.exists():
        return None
    return path.read_text()
```

Create `src/vibe_tool/commands/prompt.py`:
```python
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
        # pbcopy not available (Linux)
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
```

**Step 4: Update `src/vibe_tool/cli.py`:**

```python
import click

from vibe_tool.commands.client import client
from vibe_tool.commands.error import error
from vibe_tool.commands.index import index
from vibe_tool.commands.init import init
from vibe_tool.commands.prompt import prompt
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
cli.add_command(prompt)
cli.add_command(setup)
cli.add_command(status)
cli.add_command(sync)
```

**Step 5: Run tests**

Run: `python -m pytest tests/test_prompts.py tests/test_prompt_cmd.py tests/test_cli.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/vibe_tool/prompts.py src/vibe_tool/commands/prompt.py src/vibe_tool/cli.py tests/test_prompts.py tests/test_prompt_cmd.py
git commit -m "feat: add prompt templates module and vibe prompt list/show/copy/create commands"
```

---

### Task 7: Update `vibe init` for v2

**Files:**
- Modify: `src/vibe_tool/commands/init.py:31-113`
- Modify: `tests/test_init_cmd.py`

**Step 1: Write the failing tests**

Add to `tests/test_init_cmd.py`:
```python
def test_init_creates_vibe_directory(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    assert (project_dir / ".vibe").is_dir()


def test_init_runs_index(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    # Add a source file so index has something to scan
    (project_dir / "src").mkdir()
    (project_dir / "src" / "app.ts").write_text("export function hello() {}\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    assert (project_dir / ".vibe" / "codebase.md").exists()


def test_init_creates_error_memory(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    assert (project_dir / ".vibe" / "errors.md").exists()
    content = (project_dir / ".vibe" / "errors.md").read_text()
    assert "Error Memory" in content


def test_init_installs_prompt_templates(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    prompts = project_dir / ".vibe" / "prompts"
    assert prompts.is_dir()
    assert (prompts / "fix-bug.md").exists()


def test_init_adds_session_context_to_gitignore(tmp_path, monkeypatch):
    project_dir, _ = _setup_env(tmp_path, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0
    gitignore = project_dir / ".gitignore"
    assert gitignore.exists()
    assert "session-context.md" in gitignore.read_text()
```

**Step 2: Run new tests to verify they fail**

Run: `python -m pytest tests/test_init_cmd.py::test_init_creates_vibe_directory tests/test_init_cmd.py::test_init_runs_index tests/test_init_cmd.py::test_init_creates_error_memory tests/test_init_cmd.py::test_init_installs_prompt_templates tests/test_init_cmd.py::test_init_adds_session_context_to_gitignore -v`
Expected: FAIL

**Step 3: Update implementation**

Update `src/vibe_tool/commands/init.py` — add these imports at the top:
```python
from vibe_tool.errors import HEADER as ERRORS_HEADER
from vibe_tool.indexer import scan_project, render_index
from vibe_tool.prompts import install_templates
```

Add this block at the end of the `init()` function, before the final "Project initialized" print (after step 7 "Register project"):

```python
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
```

**Step 4: Run all init tests**

Run: `python -m pytest tests/test_init_cmd.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/commands/init.py tests/test_init_cmd.py
git commit -m "feat: update vibe init to create .vibe/ with index, errors, prompts"
```

---

### Task 8: Update `vibe setup` with v2 Global Rules

**Files:**
- Modify: `src/vibe_tool/templates.py:1-16`
- Modify: `src/vibe_tool/commands/setup.py:1-56`
- Modify: `tests/test_setup_cmd.py`
- Modify: `tests/test_templates.py`

**Step 1: Write the failing tests**

Add to `tests/test_templates.py`:
```python
def test_global_claude_md_contains_context_loading_rules():
    content = get_global_claude_md_addition()
    assert "read the `.vibe/` directory" in content or ".vibe/" in content
    assert "codebase.md" in content
    assert "errors.md" in content
    assert "navigation aid" in content.lower() or "not a source of truth" in content.lower()
```

Add to `tests/test_setup_cmd.py`:
```python
def test_setup_adds_context_loading_rules(tmp_path, monkeypatch):
    vibe_dir = tmp_path / ".vibe"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# Existing\n")

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_dir))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    runner = CliRunner()
    result = runner.invoke(cli, ["setup"], input="acme\nclaude-1\n")
    assert result.exit_code == 0

    content = claude_dir.joinpath("CLAUDE.md").read_text()
    assert ".vibe/" in content
    assert "codebase.md" in content
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_templates.py::test_global_claude_md_contains_context_loading_rules tests/test_setup_cmd.py::test_setup_adds_context_loading_rules -v`
Expected: FAIL

**Step 3: Update `src/vibe_tool/templates.py`**

Append to the return value of `get_global_claude_md_addition()`, after rule 10:
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

## Context Loading Rules (added by vibe-tool)

11. At the start of every session, read the `.vibe/` directory if it exists. Read in order: codebase.md, handoff.md, errors.md, session-context.md.
12. The codebase index (.vibe/codebase.md) is a navigation aid, not a source of truth. Use it to find files fast, then read the actual source before making changes. If the index conflicts with actual code, trust the code and re-run `vibe index`.
13. When you encounter a non-obvious error, append it to .vibe/errors.md using the ERR-NNN format with: when, cause, and fix.
14. After each session milestone, ensure .vibe/codebase.md still reflects any new or changed files, exports, or patterns.
"""
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_templates.py tests/test_setup_cmd.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/templates.py tests/test_templates.py tests/test_setup_cmd.py
git commit -m "feat: add context loading rules to global CLAUDE.md template"
```

---

### Task 9: Update `vibe sync` to Include `.vibe/`

**Files:**
- Modify: `src/vibe_tool/commands/sync.py:9`
- Modify: `tests/test_sync_cmd.py`

**Step 1: Write the failing test**

Add to `tests/test_sync_cmd.py`:
```python
def test_sync_includes_vibe_directory(tmp_path, monkeypatch):
    project_dir = tmp_path / "my-project"
    _make_git_project(project_dir)

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(tmp_path / ".vibe"))
    monkeypatch.chdir(project_dir)

    # Create .vibe/ with context files
    vibe_dir = project_dir / ".vibe"
    vibe_dir.mkdir()
    (vibe_dir / "codebase.md").write_text("# Index\n")
    (vibe_dir / "errors.md").write_text("# Errors\n")
    (vibe_dir / "handoff.md").write_text("# Handoff\n")

    runner = CliRunner()
    result = runner.invoke(cli, ["sync", "push"])
    assert result.exit_code == 0
    assert "Committed" in result.output

    # Verify .vibe files are committed
    log = subprocess.run(
        ["git", "show", "--stat", "HEAD"],
        cwd=project_dir, capture_output=True, text=True
    )
    assert ".vibe/" in log.stdout
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sync_cmd.py::test_sync_includes_vibe_directory -v`
Expected: FAIL

**Step 3: Update `src/vibe_tool/commands/sync.py` line 9**

Change `CONTEXT_FILES` to:
```python
CONTEXT_FILES = ["CLAUDE.md", ".claude", ".vibe"]
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_sync_cmd.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/commands/sync.py tests/test_sync_cmd.py
git commit -m "feat: include .vibe/ directory in vibe sync"
```

---

### Task 10: Hook Script Templates

**Files:**
- Modify: `src/vibe_tool/templates.py`
- Create: `tests/test_hook_templates.py`

**Step 1: Write the failing tests**

Create `tests/test_hook_templates.py`:
```python
from vibe_tool.templates import (
    get_hook_pre_session,
    get_hook_post_session,
    get_hook_post_commit,
)


def test_pre_session_hook_syncs_and_generates_context():
    content = get_hook_pre_session()
    assert "vibe sync pull" in content
    assert "session-context" in content or "preloader" in content


def test_post_session_hook_generates_handoff_and_syncs():
    content = get_hook_post_session()
    assert "handoff" in content
    assert "vibe sync push" in content


def test_post_commit_hook_updates_index():
    content = get_hook_post_commit()
    assert "vibe index" in content
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_hook_templates.py -v`
Expected: FAIL

**Step 3: Add hook templates to `src/vibe_tool/templates.py`**

Append to the file:
```python
def get_hook_pre_session() -> str:
    return """#!/bin/sh
# Vibe tool pre-session hook
# Syncs context from remote and generates temporal session context

# Pull latest context from remote
vibe sync pull 2>/dev/null

# Generate ephemeral session context
python -c "
from pathlib import Path
from vibe_tool.preloader import write_session_context, record_session_start
project = Path.cwd()
write_session_context(project)
record_session_start(project)
" 2>/dev/null

exit 0
"""


def get_hook_post_session() -> str:
    return """#!/bin/sh
# Vibe tool post-session hook
# Generates handoff notes and syncs context to remote

# Generate handoff from session changes
python -c "
from pathlib import Path
from vibe_tool.handoff import write_handoff
project = Path.cwd()
sha_file = project / '.vibe' / '.session-start-sha'
start_sha = sha_file.read_text().strip() if sha_file.exists() else None
write_handoff(project, start_sha)
" 2>/dev/null

# Sync context to remote
vibe sync push 2>/dev/null

exit 0
"""


def get_hook_post_commit() -> str:
    return """#!/bin/sh
# Vibe tool post-commit hook
# Updates codebase index after each commit

vibe index 2>/dev/null

exit 0
"""
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_hook_templates.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/vibe_tool/templates.py tests/test_hook_templates.py
git commit -m "feat: add Claude Code hook script templates for session lifecycle"
```

---

### Task 11: Full v2 Integration Test

**Files:**
- Create: `tests/test_v2_integration.py`

**Step 1: Write the integration test**

Create `tests/test_v2_integration.py`:
```python
"""End-to-end v2 test: init with v2 features, index, error memory, prompts, handoff, pre-loader."""

import os
import subprocess
from pathlib import Path

from click.testing import CliRunner
from vibe_tool.cli import cli
from vibe_tool.config import VibeConfig
from vibe_tool.handoff import generate_handoff
from vibe_tool.preloader import generate_session_context


def _setup(tmp_path, monkeypatch):
    vibe_cfg = tmp_path / ".vibe-cfg"
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_dir.joinpath("CLAUDE.md").write_text("# rules\n")
    project = tmp_path / "test-project"
    project.mkdir()

    monkeypatch.setenv("VIBE_CONFIG_DIR", str(vibe_cfg))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))

    # Setup
    runner = CliRunner()
    runner.invoke(cli, ["setup"], input="acme\nclaude-1\n")

    # Init git
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=project, check=True)

    # Add source files
    src = project / "src"
    src.mkdir()
    (src / "app.ts").write_text("""
import { db } from './db';
export function startServer(port: number) { }
export function healthCheck() { return 'ok'; }
""")
    (src / "db.ts").write_text("""
export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    email: varchar('email'),
});
""")

    # .env files for pre-loader test
    (project / ".env.example").write_text("DATABASE_URL=\nAPI_KEY=\n")
    (project / ".env").write_text("DATABASE_URL=postgres://localhost\n")

    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)

    monkeypatch.chdir(project)
    return project, runner


def test_full_v2_workflow(tmp_path, monkeypatch):
    project, runner = _setup(tmp_path, monkeypatch)

    # 1. Init project (should create .vibe/ with all v2 features)
    result = runner.invoke(cli, ["init"], input="1\n1\n1\n")
    assert result.exit_code == 0

    # Verify .vibe/ structure
    vibe_dir = project / ".vibe"
    assert vibe_dir.is_dir()
    assert (vibe_dir / "codebase.md").exists()
    assert (vibe_dir / "errors.md").exists()
    assert (vibe_dir / "prompts" / "fix-bug.md").exists()

    # 2. Verify codebase index content
    index_content = (vibe_dir / "codebase.md").read_text()
    assert "app.ts" in index_content
    assert "startServer" in index_content
    assert "users" in index_content  # table from db.ts

    # 3. Re-run index to verify idempotency
    result = runner.invoke(cli, ["index"])
    assert result.exit_code == 0
    assert "Indexed" in result.output

    # 4. Add an error
    result = runner.invoke(cli, ["error", "add"],
        input="Port in use\nStarting server\nPort 3000 already bound\nKill process on port 3000\n")
    assert result.exit_code == 0

    # Verify error was recorded
    result = runner.invoke(cli, ["error", "list"])
    assert "ERR-001" in result.output
    assert "Port in use" in result.output

    # 5. List prompt templates
    result = runner.invoke(cli, ["prompt", "list"])
    assert result.exit_code == 0
    assert "fix-bug" in result.output
    assert "add-endpoint" in result.output

    # 6. Show a template
    result = runner.invoke(cli, ["prompt", "show", "fix-bug"])
    assert "errors.md" in result.output

    # 7. Generate session context (pre-loader)
    md = generate_session_context(project)
    assert "## Git State" in md
    assert "## Environment Notes" in md
    assert "API_KEY" in md  # missing from .env

    # 8. Make a change and generate handoff
    start_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True
    ).stdout.strip()

    (project / "src" / "new-feature.ts").write_text("export function newThing() {}\n")
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feat: add new feature"], cwd=project, check=True)

    handoff = generate_handoff(project, start_sha)
    assert "## What was done" in handoff
    assert "new feature" in handoff
    assert "new-feature.ts" in handoff

    # 9. Verify .gitignore has session-context.md
    gitignore = (project / ".gitignore").read_text()
    assert "session-context.md" in gitignore
```

**Step 2: Run the integration test**

Run: `python -m pytest tests/test_v2_integration.py -v`
Expected: All PASS

**Step 3: Run full test suite**

Run: `python -m pytest -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_v2_integration.py
git commit -m "test: add full v2 integration test for context intelligence features"
```

---

### Task 12: Update README

**Files:**
- Modify: `README.md`

**Step 1: Read current README**

Read: `README.md`

**Step 2: Update README with v2 features**

Add after the existing "Manage clients" section:

```markdown
### Index your codebase

```bash
vibe index              # Pattern-based scan (fast, free)
vibe index --deep       # Claude-powered analysis (richer)
```

Generates `.vibe/codebase.md` — a complete map of your codebase that Claude reads instead of exploring files one by one.

### Track errors

```bash
vibe error add          # Record an error and its solution
vibe error list         # View all recorded errors
```

Claude also writes to `.vibe/errors.md` automatically when it debugs non-obvious issues.

### Use prompt templates

```bash
vibe prompt list              # See available templates
vibe prompt show fix-bug      # View a template
vibe prompt copy add-endpoint # Copy to clipboard
vibe prompt create deploy     # Create custom template
```

### How context flows

When you start a Claude Code session:
1. Claude reads `.vibe/codebase.md` — knows your entire codebase structure
2. Claude reads `.vibe/handoff.md` — knows what happened last session
3. Claude reads `.vibe/errors.md` — knows past gotchas
4. Claude reads `.vibe/session-context.md` — knows current git state and env

Result: Claude starts writing code immediately instead of spending 60%+ of time exploring your codebase.
```

**Step 3: Run full test suite one final time**

Run: `python -m pytest -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: update README with v2 context intelligence features"
```

---

## Execution Summary

| Task | Description | New Tests |
|---|---|---|
| 1 | Codebase parser (JS/TS + Python) | 6 |
| 2 | `vibe index` command + indexer module | 4 |
| 3 | Session handoff generator | 3 |
| 4 | Session pre-loader generator | 5 |
| 5 | Error memory module + commands | 8 |
| 6 | Prompt templates module + commands | 9 |
| 7 | Update `vibe init` for v2 | 5 |
| 8 | Update `vibe setup` + templates with context rules | 2 |
| 9 | Update `vibe sync` to include `.vibe/` | 1 |
| 10 | Hook script templates | 3 |
| 11 | Full v2 integration test | 1 |
| 12 | Update README | 0 |
| **Total** | | **47 new tests** |

**Dependency order:** 1 → 2, 3, 4, 5, 6 (parallel after 1) → 7 → 8, 9 (parallel) → 10 → 11 → 12
