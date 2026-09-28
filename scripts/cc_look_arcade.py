"""
ARCADE -- On This Day as the high-score screen of an old arcade cabinet.

    0:00  hook      the cabinet, filmed from a little to its right: the printed
                    marquee on top, the tube in its moulded bezel, the lime
                    USE CODE: BAD sign under it, the stick and buttons below.
                    The tube shows the title screen: a chunky pixel ON THIS DAY,
                    the two lead outfits facing off either side of the date, the
                    span of years, and PRESS START blinking. Start is pressed,
                    the screen breaks up into blocks...
    0:03  stages    ...into the HIGH SCORES screen. One stage per year: the
                    year's digits drop into place, the PLAYER SELECT panel shows
                    the outfit blocky and low-res for a few frames before it
                    snaps sharp, its rarity and type under it, and a blinking
                    FIRST DAY IN THE SHOP! when it was new that day. At the same
                    time a row of the high-score table lights up in lime and
                    the name is typed into it letter by letter behind a
                    blinking cursor, as if someone were entering initials.
                    STAGE 3/8 and a row of pips count the years; the table
                    fills. On Sep 26 the first stage is a BONUS STAGE: Battle
                    Royale's release day and a pixel birthday cake.
    end   outro     the screen breaks up again: WHICH YEAR HAD THE BEST SHOP?,
                    the lead picks side by side with their years and a selection
                    frame hopping between them, and the sign under the tube
                    lights up: lime, with the code in black.

Facts on screen are the classic format's: the date, each year, the name, its
rarity and type, "first day in the shop" only when the plan says so ("in the
Item Shop that day" otherwise), the span of years, the birthday page on Sep 26
and the outro question. The code is the lime sign under the tube, on screen and
unmoved in every frame.

Every app lays its UI over the edges (cc_safe), so the cabinet is framed for
it: the marquee sits under the apps' header, the side of the cabinet (the camera
is a little to the right) runs down under their buttons, the control panel and
coin door under their captions. Everything a viewer reads -- the tube's
picture, and the code sign under it -- is inside the safe box: the tube's
picture keeps to x 64-872, y 256-1196, and on frame 0 it starts at y 297.

Cheap to render: the cabinet is one static layer; the tube's scanlines, grille,
grain and curvature shading are one static overlay (a committed tile and
gradients). What changes is small: pieces switch on and off (visibility), the
year's digits drop (transforms), names type on (a stepped clip). The low-res
frames of each outfit are drawn once, before frame 0, into tiny canvases shown
with image-rendering: pixelated. No filters or blend modes on anything that
moves.
"""

import math
import random

from cc_looks import LIME, PREP_JS, pad_to, tex
from cc_motion import Comp, esc, trim_for

HOOK = 3.0
R = 6.5
FPS = 30
FONTS = ("VT323", "Archivo Black", "Barlow Condensed")

CYAN = "#3FD3EE"
CYAN_D = "#1B7F93"            # the pixel title's extrusion
WHITE = "#F3F5EF"
DIM = "#4E5963"
INK = "#111111"

# VT323 metrics (measured in the render browser): every glyph advances .4 em,
# capitals are .56 em tall, the baseline sits .8 em below the top of a line box
# (line-height 1).
EM, CAP, BASE = .4, .56, .8

# ---- the cabinet (the camera stands a little to its right)
FACE_R = 920                        # the front face runs x 16-920 between its T-mouldings
MID = 468                           # the middle of the front face
SCR = (42, 246, 894, 1212)          # the tube's opening: x0, y0, x1, y1
SCR_RAD = 46
CX0, CX1 = 64, 872                  # where the picture keeps its text and art (inside the safe box)
TOP = 256                           # the picture's top line (status line)
FLOOR = 1196                        # ...and its bottom
SIGN = (170, 1240, 596, 172)        # the code sign: x, y, w, h

# ---- the high-score screen
PANEL = (64, 318, 452, 1196)        # PLAYER SELECT: x0, y0, x1, y1
RCOL = (478, 872)                   # the right-hand column
YEAR_S, YEAR_Y = 212, 300           # the year's size and line-box top
NAME_Y, NAME_S = 500, 72
TABLE_Y = 688                       # "HIGH SCORES · SEP 28"
ROW_S = 36


# ------------------------------------------------------------------ timing

def _snap(t: float) -> float:
    """Half a frame before the frame nearest t, so a switch never lands on a
    frame's own time (where rounding could put it either side)."""
    return max(0.0, (round(t * FPS) - .5) / FPS)


def _union(windows: list) -> list:
    out = []
    for a, b in sorted((a, b) for a, b in windows if b > a):
        if out and a <= out[-1][1] + 1e-6:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _blink(a: float, b: float, on: float, off: float, start_on: bool = True) -> list:
    """Windows for something blinking between a and b (on first)."""
    out, t, lit = [], a, start_on
    while t < b - 1e-6:
        d = on if lit else off
        if lit:
            out.append((t, min(b, t + d)))
        t += d
        lit = not lit
    return out


class _Tracks:
    """On/off switches as keyframe tracks over the whole video: visibility for
    single pieces (costs nothing), opacity for groups."""

    def __init__(self, comp: Comp):
        self.comp = comp
        self.d = comp.duration

    def _track(self, prop: str, pts: list, before: str) -> str:
        name = self.comp.uid("av")
        ks = {0.0: before}
        for t, v in pts:
            ks[round(min(_snap(t), self.d) / self.d * 100, 4)] = v
        last = ks[max(ks)]
        frames = "".join(f"{k:.4f}%{{{prop}:{v}}}" for k, v in sorted(ks.items())) + f"100%{{{prop}:{last}}}"
        self.comp.css(f"@keyframes {name}{{{frames}}}")
        return f"{name} {self.d:.3f}s steps(1,end) 0s 1 normal both"

    def vis(self, windows: list) -> str:
        pts, before = [], "hidden"
        for a, b in _union(windows):
            if a >= self.d:
                continue
            if a <= 0:
                before = "visible"
            else:
                pts.append((a, "visible"))
            if b < self.d - .02:                     # kept on to the end: the end card fades in over it
                pts.append((b, "hidden"))
        return self._track("visibility", pts, before)

    def op(self, windows: list) -> str:
        pts, before = [], "0"
        for a, b in _union(windows):
            if a <= 0:
                before = "1"
            else:
                pts.append((a, "1"))
            pts.append((b, "0"))
        return self._track("opacity", pts, before)


def _anim(*entries) -> str:
    entries = [e for e in entries if e]
    return f"animation:{','.join(entries)};" if entries else ""


def _a(name: str, t: float, dur: float, ease: str = "linear", it: str = "1") -> str:
    return f"{name} {dur:.3f}s {ease} {t:.3f}s {it} normal both"


# ------------------------------------------------------------------ text

def _wrap(text: str, n: int) -> list:
    lines, cur = [], ""
    for w in text.split():
        cand = f"{cur} {w}" if cur else w
        if len(cand) <= n or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _fit(text: str, width: float, size: float, lines: int = 1, low: float = 16) -> tuple:
    """(size, lines): the biggest size up to `size` at which VT323 sets `text` in
    at most `lines` lines no wider than `width` (it's monospaced: .4 em a glyph)."""
    s = float(size)
    while s > low:
        n = max(1, int(width / (EM * s) + 1e-6))
        ls = _wrap(text, n)
        if len(ls) <= lines and all(len(x) <= n for x in ls):
            return s, ls
        s -= 1
    n = max(1, int(width / (EM * low)))
    return low, _wrap(text, n)


def _t(text: str, x: float, y: float, size: float, color: str = WHITE, extra: str = "", cls: str = "") -> str:
    """One line of VT323 with its line box's top-left at (x, y)."""
    return (f'<div class="abs apx{cls}" style="left:{x:.0f}px;top:{y:.0f}px;font-size:{size:.0f}px;'
            f'color:{color};{extra}">{esc(text)}</div>')


def _tc(text: str, cx: float, y: float, size: float, color: str = WHITE, extra: str = "") -> str:
    """The same, centred on cx (monospaced, so its width is known)."""
    w = len(text) * EM * size
    return _t(text, cx - w / 2, y, size, color, extra)


def _typed(text: str, x: float, y: float, size: float, color: str, t: float, dt: float,
           vis: str = "", cursor: str = "", cur_vis: str = "") -> str:
    """A line typed on one letter at a time from t (dt a letter); `cursor` is the
    colour of a block cursor that walks along with it."""
    n = max(1, len(text))
    dur = n * dt
    out = (f'<div class="abs apx" style="left:{x:.0f}px;top:{y:.0f}px;font-size:{size:.0f}px;color:{color};'
           f'{_anim(_a("actype", t, dur, f"steps({n},end)"), vis)}">{esc(text)}</div>')
    if cursor:
        cw = EM * size
        out += (f'<i class="abs" style="left:{x:.0f}px;top:{y + (BASE - CAP) * size:.0f}px;width:{cw:.1f}px;'
                f'height:{CAP * size:.0f}px;background:{cursor};--cw:{n * cw:.1f}px;'
                f'{_anim(_a("accur", t, dur, f"steps({n},end)"), cur_vis)}"></i>')
    return out


# ------------------------------------------------------------------ the chunky pixel face (title only)

GLYPHS = {
    "A": [".####.", "##..##", "##..##", "######", "##..##", "##..##", "##..##"],
    "B": ["#####.", "##..##", "##..##", "#####.", "##..##", "##..##", "#####."],
    "C": [".####.", "##..##", "##....", "##....", "##....", "##..##", ".####."],
    "D": ["####..", "##.##.", "##..##", "##..##", "##..##", "##.##.", "####.."],
    "E": ["######", "##....", "##....", "#####.", "##....", "##....", "######"],
    "F": ["######", "##....", "##....", "#####.", "##....", "##....", "##...."],
    "G": [".####.", "##..##", "##....", "##.###", "##..##", "##..##", ".#####"],
    "H": ["##..##", "##..##", "##..##", "######", "##..##", "##..##", "##..##"],
    "I": ["######", "..##..", "..##..", "..##..", "..##..", "..##..", "######"],
    "J": ["..####", "....##", "....##", "....##", "##..##", "##..##", ".####."],
    "K": ["##..##", "##.##.", "####..", "###...", "####..", "##.##.", "##..##"],
    "L": ["##....", "##....", "##....", "##....", "##....", "##....", "######"],
    "M": ["##...##", "###.###", "#######", "##.#.##", "##...##", "##...##", "##...##"],
    "N": ["##...##", "###..##", "####.##", "##.####", "##..###", "##...##", "##...##"],
    "O": [".####.", "##..##", "##..##", "##..##", "##..##", "##..##", ".####."],
    "P": ["#####.", "##..##", "##..##", "#####.", "##....", "##....", "##...."],
    "Q": [".####.", "##..##", "##..##", "##..##", "##.###", "##..##", ".###.#"],
    "R": ["#####.", "##..##", "##..##", "#####.", "####..", "##.##.", "##..##"],
    "S": [".#####", "##....", "##....", ".####.", "....##", "....##", "#####."],
    "T": ["######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."],
    "U": ["##..##", "##..##", "##..##", "##..##", "##..##", "##..##", ".####."],
    "V": ["##..##", "##..##", "##..##", "##..##", "##..##", ".####.", "..##.."],
    "W": ["##...##", "##...##", "##...##", "##.#.##", "#######", "###.###", "##...##"],
    "X": ["##..##", "##..##", ".####.", "..##..", ".####.", "##..##", "##..##"],
    "Y": ["##..##", "##..##", "##..##", ".####.", "..##..", "..##..", "..##.."],
    "Z": ["######", "....##", "...##.", "..##..", ".##...", "##....", "######"],
    "0": [".####.", "##..##", "##.###", "######", "###.##", "##..##", ".####."],
    "1": ["..##..", ".###..", "..##..", "..##..", "..##..", "..##..", ".####."],
    "2": [".####.", "##..##", "....##", "..###.", ".##...", "##....", "######"],
    "3": ["######", "...##.", "..##..", ".####.", "....##", "##..##", ".####."],
    "4": ["...##.", "..###.", ".####.", "##.##.", "######", "...##.", "...##."],
    "5": ["######", "##....", "#####.", "....##", "....##", "##..##", ".####."],
    "6": ["..###.", ".##...", "##....", "#####.", "##..##", "##..##", ".####."],
    "7": ["######", "##..##", "....##", "...##.", "..##..", "..##..", "..##.."],
    "8": [".####.", "##..##", "##..##", ".####.", "##..##", "##..##", ".####."],
    "9": [".####.", "##..##", "##..##", ".#####", "....##", "...##.", ".###.."],
    "!": ["##", "##", "##", "##", "##", "..", "##"],
    "?": [".####.", "##..##", "....##", "...##.", "..##..", "......", "..##.."],
    "-": ["....", "....", "....", "####", "....", "....", "...."],
    ".": ["..", "..", "..", "..", "..", "##", "##"],
}


def _pixel_path(text: str, p: float) -> tuple:
    """SVG path data for `text` in the chunky face, one rectangle per run of
    pixels; returns (d, width in cells)."""
    d, cx = [], 0
    for ch in text.upper():
        if ch == " ":
            cx += 3
            continue
        g = GLYPHS.get(ch, GLYPHS["?"])
        for r, row in enumerate(g):
            c = 0
            while c < len(row):
                if row[c] != "#":
                    c += 1
                    continue
                c2 = c
                while c2 < len(row) and row[c2] == "#":
                    c2 += 1
                d.append(f"M{(cx + c) * p:g} {r * p:g}h{(c2 - c) * p:g}v{p:g}h{-(c2 - c) * p:g}z")
                c = c2
        cx += len(g[0]) + 1
    return "".join(d), max(0, cx - 1)


def _pixel_width(text: str) -> int:
    return _pixel_path(text, 1)[1]


def _pixel_title(text: str, cx: float, y: float, p: float, face: str = WHITE, depth: int = 1) -> str:
    """The chunky title: a face and a stepped extrusion down-right."""
    d, wc = _pixel_path(text, p)
    w, h = wc * p + depth * p, 7 * p + depth * p
    layers = "".join(f'<path d="{d}" fill="{CYAN_D}" transform="translate({k * p:g} {k * p:g})"/>'
                     for k in range(depth, 0, -1))
    return (f'<svg class="abs" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" '
            f'shape-rendering="crispEdges" style="left:{cx - wc * p / 2:.0f}px;top:{y:.0f}px;overflow:visible">'
            f'{layers}<path d="{d}" fill="{face}"/></svg>')


def _bitmap(rows: list, colors: dict, x: float, y: float, p: float, extra: str = "") -> str:
    """A little pixel picture: rows of characters, each a colour from `colors`."""
    d = {}
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            k = row[c]
            if k not in colors:
                c += 1
                continue
            c2 = c
            while c2 < len(row) and row[c2] == k:
                c2 += 1
            d.setdefault(k, []).append(f"M{c * p:g} {r * p:g}h{(c2 - c) * p:g}v{p:g}h{-(c2 - c) * p:g}z")
            c = c2
    w, h = max(len(r) for r in rows) * p, len(rows) * p
    paths = "".join(f'<path d="{"".join(v)}" fill="{colors[k]}"/>' for k, v in d.items())
    return (f'<svg class="abs" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" '
            f'shape-rendering="crispEdges" style="left:{x:.0f}px;top:{y:.0f}px;{extra}">{paths}</svg>')


def _cake(age: int) -> tuple:
    """A pixel birthday cake with `age` candles: (rows, rows with the flames'
    other frame) -- the flames flicker between the two."""
    n = max(1, min(age, 12))
    wdt = 2 * n + 3
    pad = lambda s: s.ljust(wdt + 4, ".")
    flame_a = "." * 2 + "".join(".f" for _ in range(n)) + "."
    flame_b = "." * 2 + "".join(".g" for _ in range(n)) + "."
    tip_a = "." * 2 + "".join(".F" for _ in range(n)) + "."
    tip_b = "." * 2 + "".join(".G" for _ in range(n)) + "."
    candle = "." * 2 + "".join(".w" for _ in range(n)) + "."
    rows = [tip_a, flame_a, candle, candle, candle]
    alt = [tip_b, flame_b, candle, candle, candle]
    icing = ".." + "i" * wdt
    drips = ".." + "".join("i" if (k % 4 in (0, 1)) else "c" for k in range(wdt))
    body = ".." + "c" * wdt
    band = ".." + "".join("l" if k % 2 == 0 else "c" for k in range(wdt))
    plate = "p" * (wdt + 4)
    common = [icing, drips, body, body, band, body, body, plate]
    rows = [pad(r) for r in rows + common]
    alt = [pad(r) for r in alt + common]
    return rows, alt


CAKE_COLORS = {"f": LIME, "F": "#FFFFFF", "g": "#FFFFFF", "G": LIME, "w": WHITE, "i": WHITE,
               "c": CYAN, "l": LIME, "p": "#8C97A3"}


# ------------------------------------------------------------------ the cabinet (static)

CSS = """
.apx{font-family:'VT323',monospace;line-height:1;white-space:nowrap;letter-spacing:0}
@keyframes actype{from{clip-path:inset(-25% 100% -25% 0)}to{clip-path:inset(-25% 0 -25% 0)}}
@keyframes accur{from{transform:translateX(0)}to{transform:translateX(var(--cw))}}
@keyframes acdrop{0%{transform:translateY(-56px)}62%{transform:translateY(0)}80%{transform:translateY(-9px)}
  100%{transform:translateY(0)}}
@keyframes achop{0%,100%{transform:translateY(0)}45%{transform:translateY(-34px)}}
.acmos{position:absolute;left:0;top:0;width:100%;height:100%;image-rendering:pixelated}
.acsp{position:relative;display:inline-block;line-height:0}
"""


def _cabinet() -> str:
    """Everything that never moves: the room, the cabinet's side, the marquee,
    the bezel round the tube, the lower bezel with its speakers, the control
    panel and the coin door. Only the tube's picture and the code sign are
    content; the rest is decoration (data-safe="ignore")."""
    plastic = tex("arcade-plastic.jpg")
    metal = tex("arcade-metal.jpg")
    grain = tex("arcade-grain.png")
    x0, y0, x1, y1 = SCR
    L = []
    # the room behind, and the cabinet's right side receding from the camera
    L.append('<div class="full" style="background:linear-gradient(180deg,#0d0d12,#08080b 60%,#101014)"></div>')
    L.append(f'<div class="abs" data-safe="ignore" style="left:934px;top:0;width:146px;height:1920px;'
             f'clip-path:polygon(0 4px,100% 70px,100% 1920px,0 1920px);'
             f'background:linear-gradient(90deg,rgba(0,0,0,0),rgba(0,0,0,.55)),'
             f'repeating-linear-gradient(-58deg,transparent 0 150px,{LIME} 150px 186px,transparent 186px 204px,'
             f'{WHITE} 204px 222px,transparent 222px 240px,{CYAN} 240px 276px,transparent 276px 520px),'
             f'url({plastic}) 0 0/256px 256px"></div>')
    L.append('<div class="abs" data-safe="ignore" style="left:934px;top:0;width:146px;height:1920px;'
             'clip-path:polygon(0 4px,100% 70px,100% 1920px,0 1920px);'
             'background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(0,0,0,.35) 70%,rgba(0,0,0,.6))"></div>')
    # the front face: moulded plastic, lit from above
    L.append(f'<div class="abs" data-safe="ignore" style="left:16px;top:6px;width:{FACE_R - 16}px;height:1914px;'
             f'background:linear-gradient(180deg,rgba(255,255,255,.035),rgba(255,255,255,0) 30%,'
             f'rgba(0,0,0,.25) 100%),url({plastic}) 0 0/256px 256px"></div>')
    # T-moulding down both edges of the front (lime, rounded, catching the light)
    for x in (2, FACE_R):
        L.append(f'<div class="abs" data-safe="ignore" style="left:{x}px;top:6px;width:16px;height:1914px;'
                 f'background:linear-gradient(90deg,#9fb31f,{LIME} 30%,#f6ffb0 48%,{LIME} 62%,#8a9c16);'
                 f'box-shadow:0 0 0 1px rgba(0,0,0,.5)"></div>')

    # ---- the marquee: a printed, backlit panel between two metal strips
    L.append(f'<div class="abs" data-safe="ignore" style="left:30px;top:20px;width:878px;height:208px;'
             f'background:#060607;box-shadow:0 10px 16px rgba(0,0,0,.6);border-radius:4px"></div>')
    title_w = 820
    L.append(f'<div class="abs" data-safe="ignore" style="left:38px;top:40px;width:862px;height:168px;'
             f'background:#07080a;overflow:hidden">'
             # speed stripes either side of the title, printed flat
             f'<div class="abs" style="left:0;top:34px;width:862px;height:100px;background:'
             f'linear-gradient(180deg,transparent 0 8px,{CYAN} 8px 20px,transparent 20px 30px,{WHITE} 30px 36px,'
             f'transparent 36px 64px,{WHITE} 64px 70px,transparent 70px 80px,{CYAN} 80px 92px,transparent 92px)"></div>'
             f'<div class="abs" style="left:96px;top:10px;width:670px;height:148px;background:#07080a"></div>'
             f'<div class="abs" style="left:0;top:0;width:862px;text-align:center;font-family:\'Archivo Black\';'
             f'font-size:94px;line-height:168px;letter-spacing:.01em;color:{LIME};'
             f'text-shadow:3px 3px 0 #07080a,7px 7px 0 {CYAN},8px 8px 0 {CYAN}">ON THIS DAY</div>'
             # the tube behind the print is brighter in the middle than at the ends
             f'<div class="abs" style="inset:0;background:linear-gradient(90deg,rgba(0,0,0,.42),rgba(0,0,0,0) 22%,'
             f'rgba(0,0,0,0) 78%,rgba(0,0,0,.42)),url({grain}) 0 0/256px 256px;opacity:.9"></div>'
             f'</div>')
    for yy in (26, 206):
        L.append(f'<div class="abs" data-safe="ignore" style="left:34px;top:{yy}px;width:870px;height:16px;'
                 f'background:linear-gradient(180deg,rgba(255,255,255,.35),rgba(255,255,255,0) 40%,rgba(0,0,0,.35)),'
                 f'url({metal}) 0 0/512px 16px;box-shadow:0 2px 3px rgba(0,0,0,.6)"></div>')
        for sx in (60, 468, 876):
            L.append(f'<div class="abs" data-safe="ignore" style="left:{sx - 4}px;top:{yy + 4}px;width:8px;'
                     f'height:8px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#e9ecef,#6b7078 70%)">'
                     f'</div>')

    # ---- the bezel: a moulded surround with a lip round the tube
    L.append(f'<div class="abs" data-safe="ignore" style="left:{x0 - 14}px;top:{y0 - 14}px;width:{x1 - x0 + 28}px;'
             f'height:{y1 - y0 + 28}px;border-radius:{SCR_RAD + 14}px;background:#101013;'
             f'box-shadow:inset 0 2px 1px rgba(255,255,255,.10),inset 0 -2px 2px rgba(0,0,0,.6),'
             f'0 0 0 2px rgba(0,0,0,.55),0 6px 10px rgba(0,0,0,.35)"></div>')
    # the glass: CRT black, a touch lighter in the middle of the tube
    L.append(f'<div class="abs" data-safe="ignore" style="left:{x0}px;top:{y0}px;width:{x1 - x0}px;'
             f'height:{y1 - y0}px;border-radius:{SCR_RAD}px;background:radial-gradient(ellipse 80% 70% at 50% 48%,'
             f'#0b0d0e,#060707 70%,#030303)"></div>')

    # ---- the lower bezel: two speakers either side of the code sign
    for cx in (98, 838):
        L.append(f'<div class="abs" data-safe="ignore" style="left:{cx - 62}px;top:{1326 - 62}px;width:124px;'
                 f'height:124px;border-radius:50%;background:radial-gradient(circle,#2a2b30 0 1.7px,transparent 2.3px) '
                 f'0 0/9px 9px,radial-gradient(circle at 50% 40%,#141417,#08080a);'
                 f'box-shadow:0 0 0 5px #1d1e22,0 0 0 6px rgba(255,255,255,.07),inset 0 6px 12px rgba(0,0,0,.8),'
                 f'0 6px 10px rgba(0,0,0,.5)"></div>')
    # the recess the code sign sits in
    sx, sy, sw, sh = SIGN
    L.append(f'<div class="abs" data-safe="ignore" style="left:{sx - 10}px;top:{sy - 8}px;width:{sw + 20}px;'
             f'height:{sh + 16}px;border-radius:18px;background:#0b0b0d;'
             f'box-shadow:inset 0 5px 10px rgba(0,0,0,.85),0 1px 0 rgba(255,255,255,.06)"></div>')

    # ---- the control panel: a shelf lit from above, a stick and six buttons
    cp_top, cp_front = 1432, 1660
    L.append(f'<div class="abs" data-safe="ignore" style="left:16px;top:{cp_top}px;width:{FACE_R - 16}px;'
             f'height:{cp_front - cp_top}px;background:linear-gradient(180deg,rgba(255,255,255,.02),'
             f'rgba(255,255,255,.10) 75%,rgba(255,255,255,.14)),'
             f'repeating-linear-gradient(90deg,transparent 0 118px,rgba(63,211,238,.22) 118px 122px,transparent 122px 126px,'
             f'rgba(232,255,58,.18) 126px 128px),url({plastic}) 0 0/256px 256px;'
             f'box-shadow:0 -10px 18px rgba(0,0,0,.55)"></div>')
    L.append(f'<div class="abs" data-safe="ignore" style="left:16px;top:{cp_front}px;width:{FACE_R - 16}px;'
             f'height:14px;background:linear-gradient(180deg,#f6ffb0,{LIME} 40%,#7d8e12)"></div>')
    L.append(f'<div class="abs" data-safe="ignore" style="left:16px;top:{cp_front + 14}px;width:{FACE_R - 16}px;'
             f'height:70px;background:linear-gradient(180deg,#1b1b20,#0d0d10);'
             f'box-shadow:0 14px 22px rgba(0,0,0,.7)"></div>')
    # the stick: its shadow, the dust washer, the shaft, the ball
    jx, jy = 210, 1612
    L.append(f'<div class="abs" data-safe="ignore" style="left:{jx - 20}px;top:{jy - 26}px;width:150px;height:56px;'
             f'border-radius:50%;background:radial-gradient(closest-side,rgba(0,0,0,.55),rgba(0,0,0,0));'
             f'transform:skewX(-35deg)"></div>')
    L.append(f'<div class="abs" data-safe="ignore" style="left:{jx - 56}px;top:{jy - 16}px;width:112px;height:34px;'
             f'border-radius:50%;background:radial-gradient(ellipse at 50% 30%,#2b2c31,#0a0a0c 70%);'
             f'box-shadow:0 3px 4px rgba(0,0,0,.6)"></div>')
    L.append(f'<div class="abs" data-safe="ignore" style="left:{jx - 11}px;top:{jy - 96}px;width:22px;height:96px;'
             f'background:linear-gradient(90deg,#3a3c42,#b9bdc4 35%,#5a5d64 60%,#1c1d21)"></div>')
    L.append(f'<div class="abs" data-safe="ignore" style="left:{jx - 50}px;top:{jy - 190}px;width:100px;height:100px;'
             f'border-radius:50%;background:radial-gradient(circle at 36% 30%,#ffffff 0,#dffcff 4%,{CYAN} 22%,'
             f'#1b8ea3 62%,#0b3f4a 100%);box-shadow:0 8px 10px rgba(0,0,0,.45)"></div>')
    for i, (bx, by, col) in enumerate([(420, 1532, CYAN), (530, 1512, CYAN), (640, 1502, WHITE),
                                       (440, 1604, WHITE), (550, 1584, CYAN), (660, 1574, CYAN)]):
        dark = "#16707f" if col == CYAN else "#9aa3ab"
        L.append(f'<div class="abs" data-safe="ignore" style="left:{bx - 48}px;top:{by - 22}px;width:96px;height:52px;'
                 f'border-radius:50%;background:#050506;box-shadow:0 6px 8px rgba(0,0,0,.55)"></div>'
                 f'<div class="abs" data-safe="ignore" style="left:{bx - 40}px;top:{by - 26}px;width:80px;height:44px;'
                 f'border-radius:50%;background:radial-gradient(ellipse at 45% 30%,#ffffff 0,{col} 34%,{dark} 100%);'
                 f'box-shadow:inset 0 -6px 0 {dark}"></div>')
    # a white start button, top right of the panel
    L.append('<div class="abs" data-safe="ignore" style="left:792px;top:1478px;width:58px;height:34px;border-radius:50%;'
             'background:#050506;box-shadow:0 4px 6px rgba(0,0,0,.5)"></div>'
             f'<div class="abs" data-safe="ignore" style="left:797px;top:1474px;width:48px;height:28px;border-radius:50%;'
             f'background:radial-gradient(ellipse at 45% 30%,#fff,{WHITE} 40%,#8f979f);box-shadow:inset 0 -4px 0 #8f979f">'
             f'</div>')
    # the coin door: a brushed plate with two slots and their return buttons
    L.append(f'<div class="abs" data-safe="ignore" style="left:300px;top:1790px;width:336px;height:170px;'
             f'border-radius:8px;background:linear-gradient(180deg,rgba(255,255,255,.18),rgba(0,0,0,.25)),'
             f'url({metal}) 0 0/512px 48px;box-shadow:0 6px 12px rgba(0,0,0,.7),inset 0 0 0 2px rgba(0,0,0,.35)">'
             + "".join(f'<div class="abs" style="left:{x}px;top:26px;width:92px;height:118px;border-radius:6px;'
                       f'background:linear-gradient(180deg,#d4d8dd,#8b9098);box-shadow:inset 0 0 0 2px rgba(0,0,0,.3),'
                       f'0 2px 3px rgba(0,0,0,.4)"><div class="abs" style="left:40px;top:14px;width:12px;height:52px;'
                       f'border-radius:3px;background:#050506;box-shadow:inset 0 2px 3px #000"></div>'
                       f'<div class="abs" style="left:26px;top:80px;width:40px;height:26px;border-radius:4px;'
                       f'background:linear-gradient(180deg,#2c2d31,#0d0d0f)"></div></div>' for x in (48, 196))
             + '</div>')
    return "".join(L)


def _crt_overlay() -> str:
    """What the tube lays over its picture: scanlines, a faint RGB grille and
    grain (one tile), the curve darkening towards the edges and corners, the
    bezel's lip shading the glass, and a faint reflection. Static."""
    x0, y0, x1, y1 = SCR
    w, h = x1 - x0, y1 - y0
    return (f'<div class="abs" data-safe="ignore" style="left:{x0}px;top:{y0}px;width:{w}px;height:{h}px;'
            f'border-radius:{SCR_RAD}px;background:url({tex("arcade-crt.png")}) 0 0/240px 240px,'
            f'radial-gradient(ellipse 72% 64% at 50% 48%,rgba(0,0,0,0) 62%,rgba(0,0,0,.34) 100%);'
            f'box-shadow:inset 0 0 22px 4px rgba(0,0,0,.9),inset 0 10px 18px rgba(0,0,0,.5)"></div>'
            f'<div class="abs" data-safe="ignore" style="left:{x0}px;top:{y0}px;width:{w}px;height:{h}px;'
            f'border-radius:{SCR_RAD}px;background:linear-gradient(118deg,rgba(255,255,255,.055) 0,'
            f'rgba(255,255,255,.03) 17%,rgba(255,255,255,0) 17.3%),'
            f'radial-gradient(ellipse 40% 26% at 26% 12%,rgba(255,255,255,.035),rgba(255,255,255,0))"></div>')


def _sign(tr: _Tracks, lit: list) -> str:
    """USE CODE: BAD on the cabinet's LED sign under the tube: lime letters on
    the dark display, and in the outro the sign switched on -- a lime face with
    the letters in black. The outer box is the sign itself, unrotated: that is
    what the safe-zone check measures."""
    sx, sy, sw, sh = SIGN
    dots = ("radial-gradient(circle,#17191a 0 1.9px,transparent 2.4px) 0 0/8px 8px,"
            "linear-gradient(180deg,#060707,#0a0b0b)")
    fx, fy, fw, fh = 16, 16, sw - 32, sh - 32             # the display's face inside the housing
    bad_s, use_s, tag_s = 172, 58, 32
    col_w = 9 * EM * use_s                                  # "USE CODE:"
    bad_w = 3 * EM * bad_s
    gap = 34
    lx = (fw - col_w - gap - bad_w) / 2
    bx = lx + col_w + gap
    bad_top = (fh - CAP * bad_s) / 2 - (BASE - CAP) * bad_s   # BAD's capitals centred on the face
    use_top = bad_top + (BASE - CAP) * bad_s + 6 - (BASE - CAP) * use_s
    tag_top = bad_top + BASE * bad_s - BASE * tag_s + 2        # #EpicPartner on BAD's baseline

    def face(bg: str, fg: str, sub: str, vis: str = "") -> str:
        return (f'<div class="abs" style="left:{fx}px;top:{fy}px;width:{fw}px;height:{fh}px;border-radius:6px;'
                f'background:{bg};overflow:hidden;box-shadow:inset 0 0 0 2px rgba(0,0,0,.85),'
                f'inset 0 4px 10px rgba(0,0,0,.6);{vis}">'
                + _t("USE CODE:", lx, use_top, use_s, fg)
                + _t("#EpicPartner", lx + 2, tag_top, tag_s, sub)
                + _t("BAD", bx, bad_top, bad_s, fg)
                + '</div>')

    screws = "".join(f'<i class="abs" style="left:{x}px;top:{y}px;width:9px;height:9px;border-radius:50%;'
                     f'background:radial-gradient(circle at 35% 35%,#e3e6ea,#5f646b 75%);'
                     f'box-shadow:0 1px 1px rgba(0,0,0,.7)"></i>'
                     for x, y in ((5, 5), (sw - 14, 5), (5, sh - 14), (sw - 14, sh - 14)))
    return (f'<div class="abs" data-safe="key" data-name="code" style="left:{sx}px;top:{sy}px;width:{sw}px;'
            f'height:{sh}px">'
            f'<div class="abs" style="inset:0;border-radius:12px;background:linear-gradient(180deg,#2a2b30,#141417);'
            f'box-shadow:0 12px 18px rgba(0,0,0,.6),0 2px 3px rgba(0,0,0,.7),inset 0 1px 0 rgba(255,255,255,.14),'
            f'inset 0 -2px 0 rgba(0,0,0,.5)"></div>'
            + face(dots, LIME, "#c9d0c4")
            + (face(LIME, INK, "#2b3000", _anim(tr.vis(lit))) if lit else "")
            + screws + '</div>')


# ------------------------------------------------------------------ the cosmetics

MOSAIC_JS = """<script>(() => {
  // After cc_looks.PREP_JS has trimmed the art: each canvas[data-mos] gets the
  // picture of the image it names at data-px pixels across, alpha cut hard, so
  // it reads as a blocky low-res sprite when shown with image-rendering:pixelated.
  const prev = window.__ready;
  window.__ready = (async () => {
    if (prev) { await prev; }
    for (const cv of document.querySelectorAll('canvas[data-mos]')) {
      try {
        const img = document.getElementById(cv.dataset.mos);
        if (!img) continue;
        if (img.decode) { try { await img.decode(); } catch (e) {} }
        const w = img.naturalWidth, h = img.naturalHeight, bw = img.offsetWidth, bh = img.offsetHeight;
        if (!w || !h || !bw || !bh) continue;
        const cols = +cv.dataset.px, rows = Math.max(1, Math.round(cols * bh / bw));
        cv.width = cols; cv.height = rows;
        const g = cv.getContext('2d');
        g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
        const s = Math.min(bw / w, bh / h), k = cols / bw, dw = w * s * k, dh = h * s * k;
        g.drawImage(img, (cols - dw) / 2, rows - dh, dw, dh);
        const im = g.getImageData(0, 0, cols, rows), d = im.data;
        for (let i = 3; i < d.length; i += 4) { d[i] = d[i] > 96 ? 255 : 0; }
        g.putImageData(im, 0, 0);
      } catch (e) {}
    }
  })();
})();</script>"""


def _sprite(tr: _Tracks, uid: str, art: str, it: dict, cx: float, bottom: float, h: float, maxw: float,
            sharp: list, mosaic: list = (), extra: str = "") -> str:
    """A cosmetic standing with its feet at (cx, bottom): the real picture inside
    the `sharp` windows, and the low-res frames `mosaic` = [(px, windows)...]."""
    box = (f'left:{cx - maxw / 2:.0f}px;top:{bottom - h:.0f}px;width:{maxw:.0f}px;height:{h:.0f}px;'
           f'display:flex;justify-content:center;align-items:flex-end')
    if not art:
        return (f'<div class="abs" style="{box}"><div class="abs apx" style="left:{maxw * .12:.0f}px;'
                f'top:{h * .14:.0f}px;width:{maxw * .76:.0f}px;height:{h * .8:.0f}px;border:6px dashed {CYAN};'
                f'display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;'
                f'white-space:normal;text-align:center;color:{WHITE};{_anim(tr.vis(sharp))}">'
                f'<div style="font-size:{h * .3:.0f}px;color:{CYAN}">?</div>'
                f'<div style="font-size:34px;line-height:1.05;padding:0 12px;overflow-wrap:anywhere">'
                f'{esc(it["name"].upper())}</div></div></div>')
    trim = trim_for(it)
    tr_attr = ' data-trim="figure"' if trim == "figure" else " data-trim"
    img = (f'<img id="{uid}"{tr_attr} data-name="{esc(it["name"])}" src="{art}" style="display:block;'
           f'height:{h:.0f}px;max-width:{maxw:.0f}px;object-fit:contain;object-position:50% 100%;'
           f'{_anim(tr.vis(sharp))}">')
    mos = "".join(f'<canvas class="acmos" data-mos="{uid}" data-px="{px}" width="1" height="1" '
                  f'style="{_anim(tr.vis(w))}"></canvas>' for px, w in mosaic)
    return f'<div class="abs" style="{box}"><div class="acsp" style="{extra}">{img}{mos}</div></div>'


def _rez_in(t: float, levels=(7, 14, 28), step: float = .1) -> tuple:
    """(mosaic windows, when it's sharp) for a sprite resolving from t."""
    return [(px, [(t + i * step, t + (i + 1) * step)]) for i, px in enumerate(levels)], t + len(levels) * step


def _rez_out(t: float, levels=(28, 14, 7), step: float = .067) -> list:
    return [(px, [(t + i * step, t + (i + 1) * step)]) for i, px in enumerate(levels)]


def _merge_mosaic(*parts) -> list:
    out = {}
    for part in parts:
        for px, w in part:
            out.setdefault(px, []).extend(w)
    return sorted(out.items())


# ------------------------------------------------------------------ the screens

def _kind(it: dict) -> str:
    return " ".join(x for x in ((it.get("rarity_label") or "").strip(), (it.get("type") or "").strip()) if x).upper()


def _floor(cx: float, y: float, w: float) -> str:
    """A flat pixel shadow under a sprite's feet."""
    return "".join(f'<div class="abs" style="left:{cx - w * k / 2:.0f}px;top:{y + i * 8:.0f}px;width:{w * k:.0f}px;'
                   f'height:8px;background:#0e3a44"></div>' for i, k in enumerate((.62, 1, .7)))


def _panel_frame(x0: float, y0: float, x1: float, y1: float, label: str) -> str:
    """PLAYER SELECT's frame: a thick and a thin cyan line with notched corners,
    the label set into the top edge."""
    lw = len(label) * EM * 34 + 28
    frame = (f'<div class="abs" style="left:{x0}px;top:{y0}px;width:{x1 - x0}px;height:{y1 - y0}px;'
             f'border:6px solid {CYAN};clip-path:polygon(12px 0,calc(100% - 12px) 0,100% 12px,100% calc(100% - 12px),'
             f'calc(100% - 12px) 100%,12px 100%,0 calc(100% - 12px),0 12px)"></div>'
             f'<div class="abs" style="left:{x0 + 12}px;top:{y0 + 12}px;width:{x1 - x0 - 24}px;height:{y1 - y0 - 24}px;'
             f'border:2px solid {CYAN_D}"></div>'
             f'<div class="abs" style="left:{x0 + 26}px;top:{y0 - 4}px;width:{lw:.0f}px;height:14px;background:#050607">'
             f'</div>')
    return frame + _t(label, x0 + 40, y0 - 17, 34, CYAN)


def _year_drop(year: int, x: float, y: float, size: float, t: float, until: float, tr: _Tracks,
               color: str = LIME) -> str:
    """The year's digits dropping into place one after another."""
    out = []
    for i, ch in enumerate(str(year)):
        t_i = t + i * .07
        out.append(f'<div class="abs apx" style="left:{x + i * EM * size:.0f}px;top:{y:.0f}px;font-size:{size:.0f}px;'
                   f'color:{color};{_anim(tr.vis([(t_i, until)]), _a("acdrop", t_i, .34, "steps(6,end)"))}">'
                   f'{ch}</div>')
    return "".join(out)


def _stage(ctx, tr: _Tracks, k: int, rd: dict, it: dict, debut: bool, t0: float, t1: float,
           typing: tuple, cues: list) -> str:
    """One year's screen (everything but the table and the status line, which
    stay up): the PLAYER SELECT panel with the outfit resolving, its rarity and
    type and the banner, and the year and name in the right-hand column."""
    y = rd["year"]
    px0, py0, px1, py1 = PANEL
    pcx = (px0 + px1) / 2
    clear = t1 - .12                                   # the column clears a moment before the next year
    html = [_panel_frame(px0, py0, px1, py1, "PLAYER SELECT")]
    # the outfit: blocky for a few frames, then sharp; blocky again on its way out
    mos_in, t_sharp = _rez_in(t0 + .06)
    mos = _merge_mosaic(mos_in, _rez_out(t1 - .3))
    feet = 1010
    html.append(_floor(pcx, feet - 6, 250))
    html.append(_sprite(tr, f"acs{k}", ctx.art(it), it, pcx, feet, 630, px1 - px0 - 56,
                        [(t_sharp, t1 - .3)], mos, extra=_anim(_a("achop", t0 + 3.5, .36, "steps(6,end)"))))
    # rarity and type, then the banner
    kind = _kind(it)
    ks, klines = _fit(kind, px1 - px0 - 60, 34, 2, 22)
    t_kind = typing[0] + typing[1] + .12
    ky = 1030
    for j, line in enumerate(klines):
        html.append(_typed(line, pcx - len(line) * EM * ks / 2, ky + j * ks * 1.06, ks, CYAN, t_kind + j * .12,
                           .018, _anim_vis(tr, [(t_kind + j * .12, clear)])))
    t_ban = t_kind + .45
    by = 1116
    if debut:
        text = "FIRST DAY IN THE SHOP!"
        bs = 36
        bw = len(text) * EM * bs + 30
        on = _blink(t_ban, clear, .5, .22)
        html.append(f'<div class="abs" style="left:{pcx - bw / 2:.0f}px;top:{by:.0f}px;width:{bw:.0f}px;height:54px;'
                    f'background:{LIME};{_anim(tr.vis(on))}"></div>')
        html.append(_tc(text, pcx, by + 27 - (BASE - CAP / 2) * bs, bs, INK, _anim(tr.vis(on))))
        cues.append((t_ban, "ding"))
    else:
        text = "IN THE ITEM SHOP THAT DAY"
        bs = min(34, (px1 - px0 - 50) / (len(text) * EM))
        html.append(_tc(text, pcx, by + 25 - (BASE - CAP / 2) * bs, bs, WHITE, _anim(tr.vis([(t_ban, clear)]))))
        cues.append((t_ban, "pop"))
    # the year, and the name typed into the right-hand column
    rx0, rx1 = RCOL
    html.append(_year_drop(y, rx0, YEAR_Y, YEAR_S, t0, clear, tr))
    ns, nlines = _fit(it["name"].upper(), rx1 - rx0, NAME_S, 1, 56)
    if len(nlines) > 1 or ns < 56:
        ns, nlines = _fit(it["name"].upper(), rx1 - rx0, NAME_S, 2, 30)
    t_type, dt = typing
    t_line = t_type
    for j, line in enumerate(nlines):
        html.append(_typed(line, rx0, NAME_Y + j * ns * 1.02, ns, WHITE, t_line, dt,
                           _anim_vis(tr, [(t_line, clear)])))
        t_line += (len(line) + 1) * dt
    cues += [(t0 + .06, "reveal"), (t_sharp, "click")]
    return "".join(html)


def _anim_vis(tr: _Tracks, windows: list) -> str:
    """A visibility track as an animation entry to add to another element's list."""
    return tr.vis(windows)


def _table(tr: _Tracks, rows: list, when_short: str, on: list, done_from: list, cues: list) -> str:
    """The high-score table. rows: [(year, name, t_start, t_end, typing or None)]
    -- a row lights up in lime for its stage while its name is typed in behind a
    blinking cursor, then stays in the table in white; the ones still to come
    are dashes. `on`: when the table is on screen."""
    rx0, rx1 = RCOL
    width = rx1 - rx0
    hdr = f"HIGH SCORES · {when_short}"
    out = [_t(hdr, rx0, TABLE_Y, 36, CYAN, _anim(tr.vis(on)))]
    top = TABLE_Y + 50

    def lay(size):
        y_col = 4 * EM * size + 16                                # the name column starts here
        name_w = width - y_col - 6
        layout = []
        for year, name, a, b, typing in rows:
            s, lines = _fit(name.upper(), name_w, size, 1, 30)
            if s < 30 or len(lines) > 1:
                s, lines = _fit(name.upper(), name_w, size, 2, 22)
            layout.append((s, lines))
        n_lines = sum(len(ls) for _, ls in layout)
        return y_col, name_w, layout, min(54.0, (FLOOR - top) / max(n_lines, 1))

    ROW = 40.0                                                    # as big as the room allows (36-40 px)
    for _ in range(4):
        y_col, name_w, layout, pitch = lay(ROW)
        if ROW <= pitch * .8 or ROW <= 30:
            break
        ROW = max(30.0, round(pitch * .8))
    y_col, name_w, layout, pitch = lay(ROW)
    y = top
    t_end_all = max(w[1] for w in on) if on else 0
    for (year, name, a, b, typing), (s, lines) in zip(rows, layout):
        h = pitch * len(lines)
        ry = y + (pitch - ROW) / 2
        past = [(max(b, on[0][0]), t_end_all)]
        future = [w for w in ((on[0][0], a),) if w[1] > w[0]]
        # still to come: dashes
        out.append(_t("----", rx0, ry, ROW, DIM, _anim(tr.vis(_clip(future, on)))))
        out.append(_t("." * min(14, int(name_w / (EM * ROW))), rx0 + y_col, ry, ROW, DIM,
                      _anim(tr.vis(_clip(future, on)))))
        # its stage: a lime bar, the year and the name typed in with a cursor
        if typing:
            live = _clip([(a, b)], on)
            out.append(f'<div class="abs" style="left:{rx0 - 8}px;top:{y + 2:.0f}px;width:{width + 12}px;'
                       f'height:{h - 4:.0f}px;background:{LIME};{_anim(tr.vis(live))}"></div>')
            out.append(_t(str(year), rx0, ry, ROW, INK, _anim(tr.vis(live))))
            t_type, dt = typing
            tl = t_type
            for j, line in enumerate(lines):
                ly = ry + j * pitch + (ROW - s) * .5
                t_done = tl + len(line) * dt
                last = j == len(lines) - 1
                cur = [(tl, t_done)] + (_blink(t_done, b - .12, .3, .22) if last else [])
                out.append(_typed(line, rx0 + y_col, ly, s, INK, tl, dt, _anim_vis(tr, _clip([(tl, b)], on)),
                                  cursor=INK, cur_vis=tr.vis(_clip(cur, on))))
                tl = t_done + dt
        # in the table
        out.append(_t(str(year), rx0, ry, ROW, CYAN, _anim(tr.vis(_clip(past, on)))))
        for j, line in enumerate(lines):
            out.append(_t(line, rx0 + y_col, ry + j * pitch + (ROW - s) * .5, s, WHITE,
                          _anim(tr.vis(_clip(past, on)))))
        y += h
    return "".join(out)


def _clip(windows: list, within: list) -> list:
    out = []
    for a, b in windows:
        for c, d in within:
            lo, hi = max(a, c), min(b, d)
            if hi > lo:
                out.append((lo, hi))
    return out


def _status(tr: _Tracks, stages: list, on: list) -> str:
    """STAGE k/n top left of the tube, and a pip per stage top right."""
    n = len(stages)
    out = [_t("STAGE", CX0, TOP, 46, WHITE, _anim(tr.vis(on)))]
    for k, (a, b) in enumerate(stages):
        w = _clip([(a, b)], on)
        out.append(_t(f"{k + 1}/{n}", CX0 + 6 * EM * 46, TOP, 46, LIME, _anim(tr.vis(w))))
    pw, gap = 24, 10
    x = CX1 - n * pw - (n - 1) * gap
    for k, (a, b) in enumerate(stages):
        px = x + k * (pw + gap)
        out.append(f'<div class="abs" style="left:{px}px;top:{TOP + 14}px;width:{pw}px;height:{pw}px;'
                   f'border:3px solid {DIM};{_anim(tr.vis(on))}"></div>')
        out.append(f'<div class="abs" style="left:{px}px;top:{TOP + 14}px;width:{pw}px;height:{pw}px;'
                   f'background:{LIME};{_anim(tr.vis(_clip([(a, on[-1][1])], on)))}"></div>')
    return "".join(out)


def _dissolve(tr: _Tracks, times: list, seed: int) -> str:
    """The tube's picture breaking up into black blocks and building back: for
    each switch t in `times`, the blocks cover it between t - .3 and t - .06,
    and clear again between t and t + .24."""
    x0, y0, x1, y1 = SCR
    cols, rows = 12, 14
    bw, bh = (x1 - x0) / cols, (y1 - y0) / rows
    rnd = random.Random(seed)
    out = []
    for r in range(rows):
        for c in range(cols):
            order = .62 * (c + r) / (cols + rows - 2) + .38 * rnd.random()
            wins = [(t - .3 + .24 * order, t + .24 * order) for t in times]
            out.append(f'<i class="abs" style="left:{x0 + c * bw:.1f}px;top:{y0 + r * bh:.1f}px;width:{bw + 1:.1f}px;'
                       f'height:{bh + 1:.1f}px;background:#050607;{_anim(tr.vis(wins))}"></i>')
    return "".join(out)


def _title(ctx, tr: _Tracks, lead: list, when_short: str, span: str, bday, cues: list) -> str:
    """Frame 0: the title screen, whole."""
    a, b = lead[0], lead[1]
    out = [_pixel_title("ON THIS DAY", MID, 300, 11)]
    # the two lead outfits facing off either side of the date
    col = 288
    feet = 1068
    for i, (rd, it, _) in enumerate((a, b)):
        cx = CX0 + col / 2 if i == 0 else CX1 - col / 2
        hop = _a("achop", .5 + i * .22, .36, "steps(6,end)")
        out.append(_floor(cx, feet - 6, 200))
        out.append(_sprite(tr, f"ach{i}", ctx.art(it), it, cx, feet, 628, col - 10, [(0, 2.45)],
                           _rez_out(2.45), extra=_anim(hop)))
        out.append(_tc(str(rd["year"]), cx, feet + 8, 44, LIME))
        cues.append((.5 + i * .22, "pop"))
    mon, dnum = when_short.split(" ")
    out.append(_tc(mon, MID, 420, 172, LIME))
    out.append(_tc(dnum, MID, 572, 172, LIME))
    if bday:
        out.append(_tc(span, MID, 760, 50, WHITE))
        out.append(_tc("FORTNITE", MID, 840, 58, WHITE))
        out.append(_tc(f"TURNS {bday['age']}!", MID, 900, 58, WHITE))
        line = f"BATTLE ROYALE CAME OUT ON THIS DAY IN {bday['year']}"
    else:
        out.append(_tc(span[:4], MID, 766, 64, WHITE))
        out.append(_tc("–", MID, 830, 64, WHITE))
        out.append(_tc(span[-4:], MID, 894, 64, WHITE))
        line = "ONE OUTFIT FROM THIS DATE, EVERY YEAR"
    ls, _ = _fit(line, CX1 - CX0 - 20, 36)
    out.append(_tc(line, MID, 1124, ls, CYAN))
    press = _blink(0, 1.9, .55, .3) + _blink(1.9, 2.5, .07, .07)
    out.append(_tc("PRESS START", MID, 1160, 40, WHITE, _anim(tr.vis(press))))
    cues += [(1.9, "click"), (2.45, "click")]
    return "".join(out)


def _bonus(tr: _Tracks, bday: dict, when: str, t0: float, t1: float, cues: list) -> str:
    """Sep 26: the BONUS STAGE -- Battle Royale's release day and a birthday cake."""
    clear = t1 - .12
    out = [_tc("BONUS STAGE", MID, 330, 46, CYAN, _anim(tr.vis(_blink(t0, clear, .6, .25))))]
    out.append(_tc("FORTNITE", MID, 392, 96, WHITE, _anim(tr.vis([(t0 + .15, clear)]),
                                                         _a("acdrop", t0 + .15, .34, "steps(6,end)"))))
    out.append(_tc("BATTLE ROYALE", MID, 486, 96, WHITE, _anim(tr.vis([(t0 + .3, clear)]),
                                                              _a("acdrop", t0 + .3, .34, "steps(6,end)"))))
    rel = f"RELEASED {when.upper()}, {bday['year']}"
    s1, _ = _fit(rel, CX1 - CX0 - 30, 48)
    out.append(_typed(rel, MID - len(rel) * EM * s1 / 2, 616, s1, LIME, t0 + .8, .03, tr.vis([(t0 + .8, clear)])))
    plat = "PC · PLAYSTATION 4 · XBOX ONE"
    s2, _ = _fit(plat, CX1 - CX0 - 30, 42)
    out.append(_typed(plat, MID - len(plat) * EM * s2 / 2, 680, s2, WHITE, t0 + 1.7, .025,
                      tr.vis([(t0 + 1.7, clear)])))
    rows, alt = _cake(bday["age"])
    p = 14
    cw = len(rows[0]) * p
    cx0 = MID - cw / 2
    t_cake = t0 + 2.5
    cake_body = _bitmap(rows[2:], CAKE_COLORS, cx0, 800 + 2 * p, p, _anim(tr.vis([(t_cake, clear)])))
    flames_a = _bitmap(rows[:2], CAKE_COLORS, cx0, 800, p,
                       _anim(tr.vis(_blink(t_cake + .35, clear, .18, .18))))
    flames_b = _bitmap(alt[:2], CAKE_COLORS, cx0, 800, p,
                       _anim(tr.vis(_blink(t_cake + .53, clear, .18, .18))))
    out += [cake_body, flames_a, flames_b]
    hb = f"HAPPY BIRTHDAY — {bday['age']} YEARS TODAY"
    s3, _ = _fit(hb, CX1 - CX0 - 60, 42)
    bw = len(hb) * EM * s3 + 36
    t_hb = t0 + 3.1
    on = _blink(t_hb, clear, .55, .2)
    out.append(f'<div class="abs" style="left:{MID - bw / 2:.0f}px;top:1112px;width:{bw:.0f}px;height:60px;'
               f'background:{LIME};{_anim(tr.vis(on))}"></div>')
    out.append(_tc(hb, MID, 1112 + 30 - (BASE - CAP / 2) * s3, s3, INK, _anim(tr.vis(on))))
    cues += [(t0 + .15, "pop"), (t0 + .3, "pop"), (t0 + .8, "tick"), (t0 + 1.7, "tick"), (t_cake, "reveal"),
             (t_hb, "ding")]
    return "".join(out)


def _outro(ctx, tr: _Tracks, picks: list, t: float, end: float, cues: list) -> str:
    """WHICH YEAR HAD THE BEST SHOP? -- the picks side by side with their years,
    a selection frame hopping between them."""
    out = []
    q1, q2 = "WHICH YEAR HAD", "THE BEST SHOP?"
    qs = 84
    out.append(_typed(q1, MID - len(q1) * EM * qs / 2, 300, qs, WHITE, t + .08, .032, tr.vis([(t + .08, end)])))
    out.append(_typed(q2, MID - len(q2) * EM * qs / 2, 388, qs, LIME, t + .08 + 15 * .032, .032,
                      tr.vis([(t + .08 + 15 * .032, end)])))
    n = len(picks)
    colw = (CX1 - CX0) / n
    feet, h = 1040, 520 if n == 3 else 560
    t_pick = t + .75
    boxes = []
    for i, (year, it) in enumerate(picks):
        cx = CX0 + colw * (i + .5)
        mos, t_sharp = _rez_in(t_pick + i * .22)
        out.append(f'<div class="abs" style="inset:0;{_anim(tr.vis([(t_pick + i * .22, end)]))}">'
                   f'{_floor(cx, feet - 6, colw * .7)}</div>')
        out.append(_sprite(tr, f"aco{i}", ctx.art(it), it, cx, feet, h, colw - 26, [(t_sharp, end)], mos))
        out.append(_tc(str(year), cx, feet + 26, 60, LIME, _anim(tr.vis([(t_sharp, end)]))))
        cues.append((t_pick + i * .22, "pop"))
        boxes.append(cx)
    # the selection frame hops between them
    t_sel = t_pick + n * .22 + .6
    hop = .75
    k = 0
    s = t_sel
    while s < end - .05:
        cx = boxes[k % n]
        e = min(end, s + hop)
        out.append(f'<div class="abs" style="left:{cx - colw / 2 + 6:.0f}px;top:{feet - h - 30:.0f}px;'
                   f'width:{colw - 12:.0f}px;height:{h + 120:.0f}px;border:6px solid {CYAN};'
                   f'clip-path:polygon(0 0,34% 0,34% 6px,66% 6px,66% 0,100% 0,100% 100%,66% 100%,66% calc(100% - 6px),'
                   f'34% calc(100% - 6px),34% 100%,0 100%);{_anim(tr.vis([(s, e)]))}"></div>')
        cues.append((s, "tick"))
        s += hop
        k += 1
    cues += [(t + .1, "tick")]
    return "".join(out)


# ------------------------------------------------------------------ the video

def on_this_day(ctx, rounds: list, bday: dict | None, lead: list, third) -> Comp:
    day = ctx.day
    when = day.strftime("%B %-d")                       # September 28
    when_short = day.strftime("%b %-d").upper()         # SEP 28
    years = ([bday["year"]] if bday else []) + [rd["year"] for rd, _, _ in rounds]
    n = len(years)
    r = max(R, (62.0 - 7.5 - HOOK) / n)
    content_end = HOOK + n * r
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    comp.css(CSS)
    tr = _Tracks(comp)
    cues = []
    span = f"{years[0]}–{years[-1]}"

    stages = [(HOOK + i * r, HOOK + (i + 1) * r) for i in range(n)]
    k0 = 1 if bday else 0                                # the first regular stage
    table_on = [(stages[k0][0], content_end)]
    status_on = [(HOOK, content_end)]

    # typing times: each name typed in from .32 s into its stage
    typing = {}
    for j, (rd, it, _) in enumerate(rounds):
        t0 = stages[k0 + j][0]
        nm = it["name"]
        dt = min(.06, 1.2 / max(len(nm), 1))
        typing[j] = (t0 + .32, dt)

    # ---- the cabinet, the tube's overlay and the code sign: the whole time
    comp.add(f'<div class="full" style="z-index:0">{_cabinet()}</div>')
    comp.add(PREP_JS)
    comp.add(MOSAIC_JS)
    lit_at = content_end + 1.1
    lit = [(lit_at, lit_at + .09), (lit_at + .2, lit_at + .28), (lit_at + .42, comp.duration + 9)]
    comp.add(f'<div class="full" style="z-index:60;pointer-events:none">{_crt_overlay()}</div>')
    comp.add(f'<div class="full" style="z-index:70">{_sign(tr, lit)}</div>')
    for t in (lit_at, lit_at + .2, lit_at + .42):
        comp.cue(t, "click")
    comp.cue(lit_at + .5, "ding")

    # ---- hook: the title screen (frame 0 is the thumbnail)
    hook_cues = []
    comp.scene(0, HOOK - .02, f'<div class="full">{_title(ctx, tr, lead, when_short, span, bday, hook_cues)}</div>',
               fade_in=.01, fade_out=.01, z=10)
    for c in hook_cues:
        comp.cue(*c)

    # ---- the stages
    screen = []
    screen.append(_status(tr, stages, status_on))
    rows = []
    if bday:
        rows.append((bday["year"], "BATTLE ROYALE", *stages[0], None))
    for j, (rd, it, debut) in enumerate(rounds):
        rows.append((rd["year"], it["name"], *stages[k0 + j], typing[j]))
    screen.append(_table(tr, rows, when_short, table_on, [], cues))
    comp.add(f'<div class="full" style="z-index:12">{"".join(screen)}</div>')
    for j, (rd, it, debut) in enumerate(rounds):
        t0, t1 = stages[k0 + j]
        sc = []
        html = _stage(ctx, tr, j, rd, it, debut, t0, t1, typing[j], sc)
        comp.scene(t0 - .02, t1, f'<div class="full">{html}</div>', fade_in=.01, fade_out=.01, z=14)
        for c in sc:
            comp.cue(*c)
        # a tick per letter typed (up to 14)
        t_type, dt = typing[j]
        nm = len(it["name"])
        for q in range(min(nm, 14)):
            comp.cue(t_type + (q + 1) * dt * nm / min(nm, 14), "tick")
        comp.cue(t1 - .3, "click")
    if bday:
        t0, t1 = stages[0]
        bc = []
        comp.scene(t0 - .02, t1, f'<div class="full">{_bonus(tr, bday, when, t0, t1, bc)}</div>',
                   fade_in=.01, fade_out=.01, z=14)
        for c in bc:
            comp.cue(*c)

    # ---- outro
    picks = []
    for rd, it, _ in lead:
        picks.append((rd["year"], it))
    if third is not None:
        y3 = next((rd["year"] for rd, it, _ in rounds if it is third), None)
        if y3 is None:
            y3 = next((rd["year"] for rd, it, _ in rounds if it.get("id") == third.get("id")), "")
        picks.append((y3, third))
    oc = []
    comp.scene(content_end, comp.duration, f'<div class="full">{_outro(ctx, tr, picks, content_end, comp.duration, oc)}</div>',
               fade_in=.01, fade_out=.01, z=14)
    for c in oc:
        comp.cue(*c)

    # ---- the picture breaking up between the title, the bonus stage, the table and the outro
    cuts = [HOOK] + ([stages[1][0]] if bday else []) + [content_end]
    comp.add(f'<div class="full" style="z-index:40">{_dissolve(tr, cuts, ctx.seed)}</div>')
    for t in cuts:
        comp.cue(t - .3, "static")
    for c in cues:
        comp.cue(*c)
    comp.cues.sort()
    return comp
