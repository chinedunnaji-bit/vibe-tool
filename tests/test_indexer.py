from pathlib import Path
from vibe_tool.indexer import scan_project, render_index


def _create_project(tmp_path):
    """Create a minimal JS project for testing."""
    src = tmp_path / "src"
    src.mkdir()

    (src / "index.ts").write_text("""
import { db } from './db';
export function main() { console.log('hello'); }
""")

    (src / "db.ts").write_text("""
export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    email: varchar('email'),
});
""")

    routes = src / "api"
    routes.mkdir()
    (routes / "auth.ts").write_text("""
import { db } from '../db';
router.post('/login', loginHandler);
router.post('/signup', signupHandler);
export function loginHandler(req, res) {}
export function signupHandler(req, res) {}
""")

    # Non-source files should be ignored
    (tmp_path / "package.json").write_text('{"name": "test"}')
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("junk")

    return tmp_path


def test_scan_project_finds_source_files(tmp_path):
    project = _create_project(tmp_path)
    result = scan_project(project)
    paths = [r["path"] for r in result]
    assert any("index.ts" in p for p in paths)
    assert any("auth.ts" in p for p in paths)
    # node_modules should be excluded
    assert not any("node_modules" in p for p in paths)


def test_scan_project_extracts_exports(tmp_path):
    project = _create_project(tmp_path)
    result = scan_project(project)
    auth = next(r for r in result if "auth.ts" in r["path"])
    assert any("loginHandler" in e for e in auth["parsed"]["exports"])


def test_render_index_produces_markdown(tmp_path):
    project = _create_project(tmp_path)
    scanned = scan_project(project)
    md = render_index(scanned, project)
    assert "## File Map" in md
    assert "## Exports" in md
    assert "auth.ts" in md
    assert "loginHandler" in md


def test_render_index_includes_dependencies(tmp_path):
    project = _create_project(tmp_path)
    scanned = scan_project(project)
    md = render_index(scanned, project)
    assert "## Dependencies" in md
