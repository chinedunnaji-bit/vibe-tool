import json
from pathlib import Path

from vibe_tool.config import VibeConfig


def test_init_creates_config_dir(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    assert (tmp_path / ".vibe").is_dir()


def test_load_clients_empty(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    assert config.load_clients() == []


def test_add_client(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    config.add_client("acme-corp", "claude-account1")
    clients = config.load_clients()
    assert len(clients) == 1
    assert clients[0]["name"] == "acme-corp"
    assert clients[0]["account"] == "claude-account1"


def test_add_duplicate_client_raises(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    config.add_client("acme-corp", "claude-account1")
    import pytest
    with pytest.raises(ValueError, match="already exists"):
        config.add_client("acme-corp", "claude-account2")


def test_load_projects_empty(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    assert config.load_projects() == []


def test_add_project(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    config.add_project(
        name="marketplace",
        path="/some/path",
        client="acme-corp",
        project_type="web",
        stack="next",
    )
    projects = config.load_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == "marketplace"
    assert projects[0]["client"] == "acme-corp"


def test_update_project_tests(tmp_path):
    config = VibeConfig(config_dir=tmp_path / ".vibe")
    config.ensure_dirs()
    config.add_project(
        name="marketplace",
        path="/some/path",
        client="acme-corp",
        project_type="web",
        stack="next",
    )
    config.update_project_tests("marketplace", passed=22, failed=2, total=24)
    projects = config.load_projects()
    assert projects[0]["testCount"] == {"pass": 22, "fail": 2, "total": 24}
