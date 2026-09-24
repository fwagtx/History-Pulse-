"""
Motion engine for @usecodebad videos.

A video is ONE html document. Every element's CSS animation is placed on a single
absolute timeline (seconds from the start). To render, headless Chromium loads the
document, and for each output frame we pause every animation and seek it to that
exact time with the Web Animations API, then screenshot. Frames are piped straight
into ffmpeg.

Why seek-and-capture instead of screen recording: it's deterministic. Every frame
lands exactly on time, nothing drops on a slow machine, and a re-run produces the
same video. It also means real motion design -- overshoot, float, squash, rolling
counters, draining rings -- instead of a zoom over a still image.

Requires Playwright (pip install playwright) and ffmpeg. Chromium comes from
Playwright's managed browsers or an installed Chrome.
"""

import base64
import html as _html
import shutil
import subprocess
from pathlib import Path

from cc_common import ROOT, log

W, H = 1080, 1920
FPS = 30
FONTS = ROOT / "creator-code" / "assets" / "fonts"

ACCENT = "#E8FF3A"
INK = "#0A0A0B"

RARITY = {
    "common": "#9AA0A6", "uncommon": "#5BC44A", "rare": "#4A9FF5",
    "epic": "#B451E8", "legendary": "#EE8B3D", "mythic": "#F7D94C",
    "icon": "#3DD6C9", "marvel": "#E5504F", "dc": "#4C5EAB",
    "starwars": "#C7A008", "gaminglegends": "#8E2CF5",
}

# TikTok draws its UI over the edges: tabs across the top, the caption and handle
# across the bottom, and the like/comment/share rail down the right from about
# y=880. Anything that matters stays inside y 190..1480, and right of x=960 is off
# limits below y=880.
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT, RAIL_TOP = 190, 1480, 960, 880

esc = _html.escape


def _font_face(family: str, file: str, weight: str, style: str = "normal") -> str:
    path = FONTS / file
    if not path.exists():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    kind = ("woff2", "font/woff2") if file.endswith(".woff2") else ("truetype", "font/ttf")
    return (f"@font-face{{font-family:'{family}';src:url(data:{kind[1]};base64,{b64}) "
            f"format('{kind[0]}');font-weight:{weight};font-style:{style};font-display:block}}")


def extra_fonts(families) -> str:
    """@font-face rules for the extra (Google, OFL) fonts the new looks use,
    listed in assets/fonts/fonts.json. Only the families asked for are embedded."""
    reg = FONTS / "fonts.json"
    if not families or not reg.exists():
        return ""
    import json as _json
    return "".join(_font_face(f["family"], f["file"], f["weight"], f["style"])
                   for f in _json.loads(reg.read_text()) if f["family"] in families)


# Film grain kills the flat, too-clean look that reads as auto-generated.
GRAIN = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' "
         "stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' "
         "opacity='.55'/></svg>")

BASE_CSS = f"""
@property --p {{ syntax:'<number>'; inherits:false; initial-value:1; }}
@property --n {{ syntax:'<integer>'; inherits:false; initial-value:0; }}
*{{margin:0;padding:0;box-sizing:border-box}}
*,*::before,*::after{{animation-play-state:paused !important}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{INK};color:#fff;
  font-family:'Inter',system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
.d{{font-family:'Anton',Impact,sans-serif;text-transform:uppercase;letter-spacing:.01em;
  line-height:.9}}
.abs{{position:absolute}}
.full{{position:absolute;inset:0}}
.scene{{position:absolute;inset:0;opacity:0}}
.grain{{position:absolute;inset:-50%;background:url("{GRAIN}");opacity:.07;
  mix-blend-mode:overlay;pointer-events:none}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse 75% 60% at 50% 45%,
  transparent 55%,rgba(0,0,0,.72) 100%);pointer-events:none}}
.art{{display:block;object-fit:contain;filter:drop-shadow(0 30px 40px rgba(0,0,0,.55))}}
.pill{{display:inline-flex;align-items:center;gap:12px;background:rgba(10,10,11,.84);
  border:2px solid {ACCENT};border-radius:16px;padding:10px 20px}}
.ring{{border-radius:50%;background:conic-gradient({ACCENT} calc(var(--p)*360deg),
  rgba(255,255,255,.14) 0)}}
.count{{counter-reset:n var(--n)}}.count::after{{content:counter(n)}}

@keyframes pop{{0%{{transform:scale(.15) rotate(-8deg);opacity:0}}
  55%{{transform:scale(1.1) rotate(2deg);opacity:1}}75%{{transform:scale(.96) rotate(-1deg)}}
  100%{{transform:scale(1) rotate(0)}}}}
@keyframes slam{{0%{{transform:scale(2.6);opacity:0}}60%{{transform:scale(.94);opacity:1}}
  100%{{transform:scale(1);opacity:1}}}}
@keyframes punch{{0%{{transform:scale(1.1);opacity:1}}55%{{transform:scale(.97)}}100%{{transform:scale(1);opacity:1}}}}
@keyframes thump{{0%,100%{{transform:scale(1)}}35%{{transform:scale(1.07)}}}}
@keyframes hop{{0%,100%{{transform:none}}35%{{transform:translateY(-38px) rotate(-2deg)}}
  70%{{transform:translateY(5px) scaleY(.97)}}}}
@keyframes boing{{0%,100%{{transform:scale(1) rotate(0)}}40%{{transform:scale(1.16) rotate(3deg)}}
  70%{{transform:scale(.96) rotate(-1deg)}}}}
@keyframes rise{{0%{{transform:translateY(60px);opacity:0}}100%{{transform:none;opacity:1}}}}
@keyframes fromL{{0%{{transform:translateX(-120%) rotate(-10deg)}}70%{{transform:translateX(4%) rotate(1deg)}}
  100%{{transform:none}}}}
@keyframes fromR{{0%{{transform:translateX(120%) rotate(10deg)}}70%{{transform:translateX(-4%) rotate(-1deg)}}
  100%{{transform:none}}}}
@keyframes drop{{0%{{transform:translateY(-140%)}}60%{{transform:translateY(3%) scaleY(.93) scaleX(1.05)}}
  80%{{transform:translateY(-2%) scaleY(1.03) scaleX(.98)}}100%{{transform:none}}}}
@keyframes float{{0%{{transform:translateY(0) rotate(-1.4deg)}}100%{{transform:translateY(-22px) rotate(1.4deg)}}}}
@keyframes sway{{0%{{transform:rotate(-3deg) scaleY(1)}}50%{{transform:rotate(0) scaleY(1.025)}}
  100%{{transform:rotate(3deg) scaleY(1)}}}}
@keyframes shadow{{0%{{transform:scaleX(1);opacity:.55}}100%{{transform:scaleX(.82);opacity:.3}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.06)}}}}
@keyframes wobble{{0%,100%{{transform:rotate(-4deg)}}50%{{transform:rotate(4deg)}}}}
@keyframes shake{{0%,100%{{transform:none}}20%{{transform:translate(-12px,6px)}}
  40%{{transform:translate(10px,-8px)}}60%{{transform:translate(-8px,-4px)}}80%{{transform:translate(6px,8px)}}}}
@keyframes drain{{from{{--p:1}}to{{--p:0}}}}
@keyframes fadein{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes fadeout{{from{{opacity:1}}to{{opacity:0}}}}
@keyframes strike{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes burst{{0%{{transform:translate(0,0) rotate(0) scale(1);opacity:1}}
  100%{{transform:translate(var(--dx),var(--dy)) rotate(var(--r)) scale(.35);opacity:0}}}}
@keyframes dim{{to{{filter:grayscale(.9) brightness(.45);transform:scale(.9)}}}}
@keyframes crown{{0%{{transform:translateY(-80px) scale(.3);opacity:0}}
  60%{{transform:translateY(8px) scale(1.15);opacity:1}}100%{{transform:none;opacity:1}}}}
"""

# Anton advance widths in em (caps), measured in the render browser. Lets a
# layout size display text to fit the frame instead of letting it run off.
ANTON = {
    'A': .495, 'B': .489, 'C': .484, 'D': .503, 'E': .422, 'F': .409, 'G': .495, 'H': .509,
    'I': .237, 'J': .476, 'K': .482, 'L': .408, 'M': .756, 'N': .508, 'O': .496, 'P': .482,
    'Q': .504, 'R': .487, 'S': .472, 'T': .406, 'U': .484, 'V': .479, 'W': .722, 'X': .494,
    'Y': .456, 'Z': .42, '0': .504, '1': .341, '2': .504, '3': .504, '4': .504, '5': .504,
    '6': .504, '7': .504, '8': .504, '9': .504, "'": .224, '.': .239, ',': .246, '-': .321,
    '!': .239, '?': .502, '&': .53, ':': .252, '/': .415, '(': .301, ')': .301, '#': .556,
    '+': .365, '"': .439,
}


def anton_em(text: str) -> float:
    """Width of `text` in em as words() sets it: Anton caps, .01em tracking,
    .18em after every word."""
    ws = text.upper().split()
    return sum(ANTON.get(ch, .52) + .01 for w in ws for ch in w) + .18 * len(ws)


EASE_OUT = "cubic-bezier(.2,.8,.2,1)"
EASE_BACK = "cubic-bezier(.34,1.56,.64,1)"


def an(name: str, start: float, dur: float, ease: str = EASE_OUT,
       iters: str = "1", direction: str = "normal", fill: str = "both") -> str:
    """One `animation` shorthand entry placed at an absolute time."""
    return f"{name} {dur:.3f}s {ease} {start:.3f}s {iters} {direction} {fill}"


def style_anim(*entries: str) -> str:
    return "animation:" + ",".join(e for e in entries if e) + ";"


class Comp:
    """A composition: scenes and persistent layers on one absolute timeline."""

    def __init__(self, duration: float):
        self.duration = float(duration)
        self._css = []
        self._layers = []
        self._n = 0
        self.cues = []      # [(seconds, kind)] for sound design: whoosh/slam/tick/pop/reveal/cash
        self.fonts = set()  # extra font families to embed (see extra_fonts)

    def uid(self, prefix: str = "k") -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    def cue(self, t: float, kind: str):
        """Mark a sound effect at an exact time."""
        self.cues.append((round(float(t), 3), kind))

    def css(self, rule: str):
        self._css.append(rule)

    def use_fonts(self, *families: str):
        """Embed these extra font families (assets/fonts/fonts.json) in the page."""
        self.fonts.update(families)

    def add(self, html: str):
        """A persistent layer, visible for the whole video."""
        self._layers.append(html)

    def scene(self, start: float, end: float, inner: str,
              fade_in: float = .3, fade_out: float = .3, z: int = 1):
        """A full-frame layer visible only between start and end, with fades.

        Visibility is one keyframe track spanning the whole video, so a scene is
        exactly invisible outside its window no matter where we seek."""
        d = self.duration
        pct = lambda t: max(0.0, min(100.0, t / d * 100))
        name = self.uid("vis")
        a0, a1 = pct(start), pct(start + fade_in)
        b0, b1 = pct(end - fade_out), pct(end)
        # A scene that opens the video is fully visible on frame 0: that frame is
        # what people see as the video lands in their feed, never a black fade.
        frames = [f"0%{{opacity:{1 if start <= 0 else 0}}}"]
        if a0 > 0:
            frames.append(f"{a0:.4f}%{{opacity:0}}")
        frames.append(f"{a1:.4f}%{{opacity:1}}")
        frames.append(f"{b0:.4f}%{{opacity:1}}")
        frames.append(f"{b1:.4f}%{{opacity:0}}")
        frames.append("100%{opacity:0}")
        self.css(f"@keyframes {name}{{{''.join(frames)}}}")
        self._layers.append(
            f'<div class="scene" style="z-index:{z};animation:{name} {d:.3f}s linear 0s 1 normal both">'
            f"{inner}</div>")

    def document(self) -> str:
        fonts = (_font_face("Anton", "Anton-Regular.ttf", "400")
                 + _font_face("Inter", "Inter-Variable.ttf", "100 900") + extra_fonts(self.fonts))
        return ("<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
                + fonts + BASE_CSS + "\n".join(self._css)
                + "</style></head><body>" + "".join(self._layers) + "</body></html>")


# ---------------------------------------------------------------- components

def hexcol(c: str, fallback: str = "#2a2a33") -> str:
    c = (c or "").strip()
    return c if c.startswith("#") and len(c) == 7 else fallback


def tile_bg(colors: list, rarity: str = "", start: float = 0, rays: bool = True) -> str:
    """Epic's own tile colours as a lit stage: gradient, slow light rays,
    grain and vignette. Falls back to the rarity colour."""
    base = RARITY.get(rarity, "#3a3a44")
    c1 = hexcol(colors[0] if colors else "", base)
    c2 = hexcol(colors[1] if len(colors) > 1 else "", "#101014")
    ray = (f'<div class="abs" style="left:50%;top:40%;width:2600px;height:2600px;margin:-1300px 0 0 -1300px;'
           f'background:repeating-conic-gradient(from 0deg,rgba(255,255,255,.07) 0 6deg,transparent 6deg 18deg);'
           f'{style_anim(an("spin", start, 40, "linear", "infinite"))}"></div>') if rays else ""
    return (f'<div class="full" style="background:radial-gradient(ellipse 90% 65% at 50% 42%,{c1} 0%,'
            f'{c2} 58%,#050507 100%)"></div>{ray}<div class="grain"></div><div class="vig"></div>')


IN_PLACE = {"hop", "thump", "punch", "none"}      # entrances that start already on screen


def character(uri: str, cx: float, cy: float, h: float, start: float,
              enter: str = "pop", enter_dur: float = .8, idle: str = "float",
              rarity: str = "rare", label: str = "") -> str:
    """A cosmetic render that ENTERS (pop/drop/fromL/fromR) and then idles
    (float or sway) with a breathing floor shadow, so it reads as alive rather
    than pasted in. Three nested wrappers keep the transforms independent."""
    if uri:
        art = f'<img class="art" src="{uri}" style="height:{h:.0f}px;max-width:{W*.86:.0f}px">'
    else:
        col = RARITY.get(rarity, "#777")
        art = (f'<div class="d" style="height:{h:.0f}px;width:{h*.62:.0f}px;display:flex;'
               f'align-items:center;justify-content:center;font-size:{h*.09:.0f}px;color:{col};'
               f'border:4px dashed {col}66;border-radius:28px">{esc(label or "ITEM")}</div>')
    idle_dur = 2.2 if idle == "float" else 1.6
    idle_a = an(idle, start + enter_dur, idle_dur, "ease-in-out", "infinite", "alternate", "both")
    enter_a = an(enter, start, enter_dur, EASE_BACK if enter in ("pop",) else EASE_OUT)
    shadow_a = an("shadow", start + enter_dur, idle_dur, "ease-in-out", "infinite", "alternate", "both")
    # An in-place entrance (hop/thump/punch) means the cosmetic is already standing
    # there on frame 0, so its shadow is too; the others arrive, so it fades in.
    shadow_in = "" if enter in IN_PLACE else an("fadein", start, .4)
    return (f'<div class="abs" style="left:{cx:.0f}px;top:{cy:.0f}px;transform:translate(-50%,-50%)">'
            f'<div class="abs" style="left:50%;bottom:-{h*.06:.0f}px;width:{h*.5:.0f}px;height:{h*.07:.0f}px;'
            f'margin-left:-{h*.25:.0f}px;border-radius:50%;background:radial-gradient(closest-side,'
            f'rgba(0,0,0,.6),transparent);{style_anim(shadow_in, shadow_a)}"></div>'
            f'<div style="{style_anim(enter_a)}"><div style="transform-origin:50% 100%;{style_anim(idle_a)}">'
            f"{art}</div></div></div>")


def words(text: str, x: float, y: float, size: float, start: float, color: str = "#fff",
          stagger: float = .09, anim: str = "slam", align: str = "left", width: float = 0,
          shadow: bool = True, lh: float = .92) -> str:
    """Display text whose words land one after another."""
    parts = []
    for i, w in enumerate(text.split()):
        a = style_anim(an(anim, start + i * stagger, .5, EASE_OUT))
        parts.append(f'<span style="display:inline-block;margin-right:.18em;{a}">{esc(w)}</span>')
    sh = "text-shadow:0 8px 0 rgba(0,0,0,.35),0 0 40px rgba(0,0,0,.35);" if shadow else ""
    if align == "center":
        pos = f"left:{x - W:.0f}px;width:{2 * W:.0f}px;"      # centred on x, full room
    elif align == "right":
        pos = f"right:{W - x:.0f}px;" + (f"width:{width:.0f}px;" if width else "")
    else:
        pos = f"left:{x:.0f}px;" + (f"width:{width:.0f}px;" if width else "")
    return (f'<div class="abs d" style="{pos}top:{y:.0f}px;font-size:{size:.0f}px;'
            f'line-height:{lh};color:{color};text-align:{align};{sh}">{"".join(parts)}</div>')


def label(text: str, x: float, y: float, size: float, start: float, color: str = "#fff",
          weight: int = 700, anim: str = "rise", align: str = "left", bg: str = "",
          pad: str = "", rot: float = 0, spacing: str = "0", width: float = 0) -> str:
    a = style_anim(an(anim, start, .45))
    box = f"background:{bg};padding:{pad};border-radius:14px;" if bg else ""
    if align == "center":
        pos = f"left:{x - W:.0f}px;width:{2 * W:.0f}px;"
    elif align == "right":
        pos = f"right:{W - x:.0f}px;" + (f"width:{width:.0f}px;" if width else "")
    else:
        pos = f"left:{x:.0f}px;" + (f"width:{width:.0f}px;" if width else "")
    return (f'<div class="abs" style="{pos}top:{y:.0f}px;transform:rotate({rot}deg);'
            f'text-align:{align}"><div style="display:inline-block;font-size:{size:.0f}px;font-weight:{weight};'
            f'color:{color};letter-spacing:{spacing};white-space:{"normal" if width else "nowrap"};{box}{a}">{esc(text)}</div></div>')


def sticker(text: str, x: float, y: float, size: float, start: float, bg: str = ACCENT,
            fg: str = INK, rot: float = -6, anim: str = "pop") -> str:
    """A slightly crooked, hand-placed label. Imperfection reads as made-by-a-person."""
    a = style_anim(an(anim, start, .55, EASE_BACK))
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;transform:rotate({rot}deg)">'
            f'<div class="d" style="background:{bg};color:{fg};font-size:{size:.0f}px;padding:.16em .42em .1em;'
            f'border-radius:10px;box-shadow:0 10px 0 rgba(0,0,0,.35);{a}">{esc(text)}</div></div>')


def price_roll(value: int, x: float, y: float, size: float, start: float, dur: float = 1.1,
               color: str = ACCENT, align: str = "left", suffix: str = "V-BUCKS") -> str:
    """A price that rolls up from 0 like a counter, then settles on the exact,
    comma-formatted value."""
    comp_name = f"roll{value}_{int(start*1000)}"
    a_roll = style_anim(an(comp_name, start, dur, "cubic-bezier(.1,.7,.2,1)"),
                        an("fadeout", start + dur, .05))
    a_fin = style_anim(an("fadein", start + dur, .05), an("pulse", start + dur, .35))
    tf = f"left:{x - W:.0f}px;width:{2 * W:.0f}px;text-align:center;" if align == "center" else f"left:{x:.0f}px;"
    sfx = f'<span style="font-size:.38em;color:#fff;opacity:.8;margin-left:.2em">{esc(suffix)}</span>' if suffix else ""
    return (f'<style>@keyframes {comp_name}{{from{{--n:0}}to{{--n:{int(value)}}}}}</style>'
            f'<div class="abs d" style="{tf}top:{y:.0f}px;font-size:{size:.0f}px;color:{color};'
            f'text-shadow:0 8px 0 rgba(0,0,0,.35)">'
            f'<span class="count" style="position:absolute;white-space:nowrap;'
            f'{"left:50%;transform:translateX(-50%);" if align == "center" else ""}{a_roll}"></span>'
            f'<span style="white-space:nowrap;{a_fin}">{int(value):,}{sfx}</span></div>')


def countdown(seconds: int, cx: float, cy: float, size: float, start: float, text: str = "") -> str:
    """A ring that actually drains, with the number ticking down each second."""
    name = f"tick{int(start*1000)}"
    ring = style_anim(an("fadein", start, .2), an("drain", start, seconds, "linear"))
    num = style_anim(an(name, start, seconds, f"steps({seconds},end)"))
    cap = (f'<div class="d" style="position:absolute;top:{size+16:.0f}px;left:50%;transform:translateX(-50%);'
           f'white-space:nowrap;font-size:{size*.26:.0f}px;color:#fff;background:rgba(10,10,11,.82);'
           f'padding:.12em .45em .06em;border-radius:12px;{ring}">{esc(text)}</div>') if text else ""
    return (f'<style>@keyframes {name}{{from{{--n:{seconds}}}to{{--n:0}}}}</style>'
            f'<div class="abs" style="left:{cx-size/2:.0f}px;top:{cy-size/2:.0f}px;width:{size:.0f}px;height:{size:.0f}px">'
            f'<div class="ring" style="position:absolute;inset:0;{ring}"></div>'
            f'<div style="position:absolute;inset:{size*.09:.0f}px;border-radius:50%;background:{INK};'
            f'display:flex;align-items:center;justify-content:center">'
            f'<span class="d count" style="font-size:{size*.52:.0f}px;color:{ACCENT};{num}"></span></div>'
            f"{cap}</div>")


def burst(cx: float, cy: float, start: float, seed: int, n: int = 26,
          colors: tuple = (ACCENT, "#ffffff", "#5BC44A", "#4A9FF5", "#EE8B3D")) -> str:
    """Confetti on a reveal. Deterministic: same seed, same burst."""
    import math
    out = []
    for i in range(n):
        ang = (i / n) * 2 * math.pi + (seed % 7) * .13
        dist = 260 + ((seed * 31 + i * 57) % 280)
        dx, dy = math.cos(ang) * dist, math.sin(ang) * dist - 120
        rot = ((seed + i * 43) % 720) - 360
        sz = 14 + ((seed + i * 13) % 18)
        col = colors[(i + seed) % len(colors)]
        shape = "50%" if i % 3 == 0 else "4px"
        a = style_anim(an("burst", start, 1.1 + (i % 5) * .08, "cubic-bezier(.15,.7,.3,1)"))
        out.append(f'<i class="abs" style="left:{cx:.0f}px;top:{cy:.0f}px;width:{sz}px;height:{sz*1.4:.0f}px;'
                   f'background:{col};border-radius:{shape};--dx:{dx:.0f}px;--dy:{dy:.0f}px;--r:{rot}deg;'
                   f'opacity:0;{a}"></i>')
    return "".join(out)


def code_badge(start: float = 0) -> str:
    # On screen and at rest from frame 0 whatever `start` says: the code is the
    # whole point. The hook scene (cc_formats._hook_scene) overrides this through
    # the .codebadge class: while its big CREATOR CODE stamp is on screen, this
    # corner badge waits, then appears as the stamp shrinks into its spot.
    # USE CODE: BAD on the channel's lime, big enough to read at a glance (the
    # owner asked for the code to be noticeable in every video), and kept in the
    # band above the scenes' kicker lines (y 190-280).
    a = style_anim(an("thump", .2, .4))
    return (f'<div class="abs codebadge" style="left:48px;top:{SAFE_TOP}px;z-index:50;{a}">'
            f'<div style="display:flex;align-items:center;gap:12px;background:{ACCENT};color:{INK};'
            f'border-radius:16px;padding:8px 20px 6px 18px;box-shadow:0 8px 0 rgba(0,0,0,.38)">'
            f'<div style="font-size:23px;font-weight:900;line-height:1.02;letter-spacing:.12em">USE<br>CODE:</div>'
            f'<div class="d" style="font-size:80px;line-height:.9;letter-spacing:.02em">BAD</div></div></div>')


BADGE_W, BADGE_H = 258, 86          # code_badge's size, measured in the render browser


def disclosure() -> str:
    """Under the code badge: always on screen, never under TikTok's caption."""
    return (f'<div class="abs" style="left:52px;top:{SAFE_TOP + BADGE_H + 4}px;z-index:50;'
            f'font-size:23px;font-weight:700;line-height:1.3;color:rgba(255,255,255,.9);'
            f'text-shadow:0 2px 6px rgba(0,0,0,.9)">#EpicPartner</div>')


def progress(start: float, end: float, index: int, total: int) -> str:
    """ROUND 2/5 pips. Knowing how much is left keeps people watching."""
    pips = "".join(
        f'<i style="display:inline-block;width:46px;height:10px;border-radius:6px;margin:0 5px;'
        f'background:{ACCENT if j <= index else "rgba(255,255,255,.25)"}"></i>' for j in range(1, total + 1))
    return (f'<div class="abs" style="right:{W-SAFE_RIGHT}px;top:{SAFE_TOP+14}px;text-align:right;z-index:40">'
            f'<div style="font-size:20px;font-weight:800;letter-spacing:.22em;color:#fff;margin-bottom:10px">'
            f"ROUND {index}/{total}</div>{pips}</div>")


# ------------------------------------------------------------------- render

SEEK_JS = """(t) => { for (const a of document.getAnimations()) { a.pause(); a.currentTime = t; } }"""
# After a big jump (the first frame, or a QA still), give the compositor two
# frames to commit the new state; otherwise the capture can show the page as it
# was before the seek. Sequential frames don't need this, so render() only
# uses it where it matters.
SETTLE_JS = """async (t) => {
  for (const a of document.getAnimations()) { a.pause(); a.currentTime = t; }
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
}"""
# Chromium's first capture after load or after a big jump can show a stale frame:
# unpainted tiles (black), or the page as it looked a second or two into playback.
# Two guards: every animation is created paused (BASE_CSS), so real time never
# moves the page; and the captures that matter most -- frame 0, which is the
# thumbnail, and QA stills -- go through stable_shot(), which re-captures until
# two in a row agree. Under parallel load 1 in 4 first frames were stale before;
# 0 in 8 after.
CHROME_ARGS = ["--no-sandbox", "--font-render-hinting=none", "--force-color-profile=srgb",
               "--hide-scrollbars", "--run-all-compositor-stages-before-draw",
               "--disable-checker-imaging", "--disable-new-content-rendering-timeout"]

READY_JS = """async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map(i => i.decode ? i.decode().catch(() => {}) : null));
  if (window.__ready) { await window.__ready; }
}"""


def stable_shot(page, t_ms: float, kind: str = "jpeg", tries: int = 8) -> bytes:
    """Seek to t_ms and screenshot until two captures in a row are identical.

    The first capture after a big jump can show a frame the compositor drew
    earlier (seen on the build machine under load: frame 0 showing the page a
    second or two in). Asking again until the picture stops changing makes the
    frame we keep the frame that is actually on screen at t_ms."""
    opts = {"type": kind}
    if kind == "jpeg":
        opts["quality"] = 90
    page.evaluate(SETTLE_JS, t_ms)
    prev = page.screenshot(**opts)
    for _ in range(tries):
        page.evaluate(SETTLE_JS, t_ms)
        cur = page.screenshot(**opts)
        if cur == prev:
            return cur
        prev = cur
    return prev


def find_ffmpeg() -> str:
    for c in ("ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg"):
        p = shutil.which(c)
        if p:
            return p
    return ""


def render(comp: Comp, out: Path, audio: Path | None = None, preview: bool = False,
           stills: tuple = (), stills_dir: Path | None = None, fps: int = FPS) -> Path:
    """Render a composition to video.

    preview=True encodes VP8/WebM, which works on minimal ffmpeg builds, for
    checking locally. Otherwise H.264/AAC MP4 for publishing. `stills` are
    timestamps to also save as PNGs for visual QA."""
    from playwright.sync_api import sync_playwright

    ff = find_ffmpeg() or "/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux"
    n = int(round(comp.duration * fps))
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = comp.document()

    cmd = [ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-"]
    if preview:
        cmd += ["-c:v", "libvpx", "-b:v", "5M", "-pix_fmt", "yuv420p", str(out)]
    else:
        if audio and audio.exists():
            cmd += ["-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k"]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "128k"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                "-r", str(fps), "-t", f"{comp.duration:.3f}", "-movflags", "+faststart", str(out)]

    stills = sorted(set(round(s, 3) for s in stills))
    if stills and stills_dir:
        stills_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=CHROME_ARGS)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_content(doc, wait_until="load")
        page.evaluate(READY_JS)
        first = stable_shot(page, 0)                     # frame 0 is the thumbnail: be sure of it
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for i in range(n):
                t = i / fps
                if i == 0:
                    proc.stdin.write(first)
                    continue
                page.evaluate(SEEK_JS, t * 1000)
                proc.stdin.write(page.screenshot(type="jpeg", quality=90))
                if i % (fps * 10) == 0:
                    log(f"  frame {i}/{n} ({t:.0f}s)")
            for s in stills:
                (stills_dir / f"t{s:06.2f}.png").write_bytes(stable_shot(page, s * 1000, "png"))
        finally:
            proc.stdin.close()
            code = proc.wait()
            browser.close()
    if code != 0:
        raise RuntimeError(f"ffmpeg exited {code}")
    return out


def snapshot(comp: Comp, times: list, out_dir: Path) -> list:
    """Just the stills, no video -- fast visual QA."""
    from playwright.sync_api import sync_playwright
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=CHROME_ARGS)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_content(comp.document(), wait_until="load")
        page.evaluate(READY_JS)
        page.screenshot(type="jpeg")                     # first paint, discarded
        for t in times:
            path = out_dir / f"t{t:06.2f}.png"
            path.write_bytes(stable_shot(page, t * 1000, "png"))
            paths.append(path)
        browser.close()
    return paths
