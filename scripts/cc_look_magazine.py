"""
MAGAZINE -- On This Day as a stack of glossy magazine covers landing on a
stone table: every year is a new issue of DROP, an invented shop magazine.

    0:00  hook      the SPECIAL ISSUE on the table, complete on frame 0: the
                    masthead, ON THIS DAY, the date, the span of years, the two
                    lead cosmetics as cover stars, and the lime USE CODE: BAD
                    price sticker. The light catches the gloss once.
    0:03  issues    one cover per year (6.5 s): it drops onto the pile from
                    above, lands with weight (the pile shifts under it, its
                    shadow tightens) and the light sweeps once over the glossy
                    paper. The masthead huge across the top, the date line
                    "SEPTEMBER 28, 2019 · ON THIS DAY" and ISSUE 2/8, the
                    cosmetic as the cover star in front of the masthead, the
                    year big, the cover lines down the side (FIRST DAY IN THE
                    ITEM SHOP! or IN THE ITEM SHOP THAT DAY, the name as the
                    headline, its rarity and type) and a barcode. A debut gets
                    a red NEW THAT DAY! flash slapped on. The earlier issues
                    peek out below. On Sep 26 the first issue is a COLLECTOR'S
                    EDITION: Fortnite Battle Royale is out!
    ~0:55  outro    a NEXT ISSUE page lands on the pile: which year had the best
                    shop?, the lead picks with their years, and a bigger code
                    sticker slapped over the small one.

Facts on screen are the classic format's: the date, each year, the name, its
rarity and type, "first day in the shop"/NEW THAT DAY only when the plan says
so, the span, the birthday page and the outro question. The masthead is an
invented magazine; nothing imitates a real publication or Epic's own UI.

The code sticker is fixed in screen space at the lower left of the cover,
above every cover (they land under it), on screen and at rest in every frame.

Layout: everything a viewer reads sits inside the apps' safe box (cc_safe:
x 60-1020 above y 740, x 60-900 from there to y 1420, frame 0's text below
y 285). The cover is 880x1144 at x 100-980, y 246-1390; its right strip below
y 740 (under the apps' buttons) carries only backdrop and the barcode, which is
marked as decoration. The table and the older covers' edges run to the edges.

Render cost: covers only move by transform (the drop) and are still after it;
shadows are box-shadows or a pre-blurred sprite; the stars' shadows and the
text fitting are drawn once, before frame 0 (MG_JS).
"""

import math
import random
import zlib

from cc_looks import KIT_CSS, LIME, PREP_JS, pad_to, tex
from cc_motion import RARITY, Comp, esc

HOOK = 3.0
R = 6.5
MAST = "DROP"                      # the invented magazine
FONTS = ("Playfair Display", "Barlow Condensed")

# The cover at rest, unturned (frame px). Poses turn it a degree or two.
CX, CY, CW, CH = 100, 246, 880, 1144
# Font metrics (em), measured in the render browser: ascent, descent, cap height.
PF = (1.082, .251, .708)           # Playfair Display
BC = (1.000, .200, .700)           # Barlow Condensed
IN = (.969, .242, .727)            # Inter

# Inside the cover (cover px; frame = cover + (100, 246)).
TOP_CAP = 47                       # the date line / issue number (cap top)
MAST_F, MAST_CAP = 282, 94         # the masthead: size, cap top
COL_X, COL_W = 34, 328             # the cover lines, down the left side
YEAR_F, YEAR_CAP = 200, 322
STAR = (352, 198, 430, 914)        # the cover star's box: left, top, width, height
BAR = (694, 1040, 150, 84)         # the barcode block (bottom right, under the rail)

# The code: a lime price sticker, fixed in screen space at the cover's lower left.
CODE_W, CODE_H, CODE_ROT = 290, 204, -3.5
_cs, _sn = math.cos(math.radians(abs(CODE_ROT))), math.sin(math.radians(abs(CODE_ROT)))
CODE_BW, CODE_BH = CODE_W * _cs + CODE_H * _sn, CODE_W * _sn + CODE_H * _cs
CODE_CX, CODE_CY = 270, 1280
BIG_K = 1.2                        # the outro's sticker, slapped over the small one
BIG_CX, BIG_CY = CODE_CX + 14, 1394 - CODE_BH * BIG_K / 2

INK = "#161514"
RED = "#D8352A"
CREAM = "#FBF3E4"

# Issue colours: backdrop, masthead, text, big year, kicker box (bg, fg).
THEMES = [
    dict(bg="#F0E6D3", mast=RED, text=INK, year=INK, kbg=RED, kfg=CREAM),                    # cream
    dict(bg="#2447C0", mast=CREAM, text=CREAM, year="#FF9FBC", kbg="#FF9FBC", kfg="#101A44"),  # cobalt
    dict(bg="#EE7A2F", mast=INK, text=INK, year=CREAM, kbg=INK, kfg="#FFC79E"),                # tangerine
    dict(bg="#0F6863", mast=CREAM, text=CREAM, year="#FFB36E", kbg="#FFB36E", kfg="#0A2E2B"),  # teal
    dict(bg="#F2A9C1", mast=INK, text=INK, year=RED, kbg=INK, kfg="#F7C6D6"),                  # pink
    dict(bg="#2D5A3A", mast=CREAM, text=CREAM, year="#F3BE55", kbg="#F3BE55", kfg="#15301C"),  # forest
    dict(bg="#A6CEEA", mast="#15254B", text="#15254B", year=RED, kbg="#15254B", kfg="#E4F1FA"),  # sky
    dict(bg="#5B2C7E", mast=CREAM, text=CREAM, year="#FFB36E", kbg="#FFB36E", kfg="#2A1140"),  # plum
    dict(bg="#C9A227", mast=INK, text=INK, year=CREAM, kbg=INK, kfg="#F2DB8A"),                # mustard
]
SPECIAL = dict(bg="#D8352A", mast=CREAM, text=CREAM, year=INK, kbg=INK, kfg=CREAM)
COLLECTOR = dict(bg="#171615", mast="#D8B45C", text=CREAM, year=CREAM, kbg="#D8B45C", kfg="#171615")
TEASER = dict(bg="#F4EEE2", mast=RED, text=INK, year=RED, kbg=RED, kfg=CREAM)

# Rest poses (dx, dy, turn) in pile order: each stays within a degree or two so
# its text keeps inside the safe box; the pile underneath peeks out at the edges.
POSES = [(0, 6, -.5), (9, -3, 1.3), (-11, 7, -1.6), (12, 1, .9), (-7, -7, -1.2), (10, 8, 1.7),
         (-12, -1, -.8), (7, -6, 1.4), (-9, 9, -1.8), (11, 3, .7), (-6, 2, -1.3), (5, -4, 1.0)]
FALL = .42                         # seconds in the air before it hits the pile
SKID = .22                         # sliding to a stop after the hit


def _top(y: float, f: float, m: tuple, lh: float = 1.0) -> float:
    """The box top that puts a line's cap top at y (font size f, metrics m,
    line-height lh)."""
    asc, desc, cap = m
    return y - ((lh - asc - desc) / 2 + asc - cap) * f


def _a(name: str, t: float, dur: float, ease: str = "linear", fill: str = "both") -> str:
    return f"{name} {dur:.3f}s {ease} {t:.3f}s 1 normal {fill}"


def _ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


CSS = """
.mg-table{position:absolute;inset:0;background:
  radial-gradient(ellipse 95% 70% at 26% 18%,rgba(255,246,228,.13),rgba(255,246,228,0) 62%),
  radial-gradient(ellipse 120% 95% at 50% 46%,rgba(0,0,0,0) 52%,rgba(0,0,0,.5) 100%),
  url('@table@') center/cover}
.mg-slot{position:absolute;left:@CX@px;top:@CY@px;width:@CW@px;height:@CH@px}
.mg-drop,.mg-fall{position:absolute;inset:0}
.mg-far{position:absolute;left:-90px;top:-90px;width:1060px;height:1324px;
  background:url('@shadow@') center/100% 100%;opacity:0}
.mg-contact{position:absolute;inset:0;border-radius:3px;
  box-shadow:0 1px 1.5px rgba(0,0,0,.42),0 5px 9px rgba(0,0,0,.24),0 16px 30px -4px rgba(0,0,0,.42)}
.mg-cover{position:absolute;inset:0;overflow:hidden;border-radius:3px}
.mg-cover>.fx{position:absolute;inset:0;pointer-events:none;z-index:20}
.mg-grain{background:url('@grain@') 0 0/256px 256px;opacity:.5}
.mg-gloss{background:linear-gradient(122deg,rgba(255,255,255,.16) 0%,rgba(255,255,255,.05) 24%,
  rgba(255,255,255,0) 42%,rgba(255,255,255,0) 68%,rgba(0,0,0,.07) 100%)}
.mg-edge{border-radius:3px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.16),inset 0 0 0 2px rgba(0,0,0,.05)}
.mg-spine{right:auto!important;width:16px;
  background:linear-gradient(90deg,rgba(0,0,0,.20),rgba(0,0,0,.05) 70%,rgba(255,255,255,.18) 88%,rgba(255,255,255,0))}
.mg-sweep{position:absolute;left:0;top:-30%;width:330px;height:160%;pointer-events:none;z-index:21;
  background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.13) 34%,rgba(255,255,255,.24) 50%,
  rgba(255,255,255,.13) 66%,rgba(255,255,255,0));transform:translateX(-520px) rotate(14deg)}
.mg-mast{position:absolute;left:0;width:100%;text-align:center;font-family:'Playfair Display';font-weight:900;
  line-height:1;letter-spacing:-.02em;text-indent:-.02em;white-space:nowrap}
.mg-line{position:absolute;font-family:'Inter';font-weight:700;font-size:25px;line-height:1;letter-spacing:.09em;
  white-space:nowrap;text-transform:uppercase}
.mg-year{position:absolute;font-family:'Barlow Condensed';font-weight:800;line-height:1;white-space:nowrap;
  letter-spacing:-.01em}
.mg-cl{font-family:'Barlow Condensed';font-weight:800;text-transform:uppercase;line-height:1.02;letter-spacing:.02em}
.mg-kick{display:inline;padding:2px 12px 0;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.mg-name{font-family:'Playfair Display';font-weight:900;line-height:.98;text-wrap:balance}
.mg-kind{font-family:'Barlow Condensed';font-weight:800;font-size:29px;letter-spacing:.12em;text-transform:uppercase;
  line-height:1.1;display:flex;align-items:flex-start;gap:12px}
.mg-kind i{flex:none;width:18px;height:18px;margin-top:6px;border-radius:2px;box-shadow:0 0 0 2px rgba(255,255,255,.55)}
.mg-rule{display:flex;align-items:center;gap:18px}
.mg-rule i{flex:1;height:2px}
.mg-bar{position:absolute;background:#fbfaf6;padding:8px 7px 4px;box-shadow:0 0 0 1px rgba(0,0,0,.08)}
.mg-bar div{font-family:'Inter';font-weight:600;font-size:11px;letter-spacing:.16em;color:#222;text-align:center;
  margin-top:2px;white-space:nowrap}
.mg-star,.mg-shade{position:absolute;display:block}
.mg-shade{opacity:.36}
.mg-ph{display:flex;align-items:flex-start;justify-content:center}
.mg-ph div{font-family:'Playfair Display';font-weight:900;font-size:560px;line-height:1;opacity:.22}
.mg-flash{position:absolute;border-radius:50%;background:#D8352A;color:#FFF4E0;display:flex;flex-direction:column;
  align-items:center;justify-content:center;text-align:center;font-family:'Barlow Condensed';font-weight:800;
  text-transform:uppercase;line-height:.9;box-shadow:0 1px 1px rgba(0,0,0,.35),0 5px 10px rgba(0,0,0,.25)}
.mg-code{position:absolute;width:@CODE_W@px;height:@CODE_H@px;border-radius:14px;color:#111;transform-origin:50% 50%;
  background:linear-gradient(158deg,rgba(255,255,255,.2),rgba(255,255,255,0) 38%,rgba(0,0,0,0) 72%,rgba(0,0,0,.05)),@LIME@;
  box-shadow:0 1px 1px rgba(0,0,0,.45),0 3px 6px rgba(0,0,0,.22),0 12px 20px -4px rgba(0,0,0,.4);
  display:flex;flex-direction:column;align-items:center;justify-content:center}
.mg-code::before{content:"";position:absolute;inset:9px;border:2px solid rgba(17,17,17,.82);border-radius:8px}
.mg-code .u{font-family:'Barlow Condensed';font-weight:800;font-size:40px;line-height:1;letter-spacing:.09em;
  margin:8px 0 -6px .09em}
.mg-code .b{font-family:'Barlow Condensed';font-weight:800;font-size:152px;line-height:.86;letter-spacing:.01em}
.mg-code .h{font-family:'Inter';font-weight:700;font-size:21px;line-height:1;letter-spacing:.02em;margin:0 0 10px}
@keyframes mgshow{from{visibility:hidden}to{visibility:visible}}
@keyframes mgslide{0%{transform:translate(var(--sx),var(--sy)) rotate(var(--sr))}
  100%{transform:translate(var(--x),var(--y)) rotate(var(--r))}}
@keyframes mgfall{0%{transform:scale(var(--s0))}100%{transform:scale(1)}}
@keyframes mgfar{0%{opacity:.95;transform:translate(78px,120px) scale(1.04)}100%{opacity:0;transform:translate(6px,9px)}}
@keyframes mgland{from{opacity:0}to{opacity:1}}
@keyframes mgnudge{from{transform:translate(0,0)}to{transform:translate(var(--nx),var(--ny))}}
@keyframes mgsweep{from{transform:translateX(-520px) rotate(14deg)}to{transform:translateX(1140px) rotate(14deg)}}
@keyframes mgpress{0%,100%{transform:rotate(var(--r)) scale(var(--k))}28%{transform:rotate(var(--r)) scale(calc(var(--k) * .968))}}
@keyframes mgslap{0%{opacity:0;transform:translate(26px,-40px) scale(calc(var(--k) * 1.22)) rotate(calc(var(--r) + 7deg))}
  1%{opacity:1}
  60%{opacity:1;transform:translate(0,0) scale(calc(var(--k) * .98)) rotate(var(--r))}
  100%{opacity:1;transform:translate(0,0) scale(var(--k)) rotate(var(--r))}}
"""


def _css() -> str:
    return (CSS.replace("@table@", tex("magazine-table.jpg")).replace("@shadow@", tex("magazine-shadow.png"))
            .replace("@grain@", tex("magazine-grain.png")).replace("@LIME@", LIME)
            .replace("@CX@", str(CX)).replace("@CY@", str(CY)).replace("@CW@", str(CW)).replace("@CH@", str(CH))
            .replace("@CODE_W@", str(CODE_W)).replace("@CODE_H@", str(CODE_H)))


# Run before frame 0, after PREP_JS has cropped the art (it chains on its
# promise): each cover star is sized into its box (never past 1.35x its own
# pixels), top-anchored so its head sits in front of the masthead (or standing
# on the box's floor), and gets a soft studio shadow drawn once into a separate
# picture behind it (marked as decoration for the safe-zone check). Then the
# cover lines shrink to fit: [data-mgfit="<max width>"] and data-lines="<n>",
# checked both ways (no word may run out sideways either).
MG_JS = """<script>(() => {
  const prev = window.__ready;
  window.__ready = (async () => {
    if (prev) { try { await prev; } catch (e) {} }
    try {
      for (const img of document.querySelectorAll('img[data-mgstar]')) {
        try {
          if (img.decode) { await img.decode(); }
          const w = img.naturalWidth, h = img.naturalHeight, box = img.parentElement;
          if (!w || !h) continue;
          const W = box.clientWidth, H = box.clientHeight;
          const s = Math.min(W / w, H / h, 1.35);
          const dw = w * s, dh = h * s;
          const left = (W - dw) / 2, top = img.dataset.mgstar === 'floor' ? H - dh : 0;
          Object.assign(img.style, {left: left + 'px', top: top + 'px', width: dw + 'px', height: dh + 'px'});
          const P = Math.ceil(34 / s), c = document.createElement('canvas');
          c.width = w + 2 * P; c.height = h + 2 * P;
          const g = c.getContext('2d');
          g.filter = `brightness(0) blur(${(15 / s).toFixed(1)}px)`;
          g.drawImage(img, P, P);
          const sh = document.createElement('img');
          sh.className = 'mg-shade';
          sh.setAttribute('data-safe', 'ignore');
          sh.src = c.toDataURL('image/png');
          if (sh.decode) { await sh.decode(); }
          Object.assign(sh.style, {left: (left - P * s + 16) + 'px', top: (top - P * s + 20) + 'px',
                                   width: (dw + 2 * P * s) + 'px', height: (dh + 2 * P * s) + 'px'});
          box.insertBefore(sh, img);
        } catch (e) {}
      }
      await document.fonts.ready;
      for (const el of document.querySelectorAll('[data-mgfit]')) {
        const maxW = +el.dataset.mgfit, lines = +(el.dataset.lines || 1);
        let size = parseFloat(getComputedStyle(el).fontSize), guard = 90;
        const lh = () => parseFloat(getComputedStyle(el).lineHeight) || size * 1.1;
        const tooBig = () => el.scrollWidth > maxW + 2 || el.offsetHeight > lh() * lines + 3;
        while (guard-- > 0 && size > 12 && tooBig()) { size *= 0.96; el.style.fontSize = size + 'px'; }
      }
    } catch (e) {}
  })();
})();</script>"""


# ---------------------------------------------------------------- pieces

def _star(uri: str, name: str, box: tuple, z: int = 2, anchor: str = "head") -> str:
    """A cosmetic on the cover, sized into box (left, top, width, height):
    anchor "head" keeps its head at the box's top, "floor" stands it on the
    box's bottom. No art: a big printed initial, like a monogram."""
    x, y, w, h = box
    pos = f"left:{x}px;top:{y}px;width:{w}px;height:{h}px;z-index:{z}"
    if not uri:
        initial = next((c for c in name if c.isalnum()), "?").upper()
        return f'<div class="abs mg-ph" style="{pos}"><div>{esc(initial)}</div></div>'
    return (f'<div class="abs" style="{pos}"><img class="mg-star" data-trim="figure" data-mgstar="{anchor}" '
            f'data-name="{esc(name)}" src="{uri}" style="left:0;top:0;width:{w}px;height:{h}px;object-fit:contain">'
            f'</div>')


def _masthead(color: str) -> str:
    return (f'<div class="mg-mast" style="top:{_top(MAST_CAP, MAST_F, PF):.1f}px;font-size:{MAST_F}px;color:{color};'
            f'z-index:1">{MAST}</div>')


def _line(left: str, right: str, color: str) -> str:
    """The small print across the top: the date line, and the issue number."""
    y = _top(TOP_CAP, 25, IN)
    return (f'<div class="mg-line" style="left:34px;top:{y:.1f}px;color:{color};z-index:5">{esc(left)}</div>'
            + (f'<div class="mg-line" style="right:34px;top:{y:.1f}px;color:{color};z-index:5">{esc(right)}</div>'
               if right else ""))


def _barcode(seed: int, digits: str) -> str:
    rnd = random.Random(seed)
    x, bars = 2, ['<rect x="0" y="0" width="1.5" height="60" fill="#111"/>']
    while x < 132:
        bw = rnd.choice((1, 1, 1.5, 2, 2, 3, 4))
        if rnd.random() < .56:
            bars.append(f'<rect x="{x}" y="0" width="{bw}" height="{60 if x < 4 or x > 128 else 54}" fill="#111"/>')
        x += bw
    bars.append('<rect x="134" y="0" width="1.5" height="60" fill="#111"/>')
    bx, by, bwid, bh = BAR
    return (f'<div class="mg-bar" data-safe="ignore" style="left:{bx}px;top:{by}px;width:{bwid}px;height:{bh}px;'
            f'z-index:6"><svg width="{bwid - 14}" height="56" viewBox="0 0 136 60" preserveAspectRatio="none">'
            f'{"".join(bars)}</svg><div>{esc(digits)}</div></div>')


def _flash(lines: list, x: float, y: float, d: float, rot: float, t=None) -> str:
    """A round red flash, slapped on at t (None: printed with the cover)."""
    anim = f"--k:1;--r:{rot}deg;animation:{_a('mgslap', t, .42, 'cubic-bezier(.2,.8,.3,1)')};" if t is not None else ""
    inner = "".join(f'<div style="font-size:{fs:.0f}px;letter-spacing:{ls}">{esc(tx)}</div>' for tx, fs, ls in lines)
    return (f'<div class="mg-flash" style="left:{x:.0f}px;top:{y:.0f}px;width:{d:.0f}px;height:{d:.0f}px;'
            f'transform:rotate({rot}deg);z-index:7;{anim}">{inner}</div>')


def _cover(content: str, theme: dict, i: int, t_imp=None, nudge=None, sweep_t=None) -> str:
    """One cover on the pile. t_imp: when it hits the pile (None: there from
    frame 0). nudge: (t, dx, dy) when the next cover knocks it a little."""
    dx, dy, rot = POSES[i % len(POSES)]
    slot_anim = ""
    if nudge:
        tn, nx, ny = nudge
        slot_anim = (f"--nx:{nx:.1f}px;--ny:{ny:.1f}px;"
                     f"animation:{_a('mgnudge', tn, .16, 'cubic-bezier(.2,.8,.3,1)', 'forwards')};")
    drop_style = f"transform:translate({dx}px,{dy}px) rotate({rot}deg);"
    fall_style = far = ""
    contact = '<div class="mg-contact"></div>'
    if t_imp is not None:
        t0 = t_imp - FALL
        sx, sy, sr = [(640, -1560, 12), (-640, -1560, -12)][i % 2]
        drop_style = (f"--sx:{dx + sx}px;--sy:{dy + sy}px;--sr:{rot + sr}deg;--x:{dx}px;--y:{dy}px;--r:{rot}deg;"
                      f"animation:{_a('mgslide', t0, FALL + SKID, 'cubic-bezier(.22,.62,.3,1)')},"
                      f"{_a('mgshow', t0, .01, 'steps(1,end)')};")
        fall_style = f"--s0:1.13;animation:{_a('mgfall', t0, FALL, 'cubic-bezier(.5,0,.92,.55)')};"
        far = f'<div class="mg-far" style="animation:{_a("mgfar", t0, FALL, "cubic-bezier(.5,0,.92,.55)")}"></div>'
        contact = f'<div class="mg-contact" style="animation:{_a("mgland", t_imp - .06, .1)}"></div>'
        sweep_t = t_imp + .08
    sweep = (f'<div class="mg-sweep" style="animation:{_a("mgsweep", sweep_t, 1.05, "cubic-bezier(.4,.1,.5,.95)")}">'
             f'</div>') if sweep_t is not None else ""
    return (f'<div class="mg-slot" style="z-index:{10 + i};{slot_anim}">'
            f'<div class="mg-drop" style="{drop_style}"><div class="mg-fall" style="{fall_style}">{far}{contact}'
            f'<div class="mg-cover" style="background:{theme["bg"]}">'
            f'<div class="abs" style="inset:0;background:radial-gradient(ellipse 80% 62% at 60% 40%,'
            f'rgba(255,255,255,.10),rgba(255,255,255,0) 70%),linear-gradient(rgba(0,0,0,0) 55%,rgba(0,0,0,.10))"></div>'
            f'{content}'
            f'<div class="fx mg-grain"></div><div class="fx mg-spine"></div><div class="fx mg-gloss"></div>{sweep}'
            f'<div class="fx mg-edge"></div></div></div></div></div>')


def _words(text: str) -> str:
    """Escaped text whose hyphenated words never break at the hyphen."""
    return " ".join(f'<span style="white-space:nowrap">{esc(w)}</span>' if "-" in w else esc(w)
                    for w in text.split(" "))


def _kind(it: dict) -> str:
    return " ".join(x for x in (it.get("rarity_label") or "", it.get("type") or "") if x).strip()


def _cover_lines(theme: dict, debut: bool, name: str, kind: str, rarity: str, top: float) -> str:
    """Down the left side: what that day was, the name as the headline, its
    rarity and type."""
    kick = "First day in the Item Shop!" if debut else "In the Item Shop that day"
    if debut:
        k = (f'<div class="mg-cl" data-mgfit="{COL_W}" data-lines="2" style="width:{COL_W}px;font-size:44px;'
             f'line-height:1.18"><span class="mg-kick" style="background:{theme["kbg"]};margin-left:-12px;'
             f'color:{theme["kfg"]}">{esc(kick)}</span></div>')
    else:
        k = (f'<div class="mg-cl" data-mgfit="{COL_W}" data-lines="2" style="width:{COL_W}px;font-size:44px;'
             f'color:{theme["text"]}">{esc(kick)}</div>')
    col = RARITY.get(rarity, "#9AA0A6")
    return (f'<div class="abs" style="left:{COL_X}px;top:{top:.0f}px;width:{COL_W}px;display:flex;flex-direction:column;'
            f'gap:20px;z-index:4">{k}'
            f'<div class="mg-name" data-mgfit="{COL_W}" data-lines="3" style="width:{COL_W}px;font-size:100px;'
            f'color:{theme["text"]}">{_words(name)}</div>'
            f'<div class="mg-kind" style="color:{theme["text"]}"><i style="background:{col}"></i>'
            f'<span data-mgfit="{COL_W - 30}" data-lines="2" style="display:block;width:{COL_W - 30}px">{esc(kind)}'
            f'</span></div></div>')


def _year(year, theme: dict, cap: float = YEAR_CAP, f: float = YEAR_F, x: float = COL_X - 4) -> str:
    return (f'<div class="mg-year" style="left:{x}px;top:{_top(cap, f, BC):.1f}px;font-size:{f}px;'
            f'color:{theme["year"]};z-index:3">{year}</div>')


def _issue(ctx, rd, it, debut, k: int, n: int, when_up: str, theme: dict, t_imp: float) -> tuple:
    """A year's cover: (content, sounds)."""
    y = rd["year"]
    code = zlib.crc32(it["name"].encode()) % 100000
    content = (_line(f"{when_up}, {y} · On this day", f"Issue {k}/{n}", theme["text"])
               + _masthead(theme["mast"])
               + _star(ctx.art(it), it["name"], STAR, 2)
               + _year(y, theme)
               + _cover_lines(theme, debut, it["name"], _kind(it), it.get("rarity", ""), YEAR_CAP + 168)
               + _barcode(y * 31 + k, f"0 {y % 100:02d}{k:02d}9 {code:05d} 7"))
    sounds = []
    if debut:
        tf = t_imp + .95
        content += _flash([("New", 70, ".02em"), ("that day!", 31, ".04em")], 690, 318, 176, 9, tf)
        sounds.append((tf, "stamp"))
    return content, sounds


def _special(ctx, lead: list, span: str, when_short: str, bday) -> str:
    """Frame 0: the special ON THIS DAY issue with the two lead cosmetics."""
    th = SPECIAL
    a, b = lead[0][1], lead[1][1]
    content = (_line(f"The Item Shop on {when_short}, every year · {span}", "", th["text"])
               + _masthead(th["mast"])
               + _star(ctx.art(b), b["name"], (522, 206, 272, 716), 2, "floor")
               + _star(ctx.art(a), a["name"], (336, 196, 420, 748), 3, "floor"))
    if bday:
        head = (f'<div class="mg-name" data-mgfit="{COL_W}" data-lines="3" style="width:{COL_W}px;font-size:104px;'
                f'color:{th["text"]};line-height:.94">Fortnite turns {bday["age"]}!</div>')
        sub = f"Battle Royale came out on this day in {bday['year']} · The Item Shop, every year since"
    else:
        head = (f'<div class="mg-name" style="width:{COL_W}px;font-size:112px;color:{th["text"]};line-height:.9">'
                f'On<br>this<br>day</div>')
        sub = "The Item Shop, every year"
    content += (f'<div class="abs" style="left:{COL_X}px;top:326px;width:{COL_W}px;display:flex;flex-direction:column;'
                f'gap:16px;z-index:4">{head}'
                f'<div class="mg-year" style="position:relative;font-size:128px;line-height:.86;color:{th["year"]}">'
                f'{esc(when_short.upper())}</div></div>'
                # bottom right, under the stars' feet: what it is, and the span, big
                f'<div class="abs" style="right:{CW - 792}px;top:{_top(968, 36, BC):.1f}px;width:440px;text-align:right;'
                f'z-index:4"><div class="mg-cl" data-mgfit="440" data-lines="2" style="font-size:36px;'
                f'color:{th["text"]}">{esc(sub)}</div>'
                f'<div class="mg-year" style="position:relative;font-size:104px;line-height:.9;margin-top:6px;'
                f'color:{th["text"]}">{esc(span)}</div></div>')
    return content


def _collector(bday: dict, k: int, n: int, when_up: str, t_imp: float) -> tuple:
    """Sep 26: the birthday issue, all type. (content, sounds)"""
    th = COLLECTOR
    y = bday["year"]
    gold = th["mast"]
    content = (_line(f"{when_up}, {y} · On this day", f"Issue {k}/{n}", th["text"])
               + _masthead(gold)
               + f'<div class="abs mg-cl mg-rule" style="left:34px;right:34px;top:318px;height:44px;font-size:34px;'
                 f'letter-spacing:.32em;color:{gold};z-index:4"><i style="background:{gold}"></i>Collector\'s edition'
                 f'<i style="background:{gold}"></i></div>'
               + _year(y, th, 400, 270)
               + f'<div class="abs mg-name" data-mgfit="760" data-lines="2" style="left:{COL_X}px;top:640px;width:760px;'
                 f'font-size:100px;color:{th["text"]};z-index:4">Fortnite Battle Royale is out!</div>'
               + f'<div class="abs mg-cl" style="left:{COL_X}px;top:852px;width:760px;font-size:40px;line-height:1.12;'
                 f'color:{gold};z-index:4">September 26, {y}<br><span style="color:{th["text"]}">'
                 f'PC · PlayStation 4 · Xbox One</span></div>'
               + _barcode(y, "0 17092 6 00001 9"))
    tf = t_imp + 1.0
    content += _flash([("Happy", 44, ".04em"), (_ordinal(bday["age"]), 92, "0"), ("birthday", 38, ".03em")],
                      536, 372, 236, 8, tf)
    return content, [(tf, "stamp"), (tf + .2, "clap")]


def _code(cx: float, cy: float, k: float = 1.0, style: str = "") -> str:
    """USE CODE: BAD on a lime price sticker, centred on (cx, cy), k times the
    small one's size. The outer box is the unturned square around the turned
    sticker: what the safe-zone check measures."""
    bw, bh = CODE_BW * k, CODE_BH * k
    return (f'<div class="abs" data-safe="key" data-name="code" style="left:{cx - bw / 2:.1f}px;'
            f'top:{cy - bh / 2:.1f}px;width:{bw:.1f}px;height:{bh:.1f}px">'
            f'<div class="mg-code" style="left:{(bw - CODE_W) / 2:.1f}px;top:{(bh - CODE_H) / 2:.1f}px;'
            f'--r:{CODE_ROT}deg;--k:{k};transform:rotate({CODE_ROT}deg) scale({k});{style}">'
            f'<div class="u">USE CODE:</div><div class="b">BAD</div><div class="h">#EpicPartner</div></div></div>')


def _teaser(ctx, picks: list) -> str:
    """The NEXT ISSUE page: the question and the lead picks with their years."""
    th = TEASER
    content = (f'<div class="abs mg-cl mg-rule" style="left:34px;right:34px;top:40px;height:44px;font-size:36px;'
               f'letter-spacing:.34em;color:{RED};z-index:4"><i style="background:{RED};height:3px"></i>Next issue'
               f'<i style="background:{RED};height:3px"></i></div>'
               f'<div class="abs mg-name" data-mgfit="812" data-lines="2" style="left:34px;top:112px;width:812px;'
               f'font-size:112px;line-height:.96;color:{INK};z-index:4">Which year had the best shop?</div>')
    cols = [(36, 240), (293, 240), (550, 240)][:len(picks)]
    for (x, w), (it, year) in zip(cols, picks):
        content += _star(ctx.art(it), it["name"], (x, 330, w, 420), 2, "floor")
        content += (f'<div class="abs" style="left:{x}px;top:762px;width:{w}px;text-align:center;z-index:4">'
                    f'<div class="mg-year" style="position:relative;font-size:70px;line-height:.9;color:{RED}">{year}</div>'
                    f'<div class="mg-cl" data-mgfit="{w}" data-lines="2" style="font-size:34px;color:{INK};margin-top:6px">'
                    f'{_words(it["name"])}</div></div>')
    return content


# ---------------------------------------------------------------- the video

def on_this_day(ctx, rounds: list, bday: dict | None, lead: list, third) -> Comp:
    day = ctx.day
    when_up = day.strftime("%B %-d")                      # "September 28"
    when_short = day.strftime("%b %-d")                  # "Sep 28"
    years = ([bday["year"]] if bday else []) + [rd["year"] for rd, _, _ in rounds]
    n = len(years)
    r = max(R, (62.0 - 7.5 - HOOK) / n)
    content_end = HOOK + n * r
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(_css())
    comp.add(PREP_JS)
    comp.add(MG_JS)
    comp.add('<div class="mg-table"></div>')
    span = f"{years[0]}–{years[-1]}"

    # The pile: the special issue (frame 0), one issue per year, the NEXT ISSUE page.
    covers = [dict(content=_special(ctx, lead, span, when_short, bday), theme=SPECIAL, t=None)]
    sounds = [(.12, "paper")]
    k = 0
    if bday:
        c, s = _collector(bday, 1, n, when_up, HOOK)
        covers.append(dict(content=c, theme=COLLECTOR, t=HOOK))
        sounds += s
        k = 1
    for j, (rd, it, debut) in enumerate(rounds):
        t_imp = HOOK + (k + j) * r
        theme = THEMES[(k + j) % len(THEMES)]
        c, s = _issue(ctx, rd, it, debut, k + j + 1, n, when_up, theme, t_imp)
        covers.append(dict(content=c, theme=theme, t=t_imp))
        sounds += s
    picks = [(it, rd["year"]) for rd, it, _ in lead]
    if third is not None:
        yr = next((rd["year"] for rd, it, _ in rounds if it is third), None)
        if yr is not None:
            picks.append((third, yr))
    covers.append(dict(content=_teaser(ctx, picks), theme=TEASER, t=content_end))

    html = []
    for i, cv in enumerate(covers):
        nxt = covers[i + 1]["t"] if i + 1 < len(covers) else None
        rnd = random.Random(ctx.seed * 7 + i)
        nudge = (nxt - .02, rnd.choice((-1, 1)) * rnd.uniform(3, 7), rnd.uniform(2, 6)) if nxt else None
        html.append(_cover(cv["content"], cv["theme"], i, cv["t"], nudge, .35 if i == 0 else None))
        if cv["t"] is not None:
            sounds += [(cv["t"] - FALL + .02, "whoosh"), (cv["t"] - .2, "flip")]
    comp.add('<div class="full" style="z-index:10">' + "".join(html) + "</div>")

    # The code: the small sticker in every frame (it gives a little under each
    # landing); at the outro a bigger one is slapped over it.
    impacts = [cv["t"] for cv in covers if cv["t"] is not None]
    press = "animation:" + ",".join(_a("mgpress", t, .24, "cubic-bezier(.3,.7,.4,1)", "none") for t in impacts) + ";"
    comp.add(f'<div class="full" style="z-index:90">{_code(CODE_CX, CODE_CY, 1.0, press)}</div>')
    t_big = content_end + .6
    big = _code(BIG_CX, BIG_CY, BIG_K, f"animation:{_a('mgslap', t_big, .45, 'cubic-bezier(.2,.8,.3,1)')};")
    comp.add(f'<div class="full" style="z-index:91">{big}</div>')
    sounds.append((t_big, "stamp"))

    for t, kind in sounds:
        comp.cue(t, kind)
    comp.cues.sort()
    return comp
