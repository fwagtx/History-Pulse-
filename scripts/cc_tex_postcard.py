"""
Make the textures the POSTCARD look (cc_look_postcard) uses and save them in
creator-code/assets/textures. A development tool: the files are committed, so
the nightly builds only read them.

    PYTHONPATH=<dir with numpy + Pillow> python3 scripts/cc_tex_postcard.py

    postcard-desk.jpg    the collector's desk: ink-blue pebbled leather, lit by a
                         lamp from the upper left (the frame, at 2/3 size)
    postcard-card.jpg    cream card stock, seamless tile: fibres, grain, a little
                         mottling
    postcard-ink.png     postmark ink: an alpha mask with uneven pressure and the
                         small gaps a rubber cancel leaves (wide, so each year's
                         postmark can use a different part of it)

Needs numpy and Pillow (both free).
"""

import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "creator-code" / "assets" / "textures"


def _save(arr, name, quality=85):
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    a = np.clip(arr, 0, 255).astype(np.uint8)
    mode = {4: "RGBA", 3: "RGB", 2: "LA"}[a.shape[2]] if a.ndim == 3 else "L"
    im = Image.fromarray(a, mode)
    path = OUT / name
    if name.endswith(".png"):
        im.save(path, optimize=True)
    else:
        im.save(path, quality=quality, optimize=True, progressive=True)
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")


def _blur(a, sigma):
    """Gaussian blur of a 2-D float array, done in the frequency domain (so it
    wraps around the edges: a tile stays seamless)."""
    h, w = a.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (math.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g)).astype(np.float32)


def _periodic_noise(h, w, scale, rnd):
    """Smooth noise that tiles: random spectrum, low-passed at ~`scale` px."""
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    spec = (rnd.normal(size=(h, w)) + 1j * rnd.normal(size=(h, w))) * np.exp(-(f * scale) ** 2 * 4)
    n = np.real(np.fft.ifft2(spec))
    n -= n.min()
    return n / (n.max() or 1)


def _cells(h, w, cell, rnd, wrap=False):
    """Worley noise on a jittered grid: F1 and F2, the distances to the nearest
    and second-nearest seed, in units of `cell`."""
    gh, gw = int(math.ceil(h / cell)), int(math.ceil(w / cell))
    jit = rnd.random((gh, gw, 2))
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    cy, cx = (ys // cell).astype(int), (xs // cell).astype(int)
    f1 = np.full((h, w), 9.0, np.float32)
    f2 = np.full((h, w), 9.0, np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ny, nx = cy + dy, cx + dx
            if wrap:
                jy, jx = ny % gh, nx % gw
            else:
                jy, jx = np.clip(ny, 0, gh - 1), np.clip(nx, 0, gw - 1)
            py = (ny + jit[jy, jx, 0]) * cell
            px = (nx + jit[jy, jx, 1]) * cell
            d = np.sqrt((py - ys) ** 2 + (px - xs) ** 2) / cell
            f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = np.minimum(f1, d)
    return f1, f2


def desk(w=720, h=1280, seed=11):
    """Ink-blue pebbled leather, lamp-lit from the upper left, with a soft
    fall-off to the lower right. Drawn at 2/3 of the frame (it's shown at 1.5x)."""
    rnd = np.random.default_rng(seed)
    # the pebble grain: two sizes of cells, domed, with creases between them
    f1, f2 = _cells(h, w, 7.5, rnd)
    g1, g2 = _cells(h, w, 3.2, rnd)
    dome = 1 - np.clip(f1 / .72, 0, 1) ** 1.6
    crease = np.exp(-(f2 - f1) / .07)
    fine = 1 - np.clip(g1 / .75, 0, 1) ** 1.4
    height = dome * .8 + fine * .28 - crease * .55
    height = _blur(height.astype(np.float32), .7)
    # light from the upper left on the grain's slopes
    gy, gx = np.gradient(height)
    shade = np.clip(-(gx * .62 + gy * .78) * 2.2, -1, 1)
    # broad mottling: tanned leather is never one flat colour
    mott = _blur(rnd.random((h, w)).astype(np.float32), 38)
    mott = (mott - mott.mean()) / (mott.std() or 1)
    mott2 = _blur(rnd.random((h, w)).astype(np.float32), 9)
    mott2 = (mott2 - mott2.mean()) / (mott2.std() or 1)
    base = np.array((25, 37, 64), np.float32)          # ink-blue leather
    hi = np.array((70, 88, 122), np.float32)            # where the grain catches the lamp
    lo = np.array((9, 14, 28), np.float32)
    img = base[None, None, :] * (1 + mott[..., None] * .045 + mott2[..., None] * .03)
    img = img + np.clip(shade, 0, 1)[..., None] * (hi - base) * .55
    img = img + np.clip(-shade, 0, 1)[..., None] * (lo - base) * .5
    img = img - crease[..., None] * 6
    # the lamp: a broad warm pool upper left, falling off to the lower right
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xs - w * .22) / (w * 1.05)) ** 2 + ((ys - h * .2) / (h * .95)) ** 2)
    lamp = np.clip(1.18 - d * .75, .55, 1.18)
    warm = np.clip(1 - d, 0, 1) ** 2
    img = img * lamp[..., None]
    img = img + warm[..., None] * np.array((10, 7, 2), np.float32)
    # a faint sheen band, as leather has under a lamp
    sheen = np.exp(-(((xs * .8 + ys * .6) - w * .55) / (w * .45)) ** 2)
    img = img + sheen[..., None] * np.clip(shade, 0, 1)[..., None] * 16
    # grain noise so it never bands
    img = img + rnd.normal(0, 1.6, (h, w, 1)).astype(np.float32)
    _save(img, "postcard-desk.jpg", quality=84)


def card(size=600, seed=5):
    """Cream card stock that tiles: mottling, grain and short fibres."""
    from PIL import Image, ImageDraw
    rnd = np.random.default_rng(seed)
    n1 = _periodic_noise(size, size, 90, rnd)
    n2 = _periodic_noise(size, size, 22, rnd)
    base = np.array((241, 233, 214), np.float32)
    img = np.ones((size, size, 3), np.float32) * base
    img += ((n1 - .5) * 9 + (n2 - .5) * 5)[..., None] * np.array((1, 1, 1.25), np.float32)
    grain = _blur(rnd.normal(0, 4.2, (size, size)).astype(np.float32), .55)
    img += grain[..., None]
    # fibres, drawn with wrap-around so the tile stays seamless
    fib = Image.new("L", (size, size), 0)
    dr = ImageDraw.Draw(fib)
    for _ in range(int(size * size / 700)):
        x, y = rnd.random() * size, rnd.random() * size
        a = rnd.random() * math.pi
        L = 5 + rnd.random() * 16
        v = int(40 + rnd.random() * 120)
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                dr.line([(x + ox, y + oy), (x + ox + L * math.cos(a), y + oy + L * math.sin(a))], fill=v, width=1)
    f = _blur(np.asarray(fib, np.float32) / 255, .45)
    img -= f[..., None] * np.array((20, 21, 25), np.float32)
    # a few darker specks, as recycled card has
    sp = _blur((rnd.random((size, size)) > .99965).astype(np.float32), .9)
    img -= sp[..., None] * 60
    _save(img, "postcard-card.jpg", quality=86)


def ink(w=800, h=400, seed=9):
    """Postmark ink as an alpha mask: mostly solid, the pressure uneven across
    the stamp, and the small gaps where the rubber didn't take ink."""
    rnd = np.random.default_rng(seed)
    press = _blur(rnd.random((h, w)).astype(np.float32), 60)
    press = (press - press.min()) / ((press.max() - press.min()) or 1)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    tilt = .5 + .5 * np.sin(xs / w * math.pi * 1.3 + 1.1) * np.cos(ys / h * math.pi * .9)
    a = .62 + .38 * np.clip(press * .7 + tilt * .5, 0, 1)
    # speckle gaps: small, irregular, clumped where the pressure is light
    sp = _blur(rnd.random((h, w)).astype(np.float32), 1.1)
    sp = (sp - sp.mean()) / (sp.std() or 1)
    gaps = np.clip((sp - 1.5 + (1 - press) * 1.2) * 1.4, 0, 1)
    a = a * (1 - gaps)
    # fine grain
    a = a * (1 - np.clip(rnd.normal(0, .035, (h, w)), -.1, .1))
    # 24 levels are plenty for a mask and keep the file small
    alpha = np.round(np.clip(a, 0, 1) * 23) / 23 * 255
    la = np.zeros((h, w, 2), np.float32)
    la[..., 1] = alpha
    _save(la, "postcard-ink.png")


def main():
    desk()
    card()
    ink()


if __name__ == "__main__":
    main()
