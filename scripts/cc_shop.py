"""
Fetch today's Fortnite item shop and normalize it into a stable internal shape.

Upstream (fortnite-api.com) has changed its response shape between versions — older builds
returned `data.featured`/`data.daily` sections, current ones return a flat `data.entries` list.
The normalizer below accepts either, so an upstream change degrades into fewer items rather
than a crashed cron job.

Usage:
    python3 scripts/cc_shop.py                 # fetch live, write creator-code/out/<date>/shop.json
    python3 scripts/cc_shop.py --fixture       # use the bundled sample (no network, no API key)
"""

import sys

from cc_common import (CC_DIR, OUT_DIR, log, load_config, http_get_json, write_json,
                       read_json, today_stamp)

SHOP_URL = "https://fortnite-api.com/v2/shop"
FIXTURE = CC_DIR / "fixtures" / "shop_sample.json"

# Rarities worth leading with — these are what people actually search for and buy.
HEADLINE_RARITIES = {"legendary", "epic", "marvel", "dc", "icon", "gaminglegends", "starwars"}


def fetch_shop(cfg: dict) -> dict:
    """Fetch the raw shop payload. API key is free (no credit card) from dash.fortnite-api.com."""
    key = cfg.get("fortnite_api_key", "")
    headers = {"Accept": "application/json"}
    if key and not key.startswith("PASTE_"):
        headers["Authorization"] = key
        headers["x-api-key"] = key
    log(f"Fetching {SHOP_URL}")
    return http_get_json(SHOP_URL, headers=headers)


def _iter_raw_entries(data: dict):
    """Yield entries from whichever shape upstream gave us."""
    if isinstance(data.get("entries"), list):
        yield from data["entries"]
        return
    # Legacy shape: data.featured.entries / data.daily.entries
    for section in ("featured", "daily", "specialFeatured", "specialDaily"):
        node = data.get(section)
        if isinstance(node, dict) and isinstance(node.get("entries"), list):
            yield from node["entries"]


def _best_image(item: dict) -> str:
    images = item.get("images") or {}
    for key in ("featured", "icon", "smallIcon"):
        if images.get(key):
            return images[key]
    return ""


def normalize(payload: dict) -> dict:
    """Flatten the upstream payload into the shape the rest of the pipeline relies on."""
    data = payload.get("data") or {}
    items, seen = [], set()

    for entry in _iter_raw_entries(data):
        price = entry.get("finalPrice") or entry.get("regularPrice") or 0
        regular = entry.get("regularPrice") or price
        # An entry can bundle several cosmetics; surface each so per-item pages have content.
        br_items = entry.get("brItems") or entry.get("items") or []
        for item in br_items:
            name = (item.get("name") or "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            rarity = ((item.get("rarity") or {}).get("value") or "common").lower()
            items.append({
                "name": name,
                "description": (item.get("description") or "").strip(),
                "type": ((item.get("type") or {}).get("displayValue") or "Item"),
                "rarity": rarity,
                "rarity_label": ((item.get("rarity") or {}).get("displayValue") or "Common"),
                "price": price,
                "regular_price": regular,
                "discounted": bool(regular and price and price < regular),
                "image": _best_image(item),
            })

    # Headline items first (rarity, then price) — these drive the thumbnail and the title.
    items.sort(key=lambda i: (i["rarity"] not in HEADLINE_RARITIES, -i["price"]))

    return {
        "date": data.get("date") or today_stamp(),
        "fetched": today_stamp(),
        "hash": data.get("hash", ""),
        "item_count": len(items),
        "items": items,
    }


def main():
    use_fixture = "--fixture" in sys.argv
    cfg = load_config() if not use_fixture else {}

    if use_fixture:
        log(f"Using fixture {FIXTURE}")
        payload = read_json(FIXTURE)
        if payload is None:
            log("ERROR: fixture missing.")
            sys.exit(1)
    else:
        try:
            payload = fetch_shop(cfg)
        except Exception as e:  # noqa: BLE001
            log(f"ERROR: shop fetch failed: {e}")
            log("Check your free API key at https://dash.fortnite-api.com/")
            sys.exit(1)

    shop = normalize(payload)
    if not shop["items"]:
        log("ERROR: normalized shop is empty — upstream shape may have changed again.")
        sys.exit(1)

    out = write_json(OUT_DIR / shop["fetched"] / "shop.json", shop)
    log(f"Wrote {shop['item_count']} items -> {out}")
    top = ", ".join(i["name"] for i in shop["items"][:5])
    log(f"Headline items: {top}")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    main()
