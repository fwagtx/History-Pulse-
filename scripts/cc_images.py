"""
Download and cache Fortnite cosmetic images, and embed them into HTML.

Images are fetched once and kept in creator-code/out/_imgcache/ so a re-render
costs nothing and a shop that repeats items doesn't re-download them.

They're embedded as base64 data URIs rather than linked by URL, so the rendered
card needs no network at screenshot time — which makes the render reproducible
and stops a slow CDN from producing a half-empty card.
"""

import base64
import hashlib
import mimetypes
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

from cc_common import OUT_DIR, log

CACHE = OUT_DIR / "_imgcache"
TIMEOUT = 20
# Be a polite client; some CDNs reject the default urllib agent.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BADShopCard/1.0)"}


def _cache_path(url: str) -> Path:
    key = hashlib.sha1(url.encode("utf-8")).hexdigest()[:20]
    ext = Path(urllib.parse.urlparse(url).path).suffix or ".png"
    return CACHE / f"{key}{ext}"


def fetch(url: str) -> Path | None:
    """Return a local path for this image URL, downloading if needed."""
    if not url:
        return None
    path = _cache_path(url)
    if path.exists() and path.stat().st_size > 0:
        return path
    CACHE.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
        if not data:
            return None
        path.write_bytes(data)
        return path
    except (urllib.error.URLError, OSError, ValueError) as e:
        log(f"  image failed ({url[:60]}...): {e}")
        return None


def data_uri(path: Path | None) -> str:
    """base64 data URI for embedding, or '' if unavailable."""
    if not path or not path.exists():
        return ""
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def fetch_all(items: list, limit: int) -> dict:
    """{item name: data URI} for the first `limit` items. Missing images are
    simply absent, and the card falls back to a rarity tile for those."""
    out, got = {}, 0
    for item in items[:limit]:
        uri = data_uri(fetch(item.get("image") or ""))
        if uri:
            out[item["name"]] = uri
            got += 1
    log(f"Item images: {got}/{min(limit, len(items))} fetched")
    return out
