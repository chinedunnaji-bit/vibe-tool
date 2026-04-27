from pathlib import Path
from vibe_tool.errors import load_errors, add_error, render_errors_md, get_next_id


def test_load_errors_empty(tmp_path):
    errors_file = tmp_path / "errors.md"
    assert load_errors(errors_file) == []


def test_add_and_load_error(tmp_path):
    errors_file = tmp_path / "errors.md"
    add_error(errors_file, title="Module not found", when="importing @/lib", cause="tsconfig paths missing", fix="Add baseUrl to tsconfig")
    entries = load_errors(errors_file)
    assert len(entries) == 1
    assert entries[0]["id"] == "ERR-001"
    assert entries[0]["title"] == "Module not found"


def test_add_multiple_errors_increments_id(tmp_path):
    errors_file = tmp_path / "errors.md"
    add_error(errors_file, title="First", when="w1", cause="c1", fix="f1")
    add_error(errors_file, title="Second", when="w2", cause="c2", fix="f2")
    entries = load_errors(errors_file)
    assert len(entries) == 2
    assert entries[0]["id"] == "ERR-001"
    assert entries[1]["id"] == "ERR-002"


def test_get_next_id_empty(tmp_path):
    errors_file = tmp_path / "errors.md"
    assert get_next_id(errors_file) == "ERR-001"


def test_get_next_id_after_entries(tmp_path):
    errors_file = tmp_path / "errors.md"
    add_error(errors_file, title="First", when="w", cause="c", fix="f")
    assert get_next_id(errors_file) == "ERR-002"


def test_render_errors_md(tmp_path):
    errors_file = tmp_path / "errors.md"
    add_error(errors_file, title="Test error", when="testing", cause="bad config", fix="fix config")
    content = errors_file.read_text()
    assert "# Error Memory" in content
    assert "ERR-001" in content
    assert "Test error" in content
    assert "**When:**" in content
    assert "**Fix:**" in content
