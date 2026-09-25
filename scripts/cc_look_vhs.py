"""
VHS -- the Fortnitemares throwbacks as a camcorder tape someone found in a drawer.

    0:00  hook      the cassette on a dark desk: a marker label with the event and
                    its years ("FORTNITEMARES '17-'18"), DON'T TAPE OVER!, the day of
                    the series, a big lime USE CODE: BAD sticker, and instant photos
                    of the first two skins. It lifts off the desk into the player...
    0:01  play      ...a blue screen: PLAY, the episode's title and "how many do you
                    remember?". The tape rolls into the first recording.
    0:03  skins     one recording per skin (6.5 s): the skin standing in a foggy,
                    moonlit field, burned-in captions (its event year, name, rarity
                    and type, when it first hit the shop) and a camcorder date stamp,
                    with tape jitter and a tracking band. Between skins the tape
                    cuts, or fast-forwards.
    end   outro     the tape rewinds through every skin and stops on the player's
                    blue menu: which one did you own?

The player's own lettering (PLAY, the lime USE CODE: BAD line, #EpicPartner) sits
crisp on top of the picture from the first blue frame to the last; before that the
code is the big sticker on the cassette.

The footage is put together once, before the first frame, in the page: the field
(a committed texture), the skin lit by the moon, the fog and corn in front of it,
then the tape's smear (soft picture, colour bleeding sideways, a red/blue fringe).
While the video runs, only cheap things move: the picture (transforms), noise
layers made at load that jump about, and hard cuts.

Facts on screen are the classic format's: each skin's name, rarity and type, its
Fortnitemares year, and when it first hit the shop -- a date only from 2018 on;
for anything first seen before that, only the year. The date stamp shows that
same date (or year) and nothing else.
"""

import json
import random

from cc_looks import KIT_CSS, LIME, PREP_JS, pad_to, rough_ellipse, rough_line, tex
from cc_motion import W, H, Comp, esc

HOOK = 3.0
R = 6.5
FPS = 30
FONTS = ("VT323", "Permanent Marker", "Kalam")

# The hook: the cassette lifts at T_LIFT, the player's blue screen cuts in at
# T_CUT, and the tape rolls into the first recording at T_ROLL.
T_LIFT, T_CUT, T_ROLL = .9, 1.3, 2.7

# The footage is 1160x2000: the frame plus 40 px all round for the camera to
# drift in. The skin's feet stand at FEET (frame coordinates).
PW, PH, M = 1160, 2000, 40
FEET, FIG_H, FIG_W = 1470, 900, 860

OSD = "#f2f2ee"
CREAM = "#f4eedb"
BLUE_BG = "radial-gradient(ellipse 80% 60% at 50% 45%,#2b40c9,#1c2ca6 70%,#15208b)"

CSS = """
.osd{position:absolute;font-family:'VT323',monospace;color:#f2f2ee;line-height:1;white-space:nowrap;
  letter-spacing:.02em;text-shadow:3px 3px 0 rgba(0,0,0,.85)}
.codeline{color:@LIME@;letter-spacing:.01em;text-shadow:5px 5px 0 rgba(0,0,0,.9)}
.cam{position:absolute;font-family:'VT323',monospace;color:#f4eedb;white-space:nowrap;letter-spacing:.03em;
  line-height:1;text-shadow:-3px 0 rgba(255,60,50,.5),3px 0 rgba(40,220,255,.4),2px 2px 0 rgba(0,0,0,.6),
  0 0 8px rgba(255,250,230,.2);filter:blur(.5px)}
.mk{font-family:'Permanent Marker',cursive;color:#171615;white-space:nowrap;line-height:1}
.kl{font-family:'Kalam',cursive;white-space:nowrap;line-height:1}
.lay{will-change:transform}
.plate{position:absolute;left:-40px;top:-40px;width:1160px;height:2000px;display:block}
.scan{position:absolute;inset:0;background:repeating-linear-gradient(to bottom,rgba(0,0,0,0) 0px,
  rgba(0,0,0,.24) 3px,rgba(0,0,0,0) 6px)}
.tvig{position:absolute;inset:0;background:radial-gradient(ellipse 88% 72% at 50% 48%,rgba(0,0,0,0) 58%,
  rgba(0,0,0,.5) 100%)}
.ribs{border-radius:8px;background:repeating-linear-gradient(to right,rgba(255,255,255,.05) 0 3px,
  rgba(0,0,0,.35) 3px 7px);box-shadow:inset 0 2px 4px rgba(0,0,0,.7)}
.cass3d{transform-style:preserve-3d}
.face{border-radius:16px;overflow:hidden}
.edge{transform-origin:50% 0;transform:rotateX(-90deg);border-radius:0 0 10px 10px}
.cshadow{background:rgba(0,0,0,.9);border-radius:24px;filter:blur(22px)}
@keyframes vhpush{from{transform:scale(1)}to{transform:scale(1.045)}}
@keyframes vhlift{from{transform:translate3d(0,0,0) rotateX(0deg) rotateZ(0deg)}
  to{transform:translate3d(-30px,-300px,430px) rotateX(-14deg) rotateZ(3deg)}}
@keyframes vhjit{0%{transform:translate(0,0)}7%{transform:translate(2px,0)}13%{transform:translate(-1px,1px)}
  21%{transform:translate(1px,0)}29%{transform:translate(-2px,0)}36%{transform:translate(0,-1px)}
  44%{transform:translate(3px,0)}51%{transform:translate(-1px,0)}58%{transform:translate(1px,1px)}
  66%{transform:translate(-3px,0)}74%{transform:translate(0,0)}81%{transform:translate(2px,-1px)}
  88%{transform:translate(-1px,0)}94%{transform:translate(1px,2px)}100%{transform:translate(0,0)}}
@keyframes vhroll{0%{transform:translateY(40%);filter:saturate(0) brightness(1.2)}
  16%{transform:translateY(24%) skewX(-2deg);filter:saturate(.2) brightness(1.1)}
  32%{transform:translate(14px,10%);filter:saturate(.5)}48%{transform:translateY(3%)}
  64%{transform:translate(-6px,-1%)}80%{transform:translate(3px,0);filter:none}100%{transform:none;filter:none}}
@keyframes vhglitch{0%{transform:translateX(-28px) skewX(-4deg);filter:brightness(1.25) saturate(.2)}
  18%{transform:translate(22px,-4%);filter:brightness(.85) contrast(1.4)}
  36%{transform:translate(-8px,-15%) skewX(3deg);filter:saturate(0) brightness(1.1)}
  54%{transform:translate(0,-30%);filter:saturate(0) brightness(.7)}
  72%,100%{transform:translate(0,-46%);filter:brightness(.4)}}
@keyframes vhflick{0%{opacity:0}20%{opacity:.025}40%{opacity:.01}60%{opacity:.035}80%{opacity:.012}100%{opacity:0}}
@keyframes vhexp{from{opacity:.42}to{opacity:0}}
@keyframes vhrew{0%{transform:translate(-18px,0) scaleY(1.02)}25%{transform:translate(14px,-2%) skewX(-3deg)}
  50%{transform:translate(-6px,1%) skewX(2deg)}75%{transform:translate(20px,-1%)}100%{transform:translate(-12px,0)}}
"""


# ------------------------------------------------------------------ timing helpers

def _snap(t: float) -> float:
    """Half a frame before the frame nearest t, so a hard cut never lands on a
    frame's own time (where rounding could put it either side)."""
    return max(0.0, round(t * FPS) / FPS - .5 / FPS)


def _a(name: str, t: float, dur: float, ease: str = "linear", it: str = "1", fill: str = "both") -> str:
    return f"{name} {dur:.3f}s {ease} {t:.3f}s {it} normal {fill}"


def _minus(span: tuple, holes: list) -> list:
    """The parts of the window `span` not covered by any of `holes`."""
    out, (a, b) = [], span
    for h0, h1 in sorted(holes):
        if h1 <= a or h0 >= b:
            continue
        if h0 > a:
            out.append((a, h0))
        a = max(a, h1)
    if a < b:
        out.append((a, b))
    return out


def _style(*entries: str) -> str:
    entries = [e for e in entries if e]
    return f"animation:{','.join(entries)};" if entries else ""


class _Tracks:
    """Hard-cut visibility and stepped levels as one keyframe track each, over
    the whole video (like Comp.scene, but with no fades and many windows)."""

    def __init__(self, comp: Comp):
        self.comp = comp

    def levels(self, pts: list, before: float = 0.0) -> str:
        """[(t, opacity), ...]: the opacity jumps to each level at its time."""
        d = self.comp.duration
        name = self.comp.uid("vk")
        ks = {0.0: before}
        for t, v in sorted(pts):
            ks[round(min(max(_snap(t), 0.0), d) / d * 100, 4)] = v
        frames = [f"{0 if k == 0 else k:.4f}%{{opacity:{v}}}" for k, v in sorted(ks.items())]
        last = ks[max(ks)]
        frames.append(f"100%{{opacity:{last}}}")
        self.comp.css(f"@keyframes {name}{{{''.join(frames)}}}")
        return f"{name} {d:.3f}s steps(1,end) 0s 1 normal both"

    def vis(self, windows: list) -> str:
        pts = []
        for a, b in windows:
            pts += [(a, 1), (b, 0)]
        # A window that starts at 0 is visible on frame 0.
        before = 1 if any(a <= 0 for a, _ in windows) else 0
        return self.levels([(t, v) for t, v in pts if not (t <= 0 and v == 1)], before)


# ------------------------------------------------------------------ facts, as the tape shows them

def _yy(y) -> str:
    return f"'{str(y)[-2:]}"


def _label_title(group: list, theme: dict) -> str:
    """"FORTNITEMARES '18", "FORTNITEMARES '17–'18": the years of the skins on
    this tape, or the episode's title when they don't say."""
    years = sorted({int(it["fm_year"]) for it in group if str(it.get("fm_year") or "").isdigit()})
    if years:
        span = _yy(years[0]) if len(years) == 1 else f"{_yy(years[0])}–{_yy(years[-1])}"
        return f"FORTNITEMARES {span}"
    return (theme.get("title") or "FORTNITEMARES").upper()


def _stamp(it: dict, theme: dict) -> str:
    """The camcorder date stamp: the day it first hit the shop ('OCT. 7 2018'),
    or only the year when the records can't be sure of the day."""
    when = (theme["when"](it) if theme and theme.get("when") else "") or ""
    parts = when.replace(",", "").split()
    if len(parts) == 3 and parts[2].isdigit():             # "OCT 7, 2018"
        return f"{parts[0].upper()}. {parts[1]} {parts[2]}"
    return when.strip().upper()                            # "2017" (or whatever the rule says)


def _kind(it: dict) -> str:
    kind = f"{it['rarity_label']} {it['type']}".strip() if it.get("rarity_label") else (it.get("type") or "")
    return kind.upper()


def _era(it: dict, theme: dict) -> str:
    try:
        return (theme["era"](it) or "").upper()
    except (KeyError, TypeError):
        return ""


def _is_figure(it: dict) -> bool:
    """Outfits stand in the field; anything else (a pickaxe, an emote) hangs in the fog."""
    return (it.get("type") or "Outfit").lower() in ("outfit", "")


# ------------------------------------------------------------------ the desk and the cassette

CW, CH, CT = 960, 530, 128             # cassette face, and its thickness
PHOTO_S = 420                          # an instant photo's picture
DESK_Y = 1085                          # where the cassette's centre lies on the desk (before perspective)
PHOTOS = [(-560, -1120, -7), (-40, -1150, 6)]     # the two photos, on the desk (x, y, rotation)


def _hand(text: str, seed: int, rot: float = 3.2, dy: float = 2.2, sc: float = .04) -> str:
    """Per-letter jitter so marker lettering doesn't repeat identical glyphs like a font does."""
    rnd = random.Random(seed)
    out = []
    for ch in text:
        if ch == " ":
            out.append(" ")
            continue
        out.append(f'<span style="display:inline-block;transform:translateY({rnd.uniform(-dy, dy):.1f}px) '
                   f'rotate({rnd.uniform(-rot, rot):.1f}deg) scale({1 + rnd.uniform(-sc, sc):.3f})">{esc(ch)}</span>')
    return "".join(out)


def _reel(cx: int, cy: int, pack_r: int, win_r: int = 84) -> str:
    """A reel window: smoked plastic, the tape pack, a white hub with six teeth."""
    teeth = "".join(f'<rect x="-4" y="-27" width="8" height="12" rx="1.5" fill="#1b1b1b" '
                    f'transform="rotate({k * 60})"/>' for k in range(6))
    rings = "".join(f'<circle r="{r}" fill="none" stroke="#000" stroke-opacity=".25" stroke-width="1"/>'
                    for r in range(40, pack_r, 5))
    return (f'<div class="abs" style="left:{cx - win_r}px;top:{cy - win_r}px;width:{win_r * 2}px;'
            f'height:{win_r * 2}px;border-radius:50%;background:#070707;box-shadow:inset 0 4px 10px rgba(0,0,0,.9),'
            f'0 1px 0 rgba(255,255,255,.07),0 -1px 0 rgba(0,0,0,.6);overflow:hidden">'
            f'<svg width="{win_r * 2}" height="{win_r * 2}" viewBox="{-win_r} {-win_r} {win_r * 2} {win_r * 2}" '
            f'style="display:block"><defs><radialGradient id="pk{cx}" cx="45%" cy="40%" r="60%">'
            f'<stop offset="0" stop-color="#3a2d24"/><stop offset=".7" stop-color="#241b16"/>'
            f'<stop offset="1" stop-color="#140f0c"/></radialGradient></defs>'
            f'<circle r="{pack_r}" fill="url(#pk{cx})"/>{rings}'
            f'<circle r="37" fill="#d9d6cf"/><circle r="37" fill="none" stroke="#9c988f" stroke-width="2"/>'
            f'<circle r="29" fill="#bdb9b0"/>{teeth}<circle r="14" fill="#1b1b1b"/></svg>'
            f'<div class="abs" style="inset:0;border-radius:50%;background:linear-gradient(135deg,'
            f'rgba(255,255,255,.16) 0%,rgba(255,255,255,.03) 38%,rgba(255,255,255,0) 50%,rgba(255,255,255,.05) 80%);'
            f'box-shadow:inset 0 0 0 3px rgba(40,40,40,.9)"></div></div>')


def _label(title: str, names: str, day_txt: str, part: str) -> str:
    """The paper label, written on in marker: what's on the tape."""
    paper = tex("paper.jpg")
    ink = tex("vhs-marker.png")
    u1, _ = rough_line(50, 158, 438, 150, seed=5)
    u2, _ = rough_line(62, 170, 420, 164, seed=6)
    ring, _ = rough_ellipse(648, 144, 132, 50, seed=18, overshoot=.12, wobble=.06)
    warn = f"{part} · DON'T TAPE OVER!" if part else "DON'T TAPE OVER!"
    return (f'<div class="abs" style="left:80px;top:30px;width:800px;height:236px;transform:rotate(-1.1deg);'
            f'background:url({paper}) -140px -300px/1080px 1920px;box-shadow:0 1px 2px rgba(0,0,0,.5)">'
            f'<div class="abs" style="inset:0;background:repeating-linear-gradient(to bottom,rgba(0,0,0,0) 0 57px,'
            f'rgba(120,140,170,.22) 57px 59px);background-position:0 10px"></div>'
            f'<div class="abs" style="inset:0;-webkit-mask:url({ink}) 0 0/100% 100%;mask:url({ink}) 0 0/100% 100%">'
            f'<div class="abs mk" data-fit="740" style="left:28px;top:8px;font-size:72px;transform:rotate(-1.6deg);'
            f'transform-origin:0 50%">{_hand(title, 31)}</div>'
            f'<div class="abs kl" data-fit="470" style="left:46px;top:98px;font-size:46px;color:#c1271e;font-weight:700;'
            f'transform:rotate(-2.4deg);transform-origin:0 50%">{_hand(warn, 32, rot=2.5, dy=1.6)}</div>'
            f'<svg class="abs" width="800" height="236" style="left:0;top:0;overflow:visible">'
            f'<g fill="none" stroke="#c1271e" stroke-width="4" stroke-linecap="round" opacity=".92">'
            f'<path d="{u1}"/><path d="{u2}"/></g>'
            f'<g fill="none" stroke="#161616" stroke-width="4" stroke-linecap="round" opacity=".9">'
            f'<path d="{ring}"/></g></svg>'
            f'<div class="abs kl" data-fit="470" style="left:50px;top:180px;font-size:31px;color:#5d5a55;'
            f'transform:rotate(-1deg);transform-origin:0 50%">{esc(names)}</div>'
            f'<div class="abs mk" data-fit="230" style="left:536px;top:122px;width:230px;text-align:center;'
            f'font-size:44px;transform:rotate(-5deg)">{_hand(day_txt, 33, rot=3.5)}</div>'
            f'<div class="abs kl" style="left:606px;top:204px;font-size:22px;color:#5d5a55;'
            f'transform:rotate(-3deg)">#EpicPartner</div></div>'
            f'<div class="abs" style="inset:0;background:linear-gradient(100deg,rgba(0,0,0,.04),rgba(255,255,255,0) 30%,'
            f'rgba(0,0,0,.05) 75%,rgba(0,0,0,.12));pointer-events:none"></div></div>')


def _code_sticker() -> str:
    """The creator code on a fluorescent lime sticker slapped across the cassette."""
    return (f'<div class="abs" id="vhs-code" style="left:317px;top:292px;width:326px;height:216px;'
            f'transform:rotate(4deg);background:{LIME};border-radius:7px;box-shadow:0 1px 1px rgba(0,0,0,.5),'
            f'0 4px 8px rgba(0,0,0,.4);display:flex;flex-direction:column;align-items:center;justify-content:center;'
            f'text-align:center">'
            f'<div class="abs" style="inset:0;border-radius:7px;background:linear-gradient(160deg,'
            f'rgba(255,255,255,.16),rgba(255,255,255,0) 45%,rgba(0,0,0,.07))"></div>'
            f'<div class="mk" style="position:relative;font-size:48px;color:#111">{_hand("USE CODE:", 41, 2.5, 1.5)}</div>'
            f'<div class="mk" style="position:relative;font-size:134px;line-height:.9;color:#111;margin-top:4px">'
            f'{_hand("BAD", 42, 3, 2)}</div></div>')


def _cassette(title: str, names: str, day_txt: str, part: str) -> str:
    pl = tex("vhs-plastic.jpg")
    return (f'<div class="abs cass3d" style="left:{-CW // 2}px;top:{-CH // 2}px;width:{CW}px;height:{CH}px">'
            f'<div class="abs cshadow" style="left:26px;top:40px;width:{CW - 10}px;height:{CH - 10}px;'
            f'transform:translateZ(-{CT}px)"></div>'
            f'<div class="abs face" style="inset:0;background:url({pl}) 0 0/{CW}px 658px">'
            f'<div class="abs" style="left:66px;top:18px;width:{CW - 132}px;height:262px;border-radius:10px;'
            f'box-shadow:inset 0 2px 5px rgba(0,0,0,.85),0 1px 0 rgba(255,255,255,.06)"></div>'
            + _label(title, names, day_txt, part)
            + f'<div class="abs" style="left:150px;top:292px;width:660px;height:196px;border-radius:98px;'
              f'box-shadow:inset 0 3px 8px rgba(0,0,0,.8),0 1px 0 rgba(255,255,255,.05);background:rgba(0,0,0,.18)"></div>'
            + _reel(252, 390, 80) + _reel(708, 390, 44)
            + f'<div class="abs ribs" style="left:18px;top:300px;width:92px;height:190px"></div>'
              f'<div class="abs ribs" style="left:{CW - 110}px;top:300px;width:92px;height:190px"></div>'
              f'<div class="abs" style="inset:0;border-radius:16px;background:linear-gradient(112deg,'
              f'rgba(255,255,255,0) 18%,rgba(255,244,225,.07) 25%,rgba(255,255,255,0) 33%)"></div>'
              f'<div class="abs" style="inset:0;border-radius:16px;background:linear-gradient(168deg,'
              f'rgba(255,255,255,.10) 0%,rgba(255,255,255,.02) 30%,rgba(255,255,255,0) 55%,'
              f'rgba(255,255,255,.035) 78%,rgba(0,0,0,.25) 100%);box-shadow:inset 0 2px 0 rgba(255,255,255,.08),'
              f'inset 0 -3px 0 rgba(0,0,0,.6),inset 2px 0 0 rgba(255,255,255,.04)"></div>'
            + _code_sticker() + '</div>'
            + f'<div class="abs edge" style="left:0;top:{CH}px;width:{CW}px;height:{CT}px;'
              f'background:url({pl}) 0 -530px/{CW}px 658px">'
              f'<div class="abs" style="left:40px;top:22px;width:{CW - 80}px;height:{CT - 44}px;border-radius:6px;'
              f'box-shadow:inset 0 2px 4px rgba(0,0,0,.8)"></div>'
              f'<div class="abs" style="inset:0;background:linear-gradient(to bottom,rgba(255,255,255,.10),'
              f'rgba(0,0,0,.35))"></div></div></div>')


def _photo(k: int, it: dict, x: float, y: float, rot: float, has_art: bool) -> str:
    """An instant photo of a skin, lying on the desk (flash, at night, in the field)."""
    name = it["name"].lower()
    S, P = PHOTO_S, 24
    if has_art:
        pic = f'<img class="vhs-photo" data-p="{k}" style="display:block;width:{S}px;height:{S}px">'
    else:                                                   # it never developed
        pic = (f'<div style="width:{S}px;height:{S}px;background:linear-gradient(160deg,#5b6068,#3e434b 60%,'
               f'#34383f)"></div>')
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{S + 2 * P}px;height:{S + P + 112}px;'
            f'background:#efece4;transform:rotate({rot}deg);box-shadow:0 2px 3px rgba(0,0,0,.45),'
            f'0 14px 26px rgba(0,0,0,.4);padding:{P}px {P}px 0">{pic}'
            f'<div class="abs" style="left:{P}px;top:{P}px;width:{S}px;height:{S}px;box-shadow:inset 0 0 0 1px '
            f'rgba(0,0,0,.25);background:linear-gradient(125deg,rgba(255,255,255,.14),rgba(255,255,255,0) 35%)"></div>'
            f'<div class="abs mk" data-fit="{S - 16}" style="left:{P + 6}px;top:{S + P + 22}px;font-size:48px;'
            f'color:#23201c;transform:rotate(-1.5deg);transform-origin:0 50%">{_hand(name, 50 + k, 2.5, 1.5)}</div>'
            f'<div class="abs" style="inset:0;background:linear-gradient(180deg,rgba(255,255,255,.06),'
            f'rgba(0,0,0,.08));pointer-events:none"></div></div>')


# ------------------------------------------------------------------ the footage

def _caption(it: dict, theme: dict) -> str:
    """Burned into the recording: the event, the name, rarity and type, when it
    first hit the shop; and the camcorder's own date stamp."""
    era = _era(it, theme)
    kind = _kind(it)
    line2 = " · ".join(x for x in (kind, era) if x)
    debut = (theme["debut"](it) if theme and theme.get("debut") else "").upper()
    return (f'<div class="cam" data-fit="880" style="left:78px;top:1142px;font-size:88px">{esc(it["name"].upper())}</div>'
            f'<div class="cam" data-fit="880" style="left:80px;top:1240px;font-size:50px">{esc(line2)}</div>'
            f'<div class="cam" data-fit="880" style="left:80px;top:1294px;font-size:50px">{esc(debut)}</div>'
            f'<div class="cam" style="right:{W - 944}px;top:1366px;font-size:96px;text-align:right">'
            f'{esc(_stamp(it, theme))}</div>')


# How the camera moves in each recording, in turn: a hand-held drift, a slow zoom
# in on the face, holding still, a slow pan.
MOVES = ("drift", "zoom", "hold", "drift", "pan", "zoom", "hold", "drift")


def _move(move: str, rnd: random.Random) -> tuple:
    """(transform-origin, from, to) for one recording's camera."""
    j = lambda a: rnd.uniform(-a, a)
    if move == "zoom":
        s0, s1 = 1.03, rnd.uniform(1.2, 1.24)
        return "580px 760px", (s0, j(6), j(6), j(.2)), (s1, j(8), j(8), j(.25))
    if move == "pan":
        d = 1 if rnd.random() < .5 else -1
        return "580px 1000px", (1.1, 34 * d, j(6), j(.2)), (1.11, -34 * d, j(6), j(.2))
    if move == "hold":
        s0 = rnd.uniform(1.05, 1.07)
        return "580px 1000px", (s0, j(4), j(4), j(.1)), (s0 + .006, j(4), j(4), j(.1))
    s0 = rnd.uniform(1.035, 1.06)
    return "580px 1000px", (s0, j(14), j(14), j(.3)), (s0 + rnd.uniform(.025, .06), j(14), j(14), j(.3))


def _clip(comp: Comp, tr: _Tracks, k: int, it: dict, theme: dict, t0: float, t_in: float, rin: str, gout: str,
          band_t: float, rnd: random.Random) -> str:
    """One recording: the plate, filmed hand-held (drifting, zooming, panning or
    holding still), a tracking band rolling through once, the burned-in captions,
    and the tape's jitter."""
    hand = comp.uid("vh")
    move = MOVES[k % len(MOVES)] if _is_figure(it) else ("drift", "hold")[k % 2]
    origin, (s0, tx0, ty0, r0), (s1, tx1, ty1, r1) = _move(move, rnd)
    comp.css(f"@keyframes {hand}{{from{{transform:scale({s0:.3f}) translate({tx0:.1f}px,{ty0:.1f}px) rotate({r0:.2f}deg)}}"
             f"to{{transform:scale({s1:.3f}) translate({tx1:.1f}px,{ty1:.1f}px) rotate({r1:.2f}deg)}}}}")
    band = comp.uid("vb")
    up = rnd.random() < .5
    y_a, y_b = (1950, -200) if up else (-200, 1950)
    comp.css(f"@keyframes {band}{{from{{transform:translateY({y_a}px)}}to{{transform:translateY({y_b}px)}}}}"
             f"@keyframes {band}i{{from{{transform:translate(24px,{-y_a}px)}}to{{transform:translate(24px,{-y_b}px)}}}}")
    bdur = rnd.uniform(1.5, 2.1)
    bvis = tr.vis([(band_t, band_t + bdur)])
    pic = (f'<div class="full lay" style="transform-origin:{origin};{_style(_a(hand, t0 - .3, R + .6, "cubic-bezier(.45,.05,.55,.95)"))}">'
           f'<img class="plate vhs-plate" data-p="{k}">'
           f'<div class="abs lay" style="left:0;top:0;width:{W}px;height:150px;overflow:hidden;'
           f'{_style(_a(band, band_t, bdur), bvis)}">'
           f'<div class="abs" style="left:0;top:0;{_style(_a(band + "i", band_t, bdur))}">'
           f'<img class="plate vhs-plate" data-p="{k}" style="filter:brightness(1.12)"></div>'
           f'<canvas class="abs vhs-noise" data-kind="band" width="{W}" height="150" '
           f'style="left:0;top:0;width:{W}px;height:150px"></canvas></div></div>')
    expo = f'<div class="full" style="background:#000;{_style(_a("vhexp", t_in - .05, .6, "ease-out"))}"></div>'
    return (f'<div class="full" style="overflow:hidden;background:#000">'
            f'<div class="full lay" style="{_style(rin, gout)}">'
            f'<div class="full lay" style="{_style(_a("vhjit", 0, 1.37, "steps(1,end)", "infinite"))}">'
            f'{pic}{_caption(it, theme)}{expo}</div></div></div>')


def _search_bars(comp: Comp, tr: _Tracks, windows: list, rnd: random.Random, up: bool, count: int = 2) -> str:
    """The noise bars of a tape being searched (FF or REW): bands of snow that
    drift through the picture, their noise changing every frame."""
    if not windows:
        return ""
    out = []
    for _ in range(count):
        h = rnd.randint(96, 150)
        y0 = rnd.randint(260, 1400)
        mv, jit = comp.uid("vsb"), comp.uid("vsj")
        a, b = (y0 + 380, y0 - 380) if up else (y0 - 380, y0 + 380)
        comp.css(f"@keyframes {mv}{{from{{transform:translateY({a}px)}}to{{transform:translateY({b}px)}}}}")
        offs = [(rnd.randint(-90, 90), rnd.randint(-36, 0)) for _ in range(8)]
        comp.css(f"@keyframes {jit}{{" + "".join(f"{i * 12.5:.2f}%{{transform:translate({x}px,{y}px)}}"
                                                  for i, (x, y) in enumerate(offs)) + "}")
        out.append(f'<div class="abs lay" style="left:0;top:0;width:{W}px;height:{h}px;overflow:hidden;'
                   f'-webkit-mask:linear-gradient(to bottom,transparent,#000 30%,#000 70%,transparent);'
                   f'mask:linear-gradient(to bottom,transparent,#000 30%,#000 70%,transparent);'
                   f'{_style(_a(mv, windows[0][0], rnd.uniform(.7, 1.1), "linear", "infinite"), tr.vis(windows))}">'
                   f'<div class="abs lay" style="left:-100px;top:-36px;width:1280px;height:{h + 72}px;'
                   f'{_style(_a(jit, -.5 / FPS, 8 / FPS, "steps(1,end)", "infinite"))}">'
                   f'<canvas class="vhs-noise" data-kind="snow" width="427" height="{(h + 72) // 2}" '
                   f'style="display:block;width:1280px;height:{h + 72}px"></canvas></div></div>')
    return "".join(out)


# ------------------------------------------------------------------ in-page footage and noise

VHS_FILTER_JS = r"""
<script>(() => {
const CFG = __CFG__;
const prev = window.__ready;
window.__ready = (async () => {
  try { await prev; } catch (e) {}
  try { await vhsPrep(); } catch (e) { console.error('vhs prep', e); }
})();

function rng(seed) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
const cv = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
async function ready(img) {
  if (!img) return null;
  if (!img.complete) await new Promise(r => { img.onload = r; img.onerror = r; });
  try { await img.decode(); } catch (e) {}
  return img.naturalWidth ? img : null;
}
function blob(c) {
  return new Promise(r => c.toBlob(b => r(URL.createObjectURL(b)), 'image/jpeg', .93));
}
// A grey mask (texture) as a flat colour whose alpha is the grey.
function tint(img, rgb, k) {
  const c = cv(img.naturalWidth, img.naturalHeight), g = c.getContext('2d');
  g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, c.width, c.height), p = d.data;
  for (let i = 0; i < p.length; i += 4) {
    const a = p[i] * k; p[i] = rgb[0]; p[i + 1] = rgb[1]; p[i + 2] = rgb[2]; p[i + 3] = a > 255 ? 255 : a;
  }
  g.putImageData(d, 0, 0);
  return c;
}
// The skin as the moon lights it: darker, washed out, brighter on the moon's side
// with a thin rim of light there, darker towards the ground.
function moonlit(art, w, h, side) {
  const c = cv(w, h), g = c.getContext('2d');
  g.imageSmoothingQuality = 'high';
  g.filter = 'saturate(.62) brightness(.74) contrast(1.02)';
  g.drawImage(art, 0, 0, w, h);
  g.filter = 'none';
  g.globalCompositeOperation = 'source-atop';
  let gr = g.createLinearGradient(side > 0 ? w : 0, 0, side > 0 ? 0 : w, 0);
  gr.addColorStop(0, 'rgba(255,244,222,.06)'); gr.addColorStop(.45, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(4,5,9,.5)');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  gr = g.createLinearGradient(0, 0, 0, h);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(.5, 'rgba(0,0,0,.08)'); gr.addColorStop(1, 'rgba(6,6,6,.6)');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  g.globalCompositeOperation = 'multiply'; g.fillStyle = 'rgb(255,238,205)'; g.fillRect(0, 0, w, h);
  g.globalCompositeOperation = 'destination-in'; g.drawImage(art, 0, 0, w, h);
  const s = cv(w, h), sg = s.getContext('2d');
  sg.drawImage(art, 0, 0, w, h);
  sg.globalCompositeOperation = 'source-in'; sg.fillStyle = 'rgb(236,229,212)'; sg.fillRect(0, 0, w, h);
  sg.globalCompositeOperation = 'destination-out'; sg.drawImage(art, -5 * side, 0, w, h);
  sg.globalCompositeOperation = 'destination-in';
  gr = sg.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#000'); gr.addColorStop(.3, 'rgba(0,0,0,.8)');
  gr.addColorStop(1, 'rgba(0,0,0,0)');
  sg.fillStyle = gr; sg.fillRect(0, 0, w, h);
  g.globalCompositeOperation = 'lighter'; g.globalAlpha = .26; g.filter = 'blur(1.2px)'; g.drawImage(s, 0, 0);
  g.filter = 'none'; g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  return c;
}
// Box blur passes along rows / columns, in place.
function boxH(a, w, h, r, passes) {
  const t = new Float32Array(w), n = 2 * r + 1;
  for (let q = 0; q < passes; q++) for (let y = 0; y < h; y++) {
    const o = y * w; let s = 0;
    for (let x = -r; x <= r; x++) s += a[o + (x < 0 ? 0 : x >= w ? w - 1 : x)];
    for (let x = 0; x < w; x++) {
      t[x] = s / n;
      const xa = x + r + 1, xb = x - r;
      s += a[o + (xa >= w ? w - 1 : xa)] - a[o + (xb < 0 ? 0 : xb)];
    }
    a.set(t, o);
  }
}
function boxV(a, w, h, passes) {                     // radius 1
  const t = new Float32Array(w * h);
  for (let q = 0; q < passes; q++) {
    for (let y = 0; y < h; y++) {
      const o = y * w, u = (y > 0 ? y - 1 : 0) * w, d = (y < h - 1 ? y + 1 : h - 1) * w;
      for (let x = 0; x < w; x++) t[o + x] = (a[u + x] + a[o + x] + a[d + x]) / 3;
    }
    a.set(t);
  }
}
// The tape: a soft picture with ringing edges, colour that bleeds sideways and
// lags behind the picture, a red/blue fringe and a little grain.
function tape(src, seed) {
  const w = src.width, h = src.height, N = w * h, rand = rng(seed);
  const g = src.getContext('2d'), img = g.getImageData(0, 0, w, h), p = img.data;
  const Y = new Float32Array(N), U = new Float32Array(N), V = new Float32Array(N);
  for (let i = 0, j = 0; i < N; i++, j += 4) {
    const r = p[j], gg = p[j + 1], b = p[j + 2];
    Y[i] = .299 * r + .587 * gg + .114 * b;
    U[i] = -.168736 * r - .331264 * gg + .5 * b;
    V[i] = .5 * r - .418688 * gg - .081312 * b;
  }
  boxH(Y, w, h, 2, 2); boxV(Y, w, h, 1);
  const Yb = Y.slice(); boxH(Yb, w, h, 6, 2); boxV(Yb, w, h, 1);
  boxH(U, w, h, 10, 3); boxV(U, w, h, 2);
  boxH(V, w, h, 10, 3); boxV(V, w, h, 2);
  const Rr = new Float32Array(N), Gg = new Float32Array(N), Bb = new Float32Array(N);
  for (let y = 0; y < h; y++) {
    let gs = 0;
    for (let x = 0; x < w; x++) {
      const i = y * w + x, c = y * w + (x >= 8 ? x - 8 : 0);
      if ((x % 3) === 0) gs = (rand() + rand() + rand() - 1.5) * 7;
      const yy = Y[i] + (Y[i] - Yb[i]) * .6 + gs, u = U[c] * .8, v = V[c] * .8;
      Rr[i] = yy + 1.402 * v; Gg[i] = yy - .344136 * u - .714136 * v; Bb[i] = yy + 1.772 * u;
    }
  }
  for (let y = 0; y < h; y++) {
    const o = y * w;
    for (let x = 0; x < w; x++) {
      const j = (o + x) * 4;
      p[j] = Rr[o + (x + 3 < w ? x + 3 : w - 1)];
      p[j + 1] = Gg[o + x];
      p[j + 2] = Bb[o + (x >= 3 ? x - 3 : 0)];
      p[j + 3] = 255;
    }
  }
  const out = cv(w, h);
  out.getContext('2d').putImageData(img, 0, 0);
  return out;
}
function contain(art, bw, bh) {
  const k = Math.min(bw / art.naturalWidth, bh / art.naturalHeight);
  return [Math.max(1, Math.round(art.naturalWidth * k)), Math.max(1, Math.round(art.naturalHeight * k))];
}
function plate(P, T, art) {
  const c = cv(CFG.PW, CFG.PH), g = c.getContext('2d'), M = CFG.M, side = P.moon;
  g.imageSmoothingQuality = 'high';
  g.save();
  g.translate(CFG.PW / 2, CFG.PH / 2); g.scale(P.zoom, P.zoom);
  if (side < 0) g.scale(-1, 1);
  g.translate(-CFG.PW / 2 - 40 + P.fx, -CFG.PH / 2 - 40 + P.fy);
  g.drawImage(T.field, 0, 0);
  g.restore();
  if (art) {
    let fw, fh, x, y;
    if (P.figure) {
      [fw, fh] = contain(art, CFG.FIG_W, CFG.FIG_H);
      x = M + P.cx - fw / 2; y = M + CFG.FEET - fh;
      g.save(); g.translate(M + P.cx, M + CFG.FEET - 6); g.scale(1, 26 / Math.max(60, fw * .42));
      const sh = g.createRadialGradient(0, 0, 0, 0, 0, Math.max(60, fw * .42) * 1.25);
      sh.addColorStop(0, 'rgba(0,0,0,.6)'); sh.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = sh; g.fillRect(-1200, -1200, 2400, 2400); g.restore();
    } else {
      [fw, fh] = contain(art, 640, 640);
      x = M + P.cx - fw / 2; y = M + 1000 - fh / 2;
    }
    g.drawImage(moonlit(art, fw, fh, side), x, y);
  }
  g.save();
  g.translate(P.fogx, 0);
  g.drawImage(T.fog, -80, -80);
  g.restore();
  g.save();
  if (P.cornflip) { g.translate(CFG.PW, 0); g.scale(-1, 1); }
  g.drawImage(T.corn, -80, -80);
  g.restore();
  g.save(); g.translate(M + 560, M + 960); g.scale(760 / 1180, 1);
  const vg = g.createRadialGradient(0, 0, 0, 0, 0, 1298);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(.35, 'rgba(0,0,0,0)');
  vg.addColorStop(.55, 'rgba(0,0,0,.1)'); vg.addColorStop(.75, 'rgba(0,0,0,.3)'); vg.addColorStop(1, 'rgba(0,0,0,.62)');
  g.fillStyle = vg; g.fillRect(-2400, -2400, 4800, 4800); g.restore();
  return tape(c, CFG.seed + P.k * 101);
}
// An instant photo: the skin in the camera's flash, in full colour, the field
// dark behind it.
function photo(P, T, art) {
  const S = 440, c = cv(S, S), g = c.getContext('2d');
  g.imageSmoothingQuality = 'high';
  g.filter = 'brightness(.5) saturate(.7)';
  g.save();
  if (P.moon < 0) { g.translate(S, 0); g.scale(-1, 1); }
  g.drawImage(T.field, 250, 560, 780, 780, -30, 0, S + 60, S + 60);
  g.restore();
  g.filter = 'none';
  if (art) {
    let fw, fh, x, y;
    if (P.figure) { [fw, fh] = contain(art, S * .96, S * 1.3); x = (S - fw) / 2; y = S * .05; }
    else { [fw, fh] = contain(art, S * .8, S * .8); x = (S - fw) / 2; y = (S - fh) / 2; }
    g.filter = 'brightness(1.04) contrast(1.06) saturate(1.04)';
    g.drawImage(art, x, y, fw, fh);
    g.filter = 'none';
  }
  const fl = g.createRadialGradient(S / 2, S * .42, S * .12, S / 2, S * .45, S * .78);
  fl.addColorStop(0, 'rgba(0,0,0,0)'); fl.addColorStop(.6, 'rgba(0,0,0,.14)'); fl.addColorStop(1, 'rgba(0,0,0,.55)');
  g.fillStyle = fl; g.fillRect(0, 0, S, S);
  g.globalCompositeOperation = 'lighter'; g.fillStyle = 'rgb(20,17,14)'; g.fillRect(0, 0, S, S);
  g.globalCompositeOperation = 'multiply'; g.fillStyle = 'rgb(255,244,226)'; g.fillRect(0, 0, S, S);
  return c;
}
// Tape noise, made once and moved about while the video plays.
function noise(c, kind, rand) {
  const w = c.width, h = c.height, g = c.getContext('2d'), d = g.createImageData(w, h), p = d.data;
  if (kind === 'band') {
    const a = new Float32Array(w * h);
    for (let k = 0; k < 240; k++) {
      const y = Math.floor(rand() * h), x0 = Math.floor(rand() * (w + 100)) - 100, L = 30 + rand() * 390, v = .25 + rand() * .75;
      for (let x = Math.max(0, x0); x < Math.min(w, x0 + L); x++) a[y * w + x] = v;
    }
    boxH(a, w, h, 4, 2);
    for (let y = 0; y < h; y++) {
      const pr = Math.exp(-Math.pow((y - h * .55) / (h * .28), 2));
      for (let x = 0; x < w; x++) {
        const i = y * w + x, v = Math.min(1, a[i] * 1.6 + pr * .18) * pr;
        p[i * 4] = 236; p[i * 4 + 1] = 232; p[i * 4 + 2] = 222; p[i * 4 + 3] = v * 255;
      }
    }
  } else {
    const snow = kind === 'snow';
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const j = (y * w + x) * 4;
      if (snow) {
        const v = Math.max(0, Math.min(255, (rand() * 255 - 128) * 1.6 + 110));
        p[j] = p[j + 1] = p[j + 2] = v; p[j + 3] = 255;
      } else {
        const n = (rand() + rand() + rand() - 1.5) * 1.4, v = n > 0 ? 255 : 0;
        p[j] = p[j + 1] = p[j + 2] = v; p[j + 3] = Math.min(255, Math.abs(n) * 46);
      }
    }
    for (let k = 0; k < (snow ? 60 : 26); k++) {        // dropouts: short bright dashes
      const y = Math.floor(rand() * h), x0 = Math.floor(rand() * w), L = 3 + Math.floor(rand() * 22);
      for (let x = x0; x < Math.min(w, x0 + L); x++) {
        const j = (y * w + x) * 4; p[j] = p[j + 1] = p[j + 2] = 250; p[j + 3] = snow ? 255 : 200;
      }
    }
  }
  g.putImageData(d, 0, 0);
}
async function vhsPrep() {
  const T = {};
  T.field = await ready(document.getElementById('vhs-field'));
  const fog = await ready(document.getElementById('vhs-fog')), corn = await ready(document.getElementById('vhs-corn'));
  T.fog = tint(fog, [112, 106, 96], 1.0);
  T.corn = tint(corn, [14, 13, 11], .93);
  const arts = [];
  for (const el of document.querySelectorAll('img.vhs-art')) arts[+el.dataset.a] = await ready(el);
  const rand = rng(CFG.seed);
  for (const c of document.querySelectorAll('canvas.vhs-noise')) noise(c, c.dataset.kind, rand);
  const jobs = [];
  for (const P of CFG.plates) {
    const url = await blob(plate(P, T, P.art >= 0 ? arts[P.art] : null));
    for (const el of document.querySelectorAll(`img.vhs-plate[data-p="${P.k}"]`)) { el.src = url; jobs.push(ready(el)); }
  }
  for (const P of CFG.photos) {
    const art = P.art >= 0 ? arts[P.art] : null;
    if (!art) continue;
    const url = await blob(photo(P, T, art));
    for (const el of document.querySelectorAll(`img.vhs-photo[data-p="${P.k}"]`)) { el.src = url; jobs.push(ready(el)); }
  }
  await Promise.all(jobs);
}
})();</script>
"""


def _prep_js(cfg: dict) -> str:
    return VHS_FILTER_JS.replace("__CFG__", json.dumps(cfg))


# ------------------------------------------------------------------ the video

def _osd_text(text: str, x: float, y: float, size: float, anim: str = "", extra: str = "", cls: str = "osd",
              fit: int = 0) -> str:
    fit_attr = f' data-fit="{fit}"' if fit else ""
    return (f'<div class="{cls}"{fit_attr} style="left:{x:.0f}px;top:{y:.0f}px;font-size:{size:.0f}px;{extra}{anim}">'
            f'{text}</div>')


def _tri(px: int = 7) -> str:
    rows = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
    rects = "".join(f'<rect x="0" y="{i * px}" width="{n * px}" height="{px}"/>' for i, n in enumerate(rows))
    return (f'<svg width="{6 * px}" height="{11 * px}" style="display:inline-block;vertical-align:baseline;'
            f'margin-left:.18em;fill:currentColor;filter:drop-shadow(3px 3px 0 rgba(0,0,0,.85))">{rects}</svg>')


def _ff(px: int = 6, back: bool = False) -> str:
    """Two triangles: fast-forward, or (back=True) rewind."""
    rows = [1, 2, 3, 4, 5, 4, 3, 2, 1]
    one = lambda ox: "".join(
        f'<rect x="{(ox + (5 - n if back else 0)) * px}" y="{i * px}" width="{n * px}" height="{px}"/>'
        for i, n in enumerate(rows))
    return (f'<svg width="{11 * px}" height="{9 * px}" style="display:inline-block;vertical-align:baseline;'
            f'margin-left:.18em;fill:currentColor;filter:drop-shadow(3px 3px 0 rgba(0,0,0,.85))">'
            f'{one(0)}{one(6)}</svg>')


def _bars(px: int = 7, stop: bool = False) -> str:
    if stop:
        body = f'<rect x="0" y="0" width="{6 * px}" height="{6 * px}"/>'
        return (f'<svg width="{6 * px}" height="{6 * px}" style="display:inline-block;vertical-align:baseline;'
                f'margin-left:.2em;fill:currentColor;filter:drop-shadow(3px 3px 0 rgba(0,0,0,.85))">{body}</svg>')
    return ""


def throwback(ctx, spec: dict, group: list, theme: dict) -> Comp:
    n = len(group)
    content_end = HOOK + n * R
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(CSS.replace("@LIME@", LIME))
    tr = _Tracks(comp)
    rnd = random.Random(ctx.seed * 7 + n)
    dur = comp.duration
    theme = theme or {}

    arts, art_idx = [], {}
    for it in group:
        a = ctx.art(it) or ""
        if a and a not in art_idx:
            art_idx[a] = len(arts)
            arts.append(a)
    idx = [art_idx.get(ctx.art(it) or "", -1) for it in group]

    # ---- the plates: which way the moon is, where the skin stands, how it's framed
    plates = []
    for k, it in enumerate(group):
        plates.append({"k": k, "art": idx[k], "moon": 1 if k % 2 == 0 else -1, "figure": _is_figure(it),
                       "cx": 580 + (-18 if k % 2 else 18) + rnd.uniform(-12, 12), "zoom": round(rnd.uniform(1.0, 1.05), 3),
                       "fx": round(rnd.uniform(-30, 30)), "fy": round(rnd.uniform(-30, 30)),
                       "fogx": round(rnd.uniform(-40, 40)), "cornflip": bool(k % 3 == 1)})
    photos = [{"k": j, "art": idx[j], "moon": 1 if j == 0 else -1, "figure": _is_figure(group[j])}
              for j in range(min(2, n))]
    cfg = {"seed": int(ctx.seed) % 2147483647, "PW": PW, "PH": PH, "M": M, "FEET": FEET, "FIG_H": FIG_H,
           "FIG_W": FIG_W, "plates": plates, "photos": photos}

    # Sources for the page script: textures and each skin's art, once each.
    comp.add('<div style="display:none">'
             f'<img id="vhs-field" src="{tex("vhs-field.jpg")}"><img id="vhs-fog" src="{tex("vhs-fog.jpg")}">'
             f'<img id="vhs-corn" src="{tex("vhs-stalks.jpg")}">'
             + "".join(f'<img class="vhs-art" data-trim data-a="{i}" src="{a}">' for i, a in enumerate(arts))
             + '</div>')

    # ---- timeline of cuts: clip k is on screen from its roll-in to the next cut
    starts = [HOOK + k * R for k in range(n)]
    cuts = starts[1:]                                   # between clip k and k+1
    styles = ["ff" if (j % 3 == 1) else "glitch" for j in range(len(cuts))]

    # ---- the hook: the desk, the photos, the cassette
    title = _label_title(group, theme)
    rest = n - 2
    names = " + ".join(it["name"].lower() for it in group[:2]) + (f" + {rest} more" if rest > 0 else "")
    ep = spec.get("episode")
    of = spec.get("of", 31)
    day_txt = f"DAY {ep} OF {of}" if ep else "THROWBACK"
    part = f"PART {spec['part']}" if spec.get("part") else ""
    desk = tex("vhs-desk.jpg")
    lift = _style(_a("vhlift", T_LIFT, T_CUT - T_LIFT + .08, "cubic-bezier(.5,0,.85,.4)"))
    photos_html = "".join(_photo(j, group[j], x, y, rot, idx[j] >= 0)
                          for j, (x, y, rot) in enumerate(PHOTOS[:min(2, n)]))
    stage = (f'<div class="full" style="background:url({desk}) center/cover"></div>'
             f'<div class="full" style="perspective:1500px;perspective-origin:540px 560px;transform-origin:520px 760px;'
             f'{_style(_a("vhpush", 0, T_CUT, "cubic-bezier(.4,0,.5,1)"))}">'
             f'<div class="abs" style="left:534px;top:{DESK_Y}px;transform-style:preserve-3d;transform:rotateX(24deg) scale(.97)">'
             f'{photos_html}'
             f'<div style="transform-style:preserve-3d;{lift}"><div style="transform-style:preserve-3d;transform:rotateZ(-8.5deg)">'
             f'{_cassette(title, names, day_txt, part)}</div></div></div></div>'
             f'<div class="full" style="background:radial-gradient(ellipse 90% 75% at 46% 40%,rgba(0,0,0,0) 55%,'
             f'rgba(0,0,0,.55) 100%)"></div>')
    comp.scene(0, _snap(T_CUT), f'<div class="full">{stage}</div>', fade_in=.01, fade_out=.001, z=1)
    comp.cue(T_LIFT - .05, "tape")

    # ---- the player's blue screen, until the tape rolls
    blue = (f'<div class="full" style="background:{BLUE_BG}"></div>'
            + _osd_text(f"PLAY{_tri(11)}", 84, 600, 170)
            + _osd_text(esc((theme.get("title") or title).upper()), 88, 850, 106, fit=904)
            + _osd_text(esc(" · ".join(x for x in ((part or "THROWBACK"), f"DAY {ep} OF {of}" if ep else "") if x)),
                        90, 980, 62, fit=900)
            + _osd_text(esc((theme.get("sub") or "HOW MANY DO YOU REMEMBER?").upper()), 90, 1070, 78, fit=900))
    comp.scene(_snap(T_CUT), _snap(T_ROLL + .5), f'<div class="full">{blue}</div>', fade_in=.001, fade_out=.001, z=2)
    comp.cue(T_CUT, "click")

    # ---- the recordings
    for k, it in enumerate(group):
        t0 = starts[k]
        # in: rolls in from the blue screen, from a tape cut, or straight after a fast-forward
        if k == 0:
            t_in, rin = T_ROLL, _a("vhroll", T_ROLL, .44, "steps(1,end)")
        elif styles[k - 1] == "glitch":
            t_in, rin = t0, _a("vhroll", t0, .44, "steps(1,end)")
        else:
            t_in, rin = t0, ""
        if k < n - 1 and styles[k] == "glitch":
            t_out, gout = cuts[k], _a("vhglitch", cuts[k] - .3, .3, "steps(1,end)", fill="forwards")
        else:
            t_out, gout = (cuts[k] if k < n - 1 else content_end), ""
        band_t = t0 + rnd.uniform(1.4, 3.6)
        html = _clip(comp, tr, k, it, theme, t0, t_in, rin, gout, band_t, rnd)
        comp.scene(_snap(t_in), _snap(t_out), html, fade_in=.001, fade_out=.001, z=3 + (k % 2))

    # ---- sounds for the recordings and cuts
    comp.cue(T_ROLL, "static")
    for j, (tc, st) in enumerate(zip(cuts, styles)):
        if st == "glitch":
            comp.cue(tc - .3, "static")
        else:
            comp.cue(tc - .62, "click"); comp.cue(tc - .58, "static"); comp.cue(tc + .2, "click")

    # ---- the rewind at the end, then the player's menu
    t_rew, t_menu = content_end, content_end + min(1.3, .16 * n + .1)
    step = (t_menu - t_rew) / n
    rew = ""
    for j, k in enumerate(reversed(range(n))):
        v = tr.vis([(t_rew + j * step, t_rew + (j + 1) * step)])
        rew += (f'<div class="full" style="{_style(v)}"><div class="full" style="transform:scale(1.06);'
                f'transform-origin:580px 1000px"><img class="plate vhs-plate" data-p="{k}"></div></div>')
    rew = (f'<div class="full" style="overflow:hidden;background:#000"><div class="full lay" '
           f'style="{_style(_a("vhrew", t_rew, .24, "steps(1,end)", "infinite"))}">{rew}</div></div>')
    comp.scene(_snap(t_rew), _snap(t_menu), rew, fade_in=.001, fade_out=.001, z=6)
    comp.cue(t_rew, "click"); comp.cue(t_rew + .04, "static"); comp.cue(t_menu, "click")

    menu = (f'<div class="full" style="background:{BLUE_BG}"></div>'
            + _osd_text("WHICH ONE DID YOU OWN?", 80, 556, 96, fit=920))
    pitch = min(96, 640 / n)
    size = min(70, pitch - 12)
    t_list = t_menu + .35
    t_sel = t_list + n * .09 + .9                     # then a cursor walks down the list
    sel = 1.1
    for j, it in enumerate(group):
        y = 690 + j * pitch
        on = [(t_sel + (c * n + j) * sel, t_sel + (c * n + j + 1) * sel) for c in range(int((dur - t_sel) / (n * sel)) + 1)]
        on = [(a, b) for a, b in on if a < dur]
        line = f'<span style="color:#aab3ff">{j + 1:02d}</span>&nbsp;{esc(it["name"].upper())}'
        shown = _a("lkin", t_list + j * .09, .01, "steps(1,end)")
        menu += (f'<div class="osd" data-fit="880" style="left:84px;top:{y:.0f}px;font-size:{size:.0f}px;'
                 f'{_style(shown)}">{line}</div>')
        if on:
            menu += (f'<div class="abs" style="left:70px;top:{y - 8:.0f}px;width:900px;height:{size + 12:.0f}px;'
                     f'background:#f2f2ee;box-shadow:4px 4px 0 rgba(0,0,0,.6);{_style(tr.vis(on))}">'
                     f'<div class="osd" data-fit="880" style="left:14px;top:8px;font-size:{size:.0f}px;color:#1c2ca6;'
                     f'text-shadow:none"><span style="color:#5563d6">{j + 1:02d}</span>&nbsp;'
                     f'{esc(it["name"].upper())}</div></div>')
    comp.scene(_snap(t_menu), dur, f'<div class="full">{menu}</div>', fade_in=.001, fade_out=.001, z=7)

    ff_w = [(tc - .62, tc + .2) for tc, st in zip(cuts, styles) if st == "ff"]
    rew_w = [(t_rew, t_menu)]
    stop_w = [(t_menu, dur + 1)]

    # ---- the tape itself over everything from the first blue frame: noise,
    # snow at the cuts and search bars when it winds, scanlines, a faint flicker
    grain_k = comp.uid("vg")
    snow_k = comp.uid("vs")
    offs = [(rnd.randint(-90, 90), rnd.randint(-90, 90)) for _ in range(12)]
    comp.css(f"@keyframes {grain_k}{{" + "".join(f"{i * 100 / 12:.3f}%{{transform:translate({x}px,{y}px)}}"
                                                 for i, (x, y) in enumerate(offs)) + "}")
    offs2 = [(rnd.randint(-90, 90), rnd.randint(-90, 90)) for _ in range(12)]
    comp.css(f"@keyframes {snow_k}{{" + "".join(f"{i * 100 / 12:.3f}%{{transform:translate({x}px,{y}px)}}"
                                                for i, (x, y) in enumerate(offs2)) + "}")
    loop = lambda k: _a(k, -.5 / FPS, 12 / FPS, "steps(1,end)", "infinite")
    snow_pts = [(0, 0), (T_ROLL - .04, .95), (T_ROLL + .08, .6), (T_ROLL + .16, .38), (T_ROLL + .24, .18),
                (T_ROLL + .32, 0)]
    for tc, st in zip(cuts, styles):
        if st == "glitch":
            snow_pts += [(tc - .3, .26), (tc - .24, .5), (tc - .18, .22), (tc - .12, .42), (tc - .04, .9),
                         (tc + .06, .62), (tc + .14, .36), (tc + .22, .16), (tc + .3, 0)]
        else:
            snow_pts += [(tc - .6, .18), (tc - .5, .1), (tc - .34, .22), (tc - .2, .12), (tc - .06, .3),
                         (tc + .04, .14), (tc + .16, 0)]
    snow_pts += [(t_rew, .3), (t_rew + .1, .16), (t_menu - .12, .5), (t_menu, 0)]
    snow_v = tr.levels(snow_pts)
    tape_v = tr.vis([(T_CUT, dur + 1)])
    comp.add(f'<div class="full" style="z-index:20;pointer-events:none;{_style(tape_v)}">'
             f'<div class="abs lay" style="left:-100px;top:-100px;width:1280px;height:2120px;{_style(loop(grain_k))}">'
             f'<canvas class="vhs-noise" data-kind="grain" width="427" height="1060" '
             f'style="display:block;width:1280px;height:2120px"></canvas></div>'
             f'<div class="full" style="{_style(snow_v)}"><div class="abs lay" style="left:-100px;top:-100px;'
             f'width:1280px;height:2120px;{_style(loop(snow_k))}"><canvas class="vhs-noise" data-kind="snow" '
             f'width="427" height="1060" style="display:block;width:1280px;height:2120px"></canvas></div></div>'
             + _search_bars(comp, tr, ff_w, rnd, up=False, count=2)
             + _search_bars(comp, tr, rew_w, rnd, up=True, count=3)
             + f'<div class="scan"></div><div class="tvig"></div>'
             f'<div class="full" style="background:#fff8e8;{_style(_a("vhflick", 0, .53, "steps(1,end)", "infinite"))}"></div>'
             f'</div>')

    # ---- the player's lettering, crisp on top
    # PLAY shows while the tape plays and nothing else is showing
    play_w = _minus((T_ROLL, dur + 1), ff_w + rew_w + stop_w)
    osd = (_osd_text(f"PLAY{_tri(5)}", 78, 212, 80, _style(tr.vis(play_w)))
           + _osd_text(f"FF{_ff(6)}", 78, 212, 80, _style(tr.vis(ff_w)) if ff_w else "opacity:0;")
           + _osd_text(f"REW{_ff(6, back=True)}", 78, 212, 80, _style(tr.vis(rew_w)))
           + _osd_text(f"STOP{_bars(8, stop=True)}", 78, 212, 80, _style(tr.vis(stop_w)))
           + _osd_text("SP", 318, 228, 64, _style(tr.vis([(T_ROLL, t_menu)])))
           + _osd_text("CH 03", 0, 218, 64, _style(tr.vis([(T_CUT, T_ROLL)])), "right:66px;left:auto;")
           + "".join(_osd_text(f"{k + 1}/{n}", 0, 218, 64,
                               _style(tr.vis([(starts[k] if k else T_ROLL, (cuts[k] if k < n - 1 else t_rew))])),
                               "right:66px;left:auto;") for k in range(n))
           + _osd_text("USE CODE: BAD", 72, 292, 144, cls="osd codeline")
           + _osd_text("#EpicPartner", 80, 444, 44))
    comp.add(f'<div class="full" style="z-index:30;pointer-events:none;{_style(tape_v)}">{osd}</div>')

    comp.add(PREP_JS)
    comp.add(_prep_js(cfg))
    comp.cues.sort()
    return comp
