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
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - name: Lint
        run: npm run lint
      - name: Test
        run: npm test
"""
