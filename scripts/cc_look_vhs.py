"""
VHS -- the Fortnitemares throwbacks as a camcorder tape someone found in a drawer.

    0:00  hook      the cassette on a dark desk: a marker label with the event and
                    its years ("FORTNITEMARES '17-'18"), DON'T TAPE OVER!, the day of
                    the series, a big lime USE CODE: BAD sticker, and instant photos
                    of the first two skins. It's picked up to go in the player...
    0:01  play      ...the player's blue screen: PLAY, the episode's title and "how
                    many do you remember?". The tape rolls into the first recording.
    0:03  skins     one recording per skin (6.5 s): the skin standing in a foggy,
                    moonlit field, filmed hand-held (a drift, a slow zoom in on the
                    face, a pan, or holding still); burned-in captions (name, rarity
                    and type, its Fortnitemares year, when it first hit the shop) and
                    a camcorder date stamp; tape jitter and a tracking band. Between
                    skins the tape cuts, or fast-forwards.
    end   outro     the tape rewinds through every skin and stops on the player's
                    blue menu, a cursor walking down the list: which one did you own?

The player's own lettering (PLAY, the lime USE CODE: BAD line, #EpicPartner) sits
crisp on top of the picture from the first blue frame to the last; before that the
code is the big sticker on the cassette.

Every app lays its UI over the edges (cc_safe): a header across the top, the
like/comment/share rail down the right from y 740, the caption block across the
bottom. So the camcorder's corners are the safe box's corners, not the frame's:
PLAY and the counter sit just inside its top edge, the date stamp in its
bottom-right corner beside the rail, the skin stands in the box's narrow column,
and the desk is laid out inside it (photos in the wide band, the cassette in the
column below). Only the picture itself -- the field, the fog, the tape's noise,
scanlines and the desk's wood -- runs to the frame's edges.

The footage is put together once, before the first frame, by a script in the
page: the field (a committed texture), the skin lit by the moon, the fog and corn
in front of it, then the tape's smear (a soft picture, colour bleeding sideways, a
red/blue fringe, grain). While the video plays only cheap things change: layers
move (transforms), switch on and off (visibility) or fade (opacity of single
layers). No CSS filter, mask or blend mode is used after the first second, so the
software compositor draws each frame in one pass.

Facts on screen are the classic format's: each item's name, rarity and type, its
Fortnitemares year, and when it first hit the shop -- a date only from 2018 on;
for anything first seen before that, only the year. The date stamp shows that
same date (or year) and nothing else.
"""

import json
import random

from cc_looks import KIT_CSS, LIME, PREP_JS, pad_to, rough_ellipse, rough_line, tex
from cc_motion import SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, SAFE_TOP, W, Comp, esc

HOOK = 3.0
R = 6.5
FPS = 30
FONTS = ("VT323", "Permanent Marker", "Kalam")

# The hook: the cassette is picked up at T_LIFT, the player's blue screen cuts in
# at T_CUT, and the tape rolls into the first recording at T_ROLL.
T_LIFT, T_CUT, T_ROLL = .9, 1.3, 2.7

# The footage is 1160x2000: the frame plus 40 px all round for the camera to
# drift in. The skin stands in the safe box's narrow column (x 60-900, beside the
# apps' button rail), centred at FIG_X with its feet at FEET (frame
# coordinates), so that even at the camera's closest it stays clear of the
# player's lettering above it and the apps' caption block below; the corn and
# the burned-in captions come up over its legs, as they would on the tape.
# Anything that isn't an outfit (a pickaxe, an emote) hangs in the fog, centred
# at ITEM_Y.
PW, PH, M = 1160, 2000, 40
FIG_X = (SAFE_LEFT + SAFE_RIGHT) // 2          # 480
FEET, FIG_H, FIG_W = 1330, 780, 680
ITEM_Y, ITEM_S = 850, 560

BLUE_BG = "radial-gradient(ellipse 80% 60% at 50% 45%,#2b40c9,#1c2ca6 70%,#15208b)"

CSS = """
.vl{position:absolute;inset:0;visibility:hidden}
.osd{position:absolute;font-family:'VT323',monospace;color:#f2f2ee;line-height:1;white-space:nowrap;
  letter-spacing:.02em;text-shadow:3px 3px 0 rgba(0,0,0,.85)}
.codeline{color:@LIME@;letter-spacing:.01em;text-shadow:5px 5px 0 rgba(0,0,0,.9)}
.cam{position:absolute;font-family:'VT323',monospace;color:#f4eedb;white-space:nowrap;letter-spacing:.03em;
  line-height:1;text-shadow:-3px 0 rgba(255,60,50,.5),3px 0 rgba(40,220,255,.4),2px 2px 1px rgba(0,0,0,.6),
  0 0 3px rgba(244,238,219,.45)}
.mk{font-family:'Permanent Marker',cursive;color:#171615;white-space:nowrap;line-height:1}
.kl{font-family:'Kalam',cursive;white-space:nowrap;line-height:1}
.lay{will-change:transform}
.fade{will-change:opacity}
.plate{position:absolute;left:-40px;top:-40px;width:1160px;height:2000px;display:block}
.crt{position:absolute;inset:0;background:radial-gradient(ellipse 88% 72% at 50% 48%,rgba(0,0,0,0) 58%,
  rgba(0,0,0,.5) 100%),repeating-linear-gradient(to bottom,rgba(0,0,0,0) 0px,rgba(0,0,0,.24) 3px,rgba(0,0,0,0) 6px)}
.ribs{border-radius:8px;background:repeating-linear-gradient(to right,rgba(255,255,255,.05) 0 3px,
  rgba(0,0,0,.35) 3px 7px);box-shadow:inset 0 2px 4px rgba(0,0,0,.7)}
.cass3d{transform-style:preserve-3d}
.face{border-radius:16px;overflow:hidden}
.edge{transform-origin:50% 0;transform:rotateX(-90deg);border-radius:0 0 10px 10px}
@keyframes vhpush{from{transform:scale(1)}to{transform:scale(1.03)}}
@keyframes vhlift{from{transform:translate3d(0,0,0) rotateX(0deg) rotateZ(0deg)}
  to{transform:translate3d(-30px,-300px,430px) rotateX(-14deg) rotateZ(3deg)}}
@keyframes vhland{from{transform:translate3d(-30px,-300px,430px) rotateX(-14deg) rotateZ(3deg)}
  70%{transform:translate3d(0,6px,0) rotateX(0deg) rotateZ(0deg)}
  to{transform:translate3d(0,0,0) rotateX(0deg) rotateZ(0deg)}}
@keyframes vhpull{from{transform:scale(1.03)}to{transform:scale(1)}}
@keyframes vhjit{0%{transform:translate(0,0)}12%{transform:translate(2px,0)}24%{transform:translate(0,0)}
  41%{transform:translate(-2px,1px)}52%{transform:translate(1px,0)}66%{transform:translate(0,0)}
  79%{transform:translate(3px,0)}88%{transform:translate(-1px,0)}100%{transform:translate(0,0)}}
@keyframes vhroll{0%{transform:translateY(40%)}16%{transform:translateY(24%) skewX(-2deg)}
  32%{transform:translate(14px,10%)}48%{transform:translateY(3%)}64%{transform:translate(-6px,-1%)}
  80%{transform:translate(3px,0)}100%{transform:none}}
@keyframes vhrollw{0%{opacity:.16}32%{opacity:.07}64%,100%{opacity:0}}
@keyframes vhglitch{0%{transform:translateX(-28px) skewX(-4deg)}18%{transform:translate(22px,-4%)}
  36%{transform:translate(-8px,-15%) skewX(3deg)}54%{transform:translate(0,-30%)}72%,100%{transform:translate(0,-46%)}}
@keyframes vhglitchw{0%{opacity:.18}18%{opacity:0}36%{opacity:.12}54%,100%{opacity:0}}
@keyframes vhglitchk{0%,36%{opacity:0}54%{opacity:.3}72%,100%{opacity:.6}}
@keyframes vhflick{0%{opacity:0}25%{opacity:.03}50%{opacity:.012}75%{opacity:.035}100%{opacity:0}}
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


def _style(*entries: str) -> str:
    entries = [e for e in entries if e]
    return f"animation:{','.join(entries)};" if entries else ""


def _union(windows: list) -> list:
    out = []
    for a, b in sorted(windows):
        if out and a <= out[-1][1] + 1e-6:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _minus(span: tuple, holes: list) -> list:
    """The parts of the window `span` not covered by any of `holes`."""
    out, (a, b) = [], span
    for h0, h1 in _union(holes):
        if h1 <= a or h0 >= b:
            continue
        if h0 > a:
            out.append((a, h0))
        a = max(a, h1)
    if a < b:
        out.append((a, b))
    return out


class _Tracks:
    """Hard cuts as keyframe tracks over the whole video. Visibility for things
    that are on or off (it costs the compositor nothing); opacity only for the
    single layers that really fade (snow)."""

    def __init__(self, comp: Comp):
        self.comp = comp

    def _track(self, prop: str, pts: list, before, fmt) -> str:
        d = self.comp.duration
        name = self.comp.uid("vk")
        ks = {0.0: before}
        for t, v in pts:                                   # in order: a later point at the same time wins
            ks[round(min(max(_snap(t), 0.0), d) / d * 100, 4)] = v
        frames = "".join(f"{k:.4f}%{{{prop}:{fmt(v)}}}" for k, v in sorted(ks.items()))
        frames += f"100%{{{prop}:{fmt(ks[max(ks)])}}}"
        self.comp.css(f"@keyframes {name}{{{frames}}}")
        return f"{name} {d:.3f}s steps(1,end) 0s 1 normal both"

    def levels(self, pts: list, before: float = 0.0) -> str:
        """[(t, opacity), ...]: the opacity jumps to each level at its time."""
        return self._track("opacity", sorted(pts, key=lambda p: p[0]), before, lambda v: f"{v:g}")

    def vis(self, windows: list) -> str:
        """Visible inside the windows [(start, end), ...], hidden outside."""
        windows = _union(windows)
        pts, before = [], "hidden"
        for a, b in windows:
            if a <= 0:
                before = "visible"
            else:
                pts.append((a, "visible"))
            pts.append((b, "hidden"))
        return self._track("visibility", pts, before, str)


def _layer(tr: _Tracks, windows: list, z: int, inner: str, extra: str = "") -> str:
    """A full-frame layer shown only inside `windows`."""
    return f'<div class="vl" style="z-index:{z};{extra}{_style(tr.vis(windows))}">{inner}</div>'


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
    or only the year when the records can't be sure of the day (theme['when']
    already says which)."""
    when = (theme["when"](it) if theme.get("when") else "") or ""
    parts = when.replace(",", "").split()
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():      # "OCT 7, 2018"
        return f"{parts[0].upper()}. {parts[1]} {parts[2]}"
    return when.strip().upper()                                            # "2017"


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
    return (it.get("type") or "Outfit").lower() == "outfit"


# ------------------------------------------------------------------ the desk and the cassette

CW, CH, CT = 960, 530, 128             # cassette face, and its thickness
PHOTO_S = 400                          # an instant photo's picture
# Frame 0 is the thumbnail, laid out inside the safe box (and Instagram's 4:5
# grid crop, y >= 285): the two photos side by side in the wide band at the
# top, the cassette in the box's column below them, scaled (CS) and turned (CR)
# so that its right end stays clear of the apps' button rail. DESK_X/DESK_Y is
# where the cassette's centre lies on the desk (before perspective); the photos
# are placed from it (x, y, rotation), the second overlapping the first a
# little. PUSH is the slow lean in on the desk and where it leans to.
CS, CR = .82, -4
DESK_X, DESK_Y = 469, 1054
PHOTOS = [(-451, -900, -6), (19, -889, 5)]
PUSH_ORIGIN = "480px 850px"


def _hand(text: str, seed: int, rot: float = 3.2, dy: float = 2.2, sc: float = .04) -> str:
    """Per-letter jitter so marker lettering doesn't repeat identical glyphs like a font does.
    Each word holds together, so lettering that wraps breaks only between words."""
    rnd = random.Random(seed)
    words = []
    for word in text.split(" "):
        letters = "".join(f'<span style="display:inline-block;transform:translateY({rnd.uniform(-dy, dy):.1f}px) '
                          f'rotate({rnd.uniform(-rot, rot):.1f}deg) scale({1 + rnd.uniform(-sc, sc):.3f})">'
                          f'{esc(ch)}</span>' for ch in word)
        words.append(f'<span style="white-space:nowrap">{letters}</span>' if word else "")
    return " ".join(words)


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
    """The paper label, written on in marker: what's on the tape. Sized for the
    cassette at CS: each line reads at 30 px or more on the phone (the title at
    about 50), #EpicPartner at about 26."""
    paper = tex("paper.jpg")
    ink = tex("vhs-marker.png")
    warn = f"{part} · DON'T TAPE OVER!" if part else "DON'T TAPE OVER!"
    ux = min(500, 70 + 24 * len(warn))                     # the underlines run about as far as the words
    u1, _ = rough_line(48, 150, ux, 143, seed=5)
    u2, _ = rough_line(60, 161, ux - 22, 156, seed=6)
    ring, _ = rough_ellipse(702, 148, 140, 54, seed=18, overshoot=.12, wobble=.06)
    return (f'<div class="abs" style="left:58px;top:20px;width:844px;height:260px;transform:rotate(-1.1deg);'
            f'background:url({paper}) -120px -300px/1080px 1920px;box-shadow:0 1px 2px rgba(0,0,0,.5)">'
            f'<div class="abs" style="inset:0;background:repeating-linear-gradient(to bottom,rgba(0,0,0,0) 0 57px,'
            f'rgba(120,140,170,.22) 57px 59px);background-position:0 12px"></div>'
            f'<div class="abs" style="inset:0;-webkit-mask:url({ink}) 0 0/100% 100%;mask:url({ink}) 0 0/100% 100%">'
            f'<div class="abs mk" data-fit="792" style="left:24px;top:14px;font-size:80px;transform:rotate(-1.2deg);'
            f'transform-origin:0 50%">{_hand(title, 31)}</div>'
            f'<div class="abs kl" data-fit="520" style="left:44px;top:96px;font-size:48px;color:#c1271e;font-weight:700;'
            f'transform:rotate(-2.4deg);transform-origin:0 50%">{_hand(warn, 32, rot=2.5, dy=1.6)}</div>'
            f'<svg class="abs" width="844" height="260" style="left:0;top:0;overflow:visible">'
            f'<g fill="none" stroke="#c1271e" stroke-width="4" stroke-linecap="round" opacity=".92">'
            f'<path d="{u1}"/><path d="{u2}"/></g>'
            f'<g fill="none" stroke="#161616" stroke-width="4" stroke-linecap="round" opacity=".9">'
            f'<path d="{ring}"/></g></svg>'
            f'<div class="abs kl" data-fit="520" style="left:48px;top:182px;font-size:42px;color:#57544f;'
            f'transform:rotate(-1deg);transform-origin:0 50%">{esc(names)}</div>'
            f'<div class="abs mk" data-fit="248" style="left:574px;top:122px;width:250px;text-align:center;'
            f'font-size:48px;transform:rotate(-4deg)">{_hand(day_txt, 33, rot=3.5)}</div>'
            f'<div class="abs kl" style="left:648px;top:210px;font-size:34px;color:#57544f;'
            f'transform:rotate(-3deg)">#EpicPartner</div></div>'
            f'<div class="abs" style="inset:0;background:linear-gradient(100deg,rgba(0,0,0,.04),rgba(255,255,255,0) 30%,'
            f'rgba(0,0,0,.05) 75%,rgba(0,0,0,.12));pointer-events:none"></div></div>')


def _code_sticker() -> str:
    """The creator code on a fluorescent lime sticker slapped across the cassette
    (the code's element for the safe-box check: data-safe="key")."""
    return (f'<div class="abs vhs-code" data-safe="key" data-name="code" style="left:314px;top:294px;width:332px;'
            f'height:212px;transform:rotate(8deg);background:{LIME};border-radius:7px;box-shadow:0 1px 1px rgba(0,0,0,.5),'
            f'0 4px 8px rgba(0,0,0,.4);display:flex;flex-direction:column;align-items:center;justify-content:center;'
            f'text-align:center">'
            f'<div class="abs" style="inset:0;border-radius:7px;background:linear-gradient(160deg,'
            f'rgba(255,255,255,.16),rgba(255,255,255,0) 45%,rgba(0,0,0,.07))"></div>'
            f'<div class="mk" style="position:relative;font-size:50px;color:#111">{_hand("USE CODE:", 41, 2.5, 1.5)}</div>'
            f'<div class="mk" style="position:relative;font-size:136px;line-height:.9;color:#111;margin-top:2px">'
            f'{_hand("BAD", 42, 3, 2)}</div></div>')


def _cassette(title: str, names: str, day_txt: str, part: str) -> str:
    pl = tex("vhs-plastic.jpg")
    return (f'<div class="abs cass3d" style="left:{-CW // 2}px;top:{-CH // 2}px;width:{CW}px;height:{CH}px">'
            f'<div class="abs" style="left:26px;top:40px;width:{CW - 10}px;height:{CH - 10}px;border-radius:24px;'
            f'transform:translateZ(-{CT}px);background:rgba(0,0,0,.85);box-shadow:0 0 40px 24px rgba(0,0,0,.85)"></div>'
            f'<div class="abs face" style="inset:0;background:url({pl}) 0 0/{CW}px 658px">'
            f'<div class="abs" style="left:50px;top:12px;width:{CW - 100}px;height:278px;border-radius:10px;'
            f'box-shadow:inset 0 2px 5px rgba(0,0,0,.85),0 1px 0 rgba(255,255,255,.06)"></div>'
            + _label(title, names, day_txt, part)
            + '<div class="abs" style="left:150px;top:292px;width:660px;height:196px;border-radius:98px;'
              'box-shadow:inset 0 3px 8px rgba(0,0,0,.8),0 1px 0 rgba(255,255,255,.05);background:rgba(0,0,0,.18)"></div>'
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
    """An instant photo of a skin lying on the desk (taken with the flash, at night, in the field)."""
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
            f'<div class="abs mk" data-fit="{S - 8}" data-lines="2" style="left:{P + 6}px;top:{S + P + 14}px;'
            f'width:{S - 8}px;font-size:48px;line-height:1;white-space:normal;color:#23201c;transform:rotate(-1.5deg);'
            f'transform-origin:0 50%">{_hand(it["name"].lower(), 50 + k, 2.5, 1.5)}</div>'
            f'<div class="abs" style="inset:0;background:linear-gradient(180deg,rgba(255,255,255,.06),'
            f'rgba(0,0,0,.08));pointer-events:none"></div></div>')


def _desk(group: list, idx: list, title: str, names: str, day_txt: str, part: str, t_land: float) -> str:
    """Frame 0: the cassette and the photos on the desk; then the cassette is
    picked up. At t_land, after the tape is ejected, it's put back down: the last
    frames match the first, so the video loops."""
    photos = "".join(_photo(j, group[j], x, y, rot, idx[j] >= 0) for j, (x, y, rot) in enumerate(PHOTOS[:len(group)]))
    lift = _style(_a("vhlift", T_LIFT, T_CUT - T_LIFT + .08, "cubic-bezier(.5,0,.85,.4)"),
                  _a("vhland", t_land, .5, "cubic-bezier(.2,.7,.3,1)", fill="forwards"))
    return (f'<div class="full" style="background:url({tex("vhs-desk.jpg")}) center/cover"></div>'
            f'<div class="full" style="perspective:1500px;perspective-origin:540px 560px;transform-origin:{PUSH_ORIGIN};'
            f'{_style(_a("vhpush", 0, T_CUT, "cubic-bezier(.4,0,.5,1)"), _a("vhpull", t_land, .5, "ease-out", fill="forwards"))}">'
            f'<div class="abs" style="left:{DESK_X}px;top:{DESK_Y}px;transform-style:preserve-3d;'
            f'transform:rotateX(24deg) scale(.97)">{photos}'
            f'<div style="transform-style:preserve-3d;{lift}"><div style="transform-style:preserve-3d;'
            f'transform:rotateZ({CR}deg) scale3d({CS},{CS},{CS})">{_cassette(title, names, day_txt, part)}</div></div></div></div>'
            f'<div class="full" style="background:radial-gradient(ellipse 90% 75% at 45% 42%,rgba(0,0,0,0) 55%,'
            f'rgba(0,0,0,.55) 100%)"></div>')


# ------------------------------------------------------------------ the footage

# The burned-in captions, left-aligned from CAP_X and never wider than the box's
# column (CAP_R); the camcorder's date stamp is right-aligned to CAP_R, in the
# box's bottom-right corner: beside the button rail, above the apps' caption
# block. Tops, from the bottom up: stamp (96 px), debut and kind (50), name (88).
CAP_X, CAP_R = SAFE_LEFT + 20, SAFE_RIGHT - 20            # 80, 880
CAP_TOPS = (1096, 1190, 1244, 1318)


def _caption(it: dict, theme: dict) -> str:
    """Burned into the recording: the name, rarity and type with the event year,
    when it first hit the shop; and the camcorder's own date stamp."""
    line2 = " · ".join(x for x in (_kind(it), _era(it, theme)) if x)
    known = bool(it.get("first_shop"))
    debut = (theme["debut"](it) if known and theme.get("debut") else "").upper()
    fit = CAP_R - CAP_X
    y_name, y_kind, y_debut, y_stamp = CAP_TOPS
    return (f'<div class="cam" data-fit="{fit}" style="left:{CAP_X - 2}px;top:{y_name}px;font-size:88px">'
            f'{esc(it["name"].upper())}</div>'
            f'<div class="cam" data-fit="{fit}" style="left:{CAP_X}px;top:{y_kind}px;font-size:50px">{esc(line2)}</div>'
            f'<div class="cam" data-fit="{fit}" style="left:{CAP_X}px;top:{y_debut}px;font-size:50px">{esc(debut)}</div>'
            f'<div class="cam" data-fit="{fit}" style="right:{W - CAP_R}px;top:{y_stamp}px;font-size:96px;'
            f'text-align:right">{esc(_stamp(it, theme) if known else "")}</div>')


# How the camera moves in each recording, in turn: a hand-held drift, a slow zoom
# in on the face, holding still, a slow pan.
MOVES = ("drift", "zoom", "hold", "drift", "pan", "zoom", "hold", "drift")
CAM_MID = f"{FIG_X}px {FEET - FIG_H // 2}px"             # the skin's middle
CAM_FACE = f"{FIG_X}px {FEET - FIG_H + 90}px"            # its face


def _move(move: str, rnd: random.Random) -> tuple:
    """(transform-origin, (scale, x, y) from, (scale, x, y) to) for one
    recording's camera. No rotation: the video encoder can't follow it cheaply.
    Even at its closest the skin stays inside the box's column: under the
    player's lettering, beside the rail, its feet above the apps' captions."""
    j = lambda a: rnd.uniform(-a, a)
    if move == "zoom":
        return CAM_FACE, (1.02, j(4), j(4)), (rnd.uniform(1.1, 1.12), j(5), j(5))
    if move == "pan":
        d = 1 if rnd.random() < .5 else -1
        return CAM_MID, (1.06, 26 * d, j(4)), (1.07, -26 * d, j(4))
    if move == "hold":
        s0 = rnd.uniform(1.03, 1.045)
        return CAM_MID, (s0, j(4), j(4)), (s0 + .006, j(4), j(4))
    s0 = rnd.uniform(1.02, 1.04)
    return CAM_MID, (s0, j(10), j(10)), (s0 + rnd.uniform(.02, .04), j(10), j(10))


def _clip(comp: Comp, tr: _Tracks, k: int, it: dict, theme: dict, t0: float, t_in: float, roll: bool,
          glitch_at, band_t: float, rnd: random.Random) -> str:
    """One recording: the plate, filmed hand-held, a tracking band rolling through
    once, the burned-in captions and the tape's jitter; it rolls in when the tape
    starts, and tears away at a tape cut."""
    hand = comp.uid("vh")
    move = MOVES[k % len(MOVES)] if _is_figure(it) else ("drift", "hold")[k % 2]
    origin, (s0, tx0, ty0), (s1, tx1, ty1) = _move(move, rnd)
    comp.css(f"@keyframes {hand}{{from{{transform:scale({s0:.3f}) translate({tx0:.1f}px,{ty0:.1f}px)}}"
             f"to{{transform:scale({s1:.3f}) translate({tx1:.1f}px,{ty1:.1f}px)}}}}")
    band = comp.uid("vb")
    y_a, y_b = (1950, -200) if rnd.random() < .5 else (-200, 1950)
    comp.css(f"@keyframes {band}{{from{{transform:translateY({y_a}px)}}to{{transform:translateY({y_b}px)}}}}"
             f"@keyframes {band}i{{from{{transform:translate(24px,{-y_a}px)}}to{{transform:translate(24px,{-y_b}px)}}}}")
    bdur = rnd.uniform(1.5, 2.1)
    pic = (f'<div class="full lay vhand" style="transform-origin:{origin};'
           f'{_style(_a(hand, t0 - .3, R + .6, "cubic-bezier(.45,.05,.55,.95)"))}">'
           f'<img class="plate vhs-plate" data-p="{k}">'
           f'<div class="abs lay" style="left:0;top:0;width:{W}px;height:150px;overflow:hidden;visibility:hidden;'
           f'{_style(_a(band, band_t, bdur), tr.vis([(band_t, band_t + bdur)]))}">'
           f'<div class="abs lay" style="left:0;top:0;{_style(_a(band + "i", band_t, bdur))}">'
           f'<img class="plate vhs-plate" data-p="{k}"></div>'
           f'<canvas class="abs vhs-noise" data-kind="band" width="{W}" height="150" '
           f'style="left:0;top:0;width:{W}px;height:150px"></canvas></div></div>')
    moves, white, black = [], [], []
    if roll:
        moves.append(_a("vhroll", t_in, .44, "steps(1,end)"))
        white.append(_a("vhrollw", t_in, .44, "steps(1,end)", fill="forwards"))
    if glitch_at is not None:
        moves.append(_a("vhglitch", glitch_at - .3, .3, "steps(1,end)", fill="forwards"))
        white.append(_a("vhglitchw", glitch_at - .3, .3, "steps(1,end)", fill="forwards"))
        black.append(_a("vhglitchk", glitch_at - .3, .3, "steps(1,end)", fill="forwards"))
    flash = ""
    if white:
        flash += f'<div class="full fade" style="background:#fff;opacity:0;{_style(*white)}"></div>'
    if black:
        flash += f'<div class="full fade" style="background:#000;opacity:0;{_style(*black)}"></div>'
    expo = f'<div class="full fade" style="background:#000;{_style(_a("vhexp", t_in - .05, .6, "ease-out"))}"></div>'
    return (f'<div class="full" style="overflow:hidden;background:#000">'
            f'<div class="full lay" style="{_style(*moves)}">'
            f'<div class="full lay vjit" style="{_style(_a("vhjit", 0, 1.37, "steps(1,end)", "infinite"))}">'
            f'{pic}{_caption(it, theme)}{expo}{flash}</div></div></div>')


def _jumps(comp: Comp, rnd: random.Random, n: int, dx: int, dy: int) -> str:
    """Keyframes that jump a noise layer to a new place every frame, n frames a
    loop. A short loop (3) looks just as random, and the video encoder, which
    keeps the last 3 frames to copy from, finds each place again for free."""
    name = comp.uid("vj")
    comp.css(f"@keyframes {name}{{" + "".join(
        f"{i * 100 / n:.3f}%{{transform:translate({rnd.randint(-dx, dx)}px,{rnd.randint(-dy, dy)}px)}}"
        for i in range(n)) + "}")
    return _a(name, -.5 / FPS, n / FPS, "steps(1,end)", "infinite")


def _search_bars(comp: Comp, tr: _Tracks, windows: list, rnd: random.Random, up: bool, count: int = 2) -> str:
    """The noise bars of a tape being searched (FF or REW): bands of snow that
    drift through the picture, their noise changing every frame."""
    if not windows:
        return ""
    out = []
    for _ in range(count):
        h = rnd.randint(90, 130)
        y0 = rnd.randint(580, 1330)                  # below the player's lettering
        mv = comp.uid("vsb")
        a, b = (y0 + 70, y0 - 70) if up else (y0 - 70, y0 + 70)
        comp.css(f"@keyframes {mv}{{from{{transform:translateY({a}px)}}to{{transform:translateY({b}px)}}}}")
        out.append(f'<div class="abs lay" style="left:0;top:0;width:{W}px;height:{h}px;overflow:hidden;visibility:hidden;'
                   f'{_style(_a(mv, windows[0][0], 1.0, "linear", "infinite", ) , tr.vis(windows))}">'
                   f'<div class="abs lay" style="left:-100px;top:0;width:1280px;height:{h}px;'
                   f'{_style(_jumps(comp, rnd, 3, 90, 0))}">'
                   f'<canvas class="vhs-noise" data-kind="bar" width="427" height="{h // 2}" '
                   f'style="display:block;width:1280px;height:{h}px"></canvas></div></div>')
    return "".join(out)


def _icon(rows: list, px: int) -> str:
    """A player icon drawn in blocks, with its own hard shadow (no filters)."""
    w = max(x + n for r in rows for x, n in r) * px
    h = len(rows) * px
    rects = lambda dx, dy: "".join(f'<rect x="{x * px + dx}" y="{i * px + dy}" width="{n * px}" height="{px}"/>'
                                   for i, r in enumerate(rows) for x, n in r)
    return (f'<svg width="{w + 3}" height="{h + 3}" style="display:inline-block;vertical-align:baseline;'
            f'margin-left:.18em;overflow:visible"><g fill="rgba(0,0,0,.85)">{rects(3, 3)}</g>'
            f'<g fill="currentColor">{rects(0, 0)}</g></svg>')


PLAY_ROWS = [[(0, n)] for n in (1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1)]
FF_ROWS = [[(0, n), (6, n)] for n in (1, 2, 3, 4, 5, 4, 3, 2, 1)]
REW_ROWS = [[(5 - n, n), (11 - n, n)] for n in (1, 2, 3, 4, 5, 4, 3, 2, 1)]
STOP_ROWS = [[(0, 6)]] * 6
EJECT_ROWS = [[(5 - n, 2 * n - 1)] for n in (1, 2, 3, 4, 5)] + [[(0, 0)]] + [[(0, 9)]] * 2


# ------------------------------------------------------------------ in-page footage and noise

PREP_VHS = r"""
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
  g.filter = 'saturate(.66) brightness(.76) contrast(1.03)';
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
      if ((x % 3) === 0) gs = (rand() + rand() + rand() - 1.5) * 4;
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
      [fw, fh] = contain(art, CFG.ITEM_S, CFG.ITEM_S);
      x = M + P.cx - fw / 2; y = M + CFG.ITEM_Y - fh / 2;
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
  g.save(); g.translate(M + CFG.FIG_X + 30, M + 930); g.scale(760 / 1180, 1);
  const vg = g.createRadialGradient(0, 0, 0, 0, 0, 1298);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(.35, 'rgba(0,0,0,0)');
  vg.addColorStop(.55, 'rgba(0,0,0,.1)'); vg.addColorStop(.75, 'rgba(0,0,0,.3)'); vg.addColorStop(1, 'rgba(0,0,0,.62)');
  g.fillStyle = vg; g.fillRect(-2400, -2400, 4800, 4800); g.restore();
  // a darker lower third under the burned-in captions
  const lo = g.createLinearGradient(0, M + CFG.CAP_Y - 110, 0, M + CFG.CAP_Y + 360);
  lo.addColorStop(0, 'rgba(0,0,0,0)'); lo.addColorStop(.5, 'rgba(0,0,0,.26)'); lo.addColorStop(1, 'rgba(0,0,0,.4)');
  g.fillStyle = lo; g.fillRect(0, M + CFG.CAP_Y - 110, CFG.PW, CFG.PH);
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
  } else if (kind === 'drops') {                  // tape dropouts: short bright dashes, and nothing else
    for (let k = 0; k < 34; k++) {
      const y = Math.floor(rand() * h), x0 = Math.floor(rand() * w), L = 2 + Math.floor(rand() * 14), a = 150 + rand() * 105;
      for (let x = x0; x < Math.min(w, x0 + L); x++) { const j = (y * w + x) * 4; p[j] = p[j + 1] = p[j + 2] = 245; p[j + 3] = a; }
    }
  } else {                                          // snow, or a search bar (snow fading out top and bottom)
    const bar = kind === 'bar';
    for (let y = 0; y < h; y++) {
      const fall = bar ? Math.min(1, Math.sin(Math.PI * (y + .5) / h) * 1.6) : 1;
      for (let x = 0; x < w; x++) {
        const j = (y * w + x) * 4, v = Math.max(0, Math.min(255, (rand() * 255 - 128) * 1.6 + 110));
        p[j] = p[j + 1] = p[j + 2] = v; p[j + 3] = 255 * fall;
      }
    }
    for (let k = 0; k < (bar ? 12 : 60); k++) {
      const y = Math.floor(rand() * h), x0 = Math.floor(rand() * w), L = 3 + Math.floor(rand() * 22);
      for (let x = x0; x < Math.min(w, x0 + L); x++) { const j = (y * w + x) * 4; p[j] = p[j + 1] = p[j + 2] = 250; }
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
  for (const P of CFG.plates) {                     // one bad plate must not cost the others
    try {
      let url;
      try { url = await blob(plate(P, T, P.art >= 0 ? arts[P.art] : null)); }
      catch (e) { console.error('vhs plate', P.k, e); url = await blob(plate(P, T, null)); }
      for (const el of document.querySelectorAll(`img.vhs-plate[data-p="${P.k}"]`)) { el.src = url; jobs.push(ready(el)); }
    } catch (e) { console.error('vhs plate', P.k, e); }
  }
  for (const P of CFG.photos) {
    try {
      const art = P.art >= 0 ? arts[P.art] : null;
      if (!art) continue;
      const url = await blob(photo(P, T, art));
      for (const el of document.querySelectorAll(`img.vhs-photo[data-p="${P.k}"]`)) { el.src = url; jobs.push(ready(el)); }
    } catch (e) { console.error('vhs photo', P.k, e); }
  }
  await Promise.all(jobs);
}
})();</script>
"""


# The player's lettering sits just inside the safe box's top edge, not the
# frame's: the mode (PLAY, FF...) and the tape speed on the left, the channel or
# the counter right-aligned to OSD_R on the right (baselines level), then the
# lime code line and #EpicPartner under them. Everything the blue screens show
# below RAIL_TOP fits the box's column (OSD_FIT wide from x 88).
OSD_X, OSD_Y, OSD_R = SAFE_LEFT + 18, SAFE_TOP + 8, SAFE_RIGHT_TOP - 20     # 78, 238, 1000
CODE_Y, TAG_Y = OSD_Y + 62, OSD_Y + 198                                    # 300, 436
OSD_FIT = SAFE_RIGHT - 20 - 88                                             # 792


def _osd(text: str, x: float, y: float, size: float, anim: str = "", extra: str = "", cls: str = "osd",
         fit: int = 0, attrs: str = "") -> str:
    fit_attr = f' data-fit="{fit}"' if fit else ""
    return (f'<div class="{cls}"{fit_attr}{attrs} style="left:{x:.0f}px;top:{y:.0f}px;font-size:{size:.0f}px;'
            f'{extra}{anim}">{text}</div>')


# ------------------------------------------------------------------ the video

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

    # Each skin's art once; the page script lights it and films it.
    arts, art_idx = [], {}
    for it in group:
        a = ctx.art(it) or ""
        if a and a not in art_idx:
            art_idx[a] = len(arts)
            arts.append(a)
    idx = [art_idx.get(ctx.art(it) or "", -1) for it in group]
    plates = [{"k": k, "art": idx[k], "moon": 1 if k % 2 == 0 else -1, "figure": _is_figure(it),
               "cx": round(FIG_X + (-14 if k % 2 else 14) + rnd.uniform(-8, 8)), "zoom": round(rnd.uniform(1.0, 1.05), 3),
               "fx": round(rnd.uniform(-30, 30)), "fy": round(rnd.uniform(-30, 30)),
               "fogx": round(rnd.uniform(-40, 40)), "cornflip": k % 3 == 1}
              for k, it in enumerate(group)]
    photos = [{"k": j, "art": idx[j], "moon": 1 if j == 0 else -1, "figure": _is_figure(group[j])}
              for j in range(min(2, n))]
    cfg = {"seed": int(ctx.seed) % 2147483647, "PW": PW, "PH": PH, "M": M, "FEET": FEET, "FIG_H": FIG_H,
           "FIG_W": FIG_W, "FIG_X": FIG_X, "ITEM_Y": ITEM_Y, "ITEM_S": ITEM_S, "CAP_Y": CAP_TOPS[0],
           "plates": plates, "photos": photos}
    comp.add('<div style="display:none">'
             f'<img id="vhs-field" src="{tex("vhs-field.jpg")}"><img id="vhs-fog" src="{tex("vhs-fog.jpg")}">'
             f'<img id="vhs-corn" src="{tex("vhs-stalks.jpg")}">'
             + "".join(f'<img class="vhs-art" data-trim data-a="{i}" src="{a}">' for i, a in enumerate(arts))
             + '</div>')

    # ---- the timeline: recording k is on screen from its start to the next cut;
    # the cuts alternate between a tape cut and a fast-forward
    starts = [HOOK + k * R for k in range(n)]
    cuts = starts[1:]
    styles = ["ff" if j % 3 == 1 else "glitch" for j in range(len(cuts))]
    t_rew = content_end
    t_menu = content_end + min(1.3, .16 * n + .1)
    t_eject = dur - 1.2                               # EJECT, and the cassette is back on the desk
    t_land = t_eject + .3
    ff_w = [(tc - .62, tc + .2) for tc, st in zip(cuts, styles) if st == "ff"]
    rew_w, stop_w, eject_w = [(t_rew, t_menu)], [(t_menu, t_eject)], [(t_eject, t_land)]

    # ---- the hook: the desk (frame 0), then the player's blue screen
    title = _label_title(group, theme)
    # what's on the tape, as whoever labelled it wrote it: the first skin and how many more
    names = f"{group[0]['name'].lower()} + {n - 1} more"
    if len(names) > 26:                               # a long name: just how many
        names = f"{n} on this tape"
    ep, of = spec.get("episode"), spec.get("of", 31)
    day_txt = f"DAY {ep} OF {of}" if ep else "THROWBACK"
    part = f"PART {spec['part']}" if spec.get("part") else ""
    comp.add(_layer(tr, [(0, T_CUT), (t_land, dur + 1)], 8, _desk(group, idx, title, names, day_txt, part, t_land)))
    comp.cue(T_LIFT - .05, "tape")
    blue = (f'<div class="full" style="background:{BLUE_BG}"></div>'
            + _osd(f"PLAY{_icon(PLAY_ROWS, 11)}", 84, 660, 170)
            + _osd(esc((theme.get("title") or title).upper()), 88, 904, 106, fit=OSD_FIT)
            + _osd(esc(" · ".join(x for x in ((part or "THROWBACK"), f"DAY {ep} OF {of}" if ep else "") if x)),
                   90, 1034, 62, fit=OSD_FIT)
            + _osd(esc((theme.get("sub") or "HOW MANY DO YOU REMEMBER?").upper()), 90, 1124, 78, fit=OSD_FIT))
    comp.add(_layer(tr, [(T_CUT, T_ROLL + .5)], 2, blue))
    comp.cue(T_CUT, "click")

    # ---- the recordings
    for k, it in enumerate(group):
        t0 = starts[k]
        t_in = T_ROLL if k == 0 else t0
        roll = k == 0 or styles[k - 1] == "glitch"
        glitch_at = cuts[k] if k < n - 1 and styles[k] == "glitch" else None
        t_out = cuts[k] if k < n - 1 else t_rew
        band_t = t0 + rnd.uniform(1.4, 3.6)
        comp.add(_layer(tr, [(t_in, t_out)], 3, _clip(comp, tr, k, it, theme, t0, t_in, roll, glitch_at, band_t, rnd)))
    comp.cue(T_ROLL - .12, "static")
    for tc, st in zip(cuts, styles):
        if st == "glitch":
            comp.cue(tc - .3, "static")
        else:
            comp.cue(tc - .62, "click"); comp.cue(tc - .58, "static"); comp.cue(tc + .2, "click")

    # ---- the end: the tape rewinds through every skin, then the player's menu
    step = (t_menu - t_rew) / n
    rew = "".join(f'<div class="vl" style="{_style(tr.vis([(t_rew + j * step, t_rew + (j + 1) * step)]))}">'
                  f'<div class="full" style="transform:scale(1.06);transform-origin:{CAM_MID}">'
                  f'<img class="plate vhs-plate" data-p="{k}"></div></div>'
                  for j, k in enumerate(reversed(range(n))))
    rew = (f'<div class="full" style="overflow:hidden;background:#000"><div class="full lay" '
           f'style="{_style(_a("vhrew", t_rew, .24, "steps(1,end)", "infinite"))}">{rew}</div></div>')
    comp.add(_layer(tr, rew_w, 6, rew))
    comp.cue(t_rew, "click"); comp.cue(t_rew + .04, "static"); comp.cue(t_rew + .5, "static"); comp.cue(t_menu, "click")

    menu = f'<div class="full" style="background:{BLUE_BG}"></div>' + _osd("WHICH ONE DID YOU OWN?", 80, 556, 96, fit=920)
    pitch = min(96, 640 / n)
    size = min(70, pitch - 12)
    t_list = t_menu + .35
    t_sel = t_list + n * .09 + .9                     # then a cursor walks down the list, again and again
    sel = 1.1
    for j, it in enumerate(group):
        y = 690 + j * pitch
        # (a child's own visibility beats its layer's, so every window ends before the menu does)
        on = [(t_sel + (c * n + j) * sel, t_sel + (c * n + j + 1) * sel) for c in range(int((dur - t_sel) / (n * sel)) + 1)]
        on = [(a, min(b, t_eject)) for a, b in on if a < t_eject - .2]
        name = esc(it["name"].upper())
        row = f"height:{size:.0f}px;display:flex;align-items:center;"      # a shrunk long name stays centred
        menu += (f'<div class="osd" data-fit="{OSD_FIT - 12}" style="left:84px;top:{y:.0f}px;font-size:{size:.0f}px;{row}'
                 f'{_style(_a("lkin", t_list + j * .09, .01, "steps(1,end)"))}">'
                 f'<span style="color:#aab3ff">{j + 1:02d}</span>&nbsp;{name}</div>')
        if on:
            menu += (f'<div class="abs" style="left:70px;top:{y - 8:.0f}px;width:{SAFE_RIGHT - 16 - 70}px;'
                     f'height:{size + 12:.0f}px;'
                     f'background:#f2f2ee;box-shadow:4px 4px 0 rgba(0,0,0,.6);visibility:hidden;{_style(tr.vis(on))}">'
                     f'<div class="osd" data-fit="{OSD_FIT - 12}" style="left:14px;top:6px;font-size:{size:.0f}px;{row}'
                     f'color:#1c2ca6;'
                     f'text-shadow:none"><span style="color:#5563d6">{j + 1:02d}</span>&nbsp;{name}</div></div>')
    comp.add(_layer(tr, stop_w + eject_w, 7, menu))
    comp.cue(t_eject, "click"); comp.cue(t_land - .05, "tape")

    # ---- the tape over everything from the first blue frame: dropouts, snow at
    # the cuts, search bars when it winds, scanlines and a CRT's dark corners, a
    # flicker. (Fine grain that changes every frame would triple the file size and
    # the encoding time: the picture carries its own still grain instead.)
    snow_pts = [(0, 0), (T_ROLL - .1, 1), (T_ROLL + .04, 0)]
    for tc, st in zip(cuts, styles):
        if st == "glitch":           # the picture tears, a burst of snow, the next recording rolls in
            snow_pts += [(tc - .1, 1), (tc + .04, 0)]
        else:                        # searching: the bars do the work, a touch of snow as it lands
            snow_pts += [(tc - .04, .5), (tc + .04, 0)]
    snow_pts += [(t_rew - .04, .6), (t_rew + .04, 0), (t_menu - .1, 1), (t_menu, 0)]
    tape = (f'<div class="abs lay" style="left:-100px;top:-100px;width:1280px;height:2120px;'
            f'{_style(_jumps(comp, rnd, 3, 90, 90))}"><canvas class="vhs-noise" data-kind="drops" width="640" '
            f'height="1060" style="display:block;width:1280px;height:2120px"></canvas></div>'
            f'<div class="full fade" style="opacity:0;{_style(tr.levels(snow_pts))}"><div class="abs lay" '
            f'style="left:-100px;top:-100px;width:1280px;height:2120px;{_style(_jumps(comp, rnd, 3, 90, 90))}">'
            f'<canvas class="vhs-noise" data-kind="snow" width="256" height="530" '
            f'style="display:block;width:1280px;height:2120px"></canvas></div></div>'
            + _search_bars(comp, tr, ff_w, rnd, up=False, count=2)
            + _search_bars(comp, tr, rew_w, rnd, up=True, count=3)
            + f'<div class="crt"></div>'
              f'<div class="full fade vflick" style="background:#fff8e8;{_style(_a("vhflick", 0, .9, "steps(1,end)", "infinite"))}">'
              f'</div>')
    comp.add(_layer(tr, [(T_CUT, t_land)], 20, tape, "pointer-events:none;"))

    # ---- the player's lettering, crisp on top
    play_w = _minus((T_ROLL, t_land), ff_w + rew_w + stop_w + eject_w)
    vis = lambda w: _style(tr.vis(w)) + "visibility:hidden;" if w else "visibility:hidden;"
    right = f"right:{W - OSD_R}px;left:auto;"
    osd = (_osd(f"PLAY{_icon(PLAY_ROWS, 5)}", OSD_X, OSD_Y, 80, vis(play_w))
           + _osd(f"FF{_icon(FF_ROWS, 6)}", OSD_X, OSD_Y, 80, vis(ff_w))
           + _osd(f"REW{_icon(REW_ROWS, 6)}", OSD_X, OSD_Y, 80, vis(rew_w))
           + _osd(f"STOP{_icon(STOP_ROWS, 8)}", OSD_X, OSD_Y, 80, vis(stop_w))
           + _osd(f"EJECT{_icon(EJECT_ROWS, 6)}", OSD_X, OSD_Y, 80, vis(eject_w))
           + _osd("SP", OSD_X + 240, OSD_Y + 14, 64, vis([(T_ROLL, t_menu)]))
           + _osd("CH 03", 0, OSD_Y + 14, 64, vis([(T_CUT, T_ROLL)]), right)
           + "".join(_osd(f"{k + 1}/{n}", 0, OSD_Y + 14, 64,
                          vis([(starts[k] if k else T_ROLL, cuts[k] if k < n - 1 else t_rew)]), right) for k in range(n))
           + _osd("USE CODE: BAD", OSD_X - 6, CODE_Y, 144, cls="osd codeline", attrs=' data-safe="key" data-name="code"')
           + _osd("#EpicPartner", OSD_X + 2, TAG_Y, 48))
    comp.add(_layer(tr, [(T_CUT, t_land)], 30, osd, "pointer-events:none;"))

    comp.add(PREP_JS)
    comp.add(PREP_VHS.replace("__CFG__", json.dumps(cfg)))
    comp.cues.sort()
    return comp
