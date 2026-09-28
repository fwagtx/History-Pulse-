"""
Rarity from the Item Shop's own history: when an item was last sold, how long it
has been gone, how many times it has been in the shop, and -- for a day's shop --
what just came back after a long time.

Data: fortnite-api.com's full cosmetics list with every item's `shopHistory` (the
days it was in the Item Shop, from 2017-10-30 on). The "cosmetics-data" release
keeps a weekly copy (.github/workflows/cosmetics-data.yml on main); a build that
makes claims about TODAY's shop should load a fresh copy (load(fresh=True) on a
GitHub runner), or an item sold between the weekly copy and today would look
longer gone than it is.

Truth rules (every format using this module keeps them):
  - "Last in the Item Shop on Feb 3, 2020"  <- the latest day in its shopHistory
  - "Gone for 2,428 days"                    <- the video's day minus that day
  - "In the Item Shop 13 times"              <- separate runs: consecutive days are
                                                ONE time in the shop, not several
  - "Back after 450 days"                    <- the item is in that day's shop, and
                                                450 days passed between the end of its
                                                previous run and the start of this one
  - "First sold on ..." only when that day is on or after FIRST_SURE: the records
    start 2017-10-30, so an earlier "first" may just be where the records begin.
It never says an item will never come back, or why it hasn't.
"""

import gzip
import json
import urllib.request
from datetime import date, timedelta

from cc_common import OUT_DIR, log

RELEASE_URL = "https://github.com/fwagtx/History-Pulse-/releases/download/cosmetics-data/br-full.json.gz"
# responseFlags: 2 = gameplay tags (Battle Pass, source...), 4 = shop history
FRESH_URL = "https://fortnite-api.com/v2/cosmetics/br?responseFlags=6"
RECORDS_START = date(2017, 10, 30)
FIRST_SURE = date(2018, 1, 1)


def load(path: str | None = None, fresh: bool = False) -> list:
    """The cosmetics list with shop history: a local .json/.json.gz, today's list
    straight from fortnite-api.com (fresh=True, GitHub runners only), or the
    weekly release copy."""
    if path:
        opener = gzip.open if str(path).endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as f:
            return json.load(f)["data"]
    cache = OUT_DIR / "_data" / ("br-fresh.json" if fresh else "br-full.json.gz")
    cache.parent.mkdir(parents=True, exist_ok=True)
    url = FRESH_URL if fresh else RELEASE_URL
    log(f"Downloading {url}")
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "usecodebad"})
    with urllib.request.urlopen(req, timeout=240) as resp:
        cache.write_bytes(resp.read())
    return load(str(cache))


# Days the records list items that weren't on sale. 2023-12-06 (Chapter 5's
# launch): 58 items show up for that one day only, every one of them for the
# first time -- the default Recruit outfits, test placeholders (Set_01_OA/PA),
# Battle Pass and pack skins. On a day listed here an item counts as in the
# shop only when it was also in the shop the day before or the day after.
BAD_DAYS = {date(2023, 12, 6)}


def _clean(days: set) -> list:
    """The item's shop days without its lone appearances on BAD_DAYS."""
    return sorted(d for d in days
                  if d not in BAD_DAYS or (d - timedelta(days=1)) in days or (d + timedelta(days=1)) in days)


def _runs(days: list) -> list:
    """Consecutive days grouped into (first, last) runs."""
    runs = []
    for d in days:
        if runs and (d - runs[-1][1]).days <= 1:
            runs[-1][1] = d
        else:
            runs.append([d, d])
    return [(a, b) for a, b in runs]


class History:
    """Shop history for every cosmetic that has one, keyed by lower-case id."""

    def __init__(self, raw_items: list):
        self.items, self.days = {}, {}
        for r in raw_items:
            h = r.get("shopHistory") or []
            if not r.get("id") or not h:
                continue
            days = _clean({date.fromisoformat(d[:10]) for d in h})
            if not days:
                continue
            key = r["id"].lower()
            self.items[key] = r
            self.days[key] = days
        self.latest = max((d[-1] for d in self.days.values()), default=None)

    def has(self, item_id: str) -> bool:
        return item_id.lower() in self.days

    def runs(self, item_id: str, until: date | None = None) -> list:
        days = self.days.get(item_id.lower(), [])
        if until:
            days = [d for d in days if d <= until]
        return _runs(days)

    def times(self, item_id: str, until: date | None = None) -> int:
        """How many separate times it has been in the Item Shop (up to `until`)."""
        return len(self.runs(item_id, until))

    def last_seen(self, item_id: str, before: date) -> date | None:
        """Its last day in the shop before `before`."""
        days = [d for d in self.days.get(item_id.lower(), []) if d < before]
        return days[-1] if days else None

    def first_seen(self, item_id: str) -> date | None:
        """Its first day in the shop, only when the records can vouch for it."""
        days = self.days.get(item_id.lower(), [])
        return days[0] if days and days[0] >= FIRST_SURE else None

    def gone_days(self, item_id: str, today: date) -> int | None:
        last = self.last_seen(item_id, today)
        return (today - last).days if last else None

    def back_after(self, item_id: str, start: date) -> tuple | None:
        """For an item whose current listing started on `start` (a shop row's in_day):
        (days it had been gone, the day it was last sold before that), or None when
        the records have nothing earlier. A listing that simply continues an earlier
        run comes out as a gap of 1 day."""
        last = self.last_seen(item_id, before=start)
        return ((start - last).days, last) if last else None

    def longest_gone(self, today: date, kind: str = "outfit", n: int = 10, keep=None) -> list:
        """The n items of `kind` gone the longest as of `today`: [(item, last_seen, days, times)].
        keep(item) -> bool filters further (a series, a chapter, ...)."""
        rows = []
        for key, days in self.days.items():
            it = self.items[key]
            if (it.get("type") or {}).get("value") != kind:
                continue
            if keep and not keep(it):
                continue
            past = [d for d in days if d < today]
            if not past or days[-1] >= today:      # never sold before today, or on sale now
                continue
            rows.append((it, past[-1], (today - past[-1]).days, len(_runs(past))))
        rows.sort(key=lambda r: (-r[2], r[3], r[0].get("name", "")))
        return rows[:n]


def shop_ids(row: dict) -> list:
    """The cosmetic ids a daily-shop row sells (a single's own id, or a bundle's members)."""
    if row.get("is_bundle"):
        return [i for i in (row.get("member_ids") or []) if i]
    return [row["item_id"]] if row.get("item_id") else []


def back_in_shop(hist: History, shop: dict, today: date, min_days: int = 180) -> list:
    """Today's single offers that came back after at least `min_days` away, longest
    gap first: [(row, item_id, days_gone, last_seen, times_before)]. The gap is
    measured to the day this listing started (the row's in_day)."""
    out, seen = [], set()
    for row in shop.get("items", []):
        if row.get("is_bundle"):
            continue
        ids = shop_ids(row)
        if not ids or ids[0].lower() in seen or not hist.has(ids[0]):
            continue
        iid = ids[0]
        seen.add(iid.lower())
        start = date.fromisoformat(row["in_day"]) if row.get("in_day") else today
        ba = hist.back_after(iid, start)
        if ba and ba[0] >= min_days:
            out.append((row, iid, ba[0], ba[1], hist.times(iid, until=start - timedelta(days=1))))
    out.sort(key=lambda r: -r[2])
    return out
