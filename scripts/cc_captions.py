"""
Generate per-platform titles, captions and hashtags for a day's item shop.

Two things this deliberately does:

1. **Always appends the disclosure.** Epic's Support-A-Creator Terms require you to disclose
   that you have Creator terms with Epic and can receive payouts. It is appended here so it
   cannot be forgotten on an unattended run. Don't strip it.

2. **Rotates the hook by date.** Posting byte-identical copy every day is what automated spam
   looks like to both platform filters and humans. Rotating templates is free variety.

Usage:
    python3 scripts/cc_captions.py [--date YYYY-MM-DD]
"""

import sys
from datetime import date

from cc_common import OUT_DIR, log, load_config, creator_code, read_json, write_json, today_stamp

DISCLOSURE = "#EpicPartner"

# Rotated daily so the copy never reads as a byte-identical bot post.
# Every hook below is provable from the shop payload alone. Claims we cannot verify
# ("is BACK", "RETURNS", "rare drop") are deliberately absent: they are deceptive if wrong,
# and a title the video doesn't deliver on wrecks retention. Once shop_history.json has
# accumulated, "first time in N days" becomes a *true* hook worth adding.
TITLE_HOOKS = [
    "Fortnite Item Shop Today — {date} | {headline}",
    "{headline} in the Fortnite Item Shop — {date}",
    "Item Shop {date}: {headline} + {count} more",
    "Fortnite Item Shop {date} — is {headline} worth it?",
    "EVERYTHING in the Fortnite Item Shop Today ({date})",
    "{headline} is in the Item Shop right now — {date}",
    "Fortnite Item Shop {date} | Full Breakdown",
]

SHORT_HOOKS = [
    "{headline} is in today's item shop.",
    "Today's shop is headlined by {headline}.",
    "Shop reset: {headline} leads today's lineup.",
    "{count} items in today's shop — {headline} is the one to watch.",
    "Item shop just refreshed. {headline} is up top.",
    "If {headline} was on your list, it's in the shop today.",
    "Today's lineup starts with {headline}.",
]

BASE_TAGS = ["fortnite", "fortniteitemshop", "itemshop", "fortniteclips", "fortnitebr"]


def pick(seq, stamp: str):
    """Deterministic per-day rotation — same date always yields the same copy."""
    y, m, d = (int(x) for x in stamp.split("-"))
    return seq[date(y, m, d).toordinal() % len(seq)]


def _price_line(item: dict) -> str:
    if item.get("discounted"):
        return f"{item['name']} — {item['price']} V-Bucks (was {item['regular_price']})"
    return f"{item['name']} — {item['price']} V-Bucks"


def build(shop: dict, code: str) -> dict:
    items = shop["items"]
    stamp = shop["fetched"]
    headline = items[0]["name"]
    count = len(items)
    pretty_date = stamp

    title = pick(TITLE_HOOKS, stamp).format(headline=headline, date=pretty_date, count=count)
    hook = pick(SHORT_HOOKS, stamp).format(headline=headline, count=count)
    disclosure = DISCLOSURE.format(code=code)

    listing = "\n".join(f"• {_price_line(i)}" for i in items[:12])
    if count > 12:
        listing += f"\n• …and {count - 12} more"

    # Item names make strong long-tail tags — that's where the searchable volume actually is.
    item_tags = [i["name"].lower().replace(" ", "").replace("'", "") for i in items[:5]]
    tags = BASE_TAGS + item_tags + [f"code{code.lower()}"]

    cta = f"Use code {code} in the item shop. It genuinely helps the channel."

    long_description = (
        f"{hook}\n\n"
        f"TODAY'S ITEM SHOP ({pretty_date}):\n{listing}\n\n"
        f"{cta}\n"
        f"Codes reset every 14 days, so if you've used {code} before it's probably expired — "
        f"re-entering takes about five seconds.\n\n"
        f"{disclosure}\n\n"
        f"{' '.join('#' + t for t in tags[:15])}"
    )

    short_caption = (
        f"{hook}\n\n"
        f"Code {code} in the item shop 💛\n\n"
        f"{disclosure}\n"
        f"{' '.join('#' + t for t in tags[:8])}"
    )

    return {
        "date": stamp,
        "code": code,
        "headline": headline,
        "youtube": {"title": title[:100], "description": long_description,
                    "tags": tags[:15]},
        "short": {"title": f"{headline} — Item Shop {pretty_date} | Code {code}"[:100],
                  "caption": short_caption},
        "tiktok": {"caption": short_caption[:2200]},
        "x": {"post": f"{hook}\n\nUse code {code} at checkout.\n\n"
                      f"{disclosure}"[:280]},
        "discord": {"message": f"**Item Shop — {pretty_date}**\n\n{listing}\n\n{cta}"},
        "disclosure": disclosure,
    }


def main():
    stamp = today_stamp()
    if "--date" in sys.argv:
        stamp = sys.argv[sys.argv.index("--date") + 1]

    cfg = load_config()
    code = creator_code(cfg)

    shop = read_json(OUT_DIR / stamp / "shop.json")
    if not shop:
        log(f"ERROR: no shop.json for {stamp}. Run cc_shop.py first.")
        sys.exit(1)

    captions = build(shop, code)
    out = write_json(OUT_DIR / stamp / "captions.json", captions)
    log(f"Wrote captions -> {out}")
    log(f"YouTube title: {captions['youtube']['title']}")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    main()
