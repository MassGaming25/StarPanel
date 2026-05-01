"""
Captain's Log persistence.
Saved to XDG_DATA_HOME/starpanel/captains_log.json
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

ENTRY_TYPES = [
    "Combat / Battle Report",
    "Trade Run",
    "Exploration / Discovery",
    "Mission / Bounty",
    "General / Personal Log",
    "Incident Report",
    "Departed Location",
    "Arrived at Location",
]

ENTRY_COLORS = {
    "Combat / Battle Report":  "#e53935",
    "Trade Run":               "#f0a800",
    "Exploration / Discovery": "#00e5ff",
    "Mission / Bounty":        "#ab47bc",
    "General / Personal Log":  "#b0d4e8",
    "Incident Report":         "#ff7043",
    "Departed Location":       "#6a9ab8",
    "Arrived at Location":     "#00e676",
}


def _path() -> Path:
    data_home = os.environ.get(
        "XDG_DATA_HOME",
        os.path.join(os.path.expanduser("~"), ".local", "share")
    )
    p = Path(data_home) / "starpanel"
    p.mkdir(parents=True, exist_ok=True)
    return p / "captains_log.json"


def load_log() -> list:
    p = _path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return []
    return []


def _save(entries: list):
    _path().write_text(json.dumps(entries, indent=2))


def add_entry(entry: dict) -> dict:
    entries = load_log()
    entry["id"]        = str(uuid.uuid4())[:8]
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    entries.insert(0, entry)   # newest first
    _save(entries)
    return entry


def update_entry(entry_id: str, entry: dict) -> bool:
    entries = load_log()
    for i, e in enumerate(entries):
        if e.get("id") == entry_id:
            entry["id"]        = entry_id
            entry["timestamp"] = e["timestamp"]   # preserve original time
            entry["edited"]    = datetime.now(timezone.utc).isoformat()
            entries[i] = entry
            _save(entries)
            return True
    return False


def delete_entry(entry_id: str) -> bool:
    entries = load_log()
    new = [e for e in entries if e.get("id") != entry_id]
    if len(new) < len(entries):
        _save(new)
        return True
    return False
