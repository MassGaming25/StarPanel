#!/usr/bin/env bash
# StarPanel — Install / Update script
# Run this once after extracting a release, or to update to a new version.
# Works on Fedora and any other Linux with Python 3.10+.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/starpanel"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║     StarPanel  —  Installer      ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# ── Check Python ──────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] Python 3 not found."
    echo "          Install with: sudo dnf install python3"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  [OK]   Python $PY_VER found"

# ── Check PyQt6 ───────────────────────────────────────────────────
if ! python3 -c "import PyQt6" &>/dev/null; then
    echo "  [SETUP] Installing PyQt6…"
    if command -v dnf &>/dev/null; then
        sudo dnf install -y python3-pyqt6 python3-pyqt6-devel 2>/dev/null \
            || pip3 install --user PyQt6
    else
        pip3 install --user PyQt6
    fi
fi
echo "  [OK]   PyQt6 found"

# ── Check packaging (for version comparison) ──────────────────────
if ! python3 -c "import packaging" &>/dev/null; then
    echo "  [SETUP] Installing packaging…"
    pip3 install --user packaging
fi
echo "  [OK]   packaging found"

# ── Copy app files ────────────────────────────────────────────────
echo "  [INSTALL] Copying app to $INSTALL_DIR…"
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/src/"* "$INSTALL_DIR/"

# ── Create launcher script ────────────────────────────────────────
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/starpanel" << LAUNCHER
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/main.py" "\$@"
LAUNCHER
chmod +x "$BIN_DIR/starpanel"
echo "  [OK]   Launcher: $BIN_DIR/starpanel"

# ── Install icon ──────────────────────────────────────────────────
mkdir -p "$ICON_DIR"
if [ -f "$SCRIPT_DIR/assets/starpanel.png" ]; then
    cp "$SCRIPT_DIR/assets/starpanel.png" "$ICON_DIR/starpanel.png"
    echo "  [OK]   Icon installed"
fi

# ── Install .desktop file ─────────────────────────────────────────
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/starpanel.desktop" << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=StarPanel
GenericName=Star Citizen Companion
Comment=Ship database, commodities, trade routes and Captain's Log
Exec=$BIN_DIR/starpanel
Icon=starpanel
Terminal=false
Categories=Game;Utility;
Keywords=star;citizen;space;trading;ships;starpanel;
StartupWMClass=StarPanel
DESKTOP

# Make it trusted on GNOME
chmod +x "$DESKTOP_DIR/starpanel.desktop"
if command -v gio &>/dev/null; then
    gio set "$DESKTOP_DIR/starpanel.desktop" \
        metadata::trusted true 2>/dev/null || true
fi

# Refresh desktop database
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi
echo "  [OK]   Desktop shortcut installed"

# ── Add ~/.local/bin to PATH if needed ───────────────────────────
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "  [NOTE] Add this to your ~/.bashrc or ~/.profile:"
    echo "         export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "  ✓  StarPanel installed successfully!"
echo "     Run: starpanel"
echo "     Or find StarPanel in your app menu."
echo ""
