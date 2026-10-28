"""
RAREST, as an edit: the cosmetics that have been in the Item Shop the FEWEST
separate times, counted down on the countdown edit (cc_edit_countdown) to a
real track. Not the ones gone the longest -- that's cc_edit_longest_gone.

    build(ctx, kind="outfit")       kind: outfit | pickaxe | emote | backpack | glider

  hook    frame 0: "the rarest skins in fortnite 😭" over the five on their
          tiles, "fewest times in the item shop 🛒"; a bar later "wait for #1 👀"
  items   #5 to #2, cut on bar lines: the rank, the name, "in the item shop"
          over "? times" while the ticks run, "only once" slamming in on the
          hit; then "for just 3 days: jul 26–28, 2019", its rarity, type and
          season, and one line about it ("that was over 7 years ago 😭")
  #1      "and #1 is… 🥁" over its silhouette, "the fewest times in the item
          shop 👀", the drop, 💎 on its tile
  outro   the five with their days in the shop ("#1 · 1 day"; "#1 · once" /
          "#2 · 2x" when not all five were in it once), "do you own any of
          these? 👇", use code BAD

Ranking and truth -- cc_rarity's rules, through the classic data functions
(cc_fmt_rarity.history and _item, cc_fmt_most_common._ranked for the runs,
days and first/last days up to ctx.day):
  - "only once" / "only 2 times"  <- separate runs in the Item Shop up to
                                     ctx.day (consecutive days count once)
  - ranking    fewest times, then fewest days in the shop, then gone the
               longest; a set that left the shop together counts once
  - who counts items sold at least once and not in today's shop, whose first
               day in the shop the records can vouch for (2018 on, as
               cc_rarity.first_seen) and was at least a year before ctx.day:
               a skin that came out last month isn't rare, it's new (without
               this a glider sold once, 19 days ago, came second)
  - "for just 3 days: <dates>"    <- its days in the shop, when it had one run
  - "last seen <date>"            <- its latest day in the shop
  - "that was over 7 years ago"   <- whole years from that day to ctx.day
Every one of the five must have art, or no video (None): skipping one would
put the wrong rank on the next. Never why it's rare, never that it won't
come back, never "rarest ever" beyond what the ranking is.
"""

import random
from collections import Counter

import cc_edit_countdown as CD
from cc_fmt_most_common import KINDS, _ranked
from cc_fmt_rarity import _item, _season_text, history
from cc_formats import Ctx, Video, _caption, _hashtags, num

COUNT = 5
MIN_AGE = 365                   # days from its first day in the shop to ctx.day, at least


def rows(ctx: Ctx, kind: str, count: int = COUNT) -> list | None:
    """The `count` rarest of `kind` as of ctx.day, rarest first, or None."""
    hist = history()
    listed = CD.listed_today(ctx)
    gone = [r for r in _ranked(hist, ctx.day, kind, None) if r["key"] not in listed and r["last"] < ctx.day]
    left = Counter((_set(r["raw"]), r["last"]) for r in gone)       # who left the shop on each day, by set
    # the records must vouch for its count (first day 2018 on), and it can't be new
    cands = [r for r in gone if r["first"] is not None and (ctx.day - r["first"]).days >= MIN_AGE]
    cands.sort(key=lambda r: (r["times"], r["days"], r["last"], (r["raw"].get("name") or "").strip().lower()))
    out, seen = [], set()
    for r in cands:
        key = (_set(r["raw"]), r["last"])
        if key[0] and key in seen:
            continue                      # a set that left together counts once
        seen.add(key)
        it = _item(r["raw"])
        it["name"] = " ".join(it["name"].split())
        it["raw"] = r["raw"]              # its series' tile colours
        out.append(dict(r, item=it, gone=(ctx.day - r["last"]).days,
                        span=r["runs"][0] if r["times"] == 1 else None,
                        **{"with": left[key] - 1 if key[0] else 0}))
        if len(out) == count:
            break
    if len(out) < count:
        return None
    if any(not ctx.art(r["item"]) for r in out):
        return None
    return out


def _set(raw: dict) -> str:
    return (raw.get("set") or {}).get("value") or ""


def _days(n: int) -> str:
    return f"{n} day{'s' if n != 1 else ''}"


def _stay(r: dict) -> str:
    """'for just 3 days: jul 26–28, 2019' (one run) / 'for 12 days in all'."""
    n = r["days"]
    if r["times"] == 1:
        a, b = r["span"]
        return f"for {'just ' if n <= 7 else ''}{_days(n)}: {CD.span_str(a, b)}"
    return f"for {_days(n)} in all"


def _what(it: dict) -> str:
    """'epic outfit · chapter 1, season 3' -- its rarity, type and Epic's season."""
    what = f"{it.get('rarity_label') or it['rarity']} {it['type']}".strip().lower()
    season = _season_text(it)
    return f"{what} · {season.lower()}" if season else what


ONE_DAY = "1 day in the item shop. ever. 😭"


def _options(r: dict, rank: int, day, top_one_day: bool) -> list:
    """The true lines about it, [(kind, text)] for CD.choose; #1 gets one."""
    years = CD.years_line(r["last"], day, "that was", " ago")
    gone = f"not back in {r['gone']:,} days 💀" if r["gone"] > 1 else ""
    one_day = r["times"] == 1 and r["days"] == 1
    if rank == 1:
        return [("one_day", ONE_DAY)] if one_day else [("years", years)] if years else [("gone", gone)]
    opts = [("years", years), ("gone", gone)]
    if one_day and not top_one_day:           # #1's own line, when it has it
        opts.append(("one_day", ONE_DAY))
    return opts


def build(ctx: Ctx, kind: str = "outfit", **_):
    if kind not in KINDS:
        return None
    picked = rows(ctx, kind)
    if not picked:
        return None
    word, cap, one = KINDS[kind]
    rnd = random.Random(ctx.seed * 7 + 3)
    # The outro's labels: the days when all five were in the shop once (the
    # days are what order them then), else how many times.
    by_days = all(r["times"] == 1 for r in picked)
    top_one_day = picked[0]["times"] == 1 and picked[0]["days"] == 1
    lines = CD.choose([_options(r, rank, ctx.day, top_one_day) for rank, r in enumerate(picked, 1)], rnd)
    entries = []
    for rank, r in enumerate(picked, 1):
        it = r["item"]
        times = r["times"]
        facts = ([_stay(r)] if times == 1 else [f"last seen: {CD.day_str(r['last'])}", _stay(r)]) + [_what(it)]
        if r["with"]:
            facts.insert(1, f"+{r['with']} more from its set, gone since that day")
        entries.append(CD.Entry(
            it, CD.Stat("in the item shop", text="only once" if times == 1 else f"only {times} times",
                        guess="? times"),
            facts, lines[rank - 1],
            label=_days(r["days"]) if by_days else ("once" if times == 1 else f"{times}x")))
    comp = CD.cut(ctx, entries, salt="rarest", title=f"the rarest {cap} in fortnite 😭",
                  sub="fewest times in the item shop 🛒", tease="the fewest times in the item shop 👀",
                  ask="do you own any of these? 👇", crown="💎")
    if comp is None:
        return None

    # ------------------------------------------------------------ the post
    title_kind = cap.title() if kind != "backpack" else "Back Blings"

    def line(k, r):
        times = "only once" if r["times"] == 1 else f"only {r['times']} times"
        return (f"{num(k)} {r['item']['name']} · in the Item Shop {times} ({_days(r['days'])} in all)"
                f" · last seen {r['last']:%b %-d, %Y}")
    body = "\n".join(line(k, r) for k, r in enumerate(picked, 1))
    head = (f"💎 The rarest {cap} in Fortnite — the fewest separate times in the Item Shop, as of {ctx.day_label}\n"
            f"Ranked by separate times in the Item Shop (consecutive days count once); ties go to fewer days in "
            f"the shop, then longer gone. Only {cap} first sold at least a year ago and not in today's shop 👇")
    tags = _hashtags("rareskins" if kind == "outfit" else f"rare{cap.replace(' ', '')}", "ogfortnite",
                     picked[0]["item"]["name"])
    top = picked[0]
    once = "Only Once" if top["times"] == 1 else f"Only {top['times']} Times"
    return Video(
        f"edit_rarest_{kind}", comp,
        title=f"Rarest Fortnite {title_kind}: Fewest Times in the Item Shop — {ctx.day_label}",
        yt_title=f"Rarest Fortnite {title_kind}: Fewest Times in the Item Shop (#1: {once}) #shorts",
        caption=_caption(head + CD.credit(comp), body, "Do you own any of these?", tags),
        hashtags=tags)
