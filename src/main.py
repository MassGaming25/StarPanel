#!/usr/bin/env python3
"""SC Companion — Star Citizen Desktop App (PyQt6)"""

import sys
import os

# Allow running both as flatpak and directly
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.mainwindow import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StarPanel")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("StarPanel")

    # Dark style base
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
