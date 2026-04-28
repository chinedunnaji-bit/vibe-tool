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


# --- Go ---

def test_git_hook_pre_commit_go():
    content = get_git_hook_pre_commit("cli", "go")
    assert content.startswith("#!/")
    assert "golangci-lint" in content or "go vet" in content


def test_git_hook_pre_push_go():
    content = get_git_hook_pre_push("cli", "go")
    assert content.startswith("#!/")
    assert "go test" in content


def test_github_actions_go():
    content = get_github_actions_ci("cli", "go")
    assert "go" in content.lower()
    assert "go test" in content


# --- Rust ---

def test_git_hook_pre_commit_rust():
    content = get_git_hook_pre_commit("cli", "rust")
    assert content.startswith("#!/")
    assert "clippy" in content or "cargo check" in content


def test_git_hook_pre_push_rust():
    content = get_git_hook_pre_push("cli", "rust")
    assert content.startswith("#!/")
    assert "cargo test" in content


def test_github_actions_rust():
    content = get_github_actions_ci("cli", "rust")
    assert "cargo test" in content
    assert "clippy" in content or "lint" in content.lower()


# --- Django ---

def test_git_hook_pre_commit_django():
    content = get_git_hook_pre_commit("api", "django")
    assert content.startswith("#!/")
    assert "ruff" in content


def test_git_hook_pre_push_django():
    content = get_git_hook_pre_push("api", "django")
    assert content.startswith("#!/")
    assert "pytest" in content or "manage.py test" in content


def test_github_actions_django():
    content = get_github_actions_ci("api", "django")
    assert "python" in content.lower()
    assert "pytest" in content or "test" in content


# --- SvelteKit ---

def test_git_hook_pre_commit_svelte():
    content = get_git_hook_pre_commit("web", "svelte")
    assert content.startswith("#!/")
    assert "lint" in content.lower()


def test_git_hook_pre_push_svelte():
    content = get_git_hook_pre_push("web", "svelte")
    assert content.startswith("#!/")
    assert "test" in content.lower()


def test_github_actions_svelte():
    content = get_github_actions_ci("web", "svelte")
    assert "npm" in content
    assert "test" in content


# --- Fullstack ---

def test_github_actions_fullstack_next():
    content = get_github_actions_ci("fullstack", "next")
    assert "npm" in content
    assert "test" in content


def test_github_actions_fullstack_vite_fastapi():
    content = get_github_actions_ci("fullstack", "vite-fastapi")
    assert "python" in content.lower()
    assert "node" in content.lower()
    assert "pytest" in content
    assert "npm" in content


def test_global_claude_md_contains_context_loading_rules():
    content = get_global_claude_md_addition()
    assert "read the `.vibe/` directory" in content or ".vibe/" in content
    assert "codebase.md" in content
    assert "errors.md" in content
    assert "navigation aid" in content.lower() or "not a source of truth" in content.lower()
