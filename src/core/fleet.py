"""Fleet persistence — saves to XDG_DATA_HOME for Flatpak compatibility."""

import json
import os
from pathlib import Path


def _fleet_path() -> Path:
    data_home = os.environ.get(
        "XDG_DATA_HOME",
        os.path.join(os.path.expanduser("~"), ".local", "share")
    )
    app_dir = Path(data_home) / "starpanel"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / "fleet.json"


def load_fleet() -> list:
    path = _fleet_path()
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return []
    return []


def save_fleet(fleet: list):
    _fleet_path().write_text(json.dumps(fleet, indent=2))


def add_ship(entry: dict) -> dict:
    import uuid
    entry["id"] = str(uuid.uuid4())[:8]
    fleet = load_fleet()
    fleet.append(entry)
    save_fleet(fleet)
    return entry


def update_ship(entry_id: str, entry: dict) -> bool:
    fleet = load_fleet()
    for i, e in enumerate(fleet):
        if e.get("id") == entry_id:
            entry["id"] = entry_id
            fleet[i] = entry
            save_fleet(fleet)
            return True
    return False


def delete_ship(entry_id: str) -> bool:
    fleet = load_fleet()
    new_fleet = [e for e in fleet if e.get("id") != entry_id]
    if len(new_fleet) < len(fleet):
        save_fleet(new_fleet)
        return True
    return False
