"""SC Companion colour palette and stylesheet."""

DARK_PALETTE = """
QMainWindow, QWidget {
    background-color: #070e17;
    color: #b0d4e8;
    font-family: "Exo 2", "Segoe UI", sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #1a3048;
    background-color: #0d1825;
}

QTabBar::tab {
    background: #080e16;
    color: #3d6b88;
    padding: 10px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-size: 11px;
}

QTabBar::tab:selected {
    color: #00e5ff;
    border-bottom: 2px solid #00e5ff;
    background: #0d1825;
}

QTabBar::tab:hover:!selected {
    color: #b0d4e8;
    background: #0a1520;
}

QTableWidget {
    background-color: #0d1825;
    alternate-background-color: #0a1520;
    border: 1px solid #1a3048;
    gridline-color: #111f2e;
    color: #b0d4e8;
    selection-background-color: #0d2d45;
    selection-color: #00e5ff;
}

QTableWidget::item {
    padding: 6px 10px;
    border: none;
}

QHeaderView::section {
    background-color: #080e16;
    color: #3d6b88;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #1a3048;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}

QLineEdit, QComboBox {
    background-color: #0c1520;
    border: 1px solid #1a3048;
    border-radius: 3px;
    padding: 6px 10px;
    color: #b0d4e8;
    selection-background-color: #1a3048;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #00b8d9;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}

QComboBox QAbstractItemView {
    background-color: #0c1520;
    border: 1px solid #1a3048;
    color: #b0d4e8;
    selection-background-color: #1a3048;
}

QPushButton {
    background-color: #0c1520;
    border: 1px solid #1a3048;
    border-radius: 3px;
    padding: 7px 16px;
    color: #b0d4e8;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-size: 11px;
}

QPushButton:hover {
    border-color: #00b8d9;
    color: #00e5ff;
    background-color: #0d1e2e;
}

QPushButton:pressed {
    background-color: #0a2030;
}

QPushButton#primary {
    background-color: rgba(0,184,217,0.15);
    border-color: #00b8d9;
    color: #00e5ff;
}

QPushButton#primary:hover {
    background-color: rgba(0,184,217,0.25);
}

QPushButton#danger {
    border-color: #e53935;
    color: #e53935;
}

QPushButton#danger:hover {
    background-color: rgba(229,57,53,0.12);
}

QScrollBar:vertical {
    background: #080e16;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background: #1a3048;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover { background: #00b8d9; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal {
    background: #080e16;
    height: 8px;
    border: none;
}

QScrollBar::handle:horizontal {
    background: #1a3048;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover { background: #00b8d9; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

QLabel#section-title {
    color: #e8f4ff;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 4px 0;
    border-left: 3px solid #00b8d9;
    padding-left: 10px;
}

QLabel#stat-value {
    color: #e8f4ff;
    font-size: 22px;
    font-weight: 700;
}

QLabel#stat-label {
    color: #3d6b88;
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

QLabel#accent { color: #00e5ff; }
QLabel#gold   { color: #f0a800; }
QLabel#green  { color: #00e676; }
QLabel#muted  { color: #3d6b88; font-style: italic; }

QFrame#card {
    background-color: #0d1825;
    border: 1px solid #1a3048;
    border-radius: 4px;
}

QFrame#card-accent {
    background-color: #0d1825;
    border: 1px solid #1a3048;
    border-left: 3px solid #00b8d9;
    border-radius: 2px;
}

QStatusBar {
    background: #060d15;
    color: #3d6b88;
    border-top: 1px solid #1a3048;
    font-size: 11px;
}

QSplitter::handle {
    background: #1a3048;
}

QToolTip {
    background-color: #0d1825;
    color: #b0d4e8;
    border: 1px solid #1a3048;
    padding: 4px 8px;
}

QDialog {
    background-color: #0d1825;
}

QMessageBox {
    background-color: #0d1825;
    color: #b0d4e8;
}
"""
