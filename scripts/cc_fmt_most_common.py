"""
MOST COMMON -- the cosmetics that have been in the Item Shop the most times,
counted down 5 to 1, each one's count painted as tally marks on a dark wall.

    build(ctx, kind="outfit", since=None, count=5)

      kind    "outfit" (default), "pickaxe", "emote", "backpack", "glider"
      since   a year: only the times in the shop that STARTED in or after that
              year count ("THIS YEAR" when it is the video's own year, else
              "SINCE 2025"); None counts everything since the records began
      count   how many to count down: 5 (default) or 6 (fewer would leave a long empty outro)

  0:00  hook    THE MOST COMMON SKINS IN FORTNITE on a strip of black paint
                over a wall covered in tally marks, the #1 and #2 in front of
                it, a painted legend (a group of five = 5 TIMES IN THE ITEM
                SHOP) and the USE CODE: BAD stamp, which flies into the corner
                badge. Frame 0 is the finished picture; the motion is beats.
  0:03  items   one screen each, #5 first. A roller paints the wall clean, the
                cosmetic drops in in front of it (a contact shadow on the floor,
                a soft cast shadow on the wall), then its count is painted on as
                tally marks, groups of five, the fifth a lime slash: the first
                five slowly, then faster and faster, the last few slowly again,
                while the big number rolls up with them mark for mark and lands
                on the exact count: IN THE ITEM SHOP 107 TIMES. Then first time
                in the shop, last seen, and days in the shop.
  outro         the countdown lined up, HOW MANY OF THESE DO YOU OWN?, and USE
                CREATOR CODE BAD, big.

Data and truth (cc_rarity's rules):
  - "in the Item Shop N times"   <- hist.runs(id, until=ctx.day): consecutive days
                                    are ONE time; with `since`, only runs that
                                    started on/after Jan 1 of that year
  - ranking                      <- times, then days in the shop (the same period),
                                    then name; an item whose set-mate with the same
                                    count is already on the list is skipped (a set
                                    sold together counts once). Items tied on times
                                    carry a TIED tag.
  - "first in the shop <date>"   <- hist.first_seen (2018-01-01 on); before that
                                    the records can't vouch for a first day, so
                                    "in the shop since 2017"
  - "last seen"                  <- its latest shop day up to ctx.day
  - "days in the shop"           <- distinct shop days up to ctx.day (in the period)
Every one of the top `count` must have art, or there is no video (None): skipping
one would put the wrong rank on the next.

Render cost: each screen's marks are static SVG paths. The fast middle of a count
is revealed one row at a time by a single stepped clip-path animation (one per
row and paint colour), and only the first five and last three marks are painted
on one by one, so a screen with 107 marks runs about twenty animations.
"""

import math
import random
from datetime import date

import cc_rarity as R
from cc_fmt_rarity import _INTER, _item, history
from cc_formats import Ctx, Video, _caption, _hashtags, num
from cc_looks import KIT_CSS, PREP_JS, _catmull, pad_to, tex
from cc_motion import (ACCENT, BADGE_H, BADGE_X, BADGE_Y, INK, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, W, H, Comp,
                       an, anton_em, code_badge, disclosure, esc, style_anim, trim_for)

FONTS = ("Permanent Marker",)
LIME = ACCENT
PAINT = "#f1eee5"                  # white paint
WALL = "#1d1e20"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
KINDS = {                          # kind: (on screen, in captions, singular)
    "outfit": ("SKINS", "skins", "skin"),
    "pickaxe": ("PICKAXES", "pickaxes", "pickaxe"),
    "emote": ("EMOTES", "emotes", "emote"),
    "backpack": ("BACK BLINGS", "back blings", "back bling"),
    "glider": ("GLIDERS", "gliders", "glider"),
}

HOOK = 3.0
WIPE = .45                         # the roller painting the wall clean between screens
TEXT_W = SAFE_RIGHT - SAFE_LEFT    # 840: beside the apps' button rail
FLOOR = 1190                       # where the wall meets the floor on the item screens
# the item screen, top to bottom
KICK_Y, COUNT_Y, COUNT_SIZE = 394, 428, 190
TALLY = (44, 640, 1036, FLOOR - 12)          # x0, y0, x1, y1 of the painted area
FIG_X, FIG_TOP, FIG_MAXW = 600, 566, 440
TALLY_OPEN = (44, 640, FIG_X - 226, FLOOR - 12)   # the open wall left of the figure, for short counts
NAME_Y, STAT_Y = 1204, 1318
RANK_RIGHT, RANK_Y, RANK_SIZE = 1010, 256, 150
# the hook
HOOK_FLOOR = 1330
STAMP_X, STAMP_Y, STAMP_ROT = SAFE_LEFT + 10, 640, 3

CSS = """
.mc-wall{background:#1c1d1f url("%(wall)s") 0 0/1080px 1920px no-repeat}
.mc-floor{position:absolute;left:0;right:0;bottom:0;background:#141415 url("%(floor)s") 0 0/1080px 800px no-repeat}
.mc-floor::before{content:"";position:absolute;left:0;right:0;top:-26px;height:26px;
  background:linear-gradient(180deg,rgba(0,0,0,0),rgba(0,0,0,.42))}
.mc-floor::after{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:rgba(0,0,0,.55);
  box-shadow:0 1px 0 rgba(255,255,255,.05)}
.mc-light{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 72%% 40%% at 46%% 52%%,rgba(255,244,226,.07) 0%%,rgba(255,244,226,0) 70%%),
    radial-gradient(ellipse 95%% 70%% at 48%% 55%%,rgba(0,0,0,0) 40%%,rgba(0,0,0,.5) 100%%),
    linear-gradient(180deg,rgba(0,0,0,.5) 0%%,rgba(0,0,0,0) 26%%,rgba(0,0,0,0) 80%%,rgba(0,0,0,.35) 100%%)}
.mc-grain{position:absolute;inset:0;pointer-events:none;opacity:.5;mix-blend-mode:overlay;
  background:url("%(grain)s")}
.mc-t{position:absolute;white-space:nowrap;line-height:1}
.mc-lab{font:800 %(lab)spx/1 Inter,sans-serif;letter-spacing:.13em;color:rgba(255,255,255,.66);text-transform:uppercase}
.mc-hand{font-family:'Permanent Marker',cursive;color:%(paint)s}
.mc-sh{text-shadow:0 6px 0 rgba(0,0,0,.32),0 0 26px rgba(0,0,0,.5)}
@keyframes mcwipe{from{clip-path:inset(0 0 100%% 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes mcroller{from{transform:translateY(-60px)}to{transform:translateY(1920px)}}
@keyframes mcpaintv{from{clip-path:inset(-8%% -30%% 108%% -30%%)}to{clip-path:inset(-8%% -30%% -8%% -30%%)}}
@keyframes mcpainth{from{clip-path:inset(-30%% 108%% -30%% -8%%)}to{clip-path:inset(-30%% -8%% -30%% -8%%)}}
@keyframes mcdrop{0%%{transform:translateY(-1500px)}58%%{transform:translateY(0) scale(1.05,.93)}
  76%%{transform:translateY(-16px) scale(.985,1.02)}100%%{transform:none}}
@keyframes mcshadow{0%%,56%%{opacity:0;transform:scale(.35)}62%%{opacity:1;transform:scale(1.12)}100%%{opacity:1;transform:none}}
@keyframes mccast{0%%,50%%{opacity:0}75%%,100%%{opacity:1}}
@keyframes mcbreathe{from{transform:scaleY(1)}to{transform:scaleY(1.012)}}
@keyframes mcshake{0%%,100%%{transform:none}20%%{transform:translate(-7px,4px)}45%%{transform:translate(6px,-4px)}
  70%%{transform:translate(-3px,2px)}}
@keyframes mcslam{0%%{transform:scale(1.8);opacity:0}55%%{transform:scale(.95);opacity:1}100%%{transform:none;opacity:1}}
@keyframes mcrise{from{transform:translateY(26px);opacity:0}to{transform:none;opacity:1}}
@keyframes mcpop{0%%{transform:scale(.2) rotate(var(--r,0deg));opacity:0}60%%{transform:scale(1.08) rotate(var(--r,0deg));opacity:1}
  100%%{transform:rotate(var(--r,0deg));opacity:1}}
@keyframes mcthump{0%%,100%%{transform:none}35%%{transform:scale(1.045)}}
@keyframes mcfade{from{opacity:0}to{opacity:1}}
@keyframes mcout{from{opacity:1}to{opacity:0}}
"""

# Film grain over each screen (static; no per-frame filter work).
GRAIN = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' "
         "stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 .55 0'/></filter>"
         "<rect width='100%25' height='100%25' filter='url(%23n)'/></svg>")


# ------------------------------------------------------------------ data

def _period(since: int | None, day: date) -> dict:
    """How the counting period reads on screen and in captions."""
    if not since:
        return {"start": None, "short": "", "kicker": "IN THE ITEM SHOP", "cap": ""}
    if since >= day.year:
        return {"start": date(day.year, 1, 1), "short": "THIS YEAR", "kicker": "IN THE ITEM SHOP THIS YEAR",
                "cap": f" in {day.year}"}
    return {"start": date(since, 1, 1), "short": f"SINCE {since}", "kicker": f"IN THE ITEM SHOP SINCE {since}",
            "cap": f" since Jan 1, {since}"}


def _ranked(hist: R.History, day: date, kind: str, start: date | None) -> list:
    """Every item of `kind` with its count (times in the shop up to `day`, only
    runs that started on/after `start`), most first; ties by days in the shop."""
    rows = []
    for key, days in hist.days.items():
        raw = hist.items[key]
        if (raw.get("type") or {}).get("value") != kind:
            continue
        upto = [d for d in days if d <= day]
        if not upto:
            continue
        runs = R._runs(upto)
        counted = [r for r in runs if start is None or r[0] >= start]
        if not counted:
            continue
        rows.append({"key": key, "raw": raw, "times": len(counted), "runs": counted,
                     "days": len([d for d in upto if start is None or d >= start]),
                     "all_times": len(runs), "first": hist.first_seen(key), "last": upto[-1]})
    rows.sort(key=lambda r: (-r["times"], -r["days"], (r["raw"].get("name") or "").strip().lower()))
    return rows


def _pick(ctx: Ctx, rows: list, count: int) -> list | None:
    """The top `count`, a set sold together counted once, plus one more row for
    the tie check. None when one of them has no art."""
    out, sets = [], set()
    for r in rows:
        it = _item(r["raw"])
        it["name"] = " ".join(it["name"].split())
        if it["set"] and (it["set"], r["times"]) in sets:
            continue
        if it["set"]:
            sets.add((it["set"], r["times"]))
        out.append(dict(r, item=it))
        if len(out) == count + 1:
            break
    if len(out) < count:
        return None
    for r in out[:count]:
        if not ctx.art(r["item"]):
            return None
    for k, r in enumerate(out[:count]):
        r["tied"] = any(o is not r and o["times"] == r["times"] for o in out[max(0, k - 1):k + 2])
    return out[:count]


def _d(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def _ago(last: date, day: date) -> str:
    n = (day - last).days
    if n <= 0:
        return "TODAY"
    if n == 1:
        return "YESTERDAY"
    return f"{n} DAYS AGO" if n < 100 else _d(last)


# ------------------------------------------------------------------ paint

def _brush(x0, y0, x1, y1, w, rnd, head=1.16, tail=.7, bow=.035, rough=.09, n=9):
    """A paint stroke from (x0, y0) to (x1, y1), about `w` px wide: a closed
    outline with a loaded start, a tapering end and uneven edges.
    Returns (path d, outline points). Every outline runs the same way round, so
    strokes in one path never cut holes in each other."""
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    b = rnd.uniform(-bow, bow) * L
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        off = math.sin(t * math.pi) * b
        cx, cy = x0 + ux * L * t + nx * off, y0 + uy * L * t + ny * off
        k = head + (1 - head) * t / .2 if t < .2 else (1 - (1 - tail) * (t - .62) / .38 if t > .62 else 1.0)
        hl = w / 2 * k * (1 + rnd.uniform(-rough, rough))
        hr = w / 2 * k * (1 + rnd.uniform(-rough, rough))
        left.append((cx + nx * hl, cy + ny * hl))
        right.append((cx - nx * hr, cy - ny * hr))
    hs = w / 2 * head
    ex, ey = x1 + nx * math.sin(math.pi) * b, y1 + ny * math.sin(math.pi) * b
    tip = [(ex + ux * w * .16 + nx * w * rnd.uniform(-.1, .1), ey + uy * w * .16 + ny * w * rnd.uniform(-.1, .1))]
    cap = [(x0 - nx * hs * .72 - ux * hs * .62, y0 - ny * hs * .72 - uy * hs * .62),
           (x0 - ux * hs * 1.02, y0 - uy * hs * 1.02),
           (x0 + nx * hs * .72 - ux * hs * .62, y0 + ny * hs * .72 - uy * hs * .62)]
    pts = left + tip + right[::-1] + cap
    return _catmull(pts, closed=True) + "Z", pts


def _dot(cx, cy, r) -> str:
    """A round drop of paint (same winding as _brush)."""
    return (f"M{cx - r:.1f},{cy:.1f} A{r:.1f},{r:.1f} 0 0 0 {cx + r:.1f},{cy:.1f} "
            f"A{r:.1f},{r:.1f} 0 0 0 {cx - r:.1f},{cy:.1f}Z")


def _bbox(pts, pad=3.0):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad]


def _mark(kind: str, x0, y0, x1, y1, w, rnd, drip_p=.12) -> dict:
    """One tally mark: {'kind', 'd' (paint), 'dry' (bristle gaps, wall colour),
    'box' [x0, y0, x1, y1]}. Bars sometimes drip."""
    d, pts = _brush(x0, y0, x1, y1, w, rnd, head=1.18 if kind == "bar" else 1.1)
    box = _bbox(pts)
    dry = []
    L = math.hypot(x1 - x0, y1 - y0) or 1
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    for _ in range(rnd.choice((0, 1, 1, 2))):       # dry-brush gaps toward the end of the stroke
        a, b = rnd.uniform(.38, .6), rnd.uniform(.9, 1.02)
        o = rnd.uniform(-.24, .24) * w
        sx, sy = x0 + ux * L * a + nx * o, y0 + uy * L * a + ny * o
        ex, ey = x0 + ux * L * b + nx * (o * 1.3), y0 + uy * L * b + ny * (o * 1.3)
        dry.append(_brush(sx, sy, ex, ey, max(1.4, w * rnd.uniform(.06, .11)), rnd, head=.6, tail=1.2,
                          bow=.01, rough=.2, n=5)[0])
    if kind == "bar" and rnd.random() < drip_p:
        dl = w * rnd.uniform(1.4, 3.8)
        bx = x1 + rnd.uniform(-.12, .12) * w
        dd, dpts = _brush(bx, y1 - w * .5, bx + rnd.uniform(-1.2, 1.2), y1 + dl, w * .3, rnd, head=1.5, tail=.9,
                          bow=.01, rough=.05, n=5)
        r = w * rnd.uniform(.2, .27)
        d += " " + dd + " " + _dot(bx, y1 + dl, r)
        box = [min(box[0], bx - r - 2), box[1], max(box[2], bx + r + 2), max(box[3], y1 + dl + r + 2)]
    return {"kind": kind, "d": d, "dry": " ".join(dry), "box": box}


def _group(gx, gy, mh, bars: int, strike: bool, rnd, rot: float = 0.0, drip_p=.12) -> list:
    """A tally group with its top-left at (gx, gy): up to four bars, then the
    slash, `mh` px tall, turned `rot` degrees about its middle."""
    bw, sp, ov = mh * .12, mh * .25, mh * .16
    cxg, cyg = gx + 1.5 * sp, gy + mh / 2
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def P(x, y):
        dx, dy = x - cxg, y - cyg
        return cxg + dx * ca - dy * sa, cyg + dx * sa + dy * ca
    out = []
    for p in range(bars):
        x = gx + p * sp + rnd.uniform(-.03, .03) * mh
        lean = rnd.uniform(-.05, .05) * mh
        top = gy + rnd.uniform(-.05, .04) * mh
        bot = gy + mh * rnd.uniform(.95, 1.03)
        (ax, ay), (bx, by) = P(x - lean / 2, top), P(x + lean / 2, bot)
        out.append(_mark("bar", ax, ay, bx, by, bw * rnd.uniform(.92, 1.08), rnd, drip_p))
    if strike:
        (ax, ay) = P(gx - ov + rnd.uniform(-.03, .03) * mh, gy + mh * rnd.uniform(.74, .84))
        (bx, by) = P(gx + 3 * sp + ov + rnd.uniform(-.03, .04) * mh, gy + mh * rnd.uniform(.16, .26))
        out.append(_mark("strike", ax, ay, bx, by, mh * .135 * rnd.uniform(.94, 1.06), rnd, 0))
    return out


def _fit_grid(groups: int, x0, y0, x1, y1, mh_max=200.0) -> tuple:
    """(mark height, columns, rows) for the largest marks that fit `groups`
    groups of five into the area, in rows."""
    best = None
    for cols in range(1, 30):
        rows = math.ceil(groups / cols)
        mh = min((x1 - x0) / (cols * 1.47), (y1 - y0) / (rows * 1.3), mh_max)
        if best is None or mh > best[0] + .01:
            best = (mh, cols, rows)
    return best


def _count_marks(n: int, area: tuple, seed: int) -> tuple:
    """The n marks of a count, in the order they are painted, laid out in rows
    of groups that fill `area` -- or, when they fit there with marks at least
    100 px tall, the open wall left of the figure, so a short count is never
    hidden behind it. Returns (marks, rows) where each mark has a 'row' index."""
    groups = math.ceil(n / 5)
    if _fit_grid(groups, *TALLY_OPEN, mh_max=170)[0] >= 100:
        area = TALLY_OPEN
    x0, y0, x1, y1 = area
    mh, cols, rows = _fit_grid(groups, x0, y0, x1, y1, mh_max=170)
    cw, ch = mh * 1.47, mh * 1.3
    gw = cols * cw - (cw - mh * 1.07)              # the painted width of a full row
    gx0 = x0 + mh * .16 + (0 if area == TALLY_OPEN else (x1 - x0 - gw) / 2)
    gy0 = y0 + (y1 - y0 - rows * ch + (ch - mh)) / 2
    rnd = random.Random(seed)
    marks = []
    for g in range(groups):
        r, c = divmod(g, cols)
        left = n - g * 5
        gx = gx0 + c * cw + rnd.uniform(-.05, .05) * mh
        gy = gy0 + r * ch + rnd.uniform(-.05, .05) * mh
        ms = _group(gx, gy, mh, min(4, left), left >= 5, rnd, rot=rnd.uniform(-2.2, 2.2))
        for m in ms:
            m["row"] = r
        marks += ms
    return marks, rows


def _schedule(n: int) -> list:
    """When each mark is painted, from the start of the count: [(start, dur, alone)].
    The first five and the last three are painted one by one (alone=True), slow
    enough to see; the rest appear with their row, fastest in the middle."""
    first = min(n, 5)
    last = 3 if n > 8 else n - first
    out, t = [], 0.0
    for i in range(first):
        strike = i == 4
        out.append((t + (.04 if strike else 0), .2 if strike else .13, True))
        t += .28 if strike else .17
    mid = n - first - last
    if mid > 0:
        dur = max(.45, min(2.2, .022 * mid))
        t0 = t + .05
        for j in range(mid):
            p = (j + 1) / mid
            out.append((t0 + dur * math.acos(1 - 2 * p) / math.pi, 0.0, False))
        t = t0 + dur + .14
    gaps = (.2, .25, .32)
    for k in range(last):
        i = n - last + k
        strike = i % 5 == 4
        out.append((t, .2 if strike else .13, True))
        t += gaps[k] + (.06 if strike else 0)
    return out


def _svg(box, body: str) -> str:
    x0, y0, x1, y1 = box
    return (f'<svg width="{x1 - x0:.0f}" height="{y1 - y0:.0f}" viewBox="{x0:.1f} {y0:.1f} {x1 - x0:.1f} '
            f'{y1 - y0:.1f}" style="display:block;overflow:visible">{body}</svg>')


def _paths(marks: list, color: str) -> str:
    paint = " ".join(m["d"] for m in marks)
    dry = " ".join(m["dry"] for m in marks if m["dry"])
    return (f'<path d="{paint}" fill="{color}" fill-opacity=".95"/>'
            + (f'<path d="{dry}" fill="{WALL}" fill-opacity=".62"/>' if dry else ""))


def _static_marks(marks: list) -> str:
    """Marks already on the wall (no animation)."""
    bars = [m for m in marks if m["kind"] == "bar"]
    strikes = [m for m in marks if m["kind"] == "strike"]
    return (f'<svg class="abs" data-safe="ignore" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'style="left:0;top:0;overflow:visible">{_paths(bars, PAINT)}{_paths(strikes, LIME)}</svg>')


def _one(m: dict, start: float, dur: float) -> str:
    """One mark painted on by itself: top to bottom for a bar, left to right for the slash."""
    x0, y0, x1, y1 = m["box"]
    kf = "mcpaintv" if m["kind"] == "bar" else "mcpainth"
    return (f'<div class="abs" data-safe="ignore" style="left:{x0:.1f}px;top:{y0:.1f}px;'
            f'{style_anim(an(kf, start, dur, "cubic-bezier(.3,.1,.5,1)"))}">'
            f'{_svg(m["box"], _paths([m], PAINT if m["kind"] == "bar" else LIME))}</div>')


def _row_layer(comp: Comp, marks: list, times: list, color: str) -> str:
    """Batch marks of one row and colour, revealed left to right one mark at a
    time (a stepped clip-path: one animation for the whole row)."""
    order = sorted(zip(marks, times), key=lambda mt: mt[1])
    box = [min(m["box"][0] for m in marks) - 4, min(m["box"][1] for m in marks) - 4,
           max(m["box"][2] for m in marks) + 4, max(m["box"][3] for m in marks) + 4]
    bw = box[2] - box[0]
    lefts = sorted(m["box"][0] for m in marks)
    t0, t1 = order[0][1] - .001, order[-1][1]
    dur = max(t1 - t0, .01)
    name = comp.uid("mcrow")
    frames = [f"0%{{clip-path:inset(-60px {bw + 60:.1f}px -60px -60px)}}"]
    for m, t in order:
        right = m["box"][2]
        nxt = [x for x in lefts if x > right - 1]
        edge = min(right + 6, (right + nxt[0]) / 2) if nxt else box[2] + 60
        frames.append(f"{(t - t0) / dur * 100:.4f}%{{clip-path:inset(-60px {box[2] - edge:.1f}px -60px -60px)}}")
    comp.css(f"@keyframes {name}{{{''.join(frames)}}}")
    return (f'<div class="abs" data-safe="ignore" style="left:{box[0]:.1f}px;top:{box[1]:.1f}px;'
            f'{style_anim(an(name, t0, dur, "step-end"))}">'
            f'{_svg(box, _paths([m for m, _ in order], color))}</div>')


def _tally(comp: Comp, n: int, area: tuple, t0: float, seed: int) -> tuple:
    """The n marks painted from t0, and the counter that follows them.
    Returns (marks html, counter keyframes name, [count change times], landing time)."""
    marks, rows = _count_marks(n, area, seed)
    sched = _schedule(n)
    html, when = [], []
    batches = {}
    for m, (s, dur, alone) in zip(marks, sched):
        if alone:
            html.append(_one(m, t0 + s, dur))
            when.append(t0 + s + dur * .8)
        else:
            batches.setdefault((m["row"], m["kind"]), []).append((m, t0 + s))
            when.append(t0 + s)
    for (_, kind), mt in sorted(batches.items()):
        html.append(_row_layer(comp, [m for m, _ in mt], [t for _, t in mt], PAINT if kind == "bar" else LIME))
    return "".join(html), when, max(when) + .06


def _counter(comp: Comp, when: list, t_start: float) -> str:
    """--n keyframes that step up by one at each time in `when`."""
    name = comp.uid("mccnt")
    t0 = t_start
    t1 = max(when)
    dur = max(t1 - t0, .01)
    frames = ["0%{--n:0}"] + [f"{(t - t0) / dur * 100:.4f}%{{--n:{k}}}" for k, t in enumerate(sorted(when), 1)]
    comp.css(f"@keyframes {name}{{{''.join(frames)}}}")
    return style_anim(an(name, t0, dur, "step-end"))


# ------------------------------------------------------------------ pieces

def _a(name: str, t: float, dur: float, ease: str = "cubic-bezier(.2,.8,.2,1)") -> str:
    return an(name, t, dur, ease)


def _text_w(text: str, size: float, spacing: float = 0.0) -> float:
    """Width of an Inter 800 upper-case line (plus letter-spacing in em)."""
    return sum(_INTER.get(ch, .8) + spacing for ch in text.upper()) * size


def _fit_name(name: str, width: float = TEXT_W - 6) -> tuple:
    """(size, lines, first-line words): one line down to 58 px, else two
    lines of up to 60 px (they fit between the floor line and the stats),
    broken where the lines come out most even."""
    ws = name.upper().split()
    one = (width) / max(anton_em(name) - .18, .1)
    if one >= 58 or len(ws) == 1:
        return min(106, one), 1, len(ws)
    best = None
    for j in range(1, len(ws)):
        a, b = " ".join(ws[:j]), " ".join(ws[j:])
        s = min(60, width / max(anton_em(a) - .18, anton_em(b) - .18))
        if best is None or s > best[0]:
            best = (s, 2, j)
    return best


def _words(text: str, x: float, y: float, size: float, start: float, color: str = "#fff", stagger: float = .07,
           brk: int = 0, anim: str = "mcslam") -> str:
    """Anton words landing one after another; a line break before word `brk`."""
    parts = []
    for i, w in enumerate(text.split()):
        br = "<br>" if brk and i == brk else ""
        parts.append(f'{br}<span style="display:inline-block;margin-right:.18em;'
                     f'{style_anim(_a(anim, start + i * stagger, .45))}">{esc(w)}</span>')
    return (f'<div class="abs d mc-sh" style="left:{x:.0f}px;top:{y:.0f}px;font-size:{size:.0f}px;'
            f'line-height:.92;color:{color};white-space:nowrap">{"".join(parts)}</div>')


def _floor(y: float) -> str:
    return f'<div class="mc-floor" style="top:{y:.0f}px"></div>'


_ARTS: dict = {}          # data URI -> key, for the build in progress


def _art_key(uri: str) -> str:
    """Each picture is embedded once (a skin is on the hook, its own screen and
    the outro, each time with its shadow): the images take their src from one
    map, set by _art_js before PREP_JS trims them."""
    if uri not in _ARTS:
        _ARTS[uri] = f"a{len(_ARTS)}"
    return _ARTS[uri]


def _art_js() -> str:
    import json
    table = json.dumps({k: u for u, k in _ARTS.items()})
    return ("<script>(() => { const A = " + table + "; for (const i of document.querySelectorAll('img[data-mcsrc]')) "
            "{ i.src = A[i.dataset.mcsrc]; } })();</script>")


def _figure(ctx: Ctx, it: dict, cx: float, feet: float, h: float, maxw: float, t: float,
            cast: bool = True, drop: bool = True, idle: float = 2.8) -> str:
    """The cosmetic standing on the floor at (cx, feet), `h` px tall: it drops in
    at t and lands with weight, a contact shadow on the floor, and a soft
    shadow on the wall behind it (baked once, cc_looks.PREP_JS data-bake)."""
    uri = ctx.art(it)
    tr = ' data-trim="figure"' if trim_for(it) == "figure" else " data-trim"
    size = f"height:{h:.0f}px;max-width:{maxw:.0f}px;display:block"
    if uri:
        src = _art_key(uri)
        art = f'<img{tr} data-name="{esc(it["name"])}" data-mcsrc="{src}" style="{size}">'
        shadow = (f'<div class="abs" data-safe="ignore" style="left:{h * .03:.0f}px;bottom:{h * .012:.0f}px;'
                  f'transform:translateX(-50%);clip-path:inset(-300px -300px 0 -300px);opacity:.46;'
                  f'{style_anim(_a("mccast", t, .9, "linear")) if drop else ""}">'
                  f'<img{tr} data-bake="brightness(0) blur(18px)" data-pad="64" data-mcsrc="{src}" style="{size}"></div>'
                  ) if cast else ""
    else:
        art = (f'<div class="d" style="height:{h:.0f}px;width:{min(h * .5, maxw):.0f}px;display:flex;align-items:center;'
               f'justify-content:center;font-size:{h * .07:.0f}px;color:#777;border:4px dashed #555;border-radius:24px;'
               f'text-align:center">{esc(it["name"])}</div>')
        shadow = ""
    sw = min(maxw, h * .52)
    drop_a = style_anim(_a("mcdrop", t, .62, "cubic-bezier(.5,0,.4,1)")) if drop else ""
    shad_a = style_anim(_a("mcshadow", t, .62, "linear")) if drop else ""
    breathe = style_anim(an("mcbreathe", t + .7, idle, "ease-in-out", "infinite", "alternate")) if idle else ""
    return (f'<div class="abs" style="left:{cx:.0f}px;top:{feet:.0f}px;width:0;height:0">'
            f'<div class="abs" style="left:{-sw / 2:.0f}px;top:{-h * .035:.0f}px;width:{sw:.0f}px;height:{h * .07:.0f}px;'
            f'border-radius:50%;background:radial-gradient(closest-side,rgba(0,0,0,.78),rgba(0,0,0,.35) 60%,'
            f'rgba(0,0,0,0));{shad_a}"></div>'
            f'<div class="abs" style="left:0;top:0;{drop_a}"><div class="abs" style="left:0;top:0;'
            f'transform-origin:0 0;{breathe}">{shadow}'
            f'<div class="abs" style="left:0;bottom:0;transform:translateX(-50%)">{art}</div></div></div></div>')


def _patch(x0, y0, x1, y1, seed: int, color: str = "#0b0b0c", rot: float = 0.0) -> str:
    """A patch of black roller paint with ragged edges (text sits on it)."""
    rnd = random.Random(seed)
    pts = []
    n_x, n_y = max(6, int((x1 - x0) / 60)), max(3, int((y1 - y0) / 50))

    def edge(ax, ay, bx, by, k, jit):
        for i in range(k):
            t = i / k
            pts.append((ax + (bx - ax) * t + rnd.uniform(-jit, jit) * (ay != by),
                        ay + (by - ay) * t + rnd.uniform(-jit, jit) * (ax != bx)))
    edge(x0, y0, x1, y0, n_x, 5)
    edge(x1, y0, x1, y1, n_y, 9)
    edge(x1, y1, x0, y1, n_x, 5)
    edge(x0, y1, x0, y0, n_y, 9)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]
    lanes = "".join(
        f'<rect x="{x0 + 10:.0f}" y="{y0 + (y1 - y0) * f:.0f}" width="{x1 - x0 - 20:.0f}" height="{(y1 - y0) * .1:.0f}" '
        f'fill="#fff" opacity=".018" transform="rotate({rot} {cx:.0f} {cy:.0f})"/>' for f in (.18, .47, .73))
    return (f'<svg class="abs" data-safe="ignore" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'style="left:0;top:0;overflow:visible"><path d="{_catmull(pts, closed=True)}Z" fill="{color}" '
            f'fill-opacity=".97"/>{lanes}</svg>')


def _roller(t: float) -> str:
    """The edge of the fresh coat sweeping down the frame during a wipe."""
    return (f'<div class="abs" data-safe="ignore" style="left:-20px;right:-20px;top:0;height:60px;z-index:30;'
            f'background:linear-gradient(180deg,rgba(0,0,0,0) 0,rgba(0,0,0,.55) 55%,rgba(255,255,255,.07) 88%,'
            f'rgba(0,0,0,0) 100%);{style_anim(_a("mcroller", t, WIPE, "cubic-bezier(.55,0,.45,1)"))}"></div>')


def _screen(comp: Comp, start: float, end: float, inner: str, z: int, wipe: bool = True):
    """A full screen on its own coat of paint: wiped on from the top at `start`."""
    body = f'<div class="full mc-wall"></div>{inner}<div class="mc-grain"></div>'
    if wipe:
        body = (f'<div class="full" style="{style_anim(_a("mcwipe", start, WIPE, "cubic-bezier(.55,0,.45,1)"))}">'
                f'{body}</div>{_roller(start)}')
    comp.scene(start, end, body, fade_in=.01, fade_out=.01, z=z)


# ------------------------------------------------------------------ the code stamp (the hook)

def _stamp(comp: Comp, dock_start: float, dock_end: float) -> str:
    """USE CODE: BAD, big, on the hook: the corner badge (cc_motion.code_badge)
    at 1.4x, which shrinks and flies into the corner, where the badge takes
    over as it lands (the same hand-off as cc_formats._code_stamp, without the
    glow)."""
    k = BADGE_H / 120
    dock = comp.uid("mcdock")
    comp.css(f"@keyframes {dock}{{0%{{transform:rotate({STAMP_ROT}deg);opacity:1}}"
             f"99.9%{{transform:translate({BADGE_X - STAMP_X}px,{BADGE_Y - STAMP_Y}px) scale({k:.3f});opacity:1}}"
             f"100%{{transform:translate({BADGE_X - STAMP_X}px,{BADGE_Y - STAMP_Y}px) scale({k:.3f});opacity:0}}}}")
    comp.css(f".codebadge,.codetag{{animation:fadein .01s linear {dock_end - .01:.3f}s both paused !important}}")
    beat = style_anim(an("mcthump", .95, .42, "ease-out", fill="none"))
    return (f'<div class="abs" style="left:{STAMP_X}px;top:{STAMP_Y}px;transform-origin:0 0;z-index:20;'
            f'{style_anim(an(dock, dock_start, dock_end - dock_start, "cubic-bezier(.6,0,.4,1)"))}">'
            f'<div style="{beat}"><div data-safe="key" data-name="code" style="display:flex;align-items:center;'
            f'gap:17px;background:{LIME};color:{INK};border-radius:22px;padding:11px 28px 8px 25px;'
            f'box-shadow:0 11px 0 rgba(0,0,0,.4),0 22px 30px rgba(0,0,0,.35)">'
            f'<div style="font-size:32px;font-weight:900;line-height:1.02;letter-spacing:.12em">USE<br>CODE:</div>'
            f'<div class="d" style="font-size:112px;line-height:.9;letter-spacing:.02em">BAD</div></div>'
            f'<div style="display:inline-block;margin:5.6px 0 0 0;padding:0 8px;font-size:32px;font-weight:700;'
            f'line-height:1.3;color:rgba(255,255,255,.95);background:rgba(10,10,11,.82);border-radius:8px">'
            f'#EpicPartner</div></div></div>')


# ------------------------------------------------------------------ hook

def _hook_wall(seed: int) -> tuple:
    """A wall covered in tally groups, rows running off both edges. Returns
    (marks, [groups whose slash is painted during the hook])."""
    rnd = random.Random(seed)
    marks, late = [], []
    y, row = 236.0, 0
    while y < HOOK_FLOOR - 70:
        mh = rnd.uniform(96, 124)
        x = -rnd.uniform(20, 90)
        while x < W + 20:
            bars = 4 if rnd.random() > .08 else rnd.randint(1, 3)
            strike = bars == 4
            gm = _group(x, y + rnd.uniform(-10, 10), mh * rnd.uniform(.9, 1.06), bars, strike, rnd,
                        rot=rnd.uniform(-4, 4), drip_p=.1)
            # three groups right of middle, low on the wall, get their slash during the hook
            if strike and len(late) < 3 and row in (5, 6) and 560 < x < 900 and rnd.random() < .7:
                late.append(gm[-1])
                gm = gm[:-1]
            marks += gm
            x += mh * rnd.uniform(1.25, 1.55)
        y += rnd.uniform(118, 140)
        row += 1
    return marks, late


def _hook(comp: Comp, ctx: Ctx, rows: list, words_kind: str, period: dict) -> None:
    end = HOOK + WIPE + .05
    dock_start, dock_end = HOOK - .95, HOOK - .45
    marks, late = _hook_wall(ctx.seed)
    inner = _static_marks(marks)
    for i, m in enumerate(late):
        inner += _one(m, .45 + i * .32, .24)
        comp.cue(.45 + i * .32, "pen")
    inner += '<div class="mc-light"></div>'
    inner += _floor(HOOK_FLOOR)
    # the title on a strip of black paint
    l1 = "THE MOST COMMON"
    l2 = f"{words_kind} {period['short'] or 'IN FORTNITE'}"
    size = min(132, 930 / max(anton_em(l1) - .18, anton_em(l2) - .18))
    ty = 402
    inner += _patch(22, 270, 1058, ty + size * 1.84 + 26, ctx.seed + 3, rot=-1.2)
    inner += (f'<div class="full" style="transform-origin:50% {ty + size:.0f}px;'
              f'{style_anim(an("mcthump", .2, .42, "ease-out", fill="none"))}">'
              f'<div class="abs d" style="left:0;width:{W}px;top:{ty:.0f}px;text-align:center;font-size:{size:.0f}px;'
              f'line-height:.92;color:#fff">{esc(l1)}<br>{esc(l2)}</div></div>')
    # the date line, for the cover; it steps aside as the stamp flies to the corner
    kick = (f"AS OF {ctx.day_label.upper()}" if not period["start"]
            else f"{_d(period['start'])} – {_d(ctx.day)}")
    inner += (f'<div class="abs" style="left:0;width:{W}px;top:296px;text-align:center;{style_anim(_a("mcout", dock_start, .3))}">'
              f'<div class="mc-t mc-sh" style="position:static;display:inline-block;font:800 30px/1 Inter,sans-serif;'
              f'letter-spacing:.17em;color:{LIME}">{esc(kick)}</div></div>')
    # the legend: a painted group of five = 5 TIMES IN THE ITEM SHOP
    lx, ly = 500, 646
    inner += _patch(lx - 22, ly - 16, 1036, ly + 118, ctx.seed + 5, rot=1.0)
    leg = _group(lx, ly + 8, 86, 4, True, random.Random(ctx.seed + 9), rot=-3, drip_p=0)
    inner += _static_marks(leg)
    inner += (f'<div class="abs mc-hand" style="left:{lx + 142}px;top:{ly - 6}px;font-size:46px;line-height:1.08;'
              f'white-space:nowrap;transform:rotate(-2deg)">= 5 TIMES<br><span style="font-size:34px">IN THE ITEM SHOP'
              f'</span></div>')
    # the two at the top of the list
    a, b = rows[0]["item"], rows[1]["item"]
    inner += _figure(ctx, b, 670, HOOK_FLOOR + 6, 560, 380, 0, drop=False)
    inner += _figure(ctx, a, 292, HOOK_FLOOR + 6, 580, 380, 0, drop=False)
    inner += (f'<div class="abs" style="left:{SAFE_LEFT}px;width:{TEXT_W}px;top:{HOOK_FLOOR + 24}px;'
              f'text-align:center">'
              f'<div class="mc-t mc-sh" style="position:static;display:inline-block;font:800 30px/1 Inter,sans-serif;'
              f'letter-spacing:.12em;color:#fff">TOP {len(rows)} · RANKED BY TIMES IN THE ITEM SHOP</div></div>')
    inner += _stamp(comp, dock_start, dock_end)
    _screen(comp, 0, end, inner, z=5, wipe=False)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.95, "pop"); comp.cue(dock_start, "whoosh")


# ------------------------------------------------------------------ one item

LAB = 23                           # the stats' labels (Inter 800, px)


def _stats_row(stats: list, y: float, t: float) -> str:
    """FIRST SEEN / LAST SEEN / DAYS IN SHOP: small labels over Anton values,
    one size for all three, each column as wide as it needs, all within TEXT_W."""
    gap = 40
    lab_w = [_text_w(lab, LAB, .13) for lab, _ in stats]
    val_em = [max(anton_em(v) - .18, .1) for _, v in stats]
    vs = 62.0
    while vs > 30:
        widths = [max(lw, ve * vs) for lw, ve in zip(lab_w, val_em)]
        if sum(widths) + gap * (len(stats) - 1) <= TEXT_W - 8:
            break
        vs -= 1
    out, x = [], SAFE_LEFT
    for j, ((lab, val), w) in enumerate(zip(stats, widths)):
        out.append(f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;{style_anim(_a("mcrise", t + j * .14, .45))}">'
                   f'<div class="mc-t mc-lab" style="position:static">{esc(lab)}</div>'
                   f'<div class="d mc-sh" style="margin-top:9px;font-size:{vs:.0f}px;line-height:1;color:#fff;'
                   f'white-space:nowrap">{esc(val)}</div></div>')
        x += w + gap
    return "".join(out)


def _item_screen(comp: Comp, ctx: Ctx, r: dict, rank: int, n: int, t0: float, R_LEN: float, period: dict,
                 z: int) -> tuple:
    """One countdown screen. Returns the cues' anchor times."""
    it = r["item"]
    times = r["times"]
    inner = ""
    t_fig = t0 + .06
    t_count = t0 + 1.0
    marks_html, when, t_land = _tally(comp, times, TALLY, t_count, ctx.seed + 17 * rank)
    inner += marks_html
    inner += '<div class="mc-light"></div>'
    inner += _floor(FLOOR)
    # name and the figure
    size, lines, brk = _fit_name(it["name"])
    name_y = NAME_Y if lines == 1 else NAME_Y - 6
    feet = FLOOR + 6
    fig_h = feet - FIG_TOP
    inner += _figure(ctx, it, FIG_X, feet, fig_h, FIG_MAXW, t_fig)
    inner += _words(it["name"], SAFE_LEFT + 2, name_y, size, t0 + .62, brk=brk if lines == 2 else 0)
    # rank, top right
    rank_s = f"#{rank}"
    inner += (f'<div class="abs d mc-sh" style="right:{W - RANK_RIGHT}px;top:{RANK_Y}px;font-size:{RANK_SIZE}px;'
              f'line-height:.9;color:#fff;--r:-4deg;{style_anim(_a("mcpop", t0 + .2, .5, "cubic-bezier(.34,1.56,.64,1)"))}">'
              f'{rank_s}</div>')
    if r.get("tied"):
        inner += (f'<div class="abs" style="right:{W - RANK_RIGHT + 4}px;top:{RANK_Y + RANK_SIZE * .92:.0f}px;'
                  f'{style_anim(_a("mcrise", t_land + .5, .4))}"><div class="mc-t" style="position:static;'
                  f'font:800 26px/1 Inter,sans-serif;letter-spacing:.14em;color:#111;background:#fff;padding:7px 12px 6px;'
                  f'border-radius:6px">TIED</div></div>')
    # the count: IN THE ITEM SHOP / 107 TIMES
    inner += (f'<div class="abs mc-t mc-sh" style="left:{SAFE_LEFT + 2}px;top:{KICK_Y}px;font:800 30px/1 Inter,sans-serif;'
              f'letter-spacing:.14em;color:rgba(255,255,255,.9);{style_anim(_a("mcrise", t0 + .55, .45))}">'
              f'{esc(period["kicker"])}</div>')
    num_w = (anton_em(str(times)) - .18) * COUNT_SIZE
    cnt = _counter(comp, when, t_count)
    fin = f"{times:,}"
    inner += (f'<div class="abs d mc-sh" style="left:{SAFE_LEFT + 2}px;top:{COUNT_Y}px;font-size:{COUNT_SIZE}px;'
              f'line-height:.9;color:{LIME}">'
              f'<div class="abs" style="left:0;top:0;{style_anim(an("mcfade", t_count - .05, .05, "linear"))}">'
              f'<div style="{style_anim(an("mcout", t_land, .01, "linear"))}">'
              f'<span class="count" style="white-space:nowrap;{cnt}"></span></div></div>'
              f'<span style="white-space:nowrap;{style_anim(an("mcfade", t_land, .01, "linear"))}">{fin}</span></div>')
    inner += (f'<div class="abs d mc-sh" style="left:{SAFE_LEFT + 2 + num_w + COUNT_SIZE * .09:.0f}px;'
              f'top:{COUNT_Y + COUNT_SIZE * .9 - 88 * .9 - 6:.0f}px;font-size:88px;line-height:.9;color:#fff;'
              f'{style_anim(_a("mcslam", t_land, .42))}">{"TIME" if times == 1 else "TIMES"}</div>')
    # first / last / days
    first = ("FIRST SEEN", _d(r["first"])) if r["first"] else ("IN SHOP SINCE", "2017")
    stats = [first, ("LAST SEEN", _ago(r["last"], ctx.day))]
    if period["start"]:
        stats.append(("ALL TIME", f"{r['all_times']:,} TIMES"))
    else:
        stats.append(("DAYS IN SHOP", f"{r['days']:,}"))
    inner += _stats_row(stats, STAT_Y, t_land + .35)
    if rank == 1:
        flag = "TIED FOR #1!" if r.get("tied") else "MOST COMMON!"
        fs = 54
        fw = (anton_em(flag) - .18 + .84) * fs
        inner += (f'<div class="abs" style="left:{SAFE_RIGHT_TOP - 18 - fw:.0f}px;top:{KICK_Y + 78}px;--r:-6deg;'
                  f'{style_anim(_a("mcpop", t_land + .8, .5, "cubic-bezier(.34,1.56,.64,1)"))}">'
                  f'<div class="d" style="background:#fff;color:#111;font-size:{fs}px;padding:.16em .42em .1em;'
                  f'border-radius:8px;box-shadow:0 10px 0 rgba(0,0,0,.35)">{esc(flag)}</div></div>')
        comp.cue(t_land + .8, "reveal")
    inner = f'<div class="full" style="{style_anim(_a("mcshake", t_land, .3, "linear"))}">{inner}</div>'
    _screen(comp, t0, t0 + R_LEN + WIPE + .05, inner, z=z)
    comp.cue(t0, "whoosh"); comp.cue(t0 + .22, "stamp"); comp.cue(t_fig + .36, "slam")
    for k in range(4):
        comp.cue(t_count + k * .17, "pen")
    t = t_count + .9
    while t < t_land - .55:
        comp.cue(t, "pen")
        t += .3
    for tw in sorted(when)[-3:]:
        comp.cue(tw, "tick")
    comp.cue(t_land, "slam")
    return t_land


# ------------------------------------------------------------------ outro

def _outro(comp: Comp, ctx: Ctx, rows: list, start: float, end: float, ask: tuple) -> None:
    inner = f'<div class="full" style="opacity:.2">{_static_marks(_hook_wall(ctx.seed + 1)[0])}</div>'
    inner += '<div class="mc-light"></div>' + _floor(FLOOR)
    inner += (f'<div class="abs" style="left:0;width:{W}px;top:392px;text-align:center;'
              f'{style_anim(_a("mcrise", start + .3, .45))}"><div class="mc-t mc-sh" style="position:static;'
              f'display:inline-block;font:800 42px/1 Inter,sans-serif;letter-spacing:.26em;color:#fff">'
              f'USE CREATOR CODE</div></div>')
    inner += (f'<div class="abs d" style="left:0;width:{W}px;top:444px;text-align:center;font-size:270px;'
              f'line-height:.9;color:{LIME};text-shadow:0 14px 0 rgba(0,0,0,.4);'
              f'{style_anim(_a("mcslam", start + .45, .55))}"><span data-safe="key" data-name="code">BAD</span></div>')
    # the countdown lined up: #1 in the middle and in front
    spots = [(480, 540, 360, 4), (296, 470, 280, 3), (664, 470, 280, 3), (148, 420, 176, 2), (812, 420, 176, 2)]
    for k, (r, (x, h, mw, zz)) in enumerate(zip(rows, spots)):
        tk = start + .7 + (len(rows) - 1 - k) * .16
        inner += f'<div class="abs" style="left:0;top:0;z-index:{zz}">' + _figure(
            ctx, r["item"], x, FLOOR + 6, h, mw, tk, cast=True) + '</div>'
        comp.cue(tk + .36, "stamp")
    l1, l2 = ask
    asz = min(88, 820 / max(anton_em(l1) - .18, anton_em(l2) - .18))
    inner += (f'<div class="abs d mc-sh" style="left:{SAFE_LEFT}px;width:{TEXT_W}px;top:{FLOOR + 30}px;'
              f'text-align:center;font-size:{asz:.0f}px;line-height:.95;color:#fff;z-index:9;'
              f'{style_anim(_a("mcslam", start + 1.9, .45))}">{esc(l1)}<br><span style="color:{LIME}">{esc(l2)}</span></div>')
    _screen(comp, start, end, inner, z=60)
    comp.cue(start, "whoosh"); comp.cue(start + .45, "slam"); comp.cue(start + 1.9, "pop")


# ------------------------------------------------------------------ build

def build(ctx: Ctx, kind: str = "outfit", since: int | None = None, count: int = 5, **_):
    if kind not in KINDS:
        return None
    count = max(5, min(6, int(count)))
    _ARTS.clear()
    hist = history()
    period = _period(int(since) if since else None, ctx.day)
    rows = _pick(ctx, _ranked(hist, ctx.day, kind, period["start"]), count)
    if not rows or rows[-1]["times"] < 2:
        return None
    word, cap, _one_word = KINDS[kind]
    n = len(rows)
    r_len = max(9.4, min(11.0, (62.0 - 7.5 - HOOK) / n))
    content_end = HOOK + n * r_len
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(CSS % {"wall": tex("most-common-wall.jpg"), "floor": tex("most-common-floor.jpg"), "grain": GRAIN,
                    "paint": PAINT, "lab": LAB})
    _hook(comp, ctx, rows, word, period)
    for k, r in enumerate(reversed(rows), 1):
        t0 = HOOK + (k - 1) * r_len
        _item_screen(comp, ctx, r, n - k + 1, n, t0, r_len, period, z=10 + k)
    _outro(comp, ctx, rows, content_end, comp.duration, ("HOW MANY OF THESE", "DO YOU OWN?"))
    comp.add(_art_js())
    comp.add(PREP_JS)
    comp.add(code_badge(0))
    comp.add(disclosure())
    comp.cues.sort()

    top = rows[0]
    per = period["cap"]
    title_kind = cap.title() if kind != "backpack" else "Back Blings"
    body = "\n".join(
        f"{num(k)} {r['item']['name']} · in the Item Shop {r['times']:,} times{per}"
        f" · last seen {r['last']:%b %-d, %Y}" for k, r in enumerate(rows, 1))
    ties = any(r.get("tied") for r in rows)
    how = ("Ranked by separate times in the Item Shop (consecutive days count once"
           + ("; ties go to more days in the shop" if ties else "") + ") 👇")
    when = f"as of {ctx.day_label}" if not period["start"] else f"{period['start']:%b %-d, %Y} – {ctx.day:%b %-d, %Y}"
    head = (f"🔁 THE MOST COMMON {word} {period['short'] or 'IN FORTNITE'} — the {cap} that have been in the "
            f"Item Shop the most times, {when}\n{how}")
    tags = _hashtags("mostcommonskins" if kind == "outfit" else f"fortnite{cap.replace(' ', '')}",
                     "fortniteskins", top["item"]["name"])
    span = f" {period['short'].title()}" if period["start"] else ""
    return Video(
        f"most_common_{kind}{'_' + str(since) if since else ''}", comp,
        title=f"The Most Common Fortnite {title_kind}{span} — Item Shop History, {ctx.day_label}",
        yt_title=f"The Most Common Fortnite {title_kind}{span}: #1 Was in the Item Shop {top['times']:,} Times #shorts",
        caption=_caption(head, body, "How many of these do you own?", tags),
        hashtags=tags)
