"""
WHICH COSTS MORE? -- slot 2 (interactive quiz) for @usecodebad.

Five rounds from today's shop. Each round two single cosmetics of the same type
slide in on their own Epic tile colours, split down a diagonal seam. Their prices
sit hidden on "? ? ?" plates while a four-second ring drains between them. Then
both prices roll up at once: the pricier side gets a crown, a slapped-on "MORE"
sticker, confetti and a pulse, the cheaper side dims into the dark, and a badge
in the middle points at the winner with the exact gap. A score-check card recaps
every round so people can count, and the outro asks "HOW MANY DID YOU GET RIGHT?".

Truth rules this format keeps:
  - both prices are the rows' own `price` (single items are never discounted, so
    there is no "regular price" talk here at all)
  - "MORE" goes on the higher `price`; the gap badge is the plain difference
  - pairs always differ by at least 300 V-Bucks, so there is never a tie to fudge
  - the chip over each name is the row's own `type`; rarity tiers are not shown,
    so the word "RARE" never lands on screen where it could read as scarcity
Nothing else is claimed: no "most people picked", no rating, no "back"/"rare".
"""

import math

from cc_motion import (ACCENT, INK, RARITY, W, H, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, EASE_BACK, Comp, an,
                       burst, character, code_badge, countdown, disclosure, esc, hexcol, price_roll,
                       progress, sticker, style_anim, tile_bg, words)
from cc_formats import (MIN_SECONDS, Ctx, Video, num, _caption, _hashtags, _hook_scene, _outro_scene, _pad,
                        rng, singles)

FORMAT = "costs_more"
ROUNDS, MIN_PAIRS = 5, 4
MIN_GAP = 300                    # V-Bucks between the two prices in a round
MAX_PER_TYPE = 2                 # keep the rounds varied: outfits, pickaxes, gliders...

HOOK, R, KEY = 3.0, 10.0, 4.5    # hook, one round, score check (seconds)
XF = .3                          # a scene outlives the next one's fade-in by this much
OUTRO_MIN = 7.5                  # _pad()'s shortest outro

# Beats inside a round, in seconds from the round's start.
T_A, T_B, ENTER = .1, .25, .7    # left / right cosmetics slide in
T_HEAD = .3                      # "WHICH COSTS MORE?"
T_VS = .6                        # VS badge slams in the middle
T_NAME = .8                      # names rise
T_PLATE = 1.05                   # "? ? ?" price plates pop in
T_CD, CD = 1.7, 4                # the ring
T_REV = T_CD + CD                # time's up
T_ROLL, ROLL = T_REV + .05, 1.0  # both prices count up together
T_LAND = T_ROLL + ROLL           # exact prices land: crown, dim, burst
T_MORE = T_LAND + .12            # "MORE" sticker
T_GAP = T_LAND + .45             # gap badge

# Layout (px). Everything a viewer reads stays in the apps' safe box (cc_safe):
# x 60-1020 above y 740, x 60-900 (left of the button rail) below it, y 230-1420.
# The code badge and #EpicPartner own the top-left corner down to y ~350, the
# round counter the top-right down to y ~292. The question sits in the wide top
# band; the two sides are two columns in the band beside the rail (x 60-900),
# with the seam, the ring and the gap badge between them.
HEAD_Y, HEAD_SIZE = 370, 92                  # the tape runs y ~355-470, clear of #EpicPartner
COL_L, COL_R, COL_W = SAFE_LEFT, SAFE_RIGHT - 10, 392   # name columns: A from 60, B ends at 890
A_CX, B_CX = COL_L + 196, COL_R - 190        # 256 and 700: each cosmetic over its column
ART_MAXW = 360
CHAR_BOTTOM = 1060
MID_X, MID_Y, RING = 484, 700, 190           # between the two, on the seam
NAME_BOTTOM = 1238
PLATE_Y, PLATE_W, PLATE_H = 1256, 376, 146   # y 1256-1402
PLATE_L, PLATE_R = COL_L + 2, COL_R + 6      # A plate's left edge, B plate's right edge
SPLIT_TOP, SPLIT_BOTTOM = 530, 410           # the seam's x at y 0 and at y 1920
CROWN_MIN_TOP = 494                          # under the header tape; the crown bobs up 22px
ART_TOP = CROWN_MIN_TOP + 70                 # the cosmetics' tops: the crown sits on, not over, the head
MORE_Y = CHAR_BOTTOM - 150

# Anton advance widths in em, measured in the render browser. Used to size names
# so they never wrap awkwardly or run off their half of the frame.
_ANTON = {
    'A': .495, 'B': .489, 'C': .484, 'D': .503, 'E': .422, 'F': .409, 'G': .495, 'H': .509,
    'I': .237, 'J': .476, 'K': .482, 'L': .408, 'M': .756, 'N': .508, 'O': .496, 'P': .482,
    'Q': .504, 'R': .487, 'S': .472, 'T': .406, 'U': .484, 'V': .479, 'W': .722, 'X': .494,
    'Y': .456, 'Z': .42, '0': .504, '1': .341, '2': .504, '3': .504, '4': .504, '5': .504,
    '6': .504, '7': .504, '8': .504, '9': .504, "'": .224, '.': .239, ',': .246, '-': .321,
    '!': .239, '?': .502, '&': .53, ':': .252, '/': .415, '(': .301, ')': .301, '#': .556,
    '+': .365, '"': .439,
}

CSS = f"""
/* burst() pieces are opaque at 0%, so with fill "both" they would sit stacked at
   the winner's chest for the whole round before flying. Same motion, but invisible
   until launch. This document only. */
@keyframes burst{{0%{{transform:translate(0,0) rotate(0) scale(1);opacity:0}}3%{{opacity:1}}
  100%{{transform:translate(var(--dx),var(--dy)) rotate(var(--r)) scale(.35);opacity:0}}}}
@keyframes cmOut{{0%{{transform:scale(1);opacity:1}}100%{{transform:scale(.3) rotate(-25deg);opacity:0}}}}
@keyframes cmFlash{{0%{{opacity:0}}25%{{opacity:.22}}100%{{opacity:0}}}}
@keyframes cmShade{{to{{opacity:.55}}}}
@keyframes cmGlow{{to{{opacity:1}}}}
@keyframes cmSoft{{to{{opacity:.5}}}}
@keyframes cmPlateWin{{to{{border-color:{ACCENT};box-shadow:0 0 0 6px rgba(232,255,58,.22),
  0 0 80px rgba(232,255,58,.55),0 12px 0 rgba(0,0,0,.35)}}}}
@keyframes cmPlateLose{{to{{filter:grayscale(1) brightness(.72);transform:scale(.94)}}}}
@keyframes cmSeam{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
@keyframes cmHalo{{0%,100%{{transform:scale(1);opacity:.55}}50%{{transform:scale(1.18);opacity:.9}}}}
"""


# ------------------------------------------------------------------ helpers

def _em(text: str) -> float:
    """Width of `text` in Anton caps, in em: .01em tracking, .18em between words."""
    ws = text.upper().split()
    return sum(_ANTON.get(ch, .52) + .01 for w in ws for ch in w) + .18 * max(0, len(ws) - 1)


def _fit_lines(name: str, width: float, cap1: float, min1: float, cap2: float) -> tuple:
    """(lines, size): one line when it can be set at `min1` or more, else the
    two-line break that allows the biggest type, keeping a quoted colourway
    ("'Black Panda'") together on its own line when that costs little."""
    one = min(cap1, width / max(_em(name), .1))
    ws = name.split()
    if one >= min1 or len(ws) < 2:
        return [name], one
    splits = []
    for i in range(1, len(ws)):
        a, b = " ".join(ws[:i]), " ".join(ws[i:])
        splits.append((min(cap2, width / max(_em(a), _em(b))), ws[i][:1] in "'\"(", [a, b]))
    top = max(s[0] for s in splits)
    size, _, lines = max((s for s in splits if s[0] >= top * .92), key=lambda s: (s[1], s[0]))
    return lines, size


def _row_lines(name: str, width: float, h: float, cap: float = 52, min1: float = 40) -> tuple:
    """(lines, size) for a name in a recap row: one line down to `min1` px, else
    the two-line break that allows the biggest type (as tall as the row allows)."""
    one = min(cap, width / max(_em(name), .1))
    ws = name.split()
    if one >= min1 or len(ws) < 2:
        return [name], one
    cap2 = min(min1, (h - 30 * 1.1 - 26) / 1.8)
    best = max((min(cap2, width / max(_em(" ".join(ws[:i])), _em(" ".join(ws[i:])))), i)
               for i in range(1, len(ws)))
    return [" ".join(ws[:best[1]]), " ".join(ws[best[1]:])], best[0]


def _gap(a: dict, b: dict) -> int:
    return abs(int(a["price"]) - int(b["price"]))


def _pick(ctx: Ctx) -> list:
    """Up to five (left, right) pairs of single items whose prices differ by at
    least MIN_GAP. Same type first (a real question: which of these two OUTFITS?),
    one pair per type before any type repeats, an outfit pair first when there is
    one. Cross-type pairs only if same-type ones run out. Deterministic for the day."""
    seen, pool = set(), []
    for it in singles(ctx):
        if it["name"] not in seen and it.get("price"):
            seen.add(it["name"])
            pool.append(it)
    r = rng(ctx, 3)
    r.shuffle(pool)
    # Outfits lead: a full character is the strongest opener and the hook shows it.
    pool.sort(key=lambda it: it["type"] != "Outfit")

    pairs, used, per_type = [], set(), {}

    def tile(it):
        return ((it.get("tile_colors") or [""])[0] or "").lower()

    def partner(a, same_type, two_tones):
        for b in pool:
            if b["name"] in used or b["name"] == a["name"] or _gap(a, b) < MIN_GAP:
                continue
            if same_type and b["type"] != a["type"]:
                continue
            if two_tones and tile(b) == tile(a):
                continue
            return b
        return None

    def take(a, b):
        pairs.append((a, b))
        used.update({a["name"], b["name"]})
        per_type[a["type"]] = per_type.get(a["type"], 0) + 1

    # Within each pass, pairs on two different tile colours first, so the split
    # screen reads as two sides.
    for cap, same in ((1, True), (MAX_PER_TYPE, True), (ROUNDS, True), (ROUNDS, False)):
        for two_tones in (True, False):
            for a in pool:
                if len(pairs) >= ROUNDS:
                    break
                if a["name"] in used or per_type.get(a["type"], 0) >= cap:
                    continue
                b = partner(a, same, two_tones)
                if b:
                    take(a, b)
    if len(pairs) < MIN_PAIRS:
        return []

    # Play order: the first pair stays first (it's in the hook), the rest shuffled.
    rest = pairs[1:]
    r.shuffle(rest)
    pairs = pairs[:1] + rest

    # Which side the pricier item sits on: mixed, never all one side, so the
    # answer can't be guessed from the layout.
    n = len(pairs)
    for _ in range(40):
        sides = [r.random() < .5 for _ in range(n)]
        if sum(sides) in (n // 2, n - n // 2):
            break
    else:
        sides = [k % 2 == 0 for k in range(n)]
    out = []
    for (a, b), more_left in zip(pairs, sides):
        hi, lo = (a, b) if a["price"] > b["price"] else (b, a)
        out.append((hi, lo) if more_left else (lo, hi))
    return out


def _art_box(it: dict) -> tuple:
    """(height, centre y) for a cosmetic: outfits stand on the floor line, smaller
    cosmetics float a little higher and smaller."""
    if it["type"] == "Outfit":
        h = CHAR_BOTTOM - ART_TOP
        return h, CHAR_BOTTOM - h / 2
    h = min(470, CHAR_BOTTOM - 30 - ART_TOP)
    return h, CHAR_BOTTOM - 30 - h / 2


# --------------------------------------------------------------- components

def _header(t0: float) -> str:
    """WHICH COSTS MORE? -- words slam in one after another, MORE? in the accent.
    It sits on a strip of dark tape that wipes in first, so the accent word stays
    readable on any tile colour (some are acid yellow-green themselves)."""
    text = "WHICH COSTS MORE?"
    spans = []
    for i, w in enumerate(text.split()):
        col = ACCENT if i == 2 else "#fff"
        a = style_anim(an("slam", t0 + T_HEAD + i * .08, .45))
        spans.append(f'<span style="display:inline-block;margin:0 .09em;color:{col};{a}">{w}</span>')
    bw = (_em(text) + .18) * HEAD_SIZE + 64
    bh = HEAD_SIZE * .92 + 30
    tape = (f'<div class="abs" style="left:{(W - bw) / 2:.0f}px;top:{HEAD_Y - 15:.0f}px;width:{bw:.0f}px;'
            f'height:{bh:.0f}px"><div class="full" style="background:rgba(10,10,11,.8);border-radius:16px;'
            f'box-shadow:0 10px 0 rgba(0,0,0,.3);transform-origin:0 50%;'
            f'{style_anim(an("strike", t0 + T_HEAD - .12, .35))}"></div></div>')
    return (f'<div class="full" style="transform:rotate(-1.2deg);transform-origin:{W / 2:.0f}px {HEAD_Y + 40}px">'
            f'{tape}<div class="abs d" style="left:0;width:{W}px;top:{HEAD_Y}px;text-align:center;'
            f'font-size:{HEAD_SIZE}px;text-shadow:0 6px 0 rgba(0,0,0,.4)">'
            f'{"".join(spans)}</div></div>')


def _panel(item: dict, left: bool, t0: float, winner: bool, cx: float, cy: float, land: float) -> str:
    """One side of the split: the item's own tile colours, its stage centred on
    its own column. After the reveal the winner's side gets a spotlight and the
    loser's sinks into shadow."""
    if left:
        x0 = -70                                  # the stage's centre: (x0 + x1) / 2 = A_CX
        x1 = 2 * A_CX - x0
        clip = f"polygon(0 0,{SPLIT_TOP - x0}px 0,{SPLIT_BOTTOM - x0}px 100%,0 100%)"
    else:
        x1 = W + 70
        x0 = 2 * B_CX - x1
        clip = f"polygon({SPLIT_TOP - x0}px 0,100% 0,100% 100%,{SPLIT_BOTTOM - x0}px 100%)"
    box = f"left:{x0}px;top:0;width:{x1 - x0}px;height:{H}px;clip-path:{clip}"
    px = cx - x0
    if winner:
        fx = (f'<div class="full" style="opacity:0;background:radial-gradient(circle at {px:.0f}px {cy:.0f}px,'
              f'rgba(232,255,58,.40),rgba(232,255,58,.10) 380px,transparent 620px);'
              f'{style_anim(an("cmGlow", land, .5))}"></div>')
    else:
        fx = (f'<div class="full" style="opacity:0;background:#050507;'
              f'{style_anim(an("cmShade", land, .55))}"></div>')
    return (f'<div class="abs" style="{box}">'
            f'{tile_bg(item.get("tile_colors") or [], item.get("rarity", ""), t0)}{fx}</div>')


def _seam(t0: float) -> str:
    """The dark diagonal between the halves draws itself top to bottom."""
    deg = math.degrees(math.atan2(SPLIT_TOP - SPLIT_BOTTOM, H))
    mid = (SPLIT_TOP + SPLIT_BOTTOM) / 2
    return (f'<div class="abs" style="left:{mid - 5:.0f}px;top:-40px;width:10px;height:{H + 80}px;'
            f'transform:rotate({deg:.3f}deg)"><div class="full" style="background:{INK};'
            f'box-shadow:0 0 30px rgba(0,0,0,.6);transform-origin:50% 0;'
            f'{style_anim(an("cmSeam", t0, .45))}"></div></div>')


def _scrim() -> str:
    """Darkens the bands the words sit on, so white type and the lime code badge
    hold on pale tile colours (some are acid yellow-green themselves)."""
    return ('<div class="full" style="background:linear-gradient(180deg,rgba(0,0,0,.5) 0,'
            'rgba(0,0,0,.36) 20%,rgba(0,0,0,.2) 30%,rgba(0,0,0,0) 42%,rgba(0,0,0,0) 58%,'
            'rgba(0,0,0,.3) 70%,rgba(0,0,0,.55) 100%)"></div>')


def _kicker(it: dict, x: float, y: float, start: float, right: bool) -> str:
    """TYPE chip with a rarity-coloured dot, straight from the row's `type`."""
    col = RARITY.get(it.get("rarity", ""), "#9AA0A6")
    pos = f"right:{W - x:.0f}px;" if right else f"left:{x:.0f}px;"
    return (f'<div class="abs" style="{pos}top:{y:.0f}px;transform:rotate({1.5 if right else -1.5}deg)">'
            f'<div style="display:inline-flex;align-items:center;gap:12px;background:rgba(10,10,11,.82);'
            f'border-radius:12px;padding:6px 16px 6px 13px;font-size:30px;font-weight:800;line-height:1.2;'
            f'letter-spacing:.1em;white-space:nowrap;{style_anim(an("rise", start, .45))}">'
            f'<i style="width:16px;height:16px;border-radius:50%;background:{col};'
            f'box-shadow:0 0 14px {col}"></i><span>{esc((it.get("type") or "").upper())}</span></div></div>')


def _name(it: dict, x: float, right: bool, start: float) -> tuple:
    """The item name, bottom-aligned on NAME_BOTTOM, sized to its column.
    Returns (html, top of the block)."""
    lines, size = _fit_lines(it["name"], COL_W, 78, 56, 58)
    lh = size * .92
    top = NAME_BOTTOM - len(lines) * lh
    pos = f"right:{W - x:.0f}px;" if right else f"left:{x:.0f}px;"
    out = []
    k = 0
    for li, line in enumerate(lines):
        spans = []
        for wi, w in enumerate(line.split()):
            a = style_anim(an("rise", start + k * .06, .45))
            gap = "margin-left:.18em;" if wi else ""
            spans.append(f'<span style="display:inline-block;{gap}{a}">{esc(w)}</span>')
            k += 1
        out.append(f'<div class="abs d" style="{pos}top:{top + li * lh:.0f}px;font-size:{size:.0f}px;'
                   f'line-height:.92;white-space:nowrap;text-align:{"right" if right else "left"};'
                   f'text-shadow:0 7px 0 rgba(0,0,0,.35),0 0 30px rgba(0,0,0,.4)">{"".join(spans)}</div>')
    return "".join(out), top


def _plate(it: dict, x: float, t0: float, winner: bool, t_in: float) -> str:
    """A price plate: "? ? ?" wobbles until time's up, then the real price rolls up
    from zero. On landing the winner's plate lights up in the accent, the loser's
    goes grey and steps back."""
    w, h = PLATE_W, PLATE_H
    land = t0 + T_LAND
    after = (style_anim(an("cmPlateWin", land, .35), an("pulse", land, .4))
             if winner else style_anim(an("cmPlateLose", land, .5)))
    size, unit_size, gap = 86, 30, 16            # Anton's comma hangs below its line box
    num_top = (h - 8 - (size * .9 + gap + unit_size * .9)) / 2
    qs = (f'<div class="abs d" style="left:0;width:{w - 8}px;top:{num_top:.0f}px;text-align:center;'
          f'font-size:{size}px;color:#fff;text-shadow:0 7px 0 rgba(0,0,0,.35);'
          f'{style_anim(an("fadeout", t0 + T_REV, .15))}">'
          f'<span style="display:inline-block;'
          f'{style_anim(an("wobble", t_in + .4, .42, "ease-in-out", "infinite", "alternate"))}">'
          f'? ? ?</span></div>')
    # price_roll's counter shows "0" before it starts, so it only appears on cue.
    psize = min(size, (w - 60) / max(_em(f"{int(it['price']):,}"), .1))
    roll = (f'<div class="full" style="{style_anim(an("fadein", t0 + T_ROLL, .06))}">'
            f'{price_roll(int(it["price"]), (w - 8) / 2, num_top + (size - psize) * .45, psize, t0 + T_ROLL, ROLL, ACCENT, "center", "")}'
            f'</div>')
    unit = (f'<div class="abs d" style="left:0;width:{w - 8}px;top:{num_top + size * .9 + gap:.0f}px;'
            f'text-align:center;font-size:{unit_size}px;letter-spacing:.14em;text-indent:.14em;'
            f'color:rgba(255,255,255,.78)">V-BUCKS</div>')
    return (f'<div class="abs" style="left:{x:.0f}px;top:{PLATE_Y}px;width:{w}px;height:{h}px">'
            f'<div class="full" style="{style_anim(an("pop", t_in, .55, EASE_BACK))}">'
            f'<div class="full" style="border-radius:24px;overflow:hidden;'
            f'background:linear-gradient(165deg,#1f2029 0%,#0b0b0e 75%);'
            f'border:4px solid rgba(255,255,255,.2);box-shadow:0 12px 0 rgba(0,0,0,.35);{after}">'
            f'{qs}{roll}{unit}</div></div></div>')


def _crown(cx: float, top: float, start: float, rot: float) -> str:
    """A gold crown that drops onto the winner, then bobs gently with a halo."""
    w, h = 124, 90
    shape = "polygon(0 100%,0 28%,24% 60%,50% 4%,76% 60%,100% 28%,100% 100%)"
    jewels = "".join(
        f'<i class="abs" style="left:{jx - 11:.0f}px;top:{jy - 11:.0f}px;width:22px;height:22px;'
        f'border-radius:50%;background:{c};box-shadow:0 0 0 4px #b8740a,0 0 16px {c}"></i>'
        for jx, jy, c in ((6, 30, "#fff"), (w / 2, 8, ACCENT), (w - 6, 30, "#fff")))
    band = (f'<div class="abs" style="left:0;right:0;bottom:0;height:26%;background:#c98200;'
            f'border-top:4px solid rgba(255,255,255,.35)"></div>')
    return (f'<div class="abs" style="left:{cx - w / 2:.0f}px;top:{top:.0f}px;width:{w}px;height:{h}px;'
            f'transform:rotate({rot}deg)">'
            f'<div class="abs" style="left:-60px;top:-50px;right:-60px;bottom:-50px;'
            f'{style_anim(an("fadein", start + .3, .3))}">'
            f'<div class="full" style="border-radius:50%;'
            f'background:radial-gradient(closest-side,rgba(255,214,70,.55),transparent);'
            f'{style_anim(an("cmHalo", start + .6, 1.4, "ease-in-out", "infinite"))}"></div></div>'
            f'<div class="full" style="{style_anim(an("crown", start, .6, EASE_BACK))}">'
            f'<div class="full" style="transform-origin:50% 100%;'
            f'{style_anim(an("float", start + .6, 1.8, "ease-in-out", "infinite", "alternate"))}">'
            f'<div class="full" style="filter:drop-shadow(0 8px 0 rgba(0,0,0,.35))">'
            f'<div class="full" style="clip-path:{shape};'
            f'background:linear-gradient(180deg,#fff0a0 0%,#ffcf2e 45%,#e89b00 100%)">{band}</div>'
            f'{jewels}</div></div></div></div>')


def _gap_badge(gap: int, left: bool, start: float) -> str:
    """Centre badge after the reveal: the exact gap, with a pointer at the winner."""
    d = 200
    tri = ("polygon(100% 0,0 50%,100% 100%)" if left else "polygon(0 0,100% 50%,0 100%)")
    side = "left:-40px;" if left else "right:-40px;"
    txt = f"+{gap:,}"
    size = min(64, (d - 50) / max(_em(txt), .1))
    return (f'<div class="abs" style="left:{MID_X - d / 2:.0f}px;top:{MID_Y - d / 2:.0f}px;width:{d}px;height:{d}px">'
            f'<div class="full" style="{style_anim(an("pop", start, .55, EASE_BACK))}">'
            f'<div class="abs" style="{side}top:{d / 2 - 30:.0f}px;width:46px;height:60px;background:{ACCENT};'
            f'clip-path:{tri}"></div>'
            f'<div class="full" style="border-radius:50%;background:{INK};border:8px solid {ACCENT};'
            f'box-shadow:0 12px 0 rgba(0,0,0,.35),0 0 50px rgba(232,255,58,.35);display:flex;'
            f'flex-direction:column;align-items:center;justify-content:center">'
            f'<div class="d" style="font-size:{size:.0f}px;line-height:1;color:{ACCENT}">{txt}</div>'
            f'<div class="d" style="font-size:30px;line-height:.9;letter-spacing:.1em;margin:6px 0 0 .1em;'
            f'color:#fff">V-BUCKS</div></div></div></div>')


# -------------------------------------------------------------------- scenes

def _round(comp: Comp, ctx: Ctx, pair: tuple, k: int, n: int, t0: float, rlen: float = R):
    a, b = pair
    left_wins = a["price"] > b["price"]
    # A four-pair day gets longer rounds rather than a long end card; each whole
    # extra second goes to the ring, and everything after it moves along.
    cd = min(6, CD + int(rlen - R))
    tp = t0 + cd - CD                   # the base for every beat after the ring
    land = tp + T_LAND
    ha, cya = _art_box(a)
    hb, cyb = _art_box(b)
    win_cx, win_top = (A_CX, cya - ha / 2) if left_wins else (B_CX, cyb - hb / 2)

    inner = (_panel(a, True, t0, left_wins, A_CX, cya, land)
             + _panel(b, False, t0, not left_wins, B_CX, cyb, land))
    inner += _scrim()
    inner += _seam(t0)
    # Everything but the backdrop shakes on the landing, so no frame edge shows.
    inner += f'<div class="full" style="{style_anim(an("shake", land, .35, "linear"))}">'
    inner += _header(t0)

    for it, cx, cy, h, left, t_in in ((a, A_CX, cya, ha, True, t0 + T_A),
                                      (b, B_CX, cyb, hb, False, t0 + T_B)):
        wins = left == left_wins
        after = (style_anim(an("pulse", land, .45, "ease-in-out", "3")) if wins
                 else style_anim(an("dim", land, .55)))
        inner += (f'<div class="full" style="transform-origin:{cx:.0f}px {cy + h / 2:.0f}px;{after}">'
                  + character(ctx.art(it), cx, cy, h, t_in, "fromL" if left else "fromR", ENTER,
                              "float" if left else "sway", it.get("rarity", ""), it["name"], maxw=ART_MAXW,
                              trim=True)
                  + "</div>")

    # VS badge, then the ring takes its place and drains around it.
    inner += (f'<div class="full" style="{style_anim(an("fadeout", t0 + T_CD + .3, .2))}">'
              f'<div class="abs d" style="left:{MID_X - 88:.0f}px;top:{MID_Y - 88:.0f}px;width:176px;height:176px;'
              f'border-radius:50%;background:{INK};border:8px solid {ACCENT};display:flex;align-items:center;'
              f'justify-content:center;font-size:90px;color:{ACCENT};box-shadow:0 12px 0 rgba(0,0,0,.35);'
              f'{style_anim(an("slam", t0 + T_VS, .45))}">VS</div></div>')
    origin = f"transform-origin:{MID_X:.0f}px {MID_Y:.0f}px;"
    inner += (f'<div class="full" style="{origin}'
              f'{style_anim(an("cmOut", tp + T_REV - .08, .3, "cubic-bezier(.5,0,.8,.3)"))}">'
              f'<div class="full" style="{origin}{style_anim(an("pop", t0 + T_CD, .5, EASE_BACK))}">'
              f'{countdown(cd, MID_X, MID_Y, RING, t0 + T_CD, "LOCK IT IN")}</div></div>')

    # Names, type chips and price plates, each in its own column.
    for it, left in ((a, True), (b, False)):
        wins = left == left_wins
        x = COL_L if left else COL_R
        t_name = t0 + T_NAME + (0 if left else .1)
        name_html, name_top = _name(it, x, not left, t_name)
        soft = "" if wins else style_anim(an("cmSoft", land, .5))
        inner += (f'<div class="full" style="{soft}">'
                  + _kicker(it, x, name_top - 58, t_name - .1, not left) + name_html + "</div>")
        inner += _plate(it, PLATE_L if left else PLATE_R - PLATE_W, tp, wins,
                        t0 + T_PLATE + (0 if left else .1))

    # The reveal: crown, halo, MORE sticker, confetti, gap badge.
    more_w = (_em("MORE") + .84) * 76
    more_x = min(max(win_cx - more_w / 2, COL_L + 6), COL_R - more_w - 6)
    inner += _crown(win_cx, max(CROWN_MIN_TOP, win_top - 80), land, -6 if left_wins else 6)
    inner += sticker("MORE", more_x, MORE_Y, 76, tp + T_MORE, ACCENT, INK, -8 if left_wins else 7)
    inner += burst(win_cx, MID_Y, land, ctx.seed + k * 23)
    inner += _gap_badge(_gap(a, b), left_wins, tp + T_GAP)
    inner += "</div>"
    inner += (f'<div class="full" style="background:#fff;opacity:0;pointer-events:none;'
              f'{style_anim(an("cmFlash", land, .45, "ease-out"))}"></div>')
    inner += progress(t0, t0 + rlen, k, n)
    comp.scene(t0, t0 + rlen + XF, inner, fade_in=.25, fade_out=.05)

    comp.cue(t0 + T_A, "whoosh")
    comp.cue(t0 + T_B, "whoosh")
    comp.cue(t0 + T_HEAD, "slam")
    comp.cue(t0 + T_VS, "slam")
    comp.cue(t0 + T_PLATE, "pop")
    for s in range(cd):
        comp.cue(t0 + T_CD + s, "tick")
    comp.cue(tp + T_ROLL, "reveal")
    comp.cue(land, "cash")
    comp.cue(tp + T_MORE, "slam")
    comp.cue(tp + T_GAP, "pop")


KEY_X, KEY_W = SAFE_LEFT, SAFE_RIGHT - SAFE_LEFT           # 60-900: beside the rail
KEY_TOP, KEY_BOTTOM = 572, SAFE_BOTTOM - 12


def _key_thumb(ctx: Ctx, it: dict, x: float, y: float, th: float, winner: bool, start: float) -> str:
    """One side's thumbnail on its tile colours. The pricier side is outlined in
    the accent and tagged MORE; the other is dimmed."""
    col = RARITY.get(it.get("rarity", ""), "#777")
    tc = it.get("tile_colors") or []
    c1 = hexcol(tc[0] if tc else "", col)
    c2 = hexcol(tc[1] if len(tc) > 1 else "", "#101014")
    uri = ctx.art(it)
    dim = "" if winner else "filter:grayscale(.75) brightness(.6);"
    img = (f'<img data-trim src="{uri}" data-name="{esc(it["name"])}" '
           f'style="width:100%;height:100%;object-fit:contain;display:block;{dim}">' if uri else "")
    ring = (f"box-shadow:0 0 0 5px {ACCENT},0 0 28px rgba(232,255,58,.45);" if winner
            else "box-shadow:0 0 0 3px rgba(255,255,255,.12);")
    tag = ""
    if winner:
        tag = (f'<div class="abs" style="left:0;width:{th:.0f}px;top:{th - 26:.0f}px;text-align:center">'
               f'<div class="d" style="display:inline-block;background:{ACCENT};color:{INK};font-size:30px;'
               f'line-height:.9;padding:.14em .32em .08em;border-radius:8px;transform:rotate(-4deg);'
               f'box-shadow:0 5px 0 rgba(0,0,0,.35);{style_anim(an("pop", start + .35, .5, EASE_BACK))}">'
               f'MORE</div></div>')
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{th:.0f}px;height:{th:.0f}px">'
            f'<div class="full" style="border-radius:16px;overflow:hidden;{ring}'
            f'background:radial-gradient(circle at 50% 38%,{c1},{c2})">{img}</div>{tag}</div>')


def _key_row(ctx: Ctx, pair: tuple, k: int, y: float, h: float, start: float) -> str:
    """One score-check line: both sides' thumbnails as they stood in the round
    (the pricier one outlined and tagged MORE), then the pricier one's name and
    both prices."""
    a, b = pair
    left_wins = a["price"] > b["price"]
    hi, lo = (a, b) if left_wins else (b, a)
    th = h - 26
    tx = 14 + 2 * th + 14 + 24
    name_w = KEY_W - tx - 22
    lines, nsize = _row_lines(hi["name"], name_w, h)
    block = len(lines) * nsize * .9 + 10 + 30 * 1.1
    ny = (h - block) / 2
    prices = (f'<span style="color:{ACCENT}">{int(hi["price"]):,}</span>'
              f'<span style="color:rgba(255,255,255,.6)"> VS </span>{int(lo["price"]):,} V-BUCKS')
    return (f'<div class="abs" style="left:{KEY_X}px;top:{y:.0f}px;width:{KEY_W}px;height:{h:.0f}px">'
            f'<div class="full" style="{style_anim(an("fromL", start, .55))}">'
            f'<div class="full" style="background:rgba(10,10,11,.78);border-radius:22px"></div>'
            + _key_thumb(ctx, a, 14, 13, th, left_wins, start)
            + _key_thumb(ctx, b, 14 + th + 14, 13, th, not left_wins, start)
            + f'<div class="abs d" style="left:2px;top:2px;width:46px;height:46px;border-radius:50%;'
              f'background:{ACCENT};color:{INK};font-size:30px;line-height:48px;text-align:center;'
              f'box-shadow:0 3px 0 rgba(0,0,0,.35)">{k}</div>'
              f'<div class="abs d" style="left:{tx:.0f}px;top:{ny:.0f}px;width:{name_w:.0f}px;'
              f'font-size:{nsize:.0f}px;line-height:.9;white-space:nowrap">'
              f'{"<br>".join(esc(ln) for ln in lines)}</div>'
              f'<div class="abs" style="left:{tx + 2:.0f}px;top:{ny + len(lines) * nsize * .9 + 10:.0f}px;'
              f'font-size:30px;font-weight:800;line-height:1.1;letter-spacing:.02em;color:#fff;'
              f'white-space:nowrap">{prices}</div>'
            + '</div></div>')


def _score_check(comp: Comp, ctx: Ctx, pairs: list, t0: float):
    inner = tile_bg(["#262a36", "#0b0b0e"], "", t0)
    inner += words("SCORE CHECK", SAFE_LEFT, 366, 116, t0 + .1, "#fff", .1, "slam", "left", 900)
    inner += sticker("+1 FOR EVERY RIGHT ANSWER", SAFE_LEFT + 6, 494, 36, t0 + .45, ACCENT, INK, -3)
    n = len(pairs)
    step = min(170, (KEY_BOTTOM - KEY_TOP + 14) / n)
    for i, pair in enumerate(pairs):
        start = t0 + .55 + i * .15
        inner += _key_row(ctx, pair, i + 1, KEY_TOP + i * step, step - 14, start)
        comp.cue(start + .35, "tick")
    comp.scene(t0, t0 + KEY + XF, inner, fade_in=.25, fade_out=.05)
    comp.cue(t0 + .05, "whoosh")
    comp.cue(t0 + .1, "slam")
    comp.cue(t0 + .45, "pop")


# -------------------------------------------------------------------- build

def build(ctx: Ctx):
    pairs = _pick(ctx)
    if len(pairs) < MIN_PAIRS:
        return None
    n = len(pairs)

    # Five rounds make a 62.5 s video; four stretch (to 11.75 s) rather than
    # leave a 15-second end card.
    rlen = max(R, min(12.0, (MIN_SECONDS - OUTRO_MIN - HOOK - KEY) / n))
    content_end = HOOK + n * rlen + KEY
    comp = Comp(content_end + _pad(content_end))
    comp.css(CSS)

    _hook_scene(comp, ctx, "WHICH COSTS MORE?", "LOCK IN YOUR ANSWER", f"{n} ROUNDS",
                HOOK + .5, pairs[0][0], pairs[0][1])
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.3, "whoosh"); comp.cue(.9, "pop")

    for k, pair in enumerate(pairs, 1):
        _round(comp, ctx, pair, k, n, HOOK + (k - 1) * rlen, rlen)

    _score_check(comp, ctx, pairs, HOOK + n * rlen)

    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    winners = [max(p, key=lambda it: it["price"]) for p in pairs]
    losers = [min(p, key=lambda it: it["price"]) for p in pairs]
    _outro_scene(comp, ctx, content_end, comp.duration, "HOW MANY DID YOU GET RIGHT?",
                 winners + losers)
    comp.add(code_badge(.4))
    comp.add(disclosure())

    rounds = "\n".join(f"{num(k)} {a['name']} 🆚 {b['name']} · {a['type']}"
                       + ("" if a["type"] == b["type"] else f" vs {b['type']}")
                       for k, (a, b) in enumerate(pairs, 1))
    body = rounds          # no prices here: they're the answers
    tags = _hashtags("whichcostsmore", *(it["name"] for it in pairs[0]))
    return Video(
        FORMAT, comp,
        title=f"Which Costs More? Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"Which Costs More? Fortnite Item Shop Quiz {ctx.day_label} #shorts",
        caption=_caption(f"🤔 WHICH COSTS MORE? — Fortnite Item Shop, {ctx.day_label}\n"
                         f"{n} rounds from today's shop. Lock in your answer before each reveal 👇",
                         body, f"How many did you get right out of {n}? Comment your score", tags),
        hashtags=tags)
