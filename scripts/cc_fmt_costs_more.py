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

from cc_motion import (ACCENT, INK, RARITY, W, H, SAFE_RIGHT, EASE_BACK, Comp, an, burst,
                       character, code_badge, countdown, disclosure, esc, hexcol, price_roll,
                       progress, sticker, style_anim, tile_bg, words)
from cc_formats import (Ctx, Video, _caption, _hashtags, _hook_scene, _outro_scene, _pad, rng,
                        singles)

FORMAT = "costs_more"
ROUNDS, MIN_PAIRS = 5, 4
MIN_GAP = 300                    # V-Bucks between the two prices in a round
MAX_PER_TYPE = 2                 # keep the rounds varied: outfits, pickaxes, gliders...

HOOK, R, KEY = 3.0, 10.0, 4.5    # hook, one round, score check (seconds)
XF = .3                          # a scene outlives the next one's fade-in by this much

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

# Layout (px). Everything important sits in y 190..1480; below y=880 it stays left
# of x=960 (TikTok's like/comment rail).
HEAD_Y, HEAD_SIZE = 326, 92
A_CX, B_CX = 282, 798
CHAR_BOTTOM = 1110
MID_X, MID_Y, RING = W / 2, 780, 220
COL_L, COL_R, COL_W = 60, SAFE_RIGHT - 10, 410  # name columns: A from 60, B ends at 950
NAME_BOTTOM = 1282
PLATE_Y, PLATE_W, PLATE_H = 1300, 400, 160
SPLIT = 120                                  # the seam leans this far across the frame
CROWN_MIN_TOP = 466                          # header tape ends ~431; the crown bobs up 22px

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
/* The shared hook sets its title on one 170px line, which runs "WHICH COSTS MORE?"
   off both edges. Here it wraps to two centred lines with MORE? in the accent.
   Scoped to this video's hook scene only. */
body>.scene:first-child .abs.d[style*="font-size:170px"]{{left:40px!important;width:1000px!important;
  font-size:150px!important}}
body>.scene:first-child .abs.d[style*="font-size:170px"]>span{{margin:0 .09em!important}}
body>.scene:first-child .abs.d[style*="font-size:170px"]>span:last-child{{color:{ACCENT}}}
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
        h = 590
        return h, CHAR_BOTTOM - h / 2
    h = 500
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


def _panel(item: dict, left: bool, t0: float, winner: bool, cx: float, cy: float) -> str:
    """One half of the split: the item's own tile colours. After the reveal the
    winner's half gets a spotlight and the loser's half sinks into shadow."""
    w = W / 2 + SPLIT / 2
    if left:
        box = (f"left:0;top:0;width:{w:.0f}px;height:{H}px;"
               f"clip-path:polygon(0 0,100% 0,calc(100% - {SPLIT}px) 100%,0 100%)")
        px = cx
    else:
        box = (f"right:0;top:0;width:{w:.0f}px;height:{H}px;"
               f"clip-path:polygon({SPLIT}px 0,100% 0,100% 100%,0 100%)")
        px = cx - (W - w)
    land = t0 + T_LAND
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
    deg = math.degrees(math.atan2(SPLIT, H))
    return (f'<div class="abs" style="left:{MID_X - 5:.0f}px;top:-40px;width:10px;height:{H + 80}px;'
            f'transform:rotate({deg:.3f}deg)"><div class="full" style="background:{INK};'
            f'box-shadow:0 0 30px rgba(0,0,0,.6);transform-origin:50% 0;'
            f'{style_anim(an("cmSeam", t0, .45))}"></div></div>')


def _kicker(it: dict, x: float, y: float, start: float, right: bool) -> str:
    """TYPE chip with a rarity-coloured dot, straight from the row's `type`."""
    col = RARITY.get(it.get("rarity", ""), "#9AA0A6")
    pos = f"right:{W - x:.0f}px;" if right else f"left:{x:.0f}px;"
    return (f'<div class="abs" style="{pos}top:{y:.0f}px;transform:rotate({1.5 if right else -1.5}deg)">'
            f'<div style="display:inline-flex;align-items:center;gap:12px;background:rgba(10,10,11,.8);'
            f'border-radius:12px;padding:8px 16px 8px 13px;font-size:22px;font-weight:800;'
            f'letter-spacing:.16em;white-space:nowrap;{style_anim(an("rise", start, .45))}">'
            f'<i style="width:15px;height:15px;border-radius:50%;background:{col};'
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
    qs = (f'<div class="abs d" style="left:0;width:{w}px;top:12px;text-align:center;font-size:92px;'
          f'color:#fff;text-shadow:0 7px 0 rgba(0,0,0,.35);{style_anim(an("fadeout", t0 + T_REV, .15))}">'
          f'<span style="display:inline-block;'
          f'{style_anim(an("wobble", t_in + .4, .42, "ease-in-out", "infinite", "alternate"))}">'
          f'? ? ?</span></div>')
    # price_roll's counter shows "0" before it starts, so it only appears on cue.
    roll = (f'<div class="full" style="{style_anim(an("fadein", t0 + T_ROLL, .06))}">'
            f'{price_roll(int(it["price"]), w / 2, 12, 92, t0 + T_ROLL, ROLL, ACCENT, "center", "")}</div>')
    unit = (f'<div class="abs" style="left:0;width:{w}px;bottom:14px;text-align:center;font-size:19px;'
            f'font-weight:800;letter-spacing:.34em;color:rgba(255,255,255,.72)">V-BUCKS</div>')
    return (f'<div class="abs" style="left:{x:.0f}px;top:{PLATE_Y}px;width:{w}px;height:{h}px">'
            f'<div class="full" style="{style_anim(an("pop", t_in, .55, EASE_BACK))}">'
            f'<div class="full" style="border-radius:24px;overflow:hidden;'
            f'background:linear-gradient(165deg,#1f2029 0%,#0b0b0e 75%);'
            f'border:4px solid rgba(255,255,255,.2);box-shadow:0 12px 0 rgba(0,0,0,.35);{after}">'
            f'{qs}{roll}{unit}</div></div></div>')


def _crown(cx: float, top: float, start: float, rot: float) -> str:
    """A gold crown that drops onto the winner, then bobs gently with a halo."""
    w, h = 136, 100
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
    size = min(66, (d - 44) / max(_em(txt), .1))
    return (f'<div class="abs" style="left:{MID_X - d / 2:.0f}px;top:{MID_Y - d / 2:.0f}px;width:{d}px;height:{d}px">'
            f'<div class="full" style="{style_anim(an("pop", start, .55, EASE_BACK))}">'
            f'<div class="abs" style="{side}top:{d / 2 - 30:.0f}px;width:46px;height:60px;background:{ACCENT};'
            f'clip-path:{tri}"></div>'
            f'<div class="full" style="border-radius:50%;background:{INK};border:8px solid {ACCENT};'
            f'box-shadow:0 12px 0 rgba(0,0,0,.35),0 0 50px rgba(232,255,58,.35);display:flex;'
            f'flex-direction:column;align-items:center;justify-content:center">'
            f'<div class="d" style="font-size:{size:.0f}px;line-height:1;color:{ACCENT}">{txt}</div>'
            f'<div style="font-size:15px;font-weight:800;letter-spacing:.22em;margin:8px 0 0 .22em;'
            f'color:#fff">V-BUCKS</div></div></div></div>')


# -------------------------------------------------------------------- scenes

def _round(comp: Comp, ctx: Ctx, pair: tuple, k: int, n: int, t0: float):
    a, b = pair
    left_wins = a["price"] > b["price"]
    land = t0 + T_LAND
    ha, cya = _art_box(a)
    hb, cyb = _art_box(b)
    win_cx, win_top = (A_CX, cya - ha / 2) if left_wins else (B_CX, cyb - hb / 2)

    inner = _panel(a, True, t0, left_wins, A_CX, cya) + _panel(b, False, t0, not left_wins, B_CX, cyb)
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
                              "float" if left else "sway", it.get("rarity", ""), it["name"])
                  + "</div>")

    # VS badge, then the ring takes its place and drains around it.
    inner += (f'<div class="full" style="{style_anim(an("fadeout", t0 + T_CD + .3, .2))}">'
              f'<div class="abs d" style="left:{MID_X - 95:.0f}px;top:{MID_Y - 95:.0f}px;width:190px;height:190px;'
              f'border-radius:50%;background:{INK};border:8px solid {ACCENT};display:flex;align-items:center;'
              f'justify-content:center;font-size:96px;color:{ACCENT};box-shadow:0 12px 0 rgba(0,0,0,.35);'
              f'{style_anim(an("slam", t0 + T_VS, .45))}">VS</div></div>')
    origin = f"transform-origin:{MID_X:.0f}px {MID_Y:.0f}px;"
    inner += (f'<div class="full" style="{origin}'
              f'{style_anim(an("cmOut", t0 + T_REV - .08, .3, "cubic-bezier(.5,0,.8,.3)"))}">'
              f'<div class="full" style="{origin}{style_anim(an("pop", t0 + T_CD, .5, EASE_BACK))}">'
              f'{countdown(CD, MID_X, MID_Y, RING, t0 + T_CD, "LOCK IT IN")}</div></div>')

    # Names, type chips and price plates, each on its own half.
    for it, left in ((a, True), (b, False)):
        wins = left == left_wins
        x = COL_L if left else COL_R
        t_name = t0 + T_NAME + (0 if left else .1)
        name_html, name_top = _name(it, x, not left, t_name)
        soft = "" if wins else style_anim(an("cmSoft", land, .5))
        inner += (f'<div class="full" style="{soft}">'
                  + _kicker(it, x, name_top - 54, t_name - .1, not left) + name_html + "</div>")
        inner += _plate(it, COL_L if left else COL_R - PLATE_W, t0, wins,
                        t0 + T_PLATE + (0 if left else .1))

    # The reveal: crown, halo, MORE sticker, confetti, gap badge.
    inner += _crown(win_cx, max(CROWN_MIN_TOP, win_top - 80), land, -6 if left_wins else 6)
    inner += sticker("MORE", win_cx - 118, 948, 76, t0 + T_MORE, ACCENT, INK, -8 if left_wins else 7)
    inner += burst(win_cx, 760, land, ctx.seed + k * 23)
    inner += _gap_badge(_gap(a, b), left_wins, t0 + T_GAP)
    inner += "</div>"
    inner += (f'<div class="full" style="background:#fff;opacity:0;pointer-events:none;'
              f'{style_anim(an("cmFlash", land, .45, "ease-out"))}"></div>')
    inner += progress(t0, t0 + R, k, n)
    comp.scene(t0, t0 + R + XF, inner, fade_in=.25, fade_out=.05)

    comp.cue(t0 + T_A, "whoosh")
    comp.cue(t0 + T_B, "whoosh")
    comp.cue(t0 + T_HEAD, "slam")
    comp.cue(t0 + T_VS, "slam")
    comp.cue(t0 + T_PLATE, "pop")
    for s in range(CD):
        comp.cue(t0 + T_CD + s, "tick")
    comp.cue(t0 + T_ROLL, "reveal")
    comp.cue(land, "cash")
    comp.cue(t0 + T_MORE, "slam")
    comp.cue(t0 + T_GAP, "pop")


def _key_half(ctx: Ctx, it: dict, x: float, w: float, h: float, winner: bool, start: float) -> str:
    """One side of a score-check row: thumbnail on the tile colours, name, price.
    The pricier side is outlined in the accent and tagged MORE."""
    col = RARITY.get(it.get("rarity", ""), "#777")
    tc = it.get("tile_colors") or []
    c1 = hexcol(tc[0] if tc else "", col)
    c2 = hexcol(tc[1] if len(tc) > 1 else "", "#101014")
    uri = ctx.art(it)
    img = (f'<img src="{uri}" style="width:100%;height:100%;object-fit:contain;display:block">'
           if uri else "")
    th = h - 24
    tx = 12 + th + 14
    tw = w - tx - 14
    lines, nsize = _fit_lines(it["name"], tw, 30, 21, 22)
    nsize = min(nsize, 30)
    names = "".join(
        f'<div class="d" style="font-size:{nsize:.0f}px;line-height:1;white-space:nowrap">{esc(ln)}</div>'
        for ln in lines)
    price_col = ACCENT if winner else "rgba(255,255,255,.62)"
    frame = (f"border:4px solid {ACCENT};background:rgba(38,42,10,.82);"
             f"box-shadow:0 0 36px rgba(232,255,58,.28)" if winner
             else "border:4px solid rgba(255,255,255,.08);background:rgba(10,10,11,.74)")
    tag = ""
    if winner:
        tag = (f'<div class="abs" style="right:-8px;top:-18px;transform:rotate(6deg)">'
               f'<div class="d" style="background:{ACCENT};color:{INK};font-size:26px;padding:.16em .42em .1em;'
               f'border-radius:8px;box-shadow:0 6px 0 rgba(0,0,0,.35);'
               f'{style_anim(an("pop", start + .35, .5, EASE_BACK))}">MORE</div></div>')
    return (f'<div class="abs" style="left:{x:.0f}px;top:0;width:{w:.0f}px;height:{h:.0f}px">'
            f'<div class="full" style="border-radius:20px;{frame}"></div>'
            f'<div class="abs" style="left:12px;top:12px;width:{th:.0f}px;height:{th:.0f}px;border-radius:14px;'
            f'overflow:hidden;background:radial-gradient(circle at 50% 38%,{c1},{c2})">{img}</div>'
            f'<div class="abs" style="left:{tx:.0f}px;top:14px;width:{tw:.0f}px;color:#fff">{names}</div>'
            f'<div class="abs d" style="left:{tx:.0f}px;bottom:14px;font-size:48px;line-height:1;'
            f'color:{price_col};white-space:nowrap">{int(it["price"]):,}'
            f'<span style="font-family:Inter,sans-serif;font-size:14px;font-weight:800;letter-spacing:.2em;'
            f'color:rgba(255,255,255,.62);margin-left:10px">V-BUCKS</span></div>'
            f'{tag}</div>')


def _score_check(comp: Comp, ctx: Ctx, pairs: list, t0: float):
    inner = tile_bg(["#262a36", "#0b0b0e"], "", t0)
    inner += words("SCORE CHECK", 60, 330, 124, t0 + .1, "#fff", .1, "slam", "left", 900)
    inner += sticker("+1 FOR EVERY RIGHT ANSWER", 64, 458, 34, t0 + .45, ACCENT, INK, -3)
    x0, w, h, step, y0 = 60, 880, 128, 158, 556
    num_w = 58
    half = (w - num_w - 14) / 2
    for i, (a, b) in enumerate(pairs):
        y = y0 + i * step
        start = t0 + .55 + i * .15
        left_wins = a["price"] > b["price"]
        row = (f'<div class="abs d" style="left:0;top:{h / 2 - 25:.0f}px;width:50px;height:50px;border-radius:50%;'
               f'background:{ACCENT};color:{INK};font-size:30px;line-height:50px;text-align:center">{i + 1}</div>')
        row += _key_half(ctx, a, num_w, half, h, left_wins, start)
        row += _key_half(ctx, b, num_w + half + 14, half, h, not left_wins, start)
        inner += (f'<div class="abs" style="left:{x0}px;top:{y:.0f}px;width:{w}px;height:{h}px">'
                  f'<div class="full" style="{style_anim(an("fromL", start, .55))}">{row}</div></div>')
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

    content_end = HOOK + n * R + KEY
    comp = Comp(content_end + _pad(content_end))
    comp.css(CSS)

    _hook_scene(comp, ctx, "WHICH COSTS MORE?", "LOCK IN YOUR ANSWER", f"{n} ROUNDS",
                HOOK + .5, pairs[0][0], pairs[0][1])
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.3, "whoosh"); comp.cue(.9, "pop")

    for k, pair in enumerate(pairs, 1):
        _round(comp, ctx, pair, k, n, HOOK + (k - 1) * R)

    _score_check(comp, ctx, pairs, HOOK + n * R)

    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    winners = [max(p, key=lambda it: it["price"]) for p in pairs]
    losers = [min(p, key=lambda it: it["price"]) for p in pairs]
    _outro_scene(comp, ctx, content_end, comp.duration, "HOW MANY DID YOU GET RIGHT?",
                 winners + losers)
    comp.add(code_badge(.4))
    comp.add(disclosure())

    rounds = "\n".join(f"Round {k}: {a['name']} vs {b['name']} ({a['type']}"
                       + ("" if a["type"] == b["type"] else f" vs {b['type']}") + ")"
                       for k, (a, b) in enumerate(pairs, 1))
    body = (f"{rounds}\n\nLock in your answer before each reveal. "
            f"Prices are today's item shop prices, in V-Bucks.")
    tags = _hashtags("whichcostsmore", *(it["name"] for it in pairs[0]))
    return Video(
        FORMAT, comp,
        title=f"Which Costs More? Fortnite shop {ctx.day_label}",
        yt_title=f"Which Costs More? Fortnite Item Shop Quiz {ctx.day_label} #shorts",
        caption=_caption(f"WHICH COSTS MORE? 🤔 {n} rounds from today's Fortnite item shop ({ctx.day_label})",
                         body, f"How many did you get right out of {n}? Comment your score 👇", tags),
        hashtags=tags)
