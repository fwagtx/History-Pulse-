"""
Textures for the MOST COMMON format (cc_fmt_most_common): a dark painted
concrete wall the tally marks are painted on, and the concrete floor in front
of it. A development tool, like cc_textures.py: the files are committed, so the
builds only read them.

    python3 scripts/cc_tex_most_common.py

Writes creator-code/assets/textures/most-common-wall.jpg (1080x1920) and
most-common-floor.jpg (1080x800). Needs numpy, Pillow and opencv-python-headless.
"""

import math

import numpy as np

from cc_textures import _cv2, _noise, _save


def _fbm(h: int, w: int, rnd, sigmas=(90, 36, 12)) -> np.ndarray:
    """Soft organic noise (unit spread): blurred random fields, coarse to fine."""
    cv2 = _cv2()
    out = np.zeros((h, w), np.float32)
    for k, s in enumerate(sigmas):
        f = cv2.GaussianBlur(rnd.normal(0, 1, (h, w)).astype(np.float32), (0, 0), s)
        out += f / (f.std() + 1e-6) * (.55 ** k)
    return out / (out.std() + 1e-6)


def wall(w: int = 1080, h: int = 1920, seed: int = 11):
    """Near-black painted concrete: soft mottling, the stipple a paint roller
    leaves, faint roller lanes, a few old drip stains and hairline cracks.
    Evenly lit: the format lights it in the page, over the tally marks."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    lum = _fbm(h, w, rnd) * 3.6
    stip = cv2.GaussianBlur(rnd.random((h, w)).astype(np.float32), (0, 0), 1.7)
    stip = (stip - stip.mean()) / (stip.std() + 1e-6)
    lum += stip * 2.4
    # roller lanes: long vertical bands a little lighter or darker than their neighbours
    lanes = rnd.random((1, w // 5)).astype(np.float32) - .5
    lanes = cv2.GaussianBlur(lanes, (0, 0), 2.2)
    lum += cv2.resize(lanes, (w, h), interpolation=cv2.INTER_CUBIC) * 9
    lum += (_noise(h, w, 18, rnd) - .5) * 1.6
    # old drip stains: thin darker runs down from random heights
    stain = np.zeros((h, w), np.float32)
    for _ in range(26):
        x = int(rnd.integers(0, w))
        y0 = int(rnd.integers(0, h - 200))
        L = int(rnd.integers(120, 700))
        width = int(rnd.integers(2, 7))
        cv2.line(stain, (x, y0), (x + int(rnd.integers(-3, 4)), min(h - 1, y0 + L)), float(rnd.uniform(.4, 1)),
                 width)
    stain = cv2.GaussianBlur(stain, (0, 0), 2.2)
    lum -= stain * 5
    # hairline cracks: short wandering polylines
    crack = np.zeros((h, w), np.float32)
    for _ in range(5):
        x, y = float(rnd.integers(40, w - 40)), float(rnd.integers(80, h - 300))
        ang = rnd.uniform(0, 2 * math.pi)
        pts = []
        for _ in range(int(rnd.integers(18, 40))):
            pts.append((int(x), int(y)))
            ang += rnd.normal(0, .45)
            x += math.cos(ang) * 9
            y += math.sin(ang) * 9
        cv2.polylines(crack, [np.array(pts, np.int32)], False, 1.0, 1, cv2.LINE_AA)
    lum -= cv2.GaussianBlur(crack, (0, 0), .6) * 9
    # pale specks of old paint
    specks = (rnd.random((h, w)) > .9993).astype(np.float32)
    lum += cv2.GaussianBlur(specks, (0, 0), .9) * 60
    lum += cv2.GaussianBlur(rnd.normal(0, 3.0, (h, w)).astype(np.float32), (0, 0), .65)
    base = np.array((28, 29, 31), np.float32)
    tint = _fbm(h, w, rnd, (160,))[..., None] * np.array((.7, .35, -.5), np.float32)
    return base + lum[..., None] + tint


def floor(w: int = 1080, h: int = 800, seed: int = 5):
    """Dark concrete floor seen at a low angle: grain stretched sideways, a
    little lighter where it meets the wall, darker toward the camera."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    g = rnd.normal(0, 1, (h, w)).astype(np.float32)
    streak = cv2.GaussianBlur(g, (0, 0), sigmaX=26, sigmaY=1.1)
    streak = streak / (streak.std() + 1e-6)
    lum = streak * 2.2 + _fbm(h, w, rnd, (70, 24)) * 2.4
    lum += cv2.GaussianBlur(rnd.normal(0, 3.2, (h, w)).astype(np.float32), (0, 0), .6)
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    lum += 9 * np.exp(-y / .12) - 8 * y
    base = np.array((22, 22, 23), np.float32)
    return base + lum[..., None]


if __name__ == "__main__":
    _save(wall(), "most-common-wall.jpg", quality=86)
    _save(floor(), "most-common-floor.jpg", quality=86)
