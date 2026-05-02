"""
StarPanel storage path resolution.

Linux:   ~/.local/share/starpanel/   (respects XDG_DATA_HOME)
Windows: %APPDATA%/StarPanel/

This directory is never included in releases — user data stays local.
"""

import os
import sys
from pathlib import Path


def data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        path = Path(base) / "StarPanel"
    else:
        base = os.environ.get(
            "XDG_DATA_HOME",
            os.path.join(os.path.expanduser("~"), ".local", "share")
        )
        path = Path(base) / "starpanel"

    path.mkdir(parents=True, exist_ok=True)
    return path


def data_file(filename: str) -> Path:
    return data_dir() / filename
