"""
The long videos: five a week on YouTube, Monday to Friday, one series a day,
every word from the Item Shop's own records (cc_rarity) and Epic's item data,
so they never run out and never make anything up.

    Mon  THIS WEEK IN THE ITEM SHOP    last Monday-Sunday's biggest comebacks
    Tue  THE 30 ...                    a countdown that rotates week to week:
                                       gone the longest / the rarest (fewest
                                       separate times in the shop) / the most
                                       common, for skins, pickaxes, emotes,
                                       back blings and gliders
    Wed  <SEASON>: WHERE ARE THEY NOW  one season's shop skins, counted down to
                                       the one that has been back the fewest
                                       times; the seasons in a spread-out order
    Thu  THE ITEM SHOP IN <MONTH YEAR> this calendar month in an earlier year:
                                       the skins that were new in the shop then,
                                       and how often each has been back since
    Fri  THE RAREST <SERIES> SKINS     Icon, Marvel, DC, Star Wars, Gaming
                                       Legends and the biggest sets in turn

    out = build(day, hist, art, out_dir)   # dict(comp, wav, chapters, title, rows,
                                           #      episode, topic, hook, thumb, seed)
    meta = describe(out, day)              # YouTube title, description, tags
    thumbnail(out, path)                   # 1280x720 JPEG
    render with cc_long.render(out["comp"], mp4, out["wav"])

A day whose series can't be made (too few items with pictures) falls back to
another topic, so every weekday gets a video.

Truth rules (cc_rarity's): "in the Item Shop N times" counts separate runs
(consecutive days are one time), up to the video's day; first days only from
2018 on (the records start Oct 30, 2017). A "rarest" countdown or collection
only counts items out for a year or more and not for sale that day, so
brand-new items don't crowd it. Nothing is said about why something is gone or
whether it will come back. The code: "use code BAD" -- never a discount, never
anything about commissions.
"""

import random
from datetime import date, timedelta
from math import gcd
from pathlib import Path

import cc_edit as ED
import cc_edit_long as LE
import cc_rarity as R
from cc_common import log
from cc_fmt_rarity import _item
from cc_long_rarest import date_words, words, year_words
from cc_motion import esc, trim_for

W, H = LE.W, LE.H
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
KINDS = {"outfit": ("skin", "skins", "Skins"), "pickaxe": ("pickaxe", "pickaxes", "Pickaxes"),
         "emote": ("emote", "emotes", "Emotes"), "backpack": ("back bling", "back blings", "Back Blings"),
         "glider": ("glider", "gliders", "Gliders")}
COUNTDOWNS = [("longest_gone", "outfit"), ("rarest", "outfit"), ("most_common", "outfit"),
              ("longest_gone", "pickaxe"), ("rarest", "emote"), ("most_common", "pickaxe"),
              ("longest_gone", "emote"), ("rarest", "backpack"), ("most_common", "emote"),
              ("longest_gone", "glider"), ("rarest", "pickaxe"), ("most_common", "backpack")]
SERIES = {"Icon Series": "Icon Series", "MARVEL SERIES": "Marvel", "DC SERIES": "DC",
          "Star Wars Series": "Star Wars", "Gaming Legends Series": "Gaming Legends"}
EPOCH = date(2026, 9, 28)          # a Monday: week 0 of the rotations
POST_AT = (15, 0)                  # America/Chicago, Monday to Friday
COUNT = 30                         # items in a countdown
MIN_ROWS = 12                      # fewer than this and the day's topic falls back
AGED = 365                         # days an item must have been out to count as "rare"


def d_short(d: date) -> str:
    return f"{d:%b} {d.day}, {d.year}"


def times_words(n: int) -> str:
    return "once" if n == 1 else ("twice" if n == 2 else f"{words(n)} times")


def times_short(n: int) -> str:
    return "once" if n == 1 else ("twice" if n == 2 else f"{n:,} times")


def _raw_kind(raw: dict) -> str:
    return ((raw.get("type") or {}).get("value") or "").lower()


def _raw_value(raw: dict, field: str) -> str:
    v = raw.get(field)
    return (v.get("value") or "") if isinstance(v, dict) else ""


def _season_of(raw: dict) -> int:
    return int((raw.get("introduction") or {}).get("backendValue") or -1)


def _intro_text(raw: dict) -> str:
    return ((raw.get("introduction") or {}).get("text") or "").replace("Introduced in ", "").rstrip(".")


def _rotate(pool: list, k: int) -> list:
    k %= len(pool)
    return pool[k:] + pool[:k]


class Times(int):
    """A count said as 'once', 'twice', 'twelve times'."""


class Year(int):
    """A year said as 'twenty nineteen'."""


def two(template: str, **values) -> tuple:
    """(spoken, subtitle) from one template: the narrator gets words ("March
    fourth, twenty nineteen", "two thousand"), the subtitles digits ("Mar 4,
    2019", "2,000"). Values: date, Times, Year, int or text."""
    def said(v):
        if isinstance(v, date):
            return date_words(v)
        if isinstance(v, Times):
            return times_words(v)
        if isinstance(v, Year):
            return year_words(v)
        return words(v) if isinstance(v, int) else v

    def shown(v):
        if isinstance(v, date):
            return d_short(v)
        if isinstance(v, Times):
            return times_short(v)
        if isinstance(v, Year):
            return str(int(v))
        return f"{v:,}" if isinstance(v, int) else v
    return (template.format(**{k: said(v) for k, v in values.items()}),
            template.format(**{k: shown(v) for k, v in values.items()}))


# ------------------------------------------------------------------ pictures (16:9)
#
# Inside cc_safe.LONG (x 96-1824, y 100-960); the code sticker takes the
# top-left corner (x 100-300, y 100-250), the subtitles the bottom (from y 846).

TILE = (350, 180, 580, 660)            # x, y, w, h of the item's tile
COL, COL_W = 1040, 760                 # the right-hand column


def _fit(text: str, width: float, big: float, small: float = 34) -> float:
    """A font size that sets `text` on one line in `width` (TikTok Sans 800-900
    runs about .58 em a character, .68 in capitals), between small and big."""
    em = .68 if text.isupper() else .58
    return max(small, min(big, width / (em * max(4, len(text)))))


def item_screen(lv, seg, e: dict, move: str = "zoom"):
    """One item: its tile over its blurred canvas on the left; the rank, the
    name, the stat (counting up on the line that says it) and the facts on the
    right, each landing on its line."""
    it, uri = e["item"], e["uri"]
    x, y, w, h = TILE
    iid = lv.uid("t")
    tile = ED.tile(lv.src(uri), it, x, y, w, h, iid, trim=trim_for(it), fig=.94)
    lv.scene(seg.t0, seg.t1, ED.canvas(iid, ED.tile_colors(it), 1.3, .5) + tile)
    at = [a for a, _ in seg.lines_at] + [seg.t1] * 6
    over = ED.outline(f"#{e['rank']}", COL, 132, 140, seg.t0, align="left", lime=e["rank"] == 1, width=600)
    over += ED.caption(e["name"], COL, 330, _fit(e["name"], COL_W, 66), at[0] + .1, align="left", width=COL_W,
                       weight=800)
    a, b = seg.lines_at[min(1, len(seg.lines_at) - 1)]
    over += ED.caption(e["kicker"], COL, 452, 34, a, style="dark", align="left", width=COL_W, weight=700)
    dur = max(.6, min(1.6, (b - a) * .6))
    over += ED.caption(f"{ED.counter(e['value'], a + .1, dur)} {esc(e['unit'])}", COL, 502, 96, a + .1,
                       align="left", width=COL_W, weight=900, raw=True, lh=1.25)
    lv.cue(a + .1 + dur, "impact")
    lv.cam.punch(a + .1 + dur, .03, .3)
    fy = 668
    for text, k in e.get("facts", []):
        t = at[min(k, len(at) - 1)]
        over += ED.caption(text, COL, fy, 34, t, style="dark", align="left", width=COL_W, weight=700)
        lv.cue(t, "pop2")
        fy += 60
    if e.get("sticker"):
        over += ED.emoji(e["sticker"], x + w - 44, y + 40, 110, at[0] + .3, rot=12)
    lv.over(seg.t0, seg.t1, over)
    lv.cam.push(seg.t0, seg.t1, 1.0, 1.04, x + w / 2, y + h / 2)
    if move == "whip":
        lv.cam.whip(seg.t0, -1, 0, 520)
    else:
        lv.cam.zoom(seg.t0, .35)
    lv.cue(seg.t0, "impact")


def title_screen(lv, seg, title: str, sub: str, entries: list):
    """The opening: the title big on the left over the first item's canvas,
    three of the items on tilted tiles on the right."""
    tiles, first = "", ""
    for e, (x, y, r) in zip(entries[:3], [(1010, 290, -4), (1250, 230, 3), (1490, 310, -2)]):
        iid = lv.uid("t")
        first = first or iid
        tiles += ED.tile(lv.src(e["uri"]), e["item"], x, y, 300, 400, iid, trim=trim_for(e["item"]),
                         extra=f"transform:rotate({r}deg)")
    colors = ED.tile_colors(entries[0]["item"]) if entries else ("#333333", "#111111")
    lv.scene(seg.t0, seg.t1, ED.canvas(first, colors, 1.0, .55) + tiles)
    rows = title.upper().split("\n")
    size = min(_fit(r, 860, 150, 56) for r in rows)
    start = seg.t0 - 1 if seg.t0 <= 0 else seg.t0
    over, top = "", 300
    for r in rows:
        over += ED.outline(r, 120, top, size, start, align="left", width=860)
        top += size * 1.08
    sub_at = seg.lines_at[1][0] if len(seg.lines_at) > 1 else seg.t0 + .5
    over += ED.caption(sub, 124, top + 40, 40, sub_at, style="box", align="left", width=840, weight=800, rot=-1)
    lv.over(seg.t0, seg.t1, over)
    lv.cam.push(seg.t0, seg.t1, 1.0, 1.05, W / 2, H / 2)


def grid_screen(lv, seg, heading: str, entries: list, labels: list):
    """Up to ten items on small tiles, their labels popping on in turn."""
    n = min(10, len(entries))
    cols = 5 if n > 4 else n
    tw, th, gap = 250, 270, 24
    rows = -(-n // cols)
    x0 = (W - (cols * tw + (cols - 1) * gap)) / 2
    y0 = 262 if rows > 1 else 400
    tiles, first = "", ""
    over = ED.caption(heading, W / 2, 150 if rows > 1 else 260, 46, seg.t0, width=1300, weight=800)
    span = max(.8, (seg.t1 - seg.t0) * .5)
    for i, (e, lab) in enumerate(zip(entries[:n], labels)):
        r, c = divmod(i, cols)
        in_row = min(cols, n - r * cols)
        x, y = x0 + (cols - in_row) * (tw + gap) / 2 + c * (tw + gap), y0 + r * (th + 40)
        iid = lv.uid("t")
        first = first or iid
        tiles += ED.tile(lv.src(e["uri"]), e["item"], x, y, tw, th, iid, trim=trim_for(e["item"]))
        at = seg.t0 + .3 + span * i / max(1, n)
        over += ED.caption(lab, x + tw / 2, y + th - 48, 28, at, width=tw + 20, weight=800)
        lv.cue(at, "pop2")
    lv.scene(seg.t0, seg.t1, ED.canvas(first, ED.tile_colors(entries[0]["item"]), 1.0, .62) + tiles)
    lv.over(seg.t0, seg.t1, over)
    lv.cam.push(seg.t0, seg.t1, 1.0, 1.03, W / 2, H / 2)
    lv.cam.whip(seg.t0, 0, -1, 480)


def cta_screen(lv, seg):
    """The mid-video ask: the code, big, in the app's lime box."""
    lv.scene(seg.t0, seg.t1, '<div class="full" style="background:radial-gradient(ellipse 70% 60% at 50% 45%,'
                             '#2b3200 0%,#0b0c05 100%)"></div>')
    over = ED.caption("use code", W / 2, 290, 70, seg.t0 + .1, style="out", width=1200, weight=900)
    over += ED.caption('<span style="font-size:1.9em">BAD</span>', W / 2, 390, 110, seg.t0 + .35, style="lime",
                       width=1200, weight=900, raw=True, lh=1.05)
    last = seg.lines_at[-1][0] if seg.lines_at else seg.t0 + 1
    over += ED.caption("type BAD in the Support-A-Creator box in the Item Shop 💚", W / 2, 690, 40, last,
                       style="dark", width=1400, weight=700)
    lv.over(seg.t0, seg.t1, over)
    lv.cue(seg.t0 + .35, "boom")
    lv.cam.punch(seg.t0 + .35, .06, .35)
    lv.cam.flash(seg.t0 + .35, .35, .2)


def outro_screen(lv, seg, rows: list, question: str):
    top = rows[:10]
    grid_screen(lv, seg, question, top, [f"#{i + 1}" for i in range(len(top))])


# ------------------------------------------------------------------ the countdown core

def _facts(r: dict, hist: R.History, day: date, rnd: random.Random, skip: frozenset = frozenset()) -> list:
    """True extra facts about an item, shuffled: [((spoken, subtitle), card)]."""
    raw, key = r["raw"], r["key"]
    days = [d for d in hist.days.get(key, []) if d <= day]
    runs = R._runs(days)
    out = []
    season = _intro_text(raw)
    if season and "season" not in skip:
        out.append((two("It came out in {s}.", s=season), f"came out in {season.lower()}"))
    s = _raw_value(raw, "set")
    if s and "set" not in skip:
        out.append((two("It's part of the {s} set.", s=s), f"part of the {s} set"))
    first = hist.first_seen(key)
    if first and first <= day and "first" not in skip:
        out.append((two("Its first day in the Item Shop was {d}.", d=first), f"first in the shop {d_short(first)}"))
    if len(days) >= 3 and "total" not in skip:
        out.append((two("All told, it's been for sale on {n} different days.", n=len(days)),
                    f"for sale {len(days):,} days in total"))
    gaps = [(b[0] - a[1]).days for a, b in zip(runs, runs[1:])]
    if gaps and max(gaps) >= 60 and "gap" not in skip:
        out.append((two("Its longest time away from the shop was {n} days.", n=max(gaps)),
                    f"longest time away: {max(gaps):,} days"))
    rnd.shuffle(out)
    return out


OPENERS = ["Number {w}: {name}.", "At number {w}, {name}.", "Number {w} is {name}.",
           "Coming in at number {w}: {name}."]


def countdown(lv, rows: list, day: date, hist: R.History, rnd: random.Random, stat, skip=frozenset()):
    """Segments for a countdown, #N down to #1 (rows[0] is #1), with the ask for
    the code just before the top ten. rows: dicts with item, raw, key, uri,
    name (+ what `stat` needs); stat(row, rank) -> ((spoken, shown), value,
    unit, kicker)."""
    n = len(rows)
    cta_before = 10 if n >= 16 else max(2, n // 2)
    marks = {n, 20, 10, 5, 1}
    for rank in range(n, 0, -1):
        r = rows[rank - 1]
        line, value, unit, kicker = stat(r, rank)
        op = "And number {w}: {name}." if rank == 1 else OPENERS[(rank + day.toordinal()) % len(OPENERS)]
        facts = _facts(r, hist, day, rnd, frozenset(skip) | r.get("skip", frozenset()))[:3 if rank <= 3 else 2]
        lines = [two(op, w=rank, name=r["name"]), line] + [f[0] for f in facts]
        e = dict(item=r["item"], uri=r["uri"], rank=rank, name=r["name"], value=value, unit=unit, kicker=kicker,
                 facts=[(f[1], 2 + j) for j, f in enumerate(facts)], sticker="👑" if rank == 1 else "")
        move = "whip" if rank % 2 else "zoom"
        if rank == cta_before and rank != n:
            lv.segment([two("Quick one before the top {n}.", n=rank),
                        ("If you're buying anything in the Item Shop, you can support the channel with code B, A, D.",
                         "If you're buying anything in the Item Shop, you can support the channel with code BAD."),
                        "Just type it into the Support-A-Creator box. Thanks, it really helps. 💚"],
                       cta_screen, cue="swoosh", min_len=8)
        lv.segment(lines, lambda lv_, s, e=e, move=move: item_screen(lv_, s, e, move),
                   chapter=f"#{rank} {r['name']}" if rank in marks else "", min_len=8)


# ------------------------------------------------------------------ data

def _entry(hist: R.History, key: str, art) -> dict | None:
    raw = hist.items.get(key)
    if not raw:
        return None
    it = dict(_item(raw), raw=raw)
    uri = art(it)
    if not uri:
        return None
    return {"key": key, "raw": raw, "item": it, "uri": uri, "name": " ".join(it["name"].split())}


def _aged(hist: R.History, key: str, day: date) -> bool:
    """Out for a year or more and not in that day's shop: fair to call rare."""
    days = hist.days.get(key, [])
    return bool(days) and (day - days[0]).days >= AGED and days[-1] < day


def rows_longest_gone(hist, day, kind, count, art):
    rows, seen = [], set()
    for raw, last, days, times in hist.longest_gone(day, kind, count * 8):
        e = _entry(hist, raw["id"].lower(), art)
        if not e:
            continue
        s = (e["item"]["set"], last)
        if e["item"]["set"] and s in seen:
            continue                      # a whole set that left together counts once
        seen.add(s)
        rows.append(dict(e, last=last, days=days, times=times))
        if len(rows) == count:
            break
    return rows


def rows_by_times(hist, day, count, art, keep, fewest: bool):
    """Items passing keep(key, raw), ranked by separate times in the shop up to
    day: fewest first (ties: last sold longest ago, then fewer days for sale) or
    most first (ties: more days for sale); at most one per set with the same
    record (a set sold as a bundle moves together)."""
    cand = []
    for key in hist.days:
        raw = hist.items[key]
        if not keep(key, raw):
            continue
        upto = [d for d in hist.days[key] if d <= day]
        if upto:
            cand.append((len(R._runs(upto)), len(upto), key, upto[-1]))
    cand.sort(key=lambda c: (c[0], c[3], c[1], c[2]) if fewest else (-c[0], -c[1], c[2]))
    rows, sets = [], set()
    for times, ndays, key, last in cand:
        s = _raw_value(hist.items[key], "set")
        if s and (s, times, ndays) in sets:
            continue
        e = _entry(hist, key, art)
        if not e:
            continue
        if s:
            sets.add((s, times, ndays))
        rows.append(dict(e, times=times, ndays=ndays, last=last))
        if len(rows) == count:
            break
    return rows


def _stat_gone(r, rank):
    t = ["It was last in the Item Shop on {d}. That's {n} days ago.",
         "It hasn't been in the Item Shop since {d}: {n} days.",
         "Its last day in the shop was {d}, {n} days ago."][rank % 3]
    return two(t, d=r["last"], n=r["days"]), r["days"], "days", "gone for"


def _stat_times(day):
    def stat(r, rank):
        t, last = r["times"], r["last"]
        tail = ", and it's in the shop right now." if last >= day else ", most recently on {d}."
        head = ["It's been in the Item Shop {t}", "It's been for sale {t}", "It's shown up in the Item Shop {t}"][rank % 3]
        return two(head + tail, t=Times(t), d=last), t, "time" if t == 1 else "times", "in the item shop"
    return stat


def _stat_back(r, rank):
    return two("It came back on {d}, after {n} days away.", d=r["back_on"], n=r["days"]), r["days"], "days", \
        "back after"


def _hook(kind: str, r: dict) -> tuple:
    """A teaser line about number one, from its real numbers: (spoken, subtitle)."""
    if kind == "gone":
        return two("Number {one} hasn't been in the shop for {n} days. 👀", one=1, n=r["days"])
    if kind == "back":
        return two("The biggest one had been gone for {n} days. 👀", n=r["days"])
    if kind == "fewest":
        return two("Number {one} has been in the Item Shop just {t}. 👀", one=1, t=Times(r["times"]))
    return two("Number {one} has been in the shop {t}. 👀", one=1, t=Times(r["times"]))


# ------------------------------------------------------------------ the episodes

def week_index(day: date) -> int:
    return (day - EPOCH).days // 7


def episodes(day: date) -> list:
    """The long video for `day` (Monday to Friday) first, then fallbacks: other
    countdowns, picked well away from the ones Tuesdays use soon."""
    wd, wk = day.weekday(), week_index(day)
    if wd > 4:
        return []
    first = [{"series": "week", "start": day - timedelta(days=7), "end": day - timedelta(days=1)},
             dict(zip(("metric", "kind"), COUNTDOWNS[wk % len(COUNTDOWNS)]), series="countdown"),
             {"series": "season", "index": wk},
             {"series": "month", "index": wk},
             {"series": "collection", "index": wk}][wd]
    alt = [dict(zip(("metric", "kind"), c), series="countdown") for c in _rotate(COUNTDOWNS, wk + 6 + wd)[:4]]
    return [first] + [a for a in alt if a != first]


def _stride(n: int, k: int) -> int:
    """The k-th pick from n things, spread out: consecutive weeks jump around."""
    step = next(s for s in (7, 11, 13, 17, 19, 23, 1) if gcd(s, n) == 1)
    return (k * step) % n


def seasons(hist: R.History, day: date) -> list:
    """Seasons with 14+ shop skins that began a year or more before `day`, in
    release order: [(backendValue, text)]."""
    by = {}
    for key, days in hist.days.items():
        raw = hist.items[key]
        v = _season_of(raw)
        if _raw_kind(raw) != "outfit" or v < 0 or not days or days[0] > day:
            continue
        b = by.setdefault(v, [_intro_text(raw), 0, days[0]])
        b[1] += 1
        b[2] = min(b[2], days[0])
    return [(v, text) for v, (text, n, began) in sorted(by.items())
            if text and n >= 14 and (day - began).days >= AGED]


def collections(hist: R.History, day: date) -> list:
    """The series, then the sets with 14+ shop skins: [(field, value, display name)]."""
    count = {}
    for key, days in hist.days.items():
        raw = hist.items[key]
        s = _raw_value(raw, "set")
        if _raw_kind(raw) == "outfit" and s and days and days[0] <= day:
            count[s] = count.get(s, 0) + 1
    sets = sorted(((n, s) for s, n in count.items() if n >= 14), reverse=True)
    return [("series", k, v) for k, v in SERIES.items()] + [("set", s, s) for _, s in sets]


def _debuts(hist: R.History, y: int, month: int) -> set:
    m0, m1 = date(y, month, 1), date(y + (month == 12), month % 12 + 1, 1)
    return {k for k, days in hist.days.items() if days and m0 <= days[0] < m1 and days[0] >= R.FIRST_SURE
            and _raw_kind(hist.items[k]) == "outfit"}


def month_years(hist: R.History, day: date) -> list:
    """Earlier years whose same calendar month brought 14+ new shop skins, newest first."""
    return [y for y in range(day.year - 1, 2017, -1) if len(_debuts(hist, y, day.month)) >= 14]


def _make(ep: dict, day: date, hist: R.History, art, rnd: random.Random, seed: int):
    """(LongEdit, rows, topic, hook, thumb) for one episode, or None. thumb:
    (title lines, the lime line) for the thumbnail."""
    when = f"{day:%B %Y}"
    as_of = two("Straight from the Item Shop's own records, as of {d}. 👇", d=day)

    def open_(lv, title, sub, lines, rows):
        lv.segment(lines, lambda lv_, s: title_screen(lv_, s, title, sub, rows), chapter="Intro", cue="",
                   min_len=10)

    def close(lv, question, rows):
        lv.segment(["And that's the list.", question,
                    "If you want more like this, subscribe. There's a new one every weekday. 🔔",
                    ("And if you're buying anything in the Item Shop, use code B, A, D. See you tomorrow.",
                     "And if you're buying anything in the Item Shop, use code BAD. See you tomorrow! 💚")],
                   lambda lv_, s: outro_screen(lv_, s, rows, question.lower()), chapter="Outro", min_len=11)

    series = ep["series"]
    if series == "countdown":
        metric, kind = ep["metric"], ep["kind"]
        _, many, cap = KINDS[kind]
        if metric == "longest_gone":
            rows = rows_longest_gone(hist, day, kind, COUNT, art)
            if len(rows) < MIN_ROWS:
                return None
            n = len(rows)
            lv = LE.LongEdit(seed, f"The {n} Fortnite {cap} Gone From the Item Shop the Longest ({when})", day=day)
            hook = _hook("gone", rows[0])
            open_(lv, "gone the\nlongest", f"{n} {many} · item shop records",
                  [two("These are the {n} Fortnite {m} that have been gone from the Item Shop the longest.", n=n,
                       m=many),
                   hook, as_of], rows)
            countdown(lv, rows, day, hist, rnd, _stat_gone, skip={"gap"})
            close(lv, "Which one do you want back the most?", rows)
            return lv, rows, f"gone the longest: {many}", hook, (f"gone the\nlongest\n{many}",
                                                                 f"#1: gone {rows[0]['days']:,} days")
        fewest = metric == "rarest"
        if fewest:
            def keep(k, raw):
                return _raw_kind(raw) == kind and _aged(hist, k, day)
        else:
            def keep(k, raw):
                return _raw_kind(raw) == kind
        rows = rows_by_times(hist, day, COUNT, art, keep, fewest)
        if len(rows) < MIN_ROWS:
            return None
        n = len(rows)
        word = "rarest" if fewest else "most common"
        lv = LE.LongEdit(seed, (f"The {n} Rarest Fortnite {cap}: Fewest Times in the Item Shop ({when})" if fewest else
                                f"The {n} Most Common Fortnite {cap}: Most Times in the Item Shop ({when})"), day=day)
        hook = _hook("fewest" if fewest else "most", rows[0])
        why = ("We counted every separate time each one has been for sale, for everything out a year or more. "
               if fewest else "We counted every separate time each one has been for sale. ")
        open_(lv, f"the {word}\n{many}", f"{n} {many} · item shop records",
              [two("These are the {n} {w} {m} in Fortnite.", n=n, w=word, m=many), hook,
               why + "A few days in a row counts once.", as_of], rows)
        countdown(lv, rows, day, hist, rnd, _stat_times(day))
        close(lv, "Which of these do you own?", rows)
        return lv, rows, f"the {word} {many}", hook, (f"the {word}\n{many}",
                                                       f"#1: in the shop {times_short(rows[0]['times'])}")

    if series == "season":
        pool = seasons(hist, day)
        if not pool:
            return None
        for k in range(3):
            order, text = pool[_stride(len(pool), ep["index"] + k * 5)]
            rows = rows_by_times(hist, day, COUNT, art,
                                 lambda key, raw: _raw_kind(raw) == "outfit" and _season_of(raw) == order, True)
            if len(rows) >= MIN_ROWS:
                break
        else:
            return None
        n = len(rows)
        total = sum(1 for key in hist.days
                    if _raw_kind(hist.items[key]) == "outfit" and _season_of(hist.items[key]) == order)
        every = n >= total
        lv = LE.LongEdit(seed, (f"Every {text} Skin in the Item Shop: Where Are They Now? (Fortnite)" if every else
                                f"The {n} Rarest {text} Item Shop Skins: Where Are They Now? (Fortnite)"), day=day)
        hook = _hook("fewest", rows[0])
        these = two("the {n} rarest", n=n) if not every else ("the", "the")
        open_(lv, f"{text}\nwhere are they now?", f"{n} item shop skins from {text.lower()}",
              [(f"{text}. These are {these[0]} skins from that season that have been sold in the Item Shop.",
                f"{text}. These are {these[1]} skins from that season that have been sold in the Item Shop."),
               "For each one: how many separate times it's been in the shop, and when it was last there.",
               hook, two("Counting down to the rarest, as of {d}. 👇", d=day)], rows)
        countdown(lv, rows, day, hist, rnd, _stat_times(day), skip={"season"})
        close(lv, f"Which {text} skin is your favourite?", rows)
        ch, _, se = text.partition(", ")
        return lv, rows, text, hook, (f"{ch}\n{se}" if se else text, "where are they now?")

    if series == "month":
        years = month_years(hist, day)
        if not years:
            return None
        for k in range(3):
            y = years[(ep["index"] + k) % len(years)]
            debut = _debuts(hist, y, day.month)
            rows = rows_by_times(hist, day, COUNT, art, lambda key, raw: key in debut, True)
            if len(rows) >= MIN_ROWS:
                break
        else:
            return None
        n = len(rows)
        month = MONTHS[day.month - 1]
        label = f"{month} {y}"
        every = n >= len(debut)
        lv = LE.LongEdit(seed, (f"The Fortnite Item Shop in {label}: Every New Skin, Then and Now" if every else
                                f"The Fortnite Item Shop in {label}: {n} New Skins, Then and Now"), day=day)
        hook = _hook("fewest", rows[0])
        open_(lv, f"the item shop in\n{label}", f"{n} skins that were new that month",
              [two("The Fortnite Item Shop in {m} {y}.", m=month, y=Year(y)),
               "These skins were in the Item Shop for the very first time that month." if every else
               two("These {n} skins were in the Item Shop for the very first time that month.", n=n),
               "For each one: how many times it's been back since, and when it was last there.",
               hook, two("Counting down to the rarest, as of {d}. 👇", d=day)], rows)
        countdown(lv, rows, day, hist, rnd, _stat_times(day), skip={"first"})
        close(lv, two("Which one from {m} {y} do you remember?", m=month, y=Year(y))[1], rows)
        return lv, rows, label, hook, (f"{month}\n{y}", "every new skin: then and now" if every else "then and now")

    if series == "collection":
        cols = collections(hist, day)
        for k in range(3):
            field, value, nice = cols[(ep["index"] + k) % len(cols)]
            rows = rows_by_times(hist, day, COUNT, art,
                                 lambda key, raw: (_raw_kind(raw) == "outfit" and _raw_value(raw, field) == value
                                                   and _aged(hist, key, day)), True)
            if len(rows) >= MIN_ROWS:
                break
        else:
            return None
        n = len(rows)
        lv = LE.LongEdit(seed, f"The {n} Rarest {nice} Skins in Fortnite ({when})", day=day)
        hook = _hook("fewest", rows[0])
        open_(lv, f"the rarest\n{nice} skins", f"{n} {nice} skins · item shop records",
              [two("These are the {n} rarest {c} skins in Fortnite.", n=n, c=nice), hook,
               "Ranked by how many separate times each has been for sale, for everything out a year or more.",
               as_of], rows)
        countdown(lv, rows, day, hist, rnd, _stat_times(day), skip={"set"} if field == "set" else frozenset())
        close(lv, f"Which {nice} skin is the best?", rows)
        return lv, rows, f"the rarest {nice} skins", hook, (f"the rarest\n{nice}",
                                                            f"#1: in the shop {times_short(rows[0]['times'])}")

    # the week: last Monday to Sunday's biggest comebacks
    start, end = ep["start"], ep["end"]
    order = {"outfit": 0, "backpack": 1, "pickaxe": 2, "glider": 3, "emote": 4}
    back = []
    for key, days in hist.days.items():
        raw = hist.items[key]
        if _raw_kind(raw) not in order:
            continue
        for a, _ in R._runs([d for d in days if d <= end]):
            if start <= a <= end:
                prev = [d for d in days if d < a]
                if prev and (a - prev[-1]).days >= 30:
                    back.append(((a - prev[-1]).days, order[_raw_kind(raw)], key, a, prev[-1]))
    back.sort(key=lambda b: (-b[0], b[1], b[2]))
    rows, seen = [], set()
    for gap, _, key, a, prev in back:
        s = _raw_value(hist.items[key], "set")
        if key in seen or (s and (s, a) in seen):
            continue
        e = _entry(hist, key, art)
        if not e:
            continue
        seen.add(key)
        if s:
            seen.add((s, a))
        rows.append(dict(e, days=gap, back_on=a, last=prev, times=hist.times(key, until=end)))
        if len(rows) == 25:
            break
    if len(rows) < MIN_ROWS:
        return None
    n = len(rows)
    label = f"{start:%b} {start.day} – {end:%b} {end.day}, {end.year}"
    lv = LE.LongEdit(seed, f"This Week in the Fortnite Item Shop: The {n} Biggest Comebacks ({label})", day=day)
    hook = _hook("back", rows[0])
    open_(lv, "this week in\nthe item shop", f"{label} · the biggest comebacks",
          ["This week in the Fortnite Item Shop.",
           two("From {a} to {b}: the {n} items that came back after the longest time away.", a=start, b=end, n=n),
           hook, "Counted from the Item Shop's own records. Let's go. 👇"], rows)
    countdown(lv, rows, day, hist, rnd, _stat_back, skip={"gap"})
    close(lv, "Which comeback were you waiting for?", rows)
    return lv, rows, f"the week of {label}", hook, ("biggest\ncomebacks", f"back after {rows[0]['days']:,} days")


def build(day: date, hist: R.History, art, out_dir: Path, seed: int | None = None, accept=None) -> dict | None:
    """The day's long video, laid out and mixed (render with cc_long.render),
    or None at weekends or if no topic makes it. accept(out) -> bool is the
    caller's quality gate: a topic it turns down falls back to the next."""
    seed = seed if seed is not None else int(day.strftime("%Y%m%d"))
    for ep in episodes(day):
        got = _make(ep, day, hist, art, random.Random(seed), seed)
        if not got:
            log(f"  long video {ep}: too few items, trying the next topic")
            continue
        lv, rows, topic, hook, thumb = got
        comp, wav, chapters = lv.build(out_dir, [(r["uri"], r["item"]["rarity"]) for r in rows[:5]])
        out = {"comp": comp, "wav": wav, "chapters": chapters, "title": lv.title[:100], "rows": rows,
               "episode": ep, "topic": topic, "hook": hook, "thumb": thumb, "seed": seed}
        if accept and not accept(out):
            log(f"  long video {ep}: turned down by the quality gate, trying the next topic")
            continue
        return out
    return None


# ------------------------------------------------------------------ YouTube

def yt_chapters(chapters: list, duration: float) -> list:
    """YouTube's chapter rules: the first at 0:00, each at least 10 s, three or
    more (else none). A too-short one is dropped (the one before runs on)."""
    out = []
    for t, name in sorted(chapters):
        t = 0.0 if not out else t
        if out and t - out[-1][0] < 10:
            continue
        out.append((t, name))
    while len(out) > 1 and duration - out[-1][0] < 10:
        out.pop()
    return out if len(out) >= 3 else []


def music_credits(ids: list) -> str:
    import cc_music
    by = {t["id"]: t for t in cc_music.library()}
    return "; ".join(f"\"{by[i].get('title') or i}\" by {by[i].get('artist') or 'unknown'}" for i in ids if i in by)


def _series_tags(ep: dict, topic: str) -> list:
    """Search terms people use for each series."""
    series = ep["series"]
    if series == "week":
        return ["fortnite item shop today", "fortnite item shop comebacks", "returning fortnite skins"]
    if series == "countdown":
        many = KINDS[ep["kind"]][1]
        return {"longest_gone": [f"fortnite {many} gone the longest", f"rarest fortnite {many}", f"og fortnite {many}"],
                "rarest": [f"rarest fortnite {many}", f"rare fortnite {many}", f"og fortnite {many}"],
                "most_common": [f"most common fortnite {many}", f"fortnite {many}"]}[ep["metric"]]
    if series == "season":
        return [f"fortnite {topic.lower().replace(',', '')}", "fortnite season skins", "og fortnite skins"]
    if series == "month":
        return [f"fortnite item shop {topic.lower()}", "fortnite throwback", "old fortnite skins"]
    return [f"fortnite {topic.lower().replace('the rarest ', '')}", "rarest fortnite skins"]


def describe(out: dict, day: date) -> dict:
    """YouTube's title, description (with chapters) and tags for a built episode."""
    import cc_long as L
    rows = out["rows"]
    chapters = yt_chapters(out["chapters"], out["comp"].duration)
    credits = music_credits(getattr(out["comp"], "music_used", []))
    lines = [out["hook"][1].replace(" 👀", ""), "",
             f"Every number here comes from the Fortnite Item Shop's own records, as of {d_short(day)}. "
             "A few days in a row in the shop counts as one time.", ""]
    if chapters:
        lines += ["Chapters", L.chapters_text(chapters), ""]
    lines += ["The list"] + [f"#{i + 1} {r['name']}" for i, r in enumerate(rows)] + [""]
    lines += ["💚 Support the channel: use Creator Code BAD in the Item Shop #EpicPartner",
              "🔔 A new video every weekday.", ""]
    if credits:
        lines += [f"🎵 Music (public domain, CC0): {credits}", ""]
    lines += ["Portions of the materials used are trademarks and/or copyrighted works of Epic Games, Inc. All rights "
              "reserved by Epic. This material is not official and is not endorsed by Epic.", "",
              "#usecodebad #creatorcodebad #codebad #EpicPartner #fortnite"]
    desc = "\n".join(lines).strip()
    if len(desc) > 4900:
        desc = desc[:4900].rsplit("\n", 1)[0]
    tags, total = [], 0
    for t in (["usecodebad", "creatorcodebad", "codebad", "creator code bad", "fortnite", "fortnite item shop"]
              + _series_tags(out["episode"], out["topic"])
              + ["fortnite skins", "item shop history"] + [r["name"] for r in rows[:8]]):
        t = t.replace("<", "").replace(">", "").replace(",", "")[:60]
        if t and t.lower() not in {x.lower() for x in tags} and total + len(t) + 1 <= 480:
            tags.append(t)
            total += len(t) + 1
    return {"title": out["title"], "description": desc, "tags": tags, "chapters": chapters}


def thumbnail(out: dict, path: Path) -> Path:
    """The YouTube thumbnail, 1280x720 JPEG under 2 MB: the topic in huge
    outline type, the hook in lime, number one big on its tile with two more
    behind it, and the code; the bottom-right corner stays clear (YouTube
    prints the length there)."""
    import cc_code_entry as CE
    import cc_motion as M
    from cc_looks import PREP_JS
    from playwright.sync_api import sync_playwright
    rows = out["rows"]
    comp = CE.Frame(1.0, 1280, 720, "#0A0A0B")
    comp.use_fonts(ED.FONT, "Liberation Sans")
    comp.css(ED.CSS + CE.CSS)
    tiles = ""
    spots = [(800, 120, 360, 490, 4, 3), (700, 50, 250, 340, -8, 1), (1010, 40, 250, 340, 9, 2)]
    for i, (r, (x, y, w, h, rot, z)) in enumerate(zip(rows[:3], spots)):
        tiles += ED.tile(f'src="{r["uri"]}"', r["item"], x, y, w, h, f"th{i}", trim=trim_for(r["item"]),
                         extra=f"transform:rotate({rot}deg);z-index:{z}")
    lines_, lime = out["thumb"]
    lines_ = lines_.upper().split("\n")[:3]
    size = min(_fit(r, 640, 132, 60) for r in lines_)
    text, top = "", 40
    for r in lines_:
        text += ED.outline(r, 44, top, size, -1, align="left", width=660)
        top += size * 1.04
    text += ED.caption(lime.upper(), 48, top + 22, _fit(lime.upper(), 600, 50, 30), -1, style="lime", align="left",
                       width=640, weight=900, rot=-2)
    colors = ED.tile_colors(rows[0]["item"])
    comp.add(PREP_JS)
    comp.add(ED.PREP)
    comp.add(f'<div class="full" style="background:radial-gradient(ellipse 70% 90% at 76% 45%,{colors[0]} 0%,'
             f'{colors[1]} 48%,#0a0a0b 100%)"></div>' + tiles + text
             + '<div class="abs" style="left:48px;top:548px;width:0;height:0;z-index:110;transform:scale(.52);'
               'transform-origin:0 0">' + ED.code(0, 0) + '</div>')
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=M.CHROME_ARGS)
        pg = br.new_page(viewport={"width": 1280, "height": 720})
        pg.set_content(comp.document(), wait_until="load")
        pg.evaluate(M.READY_JS)
        png = CE._stable(pg, 500, True, False)
        br.close()
    from io import BytesIO
    from PIL import Image
    img = Image.open(BytesIO(png)).convert("RGB")
    for q in (92, 88, 82, 75):
        img.save(path, "JPEG", quality=q, optimize=True)
        if path.stat().st_size < 1_900_000:
            break
    return path
