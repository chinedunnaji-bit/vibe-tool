from pathlib import Path
from vibe_tool.detect import detect_project


def test_detect_node_project(tmp_path):
    (tmp_path / "package.json").write_text('{"name": "my-app"}')
    result = detect_project(tmp_path)
    assert result["stack"] in ("next", "vite", "svelte", "node", "express")
    assert result["project_type"] in ("web", "api", "fullstack", "cli")


def test_detect_next_project(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"next": "14.0"}}')
    result = detect_project(tmp_path)
    assert result["stack"] == "next"


def test_detect_vite_project(tmp_path):
    (tmp_path / "package.json").write_text('{"devDependencies": {"vite": "5.0"}}')
    result = detect_project(tmp_path)
    assert result["stack"] == "vite"


def test_detect_express_project(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"express": "4.0"}}')
    result = detect_project(tmp_path)
    assert result["stack"] == "express"
    assert result["project_type"] == "api"


def test_detect_python_project(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-app"\n')
    result = detect_project(tmp_path)
    assert result["stack"] in ("python", "fastapi", "flask", "django")


def test_detect_fastapi_project(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["fastapi"]\n')
    result = detect_project(tmp_path)
    assert result["stack"] == "fastapi"


def test_detect_django_project(tmp_path):
    (tmp_path / "requirements.txt").write_text("django==5.0\n")
    result = detect_project(tmp_path)
    assert result["stack"] == "django"


def test_detect_flask_project(tmp_path):
    (tmp_path / "requirements.txt").write_text("flask==3.0\n")
    result = detect_project(tmp_path)
    assert result["stack"] == "flask"


def test_detect_go_project(tmp_path):
    (tmp_path / "go.mod").write_text("module example.com/myapp\n")
    result = detect_project(tmp_path)
    assert result["stack"] == "go"


def test_detect_rust_project(tmp_path):
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "my-app"\n')
    result = detect_project(tmp_path)
    assert result["stack"] == "rust"


def test_detect_expo_project(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"expo": "50.0"}}')
    result = detect_project(tmp_path)
    assert result["stack"] == "expo"
    assert result["project_type"] == "mobile"


def test_detect_empty_project(tmp_path):
    result = detect_project(tmp_path)
    assert result["stack"] == "other"
    assert result["project_type"] == "other"


def test_detect_returns_label(tmp_path):
    (tmp_path / "go.mod").write_text("module example.com/myapp\n")
    result = detect_project(tmp_path)
    assert "label" in result
    assert len(result["label"]) > 0
