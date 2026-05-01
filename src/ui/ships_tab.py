"""Ships / loadout viewer tab."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QSplitter,
    QGridLayout, QPushButton, QDialog, QDialogButtonBox,
    QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from core.data import get_ships
from core.overrides import save_override, remove_override, load_overrides


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
    "Flight Ready": "#00e676",
    "In Concept":   "#f0a800",
}

STATUS_OPTIONS = ["Flight Ready", "In Concept"]


class StatusEditDialog(QDialog):
    def __init__(self, ship: dict, parent=None):
        super().__init__(parent)
        self._ship = ship
        self.setWindowTitle("Edit Ship Status")
        self.setFixedWidth(360)
        self._build()

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setSpacing(14)

        # Ship name heading
        name_lbl = QLabel(self._ship["name"])
        name_lbl.setStyleSheet(
            "color:#e8f4ff; font-size:14px; font-weight:700; letter-spacing:1px")
        vl.addWidget(name_lbl)

        form = QFormLayout()
        form.setSpacing(10)

        self._status_cb = QComboBox()
        self._status_cb.addItems(STATUS_OPTIONS)
        cur = self._ship.get("status", "Flight Ready")
        idx = self._status_cb.findText(cur)
        if idx >= 0:
            self._status_cb.setCurrentIndex(idx)
        form.addRow("Status:", self._status_cb)
        vl.addLayout(form)

        # Show if there's an existing user override
        overrides = load_overrides()
        key = self._ship["name"].lower().strip()
        if key in overrides:
            note = QLabel(f"★ User override active: {overrides[key]}")
            note.setStyleSheet("color:#f0a800; font-size:11px; font-style:italic")
            vl.addWidget(note)
            reset_btn = QPushButton("Remove Override (revert to auto-detect)")
            reset_btn.setObjectName("danger")
            reset_btn.clicked.connect(self._remove_override)
            vl.addWidget(reset_btn)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def _remove_override(self):
        remove_override(self._ship["name"])
        QMessageBox.information(
            self, "Override Removed",
            f"Override for {self._ship['name']} removed.\n"
            "Status will be auto-detected on next refresh."
        )
        self.reject()

    def get_status(self) -> str:
        return self._status_cb.currentText()


class ShipsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_ship = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        self._source_ships = get_ships()

        title = QLabel("Ship Database")
        title.setObjectName("section-title")
        root.addWidget(title)

        # Filter bar
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search ships…")
        self._search.setFixedWidth(200)
        self._search.textChanged.connect(self._apply_filters)

        self._mfr_cb = QComboBox()
        self._mfr_cb.addItem("All Manufacturers")
        self._mfr_cb.addItems(sorted(set(s["manufacturer"] for s in self._source_ships)))
        self._mfr_cb.currentTextChanged.connect(self._apply_filters)

        self._role_cb = QComboBox()
        self._role_cb.addItem("All Roles")
        self._role_cb.addItems(sorted(set(s["role"] for s in self._source_ships)))
        self._role_cb.currentTextChanged.connect(self._apply_filters)

        self._size_cb = QComboBox()
        self._size_cb.addItem("All Sizes")
        self._size_cb.addItems(["Small", "Medium", "Large", "Capital"])
        self._size_cb.currentTextChanged.connect(self._apply_filters)

        self._status_cb = QComboBox()
        self._status_cb.addItem("All Statuses")
        self._status_cb.addItems(STATUS_OPTIONS)
        self._status_cb.currentTextChanged.connect(self._apply_filters)

        bar.addWidget(QLabel("Search:"))
        bar.addWidget(self._search)
        bar.addWidget(QLabel("Manufacturer:"))
        bar.addWidget(self._mfr_cb)
        bar.addWidget(QLabel("Role:"))
        bar.addWidget(self._role_cb)
        bar.addWidget(QLabel("Size:"))
        bar.addWidget(self._size_cb)
        bar.addWidget(QLabel("Status:"))
        bar.addWidget(self._status_cb)
        bar.addStretch()
        root.addLayout(bar)

        # Splitter: table top, detail bottom
        splitter = QSplitter(Qt.Orientation.Vertical)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Ship", "Manufacturer", "Role", "Size", "Crew", "Cargo (SCU)", "Status"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.selectionModel().selectionChanged.connect(self._on_select)
        splitter.addWidget(self._table)

        # Detail panel
        self._detail = QFrame()
        self._detail.setObjectName("card")
        self._detail.setFrameShape(QFrame.Shape.StyledPanel)
        self._detail.setVisible(False)
        self._detail_layout = QGridLayout(self._detail)
        self._detail_layout.setContentsMargins(16, 14, 16, 14)
        splitter.addWidget(self._detail)
        splitter.setSizes([500, 180])

        root.addWidget(splitter)
        self._populate(self._source_ships)

    def _populate(self, ships):
        overrides = load_overrides()
        self._table.setRowCount(len(ships))
        for row, s in enumerate(ships):
            # Apply any saved user overrides to display
            name_key = s["name"].lower().strip()
            status = overrides.get(name_key, s.get("status", "Flight Ready"))

            self._table.setItem(row, 0, _item(s["name"], "#e8f4ff", bold=True))
            self._table.setItem(row, 1, _item(s["manufacturer"], "#6a9ab8"))
            self._table.setItem(row, 2, _item(s["role"], "#b0d4e8"))
            self._table.setItem(row, 3, _item(s["size"], "#b0d4e8"))
            self._table.setItem(row, 4, _item(str(s["crew"]),
                None, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter))
            self._table.setItem(row, 5, _item(str(s["cargo"]),
                "#f0a800" if s["cargo"] > 0 else "#3d6b88",
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))

            # Add ★ marker if user has overridden this ship
            status_text = f"★ {status}" if name_key in overrides else status
            self._table.setItem(row, 6, _item(
                status_text,
                STATUS_COLORS.get(status, "#b0d4e8"),
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter))

            # Store full ship dict + resolved status
            ship_copy = dict(s)
            ship_copy["status"] = status
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, ship_copy)

    def _apply_filters(self):
        q      = self._search.text().lower()
        mfr    = self._mfr_cb.currentText()
        role   = self._role_cb.currentText()
        size   = self._size_cb.currentText()
        status = self._status_cb.currentText()
        overrides = load_overrides()

        filtered = []
        for s in self._source_ships:
            name_key     = s["name"].lower().strip()
            resolved_st  = overrides.get(name_key, s.get("status", "Flight Ready"))
            if (q in s["name"].lower() or q in s["manufacturer"].lower())          \
            and (mfr    == "All Manufacturers" or s["manufacturer"] == mfr)        \
            and (role   == "All Roles"         or s["role"]         == role)        \
            and (size   == "All Sizes"         or s["size"]         == size)        \
            and (status == "All Statuses"      or resolved_st       == status):
                filtered.append(s)

        self._populate(filtered)
        self._detail.setVisible(False)
        self._selected_ship = None

    def _on_select(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            self._detail.setVisible(False)
            self._selected_ship = None
            return
        ship = self._table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if not ship:
            return
        self._selected_ship = ship
        self._show_detail(ship)

    def _show_detail(self, s):
        # Clear old widgets
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        status = s.get("status", "Flight Ready")
        status_color = STATUS_COLORS.get(status, "#b0d4e8")

        # Check if user has an override saved
        overrides = load_overrides()
        has_override = s["name"].lower().strip() in overrides

        name_lbl = QLabel(s["name"])
        name_lbl.setStyleSheet(
            "color:#e8f4ff; font-size:16px; font-weight:700; letter-spacing:1px")
        mfr_lbl = QLabel(f"{s['manufacturer']}  ·  {s['role']}")
        mfr_lbl.setStyleSheet("color:#00e5ff; font-size:11px")

        # Status label — show ★ if user override is active
        status_display = f"★ {status} (user override)" if has_override else status
        status_lbl = QLabel(status_display)
        status_lbl.setStyleSheet(
            f"color:{status_color}; font-size:11px; font-weight:600; font-family:monospace")
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Edit status button
        edit_btn = QPushButton("✎  Edit Status")
        edit_btn.setFixedWidth(120)
        edit_btn.clicked.connect(lambda: self._edit_status(s))

        self._detail_layout.addWidget(name_lbl,   0, 0, 1, 3)
        self._detail_layout.addWidget(mfr_lbl,    1, 0, 1, 2)
        self._detail_layout.addWidget(status_lbl, 1, 2)

        stats = [
            ("Size",  s["size"]),
            ("Crew",  str(s["crew"])),
            ("Cargo", f"{s['cargo']} SCU"),
            ("Price", f"{s['price_uec']:,} aUEC" if s["price_uec"] else "Pledge Only"),
        ]
        for col, (label, value) in enumerate(stats):
            frame = QFrame()
            frame.setObjectName("card-accent")
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(10, 8, 10, 8)
            fl.setSpacing(2)
            lbl = QLabel(label)
            lbl.setObjectName("stat-label")
            val = QLabel(value)
            val.setStyleSheet("color:#e8f4ff; font-size:14px; font-weight:700")
            fl.addWidget(lbl)
            fl.addWidget(val)
            self._detail_layout.addWidget(frame, 2, col)

        self._detail_layout.addWidget(edit_btn, 2, 4)
        self._detail.setVisible(True)

    def _edit_status(self, ship: dict):
        dlg = StatusEditDialog(ship, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_status = dlg.get_status()
            save_override(ship["name"], new_status)
            # Update the in-memory ship dict so the detail refreshes correctly
            ship["status"] = new_status
            self._selected_ship = ship
            self._apply_filters()
            # Re-select the same ship if still visible
            for row in range(self._table.rowCount()):
                item = self._table.item(row, 0)
                if item and item.text() == ship["name"]:
                    self._table.selectRow(row)
                    break

    def refresh(self, ships: list = None):
        """Called by MainWindow when live ship data arrives."""
        from core.data import get_ships
        self._source_ships = ships if ships is not None else get_ships()
        # Rebuild filter dropdowns with new manufacturer/role lists
        self._mfr_cb.blockSignals(True)
        self._mfr_cb.clear()
        self._mfr_cb.addItem("All Manufacturers")
        self._mfr_cb.addItems(sorted(set(s["manufacturer"] for s in self._source_ships)))
        self._mfr_cb.blockSignals(False)

        self._role_cb.blockSignals(True)
        self._role_cb.clear()
        self._role_cb.addItem("All Roles")
        self._role_cb.addItems(sorted(set(s["role"] for s in self._source_ships)))
        self._role_cb.blockSignals(False)

        self._apply_filters()
