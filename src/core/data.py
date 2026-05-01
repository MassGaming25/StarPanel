"""
Star Citizen data layer.

Static fallback data is always available immediately.
When the UEX API worker completes, it calls update_ships() /
update_commodities() / update_prices() to replace the live cache.
All UI code reads from get_ships() / get_commodities() so it always
gets the freshest available data without needing to know the source.
"""

# ── Static fallback ships ─────────────────────────────────────────────────────
_STATIC_SHIPS = [
    {"id": 1,  "name": "Aurora MR",              "manufacturer": "RSI",      "role": "Starter",       "size": "Small",   "crew": 1,  "cargo": 2,    "price_uec": 743000,   "status": "Flight Ready"},
    {"id": 2,  "name": "Avenger Titan",           "manufacturer": "Aegis",    "role": "Multirole",     "size": "Small",   "crew": 1,  "cargo": 8,    "price_uec": 954250,   "status": "Flight Ready"},
    {"id": 3,  "name": "Constellation Andromeda", "manufacturer": "RSI",      "role": "Multirole",     "size": "Large",   "crew": 4,  "cargo": 96,   "price_uec": 5765750,  "status": "Flight Ready"},
    {"id": 4,  "name": "Caterpillar",             "manufacturer": "Drake",    "role": "Freighter",     "size": "Large",   "crew": 5,  "cargo": 576,  "price_uec": 5765750,  "status": "Flight Ready"},
    {"id": 5,  "name": "Cutlass Black",           "manufacturer": "Drake",    "role": "Multirole",     "size": "Medium",  "crew": 2,  "cargo": 46,   "price_uec": 1636125,  "status": "Flight Ready"},
    {"id": 6,  "name": "Freelancer",              "manufacturer": "MISC",     "role": "Freighter",     "size": "Medium",  "crew": 2,  "cargo": 66,   "price_uec": 2089500,  "status": "Flight Ready"},
    {"id": 7,  "name": "Gladius",                 "manufacturer": "Aegis",    "role": "Fighter",       "size": "Small",   "crew": 1,  "cargo": 0,    "price_uec": 1060500,  "status": "Flight Ready"},
    {"id": 8,  "name": "Hammerhead",              "manufacturer": "Aegis",    "role": "Gunship",       "size": "Capital", "crew": 9,  "cargo": 0,    "price_uec": 22000000, "status": "Flight Ready"},
    {"id": 9,  "name": "Hercules C2",             "manufacturer": "Crusader", "role": "Heavy Lifter",  "size": "Capital", "crew": 2,  "cargo": 696,  "price_uec": 5290500,  "status": "Flight Ready"},
    {"id": 10, "name": "Hull C",                  "manufacturer": "MISC",     "role": "Freighter",     "size": "Capital", "crew": 3,  "cargo": 4608, "price_uec": 6567750,  "status": "Flight Ready"},
    {"id": 11, "name": "Mantis",                  "manufacturer": "RSI",      "role": "Interdiction",  "size": "Small",   "crew": 1,  "cargo": 0,    "price_uec": 2090000,  "status": "Flight Ready"},
    {"id": 12, "name": "Mercury Star Runner",     "manufacturer": "MISC",     "role": "Courier",       "size": "Medium",  "crew": 3,  "cargo": 114,  "price_uec": 4610250,  "status": "Flight Ready"},
    {"id": 13, "name": "Nomad",                   "manufacturer": "Crusader", "role": "Starter",       "size": "Small",   "crew": 1,  "cargo": 24,   "price_uec": 1326375,  "status": "Flight Ready"},
    {"id": 14, "name": "Origin 300i",             "manufacturer": "Origin",   "role": "Luxury",        "size": "Small",   "crew": 1,  "cargo": 2,    "price_uec": 1235250,  "status": "Flight Ready"},
    {"id": 15, "name": "Prospector",              "manufacturer": "MISC",     "role": "Mining",        "size": "Small",   "crew": 1,  "cargo": 32,   "price_uec": 2061000,  "status": "Flight Ready"},
    {"id": 16, "name": "Reclaimer",               "manufacturer": "Aegis",    "role": "Salvage",       "size": "Capital", "crew": 5,  "cargo": 256,  "price_uec": 16428375, "status": "Flight Ready"},
    {"id": 17, "name": "Valkyrie",                "manufacturer": "Anvil",    "role": "Dropship",      "size": "Large",   "crew": 5,  "cargo": 27,   "price_uec": 4461750,  "status": "Flight Ready"},
    {"id": 18, "name": "Vulture",                 "manufacturer": "Drake",    "role": "Salvage",       "size": "Small",   "crew": 1,  "cargo": 12,   "price_uec": 1579500,  "status": "Flight Ready"},
    {"id": 19, "name": "Arrastra",                "manufacturer": "MISC",     "role": "Mining",        "size": "Capital", "crew": 6,  "cargo": 768,  "price_uec": 0,        "status": "In Concept"},
    {"id": 20, "name": "Genesis Starliner",       "manufacturer": "Crusader", "role": "Passenger",     "size": "Capital", "crew": 4,  "cargo": 0,    "price_uec": 0,        "status": "In Shipyard"},
    {"id": 21, "name": "Kraken",                  "manufacturer": "Drake",    "role": "Carrier",       "size": "Capital", "crew": 10, "cargo": 2016, "price_uec": 0,        "status": "In Shipyard"},
    {"id": 22, "name": "Liberator",               "manufacturer": "Anvil",    "role": "Carrier",       "size": "Capital", "crew": 4,  "cargo": 0,    "price_uec": 0,        "status": "In Shipyard"},
    {"id": 23, "name": "Odyssey",                 "manufacturer": "MISC",     "role": "Explorer",      "size": "Capital", "crew": 6,  "cargo": 200,  "price_uec": 0,        "status": "In Concept"},
    {"id": 24, "name": "Orion",                   "manufacturer": "RSI",      "role": "Mining",        "size": "Capital", "crew": 4,  "cargo": 0,    "price_uec": 0,        "status": "In Shipyard"},
    {"id": 25, "name": "Pioneer",                 "manufacturer": "MISC",     "role": "Construction",  "size": "Capital", "crew": 4,  "cargo": 0,    "price_uec": 0,        "status": "In Concept"},
    {"id": 26, "name": "Polaris",                 "manufacturer": "RSI",      "role": "Corvette",      "size": "Capital", "crew": 14, "cargo": 216,  "price_uec": 0,        "status": "In Shipyard"},
]

# Static trade locations (UEX doesn't always expose these cleanly)
LOCATIONS = [
    {"id": 1,  "name": "Area18",             "body": "ArcCorp",   "system": "Stanton", "type": "City"},
    {"id": 2,  "name": "Baijini Point",      "body": "ArcCorp",   "system": "Stanton", "type": "Station"},
    {"id": 3,  "name": "Benson Mining",      "body": "Yela",      "system": "Stanton", "type": "Outpost"},
    {"id": 4,  "name": "Bezdek",             "body": "Aberdeen",  "system": "Stanton", "type": "Outpost"},
    {"id": 5,  "name": "Checkmate",          "body": "Daymar",    "system": "Stanton", "type": "Outpost"},
    {"id": 6,  "name": "Covalex Hub",        "body": "Microtech", "system": "Stanton", "type": "Station"},
    {"id": 7,  "name": "CRU-L1",             "body": "Crusader",  "system": "Stanton", "type": "Station"},
    {"id": 8,  "name": "CRU-L5",             "body": "Crusader",  "system": "Stanton", "type": "Station"},
    {"id": 9,  "name": "GrimHex",            "body": "Yela",      "system": "Stanton", "type": "Outpost"},
    {"id": 10, "name": "HUR-L1",             "body": "Hurston",   "system": "Stanton", "type": "Station"},
    {"id": 11, "name": "HUR-L2",             "body": "Hurston",   "system": "Stanton", "type": "Station"},
    {"id": 12, "name": "Levski",             "body": "Delamar",   "system": "Stanton", "type": "Outpost"},
    {"id": 13, "name": "Lorville",           "body": "Hurston",   "system": "Stanton", "type": "City"},
    {"id": 14, "name": "MIC-L1",             "body": "Microtech", "system": "Stanton", "type": "Station"},
    {"id": 15, "name": "MIC-L2",             "body": "Microtech", "system": "Stanton", "type": "Station"},
    {"id": 16, "name": "New Babbage",        "body": "Microtech", "system": "Stanton", "type": "City"},
    {"id": 17, "name": "Orison",             "body": "Crusader",  "system": "Stanton", "type": "City"},
    {"id": 18, "name": "Seraphim Station",   "body": "Crusader",  "system": "Stanton", "type": "Station"},
    {"id": 19, "name": "Port Tressler",      "body": "Microtech", "system": "Stanton", "type": "Station"},
    {"id": 20, "name": "Reclamation & Div.", "body": "Hurston",   "system": "Stanton", "type": "Outpost"},
    {"id": 21, "name": "Shubin SMO-10",      "body": "Microtech", "system": "Stanton", "type": "Outpost"},
    {"id": 22, "name": "Shubin SMO-18",      "body": "Microtech", "system": "Stanton", "type": "Outpost"},
    {"id": 23, "name": "Shubin SMO-22",      "body": "Microtech", "system": "Stanton", "type": "Outpost"},
    {"id": 24, "name": "TDD Area18",         "body": "ArcCorp",   "system": "Stanton", "type": "Trade"},
    {"id": 25, "name": "TDD Lorville",       "body": "Hurston",   "system": "Stanton", "type": "Trade"},
    {"id": 26, "name": "TDD New Babbage",    "body": "Microtech", "system": "Stanton", "type": "Trade"},
    {"id": 27, "name": "TDD Orison",         "body": "Crusader",  "system": "Stanton", "type": "Trade"},
    {"id": 28, "name": "Terra Mills",        "body": "Hurston",        "system": "Stanton", "type": "Outpost"},
    {"id": 29, "name": "Tram & Myers",       "body": "Ita",            "system": "Stanton", "type": "Outpost"},
    # ── Pyro system (added 4.0) ───────────────────────────────────────────────
    {"id": 30, "name": "Checkmate",          "body": "Pyro I",         "system": "Pyro",    "type": "Outpost"},
    {"id": 31, "name": "Gasping Reef",       "body": "Pyro I",         "system": "Pyro",    "type": "Outpost"},
    {"id": 32, "name": "Patch City",         "body": "Pyro I",         "system": "Pyro",    "type": "Outpost"},
    {"id": 33, "name": "Ruin Station",       "body": "Pyro I",         "system": "Pyro",    "type": "Station"},
    {"id": 34, "name": "Bloom",              "body": "Pyro II",        "system": "Pyro",    "type": "Outpost"},
    {"id": 35, "name": "The Necropolis",     "body": "Pyro II",        "system": "Pyro",    "type": "Outpost"},
    {"id": 36, "name": "Orbituary",          "body": "Pyro II",        "system": "Pyro",    "type": "Station"},
    {"id": 37, "name": "Fat Bottle",         "body": "Pyro III",       "system": "Pyro",    "type": "Outpost"},
    {"id": 38, "name": "Megafire",           "body": "Pyro III",       "system": "Pyro",    "type": "Outpost"},
    {"id": 39, "name": "Stash House",        "body": "Pyro III",       "system": "Pyro",    "type": "Outpost"},
    {"id": 40, "name": "Dudley & Daughters", "body": "Ignis",          "system": "Pyro",    "type": "Outpost"},
    {"id": 41, "name": "Nowhere",            "body": "Ignis",          "system": "Pyro",    "type": "Outpost"},
    {"id": 42, "name": "Pyrotechnic Amalgam","body": "Ignis",          "system": "Pyro",    "type": "Outpost"},
    {"id": 43, "name": "Rust & Bones",       "body": "Ignis",          "system": "Pyro",    "type": "Outpost"},
    {"id": 44, "name": "Starfire",           "body": "Ignis",          "system": "Pyro",    "type": "Outpost"},
    {"id": 45, "name": "Thistledown Station","body": "Pyro IV",        "system": "Pyro",    "type": "Station"},
    {"id": 46, "name": "Buried Treasure",    "body": "Pyro IV",        "system": "Pyro",    "type": "Outpost"},
    {"id": 47, "name": "Shady Glen Farms",   "body": "Vuur",           "system": "Pyro",    "type": "Outpost"},
    {"id": 48, "name": "Silk & Tin",         "body": "Vuur",           "system": "Pyro",    "type": "Outpost"},
    {"id": 49, "name": "Verdant Brink",      "body": "Vuur",           "system": "Pyro",    "type": "Outpost"},
    {"id": 50, "name": "Bolts & Scraps",     "body": "Pyro V",         "system": "Pyro",    "type": "Outpost"},
    {"id": 51, "name": "Saber's Tooth",      "body": "Pyro V",         "system": "Pyro",    "type": "Outpost"},
    {"id": 52, "name": "Terminal Velocity",  "body": "Pyro V",         "system": "Pyro",    "type": "Outpost"},
    {"id": 53, "name": "Cargo Hell",         "body": "Pyro VI",        "system": "Pyro",    "type": "Outpost"},
    {"id": 54, "name": "Checkered Flag",     "body": "Pyro VI",        "system": "Pyro",    "type": "Outpost"},
    {"id": 55, "name": "Roughneck",          "body": "Pyro VI",        "system": "Pyro",    "type": "Outpost"},
    {"id": 56, "name": "Rappel",             "body": "Pyro VI",        "system": "Pyro",    "type": "Outpost"},
    {"id": 57, "name": "PYR-L1",             "body": "Pyro",           "system": "Pyro",    "type": "Station"},
    {"id": 58, "name": "PYR-L2",             "body": "Pyro",           "system": "Pyro",    "type": "Station"},
    {"id": 59, "name": "PYR-L3",             "body": "Pyro",           "system": "Pyro",    "type": "Station"},
]

# Static fallback commodities (with location buy/sell data)
_STATIC_COMMODITIES = [
    {"id": 1,  "name": "Agricium",          "category": "Rare Metal",  "buy_locations": [(3,248),(9,255),(21,251)],    "sell_locations": [(13,263),(25,260),(16,258)]},
    {"id": 2,  "name": "Aluminum",          "category": "Metal",       "buy_locations": [(24,1.22),(25,1.20),(26,1.25),(27,1.23)], "sell_locations": [(10,1.38),(11,1.35),(14,1.33)]},
    {"id": 3,  "name": "Astatine",          "category": "Gas",         "buy_locations": [(9,210),(4,215)],             "sell_locations": [(1,225),(13,221),(16,219)]},
    {"id": 4,  "name": "Beryl",             "category": "Metal",       "buy_locations": [(22,375),(23,378),(21,372)],  "sell_locations": [(16,398),(19,395),(26,391)]},
    {"id": 5,  "name": "Bexalite",          "category": "Rare Metal",  "buy_locations": [(3,3950),(9,3970)],           "sell_locations": [(13,4110),(25,4095),(1,4080)]},
    {"id": 6,  "name": "Borase",            "category": "Metal",       "buy_locations": [(28,350),(20,353)],           "sell_locations": [(13,374),(25,371)]},
    {"id": 7,  "name": "Carbon",            "category": "Gas",         "buy_locations": [(24,1.40),(25,1.42),(26,1.38)], "sell_locations": [(7,1.62),(8,1.60),(10,1.58)]},
    {"id": 8,  "name": "Chlorine",          "category": "Gas",         "buy_locations": [(24,2.50),(25,2.52)],         "sell_locations": [(8,2.78),(18,2.75),(7,2.72)]},
    {"id": 9,  "name": "Corundum",          "category": "Metal",       "buy_locations": [(3,148),(5,150),(9,152)],     "sell_locations": [(13,163),(25,161),(1,159)]},
    {"id": 10, "name": "Diamond",           "category": "Gem",         "buy_locations": [(9,6850),(12,6920)],          "sell_locations": [(1,7250),(16,7210),(13,7180)]},
    {"id": 11, "name": "Distilled Spirits", "category": "Consumable",  "buy_locations": [(12,4.10),(9,4.15)],          "sell_locations": [(1,4.55),(17,4.52),(13,4.48)]},
    {"id": 12, "name": "Fluorine",          "category": "Gas",         "buy_locations": [(24,2.85),(27,2.88)],         "sell_locations": [(8,3.12),(7,3.10),(18,3.08)]},
    {"id": 13, "name": "Gold",              "category": "Rare Metal",  "buy_locations": [(20,5050),(28,5080),(9,5100)], "sell_locations": [(1,5330),(16,5315),(17,5300)]},
    {"id": 14, "name": "Hephaestanite",     "category": "Metal",       "buy_locations": [(21,390),(22,393),(23,395)],  "sell_locations": [(16,416),(19,413),(26,410)]},
    {"id": 15, "name": "Hydrogen",          "category": "Gas",         "buy_locations": [(24,0.48),(25,0.48),(26,0.50),(27,0.49)], "sell_locations": [(7,0.67),(8,0.66),(18,0.65)]},
    {"id": 16, "name": "Iodine",            "category": "Gas",         "buy_locations": [(24,2.10),(26,2.12)],         "sell_locations": [(10,2.32),(11,2.30),(14,2.28)]},
    {"id": 17, "name": "Laranite",          "category": "Rare Metal",  "buy_locations": [(9,3480),(12,3500)],          "sell_locations": [(1,3665),(16,3650),(13,3635)]},
    {"id": 18, "name": "Maze",              "category": "Drug",        "buy_locations": [(9,115),(12,118)],            "sell_locations": [(12,132),(9,129)]},
    {"id": 19, "name": "Medical Supplies",  "category": "Medical",     "buy_locations": [(24,24.0),(25,24.5),(26,24.0),(27,24.2)], "sell_locations": [(10,27.8),(11,27.5),(2,27.2)]},
    {"id": 20, "name": "Neon",              "category": "Gas",         "buy_locations": [(9,5.20),(12,5.25)],          "sell_locations": [(1,5.85),(17,5.82),(16,5.78)]},
    {"id": 21, "name": "Processed Food",    "category": "Consumable",  "buy_locations": [(24,1.18),(25,1.18),(26,1.20),(27,1.19)], "sell_locations": [(3,1.38),(5,1.36),(4,1.35)]},
    {"id": 22, "name": "Quantanium",        "category": "Rare Metal",  "buy_locations": [(5,7850),(9,7900),(3,7920)],  "sell_locations": [(1,8340),(16,8310),(17,8290)]},
    {"id": 23, "name": "Quartz",            "category": "Metal",       "buy_locations": [(24,1.35),(25,1.38),(26,1.36)], "sell_locations": [(10,1.58),(11,1.56),(14,1.54)]},
    {"id": 24, "name": "Revenant Pod",      "category": "Drug",        "buy_locations": [(9,3.05),(12,3.08)],          "sell_locations": [(12,3.45),(4,3.42)]},
    {"id": 25, "name": "Silicon",           "category": "Metal",       "buy_locations": [(24,8.30),(26,8.40),(27,8.35)], "sell_locations": [(10,9.15),(14,9.10),(15,9.05)]},
    {"id": 26, "name": "Stims",             "category": "Drug",        "buy_locations": [(24,4.75),(25,4.80),(26,4.78)], "sell_locations": [(9,5.25),(12,5.22)]},
    {"id": 27, "name": "Taranite",          "category": "Rare Metal",  "buy_locations": [(3,4180),(5,4210),(9,4230)],  "sell_locations": [(1,4430),(16,4415),(13,4400)]},
    {"id": 28, "name": "Titanium",          "category": "Metal",       "buy_locations": [(20,700),(28,705),(10,708)],  "sell_locations": [(16,748),(19,745),(26,742)]},
    {"id": 29, "name": "Tungsten",          "category": "Metal",       "buy_locations": [(24,3.52),(25,3.55),(27,3.50)], "sell_locations": [(10,3.94),(11,3.92),(14,3.90)]},
    {"id": 30, "name": "Waste",             "category": "Waste",       "buy_locations": [(24,0.01),(25,0.01)],         "sell_locations": [(20,0.20),(28,0.18)]},
    {"id": 31, "name": "WiDoW",             "category": "Drug",        "buy_locations": [(9,14.50),(12,14.60)],        "sell_locations": [(12,16.00),(4,15.90),(6,15.80)]},
]

# ── Live cache (starts as static, replaced by API worker when data arrives) ───
_ships_cache       = list(_STATIC_SHIPS)
_commodities_cache = list(_STATIC_COMMODITIES)
_locations_cache   = list(LOCATIONS)   # starts as static, updated by API
_data_source       = "static"          # "static" | "live"

LOCATION_BY_ID = {loc["id"]: loc for loc in LOCATIONS}


def _rebuild_location_by_id():
    """Rebuild the lookup dict from the live cache."""
    global LOCATION_BY_ID
    LOCATION_BY_ID = {loc["id"]: loc for loc in _locations_cache}


# ── Cache update functions (called by ApiWorker signals) ──────────────────────

def update_locations(locations: list):
    """Replace the location cache with live UEX terminal data."""
    global _locations_cache, _data_source
    if not locations:
        return
    _locations_cache = locations
    _data_source = "live"
    _rebuild_location_by_id()

def update_ships(ships: list):
    global _ships_cache, _data_source
    if ships:
        _ships_cache = ships
        _data_source = "live"

def update_commodities(comms: list):
    """
    Update commodity cache from UEX data.
    UEX basic commodity endpoint doesn't include per-location prices,
    so we merge with static location data where available.
    """
    global _commodities_cache, _data_source
    if not comms:
        return

    # Build name→static map for location data preservation
    static_by_name = {c["name"].lower(): c for c in _STATIC_COMMODITIES}

    merged = []
    for c in comms:
        static = static_by_name.get(c["name"].lower(), {})
        # Use UEX prices if present, otherwise keep static
        buy  = c.get("price_buy",  0) or static.get("buy_locations",  [[None,0]])[0][1] if static.get("buy_locations") else 0
        sell = c.get("price_sell", 0) or static.get("sell_locations", [[None,0]])[0][1] if static.get("sell_locations") else 0

        merged.append({
            "id":             c["id"],
            "name":           c["name"],
            "category":       c["category"],
            "buy_locations":  static.get("buy_locations",  [(None, buy)]  if buy  else []),
            "sell_locations": static.get("sell_locations", [(None, sell)] if sell else []),
            # Also expose flat prices for simple display
            "price_buy":  buy,
            "price_sell": sell,
        })

    _commodities_cache = merged
    _data_source = "live"

def update_prices(price_rows: list):
    """
    Update location-level prices from UEX commodities_prices endpoint.
    Rows typically: {commodity_name, terminal_name, price_buy, price_sell, ...}
    """
    global _commodities_cache

    if not price_rows:
        return

    # Build commodity name → index map
    comm_by_name = {}
    for i, c in enumerate(_commodities_cache):
        comm_by_name[c["name"].lower()] = i

    # Build location name → id map from live cache
    loc_by_name = {loc["name"].lower(): loc["id"] for loc in _locations_cache}

    # Group rows by commodity
    buy_map  = {}   # comm_idx -> [(loc_id, price), ...]
    sell_map = {}

    for row in price_rows:
        name = str(row.get("commodity_name", row.get("name", ""))).lower()
        idx = comm_by_name.get(name)
        if idx is None:
            continue

        loc_name = str(row.get("terminal_name", row.get("location", ""))).lower()
        loc_id   = loc_by_name.get(loc_name)
        if loc_id is None:
            continue

        bp = float(row.get("price_buy",  0) or 0)
        sp = float(row.get("price_sell", 0) or 0)

        if bp > 0:
            buy_map.setdefault(idx, []).append((loc_id, bp))
        if sp > 0:
            sell_map.setdefault(idx, []).append((loc_id, sp))

    # Write back
    for i, c in enumerate(_commodities_cache):
        if i in buy_map:
            c["buy_locations"]  = sorted(buy_map[i],  key=lambda x: x[1])
        if i in sell_map:
            c["sell_locations"] = sorted(sell_map[i], key=lambda x: x[1], reverse=True)


# ── Public accessors ──────────────────────────────────────────────────────────

def get_ships() -> list:
    return _ships_cache

def get_commodities() -> list:
    return _commodities_cache

def get_locations() -> list:
    return _locations_cache

def get_data_source() -> str:
    return _data_source

# Keep SHIPS and COMMODITIES as aliases for backwards compat with tabs
# that import them directly — they'll get static data at import time,
# but tabs should call get_ships() / get_commodities() for live data.
SHIPS      = _STATIC_SHIPS
COMMODITIES = _STATIC_COMMODITIES


# ── Commodity helpers ─────────────────────────────────────────────────────────

def get_best_buy(commodity: dict) -> tuple:
    locs = commodity.get("buy_locations", [])
    if not locs:
        p = commodity.get("price_buy", 0)
        return ("N/A", p)
    best = min(locs, key=lambda x: x[1])
    loc  = LOCATION_BY_ID.get(best[0], {})
    return (loc.get("name", "N/A"), best[1])

def get_best_sell(commodity: dict) -> tuple:
    locs = commodity.get("sell_locations", [])
    if not locs:
        p = commodity.get("price_sell", 0)
        return ("N/A", p)
    best = max(locs, key=lambda x: x[1])
    loc  = LOCATION_BY_ID.get(best[0], {})
    return (loc.get("name", "N/A"), best[1])

def get_profit_margin(commodity: dict) -> float:
    _, buy  = get_best_buy(commodity)
    _, sell = get_best_sell(commodity)
    return sell - buy if buy > 0 else 0

def get_top_routes(limit: int = 50) -> list:
    routes = []
    for c in get_commodities():
        for buy_loc_id, buy_price in c.get("buy_locations", []):
            for sell_loc_id, sell_price in c.get("sell_locations", []):
                if sell_price <= buy_price or not buy_loc_id or not sell_loc_id:
                    continue
                profit = sell_price - buy_price
                margin = (profit / buy_price * 100) if buy_price > 0 else 0
                buy_loc  = LOCATION_BY_ID.get(buy_loc_id,  {})
                sell_loc = LOCATION_BY_ID.get(sell_loc_id, {})
                routes.append({
                    "commodity":  c["name"],
                    "category":   c["category"],
                    "buy_loc":    buy_loc.get("name",  "?"),
                    "buy_body":   buy_loc.get("body",  "?"),
                    "buy_price":  buy_price,
                    "sell_loc":   sell_loc.get("name", "?"),
                    "sell_body":  sell_loc.get("body", "?"),
                    "sell_price": sell_price,
                    "profit":     profit,
                    "margin_pct": margin,
                })
    routes.sort(key=lambda r: r["profit"], reverse=True)
    return routes[:limit]
