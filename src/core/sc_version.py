"""
Star Citizen version tracker.

Sources:
  Live version  — UEX home page header (reliable, fast)
  PTU/EPTU      — RSI Spectrum PTU patch notes RSS feed
                  (official CIG posts containing exact version strings)
"""

import re
import urllib.request
import urllib.error
from PyQt6.QtCore import QThread, pyqtSignal

UEX_HOME_URL     = "https://uexcorp.space/"
RSI_PTU_RSS_URL  = "https://robertsspaceindustries.com/spectrum/community/SC/forum/190048.rss"
TIMEOUT = 8


def _get_text(url: str) -> tuple[str, str]:
    try:
        req = urllib.request.Request(
            url, headers={
                "User-Agent": "StarPanel/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml,*/*"
            })
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

        # ── Live version from UEX header ───────────────────────────
        # UEX displays "Star Citizen X.Y.Z" in their page header
        text, err = _get_text(UEX_HOME_URL)
        if not err and text:
            ver = _extract(text, r'Star\s+Citizen\s+([\d]+\.[\d]+(?:\.[\d]+)?)')
            if ver:
                result["live"] = ver
                print(f"[SCVersion] Live from UEX header: {ver}")
        else:
            print(f"[SCVersion] UEX failed: {err}")

        # ── PTU / EPTU from RSI Spectrum RSS ───────────────────────
        # CIG posts patch notes to Spectrum. The RSS feed titles contain
        # exact strings like "4.8.0-PTU.11759767" and "4.8.0-EPTU.XXXXXXX"
        # Evocati posts say "Evocati" in the title and have EPTU build strings
        text, err = _get_text(RSI_PTU_RSS_URL)
        if not err and text:
            print(f"[SCVersion] RSS feed fetched ({len(text)} chars)")

            # Find all version strings in the feed
            # Pattern: X.Y.Z-PTU.NNNNNNN  or  X.Y.Z-EPTU.NNNNNNN
            ptu_matches  = re.findall(
                r'([\d]+\.[\d]+\.[\d]+-PTU\.[\d]+)', text, re.IGNORECASE)
            eptu_matches = re.findall(
                r'([\d]+\.[\d]+\.[\d]+-(?:EPTU|PTU)\.[\d]+).*?[Ee]vocati', text)

            # Also look for Evocati posts — their titles mention Evocati
            # and contain PTU build strings (CIG uses -PTU. even for Evocati)
            evocati_section = re.findall(
                r'[Ee]vocati[^\n<]{0,200}([\d]+\.[\d]+\.[\d]+-(?:EPTU|PTU)\.[\d]+)',
                text)

            if evocati_section:
                result["eptu"] = evocati_section[0]
                print(f"[SCVersion] EPTU/Evocati: {result['eptu']}")

            if ptu_matches:
                # Latest PTU build is the first match (RSS is newest-first)
                latest_ptu = ptu_matches[0]
                # Only set as PTU if not already identified as Evocati
                if latest_ptu != result.get("eptu"):
                    result["ptu"] = latest_ptu
                    print(f"[SCVersion] PTU: {result['ptu']}")

            # If only one type found and it mentions Evocati, mark accordingly
            if result["ptu"] and not result["eptu"]:
                # Check if the PTU entries are all Evocati audience
                if re.search(r'[Ee]vocati', text[:2000]):
                    result["eptu"] = result["ptu"]
                    result["ptu"]  = ""
                    print(f"[SCVersion] Reclassified as Evocati: {result['eptu']}")
        else:
            print(f"[SCVersion] RSS failed: {err}")

        # Emit whatever we have — even partial is useful
        if any(result.values()):
            self.versions_ready.emit(result)
        else:
            self.check_failed.emit("Could not fetch SC version data")
