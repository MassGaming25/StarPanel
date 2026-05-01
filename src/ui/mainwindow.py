"""StarPanel — main application window."""

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer

from ui.theme import DARK_PALETTE
from ui.overview_tab import OverviewTab
from ui.ships_tab import ShipsTab
from ui.commodities_tab import CommoditiesTab
from ui.fleet_tab import FleetTab
from ui.log_tab import LogTab
from core.uex import ApiWorker
import core.data as data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StarPanel")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(DARK_PALETTE)

        # ── Tabs ───────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self._overview    = OverviewTab()
        self._ships       = ShipsTab()
        self._commodities = CommoditiesTab()
        self._fleet       = FleetTab()
        self._log         = LogTab()

        self._tabs.addTab(self._overview,    "  Overview  ")
        self._tabs.addTab(self._ships,       "  Ships  ")
        self._tabs.addTab(self._commodities, "  Commodities  ")
        self._tabs.addTab(self._fleet,       "  Fleet  ")
        self._tabs.addTab(self._log,         "  Captain's Log  ")
        self.setCentralWidget(self._tabs)

        # Fleet changes → overview refresh
        self._fleet.fleet_changed.connect(self._overview.refresh)

        # ── Status bar ─────────────────────────────────────────────
        bar = QStatusBar()
        self.setStatusBar(bar)

        self._status_lbl = QLabel("StarPanel  ·  Loading…")
        self._status_lbl.setStyleSheet("color:#3d6b88; padding:0 8px")
        bar.addWidget(self._status_lbl)

        self._source_badge = QLabel("● STATIC")
        self._source_badge.setStyleSheet(
            "color:#f0a800; font-family:monospace; font-size:11px; padding:0 8px")
        bar.addPermanentWidget(self._source_badge)

        self._refresh_btn = QPushButton("↻  Refresh Data")
        self._refresh_btn.setFixedHeight(22)
        self._refresh_btn.setStyleSheet("font-size:11px; padding:0 10px; letter-spacing:0")
        self._refresh_btn.clicked.connect(self._start_fetch)
        bar.addPermanentWidget(self._refresh_btn)

        self._clock_lbl = QLabel()
        self._clock_lbl.setStyleSheet(
            "color:#00b8d9; font-family:monospace; font-size:11px; padding:0 8px")
        bar.addPermanentWidget(self._clock_lbl)

        # ── Clock ──────────────────────────────────────────────────
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

        # ── Background fetch ───────────────────────────────────────
        self._worker = None
        self._start_fetch()

    def _start_fetch(self):
        if self._worker and self._worker.isRunning():
            return
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText("↻  Fetching…")
        self._source_badge.setText("● FETCHING")
        self._source_badge.setStyleSheet(
            "color:#00b8d9; font-family:monospace; font-size:11px; padding:0 8px")

        self._worker = ApiWorker()
        self._worker.status_update.connect(self._on_status)
        self._worker.ships_ready.connect(self._on_ships)
        self._worker.commodities_ready.connect(self._on_commodities)
        self._worker.prices_ready.connect(self._on_prices)
        self._worker.locations_ready.connect(self._on_locations)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.log_line.connect(lambda msg: print(f"[API] {msg}"))
        self._worker.start()

    def _on_status(self, msg: str):
        self._status_lbl.setText(msg)

    def _on_ships(self, ships: list):
        data.update_ships(ships)
        source = ships[0].get("source", "unknown") if ships else "unknown"
        label  = {"fleetyards": "Fleetyards", "rsi": "RSI Matrix"}.get(source, source.upper())
        self._status_lbl.setText(f"Ships: {len(ships)} from {label}")
        self._ships.refresh(ships)

    def _on_locations(self, locations: list):
        data.update_locations(locations)
        self._status_lbl.setText(f"Locations: {len(locations)} loaded from UEX")

    def _on_commodities(self, comms: list):
        data.update_commodities(comms)
        self._commodities.refresh()

    def _on_prices(self, price_rows: list):
        data.update_prices(price_rows)
        self._commodities.refresh()

    def _on_finished(self, success: bool):
        self._refresh_btn.setEnabled(True)
        self._refresh_btn.setText("↻  Refresh Data")
        if success:
            self._source_badge.setText("● LIVE")
            self._source_badge.setStyleSheet(
                "color:#00e676; font-family:monospace; font-size:11px; padding:0 8px")
            self._overview.refresh()
        else:
            self._source_badge.setText("● STATIC")
            self._source_badge.setStyleSheet(
                "color:#f0a800; font-family:monospace; font-size:11px; padding:0 8px")

    def _tick(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d  %H:%M:%S UTC")
        self._clock_lbl.setText(now)
