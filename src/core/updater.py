"""
StarPanel update checker and auto-updater.
Runs in a background QThread on startup.
Compares current version against the latest GitHub Release tag.
If newer, offers to download and install automatically.
"""

import json
import os
import sys
import shutil
import tempfile
import zipfile
import urllib.request
import urllib.error
from PyQt6.QtCore import QThread, pyqtSignal
from core.version import APP_VERSION, RELEASES_URL, RELEASES_PAGE, GITHUB_OWNER, GITHUB_REPO


def _parse_version(tag: str):
    """Parse 'v1.2.3' or '1.2.3' → (1, 2, 3). Returns None if unparseable."""
    try:
        cleaned = tag.lstrip("vV").strip()
        parts = [int(x) for x in cleaned.split(".")]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)
    except Exception:
        return None


class UpdateChecker(QThread):
    """Checks GitHub for a newer release. Emits signals for the UI."""
    update_available = pyqtSignal(str, str, str, str)  # (version, url, notes, asset_url)
    up_to_date       = pyqtSignal()
    check_failed     = pyqtSignal(str)

    def run(self):
        print(f"[Updater] Checking: {RELEASES_URL}")
        try:
            req = urllib.request.Request(
                RELEASES_URL,
                headers={
                    "User-Agent": "StarPanel-UpdateChecker/1.0",
                    "Accept":     "application/vnd.github+json",
                }
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())

            tag        = data.get("tag_name", "")
            html_url   = data.get("html_url", RELEASES_PAGE)
            body       = data.get("body", "")
            prerelease = data.get("prerelease", False)
            draft      = data.get("draft", False)
            print(f"[Updater] tag={tag!r}  prerelease={prerelease}  draft={draft}")

            if prerelease or draft:
                print("[Updater] Skipping pre-release / draft")
                self.up_to_date.emit()
                return

            if not tag:
                print("[Updater] No tag found")
                self.up_to_date.emit()
                return

            latest  = _parse_version(tag)
            current = _parse_version(APP_VERSION)
            print(f"[Updater] local={current}  remote={latest}")

            if latest is None:
                print(f"[Updater] Could not parse remote tag: {tag!r}")
                self.check_failed.emit(
                    f"Release tag '{tag}' is not a version number (expected e.g. v1.0.0)")
                return

            if current is None:
                print(f"[Updater] Could not parse local version: {APP_VERSION!r}")
                self.up_to_date.emit()
                return

            if latest > current:
                # 1. Look for an explicitly uploaded .zip asset
                asset_url = ""
                assets = data.get("assets", [])
                print(f"[Updater] Release assets: {[a.get('name') for a in assets]}")
                for asset in assets:
                    name = asset.get("name", "")
                    if name.endswith(".zip"):
                        asset_url = asset.get("browser_download_url", "")
                        print(f"[Updater] Found zip asset: {asset_url}")
                        break

                # 2. Fall back to GitHub's auto-generated source zip
                if not asset_url:
                    asset_url = data.get("zipball_url", "")
                    if asset_url:
                        print(f"[Updater] Using source zipball: {asset_url}")
                    else:
                        print("[Updater] No zip found at all — will open release page")

                self.update_available.emit(
                    tag.lstrip("vV"), html_url, body, asset_url)
            else:
                print(f"[Updater] Up to date ({APP_VERSION} >= {tag})")
                self.up_to_date.emit()

        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode()).get("message", str(e))
            except Exception:
                msg = str(e)
            print(f"[Updater] HTTP {e.code}: {msg}")
            self.check_failed.emit(f"HTTP {e.code}: {msg}")
        except urllib.error.URLError as e:
            print(f"[Updater] URLError: {e.reason}")
            self.check_failed.emit(f"Network error: {e.reason}")
        except Exception as e:
            print(f"[Updater] Exception: {e}")
            self.check_failed.emit(str(e))


class AppUpdater(QThread):
    """
    Downloads and installs an update in the background.
    Replaces src/ files in-place, then signals the UI to relaunch.
    """
    progress    = pyqtSignal(str)   # status message
    finished_ok = pyqtSignal()      # ready to relaunch
    failed      = pyqtSignal(str)   # error message

    def __init__(self, asset_url: str, parent=None):
        super().__init__(parent)
        self._asset_url = asset_url

    def run(self):
        # Locate the src/ directory relative to this file
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        try:
            # ── Download ──────────────────────────────────────────
            self.progress.emit("Downloading update…")
            print(f"[Updater] Downloading: {self._asset_url}")

            tmp_zip = os.path.join(tempfile.gettempdir(), "starpanel_update.zip")
            urllib.request.urlretrieve(self._asset_url, tmp_zip)
            print(f"[Updater] Downloaded to: {tmp_zip}")

            # ── Extract src/ from zip ─────────────────────────────
            self.progress.emit("Extracting files…")
            tmp_dir = tempfile.mkdtemp(prefix="starpanel_update_")

            with zipfile.ZipFile(tmp_zip, "r") as zf:
                members = zf.namelist()
                print(f"[Updater] Zip top-level entries: {members[:6]}")
                zf.extractall(tmp_dir)

            # Find extracted src/ directory — works for both:
            #   - Our release zip:   src/main.py
            #   - GitHub source zip: StarPanel-abc123/src/main.py
            extracted_src = None
            for root, dirs, files in os.walk(tmp_dir):
                if os.path.basename(root) == "src" and "main.py" in files:
                    extracted_src = root
                    break

            if not extracted_src:
                raise RuntimeError("Could not find src/main.py in downloaded zip")

            print(f"[Updater] Found extracted src: {extracted_src}")

            # ── Back up current src/ ──────────────────────────────
            self.progress.emit("Backing up current version…")
            backup_dir = src_dir + "_backup"
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            shutil.copytree(src_dir, backup_dir)
            print(f"[Updater] Backed up to: {backup_dir}")

            # ── Replace src/ files ────────────────────────────────
            self.progress.emit("Installing update…")
            # Copy new files over existing ones
            for item in os.listdir(extracted_src):
                src_path  = os.path.join(extracted_src, item)
                dest_path = os.path.join(src_dir, item)
                if os.path.isdir(src_path):
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.copytree(src_path, dest_path)
                else:
                    shutil.copy2(src_path, dest_path)

            print("[Updater] Files replaced successfully")

            # ── Clean up ──────────────────────────────────────────
            shutil.rmtree(tmp_dir, ignore_errors=True)
            os.remove(tmp_zip)

            self.progress.emit("Update installed — restarting…")
            self.finished_ok.emit()

        except Exception as e:
            print(f"[Updater] Install failed: {e}")
            # Attempt to restore backup
            if os.path.exists(backup_dir):
                try:
                    shutil.rmtree(src_dir)
                    shutil.copytree(backup_dir, src_dir)
                    print("[Updater] Restored from backup")
                except Exception as re:
                    print(f"[Updater] Restore also failed: {re}")
            self.failed.emit(str(e))


def relaunch():
    """Replace the current process with a fresh instance of StarPanel."""
    print("[Updater] Relaunching…")
    os.execv(sys.executable, [sys.executable] + sys.argv)
