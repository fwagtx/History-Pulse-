#!/usr/bin/env python3
"""
The code-entry card, with code BAD.

Item-shop YouTubers show a small card while they ask people to use their
Support-A-Creator code: a CREATOR CODE heading, a white box the code gets typed
into letter by letter, #EpicPartner under it, and an Accept button once the
code is in. This draws that card from scratch with BAD typed in, on the same
seek-and-capture engine as the videos (cc_motion), at 16:9 or 9:16.

Looks:
  classic  the card as those videos show it: navy heading bar, white box, grey
           Accept button. The code is typed in and the card holds.
  lime     the channel's colours. A pointer clicks Accept and the card turns
           into the SUPPORT-A-CREATOR: BAD confirmation.

The 9:16 versions keep everything inside the safe box every app leaves clear
(cc_safe) and add the three steps to use the code under the card.

Writes into --out, per look and size:
  code-bad-<look>-<size>.mp4          on a blurred item-shop wall, with typing sounds
  code-bad-<look>-<size>-<step>.jpg   stills of each step on that wall
and for 16:9, the overlays for putting the card over your own footage:
  code-bad-<look>-16x9-green.mp4        green screen, for any editor's chroma key
  code-bad-<look>-16x9-alpha.mov        transparent (QuickTime Animation), for editors
  code-bad-<look>-16x9-alpha.webm       transparent (VP9), for OBS and browsers
  code-bad-<look>-16x9-<step>.png       transparent stills
plus contact-sheet.jpg with every look and step side by side.

  python3 scripts/cc_code_entry.py --art DIR [--out DIR] [--looks classic,lime] [--sizes 16x9,9x16]

--art is a folder of cosmetic cut-outs with a meta.json ([{file, rarity}]) for
the backdrop; without it the backdrop is plain rarity-coloured tiles.
"""

import argparse
import base64
import json
import shutil
import subprocess
from pathlib import Path

import cc_audio as A
import cc_motion as M
from cc_common import ROOT, log
from cc_motion import ACCENT, INK, RARITY, an, esc, style_anim

CODE = "BAD"
SIZES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
GREEN = "#00FF00"
FPS = 30
SEED = 20260927

# The card as the item-shop videos draw it, measured off their 1920x1080 frames (px).
CARD_W, CARD_H, HEAD_H = 1278, 593, 234
TITLE_TOP = 59                           # CREATOR CODE line box; caps start at 62
FIELD_X, FIELD_Y, FIELD_W, FIELD_H = 42, 285, 1192, 77
EPIC_TOP = 425                           # #EpicPartner line box; caps start at 435
ACC_X, ACC_Y, ACC_W, ACC_H = 816, 417, 396, 141

# Degrees and px per letter of CREATOR CODE.
TITLE_TILT = [(-1.2, 0), (1, -2), (-.8, 1), (1.2, -1), (-1, 2), (.8, 0), (-1.2, -1), (0, 0),
              (1, 1), (-.9, -2), (1.1, 1), (-.7, 0)]

# 9:16: the card across the top of the safe box's wide band (x 60-1020, y 230-740),
# its text at y >= 285 for Instagram's grid crop; the steps below, left of the rail.
V_SCALE, V_X, V_Y = 940 / CARD_W, 70, 296

LOOKS = {
    "classic": dict(head="#1c2339", body="#2e3751", bar=False, ink="#101010", weight=400, ring="",
                    btn="#acacac", btn_ink="#3a4157", btn_edge="#ffffff", btn_weight=400, radius=0,
                    btn_shadow="", story=False, dot="#2e3751", dot_ink="#ffffff", hi="#ffffff",
                    kicker="rgba(255,255,255,.78)"),
    "lime": dict(head="#101114", body="#1f2127", bar=True, ink=INK, weight=700, ring=ACCENT,
                 btn=ACCENT, btn_ink=INK, btn_edge=ACCENT, btn_weight=700, radius=16,
                 btn_shadow="box-shadow:0 9px 0 #8fa300,0 18px 30px rgba(0,0,0,.35);", story=True,
                 dot=ACCENT, dot_ink=INK, hi=ACCENT, kicker=ACCENT),
}

# Keyframes, "ce"-prefixed: the card also goes inside every video (cc_end_card),
# next to the looks' own animations.
CSS = """
@keyframes cecardin{0%{opacity:0;transform:scale(.9)}60%{opacity:1;transform:scale(1.015)}100%{opacity:1;transform:none}}
@keyframes cecardout{from{opacity:1;transform:none}to{opacity:0;transform:scale(.94)}}
@keyframes cecardgone{from{opacity:1;transform:none}to{opacity:0;transform:scale(.4)}}
@keyframes cebtnin{0%{opacity:0;transform:scale(.7)}60%{opacity:1;transform:scale(1.06)}100%{opacity:1;transform:none}}
@keyframes cepress{0%,100%{transform:none;filter:none}35%{transform:translateY(7px) scale(.97);filter:brightness(.86)}}
@keyframes ceblink{0%,49.9%{opacity:1}50%,100%{opacity:0}}
@keyframes ceptr{0%{transform:translate(320px,230px);opacity:0}25%{opacity:1}100%{transform:none;opacity:1}}
@keyframes cesquish{0%,100%{transform:none}40%{transform:scale(.8)}}
@keyframes cedrift{from{transform:translate(0,0) scale(1.04)}to{transform:translate(-70px,-30px) scale(1.04)}}
"""

POINTER = ('<svg width="56" height="80" viewBox="0 0 28 40"><path d="M2 2v30.5l7.6-7.3 5.2 12.3 '
           '5.6-2.4-5.1-12H26z" fill="#fff" stroke="#0A0A0B" stroke-width="2.2" '
           'stroke-linejoin="round"/></svg>')


def check_icon(size: float) -> str:
    return (f'<svg width="{size:.0f}" height="{size:.0f}" viewBox="0 0 24 24" style="flex:none">'
            f'<circle cx="12" cy="12" r="12" fill="{INK}"/><path d="M6.4 12.6l3.7 3.6 7.5-8.1" '
            f'fill="none" stroke="{ACCENT}" stroke-width="3" stroke-linecap="round" '
            f'stroke-linejoin="round"/></svg>')


class Frame(M.Comp):
    """A composition at any size, on the item-shop wall, green screen or nothing."""

    def __init__(self, duration: float, w: int, h: int, bg: str):
        super().__init__(duration)
        self.w, self.h, self.bg = w, h, bg

    def document(self) -> str:
        over = f"html,body{{width:{self.w}px;height:{self.h}px;background:{self.bg}}}"
        return super().document().replace("</style>", over + "</style>", 1)


def timeline(code: str, story: bool, pop_in: bool, vertical: bool) -> dict:
    """When everything happens, in seconds. The 16:9 card pops in and out so it
    can sit over other footage; the 9:16 one is there from frame 0 (the cover)."""
    t = {"card": .12 if pop_in else 0.0}
    first = t["card"] + (.8 if pop_in else .9)
    t["keys"] = [round(first + i * .24, 3) for i in range(len(code))]
    t["accept"] = t["keys"][-1] + .42
    hold = t["accept"]
    if story:
        t["click"] = t["accept"] + 1.1
        t["done"] = t["click"] + .22
        # In 16:9 the card shrinks away first, then the confirmation pops in its
        # place; in 9:16 the card stays and the confirmation pops in under it.
        t["pill"] = t["done"] + (.22 if pop_in else .06)
        hold = t["done"]
    t["out"] = hold + (3.2 if vertical else 2.5)
    t["end"] = t["out"] + (.55 if pop_in else 0)
    return t


def still_times(t: dict, code: str) -> dict:
    """The moments worth a still: empty box, each letter, the Accept button, done."""
    s = {"1-empty": t["card"] + .45}
    for i, k in enumerate(t["keys"]):
        s[f"{i + 2}-{code[:i + 1]}"] = k + .12
    n = len(code) + 2
    s[f"{n}-accept"] = (t["click"] - .06) if "click" in t else t["accept"] + .6
    if "done" in t:
        s[f"{n + 1}-done"] = t["pill"] + .6
    return s


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _dark(c: str, f: float = .22) -> str:
    c = M.hexcol(c, "#3a3a44")
    return "#" + "".join(f"{int(int(c[i:i + 2], 16) * f):02x}" for i in (1, 3, 5))


def wall_art(art_dir: Path | None) -> list:
    """[(data URI, rarity)] from a folder of cut-outs with a meta.json."""
    arts = []
    if art_dir and (art_dir / "meta.json").exists():
        for m in json.loads((art_dir / "meta.json").read_text()):
            f = art_dir / m.get("file", "")
            if f.is_file():
                arts.append((data_uri(f), m.get("rarity", "")))
    return arts


def shop_wall(comp: M.Comp, w: int, h: int, arts: list) -> str:
    """The backdrop: a wall of item-shop tiles, blurred and dimmed so the card
    reads first -- the card sits over the shop in the videos it comes from.
    arts: [(data URI, rarity)]; each picture goes into the page once, as a CSS
    class the tiles share. Without any, plain rarity-coloured tiles."""
    tw, th, gap = 300, 430, 22
    cols, rows = (w + 260) // (tw + gap) + 1, (h + 260) // (th + gap) + 1
    classes = []
    for uri, _ in arts:
        name = comp.uid("cew")
        comp.css(f".{name}{{background:url({uri}) 50% 100%/auto 110% no-repeat}}")
        classes.append(name)
    tiles = []
    for r in range(rows):
        for col in range(cols):
            i = r * cols + col
            if arts:
                j = (i * 7 + r * 3) % len(arts)
                rarity, art = arts[j][1], f'<div class="full {classes[j]}"></div>'
            else:
                rarity, art = ("rare", "epic", "legendary", "uncommon", "icon")[i % 5], ""
            c = RARITY.get(rarity, "#3a3a44")
            tiles.append(f'<div style="position:relative;width:{tw}px;height:{th}px;border-radius:12px;'
                         f'overflow:hidden;background:radial-gradient(ellipse 95% 75% at 50% 32%,{c} 0%,'
                         f'{_dark(c)} 100%)">{art}<div class="abs" style="left:0;right:0;bottom:0;height:34%;'
                         f'background:linear-gradient(transparent,rgba(0,0,0,.7))"></div></div>')
    grid = (f'<div class="abs" style="left:-130px;top:-130px;display:grid;'
            f'grid-template-columns:repeat({cols},{tw}px);gap:{gap}px;'
            f'{style_anim(an("cedrift", 0, 14, "linear"))}">{"".join(tiles)}</div>')
    return (f'<div class="full" data-safe="ignore" style="overflow:hidden;background:{INK}">'
            f'<div class="full" style="filter:blur(7px) brightness(.5) saturate(1.1)">{grid}</div>'
            f'<div class="full" style="background:radial-gradient(ellipse 70% 62% at 50% 48%,'
            f'rgba(10,10,11,.1),rgba(10,10,11,.78))"></div><div class="grain"></div></div>')


def outlined(text: str, css: str, stroke: float, shadow: bool) -> str:
    """White bold text with a black outline, drawn as two layers so the outline
    sits outside the letters (like #EpicPartner in the videos)."""
    sh = "text-shadow:2px 4px 5px rgba(0,0,0,.55);" if shadow else ""
    return (f'<div style="{css};color:#000;-webkit-text-stroke:{stroke:.1f}px #000;{sh}">{esc(text)}</div>'
            f'<div style="{css};color:#fff">{esc(text)}</div>')


def card(L: dict, code: str, t: dict, x: float, y: float, k: float, shadow: bool, collapse: bool,
         field_px: int = 67) -> str:
    """The card at (x, y), scaled by k. t: timeline(). collapse: shrink away at t['done']
    (the confirmation takes its place). field_px: the typed code's size before scaling."""
    anims = [an("cecardin", t["card"], .42)] if t["card"] > 0 else []
    if collapse:
        anims.append(an("cecardgone", t["done"], .25, "cubic-bezier(.5,0,1,1)", fill="forwards"))
    elif t["out"] < t["end"]:
        anims.append(an("cecardout", t["out"], .35, "ease-in", fill="forwards"))

    head = (f'<div class="abs" style="left:0;top:0;width:{CARD_W}px;height:{HEAD_H}px;'
            f'background:{L["head"]};border-radius:6px 6px 0 0"></div>')
    bar = (f'<div class="abs" style="left:0;top:{HEAD_H - 8}px;width:{CARD_W}px;height:8px;'
           f'background:{ACCENT}"></div>') if L["bar"] else ""
    # Anton stands in for Fortnite's heading face: a stroke in its own colour
    # gives it the same black weight, 14% more width its proportions, and a
    # small tilt per letter its hand-cut look.
    letters = "".join(ch if ch == " " else
                      f'<span style="display:inline-block;transform:translateY({dy}px) rotate({r}deg)">{ch}</span>'
                      for ch, (r, dy) in zip("CREATOR CODE", TITLE_TILT))
    title = (f'<div class="abs" style="left:38px;top:{TITLE_TOP}px;font:400 119px/119px Anton,Impact,sans-serif;'
             f'letter-spacing:.02em;color:#fff;-webkit-text-stroke:6px #fff;white-space:nowrap;'
             f'transform:scaleX(1.14);transform-origin:0 50%">{letters}</div>')

    # The typing: one layer per prefix ("", "B", "BA", "BAD"), each showing until
    # the next key lands, with the caret after it. Its blink restarts on every key.
    click = [an("fadeout", t["click"], .001, "linear", fill="forwards")] if "click" in t else []
    layers = []
    for i in range(len(code) + 1):
        start = t["card"] if i == 0 else t["keys"][i - 1]
        show = [an("fadein", start, .001, "linear")] if i else []
        hide = [an("fadeout", t["keys"][i], .001, "linear", fill="forwards")] if i < len(code) else []
        caret = (f'<i style="display:inline-block;width:4px;height:60px;margin-left:5px;vertical-align:-9px;'
                 f'background:{L["ink"]};{style_anim(an("ceblink", start, 1.06, "linear", "infinite"), *(click if i == len(code) else []))}"></i>')
        layers.append(f'<div class="abs" style="left:22px;top:0;height:{FIELD_H}px;{style_anim(*show) if show else ""}">'
                      f'<div style="font:{L["weight"]} {field_px}px/{FIELD_H}px \'Liberation Sans\',Arial,sans-serif;'
                      f'color:{L["ink"]};white-space:pre;{style_anim(*hide) if hide else ""}">{esc(code[:i])}{caret}</div></div>')
    ring = (f'<div class="abs" style="left:{FIELD_X - 7}px;top:{FIELD_Y - 7}px;width:{FIELD_W + 14}px;'
            f'height:{FIELD_H + 14}px;border:5px solid {L["ring"]};border-radius:5px;'
            f'{style_anim(*click) if click else ""}"></div>') if L["ring"] else ""
    field = (f'<div class="abs" style="left:{FIELD_X}px;top:{FIELD_Y}px;width:{FIELD_W}px;height:{FIELD_H}px;'
             f'background:#fff;overflow:hidden">{"".join(layers)}</div>')

    epic = outlined("#EpicPartner", f"position:absolute;left:{FIELD_X}px;top:{EPIC_TOP}px;"
                    f"font:700 82px/82px 'Liberation Sans',Arial,sans-serif;letter-spacing:.012em;white-space:nowrap", 9, shadow)

    press = [an("cepress", t["click"], .22, "ease-out")] if "click" in t else []
    accept = (f'<div class="abs" style="left:{ACC_X}px;top:{ACC_Y}px;width:{ACC_W}px;height:{ACC_H}px;'
              f'{style_anim(an("cebtnin", t["accept"], .45))}">'
              f'<div class="full" style="background:{L["btn"]};border:6px solid {L["btn_edge"]};'
              f'border-radius:{L["radius"]}px;{L["btn_shadow"] if shadow else ""}display:flex;align-items:center;'
              f'justify-content:center;font:{L["btn_weight"]} 68px/1 \'Liberation Sans\',Arial,sans-serif;'
              f'color:{L["btn_ink"]};{style_anim(*press) if press else ""}">Accept</div></div>')

    pointer = ""
    if "click" in t:
        tipx, tipy = ACC_X + ACC_W * .83, ACC_Y + ACC_H * .74      # right of the word, not on it
        drop = "filter:drop-shadow(0 5px 6px rgba(0,0,0,.5));" if shadow else ""
        pointer = (f'<div class="abs" style="left:{tipx - 4:.0f}px;top:{tipy - 4:.0f}px;z-index:5;{drop}'
                   f'{style_anim(an("ceptr", t["accept"] + .25, .8, "cubic-bezier(.3,.1,.2,1)"))}">'
                   f'<div style="transform-origin:4px 4px;{style_anim(an("cesquish", t["click"] - .02, .2, "ease-out"))}">'
                   f'{POINTER}</div></div>')

    look = "box-shadow:0 26px 70px rgba(0,0,0,.6),0 6px 0 rgba(0,0,0,.28);" if shadow else ""
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{CARD_W}px;height:{CARD_H}px;'
            f'transform-origin:0 0;transform:scale({k:.4f});z-index:5">'
            f'<div class="full" style="background:{L["body"]};border-radius:6px;{look}'
            f'{style_anim(*anims) if anims else ""}">'
            f'{head}{bar}{title}{ring}{field}{epic}{accept}{pointer}</div></div>')


def confirmation(code: str, t: dict, cx: float, cy: float, s: float, with_epic: bool, shadow: bool) -> str:
    """SUPPORT-A-CREATOR: BAD -- what the shop's button reads once the code is in."""
    anims = [an("cebtnin", t["pill"], .5)]
    if t["out"] < t["end"]:
        anims.append(an("cecardout", t["out"], .35, "ease-in", fill="forwards"))
    sh = "box-shadow:0 10px 0 rgba(0,0,0,.35),0 30px 60px rgba(0,0,0,.45);" if shadow else ""
    epic = outlined("#EpicPartner", f"position:absolute;left:0;top:0;font:700 {50 * s:.0f}px/1 "
                    f"'Liberation Sans',Arial,sans-serif;white-space:nowrap", 7 * s, shadow)
    epic = (f'<div style="position:relative;height:{50 * s:.0f}px;width:{6.2 * 50 * s:.0f}px">{epic}</div>'
            if with_epic else "")
    return (f'<div class="abs" style="left:{cx:.0f}px;top:{cy:.0f}px;transform:translate(-50%,-50%);z-index:6">'
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:{30 * s:.0f}px;{style_anim(*anims)}">'
            f'<div style="display:flex;align-items:center;gap:{22 * s:.0f}px;background:{ACCENT};color:{INK};'
            f'border-radius:999px;padding:{20 * s:.0f}px {46 * s:.0f}px {20 * s:.0f}px {22 * s:.0f}px;{sh}'
            f'font:800 {58 * s:.0f}px/1 Inter,sans-serif;letter-spacing:.02em;white-space:nowrap">'
            f'{check_icon(84 * s)}SUPPORT-A-CREATOR: {esc(code)}</div>{epic}</div></div>')


def how_to(L: dict, code: str, top: int) -> str:
    """The three steps, under the card in the 9:16 version."""
    rows = ["Open the Item Shop", "Select SUPPORT-A-CREATOR",
            f'Type <b style="color:{L["hi"]}">{esc(code)}</b> and confirm']
    out = [f'<div class="abs" style="left:110px;top:{top}px;font:800 32px/1 Inter,sans-serif;letter-spacing:.16em;'
           f'color:{L["kicker"]};text-shadow:0 2px 8px rgba(0,0,0,.8)">HOW TO USE CODE {esc(code)}</div>']
    for i, row in enumerate(rows):
        y = top + 64 + i * 112
        out.append(f'<div class="abs" style="left:110px;top:{y}px;display:flex;align-items:center;gap:26px">'
                   f'<div style="flex:none;width:76px;height:76px;border-radius:50%;background:{L["dot"]};'
                   f'color:{L["dot_ink"]};display:flex;align-items:center;justify-content:center;'
                   f'font:400 46px/1 Anton,sans-serif;box-shadow:0 6px 0 rgba(0,0,0,.35)">{i + 1}</div>'
                   f'<div style="font:700 42px/1.1 Inter,sans-serif;color:#fff;white-space:nowrap;'
                   f'text-shadow:0 3px 10px rgba(0,0,0,.9)">{row}</div></div>')
    return "".join(out)


def compose(look: str, size: str, mode: str, code: str = CODE, art_dir: Path | None = None):
    """One composition. mode: 'wall' (item-shop backdrop), 'green' or 'alpha'."""
    w, h = SIZES[size]
    L = LOOKS[look]
    vertical = h > w
    t = timeline(code, L["story"], pop_in=not vertical, vertical=vertical)
    c = Frame(t["end"], w, h, {"wall": INK, "green": GREEN, "alpha": "transparent"}[mode])
    c.use_fonts("Liberation Sans")
    c.css(CSS)
    shadow = mode != "green"            # soft shadows would leave a dark fringe after keying
    if mode == "wall":
        c.add(shop_wall(c, w, h, wall_art(art_dir)))
    if vertical:
        k, x, y = V_SCALE, V_X, V_Y
    else:
        k, x, y = 1.0, (w - CARD_W) / 2, (h - CARD_H) / 2
    c.add(card(L, code, t, x, y, k, shadow, collapse=L["story"] and not vertical))
    if L["story"]:
        if vertical:
            c.add(confirmation(code, t, w / 2, V_Y + CARD_H * k + 96, .66, False, shadow))
        else:
            c.add(confirmation(code, t, w / 2, h / 2, 1.15, True, shadow))
    if vertical:
        c.add(how_to(L, code, 930 if L["story"] else 830))

    if t["card"] > 0:
        c.cue(t["card"], "pop")
    for key in t["keys"]:
        c.cue(key, "tick")
    c.cue(t["accept"], "pop")
    if "click" in t:
        c.cue(t["click"], "click")
        c.cue(t["pill"], "ding")
    if t["out"] < t["end"]:
        c.cue(t["out"], "whoosh")
    return c, t


# ------------------------------------------------------------------- render

def _grab(page, t_ms: float, png: bool, alpha: bool, settle: bool = False) -> bytes:
    page.evaluate(M.SETTLE_JS if settle else M.SEEK_JS, t_ms)
    if png:
        return page.screenshot(type="png", omit_background=alpha)
    return page.screenshot(type="jpeg", quality=92)


def _stable(page, t_ms: float, png: bool, alpha: bool) -> bytes:
    """Re-capture until two in a row agree (see cc_motion.stable_shot)."""
    prev = _grab(page, t_ms, png, alpha, True)
    for _ in range(8):
        cur = _grab(page, t_ms, png, alpha, True)
        if cur == prev:
            return cur
        prev = cur
    return prev


def capture(comp: Frame, sink, alpha: bool = False, stills: dict | None = None) -> dict:
    """Seek through every frame and hand each to sink(i, bytes): JPEG, or PNG
    with transparency when alpha. Returns {label: PNG bytes} for the stills."""
    from playwright.sync_api import sync_playwright
    n = int(round(comp.duration * FPS))
    shots = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(args=M.CHROME_ARGS)
        page = browser.new_page(viewport={"width": comp.w, "height": comp.h}, device_scale_factor=1)
        page.set_content(comp.document(), wait_until="load")
        page.evaluate(M.READY_JS)
        for i in range(n):
            t_ms = i / FPS * 1000
            sink(i, _stable(page, t_ms, alpha, alpha) if i == 0 else _grab(page, t_ms, alpha, alpha))
        for label, s in (stills or {}).items():
            shots[label] = _stable(page, s * 1000, True, alpha)
        browser.close()
    return shots


def _ffmpeg() -> str:
    return M.find_ffmpeg() or "ffmpeg"


def encode_mp4(comp: Frame, out: Path, wav: Path, stills: dict | None = None, crf: int = 16) -> dict:
    cmd = [_ffmpeg(), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
           "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-r", str(FPS), "-t", f"{comp.duration:.3f}", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        shots = capture(comp, lambda i, b: proc.stdin.write(b), stills=stills)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code:
        raise RuntimeError(f"ffmpeg exited {code} for {out.name}")
    return shots


def encode_alpha(comp: Frame, base: Path, wav: Path, stills: dict | None = None) -> dict:
    """Transparent frames -> QuickTime Animation .mov (editors) and VP9 .webm (OBS)."""
    tmp = base.parent / f".{base.name}-frames"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)

    def sink(i, b):
        (tmp / f"{i:05d}.png").write_bytes(b)
    shots = capture(comp, sink, alpha=True, stills=stills)
    frames = ["-framerate", str(FPS), "-i", str(tmp / "%05d.png"), "-i", str(wav), "-map", "0:v", "-map", "1:a",
              "-t", f"{comp.duration:.3f}"]
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", *frames, "-c:v", "qtrle", "-pix_fmt", "argb",
                    "-c:a", "pcm_s16le", str(base.with_suffix(".mov"))], check=True)
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", *frames, "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
                    "-b:v", "0", "-crf", "24", "-row-mt", "1", "-deadline", "good", "-cpu-used", "2",
                    "-auto-alt-ref", "0", "-c:a", "libopus", "-b:a", "128k", str(base.with_suffix(".webm"))],
                   check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return shots


def render_set(look: str, size: str, out: Path, art_dir: Path | None, code: str, overlays: bool) -> dict:
    name = f"code-{code.lower()}-{look}-{size}"
    wall, t = compose(look, size, "wall", code, art_dir)
    wav = out / f".{name}.wav"
    A.write_wav(A.mix(wall.duration, wall.cues, SEED, music_gain=0), wav)
    stills = still_times(t, code)
    log(f"{name}: {wall.duration:.2f}s on the shop wall")
    shots = encode_mp4(wall, out / f"{name}.mp4", wav, stills)
    files = [out / f"{name}.mp4"]
    for label, png in shots.items():
        path = out / f"{name}-{label}.jpg"
        _to_jpeg(png, path)
        files.append(path)
    if overlays:
        log(f"{name}: green screen")
        green, _ = compose(look, size, "green", code)
        encode_mp4(green, out / f"{name}-green.mp4", wav, crf=12)
        log(f"{name}: transparent")
        alpha, _ = compose(look, size, "alpha", code)
        clear = encode_alpha(alpha, out / f"{name}-alpha", wav, stills)
        files += [out / f"{name}-green.mp4", out / f"{name}-alpha.mov", out / f"{name}-alpha.webm"]
        for label, png in clear.items():
            path = out / f"{name}-{label}.png"
            path.write_bytes(png)
            files.append(path)
    wav.unlink(missing_ok=True)
    return {"name": name, "look": look, "size": size, "duration": round(wall.duration, 2),
            "stills": {k: str(out / f"{name}-{k}.jpg") for k in shots}, "files": [str(f) for f in files]}


def _to_jpeg(png: bytes, path: Path, quality: int = 92):
    from io import BytesIO
    from PIL import Image
    Image.open(BytesIO(png)).convert("RGB").save(path, quality=quality)


def contact_sheet(sets: list, dest: Path):
    """Every look and step in one picture, for choosing."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(str(M.FONTS / "Inter-Variable.ttf"), 26)
    big = ImageFont.truetype(str(M.FONTS / "Anton-Regular.ttf"), 44)
    pad, gap = 40, 18
    rows = []
    for s in sets:
        w, h = SIZES[s["size"]]
        tw = 420 if w > h else 236
        th = round(tw * h / w)
        rows.append((s, tw, th))
    width = pad * 2 + max(len(s["stills"]) * (tw + gap) - gap for s, tw, _ in rows)
    height = pad + sum(th + 110 for _, _, th in rows) + pad
    sheet = Image.new("RGB", (width, height), INK)
    d = ImageDraw.Draw(sheet)
    y = pad
    for s, tw, th in rows:
        d.text((pad, y), f"{s['look'].upper()}  {s['size'].replace('x', ':')}", font=big, fill=ACCENT)
        y += 70
        x = pad
        for label, path in s["stills"].items():
            im = Image.open(path).convert("RGB").resize((tw, th), Image.LANCZOS)
            sheet.paste(im, (x, y))
            d.text((x, y + th + 6), label.split("-", 1)[1], font=font, fill="#cfcfcf")
            x += tw + gap
        y += th + 40
    sheet.save(dest, quality=88)
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "creator-code" / "out" / "code-entry"))
    ap.add_argument("--art", default="", help="folder of cosmetic cut-outs with meta.json, for the backdrop")
    ap.add_argument("--code", default=CODE)
    ap.add_argument("--looks", default=",".join(LOOKS))
    ap.add_argument("--sizes", default=",".join(SIZES))
    ap.add_argument("--no-overlays", action="store_true", help="skip the green-screen and transparent versions")
    ap.add_argument("--check", action="store_true", help="run the safe-zone check on the 9:16 versions")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    art = Path(a.art) if a.art else None
    code = a.code.strip().upper()
    sets = []
    for size in a.sizes.split(","):
        for look in a.looks.split(","):
            if a.check and size == "9x16":
                import cc_safe as S
                res = S.check(compose(look, size, "wall", code, art)[0])
                log(f"{look} {size}: {S.summary(res)}")
            sets.append(render_set(look, size, out, art, code, overlays=(size == "16x9" and not a.no_overlays)))
    # Keep the versions rendered earlier into the same folder, so re-rendering
    # one look doesn't drop the others from the contact sheet.
    index = out / "code-entry.json"
    known = {s["name"]: s for s in (json.loads(index.read_text()) if index.exists() else [])
             if all(Path(p).exists() for p in s["stills"].values())}
    known.update({s["name"]: s for s in sets})
    order = [f"code-{code.lower()}-{look}-{size}" for size in SIZES for look in LOOKS]
    sets = sorted(known.values(), key=lambda s: order.index(s["name"]) if s["name"] in order else len(order))
    index.write_text(json.dumps(sets, indent=1))
    log(f"contact sheet: {contact_sheet(sets, out / 'contact-sheet.jpg')}")


if __name__ == "__main__":
    main()
