"""
POSTCARD -- On This Day, as vintage postcards and postage stamps on a
collector's desk: ink-blue leather, a lamp from the upper left.

    0:00  hook      a picture postcard, complete on frame 0: "Greetings from the
                    ITEM SHOP!" in big retro letters, a ribbon ON THIS DAY ·
                    SEP 28 · 2018–2025, the two lead outfits as a pair of stamps
                    under one postmark, and "one outfit from this date, every
                    year" in fountain pen. Beside it the lime airmail label
                    (USE CODE: BAD), and along the foot the stamp album with a
                    mount for every year. The card is nudged straight, the pen
                    underlines "every year", then the card is turned over...
    0:03  years     ...and its back is the first year. One postcard per year
                    (6.5 s, longer on a short day), each slid in on top of the
                    last: the outfit is a big perforated stamp in its rarity's
                    colour, the year printed on it where a stamp has its value;
                    a round postmark SEP 28 · 2019 is slammed over its corner;
                    the name is typed on the address line with the rarity and
                    type under it; a line in fountain pen ("its very first day
                    in the shop!" and a red NEW THAT DAY handstamp, or "in the
                    Item Shop that day"); and the used stamp slides into its
                    mount in the album, where the pen underlines its year.
    Sep 26          the first page is a FIRST DAY COVER lying on a postcard:
                    FORTNITE BATTLE ROYALE, released September 26, 2017, PC ·
                    PlayStation 4 · Xbox One, a commemorative stamp under a
                    FIRST DAY OF ISSUE postmark SEP 26 2017, and a red
                    9 YEARS TODAY handstamp on the card.
    0:55  outro     the back of a last postcard: "Which year had the best
                    shop?" in fountain pen, the lead picks as stamps and a
                    postmark with the date and the span; the album is full, and
                    the airmail label is pressed down once more.

Facts on screen are the classic format's: the date, each year, the item's name,
its rarity and type, "its very first day in the shop!" / NEW THAT DAY only when
the plan says it was, "in the Item Shop that day" otherwise, the span of years,
the birthday page on Sep 26 and the outro question with the lead picks. The
stamps' "ITEM SHOP" and the postmarks' ON THIS DAY are in-world print; no value
is printed on any stamp but its year, and no real postal service is named.

Layout (cc_safe): the lime label sits on the desk in the wide band above the
button rail (x 706-1018, y 290-530), above everything, and never moves or gets
covered. The postcard lies left of it (x 35-703 once turned), its words and the
stamp's picture inside x 60-900 / y 230-1420 (frame 0: from y 285), and the
album's mounts and years run along the foot of the box (y 1300-1420). Only the
desk, the card's airmail border and the album page's edges reach past it.

Render cost: one static desk, static props; cards move whole (one layer each)
and only small things animate on them. No SVG filters on anything that moves.
"""

import math
import random

from cc_looks import KIT_CSS, LIME, PREP_JS, pad_to, rough_line, tex, write_on
from cc_motion import RARITY, Comp, esc

HOOK = 3.0
R = 6.5
FONTS = ("Playfair Display", "Special Elite", "Caveat", "Oswald")

INK = "#221f29"                   # typewriter ribbon and postmark ink
PEN = "#1f2b6e"                   # fountain pen, blue-black
RED = "#c3322b"                   # red handstamp ink
PRINT = "#7a6b58"                 # small print on the card
AIR_RED, AIR_BLUE, LIP = "#c8352d", "#27468e", "#f3ecdc"
PAPER = "#fbf8f0"                 # stamp paper
NAVY = "#1f2f5c"                  # the first day cover's print

# The postcard: every card lies here (its box before its quarter-turn of tilt).
CX, CY, CW, CH = 44, 236, 650, 1054
CROT = -1.0
EDGE = 24                         # airmail border: a cream lip, then the stripes
# The lime airmail label: its turned body, and the unturned box around it.
LW, LH, LROT = 300, 224, -3.0
LBX, LBY, LBW, LBH = 706, 290, 312, 240
# The stamp album along the foot of the safe box.
ALB_Y = 1300                      # page top
MNT_Y = 1311                      # mounts' top
CAP_Y = 1392                      # years' top (26 px: their letters end above y 1420)
# A year's card (card coordinates).
ST_W, ST_H, ST_X, ST_Y = 456, 690, 154, 76   # the stamp, top right (646 tall for a two-line name)
PM_D, PM_X, PM_Y = 200, 126, 150  # the postmark: size, and its circle's centre (the date on the card)
TXT_X, TXT_W = 44, 562            # the typed lines
NOTE_W = 352                      # the pen line (NEW THAT DAY goes beside it)

CARD_T = """
.pc-air{position:absolute;inset:0;background:@lip@;border-radius:4px}
.pc-air::before{content:"";position:absolute;inset:6px;background:repeating-linear-gradient(-45deg,
  @red@ 0 18px,@lip@ 18px 27px,@blue@ 27px 45px,@lip@ 45px 54px)}
.pc-stock{position:absolute;inset:@edge@px;background:url(@card@) 0 0/600px 600px;
  box-shadow:inset 0 0 0 1px rgba(120,96,60,.12)}
"""

CSS = """
.pc-card{position:absolute;left:0;top:0;border-radius:4px;overflow:hidden;
  box-shadow:0 1px 1px rgba(0,0,0,.4),0 6px 10px rgba(0,0,0,.3),0 24px 42px rgba(0,0,0,.38)}
.pc-age{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 80% 70% at 48% 45%,rgba(0,0,0,0) 62%,rgba(140,104,52,.13) 100%)}
.pc-type{font-family:'Special Elite',monospace;color:@ink@;white-space:nowrap;line-height:1.12;
  text-shadow:0 0 .7px rgba(34,31,41,.55)}
.pc-pen{font-family:'Caveat',cursive;font-weight:700;color:@pen@;white-space:nowrap;line-height:1}
.pc-print{font-family:'Playfair Display',serif;font-weight:700;color:@print@;letter-spacing:.42em;
  white-space:nowrap}
.pc-rule{position:absolute;height:0;border-top:1.5px solid rgba(122,107,88,.55)}
.pc-lbl{position:absolute;background:@lime@;border-radius:3px;
  box-shadow:0 1px 1px rgba(0,0,0,.45),0 4px 7px rgba(0,0,0,.38),0 16px 28px rgba(0,0,0,.42)}
.pc-lbl::before{content:"";position:absolute;inset:0;border-radius:3px;background:url(@card@) 0 0/300px 300px;
  mix-blend-mode:multiply;opacity:.55}
.pc-lbl-in{position:absolute;inset:9px;border:3px solid #111;display:flex;flex-direction:column;
  align-items:center;justify-content:center}
.pc-lbl-in::after{content:"";position:absolute;inset:4px;border:1px solid #111}
.pc-hand{font-family:Oswald,sans-serif;color:@red@;display:flex;flex-direction:column;align-items:center;
  justify-content:center;border:5px solid @red@;border-radius:8px;outline:2px solid @red@;outline-offset:-12px;
  -webkit-mask:url(@ink_m@) -40px -20px/1400px 700px;mask:url(@ink_m@) -40px -20px/1400px 700px}
.pc-big{font-family:'Playfair Display',serif;font-weight:900;color:#f7c948;line-height:.9;white-space:nowrap;
  font-variant-numeric:lining-nums;text-align:center}
@keyframes pcslide{0%{transform:translate(-1010px,40px) rotate(-7deg)}
  70%{transform:translate(12px,-3px) rotate(.45deg)}86%{transform:translate(-3px,0) rotate(-.15deg)}
  100%{transform:none}}
@keyframes pcflipout{0%{transform:perspective(2600px) rotateY(0) scale(1)}
  100%{transform:perspective(2600px) rotateY(90deg) scale(1.05)}}
@keyframes pcflipin{0%{transform:perspective(2600px) rotateY(-90deg) scale(1.05)}
  70%{transform:perspective(2600px) rotateY(5deg) scale(1.004)}100%{transform:none}}
@keyframes pcslam{0%{opacity:0;transform:scale(1.32) rotate(var(--r,0deg))}
  1%{opacity:1}55%{opacity:1;transform:scale(.982) rotate(var(--r,0deg))}
  100%{opacity:1;transform:scale(1) rotate(var(--r,0deg))}}
@keyframes pcjolt{0%,100%{transform:none}35%{transform:translateY(3px) scale(.996)}}
@keyframes pcnudge{0%,100%{transform:none}40%{transform:translate(-7px,5px) rotate(-.9deg)}
  75%{transform:translate(1px,-1px) rotate(.12deg)}}
@keyframes pcmount{0%{opacity:0;transform:translateY(-74px) rotate(-9deg) scale(1.14)}
  22%{opacity:1}72%{opacity:1;transform:translateY(3px) rotate(.6deg) scale(.99)}
  100%{opacity:1;transform:none}}
@keyframes pcplace{0%{opacity:0;transform:translate(8px,-46px) scale(1.12) rotate(calc(var(--r,0deg) - 7deg))}
  25%{opacity:1}70%{opacity:1;transform:translate(0,2px) scale(.99) rotate(var(--r,0deg))}
  100%{opacity:1;transform:rotate(var(--r,0deg))}}
@keyframes pcout{to{transform:translate(1150px,60px) rotate(9deg)}}
@keyframes pcpress{0%,100%{transform:rotate(var(--r)) scale(1)}35%{transform:rotate(var(--r)) scale(1.045)}
  70%{transform:rotate(var(--r)) scale(.985)}}
@keyframes pcink{from{color:#8d7f6c}to{color:#1d1b22}}
"""


def _fill(css: str, **kw) -> str:
    for k, v in kw.items():
        css = css.replace(f"@{k}@", str(v))
    return css


def _a(name: str, t: float, dur: float, ease: str = "cubic-bezier(.2,.9,.25,1)", extra: str = "") -> str:
    return f"animation:{name} {dur:.2f}s {ease} {t:.3f}s 1 normal both;{extra}"


def _hex(c: str) -> tuple:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a: str, b: str, k: float) -> str:
    x, y = _hex(a), _hex(b)
    return "#" + "".join(f"{round(p + (q - p) * k):02x}" for p, q in zip(x, y))


def _pal(rarity: str = "", base: str = "") -> dict:
    """A stamp's inks from its rarity colour: the ground, a light centre, the
    dark engraving ink for the frame and tablets."""
    b = base or RARITY.get(rarity or "", "#8b9098")
    return {"ground": _mix(b, "#2b2520", .12), "light": _mix(b, "#fff3d8", .42),
            "deep": _mix(b, "#15131c", .3), "dark": _mix(b, "#0e0f1e", .66)}


BDAY_PAL = _pal(base="#2e57b8")


# ------------------------------------------------------------------ stamps

def _perf_path(w: float, h: float, r: float, pitch: float) -> str:
    """A stamp's outline: a rectangle with a perforation hole bitten out every
    `pitch` px along each edge (whole holes, spread evenly)."""
    nx, ny = max(2, round(w / pitch)), max(2, round(h / pitch))
    px, py = w / nx, h / ny
    d = ["M0,0"]
    for i in range(nx):
        c = px * (i + .5)
        d.append(f"L{c - r:.2f},0A{r:.2f},{r:.2f} 0 0 0 {c + r:.2f},0")
    d.append(f"L{w:.2f},0")
    for j in range(ny):
        c = py * (j + .5)
        d.append(f"L{w:.2f},{c - r:.2f}A{r:.2f},{r:.2f} 0 0 0 {w:.2f},{c + r:.2f}")
    d.append(f"L{w:.2f},{h:.2f}")
    for i in reversed(range(nx)):
        c = px * (i + .5)
        d.append(f"L{c + r:.2f},{h:.2f}A{r:.2f},{r:.2f} 0 0 0 {c - r:.2f},{h:.2f}")
    d.append(f"L0,{h:.2f}")
    for j in reversed(range(ny)):
        c = py * (j + .5)
        d.append(f"L0,{c + r:.2f}A{r:.2f},{r:.2f} 0 0 0 0,{c - r:.2f}")
    return "".join(d) + "Z"


def _wreath(size: float, color: str) -> str:
    """A laurel wreath round a star: the commemorative stamp's picture."""
    cx = cy = size / 2
    rr = size * .36
    parts = []
    for side in (-1, 1):
        pts = []
        for i in range(10):
            a = math.radians(98 + i * 15)             # from the bottom, up one side
            x = cx - rr * math.cos(a) if side > 0 else cx + rr * math.cos(a)
            y = cy + rr * math.sin(a)
            pts.append((x, y))
            ang = math.degrees(a) + 90
            ang = ang if side < 0 else 180 - ang
            off = 16 if i % 2 else -16
            parts.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{size * .075:.1f}" ry="{size * .028:.1f}" '
                         f'fill="{color}" transform="rotate({ang + off:.1f} {x:.1f} {y:.1f})"/>')
        parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" '
                     f'stroke="{color}" stroke-width="{size * .014:.1f}"/>')
    star = []
    for k in range(10):
        rad = size * (.2 if k % 2 == 0 else .085)
        a = math.radians(-90 + k * 36)
        star.append(f"{cx + rad * math.cos(a):.1f},{cy - size * .02 + rad * math.sin(a):.1f}")
    parts.append(f'<polygon points="{" ".join(star)}" fill="{color}"/>')
    return (f'<svg width="{size:.0f}" height="{size:.0f}" viewBox="0 0 {size:.1f} {size:.1f}" '
            f'style="display:block;overflow:visible">{"".join(parts)}</svg>')


def _stamp(uri: str, it: dict | None, year, w: float, h: float, *, title: str = "ITEM SHOP",
           pal: dict | None = None, motif: str = "", mini: bool = False) -> str:
    """A perforated postage stamp w x h: white paper with its holes, an
    engraved frame, the rarity's colour as the ground, the cosmetic standing
    on the year's tablet (the year where a stamp prints its value), `title`
    across the top. The box is w x h at (0, 0) of its parent."""
    p = pal or _pal((it or {}).get("rarity", ""))
    m = max(3.0, w * .046)
    r = max(1.6, w * .0125)
    pitch = max(4.8, w * .036)
    rule = max(1.2, w * .0065)
    band = max(2.4, w * .021)
    ir = max(.8, w * .0032)
    fi = rule + band + ir
    fw, fh = w - 2 * m - 2 * fi, h - 2 * m - 2 * fi
    tab = round(fh * .16) if year else 0
    tfs = max(9.0, w * .05)
    ttop = round(tfs * 1.75) if title else 0
    gap = fh * .012
    fig_h = fh - tab - ttop - gap
    shadow = ("drop-shadow(0 .5px .6px rgba(40,26,10,.35))" if mini else
              "drop-shadow(0 1px 1.2px rgba(40,26,10,.32)) drop-shadow(0 4px 6px rgba(60,40,20,.16))")
    out = [f'<div style="position:absolute;left:0;top:0;width:{w:.0f}px;height:{h:.0f}px">',
           f'<svg width="{w:.1f}" height="{h:.1f}" viewBox="0 0 {w:.2f} {h:.2f}" style="position:absolute;left:0;top:0;'
           f'overflow:visible;filter:{shadow}"><path d="{_perf_path(w, h, r, pitch)}" fill="{PAPER}"/></svg>']
    hatch = (f"repeating-linear-gradient(45deg,{p['dark']} 0 1px,transparent 1px 3.6px),"
             f"repeating-linear-gradient(-45deg,{p['dark']} 0 1px,transparent 1px 3.6px)") if not mini else "none"
    out.append(f'<div style="position:absolute;left:{m:.1f}px;top:{m:.1f}px;width:{w - 2 * m:.1f}px;'
               f'height:{h - 2 * m:.1f}px;background:{p["dark"]}">'
               f'<div style="position:absolute;inset:{rule:.1f}px;background-color:{p["ground"]};background-image:{hatch}">'
               '</div>')
    if not mini:
        c = rule + band
        for (lx, ly) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            out.append(f'<div style="position:absolute;{"right" if lx else "left"}:0;{"bottom" if ly else "top"}:0;'
                       f'width:{c:.1f}px;height:{c:.1f}px;background:radial-gradient(circle,{p["light"]} 0 22%,'
                       f'{p["dark"]} 26%)"></div>')
    out.append(f'<div style="position:absolute;left:{fi:.1f}px;top:{fi:.1f}px;width:{fw:.1f}px;height:{fh:.1f}px;'
               f'overflow:hidden;background:radial-gradient(ellipse 78% 62% at 50% 46%,{p["light"]} 0%,'
               f'{p["ground"]} 60%,{p["deep"]} 100%);box-shadow:0 0 0 {ir:.1f}px {p["dark"]}">')
    if title:
        out.append(f'<div style="position:absolute;left:0;top:0;right:0;height:{ttop}px;background:{p["dark"]};'
                   f'display:flex;align-items:center;justify-content:center;font-family:\'Playfair Display\',serif;'
                   f'font-weight:700;font-size:{tfs:.1f}px;letter-spacing:.3em;color:#f5ecd6;white-space:nowrap;'
                   f'padding-left:.3em">{esc(title)}</div>')
    fig_top = ttop + gap
    if uri:
        out.append(f'<div style="position:absolute;left:0;right:0;top:{fig_top:.1f}px;height:{fig_h:.1f}px;'
                   f'display:flex;align-items:flex-end;justify-content:center">'
                   f'<img data-trim="figure" data-name="{esc((it or {}).get("name", ""))}" src="{uri}" '
                   f'style="display:block;height:{fig_h - (2 if mini else 6):.1f}px;max-width:{fw - (4 if mini else 16):.1f}px;'
                   f'object-fit:contain;object-position:50% 100%"></div>')
    elif motif:
        out.append(f'<div style="position:absolute;left:0;right:0;top:{fig_top:.1f}px;height:{fig_h:.1f}px;'
                   f'display:flex;align-items:center;justify-content:center">{motif}</div>')
    elif it:
        initial = (it.get("name") or "?").strip()[:1].upper()
        out.append(f'<div style="position:absolute;left:0;right:0;top:{fig_top:.1f}px;height:{fig_h:.1f}px;'
                   f'display:flex;align-items:center;justify-content:center;font-family:\'Playfair Display\',serif;'
                   f'font-style:italic;font-weight:700;font-size:{fig_h * .62:.0f}px;color:{p["light"]};'
                   f'text-shadow:0 3px 0 {p["dark"]}">{esc(initial)}</div>')
    if not mini:
        out.append('<div style="position:absolute;inset:0;background:repeating-linear-gradient(0deg,'
                   'rgba(8,10,28,.075) 0 1px,transparent 1px 3px)"></div>')
    if tab:
        yfs = tab * .8
        out.append(f'<div style="position:absolute;left:0;right:0;bottom:0;height:{tab}px;background:{p["dark"]};'
                   f'display:flex;align-items:center;justify-content:center;gap:{tab * .16:.0f}px">'
                   f'<i style="width:{tab * .09:.1f}px;height:{tab * .09:.1f}px;background:{p["light"]};'
                   f'transform:rotate(45deg)"></i>'
                   f'<span style="font-family:\'Playfair Display\',serif;font-weight:900;font-size:{yfs:.1f}px;'
                   f'line-height:1;color:#f7efd9;letter-spacing:.02em;font-variant-numeric:lining-nums;'
                   f'margin-top:{-tab * .06:.1f}px">{esc(str(year))}</span>'
                   f'<i style="width:{tab * .09:.1f}px;height:{tab * .09:.1f}px;background:{p["light"]};'
                   f'transform:rotate(45deg)"></i></div>')
    out.append('</div></div></div>')
    return "".join(out)


# ------------------------------------------------------------------ ink

_uid = [0]


def _postmark(top: str, bottom: str, l1: str, l2: str, d: float = PM_D, wave: float = 310, wy: float = -30,
              seed: int = 0, color: str = INK) -> str:
    """A round date stamp: `top` and `bottom` round the ring, `l1` over `l2` in
    the middle, and wavy cancel lines running `wave` px to the right. An <svg>
    (d + wave) x d, the circle centred on (d/2, d/2), inked unevenly."""
    _uid[0] += 1
    k = _uid[0]
    rnd = random.Random(seed)
    cx = cy = d / 2
    ro = d / 2 - 3
    ri = ro - d * .2
    fs = d * .1
    rt = ri + (ro - ri) * .2
    rb = ro - (ro - ri) * .22
    w = d + wave
    s = [f'<svg width="{w:.0f}" height="{d:.0f}" viewBox="0 0 {w:.1f} {d:.1f}" style="position:absolute;left:0;top:0;'
         f'overflow:visible"><defs>'
         f'<path id="pmt{k}" d="M{cx - rt:.1f},{cy:.1f} A{rt:.1f},{rt:.1f} 0 0 1 {cx + rt:.1f},{cy:.1f}"/>'
         f'<path id="pmb{k}" d="M{cx - rb:.1f},{cy:.1f} A{rb:.1f},{rb:.1f} 0 0 0 {cx + rb:.1f},{cy:.1f}"/></defs>'
         f'<g fill="none" stroke="{color}"><circle cx="{cx}" cy="{cy}" r="{ro:.1f}" stroke-width="{d * .026:.1f}"/>'
         f'<circle cx="{cx}" cy="{cy}" r="{ri:.1f}" stroke-width="{d * .013:.1f}"/></g>'
         f'<g fill="{color}" font-family="Oswald" font-weight="500" font-size="{fs:.1f}" letter-spacing="{fs * .14:.1f}" '
         f'text-anchor="middle">'
         f'<text><textPath href="#pmt{k}" startOffset="50%">{esc(top)}</textPath></text>'
         f'<text><textPath href="#pmb{k}" startOffset="50%">{esc(bottom)}</textPath></text></g>']
    for sx in (-1, 1):                  # a star at 9 and 3 o'clock on the ring
        x = cx + sx * (ri + ro) / 2
        pts = " ".join(f"{x + (fs * (.36 if j % 2 == 0 else .15)) * math.cos(math.radians(-90 + j * 36)):.1f},"
                       f"{cy + (fs * (.36 if j % 2 == 0 else .15)) * math.sin(math.radians(-90 + j * 36)):.1f}"
                       for j in range(10))
        s.append(f'<polygon points="{pts}" fill="{color}"/>')
    f1 = min(d * .17, (2 * ri - d * .07) / max(len(l1) * .5, 1))
    f2 = min(d * .14, (2 * ri - d * .1) / max(len(l2) * .5, 1)) if l2 else 0
    y1 = cy + (f1 * .32 if not l2 else -d * .015)
    s.append(f'<text x="{cx}" y="{y1:.1f}" fill="{color}" font-family="Oswald" font-weight="700" font-size="{f1:.1f}" '
             f'text-anchor="middle" letter-spacing="{f1 * .04:.1f}">{esc(l1)}</text>')
    if l2:
        s.append(f'<line x1="{cx - ri * .62:.1f}" x2="{cx + ri * .62:.1f}" y1="{cy + d * .025:.1f}" '
                 f'y2="{cy + d * .025:.1f}" stroke="{color}" stroke-width="{d * .008:.1f}"/>')
        s.append(f'<text x="{cx}" y="{cy + d * .025 + f2 * 1.02:.1f}" fill="{color}" font-family="Oswald" '
                 f'font-weight="700" font-size="{f2:.1f}" text-anchor="middle" letter-spacing="{f2 * .05:.1f}">'
                 f'{esc(l2)}</text>')
    if wave > 0:
        amp, lam, step = d * .034, d * .3, d * .074
        ph = rnd.uniform(0, 6.28)
        x0 = cx + ro + d * .03
        for i in range(6):
            y = cy + wy + (i - 2.5) * step
            pts = []
            x = x0
            while x <= w:
                pts.append(f"{x:.1f},{y + amp * math.sin((x - x0) / lam * 2 * math.pi + ph):.1f}")
                x += 5
            s.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" '
                     f'stroke-width="{d * .018:.1f}" stroke-linecap="round"/>')
    s.append("</svg>")
    ox, oy = rnd.randint(0, 520), rnd.randint(0, 150)
    ink = tex("postcard-ink.png")
    return (f'<div style="position:absolute;left:0;top:0;width:{w:.0f}px;height:{d:.0f}px;opacity:.86;'
            f'-webkit-mask:url({ink}) {-ox}px {-oy}px/800px 400px;mask:url({ink}) {-ox}px {-oy}px/800px 400px">'
            + "".join(s) + "</div>")


def _handstamp(l1: str, l2: str, w: float, h: float, f1: float, f2: float) -> str:
    """A red rubber handstamp: a double-ruled box, `l1` big over `l2`."""
    return (f'<div class="pc-hand" style="width:{w:.0f}px;height:{h:.0f}px;opacity:.95">'
            f'<div style="font-weight:700;font-size:{f1:.0f}px;line-height:.95;letter-spacing:.04em;'
            f'white-space:nowrap">{esc(l1)}</div>'
            + (f'<div style="font-weight:500;font-size:{f2:.0f}px;line-height:1.05;letter-spacing:.2em;'
               f'white-space:nowrap;padding-left:.2em">{esc(l2)}</div>' if l2 else "")
            + '</div>')


def _centred(text: str, top: float, fit: float, cls: str, style: str, rot: float = 0, anim: str = "",
             left: float = 0, width: float = CW) -> str:
    """One line of text centred in [left, left + width], shrunk to `fit` px if
    it is wider (the fit is measured on the text itself, not on the box)."""
    return (f'<div class="abs" style="left:{left:.0f}px;width:{width:.0f}px;top:{top:.0f}px;text-align:center;'
            f'transform:rotate({rot}deg)"><div class="{cls}" data-fit="{fit:.0f}" style="display:inline-block;'
            f'white-space:nowrap;{style};{anim}">{esc(text)}</div></div>')


def _typed(text: str, seed: int) -> str:
    """Typewriter text: each letter struck a little harder or softer."""
    rnd = random.Random(seed)
    out = []
    for ch in text:
        if ch == " ":
            out.append(" ")
            continue
        out.append(f'<span style="opacity:{rnd.uniform(.74, 1):.2f};position:relative;'
                   f'top:{rnd.uniform(-1.3, 1.3):.1f}px">{esc(ch)}</span>')
    return "".join(out)


def _name_lines(name: str, maxw: float, big: float = 56, small: float = 46) -> tuple:
    """The name as one line, or two balanced lines when it won't fit at `big`
    (Special Elite runs about .58 em a letter); and the size to type it at."""
    em = .58
    if len(name) * em * big <= maxw:
        return [name], big
    words = name.split()
    if len(words) >= 2:
        best = min(((" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))),
                   key=lambda pr: max(len(pr[0]), len(pr[1])))
        return list(best), min(small, maxw / (max(len(best[0]), len(best[1])) * em))
    return [name], max(28.0, maxw / (len(name) * em))


# ------------------------------------------------------------------ the desk, the label, the album

def _desk() -> str:
    return (f'<div class="full" data-safe="ignore" style="z-index:0;background:#18223a url({tex("postcard-desk.jpg")}) '
            f'center/1080px 1920px"></div>')


def _props() -> str:
    """A magnifier and a fountain pen on the desk right of the card, below the
    label (pure decoration; they run under the button rail)."""
    desk = tex("postcard-desk.jpg")
    lx, ly, lr = 872, 700, 92                     # the magnifier's lens
    mag = (f'<div class="abs" style="left:{lx + 40}px;top:{ly - 26}px;width:250px;height:52px;border-radius:26px;'
           f'transform-origin:0 26px;transform:rotate(-24deg);background:linear-gradient(180deg,#5a3a22 0,#8c5c34 30%,'
           f'#4a2e1a 70%,#2a180c 100%);box-shadow:0 10px 16px rgba(0,0,0,.45)"></div>'
           f'<div class="abs" style="left:{lx + 60}px;top:{ly - 21}px;width:52px;height:42px;transform-origin:-20px 21px;'
           f'transform:rotate(-24deg);background:linear-gradient(180deg,#8a6a2a,#f0d78e 35%,#9a7430 70%,#5a4212);'
           f'border-radius:6px"></div>'
           f'<div class="abs" style="left:{lx - lr}px;top:{ly - lr}px;width:{2 * lr}px;height:{2 * lr}px;'
           f'border-radius:50%;box-shadow:0 14px 26px rgba(0,0,0,.5),0 3px 5px rgba(0,0,0,.45);'
           f'background:conic-gradient(from 20deg,#6d5220,#f2dc98,#9c7a34,#5a4214,#e6c878,#8a6a28,#6d5220)"></div>'
           f'<div class="abs" style="left:{lx - lr + 13}px;top:{ly - lr + 13}px;width:{2 * lr - 26}px;'
           f'height:{2 * lr - 26}px;border-radius:50%;overflow:hidden;background:url({desk}) '
           f'{-(lx - lr + 13) * 1.7 + (lr - 13) * .7:.0f}px {-(ly - lr + 13) * 1.7 + (lr - 13) * .7:.0f}px/1836px 3264px;'
           f'box-shadow:inset 0 0 18px rgba(0,0,0,.55),inset 0 0 3px rgba(255,255,255,.35)">'
           f'<div style="position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle at 32% 28%,'
           f'rgba(255,255,255,.3) 0,rgba(255,255,255,.1) 22%,rgba(255,255,255,0) 46%),radial-gradient(circle at 50% 50%,'
           f'rgba(0,0,0,0) 70%,rgba(255,255,255,.14) 93%,rgba(0,0,0,0) 100%)"></div></div>')
    # the pen: drawn lying along +x, nib first, then turned into place
    pen = ('<svg width="640" height="64" viewBox="0 -32 640 64" style="position:absolute;left:0;top:0;overflow:visible">'
           '<defs><linearGradient id="pcg" x1="0" y1="-1" x2="0" y2="1" gradientUnits="objectBoundingBox">'
           '<stop offset="0" stop-color="#6e5320"/><stop offset=".3" stop-color="#f3dd98"/>'
           '<stop offset=".6" stop-color="#a47e34"/><stop offset="1" stop-color="#4f3a10"/></linearGradient>'
           '<linearGradient id="pcl" x1="0" y1="0" x2="0" y2="1">'
           '<stop offset="0" stop-color="#3a0b10"/><stop offset=".22" stop-color="#a3323a"/>'
           '<stop offset=".42" stop-color="#6d161d"/><stop offset="1" stop-color="#1c0406"/></linearGradient>'
           '<linearGradient id="pcb" x1="0" y1="0" x2="0" y2="1">'
           '<stop offset="0" stop-color="#1a1a1a"/><stop offset=".25" stop-color="#5a5a5a"/>'
           '<stop offset=".5" stop-color="#151515"/><stop offset="1" stop-color="#050505"/></linearGradient></defs>'
           '<path d="M0,0 L60,-10 L60,10 Z" fill="url(#pcg)"/>'
           '<path d="M6,0 L44,0" stroke="#4a3610" stroke-width="1.6"/><circle cx="44" cy="0" r="2.6" fill="#4a3610"/>'
           '<rect x="58" y="-13" width="58" height="26" rx="7" fill="url(#pcb)"/>'
           '<rect x="114" y="-16" width="8" height="32" fill="url(#pcg)"/>'
           '<rect x="120" y="-17" width="300" height="34" rx="9" fill="url(#pcl)"/>'
           '<rect x="418" y="-18" width="10" height="36" fill="url(#pcg)"/>'
           '<rect x="426" y="-19" width="184" height="38" rx="17" fill="url(#pcl)"/>'
           '<rect x="446" y="-25" width="146" height="8" rx="4" fill="url(#pcg)"/>'
           '<circle cx="592" cy="-21" r="6" fill="url(#pcg)"/>'
           '</svg>')
    pen = (f'<div class="abs" style="left:752px;top:1236px;width:640px;height:64px;transform-origin:0 32px;'
           f'transform:rotate(-57deg);filter:drop-shadow(8px 14px 9px rgba(0,0,0,.5))">{pen}</div>')
    return f'<div class="full" data-safe="ignore" style="z-index:1">{mag}{pen}</div>'


def _label(press: float | None = None) -> str:
    """USE CODE: BAD as a lime airmail label stuck on the desk. The outer box
    is the unturned box around it (the safe-zone check measures it)."""
    anim = _a("pcpress", press, .5, "ease-in-out") if press is not None else ""
    return (f'<div class="abs" data-safe="key" data-name="code" style="left:{LBX}px;top:{LBY}px;width:{LBW}px;'
            f'height:{LBH}px">'
            f'<div class="pc-lbl" style="left:{(LBW - LW) / 2:.0f}px;top:{(LBH - LH) / 2:.0f}px;width:{LW}px;'
            f'height:{LH}px;--r:{LROT}deg;transform:rotate({LROT}deg);{anim}">'
            '<div class="pc-lbl-in">'
            '<div style="font-family:Oswald,sans-serif;font-weight:500;font-size:40px;line-height:1;letter-spacing:.16em;'
            'padding-left:.16em;color:#111">USE CODE:</div>'
            '<div style="font-family:Oswald,sans-serif;font-weight:700;font-size:128px;line-height:.9;'
            'letter-spacing:.02em;color:#111;margin-top:2px">BAD</div>'
            '<div style="font-family:Oswald,sans-serif;font-weight:500;font-size:23px;line-height:1;letter-spacing:.06em;'
            'color:#1a1a12;margin-top:6px">#EpicPartner</div>'
            '</div></div></div>')


def _album(ctx, slots: list, fills: list, marks: list, t_end: float) -> str:
    """The stamp album along the foot: a printed box and the year under it for
    every year; at fills[i] that year's used stamp drops into a black mount and
    the pen underlines the year until the next one comes in. slots: (year,
    item or None, bday)."""
    n = len(slots)
    s = 840 / n
    mw = min(66, s - 20)
    mh = round(mw * 1.22)
    page = (f'<div class="abs" data-safe="ignore" style="left:26px;top:{ALB_Y}px;width:914px;height:140px;'
            f'background:#efe7d4;border-radius:2px;box-shadow:0 2px 3px rgba(0,0,0,.4),0 12px 22px rgba(0,0,0,.35);'
            f'background-image:repeating-linear-gradient(0deg,rgba(120,140,160,.13) 0 1px,transparent 1px 12px),'
            f'repeating-linear-gradient(90deg,rgba(120,140,160,.13) 0 1px,transparent 1px 12px)">'
            f'<div style="position:absolute;inset:7px;border:1px solid rgba(122,107,88,.55)"></div>'
            f'<div style="position:absolute;inset:11px;border:1px solid rgba(122,107,88,.3)"></div></div>')
    out = [page]
    for i, (year, it, bday) in enumerate(slots):
        cx = 60 + s * (i + .5)
        x = cx - mw / 2
        out.append(f'<div class="abs" data-safe="ignore" style="left:{x:.1f}px;top:{MNT_Y}px;width:{mw:.0f}px;'
                   f'height:{mh}px;border:1px solid rgba(122,107,88,.6)"></div>')
        t = fills[i]
        if bday:
            st = _stamp("", None, None, mw - 8, mh - 8, title="", pal=BDAY_PAL, motif=_wreath(mw * .8, "#f3e7c8"),
                        mini=True)
        else:
            st = _stamp(ctx.art(it), it, None, mw - 8, mh - 8, title="", mini=True)
        out.append(f'<div class="abs" style="left:{x:.1f}px;top:{MNT_Y}px;width:{mw:.0f}px;height:{mh}px;'
                   f'{_a("pcmount", t, .5, "cubic-bezier(.25,.8,.3,1)")}">'
                   f'<div style="position:absolute;inset:0;background:#131313;border-radius:1px;'
                   f'box-shadow:0 1px 2px rgba(0,0,0,.35)"></div>'
                   f'<div style="position:absolute;left:4px;top:4px;width:{mw - 8:.0f}px;height:{mh - 8}px">{st}</div>'
                   f'<div style="position:absolute;inset:0;background:linear-gradient(118deg,rgba(255,255,255,.2) 0,'
                   f'rgba(255,255,255,.06) 34%,rgba(255,255,255,0) 35%,rgba(255,255,255,0) 100%)"></div></div>')
        out.append(f'<div class="abs" style="left:{cx - s / 2:.1f}px;width:{s:.1f}px;top:{CAP_Y}px;text-align:center;'
                   f'font-family:Oswald,sans-serif;font-weight:500;font-size:26px;line-height:1.1;letter-spacing:.04em;'
                   f'color:#8d7f6c;{_a("pcink", marks[i], .3, "linear")}">{year}</div>')
        t_on, t_off = marks[i], (marks[i + 1] if i + 1 < len(marks) else t_end)
        # the pen's underline, in its own small box (a full-frame SVG per year costs every frame)
        d, L = rough_line(6, 8, 66, 7, seed=year, bow=.06)
        L = int(L) + 4
        out.append(f'<svg class="abs" data-safe="ignore" width="72" height="16" viewBox="0 0 72 16" '
                   f'style="left:{cx - 36:.1f}px;top:1412px;overflow:visible">'
                   f'<path d="{d}" fill="none" stroke="{PEN}" stroke-width="4.5" stroke-linecap="round" '
                   f'style="stroke-dasharray:{L};stroke-dashoffset:{L};animation:lkdraw .3s ease-out {t_on:.3f}s 1 '
                   f'normal both,lkout .15s linear {t_off:.3f}s 1 normal both"/></svg>')
    return "".join(out)


# ------------------------------------------------------------------ cards

def _card_frame() -> str:
    return '<div class="pc-air"></div><div class="pc-stock"></div>'


def _place(inner: str, enter: str = "", jolt: str = "", z: int = 0, outer: str = "") -> str:
    """A card at its place on the desk: `enter` animates it arriving, `jolt`
    shakes it when something is stamped on it, `outer` takes it away."""
    return (f'<div class="abs" style="left:{CX}px;top:{CY}px;width:{CW}px;height:{CH}px;transform:rotate({CROT}deg);'
            f'z-index:{z}"><div style="width:100%;height:100%;{outer}">'
            f'<div style="width:100%;height:100%;{enter}"><div style="width:100%;height:100%;{jolt}">'
            f'<div class="pc-card" style="width:{CW}px;height:{CH}px">{inner}<div class="pc-age"></div></div>'
            f'</div></div></div></div>')


def _year_card(ctx, rd, it, debut, when_short: str, t0: float, k: int) -> tuple:
    """One year's card; t0 is when it has the desk to itself. Returns (inner
    html, sounds, t_fill)."""
    y = rd["year"]
    rnd = random.Random(y * 31 + k)
    lines, size = _name_lines(it["name"], TXT_W)
    sh = ST_H if len(lines) == 1 else ST_H - 44
    html = [_card_frame(),
            f'<div class="abs" style="left:{ST_X}px;top:{ST_Y}px;width:{ST_W}px;height:{sh}px;'
            f'transform:rotate({rnd.uniform(-1.4, 1.2):.2f}deg)">{_stamp(ctx.art(it), it, y, ST_W, sh)}</div>']
    html.append(f'<div class="abs pc-print" style="left:{ST_X / 2 - 150:.0f}px;top:{ST_Y + sh - 330:.0f}px;width:300px;'
                f'text-align:center;font-size:22px;letter-spacing:.5em;transform:rotate(-90deg);opacity:.8">'
                f'POST CARD</div>')
    # the postmark, slammed over the stamp's top-left corner
    t_pm = t0 + .42
    rot = rnd.uniform(-22, -12)
    px, py = PM_X + rnd.uniform(-5, 5), PM_Y + rnd.uniform(-4, 4)
    html.append(f'<div class="abs" style="left:{px - PM_D / 2:.0f}px;top:{py - PM_D / 2:.0f}px;width:{PM_D + 330}px;'
                f'height:{PM_D}px;transform-origin:{PM_D / 2:.0f}px {PM_D / 2:.0f}px;--r:{rot:.1f}deg;'
                f'transform:rotate({rot:.1f}deg);{_a("pcslam", t_pm, .2, "cubic-bezier(.3,.7,.4,1)")}">'
                + _postmark("ON THIS DAY", "ITEM SHOP", when_short, str(y), d=PM_D, wave=330, wy=-34, seed=y)
                + '</div>')
    # typed on the address lines: the name, then its rarity and type
    ty = ST_Y + sh + 22
    t_type = t0 + .8
    sounds = [(t_pm, "stamp")]
    for i, line in enumerate(lines):
        dur = min(.9, .05 * len(line) + .1)
        lh = size * 1.12
        html.append(f'<div class="abs pc-type" data-fit="{TXT_W}" style="left:{TXT_X}px;top:{ty:.0f}px;'
                    f'font-size:{size:.0f}px;{write_on(t_type, dur, max(4, len(line)))}">{_typed(line, y + i)}</div>'
                    f'<div class="pc-rule" style="left:{TXT_X - 4}px;width:{TXT_W + 6}px;top:{ty + lh - 4:.0f}px"></div>')
        for j in range(min(4, max(2, len(line) // 4))):
            sounds.append((t_type + j * dur / 4 + .03, "tick"))
        ty += lh
        t_type += dur + .05
    kind = " ".join(x for x in (it.get("rarity_label") or "", it.get("type") or "") if x).strip().upper()
    ty += 8
    html.append(f'<div class="abs pc-type" data-fit="{TXT_W}" style="left:{TXT_X}px;top:{ty:.0f}px;font-size:30px;'
                f'letter-spacing:.05em;color:#3c3842;{write_on(t_type + .05, .45, max(4, len(kind) // 2))}">'
                f'{_typed(kind, y + 7)}</div>')
    ty += 30 * 1.12 + 16
    # the pen line (and NEW THAT DAY beside it)
    note = ("its very first day", "in the shop!") if debut else ("in the Item Shop", "that day")
    t_note = t0 + 1.75
    for i, line in enumerate(note):
        html.append(f'<div class="abs pc-pen" data-fit="{NOTE_W}" style="left:{TXT_X + 2}px;top:{ty + i * 56:.0f}px;'
                    f'font-size:56px;transform:rotate(-1.5deg);{write_on(t_note + i * .5, .5, 14)}">{esc(line)}</div>')
    sounds.append((t_note, "pen"))
    if debut:
        t_new = t_note + 1.05
        html.append(f'<div class="abs" style="left:{TXT_X + NOTE_W + 22:.0f}px;top:{ty - 4:.0f}px;--r:-7deg;'
                    f'{_a("pcslam", t_new, .2, "cubic-bezier(.3,.7,.4,1)")}">'
                    + _handstamp("NEW", "THAT DAY", 176, 104, 52, 22) + '</div>')
        sounds.append((t_new, "stamp"))
    t_fill = t0 + 2.9
    sounds.append((t_fill, "paper"))
    return "".join(html), sounds, t_fill, t_pm


def _picture_card(ctx, lead: list, when_short: str, span: str, bday) -> str:
    """The hook: a big-letter picture postcard, with the two lead outfits as
    stamps under one postmark."""
    pic = ("position:absolute;inset:18px;overflow:hidden;"
           "background:radial-gradient(circle,rgba(40,30,20,.08) 32%,transparent 36%) 0 0/6px 6px,"
           "repeating-linear-gradient(0deg,rgba(60,40,20,.045) 0 1px,transparent 1px 3px),"
           "repeating-linear-gradient(90deg,rgba(60,40,20,.045) 0 1px,transparent 1px 3px),"
           "linear-gradient(180deg,#2c7486 0%,#5ea7ad 26%,#a9d1c3 44%,#f0dca6 64%,#eab77c 100%)")
    shadow = ",".join([f"{dx}px {dy}px 0 #2a1810" for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2), (1.5, 1.5),
                                                                 (-1.5, 1.5), (1.5, -1.5), (-1.5, -1.5))]
                      + [f"{i}px {i}px 0 #b0452b" for i in range(3, 11)]
                      + ["11px 11px 0 #2a1810", "14px 18px 16px rgba(0,0,0,.28)"])
    html = [f'<div style="position:absolute;inset:0;background:#f5efe2 url({tex("postcard-card.jpg")}) 0 0/600px"></div>',
            f'<div style="{pic}"></div>',
            f'<div class="abs" style="left:18px;right:18px;top:52px;text-align:center;font-family:\'Playfair Display\','
            f'serif;font-style:italic;font-weight:700;font-size:62px;line-height:1.1;color:#fff8ea;'
            f'text-shadow:2px 2px 0 #183a4c,3px 3px 0 #183a4c,5px 7px 8px rgba(0,0,0,.25)">Greetings from the</div>',
            f'<div class="abs pc-big" style="left:0;right:0;top:128px;font-size:176px;text-shadow:{shadow}">ITEM</div>',
            f'<div class="abs pc-big" style="left:0;right:0;top:282px;font-size:176px;text-shadow:{shadow}">SHOP!</div>']
    rib = f"ON THIS DAY · {when_short} · {span}"
    html.append(f'<div class="abs" style="left:34px;right:34px;top:462px;height:60px;background:{AIR_RED};'
                f'clip-path:polygon(0 0,100% 0,97.2% 50%,100% 100%,0 100%,2.8% 50%);'
                f'box-shadow:inset 0 -4px 0 rgba(0,0,0,.18);display:flex;align-items:center;justify-content:center">'
                f'<div data-fit="520" style="font-family:Oswald,sans-serif;font-weight:700;font-size:34px;'
                f'letter-spacing:.05em;color:#fff4de;white-space:nowrap">{esc(rib)}</div></div>')
    a, b = lead[0], lead[1]
    for (rd, it, _), (x, y0, rot) in zip((a, b), ((30, 548, -5), (328, 568, 4))):
        html.append(f'<div class="abs" style="left:{x}px;top:{y0}px;width:292px;height:398px;transform:rotate({rot}deg)">'
                    f'{_stamp(ctx.art(it), it, rd["year"], 292, 398)}</div>')
    html.append(f'<div class="abs" style="left:{322 - 90}px;top:{606 - 90}px;transform:rotate(-12deg);'
                f'transform-origin:90px 90px">'
                + _postmark("ON THIS DAY", "ITEM SHOP", when_short, "EVERY YEAR", d=180, wave=0, seed=7) + '</div>')
    if bday:
        html.append(_centred(f"Fortnite turns {bday['age']}!", 968, 560, "pc-pen", "font-size:66px", -2))
    else:
        html.append(_centred("one outfit from this date, every year", 980, 584, "pc-pen", "font-size:48px", -1.5))
        # the pen comes back and underlines "every year"
        d, L = rough_line(458, 1022, 618, 1017, seed=5, bow=.05)
        html.append(f'<svg class="abs" data-safe="ignore" width="{CW}" height="{CH}" style="left:0;top:0;overflow:visible">'
                    f'<path d="{d}" fill="none" stroke="{PEN}" stroke-width="5" stroke-linecap="round" '
                    f'style="stroke-dasharray:{int(L) + 4};stroke-dashoffset:{int(L) + 4};'
                    f'animation:lkdraw .35s ease-out .95s 1 normal both"/></svg>')
    return "".join(html)


def _bday_card(bday: dict, t0: float) -> tuple:
    """The birthday: a postcard with the red 9 YEARS TODAY handstamp and a pen
    line, and a first day cover laid on it (returned separately: it leaves the
    other way). Returns (card inner, envelope html, sounds, t_fill)."""
    t_hand = t0 + 1.95
    card = [_card_frame(),
            '<div class="abs pc-print" style="left:0;right:0;top:44px;text-align:center;font-size:28px;'
            'padding-left:.42em">POST CARD</div>',
            f'<div class="pc-rule" style="left:60px;width:530px;top:92px"></div>',
            f'<div class="abs" style="left:92px;top:118px;--r:-5deg;{_a("pcslam", t_hand, .2, "cubic-bezier(.3,.7,.4,1)")}">'
            + _handstamp(f"{bday['age']} YEARS", "TODAY", 470, 196, 96, 40) + '</div>',
            f'<div class="abs pc-pen" data-fit="560" style="left:46px;top:890px;font-size:62px;transform:rotate(-2deg);'
            f'{write_on(t0 + 2.45, .9, 20)}">Happy birthday, Fortnite!</div>']
    ew, eh = 846, 512
    stamp = _stamp("", None, bday["year"], 196, 256, title="BATTLE ROYALE", pal=BDAY_PAL,
                   motif=_wreath(150, "#f3e7c8"))
    t_pm = t0 + 1.15
    env = (f'<div class="abs" style="left:40px;top:572px;width:{ew}px;height:{eh}px;transform:rotate(2deg)">'
           f'<div style="position:absolute;inset:0;background:#f7f2e7 url({tex("postcard-card.jpg")}) 0 0/600px;'
           f'border-radius:3px;box-shadow:0 1px 1px rgba(0,0,0,.35),0 8px 14px rgba(0,0,0,.3),0 26px 44px rgba(0,0,0,.34)">'
           f'</div>'
           f'<div class="abs" style="left:30px;top:30px;width:530px;height:452px;border:2px solid {NAVY};'
           f'box-shadow:inset 0 0 0 5px #f7f2e7,inset 0 0 0 6px {NAVY}"></div>'
           f'<div class="abs" style="left:30px;width:530px;top:56px;text-align:center;font-family:Oswald,sans-serif;'
           f'font-weight:500;font-size:26px;letter-spacing:.32em;padding-left:.32em;color:{RED}">FIRST DAY COVER</div>'
           + _centred("FORTNITE", 96, 470, "", f"font-family:'Playfair Display',serif;font-weight:900;"
                      f"font-size:86px;line-height:1;color:{NAVY}", 0, left=30, width=530)
           + _centred("BATTLE ROYALE", 186, 470, "", f"font-family:'Playfair Display',serif;font-weight:900;"
                      f"font-size:54px;line-height:1;color:{NAVY}", 0, left=30, width=530)
           + f'<div class="abs" style="left:110px;width:370px;top:262px;border-top:2px solid {RED}"></div>'
           + _centred(f"RELEASED SEPTEMBER 26, {bday['year']}", 284, 470, "", "font-family:Oswald,sans-serif;"
                      f"font-weight:500;font-size:30px;letter-spacing:.08em;color:{NAVY}", 0, left=30, width=530)
           + _centred("PC · PlayStation 4 · Xbox One", 338, 470, "", "font-family:'Playfair Display',serif;"
                      f"font-style:italic;font-weight:700;font-size:38px;color:{NAVY}", 0, left=30, width=530)
           + f'<div class="abs" style="left:614px;top:36px;width:196px;height:256px;transform:rotate(1.5deg)">{stamp}</div>'
           f'<div class="abs" style="left:{648 - 98}px;top:{384 - 98}px;width:{196 + 96}px;height:196px;--r:-8deg;'
           f'transform-origin:98px 98px;{_a("pcslam", t_pm, .2, "cubic-bezier(.3,.7,.4,1)")}">'
           + _postmark("FIRST DAY OF ISSUE", "BATTLE ROYALE", "SEP 26", str(bday["year"]), d=196, wave=96, wy=-4,
                       seed=26)
           + '</div></div>')
    sounds = [(t_pm, "stamp"), (t_hand, "stamp"), (t0 + 2.45, "pen")]
    return "".join(card), env, sounds, t0 + 2.95


def _outro_card(ctx, picks: list, when_short: str, span: str, t: float) -> tuple:
    html = [_card_frame(),
            '<div class="abs pc-print" style="left:0;right:0;top:40px;text-align:center;font-size:28px;'
            'padding-left:.42em">POST CARD</div>',
            f'<div class="pc-rule" style="left:60px;width:530px;top:86px"></div>']
    for i, line in enumerate(("Which year had", "the best shop?")):
        html.append(_centred(line, 100 + i * 86, 560, "pc-pen", "font-size:88px", -2,
                             write_on(t + .08 + i * .55, .55, 14)))
    sounds = [(t + .08, "pen"), (t + .63, "pen")]
    if len(picks) >= 3:
        spots = [(40, 300, 262, 360, -4), (348, 312, 262, 360, 3), (56, 682, 262, 330, -2)]
        pm = (470, 850, 236)
    else:
        spots = [(34, 304, 286, 400, -4), (330, 322, 286, 400, 3)]
        pm = (325, 860, 236)
    for i, ((rd, it), (x, y0, w, h, rot)) in enumerate(zip(picks, spots)):
        tt = t + 1.15 + i * .28
        html.append(f'<div class="abs" style="left:{x}px;top:{y0}px;width:{w}px;height:{h}px;--r:{rot}deg;'
                    f'{_a("pcplace", tt, .42, "cubic-bezier(.25,.8,.3,1)")}">{_stamp(ctx.art(it), it, rd["year"], w, h)}'
                    f'</div>')
        sounds.append((tt, "paper"))
    cx, cy, d = pm
    t_pm = t + 1.15 + len(picks) * .28 + .35
    html.append(f'<div class="abs" style="left:{cx - d / 2:.0f}px;top:{cy - d / 2:.0f}px;width:{d}px;height:{d}px;'
                f'--r:8deg;transform-origin:{d / 2:.0f}px {d / 2:.0f}px;'
                f'{_a("pcslam", t_pm, .2, "cubic-bezier(.3,.7,.4,1)")}">'
                + _postmark("ON THIS DAY", "ITEM SHOP", when_short, span, d=d, wave=0, seed=99) + '</div>')
    sounds.append((t_pm, "stamp"))
    return "".join(html), sounds


# ------------------------------------------------------------------ the video

def on_this_day(ctx, rounds: list, bday: dict | None, lead: list, third) -> Comp:
    day = ctx.day
    when_short = f"{day.strftime('%b').upper()} {day.day}"
    years = ([bday["year"]] if bday else []) + [rd["year"] for rd, _, _ in rounds]
    n = len(years)
    r = max(R, (62.0 - 7.5 - HOOK) / n)
    content_end = HOOK + n * r
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(_fill(CARD_T, lip=LIP, red=AIR_RED, blue=AIR_BLUE, edge=EDGE, card=tex("postcard-card.jpg")))
    comp.css(_fill(CSS, ink=INK, pen=PEN, print=PRINT, lime=LIME, card=tex("postcard-card.jpg"), red=RED,
                   ink_m=tex("postcard-ink.png")))
    span = f"{years[0]}–{years[-1]}"

    # page k: from t0 = HOOK + k r, its card slid in over the one before
    starts = [HOOK + k * r for k in range(n)]
    slots, pages = [], []
    if bday:
        slots.append((bday["year"], None, True))
    for rd, it, debut in rounds:
        slots.append((rd["year"], it, False))

    fills = []
    k0 = 0
    if bday:
        t0 = starts[0]
        card, env, sounds, t_fill = _bday_card(bday, t0)
        pages.append(("bday", card, env, sounds, t_fill))
        fills.append(t_fill)
        k0 = 1
    for j, (rd, it, debut) in enumerate(rounds):
        t0 = starts[k0 + j]
        inner, sounds, t_fill, t_pm = _year_card(ctx, rd, it, debut, when_short, t0, k0 + j)
        pages.append(("year", inner, t_pm, sounds, t_fill))
        fills.append(t_fill)

    comp.add(_desk())
    comp.add(_props())
    marks = [starts[0] + .1] + [t + .12 for t in starts[1:]]
    comp.add(f'<div class="full" style="z-index:70">{_album(ctx, slots, fills, marks, content_end)}</div>')
    comp.add(f'<div class="full" style="z-index:90">{_label(content_end + 2.75)}</div>')
    comp.add(PREP_JS)

    # ---- hook (frame 0 is the thumbnail: the picture postcard, complete)
    t_flip = HOOK - .58
    hook = _place(_picture_card(ctx, lead, when_short, span, bday),
                  outer=_a("pcflipout", t_flip, .28, "cubic-bezier(.55,0,.9,.4)"),
                  enter=_a("pcnudge", .3, .55, "ease-in-out"))
    comp.scene(0, t_flip + .3, f'<div class="full">{hook}</div>', fade_in=.01, fade_out=.02, z=12)
    comp.cue(.3, "paper")
    if not bday:
        comp.cue(.95, "pen")
    comp.cue(t_flip + .2, "flip")

    # ---- the pages
    for k, pg in enumerate(pages):
        t0 = starts[k]
        end = (starts[k + 1] if k + 1 < n else content_end) + .25
        if k == 0:
            enter = _a("pcflipin", t_flip + .28, .34, "cubic-bezier(.2,.8,.3,1)")
            start = t_flip + .27
        else:
            enter = _a("pcslide", t0 - .5, .56, "cubic-bezier(.2,.75,.25,1)")
            start = t0 - .5
            comp.cue(t0 - .24, "paper")
        if pg[0] == "bday":
            _, card, env, sounds, _ = pg
            html = _place(card, enter=enter)
            leave = _a("pcout", end - .75, .5, "cubic-bezier(.55,0,.85,.35)")
            html += (f'<div class="abs" style="left:0;top:0;width:1080px;height:1920px;{leave}">'
                     f'<div style="width:100%;height:100%;{_a("pcslide", t0 + .12, .56, "cubic-bezier(.2,.75,.25,1)")}">'
                     f'{env}</div></div>')
            comp.cue(t0 + .36, "paper")
        else:
            _, inner, t_pm, sounds, _ = pg
            html = _place(inner, enter=enter, jolt=_a("pcjolt", t_pm + .05, .22, "ease-out"))
        comp.scene(start, end, f'<div class="full">{html}</div>', fade_in=.01, fade_out=.01, z=20 + k)
        for s in sounds:
            comp.cue(*s)

    # ---- outro: the question, the lead picks and the span, on a last card
    picks = [(rd, it) for rd, it, _ in lead] + ([(_round_of(rounds, third), third)] if third else [])
    t = content_end
    inner, sounds = _outro_card(ctx, picks, when_short, span, t)
    comp.scene(t - .5, comp.duration, f'<div class="full">{_place(inner, enter=_a("pcslide", t - .5, .56, "cubic-bezier(.2,.75,.25,1)"))}</div>',
               fade_in=.01, fade_out=.01, z=20 + n + 1)
    comp.cue(t - .24, "paper")
    for s in sounds:
        comp.cue(*s)
    comp.cue(t + 2.75, "paper")
    comp.cues.sort()
    return comp


def _round_of(rounds: list, item) -> dict:
    """The round `item` came from (for its year)."""
    return next((rd for rd, it, _ in rounds if it is item), {"year": ""})
