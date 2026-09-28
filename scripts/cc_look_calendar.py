"""
CALENDAR -- On This Day, as a chunky page-a-day tear-off desk calendar.

A walnut desk calendar stands on a desk against a plaster wall, shot straight
on: a thick pad of cream sheets glued under a walnut crown, a low walnut base
with a memo block on its right, and a lime sticky note on that block (the code).

    0:00  hook      the calendar's title sheet: ON THIS DAY in the red band,
                    "...in the Fortnite Item Shop", SEP / 28 and the span of
                    years; the two lead cosmetics stand on the desk in front of
                    it as die-cut standees. They're slid off the desk and the
                    title sheet is torn off.
    0:03  years     one sheet per year (6.5 s): the sheet for that year's date --
                    SEPTEMBER, the huge 28, the weekday that date fell on and the
                    year -- with the cosmetic printed as the day's picture, its
                    rarity and type and its name typed under it, and a red NEW
                    THAT DAY rubber stamp when it was its first day in the shop
                    ("in the Item Shop that day" otherwise). Up on the crown, a
                    strip of the years: a red slider marks this one, the years
                    already torn off are crossed out in pen. Each sheet is torn
                    off at the end: it lifts from the bottom, rips from the glued
                    edge and is tossed away to the left, revealing the next.
    0:55  outro     the NOTES sheet: "Which year had the best shop?" in pen, the
                    lead picks (and one more) stand on the desk again.

Facts on screen are the classic format's: the date, each year, the name, the
rarity and type, NEW THAT DAY only when the plan says so, the span, the
birthday sheet, the outro question. The weekday is computed from the date.

The lime sticky note (USE CODE: / BAD / #EpicPartner) sits on the memo block
from the first frame to the last, above everything, never moving more than the
stand's small jolt when a sheet is ripped off; the sheets fly away from it, to
the left. Everything a viewer reads sits inside the apps' safe box (cc_safe):
x 60-1020 above y 740, x 60-900 below, y 230-1420, and from y 285 on frame 0.
The wall, the desk and the stand's wood run to the edges.
"""

import math
import random
from datetime import date

from cc_looks import KIT_CSS, LIME, PREP_JS, pad_to, rough_line, stroke_svg, tex
from cc_motion import Comp, esc

HOOK = 3.0
R = 6.5
TEAR = 1.0                  # lift .42 s, rip, tossed away by 1.0 s
T_RIP = .44                 # the rip, into the tear
FONTS = ("Oswald", "Old Standard TT", "Special Elite", "Caveat")

# The calendar's print
PAPER = "#f2e9d6"
INK = "#231d18"
RED = "#b7302a"             # the band, weekends, the rubber stamps, the slider
MUTED = "#6e6357"
CREAM = "#f8efdc"

# ---- where things sit (frame px) -------------------------------------------
CROWN = (66, 280, 910, 342)          # x0, y0, x1, y1: the walnut crown
STRIP = (92, 293, 884, 331)          # the year strip set into it
BIND = (84, 338, 892, 368)           # the glued binding under it
STUB_Y = 380                         # the ragged remnants of torn sheets end here
SX, SY = 86, 362                     # a sheet's top-left (its top is under the binding)
SW, SH = 804, 938                    # a sheet: x 86-890, y 362-1300
BAND = (388, 466)                    # the printed red band (frame y)
BACK = (70, 300, 906, 1300)          # the backboard behind the pad
BASE = (56, 1296, 924, 1414)         # the low walnut base
BLOCK = (576, 1074, 916, 1414)       # the memo block on its right
NOTE_X, NOTE_Y, NOTE_BOX = 594, 1098, 300     # the code note's (unturned) box
NOTE_D, NOTE_ROT = 280, -3.0                  # the note itself, and its turn
# the sheet's two columns (frame x): the picture on the left, the date on the right
LX0, LX1 = 102, 578
RX0, RX1 = 598, 878
RMID = (RX0 + RX1) / 2
FIG_Y0, FIG_Y1 = 478, 1118           # the day's picture stands on y 1118
KICK_Y = 1132                        # rarity + type
NAME_Y = 1166                        # the name, typed (up to two lines, to y ~1290)
STANDEE_FEET = 1404                  # the standees' feet, on the desk

CSS = """
.cal-num{font-family:'Oswald',sans-serif;font-weight:700;line-height:1;white-space:nowrap}
.cal-sc{font-family:'Oswald',sans-serif;font-weight:500;line-height:1;white-space:nowrap}
.cal-old{font-family:'Old Standard TT',serif;line-height:1.05}
.cal-type{font-family:'Special Elite',monospace;line-height:1.04}
.cal-hand{font-family:'Caveat',cursive;font-weight:700;line-height:.95}
.cal-wood{background:url('%(walnut)s') 0 0/1100px 420px}
.cal-sheet{position:absolute;left:%(sx)dpx;top:%(sy)dpx;width:%(sw)dpx;height:%(sh)dpx;transform-origin:50%% 0;
  transform-style:preserve-3d}
.cal-face{position:absolute;inset:0;overflow:hidden;backface-visibility:hidden;-webkit-backface-visibility:hidden;
  background:%(paper_c)s url('%(paper)s') 0 0/820px 980px}
.cal-back{transform:rotateX(180deg);background:#e9dfca url('%(paper)s') -30px -40px/820px 980px}
.cal-back::after{content:"";position:absolute;left:0;right:0;top:26px;height:78px;background:rgba(183,48,42,.07)}
.cal-shine{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,rgba(60,40,20,.20) 0%%,rgba(60,40,20,0) 22%%,rgba(255,250,240,0) 55%%,
  rgba(255,250,240,.28) 100%%)}
.cal-grain{position:absolute;left:-256px;top:-256px;width:1592px;height:2432px;pointer-events:none;opacity:.045;
  background:url('%(grain)s') 0 0/256px 256px repeat}
@keyframes calgr{0%%{transform:translate(0,0)}25%%{transform:translate(-131px,77px)}50%%{transform:translate(53px,-173px)}
  75%%{transform:translate(-201px,-29px)}}
@keyframes caltear{
  0%%{transform:translate(0,0) rotateX(0deg) rotateY(0deg) rotateZ(0deg);
    animation-timing-function:cubic-bezier(.42,0,.5,1)}
  44%%{transform:translate(0,0) rotateX(36deg) rotateY(-10deg) rotateZ(1.4deg);
    animation-timing-function:cubic-bezier(.2,0,.4,1)}
  52%%{transform:translate(-16px,10px) rotateX(42deg) rotateY(-7deg) rotateZ(-4deg);
    animation-timing-function:cubic-bezier(.3,.1,.6,1)}
  74%%{transform:translate(-520px,-30px) rotateX(58deg) rotateY(16deg) rotateZ(-17deg);
    animation-timing-function:cubic-bezier(.4,0,.9,.7)}
  100%%{transform:translate(-1260px,430px) rotateX(96deg) rotateY(34deg) rotateZ(-38deg)}}
@keyframes calshine{0%%{opacity:0}44%%{opacity:1}74%%{opacity:.8}100%%{opacity:.5}}
@keyframes callift{0%%{opacity:0}44%%{opacity:1}56%%{opacity:.75}80%%{opacity:0}100%%{opacity:0}}
@keyframes calout{0%%{transform:translate(0,0) rotate(0deg)}
  100%%{transform:translate(-760px,18px) rotate(-7deg)}}
@keyframes calin{0%%{transform:translate(-760px,18px) rotate(-7deg)}
  78%%{transform:translate(8px,0) rotate(.6deg)}100%%{transform:translate(0,0) rotate(0deg)}}
@keyframes calstamp{0%%{opacity:0;transform:scale(1.14) rotate(var(--r))}
  45%%{opacity:.9;transform:scale(.985) rotate(var(--r))}100%%{opacity:.9;transform:scale(1) rotate(var(--r))}}
@keyframes calwrite{from{clip-path:inset(-20%% 100%% -30%% 0)}to{clip-path:inset(-20%% -2%% -30%% 0)}}
"""

# PREP_JS bakes each picture's die-cut edge and shadow into the image, with
# margins that keep it where it was drawn but leave its layout box two
# paddings smaller -- a picture centred (or stood on the floor) by its flex box
# would move by a padding. This gives the box its size back. Runs after PREP_JS.
FIX_JS = """<script>(() => {
  const prev = window.__ready;
  window.__ready = (async () => {
    if (prev) { await prev; }
    for (const img of document.querySelectorAll('img[data-calfix]')) {
      try {
        const st = img.style, ml = parseFloat(st.marginLeft) || 0, mt = parseFloat(st.marginTop) || 0;
        if (!ml && !mt) continue;
        st.marginRight = ((parseFloat(st.marginRight) || 0) - 2 * ml) + 'px';
        st.marginBottom = ((parseFloat(st.marginBottom) || 0) - 2 * mt) + 'px';
      } catch (e) {}
    }
  })();
})();</script>"""

PRINT_BAKE = ("url(#calcut) drop-shadow(0 2px 1.5px rgba(40,25,10,.30)) "
              "drop-shadow(5px 10px 9px rgba(40,25,10,.20))")
STANDEE_BAKE = ("url(#calboard) drop-shadow(0 3px 2px rgba(30,18,8,.35)) "
                "drop-shadow(26px 16px 16px rgba(30,18,8,.30))")


# ------------------------------------------------------------------ helpers

def _a(name: str, t: float, dur: float, ease: str = "cubic-bezier(.2,.8,.2,1)", fill: str = "both") -> str:
    return f"animation:{name} {dur:.3f}s {ease} {t:.3f}s 1 normal {fill};"


def _weekday(day: date, year: int) -> str:
    try:
        return date(year, day.month, day.day).strftime("%A").upper()
    except ValueError:                       # Feb 29 in a common year
        return ""


def _weekend(day: date, year: int) -> bool:
    try:
        return date(year, day.month, day.day).weekday() >= 5
    except ValueError:
        return False


def _cutout(fid: str, radius: float, color: str) -> str:
    """A die-cut edge for a transparent PNG (as cc_looks.diecut_filter, with a
    paper-coloured edge)."""
    return (f'<svg width="0" height="0" style="position:absolute"><defs>'
            f'<filter id="{fid}" x="-15%" y="-10%" width="130%" height="120%" color-interpolation-filters="sRGB">'
            f'<feMorphology in="SourceAlpha" operator="dilate" radius="{radius}" result="d"/>'
            f'<feGaussianBlur in="d" stdDeviation="{radius / 3.5:.1f}" result="b"/>'
            f'<feComponentTransfer in="b" result="m"><feFuncA type="linear" slope="14" intercept="-6"/>'
            f'</feComponentTransfer>'
            f'<feFlood flood-color="{color}"/><feComposite in2="m" operator="in" result="w"/>'
            f'<feMerge><feMergeNode in="w"/><feMergeNode in="SourceGraphic"/></feMerge>'
            f'</filter></defs></svg>')


def _trim(it: dict) -> str:
    t = it.get("type")
    t = t.get("value") if isinstance(t, dict) else t
    return "figure" if str(t or "").lower() == "outfit" else ""


def _kind(it: dict) -> str:
    return " ".join(x for x in (it.get("rarity_label") or "", it.get("type") or "") if x).strip()


def _picture(art: str, it: dict, box_w: float, box_h: float, bake: str, pad: int = 60) -> str:
    """The cosmetic, stood on the bottom of a box_w x box_h box and centred in
    it; a quiet printed placeholder when there's no art."""
    if art:
        trim = _trim(it)
        tr = f' data-trim="{trim}"' if trim else " data-trim"
        return (f'<div style="position:absolute;inset:0;display:flex;justify-content:center;align-items:flex-end">'
                f'<img{tr} data-calfix data-bake="{bake}" data-pad="{pad}" data-name="{esc(it["name"])}" '
                f'src="{art}" style="display:block;height:{box_h:.0f}px;max-width:{box_w:.0f}px;object-fit:contain;'
                f'filter:{bake}"></div>')
    # a printed figure silhouette over the name, in the paper's own ink
    w = min(box_w, box_h * .5)
    return (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:flex-end;'
            f'align-items:center">'
            f'<svg viewBox="0 0 100 200" width="{w * .62:.0f}" height="{w * 1.24:.0f}" style="opacity:.22">'
            f'<circle cx="50" cy="26" r="20" fill="{INK}"/>'
            f'<path d="M22 60 Q50 44 78 60 L86 128 L70 128 L66 196 L54 196 L50 132 L46 196 L34 196 L30 128 '
            f'L14 128 Z" fill="{INK}"/></svg>'
            f'<div class="cal-type" style="margin-top:14px;font-size:30px;color:{MUTED};text-align:center;'
            f'max-width:{box_w:.0f}px">{esc(it["name"])}</div></div>')


def _ragged(w: float, depth: float, seed: int, step: float = 11.0) -> list:
    """Points of a torn edge across a width w: x left to right, y 0..depth."""
    rnd = random.Random(seed)
    pts, x = [], 0.0
    while x < w:
        pts.append((x, rnd.uniform(0, depth) * (.55 if rnd.random() < .6 else 1)))
        x += rnd.uniform(step * .5, step * 1.4)
    pts.append((w, rnd.uniform(0, depth)))
    return pts


def _track(comp: Comp, stops: list, prop: str = "transform",
           ease: str = "cubic-bezier(.3,.7,.35,1)") -> str:
    """One keyframes track over the whole video: stops [(t, value)], each held
    until the next (give two stops a moment apart for a quick move)."""
    d = comp.duration
    name = comp.uid("calk")
    frames = []
    for t, v in sorted(stops, key=lambda s: s[0]):
        pct = max(0.0, min(100.0, t / d * 100))
        frames.append(f"{pct:.4f}%{{{prop}:{v};animation-timing-function:{ease}}}")
    comp.css(f"@keyframes {name}{{{''.join(frames)}}}")
    return f"animation:{name} {d:.3f}s linear 0s 1 normal both;"


# ------------------------------------------------------------------ the stand

def _room() -> str:
    """The wall and desk (one baked picture), the calendar's shadow on the wall
    and on the desk. Decoration: it runs to the edges."""
    x0, y0, x1, y1 = BACK
    return (f'<div class="full" data-safe="ignore" style="background:#cbb99d url({tex("calendar-room.jpg")}) '
            f'0 0/1080px 1920px no-repeat">'
            # the stand's shadow on the wall (light from the upper left)
            f'<div class="abs" style="left:{x0 + 26}px;top:{CROWN[1] + 22}px;width:{x1 - x0 + 10}px;'
            f'height:{BASE[1] - CROWN[1]}px;border-radius:14px;background:rgba(62,40,20,.34);filter:blur(22px)"></div>'
            # contact shadow on the desk, and a softer one thrown to the right
            f'<div class="abs" style="left:{BASE[0] - 10}px;top:{BASE[3] - 16}px;width:{BASE[2] - BASE[0] + 30}px;'
            f'height:34px;border-radius:50%;background:rgba(30,16,6,.55);filter:blur(9px)"></div>'
            f'<div class="abs" style="left:{BASE[0] + 60}px;top:{BASE[3] - 4}px;width:{BASE[2] - BASE[0] + 70}px;'
            f'height:70px;border-radius:50%;background:rgba(30,16,6,.30);filter:blur(22px)"></div>'
            f'</div>')


def _stand_back() -> str:
    """The backboard behind the pad and the pad's thickness down its right side."""
    x0, y0, x1, y1 = BACK
    return (f'<div class="abs cal-wood" style="left:{x0}px;top:{y0}px;width:{x1 - x0}px;height:{y1 - y0}px;'
            f'background-position:-40px -120px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.25);'
            f'filter:brightness(.72)"></div>'
            # the side of the pad: hundreds of sheet edges, in shade
            f'<div class="abs" style="left:{SX + SW - 2}px;top:{BIND[3] - 4}px;width:18px;'
            f'height:{BLOCK[1] - BIND[3] + 4}px;background:url({tex("calendar-edges.jpg")}) 0 0/72px 1100px;'
            f'filter:brightness(.8);clip-path:polygon(0 0,100% 6px,100% 100%,0 100%)"></div>'
            f'<div class="abs" style="left:{SX + SW - 2}px;top:{BIND[3]}px;width:18px;'
            f'height:{BLOCK[1] - BIND[3]}px;background:linear-gradient(90deg,rgba(40,25,10,.35),rgba(40,25,10,0) 40%,'
            f'rgba(40,25,10,.25))"></div>')


def _base() -> str:
    """The low walnut base the pad stands on (the sheets fly over it)."""
    x0, y0, x1, y1 = BASE
    return (f'<div class="abs cal-wood" data-safe="ignore" style="left:{x0}px;top:{y0}px;width:{x1 - x0}px;'
            f'height:{y1 - y0}px;border-radius:6px 6px 4px 4px;background-position:-200px -60px;'
            f'box-shadow:inset 0 10px 0 rgba(255,225,190,.10),inset 0 11px 0 rgba(0,0,0,.25),'
            f'inset 0 -4px 6px rgba(0,0,0,.35),inset 0 0 0 1px rgba(0,0,0,.3)"></div>')


def _block() -> str:
    """The memo block on the base's right: a solid walnut cube the note is
    stuck to. It stands in front of the pad's lower right corner."""
    x0, y0, x1, y1 = BLOCK
    return (f'<div class="abs" data-safe="ignore" style="left:{x0 - 6}px;top:{y0 - 30}px;width:{x1 - x0 + 12}px;'
            f'height:40px;background:linear-gradient(180deg,rgba(40,25,10,0),rgba(40,25,10,.28));'
            f'border-radius:8px 8px 0 0"></div>'
            f'<div class="abs cal-wood" data-safe="ignore" style="left:{x0}px;top:{y0}px;width:{x1 - x0}px;'
            f'height:{y1 - y0}px;border-radius:8px 8px 4px 4px;background-position:-520px -150px;'
            f'box-shadow:inset 0 12px 0 rgba(255,225,190,.12),inset 0 13px 0 rgba(0,0,0,.28),'
            f'inset 10px 0 18px rgba(255,220,180,.05),inset -8px 0 14px rgba(0,0,0,.3),'
            f'inset 0 -4px 6px rgba(0,0,0,.35),-8px 10px 18px rgba(30,16,6,.35)"></div>')


def _binding() -> str:
    """The glued binding under the crown and the ragged stubs of the sheets
    already torn off. In front of the sheets."""
    x0, y0, x1, y1 = BIND
    stubs = []
    for k, (dy, tone) in enumerate(((10, "#e6dcc6"), (7, "#efe6d2"), (3, "#f4ecda"))):
        pts = _ragged(x1 - x0, 7, 50 + k, 13)
        poly = ",".join(f"{x:.0f}px {py + dy + 4:.1f}px" for x, py in pts)
        stubs.append(f'<div class="abs" style="left:{x0}px;top:{y1 - 4}px;width:{x1 - x0}px;height:24px;'
                     f'background:{tone};clip-path:polygon(0 0,{x1 - x0}px 0,{poly.split(",", 0)[0] if False else ""}'
                     f'{",".join(reversed([p for p in poly.split(",")]))},0 0)"></div>')
    return (f'<div class="abs" style="left:{x0}px;top:{y1 + 2}px;width:{x1 - x0}px;height:30px;'
            f'background:linear-gradient(180deg,rgba(40,25,10,.30),rgba(40,25,10,0))"></div>'
            + "".join(stubs)
            + f'<div class="abs" style="left:{x0}px;top:{y0}px;width:{x1 - x0}px;height:{y1 - y0}px;'
              f'background:repeating-linear-gradient(90deg,rgba(255,255,255,.05) 0 2px,rgba(0,0,0,.06) 2px 3px,'
              f'rgba(0,0,0,0) 3px 5px),linear-gradient(180deg,#7a1f1b,#8e2621 30%,#6f1a17 80%,#4c100e);'
              f'box-shadow:0 3px 4px rgba(30,10,5,.35)"></div>')


def _crown(years: list) -> str:
    """The walnut crown with the strip of years set into it."""
    x0, y0, x1, y1 = CROWN
    sx0, sy0, sx1, sy1 = STRIP
    step = (sx1 - sx0) / len(years)
    size = min(28, (step - 18) / 2.0)
    labels = "".join(
        f'<div class="abs cal-sc" style="left:{sx0 + i * step:.1f}px;top:{sy0}px;width:{step:.1f}px;'
        f'height:{sy1 - sy0}px;display:flex;align-items:center;justify-content:center;font-size:{size:.1f}px;'
        f'letter-spacing:.04em;color:#3d3027">{y}</div>' for i, y in enumerate(years))
    ticks = "".join(
        f'<div class="abs" style="left:{sx0 + i * step - .5:.1f}px;top:{sy0 + 9}px;width:1px;height:{sy1 - sy0 - 18}px;'
        f'background:rgba(60,45,30,.25)"></div>' for i in range(1, len(years)))
    return (f'<div class="abs cal-wood" style="left:{x0}px;top:{y0}px;width:{x1 - x0}px;height:{y1 - y0}px;'
            f'border-radius:10px 10px 6px 6px;background-position:-300px -20px;'
            f'box-shadow:inset 0 3px 0 rgba(255,225,190,.16),inset 0 -5px 7px rgba(0,0,0,.35),'
            f'inset 0 0 0 1px rgba(0,0,0,.3),0 6px 10px rgba(30,16,6,.35)"></div>'
            f'<div class="abs" style="left:{sx0}px;top:{sy0}px;width:{sx1 - sx0}px;height:{sy1 - sy0}px;'
            f'background:#efe5cf url({tex("calendar-paper.jpg")}) 0 -200px/820px 980px;border-radius:3px;'
            f'box-shadow:inset 0 2px 3px rgba(40,25,10,.45),inset 0 -1px 0 rgba(255,255,255,.25)"></div>'
            + ticks + labels)


def _slider(comp: Comp, years: list, stops: list) -> str:
    """The red slider on the year strip; stops [(t, index or None)]."""
    sx0, sy0, sx1, sy1 = STRIP
    step = (sx1 - sx0) / len(years)
    w = step - 6
    track = []
    for t, i in stops:
        if i is None:
            track.append((t, f"translate({-w - 60:.1f}px,0)"))
        else:
            track.append((t, f"translate({i * step + 3:.1f}px,0)"))
    return (f'<div class="abs" style="left:{sx0}px;top:{sy0 - 5}px;width:{w:.1f}px;height:{sy1 - sy0 + 10}px;'
            f'{_track(comp, track, ease="cubic-bezier(.35,1.35,.45,1)")}">'
            f'<div style="position:absolute;inset:0;border:5px solid {RED};border-radius:7px;'
            f'box-shadow:0 2px 3px rgba(30,10,5,.35),inset 0 1px 0 rgba(255,255,255,.25)"></div></div>')


def _cross(years: list, i: int, t: float) -> str:
    """Year i crossed out in red pen on the strip."""
    sx0, sy0, sx1, sy1 = STRIP
    step = (sx1 - sx0) / len(years)
    cx = sx0 + (i + .5) * step
    a = rough_line(cx - 24, sy0 + 7, cx + 22, sy1 - 6, seed=i * 7 + 1, bow=.06)
    b = rough_line(cx + 23, sy0 + 6, cx - 21, sy1 - 7, seed=i * 7 + 2, bow=.06)
    return stroke_svg([a, b], RED, 4.5, t, .13, opacity=.9, gap=.04)


def _note() -> str:
    """USE CODE: BAD on a lime sticky note, handwritten in black felt tip. The
    outer box is the note's unturned square, so the check measures it."""
    d = NOTE_D
    return (f'<div class="abs" data-safe="key" data-name="code" style="left:{NOTE_X}px;top:{NOTE_Y}px;'
            f'width:{NOTE_BOX}px;height:{NOTE_BOX}px">'
            f'<div style="position:absolute;left:{(NOTE_BOX - d) / 2:.0f}px;top:{(NOTE_BOX - d) / 2:.0f}px;'
            f'width:{d}px;height:{d}px;transform:rotate({NOTE_ROT}deg)">'
            # its shadow: tight under the glued top, deeper where the bottom curls off the wood
            f'<div style="position:absolute;left:6px;right:2px;top:30px;bottom:-6px;'
            f'background:rgba(20,10,4,.42);filter:blur(7px);transform:skewX(-2deg)"></div>'
            f'<div style="position:absolute;inset:0;background:{LIME};'
            f'box-shadow:0 1px 1px rgba(20,10,4,.35)">'
            f'<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.035) 0,'
            f'rgba(0,0,0,0) 22%,rgba(255,255,255,0) 70%,rgba(255,255,255,.16) 100%)"></div>'
            f'<div style="position:absolute;left:0;right:0;top:0;height:52px;background:rgba(120,130,0,.05)"></div>'
            f'<div class="cal-hand" style="position:absolute;left:0;right:0;top:20px;text-align:center;'
            f'font-size:50px;color:#111;letter-spacing:.01em">USE CODE:</div>'
            f'<div class="cal-hand" style="position:absolute;left:0;right:0;top:66px;text-align:center;'
            f'font-size:150px;line-height:1;color:#111;transform:rotate(-2deg)">BAD</div>'
            f'<svg class="abs" width="{d}" height="{d}" style="left:0;top:0;overflow:visible">'
            f'<path d="M58 206 C110 198 170 199 226 203" fill="none" stroke="#111" stroke-width="5" '
            f'stroke-linecap="round"/></svg>'
            f'<div class="cal-hand" style="position:absolute;left:0;right:0;top:220px;text-align:center;'
            f'font-size:34px;font-weight:600;color:#1a1a12">#EpicPartner</div>'
            f'</div></div></div>')


# ------------------------------------------------------------------ the sheets

def _L(x: float, y: float) -> tuple:
    """Frame coordinates -> the sheet's own."""
    return x - SX, y - SY


def _band(text: str, size: float = 50, spacing: float = .34) -> str:
    y0, y1 = BAND
    top = y0 - SY
    return (f'<div class="abs" style="left:0;top:{top}px;width:{SW}px;height:{y1 - y0}px;'
            f'background:rgba(183,48,42,.93)">'
            f'<div class="abs" style="left:14px;right:14px;top:7px;height:1.5px;background:rgba(248,239,220,.55)"></div>'
            f'<div class="abs" style="left:14px;right:14px;bottom:7px;height:1.5px;background:rgba(248,239,220,.55)"></div>'
            f'<div class="cal-old" style="position:absolute;left:0;right:0;top:0;bottom:0;display:flex;'
            f'align-items:center;justify-content:center;font-weight:700;font-size:{size}px;'
            f'letter-spacing:{spacing}em;padding-left:{spacing}em;color:{CREAM}">{esc(text)}</div></div>'
            # the perforation just under the binding
            f'<div class="abs" style="left:10px;right:10px;top:{STUB_Y - SY + 3}px;height:2px;'
            f'background:repeating-linear-gradient(90deg,rgba(80,60,40,.28) 0 3px,rgba(0,0,0,0) 3px 7px)"></div>')


def _date_block(day: date, year: int, top: float = 470) -> str:
    """The right-hand column: the huge day, the weekday that date fell on, the year."""
    col = RED if _weekend(day, year) else INK
    lx = RX0 - SX
    w = RX1 - RX0
    num = str(day.day)
    size = min(272, (w - 4) / (.52 * len(num)))
    wd = _weekday(day, year)
    wsize = min(38, (w - 10) / (max(len(wd), 1) * .62))
    return (f'<div class="abs cal-num" style="left:{lx}px;top:{top - SY:.0f}px;width:{w}px;text-align:center;'
            f'font-size:{size:.0f}px;color:{col};opacity:.95">{num}</div>'
            f'<div class="abs cal-sc" style="left:{lx}px;top:{top - SY + size * .98 + 6:.0f}px;width:{w}px;'
            f'text-align:center;font-size:{wsize:.0f}px;letter-spacing:.22em;padding-left:.22em;color:{col};'
            f'opacity:.92">{wd}</div>'
            f'<div class="abs" style="left:{lx + 40}px;top:{top - SY + size * .98 + wsize + 26:.0f}px;'
            f'width:{w - 80}px;height:2px;background:rgba(35,29,24,.55)"></div>'
            f'<div class="abs cal-num" style="left:{lx}px;top:{top - SY + size * .98 + wsize + 34:.0f}px;'
            f'width:{w}px;text-align:center;font-size:136px;color:{INK};opacity:.95">{year}</div>')


def _stamp(lines: list, w: float, h: float, rot: float, t: float) -> str:
    """A red rubber-stamp impression: double border, uneven ink. lines: [(text, size, weight, spacing)]."""
    mask = tex("calendar-ink.png")
    rows = "".join(
        f'<div style="font-family:Oswald,sans-serif;font-weight:{wt};font-size:{sz}px;line-height:1.02;'
        f'letter-spacing:{sp}em;padding-left:{sp}em;white-space:nowrap">{esc(tx)}</div>'
        for tx, sz, wt, sp in lines)
    return (f'<div style="width:{w}px;height:{h}px;--r:{rot}deg;{_a("calstamp", t, .22, "cubic-bezier(.3,.9,.4,1)")}">'
            f'<div style="position:absolute;inset:0;border:6px solid {RED};border-radius:14px;'
            f'color:{RED};display:flex;flex-direction:column;align-items:center;justify-content:center;'
            f'-webkit-mask:url({mask}) center/cover;mask:url({mask}) center/cover">'
            f'<div style="position:absolute;inset:6px;border:2px solid {RED};border-radius:8px"></div>'
            f'{rows}</div></div>')


def _page_year(ctx, rd: dict, it: dict, debut: bool, t0: float) -> tuple:
    """One year's sheet (inner html in the sheet's coordinates) and its sounds."""
    day = ctx.day
    y = rd["year"]
    fx0, fy0 = _L(LX0, FIG_Y0)
    html = [_band(day.strftime("%B").upper()),
            # the day's picture, stood on a soft printed shadow
            f'<div class="abs" style="left:{fx0 + 60}px;top:{FIG_Y1 - SY - 16}px;width:{LX1 - LX0 - 120}px;height:30px;'
            f'border-radius:50%;background:radial-gradient(closest-side,rgba(60,40,20,.28),rgba(60,40,20,0))"></div>',
            f'<div class="abs" style="left:{fx0}px;top:{fy0}px;width:{LX1 - LX0}px;height:{FIG_Y1 - FIG_Y0}px">'
            + _picture(ctx.art(it), it, LX1 - LX0 - 8, FIG_Y1 - FIG_Y0, PRINT_BAKE, 40) + '</div>',
            # a hairline between the columns, as printed calendars have
            f'<div class="abs" style="left:{RX0 - SX - 12}px;top:{FIG_Y0 - SY + 10}px;width:1.5px;'
            f'height:{BLOCK[1] - FIG_Y0 - 40}px;background:rgba(35,29,24,.18)"></div>',
            _date_block(day, y)]
    kx, ky = _L(LX0 + 4, KICK_Y)
    kind = _kind(it)
    html.append(f'<div class="abs cal-sc" data-fit="{LX1 - LX0 - 10}" style="left:{kx}px;top:{ky}px;'
                f'font-size:25px;letter-spacing:.2em;color:{MUTED}">{esc(kind.upper())}</div>')
    nx, ny = _L(LX0 + 2, NAME_Y)
    html.append(f'<div class="abs cal-type" data-fit="{LX1 - LX0 - 6}" data-lines="2" style="left:{nx}px;top:{ny}px;'
                f'width:{LX1 - LX0 - 6}px;font-size:60px;line-height:1.02;color:{INK}">{esc(it["name"])}</div>')
    sounds = []
    if debut:
        sx, sy = _L(RX0 + 8, 948)
        html.append(f'<div class="abs" style="left:{sx}px;top:{sy}px">'
                    + _stamp([("NEW", 76, 700, .08), ("THAT DAY", 30, 500, .26)], 258, 132, -7, t0 + .75)
                    + '</div>')
        sounds.append((t0 + .75, "stamp"))
    else:
        lx, ly = _L(RX0, 962)
        html.append(f'<div class="abs cal-old" style="left:{lx}px;top:{ly}px;width:{RX1 - RX0}px;text-align:center;'
                    f'font-style:italic;font-size:36px;line-height:1.1;color:{MUTED}">in the Item Shop<br>that day</div>')
    return "".join(html), sounds


def _page_birthday(ctx, bday: dict, t0: float) -> tuple:
    day = ctx.day
    by = bday["year"]
    x, y = _L(LX0 + 4, 506)
    when = date(by, day.month, day.day).strftime("%B %-d, %Y") if _weekday(day, by) else f"{by}"
    html = [_band(day.strftime("%B").upper()), _date_block(day, by),
            f'<div class="abs" style="left:{RX0 - SX - 12}px;top:{FIG_Y0 - SY + 10}px;width:1.5px;'
            f'height:{BLOCK[1] - FIG_Y0 - 40}px;background:rgba(35,29,24,.18)"></div>',
            f'<div class="abs cal-num" data-fit="{LX1 - LX0 - 10}" data-lines="3" style="left:{x}px;top:{y}px;'
            f'width:{LX1 - LX0 - 10}px;font-size:96px;line-height:1.02;white-space:normal;color:{INK}">'
            f'FORTNITE BATTLE ROYALE COMES OUT</div>',
            f'<div class="abs cal-old" style="left:{x}px;top:{y + 330}px;width:{LX1 - LX0 - 10}px;'
            f'font-style:italic;font-size:44px;color:{INK}">{esc(when)}</div>',
            f'<div class="abs cal-type" data-fit="{LX1 - LX0 - 10}" style="left:{x}px;top:{y + 396}px;'
            f'font-size:34px;color:{MUTED};white-space:nowrap">PC · PlayStation 4 · Xbox One</div>']
    sx, sy = _L(LX0 + 10, 1010)
    html.append(f'<div class="abs" style="left:{sx}px;top:{sy}px">'
                + _stamp([("HAPPY BIRTHDAY", 58, 700, .04), (f"{bday['age']} YEARS TODAY", 34, 500, .22)],
                         440, 150, -6, t0 + .75) + '</div>')
    return "".join(html), [(t0 + .75, "stamp")]


def _page_cover(ctx, span: str, bday) -> str:
    """The calendar's title sheet (frame 0)."""
    day = ctx.day
    lx, ly = _L(LX0 + 4, 496)
    html = [_band("ON THIS DAY", 64, .16)]
    if bday:
        html.append(f'<div class="abs cal-hand" data-fit="{LX1 - LX0 - 10}" data-lines="2" style="left:{lx}px;'
                    f'top:{ly - 8}px;width:{LX1 - LX0 - 10}px;font-size:92px;line-height:.92;color:{RED};'
                    f'transform:rotate(-3deg)">Fortnite turns {bday["age"]}!</div>')
    else:
        html.append(f'<div class="abs cal-old" data-fit="{LX1 - LX0 - 10}" data-lines="2" style="left:{lx}px;'
                    f'top:{ly}px;width:{LX1 - LX0 - 10}px;font-style:italic;font-size:50px;line-height:1.08;'
                    f'color:{INK}">…in the Fortnite Item Shop</div>')
    rx, ry = _L(RX0, 486)
    w = RX1 - RX0
    html.append(f'<div class="abs cal-old" style="left:{rx}px;top:{ry}px;width:{w}px;text-align:center;'
                f'font-weight:700;font-size:58px;letter-spacing:.3em;padding-left:.3em;color:{INK}">'
                f'{esc(day.strftime("%b").upper())}</div>')
    num = str(day.day)
    size = min(272, (w - 4) / (.52 * len(num)))
    html.append(f'<div class="abs cal-num" style="left:{rx}px;top:{ry + 58}px;width:{w}px;text-align:center;'
                f'font-size:{size:.0f}px;color:{RED};opacity:.95">{num}</div>')
    html.append(f'<div class="abs" style="left:{rx + 40}px;top:{ry + 58 + size * .98 + 8:.0f}px;width:{w - 80}px;'
                f'height:2px;background:rgba(35,29,24,.55)"></div>')
    html.append(f'<div class="abs cal-num" style="left:{rx}px;top:{ry + 58 + size * .98 + 18:.0f}px;width:{w}px;'
                f'text-align:center;font-weight:500;font-size:56px;color:{INK}">{esc(span)}</div>')
    sub = (f"Battle Royale came out on this day in {bday['year']}" if bday
           else "one outfit from this date, every year")
    html.append(f'<div class="abs cal-type" data-fit="{w}" data-lines="3" style="left:{rx}px;'
                f'top:{ry + 58 + size * .98 + 96:.0f}px;width:{w}px;text-align:center;font-size:31px;'
                f'line-height:1.12;color:{MUTED}">{esc(sub)}</div>')
    return "".join(html)


def _page_outro(t: float) -> tuple:
    """The NOTES sheet at the back of the pad, and the question in pen."""
    rules = "".join(
        f'<div class="abs" style="left:18px;right:18px;top:{yy - SY}px;height:2px;background:rgba(90,120,150,.22)">'
        f'</div>' for yy in range(560, 1290, 62))
    x, y = _L(LX0 + 8, 492)
    html = (_band("NOTES", 52, .5) + rules
            + f'<div class="abs" style="left:{110 - SX}px;top:{BAND[1] - SY}px;width:2px;height:{SH}px;'
              f'background:rgba(183,48,42,.25)"></div>'
            + f'<div class="abs cal-hand" style="left:{x}px;top:{y}px;width:{RX1 - LX0 - 20}px;font-size:96px;'
              f'line-height:1.02;color:{INK};transform:rotate(-2deg);'
              f'{_a("calwrite", t + .15, 1.1, "steps(22,end)")}">Which year had<br>the best shop?</div>')
    return html, [(t + .15, "pen"), (t + .65, "pen")]


def _sheet(inner: str, seed: int, t_tear) -> str:
    """A sheet: its printed face, its blank back, and (t_tear) its tear: it lifts
    from the bottom, rips at the binding and is tossed away to the left."""
    pts = _ragged(SW, 9, seed)
    poly = ",".join(f"{x:.0f}px {y + 2:.1f}px" for x, y in pts) + f",{SW}px {SH}px,0 {SH}px"
    anim = _a("caltear", t_tear, TEAR, "linear") if t_tear is not None else ""
    shine = (f'<div class="cal-shine" style="{_a("calshine", t_tear, TEAR, "linear")}"></div>'
             if t_tear is not None else "")
    lift = (f'<div class="abs" style="left:{SX}px;top:{SY}px;width:{SW}px;height:{SH}px;'
            f'background:linear-gradient(180deg,rgba(40,25,10,.42) 0%,rgba(40,25,10,.18) 35%,rgba(40,25,10,0) 70%);'
            f'{_a("callift", t_tear, TEAR, "linear")}"></div>' if t_tear is not None else "")
    return (lift
            + f'<div class="cal-sheet" style="{anim}">'
              f'<div class="cal-face" style="clip-path:polygon({poly})">{inner}{shine}</div>'
              f'<div class="cal-face cal-back" style="clip-path:polygon({poly})"></div></div>')


def _standee(ctx, it: dict, cx: float, h: float, w: float, anim: str) -> str:
    """A cosmetic as a die-cut cardboard standee on the desk, in front of the
    calendar (its shadow falls on the calendar)."""
    return (f'<div class="abs" style="left:{cx - w / 2:.0f}px;top:{STANDEE_FEET - h:.0f}px;width:{w:.0f}px;'
            f'height:{h:.0f}px;{anim}">'
            f'<div class="abs" style="left:{w * .18:.0f}px;top:{h - 14:.0f}px;width:{w * .64:.0f}px;height:26px;'
            f'border-radius:50%;background:rgba(25,12,4,.5);filter:blur(6px)"></div>'
            + _picture(ctx.art(it), it, w, h, STANDEE_BAKE, 70) + '</div>')


# ------------------------------------------------------------------ the video

def on_this_day(ctx, rounds: list, bday: dict | None, lead: list, third) -> Comp:
    day = ctx.day
    years = ([bday["year"]] if bday else []) + [rd["year"] for rd, _, _ in rounds]
    n = len(years)
    r = max(R, (62.0 - 7.5 - HOOK) / n)
    content_end = HOOK + n * r
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(CSS % dict(walnut=tex("calendar-walnut.jpg"), paper=tex("calendar-paper.jpg"),
                        grain=tex("calendar-grain.png"), sx=SX, sy=SY, sw=SW, sh=SH, paper_c=PAPER))
    span = f"{years[0]}–{years[-1]}"
    starts = [HOOK + k * r for k in range(n)]          # each year's sheet has the frame from here
    tears = [HOOK - TEAR] + [s + r - TEAR for s in starts]   # cover, then each year
    rips = [t + T_RIP for t in tears]

    # the stand jolts a little when a sheet is ripped off (and when a stamp lands)
    jolts = list(rips)
    stamp_ts = []
    for k, (rd, it, debut) in enumerate(rounds):
        if debut:
            stamp_ts.append(starts[k + (1 if bday else 0)] + .75)
    if bday:
        stamp_ts.append(starts[0] + .75)
    stops = [(0, "translate(0,0) rotate(0deg)")]
    for t in sorted(jolts + stamp_ts):
        big = t in jolts
        stops += [(t - .01, "translate(0,0) rotate(0deg)"),
                  (t + .06, f"translate({-3 if big else 0}px,{1 if big else 2}px) rotate({-.22 if big else 0}deg)"),
                  (t + .2, f"translate({1 if big else 0}px,0) rotate({.06 if big else 0}deg)"),
                  (t + .38, "translate(0,0) rotate(0deg)")]
    jolt = _track(comp, stops, ease="ease-out")

    # ---- persistent layers
    comp.add(_room())
    comp.add(_cutout("calcut", 5, "#fbf6ea") + _cutout("calboard", 9, "#f7f2e8"))
    comp.add(f'<div class="full" style="z-index:2"><div class="full" style="{jolt}">{_stand_back()}</div></div>')
    comp.add(f'<div class="full" style="z-index:4"><div class="full" style="{jolt}">{_base()}</div></div>')
    comp.add(f'<div class="full" style="z-index:50"><div class="full" style="{jolt}">{_binding()}{_crown(years)}'
             f'</div></div>')
    # the slider: parked off the strip until the first year, then year by year
    sl = [(0, None)]
    for k in range(n):
        sl += [(starts[k] + .02, k - 1 if k else None), (starts[k] + .4, k)]
    sl += [(content_end + .3, n - 1), (content_end + .7, None)]
    marks = "".join(_cross(years, k - 1, starts[k] + .42) for k in range(1, n))
    marks += _cross(years, n - 1, content_end + .75)
    comp.add(f'<div class="full" style="z-index:51"><div class="full" style="{jolt}">'
             f'<div class="abs" style="left:{STRIP[0]}px;top:{STRIP[1] - 8}px;width:{STRIP[2] - STRIP[0]}px;'
             f'height:{STRIP[3] - STRIP[1] + 16}px;overflow:hidden">'
             f'<div class="abs" style="left:{-STRIP[0]}px;top:{-STRIP[1] + 8}px;width:1080px;height:1920px">'
             f'{_slider(comp, years, sl)}</div></div>{marks}</div></div>')
    comp.add(f'<div class="full" style="z-index:60"><div class="full" style="{jolt}">{_block()}</div></div>')
    comp.add(f'<div class="full" style="z-index:80;pointer-events:none" data-safe="ignore">'
             f'<div class="cal-grain" style="{_a("calgr", 0, .5, "steps(1,end)")}animation-iteration-count:'
             f'{int(comp.duration / .5) + 2}"></div>'
             f'<div class="full" style="background:radial-gradient(120% 80% at 40% 38%,rgba(0,0,0,0) 58%,'
             f'rgba(30,16,6,.38) 100%)"></div></div>')
    comp.add(f'<div class="full" style="z-index:90"><div class="full" style="{jolt}">{_note()}</div></div>')
    comp.add(PREP_JS)
    comp.add(FIX_JS)

    persp = f"perspective:2300px;perspective-origin:{SX + SW / 2:.0f}px {SY + 180}px"

    # ---- the title sheet (frame 0) and the two lead standees
    a, b = lead[0][1], lead[1][1]
    cover = _sheet(_page_cover(ctx, span, bday), 11, tears[0])
    comp.scene(0, HOOK + .05, f'<div class="full" style="{persp}">{cover}</div>', fade_in=.01, fade_out=.01, z=40)
    stand = (_standee(ctx, b, 420, 690, 300, _a("calout", 1.62, .5, "cubic-bezier(.5,0,.85,.4)"))
             + _standee(ctx, a, 212, 750, 330, _a("calout", 1.72, .5, "cubic-bezier(.5,0,.85,.4)")))
    comp.scene(0, 2.3, f'<div class="full">{stand}</div>', fade_in=.01, fade_out=.01, z=65)
    comp.cue(1.62, "paper")
    comp.cue(tears[0] + .05, "paper"); comp.cue(rips[0], "paper"); comp.cue(rips[0] + .12, "whoosh")

    # ---- a sheet per year
    pages = []
    if bday:
        pages.append(_page_birthday(ctx, bday, starts[0]))
    for j, (rd, it, debut) in enumerate(rounds):
        pages.append(_page_year(ctx, rd, it, debut, starts[j + (1 if bday else 0)]))
    for k, (html, sounds) in enumerate(pages):
        show = tears[k]                      # visible from when the sheet above starts to lift
        sheet = _sheet(html, 100 + k, tears[k + 1])
        comp.scene(show, tears[k + 1] + TEAR + .02, f'<div class="full" style="{persp}">{sheet}</div>',
                   fade_in=.01, fade_out=.01, z=39 - k)
        for s in sounds:
            comp.cue(*s)
        comp.cue(starts[k] + .4, "tick")
        if k:
            comp.cue(starts[k] + .42, "pen")
        t = tears[k + 1]
        comp.cue(t + .05, "paper"); comp.cue(t + T_RIP, "paper"); comp.cue(t + T_RIP + .12, "whoosh")

    # ---- outro: the NOTES sheet, the question in pen, the picks on the desk again
    t = content_end
    notes, sounds = _page_outro(t)
    comp.scene(tears[-1], comp.duration, f'<div class="full" style="{persp}">{_sheet(notes, 999, None)}</div>',
               fade_in=.01, fade_out=.01, z=39 - n - 1)
    for s in sounds:
        comp.cue(*s)
    picks = [x[1] for x in lead] + ([third] if third else [])
    spots = [(170, 610, 300), (330, 660, 300), (478, 560, 250)]
    outro = ""
    for i, (it, (cx, h, w)) in enumerate(zip(picks, spots)):
        outro += _standee(ctx, it, cx, h, w, _a("calin", t + 1.3 + i * .22, .55, "cubic-bezier(.2,.75,.3,1)"))
        comp.cue(t + 1.3 + i * .22, "paper")
    comp.scene(t + 1.2, comp.duration, f'<div class="full">{outro}</div>', fade_in=.01, fade_out=.01, z=66)
    comp.cue(t + .3, "tick"); comp.cue(t + .75, "pen")
    comp.cues.sort()
    return comp
