"""Overview dashboard tab."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from core.data import get_commodities, get_ships, get_profit_margin, get_top_routes
from core.fleet import load_fleet


def _card(parent=None):
    f = QFrame(parent)
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
        # Create the root layout once and reuse it
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(20, 20, 20, 20)
        self._root.setSpacing(16)
        self._build()

    def _build(self):
        root = self._root

        # Always use live cache accessors — never static imports
        fleet      = load_fleet()
        ships      = get_ships()
        commodities = get_commodities()
        top_comms  = sorted(commodities, key=get_profit_margin, reverse=True)
        best_margin = f"{get_profit_margin(top_comms[0]):.2f} aUEC" if top_comms else "—"
        best_name   = top_comms[0]["name"] if top_comms else "—"

        # ── Stat cards ────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        for label, value, sub in [
            ("Fleet Size",   str(len(fleet)),       "Ships registered"),
            ("Ships in DB",  str(len(ships)),        "Loadouts available"),
            ("Commodities",  str(len(commodities)), "Items tracked"),
            ("Best Margin",  best_margin,            best_name),
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

        # ── Lower panels ──────────────────────────────────────────
        lower = QHBoxLayout()
        lower.setSpacing(12)

        # Top trade routes — uses live data
        routes_card = QFrame()
        routes_card.setObjectName("card")
        routes_card.setFrameShape(QFrame.Shape.StyledPanel)
        rv = QVBoxLayout(routes_card)
        rv.setContentsMargins(14, 14, 14, 14)
        rv.setSpacing(10)
        rv.addWidget(_label("Top Trade Routes", "section-title"))

        top_routes = get_top_routes(6)
        if top_routes:
            for r in top_routes:
                row = QHBoxLayout()
                col = QVBoxLayout()
                col.setSpacing(1)
                name_lbl = QLabel(r["commodity"])
                name_lbl.setStyleSheet("color:#e8f4ff; font-weight:600")
                route_lbl = QLabel(f"{r['buy_loc']}  →  {r['sell_loc']}")
                route_lbl.setStyleSheet("color:#3d6b88; font-size:11px")
                profit_lbl = QLabel(f"+{r['profit']:.2f}")
                profit_lbl.setStyleSheet("color:#00e676; font-family:monospace")
                profit_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                col.addWidget(name_lbl)
                col.addWidget(route_lbl)
                row.addLayout(col)
                row.addWidget(profit_lbl)
                rv.addLayout(row)
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("color:#111f2e")
                rv.addWidget(sep)
        else:
            rv.addWidget(_label("No trade data available.", "muted"))

        rv.addStretch()
        lower.addWidget(routes_card, 1)

        # Fleet summary
        fleet_card = QFrame()
        fleet_card.setObjectName("card")
        fleet_card.setFrameShape(QFrame.Shape.StyledPanel)
        fv = QVBoxLayout(fleet_card)
        fv.setContentsMargins(14, 14, 14, 14)
        fv.setSpacing(10)
        fv.addWidget(_label("My Fleet", "section-title"))

        STATUS_COLORS = {
            "Active":    "#00e676",
            "In Repair": "#f0a800",
            "Stored":    "#3d6b88",
            "Destroyed": "#e53935",
        }

        if fleet:
            for ship in fleet[:8]:
                row = QHBoxLayout()
                name = ship.get("ship_name", "Unknown")
                nick = ship.get("nickname", "")
                name_lbl = QLabel(f'{name}  "{nick}"' if nick else name)
                name_lbl.setStyleSheet("color:#e8f4ff; font-weight:600")
                status = ship.get("status", "Active")
                status_lbl = QLabel(status)
                status_lbl.setStyleSheet(
                    f"color:{STATUS_COLORS.get(status,'#3d6b88')};"
                    "font-size:11px; font-family:monospace")
                status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                row.addWidget(name_lbl)
                row.addWidget(status_lbl)
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
        # Clear all items from the existing root layout
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
