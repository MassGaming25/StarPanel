#!/usr/bin/env python3
"""StarPanel — Star Citizen Companion App"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.mainwindow import MainWindow
from core.version import APP_VERSION


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StarPanel")
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("StarPanel")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
