"""
Fetch today's Fortnite item shop and normalize it into a stable internal shape.

Upstream (fortnite-api.com) has changed its response shape between versions — older builds
returned `data.featured`/`data.daily` sections, current ones return a flat `data.entries` list.
The normalizer below accepts either, so an upstream change degrades into fewer items rather
than a crashed cron job.

Usage:
    python3 scripts/cc_shop.py                 # fetch live (no API key needed)
    python3 scripts/cc_shop.py --fixture       # use the bundled sample (no network, no API key)
"""

import sys

from cc_common import (CC_DIR, OUT_DIR, log, load_config, http_get_json, write_json,
                       read_json, today_stamp)

# Default source: a community mirror on GitHub that re-publishes fortnite-api.com's
# shop JSON. Identical format, but NO API KEY and no Discord sign-up needed, which
# removes the only manual credential step in the whole pipeline.
MIRROR_URL = ("https://raw.githubusercontent.com/Fortnite-Datamining/"
              "Fortnite-Datamining/main/data/shop/current.json")
# Official API, used only if an api key is configured. Same response shape.
OFFICIAL_URL = "https://fortnite-api.com/v2/shop"
FIXTURE = CC_DIR / "fixtures" / "shop_sample.json"

# Rarities worth leading with — these are what people actually search for and buy.
HEADLINE_RARITIES = {"legendary", "epic", "marvel", "dc", "icon", "gaminglegends", "starwars"}


def fetch_shop(cfg: dict) -> dict:
    """Fetch the raw shop payload.

    Tries the keyless GitHub mirror first, since it needs no credentials at all.
    Falls back to the official API if a key is configured, and vice versa, so a
    single source going down does not stop the day's video.
    """
    key = cfg.get("fortnite_api_key", "")
    have_key = bool(key) and not key.startswith("PASTE_")

    sources = [("mirror", MIRROR_URL, {"Accept": "application/json"})]
    if have_key:
        sources.append(("official", OFFICIAL_URL,
                        {"Accept": "application/json",
                         "Authorization": key, "x-api-key": key}))

    last = None
    for name, url, headers in sources:
        try:
            log(f"Fetching shop from {name}: {url[:70]}...")
            payload = http_get_json(url, headers=headers, timeout=30)
            if (payload.get("data") or {}).get("entries"):
                return payload
            log(f"  {name} returned no entries, trying next")
        except Exception as e:  # noqa: BLE001
            log(f"  {name} failed: {e}")
            last = e
    raise RuntimeError(f"all shop sources failed (last: {last})")


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


def _item_images(item: dict) -> list:
    """Every usable image URL for a cosmetic, best first."""
    images = item.get("images") or {}
    return [images[k] for k in ("featured", "icon", "smallIcon") if images.get(k)]


def _best_image(item: dict) -> str:
    urls = _item_images(item)
    return urls[0] if urls else ""


def _entry_render_images(entry: dict) -> list:
    """The shop's own offer artwork. For bundles this is the proper group render
    rather than whichever cosmetic happened to be listed first."""
    nda = entry.get("newDisplayAsset") or {}
    out = []
    for r in nda.get("renderImages") or []:
        url = (r or {}).get("image")
        if url:
            out.append(url)
    return out


def _day(ts: str) -> str:
    """'2026-09-23T23:59:59.999Z' -> '2026-09-23' (UTC calendar day)."""
    return (ts or "")[:10]


def _tile_colors(entry: dict) -> list:
    """Epic's own shop-tile colours for this offer, as #rrggbb, darkest first.

    Using the colours the in-game shop uses is what makes a tile read as
    Fortnite rather than as a generic template."""
    raw = entry.get("colors") or {}
    out = []
    for key in ("color1", "color2", "color3", "textBackgroundColor"):
        v = (raw.get(key) or "").strip().lstrip("#")
        if len(v) >= 6:
            out.append("#" + v[:6].lower())
    return out


def _intro(item: dict) -> dict:
    intro = item.get("introduction") or {}
    return {"chapter": str(intro.get("chapter") or ""),
            "season": str(intro.get("season") or ""),
            "text": intro.get("text") or ""}


def _is_placeholder(name: str) -> bool:
    """Epic leaves unannounced items in the feed as TBD placeholders."""
    low = name.lower()
    return not name or low.startswith("tbd") or "placeholder" in low


def _bundle_label(entry: dict, items: list) -> str:
    """A readable, UNIQUE name for a multi-item offer.

    `layout.name` is the shop SECTION, not the bundle -- today 18 separate
    offers all sit under "Kingdom Hearts". Appending the item count keeps
    section context while telling the offers apart.
    """
    layout = ((entry.get("layout") or {}).get("name") or "").strip()
    if layout:
        return f"{layout} ({len(items)} items)"
    return f"{items[0]['name']} + {len(items) - 1} more"


def normalize(payload: dict) -> dict:
    """Flatten the upstream payload into the shape the rest of the pipeline relies on.

    A shop entry is ONE offer at ONE price. An entry can contain many cosmetics --
    the Kingdom Hearts offer, for example, is 19 items for 4500 V-Bucks. Splitting
    those into 19 separate items would attach the bundle's price to each one and
    claim Riku costs 4500 on his own, which is simply false. So multi-item entries
    become a single bundle row, and only single-item entries carry an item price.
    """
    data = payload.get("data") or {}
    rows, seen = [], set()

    for entry in _iter_raw_entries(data):
        price = entry.get("finalPrice") or entry.get("regularPrice") or 0
        regular = entry.get("regularPrice") or price
        raw_items = [i for i in (entry.get("brItems") or entry.get("items") or [])
                     if not _is_placeholder((i.get("name") or "").strip())]
        if not raw_items or not price:
            continue

        common = {
            "price": price,
            "regular_price": regular,
            "discounted": bool(regular and price and price < regular),
            # inDate is 00:00Z of the UTC day the offer arrived; outDate is
            # 23:59:59Z of its LAST UTC day. An offer whose out_day equals the
            # shop day disappears at the next 00:00 UTC rotation.
            "in_day": _day(entry.get("inDate")),
            "out_day": _day(entry.get("outDate")),
            "offer_id": entry.get("offerId") or "",
            "section": ((entry.get("layout") or {}).get("name") or "").strip(),
            "tile_colors": _tile_colors(entry),
        }

        offer_key = entry.get("offerId") or ""

        if len(raw_items) == 1:
            item = raw_items[0]
            name = (item.get("name") or "").strip()
            # Single cosmetics still dedupe by name: the same skin can appear in
            # several sections, and we only want to show it once.
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            rarity = ((item.get("rarity") or {}).get("value") or "common").lower()
            rows.append({
                "name": name,
                "description": (item.get("description") or "").strip(),
                "type": ((item.get("type") or {}).get("displayValue") or "Item"),
                "rarity": rarity,
                "rarity_label": ((item.get("rarity") or {}).get("displayValue") or "Common"),
                "is_bundle": False,
                "bundle_size": 1,
                "image": _best_image(item),
                "images": _item_images(item) + _entry_render_images(entry),
                "introduction": _intro(item),
                **common,
            })
        else:
            label = _bundle_label(entry, raw_items)
            key = offer_key or label.lower()
            if key in seen:
                continue
            seen.add(key)
            # Rarity of the best item in the bundle, for the colour treatment.
            rarities = [((i.get("rarity") or {}).get("value") or "common").lower()
                        for i in raw_items]
            rarity = next((r for r in rarities if r in HEADLINE_RARITIES), rarities[0])
            rows.append({
                "name": label,
                "description": ", ".join(i["name"] for i in raw_items[:5]),
                "type": f"{len(raw_items)} items",
                "rarity": rarity,
                "rarity_label": "Bundle",
                "is_bundle": True,
                "bundle_size": len(raw_items),
                "image": (_entry_render_images(entry) or [_best_image(raw_items[0])])[0],
                # Group render first, then every member's art in order, so one
                # dead URL can never blank the tile.
                "images": _entry_render_images(entry)
                          + [u for it in raw_items for u in _item_images(it)],
                "member_names": [i["name"] for i in raw_items],
                "introduction": _intro(raw_items[0]),
                **common,
            })

    # Headline rarities first, then price.
    rows.sort(key=lambda i: (i["rarity"] not in HEADLINE_RARITIES, -i["price"]))

    # Bundles are the priciest offers, so a pure price sort fills the whole card
    # with them and shows no actual cosmetics. Lead with the two biggest bundles
    # (they are the day's real news) and let individual skins take the rest --
    # the art is what makes the video worth watching.
    bundles = [r for r in rows if r["is_bundle"]]
    singles = [r for r in rows if not r["is_bundle"]]
    rows = bundles[:2] + singles + bundles[2:]

    return {
        "shop_day": _day(data.get("date")) or today_stamp(),
        "date": data.get("date") or today_stamp(),
        "fetched": today_stamp(),
        "hash": data.get("hash", ""),
        "item_count": len(rows),
        "bundle_count": sum(1 for r in rows if r["is_bundle"]),
        "items": rows,
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
            log("The default source needs no API key. If it is down, check the mirror at")
            log("github.com/Fortnite-Datamining/Fortnite-Datamining")
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
