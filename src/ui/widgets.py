"""Reusable widgets for StarPanel."""

from PyQt6.QtWidgets import QComboBox, QCompleter
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtGui import QStandardItemModel, QStandardItem


class SearchableComboBox(QComboBox):
    """
    Combobox with live contains-filter search.
    Type any part of a name to narrow the list; the dropdown
    opens automatically via the completer without interrupting typing.
    Click the arrow to see the full list.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setMaxVisibleItems(20)

        # Source model holds all items
        self._model = QStandardItemModel(self)
        self.setModel(self._model)

        # Proxy filters the completer popup
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(0)

        # Completer drives the popup — UnfilteredPopupCompletion shows
        # all proxy-visible rows without Qt doing a second filter pass
        completer = QCompleter(self._proxy, self)
        completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompleter(completer)

        # Update proxy filter as user types — do NOT call showPopup() here
        self.lineEdit().textEdited.connect(self._filter)

        self.setStyleSheet("""
            QComboBox {
                background: #0c1520;
                border: 1px solid #1a3048;
                border-radius: 3px;
                padding: 5px 10px;
                color: #b0d4e8;
                min-width: 220px;
            }
            QComboBox:focus { border-color: #00b8d9; }
            QComboBox QAbstractItemView {
                background: #0c1520;
                border: 1px solid #1a3048;
                color: #b0d4e8;
                selection-background-color: #1a3048;
                selection-color: #00e5ff;
            }
            QComboBox::drop-down { border: none; width: 20px; }
        """)

    def _filter(self, text: str):
        """Update proxy filter. The completer handles its own popup."""
        self._proxy.setFilterFixedString(text)

    def populate(self, items: list, placeholder: str = "— None —"):
        """Load all items. Clears any active filter."""
        current = self.currentText()
        self._model.clear()
        self._model.appendRow(QStandardItem(placeholder))
        for item in items:
            self._model.appendRow(QStandardItem(item))
        self._proxy.setFilterFixedString("")
        idx = self.findText(current, Qt.MatchFlag.MatchFixedString)
        self.setCurrentIndex(idx if idx >= 0 else 0)

    def selected_value(self) -> str:
        """Return selected value, or empty string if placeholder."""
        txt = self.currentText().strip()
        return "" if (not txt or txt.startswith("—")) else txt

    def set_value(self, value: str):
        """Set by text value; adds temporarily if not in list."""
        if not value:
            self.setCurrentIndex(0)
            return
        self._proxy.setFilterFixedString("")
        idx = self.findText(value, Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            self.setCurrentIndex(idx)
        else:
            self._model.appendRow(QStandardItem(value))
            self.setCurrentIndex(self._model.rowCount() - 1)
