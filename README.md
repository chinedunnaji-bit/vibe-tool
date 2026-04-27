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
