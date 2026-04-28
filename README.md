# vibe-tool

CLI tool for Claude Code productivity — automated quality gates and context continuity across machines and accounts.

## Install

```bash
# Recommended — installs globally with PATH handled automatically
pipx install git+https://github.com/chinedunnaji-bit/vibe-tool.git

# Alternative — standard pip
pip install git+https://github.com/chinedunnaji-bit/vibe-tool.git
```

After install, run `vibe --help` to verify. If pip warns about PATH, you can always use:

```bash
python3 -m vibe_tool --help
```

## Setup (one-time per machine)

```bash
vibe setup
# or: python3 -m vibe_tool setup
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

## How context flows

When you start a Claude Code session:
1. Claude reads `.vibe/codebase.md` — knows your entire codebase structure
2. Claude reads `.vibe/handoff.md` — knows what happened last session
3. Claude reads `.vibe/errors.md` — knows past gotchas
4. Claude reads `.vibe/session-context.md` — knows current git state and env

Result: Claude starts writing code immediately instead of spending 60%+ of time exploring your codebase.

## What it does

1. **Quality gates** — Every project gets tests, git hooks, and CI from day one. Claude Code is instructed to always write tests, always run them, and never claim "done" without proof.

2. **Context continuity** — Project CLAUDE.md and Claude Code memory are auto-maintained and synced across machines via Git. New sessions know everything — no re-explaining.

3. **Cross-project visibility** — `vibe status` shows all projects grouped by client with test health, last activity, and current state.
