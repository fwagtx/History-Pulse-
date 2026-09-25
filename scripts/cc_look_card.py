"""
CARD -- Who's That Skin?, as LOCKER LEGENDS trading cards on a felt playmat,
shot from above.

    0:00  hook     the playmat, complete on frame 0: the first three cards fanned
                   out, each a black silhouette with its name taped over, a
                   sticky note WHO'S THAT SKIN? (quiz number, N rounds, 4 choices
                   each), and the lime USE CODE: BAD token. The fan gathers into
                   the first card.
    0:03  rounds   one per round (9.5 s, as the classic): a card is dealt, a fresh
                   note goes on the pad, four sticky notes A-D carry the names.
                   A hold, then 3... 2... 1... in red marker on the note, a second
                   apart; the card flips (the LOCKER LEGENDS back shows in the
                   air) and lands revealed -- name, colours, set and season -- the
                   right note is circled and ticked in red, the others get a
                   pencil line. Then the notes are peeled off and the card goes.
    ~1:00 outro    every card of the video laid out face up, and the classic's
                   question on a fresh note: how many did you get out of 6?

Facts come only from the item: rarity and type (on the card from the start),
and after the flip its name, set and season (it["set"], it["season_label"]).
No invented stats. The options and the answer are the plan's. Silhouettes stay
black and names stay taped over until each reveal. The lime token is on screen
in every frame.

Render cost: the renderer keeps every animation paused, and Chrome gives each
paused-but-unfinished transform/opacity/filter animation its own compositing
layer, so swaps are done with visibility and shading with colour, and nothing
full-frame moves for the whole video.
"""

import math

from cc_looks import (KIT_CSS, LIME, PREP_JS, pad_to, rough_check, rough_ellipse, rough_line, stroke_static,
                      stroke_svg, tex, write_on)
from cc_motion import RARITY, Comp, esc

HOOK = 3.0
R1 = 9.5                        # one round, as the classic (cc_quiz.R1)
FONTS = ("Caveat", "Playfair Display", "Barlow Condensed", "Permanent Marker")
MARK = "#c8261f"                # red marker
PENCIL = "#4b463f"

# Where things sit (safe area y 190-1480; below y 880 nothing right of x 960).
CARD_X, CARD_Y, CARD_W, CARD_H = 40, 552, 580, 812
NOTE_X, NOTE_Y, NOTE_W, NOTE_H, NOTE_STEP = 648, 552, 298, 186, 209
PAD_X, PAD_Y, PAD_W, PAD_H = 40, 206, 364, 304          # the note pad: title + countdown
TOKEN_X, TOKEN_Y, TOKEN_D = 668, 208, 290

# Beats inside a round, seconds from its start.
T_DEAL = -.32                   # the card slides in from below ...
DEAL = .6                       # ... and has landed at T_DEAL + DEAL
T_NOTE = .1                     # a fresh note on the pad
T_OPT = .45                     # the four options, one after another
T_CD = 3.3                      # 3... 2... 1..., a second apart
T_FLIP, FLIP_D = 5.45, 1.45     # the card flips; its face is back round at ~T_REV
T_REV = 6.3
T_OUT = 9.0                     # notes peeled off, card cleared

NOTE_COLS = ("#fde978", "#f9c1cc", "#bfe0f3", "#fcd2a4")    # yellow, pink, blue, peach


def _a(name, t, dur, ease="linear", extra=""):
    return f"animation:{name} {dur:.3f}s {ease} {t:.3f}s 1 normal both;{extra}"


def _mix(hex_: str, other: str, k: float) -> str:
    a = [int(hex_[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * k):02x}" for x, y in zip(a, b))


def _svg_box(svg: str, w: float, h: float) -> str:
    """The kit's stroke SVGs are frame-sized; inside a note that makes the
    note's layer frame-sized too. Size them to the note (strokes may still
    overflow a little: overflow is visible)."""
    return svg.replace('width="1080" height="1920" viewBox="0 0 1080 1920"',
                       f'width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}"')


def _words(text: str) -> str:
    """Escaped text whose hyphenated words never break at the hyphen."""
    return " ".join(f'<span style="white-space:nowrap">{esc(w)}</span>' if "-" in w else esc(w)
                    for w in text.split(" "))


def _base(it: dict) -> str:
    c = RARITY.get(it.get("rarity"), "#9AA0A6")
    return c if c.startswith("#") and len(c) == 7 else "#9AA0A6"


# ---------------------------------------------------------------- the flip

def _smr(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def _io(x):
    x = min(1.0, max(0.0, x))
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


LIFT = 120


def _flip_state(u):
    """u in [0, 1] -> (angle deg, lift px, extra rotateZ deg, tx, ty): a small
    wind-up, one full turn in the air, a landing on one edge that settles flat."""
    if u < .14:
        ang = -12 * math.sin(math.pi / 2 * u / .14)
    elif u < .80:
        ang = -12 + 378 * _io((u - .14) / .66)
    else:
        ang = 366 - 6 * _smr((u - .80) / .20)
    if u < .82:
        lift = LIFT * math.sin(math.pi * u / .82) ** .85
    else:
        lift = 8 * math.sin(math.pi * min(1, (u - .82) / .12))
    k = _smr((u - .08) / .80)
    return ang, lift, 3.2 * k, 5 * k, -8 * k


def _t_angle(deg):
    for i in range(4001):
        if _flip_state(i / 4000)[0] >= deg:
            return i / 4000 * FLIP_D
    return FLIP_D


def _kf(name, fn, steps=48):
    return f"@keyframes {name}{{" + "".join(f"{i / steps * 100:.2f}%{{{fn(i / steps)}}}" for i in range(steps + 1)) + "}"


def _flip_css() -> str:
    def card(u):
        a, l, rz, tx, ty = _flip_state(u)
        return (f"transform:translate3d({tx:.1f}px,{ty:.1f}px,{l:.1f}px) rotateZ({rz:.2f}deg) "
                f"scale3d(1,1,.55) rotateY({a:.2f}deg)")

    def shadow(u):
        a, l, rz, tx, ty = _flip_state(u)
        c = max(.04, abs(math.cos(math.radians(a))))
        g = 1 + l * .0012
        return (f"transform:translate({tx + l * .32:.1f}px,{ty + l * .45:.1f}px) rotateZ({rz:.2f}deg) "
                f"scale({c * g:.3f},{g:.3f});opacity:{1 - l * .0035:.3f}")

    def shade(u):
        a = _flip_state(u)[0]
        return f"background-color:rgba(11,9,6,{.55 * abs(math.sin(math.radians(a))) ** 1.4:.3f})"

    return "\n".join([_kf("cdflip", card), _kf("cdshadow", shadow), _kf("cdshade", shade)])


T_SWAP = _t_angle(180)          # the face swaps (quiz -> revealed) while the back shows


# ---------------------------------------------------------------- CSS

CSS = """
.cd-cam{position:absolute;inset:0}
.cd-mat{position:absolute;left:-60px;top:-70px;width:1200px;height:1860px;border-radius:0 0 34px 34px;
  background:radial-gradient(ellipse 760px 900px at 470px 900px,rgba(255,226,170,.20),rgba(255,226,170,.06) 55%,rgba(255,226,170,0) 80%),
    radial-gradient(ellipse 1000px 1250px at 520px 880px,rgba(0,0,0,0) 42%,rgba(0,0,0,.5) 100%),
    url('@felt@') center/cover;box-shadow:0 5px 0 #0d1715,0 9px 12px rgba(0,0,0,.55)}
.cd-mat::before{content:"";position:absolute;left:14px;right:14px;bottom:14px;height:100%;border-radius:0 0 24px 24px;
  border:3px dashed rgba(206,226,214,.18);border-top:0}
.cd-wood{position:absolute;left:-60px;top:1760px;width:1200px;height:260px;background:url('@wood@') center/cover}
.cd-wood::after{content:"";position:absolute;inset:0;background:linear-gradient(rgba(16,8,3,.78),rgba(16,8,3,.55) 35%,rgba(8,4,2,.7))}
.cd-grain{position:absolute;inset:0;pointer-events:none;background:url('@grain@') 0 0/256px 256px;opacity:.06}
.cd-vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 85% 64% at 48% 50%,rgba(0,0,0,0) 58%,rgba(0,0,0,.34) 100%)}

/* sticky notes */
.cd-note{position:absolute;inset:0;border-radius:2px 2px 6px 3px;background-image:var(--g),url('@paper@');
  background-size:auto,cover;background-position:center;background-blend-mode:multiply;
  box-shadow:0 1px 1px rgba(0,0,0,.25),0 16px 16px -9px rgba(0,0,0,.5)}
.cd-note::after{content:"";position:absolute;inset:0;border-radius:inherit;
  background:linear-gradient(160deg,rgba(255,255,255,.2),rgba(255,255,255,0) 40%,rgba(0,0,0,0) 70%,rgba(80,60,0,.10))}
.cd-hand{font-family:'Caveat',cursive;font-weight:700;color:#1d1b18;line-height:.92}
.cd-mark{font-family:'Permanent Marker',cursive;color:#1d1b18;line-height:1}

/* the token */
.cd-token{position:absolute;border-radius:50%;transform:rotate(6deg);
  background:radial-gradient(circle at 34% 28%,#f3ff86,@LIME@ 46%,@LIME@ 80%,#d9f02f);
  box-shadow:inset 0 0 0 9px #111,inset 0 0 0 14px @LIME@,inset 0 0 0 16px #111,
    inset -3px -5px 7px rgba(0,0,0,.20),inset 3px 4px 5px rgba(255,255,255,.55),
    0 2px 1px rgba(0,0,0,.5),0 6px 4px rgba(0,0,0,.28),0 20px 22px -6px rgba(0,0,0,.55);
  display:flex;flex-direction:column;align-items:center;justify-content:center;color:#111}
.cd-token .a{font-family:'Barlow Condensed';font-weight:800;font-size:41px;line-height:1;letter-spacing:.08em;margin:14px 0 -10px .08em}
.cd-token .b{font-family:'Barlow Condensed';font-weight:800;font-size:128px;line-height:1;letter-spacing:.03em;margin-left:.03em}
.cd-token .c{font-family:'Barlow Condensed';font-weight:600;font-size:20px;letter-spacing:.06em;margin-top:-12px}

/* the card */
.cd-persp{position:absolute;inset:0;perspective:2400px}
.cd-card{position:absolute;transform-style:preserve-3d}
.cd-face{position:absolute;inset:0;border-radius:28px;overflow:hidden;backface-visibility:hidden;-webkit-backface-visibility:hidden}
.cd-back{transform:rotateY(180deg)}
.cd-inner{position:absolute;left:22px;top:22px;right:22px;bottom:22px;border-radius:13px;
  background:linear-gradient(#f6ecd6,#efe2c4),url('@paper@') center/cover;background-blend-mode:multiply;
  box-shadow:inset 0 0 0 2px rgba(120,70,20,.45),0 0 0 2px rgba(255,236,190,.5),0 3px 6px rgba(60,30,10,.35)}
.cd-namebar{position:absolute;left:10px;top:10px;right:10px;height:74px;border-radius:9px;
  background:linear-gradient(#fbf4e2,#f1e3c2);box-shadow:inset 0 0 0 2px rgba(135,82,28,.4),inset 0 -8px 12px rgba(160,100,30,.10)}
.cd-namebox{position:absolute;left:20px;top:0;bottom:0;display:flex;align-items:center}
.cd-name{font-family:'Playfair Display';font-weight:900;font-size:54px;line-height:1.0;color:#22170e;letter-spacing:.02em}
.cd-gem{position:absolute;right:24px;top:24px;width:26px;height:26px;transform:rotate(45deg);border-radius:4px}
.cd-tape{position:absolute;left:6px;top:6px;width:330px;height:64px;transform:rotate(-1.6deg);
  background:linear-gradient(rgba(240,226,184,.97),rgba(228,210,164,.97)),url('@paper@') center/cover;
  background-blend-mode:multiply;box-shadow:0 1px 2px rgba(60,40,0,.25);
  clip-path:polygon(0 8%,3% 0,7% 6%,10% 0,100% 0,97% 18%,100% 36%,97% 55%,100% 74%,97% 100%,0 100%,3% 86%,0 70%,3% 52%,0 34%);
  font-family:'Caveat';font-weight:700;font-size:64px;line-height:66px;color:#1d1b18;padding-left:30px;letter-spacing:.1em}
.cd-window{position:absolute;left:10px;top:96px;right:10px;height:436px;border-radius:7px;overflow:hidden}
.cd-winshade{position:absolute;inset:0;box-shadow:inset 0 0 28px rgba(40,20,5,.4),inset 0 10px 14px -8px rgba(30,15,0,.45)}
.cd-type{position:absolute;left:10px;right:10px;top:544px;height:46px;border-radius:7px;
  font-family:'Barlow Condensed';font-weight:800;font-size:26px;letter-spacing:.12em;color:#2e1d0c;
  display:flex;align-items:center;padding-left:18px;white-space:nowrap}
.cd-stats{position:absolute;left:10px;right:10px;top:602px;height:106px;border-radius:7px;
  background:rgba(255,250,236,.55);box-shadow:inset 0 0 0 2px rgba(135,82,28,.3);padding:4px 18px}
.cd-row{position:relative;height:49px;display:flex;align-items:center;gap:12px;
  border-bottom:1.5px solid rgba(135,82,28,.2);font-family:'Barlow Condensed'}
.cd-row:last-child{border-bottom:0}
.cd-k{font-weight:600;font-size:27px;color:#7a5530;white-space:nowrap}
.cd-v{font-weight:800;font-size:31px;color:#22170e;white-space:nowrap}
.cd-blank{position:absolute;right:6px;bottom:12px;width:230px;border-bottom:3px dotted rgba(122,68,20,.5)}
.cd-foot{position:absolute;left:0;right:0;bottom:26px;text-align:center;font-family:'Barlow Condensed';font-weight:600;
  font-size:18px;letter-spacing:.2em;color:rgba(40,22,8,.8)}
.cd-foot b{font-weight:800}
.cd-shade{position:absolute;inset:0;background-color:rgba(11,9,6,0)}
.cd-edge{position:absolute;inset:0;border-radius:28px;box-shadow:inset 0 0 0 1.5px rgba(255,244,220,.55)}
.cd-bk{position:absolute;inset:0;background:
  repeating-linear-gradient(45deg,rgba(222,178,98,.16) 0 2px,rgba(0,0,0,0) 2px 26px),
  repeating-linear-gradient(-45deg,rgba(222,178,98,.16) 0 2px,rgba(0,0,0,0) 2px 26px),
  radial-gradient(ellipse at 50% 42%,#2a3b63,#141d33 78%)}
.cd-bkline{position:absolute;inset:22px;border-radius:15px;box-shadow:inset 0 0 0 2px rgba(226,184,104,.75),0 0 0 8px #0f1626,0 0 0 10px rgba(226,184,104,.4)}
.cd-oval{position:absolute;left:66px;top:230px;width:428px;height:300px;border-radius:50%;
  background:radial-gradient(ellipse at 50% 40%,#f7eed8,#eadcb8);
  box-shadow:0 0 0 7px #141d33,0 0 0 10px #d9ad5c,0 0 0 18px rgba(20,29,51,.9),0 0 0 20px rgba(217,173,92,.6);
  display:flex;flex-direction:column;align-items:center;justify-content:center;color:#16213a}
.cd-oval .l2{font-family:'Playfair Display';font-weight:900;font-size:70px;line-height:.92;letter-spacing:.02em}
.cd-orn{position:relative;width:200px;height:2px;margin:14px 0;
  background:linear-gradient(90deg,rgba(155,107,34,0),#9b6b22 30%,#9b6b22 70%,rgba(155,107,34,0))}
.cd-orn i{position:absolute;left:93px;top:-6px;width:14px;height:14px;transform:rotate(45deg);background:#b98530}
.cd-seal{position:absolute;left:220px;top:600px;width:120px;height:120px;
  background:radial-gradient(circle at 40% 35%,#f4d58e,#d49d3f 60%,#a8741f);
  display:flex;flex-direction:column;align-items:center;justify-content:center;color:#16213a}
.cd-seal .s1{font-family:'Barlow Condensed';font-weight:800;font-size:17px;letter-spacing:.25em;margin:0 0 -4px .25em}
.cd-seal .s2{font-family:'Playfair Display';font-weight:900;font-size:40px;line-height:1}
.cd-shd{position:absolute;border-radius:30px;background:rgba(3,8,6,.55);
  box-shadow:0 0 22px 10px rgba(3,8,6,.45),0 0 60px 22px rgba(3,8,6,.22)}

@keyframes cddeal{0%{transform:translate(-70px,1260px) rotate(-13deg)}
  78%{transform:translate(2px,-7px) rotate(.7deg)}100%{transform:none}}
@keyframes cdclear{to{transform:translate(-1150px,140px) rotate(-17deg)}}
@keyframes cdpeel{0%{transform:rotate(var(--r))}25%{transform:translate(4px,-16px) rotate(calc(var(--r) + 3deg))}
  100%{transform:translate(880px,-260px) rotate(calc(var(--r) + 34deg))}}
@keyframes cdoff{from{visibility:visible}to{visibility:hidden}}
@keyframes cdon{from{visibility:hidden}to{visibility:visible}}
@keyframes cdsil{from{filter:brightness(0)}to{filter:none}}
@keyframes cdspread{from{transform:rotate(var(--r))}to{transform:translate(var(--dx),var(--dy)) rotate(var(--r2))}}
@keyframes cdgather{from{transform:translate(var(--dx),var(--dy)) rotate(var(--r2))}
  to{transform:translate(-120px,1250px) rotate(-8deg)}}
@keyframes cdfan{0%{opacity:0;transform:translate(-40px,900px) rotate(calc(var(--r) - 10deg))}
  70%{opacity:1;transform:translate(0,-5px) rotate(calc(var(--r) + .6deg))}100%{opacity:1;transform:rotate(var(--r))}}
"""


# ---------------------------------------------------------------- pieces

def _token() -> str:
    return (f'<div class="cd-token" style="left:{TOKEN_X}px;top:{TOKEN_Y}px;width:{TOKEN_D}px;height:{TOKEN_D}px">'
            f'<div class="a">USE CODE:</div><div class="b">BAD</div><div class="c">#EpicPartner</div></div>')


def _note_bg(color: str) -> str:
    """A note's colour; the paper under it comes from .cd-note, once for the page."""
    return (f"--g:linear-gradient(174deg,{_mix(color, '#ffffff', .25)} 0%,{color} 50%,"
            f"{_mix(color, '#000000', .06)} 100%);")


def _card_face(ctx, it: dict, k: int, n: int, t_swap=None, art_img=True) -> str:
    """The front of a card. t_swap=None: already revealed. Otherwise the quiz
    face (silhouette, name taped over, blanks) swaps for the revealed one at
    t_swap, while the back is showing."""
    base = _base(it)
    hi, lo = _mix(base, "#ffffff", .5), _mix(base, "#000000", .3)
    border = (f"repeating-linear-gradient(115deg,rgba(255,255,255,.06) 0 2px,rgba(255,255,255,0) 2px 6px),"
              f"linear-gradient(140deg,{hi} 0%,{_mix(base, '#ffffff', .25)} 22%,{base} 48%,"
              f"{_mix(base, '#ffffff', .18)} 72%,{lo} 100%)")
    tint = _mix(base, "#ffffff", .62)
    pat = _mix(base, "#000000", .15)
    window = (f"background:radial-gradient(ellipse 70% 62% at 50% 42%,rgba(255,250,236,.72),rgba(255,250,236,0) 70%),"
              f"radial-gradient(circle at 50% 100%,rgba(0,0,0,0) 47%,{pat}44 49%,{pat}44 55%,rgba(0,0,0,0) 57%) 0 0/56px 28px,"
              f"radial-gradient(circle at 50% 100%,rgba(0,0,0,0) 47%,{pat}44 49%,{pat}44 55%,rgba(0,0,0,0) 57%) 28px 14px/56px 28px,"
              f"linear-gradient({tint},{_mix(base, '#ffffff', .45)})")
    q = r = ""
    never = t_swap == "never"             # the quiz face for good (the hook's fan)
    if never:
        r = 'style="display:none"'
    elif t_swap is not None:
        q = f'style="{_a("cdoff", t_swap, .01, "steps(1,end)")}"'
        r = f'style="{_a("cdon", t_swap, .01, "steps(1,end)")}"'
    kind = f"{it.get('rarity_label') or ''} {it.get('type') or ''}".strip().upper()
    name = esc(it["name"])
    nw = CARD_W - 44 - 20 - 84          # the name bar, less the gem
    # One line, shrunk to fit -- unless that would go below ~32 px: then two
    # balanced lines (Playfair 900 averages about .56 em a letter).
    est = len(it["name"]) * .56 * 54
    if est <= nw or 54 * nw / est >= 32:
        name_el = f'<div class="cd-name" data-fit="{nw}" style="white-space:nowrap">{name}</div>'
    else:
        name_el = (f'<div class="cd-name" data-fit="{nw}" data-lines="2" style="width:{nw}px;font-size:36px;'
                   f'text-wrap:balance">{_words(it["name"])}</div>')
    art = ctx.art(it) if art_img else ""
    iw, ih = CARD_W - 44 - 20, 436
    if art:
        sil = ("filter:brightness(0);" if never else
               _a("cdsil", t_swap, .01, "steps(1,end)") if t_swap is not None else "")
        pic = (f'<div class="abs" style="left:0;top:0;width:{iw}px;height:{ih}px;{sil}">'
               f'<img data-trim src="{art}" style="position:absolute;left:14px;top:12px;width:{iw - 28}px;'
               f'height:{ih - 12}px;object-fit:contain"></div>')
    else:
        # No picture: a marker question mark where the silhouette would be,
        # and once it's revealed a big printed initial, like a monogram.
        qa = _a("cdoff", t_swap, .01, "steps(1,end)") if (t_swap is not None and not never) else ""
        ra = ("display:none;" if never else
              _a("cdon", t_swap, .01, "steps(1,end)") if t_swap is not None else "")
        box = f"left:0;top:0;width:{iw}px;height:{ih}px;display:flex;align-items:center;justify-content:center;"
        initial = next((c for c in it["name"] if c.isalnum()), "?").upper()
        pic = ""
        if t_swap is not None:
            pic += (f'<div class="abs cd-mark" style="{box}font-size:260px;color:rgba(20,14,8,.85);{qa}">?</div>')
        pic += (f'<div class="abs" style="{box}{ra}"><div style="font-family:\'Playfair Display\';font-weight:900;'
                f'font-size:300px;line-height:1;color:{_mix(base, "#000000", .45)};opacity:.55">{esc(initial)}</div>'
                f'</div>')
    set_ = it.get("set") or ""
    season = it.get("season_label") or ""
    rows = [("Set:", esc(set_) if set_ else "&mdash;"), ("Introduced:", esc(season) if season else "&mdash;")]
    stats = "".join(
        f'<div class="cd-row"><span class="cd-k">{kk}</span>'
        f'<span class="cd-v" {r} data-fit="{CARD_W - 44 - 20 - 36 - 150}">{vv}</span>'
        + (f'<span class="cd-blank" {q}></span>' if t_swap is not None else "") + '</div>' for kk, vv in rows)
    tape = f'<div class="cd-tape" {q}>???</div>' if t_swap is not None else ""
    return (f'<div class="abs" style="inset:0;background:{border}"></div>'
            f'<div class="cd-inner">'
            f'<div class="cd-namebar"><div class="cd-namebox" {r}>{name_el}</div>'
            f'<div class="cd-gem" style="background:linear-gradient(135deg,{hi},{base} 55%,{lo});'
            f'box-shadow:0 0 0 2px {lo}88"></div>{tape}</div>'
            f'<div class="cd-window" style="{window}">{pic}<div class="cd-winshade"></div></div>'
            f'<div class="cd-type" style="background:linear-gradient({_mix(base, "#ffffff", .55)},'
            f'{_mix(base, "#ffffff", .35)});box-shadow:inset 0 0 0 2px {lo}88"><span data-fit="{CARD_W - 44 - 20 - 36}" '
            f'style="white-space:nowrap">{esc(kind)}</span></div>'
            f'<div class="cd-stats">{stats}</div></div>'
            f'<div class="cd-foot">LOCKER LEGENDS · {k} / {n} · <b>CODE BAD</b></div>'
            f'<div class="cd-edge"></div>')


def _card_back() -> str:
    return ('<div class="cd-bk"></div><div class="cd-bkline"></div>'
            '<div class="cd-oval"><div class="cd-orn"><i></i></div><div class="l2">LOCKER</div>'
            '<div class="l2">LEGENDS</div><div class="cd-orn"><i></i></div></div>'
            '<div class="cd-seal" style="clip-path:polygon(' + _seal() + ')"><div class="s1">CODE</div>'
            '<div class="s2">BAD</div></div><div class="cd-edge"></div>')


def _seal(n=36, r1=50, r2=45.5) -> str:
    pts = []
    for i in range(n * 2):
        rr = r1 if i % 2 == 0 else r2
        a = math.pi * i / n
        pts.append(f"{50 + rr * math.cos(a):.2f}% {50 + rr * math.sin(a):.2f}%")
    return ",".join(pts)


def _card(ctx, it: dict, k: int, n: int, t0: float, rot: float, deal: bool, t_out: float) -> str:
    """One round's card: dealt in (unless it's already on the table), flipped
    at t0 + T_FLIP, cleared away at t_out."""
    t_flip = t0 + T_FLIP
    t_swap = t_flip + T_SWAP
    x, y, w, h = CARD_X, CARD_Y, CARD_W, CARD_H
    move = []
    if deal:
        move.append(f"cddeal {DEAL:.3f}s cubic-bezier(.2,.75,.3,1) {t0 + T_DEAL:.3f}s 1 normal both")
    move.append(f"cdclear .5s cubic-bezier(.55,0,.85,.35) {t_out:.3f}s 1 normal forwards")
    front = _card_face(ctx, it, k, n, t_swap)
    return (f'<div class="abs" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;animation:{",".join(move)}">'
            f'<div class="abs" style="left:{w / 2:.0f}px;top:{h / 2:.0f}px;width:0;height:0;transform:rotate({rot}deg)">'
            f'<div class="cd-shd" style="left:{-w / 2 + 14:.0f}px;top:{-h / 2 + 18:.0f}px;width:{w - 28}px;height:{h - 30}px;'
            f'{_a("cdshadow", t_flip, FLIP_D)}"></div></div>'
            f'<div class="cd-persp" style="perspective-origin:{w / 2:.0f}px {h / 2:.0f}px">'
            f'<div class="cd-card" style="left:0;top:0;width:{w}px;height:{h}px;transform:rotate({rot}deg)">'
            f'<div class="cd-card" style="left:0;top:0;width:{w}px;height:{h}px;{_a("cdflip", t_flip, FLIP_D)}">'
            f'<div class="cd-face">{front}<div class="cd-shade" style="{_a("cdshade", t_flip, FLIP_D)}"></div></div>'
            f'<div class="cd-face cd-back">{_card_back()}<div class="cd-shade" style="{_a("cdshade", t_flip, FLIP_D)}"></div></div>'
            f'</div></div></div></div>')


def _flat_card(ctx, it: dict, k: int, n: int, cx: float, cy: float, scale: float, rot: float, anim: str,
               revealed: bool) -> str:
    """A card lying still (the hook's fan, the outro's spread)."""
    w, h = CARD_W, CARD_H
    face = _card_face(ctx, it, k, n, None if revealed else "never")
    return (f'<div class="abs" style="left:{cx:.0f}px;top:{cy:.0f}px;width:0;height:0;--r:{rot}deg;'
            f'transform:rotate({rot}deg);{anim}">'
            f'<div class="abs" style="left:{-w / 2:.0f}px;top:{-h / 2:.0f}px;width:{w}px;height:{h}px;'
            f'transform:scale({scale})">'
            f'<div class="cd-shd" style="left:14px;top:22px;width:{w - 28}px;height:{h - 30}px"></div>'
            f'<div class="cd-face" style="position:absolute;inset:0">{face}</div></div></div>')


def _pad_note(t_in, lines: str, corner: str, rot: float) -> str:
    """A note on the pad (top left). t_in=None: there from frame 0."""
    anim = _a("lkslap", t_in, .5, "cubic-bezier(.2,.9,.25,1)") if t_in is not None else ""
    return (f'<div class="abs" style="left:{PAD_X}px;top:{PAD_Y}px;width:{PAD_W}px;height:{PAD_H}px;'
            f'--r:{rot}deg;transform:rotate({rot}deg);{anim}">'
            f'<div class="cd-note" style="{_note_bg(NOTE_COLS[0])}"></div>'
            f'<div class="abs cd-hand" style="left:24px;top:22px;font-size:70px;line-height:.9;transform:rotate(-1.5deg);'
            f'white-space:nowrap">WHO\'S THAT<br>SKIN?</div>'
            f'<div class="abs cd-hand" style="left:200px;top:98px;font-size:42px;font-weight:600;color:{PENCIL};'
            f'transform:rotate(-4deg);white-space:nowrap">{corner}</div>{lines}</div>')


def _countdown(t: float) -> str:
    """3... 2... 1..., written in red on the note a second apart."""
    out = []
    for j, s in enumerate(("3…", "2…", "1…")):
        out.append(f'<span style="display:inline-block;margin-right:12px;{write_on(t + j, .26, 8)}">{s}</span>')
    return (f'<div class="abs cd-hand" style="left:24px;top:168px;font-size:100px;line-height:1;color:{MARK};'
            f'transform:rotate(-3deg);white-space:nowrap;letter-spacing:-.02em">{"".join(out)}</div>')


def _options(opts: list, answer: int, t0: float, t_out: float) -> tuple:
    """Four sticky notes, A-D, slapped on one after another. On the reveal the
    right one is circled and ticked in red; the others get a pencil line.
    Returns (html, sounds)."""
    html, sounds = [], []
    t_rev = t0 + T_REV
    rnd = (int(t0 * 10) * 7919) % 1000
    for j, text in enumerate(opts):
        jit = ((rnd * (j + 3) * 37) % 100) / 100
        x, y = NOTE_X + (jit - .5) * 14, NOTE_Y + j * NOTE_STEP + (jit - .5) * 6
        rot = (1.2 + 1.6 * jit) * (1 if (j + rnd) % 2 else -1)
        t_in = t0 + T_OPT + j * .09
        col = NOTE_COLS[j]
        right = j == answer
        marks = ""
        if right:
            marks = stroke_svg([rough_ellipse(NOTE_W / 2 + 6, NOTE_H / 2 + 2, NOTE_W / 2 - 16, NOTE_H / 2 - 20,
                                              seed=int(t0 * 7) + j, overshoot=.14)], MARK, 7, t_rev + .15, .42)
            marks += stroke_svg(rough_check(NOTE_W - 78, NOTE_H - 30, 52, seed=j + 3), MARK, 8, t_rev + .62, .22)
        else:
            marks = stroke_svg([rough_line(84, NOTE_H * .58, NOTE_W - 30, NOTE_H * .5, seed=j + int(t0), bow=.02)],
                               PENCIL, 4, t_rev + .9 + j * .06, .16, opacity=.8)
        html.append(
            f'<div class="abs" style="left:{x}px;top:{y}px;width:{NOTE_W}px;height:{NOTE_H}px;--r:{rot}deg;'
            f'transform:rotate({rot}deg);animation:lkslap .45s cubic-bezier(.2,.9,.25,1) {t_in:.3f}s 1 normal both,'
            f'cdpeel .42s cubic-bezier(.5,0,.85,.4) {t_out + j * .05:.3f}s 1 normal forwards">'
            f'<div class="cd-note" style="{_note_bg(col)}"></div>'
            f'<div class="abs cd-mark" style="left:18px;top:14px;width:58px;height:58px;font-size:40px;display:flex;'
            f'align-items:center;justify-content:center">{"ABCD"[j]}</div>'
            + _svg_box(stroke_static([rough_ellipse(47, 43, 27, 25, seed=j + 11, overshoot=.12, wobble=.06)],
                                     "#1d1b18", 4, .85), NOTE_W, NOTE_H) +
            f'<div class="abs cd-hand" data-fit="{NOTE_W - 40}" data-lines="2" style="left:22px;top:76px;'
            f'width:{NOTE_W - 40}px;font-size:50px;line-height:.95;text-wrap:balance">{_words(text)}</div>'
            f'{_svg_box(marks, NOTE_W, NOTE_H)}</div>')
        sounds.append((t_in, "paper"))
    return "".join(html), sounds


# ---------------------------------------------------------------- build

def whos_that(ctx, spec: dict, rounds: list) -> Comp:
    n = len(rounds)
    content_end = HOOK + n * R1
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    css = CSS
    for k_, v in (("felt", tex("felt.jpg")), ("wood", tex("card-wood.jpg")), ("grain", tex("card-grain.png")),
                  ("paper", tex("paper.jpg")), ("LIME", LIME)):
        css = css.replace(f"@{k_}@", v)
    comp.css(KIT_CSS)
    comp.css(css)
    comp.css(_flip_css())
    ep = spec.get("episode")

    # the table: on screen the whole time
    comp.add('<div class="full" style="z-index:0;background:#14231f;overflow:hidden"><div class="cd-cam">'
             '<div class="cd-wood"></div><div class="cd-mat"></div></div></div>')

    # ---- hook: the first three cards fanned out, silhouettes, names taped over
    fan = ""
    # frame 0 has the fan; at .3 s a hand spreads it a little more, at 2.45 s it's
    # gathered up and only the first card stays.
    spread = [(560, 930, 5, .86, 3.5, 14, 6), (680, 990, 10, .8, 5, 20, 12)]
    for j, (x, y, rot, sc, dr, dx, dy) in reversed(list(enumerate(spread))):
        if j + 1 < n:
            it = rounds[j + 1][0]
            move = (f"--r2:{rot + dr}deg;--dx:{dx}px;--dy:{dy}px;"
                    f"animation:cdspread .5s cubic-bezier(.2,.8,.3,1) {.3 + j * .06:.2f}s 1 normal both,"
                    f"cdgather .5s cubic-bezier(.55,0,.85,.35) {2.45 + (1 - j) * .08:.2f}s 1 normal forwards;")
            fan += _flat_card(ctx, it, j + 2, n, x, y, sc, rot, move, False)
    comp.scene(0, HOOK, f'<div class="full" style="overflow:hidden"><div class="cd-cam">{fan}</div></div>',
               fade_in=.01, fade_out=.01, z=10)
    comp.cue(.3, "paper"); comp.cue(2.45, "paper")

    # ---- the rounds
    for k, (it, opts, answer) in enumerate(rounds, 1):
        t0 = HOOK + (k - 1) * R1
        t_out = t0 + T_OUT
        rot = [-1.6, -2.4, -1.2, -2.0, -1.4, -2.2][k % 6]
        start = 0 if k == 1 else t0 + T_DEAL - .05
        card = _card(ctx, it, k, n, t0, rot, deal=k > 1, t_out=t_out)
        notes, sounds = _options(opts, answer, t0, t_out)
        comp.scene(start, t0 + R1 + .02, f'<div class="full" style="overflow:hidden"><div class="cd-cam">{card}{notes}</div></div>',
                   fade_in=.01, fade_out=.01, z=11)
        if k > 1:
            comp.cue(t0 + T_DEAL + .05, "paper")
        for s in sounds[::2]:
            comp.cue(*s)
        for j in range(3):
            comp.cue(t0 + T_CD + j, "tick")
            comp.cue(t0 + T_CD + j + .02, "pen")
        comp.cue(t0 + T_REV - 1.6, "drumroll")
        comp.cue(t0 + T_FLIP + .05, "flip")
        comp.cue(t0 + T_REV, "ding")
        comp.cue(t0 + T_REV + .15, "pen")
        comp.cue(t_out, "paper")
        comp.cue(t_out + .05, "whoosh")

    # ---- the note pad (top left): a note for the hook, then a fresh one per round
    pad = [_pad_note(None, f'<div class="abs cd-hand" data-fit="{PAD_W - 50}" style="left:26px;top:178px;'
                           f'font-size:62px;line-height:1.05;color:{MARK};transform:rotate(-2.5deg);white-space:nowrap">'
                           f'{n} rounds<br>4 choices each</div>',
                     f"quiz #{ep}" if ep else "", -4)]
    for k in range(1, n + 1):
        t0 = HOOK + (k - 1) * R1
        pad.append(_pad_note(t0 + T_NOTE, _countdown(t0 + T_CD), f"{k}/{n}", [3, -2.5, 2, -3.5, 1.5, -2][k % 6]))
        comp.cue(t0 + T_NOTE, "paper")

    # ---- outro: every card, face up, and the question
    t = content_end
    spread = ""
    sc = .5
    cw_, ch_ = CARD_W * sc, CARD_H * sc
    top_row = (n + 1) // 2 if n <= 4 else 3
    for i, (it, _, _) in enumerate(rounds):
        row, col = (0, i) if i < top_row else (1, i - top_row)
        in_row = top_row if row == 0 else n - top_row
        gap = (910 - in_row * cw_) / max(1, in_row - 1) if in_row > 1 else 0
        x0 = 45 + (910 - (in_row * cw_ + (in_row - 1) * min(gap, 30))) / 2
        cx = x0 + col * (cw_ + min(gap, 30)) + cw_ / 2
        cy = 560 + ch_ / 2 + row * (ch_ + 26)
        jit = ((i * 37 + n * 11) % 10) / 10 - .5
        # the first one comes in while the last round's card is still leaving
        spread += _flat_card(ctx, it, i + 1, n, cx + jit * 16, cy + jit * 10, sc, jit * 7,
                             _a("cdfan", t - .3 + i * .1, .5, "cubic-bezier(.2,.8,.3,1)"), True)
        if i % 2 == 0:
            comp.cue(t - .3 + i * .1, "paper")
    comp.scene(t - .35, comp.duration, f'<div class="full" style="overflow:hidden"><div class="cd-cam">{spread}</div></div>',
               fade_in=.01, fade_out=.01, z=12)
    pad.append(f'<div class="abs" style="left:{PAD_X}px;top:{PAD_Y}px;width:{PAD_W}px;height:{PAD_H}px;--r:-2deg;'
               f'transform:rotate(-2deg);{_a("lkslap", t + .1, .5, "cubic-bezier(.2,.9,.25,1)")}">'
               f'<div class="cd-note" style="{_note_bg(NOTE_COLS[0])}"></div>'
               f'<div class="abs cd-hand" data-fit="{PAD_W - 44}" data-lines="3" style="left:24px;top:22px;'
               f'width:{PAD_W - 44}px;font-size:70px;line-height:.95">How many did you get out of {n}?</div></div>')
    comp.cue(t + .1, "paper")
    comp.add(f'<div class="full" style="z-index:20;overflow:hidden"><div class="cd-cam">{"".join(pad)}</div></div>')

    # ---- the code token and the camera's grain: above everything, the whole time
    comp.add(f'<div class="full" style="z-index:30"><div class="cd-cam">{_token()}</div>'
             f'<div class="cd-vig"></div><div class="cd-grain"></div></div>')
    comp.add(PREP_JS)
    comp.cues.sort()
    return comp
