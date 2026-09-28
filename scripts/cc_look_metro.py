"""
METRO -- On This Day, drawn as a transit line on a printed map.

    0:00  hook      the map's cover, complete on frame 0: an enamel board ON THIS
                    DAY · SEP 28 / THE FORTNITE ITEM SHOP, the whole line -- a
                    station per year -- wrapped around a lit poster case showing
                    the two lead outfits over "2018 → 2025 · one outfit from this
                    date, every year", the train waiting at the terminus, and at
                    the far end of the line its lime sign, USE CODE: BAD. The
                    stations blink through the route once and the train sets off.
    0:03  years     a station per year (6.5 s, longer on a short day): the train
                    pulls out and brakes into the next station (the line behind
                    it turns lime, the station fills in and its year is marked),
                    the station's name board slides past and stops -- SEP 28 · 2019
                    -- and the poster case scrolls to that year's poster: the
                    outfit big, its name, rarity and type, and "in the Item Shop
                    that day", or a NEW THAT DAY badge on its first day.
    0:55  outro     the train runs on into the end of the line, the code sign:
                    LAST STOP · WHICH YEAR HAD THE BEST SHOP?, and the poster
                    shows the lead picks with their years.

On Sep 26 the line starts a year earlier: its terminus, 2017, is the opening --
FORTNITE BATTLE ROYALE OPENS · SEPTEMBER 26, 2017 · PC · PLAYSTATION 4 · XBOX ONE,
9 YEARS TODAY -- and the cover says Fortnite turns 9.

Facts on screen are the classic format's: the date, each year, the name, the
rarity and type, NEW THAT DAY / "its first day in the Item Shop" only when the
plan says so, "in the Item Shop that day" otherwise, the span of years, the
birthday page and the outro question. The line, its stations and signs are
invented; nothing imitates a real transit system.

Everything a viewer reads sits inside the apps' safe box (cc_safe): the boards
in the wide band at the top (x 80-1000, y 258-428), the line's top row under
them, its column and the poster case left of the button rail, and the code
sign at the foot of the column (x 606-896, y 1168-1400). The code sign is on
screen, whole and still, in every frame. Only the map -- the paper, its folds,
the frame, the other (grey) lines and the river -- runs to the edges.
"""

import math

from cc_looks import KIT_CSS, LIME, PREP_JS, pad_to, tex
from cc_motion import RARITY, Comp, esc, trim_for

HOOK = 3.0
R = 6.5
FONTS = ("Barlow Condensed", "IBM Plex Mono")       # and Inter, always embedded

INK = "#141414"
PAPER = "#f2efe7"
GREY = "#76726a"            # a station's year before the train gets there

# ---- the boards (the wide band above the button rail)
BX, BW = 80, 920
BY, BH = 262, 130           # a station's name board
BY2, BH2 = 258, 170         # the two-line boards: the cover's and the last stop's

# ---- the line: a top row under the boards, a corner, a column down to the code sign
LY = 480                    # the top row's centre line
LX = 751                    # the column's: the centre of the code sign
RC = 70                     # the corner's radius
L0 = 56                     # the terminus
L1 = 1236                   # the line runs on under the code sign
CASE_W, CORE_W = 40, 26     # the line's black casing and its core
DISC_R, DISC_S = 25, 7      # a station: radius and ring
TOP_X0, TOP_X1 = 222, 650   # the first and the last station on the top row
COL_Y0, COL_Y1 = 612, 1050  # ... in the column
COL_STEP = 146
LAB_FS = 48                 # the stations' years
CAR_L, CAR_W, CAR_GAP = 48, 32, 5
DEPOT_X = 116               # where the train waits on the cover

# ---- the poster case, left of the column
PX, PY, PW, PH = 80, 590, 506, 810
FRAME = 14
IW, IH = PW - 2 * FRAME, PH - 2 * FRAME       # a poster: 478 x 782
SEAM = 22                                      # the gap between posters on the roll

# ---- the code sign: the lime bullet at the end of the line
CX, CY, CW, CH = 606, 1168, 290, 196
CODE_BOX_H = 232                               # with #EpicPartner under it

# ---- timing, around each page's start t0
DEP = .55                   # the train leaves this long before t0
ARR = .70                   # ... and has stopped this long after it
ARR_END = .95               # the last run, into the code sign, is a little longer
EASE_TRAIN = "cubic-bezier(.56,0,.26,1.04)"   # pulls away slowly, brakes firmly, settles
EASE_ROLL = "cubic-bezier(.6,0,.3,1)"

_A = (LX - RC) - L0
_B = math.pi / 2 * RC
LINE_LEN = _A + _B + (L1 - LY - RC)
LINE_D = f"M{L0},{LY} H{LX - RC} A{RC},{RC} 0 0 1 {LX},{LY + RC} V{L1}"


def s_top(x: float) -> float:
    return x - L0


def s_col(y: float) -> float:
    return _A + _B + (y - LY - RC)


S_DEPOT = s_top(DEPOT_X)
S_END = s_col(CY - 4 - (CAR_L + CAR_GAP / 2))   # the train's nose at the code sign

CSS = """
.mt-bd{font-family:'Barlow Condensed',sans-serif;font-weight:800;line-height:1;white-space:nowrap}
.mt-mono{font-family:'IBM Plex Mono',monospace;font-weight:500}
.mt-board{position:absolute;border-radius:14px;overflow:hidden;
  background:linear-gradient(180deg,#2a2e35 0%%,#1b1e23 38%%,#15171b 100%%);
  box-shadow:inset 0 1.5px 0 rgba(255,255,255,.16),inset 0 -2px 0 rgba(0,0,0,.5),
    0 2px 3px rgba(0,0,0,.3),0 16px 24px rgba(35,30,20,.2)}
.mt-board:before{content:"";position:absolute;inset:8px;border:1.5px solid rgba(236,236,228,.24);border-radius:8px}
.mt-board:after{content:"";position:absolute;inset:0;
  background:linear-gradient(102deg,rgba(255,255,255,0) 18%%,rgba(255,255,255,.055) 30%%,rgba(255,255,255,0) 44%%),
    url(%(grain)s) 0 0/256px 256px;opacity:.9}
.mt-screw{position:absolute;width:13px;height:13px;margin:-6.5px 0 0 -6.5px;border-radius:50%%;z-index:2;
  background:radial-gradient(circle at 38%% 32%%,#f2f2ef,#a3a6ab 52%%,#5d6066);
  box-shadow:0 1px 1.5px rgba(0,0,0,.6),inset 0 0 0 .5px rgba(0,0,0,.4)}
.mt-screw:after{content:"";position:absolute;left:2px;right:2px;top:5.5px;height:2px;border-radius:1px;
  background:rgba(45,46,50,.75);transform:rotate(var(--a,20deg))}
.mt-tab{position:absolute;border-radius:6px;background:%(lime)s;z-index:2}
.mt-case{position:absolute;border-radius:10px;
  background:repeating-linear-gradient(90deg,rgba(255,255,255,.07) 0 1px,rgba(0,0,0,.035) 1px 2px,rgba(255,255,255,0) 2px 4px),
    linear-gradient(158deg,#eceef0 0%%,#c4c7cc 26%%,#eef0f2 50%%,#b2b5bb 76%%,#d3d6da 100%%);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.55),inset 0 -2px 3px rgba(0,0,0,.2),
    0 3px 4px rgba(0,0,0,.26),0 24px 36px rgba(35,30,20,.2)}
.mt-win{position:absolute;overflow:hidden;border-radius:2px;background:#fbf8f1}
.mt-glass{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(116deg,rgba(255,255,255,0) 30%%,rgba(255,255,255,.17) 39%%,rgba(255,255,255,.04) 47%%,
    rgba(255,255,255,0) 58%%);
  box-shadow:inset 0 0 0 2px rgba(22,22,24,.62),inset 0 7px 12px rgba(0,0,0,.16),inset 0 -3px 8px rgba(0,0,0,.08)}
.mt-poster{position:absolute;left:0;width:%(iw)dpx;height:%(ih)dpx;overflow:hidden;
  background:radial-gradient(ellipse 85%% 62%% at 50%% 40%%,#fffdf8 0%%,#f8f4ea 62%%,#efe9dc 100%%)}
.mt-seam{position:absolute;left:0;width:%(iw)dpx;height:%(seam)dpx;background:#dcd8cf;
  box-shadow:inset 0 2px 3px rgba(0,0,0,.18),inset 0 -2px 3px rgba(0,0,0,.18)}
.mt-circ{position:absolute;border-radius:50%%}
.mt-fig{position:absolute;display:flex;justify-content:center;align-items:flex-end}
.mt-fig img{display:block;object-fit:contain;object-position:50%% 100%%}
.mt-rule{height:6px;background:%(ink)s}
.mt-name{font-family:Inter,sans-serif;font-weight:900;letter-spacing:-.02em;line-height:1;color:%(ink)s}
.mt-kind{display:flex;align-items:center;gap:12px;margin-top:10px;font-size:30px;letter-spacing:.06em;color:%(ink)s}
.mt-kind i{flex:none;width:20px;height:20px;border-radius:50%%;box-shadow:inset 0 0 0 2.5px rgba(0,0,0,.25)}
.mt-note{font-size:23px;line-height:1.2;color:#44403a;margin-top:8px}
.mt-badge{position:absolute;display:flex;align-items:center;gap:10px;height:62px;padding:0 20px 0 12px;
  border-radius:31px;background:#fffdf8;box-shadow:inset 0 0 0 6px %(ink)s,0 3px 5px rgba(0,0,0,.2)}
.mt-badge b{display:block;width:26px;height:26px;border-radius:50%%;background:%(ink)s}
.mt-badge span{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:34px;letter-spacing:.04em;
  color:%(ink)s;line-height:1;white-space:nowrap}
.mt-lab{position:absolute;font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:%(lab)dpx;line-height:1;
  padding:3px 10px 2px;border-radius:8px;white-space:nowrap}
.mt-car{position:absolute;left:0;top:0;width:%(cl)dpx;height:%(cw)dpx;offset-path:path('%(path)s');offset-rotate:auto;
  offset-anchor:50%% 50%%;border-radius:8px;background:linear-gradient(180deg,#34373c,#141518 45%%,#0d0e10);
  box-shadow:0 0 0 3px #fbf9f3,0 4px 6px 3px rgba(0,0,0,.28)}
.mt-car:before{content:"";position:absolute;left:9px;right:9px;top:13px;height:6px;border-radius:3px;background:#4b4f56}
.mt-car.front{border-radius:8px 17px 17px 8px}
.mt-car.front:after{content:"";position:absolute;right:5px;top:6px;width:7px;height:20px;border-radius:4px;background:%(lime)s}
.mt-code{position:absolute;left:0;top:0;width:%(cw_)dpx;height:%(ch)dpx;border-radius:44px;
  background:linear-gradient(180deg,#f0ff6a 0%%,%(lime)s 38%%,#dcf234 100%%);
  box-shadow:inset 0 0 0 7px %(ink)s,0 3px 4px rgba(0,0,0,.28),0 16px 24px rgba(35,30,20,.2);
  display:flex;flex-direction:column;align-items:center;justify-content:center;color:#111}
@keyframes mtbin{0%%{transform:translateX(1180px)}80%%{transform:translateX(-9px)}100%%{transform:translateX(0)}}
@keyframes mtbout{from{transform:translateX(0)}to{transform:translateX(-1180px)}}
@keyframes mtfill{from{transform:scale(0)}to{transform:scale(1)}}
@keyframes mtflash{0%%,100%%{opacity:0}30%%,60%%{opacity:1}}
@keyframes mtbadge{0%%{opacity:0;transform:scale(1.3)}55%%{opacity:1;transform:scale(.97)}100%%{opacity:1;transform:scale(1)}}
@keyframes mtbump{0%%,100%%{transform:translateY(0)}35%%{transform:translateY(7px)}70%%{transform:translateY(-2px)}}
"""


def _a(name: str, t: float, dur: float, ease: str = "linear", fill: str = "both") -> str:
    return f"animation:{name} {dur:.3f}s {ease} {t:.3f}s 1 normal {fill};"


def _kf(name: str, pts: list, dur: float) -> str:
    """Keyframes over the whole video from [(t, css, easing to the next point)]."""
    out, last = [], -1.0
    for t, css, ease in pts:
        pct = max(0.0, min(100.0, t / dur * 100))
        if pct <= last:
            pct = last + .0005
        last = pct
        out.append(f"{pct:.4f}%{{{css}" + (f";animation-timing-function:{ease}" if ease else "") + "}")
    return f"@keyframes {name}{{{''.join(out)}}}"


def _track(comp: Comp, name: str, pts: list) -> str:
    comp.css(_kf(name, pts, comp.duration))
    return f"animation:{name} {comp.duration:.3f}s linear 0s 1 normal both;"


def _col(it: dict) -> str:
    return RARITY.get(it.get("rarity", ""), "#9AA0A6")


def _kind(it: dict) -> str:
    return " ".join(x for x in (it.get("rarity_label") or "", it.get("type") or "") if x).strip()


# ------------------------------------------------------------------ the line

def _stations(n: int) -> list:
    """(x, y, s, where) for n stations: four along the top row (three on a
    six-year day), the rest down the column."""
    n_top = 3 if n <= 6 else 4
    n_col = n - n_top
    out = []
    for i in range(n_top):
        x = TOP_X0 + (TOP_X1 - TOP_X0) * i / (n_top - 1)
        out.append((x, LY, s_top(x), "top"))
    step = min(COL_STEP, (COL_Y1 - COL_Y0) / max(n_col - 1, 1))
    for i in range(n_col):
        y = COL_Y0 + step * i
        out.append((LX, y, s_col(y), "col"))
    return out


def _line_svg(comp: Comp, st: list, fill_anim: str, t_arr: list, flash: list) -> str:
    """The line: its black casing, a pale core the train paints lime, the
    terminus bar, and a disc per station that fills in when the train gets there."""
    L = LINE_LEN + 20
    parts = [f'<svg class="abs" width="1080" height="1920" viewBox="0 0 1080 1920" style="left:0;top:0;overflow:visible">',
             f'<path d="{LINE_D}" fill="none" stroke="{INK}" stroke-width="{CASE_W}" stroke-linejoin="round"/>',
             f'<path d="{LINE_D}" fill="none" stroke="#fbf9f3" stroke-width="{CORE_W}" stroke-linejoin="round"/>',
             f'<path d="{LINE_D}" fill="none" stroke="{LIME}" stroke-width="{CORE_W}" stroke-linejoin="round" '
             f'style="stroke-dasharray:{L:.1f} {L:.1f};{fill_anim}"/>',
             # the terminus: a bar across the line's end
             f'<rect x="{L0 - 6}" y="{LY - 34}" width="12" height="68" rx="3" fill="{INK}"/>']
    for k, (x, y, s, _) in enumerate(st):
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{DISC_R}" fill="#fffdf8" stroke="{INK}" stroke-width="{DISC_S}"/>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{DISC_R - 7}" fill="{LIME}" '
                     f'style="opacity:0;{_a("mtflash", flash[k], .34, "ease-in-out")}"/>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{DISC_R}" fill="{INK}" '
                     f'style="transform-box:fill-box;transform-origin:50% 50%;'
                     f'{_a("mtfill", t_arr[k], .3, "cubic-bezier(.3,1.5,.55,1)")}"/>')
    parts.append("</svg>")
    return "".join(parts)


def _labels(comp: Comp, st: list, years: list, t_arr: list, t_leave: list) -> str:
    out = []
    for k, ((x, y, s, where), yr) in enumerate(zip(st, years)):
        track = _track(comp, f"mtlab{k}", [
            (0, f"color:{GREY};background-color:rgba(20,20,20,0)", "linear"),
            (t_arr[k] - .05, f"color:{GREY};background-color:rgba(20,20,20,0)", "ease-out"),
            (t_arr[k] + .2, "color:#fbfaf6;background-color:rgba(20,20,20,1)", "linear"),
            (t_leave[k], "color:#fbfaf6;background-color:rgba(20,20,20,1)", "ease-in-out"),
            (t_leave[k] + .35, f"color:{INK};background-color:rgba(20,20,20,0)", "linear"),
        ])
        if where == "top":
            pos = f"left:{x - 100:.0f}px;width:200px;top:{LY + DISC_R + 10}px;text-align:center"
            out.append(f'<div class="abs" style="{pos}"><span class="mt-lab" style="position:relative;{track}">'
                       f'{yr}</span></div>')
        else:
            pos = f"right:{1080 - (LX - DISC_R - 12):.0f}px;top:{y - LAB_FS / 2 - 3:.0f}px"
            out.append(f'<div class="mt-lab" style="{pos};{track}">{yr}</div>')
    return "".join(out)


def _train(comp: Comp, moves: list) -> str:
    """Two cars on the line's path, the front one with its lime lamp. moves:
    [(t_leave, t_arrive, s_from, s_to)]; s is the middle of the train."""
    half = (CAR_L + CAR_GAP) / 2
    html = []
    for cls, off in (("front", half), ("", -half)):
        pts = [(0, f"offset-distance:{S_DEPOT + off:.1f}px", "linear")]
        for t0, t1, a, b in moves:
            pts.append((t0, f"offset-distance:{a + off:.1f}px", EASE_TRAIN))
            pts.append((t1, f"offset-distance:{b + off:.1f}px", "linear"))
        html.append(f'<div class="mt-car {cls}" style="{_track(comp, "mtcar" + (cls or "rear"), pts)}"></div>')
    return "".join(html)


def _fill_anim(comp: Comp, moves: list) -> str:
    """The lime behind the train: the core's dash, moved with the same easing."""
    L = LINE_LEN + 20
    pts = [(0, f"stroke-dashoffset:{L - S_DEPOT:.1f}px", "linear")]
    for t0, t1, a, b in moves:
        pts.append((t0, f"stroke-dashoffset:{L - a:.1f}px", EASE_TRAIN))
        pts.append((t1, f"stroke-dashoffset:{L - b:.1f}px", "linear"))
    return _track(comp, "mtlime", pts)


# ------------------------------------------------------------------ the map around it

def _map() -> str:
    """The printed map the line sits on: its frame, the other lines of the network
    (grey, out of service for this video), the river. Decoration only, and all
    of it away from the words."""
    ghost = "#b9b5ab"
    s = ['<svg class="abs" data-safe="ignore" width="1080" height="1920" viewBox="0 0 1080 1920" style="left:0;top:0">']
    # the river, across the foot of the sheet
    river = "M-40,1512 H236 L372,1648 H676 L806,1518 H1120"
    s.append(f'<path d="{river}" fill="none" stroke="#c6d3d6" stroke-width="78" stroke-linejoin="round"/>')
    s.append(f'<path d="{river}" fill="none" stroke="#d6e0e2" stroke-width="70" stroke-linejoin="round"/>')
    # two other lines of the network, drawn thin and grey
    g1 = "M-30,1738 H540 L612,1666 H1110"
    g2 = "M964,-30 V172 L1004,212 V1560 L948,1616 V1950"
    g3 = "M-30,176 H380 L430,126 H1110"
    for d in (g1, g2, g3):
        s.append(f'<path d="{d}" fill="none" stroke="{ghost}" stroke-width="12" stroke-linejoin="round"/>')
    for x, y in ((150, 1738), (330, 1738), (820, 1666), (1004, 380), (1004, 900), (1004, 1300), (240, 176), (700, 126)):
        s.append(f'<circle cx="{x}" cy="{y}" r="9" fill="#f7f4ec" stroke="{ghost}" stroke-width="4"/>')
    for x, y in ((964, 126), (1004, 1666)):
        s.append(f'<circle cx="{x}" cy="{y}" r="14" fill="#f7f4ec" stroke="#9d998f" stroke-width="5"/>')
    # the sheet's printed frame, with its grid ticks
    s.append('<rect x="26" y="26" width="1028" height="1868" fill="none" stroke="#4a4842" stroke-width="3"/>')
    s.append('<rect x="34" y="34" width="1012" height="1852" fill="none" stroke="#4a4842" stroke-width="1" opacity=".6"/>')
    for x in range(26 + 171, 1054, 171):
        s.append(f'<line x1="{x}" y1="26" x2="{x}" y2="40" stroke="#4a4842" stroke-width="2"/>'
                 f'<line x1="{x}" y1="1880" x2="{x}" y2="1894" stroke="#4a4842" stroke-width="2"/>')
    for y in range(26 + 187, 1894, 187):
        s.append(f'<line x1="26" y1="{y}" x2="40" y2="{y}" stroke="#4a4842" stroke-width="2"/>'
                 f'<line x1="1040" y1="{y}" x2="1054" y2="{y}" stroke="#4a4842" stroke-width="2"/>')
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------------------ boards

def _screws(w: int, h: int) -> str:
    return (f'<i class="mt-screw" style="left:24px;top:{h / 2:.0f}px;--a:24deg"></i>'
            f'<i class="mt-screw" style="left:{w - 24}px;top:{h / 2:.0f}px;--a:-38deg"></i>')


def _board(inner: str, y: int, h: int) -> str:
    return (f'<div class="mt-board" style="left:{BX}px;top:{y}px;width:{BW}px;height:{h}px">'
            f'{_screws(BW, h)}<div class="mt-tab" style="left:44px;top:24px;width:12px;height:{h - 48}px"></div>'
            f'{inner}</div>')


def _board_station(when: str, year: int) -> str:
    inner = (f'<div class="mt-bd" style="position:absolute;left:78px;top:{(BH - 104) / 2 + 2:.0f}px;font-size:104px;'
             f'letter-spacing:.01em;z-index:2"><span style="color:#aeb3bc">{esc(when)} ·</span> '
             f'<span style="color:#fbfaf6">{year}</span></div>')
    return _board(inner, BY, BH)


def _board_cover(when: str) -> str:
    inner = (f'<div class="mt-bd" style="position:absolute;left:78px;top:18px;font-size:96px;color:#fbfaf6;z-index:2">'
             f'ON THIS DAY</div>'
             f'<div class="mt-bd" style="position:absolute;right:40px;top:18px;font-size:96px;color:{LIME};z-index:2">'
             f'{esc(when)}</div>'
             f'<div style="position:absolute;left:80px;top:124px;font:700 28px/1 Inter,sans-serif;letter-spacing:.16em;'
             f'color:#c3c8d0;white-space:nowrap;z-index:2">THE FORTNITE ITEM SHOP</div>')
    return _board(inner, BY2, BH2)


def _board_last() -> str:
    inner = (f'<div class="mt-mono" style="position:absolute;left:80px;top:26px;font-size:28px;font-weight:700;'
             f'letter-spacing:.2em;color:#aeb3bc;line-height:1;z-index:2">LAST STOP</div>'
             f'<div class="mt-bd" data-fit="{BW - 120}" style="position:absolute;left:78px;top:68px;font-size:80px;'
             f'color:#fbfaf6;z-index:2">WHICH YEAR HAD THE BEST SHOP?</div>')
    return _board(inner, BY2, BH2)


def _slide(board: str, t_in, t_out) -> str:
    """A board passing the window: in from the right as the train brakes, out to
    the left as it pulls away. t_in/t_out None: already there / stays."""
    outer = _a("mtbout", t_out, .6, "cubic-bezier(.5,0,.85,.4)", "forwards") if t_out is not None else ""
    inner = _a("mtbin", t_in, .8, "cubic-bezier(.2,.75,.3,1)") if t_in is not None else ""
    return (f'<div class="abs" style="left:0;top:0;{outer}"><div class="abs" style="left:0;top:0;{inner}">'
            f'{board}</div></div>')


# ------------------------------------------------------------------ posters

def _figure(ctx, it: dict, h: float, maxw: float) -> str:
    uri = ctx.art(it)
    if uri:
        tr = ' data-trim="figure"' if trim_for(it) == "figure" else " data-trim"
        return (f'<img{tr} data-name="{esc(it["name"])}" src="{uri}" '
                f'style="height:{h:.0f}px;max-width:{maxw:.0f}px">')
    return (f'<div class="mt-mono" style="width:{min(maxw, h * .55):.0f}px;height:{h * .8:.0f}px;display:flex;'
            f'align-items:center;justify-content:center;text-align:center;padding:18px;font-size:26px;color:#5a564e;'
            f'border:3px dashed #b9b3a6;border-radius:24px;overflow-wrap:anywhere">{esc(it["name"])}</div>')


def _poster_station(ctx, it: dict, debut: bool, top: float, t_arr: float) -> str:
    col = _col(it)
    note = "its first day in the Item Shop" if debut else "in the Item Shop that day"
    w = IW - 52
    html = (f'<div class="mt-poster" style="top:{top:.0f}px">'
            f'<div class="mt-circ" style="left:{IW / 2 - 190:.0f}px;top:96px;width:380px;height:380px;background:{col}"></div>'
            f'<div class="mt-fig" style="left:20px;right:20px;top:24px;height:552px">{_figure(ctx, it, 552, IW - 48)}</div>'
            f'<div class="abs" style="left:26px;top:588px;width:{w}px">'
            f'<div class="mt-rule"></div>'
            f'<div class="mt-name" data-fit="{w}" data-lines="2" style="width:{w}px;font-size:48px;margin-top:12px">'
            f'{esc(it["name"])}</div>'
            f'<div class="mt-kind mt-bd"><i style="background:{col}"></i>'
            f'<span data-fit="{w - 32}" style="display:inline-block">{esc(_kind(it).upper())}</span></div>'
            f'<div class="mt-note mt-mono">{esc(note)}</div></div>')
    if debut:
        html += (f'<div class="mt-badge" style="left:20px;top:22px;transform-origin:30px 31px;'
                 f'{_a("mtbadge", t_arr + .45, .36, "cubic-bezier(.3,1.3,.5,1)")}"><b></b><span>NEW THAT DAY</span></div>')
    return html + "</div>"


def _poster_cover(ctx, lead: list, span: str, bday) -> str:
    a, b = lead[0][1], lead[1][1]
    w = IW - 52
    if bday:
        big, small = f"FORTNITE TURNS {bday['age']}!", f"Battle Royale came out on this day in {bday['year']}"
        big_fs = 54
    else:
        big, small = span, "one outfit from this date, every year"
        big_fs = 70
    return (f'<div class="mt-poster" style="top:0">'
            f'<div class="mt-circ" style="left:28px;top:110px;width:300px;height:300px;background:{_col(a)}"></div>'
            f'<div class="mt-circ" style="left:160px;top:196px;width:290px;height:290px;background:{_col(b)};'
            f'mix-blend-mode:multiply"></div>'
            f'<div class="mt-fig" style="left:6px;width:260px;top:36px;height:540px">{_figure(ctx, a, 540, 250)}</div>'
            f'<div class="mt-fig" style="left:212px;width:260px;top:64px;height:516px">{_figure(ctx, b, 516, 250)}</div>'
            f'<div class="abs" style="left:26px;top:592px;width:{w}px">'
            f'<div class="mt-rule"></div>'
            f'<div class="mt-name" data-fit="{w}" style="font-size:{big_fs}px;margin-top:14px;white-space:nowrap">'
            f'{esc(big)}</div>'
            f'<div class="mt-note mt-mono" data-fit="{w}" data-lines="2" style="width:{w}px;font-size:25px;margin-top:12px">'
            f'{esc(small)}</div></div></div>')


def _poster_bday(bday: dict, when: str, top: float, t_arr: float) -> str:
    w = IW - 52
    y = bday["year"]
    return (f'<div class="mt-poster" style="top:{top:.0f}px">'
            f'<div class="mt-name" style="position:absolute;left:24px;top:30px;font-size:160px;letter-spacing:-.04em">{y}</div>'
            f'<svg class="abs" style="left:0;top:214px" width="{IW}" height="60">'
            f'<path d="M36,30 H{IW - 20}" stroke="{INK}" stroke-width="40"/>'
            f'<path d="M36,30 H{IW - 20}" stroke="{LIME}" stroke-width="26"/>'
            f'<rect x="30" y="0" width="12" height="60" rx="3" fill="{INK}"/>'
            f'<circle cx="120" cy="30" r="{DISC_R}" fill="#fffdf8" stroke="{INK}" stroke-width="{DISC_S}"/></svg>'
            f'<div class="abs" style="left:26px;top:300px;width:{w}px">'
            f'<div class="mt-name" style="font-size:50px;line-height:1.02">FORTNITE<br>BATTLE ROYALE</div>'
            f'<div class="mt-bd" style="font-size:150px;line-height:.86;margin-top:6px;color:{INK}">OPENS</div>'
            f'<div class="mt-rule" style="margin-top:18px"></div>'
            f'<div class="mt-bd" style="font-size:46px;margin-top:14px;color:{INK}">{esc(when.upper())}, {y}</div>'
            f'<div class="mt-note mt-mono" data-fit="{w}" style="font-size:24px;margin-top:10px;white-space:nowrap">'
            f'PC · PLAYSTATION 4 · XBOX ONE</div></div>'
            f'<div class="mt-badge" style="right:20px;top:28px;background:{INK};transform-origin:80% 50%;'
            f'{_a("mtbadge", t_arr + .5, .36, "cubic-bezier(.3,1.3,.5,1)")}">'
            f'<b style="background:{LIME}"></b><span style="color:#fbfaf6">{bday["age"]} YEARS TODAY</span></div>'
            f'</div>')


def _poster_outro(ctx, picks: list, top: float) -> str:
    """The lead picks side by side, each over its year."""
    n = len(picks)
    cw = (IW - 24) / n
    html = [f'<div class="mt-poster" style="top:{top:.0f}px">']
    for i, (yr, it) in enumerate(picks):
        x = 12 + i * cw
        d = min(cw - 16, 200)
        html.append(f'<div class="mt-circ" style="left:{x + cw / 2 - d / 2:.0f}px;top:{150 + (i % 2) * 40}px;'
                    f'width:{d:.0f}px;height:{d:.0f}px;background:{_col(it)}"></div>'
                    f'<div class="mt-fig" style="left:{x:.0f}px;width:{cw:.0f}px;top:40px;height:520px">'
                    f'{_figure(ctx, it, 500, cw - 10)}</div>'
                    f'<div class="abs" style="left:{x:.0f}px;width:{cw:.0f}px;top:586px;text-align:center">'
                    f'<div class="mt-rule" style="margin:0 10px"></div>'
                    f'<div class="mt-bd" style="font-size:64px;margin-top:14px;color:{INK}">{yr}</div>'
                    f'<div class="mt-name" data-fit="{cw - 16:.0f}" data-lines="2" style="width:{cw - 16:.0f}px;'
                    f'margin:8px auto 0;font-size:24px;line-height:1.08;letter-spacing:0;font-weight:800">'
                    f'{esc(it["name"])}</div></div>')
    html.append("</div>")
    return "".join(html)


def _case(roll: str, roll_anim: str) -> str:
    return (f'<div class="mt-case" style="left:{PX}px;top:{PY}px;width:{PW}px;height:{PH}px">'
            f'<div class="mt-win" style="left:{FRAME}px;top:{FRAME}px;width:{IW}px;height:{IH}px">'
            f'<div class="abs" style="left:0;top:0;width:{IW}px;{roll_anim}">{roll}</div>'
            f'<div class="mt-glass"></div></div></div>')


# ------------------------------------------------------------------ the code sign

def _code(anim: str = "") -> str:
    return (f'<div class="abs" data-safe="key" data-name="code" style="left:{CX}px;top:{CY}px;width:{CW}px;'
            f'height:{CODE_BOX_H}px">'
            f'<div class="abs" style="left:0;top:0;width:{CW}px;height:{CODE_BOX_H}px;{anim}">'
            f'<div class="mt-code">'
            f'<div style="font:800 40px/1 Inter,sans-serif;letter-spacing:.07em;margin-top:6px">USE CODE:</div>'
            f'<div class="mt-bd" style="font-size:150px;line-height:.8;margin-top:6px;letter-spacing:.02em">BAD</div>'
            f'</div>'
            f'<div class="mt-mono" style="position:absolute;left:0;width:{CW}px;top:{CH + 8}px;text-align:center;'
            f'font-size:24px;line-height:1;color:{INK};font-weight:700">#EpicPartner</div>'
            f'</div></div>')


# ------------------------------------------------------------------ the video

def on_this_day(ctx, rounds: list, bday, lead: list, third) -> Comp:
    day = ctx.day
    when = day.strftime("%b %-d").upper()                  # SEP 28
    when_long = day.strftime("%B %-d")                     # September 28
    years = ([bday["year"]] if bday else []) + [rd["year"] for rd, _, _ in rounds]
    n = len(years)
    r = max(R, (62.0 - 7.5 - HOOK) / n)
    content_end = HOOK + n * r
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(CSS % dict(grain=tex("metro-grain.png"), lime=LIME, ink=INK, iw=IW, ih=IH, seam=SEAM, lab=LAB_FS,
                        cl=CAR_L, cw=CAR_W, path=LINE_D, cw_=CW, ch=CH))

    st = _stations(n)
    t0s = [HOOK + i * r for i in range(n)]
    t_dep = [t - DEP for t in t0s]
    t_arr = [t + ARR for t in t0s]
    t_out = content_end - DEP                   # leaves the last station
    t_end = content_end + ARR_END               # ... and stops at the code sign
    t_leave = t_dep[1:] + [t_out]
    moves = [(t_dep[i], t_arr[i], S_DEPOT if i == 0 else st[i - 1][2], st[i][2]) for i in range(n)]
    moves.append((t_out, t_end, st[-1][2], S_END))
    flash = [.55 + k * .09 for k in range(n)]

    # ---- the map, the line, its stations and the train
    comp.add(f'<div class="full" style="z-index:0;background:url({tex("metro-paper.jpg")}) center/cover"></div>')
    comp.add(f'<div class="full" style="z-index:1">{_map()}</div>')
    comp.add(f'<div class="full" style="z-index:2">{_line_svg(comp, st, _fill_anim(comp, moves), t_arr, flash)}</div>')
    comp.add(f'<div class="full" style="z-index:3">{_labels(comp, st, years, t_arr, t_leave)}</div>')
    comp.add(f'<div class="full" style="z-index:4">{_train(comp, moves)}</div>')

    # ---- the poster case: one roll of posters, scrolled on at each station
    step = IH + SEAM
    roll = [_poster_cover(ctx, lead, f"{years[0]} → {years[-1]}", bday)]
    k = 0
    if bday:
        roll.append(_poster_bday(bday, when_long, step, t_arr[0]))
        k = 1
    for j, (rd, it, debut) in enumerate(rounds):
        roll.append(_poster_station(ctx, it, debut, (k + j + 1) * step, t_arr[k + j]))
    picks = [(rd["year"], it) for rd, it, _ in lead]
    if third is not None:
        yr = next((rd["year"] for rd, it, _ in rounds if it is third), None)
        if yr is not None:
            picks.append((yr, third))
    roll.append(_poster_outro(ctx, picks, (n + 1) * step))
    roll += [f'<div class="mt-seam" style="top:{(j + 1) * step - SEAM}px"></div>' for j in range(n + 1)]
    pts = [(0, "transform:translateY(0)", "linear")]
    for j, (t0, t1) in enumerate([(t_dep[i], t_arr[i]) for i in range(n)] + [(t_out, t_end)]):
        pts.append((t0 + .12, f"transform:translateY({-j * step}px)", EASE_ROLL))
        pts.append((t1 + .08, f"transform:translateY({-(j + 1) * step}px)", "linear"))
    comp.add(f'<div class="full" style="z-index:5">{_case("".join(roll), _track(comp, "mtroll", pts))}</div>')

    # ---- the boards: the cover's, one per station, the last stop's
    boards = [_slide(_board_cover(when), None, t_dep[0])]
    for i, yr in enumerate(years):
        boards.append(_slide(_board_station(when, yr), t_arr[i] - .8, t_leave[i]))
    boards.append(_slide(_board_last(), t_end - .8, None))
    comp.add(f'<div class="full" style="z-index:6">{"".join(boards)}</div>')

    # ---- the code sign, at the end of the line: still, whole, in every frame
    comp.add(f'<div class="full" style="z-index:30">{_code(_a("mtbump", t_end - .02, .5, "ease-out"))}</div>')
    comp.add(PREP_JS)

    # ---- sound
    comp.cue(.3, "click")
    for k in range(0, n, 2):
        comp.cue(flash[k], "tick")
    for i in range(n):
        comp.cue(t_dep[i], "whoosh")
        comp.cue(t_arr[i] - .05, "ding")
    for i, (rd, it, debut) in enumerate(rounds):
        if debut:
            comp.cue(t_arr[(1 if bday else 0) + i] + .45, "click")
    if bday:
        comp.cue(t_arr[0] + .5, "click")
    comp.cue(t_out, "whoosh")
    comp.cue(t_end - .05, "ding")
    comp.cue(t_end + .4, "ding")
    comp.cues.sort()
    return comp
