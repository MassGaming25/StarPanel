"""User-defined ship status overrides."""

import json
from core.storage import data_file


def _path():
    return data_file("status_overrides.json")


def load_overrides() -> dict:
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
    overrides = load_overrides()
    if not overrides:
        return ships
    for ship in ships:
        key = ship.get("name", "").lower().strip()
        if key in overrides:
            ship["status"] = overrides[key]
    return ships
