"""
Ship image cache.

Priority order:
  1. In-memory cache (instant)
  2. Stored image_url from Fleetyards or RSI normaliser
  3. RSI media CDN fallback by ship name slug
"""

import urllib.request
import urllib.parse
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap

# In-memory cache: url → QPixmap
_cache: dict[str, QPixmap] = {}

# RSI CDN base for ship images
RSI_MEDIA_BASE = "https://robertsspaceindustries.com"


def get_cached(url: str) -> QPixmap | None:
    return _cache.get(url)


def _ship_name_to_rsi_slug(name: str) -> str:
    """Convert 'Cutlass Black' → 'cutlass-black' for RSI URL construction."""
    return name.lower().strip().replace(" ", "-").replace("'", "").replace(".", "")


class ImageFetcher(QThread):
    """
    Fetch a ship image in the background.
    Tries the stored URL first; falls back to RSI CDN by slug if that fails.
    """
    image_ready = pyqtSignal(str, QPixmap)  # (original_url_or_name, pixmap)
    failed      = pyqtSignal(str)

    def __init__(self, url: str, ship_name: str = "", parent: QObject = None):
        super().__init__(parent)
        self._url       = url
        self._ship_name = ship_name

    def run(self):
        # 1. Check memory cache first
        if self._url and self._url in _cache:
            self.image_ready.emit(self._url, _cache[self._url])
            return

        # 2. Try the stored URL
        if self._url:
            px = self._fetch(self._url)
            if px:
                _cache[self._url] = px
                self.image_ready.emit(self._url, px)
                return

        # 3. Fallback: try RSI's ship page thumbnail
        if self._ship_name:
            slug = _ship_name_to_rsi_slug(self._ship_name)
            fallback_urls = [
                f"https://robertsspaceindustries.com/media/b9ka4ohfxyb1kr/store_hub_large/{slug}.jpg",
                f"https://robertsspaceindustries.com/media/b9ka4ohfxyb1kr/product_thumb_large/{slug}.jpg",
            ]
            for url in fallback_urls:
                px = self._fetch(url)
                if px:
                    _cache[self._url or self._ship_name] = px
                    self.image_ready.emit(self._url or self._ship_name, px)
                    return

        self.failed.emit(self._url or self._ship_name)

    def _fetch(self, url: str) -> QPixmap | None:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "StarPanel/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
            px = QPixmap()
            if px.loadFromData(data) and not px.isNull():
                return px
        except Exception:
            pass
        return None
