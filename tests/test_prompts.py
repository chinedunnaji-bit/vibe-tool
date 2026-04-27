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
