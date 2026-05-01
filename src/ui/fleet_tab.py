"""Fleet management tab."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QDialog,
    QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QFrame, QSplitter,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap
from core.data import get_ships
from core import fleet as fleet_store
from core.image_cache import ImageFetcher, get_cached


def _item(text, color=None, align=None, bold=False):
    it = QTableWidgetItem(str(text))
    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
    if color:
        it.setForeground(QColor(color))
    if align:
        it.setTextAlignment(align)
    if bold:
        f = it.font(); f.setBold(True); it.setFont(f)
    return it


STATUS_COLORS = {
    "Active":     "#00e676",
    "In Repair":  "#f0a800",
    "Stored":     "#3d6b88",
    "Destroyed":  "#e53935",
}

PURCHASE_COLORS = {
    "Pledge":  "#ab47bc",
    "In-Game": "#00e5ff",
}

INSURANCE_OPTIONS = ["", "SLI", "LTI", "3M", "6M", "12M", "120M"]
STATUS_OPTIONS    = ["Active", "In Repair", "Stored", "Destroyed"]
PURCHASE_OPTIONS  = ["", "Pledge", "In-Game"]


class FleetDialog(QDialog):
    def __init__(self, parent=None, entry=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Ship" if entry else "Add Ship")
        self.setMinimumWidth(440)
        self._entry = entry or {}
        self._build()

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setSpacing(12)
        vl.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        # Ship name — from live fleet-aware ship list
        self._ship_cb = QComboBox()
        ship_names = sorted(set(s["name"] for s in get_ships()))
        self._ship_cb.addItem("— Select Ship —")
        self._ship_cb.addItems(ship_names)
        if self._entry.get("ship_name"):
            idx = self._ship_cb.findText(self._entry["ship_name"])
            if idx >= 0:
                self._ship_cb.setCurrentIndex(idx)
        form.addRow("Ship *", self._ship_cb)

        self._nick = QLineEdit(self._entry.get("nickname", ""))
        self._nick.setPlaceholderText("e.g. Stardust")
        form.addRow("Nickname", self._nick)

        self._role = QLineEdit(self._entry.get("role", ""))
        self._role.setPlaceholderText("e.g. Trading, Mining")
        form.addRow("Primary Role", self._role)

        # Purchase type — new field
        self._purchase = QComboBox()
        self._purchase.addItems(PURCHASE_OPTIONS)
        cur_purchase = self._entry.get("purchase", "")
        if cur_purchase:
            idx = self._purchase.findText(cur_purchase)
            if idx >= 0:
                self._purchase.setCurrentIndex(idx)
        form.addRow("Purchased Via", self._purchase)

        self._ins = QComboBox()
        self._ins.addItems(INSURANCE_OPTIONS)
        if self._entry.get("insurance"):
            idx = self._ins.findText(self._entry["insurance"])
            if idx >= 0:
                self._ins.setCurrentIndex(idx)
        form.addRow("Insurance", self._ins)

        self._status = QComboBox()
        self._status.addItems(STATUS_OPTIONS)
        cur_status = self._entry.get("status", "Active")
        idx = self._status.findText(cur_status)
        if idx >= 0:
            self._status.setCurrentIndex(idx)
        form.addRow("Status", self._status)

        self._notes = QTextEdit(self._entry.get("loadout_notes", ""))
        self._notes.setPlaceholderText("Weapons, components, upgrades…")
        self._notes.setFixedHeight(80)
        form.addRow("Loadout Notes", self._notes)

        vl.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def _validate(self):
        if self._ship_cb.currentIndex() == 0:
            QMessageBox.warning(self, "Validation", "Please select a ship.")
            return
        self.accept()

    def get_entry(self) -> dict:
        return {
            "ship_name":     self._ship_cb.currentText(),
            "nickname":      self._nick.text().strip(),
            "role":          self._role.text().strip(),
            "purchase":      self._purchase.currentText(),
            "insurance":     self._ins.currentText(),
            "status":        self._status.currentText(),
            "loadout_notes": self._notes.toPlainText().strip(),
        }


class FleetTab(QWidget):
    fleet_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("My Fleet")
        title.setObjectName("section-title")
        self._count_lbl = QLabel("0 ships")
        self._count_lbl.setObjectName("muted")
        add_btn = QPushButton("＋  Add Ship")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self._add_ship)
        header.addWidget(title)
        header.addWidget(self._count_lbl)
        header.addStretch()
        header.addWidget(add_btn)
        root.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Ship", "Nickname", "Role", "Purchased Via",
            "Insurance", "Status", "Notes", "Actions"
        ])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.selectionModel().selectionChanged.connect(self._on_select)
        splitter.addWidget(self._table)

        # ── Detail panel with ship image ──────────────────────────
        self._detail = QFrame()
        self._detail.setObjectName("card")
        self._detail.setFrameShape(QFrame.Shape.StyledPanel)
        self._detail.setVisible(False)
        detail_layout = QHBoxLayout(self._detail)
        detail_layout.setContentsMargins(16, 12, 16, 12)
        detail_layout.setSpacing(16)

        # Image placeholder
        self._img_lbl = QLabel()
        self._img_lbl.setFixedSize(240, 135)
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(
            "background:#060d15; border:1px solid #1a3048; border-radius:3px; color:#3d6b88")
        self._img_lbl.setText("Loading image…")
        detail_layout.addWidget(self._img_lbl)

        # Ship info
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        self._detail_name  = QLabel()
        self._detail_name.setStyleSheet("color:#e8f4ff; font-size:15px; font-weight:700; letter-spacing:1px")
        self._detail_mfr   = QLabel()
        self._detail_mfr.setStyleSheet("color:#00e5ff; font-size:11px")
        self._detail_stats = QLabel()
        self._detail_stats.setStyleSheet("color:#6a9ab8; font-size:11px; font-family:monospace")
        self._detail_notes = QLabel()
        self._detail_notes.setStyleSheet("color:#b0d4e8; font-size:11px")
        self._detail_notes.setWordWrap(True)
        info_col.addWidget(self._detail_name)
        info_col.addWidget(self._detail_mfr)
        info_col.addSpacing(4)
        info_col.addWidget(self._detail_stats)
        info_col.addWidget(self._detail_notes)
        info_col.addStretch()
        detail_layout.addLayout(info_col, 1)

        splitter.addWidget(self._detail)
        splitter.setSizes([420, 160])
        root.addWidget(splitter)

        self._fetchers = []   # keep references so threads aren't GC'd
        self._load()

    def _load(self):
        self._fleet = fleet_store.load_fleet()
        self._populate()

    def _populate(self):
        self._table.setRowCount(len(self._fleet))
        self._count_lbl.setText(f"{len(self._fleet)} ship{'s' if len(self._fleet) != 1 else ''}")

        for row, e in enumerate(self._fleet):
            self._table.setItem(row, 0, _item(e.get("ship_name",""), "#e8f4ff", bold=True))
            self._table.setItem(row, 1, _item(e.get("nickname","—"), "#00e5ff"))
            self._table.setItem(row, 2, _item(e.get("role","—"), "#b0d4e8"))

            purchase = e.get("purchase", "")
            self._table.setItem(row, 3, _item(
                purchase or "—",
                PURCHASE_COLORS.get(purchase, "#3d6b88"),
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter))

            self._table.setItem(row, 4, _item(e.get("insurance","—"), "#b0d4e8",
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter))

            status = e.get("status","Active")
            self._table.setItem(row, 5, _item(status,
                STATUS_COLORS.get(status,"#b0d4e8"),
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter))

            notes = e.get("loadout_notes","")
            notes_short = notes[:40] + "…" if len(notes) > 40 else notes
            self._table.setItem(row, 6, _item(notes_short or "—", "#6a9ab8"))

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(4, 2, 4, 2)
            btn_l.setSpacing(4)
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(50)
            edit_btn.clicked.connect(lambda _, eid=e["id"]: self._edit_ship(eid))
            del_btn = QPushButton("✕")
            del_btn.setObjectName("danger")
            del_btn.setFixedWidth(32)
            del_btn.clicked.connect(lambda _, eid=e["id"]: self._delete_ship(eid))
            btn_l.addWidget(edit_btn)
            btn_l.addWidget(del_btn)
            self._table.setCellWidget(row, 7, btn_w)
            self._table.setRowHeight(row, 40)
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, e)

    def get_fleet_ship_names(self) -> list:
        """Return sorted list of ship names in the fleet. Used by the log tab."""
        return sorted(set(e.get("ship_name", "") for e in fleet_store.load_fleet() if e.get("ship_name")))

    def _on_select(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            self._detail.setVisible(False)
            return
        entry = self._table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if entry:
            self._show_detail(entry)

    def _show_detail(self, fleet_entry: dict):
        ship_name = fleet_entry.get("ship_name", "")
        nickname  = fleet_entry.get("nickname", "")
        role      = fleet_entry.get("role", "")
        insurance = fleet_entry.get("insurance", "")
        purchase  = fleet_entry.get("purchase", "")
        status    = fleet_entry.get("status", "Active")
        notes     = fleet_entry.get("loadout_notes", "")

        # Find matching ship in DB for specs + image
        ships = get_ships()
        ship_db = next((s for s in ships if s["name"] == ship_name), {})
        image_url = ship_db.get("image_url", "")

        STATUS_COLORS = {
            "Active": "#00e676", "In Repair": "#f0a800",
            "Stored": "#3d6b88", "Destroyed": "#e53935",
        }

        self._detail_name.setText(f'{ship_name}  "{nickname}"' if nickname else ship_name)
        self._detail_mfr.setText(
            f"{ship_db.get('manufacturer','—')}  ·  {ship_db.get('role','—')}"
        )

        stats_parts = []
        if ship_db.get("size"):    stats_parts.append(f"Size: {ship_db['size']}")
        if ship_db.get("crew"):    stats_parts.append(f"Crew: {ship_db['crew']}")
        if ship_db.get("cargo"):   stats_parts.append(f"Cargo: {ship_db['cargo']} SCU")
        if role:                   stats_parts.append(f"Role: {role}")
        if purchase:               stats_parts.append(f"Via: {purchase}")
        if insurance:              stats_parts.append(f"Ins: {insurance}")
        status_color = STATUS_COLORS.get(status, "#b0d4e8")
        stats_parts.append(f'<span style="color:{status_color}">{status}</span>')
        self._detail_stats.setText("   ·   ".join(stats_parts))
        self._detail_stats.setTextFormat(Qt.TextFormat.RichText)
        self._detail_notes.setText(notes if notes else "")

        # Image
        self._img_lbl.setText("Loading…")
        self._img_lbl.setPixmap(QPixmap())

        if image_url or ship_name:
            cached = get_cached(image_url or ship_name)
            if cached:
                self._set_image(image_url or ship_name, cached)
            else:
                fetcher = ImageFetcher(image_url, ship_name, self)
                fetcher.image_ready.connect(self._set_image)
                fetcher.failed.connect(lambda _: self._img_lbl.setText("No image available"))
                self._fetchers.append(fetcher)
                fetcher.start()
        else:
            self._img_lbl.setText("No image available")

        self._detail.setVisible(True)

    def _set_image(self, url: str, pixmap: QPixmap):
        scaled = pixmap.scaled(
            240, 135,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._img_lbl.setPixmap(scaled)
        self._img_lbl.setText("")

    def _add_ship(self):
        dlg = FleetDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fleet_store.add_ship(dlg.get_entry())
            self._load()
            self.fleet_changed.emit()

    def _edit_ship(self, entry_id: str):
        entry = next((e for e in self._fleet if e["id"] == entry_id), None)
        if not entry:
            return
        dlg = FleetDialog(self, entry)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fleet_store.update_ship(entry_id, dlg.get_entry())
            self._load()
            self.fleet_changed.emit()

    def _delete_ship(self, entry_id: str):
        entry = next((e for e in self._fleet if e["id"] == entry_id), None)
        name = entry.get("ship_name","this ship") if entry else "this ship"
        reply = QMessageBox.question(
            self, "Remove Ship",
            f"Remove {name} from fleet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            fleet_store.delete_ship(entry_id)
            self._load()
            self.fleet_changed.emit()

    def refresh(self):
        self._load()
