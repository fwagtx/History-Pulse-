"""
COMIC -- On This Day as a printed comic book, read one page at a time.

    0:00  cover     frame 0 is the comic's cover: the ON THIS DAY logo in
                    extruded block letters, a caption box "one outfit from
                    this date, every year!", the two lead cosmetics inked in
                    front of a halftone action panel with their heads breaking
                    out over its frame, the date and the span of years on a
                    red title banner, the years listed along the foot in mini
                    panels, and the lime price box USE CODE: BAD in the corner.
    0:03  years     one page per year. The page before turns away to the left
                    like a real page and the next one is under it: a big panel
                    of Ben-Day dots in the cosmetic's rarity colour with ink
                    focus lines, the cosmetic inked with a thick outline and a
                    hard shadow, standing out over the top of the frame. A
                    yellow caption box is placed (SEPTEMBER 28, 2019 --), the
                    year prints in block letters, the name slides in on a red
                    title banner with its rarity and type in a small box, and
                    a jagged NEW THAT DAY! burst slams on when it was its first
                    day in the shop (a caption "in the Item Shop that day"
                    otherwise). The year's mini panel along the foot fills in.
                    On Sep 26 an ORIGIN STORY splash page comes first:
                    Fortnite Battle Royale comes out, the platforms, and a
                    HAPPY 9TH BIRTHDAY! burst.
    end   outro     the last page: a big speech balloon "which year had the
                    best shop?" over the lead picks (each with its year), and
                    THE END? lettered under them.

Facts on screen are the classic format's: the date, each year, the name, its
rarity and type, NEW THAT DAY only when it was the item's first day in the
shop ("in the Item Shop that day" otherwise), the span of years, the birthday
page, and the outro question with the lead picks. No publisher, no real
comic's trade dress: the logo, the price box and the page furniture are this
look's own.

The price box -- USE CODE: / BAD / #EpicPartner, lime with near-black letters
under a black band with lime letters -- is its own layer above the pages: it
stays put in every frame while the pages turn under it, fully opaque, never
covered.

Layout: everything a viewer reads sits in the apps' safe box (cc_safe): the
price box, the caption and the year in the wide band at the top (x 60-1020,
y 285-740), the cosmetic, the banner, the rarity box and the row of years in
the column beside the button rail (x 60-900, down to y 1420). The panels, the
dots and focus lines, the paper and the page shadows run to the edges.

Render cost: the paper, the dots and the lines are committed textures
(cc_tex_comic.py) set once as CSS classes; each cosmetic's ink outline and
shadow are baked into its image once before frame 0 (FIG_JS). The only
full-frame motion is the page turn, a compositor transform.
"""

import math
import random

from cc_looks import KIT_CSS, LIME, PREP_JS, diecut_filter, pad_to, rough_line, stroke_svg, tex
from cc_motion import RARITY, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, Comp, anton_em, esc, trim_for
from cc_safe import COVER_TOP

HOOK = 3.0
R = 6.5
FONTS = ("Archivo Black", "Kalam", "Oswald")      # + Anton, which every page has

INK = "#16130f"                  # the black plate
CAP = "#ffc93a"                  # caption yellow (warmer than the code's lime)
RED = "#df3129"
PAPER = "#f3ead3"                # unprinted newsprint, for balloons and boxes
BLUE = "#2f9bdc"                 # the cover's colour
MX, MY = -4, 3                   # the colour plate sits this far off the black plate

TURN = .56                       # a page turning over
TURN_LEAD = .48                  # ... starting this long before the next page's t0

# Where things sit. The safe box: x 60-1020 above y 740, x 60-900 below, y 230-1420.
X0 = SAFE_LEFT + 4               # 64
XR = SAFE_RIGHT - 8              # 892: right edge of text beside the button rail
XT = SAFE_RIGHT_TOP - 8          # 1012: right edge above it
CODE_W, CODE_H = 312, 232
CODE_X, CODE_Y = XT - CODE_W, COVER_TOP + 4             # 700, 289: text below the cover crop
PX, PY, PW, PH = 34, 648, 1012, 674                      # the big panel: x 34-1046, y 648-1322
PB = 10                                                  # its border
CAP_Y = COVER_TOP + 12                                   # 297: the date caption
YEAR_Y, YEAR_SIZE = 372, 180                             # the year in block letters
FIG_CX, FIG_BOTTOM, FIG_W, FIG_H = 404, 1226, 470, 668   # the cosmetic: bottom-centred in this slot
FOCUS = (FIG_CX, 880)                                    # where the dots thin out and the lines aim
BURST_CX, BURST_CY = 832, 650                            # NEW THAT DAY! (right of the head, under the price box)
NOTE_X, NOTE_Y, NOTE_W = 664, 566, 348                   # "in the Item Shop that day"
BAN_X, BAN_BOTTOM, BAN_W = 58, 1340, 830                 # the title banner, bottom-anchored
ROW_Y, ROW_H = 1360, 50                                  # the mini panels, along the foot of the box

INK_FILTER = f"url(#cmink) drop-shadow(11px 10px 0 {INK})"

CSS = """
.cm-paper{background:#efe5cc url('@paper@') center/cover}
.cm-grain{position:absolute;inset:0;pointer-events:none;background:url('@grain@') 0 0/512px 512px;
  mix-blend-mode:multiply;opacity:.6}
.cm-dots{position:absolute;-webkit-mask:url('@dots@') no-repeat;mask:url('@dots@') no-repeat;
  -webkit-mask-size:1300px 1300px;mask-size:1300px 1300px}
.cm-lines{position:absolute;-webkit-mask:url('@lines@') no-repeat;mask:url('@lines@') no-repeat;
  -webkit-mask-size:1440px 1440px;mask-size:1440px 1440px}
.cm-k{font-family:'Kalam',cursive;font-weight:700;text-transform:uppercase;color:@INK@;line-height:1.08}
.cm-o{font-family:'Oswald',sans-serif;font-weight:700;text-transform:uppercase;color:@INK@}
.cm-a{font-family:'Archivo Black',sans-serif;font-weight:400;text-transform:uppercase;line-height:1}
.cm-n{font-family:'Anton',sans-serif;text-transform:uppercase;line-height:1.02}
.cm-sh{position:absolute;inset:0;background:@INK@}
.cm-fill{position:absolute;inset:0;transform:translate(@MX@px,@MY@px)}
.cm-frame{position:absolute;inset:0;border:5px solid @INK@}
@keyframes cmshade{from{opacity:0}to{opacity:1}}
@keyframes cmplace{0%{opacity:0;transform:translate(-16px,-22px) rotate(calc(var(--r,0deg) - 5deg)) scale(1.05)}
  1%{opacity:1}
  60%{opacity:1;transform:translate(1px,2px) rotate(calc(var(--r,0deg) + .6deg)) scale(.995)}
  100%{opacity:1;transform:rotate(var(--r,0deg))}}
@keyframes cmprint{0%{opacity:0;transform:scale(1.28) rotate(var(--r,0deg))}1%{opacity:1}
  50%{opacity:1;transform:scale(.975) rotate(var(--r,0deg))}100%{opacity:1;transform:scale(1) rotate(var(--r,0deg))}}
@keyframes cmrise{0%{transform:translateY(40px) scale(.94)}60%{transform:translateY(-5px) scale(1.008)}
  100%{transform:none}}
@keyframes cmslide{0%{transform:translateX(-1150px)}70%{transform:translateX(12px)}100%{transform:none}}
@keyframes cmpop{0%{opacity:0;transform:scale(.4) rotate(var(--r,0deg))}1%{opacity:1}
  60%{opacity:1;transform:scale(1.07) rotate(var(--r,0deg))}100%{opacity:1;transform:scale(1) rotate(var(--r,0deg))}}
@keyframes cmslam{0%{opacity:0;transform:scale(2.2) rotate(calc(var(--r,0deg) - 22deg))}1%{opacity:1}
  45%{opacity:1;transform:scale(.9) rotate(calc(var(--r,0deg) + 3deg))}
  72%{transform:scale(1.035) rotate(var(--r,0deg))}100%{opacity:1;transform:scale(1) rotate(var(--r,0deg))}}
@keyframes cmdrift{from{transform:scale(1)}to{transform:scale(1.06)}}
@keyframes cmthump{0%,100%{transform:scale(1)}35%{transform:scale(1.05)}}
@keyframes cmshake{0%,100%{transform:none}20%{transform:translate(-6px,4px)}45%{transform:translate(5px,-3px)}
  70%{transform:translate(-2px,2px)}}
"""


# ---------------------------------------------------------------- helpers

def _a(name: str, t: float, dur: float, ease: str = "cubic-bezier(.2,.8,.2,1)", extra: str = "") -> str:
    return f"animation:{name} {dur:.3f}s {ease} {t:.3f}s 1 normal both;{extra}"


def _hex(c: str) -> tuple:
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def _mix(a: str, b: str, k: float) -> str:
    x, y = _hex(a), _hex(b)
    return "#" + "".join(f"{round(p + (q - p) * k):02x}" for p, q in zip(x, y))


def _rarity(it: dict) -> str:
    c = RARITY.get(it.get("rarity"), "#9AA0A6")
    return c if c.startswith("#") and len(c) == 7 else "#9AA0A6"


def _light(c: str) -> bool:
    r, g, b = _hex(c)
    return .299 * r + .587 * g + .114 * b > 150


def _ordinal(n: int) -> str:
    return f"{n}{'TH' if 10 <= n % 100 <= 20 else {1: 'ST', 2: 'ND', 3: 'RD'}.get(n % 10, 'TH')}"


def _box(inner: str, fill: str, style: str, pad: str = "10px 18px", shadow: int = 8, border: int = 5,
         cls: str = "", attrs: str = "") -> str:
    """A printed box: the black plate (frame, letters and hard shadow) and the
    colour plate a few pixels off it, like cheap four-colour printing."""
    return (f'<div class="abs {cls}" {attrs} style="{style}">'
            f'<div class="cm-sh" style="transform:translate({shadow}px,{shadow}px)"></div>'
            f'<div class="cm-fill" style="background:{fill}"></div>'
            f'<div class="cm-frame" style="border-width:{border}px"></div>'
            f'<div style="position:relative;padding:{pad}">{inner}</div></div>')


def _block(text: str, size: float, fill: str, stroke: float = 15, depth: int = 10, cls: str = "cm-a",
           extra: str = "", grad: str = "") -> str:
    """Block letters: a fill, a thick ink outline and a solid ink extrusion
    down and to the right (stacked outlined copies; the copies are decoration).
    grad: a CSS gradient for the face instead of the flat fill."""
    copies = "".join(
        f'<div class="abs" data-safe="ignore" style="left:{d}px;top:{d}px;color:{INK};'
        f'-webkit-text-stroke:{stroke}px {INK};white-space:nowrap">{esc(text)}</div>'
        for d in range(2, depth + 1, 2))
    face = ""
    if grad:
        face = (f'<div class="abs" data-safe="ignore" style="left:0;top:0;white-space:nowrap;color:transparent;'
                f'background:{grad};-webkit-background-clip:text;background-clip:text">{esc(text)}</div>')
    return (f'<div class="{cls}" style="position:relative;font-size:{size:.0f}px;white-space:nowrap;{extra}">'
            f'{copies}<div style="position:relative;color:{fill};-webkit-text-stroke:{stroke}px {INK};'
            f'paint-order:stroke fill">{esc(text)}</div>{face}</div>')


def _burst_pts(rx: float, ry: float, n: int, seed: int) -> str:
    rnd = random.Random(seed)
    pts = []
    a0 = rnd.uniform(0, math.pi / n)
    for i in range(2 * n):
        a = a0 + math.pi * i / n + rnd.uniform(-.05, .05)
        k = rnd.uniform(.9, 1.0) if i % 2 == 0 else rnd.uniform(.66, .76)
        pts.append(f"{rx + math.cos(a) * rx * k:.1f},{ry + math.sin(a) * ry * k:.1f}")
    return " ".join(pts)


def _burst(inner: str, cx: float, cy: float, w: float, h: float, fill: str, seed: int, rot: float,
           anim: str = "", n: int = 15) -> str:
    """A jagged comic burst (a shape, drawn in ink) with lettering in it."""
    pts = _burst_pts(w / 2, h / 2, n, seed)
    return (f'<div class="abs" style="left:{cx - w / 2:.0f}px;top:{cy - h / 2:.0f}px;width:{w:.0f}px;'
            f'height:{h:.0f}px;--r:{rot}deg;transform:rotate({rot}deg);{anim}">'
            f'<svg class="abs" data-safe="ignore" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" '
            f'style="left:0;top:0;overflow:visible">'
            f'<polygon points="{pts}" fill="{INK}" transform="translate(9 9)"/>'
            f'<polygon points="{pts}" fill="{fill}" transform="translate({MX} {MY})"/>'
            f'<polygon points="{pts}" fill="none" stroke="{INK}" stroke-width="6" stroke-linejoin="miter"/>'
            f'</svg><div class="abs" style="inset:0;display:flex;flex-direction:column;align-items:center;'
            f'justify-content:center;text-align:center">{inner}</div></div>')


def _panel_bg(color: str, x: float, y: float, w: float, h: float, focus: tuple, t0, dur: float,
              lines: float = .78, tint: float = .74, base: str = "", dot: str = "") -> str:
    """The panel's printed art: a light tint of the colour, Ben-Day dots of it
    that thin out towards the focus, and ink focus lines aimed at it. It drifts
    in a little over the page (a slow push, like a motion comic)."""
    fx, fy = focus[0] - x, focus[1] - y
    m = 60                                              # room for the drift
    drift = _a("cmdrift", t0, dur, "linear") if t0 is not None else ""
    mp = f"-webkit-mask-position:{fx + m - 650:.0f}px {fy + m - 650:.0f}px;mask-position:{fx + m - 650:.0f}px {fy + m - 650:.0f}px;"
    ml = f"-webkit-mask-position:{fx + m - 720:.0f}px {fy + m - 720:.0f}px;mask-position:{fx + m - 720:.0f}px {fy + m - 720:.0f}px;"
    return (f'<div class="abs" data-safe="ignore" style="left:{x + MX:.0f}px;top:{y + MY:.0f}px;width:{w:.0f}px;'
            f'height:{h:.0f}px;overflow:hidden">'
            f'<div class="abs" style="left:{-m}px;top:{-m}px;width:{w + 2 * m:.0f}px;height:{h + 2 * m:.0f}px;'
            f'transform-origin:{fx + m:.0f}px {fy + m:.0f}px;{drift}">'
            f'<div class="abs" style="inset:0;background:{base or _mix(color, PAPER, tint)};mix-blend-mode:multiply"></div>'
            f'<div class="cm-dots" style="inset:0;background:{dot or color};mix-blend-mode:multiply;{mp}"></div>'
            + (f'<div class="cm-lines" style="inset:0;background:{INK};opacity:{lines};{ml}"></div>' if lines else "")
            + f'</div></div>'
            f'<div class="abs" data-safe="ignore" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;'
            f'height:{h:.0f}px;border:{PB}px solid {INK}"></div>')


def _tier(color: str) -> str:
    """Below the row of years the page's next tier of panels runs on under the
    apps' captions: pale, quiet halftone with nothing to read in it."""
    y = ROW_Y + ROW_H + 38
    h = 1920 - 44 - y
    base, dot = _mix(color, PAPER, .86), _mix(color, PAPER, .5)
    return (_panel_bg(color, 34, y, 352, h, (34 + 352 * .7, y + h * .45), None, 0, 0, base=base, dot=dot)
            + _panel_bg(color, 410, y, 636, h, (410 + 636 * .3, y + h * .5), None, 0, .22, base=base, dot=dot))


# ---------------------------------------------------------------- the cosmetic

# After PREP_JS has cropped each cosmetic to itself (data-trim): scale it to
# fit its slot, and draw its ink outline and hard shadow into the image once
# (at the size it's shown, so the outline is the same weight on every item).
# The image keeps the fitted size as its layout box; the outline and shadow
# hang over it in a margin.
FIG_JS = """<script>(() => {
  const prev = window.__ready;
  window.__ready = (async () => {
    if (prev) { try { await prev; } catch (e) {} }
    for (const img of document.querySelectorAll('img[data-cmfig]')) {
      try {
        if (img.decode) { await img.decode(); }
        const w = img.naturalWidth, h = img.naturalHeight;
        if (!w || !h) continue;
        const mw = +img.dataset.mw, mh = +img.dataset.mh, P = 26;
        const s = Math.min(mw / w, mh / h, 1.35);
        const dw = Math.max(1, Math.round(w * s)), dh = Math.max(1, Math.round(h * s));
        const c = document.createElement('canvas');
        c.width = dw + 2 * P; c.height = dh + 2 * P;
        const g = c.getContext('2d');
        g.filter = img.dataset.cmfig;
        g.drawImage(img, P, P, dw, dh);
        img.src = c.toDataURL('image/png');
        if (img.decode) { await img.decode(); }
        const st = img.style;
        st.maxWidth = 'none'; st.maxHeight = 'none';
        st.width = (dw + 2 * P) + 'px'; st.height = (dh + 2 * P) + 'px';
        st.margin = (-P) + 'px';
      } catch (e) {}
    }
  })();
})();</script>"""


def _figure(ctx, it: dict, cx: float, bottom: float, mw: float, mh: float, anim: str = "") -> str:
    """The cosmetic, inked, standing on `bottom`, centred on cx, fitted to mw x mh."""
    art = ctx.art(it)
    if art:
        tr = 'data-trim="figure"' if trim_for(it) == "figure" else "data-trim"
        pic = (f'<img {tr} data-cmfig="{INK_FILTER}" data-mw="{mw:.0f}" data-mh="{mh:.0f}" '
               f'data-name="{esc(it["name"])}" src="{art}" style="display:block;max-width:{mw:.0f}px;'
               f'max-height:{mh:.0f}px">')
    else:
        # No picture: a mystery silhouette panel, the classic comic "who is it?"
        pw, ph = min(mw, mh * .5), mh * .9
        pic = (f'<div style="position:relative;width:{pw:.0f}px;height:{ph:.0f}px">'
               f'<div class="cm-sh" style="transform:translate(10px,10px);border-radius:40px"></div>'
               f'<div class="abs" style="inset:0;border-radius:40px;background:{_mix(_rarity(it), INK, .55)};'
               f'border:6px solid {INK}"></div>'
               f'<div class="abs cm-a" style="inset:0;display:flex;align-items:center;justify-content:center;'
               f'font-size:{pw * .7:.0f}px;color:{PAPER}">?</div></div>')
    return (f'<div class="abs" style="left:{cx - mw / 2:.0f}px;top:{bottom - mh:.0f}px;width:{mw:.0f}px;'
            f'height:{mh:.0f}px;display:flex;justify-content:center;align-items:flex-end">'
            f'<div style="transform-origin:50% 100%;{anim}">{pic}</div></div>')


# ---------------------------------------------------------------- page furniture

def _code() -> str:
    """USE CODE: BAD as the cover's price box: a black band with lime letters
    over a lime box with BAD and #EpicPartner. Its outer box is the unturned
    box itself, so the safe-zone check measures exactly it."""
    return (f'<div class="abs" data-safe="key" data-name="code" style="left:{CODE_X}px;top:{CODE_Y}px;'
            f'width:{CODE_W}px;height:{CODE_H}px">'
            f'<div class="cm-sh" style="transform:translate(10px,10px)"></div>'
            f'<div class="abs" style="inset:0;background:{LIME};display:flex;flex-direction:column;'
            f'align-items:center">'
            f'<div class="cm-k" style="width:100%;background:{INK};color:{LIME};font-size:46px;line-height:1;'
            f'text-align:center;padding:13px 0 5px;letter-spacing:.03em">USE CODE:</div>'
            f'<div class="cm-a" style="font-size:124px;line-height:1;color:#111;margin-top:6px;'
            f'letter-spacing:-.01em">BAD</div>'
            f'<div class="cm-k" style="font-size:29px;line-height:1;color:#111;margin-top:4px;'
            f'text-transform:none">#EpicPartner</div></div>'
            f'<div class="cm-frame" style="border-width:6px"></div></div>')


def _row(years: list, cur: int, t_on=None) -> str:
    """The years as mini panels along the foot of the page; this one filled."""
    n = len(years)
    gap = 10
    step = (XR - X0 + gap) / n
    w = step - gap
    size = min(31, (w - 14) / 2.0)
    out = []
    for i, y in enumerate(years):
        on, past = i == cur, i < cur
        fill = CAP if on else (_mix(PAPER, INK, .1) if past else PAPER)
        col = INK if not past or on else "#857a64"
        anim = _a("cmpop", t_on, .32, "cubic-bezier(.3,1.5,.5,1)") if (on and t_on is not None) else ""
        out.append(f'<div class="abs" style="left:{X0 + i * step:.0f}px;top:{ROW_Y}px;width:{w:.0f}px;'
                   f'height:{ROW_H}px;{anim}">'
                   + (f'<div class="cm-sh" style="transform:translate(6px,6px)"></div>' if on else "")
                   + f'<div class="abs" style="inset:0;background:{fill};border:{5 if on else 4}px solid {INK};'
                     f'display:flex;align-items:center;justify-content:center">'
                     f'<span class="cm-o" style="font-size:{size:.0f}px;line-height:1;color:{col};'
                     f'letter-spacing:.02em">{y}</span></div></div>')
    return "".join(out)


def _caption(text: str, x: float, y: float, rot: float, t, size: float = 48, maxw: float = 610) -> str:
    anim = _a("cmplace", t, .34) if t is not None else ""
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;--r:{rot}deg;transform:rotate({rot}deg);'
            f'transform-origin:0 0;{anim}">'
            + _box(f'<div class="cm-k" data-fit="{maxw - 36}" style="font-size:{size}px;white-space:nowrap">'
                   f'{esc(text)}</div>', CAP, "position:relative", "8px 18px 4px") + '</div>')


def _year(y: int, color: str, t) -> str:
    anim = _a("cmprint", t, .36, "cubic-bezier(.25,.9,.3,1)") if t is not None else ""
    return (f'<div class="abs" style="left:{X0 + 4}px;top:{YEAR_Y}px;--r:-3deg;transform:rotate(-3deg);'
            f'transform-origin:30% 60%;{anim}">'
            + _block(str(y), YEAR_SIZE, color, 16, 12, extra="transform:skewX(-7deg)") + '</div>')


def _banner(name: str, kind: str, rarity_col: str, t) -> str:
    """The name on a red title banner (bottom-anchored, one or two lines, as
    wide as the name needs), its rarity and type in a small box on its top edge."""
    tw = BAN_W - 64
    one = min(104, tw / max(anton_em(name) - .1, .1))
    if one >= 70:
        size = one
        wrap = 'style="display:inline-block;white-space:nowrap;'
    else:
        size = min(86, 2.05 * tw / max(anton_em(name), .1))
        wrap = f'data-lines="2" style="width:{tw}px;text-wrap:balance;'
    slide = _a("cmslide", t, .5, "cubic-bezier(.22,.9,.3,1)") if t is not None else ""
    pop = _a("cmpop", t + .32, .3, "cubic-bezier(.3,1.5,.5,1)") if t is not None else ""
    tab_fg = INK if _light(rarity_col) else "#fff"
    tab = (f'<div style="display:flex;justify-content:flex-end;padding:0 28px 0 40px;margin-bottom:-14px;'
           f'position:relative;z-index:2">'
           f'<div style="--r:2deg;transform:rotate(2deg);{pop}">'
           + _box(f'<div class="cm-o" data-fit="{tw - 80}" style="display:inline-block;font-size:33px;'
                  f'line-height:1.1;color:{tab_fg};letter-spacing:.05em;white-space:nowrap">{esc(kind)}</div>',
                  rarity_col, "position:relative", "5px 16px 4px", 6, 4) + '</div></div>')
    name_el = (f'<div class="cm-n" data-fit="{tw}" {wrap}font-size:{size:.0f}px;color:#fff;'
               f'-webkit-text-stroke:10px {INK};paint-order:stroke fill;letter-spacing:.01em">{esc(name)}</div>')
    return (f'<div class="abs" style="left:{BAN_X}px;bottom:{1920 - BAN_BOTTOM}px;max-width:{BAN_W}px;{slide}">'
            f'{tab}<div style="transform:skewX(-9deg);transform-origin:0 100%">'
            + _box(f'<div style="transform:skewX(9deg);text-align:center;min-width:360px">{name_el}</div>', RED,
                   "position:relative", "12px 26px 10px 30px", 10, 6) + '</div></div>')


def _note(text: str, t) -> str:
    """A second caption, the sentence the date caption started."""
    anim = _a("cmplace", t, .34) if t is not None else ""
    return (f'<div class="abs" style="left:{NOTE_X}px;top:{NOTE_Y}px;width:{NOTE_W}px;--r:2deg;'
            f'transform:rotate(2deg);{anim}">'
            + _box(f'<div class="cm-k" data-fit="{NOTE_W - 40}" data-lines="3" style="width:{NOTE_W - 40}px;'
                   f'font-size:46px;line-height:1.05;text-wrap:balance">{esc(text)}</div>', CAP,
                   "position:relative", "10px 20px 6px") + '</div>')


def _new_burst(t, seed: int) -> str:
    anim = _a("cmslam", t, .42, "cubic-bezier(.2,.8,.3,1)") if t is not None else ""
    inner = (f'<div class="cm-a" style="font-size:78px;line-height:.9;color:#fff;-webkit-text-stroke:9px {INK};'
             f'paint-order:stroke fill">NEW</div>'
             f'<div class="cm-a" style="font-size:40px;line-height:1.05;color:#fff;-webkit-text-stroke:7px {INK};'
             f'paint-order:stroke fill;margin-top:4px">THAT DAY!</div>')
    return _burst(inner, BURST_CX, BURST_CY, 350, 250, RED, seed, -7, anim)


# ---------------------------------------------------------------- pages

def _kf_turn() -> str:
    """The page turn: the page swings towards the viewer about its left edge
    (the spine), faster as it goes, and a shadow band runs across the page
    under it just ahead of its edge. Keyframes follow the projected edge."""
    P, W_ = 2600.0, 1080.0
    steps = 24
    page, shadow = [], []
    for i in range(steps + 1):
        u = i / steps
        e = u ** 1.9                                  # accelerating
        th = math.radians(91 * e)
        xp, zp = W_ * math.cos(th), W_ * math.sin(th)
        edge = 540 + (xp - 540) * P / max(P - zp, 1)
        page.append(f"{u * 100:.2f}%{{transform:rotateY({-91 * e:.2f}deg)}}")
        op = min(1, u * 3) * (1 - max(0, (u - .8) / .2))
        shadow.append(f"{u * 100:.2f}%{{transform:translateX({max(-420, min(1100, edge)):.0f}px);opacity:{op:.2f}}}")
    return ("@keyframes cmturn{" + "".join(page) + "}"
            + "@keyframes cmcast{" + "".join(shadow) + "}")


def _page(inner: str, t_turn, cast_at=None) -> str:
    """A whole printed page: paper, `inner`, grain over the inks. It turns away
    at t_turn (None: it never does); cast_at: when the page before it turns
    away (its shadow sweeps across this one)."""
    turn = shade = ""
    if t_turn is not None:
        turn = f"animation:cmturn {TURN:.3f}s linear {t_turn:.3f}s 1 normal both;"
        shade = _a("cmshade", t_turn, TURN, "cubic-bezier(.6,0,.9,.6)")
    cast = ""
    if cast_at is not None:
        cast = (f'<div class="abs" data-safe="ignore" style="left:0;top:0;width:620px;height:1920px;'
                f'background:linear-gradient(90deg,rgba(28,20,6,.66),rgba(28,20,6,.3) 28%,rgba(28,20,6,0));'
                f'animation:cmcast {TURN:.3f}s linear {cast_at:.3f}s 1 normal both"></div>')
    return (f'<div class="full" style="perspective:2600px;perspective-origin:540px 960px">'
            f'<div class="full cm-paper" style="transform-origin:0 50%;backface-visibility:hidden;'
            f'-webkit-backface-visibility:hidden;overflow:hidden;{turn}">'
            f'{inner}<div class="cm-grain"></div>{cast}'
            f'<div class="abs" data-safe="ignore" style="inset:0;background:linear-gradient(90deg,'
            f'rgba(30,22,8,.14),rgba(30,22,8,.74));opacity:0;{shade}"></div>'
            f'</div></div>')


def _page_year(ctx, rd, it, debut, t0: float, idx: int, years: list, r: float, when: str) -> tuple:
    y = rd["year"]
    col = _rarity(it)
    kind = " ".join(x for x in (it.get("rarity_label") or "", it.get("type") or "") if x).strip()
    rev = t0 - TURN_LEAD                                    # this page starts to show
    html = [_panel_bg(col, PX, PY, PW, PH, FOCUS, rev, r + TURN_LEAD),
            _figure(ctx, it, FIG_CX, FIG_BOTTOM, FIG_W, FIG_H, _a("cmrise", t0 - .05, .55, "cubic-bezier(.25,.8,.3,1)")),
            _caption(f"{when.upper()}, {y} —", X0, CAP_Y, -1.5, t0 + .02),
            _year(y, col, t0 + .2),
            _banner(it["name"], kind.upper(), col, t0 + .55),
            _row(years, idx, t0 + .3),
            _tier(col)]
    sounds = [(t0 + .02, "paper"), (t0 + .2, "slam"), (t0 + .55, "whoosh"), (t0 + .87, "pop")]
    if debut:
        html.append(_new_burst(t0 + 1.15, y * 7 + idx))
        sounds.append((t0 + 1.15, "slam"))
    else:
        html.append(_note("in the Item Shop that day", t0 + 1.1))
        sounds.append((t0 + 1.1, "paper"))
    return "".join(html), sounds


def _page_origin(bday: dict, t0: float, years: list, r: float, when: str) -> tuple:
    """Sep 26: the ORIGIN STORY splash page -- Battle Royale comes out."""
    y = bday["year"]
    rev = t0 - TURN_LEAD
    col = "#f39a1e"
    title = "".join(
        f'<div style="{_a("cmprint", t0 + .35 + i * .14, .34, "cubic-bezier(.25,.9,.3,1)")}">'
        + _block(line, size, "#fff", 13, 10) + '</div>'
        for i, (line, size) in enumerate((("FORTNITE", 104), ("BATTLE ROYALE", 86), ("COMES OUT!", 104))))
    html = [_panel_bg(col, PX, PY, PW, PH, (480, 900), rev, r + TURN_LEAD, lines=.85, tint=.7),
            _caption(f"{when.upper()}, {y} —", X0, CAP_Y, -1.5, t0 + .02),
            _year(y, RED, t0 + .2),
            # the splash's title tab, on the panel's top edge
            f'<div class="abs" style="left:{X0 + 6}px;top:{PY - 30}px;--r:-2deg;transform:rotate(-2deg);'
            f'{_a("cmplace", t0 + .25, .34)}">'
            + _box(f'<div class="cm-a" style="font-size:44px;line-height:1.1;color:#fff;letter-spacing:.04em">'
                   f'ORIGIN STORY</div>', INK, "position:relative", "6px 20px 4px", 8, 5) + '</div>',
            f'<div class="abs" style="left:{X0}px;top:760px;width:{XR - X0}px;display:flex;flex-direction:column;'
            f'align-items:center;gap:2px;transform:rotate(-2deg)">{title}</div>',
            f'<div class="abs" style="left:{X0}px;top:1086px;width:{XR - X0}px;display:flex;'
            f'justify-content:center">'
            f'<div style="--r:1deg;transform:rotate(1deg);{_a("cmplace", t0 + .95, .34)}">'
            + _box('<div class="cm-o" style="font-size:40px;line-height:1.15;letter-spacing:.04em;'
                   'white-space:nowrap">PC · PLAYSTATION 4 · XBOX ONE</div>', CAP, "position:relative",
                   "6px 22px 4px") + '</div></div>',
            _burst(f'<div class="cm-a" style="font-size:58px;line-height:1;color:#fff;-webkit-text-stroke:8px {INK};'
                   f'paint-order:stroke fill">HAPPY {_ordinal(bday["age"])}</div>'
                   f'<div class="cm-a" style="font-size:58px;line-height:1.05;color:#fff;-webkit-text-stroke:8px {INK};'
                   f'paint-order:stroke fill">BIRTHDAY!</div>', 470, 1232, 520, 240, RED, 99, -4,
                   _a("cmslam", t0 + 1.5, .44, "cubic-bezier(.2,.8,.3,1)"), 18),
            _row(years, 0, t0 + .3),
            _tier(col)]
    sounds = [(t0 + .02, "paper"), (t0 + .2, "slam"), (t0 + .35, "whoosh"), (t0 + .95, "paper"),
              (t0 + 1.5, "slam"), (t0 + 1.7, "clap")]
    return "".join(html), sounds


def _cover(ctx, lead: list, years: list, when_short: str, bday) -> str:
    """Frame 0: the comic's cover, complete."""
    a, b = lead[0][1], lead[1][1]
    span = f"{years[0]}–{years[-1]}"
    face = "linear-gradient(180deg,#ffe36b 0%,#ffd03f 45%,#ff9d24 100%)"
    logo = (f'<div class="abs" style="left:{X0 + 20}px;top:302px;transform:rotate(-4deg) skewX(-8deg);'
            f'transform-origin:0 0">'
            + _block("ON THIS", 118, CAP, 16, 12, grad=face)
            + f'<div style="margin-top:-18px;margin-left:34px">' + _block("DAY", 208, CAP, 18, 14, grad=face)
            + '</div></div>')
    html = [_panel_bg(BLUE, PX, PY, PW, PH, (470, 900), None, 0, lines=.8, tint=.72),
            _figure(ctx, b, 612, 1230, 360, 640),
            _figure(ctx, a, 300, 1236, 420, 684),
            logo]
    if bday:
        html.append(_burst(f'<div class="cm-a" style="font-size:52px;line-height:1;color:#fff;'
                           f'-webkit-text-stroke:8px {INK};paint-order:stroke fill">FORTNITE</div>'
                           f'<div class="cm-a" style="font-size:52px;line-height:1.05;color:#fff;'
                           f'-webkit-text-stroke:8px {INK};paint-order:stroke fill">TURNS {bday["age"]}!</div>',
                           BURST_CX, BURST_CY + 6, 360, 260, RED, 5, -6))
        sub = f"Battle Royale came out on this day in {bday['year']}"
    else:
        html.append(_note("one outfit from this date, every year!", None))
        sub = ""
    ban = (f'<div class="abs" style="left:{BAN_X}px;bottom:{1920 - BAN_BOTTOM}px;width:{BAN_W}px">'
           + (f'<div style="display:flex;justify-content:flex-start;margin-bottom:-12px;position:relative;z-index:2;'
              f'padding-left:22px"><div style="transform:rotate(-1.5deg)">'
              + _box(f'<div class="cm-k" data-fit="{BAN_W - 120}" style="font-size:36px;white-space:nowrap">'
                     f'{esc(sub)}</div>', CAP, "position:relative", "6px 16px 2px", 6, 4) + '</div></div>'
              if sub else "")
           + f'<div style="transform:skewX(-9deg);transform-origin:0 100%">'
           + _box(f'<div style="transform:skewX(9deg);display:flex;align-items:baseline;gap:22px;'
                  f'justify-content:center">'
                  f'<span class="cm-n" style="font-size:96px;color:#fff;-webkit-text-stroke:10px {INK};'
                  f'paint-order:stroke fill">{esc(when_short.upper())}</span>'
                  f'<span class="cm-n" style="font-size:96px;color:#fff;-webkit-text-stroke:10px {INK};'
                  f'paint-order:stroke fill">·</span>'
                  f'<span class="cm-n" style="font-size:96px;color:#fff;-webkit-text-stroke:10px {INK};'
                  f'paint-order:stroke fill">{esc(span)}</span></div>', RED, "position:relative",
                  "10px 26px 8px", 10, 6) + '</div></div>')
    html.append(ban)
    html.append(_row(years, -1))
    html.append(_tier(BLUE))
    return "".join(html)


def _outro(ctx, picks: list, t: float, years: list) -> tuple:
    """The last page: the question in a big balloon over the lead picks, each
    with its year, and THE END? lettered under them."""
    n = len(picks)
    slots = [(226, 1214, 300, 600), (530, 1214, 290, 560), (764, 1214, 190, 470)][:n]
    if n == 2:
        slots = [(290, 1214, 360, 600), (640, 1214, 330, 560)]
    figs, tags = [], []
    for i, ((it, yr), (cx, bot, mw, mh)) in enumerate(zip(picks, slots)):
        figs.append(_figure(ctx, it, cx, bot, mw, mh, _a("cmrise", t + .45 + i * .18, .5, "cubic-bezier(.25,.8,.3,1)")))
        if yr:
            tags.append(f'<div class="abs" style="left:{cx - 70:.0f}px;top:{bot - 30:.0f}px;width:140px;'
                        f'display:flex;justify-content:center">'
                        f'<div style="--r:{(-3, 2, -2)[i]}deg;transform:rotate({(-3, 2, -2)[i]}deg);'
                        f'{_a("cmpop", t + .75 + i * .18, .3, "cubic-bezier(.3,1.5,.5,1)")}">'
                        + _box(f'<div class="cm-o" style="font-size:40px;line-height:1.1;letter-spacing:.03em">{yr}</div>',
                               CAP, "position:relative", "3px 14px 1px", 6, 4) + '</div></div>')
    bw, bh = 640, 330
    bx, by = X0 - 6, 292
    tail = f"M {bw * .42:.0f} {bh - 30:.0f} L {bw * .30:.0f} {bh + 120:.0f} L {bw * .58:.0f} {bh - 38:.0f} Z"
    oval = f'<ellipse cx="{bw / 2:.0f}" cy="{bh / 2:.0f}" rx="{bw / 2 - 8:.0f}" ry="{bh / 2 - 8:.0f}"/>'
    balloon = (f'<div class="abs" style="left:{bx}px;top:{by}px;width:{bw}px;height:{bh}px;--r:-2deg;'
               f'transform:rotate(-2deg);transform-origin:40% 100%;{_a("cmpop", t + .05, .4, "cubic-bezier(.3,1.4,.5,1)")}">'
               f'<svg class="abs" data-safe="ignore" width="{bw}" height="{bh + 130}" style="left:0;top:0;overflow:visible">'
               f'<g fill="{INK}" transform="translate(10 10)">{oval}<path d="{tail}"/></g>'
               f'<g fill="{PAPER}" stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
               f'<path d="{tail}"/>{oval}</g>'
               f'<path d="M {bw * .42 + 6:.0f} {bh - 36:.0f} L {bw * .58 - 6:.0f} {bh - 42:.0f}" stroke="{PAPER}" '
               f'stroke-width="12"/></svg>'
               f'<div class="abs cm-k" data-fit="{bw - 150}" data-lines="3" style="left:75px;top:52px;'
               f'width:{bw - 150}px;height:{bh - 100}px;font-size:76px;line-height:1.02;text-align:center;'
               f'display:flex;align-items:center;justify-content:center;text-wrap:balance">'
               f'Which year had the best shop?</div></div>')
    end = (f'<div class="abs" style="left:{X0 + 60}px;top:1244px;width:{XR - X0 - 120}px;display:flex;'
           f'justify-content:center;align-items:baseline;gap:14px;--r:-3deg;transform:rotate(-3deg);'
           f'{_a("cmprint", t + 2.2, .4, "cubic-bezier(.25,.9,.3,1)")}">'
           + _block("THE END", 84, "#fff", 13, 10)
           + f'<div class="cm-k" style="font-size:120px;line-height:.8;color:{RED};-webkit-text-stroke:8px {INK};'
             f'paint-order:stroke fill;transform:rotate(12deg)">?</div></div>')
    html = (_panel_bg(CAP, PX, PY, PW, PH, (480, 900), t - TURN_LEAD, 9, lines=.7, tint=.72)
            + "".join(figs) + "".join(tags) + balloon + end + _row(years, -1) + _tier(CAP))
    sounds = [(t + .05, "pop"), (t + .45, "whoosh")] + [(t + .75 + i * .18, "pop") for i in range(len(tags))]
    sounds += [(t + 2.2, "slam")]
    return html, sounds


# ---------------------------------------------------------------- build

def on_this_day(ctx, rounds: list, bday: dict, lead: list, third) -> Comp:
    day = ctx.day
    when = day.strftime("%B %-d")
    when_short = day.strftime("%b %-d")
    years = ([bday["year"]] if bday else []) + [rd["year"] for rd, _, _ in rounds]
    n = len(years)
    r = max(R, (62.0 - 7.5 - HOOK) / n)
    content_end = HOOK + n * r
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    css = CSS
    for k, v in (("paper", tex("comic-newsprint.jpg")), ("grain", tex("comic-grain.png")),
                 ("dots", tex("comic-dots.png")), ("lines", tex("comic-lines.png")), ("INK", INK),
                 ("MX", str(MX)), ("MY", str(MY))):
        css = css.replace(f"@{k}@", v)
    comp.css(KIT_CSS)
    comp.css(css)
    comp.css(_kf_turn())

    # Under everything: bare newsprint (only ever seen past a page's edge).
    comp.add('<div class="full cm-paper" style="z-index:0"></div>')
    comp.add(diecut_filter("cmink", 6, INK))
    comp.add(PREP_JS)
    comp.add(FIG_JS)

    # ---- the pages, each over the next: the cover, (the origin story,) the years, the last page
    z = 80
    t_turn = HOOK - TURN_LEAD
    comp.scene(0, t_turn + TURN + .02, _page(_cover(ctx, lead, years, when_short, bday), t_turn),
               fade_in=.01, fade_out=.01, z=z)
    comp.cue(t_turn, "flip"); comp.cue(t_turn + .25, "paper")
    pages = []
    if bday:
        pages.append(_page_origin(bday, HOOK, years, r, when))
    for j, (rd, it, debut) in enumerate(rounds):
        k = len(pages)
        pages.append(_page_year(ctx, rd, it, debut, HOOK + k * r, k, years, r, when))
    for i, (html, sounds) in enumerate(pages):
        t0 = HOOK + i * r
        t_out = t0 + r - TURN_LEAD
        comp.scene(t0 - TURN_LEAD - .02, t_out + TURN + .02, _page(html, t_out, cast_at=t0 - TURN_LEAD),
                   fade_in=.01, fade_out=.01, z=z - 1 - i)
        for s in sounds:
            comp.cue(*s)
        comp.cue(t_out, "flip"); comp.cue(t_out + .25, "paper")

    # ---- the last page
    yr_of = {id(it): rd["year"] for rd, it, _ in rounds}
    picks = [(x[1], x[0]["year"]) for x in lead] + ([(third, yr_of.get(id(third)))] if third else [])
    t = content_end
    html, sounds = _outro(ctx, picks, t, years)
    comp.scene(t - TURN_LEAD - .02, comp.duration, _page(html, None, cast_at=t - TURN_LEAD),
               fade_in=.01, fade_out=.01, z=z - 1 - len(pages))
    for s in sounds:
        comp.cue(*s)

    # ---- the price box: above every page, in every frame
    comp.add(f'<div class="full" style="z-index:95;{_a("cmthump", t + .1, .4, "ease-out")}'
             f'transform-origin:{CODE_X + CODE_W / 2}px {CODE_Y + CODE_H / 2}px">{_code()}</div>')
    comp.cues.sort()
    return comp
