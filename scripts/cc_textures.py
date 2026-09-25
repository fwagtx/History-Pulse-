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
    "yearbook-page.jpg": lambda: yearbook_paper(1080, 1920, 21),
    "wall.jpg": lambda: paperlike("wall", 2560, 1920, 17),
    "cork.jpg": lambda: cork(1080, 1920, 7),
    "felt.jpg": lambda: felt(1260, 2100, 5),
    "school-backdrop.jpg": lambda: school_backdrop(640, 640, 3),
    "ink-stamp.png": lambda: ink_mask(560, 260, 5, .2),
}


# ---- departures- : the Last Chance look (an airport wall, a split-flap board, film grain)

def _radial(h, w, cx, cy, rx, ry):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)


def departures_slats(w=1200, h=2040, seed=31):
    """Vertical oak slats with dark gaps (a common airport wall finish), lit by a
    downlight at the top left: the fall-off and the warm pool are baked in, so
    the page needs no blend layers."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    pitch, gapw = 46, 11
    x = -13
    while x < w:
        sw = pitch - gapw
        base = np.array((150, 104, 66), np.float32) * rnd.uniform(.84, 1.08)
        base *= np.array((1, rnd.uniform(.96, 1.03), rnd.uniform(.9, 1.08)), np.float32)
        g = cv2.resize(rnd.random((h // 110 + 2, sw)).astype(np.float32), (sw, h), interpolation=cv2.INTER_CUBIC)
        fine = cv2.resize(rnd.random((h // 5, sw)).astype(np.float32), (sw, h), interpolation=cv2.INTER_LINEAR)
        slow = cv2.resize(rnd.random((6, 1)).astype(np.float32), (sw, h), interpolation=cv2.INTER_CUBIC)
        slat = base[None, None, :] + ((g - .5) * 22 + (fine - .5) * 12 + (slow - .5) * 16)[..., None]
        prof = np.ones(sw, np.float32)
        prof[:3] = [1.16, 1.1, 1.04]
        prof[-4:] = [.96, .9, .82, .72]
        slat *= prof[None, :, None]
        x0, x1 = max(0, x), min(w, x + sw)
        if x1 > x0:
            img[:, x0:x1] = slat[:, x0 - x:x1 - x]
        g0, g1 = max(0, x + sw), min(w, x + pitch)
        if g1 > g0:
            img[:, g0:g1] = (34, 25, 18)
        x += pitch
    img += rnd.normal(0, 2.5, (h, w))[..., None]
    d = _radial(h, w, .18 * w, 0, 1500, 1250)
    stops = [(0, 255), (.2, 228), (.44, 146), (.7, 66), (1.0, 30)]
    img *= (np.interp(np.clip(d, 0, 1), [a for a, _ in stops], [b for _, b in stops]) / 255)[..., None]
    pool = np.clip(1 - _radial(h, w, .16 * w, .05 * h, 700, 420) / .72, 0, 1) * .20
    pool += np.clip(1 - _radial(h, w, .32 * w, .57 * h, 520, 260) / .75, 0, 1) * .06
    return 255 - (255 - img) * (1 - pool[..., None] * np.array((255, 226, 180), np.float32) / 255)


def departures_board(w=1160, h=760, seed=22):
    """The board's housing: near-black brushed paint."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array((17, 17, 18), np.float32)
    img += ((_noise(h, w, 120, rnd) - .5) * 5)[..., None]
    img += ((cv2.resize(rnd.random((h // 3, w // 60)).astype(np.float32), (w, h)) - .5) * 3)[..., None]
    img += cv2.GaussianBlur(rnd.normal(0, 2.4, (h, w)).astype(np.float32), (0, 0), .6)[..., None]
    return img


def film_grain(size=512, seed=23, blur=.95):
    """A tile of film grain: white and black specks on transparent, for a moving
    overlay at low opacity."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rnd.normal(0, 1, (size, size)).astype(np.float32), (0, 0), blur)
    n = (n - n.mean()) / n.std()
    img = np.zeros((size, size, 4), np.float32)
    img[..., :3] = np.where(n[..., None] > 0, 255, 0)
    img[..., 3] = np.clip(np.abs(n) / 2.6, 0, 1) * 255
    return img


TEXTURES.update({
    "departures-slats.jpg": lambda: departures_slats(),
    "departures-board.jpg": lambda: departures_board(),
    "departures-grain.png": lambda: film_grain(512, 23),
})


# ---- card- : the Who's That Skin? look (a trading card on a felt playmat)

def card_wood(w=1260, h=420, seed=4):
    """The table's edge under the playmat: warm wood grain."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    warp = _noise(h, w, 260, rnd) * 60 + _noise(h, w, 40, rnd) * 8
    rings = np.sin((xx * .018 + warp) + np.sin(yy * .004) * 3) * .5 + .5
    fine = cv2.GaussianBlur(rnd.random((h, w)).astype(np.float32), (0, 0), .8)
    fine = cv2.resize(cv2.resize(fine, (w, max(2, h // 18))), (w, h))
    v = rings * .55 + fine * .45
    c1, c2 = np.array((112, 72, 44), np.float32), np.array((160, 112, 70), np.float32)
    return c1 * (1 - v[..., None]) + c2 * v[..., None] + rnd.normal(0, 3, (h, w))[..., None]


TEXTURES.update({
    "card-wood.jpg": lambda: card_wood(),
    "card-grain.png": lambda: film_grain(256, 12, .7),
})


# ---- vhs- : the Fortnitemares throwbacks (cc_look_vhs), a found camcorder tape
# The still, expensive parts: the desk the cassette lies on, its plastic, the
# marker ink on its label, and the moonlit field the "footage" was shot in, with
# the fog and the out-of-focus corn that stand in front of the skin. The skin
# itself, the VHS smear and the moving tape noise are put together in the page.

def _vhs_noise(h, w, scale, rnd, sx=1.0):
    """Smooth value noise; sx > 1 stretches it sideways, like a tape's picture."""
    cv2 = _cv2()
    small = rnd.random((max(2, int(h // scale)), max(2, int(w // (scale * sx))))).astype(np.float32)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)


def _vhs_fbm(h, w, rnd, scales=((380, .55), (150, .3), (52, .15)), sx=2.4):
    return sum(_vhs_noise(h, w, s, rnd, sx) * a for s, a in scales)


def _vhs_noise1d(n, scale, rnd):
    cv2 = _cv2()
    small = rnd.random((1, max(2, n // scale))).astype(np.float32)
    return cv2.resize(small, (n, 1), interpolation=cv2.INTER_CUBIC)[0]


def _vhs_ribbon(pts, w0, w1):
    """A filled polygon along a polyline, tapering from width w0 to w1."""
    pts = np.asarray(pts, np.float32)
    n = len(pts)
    left, right = [], []
    for i in range(n):
        d = pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]
        d /= (np.hypot(*d) + 1e-6)
        wi = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((pts[i][0] - d[1] * wi, pts[i][1] + d[0] * wi))
        right.append((pts[i][0] + d[1] * wi, pts[i][1] - d[0] * wi))
    return np.array(left + right[::-1], np.int32)


def _vhs_stalks(h, w, rnd, n, base_y, length, width, avoid=None, lean=.16):
    """Dry corn: tapering stems with drooping blades. A mask, 0..1."""
    cv2 = _cv2()
    m = np.zeros((h, w), np.float32)
    k = 0
    while k < n:
        x = rnd.uniform(-60, w + 60)
        if avoid and avoid[0] < x < avoid[1] and rnd.random() < .85:
            continue
        k += 1
        y = rnd.uniform(*base_y)
        L = rnd.uniform(*length)
        wb = rnd.uniform(*width)
        bend = rnd.uniform(-lean, lean) * L
        pts = [(x + bend * (i / 14) ** 2, y - L * i / 14) for i in range(15)]
        cv2.fillPoly(m, [_vhs_ribbon(pts, wb, max(1.5, wb * .3))], 1.0, cv2.LINE_AA)
        for _ in range(int(rnd.integers(3, 7))):          # blades: rise, arch, droop
            px, py = pts[int(rnd.integers(3, 12))]
            side = 1 if rnd.random() < .5 else -1
            ll = rnd.uniform(.35, .75) * L * .55
            up = rnd.uniform(.25, .7)
            blade = [(px + side * ll * t, py - ll * up * math.sin(t * math.pi * .8) + ll * .5 * t * t)
                     for t in (q / 9 for q in range(10))]
            cv2.fillPoly(m, [_vhs_ribbon(blade, wb * rnd.uniform(1.0, 1.8), 1)], 1.0, cv2.LINE_AA)
    return m


# The footage is composed at 1160x2000 (the frame plus 40 px all round, room for
# the camera to drift); the field is 80 px bigger again so each clip can frame it
# a little differently. In frame coordinates the horizon sits at y 1040, the moon
# up to the right (the look mirrors it for some clips) and the skin's feet at 1470.
_VHS_FIELD = (1240, 2080)
_VHS_OFF = 80                       # frame (0, 0) is at (80, 80) in the field


def vhs_field(seed=7):
    """The empty field at night: moon and cloud, a tree line, a bank of fog on
    the horizon, fence posts and dry corn, graded like cheap tape (milky blacks,
    washed-out warm colour)."""
    cv2 = _cv2()
    w, h = _VHS_FIELD
    o = _VHS_OFF
    rnd = np.random.default_rng(seed)
    moon, hor = (860 + o, 610 + o), 1040 + o          # clear of the player's lettering, either way round
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip(yy / hor, 0, 1)[..., None] ** 1.3
    img = np.array([15, 17, 23.], np.float32) * (1 - t) + np.array([60, 56, 49.], np.float32) * t
    dm = np.hypot(xx - moon[0], yy - moon[1])
    glow = np.exp(-(dm / 470) ** 2)
    clouds = np.clip((_vhs_fbm(h, w, rnd, ((300, .6), (110, .3), (40, .1)), sx=3.2) - .42) * 2.4, 0, 1)
    clouds *= np.clip(1.15 - yy / hor, 0, 1)
    img += (clouds * (10 + 46 * glow))[..., None] * np.array([1, .96, .9])
    img += (glow * 30)[..., None] * np.array([1, .98, .94])
    img += (np.exp(-(dm / 80) ** 2) * 80)[..., None]
    disc = cv2.GaussianBlur((dm < 27).astype(np.float32), (0, 0), 2.2)
    img = img * (1 - disc[..., None]) + np.array([238, 232, 214.]) * disc[..., None]
    tl = hor - (26 + 64 * _vhs_noise1d(w, 46, rnd) + 22 * _vhs_noise1d(w, 9, rnd))     # the tree line
    tree = (yy >= tl[None, :]) & (yy <= hor + 6)
    img[tree] = img[tree] * .25 + np.array([10, 10, 9.]) * .75
    g = np.clip((yy - hor) / 3, 0, 1)[..., None]                                  # the ground
    ground = np.array([25, 23, 19.], np.float32) + ((_vhs_fbm(h, w, rnd, ((60, .6), (14, .4)), sx=3) - .5) * 18)[..., None]
    img = img * (1 - g) + ground * g
    F = _vhs_fbm(h, w, rnd)                                                          # fog on the horizon
    dens = np.exp(-((yy - (hor + 30)) / 190) ** 2) * .95 + np.clip((yy - hor) / 1000, 0, 1) * .3 + .07
    fog_a = np.clip(F * 1.35 - .12, 0, 1) * dens
    fogc = np.array([104, 99, 90.], np.float32) + (glow * 40)[..., None]
    img = img * (1 - fog_a[..., None]) + fogc * fog_a[..., None]
    posts = []                                                                    # fence posts, left
    for i, px in enumerate((70 + o, 230 + o, 372 + o)):
        py, ph = hor + 150 + i * 10, 170 - i * 22
        lean = rnd.uniform(-6, 6)
        cv2.line(img, (int(px), int(py)), (int(px + lean), int(py - ph)), (20, 19, 17), 11 - i * 2, cv2.LINE_AA)
        posts.append((px + lean, py - ph * .8))
    for a, b in zip(posts, posts[1:]):
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 14)
        cv2.polylines(img, [np.array([a, mid, b], np.int32)], False, (26, 25, 22), 2, cv2.LINE_AA)
    m = cv2.GaussianBlur(_vhs_stalks(h, w, rnd, 96, (hor + 120, hor + 300), (110, 300), (3, 6)), (0, 0), 1.4)
    img = img * (1 - m[..., None] * .72) + np.array([30, 28, 24.]) * m[..., None] * .72
    L = img.mean(-1, keepdims=True)
    img = L + (img - L) * .42
    img *= np.array([1.08, 1.0, .82])
    return img * .93 + 9


def vhs_fog(seed=9):
    """The fog in front of the skin, as a grey mask (white = thick): a bank round
    its feet and a thin veil over the rest of the ground."""
    w, h = _VHS_FIELD
    rnd = np.random.default_rng(seed)
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
    feet, hor = 1470 + _VHS_OFF, 1040 + _VHS_OFF
    F = _vhs_fbm(h, w, rnd, ((260, .6), (90, .3), (30, .1)), sx=3.0)
    dens = np.exp(-((yy - (feet - 30)) / 150) ** 2) * .8 + np.clip((yy - hor) / 1400, 0, 1) * .15 + .06
    a = np.clip(F * 1.4 - .3, 0, 1) * dens
    return np.repeat((a.clip(0, 1) * 255)[..., None], 3, -1)


def vhs_stalks(seed=13):
    """Corn right in front of the lens, out of focus, as a grey mask; a gap in the
    middle leaves the skin clear."""
    cv2 = _cv2()
    w, h = _VHS_FIELD
    rnd = np.random.default_rng(seed)
    o, cx = _VHS_OFF, 580 + _VHS_OFF
    m = _vhs_stalks(h, w, rnd, 16, (1590 + o, 2080 + o), (420, 820), (9, 17), avoid=(cx - 220, cx + 220))
    m = cv2.GaussianBlur(m, (0, 0), 5.5)
    return np.repeat((m.clip(0, 1) * 255)[..., None], 3, -1)


def vhs_desk(seed=21):
    """A dark plank desk seen at an angle, lit by a warm lamp: where the cassette lies."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    sw, sh = 1080, 1920                                    # a wood texture to cut the planks from
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    warp = _noise(sh, sw, 260, rnd) * 60 + _noise(sh, sw, 40, rnd) * 8
    rings = np.sin((xx * .018 + warp) + np.sin(yy * .004) * 3) * .5 + .5
    fine = cv2.GaussianBlur(rnd.random((sh, sw)).astype(np.float32), (0, 0), .8)
    fine = cv2.resize(cv2.resize(fine, (sw, sh // 18)), (sw, sh))
    v = rings * .55 + fine * .45
    src = np.array((112, 72, 44), np.float32) * (1 - v[..., None]) + np.array((160, 112, 70), np.float32) * v[..., None]
    src += rnd.normal(0, 3, (sh, sw))[..., None]
    tw, th = 1500, 2600
    out = np.zeros((th, tw, 3), np.float32)
    x = -int(rnd.integers(20, 120))
    while x < tw:
        pw = int(rnd.integers(260, 360))
        ch = int(th / 5.5) + 4
        sx0 = int(rnd.integers(0, src.shape[1] - min(pw, src.shape[1] - 1)))
        sy0 = int(rnd.integers(0, src.shape[0] - ch))
        crop = src[sy0:sy0 + ch, sx0:sx0 + min(pw, src.shape[1] - sx0)]
        board = cv2.resize(crop, (pw, th), interpolation=cv2.INTER_CUBIC) * rnd.uniform(.85, 1.1)
        x0, x1 = max(0, x), min(tw, x + pw)
        out[:, x0:x1] = board[:, x0 - x:x1 - x]
        if 0 < x + pw < tw:
            out[:, max(0, x + pw - 4):x + pw] *= .25
        x += pw
    out *= .34
    out[..., 0] *= 1.06
    out[..., 2] *= .8
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [tw, 0], [tw, th], [0, th]]),
                                    np.float32([[150, -160], [930, -160], [1520, 2080], [-440, 2080]]))
    img = cv2.warpPerspective(out, M, (1080, 1920), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    yy, xx = np.mgrid[0:1920, 0:1080].astype(np.float32)
    lamp = np.exp(-(((xx - 480) / 780) ** 2 + ((yy - 800) / 860) ** 2))
    img *= (.2 + 1.08 * lamp)[..., None]
    img[..., 0] *= 1 + .06 * lamp
    return img + rnd.normal(0, 1.6, (1920, 1080))[..., None]


def vhs_plastic(w=960, h=658, seed=4):
    """Black cassette plastic: faint mottling, fine scratches and dust."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.ones((h, w), np.float32) * 22
    img += cv2.GaussianBlur(rnd.normal(0, 3.2, (h, w)).astype(np.float32), (0, 0), .7)
    img += (_noise(h, w, 90, rnd) - .5) * 5
    for _ in range(30):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        a = rnd.uniform(0, math.pi)
        L = rnd.uniform(20, 90)
        cv2.line(img, (int(x), int(y)), (int(x + L * math.cos(a)), int(y + L * math.sin(a))),
                 float(22 + rnd.uniform(6, 14)), 1, cv2.LINE_AA)
    img += cv2.GaussianBlur((rnd.random((h, w)) > .9985).astype(np.float32), (0, 0), .8) * 60
    return np.stack([img, img * .99, img * 1.02], -1)


def vhs_marker(w=800, h=236, seed=12):
    """Alpha mask for felt-tip ink on a label: slightly uneven, a few dry spots."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    a = .84 + .16 * np.clip(_vhs_noise(h, w, 22, rnd, sx=3.0), 0, 1)
    a *= 1 - (cv2.GaussianBlur(rnd.random((h, w)).astype(np.float32), (0, 0), .6) > .93) * .35
    img = np.zeros((h, w, 4), np.float32)
    img[..., 3] = np.clip(a, 0, 1) * 255
    return img


TEXTURES.update({
    "vhs-field.jpg": lambda: vhs_field(),
    "vhs-fog.jpg": lambda: vhs_fog(),
    "vhs-stalks.jpg": lambda: vhs_stalks(),
    "vhs-desk.jpg": lambda: vhs_desk(),
    "vhs-plastic.jpg": lambda: vhs_plastic(),
    "vhs-marker.png": lambda: vhs_marker(),
})



# ---- yearbook- / case- : Guess the Season and Throwback (cc_look_yearbook), Odd One Out (cc_look_caseboard)

def yearbook_paper(w=1080, h=1920, seed=21):
    """Yearbook stock: smooth, warm white coated paper in soft light (a little
    brighter up top, falling off to the lower corners), fine grain, no fibres."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array((243, 239, 230), np.float32)
    img += ((_noise(h, w, 280, rnd) - .5) * 6)[..., None]
    img += ((_noise(h, w, 70, rnd) - .5) * 2.5)[..., None]
    img += cv2.GaussianBlur(rnd.normal(0, 3.0, (h, w)).astype(np.float32), (0, 0), .7)[..., None]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w * .56) / (w * .95)) ** 2 + ((yy - h * .32) / (h * .8)) ** 2)
    return img * (1.015 - .075 * np.clip(d, 0, 1.3) ** 1.7)[..., None]


def case_wood(w=1080, h=170, seed=3):
    """Straight-grained wood for the top rail of the case board's frame."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    warp = cv2.resize(rnd.random((5, 14)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) * 26
    rings = (np.sin((yy * .23 + warp * .35) + np.sin(xx * .0045 + 1.3) * 2.2) * .5 + .5) ** 1.6
    fine = cv2.resize(rnd.random((h, max(2, w // 55))).astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    streak = cv2.resize(rnd.random((max(2, h // 3), max(2, w // 160))).astype(np.float32), (w, h),
                        interpolation=cv2.INTER_CUBIC)
    v = rings * .42 + fine * .38 + streak * .2
    c1, c2 = np.array((78, 46, 26), np.float32), np.array((146, 96, 56), np.float32)
    img = c1 * (1 - v[..., None]) + c2 * v[..., None]
    img += rnd.normal(0, 3.5, (h, w))[..., None]
    for _ in range(40):
        x, y = rnd.integers(0, w), rnd.integers(0, h)
        cv2.line(img, (int(x), int(y)), (int(x + rnd.integers(6, 30)), int(y)), (60, 36, 20), 1)
    return img


TEXTURES.update({
    "case-wood.jpg": lambda: case_wood(1080, 170, 3),
    "case-card.jpg": lambda: paperlike("paper", 640, 640, 21),
})


# ---- museum- : the OG Check look (a quiet gallery: plaster wall, stone floor, velvet rope)

def _museum_periodic(h, w, sigma, rnd):
    """Smooth noise that tiles left-right (and top-bottom): white noise low-passed
    in the frequency domain, so the room's wall can repeat along a long gallery
    without a seam."""
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    lp = np.exp(-(fx ** 2 + fy ** 2) * (2 * math.pi * sigma) ** 2 / 2)
    n = np.real(np.fft.ifft2(np.fft.fft2(rnd.normal(0, 1, (h, w))) * lp))
    return ((n - n.mean()) / (n.std() + 1e-6)).astype(np.float32)


def museum_wall(w=1440, h=1360, seed=17):
    """Warm grey plaster: broad soft blotches, faint trowel sweeps, fine grain.
    Tiles horizontally. The page darkens and lights it."""
    rnd = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array((226, 221, 212), np.float32)
    v = _museum_periodic(h, w, 60, rnd) * 4.2 + _museum_periodic(h, w, 16, rnd) * 2.4
    sweep = _museum_periodic(h // 4, w, 5, rnd)
    sweep = np.repeat(sweep, 4, axis=0)[:h] * 1.6
    img += (v + sweep)[..., None]
    img += rnd.normal(0, 2.6, (h, w)).astype(np.float32)[..., None]
    return img


def museum_floor(w=1440, h=640, seed=29):
    """Honed stone floor: grey-brown, soft mottling, sparse darker flecks. Tiles
    horizontally."""
    rnd = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array((170, 158, 142), np.float32)
    v = _museum_periodic(h, w, 40, rnd) * 7 + _museum_periodic(h, w, 9, rnd) * 3.5
    img += v[..., None]
    fleck = (_museum_periodic(h, w, 1.2, rnd) > 2.6).astype(np.float32)
    img -= fleck[..., None] * np.array((34, 32, 30), np.float32)
    img += rnd.normal(0, 2.2, (h, w)).astype(np.float32)[..., None]
    return img


def museum_rope(period=1480, h=600, seed=5):
    """One span of velvet rope and its brass stanchion, out of focus (the rope is
    the nearest thing to the camera). Tiles left-right: the post sits at x=40 and
    the rope leaves it on both sides. Local y 0 is frame y 1180."""
    cv2 = _cv2()
    y0 = 1180
    W3 = period * 3
    col = np.zeros((h, W3, 3), np.float32)
    a = np.zeros((h, W3), np.float32)

    def paint(mask, rgb, alpha=1.0):
        m = np.clip(mask, 0, 1) * alpha
        col[:] = col * (1 - m[..., None]) + np.array(rgb, np.float32) * m[..., None]
        a[:] = a * (1 - m) + m

    def rope_curve(x1, x2, yh, sag, n=400):
        t = np.linspace(0, 1, n)
        mx = (x1 + x2) / 2
        p0, p1 = np.array([x1, yh]), np.array([x1 + (mx - x1) * .55, yh + sag * 1.33])
        p2, p3 = np.array([x2 - (x2 - mx) * .55, yh + sag * 1.33]), np.array([x2, yh])
        pts = ((1 - t) ** 3)[:, None] * p0 + (3 * (1 - t) ** 2 * t)[:, None] * p1 \
            + (3 * (1 - t) * t ** 2)[:, None] * p2 + (t ** 3)[:, None] * p3
        return pts

    def stroke(pts, width, dy=0):
        m = np.zeros((h, W3), np.uint8)
        p = np.round(np.stack([pts[:, 0], pts[:, 1] - y0 + dy], 1)).astype(np.int32)
        cv2.polylines(m, [p], False, 255, int(width), cv2.LINE_AA)
        return m.astype(np.float32) / 255

    posts = [40 + k * period for k in range(4)]
    yh, sag = 1268, 104
    for pa, pb in zip(posts, posts[1:]):
        pts = rope_curve(pa + 14, pb - 14, yh, sag)
        paint(stroke(pts, 34), (51, 6, 13))
        paint(stroke(pts, 24, -3), (110, 17, 32))
        paint(stroke(pts, 9, -9), (178, 58, 72), .5)
    xx = np.arange(W3, dtype=np.float32)[None, :]
    yy = np.arange(h, dtype=np.float32)[:, None] + y0
    for x in posts:
        # base: a flat brass disc, lit from the upper left
        d = ((xx - x) / 96) ** 2 + ((yy - 1716) / 26) ** 2
        shade = np.clip(1 - (xx - x + 40) / 190, 0, 1) * .6 + .4
        base = np.stack([240 * shade, 205 * shade, 120 * shade], -1) * np.ones((h, 1, 1))
        m = np.clip(1.0 - (np.sqrt(d) - 1) * 26, 0, 1)
        col[:] = col * (1 - m[..., None]) + base * m[..., None]
        a[:] = np.maximum(a, m)
        # the pole, a cylinder: bright stripe left of centre
        u = (xx - (x - 15)) / 30
        pole = ((u >= 0) & (u <= 1) & (yy >= 1238) & (yy <= 1710)).astype(np.float32)
        prof = np.interp(u, [0, .38, .62, 1], [.36, 1, .72, .3])
        rgb = np.stack([240 * prof, 212 * prof, 140 * prof], -1) * np.ones((h, 1, 1))
        col[:] = col * (1 - pole[..., None]) + rgb * pole[..., None]
        a[:] = np.maximum(a, pole)
        # collar and knob
        u2 = (xx - (x - 22)) / 44
        collar = ((u2 >= 0) & (u2 <= 1) & (yy >= 1254) & (yy <= 1280)).astype(np.float32)
        prof2 = np.interp(u2, [0, .38, .62, 1], [.36, 1, .72, .3])
        rgb2 = np.stack([240 * prof2, 212 * prof2, 140 * prof2], -1) * np.ones((h, 1, 1))
        col[:] = col * (1 - collar[..., None]) + rgb2 * collar[..., None]
        a[:] = np.maximum(a, collar)
        dk = np.sqrt((xx - x) ** 2 + (yy - 1224) ** 2)
        knob = np.clip(25.5 - dk, 0, 1)
        lit = np.clip(1 - np.sqrt((xx - x + 9) ** 2 + (yy - 1215) ** 2) / 34, 0, 1)
        rgbk = np.stack([90 + 165 * lit, 66 + 174 * lit, 22 + 174 * lit], -1)
        col[:] = col * (1 - knob[..., None]) + rgbk * knob[..., None]
        a[:] = np.maximum(a, knob)
    # out of focus: blur premultiplied colour and alpha together
    pre = col * a[..., None]
    pre = cv2.GaussianBlur(pre, (0, 0), 5)
    a2 = cv2.GaussianBlur(a, (0, 0), 5)
    rgb = pre / np.maximum(a2[..., None], 1e-4)
    out = np.zeros((h, period, 4), np.float32)
    out[..., :3] = rgb[:, period:2 * period]
    out[..., 3] = a2[:, period:2 * period] * 255
    return out


def museum_grain(size=256, seed=31):
    """Fine film grain on transparent, for a moving overlay at low opacity."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rnd.normal(0, 1, (size, size)).astype(np.float32), (0, 0), .7)
    n = n / np.abs(n).max()
    img = np.zeros((size, size, 4), np.float32)
    img[..., :3] = np.where(n[..., None] > 0, 255, 0)
    img[..., 3] = np.abs(n) * 255
    return img


TEXTURES.update({
    "museum-wall.jpg": lambda: museum_wall(),
    "museum-floor.jpg": lambda: museum_floor(),
    "museum-rope.png": lambda: museum_rope(),
    "museum-grain.png": lambda: museum_grain(),
})


# ---- receipt- : the Bundle Math look (an oak counter, thermal paper, film grain)

def _receipt_radial(h, w, cx, cy, rx, ry):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)


def receipt_counter(w=1240, h=2100, seed=41):
    """Oiled oak butcher-block counter, planks running across, window light from
    the top left."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    y = -30
    while y < h:
        ph = int(rnd.integers(118, 190))
        base = np.array((170, 118, 74), np.float32) * rnd.uniform(.84, 1.07)
        base *= np.array((1, rnd.uniform(.97, 1.03), rnd.uniform(.9, 1.06)), np.float32)
        yy = np.mgrid[0:ph, 0:w][0].astype(np.float32)
        warp = cv2.resize(rnd.random((4, w // 160 + 2)).astype(np.float32), (w, ph), interpolation=cv2.INTER_CUBIC)
        lines = (np.sin((yy + warp * 46) * rnd.uniform(.22, .36) + rnd.uniform(0, 6)) * .5 + .5) ** 4
        g1 = cv2.resize(rnd.random((ph // 4 + 2, w // 220 + 2)).astype(np.float32), (w, ph),
                        interpolation=cv2.INTER_CUBIC)
        g2 = cv2.resize(rnd.random((ph, w // 30 + 2)).astype(np.float32), (w, ph), interpolation=cv2.INTER_LINEAR)
        streak = cv2.resize(rnd.random((ph // 10 + 2, w // 90 + 2)).astype(np.float32), (w, ph),
                            interpolation=cv2.INTER_CUBIC)
        val = (g1 - .5) * 24 + (g2 - .5) * 8 - lines * 13 + (streak - .5) * 12
        plank = base[None, None, :] + val[..., None]
        plank[:2] *= .62
        plank[2:4] *= .9
        plank[-2:] *= .82
        y0, y1 = max(0, y), min(h, y + ph)
        if y1 > y0:
            img[y0:y1] = plank[y0 - y:y1 - y]
        y += ph
    img = cv2.GaussianBlur(img, (0, 0), .8)
    img += rnd.normal(0, 2.2, (h, w)).astype(np.float32)[..., None]
    d = _receipt_radial(h, w, .2 * w, .12 * h, 1500, 1900)
    img *= np.interp(np.clip(d, 0, 1.3), [0, .35, .7, 1.0, 1.3], [1.12, 1.0, .82, .62, .5])[..., None]
    img += (np.clip(1 - _receipt_radial(h, w, .28 * w, .3 * h, 520, 900), 0, 1) ** 2 * 14)[..., None]
    img[..., 2] *= .96
    return img


def receipt_paper(w=640, h=1700, seed=42):
    """Thermal paper: faint mottling, fibres, a slight curl at the edges."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array((245, 242, 234), np.float32)
    img += ((_noise(h, w, 160, rnd) - .5) * 5)[..., None]
    img += cv2.GaussianBlur(rnd.normal(0, 3.2, (h, w)).astype(np.float32), (0, 0), .6)[..., None]
    fib = np.zeros((h, w), np.float32)
    for _ in range(int(w * h / 1400)):
        x0, y0 = rnd.integers(0, w), rnd.integers(0, h)
        ang = rnd.random() * math.pi
        L = rnd.integers(5, 18)
        cv2.line(fib, (int(x0), int(y0)), (int(x0 + L * math.cos(ang)), int(y0 + L * math.sin(ang))),
                 float(rnd.random()), 1)
    img -= cv2.GaussianBlur(fib, (0, 0), .5)[..., None] * 5
    xx = np.arange(w, dtype=np.float32)
    curl = 1 - .075 * np.exp(-xx / 16) - .10 * np.exp(-(w - 1 - xx) / 22) + .025 * np.exp(-((xx - w * .8) / 70) ** 2)
    img *= curl[None, :, None]
    yy = np.arange(h, dtype=np.float32)
    img *= (1 + .018 * np.sin(yy / 190 + .7) + .01 * np.sin(yy / 67 + 2))[:, None, None]
    return img


def receipt_printmask(w=640, h=1700, seed=43):
    """Thermal print isn't even: faint blotches, a weaker right side, banding and
    pin-hole specks. An alpha mask for the ink layer."""
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    a = .86 + .14 * _noise(h, w, 55, rnd)
    a *= (1 - .10 * np.linspace(0, 1, w, dtype=np.float32))[None, :]
    band = cv2.resize(rnd.random((h // 9, 1)).astype(np.float32), (w, h), interpolation=cv2.INTER_NEAREST)
    a *= 1 - .06 * (band > .8)
    sp = (rnd.random((h, w)) > .992).astype(np.float32)
    a *= 1 - .6 * cv2.GaussianBlur(sp, (0, 0), .7) * 2.2
    img = np.zeros((h, w, 4), np.float32)
    img[..., 3] = np.clip(a, 0, 1) * 255
    return img


def receipt_grain(size=256, seed=44):
    cv2 = _cv2()
    rnd = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rnd.normal(0, 1, (size, size)).astype(np.float32), (0, 0), .95)
    n = (n - n.mean()) / n.std()
    img = np.zeros((size, size, 4), np.float32)
    img[..., :3] = np.where(n[..., None] > 0, 255, 0)
    img[..., 3] = np.clip(np.abs(n) / 2.6, 0, 1) * 255
    return img


TEXTURES.update({
    "receipt-counter.jpg": lambda: receipt_counter(),
    "receipt-paper.jpg": lambda: receipt_paper(),
    "receipt-printmask.png": lambda: receipt_printmask(),
    "receipt-grain.png": lambda: receipt_grain(),
})


def main(names):
    for name, make in TEXTURES.items():
        if names and name.split(".")[0] not in names and name not in names:
            continue
        _save(make(), name)


if __name__ == "__main__":
    main(sys.argv[1:])
