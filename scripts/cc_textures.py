"""
Make the textures the new looks use (paper, cork, felt, wood...) and save them
in creator-code/assets/textures. A development tool: the files are committed, so
the nightly builds only read them and need nothing beyond numpy.

    python3 scripts/cc_textures.py            # (re)make every texture
    python3 scripts/cc_textures.py paper cork # just these

Needs numpy, Pillow and opencv-python-headless (all free) on the machine that
runs it.
"""

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "creator-code" / "assets" / "textures"


def _cv2():
    import cv2
    return cv2


def _noise(h, w, scale, rnd):
    cv2 = _cv2()
    small = rnd.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)


def _save(img, name, quality=88):
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    arr = np.clip(img, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGBA" if arr.ndim == 3 and arr.shape[2] == 4 else "RGB")
    path = OUT / name
    if name.endswith(".png"):
        im.save(path, optimize=True)
    else:
        im.save(path, quality=quality, optimize=True, progressive=True)
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")
    return path


def paperlike(kind, w, h, seed=7):
    """paper, newsprint, kraft, wall, notebook: base colour, blotches, grain, fibres."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    base = {"paper": (238, 232, 219), "kraft": (196, 160, 118), "wall": (232, 229, 222),
            "notebook": (246, 243, 234), "yearbook": (236, 235, 230)}[kind]
    img = np.ones((h, w, 3), np.float32) * np.array(base, np.float32)
    amp = 6 if kind == "wall" else 14
    img += ((_noise(h, w, 180, rnd) - .5) * amp + (_noise(h, w, 45, rnd) - .5) * 7)[..., None]
    grain = rnd.normal(0, 5 if kind != "kraft" else 9, (h, w)).astype(np.float32)
    img += cv2.GaussianBlur(grain, (0, 0), .6)[..., None]
    if kind in ("paper", "kraft", "yearbook"):
        fib = np.zeros((h, w), np.float32)
        for _ in range(int(w * h / 900)):
            x, y = rnd.integers(0, w), rnd.integers(0, h)
            ang = rnd.random() * math.pi
            L = rnd.integers(6, 26)
            cv2.line(fib, (int(x), int(y)), (int(x + L * math.cos(ang)), int(y + L * math.sin(ang))),
                     float(rnd.random() * .9), 1)
        img -= cv2.GaussianBlur(fib, (0, 0), .5)[..., None] * (10 if kind != "kraft" else 16)
    if kind == "kraft":
        sp = (rnd.random((h, w)) > .9965).astype(np.float32)
        img -= cv2.GaussianBlur(sp, (0, 0), 1.1)[..., None] * 90
    return img


def cork(w, h, seed=7):
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array((176, 128, 82), np.float32)
    n1 = cv2.GaussianBlur(rnd.random((h, w)).astype(np.float32), (0, 0), 1.3)
    v = (n1 - .5) * 3.2 + (_noise(h, w, 6, rnd) - .5) * 1.2
    img += v[..., None] * np.array((52, 40, 30), np.float32)
    dark = (rnd.random((h, w)) > .985).astype(np.float32)
    img -= cv2.GaussianBlur(dark, (0, 0), 1.6)[..., None] * np.array((140, 110, 80), np.float32)
    light = (rnd.random((h, w)) > .992).astype(np.float32)
    img += cv2.GaussianBlur(light, (0, 0), 1.2)[..., None] * np.array((120, 100, 70), np.float32)
    img += ((_noise(h, w, 220, rnd) - .5) * 30)[..., None]
    return img


def felt(w, h, seed=7, color=(31, 58, 52)):
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array(color, np.float32)
    img += cv2.GaussianBlur(rnd.normal(0, 14, (h, w)).astype(np.float32), (0, 0), .7)[..., None]
    img += ((_noise(h, w, 200, rnd) - .5) * 16)[..., None]
    return img


def school_backdrop(w, h, seed=3):
    """The mottled blue-grey 'laser' backdrop of school portraits."""
    rnd = np.random.default_rng(seed)
    n = _noise(h, w, 60, rnd) * .5 + _noise(h, w, 22, rnd) * .3 + _noise(h, w, 8, rnd) * .2
    c1, c2 = np.array((64, 88, 118), np.float32), np.array((150, 170, 190), np.float32)
    return c1 * (1 - n[..., None]) + c2 * n[..., None]


def ink_mask(w, h, seed=3, holes=.2):
    """Alpha mask that makes a solid shape look rubber-stamped."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    a = np.ones((h, w), np.float32)
    n = cv2.GaussianBlur(rnd.random((h, w)).astype(np.float32), (0, 0), 1.2)
    a -= (n > np.quantile(n, 1 - holes)).astype(np.float32) * .95
    a *= np.clip(.55 + _noise(h, w, 30, rnd) * .9, 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), .6)
    img = np.zeros((h, w, 4), np.float32)
    img[..., 3] = a.clip(0, 1) * 255
    return img


TEXTURES = {
    "paper.jpg": lambda: paperlike("paper", 1080, 1920, 7),
    "kraft-strip.jpg": lambda: paperlike("kraft", 1080, 400, 11),
    "yearbook-page.jpg": lambda: paperlike("yearbook", 1080, 1920, 21),
    "wall.jpg": lambda: paperlike("wall", 2560, 1920, 17),
    "cork.jpg": lambda: cork(1080, 1920, 7),
    "felt.jpg": lambda: felt(1260, 2100, 5),
    "school-backdrop.jpg": lambda: school_backdrop(640, 640, 3),
    "ink-stamp.png": lambda: ink_mask(560, 260, 5, .2),
}


def main(names):
    for name, make in TEXTURES.items():
        if names and name.split(".")[0] not in names and name not in names:
            continue
        _save(make(), name)


if __name__ == "__main__":
    main(sys.argv[1:])
