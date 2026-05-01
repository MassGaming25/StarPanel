"""Overview dashboard tab."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from core.data import get_commodities, get_ships, get_profit_margin, get_top_routes
from core.fleet import load_fleet

CHANNEL_COLORS = {
    "live":         "#00e676",
    "ptu":          "#00e5ff",
    "eptu":         "#f0a800",
    "tech_preview": "#ab47bc",
}
CHANNEL_LABELS = {
    "live":         "LIVE",
    "ptu":          "PTU",
    "eptu":         "EVOCATI",
    "tech_preview": "TECH PREVIEW",
}


def _card():
    f = QFrame()
    f.setObjectName("card-accent")
    f.setFrameShape(QFrame.Shape.StyledPanel)
    return f


def _label(text, obj_name=None):
    l = QLabel(text)
    if obj_name:
        l.setObjectName(obj_name)
    return l


class OverviewTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sc_versions = {}
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(20, 20, 20, 20)
        self._root.setSpacing(16)
        self._build()

    def update_sc_versions(self, versions: dict):
        self._sc_versions = versions
        self.refresh()

    def _build(self):
        root = self._root

        fleet       = load_fleet()
        ships       = get_ships()
        commodities = get_commodities()
        top_comms   = sorted(commodities, key=get_profit_margin, reverse=True)
        best_margin = f"{get_profit_margin(top_comms[0]):.2f} aUEC" if top_comms else "—"
        best_name   = top_comms[0]["name"] if top_comms else "—"

        # ── Stat cards ────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        for label, value, sub in [
            ("Fleet Size",   str(len(fleet)),        "Ships registered"),
            ("Ships in DB",  str(len(ships)),         "Loadouts available"),
            ("Commodities",  str(len(commodities)),  "Items tracked"),
            ("Best Margin",  best_margin,             best_name),
        ]:
            card = _card()
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            vl = QVBoxLayout(card)
            vl.setContentsMargins(14, 12, 14, 12)
            vl.setSpacing(2)
            vl.addWidget(_label(label, "stat-label"))
            vl.addWidget(_label(value, "stat-value"))
            vl.addWidget(_label(sub,   "muted"))
            stats_row.addWidget(card)
        root.addLayout(stats_row)

        # ── SC Version tracker ────────────────────────────────────
        ver_card = QFrame()
        ver_card.setObjectName("card")
        ver_card.setFrameShape(QFrame.Shape.StyledPanel)
        ver_layout = QHBoxLayout(ver_card)
        ver_layout.setContentsMargins(16, 12, 16, 12)
        ver_layout.setSpacing(0)

        title_lbl = QLabel("Star Citizen Versions")
        title_lbl.setStyleSheet(
            "color:#3d6b88; font-size:10px; font-weight:700; letter-spacing:2px")
        ver_layout.addWidget(title_lbl)
        ver_layout.addSpacing(24)

        versions = self._sc_versions
        has_any  = any(versions.values()) if versions else False

        if has_any:
            for key in ["live", "ptu", "eptu", "tech_preview"]:
                ver = versions.get(key, "").strip()
                # Skip if empty or looks like just a channel name
                if not ver or ver.lower() in ("live", "ptu", "eptu", "active",
                                               "true", "false", "1", "0"):
                    continue
                color = CHANNEL_COLORS[key]
                ch_lbl = CHANNEL_LABELS[key]

                cw = QFrame()
                cw.setStyleSheet(
                    f"border:none; border-left:2px solid {color}; "
                    f"margin-right:24px; padding-left:8px")
                cw_vl = QVBoxLayout(cw)
                cw_vl.setContentsMargins(0, 0, 0, 0)
                cw_vl.setSpacing(1)

                ch_label = QLabel(ch_lbl)
                ch_label.setStyleSheet(
                    f"color:{color}; font-size:9px; font-weight:700; "
                    f"letter-spacing:2px; font-family:monospace; border:none")
                ver_label = QLabel(ver)
                ver_label.setStyleSheet(
                    "color:#e8f4ff; font-size:13px; font-weight:700; "
                    "font-family:monospace; border:none")

                cw_vl.addWidget(ch_label)
                cw_vl.addWidget(ver_label)
                ver_layout.addWidget(cw)
        else:
            loading = QLabel("Fetching SC version data…")
            loading.setObjectName("muted")
            ver_layout.addWidget(loading)

        ver_layout.addStretch()
        root.addWidget(ver_card)

        # ── Lower panels ──────────────────────────────────────────
        lower = QHBoxLayout()
        lower.setSpacing(12)

        routes_card = QFrame()
        routes_card.setObjectName("card")
        routes_card.setFrameShape(QFrame.Shape.StyledPanel)
        rv = QVBoxLayout(routes_card)
        rv.setContentsMargins(14, 14, 14, 14)
        rv.setSpacing(10)
        rv.addWidget(_label("Top Trade Routes", "section-title"))

        for r in get_top_routes(6):
            row = QHBoxLayout()
            col = QVBoxLayout()
            col.setSpacing(1)
            nl = QLabel(r["commodity"])
            nl.setStyleSheet("color:#e8f4ff; font-weight:600")
            rl = QLabel(f"{r['buy_loc']}  →  {r['sell_loc']}")
            rl.setStyleSheet("color:#3d6b88; font-size:11px")
            pl = QLabel(f"+{r['profit']:.2f}")
            pl.setStyleSheet("color:#00e676; font-family:monospace")
            pl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            col.addWidget(nl); col.addWidget(rl)
            row.addLayout(col); row.addWidget(pl)
            rv.addLayout(row)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color:#111f2e")
            rv.addWidget(sep)

        if not get_top_routes(1):
            rv.addWidget(_label("No trade data available.", "muted"))
        rv.addStretch()
        lower.addWidget(routes_card, 1)

        fleet_card = QFrame()
        fleet_card.setObjectName("card")
        fleet_card.setFrameShape(QFrame.Shape.StyledPanel)
        fv = QVBoxLayout(fleet_card)
        fv.setContentsMargins(14, 14, 14, 14)
        fv.setSpacing(10)
        fv.addWidget(_label("My Fleet", "section-title"))

        STATUS_COLORS = {
            "Active":    "#00e676", "In Repair": "#f0a800",
            "Stored":    "#3d6b88", "Destroyed": "#e53935",
        }

        if fleet:
            for ship in fleet[:8]:
                row = QHBoxLayout()
                name = ship.get("ship_name", "Unknown")
                nick = ship.get("nickname", "")
                nl = QLabel(f'{name}  "{nick}"' if nick else name)
                nl.setStyleSheet("color:#e8f4ff; font-weight:600")
                status = ship.get("status", "Active")
                sl = QLabel(status)
                sl.setStyleSheet(
                    f"color:{STATUS_COLORS.get(status,'#3d6b88')};"
                    "font-size:11px; font-family:monospace")
                sl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                row.addWidget(nl); row.addWidget(sl)
                fv.addLayout(row)
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("color:#111f2e")
                fv.addWidget(sep)
        else:
            empty = QLabel("No ships in fleet yet.\nAdd ships in the Fleet tab.")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fv.addWidget(empty)

        fv.addStretch()
        lower.addWidget(fleet_card, 1)
        root.addLayout(lower)

    def refresh(self):
        while self._root.count():
            item = self._root.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
        self._build()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
