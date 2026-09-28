"""
The textures of the METRO look (cc_look_metro): the printed map sheet the line
is drawn on, and a fine grain for the enamel and the light box. A development
tool: the files are committed, so the nightly builds only read them.

    PYTHONPATH=<a folder with numpy + Pillow> python3 scripts/cc_tex_metro.py

Writes to creator-code/assets/textures:
    metro-paper.jpg   1080x1920  smooth off-white map paper: a fine print grain,
                                 a faint mottle, the two creases of a sheet that
                                 was folded in three and in half, and edges a
                                 touch darker than the middle
    metro-grain.png   256x256    light and dark specks on transparent (tiles)
"""

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "creator-code" / "assets" / "textures"
W, H = 1080, 1920


def _smooth(h, w, cell, rnd):
    """Value noise: random values on a coarse grid, resized smoothly (bicubic)."""
    small = rnd.random((max(2, h // cell + 2), max(2, w // cell + 2))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8), "L").resize((w + 2 * cell, h + 2 * cell), Image.BICUBIC)
    return np.asarray(im, np.float32)[cell:cell + h, cell:cell + w] / 255.0


def _blur(a, radius):
    lo, hi = float(a.min()), float(a.max())
    span = (hi - lo) or 1.0
    im = Image.fromarray(((a - lo) / span * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(im, np.float32) / 255.0 * span + lo


def _crease(img, pos, horizontal, rnd, strength=1.0):
    """A fold: a soft valley of shade on one side of the line, a thin catch of
    light on the other, wandering a pixel or two along its length."""
    h, w = img.shape[:2]
    n = w if horizontal else h
    wob = np.cumsum(rnd.normal(0, .08, n)).astype(np.float32)
    wob = np.convolve(wob - wob.mean(), np.ones(60) / 60, mode="same")
    along = np.arange(h if horizontal else w, dtype=np.float32)
    d = along[:, None] - (pos + wob[None, :]) if horizontal else along[None, :] - (pos + wob[:, None])
    # fades a little toward the sheet's edges, and varies in depth along its length
    depth = .75 + .25 * _smooth(1, n, 160, rnd)[0]
    depth = depth[None, :] if horizontal else depth[:, None]
    shade = np.exp(-((d - 3.0) / 5.5) ** 2) * -9.0 + np.exp(-((d + 1.2) / 1.1) ** 2) * 5.0
    shade += np.where(d > 0, -1.6 * np.exp(-d / 90.0), 0)          # the far panel sits a hair lower
    img += (shade * depth * strength)[..., None]


def paper(seed=11):
    rnd = np.random.default_rng(seed)
    base = np.array((241, 238, 230), np.float32)
    img = np.ones((H, W, 3), np.float32) * base
    # a faint, broad mottle, a little warmer in places
    m = _smooth(H, W, 260, rnd) - .5
    m2 = _smooth(H, W, 70, rnd) - .5
    img += (m * 5.0 + m2 * 2.2)[..., None]
    img[..., 2] -= m * 2.0
    # print grain: fine, slightly soft
    g = rnd.normal(0, 3.1, (H, W)).astype(np.float32)
    img += _blur(g, .55)[..., None]
    # a few paper fibres, barely there
    fib = Image.new("L", (W, H), 0)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(fib)
    for _ in range(1400):
        x, y = rnd.integers(0, W), rnd.integers(0, H)
        a = rnd.random() * math.pi
        L = rnd.integers(5, 18)
        dr.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=int(rnd.integers(40, 120)), width=1)
    fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(.5)), np.float32) / 255.0
    img -= (fib * 5.0)[..., None]
    # the folds: in half across the middle, and in three down the length
    _crease(img, W * .5 + 6, False, rnd, 1.0)
    _crease(img, H * .333 - 10, True, rnd, .8)
    _crease(img, H * .667 + 8, True, rnd, .9)
    # edges a touch darker than the middle
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .6)) ** 2)
    img -= (np.clip(r - .55, 0, None) ** 1.6 * 16.0)[..., None]
    return img


def grain(size=256, seed=5):
    rnd = np.random.default_rng(seed)
    n = rnd.normal(0, 1, (size, size)).astype(np.float32)
    n = _blur(n, .6)
    n = (n - n.mean()) / (n.std() + 1e-6)
    a = np.clip(np.abs(n) - .9, 0, None) * 120
    rgb = np.where(n[..., None] > 0, 255, 0).astype(np.float32) * np.ones((1, 1, 3), np.float32)
    return np.dstack([rgb, np.clip(a, 0, 90)])


def _save(arr, name, quality=86):
    OUT.mkdir(parents=True, exist_ok=True)
    a = np.clip(arr, 0, 255).astype(np.uint8)
    im = Image.fromarray(a, "RGBA" if a.shape[2] == 4 else "RGB")
    path = OUT / name
    if name.endswith(".png"):
        im.save(path, optimize=True)
    else:
        im.save(path, quality=quality, optimize=True, progressive=True)
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    _save(paper(), "metro-paper.jpg", 84)
    _save(grain(), "metro-grain.png")
