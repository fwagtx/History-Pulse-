"""
When each of a day's videos goes up on each network.

The owner asked (2026-10-28) for every video to go out at the best time for
engagement on each platform. creator-code/post_times.json holds Metricool's
best-time-to-post scores for the usecodebad brand (for each network, weekday
and hour of the day in America/Chicago; higher is better). Metricool has none
for Threads, whose audience is the Instagram account's, so Threads follows
Instagram.

For each network and day:
  1. the day's five slots (cc_lineup.SLOTS) take the best-scoring set of whole
     hours from 9 AM to 8 PM, at least two hours apart, so two of our posts
     never compete with each other;
  2. the slots pick from that set in order of importance: the shop recap first
     (the best of them up to noon: it's the day's news), then the shop game
     (the best left that is still 45 minutes before the shop rotates), then
     the history format, the quiz and On This Day; the shop recap always goes
     up before the shop game (they swap hours if the scores say otherwise).
The same five hours whichever videos a build makes, so videos built on
different nights for one day (cc_build.py --ahead) never land on one hour.

    python3 scripts/cc_post_times.py [DAY]      # print a day's times
"""

import json
import sys
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from itertools import combinations
from zoneinfo import ZoneInfo

from cc_common import CC_DIR

LOCAL_TZ = ZoneInfo("America/Chicago")
NETWORKS = ("tiktok", "youtube", "facebook", "instagram", "threads")
FOLLOWS = {"threads": "instagram"}       # no Threads scores from Metricool
FIRST_HOUR, LAST_HOUR, GAP = 9, 20, 2
ORDER = ("shop", "shop_game", "history", "quiz", "on_this_day")
SHOP_SLOTS = {"shop", "shop_game"}
EARLY = 12                                # the shop recap goes up by noon
MARGIN = timedelta(minutes=45)            # a shop video is up at least this long before the shop rotates


@lru_cache(None)
def _scores() -> dict:
    return json.loads((CC_DIR / "post_times.json").read_text())["scores"]


def _at(day: date, hour: int) -> datetime:
    return datetime(day.year, day.month, day.day, hour, tzinfo=LOCAL_TZ)


@lru_cache(None)
def day_times(day: date, network: str) -> dict:
    """{slot name: local datetime} for all five slots on day on network; {} if
    the scores can't place them (the slot's own time then stands)."""
    score = _scores()[FOLLOWS.get(network, network)][str(day.isoweekday())]
    latest = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(days=1) - MARGIN
    ok_for_shop = lambda h: _at(day, h) <= latest          # noqa: E731
    best, best_sum = None, -1
    for hours in combinations(range(FIRST_HOUR, LAST_HOUR + 1), len(ORDER)):
        if any(b - a < GAP for a, b in zip(hours, hours[1:])):
            continue
        if sum(1 for h in hours if ok_for_shop(h)) < len(SHOP_SLOTS):
            continue
        total = sum(score[h] for h in hours)
        if total > best_sum:
            best, best_sum = hours, total
    if best is None:
        return {}
    left = sorted(best, key=lambda h: (-score[h], h))
    out = {}
    for name in ORDER:
        fits = [h for h in left if name not in SHOP_SLOTS or ok_for_shop(h)]
        if name == "shop":
            fits = [h for h in fits if h <= EARLY] or fits
        if not fits:
            return {}
        out[name] = _at(day, fits[0])
        left.remove(fits[0])
    if out["shop_game"] < out["shop"]:          # the day's shop goes up before the game on it
        out["shop"], out["shop_game"] = out["shop_game"], out["shop"]
    return out


def post_at(day: date, slot_name: str, fallback: datetime) -> dict:
    """{network: {"local": ..., "iso": ...}} for one video: its time on each
    network, or the slot's own time where the scores can't place it."""
    out = {}
    for net in NETWORKS:
        t = day_times(day, net).get(slot_name) or fallback
        out[net] = {"local": t.strftime("%Y-%m-%dT%H:%M:%S"), "iso": t.isoformat(timespec="seconds")}
    return out


if __name__ == "__main__":
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    print(f"{d} ({d:%A})")
    for net in NETWORKS:
        ts = day_times(d, net)
        print(f"  {net:<10}" + "  ".join(f"{n} {ts[n]:%-I %p}" for n in sorted(ts, key=lambda n: ts[n])))
