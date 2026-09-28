"""
Textures for the CALENDAR look (cc_look_calendar): a warm desk against a plaster
wall, the calendar's cream paper, the walnut of its stand, the edges of its pad,
rubber-stamp ink and a film grain. A development tool: the files are committed
in creator-code/assets/textures (calendar-*), so the nightly builds only read
them.

    PYTHONPATH=<pylib with numpy, Pillow, opencv-python-headless> python3 scripts/cc_tex_calendar.py [name ...]

All free: numpy, Pillow, opencv-python-headless.
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
    """Smooth value noise: a coarse random grid blown up with cubic filtering."""
    cv2 = _cv2()
    small = rnd.random((max(2, h // scale + 2), max(2, w // scale + 2))).astype(np.float32)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)


def _fbm(h, w, rnd, scales=((420, .5), (160, .3), (60, .14), (22, .06))):
    out = np.zeros((h, w), np.float32)
    for s, a in scales:
        out += (_noise(h, w, s, rnd) - .5) * a
    return out


def _save(img, name, quality=86):
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    arr = np.clip(img, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGBA" if arr.ndim == 3 and arr.shape[2] == 4 else "RGB")
    path = OUT / name
    if name.endswith(".png"):
        im.save(path, optimize=True)
    else:
        im.save(path, quality=quality, optimize=True, progressive=True)
    print(f"{path.relative_to(ROOT)}  {im.size[0]}x{im.size[1]}  {path.stat().st_size // 1024} KB")
    return path


def _grain(h, w, rnd, sigma=2.0, blur=.6):
    cv2 = _cv2()
    return cv2.GaussianBlur(rnd.normal(0, sigma, (h, w)).astype(np.float32), (0, 0), blur)


# ------------------------------------------------------------------ the room

WALL_BOTTOM = 1338          # where the desk top meets the wall (frame px)
DESK_EDGE = 1756            # the desk's rounded front edge


def _rings(n, rnd, lo=5.0, hi=16.0):
    """A 1-D growth-ring profile: light earlywood rising to a thin dark band of
    latewood, rings of uneven width. Returns darkness 0..1 per pixel."""
    prof = np.zeros(n, np.float32)
    x = -rnd.uniform(0, hi)
    while x < n:
        wdt = rnd.uniform(lo, hi) * (1.6 if rnd.random() < .12 else 1.0)
        a, b = int(max(0, x)), int(min(n, x + wdt))
        if b > a:
            f = (np.arange(a, b, dtype=np.float32) - x) / wdt
            strength = rnd.uniform(.45, 1.0)
            prof[a:b] = strength * (np.clip((f - .55) / .45, 0, 1) ** 2.2)
        x += wdt
    return prof


def _plank_rows(h, w, rnd, base, pitch=(150, 230), contrast=1.0, ring=(5.0, 16.0), wave=7.0):
    """Walnut planks running across, in flat (unprojected) coordinates: fine,
    nearly straight growth rings, long streaks along the grain, pores."""
    cv2 = _cv2()
    img = np.zeros((h, w, 3), np.float32)
    y = -int(rnd.integers(0, 80))
    while y < h:
        ph = int(rnd.integers(*pitch))
        b = np.array(base, np.float32) * rnd.uniform(.9, 1.07)
        b *= np.array((1, rnd.uniform(.97, 1.03), rnd.uniform(.93, 1.04)), np.float32)
        yy = np.mgrid[0:ph, 0:w][0].astype(np.float32)
        warp = (_noise(ph, w, 260, rnd) - .5) * wave * 2 + (_noise(ph, w, 900, rnd) - .5) * wave * 5
        prof = _rings(ph + 400, rnd, *ring)
        u = np.clip(yy + warp + 200, 0, ph + 399)
        dark = np.interp(u.ravel(), np.arange(ph + 400, dtype=np.float32), prof).reshape(ph, w)
        streak = cv2.resize(rnd.random((ph, max(2, w // 120))).astype(np.float32), (w, ph),
                            interpolation=cv2.INTER_CUBIC)
        fine = cv2.resize(rnd.random((ph, max(2, w // 14))).astype(np.float32), (w, ph),
                          interpolation=cv2.INTER_LINEAR)
        tone = _noise(ph, w, 300, rnd)
        val = (-dark * 30 + (streak - .5) * 16 + (fine - .5) * 7 + (tone - .5) * 18) * contrast
        plank = b[None, None, :] + val[..., None] * np.array((1, .8, .62), np.float32)
        pores = (rnd.random((ph, w // 4)) > .975).astype(np.float32)
        pores = cv2.resize(pores, (w, ph), interpolation=cv2.INTER_LINEAR)
        plank -= cv2.GaussianBlur(pores, (0, 0), .6)[..., None] * 16 * contrast
        plank[:2] *= .55                                  # the seam between planks
        plank[2:4] *= .86
        y0, y1 = max(0, y), min(h, y + ph)
        if y1 > y0:
            img[y0:y1] = plank[y0 - y:y1 - y]
        y += ph
    return img


def room(w=1080, h=1920, seed=5):
    """The wall and the desk, lit from a window up to the left (baked in: the
    page needs no blend layers). The wall stops at WALL_BOTTOM, where the desk
    top begins; the desk's front edge is at DESK_EDGE."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)

    # -- the wall: warm limewashed plaster
    wh = WALL_BOTTOM
    wall = np.ones((wh, w, 3), np.float32) * np.array((219, 204, 181), np.float32)
    mott = _fbm(wh, w, rnd, ((700, .55), (260, .3), (90, .1), (26, .05)))
    wall += mott[..., None] * np.array((13, 12, 11), np.float32)
    # trowel marks: soft, long, slightly diagonal smears
    sm = _noise(wh, w, 30, rnd)
    sm = cv2.GaussianBlur(sm, (0, 0), 9)
    M = cv2.getRotationMatrix2D((w / 2, wh / 2), 24, 1.0)
    sm = cv2.warpAffine(cv2.resize(sm, (w, wh)), M, (w, wh), borderMode=cv2.BORDER_REFLECT)
    wall += ((sm - sm.mean()) * 5)[..., None]
    wall += _grain(wh, w, rnd, 2.4, .7)[..., None]
    # light: from the upper left, falling off to the lower right
    yy, xx = np.mgrid[0:wh, 0:w].astype(np.float32)
    d = np.sqrt(((xx + 160) / 1500) ** 2 + ((yy + 260) / 1700) ** 2)
    light = np.interp(d, [0, .45, .8, 1.1, 1.4], [1.10, 1.04, .90, .76, .66])
    wall *= light[..., None]
    # ambient occlusion where the wall meets the desk
    ao = np.clip((yy - (wh - 120)) / 120, 0, 1) ** 2
    wall *= (1 - .32 * ao)[..., None]
    wall[..., 0] *= 1.01
    wall[..., 2] *= .97
    img[:wh] = wall

    # -- the desk top, seen from a little above: planks run across, closer
    # together towards the back (perspective), a soft sheen from the window
    dh = DESK_EDGE - wh
    flat_h = 900
    flat = _plank_rows(flat_h, w, rnd, (118, 76, 48), pitch=(170, 260))
    # map desk depth to frame rows: far rows compressed
    t = np.linspace(0, 1, dh, dtype=np.float32)
    zfar, znear = 3.2, 1.0
    z = 1 / (1 / zfar + (1 / znear - 1 / zfar) * t)          # depth for each row
    src = (zfar - z) / (zfar - znear) * (flat_h - 1)
    top = cv2.remap(flat, np.tile(np.arange(w, dtype=np.float32), (dh, 1)),
                    np.tile(src[:, None], (1, w)).astype(np.float32), cv2.INTER_LINEAR)
    # the far rows are also a touch blurred (further away)
    top = top * (.72 + .28 * t[:, None, None])
    yy, xx = np.mgrid[0:dh, 0:w].astype(np.float32)
    sheen = np.exp(-(((xx - 260) / 520) ** 2 + ((yy - dh * .28) / (dh * .5)) ** 2)) * .22
    top *= (1 + sheen)[..., None]
    top *= np.interp(xx / w, [0, .5, 1], [1.02, .97, .86])[..., None]
    # contact darkness along the wall
    top *= (1 - .45 * np.exp(-yy / 14))[..., None]
    top += _grain(dh, w, rnd, 2.2, .6)[..., None]
    img[wh:DESK_EDGE] = top

    # -- the rounded front edge and the front face
    fh = h - DESK_EDGE
    front = _plank_rows(fh + 40, w, rnd, (92, 58, 37), pitch=(400, 500), contrast=.7)[:fh]
    yy = np.arange(fh, dtype=np.float32)
    edge = np.interp(yy, [0, 3, 7, 14, 30, fh], [1.55, 1.38, 1.05, .78, .62, .5])
    front *= edge[:, None, None]
    front += _grain(fh, w, rnd, 2.0, .6)[..., None]
    img[DESK_EDGE:] = front
    img[DESK_EDGE - 2:DESK_EDGE] *= .78
    return img


# ------------------------------------------------------------------ paper & ink

def paper(w=820, h=980, seed=11):
    """The calendar's paper: a warm cream, uncoated, with fibres and faint
    mottling. Tiles well enough for the sheet's size."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array((244, 237, 221), np.float32)
    img += (_fbm(h, w, rnd, ((300, .5), (90, .3), (30, .2))) * 14)[..., None]
    img += _grain(h, w, rnd, 3.0, .55)[..., None]
    fib = np.zeros((h, w), np.float32)
    for _ in range(int(w * h / 700)):
        x0, y0 = rnd.integers(0, w), rnd.integers(0, h)
        ang = rnd.random() * math.pi
        L = rnd.integers(5, 22)
        cv2.line(fib, (int(x0), int(y0)), (int(x0 + L * math.cos(ang)), int(y0 + L * math.sin(ang))),
                 float(rnd.random()), 1)
    img -= cv2.GaussianBlur(fib, (0, 0), .55)[..., None] * 7
    specks = (rnd.random((h, w)) > .9993).astype(np.float32)
    img -= cv2.GaussianBlur(specks, (0, 0), .8)[..., None] * 60 * np.array((1, 1.05, 1.1), np.float32)
    return img


def walnut(w=1100, h=420, seed=17):
    """Oiled walnut for the stand: dark, warm, a clear grain along its length."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = _plank_rows(h, w, rnd, (98, 62, 40), pitch=(900, 1000), contrast=1.2, ring=(4.0, 11.0), wave=5.0)
    # long pores
    pores = (rnd.random((h, w // 3)) > .985).astype(np.float32)
    pores = cv2.resize(pores, (w, h), interpolation=cv2.INTER_LINEAR)
    img -= cv2.GaussianBlur(pores, (0, 0), .7)[..., None] * 26
    img += _grain(h, w, rnd, 1.6, .6)[..., None]
    return cv2.GaussianBlur(img, (0, 0), .5)


def edges(w=72, h=1100, seed=23):
    """The side of the pad: hundreds of sheet edges, cream with thin shadows,
    slightly uneven."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    x = 0.0
    while x < w:
        sw = rnd.uniform(1.2, 2.6)
        tone = rnd.uniform(.84, 1.0)
        c = np.array((238, 229, 210), np.float32) * tone
        x0, x1 = int(x), int(min(w, x + sw))
        img[:, x0:max(x1, x0 + 1)] = c
        if x1 < w:
            img[:, x1:x1 + 1] = c * rnd.uniform(.55, .78)
        x += sw + 1
    wav = _noise(h, w, 60, rnd)
    img *= (.94 + .1 * wav)[..., None]
    img += _grain(h, w, rnd, 2.0, .5)[..., None]
    return cv2.GaussianBlur(img, (0, 0), .4)


def ink(w=720, h=320, seed=31):
    """A rubber stamp's ink as an alpha mask: mostly solid, with pinholes, a
    few worn patches and a dry edge -- stamps are never perfectly even."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    a = .88 + .12 * _noise(h, w, 30, rnd)
    worn = _noise(h, w, 90, rnd)
    a *= 1 - .3 * np.clip((worn - .8) / .15, 0, 1)
    holes = (rnd.random((h, w)) > .9965).astype(np.float32)
    a *= 1 - np.clip(cv2.GaussianBlur(holes, (0, 0), 1.3) * 7, 0, .85)
    dry = cv2.GaussianBlur((rnd.random((h, w)) > .6).astype(np.float32), (0, 0), .6)
    a *= .86 + .14 * dry
    img = np.zeros((h, w, 4), np.float32)
    img[..., 3] = np.clip(a, 0, 1) * 255
    return img


def grain(size=256, seed=37):
    """Film grain: light and dark specks on transparent, for an overlay."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rnd.normal(0, 1, (size, size)).astype(np.float32), (0, 0), .9)
    n = (n - n.mean()) / n.std()
    img = np.zeros((size, size, 4), np.float32)
    img[..., :3] = np.where(n[..., None] > 0, 255, 0)
    img[..., 3] = np.clip(np.abs(n) / 2.6, 0, 1) * 255
    return img


TEXTURES = {
    "calendar-room.jpg": lambda: room(),
    "calendar-paper.jpg": lambda: paper(),
    "calendar-walnut.jpg": lambda: walnut(),
    "calendar-edges.jpg": lambda: edges(),
    "calendar-ink.png": lambda: ink(),
    "calendar-grain.png": lambda: grain(),
}


def main(names):
    for name, make in TEXTURES.items():
        if names and name not in names and name.split(".")[0] not in names \
                and name.split(".")[0].replace("calendar-", "") not in names:
            continue
        _save(make(), name, 84 if name == "calendar-room.jpg" else 86)


if __name__ == "__main__":
    main(sys.argv[1:])
