"""
HIGHER OR LOWER? -- Item Shop edition, for @usecodebad.

Which skin has been in the Fortnite Item Shop MORE times? Six outfits make a
chain of five rounds. The frame is a game-show board split in two flat colour
fields (each tinted by its skin's rarity): the TOP half is the skin you know,
with its number ("IN THE ITEM SHOP 91 TIMES"); the BOTTOM half is the next
skin with a big "?" inside a draining lime timer ring and the two answers,
HIGHER / LOWER. After three seconds the number rolls up, the right answer
lights up lime, the other one dims and the verdict slams onto the seam, then
flies into the answer tally (top right). The bottom half slides up to become
the new top and the next skin rises in from below.

    0:00  the cover: USE CODE: BAD, HIGHER OR LOWER?, ITEM SHOP EDITION and the
          first two skins as two cards -- "91 TIMES" against "?". At ~2.5 s
          the stamp settles into the corner badge and the cards open up into
          the two halves of the board.
    0:03  five rounds (~9 s each)
    ~0:48 HOW MANY DID YOU GET RIGHT? 5/5? -- the whole chain as an answer key,
          every count and every arrow, and the code big.

Picking (deterministic from ctx.seed, so every day's episode differs): well-
known outfits (legendary, epic, Icon Series, the collaboration series ...;
`pool` narrows it to Chapter 1 or the Icon Series) that have been in the shop
at least twice, each with art. Every count differs from the one before by 18%
and 2 or more (so each answer is a fair call), no count repeats, no two skins
share a set, and the answers mix HIGHER and LOWER: two or three of each kind,
never strictly alternating.

Truth rules (cc_rarity's): every number is History.times(id, until=ctx.day) --
separate runs in the Item Shop, consecutive days counted once -- said as "in the
Item Shop N times", and the video says once on screen and in the caption that
the counts go back to when the records began, in 2017. Nothing about why, what
comes next, or who is "rarest"; HIGHER/LOWER only compares the two numbers on
screen.

    build(ctx, pool="all")      pool: "all" | "ch1" | "icon" | "collab"
"""

import itertools
import math
import random
from collections import defaultdict

import cc_fmt_rarity as FR
from cc_formats import Ctx, Video, _caption, _hashtags, num
from cc_motion import (ACCENT, BADGE_X, BADGE_Y, EASE_BACK, EASE_OUT, H, INK, SAFE_BOTTOM, SAFE_LEFT,
                       SAFE_RIGHT, SAFE_RIGHT_TOP, W, Comp, an, anton_em, code_badge, disclosure, esc,
                       style_anim)

# ------------------------------------------------------------------ picking

ROUNDS = 5
MIN_RATIO = 1.18            # the next count is at least 18% away from the one before
MIN_DIFF = 2                # ... and at least 2 away
MIN_TIMES = 2
# A skin's weight in the draw: the headline rarities and the collaboration series first.
NOTABLE = {"legendary": 3.0, "icon": 3.0, "gaminglegends": 3.0, "marvel": 3.0, "dc": 3.0, "starwars": 3.0,
           "epic": 2.0, "dark": 2.0, "slurp": 2.0, "frozen": 2.0, "lava": 2.0, "shadow": 2.0}
COLLAB = {"MARVEL SERIES", "DC SERIES", "Star Wars Series", "Gaming Legends Series"}


def _rarity(raw: dict) -> str:
    return ((raw.get("rarity") or {}).get("value") or "").lower()


def _series(raw: dict) -> str:
    return (raw.get("series") or {}).get("value") or ""


def _chapter(raw: dict) -> str:
    return str((raw.get("introduction") or {}).get("chapter") or "")


# key: (weights by rarity, filter, the edition line under the title, caption word)
POOLS = {
    "all": (NOTABLE, None, "", ""),
    # Chapter 1 had its famous skins at every rarity (Brite Bomber is rare).
    "ch1": (dict(NOTABLE, rare=1.6, uncommon=1.0), lambda r: _chapter(r) == "1", "CHAPTER 1 SKINS", "Chapter 1 "),
    "icon": ({"icon": 1.0}, lambda r: _series(r) == "Icon Series", "ICON SERIES SKINS", "Icon Series "),
    "collab": ({"marvel": 1.0, "dc": 1.0, "starwars": 1.0, "gaminglegends": 1.0}, lambda r: _series(r) in COLLAB,
               "COLLAB SKINS", "collab "),
}

# Answer patterns for five rounds: two or three of each, never strictly alternating.
PATTERNS = [p for p in itertools.product("HL", repeat=ROUNDS)
            if 2 <= p.count("H") <= 3 and p not in (tuple("HLHLH"), tuple("LHLHL"))]


def _fair(a: int, b: int) -> bool:
    lo, hi = min(a, b), max(a, b)
    return hi - lo >= MIN_DIFF and hi >= lo * MIN_RATIO


# Words that don't make two names the same character ("Skull Trooper" and "Ghoul
# Trooper" may meet; "Ariana Grande" and "Spacefarer Ariana Grande" may not).
GENERIC = {"outfit", "style", "series", "trooper", "agent", "knight", "ranger", "soldier", "commando",
           "specialist", "team", "leader", "black", "dark", "golden", "gold", "blue", "pink", "white", "shadow",
           "ghost", "iron", "super", "captain", "lord", "king", "queen", "master", "lady", "girl", "raider",
           "warrior", "hunter", "guard", "brite", "red", "the", "and"}


def _words(name: str) -> set:
    return {w for w in "".join(ch if ch.isalnum() else " " for ch in name.lower()).split() if len(w) >= 3}


def _same_family(a: set, b: set) -> bool:
    common = a & b
    return len(common) >= 2 or any(len(w) >= 4 and w not in GENERIC for w in common)


def _candidates(hist, day, weights: dict, keep) -> list:
    """[item, count, weight, set, name words] for every outfit in the pool sold at
    least MIN_TIMES times. A name that two outfits share is left out: its count
    wouldn't be the skin's. Skins sold more often weigh a little more (more
    people have seen them)."""
    by_name = defaultdict(list)
    for key in hist.days:
        raw = hist.items[key]
        if (raw.get("type") or {}).get("value") != "outfit":
            continue
        name = (raw.get("name") or "").strip()
        if name.lower() in ("", "tbd", "null", "npc"):
            continue
        by_name[name.lower()].append(raw)
    out = []
    for name, raws in by_name.items():
        if len(raws) != 1:
            continue
        raw = raws[0]
        w = weights.get(_rarity(raw))
        if not w or (keep and not keep(raw)):
            continue
        n = hist.times(raw["id"], until=day)
        if n < MIN_TIMES:
            continue
        it = FR._item(raw)
        it["name"] = it["name"].strip()
        out.append((it, n, w * (1 + min(n, 60) / 40), it["set"], _words(it["name"])))
    out.sort(key=lambda c: (c[1], c[0]["id"]))
    return out


def _max_run(pattern) -> int:
    return max(len(list(g)) for _, g in itertools.groupby(pattern))


def _chain(rng: random.Random, cands: list, excluded: set, n: int = ROUNDS + 1, want: int = 10):
    """Six (item, count) with the rules above, or None. Draws up to `want`
    chains that keep every rule and keeps the best: well-known skins, a wide
    spread of counts, no run of three answers alike if it can."""
    pool = [c for c in cands if c[0]["id"] not in excluded]
    counts = sorted({c[1] for c in pool})
    if len(counts) < n:
        return None
    lo, hi = math.log(counts[0]), math.log(counts[-1])
    found = []
    for _ in range(500):
        if len(found) >= want:
            break
        pattern = rng.choice(PATTERNS)
        # the first skin: from the middle of the range, so both answers can follow
        mid = [c for c in pool if lo + (hi - lo) * .25 <= math.log(c[1]) <= lo + (hi - lo) * .75]
        if not mid:
            mid = pool
        chain = [rng.choices(mid, weights=[c[2] for c in mid])[0]]
        for d in pattern:
            a = chain[-1][1]
            used = {c[1] for c in chain}
            opts = [c for c in pool if c[1] not in used and _fair(a, c[1]) and ((c[1] > a) if d == "H" else (c[1] < a))
                    and not any((c[3] and c[3] == p[3]) or _same_family(c[4], p[4]) for p in chain)]
            if not opts:
                break
            # a jump of about 1.35x to 3.6x reads well: skins near a random one, the known ones first
            r = math.exp(rng.uniform(math.log(1.35), math.log(3.6)))
            target = math.log(a * r if d == "H" else a / r)
            ws = [c[2] * math.exp(-((math.log(c[1]) - target) / .3) ** 2) for c in opts]
            if sum(ws) <= 1e-9:
                ws = [c[2] for c in opts]
            chain.append(rng.choices(opts, weights=ws)[0])
        if len(chain) == n:
            vals = [c[1] for c in chain]
            score = (sum(c[2] for c in chain) / n + 1.2 * math.log(max(vals) / min(vals))
                     - (.8 if _max_run(pattern) >= 3 else 0))
            found.append((score, len(found), chain))
    if not found:
        return None
    return [(c[0], c[1]) for c in max(found)[2]]


def pick(ctx: Ctx, pool: str = "all"):
    """The episode's six (item, count), each with art, or None."""
    weights, keep, _, _ = POOLS[pool]
    hist = FR.history()
    cands = _candidates(hist, ctx.day, weights, keep)
    rng = random.Random(ctx.seed * 1000 + 77 + sorted(POOLS).index(pool))
    excluded = set()
    for _ in range(6):
        chain = _chain(rng, cands, excluded)
        if not chain:
            return None
        missing = [it["id"] for it, _ in chain if not ctx.art(it)]
        if not missing:
            return chain
        excluded.update(missing)
    return None


# ------------------------------------------------------------------ the look

BG = "#0E0E11"
LIME = ACCENT
# Flat field colours, one per rarity: deep enough that white type and the lime hold on them.
TINT = {
    "legendary": "#6E3D1C", "epic": "#512664", "rare": "#1E4371", "uncommon": "#235922", "common": "#3A3D43",
    "icon": "#185952", "marvel": "#6B1F24", "dc": "#293465", "starwars": "#574919", "gaminglegends": "#45206F",
    "dark": "#40203F", "slurp": "#185667", "frozen": "#2A5670", "lava": "#73301B", "shadow": "#2E2E34",
    "mythic": "#665814",
}

SEAM = 872                      # the line between the two halves
TEXT_X, TEXT_W = SAFE_LEFT, 520  # the words' column; the skins stand to its right
ART_CX, ART_MAXW, ART_H = 752, 296, 500
FEET_T, FEET_B = SEAM - 12, SAFE_BOTTOM - 16      # 860, 1404
NUM = 200                       # the counts, Anton px (caps are .87em tall, top of the box)
NY_T, NY_B = 604, 1104          # the count's box top, in the top and in the bottom half
D_TEXT, D_ART = NY_T - NY_B, FEET_T - FEET_B      # -500, -544: bottom half -> top half
BTN_Y, BTN_H, BTN_W, BTN_GAP = 1306, 92, 252, 20
RING_D = 194
RING_CX, RING_CY = TEXT_X + RING_D / 2, NY_B + 87
# the tally, top right
SLOT, SLOT_GAP = 46, 10
SLOT_X0 = SAFE_RIGHT_TOP - (ROUNDS * SLOT + (ROUNDS - 1) * SLOT_GAP)
SLOT_Y = 288

HOOK = 3.3                      # the cover, then the board is set
TR = .9                         # a round's opening: the halves move
RQ = 8.3                        # the question, the reveal and the hold
T_RING, CD, T_ROLL, ROLL = .25, 3, 3.25, 1.3
T_LAND = T_ROLL + ROLL          # 4.55
T_FLY, FLY = 6.2, .5
OUTRO = 7.5
MIN_TOTAL = 57.0                # + the 5.1 s end card = 62.1 s

MOVE_EASE = "cubic-bezier(.7,0,.25,1)"
IN_EASE = "cubic-bezier(.2,.8,.25,1)"

CSS = f"""
@keyframes hlty{{from{{transform:translateY(var(--a,0px))}}to{{transform:translateY(var(--b,0px))}}}}
@keyframes hlbob{{from{{transform:translateY(0)}}to{{transform:translateY(-9px)}}}}
@keyframes hlshadow{{from{{transform:scaleX(1);opacity:1}}to{{transform:scaleX(.9);opacity:.75}}}}
@keyframes hlhide{{from{{visibility:visible}}to{{visibility:hidden}}}}
@keyframes hlshow{{from{{visibility:hidden}}to{{visibility:visible}}}}
@keyframes hlin{{from{{opacity:0;transform:translateY(26px)}}to{{opacity:1;transform:none}}}}
@keyframes hlout{{from{{opacity:1;transform:none}}to{{opacity:0;transform:translateY(-30px)}}}}
@keyframes hlpop{{0%{{opacity:0;transform:scale(.5)}}60%{{opacity:1;transform:scale(1.08)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes hlslam{{0%{{opacity:0;transform:scale(2.2)}}55%{{opacity:1;transform:scale(.95)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes hldrop{{from{{opacity:1;transform:none}}to{{opacity:0;transform:translateY(46px) scale(.9)}}}}
@keyframes hlburst{{from{{opacity:1;transform:scale(1)}}to{{opacity:0;transform:scale(1.35)}}}}
@keyframes hlpunch{{0%{{transform:scale(1.12)}}100%{{transform:scale(1)}}}}
@keyframes hlnudge{{0%,100%{{transform:none}}50%{{transform:translateY(-6px)}}}}
@keyframes hlthump{{0%,100%{{transform:scale(1)}}35%{{transform:scale(1.045)}}}}
@keyframes hlhop{{0%,100%{{transform:none}}35%{{transform:translateY(-26px)}}70%{{transform:translateY(3px)}}}}
@keyframes hlwipe{{from{{transform:translateY(1920px)}}to{{transform:none}}}}
@keyframes hlfly{{0%{{transform:none;opacity:1}}85%{{opacity:1}}100%{{transform:translate(var(--fx),var(--fy)) scale(.1);opacity:0}}}}
@keyframes hlclip{{from{{clip-path:var(--c0)}}to{{clip-path:var(--c1)}}}}
@keyframes hlmorph{{from{{transform:translate(var(--mx),var(--my)) scale(var(--ms))}}to{{transform:none}}}}
.hl-lab{{font-size:27px;font-weight:800;letter-spacing:.16em;color:rgba(255,255,255,.8);white-space:nowrap;
  line-height:34px}}
.hl-name{{color:#fff;line-height:.92;text-shadow:0 5px 0 rgba(0,0,0,.26)}}
.hl-num{{color:#fff;font-size:{NUM}px;line-height:.9;white-space:nowrap;text-shadow:0 8px 0 rgba(0,0,0,.26)}}
.hl-sfx{{font-size:.38em;margin-left:.16em;color:rgba(255,255,255,.86)}}
.hl-btn{{position:absolute;display:flex;align-items:center;justify-content:center;gap:14px;border-radius:18px;
  font-family:'Anton',Impact,sans-serif;font-size:50px;line-height:1;letter-spacing:.02em}}
.hl-ring{{position:absolute;border-radius:50%;
  background:conic-gradient({LIME} calc(var(--p)*360deg),rgba(255,255,255,.17) 0);
  -webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 14px),#000 calc(100% - 13px));
  mask:radial-gradient(farthest-side,transparent calc(100% - 14px),#000 calc(100% - 13px))}}
"""


def _tint(it: dict) -> str:
    return TINT.get(it["rarity"], TINT["common"])


def _tints(chain: list) -> list:
    """Each skin's field colour. Two neighbours of the same rarity would make
    one field of the board: the second takes a darker shade of it."""
    out, dark = [], []
    for i, (it, _) in enumerate(chain):
        base = _tint(it)
        d = i > 0 and base == _tint(chain[i - 1][0]) and not dark[-1]
        dark.append(d)
        out.append("#" + "".join(f"{round(int(base[j:j + 2], 16) * .6):02x}" for j in (1, 3, 5)) if d else base)
    return out


def _a(name: str, start: float, dur: float, ease: str = EASE_OUT, fill: str = "both",
       iters: str = "1", direction: str = "normal") -> str:
    return an(name, start, dur, ease, iters, direction, fill)


def _wrap(inner: str, anim: str, style: str = "") -> str:
    """A full-frame wrapper that carries one animation (so several can stack)."""
    return f'<div class="full" style="{style}{style_anim(anim)}">{inner}</div>'


def _tri(up: bool, size: float, color: str = "currentColor") -> str:
    """A solid triangle, pointing up or down (drawn, not a font glyph)."""
    w, h = size, size * .86
    pts = f"{w / 2:.1f},0 {w:.1f},{h:.1f} 0,{h:.1f}" if up else f"0,0 {w:.1f},0 {w / 2:.1f},{h:.1f}"
    return (f'<svg width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.1f} {h:.1f}" style="display:block;flex:none">'
            f'<polygon points="{pts}" fill="{color}"/></svg>')


def _lines(text: str, size: float, width: float) -> list:
    """Words split into lines of at most `width` px (Anton); two lines break
    where they come out most even."""
    ws = text.upper().split()
    one = anton_em(text) * size - .18 * size
    if one <= width or len(ws) == 1:
        return [" ".join(ws)]
    best = None
    for j in range(1, len(ws)):
        a, b = " ".join(ws[:j]), " ".join(ws[j:])
        wa, wb = (anton_em(a) - .18) * size, (anton_em(b) - .18) * size
        if wa <= width and wb <= width and (best is None or max(wa, wb) < best[0]):
            best = (max(wa, wb), [a, b])
    return best[1] if best else [" ".join(ws)]


def _name_fit(text: str, width: float, big: int = 88, one_min: int = 66, two_max: int = 72,
              small: int = 44) -> tuple:
    """(size, lines): one line as big as fits (down to one_min), else two."""
    for s in range(big, one_min - 1, -2):
        if (anton_em(text) - .18) * s <= width:
            return s, [text.upper()]
    for s in range(two_max, small - 1, -2):
        ls = _lines(text, s, width)
        if len(ls) == 2 and all((anton_em(x) - .18) * s <= width for x in ls):
            return s, ls
    s = small
    while s > 24 and (anton_em(text) - .18) * s / 2 > width:
        s -= 2
    return s, _lines(text, s, width)


def _name_html(text: str, x: float, bottom: float, width: float, cls: str = "", fit=None) -> tuple:
    """The name, set so its last line's letters end at `bottom`. Returns (html, top)."""
    size, ls = fit or _name_fit(text, width)
    top = bottom - ((len(ls) - 1) * .92 * size + .8825 * size)
    html = (f'<div class="abs d hl-name {cls}" style="left:{x:.0f}px;top:{top:.0f}px;width:{width + 20:.0f}px;'
            f'font-size:{size}px;white-space:nowrap">{"<br>".join(esc(x) for x in ls)}</div>')
    return html, top


def _num_w(value: int, size: float = NUM) -> float:
    """Width of 'N TIMES' as the count is set (the suffix at .38em)."""
    return (anton_em(str(value)) - .18) * size + (.16 + anton_em("TIMES") - .18) * .38 * size


# ------------------------------------------------------------------ pieces

def _art(uri: str, name: str, cx: float, feet: float, h: float, maxw: float, bob_t: float) -> str:
    """A skin standing with its feet on `feet`: a soft contact shadow under it and
    a slow, small bob. The art is cropped to the figure (data-trim)."""
    if uri:
        img = (f'<img data-trim="figure" data-name="{esc(name)}" src="{uri}" style="position:absolute;left:0;top:0;'
               f'width:{maxw:.0f}px;height:{h:.0f}px;object-fit:contain;object-position:50% 100%;'
               f'filter:drop-shadow(0 18px 16px rgba(0,0,0,.38))">')
    else:
        img = (f'<div class="d" style="position:absolute;left:{maxw * .15:.0f}px;top:{h * .1:.0f}px;'
               f'width:{maxw * .7:.0f}px;height:{h * .9:.0f}px;border:5px dashed rgba(255,255,255,.35);'
               f'border-radius:30px;display:flex;align-items:center;justify-content:center;text-align:center;'
               f'font-size:40px;color:rgba(255,255,255,.6)">{esc(name)}</div>')
    shadow = (f'<div class="abs" style="left:{maxw * .16:.0f}px;top:{h - 16:.0f}px;width:{maxw * .68:.0f}px;height:30px;'
              f'border-radius:50%;background:radial-gradient(closest-side,rgba(0,0,0,.46),rgba(0,0,0,0));'
              f'{style_anim(_a("hlshadow", bob_t, 2.8, "ease-in-out", "both", "infinite", "alternate"))}"></div>')
    body = f'<div class="full" style="{style_anim(_a("hlbob", bob_t, 2.8, "ease-in-out", "both", "infinite", "alternate"))}">{img}</div>'
    return (f'<div class="abs" style="left:{cx - maxw / 2:.0f}px;top:{feet - h:.0f}px;width:{maxw:.0f}px;'
            f'height:{h:.0f}px">{shadow}{body}</div>')


def _field(color: str, top: float, z: int, extra: str = "") -> str:
    """One flat colour half: a full-width sheet from `top` down past the frame.
    It lies over the half above it, so it casts a soft shadow up onto it."""
    return (f'<div class="abs" style="left:0;top:{top:.0f}px;width:{W}px;height:{H + 240}px;background:{color};'
            f'box-shadow:0 -12px 30px rgba(0,0,0,.32),inset 0 2px 0 rgba(255,255,255,.07);z-index:{z};{extra}">'
            f'</div>')


def _label(text: str, x: float, y: float, extra: str = "") -> str:
    return f'<div class="abs hl-lab" style="left:{x:.0f}px;top:{y:.0f}px;{extra}">{esc(text)}</div>'


def _count(value: int, x: float, y: float) -> str:
    return (f'<div class="abs d hl-num" style="left:{x:.0f}px;top:{y:.0f}px">{value:,}'
            f'<span class="hl-sfx">TIMES</span></div>')


def _roll(comp: Comp, value: int, x: float, y: float, start: float, dur: float = ROLL) -> str:
    """The count rolling up from 0, then settling on the exact number with its
    TIMES. Hidden until it starts."""
    name = comp.uid("hlroll")
    comp.css(f"@keyframes {name}{{from{{--n:0}}to{{--n:{int(value)}}}}}")
    rolling = style_anim(_a(name, start, dur, "cubic-bezier(.15,.6,.25,1)"), _a("fadeout", start + dur, .04))
    final = style_anim(_a("fadein", start + dur, .04), _a("hlpunch", start + dur, .35, EASE_OUT, "none"))
    return (f'<div class="abs" style="left:0;top:0;{style_anim(_a("fadein", start, .01))}">'
            f'<div class="abs d hl-num" style="left:{x:.0f}px;top:{y:.0f}px">'
            f'<span class="count" style="position:absolute;left:0;top:0;{rolling}"></span>'
            f'<span style="display:inline-block;transform-origin:0 80%;{final}">{value:,}'
            f'<span class="hl-sfx">TIMES</span></span></div></div>')


def _button(up: bool, state: str) -> str:
    """HIGHER (left) or LOWER (right) as a physical key: idle (dark, white
    rim), lit (lime) or a dimming veil."""
    x = TEXT_X if up else TEXT_X + BTN_W + BTN_GAP
    box = f"left:{x}px;top:{BTN_Y}px;width:{BTN_W}px;height:{BTN_H}px;"
    word = "HIGHER" if up else "LOWER"
    if state == "dim":
        return (f'<div class="abs" style="{box}border-radius:18px;background:rgba(8,8,10,.62)" '
                f'data-safe="ignore"></div>')
    if state == "lit":
        look = f"background:{LIME};color:{INK};box-shadow:0 8px 0 rgba(0,0,0,.4),inset 0 0 0 3px {LIME};"
    else:
        look = ("background:rgba(12,12,14,.86);color:#fff;"
                "box-shadow:0 8px 0 rgba(0,0,0,.4),inset 0 0 0 3px rgba(255,255,255,.92);")
    return f'<div class="hl-btn" style="{box}{look}">{_tri(up, 34)}<span>{word}</span></div>'


# ------------------------------------------------------------------ the video

def _times(n_rounds: int) -> dict:
    """Round k (1..n): T[k] its start (the halves move), Q[k] the question."""
    T, Q = {}, {}
    t = HOOK
    for k in range(1, n_rounds + 1):
        T[k] = t
        Q[k] = t if k == 1 else t + TR
        t = Q[k] + RQ
    return {"T": T, "Q": Q, "end": t}


def _slot_xy(k: int) -> tuple:
    return SLOT_X0 + (k - 1) * (SLOT + SLOT_GAP), SLOT_Y


def _stamp(comp: Comp, dock_start: float, dock_end: float) -> str:
    """USE CODE: BAD at 1.4x on the cover (text below y 285: the cover crop),
    shrinking into the corner badge, which takes over as it lands."""
    sx, sy, k = SAFE_LEFT, 298, 1.4
    dock = comp.uid("hldock")
    to = f"translate({BADGE_X - sx}px,{BADGE_Y - sy}px) scale({1 / k:.4f})"
    comp.css(f"@keyframes {dock}{{0%{{transform:none;opacity:1}}99.9%{{transform:{to};opacity:1}}"
             f"100%{{transform:{to};opacity:0}}}}")
    comp.css(f".codebadge,.codetag{{animation:fadein .01s linear {dock_end - .01:.3f}s both paused !important}}")
    return (f'<div class="abs" style="left:{sx}px;top:{sy}px;transform-origin:0 0;z-index:60;'
            f'{style_anim(_a(dock, dock_start, dock_end - dock_start, "cubic-bezier(.6,0,.4,1)"))}">'
            f'<div style="display:inline-flex;align-items:center;gap:17px;background:{LIME};color:{INK};'
            f'border-radius:22px;padding:11px 28px 8px 25px;box-shadow:0 11px 0 rgba(0,0,0,.38)">'
            f'<div style="font-size:32px;font-weight:900;line-height:1.02;letter-spacing:.12em">USE<br>CODE:</div>'
            f'<div class="d" style="font-size:112px;line-height:.9;letter-spacing:.02em">BAD</div></div>'
            f'<div style="margin:6px 0 0 6px;font-size:32px;font-weight:700;line-height:1.3;'
            f'color:rgba(255,255,255,.92);text-shadow:0 2px 8px rgba(0,0,0,.9)">#EpicPartner</div></div>')


def _cover(comp: Comp, ctx: Ctx, chain: list, edition: str) -> tuple:
    """Frame 0: the code, the title, the edition and the first two skins as two
    cards. Returns (html, card rects) -- the cards open into the board."""
    out = [f'<div class="full" style="background:{BG};z-index:1"></div>']
    t_out = 2.38
    gone = _a("hlout", t_out, .22, "ease-in")
    # the edition block, top right, level with the stamp
    ed = (f'<div class="abs" style="right:{W - SAFE_RIGHT_TOP}px;top:300px;text-align:right;z-index:5;'
          f'{style_anim(gone)}">'
          f'<div class="d" style="font-size:70px;line-height:.9;color:#fff">ITEM SHOP</div>'
          f'<div style="margin-top:10px;font-size:27px;font-weight:800;letter-spacing:.42em;'
          f'color:rgba(255,255,255,.82)">EDITION</div>')
    if edition:
        ed += (f'<div style="display:inline-block;margin-top:12px;background:#fff;color:{INK};font-size:24px;'
               f'font-weight:800;letter-spacing:.12em;padding:6px 12px 5px;border-radius:8px;'
               f'box-shadow:0 5px 0 rgba(0,0,0,.35)">{esc(edition)}</div>')
    out.append(ed + "</div>")
    # the title, one line across the frame
    title = "HIGHER OR LOWER?"
    size = min(132, (SAFE_RIGHT_TOP - SAFE_LEFT - 12) / (anton_em(title) - .18))
    out.append(f'<div class="abs" style="left:0;top:0;width:{W}px;z-index:5;{style_anim(gone)}">'
               f'<div class="abs d" style="left:{SAFE_LEFT}px;top:482px;font-size:{size:.0f}px;line-height:.9;'
               f'color:#fff;white-space:nowrap;transform-origin:30% 50%;text-shadow:0 8px 0 rgba(0,0,0,.35);'
               f'{style_anim(_a("hlthump", .2, .4, EASE_OUT, "none"))}">HIGHER OR LOWER<span style="color:{LIME}">?</span>'
               f'</div></div>')
    # the two cards
    y0, y1 = 636, 1400
    rects = [(SAFE_LEFT, y0, 468, y1), (492, y0, SAFE_RIGHT, y1)]
    for j, ((it, n), (x0, _, x1, _)) in enumerate(zip(chain[:2], rects)):
        cw = x1 - x0
        txt = []
        if j == 0:
            txt.append(f'<div class="abs d" style="left:{x0 + 26}px;top:{y0 + 26}px;font-size:116px;line-height:.9;'
                       f'color:#fff;white-space:nowrap;text-shadow:0 6px 0 rgba(0,0,0,.3)">{n:,}'
                       f'<span style="font-size:.4em;margin-left:.14em;color:rgba(255,255,255,.86)">TIMES</span></div>')
        else:
            txt.append(f'<div class="abs d" style="left:{x0 + 22}px;top:{y0 + 22}px;width:124px;height:124px;'
                       f'border-radius:50%;background:{LIME};color:{INK};font-size:96px;line-height:124px;'
                       f'text-align:center;box-shadow:0 7px 0 rgba(0,0,0,.35);'
                       f'{style_anim(_a("hlnudge", 1.1, .5, "ease-in-out", "none"))}">?</div>')
        nm, _ = _name_html(it["name"], x0 + 26, y1 - 30, cw - 52,
                           fit=_name_fit(it["name"], cw - 52, big=52, one_min=40, two_max=44, small=30))
        txt.append(nm)
        out.append(f'<div class="full" style="z-index:40;{style_anim(gone)}">{"".join(txt)}</div>')
    return "".join(out), rects


def build(ctx: Ctx, pool: str = "all", **_ignored):
    if pool not in POOLS:
        return None
    chain = pick(ctx, pool)
    if not chain:
        return None
    _, _, edition, cap_word = POOLS[pool]
    n = len(chain) - 1
    tm = _times(n)
    T, Q, content_end = tm["T"], tm["Q"], tm["end"]
    total = max(content_end + OUTRO, MIN_TOTAL)
    comp = Comp(total)
    comp.css(CSS)
    ups = [chain[k][1] > chain[k - 1][1] for k in range(1, n + 1)]
    uris = [ctx.art(it) for it, _ in chain]
    tints = _tints(chain)

    L = []                        # the board scene's layers
    cover, rects = _cover(comp, ctx, chain, edition)
    L.append(cover)
    L.append(_stamp(comp, 2.1, 2.6))
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop"); comp.cue(2.1, "whoosh")

    M0, M1 = 2.45, 3.2            # the cards open into the board
    comp.cue(M0, "whoosh")

    # ---- each skin: its half (field), its words, its art
    for i, (it, count) in enumerate(chain):
        tint = tints[i]
        zf, zc = 10 + 2 * i, 11 + 2 * i
        # when this skin arrives in the bottom half, moves to the top, and is covered
        t_enter = None if i < 2 else T[i]
        t_up = T[i + 1] if i + 1 <= n and i >= 1 else None
        t_gone = T[i + 2] if i + 2 <= n else None
        top_now = i == 0
        # the field
        if i < 2:
            x0, y0, x1, y1 = rects[i]
            if i == 0:
                c0 = f"inset({y0}px {W - x1}px {H + 240 - y1}px {x0}px round 28px)"
                c1 = f"inset(0px 0px {H + 240 - SEAM}px 0px round 0px)"
                fld = _field(tint, 0, zf, f"--c0:{c0};--c1:{c1};{style_anim(_a('hlclip', M0, M1 - M0, MOVE_EASE))}")
            else:
                # drawn from the frame's top so the card (above the seam) can be cut from it
                c0 = f"inset({y0}px {W - x1}px {H + 240 - y1}px {x0}px round 28px)"
                c1 = f"inset({SEAM}px 0px 0px 0px round 0px)"
                fld = _field(tint, 0, zf, f"box-shadow:none;--c0:{c0};--c1:{c1};"
                                          f"{style_anim(_a('hlclip', M0, M1 - M0, MOVE_EASE))}")
                # after the morph the real bottom sheet (with its shadow) takes over
                fld = (_wrap(fld, _a("hlhide", M1 + .02, .01, "linear")) +
                       _wrap(_field(tint, SEAM, zf), _a("hlshow", M1 + .02, .01, "linear")))
        else:
            fld = _field(tint, SEAM, zf)
        if t_enter is not None:
            fld = _wrap(fld, _a("hlty", t_enter + .08, .8, IN_EASE), f"--a:{H - SEAM}px;--b:0px;z-index:{zf};")
        if t_up is not None:
            fld = _wrap(fld, _a("hlty", t_up, .78, MOVE_EASE), f"--a:0px;--b:{-SEAM}px;z-index:{zf};")
        L.append(f'<div class="full" style="z-index:{zf}">{fld}</div>')

        # the words
        ny = NY_T if top_now else NY_B
        words = []
        nm, name_top = _name_html(it["name"], TEXT_X, ny - 62, TEXT_W)
        words.append(nm)
        words.append(_label("IN THE ITEM SHOP", TEXT_X + 2, ny - 46))
        if i == 0:
            words.append(_count(count, TEXT_X, ny))
            words.append(_wrap(_label("SINCE THE RECORDS BEGAN IN 2017", TEXT_X + 2, ny + 190,
                                      "font-size:22px;letter-spacing:.14em;color:rgba(255,255,255,.62)"),
                               _a("fadeout", T[2] - .2, .25) if n >= 2 else ""))
        else:
            q = Q[i]
            # the ? in its timer ring, and TIMES, until the count rolls
            ring = (f'<div class="hl-ring" style="left:{RING_CX - RING_D / 2:.0f}px;top:{RING_CY - RING_D / 2:.0f}px;'
                    f'width:{RING_D}px;height:{RING_D}px;{style_anim(_a("drain", q + T_RING, CD, "linear"))}"></div>')
            ring = _wrap(ring, _a("hlpop", q, .4, EASE_BACK), f"transform-origin:{RING_CX:.0f}px {RING_CY:.0f}px;")
            ring = _wrap(ring, _a("hlburst", q + T_ROLL, .22, "ease-out"),
                         f"transform-origin:{RING_CX:.0f}px {RING_CY:.0f}px;")
            qm = (f'<div class="abs d" style="left:{RING_CX - 100:.0f}px;top:{RING_CY - 61:.0f}px;width:200px;'
                  f'text-align:center;font-size:140px;line-height:.9;color:#fff;text-shadow:0 6px 0 rgba(0,0,0,.28)">?</div>')
            qm = _wrap(qm, _a("hlslam", q, .38), f"transform-origin:{RING_CX:.0f}px {RING_CY:.0f}px;")
            qm = _wrap(qm, _a("hldrop", q + T_ROLL, .2, "ease-in"))
            base = ny + .8725 * NUM
            sfx = (f'<div class="abs d" style="left:{RING_CX + RING_D / 2 + 20:.0f}px;top:{base - .8725 * 76:.0f}px;'
                   f'font-size:76px;line-height:.9;color:rgba(255,255,255,.86)">TIMES</div>')
            sfx = _wrap(_wrap(sfx, _a("fadein", q + .1, .25)), _a("fadeout", q + T_ROLL, .15))
            words += [ring, qm, sfx, _roll(comp, count, TEXT_X, ny, q + T_ROLL)]
        grp = "".join(words)
        if i == 1:
            grp = _wrap(grp, _a("hlin", M1 - .12, .35))
        if i == 0:
            grp = _wrap(grp, _a("hlin", M1 - .2, .35))
        if t_enter is not None:
            grp = _wrap(grp, _a("hlty", t_enter + .08, .8, IN_EASE), f"--a:{H - SEAM}px;--b:0px;")
        if t_up is not None:
            grp = _wrap(grp, _a("hlty", t_up, .78, MOVE_EASE), f"--a:0px;--b:{D_TEXT}px;")
        if t_gone is not None:
            grp = _wrap(grp, _a("hlty", t_gone, .78, MOVE_EASE), "--a:0px;--b:-260px;")
            grp = _wrap(grp, _a("hlhide", t_gone + .8, .01, "linear"))

        # the art
        feet = FEET_T if top_now else FEET_B
        art = _art(uris[i], it["name"], ART_CX, feet, ART_H, ART_MAXW, (M1 if i < 2 else T[i] + .9) + .1 * i)
        if i < 2:
            # from its card on the cover to its half of the board
            x0, y0, x1, y1 = rects[i]
            pc_x, pc_feet, ph = (x0 + x1) / 2, y1 - 104, 520
            s = ph / ART_H
            mx, my = pc_x - ART_CX, (pc_feet - ph / 2) - (feet - ART_H / 2)
            art = _wrap(art, _a("hlmorph", M0, M1 - M0, MOVE_EASE),
                        f"--mx:{mx:.0f}px;--my:{my:.0f}px;--ms:{s:.3f};"
                        f"transform-origin:{ART_CX:.0f}px {feet - ART_H / 2:.0f}px;")
            art = _wrap(art, _a("hlhop", .9 + .12 * i, .45, EASE_OUT, "none"))
        if t_enter is not None:
            art = _wrap(art, _a("hlty", t_enter + .08, .8, IN_EASE), f"--a:{H - SEAM}px;--b:0px;")
        if t_up is not None:
            art = _wrap(art, _a("hlty", t_up, .78, MOVE_EASE), f"--a:0px;--b:{D_ART}px;")
        if t_gone is not None:
            art = _wrap(art, _a("hlty", t_gone, .78, MOVE_EASE), "--a:0px;--b:-260px;")
            art = _wrap(art, _a("hlhide", t_gone + .8, .01, "linear"))
        L.append(f'<div class="full" style="z-index:{zc}">{grp}{art}</div>')

    # ---- the answer keys, the verdicts, the tally
    console = [_button(True, "idle"), _button(False, "idle")]
    hud = []
    for k in range(1, n + 1):
        q, up = Q[k], ups[k - 1]
        land = q + T_LAND
        until = (T[k + 1] + .2) if k < n else content_end + 1
        lit = _wrap(_button(up, "lit"), _a("hlpunch", land, .3, EASE_OUT, "none"))
        lit += _button(not up, "dim")
        console.append(_wrap(_wrap(lit, _a("fadein", land, .08)), _a("fadeout", until, .2)))
        # the verdict on the seam, then into its tally slot
        word = "HIGHER!" if up else "LOWER!"
        ps = 124
        pw = (anton_em(word) - .18) * ps + ps * .5 + 60 + 20
        ph = ps * .87 + 58
        sx, sy = _slot_xy(k)
        plate = (f'<div class="d" style="display:flex;align-items:center;justify-content:center;gap:{ps * .16:.0f}px;'
                 f'width:{pw:.0f}px;height:{ph:.0f}px;background:{LIME};color:{INK};border-radius:22px;'
                 f'font-size:{ps}px;line-height:1;padding-top:4px;'
                 f'box-shadow:0 12px 0 rgba(0,0,0,.34),0 30px 44px rgba(0,0,0,.32)">'
                 f'{_tri(up, ps * .5)}<span>{word}</span></div>')
        plate = f'<div style="transform:rotate({-4 if up else 3}deg)">{plate}</div>'
        plate = f'<div style="transform-origin:50% 50%;{style_anim(_a("hlslam", land + .05, .42))}">{plate}</div>'
        cx, cy = (SAFE_LEFT + SAFE_RIGHT) / 2, SEAM
        hud.append(f'<div class="abs" style="left:{cx - pw / 2:.0f}px;top:{cy - ph / 2:.0f}px;width:{pw:.0f}px;'
                   f'height:{ph:.0f}px;z-index:150;--fx:{sx + SLOT / 2 - cx:.0f}px;--fy:{sy + SLOT / 2 - cy:.0f}px;'
                   f'{style_anim(_a("hlfly", q + T_FLY, FLY, "cubic-bezier(.55,0,.75,.4)"))}">{plate}</div>')
        comp.cue(q, "pop")
        for s in range(CD):
            comp.cue(q + T_RING + s, "tick")
        comp.cue(q + T_ROLL - .3, "drumroll")
        comp.cue(land + .05, "slam"); comp.cue(land + .1, "ding")
        comp.cue(q + T_FLY, "whoosh"); comp.cue(q + T_FLY + FLY, "pop")
        if k > 1:
            comp.cue(T[k] + .05, "whoosh")
        # the slot fills
        fill = (f'<div class="abs" style="left:{sx}px;top:{sy}px;width:{SLOT}px;height:{SLOT}px;border-radius:11px;'
                f'background:{LIME};color:{INK};display:flex;align-items:center;justify-content:center;'
                f'box-shadow:0 5px 0 rgba(0,0,0,.35);{style_anim(_a("hlpop", q + T_FLY + FLY - .02, .35, EASE_BACK))}">'
                f'{_tri(up, 24)}</div>')
        hud.append(fill)
        # the active slot, and the round label
        r0 = HOOK - .15 if k == 1 else T[k] + .35
        r1 = T[k + 1] + .35 if k < n else content_end + 1
        act = (f'<div class="abs" style="left:{sx - 3}px;top:{sy - 3}px;width:{SLOT + 6}px;height:{SLOT + 6}px;'
               f'border-radius:13px;border:4px solid #fff"></div>')
        hud.append(_wrap(_wrap(act, _a("fadein", r0, .2)), _a("fadeout", q + T_FLY + FLY, .1)))
        lab = (f'<div class="abs" style="right:{W - SAFE_RIGHT_TOP}px;top:242px;font-size:25px;font-weight:800;'
               f'letter-spacing:.18em;color:#fff;white-space:nowrap">'
               f'{"FINAL ROUND" if k == n else f"ROUND {k}/{n}"}</div>')
        hud.append(_wrap(_wrap(lab, _a("fadein", r0, .2)), _a("fadeout", r1 - .05, .15)))
    slots = "".join(f'<div class="abs" style="left:{_slot_xy(k)[0]}px;top:{SLOT_Y}px;width:{SLOT}px;height:{SLOT}px;'
                    f'border-radius:11px;border:3px solid rgba(255,255,255,.42);background:rgba(0,0,0,.14)"></div>'
                    for k in range(1, n + 1))
    hud.insert(0, _wrap(slots, _a("fadein", HOOK - .15, .25)))
    con = "".join(console)
    con = _wrap(con, _a("hlpop", Q[1] - .05, .4, EASE_BACK), f"transform-origin:{TEXT_X + BTN_W:.0f}px {BTN_Y + BTN_H / 2:.0f}px;")
    L.append(f'<div class="full" style="z-index:100">{con}</div>')
    L.append(f'<div class="full" style="z-index:120">{"".join(hud)}</div>')
    L.append('<div class="grain" style="z-index:200" data-safe="ignore"></div>')
    comp.scene(0, content_end + .6, "".join(L), fade_in=.01, fade_out=.05)

    _outro(comp, ctx, chain, ups, uris, tints, content_end, total)
    comp.add(code_badge(0))
    comp.add(disclosure())

    # ---- words
    body = "\n".join(
        f"{num(i + 1)} {it['name']} · in the Item Shop {cnt:,} times"
        + ("" if i == 0 else f" ({'HIGHER' if ups[i - 1] else 'LOWER'})")
        for i, (it, cnt) in enumerate(chain))
    tags = _hashtags("higherorlower", "fortniteskins", chain[0][0]["name"])
    return Video(
        f"higher_lower_{pool}", comp,
        title=f"Higher or Lower: Fortnite {cap_word}Item Shop Edition — {ctx.day_label}",
        yt_title=f"Higher or Lower? Which Fortnite {cap_word.title() if cap_word else ''}Skin Was in the Item Shop More? #shorts",
        caption=_caption(f"🔼🔽 HIGHER OR LOWER? Fortnite Item Shop edition — {ctx.day_label}\n"
                         f"Which {cap_word}skin has been in the Item Shop more times? "
                         f"Counts since the records began in 2017 👇",
                         body, "How many did you get right? 5/5?", tags),
        hashtags=tags)


def _outro(comp: Comp, ctx: Ctx, chain: list, ups: list, uris: list, tints: list, start: float, end: float):
    """HOW MANY DID YOU GET RIGHT? The chain as an answer key, and the code."""
    out = [f'<div class="full" style="background:{BG};{style_anim(_a("hlwipe", start, .55, IN_EASE))}"></div>',
           '<div class="grain" data-safe="ignore"></div>']
    t = start + .35
    out.append(f'<div class="abs d" style="left:{SAFE_LEFT}px;top:392px;font-size:100px;line-height:.92;color:#fff;'
               f'text-shadow:0 7px 0 rgba(0,0,0,.35);transform-origin:0 50%;{style_anim(_a("hlslam", t, .45))}">'
               f'HOW MANY DID YOU<br>GET RIGHT?</div>')
    gw = (anton_em("GET RIGHT?") - .18) * 100
    out.append(f'<div class="abs" style="left:{SAFE_LEFT + gw + 34:.0f}px;top:470px;transform:rotate(-5deg)">'
               f'<div class="d" style="background:{LIME};color:{INK};font-size:96px;line-height:.9;padding:12px 22px 6px;'
               f'border-radius:16px;box-shadow:0 9px 0 rgba(0,0,0,.35);{style_anim(_a("hlpop", start + 1.4, .5, EASE_BACK))}">'
               f'5/5?</div></div>')
    # the answer key
    y0, rh, gap = 640, 78, 10
    out.append(_label("THE ANSWERS", SAFE_LEFT + 2, y0 - 40, f"color:{LIME};{style_anim(_a('fadein', start + .7, .3))}"))
    for i, (it, cnt) in enumerate(chain):
        y = y0 + i * (rh + gap)
        ta = start + .75 + .09 * i
        chip = ""
        if i:
            chip = (f'<div class="abs" style="left:12px;top:{(rh - 54) / 2:.0f}px;width:54px;height:54px;border-radius:12px;'
                    f'background:{LIME};color:{INK};display:flex;align-items:center;justify-content:center">'
                    f'{_tri(ups[i - 1], 28)}</div>')
        av = ""
        if uris[i]:
            av = (f'<div class="abs" style="left:80px;top:{(rh - 62) / 2:.0f}px;width:62px;height:62px;border-radius:50%;'
                  f'overflow:hidden;background:rgba(0,0,0,.28)">'
                  f'<img data-trim="figure" data-name="{esc(it["name"])}" src="{uris[i]}" style="width:62px;height:62px;'
                  f'object-fit:cover;object-position:50% 6%"></div>')
        nw = 470
        s = min(44, nw / max(1e-6, anton_em(it["name"]) - .18))
        name = (f'<div class="abs d" style="left:160px;top:{(rh - s * .87) / 2:.0f}px;font-size:{s:.0f}px;line-height:.9;'
                f'color:#fff;white-space:nowrap">{esc(it["name"].upper())}</div>')
        count = (f'<div class="abs d" style="right:20px;top:{(rh - 56 * .87) / 2:.0f}px;font-size:56px;line-height:.9;'
                 f'color:#fff;white-space:nowrap">{cnt:,}<span style="font-size:.36em;margin-left:.2em;'
                 f'color:rgba(255,255,255,.85)">TIMES</span></div>')
        out.append(f'<div class="abs" style="left:{SAFE_LEFT}px;top:{y}px;width:{SAFE_RIGHT - SAFE_LEFT}px;height:{rh}px;'
                   f'border-radius:14px;background:{tints[i]};box-shadow:0 6px 0 rgba(0,0,0,.32);'
                   f'{style_anim(_a("hlin", ta, .35))}">{chip}{av}{name}{count}</div>')
    # the code, big
    cy = 1238
    out.append(f'<div class="abs" style="left:{SAFE_LEFT}px;top:{cy}px;{style_anim(_a("hlpop", start + 1.9, .5, EASE_BACK))}">'
               f'<div style="display:inline-flex;align-items:center;gap:22px;background:{LIME};color:{INK};'
               f'border-radius:24px;padding:12px 34px 6px 30px;box-shadow:0 12px 0 rgba(0,0,0,.4)">'
               f'<div style="font-size:40px;font-weight:900;line-height:1.02;letter-spacing:.12em">USE<br>CODE:</div>'
               f'<div class="d" style="font-size:136px;line-height:.9;letter-spacing:.02em">BAD</div></div></div>')
    out.append(_label("#EpicPartner", SAFE_LEFT + 470, cy + 66,
                      f"font-size:28px;letter-spacing:0;font-weight:700;color:rgba(255,255,255,.9);"
                      f"{style_anim(_a('fadein', start + 2.2, .3))}"))
    comp.cue(start + .05, "whoosh"); comp.cue(start + .35, "slam"); comp.cue(start + .8, "clap")
    comp.cue(start + 1.4, "pop"); comp.cue(start + 1.9, "reveal")
    comp.scene(start, end, "".join(out), fade_in=.01, fade_out=.01, z=2)
