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
