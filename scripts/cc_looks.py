"""
The new looks -- each video type drawn as something a person made (a scrapbook
page, a trading card, a departures board...) instead of the neon-glow template.

A look only changes the picture. The facts, the titles and the captions are the
format's own: a format builder picks its data exactly as before, then asks
get(format) for a look; when one is switched on it draws the Comp, otherwise the
format draws its classic scenes.

Switches
    creator-code/looks.json   {"on_this_day": true, ...}: the looks that are live.
                              A look goes live only after full-length renders
                              with real art have been checked (creator-code/LOOKS.md).
    CC_LOOKS (env)            overrides the file, for preview builds:
                              "all", "none", or a list like "on_this_day,og_check".

The rest of this module is the kit every look shares: textures, hand-drawn
marker strokes, write-on text and the lime code element rules.
"""

import base64
import importlib
import json
import math
import os
import random
from functools import lru_cache
from pathlib import Path

from cc_motion import ACCENT, W, H

ROOT = Path(__file__).resolve().parent.parent
SWITCHES = ROOT / "creator-code" / "looks.json"
TEXTURES = ROOT / "creator-code" / "assets" / "textures"

# format (or "format@series") -> the module that draws it
LOOKS = {
    "on_this_day": "cc_look_scrapbook",
    "throwback@fortnitemares": "cc_look_vhs",
    "guess_season": "cc_look_yearbook",
    "throwback": "cc_look_yearbook",
    "whos_that": "cc_look_card",
    "odd_one_out": "cc_look_caseboard",
    "last_chance": "cc_look_departures",
    "bundle_math": "cc_look_receipt",
    "og_check": "cc_look_museum",
}

LIME = ACCENT            # the code's colour in every look: the channel's lime
CODE_WORDS = ("USE CODE:", "BAD")


def _switched_on() -> set:
    env = os.environ.get("CC_LOOKS", "").strip()
    if env:
        if env == "all":
            return set(LOOKS)
        if env == "none":
            return set()
        return {k.strip() for k in env.split(",") if k.strip()}
    try:
        return {k for k, v in json.loads(SWITCHES.read_text()).items() if v is True}
    except (OSError, ValueError):
        return set()


def get(fmt: str, series: str = ""):
    """The look module for this format, or None when it isn't switched on."""
    key = f"{fmt}@{series}" if series else fmt
    if key not in LOOKS or key not in _switched_on():
        return None
    try:
        return importlib.import_module(LOOKS[key])
    except ModuleNotFoundError:
        return None


# ------------------------------------------------------------------ assets

@lru_cache(None)
def tex(name: str) -> str:
    """A texture from creator-code/assets/textures as a data URI (the renderer
    loads pages with set_content, so everything is embedded)."""
    path = TEXTURES / name
    mime = "image/png" if path.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def pad_to(content_end: float, minimum: float = 62.0, outro: float = 7.5) -> float:
    """Total length: at least `outro` seconds after the content, and at least
    `minimum` overall (TikTok's one-minute bar, with margin)."""
    return max(content_end + outro, minimum)


# ------------------------------------------------------------------ hand-drawn strokes

def _catmull(pts, closed=False):
    """Smooth SVG path through points (Catmull-Rom -> cubic Bezier)."""
    pts = ([pts[-1]] + pts + [pts[0], pts[1]]) if closed else ([pts[0]] + pts + [pts[-1]])
    d = f"M{pts[1][0]:.1f},{pts[1][1]:.1f}"
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def _plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def rough_ellipse(cx, cy, rx, ry, seed=1, overshoot=.18, wobble=.05, start=-100):
    """A marker circle as a person draws it: one loop, slightly off, overshooting
    where it started. Returns (path_d, approx_length)."""
    rnd = random.Random(seed)
    n = 18
    a0 = math.radians(start + rnd.uniform(-20, 20))
    total = 2 * math.pi * (1 + overshoot)
    drift = rnd.uniform(-.06, .06)
    pts = []
    for i in range(n + 1):
        t = i / n
        a = a0 + total * t
        k = 1 + rnd.uniform(-wobble, wobble) + drift * t
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return _catmull(pts), _plen(pts) * 1.05


def rough_line(x1, y1, x2, y2, seed=1, bow=.03, n=6):
    rnd = random.Random(seed)
    L = max(math.dist((x1, y1), (x2, y2)), 1)
    nx, ny = -(y2 - y1) / L, (x2 - x1) / L
    b = rnd.uniform(-bow, bow) * L
    pts = []
    for i in range(n + 1):
        t = i / n
        off = math.sin(t * math.pi) * b + rnd.uniform(-1.5, 1.5)
        pts.append((x1 + (x2 - x1) * t + nx * off, y1 + (y2 - y1) * t + ny * off))
    return _catmull(pts), _plen(pts) * 1.03


def rough_arrow(x1, y1, x2, y2, seed=1, head=34, curve=.18):
    """A curved marker arrow: body + two head strokes. Returns [(d, len), ...]."""
    rnd = random.Random(seed)
    L = max(math.dist((x1, y1), (x2, y2)), 1)
    nx, ny = -(y2 - y1) / L, (x2 - x1) / L
    b = curve * L * (1 if rnd.random() > .5 else -1)
    pts = []
    for i in range(9):
        t = i / 8
        off = math.sin(t * math.pi) * b
        pts.append((x1 + (x2 - x1) * t + nx * off, y1 + (y2 - y1) * t + ny * off))
    out = [(_catmull(pts), _plen(pts))]
    ex, ey = pts[-1]
    px, py = pts[-2]
    ang = math.atan2(ey - py, ex - px)
    for s in (1, -1):
        a = ang + math.pi - s * math.radians(28 + rnd.uniform(-5, 5))
        out.append((f"M{ex:.1f},{ey:.1f} L{ex + head * math.cos(a):.1f},{ey + head * math.sin(a):.1f}", head))
    return out


def rough_check(x, y, size=60, seed=1):
    """A hand-drawn tick mark, bottom-left of it at (x, y)."""
    rnd = random.Random(seed)
    j = lambda: rnd.uniform(-3, 3)
    a = (x + j(), y - size * .45 + j())
    b = (x + size * .35 + j(), y + j())
    c = (x + size + j(), y - size + j())
    return [(f"M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f} L{c[0]:.1f},{c[1]:.1f}",
             math.dist(a, b) + math.dist(b, c))]


def stroke_svg(paths, color="#e0262b", width=9, start=0.0, dur=.5, opacity=.92, gap=.06):
    """An SVG layer whose marker strokes draw themselves on, one after another,
    starting at `start` seconds (absolute video time)."""
    out = [f'<svg class="abs" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'style="left:0;top:0;overflow:visible;pointer-events:none">']
    t = start
    for d, L in paths:
        L = int(L) + 4
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
                   f'stroke-linejoin="round" opacity="{opacity}" style="stroke-dasharray:{L};stroke-dashoffset:{L};'
                   f'animation:lkdraw {dur:.2f}s cubic-bezier(.45,.05,.35,1) {t:.3f}s 1 normal both"/>')
        t += dur + gap
    out.append("</svg>")
    return "".join(out)


def stroke_static(paths, color="#e0262b", width=9, opacity=.92):
    """The same strokes, already drawn (for frame 0)."""
    return (f'<svg class="abs" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'style="left:0;top:0;overflow:visible;pointer-events:none">'
            + "".join(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
                      f'stroke-linejoin="round" opacity="{opacity}"/>' for d, _ in paths)
            + "</svg>")


# Keyframes every look can use. Times go in the animation shorthand, as absolute
# video seconds, like the rest of the engine (cc_motion.an).
KIT_CSS = """
@keyframes lkdraw{to{stroke-dashoffset:0}}
@keyframes lkwrite{from{clip-path:inset(-30% 100% -30% 0)}to{clip-path:inset(-30% -3% -30% 0)}}
@keyframes lkslap{0%{opacity:0;transform:translate(30px,-50px) scale(1.16) rotate(calc(var(--r,0deg) + 6deg))}
  55%{opacity:1;transform:translate(0,0) scale(.985) rotate(var(--r,0deg))}
  100%{opacity:1;transform:translate(0,0) scale(1) rotate(var(--r,0deg))}}
@keyframes lkstamp{0%{opacity:0;transform:scale(1.5) rotate(var(--r,0deg))}
  100%{opacity:1;transform:scale(1) rotate(var(--r,0deg))}}
@keyframes lkin{from{opacity:0}to{opacity:1}}
@keyframes lkout{from{opacity:1}to{opacity:0}}
"""


def write_on(t: float, dur: float = .8, steps: int = 18) -> str:
    """Inline style that reveals text left to right like handwriting."""
    return f"animation:lkwrite {dur:.2f}s steps({steps},end) {t:.3f}s 1 normal both;"


def diecut_filter(fid: str = "lkdiecut", radius: int = 14, color: str = "#fff") -> str:
    """SVG filter that gives a transparent PNG a smooth die-cut sticker border.
    Put the returned <svg> once in the page; use style="filter:url(#fid)"."""
    return (f'<svg width="0" height="0" style="position:absolute"><defs>'
            f'<filter id="{fid}" x="-15%" y="-10%" width="130%" height="120%" color-interpolation-filters="sRGB">'
            f'<feMorphology in="SourceAlpha" operator="dilate" radius="{radius}" result="d"/>'
            f'<feGaussianBlur in="d" stdDeviation="{radius / 3.5:.1f}" result="b"/>'
            f'<feComponentTransfer in="b" result="m"><feFuncA type="linear" slope="14" intercept="-6"/>'
            f'</feComponentTransfer>'
            f'<feFlood flood-color="{color}"/><feComposite in2="m" operator="in" result="w"/>'
            f'<feMerge><feMergeNode in="w"/><feMergeNode in="SourceGraphic"/></feMerge>'
            f'</filter></defs></svg>')


# Run once, before the first frame is drawn (cc_motion.READY_JS waits for
# window.__ready):
#   - img[data-trim]: Fortnite's art is a square with wide transparent margins;
#     the image is cropped to the cosmetic itself (plus 1%), so sizes mean the
#     cosmetic, not the square. Done first.
#   - img[data-bake="<css filter>"]: the filter (e.g. a die-cut border and a drop
#     shadow) is drawn into the image once, instead of on every frame. SVG filters
#     cost about three times the frame's own render time.
#   - [data-fit="<max width px>"] (and data-lines="<n>" for wrapping text, with an
#     explicit width and a unitless line-height): the text shrinks until it fits.
PREP_JS = """<script>window.__ready = (async () => {
  try {
    // The script sits before the scenes in the page: wait until they exist.
    if (document.readyState === 'loading') {
      await new Promise(r => document.addEventListener('DOMContentLoaded', r, {once: true}));
    }
    for (const img of document.querySelectorAll('img[data-trim]')) {
      try {
        if (img.decode) { await img.decode(); }
        const w = img.naturalWidth, h = img.naturalHeight;
        if (!w || !h) continue;
        const c = document.createElement('canvas'); c.width = w; c.height = h;
        const g = c.getContext('2d'); g.drawImage(img, 0, 0);
        const d = g.getImageData(0, 0, w, h).data;
        let x0 = w, y0 = h, x1 = -1, y1 = -1;
        for (let y = 0; y < h; y += 2) {
          for (let x = 0; x < w; x += 2) {
            if (d[(y * w + x) * 4 + 3] > 16) {
              if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
            }
          }
        }
        if (x1 < 0) continue;
        const pad = Math.round(Math.max(w, h) * 0.01);
        x0 = Math.max(0, x0 - pad); y0 = Math.max(0, y0 - pad);
        x1 = Math.min(w - 1, x1 + pad + 1); y1 = Math.min(h - 1, y1 + pad + 1);
        const cw = x1 - x0 + 1, ch = y1 - y0 + 1;
        if (cw >= w - 2 && ch >= h - 2) continue;
        const c2 = document.createElement('canvas'); c2.width = cw; c2.height = ch;
        c2.getContext('2d').drawImage(img, x0, y0, cw, ch, 0, 0, cw, ch);
        img.src = c2.toDataURL('image/png');
        if (img.decode) { await img.decode(); }
      } catch (e) {}
    }
    for (const img of document.querySelectorAll('img[data-bake]')) {
      try {
        if (img.decode) { await img.decode(); }
        const w = img.naturalWidth, h = img.naturalHeight;
        if (!w || !h) continue;
        const P = +(img.dataset.pad || 60);
        const bw = img.offsetWidth, bh = img.offsetHeight;
        const s = Math.min(bw / w, bh / h);
        const c = document.createElement('canvas');
        c.width = w + 2 * P; c.height = h + 2 * P;
        const g = c.getContext('2d');
        g.filter = img.dataset.bake;
        g.drawImage(img, P, P);
        const url = c.toDataURL('image/png');
        // Same place and scale as before; the padding holds the border and shadow.
        const dw = (w + 2 * P) * s, dh = (h + 2 * P) * s;
        const ox = (bw - w * s) / 2, oy = (bh - h * s) / 2;
        img.style.objectFit = 'fill';
        img.style.maxWidth = 'none';
        img.style.width = dw + 'px'; img.style.height = dh + 'px';
        img.style.margin = `${oy - P * s}px ${-(dw - bw - (ox - P * s))}px ${-(dh - bh - (oy - P * s))}px ${ox - P * s}px`;
        img.style.filter = 'none';
        img.src = url;
        if (img.decode) { await img.decode(); }
      } catch (e) {}
    }
    await document.fonts.ready;
    for (const el of document.querySelectorAll('[data-fit]')) {
      const maxW = +el.dataset.fit, lines = +(el.dataset.lines || 1);
      let size = parseFloat(getComputedStyle(el).fontSize), guard = 80;
      const tooBig = () => {
        if (lines === 1) return el.scrollWidth > maxW + 4;
        const lh = parseFloat(getComputedStyle(el).lineHeight) || size * 1.1;
        return el.offsetHeight > lh * lines + 2;
      };
      while (guard-- > 0 && size > 12 && tooBig()) { size *= 0.95; el.style.fontSize = size + 'px'; }
    }
  } catch (e) {}
})();</script>"""
FIT_JS = PREP_JS        # older name
