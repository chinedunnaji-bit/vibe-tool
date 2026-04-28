import json
from pathlib import Path


def detect_project(project_dir: Path) -> dict:
    """Auto-detect project type and stack from files in the directory."""

    # Check for Node/JS projects
    package_json = project_dir / "package.json"
    if package_json.exists():
        return _detect_node(package_json)

    # Check for Python projects
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        return _detect_python_from_pyproject(pyproject)

    requirements = project_dir / "requirements.txt"
    if requirements.exists():
        return _detect_python_from_requirements(requirements)

    # Check for Go projects
    if (project_dir / "go.mod").exists():
        return {"project_type": "cli", "stack": "go", "label": "Go project"}

    # Check for Rust projects
    if (project_dir / "Cargo.toml").exists():
        return {"project_type": "cli", "stack": "rust", "label": "Rust project"}

    # Nothing detected
    return {"project_type": "other", "stack": "other", "label": "empty project"}


def _detect_node(package_json: Path) -> dict:
    """Detect stack from package.json."""
    try:
        data = json.loads(package_json.read_text())
    except (json.JSONDecodeError, OSError):
        return {"project_type": "web", "stack": "node", "label": "Node.js project"}

    all_deps = {}
    all_deps.update(data.get("dependencies", {}))
    all_deps.update(data.get("devDependencies", {}))

    # Mobile
    if "expo" in all_deps or "react-native" in all_deps:
        return {"project_type": "mobile", "stack": "expo", "label": "React Native / Expo project"}

    # Frameworks
    if "next" in all_deps:
        return {"project_type": "web", "stack": "next", "label": "Next.js project"}

    if "svelte" in all_deps or "@sveltejs/kit" in all_deps:
        return {"project_type": "web", "stack": "svelte", "label": "SvelteKit project"}

    # API frameworks
    if "express" in all_deps:
        return {"project_type": "api", "stack": "express", "label": "Express API"}

    if "fastify" in all_deps:
        return {"project_type": "api", "stack": "fastify", "label": "Fastify API"}

    if "hono" in all_deps:
        return {"project_type": "api", "stack": "hono", "label": "Hono API"}

    # Vite (check after frameworks since Next/Svelte may also have vite)
    if "vite" in all_deps:
        return {"project_type": "web", "stack": "vite", "label": "Vite project"}

    # Generic Node
    return {"project_type": "web", "stack": "node", "label": "Node.js project"}


def _detect_python_from_pyproject(pyproject: Path) -> dict:
    """Detect Python framework from pyproject.toml."""
    try:
        content = pyproject.read_text().lower()
    except OSError:
        return {"project_type": "api", "stack": "python", "label": "Python project"}

    if "fastapi" in content:
        return {"project_type": "api", "stack": "fastapi", "label": "FastAPI project"}
    if "django" in content:
        return {"project_type": "api", "stack": "django", "label": "Django project"}
    if "flask" in content:
        return {"project_type": "api", "stack": "flask", "label": "Flask project"}
    if "click" in content or "typer" in content:
        return {"project_type": "cli", "stack": "python", "label": "Python CLI project"}

    return {"project_type": "api", "stack": "python", "label": "Python project"}


def _detect_python_from_requirements(requirements: Path) -> dict:
    """Detect Python framework from requirements.txt."""
    try:
        content = requirements.read_text().lower()
    except OSError:
        return {"project_type": "api", "stack": "python", "label": "Python project"}

    if "fastapi" in content:
        return {"project_type": "api", "stack": "fastapi", "label": "FastAPI project"}
    if "django" in content:
        return {"project_type": "api", "stack": "django", "label": "Django project"}
    if "flask" in content:
        return {"project_type": "api", "stack": "flask", "label": "Flask project"}

    return {"project_type": "api", "stack": "python", "label": "Python project"}
