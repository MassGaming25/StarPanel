"""
SC Companion API client.

Ship data sources (in priority order):
  1. Fleetyards API     — api.fleetyards.net/v1/models  (no key, paginated)
  2. RSI Ship Matrix    — robertsspaceindustries.com/ship-matrix/index  (POST, no key)
  3. Static fallback    — built-in data.py list

Commodity/trade data:
  UEX Corp API          — uexcorp.space/api/2.0

All network calls run in a background QThread — the UI never blocks.
User status overrides (core.overrides) always take final priority.
"""

import json
import urllib.request
import urllib.error
from PyQt6.QtCore import QThread, pyqtSignal

# ── Endpoints ─────────────────────────────────────────────────────────────────
FLEETYARDS_BASE = "https://api.fleetyards.net/v1"
RSI_SHIPMATRIX  = "https://robertsspaceindustries.com/ship-matrix/index"
UEX_BASE        = "https://uexcorp.space/api/2.0"
TIMEOUT         = 8


# ── Low-level HTTP helpers ────────────────────────────────────────────────────

def _get(url: str) -> tuple[any, str]:
    """GET url → (parsed_json_or_list, error_str). Never raises."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SC-Companion/1.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode()), ""
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {url}"
    except urllib.error.URLError as e:
        return None, f"URLError: {e.reason}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _post(url: str, payload: dict) -> tuple[any, str]:
    """POST url with JSON payload → (parsed_json, error_str). Never raises."""
    try:
        body = json.dumps(payload).encode()
        req  = urllib.request.Request(
            url, data=body,
            headers={
                "User-Agent":   "SC-Companion/1.0",
                "Accept":       "application/json",
                "Content-Type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode()), ""
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {url}"
    except urllib.error.URLError as e:
        return None, f"URLError: {e.reason}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


# ── Type helpers ──────────────────────────────────────────────────────────────

def _int(val, default=0) -> int:
    try:
        return int(float(str(val).replace(",", ".")))
    except (ValueError, TypeError):
        return default

def _float(val, default=0.0) -> float:
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return default

def _str(val, default="Unknown") -> str:
    v = str(val).strip() if val else ""
    return v if v and v.lower() not in ("none", "null", "") else default


# ── Status resolution ─────────────────────────────────────────────────────────
# Fleetyards uses: "flight-ready", "in-concept", "in-production"
# RSI uses:        "Flight Ready", "In Concept", "In Production"
# We normalise to: "Flight Ready", "In Concept", "In Concept"

def _resolve_status(name: str, raw_status: str) -> str:
    """
    Priority: user overrides (checked in caller) → this function.
    Handles Fleetyards, RSI, and UEX status strings.
    """
    from core.overrides import load_overrides
    user = load_overrides().get(name.lower().strip())
    if user:
        return user

    s = str(raw_status).lower().replace("-", " ").replace("_", " ")
    if "concept" in s:
        return "In Concept"
    if any(k in s for k in ("production", "shipyard", "wip", "development", "long term")):
        return "In Concept"
    if "flight" in s or "ready" in s:
        return "Flight Ready"
    # Default: if it has no status at all, assume flight ready
    return "Flight Ready"


# ── Fleetyards normalisers ────────────────────────────────────────────────────

def _normalise_fleetyards(raw: dict) -> dict:
    """Map Fleetyards /v1/models item → internal schema."""
    name = _str(raw.get("name"))

    # Fleetyards manufacturer is nested: {"name": "...", "slug": "..."}
    mfr_obj = raw.get("manufacturer") or {}
    if isinstance(mfr_obj, dict):
        mfr = _str(mfr_obj.get("name"))
    else:
        mfr = _str(mfr_obj)

    # Fleetyards status field
    status_raw = _str(raw.get("productionStatus", raw.get("status", "")), default="")
    status = _resolve_status(name, status_raw)

    # Fleetyards size is lowercase e.g. "small"
    size_raw = _str(raw.get("size", raw.get("sizeLabel", "")), default="Unknown")
    size = size_raw.capitalize()

    # Store image URL from Fleetyards
    image_url = _str(raw.get("storeImage", raw.get("store_image", "")), default="")

    return {
        "id":           raw.get("id", 0),
        "name":         name,
        "manufacturer": mfr,
        "role":         _str(raw.get("focus", raw.get("classification", raw.get("role", "")))),
        "size":         size,
        "crew":         _int(raw.get("maxCrew", raw.get("minCrew", 1)), default=1),
        "cargo":        _int(raw.get("cargo", 0), default=0),
        "price_uec":    _int(raw.get("pledgePrice", raw.get("price", 0)), default=0),
        "status":       status,
        "image_url":    image_url,
        "source":       "fleetyards",
    }


# ── RSI Ship Matrix normalisers ───────────────────────────────────────────────

def _normalise_rsi(raw: dict) -> dict:
    """Map RSI Ship Matrix item → internal schema."""
    name = _str(raw.get("name"))

    mfr_obj = raw.get("manufacturer") or {}
    if isinstance(mfr_obj, dict):
        mfr = _str(mfr_obj.get("name", mfr_obj.get("code", "")))
    else:
        mfr = _str(mfr_obj)

    status_raw = _str(raw.get("production_status", raw.get("status", "")), default="")
    status = _resolve_status(name, status_raw)

    # RSI media array: [{"source_url": "...", ...}, ...]
    image_url = ""
    media = raw.get("media", [])
    if isinstance(media, list) and media:
        first = media[0]
        if isinstance(first, dict):
            imgs = first.get("images", {})
            image_url = (
                imgs.get("product_thumb_large", "")
                or imgs.get("store_hub_large", "")
                or first.get("source_url", "")
            )

    return {
        "id":           raw.get("id", 0),
        "name":         name,
        "manufacturer": mfr,
        "role":         _str(raw.get("focus", raw.get("type", ""))),
        "size":         _str(raw.get("size", "")).capitalize(),
        "crew":         _int(raw.get("max_crew", raw.get("min_crew", 1)), default=1),
        "cargo":        _int(raw.get("cargocapacity", raw.get("cargo", 0)), default=0),
        "price_uec":    _int(raw.get("price", 0), default=0),
        "status":       status,
        "image_url":    image_url,
        "source":       "rsi",
    }


# ── UEX commodity normalisers ─────────────────────────────────────────────────

def _normalise_commodity(raw: dict) -> dict:
    return {
        "id":             raw.get("id", 0),
        "name":           _str(raw.get("name")),
        "category":       _str(raw.get("kind", raw.get("category", "Other"))),
        "price_buy":      _float(raw.get("price_buy",  raw.get("buy",  0))),
        "price_sell":     _float(raw.get("price_sell", raw.get("sell", 0))),
        "buy_locations":  [],
        "sell_locations": [],
    }


# ── Ship fetching functions ────────────────────────────────────────────────────

def fetch_ships_fleetyards(log) -> list | None:
    """
    Fetch all ships from Fleetyards, handling pagination.
    Returns normalised list or None on failure.
    """
    ships = []
    page  = 1
    while True:
        url = f"{FLEETYARDS_BASE}/models?perPage=200&page={page}"
        data, err = _get(url)
        if err:
            log(f"[fleetyards/page{page}] {err}")
            return None if not ships else ships
        if not data:
            break
        # Fleetyards returns a plain array
        items = data if isinstance(data, list) else data.get("data", [])
        if not items:
            break
        ships.extend([_normalise_fleetyards(s) for s in items])
        log(f"[fleetyards/page{page}] got {len(items)} ships (total so far: {len(ships)})")
        # If we got fewer than 200, we're on the last page
        if len(items) < 200:
            break
        page += 1
    return ships if ships else None


def fetch_ships_rsi(log) -> list | None:
    """
    Fetch ships from RSI Ship Matrix via POST.
    Returns normalised list or None on failure.
    """
    data, err = _post(RSI_SHIPMATRIX, {})
    if err:
        log(f"[rsi-shipmatrix] {err}")
        return None
    if not data:
        return None

    # RSI returns {"success": 1, "data": [...]}
    items = data.get("data", []) if isinstance(data, dict) else data
    if not items:
        log("[rsi-shipmatrix] empty response")
        return None

    ships = [_normalise_rsi(s) for s in items]
    log(f"[rsi-shipmatrix] got {len(ships)} ships")
    return ships


# ── Terminal/location normalisers ─────────────────────────────────────────────

def _normalise_terminals(items: list) -> list:
    """
    Convert UEX terminal list to our location schema.
    Deduplicates by location name — multiple terminals at the same
    location (e.g. a trade kiosk and a refinery) become one entry.
    UEX terminal fields: name, star_system_name, planet_name,
                         moon_name, space_station_name, type, mcs
    """
    seen = {}
    counter = 1

    for raw in items:
        # Build a clean location name from the most specific field
        name = (
            _str(raw.get("name"), default="")
            or _str(raw.get("space_station_name"), default="")
            or _str(raw.get("outpost_name"), default="")
        )
        if not name or name.lower() in ("unknown", "none", "null", ""):
            continue

        # Deduplicate — same name = same location
        key = name.lower().strip()
        if key in seen:
            continue

        system = _str(raw.get("star_system_name", "Stanton"), default="Stanton")
        # Body: prefer moon > planet > space station
        body = (
            _str(raw.get("moon_name"), default="")
            or _str(raw.get("planet_name"), default="")
            or _str(raw.get("space_station_name"), default="")
            or system
        )

        # Map UEX terminal type to our type labels
        raw_type = _str(raw.get("mcs", raw.get("type", "")), default="").lower()
        if "city" in raw_type or "landing zone" in raw_type:
            loc_type = "City"
        elif "station" in raw_type or "orbital" in raw_type:
            loc_type = "Station"
        elif "outpost" in raw_type:
            loc_type = "Outpost"
        elif "asteroid" in raw_type:
            loc_type = "Asteroid"
        elif "trade" in raw_type or "tdd" in raw_type:
            loc_type = "Trade"
        else:
            loc_type = "Outpost"

        seen[key] = {
            "id":     counter,
            "name":   name,
            "body":   body,
            "system": system,
            "type":   loc_type,
        }
        counter += 1

    return list(seen.values())


# ── Worker thread ─────────────────────────────────────────────────────────────

class ApiWorker(QThread):
    ships_ready       = pyqtSignal(list)
    commodities_ready = pyqtSignal(list)
    prices_ready      = pyqtSignal(list)
    locations_ready   = pyqtSignal(list)
    status_update     = pyqtSignal(str)
    finished_all      = pyqtSignal(bool)
    log_line          = pyqtSignal(str)

    def run(self):
        any_success = False

        # ── Ships: try Fleetyards first, then RSI ──────────────────
        self.status_update.emit("Fetching ships from Fleetyards…")
        ships = fetch_ships_fleetyards(self.log_line.emit)

        if ships:
            from core.overrides import apply_overrides
            ships = apply_overrides(ships)
            self.log_line.emit(f"[ships] Fleetyards OK: {len(ships)} ships")
            self.ships_ready.emit(ships)
            self.status_update.emit(f"Ships: {len(ships)} loaded from Fleetyards")
            any_success = True
        else:
            self.log_line.emit("[ships] Fleetyards failed — trying RSI Ship Matrix…")
            self.status_update.emit("Fleetyards unavailable, trying RSI Ship Matrix…")
            ships = fetch_ships_rsi(self.log_line.emit)

            if ships:
                from core.overrides import apply_overrides
                ships = apply_overrides(ships)
                self.log_line.emit(f"[ships] RSI OK: {len(ships)} ships")
                self.ships_ready.emit(ships)
                self.status_update.emit(f"Ships: {len(ships)} loaded from RSI Ship Matrix")
                any_success = True
            else:
                self.log_line.emit("[ships] Both sources failed — using static data")
                self.status_update.emit("Ship sources unavailable — using static data")

        # ── Commodities: UEX ───────────────────────────────────────
        self.status_update.emit("Fetching commodities from UEX…")
        data, err = _get(f"{UEX_BASE}/commodities")
        if err:
            self.log_line.emit(f"[commodities] {err}")
        elif data:
            items = data.get("data", [])
            self.log_line.emit(f"[commodities] got {len(items)} items, status={data.get('status')}")
            if items:
                comms = [_normalise_commodity(c) for c in items]
                self.commodities_ready.emit(comms)
                any_success = True
                self.status_update.emit(f"Commodities: {len(comms)} loaded from UEX")

        # ── Locations: UEX terminals ───────────────────────────────
        self.status_update.emit("Fetching locations from UEX…")
        data, err = _get(f"{UEX_BASE}/terminals")
        if err:
            self.log_line.emit(f"[terminals] {err}")
        elif data:
            items = data.get("data", [])
            self.log_line.emit(f"[terminals] got {len(items)} items, status={data.get('status')}")
            if items:
                locations = _normalise_terminals(items)
                if locations:
                    self.locations_ready.emit(locations)
                    any_success = True
                    self.status_update.emit(f"Locations: {len(locations)} loaded from UEX")

        # ── Trade prices: UEX ──────────────────────────────────────
        # commodities_prices requires query params (returns 400 without them)
        # commodities_prices_all returns everything — use that directly
        for ep in ["commodities_prices_all", "trade_routes"]:
            self.status_update.emit(f"Fetching prices ({ep})…")
            data, err = _get(f"{UEX_BASE}/{ep}")
            if err:
                self.log_line.emit(f"[prices/{ep}] {err}")
                continue
            if data:
                items = data.get("data", [])
                self.log_line.emit(f"[prices/{ep}] got {len(items)} items")
                if items:
                    self.prices_ready.emit(items)
                    any_success = True
                    self.status_update.emit(f"Prices: {len(items)} entries loaded")
                    break

        # ── Done ───────────────────────────────────────────────────
        self.finished_all.emit(any_success)
        self.status_update.emit(
            "Live data loaded" if any_success else "API unavailable — using static data"
        )
