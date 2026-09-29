"""
YouTube thumbnails for the v2 long videos (cc_long_v2): 1280x720, a different
picture every time.

Each video's builder hands a spec -- a layout family and its words -- with the
video's own rows (#1 first). Here that becomes three thumbnails: the main one
(the one posted) and two alternates in other layouts, for YouTube Studio's
Test & Compare if the owner ever wants it.

    stamp      the skin big on the right, a word stamped across the left
               ("OVERDUE"), the number under it ("59× LONGER")
    hero_stat  the skin big on the left, the kicker and a huge number on the
               right ("BACK AFTER" / "5+ YEARS")
    podium     #1 big with a red ring round its head and a #1 badge, #2 and #3
               behind it, two words ("RAREST" / "MARVEL") and a badge
    calendar   a torn-off calendar page (month, year) and three of the skins
    silhouette the skin as a black shape with a glow and a huge "?" (quizzes)
    versus     two skins split by a slash, "VS" between them (which came first)
    zoom       a close-up of the skin in a round lens and a "?" (zoomed in)

Rules every thumbnail keeps (checked on the rendered page):
  * at most three big words, the smallest text 44 px (readable when YouTube
    shows the thumbnail 168 px wide)
  * no text in the bottom-right corner, where YouTube prints the length, or
    the top-right, where the desktop player puts its buttons on hover
  * the skin's colours make the background, so no two videos look alike
  * the lead skin isn't one another recent video's thumbnail led with, and
    the picture isn't a near-copy of a recent one (a 64-bit difference hash
    against the last ones' hashes); else the next layout or skin is tried
The numbers are the video's own, taken from the same row as the skin shown.
"""

from io import BytesIO
from pathlib import Path

import cc_code_entry as CE
import cc_edit as ED
import cc_motion as M
from cc_looks import PREP_JS
from cc_motion import esc

TW, TH = 1280, 720
RED = "#FF3B30"
LIME = ED.LIME
NO_TEXT = [(1060, 600, 1280, 720), (1140, 0, 1280, 96)]   # the length badge; the hover buttons
MIN_TEXT = 44
SIMILAR = 10                     # difference-hash bits: this close to a recent one = too alike

CSS = """
.th-word{position:absolute;font-family:'TikTok Sans',sans-serif;font-weight:900;white-space:nowrap;line-height:1}
.th-hero{position:absolute;display:block;filter:drop-shadow(0 14px 22px rgba(0,0,0,.55))}
.th-sil{filter:brightness(0) drop-shadow(0 0 3px #E8FF3A) drop-shadow(0 0 18px rgba(232,255,58,.85))}
.th-ring{position:absolute;border:12px solid #FF3B30;border-radius:50%;box-shadow:0 0 0 5px #000,inset 0 0 0 5px #000}
.th-badge{position:absolute;font:900 44px/1 'TikTok Sans',sans-serif;background:#FF3B30;color:#fff;
  padding:10px 20px 12px;border-radius:16px;border:5px solid #000;white-space:nowrap}
"""


def _outline(text: str, x: float, y: float, size: float, color: str = "#fff", rot: float = 0, align: str = "left",
             width: float = 800) -> str:
    """Big words as SVG text with a black edge (round joins), `data-th` for the check."""
    tx, anchor = {"center": (width / 2, "middle"), "right": (width, "end")}.get(align, (0, "start"))
    h = 1.28 * size
    return (f'<div data-th="text" style="position:absolute;left:{x:.0f}px;top:{y:.0f}px;width:{width:.0f}px;'
            f'height:{h:.0f}px;transform:rotate({rot}deg);transform-origin:0 50%">'
            f'<svg width="{width:.0f}" height="{h:.0f}" style="display:block;overflow:visible">'
            f'<text x="{tx:.0f}" y="{size:.1f}" text-anchor="{anchor}" font-family="TikTok Sans" font-weight="900" '
            f'font-size="{size:.0f}" fill="{color}" stroke="#000" stroke-width="{.16 * size:.1f}" '
            f'stroke-linejoin="round" paint-order="stroke">{esc(text)}</text></svg></div>')


def _box(text: str, x: float, y: float, size: float, bg: str = LIME, fg: str = "#0A0A0B", rot: float = 0,
         border: str = "#000") -> str:
    return (f'<div data-th="text" class="th-word" style="left:{x:.0f}px;top:{y:.0f}px;font-size:{size:.0f}px;'
            f'background:{bg};color:{fg};padding:.1em .34em .16em;border-radius:.22em;border:6px solid {border};'
            f'transform:rotate({rot}deg);transform-origin:0 50%;box-shadow:0 10px 0 rgba(0,0,0,.35)">'
            f'{esc(text)}</div>')


def _fit(text: str, width: float, big: float, small: float = MIN_TEXT) -> float:
    import cc_edit_long as LE
    return LE.fit(text, width, big, small, 900, .3)


def _hero(uri: str, cx: float, top: float, height: float, extra: str = "", cls: str = "") -> str:
    """The skin, trimmed to its figure, `height` tall from `top` (so it runs off
    the bottom: head and chest fill the thumbnail)."""
    return (f'<img class="th-hero {cls}" data-trim="figure" src="{uri}" style="left:{cx:.0f}px;top:{top:.0f}px;'
            f'height:{height:.0f}px;transform:translateX(-50%);{extra}">')


def _bg(colors: tuple, at: str = "72% 42%", rays: bool = True) -> str:
    c1, c2 = colors
    layers = (f'<div class="full" style="background:radial-gradient(ellipse 75% 95% at {at},{c1} 0%,{c2} 52%,'
              f'#07080a 100%)"></div>')
    if rays:
        layers += (f'<div class="full" style="background:repeating-conic-gradient(from 0deg at {at},'
                   f'rgba(255,255,255,.07) 0deg 7deg,rgba(255,255,255,0) 7deg 16deg);'
                   f'-webkit-mask:radial-gradient(ellipse 70% 80% at {at},#000 20%,transparent 75%)"></div>')
    return layers + ('<div class="full" style="background:radial-gradient(ellipse 110% 90% at 50% 50%,'
                     'rgba(0,0,0,0) 55%,rgba(0,0,0,.55) 100%)"></div>')


def _code() -> str:
    return ('<div data-th="key" style="position:absolute;left:30px;top:598px;width:0;height:0;transform:scale(.4);'
            'transform-origin:0 0">' + ED.code(0, 0) + '</div>')


def _colors(row: dict, theme: str = "") -> tuple:
    if theme == "halloween":
        return ("#FF7A1A", "#3B0A57")
    if theme == "winter":
        return ("#8FE3FF", "#0B2A6B")
    return ED.tile_colors(row["item"])


# ------------------------------------------------------------------ layouts

def stamp(spec, rows, hero, flip=False):
    c = _colors(hero, spec.get("theme", ""))
    hx = 330 if flip else 930
    tx = 700 if flip else 44
    word = spec["stamp"]
    stat = spec["stat"](hero)
    html = _bg(c, "30% 45%" if flip else "72% 42%") + _hero(hero["uri"], hx, 26, 1120)
    html += (f'<div data-th="text" class="th-word" style="left:{tx:.0f}px;top:{150 if flip else 128}px;font-size:'
             f'{_fit(word, 500, 132, 80):.0f}px;color:#fff;background:{RED};padding:.06em .3em .12em;'
             f'border:10px solid #fff;border-radius:.14em;transform:rotate({5 if flip else -8}deg);'
             f'box-shadow:0 0 0 7px #000,0 14px 0 rgba(0,0,0,.4)">{esc(word)}</div>')
    size = _fit(stat, 520, 124, 70)
    html += _outline(stat, tx, 350, size, "#fff", width=560)
    if spec.get("sub"):
        html += _box(spec["sub"], tx + 6, 340 + size * 1.25, _fit(spec["sub"], 480, 56, MIN_TEXT), rot=-2)
    return html + _code()


def hero_stat(spec, rows, hero, flip=False):
    c = _colors(hero, spec.get("theme", ""))
    hx = 940 if flip else 340
    tx = 44 if flip else 640
    kicker = spec["kicker"]
    stat = spec["stat"](hero)
    html = _bg(c, "70% 45%" if flip else "28% 45%") + _hero(hero["uri"], hx, 20, 1150)
    html += _box(kicker, tx, 140, _fit(kicker, 520, 76, 50), rot=-3)
    size = _fit(stat, 580, 170, 90)
    html += _outline(stat, tx - 8, 262, size, LIME, width=600)
    return html + _code()


def podium(spec, rows, hero, flip=False):
    c = _colors(rows[0], spec.get("theme", ""))
    one, two_, three = rows[0], rows[1 % len(rows)], rows[2 % len(rows)]
    base = 170 if not flip else 640
    html = _bg(c, "30% 46%" if not flip else "70% 46%")
    html += _hero(two_["uri"], base + 290, 150, 700, "opacity:.9;filter:brightness(.72) drop-shadow(0 10px 18px #000)")
    html += _hero(three["uri"], base - 20, 170, 680, "opacity:.9;filter:brightness(.72) drop-shadow(0 10px 18px #000)")
    html += _hero(one["uri"], base + 140, 40, 1060)
    html += f'<div class="th-ring" style="left:{base + 20:.0f}px;top:14px;width:240px;height:240px"></div>'
    html += _box("#1", base + 196, 238, 64, bg=RED, fg="#fff", rot=8)
    tx = 700 if not flip else 44
    top = 104 if not flip else 70
    w1, w2 = (spec["words"] + [""])[:2]
    s1 = _fit(w1, 520, 136, 70)
    html += _outline(w1, tx, top, s1, "#fff", width=540)
    if w2:
        s2 = _fit(w2, 520, 136, 60)
        html += _outline(w2, tx, top + s1 * 1.08, s2, LIME, width=540)
        y = top + s1 * 1.08 + s2 * 1.15
    else:
        y = top + s1 * 1.15
    badge = spec["badge"](one) if callable(spec.get("badge")) else spec.get("badge", "")
    if badge:
        html += (f'<div data-th="text" class="th-badge" style="left:{tx + 4:.0f}px;top:{y + 18:.0f}px;'
                 f'font-size:{_fit(badge, 500, 52, MIN_TEXT):.0f}px;transform:rotate(-2deg)">{esc(badge)}</div>')
    return html + _code()


def calendar(spec, rows, hero, flip=False):
    c = _colors(hero, spec.get("theme", ""))
    html = _bg(c, "72% 44%")
    for r, (cx, top, h, rot, dim) in zip(rows[1:3], [(780, 150, 760, -6, .75), (1120, 170, 740, 7, .75)]):
        html += _hero(r["uri"], cx, top, h, f"transform:translateX(-50%) rotate({rot}deg);filter:brightness({dim})")
    html += _hero(hero["uri"], 950, 40, 1080)
    card = (f'<div data-th="text" style="position:absolute;left:56px;top:52px;width:450px;height:392px;'
            f'background:#fff;border-radius:26px;border:8px solid #000;transform:rotate(-5deg);overflow:hidden;'
            f'box-shadow:0 18px 0 rgba(0,0,0,.4)">'
            f'<div style="height:136px;background:{RED};border-bottom:8px solid #000;display:flex;align-items:center;'
            f'justify-content:center;font:900 104px/1 \'TikTok Sans\',sans-serif;color:#fff">{esc(spec["month"])}</div>'
            f'<div style="height:248px;display:flex;align-items:center;justify-content:center;'
            f'font:900 140px/1 \'TikTok Sans\',sans-serif;color:#0A0A0B">{esc(spec["year"])}</div></div>')
    html += card
    html += _box(spec["word"], 74, 478, _fit(spec["word"], 520, 64, MIN_TEXT), rot=-3)
    return html + _code()


def silhouette(spec, rows, hero, flip=False):
    c = _colors(hero, spec.get("theme", ""))
    hx = 880 if not flip else 400
    html = _bg(c, "68% 45%" if not flip else "32% 45%") + _hero(hero["uri"], hx, 40, 1060, cls="th-sil")
    qx = 1120 if not flip else 150
    html += _outline("?", qx - 110, 60, 330, LIME, width=240, align="center")
    tx = 44 if not flip else 720
    w1, w2 = (spec["words"] + [""])[:2]
    s1 = _fit(w1, 560, 118, 70)
    html += _outline(w1, tx, 110, s1, "#fff", width=600)
    s2 = _fit(w2, 560, 150, 70) if w2 else 0
    if w2:
        html += _outline(w2, tx, 110 + s1 * 1.1, s2, "#fff", width=600)
    if spec.get("tag"):
        html += _box(spec["tag"], tx + 6, 130 + s1 * 1.1 + s2 * 1.2, _fit(spec["tag"], 460, 64, MIN_TEXT), rot=-3)
    return html + _code()


def versus(spec, rows, hero, flip=False):
    a, b = spec["pair"]
    c = _colors(a)
    c2 = _colors(b)
    html = (f'<div class="full" style="background:linear-gradient(105deg,{c[0]} 0%,{c[1]} 49.6%,#000 49.6%,#000 50.4%,'
            f'{c2[1]} 50.4%,{c2[0]} 100%)"></div>')
    html += _bg(("rgba(0,0,0,0)", "rgba(0,0,0,0)"), "50% 45%")
    html += _hero(a["uri"], 330, 60, 1000) + _hero(b["uri"], 950, 60, 1000)
    html += (f'<div data-th="text" class="th-word" style="left:540px;top:250px;width:200px;height:200px;'
             f'border-radius:50%;background:{RED};border:10px solid #000;display:flex;align-items:center;'
             f'justify-content:center;font-size:96px;color:#fff;transform:rotate(-8deg)">VS</div>')
    w1, w2 = (spec["words"] + [""])[:2]
    html += _outline(w1, 40, 28, _fit(w1, 1000, 104, 60), "#fff", width=1200, align="left")
    if w2:
        html += _box(w2, 48, 170, _fit(w2, 520, 70, MIN_TEXT), rot=-3)
    return html + _code()


def zoom(spec, rows, hero, flip=False):
    c = _colors(hero)
    html = _bg(c, "62% 45%")
    lens = (f'<div style="position:absolute;left:560px;top:40px;width:640px;height:640px;border-radius:50%;'
            f'overflow:hidden;border:14px solid #fff;box-shadow:0 0 0 8px #000,0 20px 40px rgba(0,0,0,.6);'
            f'background:radial-gradient(circle,{c[0]},{c[1]})">'
            f'<img class="th-hero" data-trim="figure" src="{hero["uri"]}" style="left:50%;top:-40px;height:2600px;'
            f'transform:translateX(-50%)"></div>')
    html += lens
    html += _outline("?", 1020, 380, 300, LIME, width=240, align="center")
    w1, w2 = (spec["words"] + [""])[:2]
    s1 = _fit(w1, 470, 120, 70)
    html += _outline(w1, 40, 120, s1, "#fff", width=500)
    if w2:
        html += _outline(w2, 40, 120 + s1 * 1.1, _fit(w2, 470, 120, 60), LIME, width=500)
    if spec.get("tag"):
        html += _box(spec["tag"], 46, 420, _fit(spec["tag"], 440, 60, MIN_TEXT), rot=-3)
    return html + _code()


LAYOUTS = {"stamp": stamp, "hero_stat": hero_stat, "podium": podium, "calendar": calendar,
           "silhouette": silhouette, "versus": versus, "zoom": zoom}
# The alternates each family offers (the main layout first). A layout marked
# "top" shows #1 as #1, so only rows[0] can lead it.
ALTERNATES = {"stamp": ["stamp", "hero_stat", "podium"], "hero_stat": ["hero_stat", "stamp", "podium"],
              "podium": ["podium", "hero_stat", "stamp"], "calendar": ["calendar", "podium", "hero_stat"],
              "silhouette": ["silhouette", "zoom", "silhouette"], "versus": ["versus", "silhouette", "versus"],
              "zoom": ["zoom", "silhouette", "zoom"]}
NEEDS_TOP = {"podium"}


def _kind(r: dict) -> str:
    return (((r.get("raw") or {}).get("type") or {}).get("value") or "").lower()


def _spec_for(layout: str, spec: dict) -> dict:
    """A family's spec, filled in for another layout (words, stat, stamp)."""
    s = dict(spec)
    stat = spec.get("stat")
    badge = spec.get("badge")
    words = spec.get("words") or []
    if layout == "stamp":
        s.setdefault("stamp", spec.get("kicker") or (words[0] if words else "RARE"))
        s["stat"] = stat or (badge if callable(badge) else (lambda r, b=badge: b or ""))
    elif layout == "hero_stat":
        s.setdefault("kicker", spec.get("stamp") or " ".join(words[:2]) or "")
        s["stat"] = stat or (badge if callable(badge) else (lambda r, b=badge: b or ""))
    elif layout == "podium":
        if not words:
            s["words"] = [spec.get("stamp") or spec.get("kicker") or "THE", spec.get("word", "")][:2]
        s.setdefault("badge", stat)
    elif layout in ("silhouette", "zoom"):
        s.setdefault("words", words or ["GUESS THE", "SKIN"])
    return s


# ------------------------------------------------------------------ render + checks

CHECK_JS = r"""(zones) => {
  const bad = [];
  for (const el of document.querySelectorAll('[data-th="text"]')) {
    const t = el.querySelector('svg text');
    const r = (t || el).getBoundingClientRect();
    if (r.width < 2) continue;
    if (r.left < 12 || r.top < 8 || r.right > 1268 || r.bottom > 712) bad.push(['edge', Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]);
    for (const [x0, y0, x1, y1] of zones) {
      if (r.right > x0 && r.left < x1 && r.bottom > y0 && r.top < y1) bad.push(['corner', Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]);
    }
  }
  return bad;
}"""


def dhash(img) -> int:
    g = img.convert("L").resize((9, 8))
    px = list(g.getdata())
    bits = 0
    for y in range(8):
        for x in range(8):
            bits = (bits << 1) | (px[y * 9 + x] > px[y * 9 + x + 1])
    return bits


def distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _page(pw):
    br = pw.chromium.launch(args=M.CHROME_ARGS)
    return br, br.new_page(viewport={"width": TW, "height": TH})


def _shot(pg, html: str):
    comp = CE.Frame(1.0, TW, TH, "#0A0A0B")
    comp.use_fonts(ED.FONT, "Liberation Sans")
    comp.css(ED.CSS + CE.CSS + CSS)
    comp.add(PREP_JS)
    comp.add(ED.PREP)
    comp.add(html)
    pg.set_content(comp.document(), wait_until="load")
    pg.evaluate(M.READY_JS)
    png = CE._stable(pg, 500, True, False)
    return png, pg.evaluate(CHECK_JS, NO_TEXT)


def render(spec: dict, dest: list, recent_heroes: set = frozenset(), recent_hashes: list = (),
           variant: int = 0, check: bool = True) -> list:
    """Draw the main thumbnail and two alternates into the paths `dest` (JPEG).
    Returns [{"path", "layout", "hero", "hash"}] in dest order. `variant`
    (the week) mirrors the layouts on alternate weeks; check=False draws
    without the checks (the last resort)."""
    from PIL import Image
    from playwright.sync_api import sync_playwright
    rows = spec["rows"]
    order = ALTERNATES.get(spec["family"], [spec["family"]])
    done, used_heroes, hashes = [], set(), list(recent_hashes)
    tries = [(lay, k) for k, lay in enumerate(order)] + [(lay, k + 3) for k, lay in enumerate(order)]
    with sync_playwright() as pw:
        br, pg = _page(pw)
        for lay, k in tries:
            if len(done) == len(dest):
                break
            s = _spec_for(lay, spec)
            if lay in ("versus",) and not s.get("pair"):
                continue
            pool = rows[:1] if lay in NEEDS_TOP else sorted(rows[:12], key=lambda r: _kind(r) != "outfit")
            fresh = [r for r in pool if r["key"] not in recent_heroes and r["key"] not in used_heroes]
            if not fresh and lay in NEEDS_TOP and done:
                continue
            hero = (fresh or pool)[0]
            flip = bool((variant + k) % 2)
            try:
                png, bad = _shot(pg, LAYOUTS[lay](s, rows, hero, flip))
            except Exception as e:  # noqa: BLE001 - a layout that can't draw this spec: the next one
                print(f"  thumbnail {lay}: {e!r}")
                continue
            if bad and check:
                print(f"  thumbnail {lay}: text where it shouldn't be {bad[:3]}")
                continue
            img = Image.open(BytesIO(png)).convert("RGB")
            h = dhash(img)
            if check and any(distance(h, o) <= SIMILAR for o in hashes):
                print(f"  thumbnail {lay}: too close to a recent one, trying another")
                continue
            path = Path(dest[len(done)])
            for q in (92, 88, 82, 75):
                img.save(path, "JPEG", quality=q, optimize=True)
                if path.stat().st_size < 1_900_000:
                    break
            done.append({"path": str(path), "layout": lay, "hero": hero["key"], "hash": f"{h:016x}"})
            used_heroes.add(hero["key"])
            hashes.append(h)
        br.close()
    return done
