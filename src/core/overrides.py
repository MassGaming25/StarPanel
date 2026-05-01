"""
User-defined ship status overrides.
Saved to XDG_DATA_HOME/starpanel/status_overrides.json.
Takes priority over all API sources.
"""

import json
import os
from pathlib import Path


def _path() -> Path:
    data_home = os.environ.get(
        "XDG_DATA_HOME",
        os.path.join(os.path.expanduser("~"), ".local", "share")
    )
    p = Path(data_home) / "starpanel"
    p.mkdir(parents=True, exist_ok=True)
    return p / "status_overrides.json"


def load_overrides() -> dict:
    """Return {ship_name_lowercase: status_string}."""
    p = _path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


def save_override(ship_name: str, status: str):
    overrides = load_overrides()
    overrides[ship_name.lower().strip()] = status
    _path().write_text(json.dumps(overrides, indent=2))


def remove_override(ship_name: str):
    overrides = load_overrides()
    key = ship_name.lower().strip()
    if key in overrides:
        del overrides[key]
        _path().write_text(json.dumps(overrides, indent=2))


def apply_overrides(ships: list) -> list:
    """Apply saved user overrides to a ship list. Returns the list."""
    overrides = load_overrides()
    if not overrides:
        return ships
    for ship in ships:
        key = ship.get("name", "").lower().strip()
        if key in overrides:
            ship["status"] = overrides[key]
    return ships
