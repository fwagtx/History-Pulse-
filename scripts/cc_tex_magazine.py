"""
Textures for the MAGAZINE look (scripts/cc_look_magazine.py). Run once; the
JPG/PNG files it writes are committed, so rendering never needs this script
(or Pillow).

    PYTHONPATH=<a folder with numpy + Pillow> python3 scripts/cc_tex_magazine.py

    magazine-table.jpg   a dark honed stone tabletop, 1080x1920: soft mottling,
                         a few faint veins and fine mineral grain. Matte: the
                         light falloff is added in CSS, so it stays tweakable.
    magazine-grain.png   256x256 tile of print grain (black and white specks
                         at low alpha), laid over every cover so the flat ink
                         colours read as printed paper.
"""

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "creator-code" / "assets" / "textures"


def _smooth_noise(h, w, cell, rnd, octaves=5, gain=.5):
    """Fractal value noise in [0, 1]: random grids upsampled bicubically."""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2, cell / (2 ** o))
        gh, gw = int(h / c) + 3, int(w / c) + 3
        g = rnd.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8), "L").resize(
            (int(gw * c), int(gh * c)), Image.BICUBIC)
        a = np.asarray(im, np.float32)[:h, :w] / 255.0
        out += a * amp
        tot += amp
        amp *= gain
    out /= tot
    lo, hi = np.percentile(out, 1), np.percentile(out, 99)
    return np.clip((out - lo) / (hi - lo), 0, 1)


def _veins(h, w, rnd):
    """Wispy light veins running on one diagonal, as in a honed grey stone:
    level lines of a gently warped ramp (the warp is kept small next to the
    spacing, so a vein wanders but never loops back), each fading in and out
    along its length, with a few fainter hairlines across them."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    acc = np.zeros((h, w), np.float32)
    passes = [(-32, 820, .16, 1.0, .0060), (-26, 460, .10, .55, .0045), (58, 1100, .08, .35, .0035)]
    for ang, spacing, amp, strength, w0 in passes:
        th = math.radians(ang + rnd.uniform(-4, 4))
        warp = (_smooth_noise(h, w, 520, rnd, 4) - .5) * 2
        warp2 = (_smooth_noise(h, w, 90, rnd, 3) - .5) * 2
        ramp = (xx * math.cos(th) + yy * math.sin(th)) / spacing
        f = ramp + amp * warp + amp * .18 * warp2 + rnd.uniform(0, 1)
        d = np.abs(f - np.round(f)) * spacing / 100.0      # distance to the nearest line, ~px/100
        width = w0 * 100 * (.5 + 1.1 * _smooth_noise(h, w, 260, rnd, 3))
        core = np.exp(-(d / (width * .28)) ** 2)
        soft = np.exp(-(d / (width * 2.0)) ** 2) * .38
        fade = np.clip((_smooth_noise(h, w, 420, rnd, 3) - .30) * 2.2, 0, 1) ** 1.3
        acc = np.maximum(acc, (core + soft) * fade * strength)
    acc = np.clip(acc, 0, 1)
    # the mineral bleeds a little into the stone around each vein
    halo = np.asarray(Image.fromarray((acc * 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(9)), np.float32) / 255.0
    return acc, halo


def table(w=1080, h=1920, seed=41):
    rnd = np.random.default_rng(seed)
    big = _smooth_noise(h, w, 640, rnd, 5, .55)             # cloudy mottling
    mid = _smooth_noise(h, w, 90, rnd, 4, .5)
    fine = rnd.normal(0, 1, (h, w)).astype(np.float32)
    fine = np.asarray(Image.fromarray(np.clip(128 + fine * 40, 0, 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(.6)), np.float32) / 255.0 - .5
    veins, halo = _veins(h, w, rnd)
    # mineral flecks: a few tiny light and dark specks
    fleck = np.zeros((h, w), np.float32)
    for _ in range(2600):
        x, y = int(rnd.integers(0, w)), int(rnd.integers(0, h))
        r = rnd.uniform(.6, 1.8)
        v = rnd.choice([1.0, -1.0], p=[.55, .45]) * rnd.uniform(.25, .7)
        x0, x1, y0, y1 = max(0, x - 3), min(w, x + 4), max(0, y - 3), min(h, y + 4)
        gy, gx = np.mgrid[y0:y1, x0:x1]
        fleck[y0:y1, x0:x1] += v * np.exp(-((gx - x) ** 2 + (gy - y) ** 2) / (r * r))
    fleck = np.clip(fleck, -1, 1)

    # value: a charcoal stone, cool grey with a faint warm drift
    v = (.200 + .060 * (big - .5) + .024 * (mid - .5) + .028 * fine
         + .085 * veins + .045 * halo + .045 * fleck)
    warm = (_smooth_noise(h, w, 700, rnd, 3) - .5)
    r = v * (1.00 + .05 * warm)
    g = v * (1.00 + .012 * warm)
    b = v * (1.045 - .04 * warm)
    img = np.stack([r, g, b], -1)
    img = np.clip(img * 255, 0, 255).astype(np.uint8)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "magazine-table.jpg"
    Image.fromarray(img, "RGB").save(path, quality=86, optimize=True, progressive=True)
    return path


def grain(size=256, seed=7):
    """Print grain that tiles: black and white specks at low alpha."""
    rnd = np.random.default_rng(seed)
    n = rnd.normal(0, 1, (size, size)).astype(np.float32)
    # a touch of blur so it reads as paper tooth, not digital noise; wrap-pad so it tiles
    pad = np.pad(n, 4, mode="wrap")
    im = Image.fromarray(np.clip(128 + pad * 42, 0, 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(.55))
    n = (np.asarray(im, np.float32)[4:-4, 4:-4] - 128) / 42
    a = np.clip(np.abs(n) * 38, 0, 110).astype(np.uint8)
    rgb = np.where(n[..., None] > 0, 255, 0).astype(np.uint8).repeat(3, -1)
    img = np.concatenate([rgb, a[..., None]], -1)
    path = OUT / "magazine-grain.png"
    Image.fromarray(img, "RGBA").save(path, optimize=True)
    return path


def shadow(w=530, h=662, rw=440, rh=572, sigma=21):
    """The soft shadow a cover casts while it is still in the air: a blurred
    rectangle at half size (it is drawn at 2x, 1060x1324 around an 880x1144
    cover), so moving it costs nothing per frame."""
    a = np.zeros((h, w), np.float32)
    x0, y0 = (w - rw) // 2, (h - rh) // 2
    a[y0:y0 + rh, x0:x0 + rw] = 1.0
    im = Image.fromarray((a * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(sigma))
    alpha = (np.asarray(im, np.float32) / 255.0) ** 1.15 * .62
    img = np.zeros((h, w, 4), np.uint8)
    img[..., 0:3] = (8, 6, 4)
    img[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    path = OUT / "magazine-shadow.png"
    Image.fromarray(img, "RGBA").save(path, optimize=True)
    return path


if __name__ == "__main__":
    for p in (table(), grain(), shadow()):
        print(p, p.stat().st_size // 1024, "KB")
