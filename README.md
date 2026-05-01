# StarPanel — Star Citizen Companion App

A native Linux desktop companion for Star Citizen.
Ships, commodity prices, trade routes, fleet manager, and Captain's Log.

---

## Install (from a release)

```bash
# Download latest release
wget https://github.com/YOUR-USERNAME/starpanel/releases/latest/download/starpanel-VERSION.tar.gz

# Extract
tar -xzf starpanel-VERSION.tar.gz
cd starpanel-VERSION

# Install
./install.sh
```

The installer will:
- Install PyQt6 and dependencies if missing
- Copy the app to `~/.local/share/starpanel/`
- Create a `starpanel` launcher in `~/.local/bin/`
- Install a `.desktop` shortcut so StarPanel appears in your app menu

---

## Run

```bash
starpanel
# or find StarPanel in your GNOME app grid
```

---

## Setting up your own GitHub repo

1. Create a repo named `starpanel` on GitHub
2. Edit `src/core/version.py` and set your GitHub username:
   ```python
   GITHUB_OWNER = "your-github-username"
   ```
3. Push the code:
   ```bash
   git init
   git add .
   git commit -m "Initial release"
   git remote add origin https://github.com/YOUR-USERNAME/starpanel.git
   git push -u origin main
   ```

## Publishing a release

```bash
# Bump version in src/core/version.py first, then:
git add src/core/version.py CHANGELOG.md
git commit -m "Release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

The GitHub Actions workflow (`.github/workflows/release.yml`) will automatically:
- Build the release zip and tar.gz
- Create a GitHub Release with the files attached
- Users running StarPanel will see an update notification on next startup

---

## Data sources

| Data | Source | Fallback |
|------|--------|---------|
| Ships | Fleetyards API | RSI Ship Matrix |
| Commodities | UEX Corp API | Static data |
| Prices | UEX Corp API | Static data |
| Locations | UEX Corp API | Static data |

---

## Requirements

- Fedora / Linux
- Python 3.10+
- PyQt6 (`sudo dnf install python3-pyqt6`)
