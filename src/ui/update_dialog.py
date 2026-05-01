"""Update available / progress dialog."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from core.version import APP_VERSION


class UpdateDialog(QDialog):
    def __init__(self, latest_version: str, release_url: str,
                 release_notes: str, asset_url: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setMinimumWidth(500)
        self._release_url  = release_url
        self._asset_url    = asset_url
        self._latest       = latest_version
        self._build(latest_version, release_notes)

    def _build(self, latest: str, notes: str):
        vl = QVBoxLayout(self)
        vl.setSpacing(14)
        vl.setContentsMargins(24, 20, 24, 20)

        # Header
        title = QLabel("⬆  New Version Available")
        title.setStyleSheet(
            "color:#00e5ff; font-size:15px; font-weight:700; letter-spacing:1px")
        vl.addWidget(title)

        # Version row
        ver_row = QHBoxLayout()
        cur_lbl = QLabel(f"Installed:  {APP_VERSION}")
        cur_lbl.setStyleSheet("color:#6a9ab8; font-family:monospace; font-size:12px")
        new_lbl = QLabel(f"Available:  {latest}")
        new_lbl.setStyleSheet(
            "color:#00e676; font-family:monospace; font-size:12px; font-weight:700")
        ver_row.addWidget(cur_lbl)
        ver_row.addSpacing(24)
        ver_row.addWidget(new_lbl)
        ver_row.addStretch()
        vl.addLayout(ver_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#1a3048")
        vl.addWidget(sep)

        # Release notes
        if notes.strip():
            notes_lbl = QLabel("Release notes:")
            notes_lbl.setStyleSheet(
                "color:#3d6b88; font-size:10px; letter-spacing:1px; text-transform:uppercase")
            vl.addWidget(notes_lbl)
            notes_box = QTextEdit()
            notes_box.setPlainText(notes.strip())
            notes_box.setReadOnly(True)
            notes_box.setFixedHeight(110)
            notes_box.setStyleSheet(
                "background:#060d15; border:1px solid #1a3048; "
                "color:#b0d4e8; font-size:11px; padding:6px")
            vl.addWidget(notes_box)

        # Progress bar (hidden until update starts)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)   # indeterminate
        self._progress_bar.setVisible(False)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background: #0c1520; border: 1px solid #1a3048;
                border-radius: 3px; height: 6px; text-align: center;
            }
            QProgressBar::chunk { background: #00b8d9; border-radius: 3px; }
        """)
        vl.addWidget(self._progress_bar)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color:#6a9ab8; font-size:11px")
        self._status_lbl.setVisible(False)
        vl.addWidget(self._status_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._skip_btn = QPushButton("Remind Me Later")
        self._skip_btn.clicked.connect(self.reject)

        self._browser_btn = QPushButton("Open Release Page")
        self._browser_btn.clicked.connect(self._open_browser)

        self._update_btn = QPushButton("⬇  Update Now")
        self._update_btn.setObjectName("primary")
        self._update_btn.clicked.connect(self._start_update)

        # Only show "Update Now" if we have a direct download URL
        if not self._asset_url:
            self._update_btn.setVisible(False)

        btn_row.addWidget(self._skip_btn)
        btn_row.addWidget(self._browser_btn)
        btn_row.addWidget(self._update_btn)
        vl.addLayout(btn_row)

    def _open_browser(self):
        QDesktopServices.openUrl(QUrl(self._release_url))

    def _start_update(self):
        from core.updater import AppUpdater, relaunch

        self._update_btn.setEnabled(False)
        self._skip_btn.setEnabled(False)
        self._browser_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._status_lbl.setVisible(True)
        self._status_lbl.setText("Starting download…")

        self._worker = AppUpdater(self._asset_url, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_success)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, msg: str):
        self._status_lbl.setText(msg)

    def _on_success(self):
        from core.updater import relaunch
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(1)
        self._status_lbl.setText("✓  Update installed — restarting now…")
        # Short delay so user can read the message, then relaunch
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, relaunch)

    def _on_failed(self, error: str):
        self._progress_bar.setVisible(False)
        self._status_lbl.setText(f"✗  Update failed: {error}")
        self._status_lbl.setStyleSheet("color:#e53935; font-size:11px")
        self._skip_btn.setEnabled(True)
        self._browser_btn.setEnabled(True)
        # Offer manual download as fallback
        self._update_btn.setText("Try Again")
        self._update_btn.setEnabled(True)
