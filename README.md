# StarPanel — Star Citizen Companion App

A native desktop companion for Star Citizen built with Python and PyQt6.
Runs on **Fedora / Linux** and **Windows**.

**GitHub:** https://github.com/MassGaming25/StarPanel

---

## Features

| Tab | What it does |
|-----|-------------|
| **Overview** | Fleet summary, top trade routes, SC version tracker (Live / PTU / Evocati) |
| **Ships** | Full ship database from RSI Ship Matrix — filter by manufacturer, role, size, status |
| **Commodities** | Live prices from UEX Corp — best buy/sell locations and ranked trade routes |
| **Fleet** | Track your ships with status, insurance, purchase type, loadout notes and ship images |
| **Captain's Log** | 8 entry types — trade runs, combat, exploration, missions, departures, arrivals and more |

---

## Data Sources

| Data | Primary | Fallback |
|------|---------|---------|
| Ships | Fleetyards API | RSI Ship Matrix |
| Commodities & Prices | UEX Corp API | Static built-in data |
| Trade Locations | UEX Corp terminals | Static built-in data |
| SC Live Version | UEX header | — |
| SC PTU / Evocati | RSI PTU FAQ page | — |
| Ship Images | Fleetyards / RSI CDN | — |

All API data fetches in background threads — the app opens instantly with static data and updates silently.

---

## Requirements

### Fedora / Linux
```bash
sudo dnf install python3-pyqt6
```

### Windows
- Python 3.10+ from https://python.org — check **"Add Python to PATH"** during install
- PyQt6 is installed automatically by `install.bat`

---

## Install

Download the latest release from:
**https://github.com/MassGaming25/StarPanel/releases**

### Fedora / Linux
```bash
tar -xzf starpanel-VERSION.tar.gz
cd starpanel-VERSION
./install.sh
```

### Windows
```
Extract starpanel-VERSION.zip
Double-click install.bat
```

Both installers:
- Check / install PyQt6 if missing
- Copy the app to the correct location
- Create a launcher and desktop/Start Menu shortcut

---

## Run

| Platform | Command |
|----------|---------|
| Linux | `starpanel` or `python3 src/main.py` |
| Windows | Start Menu → StarPanel, or `python src\main.py` |

---

## User Data

| Platform | Location |
|----------|---------|
| Linux | `~/.local/share/starpanel/` |
| Windows | `%APPDATA%\StarPanel\` |

User data (fleet, logs, overrides) is **never included in releases**.

---

## Auto-Updates

StarPanel checks for updates on startup. If a newer version is found a dialog
appears with release notes and an **Update Now** button that downloads, installs,
and restarts automatically.

---

## Publishing a Release

```bash
# 1. Bump APP_VERSION in src/core/version.py
# 2. Update CHANGELOG.md
git add src/core/version.py CHANGELOG.md
git commit -m "Release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

GitHub Actions builds and publishes the release zip automatically.

---

## Project Structure

```
StarPanel/
├── src/
│   ├── main.py                  ← Entry point (Linux + Windows)
│   ├── starpanel.png            ← App icon
│   ├── ui/                      ← All UI tabs and widgets
│   └── core/                    ← Data, API, storage, update logic
├── assets/                      ← Icons (64, 128, 256px)
├── flatpak/                     ← Flatpak manifest (Linux only)
├── .github/workflows/           ← GitHub Actions release workflow
├── install.sh                   ← Linux installer
├── install.bat                  ← Windows installer
├── CHANGELOG.md
└── README.md
```

---

## Linux — Flatpak

```bash
sudo dnf install flatpak flatpak-builder
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08
cd flatpak
flatpak-builder --user --install --force-clean build-dir io.github.starpanel.yml
flatpak run io.github.starpanel
```
