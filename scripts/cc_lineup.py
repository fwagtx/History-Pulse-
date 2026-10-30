"""
The daily lineup: five shorts a day in the edit style (cc_edit.py), all built
the night of their day from fresh data, for TikTok, YouTube Shorts, Instagram
Reels and Facebook Reels.

    slot  time (Chicago)  what
    1     08:00           nostalgia: a planned throwback (creator-code/quiz/plan.json),
                          else a countdown from the shop's history; no quizzes
                          since 2026-10-30
    2     11:00           today's Item Shop
    3     13:00           On This Day
    4     16:00           Back in the Shop After N Days, else another format on
                          today's shop
    5     19:00           a countdown from the shop's history (rotates)

Shop slots post before the shop rotates (7 PM CDT / 6 PM CST). Every slot has
fallbacks: a format that can't be made honestly from the day's data gives None
and the next one is tried; a slot 5 fallback is never about today's shop,
because it posts after the rotation.

Quality gate, stricter than the classic build: a video only posts if every
frame keeps its text, cosmetics and code inside the apps' safe box (cc_safe:
sampled every 0.25 s), its length is 62-90 s, and its post text passes
post_problems. A video that fails is never published "as the best we had";
the slot tries its next format, or stays empty.
"""

import importlib
import os
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import cc_end_card as E
import cc_formats as F
import cc_safe as S
from cc_common import log

LOCAL_TZ = ZoneInfo("America/Chicago")

SLOTS = [
    {"slot": 1, "name": "quiz", "at": (8, 0), "shop": False},
    {"slot": 2, "name": "shop", "at": (11, 0), "shop": True},
    {"slot": 3, "name": "on_this_day", "at": (13, 0), "shop": False},
    {"slot": 4, "name": "shop_game", "at": (16, 0), "shop": True},
    {"slot": 5, "name": "history", "at": (19, 0), "shop": False},
]

# format -> (module, function); kwargs come with each candidate
EDITS = {
    "shop_recap": ("cc_edit_shop_recap", "build"),
    "back_after": ("cc_edit_back_after", "build"),
    "og_check": ("cc_edit_og_check", "build"),
    "last_chance": ("cc_edit_last_chance", "build"),
    "guess_price": ("cc_edit_guess_price", "build"),
    "this_or_that": ("cc_edit_this_or_that", "build"),
    "higher_lower": ("cc_edit_higher_lower", "build"),
    "most_common": ("cc_edit_most_common", "build"),
    "rarest": ("cc_edit_rarest", "build"),
    "longest_gone": ("cc_edit_longest_gone", "build"),
}

# The owner asked on 2026-10-30 to stop the quizzes if they weren't doing well,
# and they were the weakest videos (TikTok, Sep 23 - Oct 29: about 200 views
# each, against 450-550 for the shop, On This Day and the countdowns). What's
# left is nostalgia and the shop: the planned throwbacks ("remember these?")
# aren't quizzes, so they stay.
NOSTALGIA_PLAN = {"throwback"}

# The shop slot's other formats, best first: Back in the Shop After N Days did
# best of everything (about 1,000-1,250 TikTok views each time); the guessing
# game is only the last fallback.
SHOP_GAMES = ["back_after", "og_check", "last_chance", "guess_price"]


def history_rotation(day: date) -> list:
    """The countdowns' cycle (slot 5, and slot 1's fallback): each variant
    about once in two and a half weeks. Higher or Lower left with the quizzes."""
    y = day.year
    return [
        ("most_common", {"kind": "outfit"}),
        ("rarest", {"kind": "outfit"}),
        ("longest_gone", {"kind": "outfit"}),
        ("most_common", {"kind": "outfit", "since": y}),
        ("rarest", {"kind": "pickaxe"}),
        ("most_common", {"kind": "emote"}),
        ("longest_gone", {"kind": "pickaxe"}),
        ("rarest", {"kind": "emote"}),
        ("most_common", {"kind": "pickaxe"}),
        ("rarest", {"kind": "backpack"}),
        ("most_common", {"kind": "backpack"}),
        ("longest_gone", {"kind": "emote"}),
        ("rarest", {"kind": "glider"}),
        ("most_common", {"kind": "glider"}),
        ("most_common", {"kind": "outfit", "since": y - 1}),
        ("rarest", {"kind": "outfit"}),
    ]


def _rotate(pool: list, k: int) -> list:
    k %= len(pool)
    return pool[k:] + pool[:k]


def candidates(day: date, plan: dict) -> list:
    """Per slot, the candidates in order: ("edit", format, kwargs) or
    ("plan", spec) for a planned quiz / series / On This Day."""
    k = day.toordinal()
    todays = sorted((v for v in plan.get("videos", []) if v["date"] == day.isoformat()),
                    key=lambda v: (not v.get("series"), v.get("slot", 9)))
    otd = [("plan", v) for v in todays if v["format"] == "on_this_day"]
    nostalgia = [("plan", v) for v in todays if v["format"] in NOSTALGIA_PLAN]
    history = [("edit", f, kw) for f, kw in _rotate(history_rotation(day), k)]
    return [
        nostalgia + history[3:6],
        [("edit", "shop_recap", {}), ("edit", "og_check", {}), ("edit", "last_chance", {})],
        otd + history[6:9],
        [("edit", f, {}) for f in SHOP_GAMES],
        history[:3] + history[9:12],
    ]


def _builder(cand, items: dict):
    """A make(ctx) for a candidate, or None when its module isn't there."""
    if cand[0] == "plan":
        spec = cand[1]
        if spec["format"] == "on_this_day":
            import cc_quiz as Q
            return lambda c: Q.build(spec, items, c)
        try:
            mod = importlib.import_module("cc_edit_quiz")
        except ModuleNotFoundError:
            return None
        return lambda c: mod.build(spec, items, c)
    _, fmt, kw = cand
    mod_name, fn = EDITS[fmt]
    try:
        mod = importlib.import_module(mod_name)
    except ModuleNotFoundError:
        return None
    return lambda c: getattr(mod, fn)(c, **kw)


def _name(cand) -> str:
    if cand[0] == "plan":
        s = cand[1]
        return f"{s.get('series', '') + ' ' if s.get('series') else ''}{s['format']} #{s.get('episode', '')}"
    return cand[1] + (" " + ",".join(f"{k}={v}" for k, v in cand[2].items()) if cand[2] else "")


def _key(cand) -> str:
    """What counts as 'the same video' within a day."""
    if cand[0] == "plan":
        return f"plan:{cand[1]['format']}:{cand[1].get('series', '')}"
    return cand[1]


def _edit_look_for_otd():
    """On This Day goes through cc_series with the edit look switched on."""
    import cc_looks as LK
    LK.LOOKS["on_this_day"] = "cc_edit_on_this_day"
    cur = {x.strip() for x in os.environ.get("CC_LOOKS", "").split(",") if x.strip()}
    os.environ["CC_LOOKS"] = ",".join(sorted(cur | {"on_this_day"}))


def build_day(shop: dict, art, day: date, plan: dict, only: list | None = None,
              post_problems=None) -> list:
    """[(slot, video, safe)] for the day, best candidate per slot."""
    import cc_looks as LK
    _edit_look_for_otd()
    items = plan.get("items", {})
    ctx = F.Ctx(shop=shop, art=art, day=day, seed=int(day.strftime("%Y%m%d")))
    chosen, used = [], set()
    per_slot = candidates(day, plan)
    for slot, cands in zip(SLOTS, per_slot):
        if only and slot["name"] not in only and slot["slot"] not in {int(x) for x in only if x.isdigit()}:
            continue
        got = None
        for cand in cands:
            key = _key(cand)
            if key in used:
                continue
            make = _builder(cand, items)
            name = f"slot {slot['slot']} {_name(cand)}"
            if make is None:
                log(f"  {name}: not built yet, skipping")
                continue
            LK.draw.last = None
            try:
                video = E.finish(make, ctx)
            except Exception as e:  # noqa: BLE001 - one bad format must not sink the day
                log(f"  {name} crashed: {e!r}")
                continue
            if video is None:
                log(f"  {name}: can't be made honestly today, trying the next")
                continue
            if cand[0] == "plan" and cand[1]["format"] == "on_this_day" and LK.draw.last != "cc_edit_on_this_day":
                log(f"  {name}: drawn by {LK.draw.last}, not the edit look; trying the next")
                continue
            if getattr(video.comp, "music", None) is None:
                log(f"  {name}: not an edit (no music track); trying the next")
                continue
            dur = video.comp.duration
            if not F.MIN_SECONDS - .01 <= dur <= 90.0:
                log(f"  {name}: {dur:.1f}s is outside 62-90 s, trying the next")
                continue
            problems = (post_problems or (lambda v: []))(video)
            if problems:
                log(f"  {name}: post text problems ({'; '.join(problems)}), trying the next")
                continue
            safe = S.check(video.comp)
            if not safe["ok"]:
                log(f"  {name}: something sits under the apps' UI -- {S.summary(safe, 4)}; trying the next")
                continue
            got = (slot, video, safe)
            used.add(key)
            log(f"  {name}: {dur:.1f}s, safe zones OK, music {video.comp.music.get('title') or 'synth'}")
            break
        if got is None:
            print(f"::warning::slot {slot['slot']} ({slot['name']}): no video passed today", file=sys.stderr)
            continue
        chosen.append(got)
    return chosen


def slot_time(day: date, slot: dict) -> datetime:
    """The local post time; a shop slot is pulled earlier if it would land at
    or after the shop rotation (00:00 UTC) less 45 minutes."""
    hh, mm = slot["at"]
    local = datetime(day.year, day.month, day.day, hh, mm, tzinfo=LOCAL_TZ)
    if slot["shop"]:
        latest = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(days=1, minutes=-45)
        if local > latest:
            local = latest.astimezone(LOCAL_TZ).replace(second=0, microsecond=0)
    return local
