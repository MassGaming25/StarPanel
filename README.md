# SC Companion — Star Citizen Desktop App

A native PyQt6 desktop app for Fedora Linux.
Ships, commodities with best buy/sell locations, trade routes, and fleet manager.

---

## Quickest way to run (no Flatpak needed)

Install PyQt6 and run directly:

```bash
sudo dnf install python3-pyqt6
cd sc-companion-flatpak
python3 src/main.py
```

That's it. Your fleet data is saved to `~/.local/share/sc-companion/fleet.json`.

---

## Run as Flatpak (proper desktop integration)

### 1. Install Flatpak tools

```bash
sudo dnf install flatpak flatpak-builder
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08
```

### 2. Install PyQt6 into the Flatpak build

```bash
pip3 install flatpak-pip-generator
flatpak-pip-generator PyQt6 --output flatpak/pyqt6-deps
```

### 3. Build and install

```bash
cd flatpak
flatpak-builder --user --install --force-clean build-dir io.github.sccompanion.yml
```

### 4. Run

```bash
flatpak run io.github.sccompanion
```

Or find **SC Companion** in your GNOME app grid.

### Uninstall

```bash
flatpak uninstall io.github.sccompanion
```

---

## Project structure

```
sc-companion-flatpak/
├── src/
│   ├── main.py                  ← Entry point
│   ├── ui/
│   │   ├── mainwindow.py        ← Main window
│   │   ├── overview_tab.py      ← Dashboard
│   │   ├── ships_tab.py         ← Ship browser
│   │   ├── commodities_tab.py   ← Market + trade routes
│   │   ├── fleet_tab.py         ← Fleet manager
│   │   └── theme.py             ← Dark stylesheet
│   └── core/
│       ├── data.py              ← Ships, commodities, locations
│       └── fleet.py             ← Fleet persistence
├── flatpak/
│   └── io.github.sccompanion.yml  ← Flatpak manifest
├── io.github.sccompanion.desktop
└── io.github.sccompanion.metainfo.xml
```

---

## Features

- **Overview** — Fleet summary and top trade routes at a glance
- **Ships** — Browse all ships, filter by manufacturer/role/size/status, click for detail
- **Commodities**
  - *Market Overview* — Best buy/sell price per commodity with profit per SCU
  - *Best Locations* — Single best place to buy and sell each item
  - *Trade Routes* — All routes ranked by profit, filterable and sortable
- **Fleet** — Add/edit/remove ships, track status, insurance, loadout notes
