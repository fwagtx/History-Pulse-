"""
OVERDUE -- skins the Item Shop usually brings back every few weeks... that
haven't been back in months. A countdown of the most overdue (five, or four on
a thin day), from the Item Shop's own history (cc_rarity).

    0:00  hook   OVERDUE, what it means in one line, the #1's real timeline
                 under the title, the two most overdue skins, and USE CODE: BAD,
                 which flies into the corner badge.
    0:03  items  one screen each, #5 up to #1 (~10 s). A playhead sweeps the
                 item's timeline -- every Item Shop visit as a bar -- then
                 crosses the empty stretch up to TODAY while GONE N DAYS counts
                 up with it. Then the usual gap between visits, the times in the
                 shop, the day it was last seen; the usual gap is laid end to end
                 across the empty stretch (x1, x2 ... xN) and N× LONGER THAN USUAL
                 is stamped on. Then it holds.
    ~0:54 outro  WHICH ONE SHOULD COME BACK FIRST? over all of them ranked, each
                 with its timeline on one shared time axis, and the code big.

The numbers, all from the shop history up to ctx.day:
    times in the shop  separate runs of consecutive days (hist.runs): "IN THE
                       ITEM SHOP 31 TIMES"
    a gap              days from the end of one run to the start of the next
    the typical gap    the median gap: "USUALLY BACK EVERY ~21 DAYS", labelled
                       TYPICAL GAP BETWEEN VISITS; shown rounded down, with the ~
    gone               days since it was last in the shop (hist.gone_days)
    the factor         gone / typical gap; "10× LONGER THAN USUAL" is its floor
Candidates: at least `min_runs` runs, gone at least `min_days`, factor at least
`min_factor`, not in today's shop. Ranked by factor; a set that left together
(same set, same last day) counts once; each needs art. Fewer than `min_count`:
None.

Seasonal items are left out unless seasonal=True: most of their visits (75%)
fall in the same 61 days of the calendar, in two or more different years
(Winterfest, Fortnitemares). Their typical gap is the gap inside the season, so
"usually back every ~10 days" would mislead in September.

The strip shows every visit since the item's first; when that is too dense to
read (more than 60 runs, or bars closer than 8 px), it starts ~3 years back
(always keeping a year of visits before the last one), and its title says
"SINCE <MONTH YEAR>" either way. Nothing says why an item is gone, or that it
will (or won't) come back; "overdue" is always measured against its own gaps.

Look: dark slate with grain, lime #E8FF3A for the gap (the count, the empty
stretch, TODAY, the stamp), white for the visits, Anton for the numbers and
names, IBM Plex Mono for data labels, Inter for sentences. No glow, rays or
confetti.
"""

import statistics
from datetime import date, timedelta

import cc_rarity as R
from cc_fmt_rarity import MONTHS, _d, _item, history
from cc_formats import Ctx, Video, _caption, _hashtags, num
from cc_looks import pad_to
from cc_motion import (ACCENT, ANTON, BADGE_H, BADGE_X, BADGE_Y, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP,
                       W, Comp, an, code_badge, disclosure, esc, style_anim, trim_for)

LIME = ACCENT
PAPER = "#F3F2EC"                 # white type and the visit bars
GREY = "#97A0A9"                  # data labels
DIM = "rgba(255,255,255,.14)"     # hairlines
MONO = "'IBM Plex Mono',ui-monospace,monospace"

HOOK = 3.2                        # the first item's screen starts here
OUTRO = 7.5
R_MIN, R_MAX = 9.6, 12.0          # one item's screen, stretched on a four-item day

# One item's screen, seconds from its start.
T_FIG, T_NAME, T_CHART = .06, .18, .2
T_A, D_A = .34, .56               # the playhead sweeps the visits
D_B = 1.5                         # ... then crosses the empty stretch; GONE N DAYS counts with it
T_B = T_A + D_A
T_TODAY = T_B + D_B               # TODAY lands, the count settles
T_STATS = (2.8, 3.3, 3.8)
T_TILE = 4.55                     # the usual gap laid end to end across the empty stretch
EASE_B = "cubic-bezier(.3,.1,.3,1)"

# Layout (cc_safe's box: x 60-1020 above y 740, x 60-900 below; y 230-1420).
# The corner x 60-400, y 230-380 is the code badge's.
X0, X1 = 76, 1000                 # the time axis: the window's first day .. TODAY
NUM_Y = 384                       # GONE N DAYS
TAG_Y = 590                       # the chart's title and the TODAY tag
STRIP_Y, STRIP_H = 626, 72        # the visits
AXIS_Y = STRIP_Y + STRIP_H + 8    # year labels, ending ~730 (above the rail at 740)
RULER_H = 14
COL_X = 490                       # the facts column, to SAFE_RIGHT (900)
COL_W = SAFE_RIGHT - COL_X
FIG_CX, FIG_TOP, FIG_BOTTOM, FIG_MAXW = 268, 768, 1398, 404

SEASON_DAYS, SEASON_SHARE = 61, .75
FEW_WEEKS = (10, 60)              # typical gaps that "every few weeks" describes

KINDS = {  # kind: (on screen, in words, hashtags)
    "outfit": ("SKINS", "skins", ("fortniteskins", "rareskins")),
    "pickaxe": ("PICKAXES", "pickaxes", ("fortnitepickaxes", "rarepickaxes")),
    "emote": ("EMOTES", "emotes", ("fortniteemotes", "rareemotes")),
    "glider": ("GLIDERS", "gliders", ("fortnitegliders", "raregliders")),
    "backpack": ("BACK BLINGS", "back blings", ("fortnitebackbling", "rarebackbling")),
}

CSS = f"""
.od-m{{font-family:{MONO};font-weight:500;text-transform:uppercase;white-space:nowrap;letter-spacing:.1em;color:{GREY}}}
.od-t{{font-family:'Inter',sans-serif;white-space:nowrap}}
@keyframes odrise{{0%{{transform:translateY(26px);opacity:0}}100%{{transform:none;opacity:1}}}}
@keyframes odfig{{0%{{transform:translateY(80px);opacity:0}}100%{{transform:none;opacity:1}}}}
@keyframes odbob{{0%{{transform:translateY(0)}}100%{{transform:translateY(-8px)}}}}
@keyframes odstamp{{0%{{transform:scale(1.9) rotate(var(--r,0deg));opacity:0}}
  55%{{transform:scale(.95) rotate(var(--r,0deg));opacity:1}}100%{{transform:scale(1) rotate(var(--r,0deg));opacity:1}}}}
@keyframes odtoday{{0%{{transform:translateY(-30px);opacity:0}}60%{{transform:translateY(3px);opacity:1}}
  100%{{transform:none;opacity:1}}}}
@keyframes odgrow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes odin{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes odout{{from{{opacity:1}}to{{opacity:0}}}}
@keyframes odthump{{0%,100%{{transform:scale(1)}}35%{{transform:scale(1.045)}}}}
@keyframes odsettle{{0%{{transform:scale(1.07)}}100%{{transform:scale(1)}}}}
@keyframes odwipe{{from{{clip-path:inset(-20px 100% -20px 0)}}to{{clip-path:inset(-20px 0 -20px 0)}}}}
"""


# ------------------------------------------------------------------ data

def _seasonal(runs: list) -> bool:
    """Most of its visits (SEASON_SHARE) start inside the same SEASON_DAYS of the
    calendar, and in at least two different years: a Winterfest or Fortnitemares
    item, whose gaps inside the season aren't how often it comes back."""
    doys = [a.timetuple().tm_yday for a, _ in runs]
    best, at = 0, 1
    for s in range(1, 367):
        k = sum(1 for d in doys if (d - s) % 366 < SEASON_DAYS)
        if k > best:
            best, at = k, s
    if best < SEASON_SHARE * len(runs):
        return False
    years = {(a - timedelta(days=(a.timetuple().tm_yday - at) % 366)).year
             for a, _ in runs if (a.timetuple().tm_yday - at) % 366 < SEASON_DAYS}
    return len(years) >= 2


def overdue(hist: R.History, day: date, kind: str = "outfit", skip=(), min_runs: int = 6, min_days: int = 90,
            min_factor: float = 3.0, seasonal: bool = False) -> list:
    """Every candidate of `kind` as of `day`, most overdue first:
    [{key, raw, runs, gaps, typical, gone, factor, last}]."""
    rows = []
    for key in hist.days:
        raw = hist.items[key]
        if (raw.get("type") or {}).get("value") != kind or key in skip:
            continue
        runs = hist.runs(key, until=day)
        if len(runs) < min_runs or runs[-1][1] >= day:         # in the shop on `day`
            continue
        gaps = [(b[0] - a[1]).days for a, b in zip(runs, runs[1:])]
        typical = statistics.median(gaps)
        gone = hist.gone_days(key, day)
        if gone is None or gone < min_days or gone / typical < min_factor:
            continue
        if not seasonal and _seasonal(runs):
            continue
        rows.append({"key": key, "raw": raw, "runs": runs, "gaps": gaps, "typical": typical, "gone": gone,
                     "factor": gone / typical, "last": runs[-1][1]})
    rows.sort(key=lambda r: (-r["factor"], -r["gone"], r["raw"].get("name", "")))
    return rows


def _window(runs: list, day: date, width: float) -> tuple:
    """(first day of the strip, whether it starts later than the item's first
    visit). Every visit when that reads; else about three years, keeping at
    least a year of visits before the last one in view."""
    first = runs[0][0].replace(day=1)
    ppd = width / max(1, (day - first).days)
    starts = [a for a, _ in runs]
    spacing = statistics.median([(b - a).days for a, b in zip(starts, starts[1:])]) * ppd
    if len(runs) <= 60 and spacing >= 8:
        return first, False
    start = date(day.year - 3, day.month, 1)
    last = runs[-1][1]
    if (last - start).days < 365:
        start = date(last.year - 1, last.month, 1)
    return (start, True) if start > first else (first, False)


def _mon_year(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.year}"


# ------------------------------------------------------------------ measuring

def _aw(text: str) -> float:
    """Anton text width in em (the .d class: capitals, .01em tracking)."""
    return sum(ANTON.get(ch, .5) + .01 for ch in text.upper())


def _wrap(text: str, size: float, width: float) -> list:
    """Words into lines of at most `width` px (Anton, .25em between words)."""
    lines, cur = [], ""
    for w in text.split():
        cand = f"{cur} {w}".strip()
        if cur and (_aw(cand) + .25 * cand.count(" ")) * size > width:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    return lines + [cur]


def _name_fit(name: str, width: float, big: int = 80, small: int = 46, max_lines: int = 3) -> tuple:
    """(size, lines): the largest size that keeps the name on one line down to
    64 px, else on two lines, else three."""
    for lim, lo in ((1, 64), (2, 52), (max_lines, small)):
        for s in range(big, lo - 1, -2):
            ls = _wrap(name, s, width)
            if len(ls) <= lim and all(_aw(x) * s <= width for x in ls):
                return s, ls
    s = small
    while s > 30 and any(_aw(x) * s > width for x in _wrap(name, s, width)):
        s -= 2
    return s, _wrap(name, s, width)


# ------------------------------------------------------------------ pieces

def _a(*entries) -> str:
    return style_anim(*entries)


def _mono(text: str, x: float, y: float, size: float = 22, t: float = None, color: str = "", align: str = "left",
          weight: int = 500, ls: str = "", extra: str = "") -> str:
    pos = {"left": f"left:{x:.0f}px;", "right": f"right:{W - x:.0f}px;",
           "center": f"left:{x - 540:.0f}px;width:1080px;text-align:center;"}[align]
    anim = _a(an("odrise", t, .45)) if t is not None else ""
    col = f"color:{color};" if color else ""
    sp = f"letter-spacing:{ls};" if ls else ""
    return (f'<div class="abs od-m" style="{pos}top:{y:.0f}px;font-size:{size:.0f}px;font-weight:{weight};'
            f'{col}{sp}{anim}{extra}">{esc(text)}</div>')


# Fine grey noise (desaturated, so it reads as film grain, not colour speckle),
# laid over the slate at low opacity with a normal blend: overlay does nothing
# on a near-black background. Static, so the browser paints it once.
GRAIN = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='256' height='256'>"
         "<filter id='g'><feTurbulence type='fractalNoise' baseFrequency='.82' numOctaves='2' stitchTiles='stitch'/>"
         "<feColorMatrix type='saturate' values='0'/></filter>"
         "<rect width='100%25' height='100%25' filter='url(%23g)'/></svg>")


def _backdrop() -> str:
    """Deep slate, a faint chart-paper grid, grain and a soft vignette: one
    layer under everything, the whole video."""
    grid = ("repeating-linear-gradient(0deg,rgba(255,255,255,.024) 0 1px,transparent 1px 64px),"
            "repeating-linear-gradient(90deg,rgba(255,255,255,.024) 0 1px,transparent 1px 64px)")
    return ('<div class="full" data-safe="ignore" style="z-index:0;overflow:hidden;'
            'background:linear-gradient(180deg,#171b20 0%,#111418 46%,#0b0d10 100%)">'
            f'<div class="full" style="background-image:{grid};background-position:12px 4px"></div>'
            f'<div class="full" style="background:url(&quot;{GRAIN}&quot;);opacity:.075"></div>'
            '<div class="full" style="background:radial-gradient(ellipse 90% 72% at 50% 40%,transparent 50%,'
            'rgba(0,0,0,.5) 100%)"></div></div>')


def _figure(ctx: Ctx, it: dict, cx: float, bottom: float, h: float, t: float, enter: str = "rise",
            maxw: float = FIG_MAXW, idle: bool = True) -> str:
    """The cosmetic standing on a floor line at `bottom`: an outfit keeps only its
    figure (trim), everything else is centred in the box. A soft contact shadow,
    a real drop shadow, and a slow bob."""
    uri = ctx.art(it)
    trim = trim_for(it)
    pos = "50% 100%" if trim == "figure" else "50% 60%"
    if uri:
        tr = ' data-trim="figure"' if trim == "figure" else " data-trim"
        art = (f'<img class="art"{tr} data-name="{esc(it["name"])}" src="{uri}" '
               f'style="height:{h:.0f}px;max-width:{maxw:.0f}px;object-position:{pos};'
               f'filter:drop-shadow(0 26px 30px rgba(0,0,0,.6))">')
    else:
        art = (f'<div class="d" style="height:{h:.0f}px;width:{min(h * .6, maxw):.0f}px;display:flex;'
               f'align-items:center;justify-content:center;text-align:center;font-size:{h * .08:.0f}px;color:{GREY};'
               f'border:3px dashed rgba(255,255,255,.2);border-radius:18px">{esc(it["name"])}</div>')
    enter_a = {"rise": an("odfig", t, .75), "hop": an("hop", t, .45, fill="none"), "none": ""}[enter]
    bob = an("odbob", t + .75, 2.9, "ease-in-out", "infinite", "alternate") if idle else ""
    shadow = ""
    if trim == "figure":
        sw = min(maxw * .8, h * .42)
        shadow = (f'<div class="abs" style="left:50%;bottom:-{h * .022:.0f}px;width:{sw:.0f}px;height:{h * .05:.0f}px;'
                  f'margin-left:-{sw / 2:.0f}px;border-radius:50%;background:radial-gradient(closest-side,'
                  f'rgba(0,0,0,.7),rgba(0,0,0,0));{_a(an("odin", t, .5)) if enter == "rise" else ""}"></div>')
    return (f'<div class="abs" style="left:{cx - maxw / 2:.0f}px;top:{bottom - h:.0f}px;width:{maxw:.0f}px;'
            f'height:{h:.0f}px;display:flex;justify-content:center;align-items:flex-end">{shadow}'
            f'<div style="{_a(enter_a)}"><div style="transform-origin:50% 100%;{_a(bob)}">{art}</div></div></div>')


class _Axis:
    """Days to x on a strip from `start` (x0) to `day` (x1, TODAY)."""

    def __init__(self, start: date, day: date, x0: float, x1: float):
        self.start, self.day, self.x0, self.x1 = start, day, x0, x1
        self.ppd = (x1 - x0) / max(1, (day - start).days)

    def x(self, d: date) -> float:
        return self.x0 + (d - self.start).days * self.ppd


def _bars(ax: _Axis, runs: list, h: float, min_w: float = 4) -> str:
    """Each visit (run) as a bar, in the strip's own coordinates (x0 = 0)."""
    out = []
    for a, b in runs:
        if b < ax.start:
            continue
        a = max(a, ax.start)
        x = ax.x(a) - ax.x0
        w = max(min_w, ((b - a).days + 1) * ax.ppd)
        out.append(f'<rect x="{x:.2f}" y="0" width="{w:.2f}" height="{h:.0f}" rx="1" fill="{PAPER}"/>')
    return "".join(out)


def _band(ax: _Axis, last: date, h: float, pid: str, edge: float = 2, hatch: float = .2, gap: int = 11) -> str:
    """The empty stretch, from its last day in the shop to TODAY: lime hatching
    between two lime rules (`pid`: a page-unique id for the hatch pattern)."""
    x = ax.x(last) - ax.x0
    w = ax.x1 - ax.x(last)
    return (f'<defs><pattern id="{pid}" patternUnits="userSpaceOnUse" width="{gap}" height="{gap}" '
            f'patternTransform="rotate(-45)"><rect x="0" y="0" width="2.2" height="{gap}" '
            f'fill="rgba(232,255,58,{hatch})"/></pattern></defs>'
            f'<rect x="{x:.2f}" y="0" width="{w:.2f}" height="{h:.0f}" fill="rgba(232,255,58,.045)"/>'
            f'<rect x="{x:.2f}" y="0" width="{w:.2f}" height="{h:.0f}" fill="url(#{pid})"/>'
            f'<rect x="{x:.2f}" y="0" width="{w:.2f}" height="{edge}" fill="{LIME}"/>'
            f'<rect x="{x:.2f}" y="{h - edge:.1f}" width="{w:.2f}" height="{edge}" fill="{LIME}"/>')


def _ticks(ax: _Axis) -> list:
    """(x, label) for the axis: every year boundary; on a short strip also the
    quarters. Labels too close to each other or to the ends are dropped."""
    marks = []
    y = ax.start.year + (0 if ax.start.month == 1 and ax.start.day == 1 else 1)
    years = [date(k, 1, 1) for k in range(y, ax.day.year + 1) if date(k, 1, 1) <= ax.day]
    if len(years) >= 2:
        marks = [(ax.x(d), str(d.year)) for d in years]
    else:
        d = ax.start.replace(day=1)
        while d <= ax.day:
            if d.month in (1, 4, 7, 10) and d > ax.start:
                marks.append((ax.x(d), str(d.year) if d.month == 1 else MONTHS[d.month - 1]))
            d = (d + timedelta(days=32)).replace(day=1)
    out, last_x = [], -1e9
    for x, lab in marks:
        half = len(lab) * .66 * 21 / 2
        if x - half < ax.x0 + 4 or x + half > ax.x1 - 6 or x - last_x < half * 2 + 26:
            continue
        out.append((x, lab))
        last_x = x
    return out


def _grid(ax: _Axis, top: float, h: float, marks: list) -> str:
    return "".join(f'<div class="abs" style="left:{x - .5:.1f}px;top:{top - 6:.0f}px;width:1px;height:{h + 12:.0f}px;'
                   f'background:rgba(255,255,255,.13)"></div>' for x, _ in marks)


def _today(x: float, top: float, bottom: float, t: float = None, size: int = 22, below: bool = False) -> str:
    """The TODAY tag and its lime line, hung left of x so it stays on screen;
    the tag at the line's top, or its bottom (below=True)."""
    anim = _a(an("odtoday", t, .5, "cubic-bezier(.3,1.4,.5,1)")) if t is not None else ""
    where, radius = ("bottom:0", "3px 0 3px 3px") if below else ("top:0", "3px 3px 0 3px")
    return (f'<div class="abs" style="left:{x - 2:.1f}px;top:{top:.0f}px;width:4px;height:{bottom - top:.0f}px;{anim}">'
            f'<div class="abs" style="left:0;top:0;width:4px;height:100%;background:{LIME}"></div>'
            f'<div class="abs od-m" style="right:-2px;{where};font-size:{size}px;font-weight:700;color:#101214;'
            f'background:{LIME};padding:2px 10px 1px;border-radius:{radius};letter-spacing:.12em">TODAY</div>'
            f'</div>')


# ------------------------------------------------------------------ one item's screen

def _numline(r: dict, t: float) -> str:
    """GONE N DAYS: the count runs with the playhead across the empty stretch
    (same start, length and easing), then the exact figure with its comma."""
    gone = r["gone"]
    num_s, word_s = 196, 90
    final = f"{gone:,}"
    box = _aw(final) * num_s + 4
    roll = f'odroll{r["uid"]}'
    rise = _a(an("odrise", t, .4))
    return (f'<style>@keyframes {roll}{{from{{--n:0}}to{{--n:{gone}}}}}</style>'
            f'<div class="abs" style="left:{SAFE_LEFT}px;top:{NUM_Y}px;display:flex;align-items:baseline;'
            f'gap:22px;white-space:nowrap">'
            f'<div class="d" style="font-size:{word_s}px;color:{PAPER};{rise}">GONE</div>'
            f'<div class="d" style="position:relative;width:{box:.0f}px;text-align:right;font-size:{num_s}px;'
            f'color:{LIME};{rise}">'
            f'<span class="count" style="position:absolute;right:0;top:0;'
            f'{_a(an(roll, t, D_B, EASE_B), an("odout", t + D_B, .04))}"></span>'
            f'<span style="display:inline-block;transform-origin:100% 80%;'
            f'{_a(an("odin", t + D_B, .04), an("odsettle", t + D_B, .45))}">{final}</span></div>'
            f'<div class="d" style="font-size:{word_s}px;color:{PAPER};{_a(an("odrise", t + .08, .4))}">'
            f'{"DAY" if gone == 1 else "DAYS"}</div></div>')


def _chart(comp: Comp, r: dict, t0: float) -> str:
    """The item's timeline: every visit as a bar, then the empty stretch to
    TODAY. A playhead sweeps it; the usual gap is then laid end to end across
    the empty stretch, xN, where N is the stamped factor."""
    ax = _Axis(r["start"], r["day"], X0, X1)
    cw = X1 - X0
    top, h = STRIP_Y, STRIP_H
    marks = _ticks(ax)
    uid = r["uid"]
    last_end = min(X1, ax.x(r["last"]) + max(4, ax.ppd))
    a = (last_end - X0) / cw
    pa = D_A / (D_A + D_B) * 100
    comp.css(f"@keyframes odsw{uid}{{0%{{clip-path:inset(-16px 100% -16px 0);animation-timing-function:linear}}"
             f"{pa:.3f}%{{clip-path:inset(-16px {100 - a * 100:.3f}% -16px 0);animation-timing-function:{EASE_B}}}"
             f"100%{{clip-path:inset(-16px 0% -16px 0)}}}}"
             f"@keyframes odph{uid}{{0%{{transform:translateX(0);animation-timing-function:linear}}"
             f"{pa:.3f}%{{transform:translateX({a * cw:.1f}px);animation-timing-function:{EASE_B}}}"
             f"100%{{transform:translateX({cw:.1f}px)}}}}")
    tc, ta = t0 + T_CHART, t0 + T_A
    out = [_mono(r["range_label"], X0, TAG_Y, 22, tc),
           # the track, its baseline and the year lines
           f'<div class="abs" style="left:{X0}px;top:{top}px;width:{cw}px;height:{h}px;background:rgba(255,255,255,.04);'
           f'transform-origin:0 50%;{_a(an("odgrow", tc, .5))}"></div>',
           f'<div class="full" style="{_a(an("odin", tc + .1, .4))}">{_grid(ax, top, h, marks)}</div>',
           "".join(f'<div class="abs od-m" style="left:{x - 60:.0f}px;width:120px;text-align:center;'
                   f'top:{AXIS_Y}px;font-size:21px;{_a(an("odin", tc + .15, .4))}">{lab}</div>' for x, lab in marks),
           # the visits and the empty stretch, revealed by the sweep
           f'<div class="abs" style="left:{X0}px;top:{top}px;width:{cw}px;height:{h}px;'
           f'{_a(an(f"odsw{uid}", ta, D_A + D_B))}">'
           f'<svg width="{cw}" height="{h}" style="display:block;overflow:visible">'
           f'{_band(ax, r["last"], h, f"odh{uid}")}{_bars(ax, r["runs"], h)}</svg></div>',
           # the playhead: white, handing over to TODAY
           f'<div class="abs" style="left:{X0 - 1.5:.1f}px;top:{top - 12}px;width:3px;height:{h + 24}px;'
           f'{_a(an("odin", ta, .1), an("odout", ta + D_A + D_B, .12))}">'
           f'<div class="full" style="background:#fff;{_a(an(f"odph{uid}", ta, D_A + D_B))}"></div></div>',
           _today(X1, TAG_Y - 1, top + h + 6, t0 + T_TODAY)]
    # what the empty stretch is, when there's room to say it
    band_w = X1 - last_end
    label = "NOT IN THE ITEM SHOP"
    if band_w >= len(label) * .7 * 19 + 40:
        out.append(f'<div class="abs od-m" style="left:{last_end + 14:.0f}px;top:{top + 9}px;font-size:19px;'
                   f'font-weight:700;color:{LIME};letter-spacing:.12em;{_a(an("odin", t0 + T_B + .35, .4))}">'
                   f'{label}</div>')
    # the usual gap, end to end across the empty stretch
    n = int(r["factor"])
    w = r["typical"] * ax.ppd
    xs = ax.x(r["last"])
    g = min(1.6, w * .16)
    rects = "".join(f'<rect x="{k * w + g:.2f}" y="0" width="{max(.7, w - 2 * g):.2f}" height="{RULER_H}" '
                    f'fill="{PAPER}"/>' for k in range(n))
    tt, dt = t0 + T_TILE, r["d_tile"]
    ry = top + h - RULER_H - 7
    comp.css(f"@keyframes odrl{uid}{{from{{clip-path:inset(-4px 100% -4px 0)}}to{{clip-path:inset(-4px 0 -4px 0)}}}}"
             f"@keyframes odrx{uid}{{from{{transform:translateX(0)}}to{{transform:translateX({n * w:.2f}px)}}}}"
             f"@keyframes odrn{uid}{{from{{--n:0}}to{{--n:{n}}}}}")
    steps = f"steps({n},jump-start)"
    out.append(f'<div class="abs" style="left:{xs:.2f}px;top:{ry}px;width:{n * w:.2f}px;height:{RULER_H}px;'
               f'{_a(an(f"odrl{uid}", tt, dt, steps))}">'
               f'<svg width="{n * w:.2f}" height="{RULER_H}" style="display:block">{rects}</svg></div>')
    out.append(f'<div class="abs" style="left:{xs:.2f}px;top:{ry - 8}px;width:0;height:0;'
               f'{_a(an("odin", tt, .05), an(f"odrx{uid}", tt, dt, steps))}">'
               f'<div class="abs od-m" style="right:6px;bottom:0;font-size:24px;font-weight:700;color:#fff;'
               f'background:rgba(13,15,18,.86);padding:1px 8px 0;border-radius:4px;letter-spacing:.04em">'
               f'×<span class="count" style="{_a(an(f"odrn{uid}", tt, dt, steps))}"></span></div></div>')
    return "".join(out)


def _stats(r: dict, t0: float) -> str:
    """The facts column, anchored to the bottom of the safe box."""
    x = COL_X
    typ = int(r["typical"])
    out = []

    def rule(y, t):
        return (f'<div class="abs" style="left:{x}px;top:{y:.0f}px;width:{COL_W}px;height:2px;background:{DIM};'
                f'transform-origin:0 50%;{_a(an("odgrow", t, .45))}"></div>')

    def value(text, y, size, t, color=PAPER):
        return (f'<div class="abs d" style="left:{x - 2}px;top:{y:.0f}px;font-size:{size}px;color:{color};'
                f'white-space:nowrap;{_a(an("odrise", t, .45))}">{esc(text)}</div>')

    t1, t2, t3 = (t0 + s for s in T_STATS)
    # 1: the typical gap
    out += [rule(980, t1 - .05), _mono("USUALLY BACK EVERY", x, 998, 22, t1),
            value(f"~{typ} DAY" + ("" if typ == 1 else "S"), 1030, 80, t1 + .06),
            _mono("TYPICAL GAP BETWEEN VISITS", x, 1111, 19, t1 + .12, ls=".06em")]
    # 2: how many times it has been in the shop
    out += [rule(1152, t2 - .05), _mono("IN THE ITEM SHOP", x, 1170, 22, t2),
            value(f"{r['times']} TIMES", 1202, 80, t2 + .06)]
    # 3: its last day in the shop
    out += [rule(1287, t3 - .05), _mono("LAST SEEN", x, 1305, 22, t3),
            value(_d(r["last"]), 1337, 66, t3 + .06)]
    return "".join(out)


def _sticker(n: int, x: float, y: float, t: float, rot: float = -4, big: int = 104) -> str:
    """N× LONGER THAN USUAL, stamped on."""
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;--r:{rot}deg;transform-origin:30% 60%;'
            f'{_a(an("odstamp", t, .42, "cubic-bezier(.3,.7,.3,1)"))}">'
            f'<div style="background:{LIME};color:#101214;border-radius:6px;padding:14px 20px 13px 18px;'
            f'box-shadow:0 9px 0 rgba(0,0,0,.34),0 26px 36px rgba(0,0,0,.42)">'
            f'<div class="d" style="font-size:{big}px;line-height:.86;white-space:nowrap">{n}×</div>'
            f'<div class="d" style="font-size:{big * .32:.0f}px;line-height:1;margin-top:9px;letter-spacing:.03em;'
            f'white-space:nowrap">LONGER THAN USUAL</div></div></div>')


def _card(comp: Comp, ctx: Ctx, r: dict, t0: float, dur: float, rank: int):
    it = r["item"]
    inner = []
    # the rank, top right (the corner at the left is the code badge's)
    inner.append(f'<div class="abs" style="right:{W - SAFE_RIGHT_TOP + 4}px;top:238px;text-align:right;'
                 f'{_a(an("odrise", t0 + .05, .45))}">'
                 f'<div class="od-m" style="font-size:22px;letter-spacing:.16em">MOST OVERDUE</div>'
                 f'<div class="d" style="font-size:108px;color:{PAPER};margin-top:8px">#{rank}</div></div>')
    inner.append(_numline(r, t0 + T_B))
    inner.append(_chart(comp, r, t0))
    fig_h = FIG_BOTTOM - FIG_TOP
    inner.append(_figure(ctx, it, FIG_CX, FIG_BOTTOM, fig_h, t0 + T_FIG))
    # the name and what it is
    size, lines = _name_fit(it["name"], COL_W)
    y = 772
    inner.append(f'<div class="abs d" style="left:{COL_X - 2}px;top:{y}px;width:{COL_W + 40}px;font-size:{size}px;'
                 f'line-height:.94;color:{PAPER}">'
                 + "".join(f'<div style="white-space:nowrap;{_a(an("odrise", t0 + T_NAME + i * .07, .45))}">'
                           f'{esc(ln)}</div>' for i, ln in enumerate(lines)) + "</div>")
    y += size * .94 * len(lines) + 12
    kind = f"{it['rarity_label']} {it['type']}".strip().upper()
    inner.append(_mono(kind, COL_X, y, 21, t0 + T_NAME + .15))
    inner.append(_stats(r, t0))
    inner.append(_sticker(r["n"], SAFE_LEFT + 16, 1262, t0 + r["t_stick"], big=94))
    # Out quickly while the next screen builds: the persistent backdrop stays, so
    # the change reads as the page turning over, not two pages on top of each other.
    comp.scene(t0, t0 + dur + .12, "".join(inner), fade_in=.2, fade_out=.3)
    # sound: in, a tick as the playhead passes visits, the count, TODAY, the facts, the ruler, the stamp
    comp.cue(t0 + .05, "whoosh")
    xs = sorted({ax_x for ax_x in r["bar_x"] if ax_x <= r["a_px"]})
    for x in xs[:: max(1, len(xs) // 5)][:5]:
        comp.cue(t0 + T_A + D_A * (x - X0) / max(1, r["a_px"] - X0), "tick")
    comp.cue(t0 + T_B, "drumroll")
    comp.cue(t0 + T_TODAY, "slam")
    for s in T_STATS:
        comp.cue(t0 + s, "pop")
    comp.cue(t0 + T_TILE, "flap")
    if r["d_tile"] > .8:
        comp.cue(t0 + T_TILE + .5, "flap")
    comp.cue(t0 + r["t_stick"], "stamp")


# ------------------------------------------------------------------ hook and outro

STAMP_W, STAMP_H = 358, 120       # cc_formats' USE CODE: BAD stamp, measured in the render browser


def _stamp(comp: Comp, x: float, y: float, dock_start: float, dock_end: float) -> str:
    """USE CODE: BAD, big, for the thumbnail. It flies into the top-left corner
    and shrinks into the corner badge (same design at 1.4x), which takes over as
    it lands. A solid shadow, no glow."""
    k = BADGE_H / STAMP_H
    dock = comp.uid("oddock")
    comp.css(f"@keyframes {dock}{{0%{{transform:rotate(-3deg);opacity:1}}"
             f"99.9%{{transform:translate({BADGE_X - x:.1f}px,{BADGE_Y - y:.1f}px) scale({k:.4f}) rotate(0deg);opacity:1}}"
             f"100%{{transform:translate({BADGE_X - x:.1f}px,{BADGE_Y - y:.1f}px) scale({k:.4f}) rotate(0deg);opacity:0}}}}")
    comp.css(f".codebadge,.codetag{{animation:fadein .01s linear {dock_end - .01:.3f}s both paused !important}}")
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;transform-origin:0 0;z-index:5;'
            f'{_a(an(dock, dock_start, dock_end - dock_start, "cubic-bezier(.6,0,.4,1)"))}">'
            f'<div style="{_a(an("odthump", .2, .4, fill="none"), an("pulse", 1.35, .5, "ease-in-out", fill="none"))}">'
            f'<div data-safe="key" data-name="code" style="display:flex;align-items:center;gap:17px;background:{LIME};'
            f'color:#0A0A0B;border-radius:22px;padding:11px 28px 8px 25px;'
            f'box-shadow:0 11px 0 rgba(0,0,0,.4),0 26px 40px rgba(0,0,0,.45)">'
            f'<div style="font-size:32px;font-weight:900;line-height:1.02;letter-spacing:.12em">USE<br>CODE:</div>'
            f'<div class="d" style="font-size:112px;line-height:.9;letter-spacing:.02em">BAD</div></div>'
            f'<div style="margin:5.6px 0 0 5.6px;font-size:32px;font-weight:700;line-height:1.3;'
            f'color:rgba(255,255,255,.92);text-shadow:0 2px 8px rgba(0,0,0,.9)">#EpicPartner</div></div></div>')


def _hook(comp: Comp, ctx: Ctx, picks: list, sub1: str, sub2: str, end: float):
    """Frame 0 is the thumbnail, complete: the date line, OVERDUE, the #1's real
    timeline under it (GONE N DAYS in its empty stretch), the one-line premise,
    the two most overdue and USE CODE: BAD. Then beats, and the code flies into
    the corner."""
    top1, top2 = picks[0], picks[1]
    dock_end = min(2.6, end - .7)
    dock_start = dock_end - .5
    inner = []
    kick = f"ITEM SHOP HISTORY · {ctx.day_label.upper()}"
    inner.append(f'<div class="full" style="{_a(an("odout", dock_start, .3))}">'
                 + _mono(kick, 540, 288, 25, color="#C9CED3", align="center", ls=".16em") + "</div>")
    inner.append(f'<div class="abs d" style="left:0;width:{W}px;top:334px;text-align:center;font-size:236px;'
                 f'line-height:.9;color:{PAPER};text-shadow:0 10px 0 rgba(0,0,0,.3);transform-origin:50% 70%;'
                 f'{_a(an("odthump", .2, .45, fill="none"))}">OVERDUE</div>')
    # the #1's real timeline under the title
    x0, x1 = 118, 962
    ax = _Axis(top1["start"], ctx.day, x0, x1)
    sy, sh = 566, 54
    inner.append(f'<div class="abs" style="left:{x0}px;top:{sy}px;width:{x1 - x0}px;height:{sh}px;'
                 f'background:rgba(255,255,255,.05)"></div>'
                 f'<div class="abs" style="left:{x0}px;top:{sy}px"><svg width="{x1 - x0}" height="{sh}" '
                 f'style="display:block;overflow:visible">{_band(ax, top1["last"], sh, "odhk", hatch=.24)}'
                 f'{_bars(ax, top1["runs"], sh, 3)}</svg></div>')
    gone = f"GONE {top1['gone']:,} DAYS"
    bx = min(x1, ax.x(top1["last"]) + max(3, ax.ppd))
    if x1 - bx >= len(gone) * .7 * 24 + 36:
        inner.append(f'<div class="abs od-m" style="left:{bx + 16:.0f}px;top:{sy + 13}px;font-size:24px;font-weight:700;'
                     f'color:{LIME};letter-spacing:.1em;background:rgba(14,16,19,.82);padding:1px 8px 0;'
                     f'border-radius:3px">{gone}</div>')
    inner.append(_today(x1, sy - 6, sy + sh + 36, size=20, below=True))
    inner.append(_mono(f"{top1['item']['name']} · every Item Shop visit", x0, sy + sh + 11, 19, ls=".08em"))
    # the premise
    inner.append(f'<div class="abs od-t" style="left:0;width:{W}px;top:674px;text-align:center;font-size:37px;'
                 f'font-weight:700;line-height:1.16;color:{PAPER}">{esc(sub1)}<br>'
                 f'<span style="color:{LIME}">{esc(sub2)}</span></div>')
    # the two most overdue, and the code
    mid = (SAFE_LEFT + SAFE_RIGHT) / 2
    inner.append(_figure(ctx, top2["item"], mid + 200, 1360, 556, .3, "hop", 380))
    inner.append(_figure(ctx, top1["item"], mid - 186, 1380, 598, .15, "hop", 400))
    inner.append(_stamp(comp, mid - STAMP_W / 2, 1246, dock_start, dock_end))
    comp.scene(0, end, "".join(inner), fade_in=.01, fade_out=.3)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.3, "whoosh"); comp.cue(.9, "pop")
    comp.cue(dock_start, "whoosh")


def _outro(comp: Comp, ctx: Ctx, picks: list, start: float, end: float, ask: str):
    """The ask, all of them ranked on one shared time axis, and the code big."""
    inner = []
    lines = ["WHICH ONE SHOULD", "COME BACK FIRST?"] if ask == "WHICH ONE SHOULD COME BACK FIRST?" else [ask]
    size = min(104, int(900 / max(_aw(x) for x in lines)))
    for i, ln in enumerate(lines):
        inner.append(f'<div class="abs d" style="left:{SAFE_LEFT}px;top:{386 + i * size * .95:.0f}px;font-size:{size}px;'
                     f'color:{LIME if i == len(lines) - 1 else PAPER};white-space:nowrap;'
                     f'{_a(an("odrise", start + .1 + i * .1, .5))}">{esc(ln)}</div>')
    # rows: rank | bust | name over its strip (one shared time axis) | the factor
    first = min(p["start"] for p in picks)
    ax_x0, ax_x1 = 216, 752
    ax = _Axis(first, ctx.day, ax_x0, ax_x1)
    row_h = 118
    y0 = 604
    for i, p in enumerate(picks):
        y = y0 + i * row_h
        t = start + .35 + i * .12
        it = p["item"]
        uri = ctx.art(it)
        trim = ' data-trim="figure"' if trim_for(it) == "figure" else " data-trim"
        fit = "object-fit:cover;object-position:50% 0" if trim_for(it) == "figure" else "object-fit:contain"
        bust = (f'<img{trim} data-name="{esc(it["name"])}" src="{uri}" style="display:block;width:100%;'
                f'height:100%;{fit}">' if uri else "")
        nsize = min(46, int((ax_x1 - ax_x0 - 8) / max(1, _aw(it["name"]))))
        inner.append(f'<div class="abs" style="left:{SAFE_LEFT}px;top:{y}px;width:{SAFE_RIGHT - SAFE_LEFT}px;'
                     f'height:{row_h - 14}px;{_a(an("odrise", t, .45))}">'
                     f'<div class="abs od-m" style="left:0;top:33px;font-size:26px;font-weight:700;color:{LIME};'
                     f'letter-spacing:0">#{i + 1}</div>'
                     f'<div class="abs" style="left:44px;top:0;width:98px;height:98px;border-radius:10px;overflow:hidden;'
                     f'background:#1f252b;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)">{bust}</div>'
                     f'<div class="abs d" style="left:{ax_x0 - SAFE_LEFT}px;top:{46 - nsize:.0f}px;font-size:{nsize}px;'
                     f'color:{PAPER};white-space:nowrap">{esc(it["name"])}</div>'
                     f'<div class="abs d" style="right:0;top:10px;font-size:66px;color:{LIME};white-space:nowrap">'
                     f'{p["n"]}×</div></div>')
        sy, sh = y + 62, 24
        inner.append(f'<div class="abs" style="left:{ax_x0}px;top:{sy}px;width:{ax_x1 - ax_x0}px;height:{sh}px;'
                     f'background:rgba(255,255,255,.05);{_a(an("odwipe", t + .15, .7))}">'
                     f'<svg width="{ax_x1 - ax_x0}" height="{sh}" style="display:block;overflow:visible">'
                     f'{_band(ax, p["last"], sh, f"odho{i}", 1.5, .26, 8)}{_bars(ax, p["runs"], sh, 2.5)}</svg></div>')
    ly = y0 + len(picks) * row_h - 8
    inner.append(f'<div class="abs od-m" style="left:{ax_x0}px;top:{ly}px;font-size:19px;'
                 f'{_a(an("odin", start + .9, .4))}">ITEM SHOP VISITS SINCE {_mon_year(first)}</div>')
    inner.append(f'<div class="abs" style="left:{ax_x1 - 1}px;top:{y0 + 54}px;width:2px;'
                 f'height:{ly - y0 - 54:.0f}px;background:{LIME};{_a(an("odin", start + .9, .3))}"></div>')
    inner.append(_mono("TODAY", ax_x1 + 1, ly, 19, start + .9, color=LIME, align="right", weight=700))
    # the code, big
    cw, ch = 560, 150
    cx = (SAFE_LEFT + SAFE_RIGHT) / 2 - cw / 2
    inner.append(f'<div class="abs" style="left:{cx:.0f}px;top:{SAFE_BOTTOM - ch - 18}px;--r:-2deg;'
                 f'{_a(an("odstamp", start + 1.2, .45, "cubic-bezier(.3,.7,.3,1)"))}">'
                 f'<div data-safe="key" data-name="code" style="width:{cw}px;height:{ch}px;display:flex;'
                 f'align-items:center;justify-content:center;gap:22px;background:{LIME};color:#0A0A0B;border-radius:22px;'
                 f'box-shadow:0 11px 0 rgba(0,0,0,.4),0 26px 40px rgba(0,0,0,.45)">'
                 f'<div style="font-size:42px;font-weight:900;line-height:1.02;letter-spacing:.1em">USE<br>CODE:</div>'
                 f'<div class="d" style="font-size:146px;line-height:.9;letter-spacing:.02em">BAD</div></div></div>')
    comp.scene(start, end, "".join(inner), fade_in=.3, fade_out=.01, z=2)
    comp.cue(start + .1, "whoosh")
    for i in range(len(picks)):
        comp.cue(start + .35 + i * .12, "tick")
    comp.cue(start + 1.2, "stamp")


# ------------------------------------------------------------------ the video

def build(ctx: Ctx, kind: str = "outfit", count: int = 5, min_count: int = 4, min_runs: int = 6,
          min_days: int = 90, min_factor: float = 3.0, seasonal: bool = False) -> Video | None:
    """OVERDUE <kind>: the `count` most overdue, as of ctx.day. None when fewer
    than `min_count` qualify."""
    if kind not in KINDS:
        return None
    word, words_, tags_extra = KINDS[kind]
    hist = history()
    today_ids = {i.lower() for row in (ctx.shop or {}).get("items", []) for i in R.shop_ids(row)}
    picks, sets = [], set()
    for r in overdue(hist, ctx.day, kind, today_ids, min_runs, min_days, min_factor, seasonal):
        it = _item(r["raw"])
        key = (it["set"], r["last"])
        if it["set"] and key in sets:
            continue          # a set that left together counts once
        if not ctx.art(it):
            continue
        if it["set"]:
            sets.add(key)
        r["item"] = it
        picks.append(r)
        if len(picks) == count:
            break
    if len(picks) < max(2, min_count):
        return None

    n = len(picks)
    for i, r in enumerate(picks):
        r["uid"] = f"{i}"
        r["day"] = ctx.day
        r["times"] = len(r["runs"])
        r["n"] = int(r["factor"])
        r["start"], r["windowed"] = _window(r["runs"], ctx.day, X1 - X0)
        r["range_label"] = f"EVERY ITEM SHOP VISIT SINCE {_mon_year(r['start'])}"
        ax = _Axis(r["start"], ctx.day, X0, X1)
        r["bar_x"] = [ax.x(max(a, r["start"])) for a, b in r["runs"] if b >= r["start"]]
        r["a_px"] = min(X1, ax.x(r["last"]) + max(4, ax.ppd))
        r["d_tile"] = min(1.7, .3 + .09 * r["n"])
        r["t_stick"] = T_TILE + r["d_tile"] + .25

    rlen = max(R_MIN, min(R_MAX, (62 - OUTRO - HOOK) / n))
    content_end = HOOK + n * rlen
    comp = Comp(pad_to(content_end, outro=OUTRO))
    comp.use_fonts("IBM Plex Mono")
    comp.css(CSS)
    comp.add(_backdrop())

    typs = [r["typical"] for r in picks]
    lo, hi = int(min(typs)), int(max(typs))
    if FEW_WEEKS[0] <= min(typs) and max(typs) <= FEW_WEEKS[1]:
        every, every_cap = "every few weeks", "every few weeks"
    else:
        every = f"every ~{lo}–{hi} days" if lo != hi else f"every ~{lo} days"
        every_cap = every
    since = "years" if min(r["gone"] for r in picks) >= 730 else "months"
    sub1 = f"{words_.capitalize()} that usually come back {every}…"
    sub2 = f"…that haven't been back in {since}."
    _hook(comp, ctx, picks, sub1, sub2, HOOK + .12)

    for k, r in enumerate(reversed(picks)):
        _card(comp, ctx, r, HOOK + k * rlen, rlen, n - k)

    ask = "WHICH ONE SHOULD COME BACK FIRST?"
    comp.cue(content_end + .25, "slam")
    _outro(comp, ctx, picks, content_end, comp.duration, ask)
    comp.add(code_badge(0))
    comp.add(disclosure())

    top = picks[0]
    body = "\n".join(
        f"{num(k)} {r['item']['name']} · gone {r['gone']:,} days · usually back every ~{int(r['typical'])} · "
        f"{r['n']}× longer than usual" for k, r in enumerate(picks, 1))
    tags = _hashtags(*tags_extra, top["item"]["name"])
    return Video(
        f"overdue_{kind}", comp,
        title=f"Overdue Fortnite {words_.title()} — Item Shop History, {ctx.day_label}",
        yt_title=f"Overdue Fortnite {words_.title()}: Gone Up to {top['n']}× Longer Than Usual #shorts",
        caption=_caption(
            f"⏳ OVERDUE — Fortnite {words_} the Item Shop usually brings back {every_cap}, as of {ctx.day_label}\n"
            f"Days gone vs. the typical gap between visits, from the Item Shop's own history 👇",
            body, "Which one should come back first?", tags),
        hashtags=tags)
