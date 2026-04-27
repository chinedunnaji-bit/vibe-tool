# Vibe Tool — Design Document

**Date:** 2026-04-27
**Goal:** 100x productivity for a non-engineer building web apps, mobile apps, and APIs with Claude Code across 2 Macs and multiple Claude accounts (per-client billing).

**Core problems solved:**
1. Cannot spot bugs by code inspection — needs automated quality gates
2. Wastes time re-explaining project context in new Claude sessions

---

## Architecture Overview

Five components, no web server, no cloud backend (except Git remote and GitHub Actions):

```
┌─────────────────────────────────────────────┐
│                 Both Macs                    │
│                                              │
│  ~/.claude/CLAUDE.md  (global quality rules) │
│  ~/.vibe/projects.json (project index)       │
│  ~/.vibe/config.json   (clients/accounts)    │
│                                              │
│  Per Project:                                │
│  ├── CLAUDE.md         (project context)     │
│  ├── .claude/          (memory, settings)    │
│  ├── .git/hooks/       (pre-commit, pre-push)│
│  ├── .github/workflows/(CI pipeline)         │
│  └── tests/            (auto-generated)      │
│                                              │
│  Claude Code Hooks:                          │
│  ├── pre-session:  vibe sync pull            │
│  ├── post-commit:  run tests, update index   │
│  └── post-session: commit context, sync push │
└─────────────────────────────────────────────┘
         │
         │ Git push/pull (.claude/, CLAUDE.md)
         ▼
   ┌──────────┐
   │ Git Remote│  (GitHub/GitLab — already used for code)
   └──────────┘
```

---

## Component 1: Global CLAUDE.md

**Location:** `~/.claude/CLAUDE.md` (both Macs)

**Purpose:** Enforce quality rules on every Claude Code session regardless of project or account.

**Rules enforced:**
1. Always write tests before implementation (TDD)
2. Always run full test suite before claiming any task is complete
3. Never say "done" without pasting test output as proof
4. Fix failing tests before moving on — do not ask the user to fix them
5. Run the app/server and verify end-to-end after completing a feature
6. When modifying existing code, run tests before AND after changes
7. Update project CLAUDE.md with architectural decisions and current state
8. Update Claude Code memory after significant milestones
9. Write behavioral tests (test what it does, not how it does it)
10. If unsure about a requirement, ask — do not guess and ship

**Note:** This augments the user's existing global CLAUDE.md, which focuses on honest assessment and rigorous mentorship.

---

## Component 2: `vibe init` — Project Scaffolding

**Purpose:** Set up any new project with quality gates from minute one.

**Flow:**
1. Prompt for client (maps to Claude account for billing)
2. Prompt for project type (web app, mobile app, API) or description
3. Scaffold appropriate test framework, linting, git hooks, CI
4. Create project CLAUDE.md template
5. Initialize Claude Code memory
6. Register project in `~/.vibe/projects.json`

**Scaffolding matrix:**

| Project Type | Framework Options | Test Framework | E2E Testing | Linting |
|---|---|---|---|---|
| Web app | Next.js, React + Vite | Vitest | Playwright | ESLint + Prettier |
| Mobile app | React Native, Expo | Jest | Detox | ESLint + Prettier |
| API (JS/TS) | Express, Fastify, Hono | Vitest | Supertest | ESLint + Prettier |
| API (Python) | FastAPI, Flask | pytest | pytest + httpx | Ruff |

**Git hooks installed:**
- `pre-commit`: lint + type check (fast, blocks broken syntax)
- `pre-push`: full test suite (blocks pushes with failing tests)

**CI pipeline:**
- GitHub Actions workflow: lint, type check, test on every push
- Fail-fast: stops on first failure

**Project CLAUDE.md template:**
```markdown
# [Project Name]

## What this is
[One-line description]

## Architecture
[Updated by Claude as the project evolves]

## How to run
- `[command]` — start dev server
- `[command]` — run tests
- `[command]` — run E2E tests
- `[command]` — lint

## Key decisions
[Updated by Claude as decisions are made]

## Current state
[Updated by Claude after each session]
```

**`~/.vibe/projects.json` schema:**
```json
{
  "projects": [
    {
      "name": "marketplace",
      "path": "/Users/chinedunnaji/Documents/workspace/marketplace",
      "client": "client-a",
      "type": "web",
      "stack": "next",
      "created": "2026-04-27",
      "lastActive": "2026-04-27T14:30:00Z",
      "testCount": { "pass": 24, "fail": 0, "total": 24 }
    }
  ]
}
```

---

## Component 3: Context Continuity System

**Purpose:** New Claude Code sessions automatically have full project context. No re-explaining.

**Three layers:**

### Layer 1: Project CLAUDE.md (auto-maintained)
- Created by `vibe init`, updated by Claude after every significant change
- Contains: what the project is, architecture, how to run, key decisions, current state
- Read automatically by Claude Code when a session starts in the project directory

### Layer 2: Claude Code Memory (auto-updated)
- `.claude/` directory with memory files
- Global CLAUDE.md rules enforce updates after milestones
- Stores granular context: decisions, user preferences, project-specific patterns

### Layer 3: `vibe sync` (cross-machine sync)
- Commits `.claude/` directory and `CLAUDE.md` to Git
- Pushes to remote, pulls on other machine
- Runs automatically via Claude Code hooks (pre-session pull, post-session push)
- Git handles conflicts naturally

**`vibe sync` commands:**
- `vibe sync` — pull then push (default)
- `vibe sync push` — push only
- `vibe sync pull` — pull only

---

## Component 4: `vibe status` — Cross-Project Visibility

**Purpose:** One command to see all projects, their health, and current state.

**Output grouped by client:**
```
┌─────────────────────────────────────────────────────────────────┐
│ CLIENT-A (claude-account1)                                      │
├──────────────┬──────────┬───────┬────────────┬──────────────────┤
│ Project      │ Tests    │ Stack │ Last Active│ Status           │
├──────────────┼──────────┼───────┼────────────┼──────────────────┤
│ marketplace  │ 24/24 ✓  │ Next  │ 2h ago     │ Payment WIP      │
│ admin-portal │ 11/11 ✓  │ Next  │ 1d ago     │ Deployed         │
├─────────────────────────────────────────────────────────────────┤
│ CLIENT-B (claude-account2)                                      │
├──────────────┬──────────┬───────┬────────────┬──────────────────┤
│ fitness-api  │ 18/20 ✗  │ Py    │ 1d ago     │ 2 tests failing  │
│ mobile-app   │ 12/12 ✓  │ RN    │ 3d ago     │ Ready for review │
└──────────────┴──────────┴───────┴────────────┴──────────────────┘
```

**Data sources:**
- Test counts: cached from last test run (updated by post-commit hook)
- Last active: from Git log
- Status: parsed from "Current state" section of project CLAUDE.md
- Client grouping: from `~/.vibe/projects.json`

---

## Component 5: Claude Code Hooks

**Purpose:** Automate everything so nothing requires user discipline.

**Location:** `~/.claude/settings.json` (both Macs)

**Hooks:**

| Event | Action | Purpose |
|---|---|---|
| Pre-session start | `vibe sync pull` for current project | Latest context from other Mac |
| Post-commit | Run test suite, update project index | Fresh test counts in `vibe status` |
| Post-session end | Commit CLAUDE.md + .claude/ changes, `vibe sync push` | Preserve and sync context |
| Pre-push | Run full test suite, block if failing | No broken code leaves the machine |

---

## Tech Stack for the CLI

- **Language:** Python 3.11+
- **Package:** Installable via `pip install vibe-tool`
- **Dependencies:** Minimal — click (CLI framework), rich (terminal UI for status table), GitPython (Git operations)
- **Config:** JSON files in `~/.vibe/`
- **No server, no database, no cloud services** (beyond Git remote)

---

## Installation (one-time per Mac)

```bash
pip install vibe-tool
vibe setup
```

`vibe setup` does:
1. Augments `~/.claude/CLAUDE.md` with quality rules
2. Configures Claude Code hooks in `~/.claude/settings.json`
3. Creates `~/.vibe/` config directory
4. Prompts to add clients/accounts

---

## CLI Command Summary

| Command | What it does |
|---|---|
| `vibe setup` | One-time machine setup (global CLAUDE.md, hooks, config) |
| `vibe init` | Scaffold new project with tests, hooks, CI, context |
| `vibe status` | Show all projects grouped by client with test health |
| `vibe sync` | Sync project context across machines via Git |
| `vibe client add` | Register a new client/account |
| `vibe client list` | List configured clients |

---

## Known Limitations

1. **Test quality is not guaranteed.** Claude can write tests that pass but don't test meaningful behavior. The global CLAUDE.md includes rules about behavioral testing, but this improves over time, not overnight.
2. **Context sync relies on Git.** Both Macs need access to the same Git remotes. If a project isn't pushed yet, sync won't work.
3. **Hook reliability.** Claude Code hooks may not fire if a session crashes or is force-killed. Context from that session could be lost.
4. **No real-time monitoring.** `vibe status` is a snapshot, not a live dashboard. This is intentional — a dashboard can be built later on top of this foundation if needed.
5. **Account switching is manual.** The tool tracks which client maps to which account, but switching Claude accounts is still done by the user in Claude Code.
