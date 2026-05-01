"""Captain's Log tab."""

from datetime import datetime, timezone
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QFrame, QSplitter,
    QDateTimeEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QColor
from core.captains_log import (
    load_log, add_entry, update_entry, delete_entry,
    ENTRY_TYPES, ENTRY_COLORS
)
from core import fleet as fleet_store
from core.data import get_locations
from ui.widgets import SearchableComboBox


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


def _fmt_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone()
        return dt.strftime("%Y-%m-%d  %H:%M")
    except Exception:
        return iso[:16]


def _fleet_ship_names() -> list:
    """Return sorted ship names from the fleet. Log entries are fleet-only."""
    fleet = fleet_store.load_fleet()
    return sorted(set(e.get("ship_name", "") for e in fleet if e.get("ship_name")))


class LogEntryDialog(QDialog):
    def __init__(self, parent=None, entry=None):
        super().__init__(parent)
        self._entry = entry or {}
        self.setWindowTitle("Edit Log Entry" if entry else "New Log Entry")
        self.setMinimumWidth(540)
        self._build()

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setSpacing(12)
        vl.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        # ── Date & Time ────────────────────────────────────────────
        self._dt_edit = QDateTimeEdit()
        self._dt_edit.setDisplayFormat("yyyy-MM-dd  HH:mm")
        self._dt_edit.setCalendarPopup(True)
        self._dt_edit.setStyleSheet(
            "QDateTimeEdit { background:#0c1520; border:1px solid #1a3048; "
            "border-radius:3px; padding:5px 10px; color:#b0d4e8; }"
            "QDateTimeEdit::drop-down { border:none; width:18px; }"
        )
        # Load existing timestamp or default to now
        if self._entry.get("log_datetime"):
            try:
                dt = datetime.fromisoformat(self._entry["log_datetime"])
                self._dt_edit.setDateTime(QDateTime(
                    dt.year, dt.month, dt.day,
                    dt.hour, dt.minute
                ))
            except Exception:
                self._dt_edit.setDateTime(QDateTime.currentDateTime())
        else:
            self._dt_edit.setDateTime(QDateTime.currentDateTime())
        form.addRow("Date / Time:", self._dt_edit)

        # ── Entry type ─────────────────────────────────────────────
        self._type_cb = QComboBox()
        self._type_cb.addItems(ENTRY_TYPES)
        if self._entry.get("entry_type"):
            idx = self._type_cb.findText(self._entry["entry_type"])
            if idx >= 0:
                self._type_cb.setCurrentIndex(idx)
        self._type_cb.currentTextChanged.connect(self._on_type_changed)
        form.addRow("Entry Type:", self._type_cb)

        # ── Title ──────────────────────────────────────────────────
        self._title = QLineEdit(self._entry.get("title", ""))
        self._title.setPlaceholderText("Brief summary…")
        form.addRow("Title:", self._title)

        # ── Ship — fleet only ──────────────────────────────────────
        self._ship_cb = QComboBox()
        self._ship_cb.addItem("— None —")
        fleet_ships = _fleet_ship_names()
        if fleet_ships:
            self._ship_cb.addItems(fleet_ships)
        else:
            self._ship_cb.addItem("(no ships in fleet)")
        cur_ship = self._entry.get("ship", "")
        if cur_ship:
            idx = self._ship_cb.findText(cur_ship)
            if idx >= 0:
                self._ship_cb.setCurrentIndex(idx)
        form.addRow("Ship:", self._ship_cb)

        # ── Location fields ────────────────────────────────────────
        loc_names = sorted(set(l["name"] for l in get_locations()))

        self._loc_from_cb    = SearchableComboBox()
        self._loc_from_cb.populate(loc_names, "— None —")
        self._loc_from_label = QLabel("Departed From:")
        cur_from = self._entry.get("location_from", "")
        if cur_from:
            self._loc_from_cb.set_value(cur_from)
        form.addRow(self._loc_from_label, self._loc_from_cb)

        self._loc_to_cb    = SearchableComboBox()
        self._loc_to_cb.populate(loc_names, "— None —")
        self._loc_to_label = QLabel("Arrived At:")
        cur_to = self._entry.get("location_to", "")
        if cur_to:
            self._loc_to_cb.set_value(cur_to)
        form.addRow(self._loc_to_label, self._loc_to_cb)

        # ── Type-specific fields ───────────────────────────────────
        self._profit       = QLineEdit(self._entry.get("profit", ""))
        self._profit.setPlaceholderText("e.g. 45000")
        self._profit_label = QLabel("Profit (aUEC):")
        form.addRow(self._profit_label, self._profit)

        self._outcome_cb    = QComboBox()
        self._outcome_cb.addItems([
            "Victory", "Defeat", "Draw", "Escaped",
            "Destroyed", "Completed", "Failed", "Partial"
        ])
        cur_out = self._entry.get("outcome", "")
        if cur_out:
            idx = self._outcome_cb.findText(cur_out)
            if idx >= 0: self._outcome_cb.setCurrentIndex(idx)
        self._outcome_label = QLabel("Outcome:")
        form.addRow(self._outcome_label, self._outcome_cb)

        self._system       = QLineEdit(self._entry.get("system", ""))
        self._system.setPlaceholderText("e.g. Stanton, Pyro")
        self._system_label = QLabel("System:")
        form.addRow(self._system_label, self._system)

        vl.addLayout(form)

        # ── Notes ──────────────────────────────────────────────────
        vl.addWidget(QLabel("Notes:"))
        self._notes = QTextEdit(self._entry.get("notes", ""))
        self._notes.setPlaceholderText("Detailed account…")
        self._notes.setMinimumHeight(110)
        vl.addWidget(self._notes)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

        self._on_type_changed(self._type_cb.currentText())

    def _on_type_changed(self, entry_type: str):
        is_trade    = entry_type == "Trade Run"
        is_combat   = entry_type == "Combat / Battle Report"
        is_mission  = entry_type == "Mission / Bounty"
        is_incident = entry_type == "Incident Report"
        is_departed = entry_type == "Departed Location"
        is_arrived  = entry_type == "Arrived at Location"
        is_explore  = entry_type == "Exploration / Discovery"

        show_from    = is_departed or is_arrived or is_trade or is_combat or is_mission or is_incident
        show_to      = is_arrived  or is_trade
        show_profit  = is_trade or is_mission
        show_outcome = is_combat or is_mission or is_incident
        show_system  = is_explore or is_arrived or is_departed

        self._loc_from_label.setVisible(show_from)
        self._loc_from_cb.setVisible(show_from)
        self._loc_to_label.setVisible(show_to)
        self._loc_to_cb.setVisible(show_to)
        self._profit_label.setVisible(show_profit)
        self._profit.setVisible(show_profit)
        self._outcome_label.setVisible(show_outcome)
        self._outcome_cb.setVisible(show_outcome)
        self._system_label.setVisible(show_system)
        self._system.setVisible(show_system)

        placeholders = {
            "Departed Location":       "Departed [location]",
            "Arrived at Location":     "Arrived at [location]",
            "Combat / Battle Report":  "Engagement near [location]",
            "Trade Run":               "[commodity] run: [from] → [to]",
            "Exploration / Discovery": "Discovered [object/area]",
            "Mission / Bounty":        "Bounty: [target]",
            "Incident Report":         "Incident at [location]",
            "General / Personal Log":  "Log entry",
        }
        self._title.setPlaceholderText(placeholders.get(entry_type, "Brief summary…"))

    def _validate(self):
        if not self._title.text().strip():
            QMessageBox.warning(self, "Validation", "Please enter a title.")
            return
        self.accept()

    def get_entry(self) -> dict:
        t  = self._type_cb.currentText()
        qt = self._dt_edit.dateTime()
        log_dt = datetime(
            qt.date().year(), qt.date().month(), qt.date().day(),
            qt.time().hour(), qt.time().minute()
        ).astimezone().isoformat()

        # Always save location/field values — don't guard on isVisible()
        # since Qt visibility can be unreliable during dialog init.
        # Empty string means "not set".
        loc_from = self._loc_from_cb.selected_value()
        loc_to   = self._loc_to_cb.selected_value()
        profit   = self._profit.text().strip()
        outcome  = self._outcome_cb.currentText()  if self._outcome_cb.currentIndex()  >= 0 else ""
        system   = self._system.text().strip()

        return {
            "entry_type":    t,
            "log_datetime":  log_dt,
            "title":         self._title.text().strip(),
            "ship":          self._ship_cb.currentText() if self._ship_cb.currentIndex() > 0 else "",
            "notes":         self._notes.toPlainText().strip(),
            "location_from": loc_from,
            "location_to":   loc_to,
            "profit":        profit,
            "outcome":       outcome,
            "system":        system,
        }


class LogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # ── Header ────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Captain's Log")
        title.setObjectName("section-title")
        self._count_lbl = QLabel("")
        self._count_lbl.setObjectName("muted")

        self._filter_cb = QComboBox()
        self._filter_cb.addItem("All Types")
        self._filter_cb.addItems(ENTRY_TYPES)
        self._filter_cb.currentTextChanged.connect(self._apply_filter)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search log…")
        self._search.setFixedWidth(180)
        self._search.textChanged.connect(self._apply_filter)

        new_btn = QPushButton("＋  New Entry")
        new_btn.setObjectName("primary")
        new_btn.clicked.connect(self._new_entry)

        header.addWidget(title)
        header.addWidget(self._count_lbl)
        header.addStretch()
        header.addWidget(QLabel("Filter:"))
        header.addWidget(self._filter_cb)
        header.addWidget(self._search)
        header.addWidget(new_btn)
        root.addLayout(header)

        # ── Splitter ───────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Vertical)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Log Date / Time", "Type", "Title", "Ship", "Location", "Outcome", ""
        ])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.selectionModel().selectionChanged.connect(self._on_select)
        splitter.addWidget(self._table)

        self._detail = QFrame()
        self._detail.setObjectName("card")
        self._detail.setFrameShape(QFrame.Shape.StyledPanel)
        self._detail.setVisible(False)
        self._detail_vl = QVBoxLayout(self._detail)
        self._detail_vl.setContentsMargins(18, 14, 18, 14)
        self._detail_vl.setSpacing(8)
        splitter.addWidget(self._detail)
        splitter.setSizes([460, 200])

        root.addWidget(splitter)
        self._load()

    def _load(self):
        self._all_entries = load_log()
        self._apply_filter()

    def _apply_filter(self):
        f_type  = self._filter_cb.currentText()
        search  = self._search.text().lower()
        entries = [
            e for e in self._all_entries
            if (f_type == "All Types" or e.get("entry_type") == f_type)
            and (not search
                 or search in e.get("title", "").lower()
                 or search in e.get("notes", "").lower()
                 or search in e.get("ship", "").lower())
        ]
        self._populate(entries)

    def _populate(self, entries):
        self._table.setRowCount(len(entries))
        self._count_lbl.setText(f"{len(self._all_entries)} entries")

        for row, e in enumerate(entries):
            etype = e.get("entry_type", "General / Personal Log")
            color = ENTRY_COLORS.get(etype, "#b0d4e8")

            # Show user-set log datetime, fall back to creation timestamp
            display_dt = _fmt_ts(e.get("log_datetime", e.get("timestamp", "")))

            loc_from = e.get("location_from", "")
            loc_to   = e.get("location_to", "")
            if loc_from and loc_to:
                loc_str = f"{loc_from} → {loc_to}"
            elif loc_from:
                loc_str = f"↑ {loc_from}"
            elif loc_to:
                loc_str = f"↓ {loc_to}"
            else:
                loc_str = e.get("system", "—")

            self._table.setItem(row, 0, _item(display_dt, "#3d6b88"))
            self._table.setItem(row, 1, _item(etype, color, bold=True))
            self._table.setItem(row, 2, _item(e.get("title", ""), "#e8f4ff", bold=True))
            self._table.setItem(row, 3, _item(e.get("ship", "—"), "#6a9ab8"))
            self._table.setItem(row, 4, _item(loc_str, "#b0d4e8"))
            self._table.setItem(row, 5, _item(e.get("outcome", "—"), "#b0d4e8"))

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(4, 2, 4, 2)
            btn_l.setSpacing(4)
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(48)
            edit_btn.clicked.connect(lambda _, eid=e["id"]: self._edit_entry(eid))
            del_btn = QPushButton("✕")
            del_btn.setObjectName("danger")
            del_btn.setFixedWidth(28)
            del_btn.clicked.connect(lambda _, eid=e["id"]: self._delete_entry(eid))
            btn_l.addWidget(edit_btn)
            btn_l.addWidget(del_btn)
            self._table.setCellWidget(row, 6, btn_w)
            self._table.setRowHeight(row, 36)
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, e)

        self._detail.setVisible(False)

    def _on_select(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            self._detail.setVisible(False)
            return
        entry = self._table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if entry:
            self._show_detail(entry)

    def _show_detail(self, e):
        while self._detail_vl.count():
            item = self._detail_vl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        etype = e.get("entry_type", "")
        color = ENTRY_COLORS.get(etype, "#b0d4e8")

        # Header
        hrow = QHBoxLayout()
        type_lbl  = QLabel(etype)
        type_lbl.setStyleSheet(f"color:{color}; font-weight:700; font-size:11px; font-family:monospace; letter-spacing:1px")
        title_lbl = QLabel(e.get("title", ""))
        title_lbl.setStyleSheet("color:#e8f4ff; font-size:14px; font-weight:700")

        # Show user log datetime prominently, plus created timestamp if different
        log_dt  = _fmt_ts(e.get("log_datetime", e.get("timestamp", "")))
        created = _fmt_ts(e.get("timestamp", ""))
        dt_text = log_dt
        if e.get("log_datetime") and e.get("timestamp") and log_dt != created:
            dt_text = f"{log_dt}  (recorded {created})"
        ts_lbl = QLabel(dt_text)
        ts_lbl.setStyleSheet("color:#3d6b88; font-family:monospace; font-size:11px")
        ts_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        hrow.addWidget(type_lbl)
        hrow.addSpacing(14)
        hrow.addWidget(title_lbl)
        hrow.addStretch()
        hrow.addWidget(ts_lbl)
        self._detail_vl.addLayout(hrow)

        # Meta
        meta_parts = []
        if e.get("ship"):          meta_parts.append(f"🚀 {e['ship']}")
        if e.get("location_from") and e.get("location_to"):
            meta_parts.append(f"📍 {e['location_from']} → {e['location_to']}")
        elif e.get("location_from"): meta_parts.append(f"📍 From: {e['location_from']}")
        elif e.get("location_to"):   meta_parts.append(f"📍 To: {e['location_to']}")
        if e.get("system"):        meta_parts.append(f"🌌 {e['system']}")
        if e.get("outcome"):       meta_parts.append(f"⚡ {e['outcome']}")
        if e.get("profit"):
            try:    meta_parts.append(f"💰 {int(e['profit']):,} aUEC")
            except: meta_parts.append(f"💰 {e['profit']} aUEC")

        if meta_parts:
            meta_lbl = QLabel("   ·   ".join(meta_parts))
            meta_lbl.setStyleSheet("color:#6a9ab8; font-size:11px")
            meta_lbl.setWordWrap(True)
            self._detail_vl.addWidget(meta_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#1a3048; margin:2px 0")
        self._detail_vl.addWidget(line)

        notes = e.get("notes", "").strip()
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setWordWrap(True)
            notes_lbl.setStyleSheet("color:#b0d4e8; font-size:12px")
            notes_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._detail_vl.addWidget(notes_lbl)
        else:
            self._detail_vl.addWidget(QLabel("No notes recorded.") )

        if e.get("edited"):
            edited_lbl = QLabel(f"Edited: {_fmt_ts(e['edited'])}")
            edited_lbl.setStyleSheet("color:#3d6b88; font-size:10px; font-style:italic")
            self._detail_vl.addWidget(edited_lbl)

        self._detail_vl.addStretch()
        self._detail.setVisible(True)

    def _new_entry(self):
        dlg = LogEntryDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            add_entry(dlg.get_entry())
            self._load()

    def _edit_entry(self, entry_id: str):
        entry = next((e for e in self._all_entries if e.get("id") == entry_id), None)
        if not entry:
            return
        dlg = LogEntryDialog(self, entry)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            update_entry(entry_id, dlg.get_entry())
            self._load()

    def _delete_entry(self, entry_id: str):
        entry = next((e for e in self._all_entries if e.get("id") == entry_id), None)
        title = entry.get("title", "this entry") if entry else "this entry"
        reply = QMessageBox.question(
            self, "Delete Entry", f"Delete \"{title}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_entry(entry_id)
            self._load()

    def refresh(self):
        self._load()
