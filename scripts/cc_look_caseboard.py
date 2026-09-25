"""
CASEBOARD -- Odd One Out as a detective's cork board.

    0:00  hook      the board: a typed CASE FILE card, a yellow "?" note, the
                    four photos of case 1 pinned up (A-D, handwritten names), and
                    the lime USE CODE: BAD card pinned along the bottom
    0:03  cases     one case per 10.4 s: the photos get pinned one by one, a
                    typed CASE k OF n strip goes up under the "?" pad, the pad
                    counts down 3-2-1 on sticky notes, then the odd one is circled
                    in red marker, a note slaps on it, a typed slip over the case
                    file says THE OTHER 3: <SET> SET and red yarn ties the three
                    together. The photos drop off the board for the next case.
    outro           the odd ones out, pinned up in order with their case and
                    letter (the answer key), CASE CLOSED stamped on the file

Facts on screen are the classic format's: the names, and the set the other
three share. Nothing is said about the odd one's own set (we don't have it).
The photos come from the yearbook's photo lab (cc_look_yearbook), which crops
each render head-to-thigh and prints it as an instant photo, in the browser.

Layout: everything a viewer reads sits in the apps' safe box (cc_safe: x 60-1020
above y 740, x 60-900 from there down to y 1420; frame 0's text below y 285).
The case file and the pad fill the top band, the photos stand in two staggered
columns that stop short of the button rail, and the code card and #EpicPartner
run along the bottom of the box. Only the cork, the wooden rail, pins, yarn and
marker strokes reach the covered edges.
"""

import math
import random

from cc_look_yearbook import photo, photo_lab
from cc_looks import KIT_CSS, LIME, PREP_JS, _catmull, _plen, pad_to, stroke_svg, tex
from cc_motion import W, H, Comp, esc

HOOK = 3.0
R2 = 10.4           # one case, as cc_quiz.R2
T_REV = 7.6         # the answer lands this far into a case, as cc_quiz.T2_REV
FALL = .45          # the photos dropping off the board
LETTERS = "ABCD"
FONTS = ("Special Elite", "Kalam", "Permanent Marker")
RED = "#c81d27"
MARKER = "#d42a2a"

POL_W, POL_H, PM, PHS = 306, 396, 14, 278
CAP_Y = PM + PHS + 2                     # the caption: two handwritten lines of 48 px
CAP_H = POL_H - CAP_Y - 4
# A, B, C, D: (left, top, rotation, pin in the photo's own coordinates). Each
# column leans one way, so a photo's low corner and the one below's high corner
# are on opposite sides; the right column stops ~35 px short of the rail.
POLS = [(94, 476, -2.4, (262, 20)), (542, 512, 3.0, (150, 16)),
        (106, 888, -2.2, (272, 20)), (550, 930, 2.6, (40, 20))]
PIN_COLS = ["yellow", "blue", "red", "yellow", "green", "red", "blue", "yellow"]
TAG_S = 66                              # the evidence letters
CODE_X, CODE_Y, CODE_W, CODE_H, CODE_R = 72, 1298, 488, 108, -1.4
BIG_X, BIG_Y, BIG_W, BIG_H, BIG_R = 68, 1266, 584, 140, -1.4    # the outro's, pinned over it
EP_X, EP_Y = 668, 1354                  # #EpicPartner, typed on a slip beside the code
CARD_X, CARD_Y, CARD_W, CARD_H, CARD_R = 66, 276, 590, 190, -1.2
PAD_X, PAD_Y, PAD_S, PAD_R = 784, 252, 212, 5
STRIP_X, STRIP_Y = 790, 452             # CASE k OF n, under the pad
SLIP_X, SLIP_Y, SLIP_W, SLIP_R = 80, 350, 566, 1.2     # THE OTHER 3, over the case file's rules

CSS = r"""
.cb-type{font-family:'Special Elite',monospace;color:#232220}
.cb-hand{font-family:Kalam,cursive;font-weight:700}
.cb-pol{position:absolute;left:0;top:0;width:%(PW)dpx;height:%(PH)dpx;
  background:linear-gradient(170deg,#fbfaf5 0%%,#f1eee6 60%%,#e9e5da 100%%);border-radius:2px;
  box-shadow:0 1px 1px rgba(0,0,0,.28),0 6px 8px rgba(0,0,0,.22),0 18px 26px -6px rgba(0,0,0,.35)}
.cb-pol .ph{position:absolute;left:%(PM)dpx;top:%(PM)dpx;width:%(PHS)dpx;height:%(PHS)dpx;overflow:hidden;
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.18)}
.cb-pol .ph::after{content:"";position:absolute;inset:0;box-shadow:inset 0 2px 5px rgba(0,0,0,.35);
  background:linear-gradient(125deg,rgba(255,255,255,.13) 0%%,rgba(255,255,255,0) 38%%,rgba(255,255,255,0) 70%%,
  rgba(255,255,255,.06) 100%%)}
.cb-pol .cap{position:absolute;left:%(PM)dpx;top:%(CAPY)dpx;width:%(PHS)dpx;height:%(CAPH)dpx;display:flex;
  align-items:center}
.cb-pol .cap div{font:700 48px/1.0 Kalam,cursive;color:#1f2a48;width:%(PHS)dpx;text-wrap:balance}
.cb-tag{position:absolute;width:%(TS)dpx;height:%(TS)dpx;background:#fdfcf7;border:3px solid #1b1a18;display:flex;
  align-items:center;justify-content:center;font:400 52px/1 'Special Elite',monospace;color:#1b1a18;
  box-shadow:0 1px 1px rgba(0,0,0,.3),0 4px 6px rgba(0,0,0,.25)}
.cb-pin{position:absolute;width:0;height:0;z-index:20}
.cb-pin b{position:absolute;border-radius:50%%;box-shadow:inset -2px -3px 4px rgba(0,0,0,.35)}
.cb-pin i{position:absolute;border-radius:50%%;background:rgba(25,12,0,.5);filter:blur(4px);transform:translate(8px,10px)}
.cb-pin s{position:absolute;left:0;top:-2px;width:16px;height:3px;background:rgba(25,12,0,.35);transform-origin:0 50%%;
  transform:rotate(38deg);filter:blur(1px)}
.cb-sticky{position:absolute;box-shadow:0 1px 1px rgba(0,0,0,.18),0 14px 14px -8px rgba(0,0,0,.45)}
.cb-sticky::before{content:"";position:absolute;inset:0;background:url(%(paper)s) center/cover;opacity:.5;
  mix-blend-mode:multiply}
.cb-sticky::after{content:"";position:absolute;left:6%%;right:6%%;bottom:0;height:24px;
  background:linear-gradient(180deg,rgba(0,0,0,0),rgba(0,0,0,.07))}
.cb-yellow{background:linear-gradient(180deg,#fff27d 0%%,#f9e664 65%%,#f0da55 100%%)}
.cb-pink{background:linear-gradient(180deg,#ff9fca 0%%,#fb8dbd 65%%,#f27fb2 100%%)}
.cb-screw{position:absolute;width:22px;height:22px;border-radius:50%%;
  background:radial-gradient(circle at 38%% 34%%,#e9e4da 0 2px,#b9b1a2 5px,#7d7466 11px);
  box-shadow:0 2px 2px rgba(0,0,0,.45),inset 0 -1px 1px rgba(0,0,0,.35)}
.cb-screw::after{content:"";position:absolute;left:3px;right:3px;top:10px;height:2px;background:rgba(40,34,26,.7)}
@keyframes cbslap{0%%{opacity:0;transform:translate(46px,-80px) scale(1.2) rotate(calc(var(--r) + 8deg))}
  12%%{opacity:1}58%%{transform:translate(0,0) scale(.985) rotate(var(--r))}
  100%%{opacity:1;transform:translate(0,0) scale(1) rotate(var(--r))}}
@keyframes cbpin{0%%{opacity:0;transform:translate(6px,-34px) scale(1.05)}35%%{opacity:1}
  100%%{opacity:1;transform:none}}
@keyframes cbfall{0%%{transform:none}100%%{transform:translate(var(--dx),1500px) rotate(var(--dr))}}
@keyframes cbswing{0%%{transform:none}18%%{transform:rotate(var(--sw)) translateY(2px)}
  45%%{transform:rotate(calc(var(--sw) * -.45))}70%%{transform:rotate(calc(var(--sw) * .18))}100%%{transform:none}}
@keyframes cbdraw{to{stroke-dashoffset:0}}
@keyframes cbin{from{opacity:0}to{opacity:1}}
@keyframes cbstamp{0%%{opacity:0;transform:scale(1.6) rotate(var(--r))}60%%{opacity:.9}
  100%%{opacity:.88;transform:scale(1) rotate(var(--r))}}
"""

# Handwriting that must fit a box both ways: shrink until no word runs past the
# width and it takes at most data-lines lines (PREP_JS's data-fit checks only
# the height of wrapping text, so one long word could still run out sideways).
FIT_JS = """<script>(() => {
  const prev = window.__ready;
  window.__ready = (async () => {
    if (prev) { try { await prev; } catch (e) {} }
    try {
      await document.fonts.ready;
      for (const el of document.querySelectorAll('[data-cbfit]')) {
        const maxW = +el.dataset.cbfit, lines = +(el.dataset.lines || 1);
        let size = parseFloat(getComputedStyle(el).fontSize), guard = 90;
        const lh = () => parseFloat(getComputedStyle(el).lineHeight) || size * 1.1;
        const tooBig = () => el.scrollWidth > maxW + 2 || el.offsetHeight > lh() * lines + 2;
        while (guard-- > 0 && size > 12 && tooBig()) { size *= 0.96; el.style.fontSize = size + 'px'; }
      }
    } catch (e) {}
  })();
})();</script>"""

PIN_COL = {"red": ("#ff8a80", "#d7262b", "#7d0f13"), "yellow": ("#fff3a0", "#f2c230", "#8a6206"),
           "blue": ("#9fc6ff", "#2f6fd6", "#12306b"), "green": ("#b8f5b0", "#3aa345", "#14521b")}


def _a(name: str, t: float, dur: float, ease: str = "cubic-bezier(.2,.9,.25,1)", extra: str = "") -> str:
    return f"animation:{name} {dur:.2f}s {ease} {t:.3f}s 1 normal both;{extra}"


def _rot_point(left, top, w, h, rot, lx, ly):
    """A point in a box's own coordinates (the box rotated about its centre) -> page."""
    cx, cy = left + w / 2, top + h / 2
    a = math.radians(rot)
    dx, dy = lx - w / 2, ly - h / 2
    return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)


def _pin(x: float, y: float, col: str = "red", size: int = 30, style: str = "") -> str:
    lt, base, dk = PIN_COL[col]
    r = size / 2
    return (f'<div class="cb-pin" style="left:{x:.1f}px;top:{y:.1f}px;{style}">'
            f'<i style="left:{-r * .55:.1f}px;top:{-r * .35:.1f}px;width:{size * .95:.1f}px;height:{size * .8:.1f}px">'
            f'</i><s></s><b style="left:{-r:.1f}px;top:{-r * 1.25:.1f}px;width:{size}px;height:{size}px;'
            f'background:radial-gradient(circle at 36% 30%,#fff 0 {size * .07:.1f}px,{lt} {size * .2:.1f}px,'
            f'{base} 55%,{dk} 100%)"></b></div>')


def _question_mark(x0, y0, s=1.0, rot=0.0):
    """A '?' as a person scribbles it: the hook, then a separate dot."""
    a = math.radians(rot)
    cxl, cyl = 48, 75

    def P(x, y):
        dx, dy = x - cxl, y - cyl
        return (x0 + (cxl + dx * math.cos(a) - dy * math.sin(a)) * s,
                y0 + (cyl + dx * math.sin(a) + dy * math.cos(a)) * s)
    pts = [P(x, y) for x, y in [(14, 46), (17, 24), (35, 7), (60, 5), (80, 20), (83, 42), (71, 61), (53, 75),
                                (48, 95), (49, 113)]]
    dot = [P(46, 138), P(51, 143), P(47, 145)]
    return [(_catmull(pts), _plen(pts) * 1.08), (_catmull(dot), _plen(dot) * 1.2)]


def _strokes(paths, color, width, w, h, start=None, durs=None) -> str:
    """Marker strokes in a box's own coordinates; drawn on from `start`, or already there."""
    out = [f'<svg class="abs" width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="left:0;top:0;overflow:visible">']
    t = start
    for k, (d, L) in enumerate(paths):
        L = int(L) + 4
        anim = ""
        if start is not None:
            dur = durs[k]
            anim = (f' style="stroke-dasharray:{L};stroke-dashoffset:{L};'
                    f'animation:cbdraw {dur:.2f}s cubic-bezier(.4,.1,.5,1) {t:.2f}s 1 normal both"')
            t += dur + .08
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
                   f'stroke-linejoin="round" opacity=".9"{anim}/>')
    out.append("</svg>")
    return "".join(out)


def _rough_box(cx, cy, a, b, rot, seed=1, r=40, n=44, overshoot=.13, wobble=2.5):
    """A marker loop drawn round a photo: a rounded rectangle (half sizes a, b)
    turned by rot, a little wobbly, ending past where it started. Unlike an
    ellipse it clears the photo's corners, where the letter and the name are.
    Returns (path_d, approx_length)."""
    rnd = random.Random(seed)
    sw, sh = a - r, b - r
    segs = [("l", (0, -b), (sw, -b)), ("c", (sw, -sh), -90), ("l", (a, -sh), (a, sh)), ("c", (sw, sh), 0),
            ("l", (sw, b), (-sw, b)), ("c", (-sw, sh), 90), ("l", (-a, sh), (-a, -sh)), ("c", (-sw, -sh), 180),
            ("l", (-sw, -b), (0, -b))]
    lens = [math.dist(p, q) if k == "l" else math.pi * r / 2 for k, p, q in segs]
    per = sum(lens)

    def at(s_):
        s_ %= per
        for (k, p, q), L in zip(segs, lens):
            if s_ <= L:
                u = s_ / max(L, 1e-6)
                if k == "l":
                    x, y = p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u
                    nx, ny = (0, -1) if p[1] == q[1] == -b else (0, 1) if p[1] == q[1] == b else \
                        (1, 0) if p[0] == q[0] == a else (-1, 0)
                    return x, y, nx, ny
                ang = math.radians(q + 90 * u)
                return p[0] + r * math.cos(ang), p[1] + r * math.sin(ang), math.cos(ang), math.sin(ang)
            s_ -= L
        return 0, -b, 0, -1
    s0 = per * rnd.uniform(.04, .12)
    ph1, ph2 = rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = []
    for i in range(n + 1):
        t = i / n
        x, y, nx, ny = at(s0 + per * (1 + overshoot) * t)
        off = wobble * (math.sin(t * 9 + ph1) + .6 * math.sin(t * 23 + ph2)) + 7 * (t - .5)
        x, y = x + nx * off, y + ny * off
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return _catmull(pts), _plen(pts) * 1.04


# ------------------------------------------------------------------ the board

def _board(n: int, t_closed: float) -> str:
    """The cork, the rail, the case file and the "?" pad. The rules come off
    the case file just before CASE CLOSED is stamped where they were."""
    wood = tex("case-wood.jpg")
    card = tex("case-card.jpg")
    # an index card: a red rule under the heading, a blue one under each row
    lines = "".join(f'<div class="abs" style="left:0;right:0;top:{84 + 46 * k}px;height:2px;'
                    f'background:rgba(96,150,210,.42)"></div>' for k in range(1, 3))
    qs = _question_mark(58, 40, 1.04)             # low enough on the pad for the 4:5 cover crop
    return (f'<div class="full" style="background:#8a5f3a url({tex("cork.jpg")}) center/cover"></div>'
            '<div class="full" style="background:radial-gradient(120% 80% at 38% 40%,rgba(255,236,200,.10) 0%,'
            'rgba(0,0,0,0) 45%,rgba(20,8,0,.34) 100%)"></div>'
            f'<div class="abs" style="left:0;top:0;width:{W}px;height:150px;background:url({wood}) center/cover;'
            'box-shadow:0 3px 2px rgba(0,0,0,.35),0 14px 26px rgba(0,0,0,.45)"></div>'
            '<div class="abs" style="left:0;top:132px;width:1080px;height:18px;'
            'background:linear-gradient(180deg,rgba(255,220,170,.22),rgba(0,0,0,.28))"></div>'
            '<div class="cb-screw" style="left:52px;top:62px;transform:rotate(24deg)"></div>'
            '<div class="cb-screw" style="left:1004px;top:66px;transform:rotate(-38deg)"></div>'
            # the case file, typed on an index card
            f'<div class="abs" style="left:{CARD_X}px;top:{CARD_Y}px;width:{CARD_W}px;height:{CARD_H}px;'
            f'transform:rotate({CARD_R}deg);background:#fbfaf3;box-shadow:0 1px 1px rgba(0,0,0,.25),'
            f'0 8px 14px -2px rgba(0,0,0,.3)">'
            f'<div class="abs" style="inset:0;background:url({card}) center/cover;opacity:.55;mix-blend-mode:multiply">'
            f'</div>{lines}<div class="abs" style="left:0;right:0;top:80px;height:2px;background:rgba(214,70,80,.7)">'
            '</div><div class="abs cb-type" style="left:24px;top:14px;line-height:1;white-space:nowrap">'
            '<span style="font-size:30px">CASE FILE: </span><span style="font-size:56px">ODD ONE OUT</span></div>'
            '<div class="abs cb-type" style="left:24px;top:86px;font-size:34px;line-height:46px;white-space:nowrap;'
            f'{_a("lkout", t_closed - .16, .14, "linear")}">'
            f'Three share a set. One doesn\'t.<br>{n} cases. Find the odd one.</div></div>'
            + _pin(*_rot_point(CARD_X, CARD_Y, CARD_W, CARD_H, CARD_R, CARD_W - 30, 16), "red")
            # the "?" pad
            + f'<div class="cb-sticky cb-yellow" style="left:{PAD_X}px;top:{PAD_Y}px;width:{PAD_S}px;'
              f'height:{PAD_S}px;transform:rotate({PAD_R}deg)">{_strokes(qs, "#23211e", 14, PAD_S, PAD_S)}'
              f'{_strokes(_question_mark(144, 34, .48, rot=12), "#23211e", 12, PAD_S, PAD_S, .7, (.45, .1))}</div>')


def _code(big: bool = False, t: float = 0) -> str:
    """USE CODE: BAD on a lime card pinned to the cork (#EpicPartner is typed
    beside it, see _partner). big=True: the outro's bigger card, pinned over it at t."""
    x, y, w, h, r = (BIG_X, BIG_Y, BIG_W, BIG_H, BIG_R) if big else (CODE_X, CODE_Y, CODE_W, CODE_H, CODE_R)
    uc, bad = (48, 132) if big else (40, 110)
    px, py = _rot_point(x, y, w, h, r, 40, 20)
    anim = _a("cbslap", t, .45, extra=f"--r:{r}deg;transform-origin:10% 20%;") if big else f"transform:rotate({r}deg);"
    return (f'<div class="abs" style="left:0;top:0;{_a("cbin", t, .01, "linear") if big else ""}">'
            f'<div class="cb-sticky" data-safe="key" data-name="code" style="left:{x}px;top:{y}px;width:{w}px;'
            f'height:{h}px;{anim}display:flex;align-items:baseline;justify-content:center;gap:14px;'
            f'padding:4px 22px 6px;color:#111;background:linear-gradient(180deg,#efff62 0%,{LIME} 45%,#ddf236 100%)">'
            f'<span style="position:relative;flex:none;white-space:nowrap;font:400 {uc}px/1 \'Permanent Marker\'">'
            f'USE CODE:</span><span style="position:relative;flex:none;white-space:nowrap;'
            f'font:400 {bad}px/.84 \'Permanent Marker\'">BAD</span></div>'
            + _pin(px, py, "red", 28 if big else 26,
                   _a("cbpin", t + .3, .25, "cubic-bezier(.3,1.2,.5,1)") if big else "")
            + '</div>')


def _partner() -> str:
    """#EpicPartner, typed on a slip beside the code card; there the whole time."""
    return (f'<div class="abs cb-type" style="left:{EP_X}px;top:{EP_Y}px;transform:rotate(1.8deg);'
            f'background:#f7f4ea;padding:9px 14px 7px;font-size:26px;white-space:nowrap;box-shadow:0 1px 1px '
            f'rgba(0,0,0,.25),0 6px 8px -2px rgba(0,0,0,.35)">#EpicPartner</div>')


def _polaroid(ctx, it: dict, j: int, k: int, seed: int) -> tuple:
    """Photo j (A-D) of case k. Returns (html, rotation, pin xy on the page)."""
    left, top, rot, (px, py) = POLS[j]
    rot += ((k * 7 + j * 3) % 5 - 2) * .5          # never quite the same twice
    art = ctx.art(it)
    ph = photo(art, PHS, PHS, "three", seed, kind="studio", film="instant", bg="#ddd5c6|#7a7066",
               none="")
    # the letter goes on the top corner away from the pin, a little over the edge
    tag_x = PHS + PM - TAG_S + 12 if px < POL_W / 2 else PM - 10
    html = (f'<div class="abs" style="left:{left}px;top:{top}px;width:{POL_W}px;height:{POL_H}px;'
            f'transform:rotate({rot:.2f}deg)"><div class="cb-pol" style="transform-origin:{px}px {py}px;%SWING%">'
            f'<div class="ph">{ph}</div>'
            f'<div class="cap"><div data-cbfit="{PHS}" data-lines="2">{esc(it["name"])}</div></div>'
            f'<div class="cb-tag" style="left:{tag_x}px;top:{PM + 8}px;--r:{(j % 2) * 5 - 3}deg;%TAG%">'
            f'{LETTERS[j]}</div></div></div>')
    return html, rot, _rot_point(left, top, POL_W, POL_H, rot, px, py)


# ------------------------------------------------------------------ the red yarn

def _sag_path(a, b, sag):
    ax, ay = a
    bx, by = b
    mx, my = (ax + bx) / 2, (ay + by) / 2
    L = max(math.dist(a, b), 1)
    nx, ny = -(by - ay) / L, (bx - ax) / L
    if ny < 0:
        nx, ny = -nx, -ny
    steep = abs(by - ay) / L
    cx = mx + nx * sag * L * (1 - .55 * steep) + (sag * L * .5 * steep)
    cy = my + ny * sag * L * (1 - .55 * steep)
    return f"M{ax:.1f},{ay:.1f} Q{cx:.1f},{cy:.1f} {bx:.1f},{by:.1f}"


def _yarn(comp: Comp, a, b, t0: float, grow: float = .45, sag: float = .085) -> str:
    """Red yarn pulled from pin a to pin b, then relaxing into a sag."""
    uid = comp.uid("cbyarn")
    L = math.dist(a, b) * 1.15 + 30
    keys = [(0, .012), (.55, .018), (.72, sag * 1.35), (.86, sag * .9), (1, sag)]
    dur = grow / .55
    comp.css(f"@keyframes {uid}{{" + "".join(f'{int(p * 100)}%{{d:path("{_sag_path(a, b, s)}")}}' for p, s in keys)
             + "}")
    ad = f"{uid} {dur:.2f}s cubic-bezier(.3,.6,.4,1) {t0:.2f}s both"
    d0 = _sag_path(a, b, .012)
    return (f'<mask id="m{uid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<path d="{d0}" fill="none" stroke="#fff" stroke-width="34" stroke-linecap="round" '
            f'style="stroke-dasharray:{L:.0f};stroke-dashoffset:{L:.0f};'
            f'animation:cbdraw {grow:.2f}s cubic-bezier(.5,.1,.6,1) {t0:.2f}s both,{ad}"/></mask>'
            f'<g mask="url(#m{uid})">'
            f'<path d="{d0}" fill="none" stroke="rgba(20,8,0,.5)" stroke-width="6" filter="url(#cbyb)" '
            f'transform="translate(6,11)" style="animation:{ad}"/>'
            f'<path d="{d0}" fill="none" stroke="#8e0f17" stroke-width="7.5" stroke-linecap="round" style="animation:{ad}"/>'
            f'<path d="{d0}" fill="none" stroke="{RED}" stroke-width="5" stroke-linecap="round" style="animation:{ad}"/>'
            f'<path d="{d0}" fill="none" stroke="#ef5a60" stroke-width="2.2" stroke-dasharray="2.5 4.5" '
            f'stroke-linecap="round" transform="translate(-.8,-1.2)" style="animation:{ad}"/></g>')


# ------------------------------------------------------------------ one case

def _slip(set_name: str, t: float) -> str:
    """THE OTHER 3: <SET> SET, typed on a slip pinned over the case file's rules."""
    label = f"{set_name.upper()} SET"
    inner = SLIP_W - 40
    return (f'<div class="abs" style="left:{SLIP_X}px;top:{SLIP_Y}px;width:{SLIP_W}px;--r:{SLIP_R}deg;'
            f'{_a("cbslap", t, .45, extra="transform-origin:50% 10%;")}">'
            f'<div style="position:relative;background:#f4efe2;padding:12px 20px 10px;'
            f'box-shadow:0 1px 1px rgba(0,0,0,.3),0 8px 10px -3px rgba(0,0,0,.4)">'
            f'<div class="cb-type" style="font-size:30px;line-height:1.1;letter-spacing:.02em;color:#6b5a4a;'
            f'white-space:nowrap">THE OTHER 3:</div>'
            f'<div class="cb-type" data-cbfit="{inner}" style="width:{inner}px;font-size:46px;line-height:1.1;'
            f'margin-top:2px;color:#1b1a18;white-space:nowrap">{esc(label)}</div>'
            f'{_pin(SLIP_W / 2, 13, "green", 24)}</div></div>')


def _case(comp: Comp, ctx, four: list, odd: int, set_name: str, k: int, n: int, t0: float, first: bool) -> tuple:
    """Case k: returns (html, sounds). t0 is when the case starts; the first
    case's photos are already up on frame 0."""
    rev = t0 + T_REV
    sounds = []
    photos = []
    pins, rots = [], []
    for j, it in enumerate(four):
        html, rot, pin = _polaroid(ctx, it, j, k, 100 * k + j)
        rots.append(rot)
        swing = (f"animation:cbswing .9s cubic-bezier(.3,.7,.4,1) {rev + .72:.2f}s both;--sw:1.6deg"
                 if j == odd else "")
        t_tag = t0 + (.12 if first else .75) + j * .16       # the evidence letters go on as the case opens
        html = html.replace("%SWING%", swing).replace("%TAG%", _a("cbslap", t_tag, .3, extra="transform-origin:50% 50%;"))
        col = PIN_COLS[(k + j) % len(PIN_COLS)]
        t_in = t0 + .05 + j * .14
        enter = "" if first else _a("cbpin", t_in, .32, "cubic-bezier(.3,1.2,.5,1)")
        if not first:
            sounds.append((t_in + .1, "pin"))
        # each photo drops off the board at the end of the case, on its own
        dx, dr = (-40, -9, 30, 12)[j], (-14, 9, 16, -11)[j]
        fall = _a("cbfall", t0 + R2 - FALL + j * .04, FALL, "cubic-bezier(.55,0,.9,.5)",
                  f"--dx:{dx}px;--dr:{dr}deg;")
        photos.append(f'<div class="full" style="{fall}"><div class="full" style="{enter}">'
                      f'{html}{_pin(*pin, col)}</div></div>')
        pins.append(pin)

    out = ["".join(photos)]
    sounds.append((t0 + (.12 if first else .75), "paper"))

    # 3-2-1 on sticky notes slapped onto the "?" pad, then the letter
    group = []
    for i, d in enumerate("321"):
        t = rev - 3 + i
        r = (-4, 3, -2)[i]
        group.append(f'<div class="cb-sticky cb-yellow" style="left:{PAD_X + (i - 1) * 5}px;top:{PAD_Y + i * 3}px;'
                     f'width:{PAD_S}px;height:{PAD_S}px;display:flex;align-items:center;justify-content:center;'
                     f'--r:{PAD_R + r}deg;{_a("cbslap", t, .4, extra="transform-origin:50% 25%;")}">'
                     f'<span style="position:relative;font:400 150px/1 \'Permanent Marker\';color:#1b1a18">{d}</span>'
                     f'</div>')
        sounds.append((t, "tick"))
    group.append(f'<div class="cb-sticky cb-pink" style="left:{PAD_X - 4}px;top:{PAD_Y + 4}px;width:{PAD_S}px;'
                 f'height:{PAD_S}px;display:flex;flex-direction:column;align-items:center;justify-content:center;'
                 f'--r:{PAD_R - 5}deg;{_a("cbslap", rev + .1, .4, extra="transform-origin:50% 25%;")}">'
                 f'<span class="cb-hand" style="position:relative;font-size:34px;line-height:1;color:#a80f18">'
                 f'odd one out:</span><span style="position:relative;font:400 130px/1 \'Permanent Marker\';'
                 f'color:#a80f18">{LETTERS[odd]}</span></div>')
    sounds += [(rev, "ding"), (rev + .1, "paper")]

    # the odd one, circled in red marker
    left, top, _, _ = POLS[odd]
    rot = rots[odd]
    # margins: roomy on the open sides, tight where it faces the other row, so
    # it crosses that row's white border but never its names or letters
    m_top, m_bot = (12, 4) if odd < 2 else (2, 16)
    bx, by = _rot_point(left, top, POL_W, POL_H, rot, POL_W / 2, POL_H / 2 + (m_bot - m_top) / 2)
    group.append(stroke_svg([_rough_box(bx, by, POL_W / 2 + 18, POL_H / 2 + (m_top + m_bot) / 2, rot, seed=7 + k)],
                            MARKER, 10, rev, .55))
    sounds.append((rev, "pen"))
    # a note slapped onto it, on the side facing the middle of the board, below the face
    lx = POL_W - 44 if odd % 2 == 0 else 44
    nx, ny = _rot_point(left, top, POL_W, POL_H, rot, lx, POL_H * .5)
    group.append(f'<div class="cb-sticky cb-pink" style="left:{nx - 102:.0f}px;top:{ny - 72:.0f}px;width:204px;'
                 f'height:150px;display:flex;align-items:center;justify-content:center;text-align:center;'
                 f'--r:{7 if odd % 2 == 0 else -7}deg;{_a("cbslap", rev + .5, .45, extra="transform-origin:50% 25%;")}">'
                 f'<span class="cb-hand" style="position:relative;font-size:44px;line-height:1;color:#a80f18">'
                 f'ODD ONE<br>OUT!</span></div>')
    sounds.append((rev + .5, "paper"))
    # the typed slip: what the other three share
    group.append(_slip(set_name, rev + .3))
    sounds.append((rev + .3, "paper"))
    # red yarn between the other three
    others = [pins[j] for j in range(4) if j != odd]
    svg = [f'<svg class="abs" width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="left:0;top:0;overflow:visible">']
    for i, (a, b) in enumerate([(others[0], others[1]), (others[1], others[2]), (others[2], others[0])]):
        svg.append(_yarn(comp, a, b, rev + .75 + i * .42, grow=(.45, .38, .5)[i]))
    svg.append("</svg>")
    fall = _a("cbfall", t0 + R2 - FALL + .06, FALL, "cubic-bezier(.55,0,.9,.5)", "--dx:10px;--dr:4deg;")
    # yarn first (under the photos' pins), then the rest over the photos
    out.insert(0, f'<div class="full" style="{fall}">{"".join(svg)}</div>')
    out.append(f'<div class="full" style="{fall}">{"".join(group)}</div>')
    # the case number, typed on a strip pinned under the "?" pad (over the notes)
    out.append(f'<div class="full" style="{_a("cbfall", t0 + R2 - FALL, FALL, "cubic-bezier(.55,0,.9,.5)", "--dx:0px;--dr:6deg;")}">'
               f'<div class="abs cb-type" style="left:{STRIP_X}px;top:{STRIP_Y}px;--r:-2.5deg;'
               f'{_a("cbslap", t0 + (0 if first else .45), .35)}background:#fdfcf6;'
               f'padding:8px 16px 6px;font-size:30px;color:#b3261e;letter-spacing:.04em;white-space:nowrap;'
               f'box-shadow:0 1px 1px rgba(0,0,0,.25),0 5px 7px -2px rgba(0,0,0,.3)">CASE {k} OF {n}</div></div>')
    return "".join(out), sounds


# ------------------------------------------------------------------ the outro

def _answer_spots(n: int) -> tuple:
    """Where the answer key's photos go: ([(x, y, rot)], width, height). Rows of
    3 (or 2 for four cases), centred in the band below the pad, clear of the
    rail and of the big code card."""
    rows = [n] if n <= 3 else [2, n - 2] if n == 4 else [3, n - 3]
    three = max(rows) >= 3
    pw = 250 if three else 262
    ph = pw + 82                                        # photo + a two-line caption
    y0 = 540 if len(rows) > 1 else 700
    rots = [-3, 2.5, -2, 2, -2.5, 3]
    spots = []
    for r, m in enumerate(rows):
        for c in range(m):
            cx = 60 + 840 / m * (c + .5) if m >= 3 else 480 + (c - (m - 1) / 2) * 370
            drop = (c % 2) * 18 if three else (c % 2) * 8
            spots.append((cx - pw / 2, y0 + r * (ph + 18) + drop, rots[len(spots) % len(rots)]))
    return spots, pw, ph


def odd_one_out(ctx, spec: dict, rounds: list) -> Comp:
    """rounds: [([4 items], odd index, set name)], 4 or 5 of them."""
    n = len(rounds)
    content_end = HOOK + n * R2
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(CSS % dict(PW=POL_W, PH=POL_H, PM=PM, PHS=PHS, CAPY=CAP_Y, CAPH=CAP_H, TS=TAG_S,
                        paper=tex("case-card.jpg")))

    t_stamp = content_end + .15 + n * .5 + .35          # CASE CLOSED (the outro)
    comp.add(f'<div class="full" style="z-index:0">{_board(n, t_stamp)}</div>'
             '<svg width="0" height="0" style="position:absolute"><defs><filter id="cbyb" x="-10%" y="-10%" '
             'width="120%" height="120%"><feGaussianBlur stdDeviation="2.6"/></filter></defs></svg>')
    comp.cue(.7, "pen")
    for k, (four, odd, set_name) in enumerate(rounds, 1):
        t0 = HOOK + (k - 1) * R2
        html, sounds = _case(comp, ctx, four, odd, set_name, k, n, t0, k == 1)
        start = 0 if k == 1 else t0 - .05
        comp.scene(start, t0 + R2, f'<div class="full">{html}</div>', fade_in=.01, fade_out=.01, z=10)
        comp.cue(t0 + R2 - FALL, "paper")
        for s in sounds:
            comp.cue(*s)

    # ---- outro: the odd ones out, in order -- the answer key -- and CASE CLOSED
    t = content_end
    spots, pw, ph = _answer_spots(n)
    pm = 12
    phs = pw - 2 * pm
    out = []
    for i, (four, odd, _) in enumerate(rounds):
        x, y, r = spots[i]
        it = four[odd]
        ti = t + .15 + i * .5
        out.append(f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{pw}px;height:{ph}px;'
                   f'transform:rotate({r}deg)"><div class="abs" style="inset:0;'
                   f'{_a("cbpin", ti, .32, "cubic-bezier(.3,1.2,.5,1)")}">'
                   f'<div class="cb-pol" style="width:{pw}px;height:{ph}px">'
                   f'<div class="ph" style="left:{pm}px;top:{pm}px;width:{phs}px;height:{phs}px">'
                   f'{photo(ctx.art(it), phs, phs, "three", 900 + i, kind="studio", film="instant", bg="#ddd5c6|#7a7066", none="")}'
                   f'</div><div class="cap" style="left:{pm}px;top:{phs + pm + 2}px;width:{phs}px;'
                   f'height:{ph - phs - pm - 4}px">'
                   f'<div data-cbfit="{phs}" data-lines="2" style="width:{phs}px;font-size:42px">{esc(it["name"])}</div>'
                   f'</div></div>'
                   f'<div class="abs cb-type" style="left:8px;top:-20px;transform:rotate(-4deg);background:#fdfcf6;'
                   f'padding:6px 12px 4px;font-size:32px;color:#b3261e;white-space:nowrap;box-shadow:0 1px 1px '
                   f'rgba(0,0,0,.25),0 5px 7px -2px rgba(0,0,0,.3)">CASE {i + 1}: {LETTERS[odd]}</div>'
                   + _pin(pw - 30, 16, PIN_COLS[i % len(PIN_COLS)]) + '</div></div>')
        comp.cue(ti + .1, "pin")
    # stamped on the card's body, where the rules were: clear of the title
    out.append(f'<div class="abs cb-type" style="left:{CARD_X + CARD_W / 2 - 220:.0f}px;top:{CARD_Y + 82}px;'
               f'width:440px;height:92px;--r:-4deg;'
               f'border:9px solid {RED};border-radius:14px;color:{RED};background:rgba(251,250,243,.6);'
               f'display:flex;align-items:center;justify-content:center;white-space:nowrap;'
               f'font:700 56px/1 \'Special Elite\',monospace;letter-spacing:.02em;'
               f'-webkit-mask:url({tex("ink-stamp.png")}) center/cover;mask:url({tex("ink-stamp.png")}) center/cover;'
               f'{_a("cbstamp", t_stamp, .28, "cubic-bezier(.3,1.5,.5,1)")}">CASE CLOSED</div>')
    comp.cue(t_stamp, "stamp")
    t_ask = t_stamp + .6
    ask = 244
    out.append(f'<div class="cb-sticky cb-yellow" style="left:{PAD_X + PAD_S - ask + 6}px;top:{PAD_Y + 4}px;'
               f'width:{ask}px;height:{ask}px;display:flex;align-items:center;justify-content:center;'
               f'text-align:center;--r:-2deg;{_a("cbslap", t_ask, .4, extra="transform-origin:50% 25%;")}">'
               f'<span class="cb-hand" style="position:relative;font-size:50px;line-height:1.02;color:#1b1a18">'
               f'how many<br>did you<br>get?</span></div>')
    comp.cue(t_ask, "paper")
    comp.scene(t - .05, comp.duration, f'<div class="full">{"".join(out)}</div>', fade_in=.01, fade_out=.01, z=12)

    t_big = t_ask + 1.1
    comp.add(f'<div class="full" style="z-index:40;{_a("lkout", t_big + .4, .1, "linear")}">{_code()}</div>')
    comp.add(f'<div class="full" style="z-index:41">{_code(True, t_big)}</div>')
    comp.add(f'<div class="full" style="z-index:42">{_partner()}</div>')
    comp.cue(t_big, "paper")
    comp.cue(t_big + .35, "pin")
    comp.add(PREP_JS)
    comp.add(photo_lab())
    comp.add(FIT_JS)
    comp.cues.sort()
    return comp
