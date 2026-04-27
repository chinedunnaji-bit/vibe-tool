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


def test_global_claude_md_contains_context_loading_rules():
    content = get_global_claude_md_addition()
    assert "read the `.vibe/` directory" in content or ".vibe/" in content
    assert "codebase.md" in content
    assert "errors.md" in content
    assert "navigation aid" in content.lower() or "not a source of truth" in content.lower()
