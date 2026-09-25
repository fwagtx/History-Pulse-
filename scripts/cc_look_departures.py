"""
DEPARTURES -- Last Chance, as an airport split-flap board filmed on a phone.

    0:00  hook     the DEPARTURES · ITEM SHOP board, complete on frame 0: every
                   offer in the video with its price and a blinking LAST CALL,
                   and under it the lime USE CODE: B A D flap sign. An airport
                   chime, the rows re-sync (a cascade of flaps), the first row
                   lights up and the camera pushes in on it.
    0:03  offers   one per offer (R s; longer on a thin day, so the video still
                   runs past a minute). Cut to the gate: the gate sign's flaps
                   clatter over to the offer's name and price (its status says
                   LAST CALL, then LEAVES 8 PM ET), and the gate monitor switches
                   to the cosmetic with its type, "in the shop since" / "added
                   today", a bundle's regular price and what it includes.
    ~0:55 board    back on the board: every row flips to LAST CALL again, a
                   light runs down the rows and the two sub-rows flip to WHICH ONE
                   ARE / YOU GRABBING? On a longer hold they page back and forth
                   with the reset time while the light moves row to row.

Everything with words on it sits inside the apps' safe box (cc_safe): the board
and the gate monitor run down past y 740, so their content stays left of the
button rail; the gate sign is above it and may use the full width. Only the
slatted wall and the frames of the board, sign and monitor run past it. Names
on the board are 48 px flaps and wrap onto a second line rather than shrink,
unless a day's names are too long for the board even then.

Facts on screen are the classic format's (cc_fmt_last_chance): the shown name,
the type (rarity and type, or BUNDLE · N ITEMS), the price, a bundle's regular
price when Epic lists one above today's, its contents, "in the shop since" /
"added today" from in_day, and the reset time, ctx.reset_et, exactly. The
wording is "leaving at reset" / "last call": nothing says anything won't come
back. The lime code sign is on screen in every frame.
"""

import random

from cc_fmt_last_chance import _members, _meta, _regular, _shown_name, _since
from cc_looks import LIME, PREP_JS, pad_to, tex
from cc_motion import RARITY, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, SAFE_TOP, Comp, esc

HOOK = 3.0
R = 6.2                     # one offer, as the classic format
R_MAX = 9.5                 # a thin day (4-5 offers) stretches each offer up to this
FONTS = ("Barlow Condensed", "Oswald")

INK = "#ece6d7"             # off-white flap print
AMBER = "#ffb21f"
CHARS = "ABCDEFGHIJKLMNOPRSTUVWXYZ0123456789"
LAST_CALL = "LAST|CALL"     # the gate's status flap: two short lines
STATUS = "LAST CALL"        # a board row's status flap: one line
SD = .062                   # seconds per flap step
NARROW = {"·", ",", ":", ".", "'"}
NF = .52                    # a separator flap's width, as a share of a letter flap

# The lime code sign, on the wall under the board in both shots, centred under
# the board inside the bottom of the safe box.
SIGN_W, SIGN_H = 600, 150
SIGN_X, SIGN_Y = 180, SAFE_BOTTOM - 16 - SIGN_H          # 180 .. 780, y 1254 .. 1404
TOP, BOTTOM = SAFE_TOP + 34, SIGN_Y - 26                   # what the board or the gate may use
# The board: its rows run below y 740, so its content stays left of the rail.
CX0, CX1 = SAFE_LEFT + 20, SAFE_RIGHT - 20                 # 80 .. 880
BX0, BX1 = CX0 - 22, CX1 + 22                              # its frame
GAP = 14                    # between the board's columns
LG = 6                      # between the two lines of a two-line row
FS_NAME = 48                # the names' letters, when they fit
P_NAME = FS_NAME / 1.66 + 3.5
ST_W, ST_FS, LAMP = 150, 30, 18                            # a row's status flap and its lamp
# The gate sign is above y 740: it may use the full width of the box.
GX0, GX1 = SAFE_LEFT + 20, SAFE_RIGHT_TOP - 20             # 80 .. 1000
MX0, MX1 = BX0, BX1                                        # the gate monitor's bezel


def _a(name, t, dur, ease="linear", extra=""):
    return f"animation:{name} {dur:.3f}s {ease} {t:.3f}s 1 normal both;{extra}"


def _shown(since=None, until=None) -> str:
    """A glyph that is only there while its flap shows it (see Flaps)."""
    a = []
    if since is not None:
        a.append(f"dpon .01s steps(1,end) {since:.3f}s 1 normal both")
    if until is not None:
        a.append(f"dpoff .01s steps(1,end) {until:.3f}s 1 normal forwards")
    return f' style="animation:{",".join(a)}"' if a else ""


# ---------------------------------------------------------------- split-flap cells

class Flaps:
    """Split-flap modules. A cell shows `first`; each flip (t, glyph) spins it
    through a few random glyphs and lands on `glyph`: a stepped strip of glyphs
    (one nested, relatively positioned wrapper per flip, so the offsets add up)
    and a flap half that falls on every step.

    The strip's other glyphs sit above and below the cell, clipped. So nothing
    is ever there that nobody can see, each real glyph is visible only while its
    cell shows it, and the random ones a spin runs through are marked as the
    decoration they are.

    Only layout and paint properties move (top, height, colour, visibility). The
    renderer keeps every animation paused, and Chrome gives each paused-but-
    unfinished transform or opacity animation its own compositing layer: with a
    board of flaps that was over a thousand layers and twice the render time."""

    def __init__(self, seed: int):
        self.rnd = random.Random(seed)

    @staticmethod
    def glyph(g: str, attrs: str = "") -> str:
        if not g.strip():
            return "<b>&nbsp;</b>"
        if "|" in g:                               # a two-line status: "LAST|CALL"
            top, bottom = g.split("|", 1)
            return f'<b class="w2"{attrs}>{esc(top)}<br>{esc(bottom)}</b>'
        cls = {"M": ' class="nm"', "W": ' class="nw"'}.get(g, "")
        return f"<b{cls}{attrs}>{esc(g)}</b>"

    def cell(self, x, y, w, h, fs, first=" ", flips=(), cls="", word=False, lo=5, hi=10) -> str:
        r = self.rnd
        v = r.uniform(-.018, .03)                   # each flap a touch lighter or darker
        oy = r.uniform(-.7, .7)                     # and not quite level
        st = f"left:{x:.1f}px;top:{y:.1f}px;width:{w:.1f}px;height:{h:.0f}px;--h:{h:.0f}px;--fs:{fs:.0f}px;--v:{v:.3f}"
        flips = list(flips)
        glyphs = [self.glyph(first, _shown(None, flips[0][0] if flips else None))]
        opens, pulses = [], []
        for j, (t, g) in enumerate(flips):
            n = r.randint(lo, hi)
            spin = [" "] * (n - 1) if word else [r.choice(CHARS) for _ in range(n - 1)]
            glyphs += [self.glyph(s, ' data-safe="ignore"') for s in spin]
            nxt = flips[j + 1][0] if j + 1 < len(flips) else None
            glyphs.append(self.glyph(g, _shown(t + (n - 1) * SD - .012, nxt)))
            opens.append(f'<div style="--d:-{n * h:.0f}px;{_a("dpfl", t, n * SD, f"steps({n},start)")}">')
            pulses.append(f"dppu {SD:.3f}s linear {t:.3f}s {n} forwards")
        strip = "".join(opens) + "".join(glyphs) + "</div>" * len(opens)
        pulse = f'<i class="p" style="animation:{",".join(pulses)}"></i>' if pulses else ""
        return (f'<div class="dp-f {cls}" style="{st}"><div class="s" style="top:{oy:.1f}px">{strip}</div>'
                f'{pulse}</div>')

    def run(self, x, y, text, pitch, w, h, fs, cls="", first="", flips_at=None, lo=5, hi=10, narrow=False):
        """A run of cells showing `text`. `first` is what they show before their
        flips (default: the text itself); flips_at(i, ch) -> [(t, glyph)...] or ()
        for each cell. narrow: separators get half-width flaps (only for text
        whose layout never changes, like the header)."""
        out = []
        first = first.ljust(len(text)) if first else text
        for i, ch in enumerate(text):
            nar = narrow and ch in NARROW
            cw, cp = (w * NF, pitch * NF) if nar else (w, pitch)
            fl = flips_at(i, ch) if flips_at else ()
            out.append(self.cell(x, y, cw, h, fs, first[i], fl, cls, lo=lo, hi=hi))
            x += cp
        return "".join(out), x


# ---------------------------------------------------------------- shared pieces

CSS = """
.dp-wall{position:absolute;left:-60px;top:-60px;width:1200px;height:2040px;background:url('@slats@') center/cover}
.dp-ceil{position:absolute;left:-60px;top:-60px;width:1200px;height:190px;
  background:linear-gradient(180deg,#0b0a09 0%,#161412 78%,#262220 100%);box-shadow:0 6px 14px rgba(0,0,0,.6)}
.dp-dl{position:absolute;border-radius:50%}
.dp-bd{position:absolute;background:url('@board@') center/cover;border-radius:10px;overflow:hidden;
  box-shadow:0 0 0 2px #050505,0 3px 0 3px #1e1d1b,0 34px 44px rgba(0,0,0,.62),0 10px 14px rgba(0,0,0,.5)}
.dp-bd .edge{position:absolute;left:0;right:0;top:0;height:7px;
  background:linear-gradient(180deg,rgba(255,236,210,.42),rgba(255,236,210,0))}
.dp-chan{position:absolute;background:#070707;border-radius:3px;
  box-shadow:inset 0 3px 4px rgba(0,0,0,.9),0 1px 0 rgba(255,255,255,.06)}
.dp-rail{position:absolute;height:2px;background:#2c2b29;box-shadow:0 1px 0 #000}
.dp-screw{position:absolute;width:10px;height:10px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#8a8883,#3a3936 70%);box-shadow:0 1px 1px #000}
.dp-lab{position:absolute;font-family:'Barlow Condensed';font-weight:600;font-size:30px;line-height:34px;
  letter-spacing:.12em;color:#ddd6c5;opacity:.86;white-space:nowrap}
.dp-f{position:absolute;border-radius:3px;overflow:hidden;
  background:linear-gradient(180deg,#333334 0%,#29292a 47%,#202021 50.5%,#262627 53%,#1b1b1c 100%);
  box-shadow:0 1px 1.5px rgba(0,0,0,.8),inset 0 1px 0 rgba(255,255,255,.07)}
.dp-f .s{position:absolute;left:0;width:100%}
.dp-f .s div{position:relative}
.dp-f b{display:block;height:var(--h);line-height:var(--h);text-align:center;color:@INK@;
  font-family:'Barlow Condensed';font-weight:800;font-size:var(--fs);white-space:nowrap}
.dp-f b.nm{transform:scaleX(.86)}
.dp-f b.nw{transform:scaleX(.7)}
.dp-f::before{content:"";position:absolute;inset:0;z-index:2;pointer-events:none;
  background:linear-gradient(180deg,rgba(255,255,255,.07) 0%,rgba(255,255,255,0) 30%,rgba(0,0,0,.08) 47%,
  rgba(0,0,0,.34) 50.5%,rgba(0,0,0,.02) 56%,rgba(0,0,0,.2) 100%),rgba(255,255,255,var(--v))}
.dp-f::after{content:"";position:absolute;left:0;right:0;top:calc(50% - 1px);height:2px;z-index:3;
  background:#060606;box-shadow:0 1px 0 rgba(255,255,255,.08)}
.dp-f .p{position:absolute;left:0;right:0;top:0;height:0;z-index:4;background-color:rgba(62,62,64,0)}
/* 0% is invisible on purpose: Chrome can land a multi-iteration forwards fill on ~0 */
@keyframes dppu{0%{top:0;height:50%;background-color:rgba(62,62,64,0)}3%{top:0;height:50%;background-color:rgba(62,62,64,1)}
  70%{top:45%;height:5%;background-color:rgba(44,44,46,1)}100%{top:50%;height:0;background-color:rgba(30,30,31,0)}}
@keyframes dpfl{from{top:0}to{top:var(--d)}}
/* a status flap blinks as a whole (its glyphs carry their own show/hide times) */
.dp-f.rem .s{color:@AMBER@;animation:dpblink 1.2s linear 0s infinite}
.dp-f.rem b{letter-spacing:.06em;color:inherit}
.dp-f.rem b.w2{line-height:calc(var(--h) / 2);white-space:normal}
@keyframes dpblink{0%,46%{color:@AMBER@;text-shadow:0 0 5px rgba(255,170,30,.5)}
  50%,96%{color:#a87a22;text-shadow:none}100%{color:@AMBER@;text-shadow:0 0 5px rgba(255,170,30,.5)}}
.dp-lamp{position:absolute;border-radius:50%;background-color:#ffbe3a;
  background-image:radial-gradient(circle at 40% 35%,rgba(255,246,214,.95) 0%,rgba(255,246,214,0) 38%,rgba(0,0,0,0) 62%,rgba(60,30,0,.55) 100%);
  box-shadow:0 0 0 2px #0a0a0a,0 0 9px 2px rgba(255,170,30,.5);animation:dplampb 1.2s linear 0s infinite}
@keyframes dplampb{0%,46%{background-color:#ffbe3a;box-shadow:0 0 0 2px #0a0a0a,0 0 9px 2px rgba(255,170,30,.5)}
  50%,96%{background-color:#4a3210;box-shadow:0 0 0 2px #0a0a0a,0 0 0 0 rgba(255,170,30,0)}
  100%{background-color:#ffbe3a;box-shadow:0 0 0 2px #0a0a0a,0 0 9px 2px rgba(255,170,30,.5)}}
.dp-lit{position:absolute;border-radius:4px;visibility:hidden;
  box-shadow:0 0 0 2px rgba(255,190,70,.85),0 0 12px 1px rgba(255,170,40,.3),inset 0 0 14px rgba(255,170,40,.18)}
@keyframes dpon{from{visibility:hidden}to{visibility:visible}}
@keyframes dpoff{from{visibility:visible}to{visibility:hidden}}
@keyframes dpflash2{0%{background-color:rgba(170,190,226,0)}20%{background-color:rgba(170,190,226,.32)}
  100%{background-color:rgba(170,190,226,0)}}
@keyframes dpblink2{0%,46%{background-color:#ffb21f}50%,96%{background-color:rgba(255,178,31,.25)}100%{background-color:#ffb21f}}
.dp-shade{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(165deg,rgba(0,0,0,0) 25%,rgba(0,0,0,.26) 75%,rgba(0,0,0,.4) 100%)}
.dp-blight{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(900px 520px at 12% 0%,rgba(255,232,200,.10),rgba(255,232,200,0) 70%)}
.dp-glare{position:absolute;width:260px;height:1700px;left:520px;top:-300px;transform:rotate(27deg);pointer-events:none;
  background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.035) 30%,
  rgba(255,255,255,.085) 52%,rgba(255,255,255,.025) 70%,rgba(255,255,255,0))}
.dp-sign{position:absolute;border-radius:8px;background:url('@board@') center/cover;overflow:hidden;
  box-shadow:0 0 0 2px #050505,0 2px 0 3px #1e1d1b,0 24px 30px rgba(0,0,0,.6)}
.dp-slight{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(560px 220px at 40% 0%,rgba(255,236,205,.07),rgba(255,236,205,0) 70%),
             linear-gradient(180deg,rgba(0,0,0,0) 40%,rgba(0,0,0,.22) 100%)}
.dp-slab{position:absolute;font-family:'Barlow Condensed';font-weight:800;font-size:54px;line-height:56px;
  letter-spacing:.06em;color:@LIME@;white-space:nowrap}
.dp-f.lime{background:linear-gradient(180deg,#efff62 0%,@LIME@ 46%,#d2e62c 50.5%,#e3f736 53%,#d8ec33 100%)}
.dp-f.lime b{color:#111}
.dp-f.lime::before{background:linear-gradient(180deg,rgba(255,255,255,.12) 0%,rgba(255,255,255,0) 32%,
  rgba(0,0,0,.03) 47%,rgba(0,0,0,.14) 50.5%,rgba(0,0,0,0) 56%,rgba(0,0,0,.06) 100%)}
.dp-plate{position:absolute;padding:3px 12px 4px;border-radius:3px;font-family:'Barlow Condensed';font-weight:600;
  font-size:27px;line-height:32px;letter-spacing:.05em;color:#23221f;white-space:nowrap;
  background:linear-gradient(180deg,#c4c1b9,#98958e);box-shadow:0 1px 0 rgba(255,255,255,.25) inset,0 2px 4px rgba(0,0,0,.6)}
/* the lens: one still layer for the vignette, the colour cast and the grain */
.dp-lens{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(125% 80% at 44% 40%,rgba(0,0,0,0) 52%,rgba(0,0,0,.6) 100%),
    linear-gradient(180deg,rgba(255,190,120,.035) 0%,rgba(0,0,0,0) 45%,rgba(18,28,42,.30) 100%)}
.dp-grain{position:absolute;inset:0;pointer-events:none;opacity:.05;background:url('@grain@') 0 0/512px 512px repeat}

/* the gate monitor */
.dp-mon{position:absolute;border-radius:14px;background:linear-gradient(180deg,#1b1b1d,#0c0c0d);
  box-shadow:0 0 0 2px #050505,inset 0 1px 0 rgba(255,255,255,.12),0 30px 40px rgba(0,0,0,.6),0 8px 12px rgba(0,0,0,.5)}
.dp-scr{position:absolute;overflow:hidden;border-radius:4px;background:#07101f}
.dp-ui{font-family:'Barlow Condensed';color:#e9eef7;white-space:nowrap}
.dp-scan{position:absolute;inset:0;pointer-events:none;
  background:repeating-linear-gradient(180deg,rgba(0,0,0,.16) 0 1px,rgba(0,0,0,0) 1px 3px)}
.dp-glass{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(420px 170px at 18% 4%,rgba(255,244,226,.11),rgba(255,244,226,0) 70%),
    linear-gradient(118deg,rgba(255,255,255,.06) 0%,rgba(255,255,255,0) 38%,rgba(255,255,255,0) 62%,rgba(255,255,255,.03) 100%),
    radial-gradient(ellipse 80% 75% at 50% 50%,rgba(0,0,0,0) 60%,rgba(0,0,0,.35) 100%)}
@keyframes dpkb{from{transform:scale(1)}to{transform:scale(1.05)}}
@keyframes dpup{from{visibility:hidden;top:var(--y0)}to{visibility:visible;top:var(--y1)}}
@keyframes dppush{from{transform:scale(1)}to{transform:scale(1.07)}}
@keyframes dpdrift{from{transform:scale(1)}to{transform:scale(1.02)}}
@keyframes dpstrike{from{width:0}to{width:calc(100% + 8px)}}
"""


def _wall(close: bool = False) -> str:
    """The slatted wall and the ceiling. Close: the gate, framed tighter."""
    if close:
        return ('<div class="dp-wall" style="transform:scale(1.45);transform-origin:18% 30%"></div>'
                '<div class="abs" style="left:0;top:0;width:1080px;height:420px;'
                'background:linear-gradient(180deg,rgba(8,7,6,.75),rgba(8,7,6,0))"></div>')
    return ('<div class="dp-wall"></div><div class="dp-ceil"></div>'
            '<div class="dp-dl" style="left:-300px;top:-200px;width:980px;height:460px;background:radial-gradient('
            'closest-side,rgba(255,246,228,.34),rgba(255,246,228,.12) 55%,rgba(255,246,228,0))"></div>'
            '<div class="dp-dl" style="left:-150px;top:-30px;width:480px;height:130px;background:radial-gradient('
            'closest-side,#fffaf0 0%,#fffaf0 48%,rgba(255,248,236,.55) 72%,rgba(255,248,236,0))"></div>'
            '<div class="dp-dl" style="left:740px;top:0px;width:290px;height:70px;opacity:.5;background:radial-gradient('
            'closest-side,#fff8ec 0%,#fff8ec 40%,rgba(255,248,236,0))"></div>')


def _lens() -> str:
    return '<div class="dp-lens"></div><div class="dp-grain"></div>'


def _code_sign() -> str:
    """USE CODE: B A D -- painted lime words and three lime flaps on its own dark
    sign under the board, with the #EpicPartner plate screwed on under the words."""
    fl = Flaps(7)
    x0, y0, w, h = SIGN_X, SIGN_Y, SIGN_W, SIGN_H
    flaps = "".join(fl.cell(x0 + 276 + i * 100, y0 + 11, 92, h - 22, 114, ch, cls="lime")
                    for i, ch in enumerate("BAD"))
    return (f'<div class="dp-sign" data-safe="key" data-name="code" style="left:{x0}px;top:{y0}px;width:{w}px;'
            f'height:{h}px"><div class="abs" style="left:{-x0}px;top:{-y0}px;width:1080px;height:1920px">'
            f'<div class="dp-slab" style="left:{x0 + 26}px;top:{y0 + 24}px">USE CODE:</div>{flaps}'
            f'<div class="dp-plate" style="left:{x0 + 28}px;top:{y0 + 92}px">#EpicPartner</div></div>'
            f'<div class="dp-slight"></div></div>')


# ---------------------------------------------------------------- the board

def _price(p: int) -> str:
    return f"{int(p):,}"


def _price_units(D: int) -> float:
    """A price's width in letter pitches: the thousands comma is a narrow flap."""
    return (D - 1) + NF if D >= 5 else D


def _row_lines(name: str, N: int) -> list:
    up = name.upper()
    return [up] if len(up) <= N else _wrap(up, N)


def _board_geom(names: list, prices: list, head: str) -> dict:
    """The board's grid. A row: the name (on two lines, split between words, when
    it's longer than a line at the names' size), the price in V-Bucks, a lamp and
    the status. The header and the two sub-rows share one grid above the rows."""
    n = len(names)
    width = CX1 - CX0
    D = max(3, max(len(_price(p)) for p in prices))
    pu = _price_units(D)
    avail = width - 2 * GAP - LAMP - 8 - ST_W          # names and prices
    hp = min(44.0, width / (len(head) - sum(c in NARROW for c in head) * (1 - NF)))
    hh = round((hp - 3.5) * 1.6)
    S = int(width // hp)                                # the sub-rows' cells
    head_h = 18 + hh + 12 + 2 * hh + LG + 14 + 34 + 10
    ok2 = lambda s, c: len(s) <= c or (len(_wrap(s.upper(), c)) <= 2
                                       and max(len(l) for l in _wrap(s.upper(), c)) <= c)
    room = BOTTOM - TOP
    c = max(12, int(avail / P_NAME - pu))
    longest = max(len(s) for s in names)
    while True:
        while not all(ok2(s, c) for s in names):
            c += 1
        lines = [_row_lines(s, c) for s in names]
        N = max(12, max(len(l) for ls in lines for l in ls))
        P = min(42.0, avail / (N + pu))
        cw = P - 3.5
        ch = round(min(cw * 1.6, 74))
        rh = [ch * len(ls) + LG * (len(ls) - 1) for ls in lines]
        fixed = head_h + sum(rh) + 18
        # too tall with the long names on two lines: fewer two-line rows, smaller letters
        if fixed + 14 * (n - 1) <= room or c >= longest:
            break
        c += 1
    rg = max(14.0, min(34.0 if n > 5 else 46.0, (room - fixed) / max(1, n - 1)))
    total = fixed + rg * (n - 1)
    top = TOP + max(0.0, (room - total) / 2)
    head_y = top + 18
    sub_y = head_y + hh + 12
    rail_y = sub_y + 2 * hh + LG + 7
    lab_y = rail_y + 7
    row_y, y = [], lab_y + 34 + 10
    for h_ in rh:
        row_y.append(y)
        y += h_ + rg
    return dict(n=n, N=N, D=D, pu=pu, P=P, cw=cw, ch=ch, fs=cw * 1.66, hp=hp, hh=hh, S=S, lines=lines, rh=rh,
                row_y=row_y, top=top, bottom=row_y[-1] + rh[-1] + 18, head_y=head_y, sub_y=sub_y,
                rail_y=rail_y, lab_y=lab_y)


def _board(fl: Flaps, g: dict, prices: list, head: str, sub: tuple, *, resync=None, sub_seq=(),
           lit=None) -> str:
    """The departures board. sub: the sub-rows' two lines; resync: time the rows
    re-sync (a cascade over the same text); sub_seq: [(time, (line, line))] the
    sub-rows flip to, in turn; lit: [(row, t_on, t_off)] rows that light up."""
    x = CX0
    parts = []
    hp, hh = g["hp"], g["hh"]
    # the header and the two sub-rows
    s, _ = fl.run(x, g["head_y"], head, hp, hp - 3.5, hh, (hp - 3.5) * 1.62, narrow=True)
    parts.append(s)
    for li in range(2):
        seq = [(t, lines[li].ljust(g["S"])) for t, lines in sub_seq]

        def fa(i, ch, seq=seq, li=li):
            out, cur = [], ch
            for t, txt in seq:
                if cur != " " or txt[i] != " ":
                    out.append((t + li * .09 + i * .018 + fl.rnd.uniform(0, .06), txt[i]))
                cur = txt[i]
            return out
        s, _ = fl.run(x, g["sub_y"] + li * (hh + LG), sub[li].ljust(g["S"]), hp, hp - 3.5, hh, (hp - 3.5) * 1.62,
                      flips_at=fa if seq else None)
        parts.append(s)
    # the rows
    P, cw, ch, fs = g["P"], g["cw"], g["ch"], g["fs"]
    col_price = x + g["N"] * P + GAP
    price_w = g["pu"] * P
    col_status = col_price + price_w + GAP
    for r, (lines, pr) in enumerate(zip(g["lines"], prices)):
        y, rh = g["row_y"][r], g["rh"][r]
        yc = y + (rh - ch) / 2                       # the price and the status, centred on the row
        t_r = resync + r * .11 if resync is not None else None
        for li, line in enumerate(lines):
            fa = (lambda i, c, t_l=t_r + li * .07: [(t_l + i * .012 + fl.rnd.uniform(0, .07), c)] if c != " " else ()) \
                if t_r is not None else None
            s, _ = fl.run(x, y + li * (ch + LG), line.ljust(g["N"]), P, cw, ch, fs, flips_at=fa)
            parts.append(s)
        pt = _price(pr).rjust(g["D"])
        # the comma slot is narrow in every row, so the digits line up
        px = col_price
        for i, c in enumerate(pt):
            nar = i == g["D"] - 4 and g["D"] >= 5
            w_ = cw * NF if nar else cw
            fl_ = [(t_r + .25 + i * .012 + fl.rnd.uniform(0, .07), c)] if (t_r is not None and c != " ") else ()
            parts.append(fl.cell(px, yc, w_, ch, fs, c, fl_))
            px += P * NF if nar else P
        parts.append(f'<div class="dp-lamp" style="left:{col_status:.1f}px;top:{yc + ch / 2 - LAMP / 2:.1f}px;'
                     f'width:{LAMP}px;height:{LAMP}px"></div>')
        st_x = col_status + LAMP + 8
        fl_ = [(t_r + .4, STATUS)] if t_r is not None else ()
        parts.append(fl.cell(st_x, yc, CX1 - st_x, ch, ST_FS, STATUS, fl_, "rem", word=True, lo=3, hi=5))
        for row, t_on, t_off in (lit or ()):
            if row == r:
                parts.append(f'<div class="dp-lit" style="left:{x - 7:.0f}px;top:{y - 6:.0f}px;'
                             f'width:{CX1 - x + 14:.0f}px;height:{rh + 12:.0f}px;'
                             f'animation:dpon .01s steps(1,end) {t_on:.3f}s 1 normal both,'
                             f'dpoff .01s steps(1,end) {t_off:.3f}s 1 normal forwards"></div>')
    parts.append(f'<div class="dp-lab" style="left:{x + 1:.0f}px;top:{g["lab_y"]:.0f}px">ITEM</div>'
                 f'<div class="dp-lab" style="right:{1080 - col_price - price_w:.0f}px;top:{g["lab_y"]:.0f}px;'
                 f'letter-spacing:.08em">V-BUCKS</div>'
                 f'<div class="dp-lab" style="left:{col_status + LAMP + 12:.0f}px;top:{g["lab_y"]:.0f}px">STATUS</div>')
    cells = "".join(parts)

    bx, by, bw, bh = BX0, g["top"], BX1 - BX0, g["bottom"] - g["top"]
    chans = "".join(f'<div class="dp-chan" style="left:10px;right:10px;top:{g["row_y"][r] - 5 - by:.0f}px;'
                    f'height:{g["rh"][r] + 10:.0f}px"></div>' for r in range(g["n"]))
    chans += "".join(f'<div class="dp-chan" style="left:10px;right:10px;top:{yy - 5 - by:.0f}px;height:{hh + 10}px">'
                     f'</div>' for yy in (g["head_y"], g["sub_y"], g["sub_y"] + hh + LG))
    chans += f'<div class="dp-rail" style="left:10px;right:10px;top:{g["rail_y"] - by:.0f}px"></div>'
    screws = "".join(f'<div class="dp-screw" style="left:{sx}px;top:{sy:.0f}px"></div>'
                     for sx, sy in ((10, 10), (10, bh - 20), (bw - 20, 10), (bw - 20, bh - 20)))
    return (f'<div class="dp-bd" style="left:{bx}px;top:{by:.0f}px;width:{bw}px;height:{bh:.0f}px">'
            f'{chans}{screws}<div class="abs" style="left:{-bx}px;top:{-by:.0f}px;width:1080px;height:1920px">'
            f'{cells}</div><div class="dp-shade"></div><div class="dp-blight"></div><div class="dp-glare"></div>'
            f'<div class="edge"></div></div>')


# ---------------------------------------------------------------- the gate

def _wrap(name: str, width: int) -> list:
    lines, cur = [], ""
    for w in name.split():
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    lines.append(cur)
    return lines


def _gate_geom(names: list, prices: list) -> dict:
    """The gate sign's cells, sized from the longest name: one line up to 26
    letters, else two lines (split between words) as wide as the longest line."""
    longest = max(len(s) for s in names)
    if longest <= 26:
        lines, C = 1, max(12, longest)
    else:
        C = max(12, (longest + 1) // 2)
        while any(len(_wrap(s.upper(), C)) > 2 or max(len(l) for l in _wrap(s.upper(), C)) > C for s in names):
            C += 1
        lines = 2
    P = min(60.0, (GX1 - GX0) / C)
    cw = P - 4
    ch = round(cw * 1.55)
    D = max(3, max(len(_price(p)) for p in prices))
    top = SAFE_TOP - 4
    y_name = top + 24
    y_b = y_name + lines * ch + (lines - 1) * 10 + 22
    bh = max(78, round((max(52.0, P) - 4) * 1.55))
    bottom = y_b + bh + 22
    return dict(lines=lines, C=C, P=P, cw=cw, ch=ch, fs=cw * 1.62, D=D, top=top, y_name=y_name, y_b=y_b,
                bh=bh, bottom=bottom)


def _name_lines(name: str, g: dict) -> list:
    up = name.upper()
    if g["lines"] == 1:
        return [up.ljust(g["C"])]
    ls = _wrap(up, g["C"])
    return [l.ljust(g["C"]) for l in (ls + [""])[:2]]


def _gate_sign(fl: Flaps, g: dict, name: str, price: int, prev: tuple, t0: float, first: bool, R_: float,
               leaves: str) -> str:
    """The gate's flap sign: the name, then the price in V-Bucks and LAST CALL.
    Its cells start on the previous offer's text and clatter over to this one's."""
    x0 = GX0
    parts = []
    lines = _name_lines(name, g)
    prev_lines = _name_lines(prev[0], g) if prev[0] else [" " * g["C"]] * g["lines"]
    P, cw, ch, fs = g["P"], g["cw"], g["ch"], g["fs"]
    for li, (txt, old) in enumerate(zip(lines, prev_lines)):
        y = g["y_name"] + li * (ch + 10)
        for i, c in enumerate(txt):
            o = old[i]
            fl_ = [(t0 + .02 + li * .06 + i * .014 + fl.rnd.uniform(0, .08), c)] if (c != o or c != " ") else ()
            parts.append(fl.cell(x0 + i * P, y, cw, ch, fs, o, fl_, lo=5, hi=11))
    # price, in its own run of cells
    PB = max(52.0, P)
    cb = PB - 4
    hb = g["bh"]
    pt, po = _price(price).rjust(g["D"]), (_price(prev[1]).rjust(g["D"]) if prev[1] else " " * g["D"])
    x = x0
    for i, c in enumerate(pt):
        nar = i == g["D"] - 4 and g["D"] >= 5
        w_ = cb * NF if nar else cb
        o = po[i]
        fl_ = [(t0 + .22 + i * .02 + fl.rnd.uniform(0, .06), c)] if (c != o or c != " ") else ()
        parts.append(fl.cell(x, g["y_b"], w_, hb, cb * 1.62, o, fl_))
        x += PB * NF if nar else PB
    parts.append(f'<div class="dp-lab" style="left:{x + 12:.0f}px;top:{g["y_b"] + hb / 2 - 19:.0f}px;font-size:34px;'
                 f'line-height:38px;font-weight:800;opacity:.9">V-BUCKS</div>')
    # the status: a blinking lamp and the LAST CALL flap
    sx = GX1 - 190
    parts.append(f'<div class="dp-lab" style="left:{sx - 162:.0f}px;top:{g["y_b"] + hb / 2 - 17:.0f}px">STATUS</div>')
    parts.append(f'<div class="dp-lamp" style="left:{sx - 32:.0f}px;top:{g["y_b"] + hb / 2 - 9:.0f}px;width:18px;height:18px"></div>')
    # LAST CALL, then halfway through, when it leaves (the next offer flips it back)
    fl_ = [(t0 + .5, LAST_CALL), (t0 + min(3.4, R_ * .52), leaves)]
    parts.append(fl.cell(sx, g["y_b"], 190, hb, hb * .44, " " if first else leaves, fl_, "rem", word=True,
                         lo=3, hi=5))
    bx, by = GX0 - 22, g["top"]
    bw, bh = GX1 - GX0 + 44, g["bottom"] - g["top"]
    chans = "".join(f'<div class="dp-chan" style="left:10px;right:10px;top:{g["y_name"] + li * (ch + 10) - 5 - by:.0f}px;'
                    f'height:{ch + 10:.0f}px"></div>' for li in range(g["lines"]))
    chans += (f'<div class="dp-chan" style="left:10px;right:10px;top:{g["y_b"] - 5 - by:.0f}px;height:{hb + 10}px"></div>')
    screws = "".join(f'<div class="dp-screw" style="left:{sx_}px;top:{sy:.0f}px"></div>'
                     for sx_, sy in ((10, 10), (10, bh - 20), (bw - 20, 10), (bw - 20, bh - 20)))
    return (f'<div class="dp-bd" style="left:{bx}px;top:{by:.0f}px;width:{bw}px;height:{bh:.0f}px">'
            f'{chans}{screws}<div class="abs" style="left:{-bx}px;top:{-by:.0f}px;width:1080px;height:1920px">'
            f'{"".join(parts)}</div><div class="dp-shade"></div><div class="dp-blight"></div>'
            f'<div class="edge"></div></div>')


def _monitor(ctx, it: dict, k: int, n: int, t0: float, R_: float, g: dict) -> str:
    """The gate monitor: the cosmetic, and beside it what the classic format says
    about the offer. It switches over at t0 + .25. It runs down past y 740, so
    the screen stays left of the button rail."""
    mx, my, mw = MX0, g["bottom"] + 26, MX1 - MX0
    mh = BOTTOM - my
    bz = 18
    sw, sh = mw - 2 * bz, mh - 2 * bz
    bar, foot = 60, 58
    col = RARITY.get(it.get("rarity"), "#6a7384")
    art = ctx.art(it)
    name = _shown_name(it)
    info_w = 318
    ax, aw, ah = 20, sw - info_w - 56, sh - bar - foot - 28
    if art:
        pic = (f'<img data-trim data-bake="drop-shadow(0 18px 18px rgba(0,0,0,.55))" data-pad="50" src="{art}" '
               f'style="position:absolute;left:0;top:0;width:{aw}px;height:{ah}px;object-fit:contain">')
    else:
        pic = (f'<div class="dp-ui" data-fit="{aw - 40}" data-lines="3" style="position:absolute;left:20px;'
               f'top:{ah / 2 - 110:.0f}px;width:{aw - 40}px;white-space:normal;text-align:center;font-weight:800;'
               f'font-size:72px;line-height:1;color:rgba(233,238,247,.92)">{esc(name.upper())}</div>')
    t_sw = t0 + .25
    # the info column: blocks of (label, value), centred beside the cosmetic
    bundle = bool(it.get("is_bundle"))
    vfs = 44 if bundle else 50
    blocks = []                                   # (html, height)
    lab = lambda t: (f'<div class="dp-ui" style="font-size:30px;line-height:34px;font-weight:600;letter-spacing:.1em;'
                     f'color:#a3b2c8">{t}</div>')
    blocks.append((lab("TYPE") + f'<div class="dp-ui" data-fit="{info_w}" style="font-size:{vfs}px;font-weight:800;'
                   f'line-height:1.02;margin-top:4px">{esc(_meta(it))}</div>', 38 + vfs * 1.02))
    since = _since(it, ctx)
    if since:
        head_, v = ("IN THE SHOP", "ADDED TODAY") if since == "ADDED TODAY" else \
            ("IN THE SHOP SINCE", since.replace("IN THE SHOP SINCE ", ""))
        blocks.append((lab(head_) + f'<div class="dp-ui" data-fit="{info_w}" style="font-size:{vfs}px;'
                       f'font-weight:800;line-height:1.02;margin-top:4px">{esc(v)}</div>', 38 + vfs * 1.02))
    reg = _regular(it)
    if reg:
        blocks.append((lab("REGULAR PRICE") + f'<div class="dp-ui" style="position:relative;display:inline-block;'
                       f'font-size:44px;line-height:1.02;font-weight:800;color:#c2cbd9;margin-top:4px">{reg:,}'
                       f'<span style="position:absolute;left:-4px;width:0;top:50%;height:4px;background:#ff5a4f;'
                       f'{_a("dpstrike", t0 + 1.4, .25, "ease-out")}"></span></div>', 38 + 45))
    members = _members(it) if bundle else []
    gap = 40 if not bundle else 26
    if members:
        used = sum(h for _, h in blocks) + gap * len(blocks)
        room = int((ah - 30 - used - 40) // 36)
        shown = members if len(members) <= room else members[:max(1, room - 1)]
        more = len(members) - len(shown)
        lis = "".join(f'<div class="dp-ui" data-fit="{info_w}" style="font-size:30px;font-weight:600;'
                      f'line-height:36px">{esc(m)}</div>' for m in shown)
        if more:
            lis += (f'<div class="dp-ui" style="font-size:30px;font-weight:600;line-height:36px;color:#a3b2c8">'
                    f'+ {more} more</div>')
        blocks.append((f'<div style="margin-bottom:6px">{lab("INCLUDES")}</div>{lis}',
                       40 + 36 * (len(shown) + (1 if more else 0))))
    total = sum(h for _, h in blocks) + gap * (len(blocks) - 1)
    y = max(10, (ah - total) / 2 - 6)
    info = []
    for i, (html, h) in enumerate(blocks):
        if i:
            info.append(f'<div class="abs" style="left:0;top:{y - gap / 2:.0f}px;width:{info_w - 20}px;height:1px;'
                        f'background:rgba(201,211,226,.18);{_a("dpon", t0 + .7 + i * .16, .01, "steps(1,end)")}"></div>')
        info.append(f'<div class="abs" style="left:0;--y0:{y + 10:.0f}px;--y1:{y:.0f}px;width:{info_w}px;'
                    f'{_a("dpup", t0 + .7 + i * .16, .2, "steps(2,start)")}">{html}</div>')
        y += h + gap
    # The screen's frame stays lit (the navy page, LAST CALL, the leaving bar);
    # at t_sw the page refreshes to this offer: its colour, the cosmetic, the
    # facts and which offer it is -- the way a gate display updates.
    frame = (
        f'<div class="abs" style="inset:0;background:linear-gradient(180deg,#0d1a31,#081226)"></div>'
        f'<div class="abs" style="left:0;top:0;width:{sw}px;height:{bar}px;background:#0f2242;'
        f'box-shadow:inset 0 -2px 0 rgba(255,178,31,.55)"></div>'
        f'<div class="abs" style="left:22px;top:{bar / 2 - 8:.0f}px;width:16px;height:16px;border-radius:50%;'
        f'background-color:{AMBER};animation:dpblink2 1.2s linear 0s infinite"></div>'
        f'<div class="dp-ui abs" style="left:50px;top:0;line-height:{bar}px;font-size:36px;font-weight:800;'
        f'letter-spacing:.08em;color:{AMBER}">LAST CALL</div>'
        f'<div class="abs" style="left:0;top:{sh - foot}px;width:{sw}px;height:{foot}px;background:#0b1a33;'
        f'box-shadow:inset 0 2px 0 rgba(255,255,255,.08)"></div>'
        f'<div class="dp-ui abs" data-fit="{sw - 44}" style="left:22px;top:{sh - foot}px;line-height:{foot}px;'
        f'font-size:31px;font-weight:600;letter-spacing:.08em">LEAVING THE SHOP AT RESET · '
        f'<span style="color:{AMBER};font-weight:800">{esc(ctx.reset_et.upper())}</span></div>')
    page = (
        f'<div class="abs" style="left:0;top:{bar}px;width:{sw}px;height:{sh - bar - foot}px;'
        f'background:radial-gradient(ellipse 62% 58% at 34% 56%,{col}55,{col}14 60%,rgba(0,0,0,0) 100%)"></div>'
        f'<div class="dp-ui abs" style="right:22px;top:0;line-height:{bar}px;font-size:32px;font-weight:600;'
        f'letter-spacing:.1em;color:#d3dbe8">{k} / {n}</div>'
        # the cosmetic, slowly pushing in
        f'<div class="abs" style="left:{ax}px;top:{bar + 14}px;width:{aw}px;height:{ah}px;transform-origin:50% 60%;'
        f'{_a("dpkb", t0, R_ + .3, "linear")}">{pic}</div>'
        f'<div class="abs" style="left:{sw - info_w - 18}px;top:{bar + 14}px;width:{info_w}px;height:{ah}px">'
        f'{"".join(info)}</div>')
    switch = (f'{frame}<div class="abs" style="inset:0;{_a("dpon", t_sw, .01, "steps(1,end)")}">{page}</div>'
              f'<div class="abs" style="inset:0;{_a("dpflash2", t_sw, .24, "ease-out")}"></div>')
    return (f'<div class="dp-mon" style="left:{mx}px;top:{my:.0f}px;width:{mw}px;height:{mh:.0f}px">'
            f'<div class="dp-scr" style="left:{bz}px;top:{bz}px;width:{sw}px;height:{sh:.0f}px">{switch}'
            f'<div class="dp-scan"></div><div class="dp-glass"></div></div>'
            f'<div class="abs" style="right:26px;bottom:6px;width:7px;height:7px;border-radius:50%;background:#5fe07a;'
            f'box-shadow:0 0 6px #5fe07a"></div></div>')


# ---------------------------------------------------------------- build

def last_chance(ctx, picked: list) -> Comp:
    n = len(picked)
    R_ = max(R, min(R_MAX, (62.0 - 7.5 - HOOK) / n))
    content_end = HOOK + n * R_
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    css = CSS
    for k, v in (("slats", tex("departures-slats.jpg")), ("board", tex("departures-board.jpg")),
                 ("grain", tex("departures-grain.png")), ("INK", INK), ("AMBER", AMBER), ("LIME", LIME)):
        css = css.replace(f"@{k}@", v)
    comp.css(css)
    names = [_shown_name(it) for it in picked]
    prices = [int(it["price"]) for it in picked]
    reset = ctx.reset_et.upper()
    head = "DEPARTURES · ITEM SHOP"
    sub = ("LEAVING AT RESET", reset)
    cta = ("WHICH ONE ARE", "YOU GRABBING?")
    bg = _board_geom(names, prices, head)
    gg = _gate_geom(names, prices)
    fl = Flaps(ctx.seed)

    comp.add('<div class="full" style="z-index:0;background:#0c0b0a"></div>')

    def shot(inner: str) -> str:
        return f'<div class="full" style="overflow:hidden">{inner}</div>'

    # ---- hook: the board, complete on frame 0; the rows re-sync, row 1 lights up
    hook = _wall() + _board(fl, bg, prices, head, sub, resync=.35, lit=[(0, 2.2, HOOK + 1)])
    y_row1 = bg["row_y"][0] + bg["rh"][0] / 2
    push = f"transform-origin:320px {y_row1:.0f}px;{_a('dppush', 2.45, HOOK - 2.45 + .05, 'cubic-bezier(.5,0,.9,.5)')}"
    comp.scene(0, HOOK + .02, shot(f'<div class="full" style="{push}">{hook}</div>'), fade_in=.01, fade_out=.01, z=10)
    comp.cue(.1, "ding")
    comp.cue(.35, "flap"); comp.cue(.75, "flap"); comp.cue(1.2, "flap")
    comp.cue(2.2, "click")

    # ---- offers: the gate
    prev = ("", 0)
    for k, it in enumerate(picked, 1):
        t0 = HOOK + (k - 1) * R_
        t1 = t0 + R_
        sign = _gate_sign(fl, gg, names[k - 1], prices[k - 1], prev, t0, k == 1, R_, f"LEAVES|{reset}")
        mon = _monitor(ctx, it, k, n, t0, R_, gg)
        comp.scene(t0 - .04, t1 + .02, shot(_wall(close=True) + sign + mon), fade_in=.01, fade_out=.01, z=11)
        comp.cue(t0 + .02, "flap"); comp.cue(t0 + .3, "flap")
        comp.cue(t0 + .25, "click")
        comp.cue(t0 + .5, "flap"); comp.cue(t0 + min(3.4, R_ * .52), "flap")
        prev = (names[k - 1], prices[k - 1])

    # ---- back on the board: LAST CALL on every row, a light runs down them, and
    # the sub-rows ask the question. On a long hold (a thin day) they go back and
    # forth between the question and the reset time, the way boards page, and
    # the light keeps moving from row to row.
    t = content_end
    end = comp.duration
    t_q = t + 1.5 + n * .16
    lit = [(r, t + .9 + r * .16, t + 1.25 + r * .16) for r in range(n)]
    seq = [(t_q, cta)]
    while seq[-1][0] + 6.5 + 6.5 + 3.5 <= end:
        seq += [(seq[-1][0] + 6.5, sub), (seq[-1][0] + 13.0, cta)]
    j, ts = 0, t_q + 1.8
    while ts + 1.2 < end - .3:
        lit.append((j % n, ts, ts + 1.15))
        j, ts = j + 1, ts + 1.5
    fin = _wall() + _board(fl, bg, prices, head, sub, resync=t + .05, sub_seq=seq, lit=lit)
    drift = f"transform-origin:{(CX0 + CX1) / 2:.0f}px {(bg['top'] + bg['bottom']) / 2:.0f}px"
    comp.scene(t - .04, end, shot(f'<div class="full" style="{drift};'
                                  f'{_a("dpdrift", t, end - t, "ease-in-out")}">{fin}</div>'),
               fade_in=.01, fade_out=.01, z=12)
    comp.cue(t + .08, "ding")
    comp.cue(t + .1, "flap"); comp.cue(t + .5, "flap")
    for ts_, _ in seq:
        comp.cue(ts_, "flap"); comp.cue(ts_ + .4, "flap")

    # ---- the code sign: on screen the whole time, above everything
    comp.add(f'<div class="full" style="z-index:25">{_lens()}</div>')
    comp.add(f'<div class="full" style="z-index:30">{_code_sign()}</div>')
    comp.add(PREP_JS)
    comp.cues.sort()
    return comp
