"""
The long videos from creator-code/lineup.json's "long_v2_from" day on: three a
week on YouTube, one show a day, 3 PM Chicago (cc_long_build posts them).

    Mon  THE DATA SAYS  a question answered from the Item Shop's own records,
                        in turn: the most overdue skins (gone far longer than
                        their own usual time away), a season's shop skins where
                        are they now, the biggest comebacks in the shop's
                        history, this month some years back then and now. From
                        November 2026 the first Monday of each month wraps up
                        the month before instead.
    Wed  COUNTDOWN      the 30 rarest / gone the longest / most common: skins,
                        emotes, pickaxes, back blings, gliders, the big collabs
                        (Marvel, DC, Star Wars, Icon Series, Gaming Legends) and
                        the biggest sets, in a fixed order that takes months to
                        come round; every Fortnitemares skin on the last
                        Wednesday of October.
    Sat  QUIZ NIGHT     40 levels from easy to impossible (cc_long_quiz): the
                        skin from its silhouette, which came first, zoomed in,
                        guess the season, in turn; the Fortnitemares edition on
                        Halloween's Saturday.

    show_for(day)                -> "data" | "countdown" | "quiz" | "classic" | None
    out = build(day, hist, art, out_dir, accept=...)
    meta = describe(out, day)    # YouTube title, description, tags, chapters

Truth rules as in cc_long_series: every number from the records up to the
video's day, nothing about why an item is gone or whether it will come back.
"Overdue" is always measured against the item's own gaps between visits.
CC_LONG_SHOW (data / countdown / quiz) and CC_LONG_EPISODE (JSON) force a show
or an episode for samples.
"""

import json
import os
import random
from datetime import date, timedelta
from pathlib import Path

import cc_edit as ED
import cc_edit_long as LE
import cc_long_series as SER
import cc_rarity as R
from cc_common import CC_DIR, log
from cc_long_series import (KINDS, MIN_ROWS, MONTHS, Times, _entry, _facts, _fit, _raw_kind, _raw_value,
                            cta_screen, d_short, item_screen, outro_screen, title_screen)
from cc_motion import esc, trim_for

W, H = LE.W, LE.H
LINEUP = CC_DIR / "lineup.json"
SEASONS = CC_DIR / "quiz" / "seasons.json"
V2_DAYS = {0: "data", 2: "countdown", 5: "quiz"}      # Monday, Wednesday, Saturday
V2_EPOCH = date(2026, 10, 5)                          # a Monday: week 0 of the rotations
WRAPPED_FROM = date(2026, 11, 2)                      # the first monthly wrap-up
COUNT = 30                                            # items in a countdown
OVERDUE_COUNT = 25
COMEBACK_COUNT = 25
CADENCE = "There's a new one every Monday, Wednesday and Saturday."
LIME = ED.LIME
PAPER = "#F3F2EC"
GREY = "#A7B0B9"


class Days(int):
    """A count of days: said 'one thousand ... days', shown '1,785 days'."""


def two(template: str, **values) -> tuple:
    """cc_long_series.two, plus Days."""
    spoken = {k: (f"{SER.words(int(v))} days" if isinstance(v, Days) else v) for k, v in values.items()}
    shown = {k: (f"{int(v):,} days" if isinstance(v, Days) else v) for k, v in values.items()}
    return SER.two(template, **spoken)[0], SER.two(template, **shown)[1]


# ------------------------------------------------------------------ schedule

def v2_from() -> date | None:
    try:
        v = json.loads(LINEUP.read_text()).get("long_v2_from")
    except (OSError, ValueError):
        return None
    return date.fromisoformat(v) if v else None


def show_for(day: date) -> str | None:
    """Which long video `day` gets: a v2 show on its three days from long_v2_from
    on (none on the other four), the five weekday series before it."""
    forced = os.environ.get("CC_LONG_SHOW", "").strip()
    if forced:
        return forced
    start = v2_from()
    if start and day >= start:
        return V2_DAYS.get(day.weekday())
    return "classic" if day.weekday() <= 4 else None


def _wrapped_day(day: date) -> bool:
    return day >= WRAPPED_FROM and day.weekday() == 0 and day.day <= 7


def _data_k(day: date) -> int:
    """How many regular (not wrap-up) Mondays came before `day` since the epoch."""
    k, m = 0, V2_EPOCH
    while m < day:
        k += not _wrapped_day(m)
        m += timedelta(days=7)
    return k


# Mondays, in turn (a wrap-up Monday doesn't use a turn). The second overdue and
# comebacks of each round go through the other kinds, round by round.
DATA_CYCLE = [("overdue", "outfit"), ("season", None), ("comebacks", "outfit"), ("month", None),
              ("overdue", "*"), ("season", None), ("comebacks", "*"), ("month", None)]
OTHER_KINDS = ["emote", "pickaxe", "backpack", "glider"]

# Wednesdays, in turn: skins most often, the collabs between.
CD_CYCLE = [
    {"series": "countdown", "metric": "rarest", "kind": "outfit"},
    {"series": "collection", "field": "series", "value": "MARVEL SERIES", "nice": "Marvel"},
    {"series": "countdown", "metric": "longest_gone", "kind": "outfit"},
    {"series": "collection", "field": "series", "value": "Icon Series", "nice": "Icon Series"},
    {"series": "countdown", "metric": "rarest", "kind": "emote"},
    {"series": "collection", "field": "series", "value": "DC SERIES", "nice": "DC"},
    {"series": "countdown", "metric": "most_common", "kind": "outfit"},
    {"series": "collection", "field": "series", "value": "Star Wars Series", "nice": "Star Wars"},
    {"series": "countdown", "metric": "longest_gone", "kind": "pickaxe"},
    {"series": "collection", "field": "series", "value": "Gaming Legends Series", "nice": "Gaming Legends"},
    {"series": "countdown", "metric": "longest_gone", "kind": "emote"},
    {"series": "collection", "set_index": 0},
    {"series": "countdown", "metric": "rarest", "kind": "backpack"},
    {"series": "countdown", "metric": "rarest", "kind": "pickaxe"},
    {"series": "collection", "set_index": 1},
    {"series": "countdown", "metric": "most_common", "kind": "emote"},
    {"series": "countdown", "metric": "longest_gone", "kind": "backpack"},
    {"series": "collection", "set_index": 2},
    {"series": "countdown", "metric": "rarest", "kind": "glider"},
    {"series": "countdown", "metric": "most_common", "kind": "pickaxe"},
    {"series": "collection", "set_index": 3},
    {"series": "countdown", "metric": "longest_gone", "kind": "glider"},
]

QUIZ_CYCLE = ["whos_that", "which_first", "zoomed_in", "guess_season"]


def _week(day: date) -> int:
    return (day - V2_EPOCH).days // 7


def _last_weekday_of_month(day: date) -> bool:
    return (day + timedelta(days=7)).month != day.month


def data_episodes(day: date) -> list:
    if _wrapped_day(day):
        prev = day.replace(day=1) - timedelta(days=1)
        first = {"series": "wrapped", "year": prev.year, "month": prev.month}
        k = _data_k(day)
    else:
        k = _data_k(day)
        rnd_, i = divmod(k, len(DATA_CYCLE))
        typ, kind = DATA_CYCLE[i]
        first = {"series": typ, "index": k}
        if kind:
            first["kind"] = OTHER_KINDS[rnd_ % len(OTHER_KINDS)] if kind == "*" else kind
    alts = [{"series": "overdue", "kind": "outfit"}, {"series": "comebacks", "kind": "outfit"},
            {"series": "season", "index": k + 1}, {"series": "month", "index": k + 1},
            {"series": "overdue", "kind": "emote"}]
    same = (first["series"], first.get("kind"))
    return [first] + [a for a in alts if (a["series"], a.get("kind")) != same]


def countdown_episodes(day: date) -> list:
    wk = _week(day)
    first = dict(CD_CYCLE[wk % len(CD_CYCLE)])
    if day.month == 10 and _last_weekday_of_month(day):
        first = {"series": "seasonal", "event": "fortnitemares"}
    alts = [dict(CD_CYCLE[(wk + j) % len(CD_CYCLE)]) for j in (5, 9, 13)]
    return [first] + [a for a in alts if a != first] + [{"series": "countdown", "metric": "rarest", "kind": "outfit"}]


def quiz_episodes(day: date) -> list:
    wk = _week(day)
    fmt = QUIZ_CYCLE[wk % len(QUIZ_CYCLE)]
    first = {"series": "quiz", "format": fmt}
    if day.month == 10 and day.day >= 25:
        first = {"series": "quiz", "format": "whos_that", "event": "fortnitemares"}
    alts = [{"series": "quiz", "format": f} for f in QUIZ_CYCLE if f != fmt]
    return [first] + alts


def episodes(day: date, show: str | None = None) -> list:
    show = show or show_for(day)
    shows = {"data": data_episodes, "countdown": countdown_episodes, "quiz": quiz_episodes}
    listed = shows.get(show, lambda d: [])(day)
    forced = os.environ.get("CC_LONG_EPISODE", "").strip()
    if forced:
        ep = json.loads(forced)
        return [ep] + [e for e in listed if e != ep][:2]
    return listed


# ------------------------------------------------------------------ shared pieces

def _open(lv, title: str, sub: str, lines: list, rows: list):
    lv.segment(lines, lambda lv_, s: title_screen(lv_, s, title, sub, rows), chapter="Intro", cue="", min_len=10)


def _close(lv, question, rows: list, done: str = "And that's the list."):
    ask = question if isinstance(question, str) else question[1]
    lv.segment([done, question,
                f"If you want more like this, subscribe. {CADENCE} 🔔",
                ("And if you're buying anything in the Item Shop, use code B, A, D. See you next time.",
                 "And if you're buying anything in the Item Shop, use code BAD. See you next time! 💚")],
               lambda lv_, s: outro_screen(lv_, s, rows, ask.lower()), chapter="Outro", min_len=11)


def _cta(lv, rank: int):
    lv.segment([two("Quick one before the top {n}.", n=rank),
                ("If you're buying anything in the Item Shop, you can support the channel with code B, A, D.",
                 "If you're buying anything in the Item Shop, you can support the channel with code BAD."),
                "Just type it into the Support-A-Creator box. Thanks, it really helps. 💚"],
               cta_screen, cue="swoosh", min_len=8)


def run_countdown(lv, rows: list, lines_for, screen):
    """#N down to #1 (rows[0] is #1), the ask for the code before the top ten,
    chapters at the start, #20, #10, #5 and #1. lines_for(row, rank) ->
    (lines, entry for screen(lv, seg, entry))."""
    n = len(rows)
    cta_before = 10 if n >= 16 else max(2, n // 2)
    marks = {n, 20, 10, 5, 1}
    for rank in range(n, 0, -1):
        r = rows[rank - 1]
        lines, e = lines_for(r, rank)
        if rank == cta_before and rank != n:
            _cta(lv, rank)
        lv.segment(lines, lambda lv_, s, e=e: screen(lv_, s, e),
                   chapter=f"#{rank} {r['name']}" if rank in marks else "", min_len=8)


OPENERS = SER.OPENERS


def _opener(rank: int, day: date, name: str) -> tuple:
    op = "And number {w}: {name}." if rank == 1 else OPENERS[(rank + day.toordinal()) % len(OPENERS)]
    return two(op, w=rank, name=name)


def _dedupe_sets(cands: list, keyf, count: int, hist, art) -> list:
    """Rows with art, at most one per set with the same record (keyf(c) -> the
    record's key, e.g. its last day): a set sold as a bundle moves together."""
    rows, seen = [], set()
    for c in cands:
        key = c["key"]
        s = _raw_value(hist.items[key], "set")
        if s and (s, keyf(c)) in seen:
            continue
        e = _entry(hist, key, art)
        if not e:
            continue
        if s:
            seen.add((s, keyf(c)))
        rows.append(dict(c, **e))
        if len(rows) == count:
            break
    return rows


# ------------------------------------------------------------------ overdue

def overdue_rows(hist: R.History, day: date, kind: str, art, count: int = OVERDUE_COUNT) -> list:
    import cc_fmt_overdue as OD
    cands = OD.overdue(hist, day, kind, min_runs=6, min_days=180, min_factor=3.0)
    return _dedupe_sets(cands, lambda c: c["last"], count, hist, art)


_TL_CSS = """
@keyframes tlwipe{from{clip-path:inset(-30px 100% -30px 0)}to{clip-path:inset(-30px 0 -30px 0)}}
@keyframes tlgrow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.tl-bar{position:absolute;background:#F3F2EC;border-radius:3px}
.tl-lab{position:absolute;font:700 22px/1 'TikTok Sans',sans-serif;color:#C9D0D6;white-space:nowrap}
"""

TL_X0, TL_X1 = 880, 1790          # the time axis: the window's first day .. the video's day
TL_Y, TL_H = 596, 54


def _css_once(lv, key: str, css: str):
    done = getattr(lv, "_css_done", set())
    if key not in done:
        lv.comp.css(css)
        done.add(key)
        lv._css_done = done


def _timeline(runs: list, day: date, t_sweep: float, t_grow: float, grow: float) -> str:
    """Every Item Shop visit as a bar on one time axis up to `day`, swept in
    from the left at t_sweep; the empty stretch since the last one grows in
    lime from t_grow, and TODAY lands at its end."""
    import cc_fmt_overdue as OD
    width = TL_X1 - TL_X0
    start, _ = OD._window(runs, day, width)
    ppd = width / max(1, (day - start).days)
    bars = ""
    for a, b in runs:
        if b < start:
            continue
        a = max(a, start)
        x = (a - start).days * ppd
        w = max(3.0, ((b - a).days + 1) * ppd)
        bars += f'<div class="tl-bar" style="left:{x:.1f}px;top:0;width:{w:.1f}px;height:{TL_H}px"></div>'
    ticks = (f'<div style="position:absolute;left:0;top:{TL_H + 4}px;width:{width}px;height:2px;'
             f'background:rgba(255,255,255,.3)"></div>')
    for y in range(start.year + 1, day.year + 1):
        x = (date(y, 1, 1) - start).days * ppd
        if 30 <= x <= width - 40:
            ticks += (f'<div style="position:absolute;left:{x:.0f}px;top:{TL_H + 4}px;width:2px;height:12px;'
                      f'background:rgba(255,255,255,.45)"></div>'
                      f'<div class="tl-lab" style="left:{x - 30:.0f}px;top:{TL_H + 22}px;width:60px;'
                      f'text-align:center">{y}</div>')
    strip = (f'<div style="position:absolute;left:{TL_X0}px;top:{TL_Y}px;width:{width}px;height:{TL_H + 50}px;'
             f'animation:tlwipe .9s cubic-bezier(.2,.8,.2,1) {t_sweep:.2f}s 1 normal both">{bars}{ticks}</div>')
    last_x = TL_X0 + (runs[-1][1] - start).days * ppd + 3
    gap = (f'<div style="position:absolute;left:{last_x:.0f}px;top:{TL_Y - 6}px;width:{TL_X1 - last_x:.0f}px;'
           f'height:{TL_H + 12}px;background:rgba(232,255,58,.26);border:3px solid {LIME};border-radius:6px;'
           f'box-sizing:border-box;transform-origin:0 50%;'
           f'animation:tlgrow {grow:.2f}s cubic-bezier(.3,.1,.3,1) {t_grow:.2f}s 1 normal both"></div>')
    since = f"every item shop visit since {MONTHS[start.month - 1].lower()} {start.year}"
    label = (f'<div class="tl-lab" style="left:{TL_X0}px;top:{TL_Y - 44}px;font-size:24px;color:#E4E8EC;'
             f'animation:fadein .001s linear {t_sweep:.2f}s 1 normal both">{esc(since)}</div>')
    today = ED.caption("today", TL_X1 + 6, TL_Y - 58, 30, t_grow + grow, style="lime", align="right", width=220,
                       weight=900)
    return label + strip + gap + today


def overdue_screen(lv, seg, e: dict):
    _css_once(lv, "tl", _TL_CSS)
    it, uri = e["item"], e["uri"]
    x, y, w, h = 330, 170, 490, 620
    iid = lv.uid("t")
    tile = ED.tile(lv.src(uri), it, x, y, w, h, iid, trim=trim_for(it), fig=.94)
    lv.scene(seg.t0, seg.t1, ED.canvas(iid, ED.tile_colors(it), 1.3, .55) + tile)
    at = [a for a, _ in seg.lines_at] + [seg.t1] * 6
    col, cw = 880, 910
    over = ED.outline(f"#{e['rank']}", col, 104, 118, seg.t0, align="left", lime=e["rank"] == 1, width=500)
    over += ED.caption(e["name"], col, 252, _fit(e["name"], cw - 10, 62, 30), at[0] + .1, align="left", width=cw,
                       weight=800)
    t1 = at[1] if len(seg.lines_at) > 1 else seg.t0 + 1.5
    over += ED.caption(f"usually back within ~{e['typical']:,} days", col, 350, 34, t1 + .3, style="dark",
                       align="left", width=cw, weight=700)
    a2, b2 = seg.lines_at[min(2, len(seg.lines_at) - 1)]
    grow = max(.8, min(1.8, (b2 - a2) * .55))
    over += ED.caption("gone", col, 414, 34, a2 + .05, style="dark", align="left", width=200, weight=800)
    over += ED.caption(f"{ED.counter(e['gone'], a2 + .1, grow)} days", col + 130, 402, 84, a2 + .1, align="left",
                       width=cw - 130, weight=900, raw=True, lh=1.2)
    over += _timeline(e["runs"], e["day"], t1, a2 + .1, grow)
    stamp_at = min(seg.t1 - .6, a2 + .1 + grow + .45)
    over += ED.caption(f"{e['factor']}× longer than usual", col, 736, 46, stamp_at, style="lime", align="left",
                       width=cw, weight=900, rot=-2)
    lv.cue(a2 + .1 + grow, "impact")
    lv.cue(stamp_at, "slam")
    lv.cam.punch(stamp_at, .03, .3)
    if e.get("sticker"):
        over += ED.emoji(e["sticker"], x + w - 44, y + 40, 110, at[0] + .3, rot=12)
    lv.over(seg.t0, seg.t1, over)
    lv.cam.push(seg.t0, seg.t1, 1.0, 1.035, x + w / 2, y + h / 2)
    if e["rank"] % 2:
        lv.cam.whip(seg.t0, -1, 0, 520)
    else:
        lv.cam.zoom(seg.t0, .35)
    lv.cue(seg.t0, "impact")


def make_overdue(ep, day, hist, art, rnd, seed):
    kind = ep.get("kind", "outfit")
    one, many, cap = KINDS[kind]
    rows = overdue_rows(hist, day, kind, art)
    if len(rows) < MIN_ROWS:
        return None
    n = len(rows)
    for r in rows:
        r["typical"] = int(r["typical"])
        r["factor"] = int(r["factor"])
        r["times"] = len(r["runs"])
    top = rows[0]
    lv = LE.LongEdit(seed, f"The {n} Most Overdue Fortnite {cap}: Gone Way Longer Than Usual ({day:%B %Y})",
                     day=day)
    hook = two("Number {one} usually came back within about {t} days. It's been gone {g}. 👀", one=1,
               t=top["typical"], g=Days(top["gone"]))
    _open(lv, f"the most\noverdue\n{many}", f"{n} {many} · item shop records",
          [two("These are the {n} most overdue {m} in Fortnite.", n=n, m=many),
           "For each one, we measured how long it usually stayed away between visits to the Item Shop, "
           "and how long it's been gone now.",
           hook, two("Counting down to the most overdue, as of {d}. 👇", d=day)], rows)

    def lines_for(r, rank):
        l1 = two("It's been in the Item Shop {t}, and between visits it was usually back within about {n} days.",
                 t=Times(r["times"]), n=r["typical"])
        l2 = two("This time it's been gone {g}. That's {f} times longer than usual.", g=Days(r["gone"]),
                 f=r["factor"])
        facts = _facts(r, hist, day, rnd, frozenset({"gap", "total", "first"}))[:1 if rank <= 5 else 0]
        e = dict(item=r["item"], uri=r["uri"], rank=rank, name=r["name"], typical=r["typical"], gone=r["gone"],
                 factor=r["factor"], runs=r["runs"], day=day, sticker="👑" if rank == 1 else "")
        return [_opener(rank, day, r["name"]), l1, l2] + [f[0] for f in facts], e

    run_countdown(lv, rows, lines_for, overdue_screen)
    _close(lv, "Which one do you want back first?", rows)
    thumb = {"family": "stamp", "stamp": "OVERDUE", "stat": lambda r: f"{r['factor']}× LONGER", "sub": "THAN USUAL",
             "kicker": "OVERDUE", "rows": rows}
    return lv, rows, f"the most overdue {many}", hook, thumb


# ------------------------------------------------------------------ comebacks

def comeback_rows(hist: R.History, day: date, kind: str, art, count: int = COMEBACK_COUNT) -> list:
    """Each item's longest time away that ended in a return, up to `day`; the
    longest first."""
    cands = []
    for key, days in hist.days.items():
        raw = hist.items[key]
        if _raw_kind(raw) != kind:
            continue
        runs = R._runs([d for d in days if d <= day])
        best = None
        for a, b in zip(runs, runs[1:]):
            gap = (b[0] - a[1]).days
            if best is None or gap > best[0]:
                best = (gap, a[1], b[0])
        if best and best[0] >= 365:
            cands.append({"key": key, "days": best[0], "last": best[1], "back_on": best[2], "times": len(runs)})
    cands.sort(key=lambda c: (-c["days"], c["back_on"], c["key"]))
    return _dedupe_sets(cands, lambda c: c["back_on"], count, hist, art)


def _years_word(days: int) -> str:
    y = int(days // 365.25)
    return f"{y}+ YEARS" if y >= 2 else f"{days:,} DAYS"


def make_comebacks(ep, day, hist, art, rnd, seed):
    kind = ep.get("kind", "outfit")
    one, many, cap = KINDS[kind]
    rows = comeback_rows(hist, day, kind, art)
    if len(rows) < MIN_ROWS:
        return None
    n = len(rows)
    top = rows[0]
    lv = LE.LongEdit(seed, f"The {n} Biggest Comebacks in Fortnite Item Shop History: {cap} Gone for Years", day=day)
    hook = two("The biggest one was gone for {g} before it came back. 👀", g=Days(top["days"]))
    _open(lv, "the biggest\ncomebacks\never", f"{n} {many} · item shop records",
          [two("These are the {n} biggest comebacks in the history of the Fortnite Item Shop.", n=n),
           two("{m} that left the shop, stayed gone for years, and then came back.", m=cap),
           hook, two("Counting down to the longest time away, as of {d}. 👇", d=day)], rows)

    def lines_for(r, rank):
        line = two("It left the Item Shop on {a}, and came back on {b}: {g} later.", a=r["last"], b=r["back_on"],
                   g=Days(r["days"]))
        facts = _facts(r, hist, day, rnd, frozenset({"gap"}))[:2 if rank <= 5 else 1]
        e = dict(item=r["item"], uri=r["uri"], rank=rank, name=r["name"], value=r["days"], unit="days",
                 kicker="gone for", facts=[(f[1], 2 + j) for j, f in enumerate(facts)],
                 sticker="👑" if rank == 1 else "")
        return [_opener(rank, day, r["name"]), line] + [f[0] for f in facts], e

    run_countdown(lv, rows, lines_for, lambda lv_, s, e: item_screen(lv_, s, e, "whip" if e["rank"] % 2 else "zoom"))
    _close(lv, "Which comeback were you waiting for?", rows)
    thumb = {"family": "hero_stat", "kicker": "BACK AFTER", "stat": lambda r: _years_word(r["days"]),
             "stamp": "BACK!", "rows": rows}
    return lv, rows, f"the biggest comebacks: {many}", hook, thumb


# ------------------------------------------------------------------ wrapped: last month

def wrapped_rows(hist: R.History, y: int, month: int, art) -> dict | None:
    """The month's numbers from the records: items for sale, new ones, the
    comebacks (back after 90+ days, longest first), the most days in the shop."""
    m0 = date(y, month, 1)
    m1 = date(y + (month == 12), month % 12 + 1, 1)
    sold, new, back, most = set(), [], [], []
    kinds = {"outfit", "emote", "pickaxe", "backpack", "glider"}
    for key, days in hist.days.items():
        raw = hist.items[key]
        if _raw_kind(raw) not in kinds:
            continue
        inside = [d for d in days if m0 <= d < m1]
        if not inside:
            continue
        sold.add(key)
        if days[0] >= m0 and days[0] >= R.FIRST_SURE:
            new.append({"key": key, "first": days[0]})
        for a, _ in R._runs([d for d in days if d < m1]):
            if m0 <= a < m1:
                prev = [d for d in days if d < a]
                if prev and (a - prev[-1]).days >= 90:
                    back.append({"key": key, "days": (a - prev[-1]).days, "back_on": a, "last": prev[-1],
                                 "times": len(R._runs([d for d in days if d < m1]))})
        if _raw_kind(raw) == "outfit":
            most.append({"key": key, "ndays": len(inside)})
    if len(sold) < 50:
        return None
    back.sort(key=lambda c: (-c["days"], c["key"]))
    best = {}
    for c in back:
        best.setdefault(c["key"], c)
    back_rows = _dedupe_sets(list(best.values()), lambda c: c["back_on"], 15, hist, art)
    new_skins = [c for c in new if _raw_kind(hist.items[c["key"]]) == "outfit"]
    new_skins.sort(key=lambda c: (c["first"], c["key"]))
    new_rows = _dedupe_sets(new_skins, lambda c: c["first"], 10, hist, art)
    most.sort(key=lambda c: (-c["ndays"], c["key"]))
    most_rows = _dedupe_sets(most, lambda c: c["ndays"], 5, hist, art)
    return {"sold": len(sold), "new": len(new), "new_skins": len(new_skins), "back_count": len(best),
            "back": back_rows, "new_rows": new_rows, "most": most_rows, "start": m0, "end": m1 - timedelta(days=1)}


def stat_screen(lv, seg, e: dict):
    """Three big numbers of the month, landing one per line, over its first
    comeback's canvas."""
    first = e["rows"][0]
    iid = lv.uid("t")
    tile = ED.tile(lv.src(first["uri"]), first["item"], 1380, 300, 360, 470, iid, trim=trim_for(first["item"]),
                   extra="transform:rotate(3deg)")
    lv.scene(seg.t0, seg.t1, ED.canvas(iid, ED.tile_colors(first["item"]), 1.0, .66) + tile)
    at = [a for a, _ in seg.lines_at] + [seg.t1] * 6
    over = ED.caption(e["heading"], 360, 150, _fit(e["heading"], 1000, 52, 30), seg.t0 + .1, style="box",
                      align="left", width=1000, weight=900)
    y = 290
    for k, (value, label) in enumerate(e["stats"]):
        t = at[min(k + 1, len(at) - 1)]
        over += ED.caption(f"{ED.counter(value, t + .05, .9)}", 360, y, 110, t + .05, align="left", width=520,
                           weight=900, raw=True, lh=1.1, style="out")
        over += ED.caption(label, 800, y + 40, _fit(label, 540, 40, 26), t + .3, style="dark", align="left",
                           width=560, weight=800)
        lv.cue(t + .95, "impact")
        y += 170
    lv.over(seg.t0, seg.t1, over)
    lv.cam.push(seg.t0, seg.t1, 1.0, 1.04, W / 2, H / 2)


def make_wrapped(ep, day, hist, art, rnd, seed):
    y, month = ep["year"], ep["month"]
    data = wrapped_rows(hist, y, month, art)
    if not data or len(data["back"]) < 8:
        return None
    label = f"{MONTHS[month - 1]} {y}"
    back = data["back"]
    lv = LE.LongEdit(seed, f"{label} in the Fortnite Item Shop: Every Big Comeback, New Skin and Record", day=day)
    top = back[0]
    hook = two("And the biggest comeback of the month had been gone {g}. 👀", g=Days(top["days"]))
    _open(lv, f"{MONTHS[month - 1]}\n{y}\nwrapped", f"the item shop in {label.lower()} · by the numbers",
          [two("{m} in the Fortnite Item Shop, wrapped up.", m=label),
           "The comebacks, the new skins, and the ones that just wouldn't leave.",
           hook, "All from the Item Shop's own records. Let's go. 👇"], back)
    lv.segment([two("First, the numbers. In {m}:", m=label),
                two("{n} different cosmetics were for sale.", n=data["sold"]),
                two("{n} of them were brand new.", n=data["new"]),
                two("And {n} came back after three months or more away.", n=data["back_count"])],
               lambda lv_, s: stat_screen(lv_, s, {"rows": back, "heading": f"{label.lower()} in numbers",
                                                   "stats": [(data["sold"], "cosmetics for sale"),
                                                             (data["new"], "brand new"),
                                                             (data["back_count"], "back after 3+ months")]}),
               chapter="The numbers", min_len=10)
    if len(data["new_rows"]) >= 4:
        nr = data["new_rows"]
        names = [r["name"] for r in nr[:3]]
        lv.segment([two("{n} skins hit the Item Shop for the very first time.", n=data["new_skins"]),
                    ("Including " + ", ".join(names[:-1]) + " and " + names[-1] + "." if len(names) > 1 else
                     f"Including {names[0]}."),
                    "Here are some of them. 👇"],
                   lambda lv_, s: SER.grid_screen(lv_, s, f"new in {MONTHS[month - 1].lower()}", nr,
                                                  [d_short(r["first"]).rsplit(",", 1)[0] for r in nr]),
                   chapter="New skins", min_len=9)
    if len(data["most"]) >= 3:
        mr = data["most"]
        lv.segment([two("The skin you saw the most: {name}, in the shop on {n} days that month.", name=mr[0]["name"],
                        n=mr[0]["ndays"]),
                    "Here's who else just wouldn't leave. 👇"],
                   lambda lv_, s: SER.grid_screen(lv_, s, "most days in the shop", mr,
                                                  [f"{r['ndays']} days" for r in mr]),
                   chapter="Most days in the shop", min_len=8)
    lv.segment([two("Now, the {n} biggest comebacks of {m}.", n=len(back), m=label),
                "Counting down to the one that had been gone the longest. 👇"],
               lambda lv_, s: title_screen(lv_, s, "biggest\ncomebacks", label.lower(), back[:3]),
               chapter="Biggest comebacks", min_len=6)

    def lines_for(r, rank):
        line = two("It came back on {b}, after {g} away.", b=r["back_on"], g=Days(r["days"]))
        facts = _facts(r, hist, day, rnd, frozenset({"gap"}))[:1]
        e = dict(item=r["item"], uri=r["uri"], rank=rank, name=r["name"], value=r["days"], unit="days",
                 kicker="back after", facts=[(f[1], 2 + j) for j, f in enumerate(facts)],
                 sticker="👑" if rank == 1 else "")
        return [_opener(rank, day, r["name"]), line] + [f[0] for f in facts], e

    run_countdown(lv, back, lines_for,
                  lambda lv_, s, e: item_screen(lv_, s, e, "whip" if e["rank"] % 2 else "zoom"))
    _close(lv, two("What was your favourite moment of {m}?", m=label), back, done=two("That was {m}.", m=label))
    thumb = {"family": "calendar", "month": MONTHS[month - 1][:3].upper(), "year": str(y), "word": "WRAPPED",
             "rows": back}
    return lv, back, f"{label} wrapped", hook, thumb


# ------------------------------------------------------------------ countdowns

def _seasonal_keys(hist: R.History, event: str) -> set:
    """Outfits from seasons.json's lists, each also first in the Item Shop in
    that year's window (the Fortnite Wiki's lists, checked against the records)."""
    try:
        s = json.loads(SEASONS.read_text())[event]
    except (OSError, ValueError, KeyError):
        return set()
    lo, hi = s.get("window", ["09-15", "11-15"])
    by_name = {}
    for key, raw in hist.items.items():
        if _raw_kind(raw) == "outfit":
            by_name.setdefault((raw.get("name") or "").strip().lower(), []).append(key)
    out = set()
    for year, rows in (s.get("years") or {}).items():
        for name, typ in rows:
            if typ != "Outfit":
                continue
            for key in by_name.get(name.strip().lower(), []):
                days = hist.days.get(key) or []
                if days and str(days[0].year) == year and lo <= days[0].strftime("%m-%d") <= hi:
                    out.add(key)
    return out


def _times_badge(r: dict) -> str:
    return "ONLY ONCE" if r["times"] == 1 else f"{r['times']} TIMES EVER"


def make_countdown(ep, day, hist, art, rnd, seed):
    series = ep["series"]
    if series == "countdown":
        got = SER._make(ep, day, hist, art, rnd, seed, cadence=CADENCE)
        if not got:
            return None
        lv, rows, topic, hook, (_, _) = got
        metric = ep["metric"]
        _, many, _ = KINDS[ep["kind"]]
        if metric == "longest_gone":
            thumb = {"family": "hero_stat", "kicker": "GONE FOR", "stat": lambda r: _years_word(r["days"]),
                     "stamp": "GONE", "rows": rows}
        elif metric == "rarest":
            thumb = {"family": "podium", "words": ["RAREST", many.upper()], "badge": _times_badge, "rows": rows}
        else:
            thumb = {"family": "podium", "words": ["MOST", "COMMON"],
                     "badge": lambda r: f"{r['times']} TIMES", "rows": rows}
        return lv, rows, topic, hook, thumb
    if series == "collection":
        if "set_index" in ep:
            sets = [c for c in SER.collections(hist, day) if c[0] == "set"]
            if not sets:
                return None
            field, value, nice = sets[ep["set_index"] % len(sets)]
        else:
            field, value, nice = ep["field"], ep["value"], ep["nice"]
        got = SER._make({"series": "collection", "field": field, "value": value, "nice": nice, "index": 0}, day,
                        hist, art, rnd, seed, cadence=CADENCE)
        if not got:
            return None
        lv, rows, topic, hook, _ = got
        return lv, rows, topic, hook, {"family": "podium", "words": ["RAREST", nice.upper()], "badge": _times_badge,
                                       "rows": rows}
    if series == "seasonal":
        keys = _seasonal_keys(hist, ep["event"])
        rows = SER.rows_by_times(hist, day, 40, art, lambda k, raw: k in keys and SER._aged(hist, k, day), True)
        if len(rows) < MIN_ROWS:
            return None
        n = len(rows)
        every = n >= len([k for k in keys if SER._aged(hist, k, day)])
        lv = LE.LongEdit(seed, (f"Every Fortnitemares Skin in the Item Shop, Rarest to Most Common ({day.year})"
                                if every else f"The {n} Rarest Fortnitemares Skins in the Item Shop ({day.year})"),
                         day=day)
        hook = SER._hook("fewest", rows[0])
        what = (("Every Halloween skin that's been sold in the Item Shop,",) * 2 if every else
                two("The {n} rarest Halloween skins sold in the Item Shop,", n=n))
        _open(lv, "the rarest\nfortnitemares\nskins", f"{n} halloween skins · item shop records",
              [(f"Fortnitemares. {what[0]} counting down to the rarest.",
                f"Fortnitemares. {what[1]} counting down to the rarest."),
               "Ranked by how many separate times each has been for sale, for everything out a year or more.",
               hook, two("As of {d}. 🎃👇", d=day)], rows)
        SER.countdown(lv, rows, day, hist, rnd, SER._stat_times(day))
        _close(lv, "Which Fortnitemares skin is the best?", rows)
        return lv, rows, "the rarest fortnitemares skins", hook, {
            "family": "podium", "words": ["RAREST", "HALLOWEEN"], "badge": _times_badge, "rows": rows,
            "theme": "halloween"}
    return None


# ------------------------------------------------------------------ build

def make(ep, day, hist, art, rnd, seed):
    series = ep["series"]
    if series == "overdue":
        return make_overdue(ep, day, hist, art, rnd, seed)
    if series == "comebacks":
        return make_comebacks(ep, day, hist, art, rnd, seed)
    if series == "wrapped":
        return make_wrapped(ep, day, hist, art, rnd, seed)
    if series in ("season", "month"):
        got = SER._make(ep, day, hist, art, rnd, seed, cadence=CADENCE)
        if not got:
            return None
        lv, rows, topic, hook, (lines_, lime) = got
        if series == "season":
            thumb = {"family": "podium", "words": [w.upper() for w in lines_.split("\n")][:2],
                     "badge": "WHERE ARE THEY NOW?", "rows": rows}
        else:
            month, _, year = topic.partition(" ")
            thumb = {"family": "calendar", "month": month[:3].upper(), "year": year, "word": "THEN & NOW", "rows": rows}
        return lv, rows, topic, hook, thumb
    if series in ("countdown", "collection", "seasonal"):
        return make_countdown(ep, day, hist, art, rnd, seed)
    if series == "quiz":
        import cc_long_quiz as Q
        return Q.make(ep, day, hist, art, rnd, seed)
    return None


def build(day: date, hist: R.History, art, out_dir: Path, seed: int | None = None, accept=None,
          show: str | None = None) -> dict | None:
    """The day's v2 long video, laid out and mixed (render with cc_long.render),
    or None when `day` has no show or no topic makes it. accept(out) -> bool is
    the caller's quality gate: a topic it turns down falls back to the next."""
    seed = seed if seed is not None else int(day.strftime("%Y%m%d"))
    show = show or show_for(day)
    for ep in episodes(day, show):
        got = make(ep, day, hist, art, random.Random(seed), seed)
        if not got:
            log(f"  long video {ep}: too few items, trying the next topic")
            continue
        lv, rows, topic, hook, thumb = got
        comp, wav, chapters = lv.build(out_dir, [(r["uri"], r["item"]["rarity"]) for r in rows[:5]])
        out = {"comp": comp, "wav": wav, "chapters": chapters, "title": lv.title[:100], "rows": rows,
               "episode": dict(ep, show=show), "topic": topic, "hook": hook, "thumb": thumb, "seed": seed,
               "show": show}
        if accept and not accept(out):
            log(f"  long video {ep}: turned down by the quality gate, trying the next topic")
            continue
        return out
    return None


# ------------------------------------------------------------------ YouTube

SHOW_TAGS = {
    "overdue": lambda m: [f"overdue fortnite {m}", f"fortnite {m} coming back", f"rarest fortnite {m}"],
    "comebacks": lambda m: ["fortnite item shop comebacks", f"returning fortnite {m}", f"og fortnite {m}"],
    "wrapped": lambda m: ["fortnite item shop recap", "fortnite item shop this month", "new fortnite skins"],
    "seasonal": lambda m: ["fortnitemares skins", "fortnite halloween skins", "rarest fortnitemares skins"],
}


def _tags(out: dict) -> list:
    ep = out["episode"]
    series = ep["series"]
    many = KINDS[ep["kind"]][1] if ep.get("kind") in KINDS else "skins"
    if series in SHOW_TAGS:
        return SHOW_TAGS[series](many)
    if series == "quiz":
        import cc_long_quiz as Q
        return Q.tags(ep)
    if series == "collection":
        return [f"rarest fortnite {ep.get('nice', '').lower()} skins".replace("  ", " "), "rarest fortnite skins"]
    return SER._series_tags(ep, out["topic"])


def describe(out: dict, day: date) -> dict:
    """YouTube's title, description (with chapters) and tags."""
    import cc_long as L
    rows, ep = out["rows"], out["episode"]
    chapters = SER.yt_chapters(out["chapters"], out["comp"].duration)
    credits = SER.music_credits(getattr(out["comp"], "music_used", []))
    quiz = ep["series"] == "quiz"
    if quiz:
        import cc_long_quiz as Q
        lines = Q.describe_lines(out)
    else:
        lines = [out["hook"][1].replace(" 👀", ""), "",
                 f"Every number here comes from the Fortnite Item Shop's own records, as of {d_short(day)}. "
                 "A few days in a row in the shop counts as one time.", ""]
    if chapters:
        lines += ["Chapters", L.chapters_text(chapters), ""]
    if not quiz:
        lines += ["The list"] + [f"#{i + 1} {r['name']}" for i, r in enumerate(rows)] + [""]
    lines += ["💚 Support the channel: use Creator Code BAD in the Item Shop #EpicPartner",
              "🔔 New videos every Monday, Wednesday and Saturday.", ""]
    if credits:
        lines += [f"🎵 Music (public domain, CC0): {credits}", ""]
    lines += ["Portions of the materials used are trademarks and/or copyrighted works of Epic Games, Inc. All rights "
              "reserved by Epic. This material is not official and is not endorsed by Epic.", "",
              "#usecodebad #creatorcodebad #codebad #EpicPartner #fortnite"]
    desc = "\n".join(lines).strip()
    if len(desc) > 4900:
        desc = desc[:4900].rsplit("\n", 1)[0]
    tags, total = [], 0
    names = [] if quiz else [r["name"] for r in rows[:8]]
    for t in (["usecodebad", "creatorcodebad", "codebad", "creator code bad", "fortnite", "fortnite item shop"]
              + _tags(out) + ["fortnite skins", "item shop history"] + names):
        t = t.replace("<", "").replace(">", "").replace(",", "")[:60]
        if t and t.lower() not in {x.lower() for x in tags} and total + len(t) + 1 <= 480:
            tags.append(t)
            total += len(t) + 1
    return {"title": out["title"], "description": desc, "tags": tags, "chapters": chapters}
