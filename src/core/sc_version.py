"""
Star Citizen version tracker.

Sources:
  PTU STATUS / LIVE STATUS — RSI Knowledge Base PTU FAQ page
  (contains "PTU STATUS: X.Y" and "LIVE STATUS: X.Y" at the top,
   maintained directly by CIG)

  Fallback for Live — UEX home page header
"""

import re
import urllib.request
import urllib.error
from PyQt6.QtCore import QThread, pyqtSignal

RSI_PTU_FAQ_URL = (
    "https://support.robertsspaceindustries.com/hc/en-us/articles/"
    "115013195927-Public-Test-Universe-PTU-FAQ"
)
RSI_PTU_INSTALL_URL = (
    "https://support.robertsspaceindustries.com/hc/en-us/articles/"
    "360000668488-Install-the-Star-Citizen-PTU"
)
UEX_HOME_URL = "https://uexcorp.space/"
TIMEOUT = 10


def _get_text(url: str) -> tuple[str, str]:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace"), ""
    except urllib.error.HTTPError as e:
        return "", f"HTTP {e.code}"
    except Exception as e:
        return "", str(e)


def _extract(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


class SCVersionChecker(QThread):
    versions_ready = pyqtSignal(dict)
    check_failed   = pyqtSignal(str)

    def run(self):
        result = {"live": "", "ptu": "", "eptu": "", "tech_preview": ""}

        # ── Source 1: RSI PTU FAQ page ─────────────────────────────
        # Page header always contains:
        #   "PTU STATUS: 4.8 - Wave 1"
        #   "LIVE STATUS: 4.7"
        for url in [RSI_PTU_FAQ_URL, RSI_PTU_INSTALL_URL]:
            text, err = _get_text(url)
            if err:
                print(f"[SCVersion] {url} failed: {err}")
                continue

            print(f"[SCVersion] RSI page fetched ({len(text)} chars)")

            # Extract PTU status — e.g. "4.8 - Wave 1" or "4.8.0" or "Inactive"
            ptu_raw = _extract(
                text,
                r'PTU\s+STATUS\s*:\s*([^\n<]{1,30}?)(?:\s+LIVE|\s*[\n<]|$)'
            )
            live_raw = _extract(
                text,
                r'LIVE\s+STATUS\s*:\s*([\d]+\.[\d]+(?:\.[\d]+)?)'
            )

            print(f"[SCVersion] raw PTU='{ptu_raw}'  LIVE='{live_raw}'")

            if live_raw:
                # Extract just the version number e.g. "4.7" from "4.7" or "4.7.2"
                live_ver = _extract(live_raw, r'([\d]+\.[\d]+(?:\.[\d]+)?)')
                result["live"] = live_ver or live_raw.strip()

            if ptu_raw:
                ptu_lower = ptu_raw.lower()
                if "inactive" in ptu_lower or "closed" in ptu_lower or "n/a" in ptu_lower:
                    result["ptu"] = ""
                    print("[SCVersion] PTU is inactive")
                else:
                    ptu_ver = _extract(ptu_raw, r'([\d]+\.[\d]+(?:\.[\d]+)?)')
                    # Wave info: grab only "Wave N" or "All Waves" — stop at space+uppercase or end
                    wave = _extract(ptu_raw, r'[-–]\s*((?:All\s+Waves?|Wave\s+\d+|Evocati))')
                    if ptu_ver:
                        result["ptu"] = f"{ptu_ver}  {wave}".strip() if wave else ptu_ver
                    if "evocati" in ptu_lower:
                        result["eptu"] = result["ptu"]
                        result["ptu"]  = ""

            if any(result.values()):
                break  # got what we need

        # ── Fallback for Live: UEX header ──────────────────────────
        if not result["live"]:
            text, err = _get_text(UEX_HOME_URL)
            if not err and text:
                ver = _extract(text, r'Star\s+Citizen\s+([\d]+\.[\d]+(?:\.[\d]+)?)')
                if ver:
                    result["live"] = ver
                    print(f"[SCVersion] Live fallback from UEX: {ver}")

        print(f"[SCVersion] Final: {result}")

        if any(result.values()):
            self.versions_ready.emit(result)
        else:
            self.check_failed.emit("Could not fetch SC version data")
