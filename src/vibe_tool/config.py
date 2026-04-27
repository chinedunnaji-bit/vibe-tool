import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".vibe"


class VibeConfig:
    def __init__(self, config_dir: Path = DEFAULT_CONFIG_DIR):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.projects_file = self.config_dir / "projects.json"

    def ensure_dirs(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    def _write_json(self, path: Path, data: dict):
        path.write_text(json.dumps(data, indent=2) + "\n")

    # --- Clients ---

    def load_clients(self) -> list[dict]:
        data = self._read_json(self.config_file)
        return data.get("clients", [])

    def add_client(self, name: str, account: str = ""):
        data = self._read_json(self.config_file)
        clients = data.get("clients", [])
        if any(c["name"] == name for c in clients):
            raise ValueError(f"Client '{name}' already exists")
        clients.append({"name": name, "account": account})
        data["clients"] = clients
        self._write_json(self.config_file, data)

    # --- Projects ---

    def load_projects(self) -> list[dict]:
        data = self._read_json(self.projects_file)
        return data.get("projects", [])

    def add_project(self, name: str, path: str, client: str, project_type: str, stack: str):
        data = self._read_json(self.projects_file)
        projects = data.get("projects", [])
        now = datetime.now(timezone.utc).isoformat()
        projects.append({
            "name": name,
            "path": path,
            "client": client,
            "type": project_type,
            "stack": stack,
            "created": now[:10],
            "lastActive": now,
            "testCount": {"pass": 0, "fail": 0, "total": 0},
        })
        data["projects"] = projects
        self._write_json(self.projects_file, data)

    def update_project_tests(self, name: str, passed: int, failed: int, total: int):
        data = self._read_json(self.projects_file)
        projects = data.get("projects", [])
        for p in projects:
            if p["name"] == name:
                p["testCount"] = {"pass": passed, "fail": failed, "total": total}
                p["lastActive"] = datetime.now(timezone.utc).isoformat()
                break
        data["projects"] = projects
        self._write_json(self.projects_file, data)
