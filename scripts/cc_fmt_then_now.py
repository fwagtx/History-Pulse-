"""
THEN VS NOW for @usecodebad -- "THE ITEM SHOP: 2018 VS NOW": the Item Shop's own
records (cc_rarity) turned into five numbers, each with its own chart, on a
charcoal infographic page. Anton for the numbers, Inter for the words, THEN in
blue and NOW in the channel's lime.

    0:00  hook   THE ITEM SHOP / 2018 VS NOW: a skin first sold in 2018 beside one
                 first sold this year, NEARLY 12x MORE SKINS A DAY, and the big
                 USE CODE: BAD stamp, which flies into the corner badge.
    0:03  1      ON AN AVERAGE DAY: the two averages roll up, a square per skin
                 fills in under each, and the multiple lands.
    0:13  2      EVERY YEAR: different skins in the shop each year, one bar per
                 year from THEN to NOW (so far).
    0:24  3      BRAND-NEW: the same bars stretch to 100% and split into the skins
                 that were brand-new that year and the ones from earlier years.
    0:34  4      THE BUSIEST DAY: the most skins in the shop on one day, a square
                 per skin, a few of them standing by, and THEN's own record.
    0:45  5      THE REGULAR: the THEN skin in the shop the most times since, each
                 of those times a tick on a timeline.
    0:55  outro  WHICH SHOP WAS BETTER: THEN OR NOW? and the code, big.

What counts as an item: OUTFITS ("skins"). They are the one kind of cosmetic the
records list the same way in every year (back blings, for one, only show up on
their own from 2020 on, so counting every cosmetic would inflate NOW). Said on
screen and in the caption: "skins (outfits)".

Truth rules: cc_rarity's, plus
  - "on an average day"      <- distinct outfits in the shop each day the records
                                have, averaged over that year's days
  - "<year> SO FAR"          <- Jan 1 through the video's day (or the records'
                                last day, if earlier); a full year says just the year
  - "different skins in the shop in <year>"  <- outfits in the shop at least once
  - "brand-new that year"    <- its first day in the records is in that year; the
                                records start 2017-10-30 and the shop opened in
                                2017, so a year from 2018 on is always right
  - "busiest day on record"  <- the most outfits in the shop on one day, of all
                                the days in the records
  - "in the Item Shop N times" <- separate runs, consecutive days are one time
  - multiples: "12x" only when it is 12.0x to one decimal; "NEARLY 12x" for
    11.8-11.9x, "OVER 7x" for 7.0-7.2x, otherwise one decimal ("8.7x")
Never why, never what comes next.

    build(ctx, then=2018)   then: any full year of records (2018 on) before the
                            latest year; "2019 VS NOW", "2020 VS NOW" ...
"""

import math
from collections import Counter
from datetime import date

import cc_rarity as R
from cc_fmt_rarity import _item, _label_w, history
from cc_formats import Ctx, Video, _caption, _hashtags, num
from cc_looks import PREP_JS, pad_to
from cc_motion import (ACCENT, BADGE_H, BADGE_W, BADGE_X, BADGE_Y, EASE_OUT, INK, SAFE_BOTTOM, SAFE_LEFT,
                       SAFE_RIGHT, SAFE_RIGHT_TOP, W, Comp, an, anton_em, character, code_badge, disclosure, esc,
                       style_anim, trim_for)

# ------------------------------------------------------------------ look

BG = "#111113"
TEXT = "#F3F3EE"
MUTED = "#8E8E97"
RULE = "#2B2B31"
NOW_C = ACCENT                   # lime: NOW
THEN_C = "#5CB8FF"               # blue: THEN (validated against lime on this charcoal:
                                 # CVD dE 34, normal dE 36; every mark is also labelled)
MID_C = "#505159"                # the years in between
MIDNEW_C = "#9C9DA6"             # brand-new part of an in-between year
OLD_C = "#34353C"                # "in the shop in an earlier year" part

HOOK = 3.0
BEAT = 10.5                      # seconds per number
N_BEATS = 5
MIN_THEN_DAYS = 300              # a THEN year needs (nearly) every day on record
MIN_NOW_DAYS = 45                # fewer days this year: NOW is last year instead
MIN_RATIO = 1.2                  # the average day has to have grown this much

L, R_TOP, R_LOW = SAFE_LEFT, SAFE_RIGHT_TOP, SAFE_RIGHT     # 60, 1020, 900
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# The bar charts (beats 2 and 3): x 60-900, baseline at y 1232.
CH_L, CH_R, CH_BASE = L, R_LOW, 1232
CH_H2 = 400                      # beat 2: the tallest bar
CH_H3 = 386                      # beat 3: every column (100%)

CSS = f"""
.tn-bg{{position:absolute;inset:0;background:{BG}}}
.tn-bg .lit{{position:absolute;inset:0;background:radial-gradient(130% 70% at 22% 12%,#1d1d22 0%,{BG} 52%,#0a0a0c 100%)}}
.tn-bg .dots{{position:absolute;inset:0;opacity:.55;background-image:radial-gradient(rgba(255,255,255,.075) 1.3px,transparent 1.6px);
  background-size:36px 36px;background-position:18px 12px}}
.tn-t{{position:absolute;white-space:nowrap;line-height:1.05}}
.tn-i{{font-family:'Inter',sans-serif}}
.tn-a{{font-family:'Anton',Impact,sans-serif;text-transform:uppercase;letter-spacing:.01em;line-height:.9}}
.tn-line{{overflow:hidden;padding:.04em 0 .06em;margin:-.04em 0 -.06em}}
.tn-line>span{{display:inline-block;white-space:nowrap}}
.tn-rs{{position:absolute;top:0;white-space:nowrap;opacity:0}}
.tn-cell{{position:absolute;border-radius:7px}}
.tn-chip{{display:inline-block;font-family:'Anton',Impact,sans-serif;line-height:1;border-radius:8px;
  padding:.14em .32em .08em;letter-spacing:.02em}}
.tn-stamp{{display:inline-block;border-radius:14px;box-shadow:0 10px 0 rgba(0,0,0,.42),0 22px 34px rgba(0,0,0,.4)}}
.tn-x{{font-family:'Inter',sans-serif;font-weight:900;font-size:.88em;margin:0 .03em 0 .04em;vertical-align:.02em}}
.tn-panel{{position:absolute;border-radius:26px;background:linear-gradient(180deg,#1b1b20 0%,#141417 100%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 18px 40px rgba(0,0,0,.45)}}
@keyframes tnshow{{from{{opacity:1}}to{{opacity:1}}}}
@keyframes tnrise{{from{{transform:translateY(34px);opacity:0}}to{{transform:none;opacity:1}}}}
@keyframes tnup{{from{{transform:translateY(108%)}}to{{transform:none}}}}
@keyframes tnin{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes tngrow{{0%{{transform:scaleY(0)}}72%{{transform:scaleY(1.025)}}100%{{transform:scaleY(1)}}}}
@keyframes tnwide{{0%{{transform:scaleX(0)}}100%{{transform:scaleX(1)}}}}
@keyframes tnpop{{0%{{transform:scale(0);opacity:0}}60%{{transform:scale(1.14);opacity:1}}100%{{transform:scale(1);opacity:1}}}}
@keyframes tnslam{{0%{{transform:scale(1.55);opacity:0}}55%{{transform:scale(.965);opacity:1}}
  100%{{transform:scale(1);opacity:1}}}}
@keyframes tnbreathe{{0%{{transform:translateY(0)}}100%{{transform:translateY(-9px)}}}}
@keyframes tnsway{{0%{{transform:rotate(-1.2deg)}}100%{{transform:rotate(1.2deg)}}}}
@keyframes tndraw{{to{{stroke-dashoffset:0}}}}
@keyframes tnhead{{from{{transform:translateX(0)}}to{{transform:translateX(var(--dx))}}}}
"""


# ------------------------------------------------------------------ numbers

def _d(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def _dc(d: date) -> str:
    """For captions: Dec 29, 2025."""
    return d.strftime("%b %-d, %Y")


def _one(v: float) -> str:
    """An average: one decimal (4.2, 50.1), commas from 1,000."""
    return f"{v:,.1f}"


def _mult(r: float) -> str:
    """How many times as many, never rounded up past the truth."""
    r1 = round(r, 1)
    if abs(r1 - round(r1)) < 1e-9:
        return f"{int(round(r1))}×"
    if r >= 5:
        up, down = math.ceil(r), math.floor(r)
        if up - r <= .2:
            return f"NEARLY {up}×"
        if r - down <= .2:
            return f"OVER {down}×"
    return f"{r1:.1f}×"


def _mult_parts(r: float) -> tuple:
    """("NEARLY", "12×"), ("", "8.7×") ..."""
    m = _mult(r)
    q, _, core = m.rpartition(" ")
    return q, core


def _pct(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


def _stats(hist: R.History, then: int, upto: date) -> dict | None:
    """Everything the video says, computed from the records up to `upto`.
    None when the records can't support an honest THEN vs NOW."""
    record_days, per_day, outfits = set(), Counter(), {}
    for key, days in hist.days.items():
        ds = [d for d in days if d <= upto]
        if not ds:
            continue
        record_days.update(ds)
        if ((hist.items[key].get("type") or {}).get("value") or "") != "outfit":
            continue
        outfits[key] = ds
        for d in ds:
            per_day[d] += 1

    # NOW: this year so far, or last year when this one has barely started.
    now = upto.year
    if sum(1 for d in record_days if d.year == now) < MIN_NOW_DAYS:
        now -= 1
    partial = now == upto.year and upto < date(now, 12, 31)
    days_in = {y: sorted(d for d in record_days if d.year == y) for y in range(then, now + 1)}
    if then < R.FIRST_SURE.year or then >= now or len(days_in[then]) < MIN_THEN_DAYS:
        return None

    avg = {y: sum(per_day[d] for d in ds) / len(ds) for y, ds in days_in.items() if ds}
    if then not in avg or now not in avg or avg[now] < MIN_RATIO * avg[then]:
        return None
    years = list(range(then, now + 1))
    distinct = {y: sum(1 for ds in outfits.values() if any(d.year == y for d in ds)) for y in years}
    new = {y: sum(1 for ds in outfits.values() if ds[0].year == y) for y in years}
    if not distinct[then] or not distinct[now]:
        return None

    # The busiest day on record, and THEN's (ties: the latest such day; "tied" said).
    top = max(per_day.values())
    tops = sorted(d for d, c in per_day.items() if c == top)
    top_then = max(per_day[d] for d in days_in[then])
    tops_then = sorted(d for d in days_in[then] if per_day[d] == top_then)

    # THE REGULAR: first sold in THEN, in the shop in NOW, the most times in the shop.
    rows = []
    for key, ds in outfits.items():
        if ds[0].year != then:
            continue
        runs = R._runs(ds)
        rows.append((len(runs), key, runs, any(d.year == now for d in ds)))
    rows.sort(key=lambda r: (-r[0], r[2][0][0], hist.items[r[1]].get("name", "")))
    still = [r for r in rows if r[3]]
    if not still:
        return None
    times, key, runs, _ = still[0]
    best_all = rows[0][0]
    regular = {"raw": hist.items[key], "key": key, "times": times, "runs": runs, "first": runs[0][0],
               "last": runs[-1][1],
               # how the ranking may be said
               "rank": ("most" if best_all == times and sum(1 for r in rows if r[0] == times) == 1 else
                        "tied" if best_all == times else "most_still")}

    # NOW's face for the hook and the outro: first sold in NOW, in the shop the most
    # separate times this year.
    fresh = []
    for key, ds in outfits.items():
        if ds[0].year != now:
            continue
        fresh.append((len(R._runs(ds)), len(ds), hist.items[key].get("name", ""), key))
    fresh.sort(key=lambda r: (-r[0], -r[1], r[2]))

    return {"then": then, "now": now, "partial": partial, "upto": upto, "years": years,
            "now_label": f"{now} SO FAR" if partial else str(now),
            "avg": avg, "ndays": {y: len(ds) for y, ds in days_in.items()},
            "distinct": distinct, "new": new,
            "busiest": (tops[-1], top, len(tops) > 1), "busiest_then": (tops_then[-1], top_then, len(tops_then) > 1),
            "busiest_ids": sorted(k for k, ds in outfits.items() if tops[-1] in ds),
            "regular": regular, "fresh": [r[3] for r in fresh]}


# ------------------------------------------------------------------ drawing kit

def _a(name: str, start: float, dur: float, ease: str = EASE_OUT, fill: str = "both") -> str:
    return style_anim(an(name, start, dur, ease, fill=fill))


def _t(text: str, x: float, y: float, size: float, start: float | None = None, *, anton: bool = False,
       weight: int = 800, color: str = TEXT, align: str = "left", spacing: str = "0", anim: str = "tnrise",
       dur: float = .5, extra: str = "") -> str:
    """One line of text, its top at y. start=None: already there."""
    if align == "center":
        pos = f"left:{x - W:.0f}px;width:{2 * W}px;text-align:center;"
    elif align == "right":
        pos = f"right:{W - x:.0f}px;text-align:right;"
    else:
        pos = f"left:{x:.0f}px;"
    font = "tn-a" if anton else "tn-i"
    wt = "" if anton else f"font-weight:{weight};"
    a = _a(anim, start, dur) if start is not None else ""
    return (f'<div class="tn-t {font}" style="{pos}top:{y:.0f}px;font-size:{size:.0f}px;{wt}color:{color};'
            f'letter-spacing:{spacing};{extra}"><span style="display:inline-block;{a}">{esc(text)}</span></div>')


def _wrap(text: str, size: float, width: float) -> list:
    """Anton lines that fit `width` (a little slack for the renderer)."""
    lines, cur = [], []
    for w in text.split():
        trial = " ".join(cur + [w])
        if cur and anton_em(trial) * size > width * .97:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def _fit(text: str, width: float, big: float, small: float, max_lines: int = 2) -> tuple:
    """(size, lines): the largest size from `big` down to `small` at which the
    Anton text takes at most `max_lines` lines of `width`."""
    size = big
    while size > small and len(_wrap(text, size, width)) > max_lines:
        size -= 2
    return size, _wrap(text, size, width)


def _reveal(lines: list, x: float, y: float, size: float, start: float, color: str = TEXT,
            lh: float = .96, stagger: float = .09) -> str:
    """Anton lines that slide up out of their own line, one after another."""
    out = []
    for i, ln in enumerate(lines):
        out.append(f'<div class="tn-line tn-a" style="position:absolute;left:{x:.0f}px;top:{y + i * size * lh:.0f}px;'
                   f'font-size:{size:.0f}px;color:{color}">'
                   f'<span style="{_a("tnup", start + i * stagger, .62, "cubic-bezier(.2,.85,.25,1)")}">'
                   f'{esc(ln)}</span></div>')
    return "".join(out)


def _roll(value: float, fmt, x: float, y: float, size: float, start: float, dur: float = 1.1,
          color: str = TEXT, align: str = "left", steps: int = 18, extra: str = "") -> str:
    """A number that counts up to `value` (ease-out) and lands on fmt(value)
    exactly: one span per step, each shown for its slice of time."""
    texts = []
    for i in range(steps + 1):
        f = i / steps
        texts.append(fmt(value) if i == steps else fmt(value * (1 - (1 - f) ** 3)))
    if align == "right":
        box, sp = f"right:{W - x:.0f}px;", "right:0;"
    elif align == "center":
        box, sp = f"left:{x:.0f}px;", "left:0;transform:translateX(-50%);"
    else:
        box, sp = f"left:{x:.0f}px;", "left:0;"
    spans, i = [], 0
    while i <= steps:
        j = i
        while j + 1 <= steps and texts[j + 1] == texts[i]:
            j += 1
        t_in = start + dur * i / steps
        if j == steps:
            anim = an("tnshow", t_in, .01, "linear", fill="forwards")
        else:
            anim = an("tnshow", t_in, dur * (j + 1 - i) / steps, "linear", fill="none")
        spans.append(f'<span class="tn-rs" style="{sp}{style_anim(anim)}">{esc(texts[i])}</span>')
        i = j + 1
    return (f'<div class="tn-a" style="position:absolute;{box}top:{y:.0f}px;font-size:{size:.0f}px;color:{color};'
            f'height:{size * .9:.0f}px;{extra}">{"".join(spans)}</div>')


def _ax(text: str) -> str:
    """Escaped Anton text, with a real multiplication sign."""
    return esc(text).replace("×", '<span class="tn-x">×</span>')


def _chip(text: str, size: float, bg: str, fg: str = INK) -> str:
    return f'<span class="tn-chip" style="font-size:{size:.0f}px;background:{bg};color:{fg}">{esc(text)}</span>'


def _stamp(lines: list, x: float, y: float, start: float, rot: float = -4, bg: str = NOW_C, fg: str = INK,
           align: str = "left", pad: str = "16px 26px 12px") -> str:
    """A slab of lime (or blue) that slams onto the page: lines = [(text, size, anton)]."""
    rows = "".join(
        f'<div class="{"tn-a" if anton else "tn-i"}" style="font-size:{size:.0f}px;line-height:{.92 if anton else 1.15};'
        f'{"" if anton else "font-weight:900;letter-spacing:.12em;"}white-space:nowrap">{_ax(text)}</div>'
        for text, size, anton in lines)
    pos = f"right:{W - x:.0f}px;" if align == "right" else f"left:{x:.0f}px;"
    origin = "100% 50%" if align == "right" else "0 50%"
    return (f'<div style="position:absolute;{pos}top:{y:.0f}px;transform:rotate({rot}deg);transform-origin:{origin}">'
            f'<div class="tn-stamp" style="background:{bg};color:{fg};padding:{pad};text-align:{align};'
            f'{_a("tnslam", start, .5, "cubic-bezier(.3,.7,.3,1)")}">{rows}</div></div>')


def _swatch(color: str, size: float = 22) -> str:
    return (f'<span style="display:inline-block;width:{size:.0f}px;height:{size:.0f}px;border-radius:5px;'
            f'background:{color};margin-right:12px;vertical-align:-2px"></span>')


def _skin(ctx: Ctx, it: dict, cx: float, bottom: float, h: float, start: float, enter: str = "tnrise",
          idle: str = "tnbreathe", maxw: float = 0, dur: float = .7) -> str:
    """A cosmetic standing with its feet at `bottom`; a quiet stand-in figure when
    there is no art."""
    uri = ctx.art(it)
    if uri:
        return character(uri, cx, bottom - h / 2, h, start, enter, dur, idle, it["rarity"], it["name"],
                         maxw=maxw, trim=trim_for(it))
    w = min(h * .46, maxw or h)
    head = w * .34
    body = (f'<svg width="{w:.0f}" height="{h:.0f}" viewBox="0 0 100 {100 * h / w:.0f}" style="display:block">'
            f'<circle cx="50" cy="{head / w * 50 + 4:.0f}" r="{head / w * 50:.0f}" fill="#2c2d33"/>'
            f'<path d="M14 {100 * h / w:.0f} L20 {head / w * 100 + 18:.0f} Q50 {head / w * 100 + 2:.0f} 80 '
            f'{head / w * 100 + 18:.0f} L86 {100 * h / w:.0f} Z" fill="#2c2d33"/></svg>')
    return (f'<div style="position:absolute;left:{cx - w / 2:.0f}px;top:{bottom - h:.0f}px;{_a(enter, start, dur)}">'
            f'{body}</div>')


def _backdrop() -> str:
    return '<div class="tn-bg" data-safe="ignore"><div class="lit"></div><div class="dots"></div><div class="grain"></div></div>'


def _header(k: int, S: dict) -> str:
    """Top right, every number: what the video is, and which of the five this is."""
    pips = "".join(f'<i style="display:inline-block;width:40px;height:8px;border-radius:4px;margin-left:8px;'
                   f'background:{NOW_C if j <= k else "#34343a"}"></i>' for j in range(1, N_BEATS + 1))
    return (_t(f"THE ITEM SHOP · {S['then']} VS NOW", R_TOP, 242, 26, None, color=MUTED, align="right",
               spacing=".14em")
            + f'<div style="position:absolute;right:{W - R_TOP}px;top:290px;line-height:0">{pips}</div>')


def _title(k: int, kicker: str, headline: str, t0: float, size: float = 84) -> tuple:
    """The number's label and its headline. Returns (html, the headline's bottom y)."""
    chip = _chip(f"{k:02d}", 36, NOW_C)
    html = (f'<div class="tn-t tn-i" style="left:{L}px;top:398px;font-size:30px;font-weight:800;color:{TEXT};'
            f'letter-spacing:.16em;{_a("tnrise", t0 + .15, .45)}">{chip}<span style="margin-left:16px;'
            f'vertical-align:4px">{esc(kicker)}</span></div>')
    size, lines = _fit(headline, R_TOP - L, size, 64)
    html += _reveal(lines, L, 452, size, t0 + .25)
    return html, 452 + len(lines) * size * .96


def _so_far(S: dict) -> str:
    """ · 2026: Jan 1 – Sep 24, never split across lines."""
    if not S["partial"]:
        return ""
    return "\u00a0· " + f"{S['now']}: Jan 1 – {S['upto']:%b %-d}".replace(" ", "\u00a0")


def _foot(text: str, t0: float) -> str:
    """The small print: what exactly was counted."""
    return (f'<div class="tn-i" style="position:absolute;left:{L}px;top:1346px;width:{R_LOW - L}px;font-size:26px;'
            f'font-weight:600;line-height:1.25;color:{MUTED};{_a("tnin", t0 + 1.0, .6)}">{esc(text)}</div>')


def _waffle(value: float, x: float, y: float, cols: int, cell: float, gap: float, color: str,
            start: float, dur: float) -> str:
    """One square per skin, filling in reading order; a fraction as part of a square."""
    full, frac = int(value), value - int(value)
    n = full + (1 if frac >= .05 else 0)
    out = []
    for i in range(n):
        r, c = divmod(i, cols)
        w = cell if i < full else max(4.0, cell * frac)
        t = start + dur * (i / max(1, n - 1)) ** .85
        out.append(f'<i class="tn-cell" style="left:{x + c * (cell + gap):.1f}px;top:{y + r * (cell + gap):.1f}px;'
                   f'width:{w:.1f}px;height:{cell:.1f}px;background:{color};'
                   f'border-radius:{min(7, w / 2):.0f}px;{_a("tnpop", t, .32, "cubic-bezier(.3,.9,.4,1.2)")}"></i>')
    return f'<div data-safe="ignore">{"".join(out)}</div>'


def _chart_x(n: int) -> tuple:
    """(bar width, [bar centre x]) for n years across x 60-900."""
    slot = (CH_R - CH_L) / n
    bw = min(100.0, slot * .64)
    return bw, [CH_L + slot * (i + .5) for i in range(n)]


def _year_labels(S: dict, xs: list, t: float | None) -> str:
    """The years under the bars (t=None: already there, for a scene that opens on them)."""
    out = []
    for i, (y, x) in enumerate(zip(S["years"], xs)):
        hi = y in (S["then"], S["now"])
        col = TEXT if hi else MUTED
        ti = None if t is None else t + i * .03
        out.append(_t(str(y), x, CH_BASE + 14, 26, ti, color=col, align="center", weight=800))
        if y == S["now"] and S["partial"]:
            out.append(_t("SO FAR", x, CH_BASE + 45, 22, ti, color=col, align="center", weight=800,
                          spacing=".04em"))
    grow = "" if t is None else f"transform-origin:0 50%;{_a('tnwide', t - .2, .5)}"
    base = (f'<div data-safe="ignore" style="position:absolute;left:{CH_L}px;top:{CH_BASE}px;width:{CH_R - CH_L}px;'
            f'height:2px;background:#3b3b42;{grow}"></div>')
    return base + "".join(out)


def _color(S: dict, y: int, mid: str = MID_C) -> str:
    return THEN_C if y == S["then"] else NOW_C if y == S["now"] else mid


# ------------------------------------------------------------------ the scenes

def _hook(comp: Comp, ctx: Ctx, S: dict, a: dict, b: dict, end: float):
    """Frame 0 is the thumbnail: everything is already in place, and the motion
    is beats that start and end at rest (a thump, a hop, a boing)."""
    then, now = S["then"], S["now"]
    ratio = S["avg"][now] / S["avg"][then]
    inner = _code_stamp(comp, end)
    inner += _t("FORTNITE ITEM SHOP", R_TOP, 318, 30, None, color=TEXT, align="right", spacing=".16em")
    inner += _t("BY THE NUMBERS", R_TOP, 360, 30, None, color=MUTED, align="right", spacing=".16em")
    # THE ITEM SHOP / 2018 VS NOW
    s1 = min(138, (R_TOP - L) / anton_em("THE ITEM SHOP"))
    s2 = min(172, (R_TOP - L) / (anton_em(f"{then} NOW") + .75 * anton_em("VS")))
    thump = style_anim(an("thump", .2, .4))
    inner += (f'<div style="position:absolute;left:{L}px;top:492px;transform-origin:0 50%;{thump}">'
              f'<div class="tn-a" style="font-size:{s1:.0f}px;color:{TEXT}">THE ITEM SHOP</div>'
              f'<div class="tn-a" style="font-size:{s2:.0f}px;margin-top:8px;white-space:nowrap">'
              f'<span style="color:{THEN_C}">{then}</span>'
              f'<span style="color:{TEXT};font-size:.62em;margin:0 .22em;vertical-align:.12em">VS</span>'
              f'<span style="color:{NOW_C}">NOW</span></div></div>')
    # Two panels: THEN's skin and NOW's.
    py, ph = 812, 590
    for it, x0, col, year, t_hop, idle in ((a, L, THEN_C, str(then), .15, "tnbreathe"),
                                            (b, 490, NOW_C, str(now), .3, "tnsway")):
        inner += (f'<div class="tn-panel" data-safe="ignore" style="left:{x0}px;top:{py}px;width:410px;height:{ph}px">'
                  f'<div style="position:absolute;left:0;right:0;top:0;height:6px;border-radius:26px 26px 0 0;'
                  f'background:{col}"></div></div>')
        inner += (f'<div style="position:absolute;left:{x0 + 22}px;top:{py + 26}px">'
                  f'{_chip(year, 44, col)}</div>')
        inner += _skin(ctx, it, x0 + 205, py + ph - 112, 410, t_hop, enter="hop", idle=idle, maxw=330, dur=.45)
    # The teaser: the average day's multiple.
    teaser = f"{_mult(ratio)} MORE SKINS A DAY"
    size = min(62, 720 / (anton_em(teaser) + .6))
    inner += (f'<div style="position:absolute;left:0;width:{2 * 480}px;top:{py + ph - 96}px;text-align:center">'
              f'<div style="display:inline-block;transform:rotate(-2deg)">'
              f'<div class="tn-stamp tn-a" style="background:{NOW_C};color:{INK};font-size:{size:.0f}px;'
              f'padding:.2em .5em .12em;{style_anim(an("boing", .9, .55, fill="none"))}">{_ax(teaser)}</div>'
              f'</div></div>')
    comp.scene(0, end, inner, fade_in=.01, fade_out=.3)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.3, "whoosh"); comp.cue(.9, "pop")


def _code_stamp(comp: Comp, end: float) -> str:
    """USE CODE: BAD, big, for the thumbnail (USE CODE: 36 px, BAD 118 px, lime).
    Near the end of the hook it shrinks into the corner badge, which takes over
    as it lands: the code is on screen in every frame. The box has the badge's
    proportions (3:1), so it lands exactly on it."""
    sw, sh = 372, 124
    k = BADGE_H / sh
    x0, y0, rot = L + 8, 300, -3
    dock_end = min(2.6, end - .7)
    dock_start = dock_end - .5
    dock = comp.uid("tndock")
    move = f"translate({BADGE_X - x0}px,{BADGE_Y - y0}px) scale({k:.4f}) rotate(0deg)"
    comp.css(f"@keyframes {dock}{{0%{{transform:rotate({rot}deg);opacity:1}}99.9%{{transform:{move};opacity:1}}"
             f"100%{{transform:{move};opacity:0}}}}")
    comp.css(f".codebadge,.codetag{{animation:fadein .01s linear {dock_end - .01:.3f}s both paused !important}}")
    comp.cue(dock_start, "whoosh")
    return (f'<div data-safe="key" data-name="code" style="position:absolute;left:{x0}px;top:{y0}px;'
            f'transform-origin:0 0;z-index:5;{style_anim(an(dock, dock_start, .5, "cubic-bezier(.6,0,.4,1)"))}">'
            f'<div style="{style_anim(an("thump", .2, .4, fill="none"))}">'
            f'<div style="width:{sw}px;height:{sh}px;box-sizing:border-box;display:flex;align-items:center;'
            f'justify-content:center;gap:18px;background:{NOW_C};color:{INK};border-radius:24px;'
            f'padding-top:6px;box-shadow:0 12px 0 rgba(0,0,0,.4),0 24px 40px rgba(0,0,0,.45)">'
            f'<div class="tn-i" style="font-size:36px;font-weight:900;line-height:1.0;letter-spacing:.1em">'
            f'USE<br>CODE:</div><div class="tn-a" style="font-size:118px;line-height:.86">BAD</div></div>'
            f'<div class="tn-i" style="margin:{4 / k:.0f}px 0 0 {4 / k:.0f}px;font-size:{23 / k:.0f}px;font-weight:700;'
            f'line-height:1.3;color:rgba(255,255,255,.92)">#EpicPartner</div></div></div>')


def _beat_average(comp: Comp, S: dict, t0: float, k: int):
    """1 -- skins in the shop on an average day, THEN vs NOW."""
    then, now = S["then"], S["now"]
    a0, a1 = S["avg"][then], S["avg"][now]
    inner = _header(k, S)
    html, _ = _title(k, "THE DAILY SHOP", "SKINS IN THE ITEM SHOP ON AN AVERAGE DAY", t0)
    inner += html
    cols = ((L, str(then), a0, THEN_C, 6), (484, S["now_label"], a1, NOW_C, 8))
    cell, gap = 44, 8
    t_num = t0 + .7
    for x, lab, v, col, n_cols in cols:
        inner += (f'<div class="tn-t tn-i" style="left:{x}px;top:652px;font-size:34px;font-weight:800;color:{TEXT};'
                  f'letter-spacing:.06em;{_a("tnrise", t0 + .45, .45)}">{_swatch(col, 24)}{esc(lab)}</div>')
        inner += _roll(v, _one, x, 706, 196, t_num, 1.25)
        inner += _t("SKINS A DAY", x, 896, 28, t_num + .9, color=MUTED, spacing=".12em")
        inner += _waffle(v, x, 950, n_cols, cell, gap, col, t_num + .1, 1.3)
    q, core = _mult_parts(a1 / a0)
    inner += _stamp(([(q, 30, False)] if q else []) + [(f"{core} MORE", 88, True)], L + 6, 1080, t0 + 3.0, rot=-4)
    inner += _foot(f"Different skins (outfits) in the Item Shop each day, averaged over the year"
                   + _so_far(S), t0)
    comp.scene(t0, t0 + BEAT + .3, inner, fade_in=.3, fade_out=.3)
    comp.cue(t0 + .05, "whoosh"); comp.cue(t0 + .3, "pop")
    comp.cue(t_num + .05, "flap"); comp.cue(t_num + .5, "flap"); comp.cue(t_num + 1.25, "slam")
    comp.cue(t0 + 3.0, "stamp")


def _beat_years(comp: Comp, S: dict, t0: float, k: int) -> dict:
    """2 -- different skins in the shop each year: one bar per year."""
    then, now = S["then"], S["now"]
    inner = _header(k, S)
    html, _ = _title(k, "EVERY YEAR", "DIFFERENT SKINS IN THE SHOP EACH YEAR", t0)
    inner += html
    years = S["years"]
    bw, xs = _chart_x(len(years))
    top = max(S["distinct"].values())
    geo = {}
    t_bar = t0 + .7
    for i, (y, x) in enumerate(zip(years, xs)):
        v = S["distinct"][y]
        h = max(6.0, CH_H2 * v / top)
        geo[y] = (x, h)
        t = t_bar + i * .09
        inner += (f'<div data-safe="ignore" style="position:absolute;left:{x - bw / 2:.1f}px;top:{CH_BASE - h:.1f}px;'
                  f'width:{bw:.1f}px;height:{h:.1f}px;border-radius:9px 9px 0 0;background:{_color(S, y)};'
                  f'transform-origin:50% 100%;{_a("tngrow", t, .85, "cubic-bezier(.25,.9,.3,1)")}"></div>')
        hi = y in (then, now)
        size = 34 if hi else 24
        lab = f"{v:,}"
        inner += _t(lab, x, CH_BASE - h - size * 1.25, size, t + .6, color=TEXT if hi else MUTED, align="center",
                    weight=900 if hi else 800)
    inner += _year_labels(S, xs, t_bar - .1)
    ratio = S["distinct"][now] / S["distinct"][then]
    if ratio >= MIN_RATIO:
        q, core = _mult_parts(ratio)
        who = f"{S['now_label']} VS ALL OF {then}"
        inner += _stamp([(who, 24, False), (f"{q} {core}".strip(), 96, True)], L + 6, 700, t0 + 3.2, rot=-3)
        comp.cue(t0 + 3.2, "stamp")
    inner += _foot("Different skins (outfits) in the Item Shop at least once that year" + _so_far(S), t0)
    comp.scene(t0, t0 + BEAT + .3, inner, fade_in=.3, fade_out=.3)
    comp.cue(t0 + .05, "whoosh"); comp.cue(t0 + .3, "pop")
    for i in range(len(years)):
        comp.cue(t_bar + i * .09 + .6, "tick")
    return {"bw": bw, "geo": geo}


def _beat_new(comp: Comp, S: dict, t0: float, k: int, g: dict):
    """3 -- the same bars stretch to 100% and split: brand-new that year vs from an
    earlier year. The scene opens exactly where the last one left its bars."""
    then, now = S["then"], S["now"]
    inner = _header(k, S)
    html, hb = _title(k, "BRAND-NEW", "HOW MANY SKINS WERE BRAND-NEW?", t0)
    inner += html
    inner += (f'<div class="tn-t tn-i" style="left:{L}px;top:{hb + 18:.0f}px;font-size:26px;font-weight:800;color:{TEXT};'
              f'letter-spacing:.08em;{_a("tnrise", t0 + .5, .45)}">{_swatch(MIDNEW_C)}BRAND-NEW THAT YEAR'
              f'<span style="display:inline-block;width:34px"></span>{_swatch(OLD_C)}'
              f'<span style="color:{MUTED}">IN THE SHOP IN AN EARLIER YEAR</span></div>')
    bw = g["bw"]
    t_go = t0 + .55
    gap = 4
    for i, y in enumerate(S["years"]):
        x, h2 = g["geo"][y]
        share = S["new"][y] / S["distinct"][y]
        hn = max(4.0, CH_H3 * share)
        ho = max(0.0, CH_H3 - hn - gap)
        c2, c3 = _color(S, y), _color(S, y, MIDNEW_C)
        kn, ko = comp.uid("tnn"), comp.uid("tno")
        comp.css(f"@keyframes {kn}{{from{{height:{h2:.1f}px;border-radius:9px 9px 0 0;background:{c2}}}"
                 f"to{{height:{hn:.1f}px;border-radius:0;background:{c3}}}}}"
                 f"@keyframes {ko}{{from{{height:0}}to{{height:{ho:.1f}px}}}}")
        t = t_go + i * .06
        inner += (f'<div data-safe="ignore" style="position:absolute;left:{x - bw / 2:.1f}px;bottom:{1920 - CH_BASE}px;'
                  f'width:{bw:.1f}px;display:flex;flex-direction:column-reverse;gap:{gap}px">'
                  f'<div style="height:{hn:.1f}px;background:{c3};{_a(kn, t, 1.0, "cubic-bezier(.5,0,.2,1)")}"></div>'
                  f'<div style="height:{ho:.1f}px;background:{OLD_C};border-radius:9px 9px 0 0;'
                  f'{_a(ko, t, 1.0, "cubic-bezier(.5,0,.2,1)")}"></div></div>')
    inner += _year_labels(S, _chart_x(len(S["years"]))[1], None)
    # The two numbers that matter, over their own columns.
    xs = _chart_x(len(S["years"]))[1]
    t_lab = t_go + 1.5
    col_top = CH_BASE - CH_H3
    for y, x, align in ((then, xs[0] - bw / 2, "left"), (now, xs[-1] + bw / 2, "right")):
        p = _pct(S["new"][y], S["distinct"][y])
        inner += _roll(p, lambda v: f"{round(v)}%", x, col_top - 126, 88, t_lab, .8, align=align)
        inner += _t(f"{S['new'][y]:,} OF {S['distinct'][y]:,}", x, col_top - 40, 26, t_lab + .7, color=MUTED,
                    align=align, spacing=".06em")
    inner += _foot(f"Brand-new = its first time in the Item Shop (records start Oct 30, 2017) · skins = outfits", t0)
    comp.scene(t0, t0 + BEAT + .3, inner, fade_in=.3, fade_out=.3)
    comp.cue(t0 + .3, "pop"); comp.cue(t_go + .1, "whoosh"); comp.cue(t_lab, "flap"); comp.cue(t_lab + .8, "slam")


def _beat_busiest(comp: Comp, ctx: Ctx, S: dict, t0: float, k: int, faces: list):
    """4 -- the busiest day on record: a square per skin, THEN's own record
    marked on the same squares, a few of that day's skins standing by."""
    day, count, tied = S["busiest"]
    tday, tcount, ttied = S["busiest_then"]
    then = S["then"]
    inner = _header(k, S)
    html, _ = _title(k, "ONE DAY", "THE BUSIEST DAY ON RECORD" if not tied else "TIED FOR THE BUSIEST DAY", t0)
    inner += html
    t_num = t0 + .7
    inner += _roll(count, lambda v: f"{round(v):,}", L, 552, 250, t_num, 1.3, color=NOW_C)
    inner += _t("SKINS IN THE SHOP", L, 784, 30, t_num + .6, spacing=".12em")
    inner += _t(_d(day), L, 826, 60, t_num + .75, anton=True)
    # Some of that day's skins, standing beside the number, feet on the squares' top edge.
    wy = 912
    spots = [(590, 330, 180, .55), (800, 330, 180, .7), (695, 372, 200, .85)][:len(faces)]
    for it, (cx, h, mw, dt) in zip(faces, spots):
        inner += _skin(ctx, it, cx, wy - 16, h, t0 + dt, maxw=mw)
    # The waffle: one square per skin.
    cols, cell, gp = 14, 46, 6
    wx = L
    rows = math.ceil(count / cols)
    if rows > 7:                               # a bigger record than 98: smaller squares
        cell = (358 - (rows - 1) * gp) / rows
    inner += _waffle(count, wx, wy, cols, cell, gp, NOW_C, t_num + .1, 1.4)
    # THEN's record, outlined on the same squares.
    if tday.year != day.year and tcount < count:
        full_rows, rest = divmod(tcount, cols)
        p = cell + gp
        pts = [(0, 0), (cols * p - gp, 0)]
        if rest:
            pts += [(cols * p - gp, full_rows * p - gp), (rest * p - gp, full_rows * p - gp),
                    (rest * p - gp, (full_rows + 1) * p - gp), (0, (full_rows + 1) * p - gp)]
        elif full_rows:
            pts += [(cols * p - gp, full_rows * p - gp), (0, full_rows * p - gp)]
        else:
            pts = [(0, 0), (tcount * p - gp, 0), (tcount * p - gp, cell), (0, cell)]
        o = 7
        path = "M" + " L".join(f"{wx + px + (o if px > 0 else -o):.1f},{wy + py + (o if py > 0 else -o):.1f}"
                               for px, py in pts) + " Z"
        length = 2 * (cols * p + (full_rows + 1) * p) + 80
        t_line = t0 + 3.4
        inner += (f'<svg data-safe="ignore" width="{W}" height="1920" style="position:absolute;left:0;top:0;overflow:visible">'
                  f'<path d="{path}" fill="none" stroke="{THEN_C}" stroke-width="6" stroke-linejoin="round" '
                  f'style="stroke-dasharray:{length:.0f};stroke-dashoffset:{length:.0f};'
                  f'{_a("tndraw", t_line, .9, "cubic-bezier(.45,.05,.35,1)")}"/></svg>')
        rows_used = math.ceil(count / cols)
        ly = wy + rows_used * (cell + gp) + 6
        inner += (f'<div class="tn-t tn-i" style="left:{L}px;top:{ly:.0f}px;font-size:28px;font-weight:800;'
                  f'color:{TEXT};letter-spacing:.06em;{_a("tnrise", t_line + .6, .45)}">{_swatch(THEN_C)}'
                  f'MOST IN ONE DAY IN {then}: {tcount}</div>')
        comp.cue(t_line, "pen")
    inner += _foot("Different skins (outfits) in the Item Shop on one day, of every day on record (since Oct 30, 2017)",
                   t0)
    comp.scene(t0, t0 + BEAT + .3, inner, fade_in=.3, fade_out=.3)
    comp.cue(t0 + .05, "whoosh"); comp.cue(t0 + .3, "pop"); comp.cue(t0 + .6, "pop")
    comp.cue(t_num + 1.3 - 1.6, "drumroll"); comp.cue(t_num + 1.3, "slam")


def _beat_regular(comp: Comp, ctx: Ctx, S: dict, t0: float, k: int, it: dict):
    """5 -- the THEN skin in the shop the most times since: every one of those
    times a tick on a timeline from THEN to today."""
    reg = S["regular"]
    then, now = S["then"], S["now"]
    inner = _header(k, S)
    head = f"THE {then} SKIN IN THE SHOP MOST OFTEN"
    html, _ = _title(k, "THE REGULAR", head, t0)
    inner += html
    t_num = t0 + .7
    inner += _roll(reg["times"], lambda v: f"{round(v):,}", L, 628, 250, t_num, 1.4, color=NOW_C)
    inner += _t("TIMES IN THE ITEM SHOP", L, 858, 28, t_num + .6, spacing=".08em")
    size, lines = _fit(it["name"], 470, 76, 48)
    inner += _reveal(lines, L, 912, size, t0 + 1.6)
    y = 912 + len(lines) * size * .96 + 14
    last = reg["last"]
    last_s = "IN THE SHOP TODAY" if last == ctx.day else f"MOST RECENTLY {_d(last)}"
    for j, line in enumerate((f"FIRST SOLD {_d(reg['first'])}", last_s)):
        inner += _t(line, L, y + j * 38, 26, t0 + 1.9 + j * .12, color=MUTED, spacing=".04em")
    inner += _skin(ctx, it, 712, 1150, 520, t0 + .5, maxw=340)
    # The timeline: THEN's Jan 1 to the records' last day, a tick per time in the shop.
    x0, x1, ty = L, R_LOW, 1206
    span0, span1 = date(then, 1, 1), S["upto"]
    tot = (span1 - span0).days or 1
    xa = lambda d: x0 + (x1 - x0) * (d - span0).days / tot
    t_line = t0 + 2.2
    dur = 2.2
    ticks = []
    for a_, b_ in reg["runs"]:
        xs_, xe_ = xa(a_), max(xa(b_), xa(a_) + 3)
        f = (xs_ - x0) / (x1 - x0)
        ticks.append(f'<i style="position:absolute;left:{xs_:.1f}px;top:{ty}px;width:{max(3.0, xe_ - xs_):.1f}px;'
                     f'height:72px;border-radius:2px;background:{NOW_C};{_a("tnin", t_line + dur * f, .12, "linear")}"></i>')
    inner += f'<div data-safe="ignore">{"".join(ticks)}</div>'
    inner += (f'<div data-safe="ignore" style="position:absolute;left:{x0}px;top:{ty + 82}px;width:{x1 - x0}px;height:2px;'
              f'background:#44444b;transform-origin:0 50%;{_a("tnwide", t_line, dur, "linear")}"></div>')
    for yr in range(then, S["upto"].year + 1):
        d0 = max(date(yr, 1, 1), span0)
        if (span1 - d0).days < 120 and yr != then:
            continue
        xx = xa(d0)
        inner += (f'<i data-safe="ignore" style="position:absolute;left:{xx:.1f}px;top:{ty + 76}px;width:2px;height:14px;'
                  f'background:#44444b;{_a("tnin", t_line + dur * (xx - x0) / (x1 - x0), .2)}"></i>')
        inner += _t(f"'{yr % 100:02d}", xx + 6, ty + 94, 26, t_line + dur * (xx - x0) / (x1 - x0),
                    color=TEXT if yr in (then, now) else MUTED, weight=800)
    rank = {"most": f"More times than any other skin first sold in {then}.",
            "tied": f"Tied for the most times of any skin first sold in {then}.",
            "most_still": f"The most times of any {then} skin also in the shop in {now}."}[reg["rank"]]
    inner += _foot(f"{rank} Consecutive days count as one time.", t0 + 1.2)
    comp.scene(t0, t0 + BEAT + .3, inner, fade_in=.3, fade_out=.3)
    comp.cue(t0 + .05, "whoosh"); comp.cue(t0 + .3, "pop")
    comp.cue(t_num + .05, "flap"); comp.cue(t_num + .55, "flap"); comp.cue(t_num + 1.4, "slam")
    for j in range(4):
        comp.cue(t_line + j * dur / 4, "printer")
    comp.cue(t_line + dur, "reveal")


def _outro(comp: Comp, ctx: Ctx, S: dict, start: float, end: float, a: dict, b: dict):
    """WHICH SHOP WAS BETTER: THEN OR NOW? -- the two skins, and the code, big."""
    then, now = S["then"], S["now"]
    inner = ""
    s1 = min(96, (R_TOP - L) / anton_em("WHICH SHOP WAS BETTER:"))
    inner += _reveal(["WHICH SHOP WAS BETTER:"], L, 402, s1, start + .15)
    s2 = min(170, (R_TOP - L) / anton_em("THEN OR NOW?"))
    inner += (f'<div class="tn-line tn-a" style="position:absolute;left:{L}px;top:{402 + s1 * 1.02:.0f}px;'
              f'font-size:{s2:.0f}px"><span style="{_a("tnup", start + .3, .62, "cubic-bezier(.2,.85,.25,1)")}">'
              f'<span style="color:{THEN_C}">THEN</span> <span style="color:{TEXT}">OR</span> '
              f'<span style="color:{NOW_C}">NOW?</span></span></div>')
    # The two skins, each with its year and its average day.
    for it, cx, col, year, v, dt in ((a, 270, THEN_C, str(then), S["avg"][then], .5),
                                     (b, 690, NOW_C, S["now_label"], S["avg"][now], .62)):
        inner += _skin(ctx, it, cx, 1122, 440, start + dt, maxw=340)
        inner += (f'<div style="position:absolute;left:{cx - 210}px;width:420px;top:1134px;text-align:center;'
                  f'{_a("tnrise", start + dt + .3, .45)}">{_chip(year, 42, col)}</div>')
        inner += _t(f"{_one(v)} SKINS A DAY", cx, 1192, 26, start + dt + .45, color=MUTED, align="center",
                    spacing=".08em")
    # The code: USE CODE: BAD on lime, big.
    cw, chh = 560, 150
    cx0 = (L + R_LOW) / 2 - cw / 2
    inner += (f'<div data-safe="key" data-name="code" style="position:absolute;left:{cx0:.0f}px;top:1252px;'
              f'width:{cw}px;height:{chh}px;{_a("tnslam", start + 1.0, .55, "cubic-bezier(.3,.7,.3,1)")}">'
              f'<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;gap:24px;'
              f'background:{NOW_C};color:{INK};border-radius:26px;padding-top:8px;'
              f'box-shadow:0 12px 0 rgba(0,0,0,.42),0 26px 44px rgba(0,0,0,.45)">'
              f'<div class="tn-i" style="font-size:44px;font-weight:900;line-height:1;letter-spacing:.1em">USE<br>CODE:</div>'
              f'<div class="tn-a" style="font-size:142px;line-height:.86">BAD</div></div></div>')
    comp.scene(start, end, inner, fade_in=.3, fade_out=.01, z=2)
    comp.cue(start + .15, "whoosh"); comp.cue(start + .5, "pop"); comp.cue(start + 1.0, "slam")


# ------------------------------------------------------------------ build

def build(ctx: Ctx, then: int = 2018, **_kw) -> Video | None:
    """THE ITEM SHOP: <then> VS NOW. None when the records can't carry it."""
    hist = history()
    if not hist.latest:
        return None
    upto = min(ctx.day, hist.latest)
    try:
        then = int(then)
    except (TypeError, ValueError):
        return None
    S = _stats(hist, then, upto)
    if S is None:
        return None
    now = S["now"]
    reg = S["regular"]
    old = _item(reg["raw"])
    # NOW's face: a skin first sold in NOW (the most separate times this year), with art.
    fresh = [_item(hist.items[k]) for k in S["fresh"][:40]]
    new_face = next((it for it in fresh if ctx.art(it)), fresh[0] if fresh else None)
    if new_face is None:
        return None
    # A few of the busiest day's skins (the most times in the shop overall), with art.
    pool = sorted(S["busiest_ids"], key=lambda key: (-hist.times(key, upto), hist.items[key].get("name", "")))
    faces = []
    for key in pool:
        it = _item(hist.items[key])
        if it["id"].lower() in (old["id"].lower(), new_face["id"].lower()):
            continue
        if ctx.art(it):
            faces.append(it)
        if len(faces) == 3:
            break

    content_end = HOOK + N_BEATS * BEAT
    comp = Comp(pad_to(content_end))
    comp.css(CSS)
    comp.add(_backdrop())
    comp.add(PREP_JS)
    _hook(comp, ctx, S, old, new_face, HOOK + .3)
    t = HOOK
    _beat_average(comp, S, t, 1)
    g = _beat_years(comp, S, t + BEAT, 2)
    _beat_new(comp, S, t + 2 * BEAT, 3, g)
    _beat_busiest(comp, ctx, S, t + 3 * BEAT, 4, faces)
    _beat_regular(comp, ctx, S, t + 4 * BEAT, 5, old)
    _outro(comp, ctx, S, content_end, comp.duration, old, new_face)
    comp.add(code_badge(0))
    comp.add(disclosure())

    # ---- the words
    a0, a1 = S["avg"][then], S["avg"][now]
    nl = S["now_label"].lower()
    day, count, tied = S["busiest"]
    tcount = S["busiest_then"][1]
    rank = {"most": f", more than any other {then} skin", "tied": f", tied for the most of any {then} skin",
            "most_still": f", the most of any {then} skin still in the shop in {now}"}[reg["rank"]]
    lines = [
        f"{num(1)} On an average day: {_one(a0)} skins in the shop in {then} → {_one(a1)} in {nl} "
        f"({_mult(a1 / a0).lower()} more)",
        f"{num(2)} Different skins in the shop in a year: {S['distinct'][then]:,} in {then} → "
        f"{S['distinct'][now]:,} in {nl}",
        f"{num(3)} Brand-new that year: {_pct(S['new'][then], S['distinct'][then])}% in {then} "
        f"({S['new'][then]:,} of {S['distinct'][then]:,}) → {_pct(S['new'][now], S['distinct'][now])}% in {nl} "
        f"({S['new'][now]:,} of {S['distinct'][now]:,})",
        f"{num(4)} {'Tied for the busiest' if tied else 'Busiest'} day on record: {_dc(day)}, with {count} skins "
        f"(most in one day in {then}: {tcount})",
        f"{num(5)} {old['name']}, first sold {reg['first']:%b %-d, %Y}: in the Item Shop {reg['times']} times{rank}",
    ]
    so_far = f" · {nl} = Jan 1 – {S['upto']:%b %-d}" if S["partial"] else ""
    tags = _hashtags("ogfortnite", "fortnitestats", old["name"])
    ratio_s = _mult(a1 / a0)
    return Video(
        f"then_now_{then}", comp,
        title=f"The Fortnite Item Shop: {then} vs Now — by the Numbers",
        yt_title=f"The Fortnite Item Shop: {then} vs Now ({ratio_s.title().replace('×', 'x')} More Skins a Day) #shorts",
        caption=_caption(f"📊 THE ITEM SHOP: {then} VS NOW — by the numbers, as of {ctx.day_label}\n"
                         f"From the Item Shop's own records, counting skins (outfits){so_far} 👇",
                         "\n".join(lines), "Which shop was better: then or now?", tags),
        hashtags=tags)
