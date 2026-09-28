"""
Textures for the ARCADE look (cc_look_arcade.py). Run once; the files it writes
are committed, so nothing here runs at render time:

    PYTHONPATH=<numpy+Pillow> python3 scripts/cc_tex_arcade.py

    arcade-plastic.jpg   the cabinet's molded plastic: near-black ABS with a
                         fine orange-peel stipple and faint mottling (tiles)
    arcade-crt.png       what the tube lays over its picture, as one tile: soft
                         scanlines (6 px pitch), a faint RGB aperture grille and
                         a little grain (white/black with alpha; tiles)
    arcade-metal.jpg     brushed aluminium for the trim strips and the sign's
                         bezel (tiles left to right)
    arcade-grain.png     print grain for the printed panels (grey, alpha; tiles)

Everything is deterministic (fixed seeds) and tileable: noise is filtered in
the frequency domain, which wraps round the edges.
"""

from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "creator-code" / "assets" / "textures"


def _periodic_noise(rs, h, w, sigma_y, sigma_x=None):
    """White noise blurred with a Gaussian in the frequency domain (so it tiles),
    normalised to mean 0, std 1."""
    sigma_x = sigma_y if sigma_x is None else sigma_x
    n = rs.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi ** 2) * ((fy * sigma_y) ** 2 + (fx * sigma_x) ** 2))
    out = np.real(np.fft.ifft2(np.fft.fft2(n) * g))
    return (out - out.mean()) / (out.std() + 1e-9)


def _save(arr, name, quality=86):
    OUT.mkdir(parents=True, exist_ok=True)
    arr = np.clip(np.rint(arr), 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGBA" if arr.shape[-1] == 4 else "RGB")
    path = OUT / name
    if name.endswith(".png"):
        im.save(path, optimize=True)
    else:
        im.save(path, quality=quality, optimize=True, progressive=True)
    print(f"{path.name}  {path.stat().st_size // 1024} KB")


def plastic(size=512, seed=31):
    rs = np.random.default_rng(seed)
    base = np.array([24.0, 24.0, 28.0])
    mottle = _periodic_noise(rs, size, size, 60) * 2.2          # big soft variations in the moulding
    peel = _periodic_noise(rs, size, size, 1.6) * 3.2            # the orange-peel stipple
    fine = rs.standard_normal((size, size)) * 1.6                # sensor-ish grain
    v = mottle + peel + fine
    img = base[None, None, :] + v[..., None] * np.array([1.0, 1.0, 1.08])[None, None, :]
    _save(img, "arcade-plastic.jpg", 88)


def crt(size=240, pitch=6, seed=5):
    """RGBA overlay tile. result = bg*(1-A) + C*A per pixel."""
    rs = np.random.default_rng(seed)
    y = np.arange(size)[:, None].astype(np.float64)
    x = np.arange(size)[None, :].astype(np.float64)
    # scanlines: a soft dark band between lines, darkest between them
    ph = (y % pitch) / pitch
    s = .24 * (.5 - .5 * np.cos(2 * np.pi * (ph - .5))) ** 1.6       # 0 on the line, .24 between
    s = np.broadcast_to(s, (size, size))
    # aperture grille: R, G, B columns, 2 px each, a faint tint
    col = (x // 2).astype(int) % 3
    tint = np.zeros((1, size, 3))
    tint[0, col[0] == 0] = (255, 40, 60)
    tint[0, col[0] == 1] = (60, 255, 80)
    tint[0, col[0] == 2] = (60, 90, 255)
    tint = np.broadcast_to(tint, (size, size, 3))
    at = .028
    # grain: a little white and black speckle
    g = _periodic_noise(rs, size, size, .55) * .5 + rs.standard_normal((size, size)) * .5
    g = np.clip(g, -3, 3)
    # compose: black at s, then tint at `at`, then grain (white where g>0, black where g<0)
    A = 1 - (1 - s) * (1 - at)
    CA = tint * at                                   # colour * alpha (black contributes none)
    ga = np.clip(np.abs(g) * .022, 0, .08)
    white = (g > 0)[..., None]
    CA = CA * (1 - ga[..., None]) + np.where(white, 255.0, 0.0) * ga[..., None]
    A = A * (1 - ga) + ga
    C = np.where(A[..., None] > 1e-6, CA / np.maximum(A[..., None], 1e-6), 0)
    rgba = np.concatenate([C, (A * 255)[..., None]], axis=-1)
    _save(rgba, "arcade-crt.png")


def metal(w=512, h=48, seed=11):
    rs = np.random.default_rng(seed)
    streak = _periodic_noise(rs, h, w, .5, 40) * 7 + _periodic_noise(rs, h, w, .5, 6) * 4
    wave = _periodic_noise(rs, h, w, 20, 120) * 3
    v = 158 + streak + wave + rs.standard_normal((h, w)) * 2
    img = np.stack([v, v + 1.5, v + 4], axis=-1)
    _save(img, "arcade-metal.jpg", 88)


def grain(size=256, seed=23):
    rs = np.random.default_rng(seed)
    g = _periodic_noise(rs, size, size, .6) * .6 + rs.standard_normal((size, size)) * .4
    a = np.clip(np.abs(g) * 30, 0, 90)
    v = np.where(g > 0, 255.0, 0.0)
    rgba = np.stack([v, v, v, a], axis=-1)
    _save(rgba, "arcade-grain.png")


if __name__ == "__main__":
    plastic()
    crt()
    metal()
    grain()
