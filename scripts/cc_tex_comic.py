"""
Textures for the COMIC look (cc_look_comic.py). Run once; the files it writes
are committed, so nothing here runs at render time:

    PYTHONPATH=<numpy+Pillow> python3 scripts/cc_tex_comic.py

    comic-newsprint.jpg   the page: slightly yellowed newsprint, fibres, grain,
                          a few specks and the faint mottling of cheap paper
    comic-dots.png        a halftone screen as a mask (white, alpha = ink): dots
                          on a 45-degree grid that are tiny in the middle and fat
                          at the edges, so a panel tinted through it reads as
                          Ben-Day colour with a clear spot behind the figure
    comic-lines.png       ink focus lines as a mask: tapered strokes aimed at the
                          middle, stopping short of it, drawn by hand-ish
                          (uneven widths, lengths and spacing)

Everything is deterministic (fixed seeds).
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "creator-code" / "assets" / "textures"


def _blur_noise(rs, w, h, sigma, scale=1.0):
    """Gaussian-blurred white noise, normalised to about [-1, 1]."""
    sw, sh = max(4, int(w / scale)), max(4, int(h / scale))
    n = rs.standard_normal((sh, sw)).astype(np.float32)
    im = Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8))
    im = im.filter(ImageFilter.GaussianBlur(sigma / scale)).resize((w, h), Image.BICUBIC)
    a = np.asarray(im).astype(np.float32)
    a = (a - a.mean()) / (a.std() + 1e-6)
    return np.clip(a / 2.5, -1, 1)


def _fibres(w, h, rs, n, lo, hi, alpha):
    """Short, slightly curved fibres, drawn light and dark on a grey 128 field."""
    im = Image.new("L", (w, h), 128)
    d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rs.uniform(0, w), rs.uniform(0, h)
        L = rs.uniform(lo, hi)
        a = rs.uniform(0, math.pi)
        bend = rs.uniform(-.5, .5)
        pts = []
        for k in range(6):
            t = k / 5
            aa = a + bend * (t - .5)
            pts.append((x + math.cos(aa) * L * t, y + math.sin(aa) * L * t))
        v = 128 + (rs.uniform(18, 40) if rs.rand() < .45 else -rs.uniform(14, 34)) * alpha
        d.line(pts, fill=int(v), width=1)
    return (np.asarray(im.filter(ImageFilter.GaussianBlur(.55))).astype(np.float32) - 128) / 128


def _levels(im, n):
    """Alpha rounded to n levels: edges stay soft, the PNG gets several times smaller."""
    a = np.asarray(im).astype(np.float32) / 255
    return Image.fromarray((np.round(a * (n - 1)) / (n - 1) * 255).astype(np.uint8))


def newsprint(w=1080, h=1920, seed=7):
    rs = np.random.RandomState(seed)
    base = np.array([239, 229, 204], np.float32)             # yellowed newsprint
    tone = (_blur_noise(rs, w, h, 90, 4) * 4.0              # big soft blotches
            + _blur_noise(rs, w, h, 12, 2) * 3.0            # mottling
            + _blur_noise(rs, w, h, .6) * 7.0               # fine grain
            + _fibres(w, h, rs, 9000, 5, 28, 1.0) * 30.0)
    # the page yellows a touch more towards its edges
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.clip(1 - np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / 90, 0, 1) ** 2
    img = base[None, None, :] + tone[..., None] * np.array([1, 1, 1.15], np.float32)
    img -= edge[..., None] * np.array([4, 7, 14], np.float32)
    # specks: a few flecks of ink and wood pulp
    sp = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(sp)
    for _ in range(260):
        x, y = rs.uniform(0, w), rs.uniform(0, h)
        r = rs.choice([.6, .8, 1.0, 1.3, 1.8], p=[.35, .3, .2, .1, .05])
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(rs.uniform(60, 170)))
    spa = np.asarray(sp.filter(ImageFilter.GaussianBlur(.4))).astype(np.float32) / 255
    img = img * (1 - spa[..., None] * .55) + np.array([70, 62, 50], np.float32) * spa[..., None] * .55
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT / "comic-newsprint.jpg", quality=85,
                                                                 optimize=True, progressive=True)


def dots(size=1300, pitch=16.0, seed=3):
    """A 45-degree halftone screen as an alpha mask: dot radius grows from the
    centre outwards (and a little with a slow wobble, like uneven inking)."""
    rs = np.random.RandomState(seed)
    ss = 3                                                   # supersample
    S = size * ss
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / ss
    c = size / 2
    # grid coordinates, rotated 45 degrees
    u = ((xx - c) + (yy - c)) / math.sqrt(2) / pitch
    v = ((xx - c) - (yy - c)) / math.sqrt(2) / pitch
    fu, fv = u - np.round(u), v - np.round(v)
    dist = np.sqrt(fu * fu + fv * fv) * pitch                # px from the nearest dot centre
    # the dot's own centre, for its radius
    cu, cv = np.round(u), np.round(v)
    dcx = c + (cu + cv) * pitch / math.sqrt(2)
    dcy = c + (cu - cv) * pitch / math.sqrt(2)
    rr = np.sqrt((dcx - c) ** 2 + (dcy - c) ** 2) / (size * .5)
    k = np.clip((rr - .16) / .78, 0, 1)
    k = k * k * (3 - 2 * k)
    wob = _blur_noise(rs, size, size, 60, 3)
    wob = np.asarray(Image.fromarray(((wob + 1) * 127.5).astype(np.uint8)).resize((S, S), Image.BILINEAR),
                     np.float32) / 127.5 - 1
    radius = pitch * (.11 + .35 * k) * (1 + .06 * wob)
    a = np.clip(radius - dist + .5, 0, 1)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)
    white = Image.new("L", (size, size), 255)
    Image.merge("LA", (white, _levels(im, 6))).save(OUT / "comic-dots.png", optimize=True)


def lines(size=1300, n=200, seed=5):
    """Focus lines: tapered ink strokes from beyond the edge towards the centre."""
    rs = np.random.RandomState(seed)
    ss = 3
    S = size * ss
    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    c = S / 2
    R_out = S * .75
    angs = np.sort(rs.uniform(0, 2 * math.pi, n))
    for a in angs:
        r_in = S * rs.uniform(.17, .29) * (1 + .3 * rs.rand() ** 3)
        wdt = S * rs.uniform(.0025, .011) * (1.6 if rs.rand() < .12 else 1)
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa, ca
        p_in = (c + ca * r_in, c + sa * r_in)
        o1 = (c + ca * R_out + px * wdt, c + sa * R_out + py * wdt)
        o2 = (c + ca * R_out - px * wdt, c + sa * R_out - py * wdt)
        d.polygon([p_in, o1, o2], fill=int(rs.uniform(210, 255)))
    im = im.resize((size, size), Image.LANCZOS)
    white = Image.new("L", (size, size), 255)
    Image.merge("LA", (white, _levels(im, 6))).save(OUT / "comic-lines.png", optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    which = set(sys.argv[1:]) or {"newsprint", "dots", "lines"}
    if "newsprint" in which:
        newsprint()
    if "dots" in which:
        dots()
    if "lines" in which:
        lines()
    for p in sorted(OUT.glob("comic-*")):
        print(f"{p.name:22s} {p.stat().st_size / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
