"""
DEPARTURES -- Last Chance, as an airport split-flap board filmed on a phone.

    0:00  hook     the DEPARTURES · ITEM SHOP board, complete on frame 0: every
                   offer in the video with its price and a blinking LAST CALL,
                   and under it the lime USE CODE: B A D flap sign. The rows
                   re-sync (a cascade of flaps), then the first row lights up.
    0:03  offers   one per offer (R s; a little longer on a thin day, so the
                   video still runs past a minute). Cut to the gate: the gate
                   sign's flaps clatter over to the offer's name and price, and
                   the gate monitor switches to the cosmetic, with its type,
                   how long it's been in the shop, and what a bundle includes.
    ~0:53 board    back on the board: every row flips to LAST CALL again, a
                   light runs down the rows, and the sub-row flips to WHICH ONE
                   ARE YOU GRABBING? It holds there to the end.

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
from cc_motion import RARITY, Comp, esc

HOOK = 3.0
R = 6.2                     # one offer, as the classic format
R_MAX = 9.5                 # a thin day (4-5 offers) stretches each offer up to this
FONTS = ("Barlow Condensed", "Oswald")

INK = "#ece6d7"             # off-white flap print
AMBER = "#ffb21f"
CHARS = "ABCDEFGHIJKLMNOPRSTUVWXYZ0123456789"
SD = .062                   # seconds per flap step
NARROW = {"·", ",", ":", ".", "'"}
NF = .52                    # a separator flap's width, as a share of a letter flap

# The lime code sign, fixed on the wall in both shots (TikTok's safe area is
# y 190-1480; below y 880 nothing right of x 960).
SIGN_X, SIGN_Y, SIGN_W, SIGN_H = 56, 1290, 600, 160
TOP, BOTTOM = 204, 1256     # what the board or the gate monitor may use

# The board: its content stays left of x 950 (its lower rows are below y 880).
BX0, BX1 = 40, 964
CX0, CX1 = 56, 948
GAP = 14                    # between the board's columns


def _a(name, t, dur, ease="linear", extra=""):
    return f"animation:{name} {dur:.3f}s {ease} {t:.3f}s 1 normal both;{extra}"


# ---------------------------------------------------------------- split-flap cells

class Flaps:
    """Split-flap modules. A cell shows `first`; each flip (t, glyph) spins it
    through a few random glyphs and lands on `glyph`: a stepped strip of glyphs
    (one nested wrapper per flip, so the offsets add up) and a flap half that
    falls on every step."""

    def __init__(self, seed: int):
        self.rnd = random.Random(seed)

    @staticmethod
    def glyph(g: str) -> str:
        if not g.strip():
            return "<b>&nbsp;</b>"
        if g == "LAST CALL":
            return '<b class="w2">LAST<br>CALL</b>'
        cls = {"M": ' class="nm"', "W": ' class="nw"'}.get(g, "")
        return f"<b{cls}>{esc(g)}</b>"

    def cell(self, x, y, w, h, fs, first=" ", flips=(), cls="", word=False, lo=5, hi=10) -> str:
        r = self.rnd
        v = r.uniform(-.018, .03)                   # each flap a touch lighter or darker
        oy = r.uniform(-.7, .7)                     # and not quite level
        st = f"left:{x:.1f}px;top:{y:.1f}px;width:{w:.1f}px;height:{h:.0f}px;--h:{h:.0f}px;--fs:{fs:.0f}px;--v:{v:.3f}"
        glyphs = [first]
        opens, pulses = [], []
        for t, g in flips:
            n = r.randint(lo, hi)
            glyphs += ([" "] * (n - 1) if word else [r.choice(CHARS) for _ in range(n - 1)]) + [g]
            opens.append(f'<div style="--d:-{n * h:.0f}px;{_a("dpfl", t, n * SD, f"steps({n},start)")}">')
            pulses.append(f"dppu {SD:.3f}s linear {t:.3f}s {n} forwards")
        strip = "".join(opens) + "".join(self.glyph(g) for g in glyphs) + "</div>" * len(opens)
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


def _run_width(text: str, pitch: float) -> float:
    return sum(pitch * NF if ch in NARROW else pitch for ch in text)


# ---------------------------------------------------------------- shared pieces

CSS = """
.dp-cam{position:absolute;inset:0;animation:dpshake 2.7s ease-in-out 0s infinite alternate}
@keyframes dpshake{0%{transform:translate(0,0)}35%{transform:translate(1.4px,-.9px)}
  70%{transform:translate(-.8px,.6px)}100%{transform:translate(.5px,1.3px)}}
.dp-stage{position:absolute;inset:0;perspective:2300px;perspective-origin:540px 700px}
.dp-tilt{position:absolute;inset:0;transform-origin:540px 760px;
  transform:rotateX(2.4deg) rotateY(1deg) rotateZ(.3deg)}
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
.dp-lab{position:absolute;font-family:'Barlow Condensed';font-weight:600;font-size:21px;letter-spacing:.16em;
  color:#d9d2c1;opacity:.78;white-space:nowrap}
.dp-f{position:absolute;border-radius:3px;overflow:hidden;
  background:linear-gradient(180deg,#333334 0%,#29292a 47%,#202021 50.5%,#262627 53%,#1b1b1c 100%);
  box-shadow:0 1px 1.5px rgba(0,0,0,.8),inset 0 1px 0 rgba(255,255,255,.07)}
.dp-f .s{position:absolute;left:0;width:100%}
.dp-f b{display:block;height:var(--h);line-height:var(--h);text-align:center;color:@INK@;
  font-family:'Barlow Condensed';font-weight:800;font-size:var(--fs);white-space:nowrap}
.dp-f b.nm{transform:scaleX(.86)}
.dp-f b.nw{transform:scaleX(.7)}
.dp-f::before{content:"";position:absolute;inset:0;z-index:2;pointer-events:none;
  background:linear-gradient(180deg,rgba(255,255,255,.07) 0%,rgba(255,255,255,0) 30%,rgba(0,0,0,.08) 47%,
  rgba(0,0,0,.34) 50.5%,rgba(0,0,0,.02) 56%,rgba(0,0,0,.2) 100%),rgba(255,255,255,var(--v))}
.dp-f::after{content:"";position:absolute;left:0;right:0;top:calc(50% - 1px);height:2px;z-index:3;
  background:#060606;box-shadow:0 1px 0 rgba(255,255,255,.08)}
.dp-f .p{position:absolute;left:0;right:0;top:0;height:50%;z-index:4;opacity:0;transform-origin:50% 100%;
  background:linear-gradient(180deg,#4a4a4c 0%,#323234 55%,#1c1c1d 100%)}
@keyframes dppu{0%{opacity:0;transform:scaleY(1)}3%{opacity:1;transform:scaleY(1)}
  70%{opacity:1;transform:scaleY(.1)}100%{opacity:0;transform:scaleY(0)}}
@keyframes dpfl{from{transform:none}to{transform:translateY(var(--d))}}
.dp-f.rem b{letter-spacing:.06em;color:@AMBER@;animation:dpblink 1.2s linear 0s infinite}
.dp-f.rem b.w2{line-height:calc(var(--h) / 2);white-space:normal}
@keyframes dpblink{0%,46%{color:@AMBER@;text-shadow:0 0 5px rgba(255,170,30,.5)}
  50%,96%{color:#a87a22;text-shadow:none}100%{color:@AMBER@;text-shadow:0 0 5px rgba(255,170,30,.5)}}
.dp-lamp{position:absolute;border-radius:50%;
  background:radial-gradient(circle at 40% 35%,#fff3c8 0%,#ffbe3a 35%,#c77a06 75%,#6b3f02 100%);
  box-shadow:0 0 0 2px #0a0a0a,0 0 9px 2px rgba(255,170,30,.5);animation:dplampb 1.2s linear 0s infinite}
@keyframes dplampb{0%,46%{filter:none}50%,96%{filter:brightness(.25) saturate(.6)}100%{filter:none}}
.dp-lit{position:absolute;border-radius:4px;opacity:0;
  box-shadow:0 0 0 2px rgba(255,190,70,.85),0 0 12px 1px rgba(255,170,40,.3),inset 0 0 14px rgba(255,170,40,.18)}
@keyframes dpon{from{opacity:0}to{opacity:1}}
@keyframes dpoff{from{opacity:1}to{opacity:0}}
@keyframes dpflash{0%{opacity:0}25%{opacity:1}100%{opacity:0}}
@keyframes dpflash2{0%{opacity:0}20%{opacity:.35}100%{opacity:0}}
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
.dp-slab{position:absolute;font-family:'Barlow Condensed';font-weight:800;font-size:50px;line-height:52px;
  letter-spacing:.06em;color:@LIME@;white-space:nowrap}
.dp-f.lime{background:linear-gradient(180deg,#efff62 0%,@LIME@ 46%,#d2e62c 50.5%,#e3f736 53%,#d8ec33 100%)}
.dp-f.lime b{color:#111}
.dp-f.lime::before{background:linear-gradient(180deg,rgba(255,255,255,.12) 0%,rgba(255,255,255,0) 32%,
  rgba(0,0,0,.03) 47%,rgba(0,0,0,.14) 50.5%,rgba(0,0,0,0) 56%,rgba(0,0,0,.06) 100%)}
.dp-plate{position:absolute;padding:5px 14px 6px;border-radius:3px;font-family:'Barlow Condensed';font-weight:600;
  font-size:22px;letter-spacing:.08em;color:#2a2926;white-space:nowrap;
  background:linear-gradient(180deg,#b9b6ae,#8f8c85);box-shadow:0 1px 0 rgba(255,255,255,.25) inset,0 2px 4px rgba(0,0,0,.6)}
.dp-grain{position:absolute;left:-256px;top:-256px;width:1592px;height:2432px;pointer-events:none;opacity:.055;
  background:url('@grain@') 0 0/512px 512px repeat;animation:dpgr .5s steps(1,end) 0s infinite}
@keyframes dpgr{0%{transform:translate(0,0)}20%{transform:translate(-131px,77px)}40%{transform:translate(53px,-173px)}
  60%{transform:translate(-201px,-29px)}80%{transform:translate(97px,149px)}}
.dp-vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(125% 80% at 42% 36%,rgba(0,0,0,0) 52%,rgba(0,0,0,.6) 100%)}
.dp-tint{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,rgba(255,190,120,.035) 0%,rgba(0,0,0,0) 45%,rgba(18,28,42,.30) 100%)}

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
@keyframes dpkb{from{transform:scale(1)}to{transform:scale(1.06)}}
@keyframes dpup{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@keyframes dppush{from{transform:scale(1)}to{transform:scale(1.07)}}
@keyframes dpdrift{from{transform:scale(1)}to{transform:scale(1.035)}}
@keyframes dpstrike{from{transform:scaleX(0)}to{transform:scaleX(1)}}
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


def _overlays() -> str:
    return '<div class="dp-tint"></div><div class="dp-grain"></div><div class="dp-vig"></div>'


def _code_sign() -> str:
    """USE CODE: B A D -- painted lime words and three lime flaps, on its own
    dark sign under the board, with a small #EpicPartner plate."""
    fl = Flaps(7)
    x0, y0, w, h = SIGN_X, SIGN_Y, SIGN_W, SIGN_H
    flaps = "".join(fl.cell(x0 + 272 + i * 100, y0 + 13, 92, 134, 118, ch, cls="lime")
                    for i, ch in enumerate("BAD"))
    return (f'<div class="dp-sign" style="left:{x0}px;top:{y0}px;width:{w}px;height:{h}px">'
            f'<div class="abs" style="left:{-x0}px;top:{-y0}px;width:1080px;height:1920px">'
            f'<div class="dp-slab" style="left:{x0 + 30}px;top:{y0 + h / 2 - 26:.0f}px">USE CODE:</div>{flaps}</div>'
            f'<div class="dp-slight"></div></div>'
            f'<div class="dp-plate" style="left:{x0 + w + 22}px;top:{y0 + h - 38}px">#EpicPartner</div>')


# ---------------------------------------------------------------- the board

def _price(p: int) -> str:
    return f"{int(p):,}"


def _board_geom(names: list, prices: list, head: str, subs: list) -> dict:
    n = len(names)
    N = max(12, max(len(s) for s in names))
    D = max(3, max(len(_price(p)) for p in prices))
    width = CX1 - CX0
    # name cells + price cells (the comma is a narrow flap) + lamp and status
    status = 1.42                                     # status flap width in letter pitches
    P = min(42.0, (width - 2 * GAP - 20) / (N + (D - 1) + NF + status))
    if P * status < 76:                               # never narrower than LAST/CALL needs
        P = (width - 2 * GAP - 20 - 76) / (N + (D - 1) + NF)
    cw = P - 3.5
    ch = round(min(cw * 1.6, 74))
    fs = cw * 1.66
    rp = min(ch + 38, 100)
    sw = max(P * status, 76)
    hp = min(44.0, width / (len(head) - sum(c in NARROW for c in head) * (1 - NF)))
    sp = min(40.0, width / max(len(s) for s in subs))
    hh, sh = round((hp - 3.5) * 1.6), round((sp - 3.5) * 1.6)
    head_h = 20 + hh + 16 + sh + 14 + 26 + 10
    total = head_h + n * rp + 10
    top = TOP + max(0, (BOTTOM - TOP - total) / 2)
    return dict(n=n, N=N, D=D, P=P, cw=cw, ch=ch, fs=fs, rp=rp, sw=sw, hp=hp, sp=sp, hh=hh, sh=sh,
                top=top, bottom=top + total, head_y=top + 20, sub_y=top + 20 + hh + 16,
                lab_y=top + 20 + hh + 16 + sh + 14, row0=top + head_h)


def _board(fl: Flaps, g: dict, names: list, prices: list, head: str, sub: str, *, resync=None,
           sub_seq=(), lit=None, cells_sub=0) -> str:
    """The departures board. resync: time the rows re-sync (a cascade over the same
    text); sub_seq: [(time, text)] the sub-row flips to, in turn; lit: [(row,
    t_on, t_off)] rows that light up."""
    x = CX0
    parts = []
    # the header and the sub-row
    s, _ = fl.run(x, g["head_y"], head, g["hp"], g["hp"] - 3.5, g["hh"], (g["hp"] - 3.5) * 1.62, narrow=True)
    parts.append(s)
    sub_cells = max([len(sub), cells_sub] + [len(t) for _, t in sub_seq])
    sub_txt = sub.ljust(sub_cells)
    seq = [(t, txt.ljust(sub_cells)) for t, txt in sub_seq]

    def fa(i, ch):
        out, cur = [], ch
        for t, txt in seq:
            if cur != " " or txt[i] != " ":
                out.append((t + i * .018 + fl.rnd.uniform(0, .06), txt[i]))
            cur = txt[i]
        return out
    s, _ = fl.run(x, g["sub_y"], sub_txt, g["sp"], g["sp"] - 3.5, g["sh"], (g["sp"] - 3.5) * 1.62,
                  flips_at=fa if seq else None)
    parts.append(s)
    # the rows
    P, cw, ch, fs = g["P"], g["cw"], g["ch"], g["fs"]
    col_price = x + g["N"] * P + GAP
    price_w = (g["D"] - 1) * P + P * NF
    col_status = col_price + price_w + GAP
    for r, (nm, pr) in enumerate(zip(names, prices)):
        y = g["row0"] + r * g["rp"]
        t_r = resync + r * .11 if resync is not None else None
        fa = (lambda i, c, t_r=t_r: [(t_r + i * .012 + fl.rnd.uniform(0, .07), c)] if c != " " else ()) \
            if t_r is not None else None
        s, _ = fl.run(x, y, nm.upper().ljust(g["N"]), P, cw, ch, fs, flips_at=fa)
        parts.append(s)
        pt = _price(pr).rjust(g["D"])
        # the comma slot is narrow in every row, so the digits line up
        px = col_price
        for i, c in enumerate(pt):
            nar = i == g["D"] - 4 and g["D"] >= 5
            w_ = cw * NF if nar else cw
            fl_ = [(t_r + .25 + i * .012 + fl.rnd.uniform(0, .07), c)] if (t_r is not None and c != " ") else ()
            parts.append(fl.cell(px, y, w_, ch, fs, c, fl_))
            px += P * NF if nar else P
        lamp = max(10, ch * .22)
        parts.append(f'<div class="dp-lamp" style="left:{col_status:.1f}px;top:{y + ch / 2 - lamp / 2:.1f}px;'
                     f'width:{lamp:.0f}px;height:{lamp:.0f}px"></div>')
        st_x = col_status + lamp + 7
        fl_ = [(t_r + .4, "LAST CALL")] if t_r is not None else ()
        parts.append(fl.cell(st_x, y, CX1 - st_x, ch, max(15, ch * .46), "LAST CALL", fl_, "rem", word=True,
                             lo=3, hi=5))
        if lit:
            for row, t_on, t_off in lit:
                if row == r:
                    parts.append(f'<div class="dp-lit" style="left:{x - 6:.0f}px;top:{y - 5:.0f}px;'
                                 f'width:{CX1 - x + 12:.0f}px;height:{ch + 10:.0f}px;'
                                 f'animation:dpon .12s linear {t_on:.3f}s 1 normal both,'
                                 f'dpoff .25s linear {t_off:.3f}s 1 normal forwards"></div>')
    lfs = min(21, max(16, P * .6))
    parts.append(f'<div class="dp-lab" style="left:{x + 1:.0f}px;top:{g["lab_y"]:.0f}px;font-size:{lfs:.0f}px">ITEM</div>'
                 f'<div class="dp-lab" style="right:{1080 - col_price - price_w:.0f}px;top:{g["lab_y"]:.0f}px;'
                 f'font-size:{lfs:.0f}px;letter-spacing:.1em">V-BUCKS</div>'
                 f'<div class="dp-lab" style="left:{col_status:.0f}px;top:{g["lab_y"]:.0f}px;font-size:{lfs:.0f}px">STATUS</div>')
    cells = "".join(parts)

    bx, by, bw, bh = BX0, g["top"], BX1 - BX0, g["bottom"] - g["top"]
    chans = "".join(f'<div class="dp-chan" style="left:8px;right:8px;top:{g["row0"] + r * g["rp"] - 5 - by:.0f}px;'
                    f'height:{ch + 10:.0f}px"></div>' for r in range(g["n"]))
    chans += (f'<div class="dp-chan" style="left:8px;right:8px;top:{g["head_y"] - 5 - by:.0f}px;height:{g["hh"] + 10}px"></div>'
              f'<div class="dp-chan" style="left:8px;right:8px;top:{g["sub_y"] - 5 - by:.0f}px;height:{g["sh"] + 10}px"></div>'
              f'<div class="dp-rail" style="left:8px;right:8px;top:{g["sub_y"] + g["sh"] + 7 - by:.0f}px"></div>')
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
        while any(len(_wrap(s, C)) > 2 or max(len(l) for l in _wrap(s, C)) > C for s in names):
            C += 1
        lines = 2
    P = min(60.0, (1044 - 36 - 36) / C)
    cw = P - 4
    ch = round(cw * 1.55)
    D = max(3, max(len(_price(p)) for p in prices))
    top = TOP - 4
    y_name = top + 22
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


def _gate_sign(fl: Flaps, g: dict, name: str, price: int, prev: tuple, t0: float, first: bool) -> tuple:
    """The gate's flap sign: the name, then the price in V-Bucks and LAST CALL.
    Its cells start on the previous offer's text and clatter over to this one's."""
    x0 = 36
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
    parts.append(f'<div class="dp-lab" style="left:{x + 12:.0f}px;top:{g["y_b"] + hb / 2 - 17:.0f}px;font-size:30px;'
                 f'font-weight:800;opacity:.85">V-BUCKS</div>')
    # the status: a blinking lamp and the LAST CALL flap
    sx = 1044 - 36 - 190
    parts.append(f'<div class="dp-lab" style="left:{sx - 150:.0f}px;top:{g["y_b"] + hb / 2 - 13:.0f}px">STATUS</div>')
    parts.append(f'<div class="dp-lamp" style="left:{sx - 30:.0f}px;top:{g["y_b"] + hb / 2 - 9:.0f}px;width:18px;height:18px"></div>')
    fl_ = [(t0 + .5, "LAST CALL")] if first else ()
    parts.append(fl.cell(sx, g["y_b"], 190, hb, hb * .44, " " if first else "LAST CALL", fl_, "rem", word=True,
                         lo=3, hi=5))
    bw, bh = 1044 - 36 + 20, g["bottom"] - g["top"]
    bx, by = 26, g["top"]
    chans = "".join(f'<div class="dp-chan" style="left:8px;right:8px;top:{g["y_name"] + li * (ch + 10) - 5 - by:.0f}px;'
                    f'height:{ch + 10:.0f}px"></div>' for li in range(g["lines"]))
    chans += (f'<div class="dp-chan" style="left:8px;right:8px;top:{g["y_b"] - 5 - by:.0f}px;height:{hb + 10}px"></div>')
    screws = "".join(f'<div class="dp-screw" style="left:{sx_}px;top:{sy:.0f}px"></div>'
                     for sx_, sy in ((10, 10), (10, bh - 20), (bw - 20, 10), (bw - 20, bh - 20)))
    html = (f'<div class="dp-bd" style="left:{bx}px;top:{by:.0f}px;width:{bw}px;height:{bh:.0f}px">'
            f'{chans}{screws}<div class="abs" style="left:{-bx}px;top:{-by:.0f}px;width:1080px;height:1920px">'
            f'{"".join(parts)}</div><div class="dp-shade"></div><div class="dp-blight"></div>'
            f'<div class="edge"></div></div>')
    return html


def _monitor(ctx, it: dict, k: int, n: int, t0: float, R_: float, g: dict) -> str:
    """The gate monitor: the cosmetic, and beside it what the classic format says
    about the offer. It switches over at t0 + .25."""
    mx, my, mw = 40, g["bottom"] + 34, 910
    mh = BOTTOM - my
    bz = 22
    sw, sh = mw - 2 * bz, mh - 2 * bz
    bar, foot = 58, 54
    col = RARITY.get(it.get("rarity"), "#6a7384")
    art = ctx.art(it)
    name = _shown_name(it)
    info_w = 292
    ax, aw, ah = 18, sw - info_w - 36, sh - bar - foot - 24
    if art:
        pic = (f'<img data-trim data-bake="drop-shadow(0 18px 18px rgba(0,0,0,.55))" data-pad="50" src="{art}" '
               f'style="position:absolute;left:0;top:0;width:{aw}px;height:{ah}px;object-fit:contain">')
    else:
        pic = (f'<div class="dp-ui" data-fit="{aw - 60}" data-lines="3" style="position:absolute;left:30px;'
               f'top:{ah / 2 - 100:.0f}px;width:{aw - 60}px;white-space:normal;text-align:center;font-weight:800;'
               f'font-size:72px;line-height:1;color:rgba(233,238,247,.9)">{esc(name.upper())}</div>')
    t_sw = t0 + .25
    # the info column: blocks of (label, value), centred beside the cosmetic
    bundle = bool(it.get("is_bundle"))
    vfs = 40 if bundle else 50
    blocks = []                                   # (html, height)
    lab = lambda t: (f'<div class="dp-ui" style="font-size:21px;font-weight:600;letter-spacing:.16em;'
                     f'color:#8fa0b8">{t}</div>')
    meta = esc(_meta(it))
    val = meta.replace("BUNDLE · ", "BUNDLE<br>") if bundle else meta
    nl = 2 if "<br>" in val else 1
    blocks.append((lab("TYPE") + f'<div class="dp-ui" data-fit="{info_w}" style="font-size:{vfs}px;font-weight:800;'
                   f'line-height:1.02;margin-top:4px">{val}</div>', 30 + vfs * 1.02 * nl))
    since = _since(it, ctx)
    if since:
        head_, v = ("IN THE SHOP", "ADDED TODAY") if since == "ADDED TODAY" else \
            ("IN THE SHOP SINCE", since.replace("IN THE SHOP SINCE ", ""))
        blocks.append((lab(head_) + f'<div class="dp-ui" data-fit="{info_w}" style="font-size:{vfs}px;'
                       f'font-weight:800;line-height:1.02;margin-top:4px">{esc(v)}</div>', 30 + vfs * 1.02))
    reg = _regular(it)
    if reg:
        blocks.append((lab("REGULAR PRICE") + f'<div class="dp-ui" style="position:relative;display:inline-block;'
                       f'font-size:40px;font-weight:800;color:#b8c2d2;margin-top:4px">{reg:,}<span style="position:'
                       f'absolute;left:-4px;right:-4px;top:52%;height:4px;background:#ff5a4f;transform-origin:0 50%;'
                       f'{_a("dpstrike", t0 + 1.4, .25, "ease-out")}"></span></div>', 30 + 42))
    members = _members(it) if bundle else []
    gap = 44 if not bundle else 30
    if members:
        used = sum(h for _, h in blocks) + gap * len(blocks)
        room = int((ah - 40 - used - 32) // 33)
        shown = members if len(members) <= room else members[:max(1, room - 1)]
        more = len(members) - len(shown)
        lis = "".join(f'<div class="dp-ui" data-fit="{info_w}" style="font-size:27px;font-weight:600;'
                      f'line-height:33px">{esc(m)}</div>' for m in shown)
        if more:
            lis += (f'<div class="dp-ui" style="font-size:27px;font-weight:600;line-height:33px;color:#8fa0b8">'
                    f'+ {more} more</div>')
        blocks.append((f'<div style="margin-bottom:6px">{lab("INCLUDES")}</div>{lis}',
                       32 + 33 * (len(shown) + (1 if more else 0))))
    total = sum(h for _, h in blocks) + gap * (len(blocks) - 1)
    y = max(10, (ah - total) / 2 - 10)
    info = []
    for i, (html, h) in enumerate(blocks):
        if i:
            info.append(f'<div class="abs" style="left:0;top:{y - gap / 2:.0f}px;width:{info_w - 20}px;height:1px;'
                        f'background:rgba(201,211,226,.16);{_a("dpon", t0 + .7 + i * .16, .3)}"></div>')
        info.append(f'<div class="abs" style="left:0;top:{y:.0f}px;width:{info_w}px;'
                    f'{_a("dpup", t0 + .7 + i * .16, .3, "cubic-bezier(.2,.8,.2,1)")}">{html}</div>')
        y += h + gap
    screen = (
        f'<div class="abs" style="inset:0;background:radial-gradient(ellipse 62% 58% at 34% 56%,{col}55,{col}14 60%,'
        f'rgba(0,0,0,0) 100%),linear-gradient(180deg,#0d1a31,#081226)"></div>'
        # top bar: LAST CALL, and which offer this is
        f'<div class="abs" style="left:0;top:0;width:{sw}px;height:{bar}px;background:#0f2242;'
        f'box-shadow:inset 0 -2px 0 rgba(255,178,31,.55)"></div>'
        f'<div class="abs" style="left:22px;top:{bar / 2 - 8:.0f}px;width:16px;height:16px;border-radius:50%;'
        f'background:{AMBER};animation:dpblink2 1.2s linear 0s infinite"></div>'
        f'<div class="dp-ui abs" style="left:50px;top:0;line-height:{bar}px;font-size:34px;font-weight:800;'
        f'letter-spacing:.08em;color:{AMBER}">LAST CALL</div>'
        f'<div class="dp-ui abs" style="right:22px;top:0;line-height:{bar}px;font-size:30px;font-weight:600;'
        f'letter-spacing:.1em;color:#c9d3e2">{k} / {n}</div>'
        # the cosmetic, slowly pushing in
        f'<div class="abs" style="left:{ax}px;top:{bar + 12}px;width:{aw}px;height:{ah}px;transform-origin:50% 60%;'
        f'{_a("dpkb", t0, R_ + .3, "linear")}">{pic}</div>'
        f'<div class="abs" style="left:{sw - info_w - 18}px;top:{bar + 12}px;width:{info_w}px;height:{ah}px">'
        f'{"".join(info)}</div>'
        # bottom bar: when it leaves
        f'<div class="abs" style="left:0;top:{sh - foot}px;width:{sw}px;height:{foot}px;background:#0b1a33;'
        f'box-shadow:inset 0 2px 0 rgba(255,255,255,.08)"></div>'
        f'<div class="dp-ui abs" style="left:22px;top:{sh - foot}px;line-height:{foot}px;font-size:28px;'
        f'font-weight:600;letter-spacing:.1em">LEAVING THE SHOP AT RESET · '
        f'<span style="color:{AMBER};font-weight:800">{esc(ctx.reset_et.upper())}</span></div>')
    switch = (f'<div class="abs" style="inset:0;{_a("dpon", t_sw, .1)}">{screen}</div>'
              f'<div class="abs" style="inset:0;background:#9fb4d8;opacity:0;mix-blend-mode:screen;'
              f'{_a("dpflash2", t_sw, .22, "ease-out")}"></div>')
    return (f'<div class="dp-mon" style="left:{mx}px;top:{my:.0f}px;width:{mw}px;height:{mh:.0f}px">'
            f'<div class="dp-scr" style="left:{bz}px;top:{bz}px;width:{sw}px;height:{sh:.0f}px">{switch}'
            f'<div class="dp-scan"></div><div class="dp-glass"></div></div>'
            f'<div class="abs" style="right:28px;bottom:7px;width:7px;height:7px;border-radius:50%;background:#5fe07a;'
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
    comp.css("@keyframes dpblink2{0%,46%{opacity:1}50%,96%{opacity:.25}100%{opacity:1}}")
    names = [_shown_name(it) for it in picked]
    prices = [int(it["price"]) for it in picked]
    reset = ctx.reset_et.upper()
    head = "DEPARTURES · ITEM SHOP"
    sub = f"LEAVING AT RESET · {reset}"
    cta = "WHICH ONE ARE YOU GRABBING?"
    bg = _board_geom(names, prices, head, [sub, cta])
    gg = _gate_geom(names, prices)
    fl = Flaps(ctx.seed)

    comp.add('<div class="full" style="z-index:0;background:#0c0b0a"></div>')

    def shot(inner: str, push: str = "") -> str:
        return (f'<div class="full"><div class="dp-cam"><div class="dp-stage"><div class="dp-tilt" '
                f'style="{push}">{inner}</div></div></div>{_overlays()}</div>')

    # ---- hook: the board, complete on frame 0; the rows re-sync, row 1 lights up
    hook = _wall() + _board(fl, bg, names, prices, head, sub, resync=.35, lit=[(0, 2.2, HOOK + 1)],
                            cells_sub=len(cta))
    y_row1 = bg["row0"] + bg["ch"] / 2
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
        sign = _gate_sign(fl, gg, names[k - 1], prices[k - 1], prev, t0, k == 1)
        mon = _monitor(ctx, it, k, n, t0, R_, gg)
        comp.scene(t0 - .04, t1 + .02, shot(_wall(close=True) + sign + mon), fade_in=.01, fade_out=.01, z=11)
        comp.cue(t0 + .02, "flap"); comp.cue(t0 + .3, "flap")
        comp.cue(t0 + .25, "click")
        prev = (names[k - 1], prices[k - 1])

    # ---- back on the board: LAST CALL on every row, a light runs down them, and
    # the sub-row asks the question. On a long hold (a thin day) the sub-row goes
    # back and forth between the question and the reset time, the way boards
    # page, and the light keeps moving from row to row.
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
    fin = _wall() + _board(fl, bg, names, prices, head, sub, resync=t + .05, sub_seq=seq, lit=lit)
    comp.scene(t - .04, end, shot(f'<div class="full" style="transform-origin:950px 700px;'
                                  f'{_a("dpdrift", t, end - t, "ease-in-out")}">{fin}</div>'),
               fade_in=.01, fade_out=.01, z=12)
    comp.cue(t + .08, "ding")
    comp.cue(t + .1, "flap"); comp.cue(t + .5, "flap")
    for ts_, _ in seq:
        comp.cue(ts_, "flap"); comp.cue(ts_ + .4, "flap")

    # ---- the code sign: on screen the whole time, above everything
    comp.add(f'<div class="full" style="z-index:30"><div class="dp-cam">{_code_sign()}</div></div>')
    comp.add(PREP_JS)
    comp.cues.sort()
    return comp
