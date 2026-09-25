"""
COP OR DROP -- slot 2 (interactive) for @usecodebad.

Seven single items from today's shop, one at a time, and the viewer votes on each
in the comments. Every round: the cosmetic lands big and central on its own Epic
tile colours, the name slams in, a V-Bucks coin rolls up to the real price, and two
chunky arcade buttons -- COP and DROP -- pop in and wobble while a ring between
them drains. When it runs out we never press either button: we don't know how
people vote, so there is no verdict, just "COMMENT IT!". A ballot recaps all seven
so people can vote in order, and the outro asks "COMMENT COP OR DROP FOR EACH".

Truth rules this format keeps (every claim is a row field):
  - the price is the row's `price` (single items are never discounted, so there is
    no "regular price" talk here at all)
  - the kicker is the row's `type`, plus its series label when it has one
    ("ICON SERIES"); plain tiers are not shown, so the word "RARE" never appears
  - the INTRODUCED card is the row's `introduction` chapter/season
  - "LEAVES AT THE NEXT RESET" only when `out_day` is today's shop day, otherwise
    "IN THE SHOP SINCE <in_day>"
No "most people", no rating, no "back"/"returning"/"first time"/"rare".
"""

import math
from datetime import date

from cc_motion import (ACCENT, INK, RARITY, EASE_BACK, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP,
                       W, Comp, an, burst, character, code_badge, countdown, disclosure, esc, hexcol,
                       price_roll, progress, sticker, style_anim, tile_bg, words)
from cc_formats import (MIN_SECONDS, Ctx, Video, num, _caption, _hashtags, _hook_scene, _outro_scene,
                        _pad, rng, singles)

FORMAT = "cop_or_drop"
ROUNDS = 7
MIN_SINGLES = 5
OUTFITS = 3                      # full characters read best on screen; the rest mixed types

HOOK, R, BALLOT = 3.0, 7.8, 4.2  # hook, one item, ballot recap (seconds)
OUTRO_MIN = 7.5                  # _pad()'s shortest outro

# Beats inside a round, in seconds from the round's start.
T_CHAR = .1                      # cosmetic enters
T_KICK = .3                      # type chip
T_NAME = .4                      # name slams
T_COIN = .8                      # V-Bucks coin pops in
T_ROLL, ROLL = 1.0, .85          # price counts up
T_LAND = T_ROLL + ROLL           # exact price lands: jolt, confetti
T_CARD = 1.35                    # INTRODUCED card
T_TAG = 2.0                      # leaves / in-shop-since tag
T_BTN = 2.25                     # COP pops (DROP .12 later)
T_OR = 2.6                       # "OR" disc between the buttons
T_CD, CD = 3.0, 4                # the voting ring takes over the OR disc
T_END = T_CD + CD                # ring done: no verdict, just "COMMENT IT!"
WIPE, WIPE_W = .56, 2400         # the colour wipe between scenes, centred on each cut

# Layout (px). Everything a viewer reads stays in the apps' safe box (cc_safe):
# x 60-1020 above y 740, x 60-900 (left of the button rail) below it, y 230-1420.
# The code badge and #EpicPartner own the top-left corner down to y ~350, the
# round counter the top-right down to y ~292.
#
#   y 366-650   type chip + name (left column)   | V-Bucks coin + leaves/since sticker
#   y 560-1176  INTRODUCED card (left) and the cosmetic, centred on the band
#   y 1196-1336 COP [ring] DROP, centred on the band beside the rail
#   y 1344-1400 COMMENT IT! once the ring runs out
KICK_Y = 366                     # under #EpicPartner
NAME_X, NAME_Y = SAFE_LEFT, 424
COIN_D = 226
COIN_CX, COIN_CY = SAFE_RIGHT_TOP - 8 - COIN_D / 2, 452      # top right: x 786-1012, y 339-565
NAME_W = COIN_CX - COIN_D / 2 - 26 - NAME_X                  # the name column stops short of the coin
TAG_XR = SAFE_RIGHT_TOP - 10     # right edge of the leaves/since sticker, under the coin
TAG_SIZE = 32
CARD_X, CARD_W, CARD_TOP = SAFE_LEFT, 240, 640
CHAR_CX, CHAR_BOTTOM, CHAR_MAXW = 520, 1176, 660
BTN_Y, BTN_H, BTN_W, BTN_FS = 1196, 120, 292, 86
COP_X, DROP_X = SAFE_LEFT + 10, SAFE_RIGHT - 10 - BTN_W       # 70-362 and 598-890
RING_CX, RING_CY, RING_D = (COP_X + DROP_X + BTN_W) / 2, BTN_Y + BTN_H / 2, 150
CTA_Y, CTA_SIZE = BTN_Y + BTN_H + 28, 44
COP_COL, COP_LIGHT, COP_EDGE = "#3BD16F", "#7CF0A3", "#1C8A43"
DROP_COL, DROP_LIGHT, DROP_EDGE = "#FF4D4D", "#FF8A8A", "#B52323"

# Inter 800 advance widths in em (caps, digits, punctuation), measured in the
# render browser, for sizing the type chip to its column.
_INTER800 = {
    'A': .75, 'B': .647, 'C': .728, 'D': .706, 'E': .619, 'F': .593, 'G': .738, 'H': .722, 'I': .27,
    'J': .573, 'K': .706, 'L': .565, 'M': .909, 'N': .731, 'O': .747, 'P': .639, 'Q': .747, 'R': .658,
    'S': .668, 'T': .645, 'U': .705, 'V': .742, 'W': 1.033, 'X': .718, 'Y': .709, 'Z': .643, ' ': .2,
    '·': .254, ',': .254, '.': .254, '-': .45, "'": .25, '0': .665, '1': .665, '2': .665, '3': .665,
    '4': .665, '5': .665, '6': .665, '7': .665, '8': .665, '9': .665,
}

ENTER = ["pop", "drop", "fromR", "pop", "fromL", "drop", "pop"]

# Tier order for "prefer higher rarity". Series sit with Legendary.
RANK = {"mythic": 6, "legendary": 5, "icon": 5, "gaminglegends": 5, "marvel": 5, "dc": 5,
        "starwars": 5, "epic": 4, "rare": 3, "uncommon": 2, "common": 1}
# After the outfits, one of each of these types in this order of preference.
TYPE_PREF = ["Pickaxe", "Glider", "Emote", "Sidekick", "Back Bling", "Shoes", "Wrap",
             "Contrail", "Kicks", "Loading Screen", "Spray"]

# Anton advance widths in em, measured in the render browser. Used to size names
# so they never wrap awkwardly or run off the frame.
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
/* burst() pieces are opaque at 0%, so with fill "both" they sat stacked at the
   origin until they flew. Same motion, invisible until launch. This document only. */
@keyframes burst{{0%{{transform:translate(0,0) rotate(0) scale(1);opacity:0}}3%{{opacity:1}}
  100%{{transform:translate(var(--dx),var(--dy)) rotate(var(--r)) scale(.35);opacity:0}}}}
@keyframes cdWob{{0%{{transform:rotate(-2.6deg) translateY(0)}}100%{{transform:rotate(2.6deg) translateY(-8px)}}}}
@keyframes cdNudge{{0%,100%{{transform:scale(1)}}35%{{transform:scale(1.09)}}70%{{transform:scale(.97)}}}}
@keyframes cdShine{{0%{{transform:translateX(-200%) skewX(-20deg)}}100%{{transform:translateX(480%) skewX(-20deg)}}}}
@keyframes cdOut{{0%{{transform:scale(1);opacity:1}}100%{{transform:scale(.3) rotate(-25deg);opacity:0}}}}
@keyframes cdWipe{{0%{{transform:translateX(-2700px) skewX(-14deg)}}100%{{transform:translateX(1360px) skewX(-14deg)}}}}
@keyframes cdCoin{{0%,100%{{transform:rotate(7deg) translateY(0)}}50%{{transform:rotate(3deg) translateY(-12px)}}}}
@keyframes cdJolt{{0%,100%{{transform:none}}20%{{transform:translate(-9px,5px) rotate(-4deg) scale(1.08)}}
  45%{{transform:translate(8px,-6px) rotate(3deg)}}70%{{transform:translate(-4px,3px) rotate(-1deg)}}}}
/* The shared hook's title keeps a word-gap after its last word, which nudges
   "COP OR DROP?" off centre. Scoped to this video's hook scene only. */
body>.scene:first-child .abs.d[style*="font-size:170px"]>span:last-child{{margin-right:0!important}}
"""


# ------------------------------------------------------------------ helpers

def _em(text: str) -> float:
    """Width of `text` in em as words() sets it: Anton caps, .01em tracking,
    .18em after every word."""
    ws = text.upper().split()
    return sum(_ANTON.get(ch, .52) + .01 for w in ws for ch in w) + .18 * len(ws)


def _fit(text: str, width: float, cap: float) -> float:
    return min(cap, width / max(_em(text), .1))


def _row_lines(name: str, width: float, h: float, cap: float = 52, min1: float = 40) -> tuple:
    """(lines, size) for a name in a recap row: one line down to `min1` px, else
    the two-line break that allows the biggest type (as tall as the row allows)."""
    one = _fit(name, width, cap)
    ws = name.split()
    if one >= min1 or len(ws) < 2:
        return [name], one
    cap2 = min(min1, (h - 30 * 1.1 - 26) / 1.8)
    best = max((min(cap2, width / max(_em(" ".join(ws[:i])), _em(" ".join(ws[i:])))), i)
               for i in range(1, len(ws)))
    return [" ".join(ws[:best[1]]), " ".join(ws[best[1]:])], best[0]


def _inter_w(text: str, size: float, spacing: float = 0) -> float:
    """Width in px of `text` in Inter 800 caps with `spacing` em of letter-spacing."""
    s = text.upper()
    return sum(_INTER800.get(ch, .7) + spacing for ch in s) * size


def _name_lines(name: str, width: float = NAME_W) -> tuple:
    """(lines, font size). One line when it can be set at 84px or more, else the
    two-line break that allows the biggest type (keeping a quoted colourway
    together when that costs little)."""
    one = _fit(name, width, 118)
    ws = name.split()
    if one >= 84 or len(ws) < 2:
        return [name], one
    splits = []
    for i in range(1, len(ws)):
        a, b = " ".join(ws[:i]), " ".join(ws[i:])
        splits.append((min(98, width / max(_em(a), _em(b))), ws[i][:1] in "'\"(", [a, b]))
    top = max(s[0] for s in splits)
    size, _, lines = max((s for s in splits if s[0] >= top * .92), key=lambda s: (s[1], s[0]))
    return lines, size


def _rank(it: dict) -> int:
    if it.get("rarity") in RANK:
        return RANK[it["rarity"]]
    return 5 if (it.get("rarity_label") or "").lower().endswith("series") else 2


def _pick(ctx: Ctx) -> list:
    """Up to seven singles: up to three outfits, then one each of the other types,
    highest rarity first, a different shop section where the shop allows.
    Deterministic for the day. Play order opens on an outfit and interleaves."""
    seen, pool = set(), []
    for it in singles(ctx):
        if it["name"] not in seen and it.get("price"):
            seen.add(it["name"])
            pool.append(it)
    if len(pool) < MIN_SINGLES:
        return []
    r = rng(ctx, 4)
    r.shuffle(pool)
    pool.sort(key=lambda it: -_rank(it))          # stable: shuffled within a tier
    n = min(ROUNDS, len(pool))

    picked, sections = [], set()

    def best(cands):
        names = {p["name"] for p in picked}
        cands = [c for c in cands if c["name"] not in names]
        if not cands:
            return None
        # Highest tier; among equals, a set we haven't shown yet.
        return min(cands, key=lambda c: (-_rank(c), bool(c.get("section")) and c.get("section") in sections))

    def take(c):
        if c is not None and len(picked) < n:
            picked.append(c)
            sections.add(c.get("section") or "")

    outfits = [c for c in pool if c["type"] == "Outfit"]
    for _ in range(min(OUTFITS, len(outfits))):
        take(best(outfits))

    by_type = {}
    for c in pool:
        if c["type"] != "Outfit":
            by_type.setdefault(c["type"], []).append(c)
    pref = {t: i for i, t in enumerate(TYPE_PREF)}
    order = sorted(by_type, key=lambda t: (-max(_rank(c) for c in by_type[t]),
                                           pref.get(t, len(pref)), t))
    for t in order:
        take(best(by_type[t]))
    while len(picked) < n:                          # few types today: top up
        take(best(pool))

    outs = [p for p in picked if p["type"] == "Outfit"]
    rest = [p for p in picked if p["type"] != "Outfit"]
    r.shuffle(outs)
    r.shuffle(rest)
    played = []
    while outs or rest:
        if outs and (not played or played[-1]["type"] != "Outfit" or not rest):
            played.append(outs.pop(0))
        else:
            played.append(rest.pop(0))
    return played


def _scrim() -> str:
    """Darkens the bands the words sit on, so white type and the lime code badge
    hold on pale tile colours (some are acid yellow-green themselves)."""
    return ('<div class="full" style="background:linear-gradient(180deg,rgba(0,0,0,.5) 0,'
            'rgba(0,0,0,.36) 20%,rgba(0,0,0,.2) 30%,rgba(0,0,0,0) 42%,rgba(0,0,0,0) 58%,'
            'rgba(0,0,0,.3) 70%,rgba(0,0,0,.55) 100%)"></div>')


def _leaves_today(ctx: Ctx, it: dict) -> bool:
    try:
        return date.fromisoformat(it.get("out_day") or "") == ctx.day
    except ValueError:
        return False


def _in_since(ctx: Ctx, it: dict) -> str:
    try:
        d = date.fromisoformat(it.get("in_day") or "")
    except ValueError:
        return ""
    if d == ctx.day:
        return "ADDED TO THE SHOP TODAY"
    return f"IN THE SHOP SINCE {d.strftime('%b %-d').upper()}"


def _intro(it: dict) -> tuple:
    intro = it.get("introduction") or {}
    return str(intro.get("chapter") or "").strip(), str(intro.get("season") or "").strip()


# --------------------------------------------------------------- components

def _kicker(it: dict, x: float, y: float, start: float, width: float = NAME_W) -> str:
    """TYPE chip with a rarity-coloured dot. A series label ("ICON SERIES") is
    added when the chip still fits its column ("GAMING LEGENDS" without the word
    SERIES if that's what fits); plain tiers are not, so "RARE" never reads as a
    scarcity claim."""
    col = RARITY.get(it.get("rarity", ""), "#9AA0A6")
    kind = (it.get("type") or "").upper()
    series = (it.get("rarity_label") or "").strip()
    size, sp = 30, .1
    room = width - 16 - 12 - 32 - 8                # dot, gap, padding, the tilt
    rest = ""
    if series.lower().endswith("series"):
        for s in (series.upper(), series.upper()[:-len(" SERIES")].strip()):
            if s and _inter_w(f"{kind} · {s}", size, sp) <= room:
                rest = s
                break
    extra = (f'<span style="color:rgba(255,255,255,.74)">·&nbsp;{esc(rest)}</span>' if rest else "")
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;transform:rotate(-1.5deg)">'
            f'<div style="display:inline-flex;align-items:center;gap:12px;background:rgba(10,10,11,.84);'
            f'border-radius:12px;padding:6px 16px 6px 14px;font-size:{size}px;font-weight:800;line-height:1.2;'
            f'letter-spacing:{sp}em;white-space:nowrap;{style_anim(an("rise", start, .45))}">'
            f'<i style="width:16px;height:16px;border-radius:50%;background:{col};'
            f'box-shadow:0 0 14px {col}"></i><span>{esc(kind)}</span>{extra}</div></div>')


def _coin(price: int, cx: float, cy: float, t0: float) -> str:
    """A V-Bucks coin: pops in empty, the price counts up from 0 inside it, lands
    with a jolt, then the coin keeps a slow tilt-and-bob so it never sits dead."""
    d = COIN_D
    size = _fit(f"{price:,}", d * .72, 92)
    unit_size = 30
    block = size * .9 + 6 + unit_size * .9          # the number, a gap, V-BUCKS
    num_top = d / 2 - block / 2 - 4
    t_in, t_roll, t_land = t0 + T_COIN, t0 + T_ROLL, t0 + T_LAND
    face = (f'<div class="full" style="border-radius:50%;'
            f'background:radial-gradient(circle at 34% 28%,#34353f 0%,#121216 55%,#0a0a0b 100%);'
            f'border:8px solid {ACCENT};box-shadow:0 14px 0 rgba(0,0,0,.38),0 0 70px rgba(232,255,58,.28),'
            f'inset 0 0 0 7px #0a0a0b,inset 0 0 0 10px rgba(232,255,58,.38)"></div>')
    # price_roll's counter shows "0" before it starts; it only appears on cue.
    roll = (f'<div class="full" style="{style_anim(an("fadein", t_roll, .06))}">'
            f'{price_roll(price, d / 2, num_top, size, t_roll, ROLL, ACCENT, "center", "")}</div>')
    unit = (f'<div class="abs d" style="left:0;right:0;top:{num_top + size * .9 + 6:.0f}px;text-align:center;'
            f'font-size:{unit_size}px;letter-spacing:.14em;text-indent:.14em;'
            f'color:rgba(255,255,255,.82)">V-BUCKS</div>')
    return (f'<div class="abs" style="left:{cx - d / 2:.0f}px;top:{cy - d / 2:.0f}px;width:{d}px;height:{d}px">'
            f'<div class="full" style="{style_anim(an("pop", t_in, .6, EASE_BACK))}">'
            f'<div class="full" style="{style_anim(an("cdCoin", t_in + .6, 2.8, "ease-in-out", "infinite"))}">'
            f'<div class="full" style="{style_anim(an("cdJolt", t_land, .4, "linear"))}">'
            f'{face}{roll}{unit}</div></div></div></div>')


def _intro_card(it: dict, x: float, top: float, start: float) -> str:
    """'INTRODUCED / CHAPTER 2 / SEASON 1' from the row's own introduction field."""
    ch, se = _intro(it)
    if not ch or not se:
        return ""
    col = RARITY.get(it.get("rarity", ""), "#9AA0A6")
    lines = [f"CHAPTER {ch}", f"SEASON {se}"]
    size = min(52, (CARD_W - 44) / max(_em(s) for s in lines))
    a = style_anim(an("pop", start, .55, EASE_BACK))
    # Tilted 4 degrees into the frame, so its corners stay inside the safe box.
    return (f'<div class="abs" style="left:{x + 8:.0f}px;top:{top:.0f}px;width:{CARD_W - 16}px;'
            f'transform:rotate(-4deg)"><div style="background:rgba(10,10,11,.88);border:3px solid {col};'
            f'border-radius:18px;padding:12px 8px 14px;text-align:center;'
            f'box-shadow:0 10px 0 rgba(0,0,0,.35);{a}">'
            f'<div class="d" style="font-size:30px;letter-spacing:.1em;text-indent:.1em;'
            f'color:#B4B9C2;margin-bottom:8px">INTRODUCED</div>'
            f'<div class="d" style="font-size:{size:.0f}px;line-height:1">{esc(lines[0])}</div>'
            f'<div class="d" style="font-size:{size:.0f}px;line-height:1;color:{ACCENT}">{esc(lines[1])}</div>'
            f'</div></div>')


def _two_lines(text: str) -> list:
    """Break a sticker's words into the two most even lines."""
    ws = text.split()
    if len(ws) < 3:
        return [text]
    best = min(range(1, len(ws)), key=lambda i: abs(_em(" ".join(ws[:i])) - _em(" ".join(ws[i:]))))
    return [" ".join(ws[:best]), " ".join(ws[best:])]


def _tag(text: str, xr: float, y: float, size: float, start: float, bg: str, fg: str,
         rot: float) -> str:
    """A crooked sticker on two lines, anchored by its right edge (under the coin)."""
    a = style_anim(an("pop", start, .55, EASE_BACK))
    body = "<br>".join(esc(s) for s in _two_lines(text))
    return (f'<div class="abs" style="right:{W - xr:.0f}px;top:{y:.0f}px;transform:rotate({rot}deg)">'
            f'<div class="d" style="background:{bg};color:{fg};font-size:{size:.0f}px;line-height:.98;'
            f'padding:.18em .42em .1em;border-radius:10px;white-space:nowrap;text-align:center;'
            f'box-shadow:0 8px 0 rgba(0,0,0,.35);{a}">{body}</div></div>')


def _icon(kind: str, col: str, d: int = 60) -> str:
    """A check (COP) or a cross (DROP), drawn in CSS: fonts may lack the glyphs."""
    if kind == "check":
        mark = (f'<i style="position:absolute;left:{d * .36:.0f}px;top:{d * .17:.0f}px;width:{d * .27:.0f}px;'
                f'height:{d * .5:.0f}px;border-right:{d * .14:.0f}px solid {col};'
                f'border-bottom:{d * .14:.0f}px solid {col};border-radius:2px;transform:rotate(45deg)"></i>')
    else:
        bar = (f'position:absolute;left:50%;top:50%;width:{d * .14:.0f}px;height:{d * .58:.0f}px;'
               f'margin:-{d * .29:.0f}px 0 0 -{d * .07:.0f}px;background:{col};border-radius:3px;')
        mark = (f'<i style="{bar}transform:rotate(45deg)"></i>'
                f'<i style="{bar}transform:rotate(-45deg)"></i>')
    return (f'<i style="position:relative;display:block;flex:none;width:{d}px;height:{d}px;border-radius:50%;'
            f'background:#fff;box-shadow:0 5px 0 rgba(0,0,0,.18)">{mark}</i>')


def _button(text: str, x: float, rot: float, col: str, light: str, edge: str, icon: str,
            start: float, t_nudge: float, reverse: bool) -> str:
    """A chunky arcade key: lit top face, a hard bottom edge, a shine that sweeps
    across when it lands. It pops in, then wobbles on its own beat for as long as
    the vote is open, and gets a nudge when the ring runs out. Never pressed."""
    wob = an("cdWob", start + .55, .95, "ease-in-out", "infinite",
             "alternate-reverse" if reverse else "alternate")
    face = (f'<div class="full" style="border-radius:30px;overflow:hidden;'
            f'background:linear-gradient(180deg,{light} 0%,{col} 46%,{col} 100%);'
            f'box-shadow:0 14px 0 {edge},0 28px 36px rgba(0,0,0,.45),inset 0 4px 0 rgba(255,255,255,.45),'
            f'inset 0 -8px 0 rgba(0,0,0,.14);display:flex;align-items:center;justify-content:center;gap:16px">'
            f'{_icon(icon, col, 52)}'
            f'<span class="d" style="font-size:{BTN_FS}px;line-height:1;padding-top:.08em;color:#fff;'
            f'text-shadow:0 6px 0 {edge}">{esc(text)}</span>'
            f'<div class="abs" style="top:-30%;bottom:-30%;left:0;width:26%;'
            f'background:linear-gradient(90deg,transparent,rgba(255,255,255,.55),transparent);'
            f'{style_anim(an("cdShine", start + .5, .8, "cubic-bezier(.3,0,.2,1)"))}"></div></div>')
    return (f'<div class="abs" style="left:{x:.0f}px;top:{BTN_Y}px;width:{BTN_W}px;height:{BTN_H}px;'
            f'transform:rotate({rot}deg)">'
            f'<div class="full" style="{style_anim(an("pop", start, .55, EASE_BACK))}">'
            f'<div class="full" style="transform-origin:50% 100%;{style_anim(wob)}">'
            f'<div class="full" style="{style_anim(an("cdNudge", t_nudge, .45, "ease-out"))}">'
            f'{face}</div></div></div></div>')


def _or_disc(cx: float, cy: float, start: float, out: float = 0) -> str:
    d = 106
    origin = f"transform-origin:{cx:.0f}px {cy:.0f}px;"
    gone = style_anim(an("cdOut", out, .2)) if out else ""
    return (f'<div class="full" style="{origin}{gone}">'
            f'<div class="abs d" style="left:{cx - d / 2:.0f}px;top:{cy - d / 2:.0f}px;width:{d}px;'
            f'height:{d}px;border-radius:50%;background:{INK};border:6px solid #fff;display:flex;'
            f'align-items:center;justify-content:center;font-size:50px;padding-top:4px;color:#fff;'
            f'box-shadow:0 10px 0 rgba(0,0,0,.35);transform-origin:50% 50%;'
            f'{style_anim(an("pop", start, .5, EASE_BACK))}">OR</div></div>')


def _vote_center(t0: float, cd: int = CD) -> str:
    """Between the buttons: an OR disc, then the voting ring pops over it and
    drains. When it runs out the ring shrinks away, the OR disc comes back and a
    COMMENT IT! sticker lands under the buttons. Neither button is ever chosen."""
    cx, cy, d = RING_CX, RING_CY, RING_D
    t_end = T_CD + cd
    origin = f"transform-origin:{cx:.0f}px {cy:.0f}px;"
    ring = (f'<div class="full" style="{origin}{style_anim(an("cdOut", t0 + t_end, .28, "cubic-bezier(.5,0,.8,.3)"))}">'
            f'<div class="full" style="{origin}{style_anim(an("pop", t0 + T_CD, .5, EASE_BACK))}">'
            f'<div class="abs" style="left:{cx - d / 2 - 8:.0f}px;top:{cy - d / 2 - 8:.0f}px;width:{d + 16}px;'
            f'height:{d + 16}px;border-radius:50%;background:{INK};box-shadow:0 12px 0 rgba(0,0,0,.35)"></div>'
            f'{countdown(cd, cx, cy, d, t0 + T_CD)}</div></div>')
    # COMMENT IT! lands under the buttons, centred on the ring, above the caption zone.
    cta_w = (_em("COMMENT IT!") + .84) * CTA_SIZE
    cta = (f'<div class="abs" style="left:{cx - cta_w / 2:.0f}px;top:{CTA_Y}px;'
           f'transform:rotate(-3deg)"><div class="d" style="background:#fff;color:{INK};font-size:{CTA_SIZE}px;'
           f'padding:.16em .42em .1em;border-radius:10px;white-space:nowrap;'
           f'box-shadow:0 8px 0 rgba(0,0,0,.35);{style_anim(an("pop", t0 + t_end + .12, .55, EASE_BACK))}">'
           f'COMMENT IT!</div></div>')
    # Clean hand-offs: the OR disc is gone before the ring pops (its pop starts
    # transparent, so an overlap reads as "4" printed over "OR"), and it only
    # comes back once the ring has shrunk away.
    return (_or_disc(cx, cy, t0 + T_OR, t0 + T_CD - .18) + ring
            + _or_disc(cx, cy, t0 + t_end + .3) + cta)


def _round(comp: Comp, ctx: Ctx, it: dict, k: int, n: int, t0: float, rlen: float = R):
    # A shorter run (5-6 items) gets longer rounds rather than a padded outro;
    # each whole extra second goes to the vote.
    cd = min(6, CD + int(rlen - R))
    t_end = T_CD + cd
    art = ctx.art(it)
    lines, size = _name_lines(it["name"])
    name_bottom = NAME_Y + len(lines) * size * .92
    land = t0 + T_LAND

    # Under the coin: when it leaves, or how long it's been in the shop.
    leaves = _leaves_today(ctx, it)
    tag_text = "LEAVES AT THE NEXT RESET" if leaves else _in_since(ctx, it)
    tag_y = COIN_CY + COIN_D / 2 + 20

    # The cosmetic fills the band between the header and the buttons, centred a
    # little right of the band so the INTRODUCED card has the left edge.
    top = name_bottom + 16
    outfit = it["type"] == "Outfit"
    h = min(760 if outfit else 560, CHAR_BOTTOM - top)
    cy = CHAR_BOTTOM - h / 2 if outfit else (top + CHAR_BOTTOM) / 2 + 10

    inner = tile_bg(it.get("tile_colors") or [], it["rarity"], t0) + _scrim()
    inner += character(art, CHAR_CX, cy, h, t0 + T_CHAR, ENTER[(k - 1) % len(ENTER)], .75,
                       "float" if k % 2 else "sway", it["rarity"], it["name"], maxw=CHAR_MAXW, trim=True)
    inner += _kicker(it, NAME_X, KICK_Y, t0 + T_KICK)
    for i, line in enumerate(lines):
        inner += words(line, NAME_X, NAME_Y + i * size * .92, size, t0 + T_NAME + i * .12,
                       "#fff", .07, "slam", "left", NAME_W + 40)

    inner += _intro_card(it, CARD_X, max(CARD_TOP, name_bottom + 40), t0 + T_CARD)
    inner += _coin(it["price"], COIN_CX, COIN_CY, t0)
    inner += burst(COIN_CX, COIN_CY, land, ctx.seed + k * 23, 22)
    if tag_text:
        bg, fg = (ACCENT, INK) if leaves else ("rgba(10,10,11,.88)", "#fff")
        inner += _tag(tag_text, TAG_XR, tag_y, TAG_SIZE, t0 + T_TAG, bg, fg, -3)

    inner += _button("COP", COP_X, -3, COP_COL, COP_LIGHT, COP_EDGE, "check",
                     t0 + T_BTN, t0 + t_end, False)
    inner += _button("DROP", DROP_X, 3, DROP_COL, DROP_LIGHT, DROP_EDGE, "cross",
                     t0 + T_BTN + .12, t0 + t_end + .06, True)
    inner += _vote_center(t0, cd)
    inner += progress(t0, t0 + rlen, k, n)
    comp.scene(t0, t0 + rlen + .05, inner, fade_in=.05, fade_out=.05)

    # The wipe's whoosh (just before t0) carries the cosmetic's entrance.
    comp.cue(t0 + T_NAME, "slam")
    comp.cue(t0 + T_ROLL, "reveal")
    comp.cue(land, "cash")
    comp.cue(t0 + T_CARD, "pop")
    comp.cue(t0 + T_BTN, "pop")
    comp.cue(t0 + T_BTN + .12, "pop")
    for s in range(cd):
        comp.cue(t0 + T_CD + s, "tick")
    comp.cue(t0 + t_end + .12, "pop")


def _wipe(comp: Comp, t: float, colors: list, rarity: str = ""):
    """A slanted panel in the NEXT item's own tile colours, with a brand-yellow
    leading edge, whips across the frame. It covers the whole frame for a couple
    of frames around `t`, which is exactly where the scenes hard-cut underneath:
    a proper wipe rather than a crossfade. The code badge stays on top."""
    base = RARITY.get(rarity, "#3a3a44")
    c1 = hexcol(colors[0] if colors else "", base)
    c2 = hexcol(colors[1] if len(colors) > 1 else "", "#101014")
    a = style_anim(an("cdWipe", t - WIPE / 2, WIPE, "cubic-bezier(.45,0,.55,1)"))
    comp.add(f'<div class="abs" style="left:0;top:-240px;width:{WIPE_W}px;height:2400px;z-index:30;{a}">'
             f'<div class="full" style="background:linear-gradient(90deg,{c2} 0%,{c1} 70%)"></div>'
             f'<div class="full" style="overflow:hidden"><div class="grain" style="opacity:.12"></div></div>'
             f'<div class="abs" style="top:0;bottom:0;right:0;width:70px;background:{ACCENT}"></div>'
             f'<div class="abs" style="top:0;bottom:0;right:100px;width:18px;background:{ACCENT};opacity:.8"></div>'
             f'</div>')
    comp.cue(t - WIPE / 2 + .05, "whoosh")


BAL_X, BAL_W = SAFE_LEFT, SAFE_RIGHT - SAFE_LEFT          # 60-900: beside the rail
BAL_TOP, BAL_BOTTOM = 572, SAFE_BOTTOM - 12
BOX, BOX_GAP, BOX_R = 58, 16, 18                          # the two tick boxes, from the row's right


def _box_x(j: int) -> float:
    """Left edge (in the row) of tick box j: 0 = COP, 1 = DROP."""
    return BAL_W - BOX_R - BOX - (1 - j) * (BOX + BOX_GAP)


def _ballot_row(ctx: Ctx, it: dict, k: int, y: float, h: float, start: float) -> str:
    """One ballot line: numbered cosmetic on its tile colours, name, type and
    price, and two empty tick boxes under the COP and DROP column heads -- the
    vote is the viewer's to fill in."""
    col = RARITY.get(it.get("rarity", ""), "#777")
    tc = it.get("tile_colors") or []
    c1 = hexcol(tc[0] if tc else "", col)
    c2 = hexcol(tc[1] if len(tc) > 1 else "", "#101014")
    thumb = h - 14
    uri = ctx.art(it)
    fig = (character(uri, thumb / 2, thumb / 2 + 2, thumb - 8, start + .15, "pop", .5, "sway",
                     it["rarity"], it["name"], maxw=thumb - 6, trim=True) if uri else "")
    tx = 12 + thumb + 18
    name_w = _box_x(0) - 22 - tx
    lines, nsize = _row_lines(it["name"], name_w, h)
    meta_size = 30
    block = len(lines) * nsize * .9 + 8 + meta_size * 1.1
    ny = (h - block) / 2

    def box(bc):
        return (f'<i style="display:block;width:{BOX}px;height:{BOX}px;border:4px solid {bc};border-radius:12px;'
                f'background:rgba(10,10,11,.45);box-shadow:inset 0 0 0 3px rgba(0,0,0,.25)"></i>')

    meta = f'{(it.get("type") or "").upper()} · {it["price"]:,} V-BUCKS'
    boxes = "".join(f'<div class="abs" style="left:{_box_x(j):.0f}px;top:{(h - BOX) / 2:.0f}px">{box(bc)}</div>'
                    for j, bc in enumerate((COP_COL, DROP_COL)))
    return (f'<div class="abs" style="left:{BAL_X}px;top:{y:.0f}px;width:{BAL_W}px;height:{h:.0f}px">'
            f'<div class="full" style="background:rgba(10,10,11,.78);border-radius:22px;'
            f'border-left:8px solid {col};{style_anim(an("fromL", start, .55))}">'
            f'<div class="abs" style="left:12px;top:{(h - thumb) / 2:.0f}px;width:{thumb:.0f}px;height:{thumb:.0f}px;'
            f'border-radius:16px;overflow:hidden;background:radial-gradient(circle at 50% 38%,{c1},{c2})">'
            f'{fig}</div>'
            f'<div class="abs d" style="left:4px;top:4px;width:44px;height:44px;border-radius:50%;'
            f'background:{ACCENT};color:{INK};font-size:30px;line-height:46px;text-align:center;'
            f'box-shadow:0 3px 0 rgba(0,0,0,.35)">{k}</div>'
            f'<div class="abs d" style="left:{tx:.0f}px;top:{ny:.0f}px;width:{name_w:.0f}px;'
            f'font-size:{nsize:.0f}px;line-height:.9;white-space:nowrap">{"<br>".join(esc(ln) for ln in lines)}</div>'
            f'<div class="abs" style="left:{tx + 2:.0f}px;top:{ny + len(lines) * nsize * .9 + 8:.0f}px;'
            f'font-size:{meta_size}px;'
            f'font-weight:700;line-height:1.1;letter-spacing:.03em;color:rgba(255,255,255,.74);white-space:nowrap">'
            f'{esc(meta)}</div>'
            f'{boxes}</div></div>')


def _ballot(comp: Comp, ctx: Ctx, items: list, t0: float):
    inner = tile_bg(["#262a36", "#0b0b0e"], "", t0)
    inner += words("YOUR BALLOT", SAFE_LEFT, 366, 110, t0 + .1, "#fff", .1, "slam", "left", 900)
    inner += sticker(f"VOTE 1 TO {len(items)} IN THE COMMENTS", SAFE_LEFT + 6, 490, 34, t0 + .45,
                     ACCENT, INK, -3)
    n = len(items)
    step = min(162, (BAL_BOTTOM - BAL_TOP + 10) / n)
    h = step - 10
    # Column heads over the tick boxes: a ballot, not a verdict.
    for j, (txt, bc) in enumerate((("COP", COP_COL), ("DROP", DROP_COL))):
        cx = BAL_X + _box_x(j) + BOX / 2
        inner += (f'<div class="abs d" style="left:{cx - 60:.0f}px;width:120px;top:{BAL_TOP - 44}px;'
                  f'text-align:center;font-size:32px;color:{bc};text-shadow:0 3px 0 rgba(0,0,0,.5);'
                  f'{style_anim(an("rise", t0 + .5 + j * .08, .4))}">{txt}</div>')
    for i, it in enumerate(items):
        inner += _ballot_row(ctx, it, i + 1, BAL_TOP + i * step, h, t0 + .55 + i * .14)
        comp.cue(t0 + .55 + i * .14 + .3, "tick")
    comp.scene(t0, t0 + BALLOT + .05, inner, fade_in=.05, fade_out=.05)
    comp.cue(t0 + .1, "slam")
    comp.cue(t0 + .45, "pop")


# -------------------------------------------------------------------- build

def build(ctx: Ctx):
    items = _pick(ctx)
    if len(items) < MIN_SINGLES:
        return None
    n = len(items)

    # Rounds stretch when there are fewer than seven, so content (not a padded
    # outro) carries the video past MIN_SECONDS.
    rlen = max(R, math.ceil((MIN_SECONDS - OUTRO_MIN - HOOK - BALLOT) / n * 100) / 100)
    ballot_at = HOOK + n * rlen
    content_end = ballot_at + BALLOT
    comp = Comp(content_end + _pad(content_end))
    comp.css(CSS)

    outfits = [i for i in items if i["type"] == "Outfit"]
    a_item = outfits[0] if outfits else items[0]
    b_item = next((i for i in outfits[1:] + items if i is not a_item), None)
    _hook_scene(comp, ctx, "COP OR DROP?", "VOTE ON EVERY ITEM IN THE COMMENTS", "YOU DECIDE",
                HOOK + .3, a_item, b_item)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop")

    for k, it in enumerate(items, 1):
        t0 = HOOK + (k - 1) * rlen
        _wipe(comp, t0, it.get("tile_colors") or [], it["rarity"])
        _round(comp, ctx, it, k, n, t0, rlen)

    _wipe(comp, ballot_at, ["#3a3f52", "#14151b"])
    _ballot(comp, ctx, items, ballot_at)

    _wipe(comp, content_end, ["#4a5a00", "#15180a"])
    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    _outro_scene(comp, ctx, content_end, comp.duration, "COMMENT COP OR DROP FOR EACH", outfits + [
        i for i in items if i["type"] != "Outfit"])
    comp.add(code_badge(.4))
    comp.add(disclosure())

    def line(k, it):
        s = f"{num(k)} {it['name']} · {it['type']} · {it['price']:,}"
        return s + (" ⏰" if _leaves_today(ctx, it) else "")

    legend = "Prices in V-Bucks."
    if any(_leaves_today(ctx, it) for it in items):
        legend += f" ⏰ = leaves at the next reset ({ctx.reset_et})."
    body = "\n".join(line(k, it) for k, it in enumerate(items, 1)) + "\n\n" + legend
    tags = _hashtags("copordrop", *(it["name"] for it in items[:2]))
    return Video(
        FORMAT, comp,
        title=f"Cop or Drop — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"Cop or Drop: Fortnite Item Shop {ctx.day_label} #shorts",
        caption=_caption(f"✅❌ COP OR DROP? — Fortnite Item Shop, {ctx.day_label}\n"
                         f"{n} items from today's shop. You decide 👇",
                         body, f"Comment COP or DROP for each one, numbered 1–{n}", tags),
        hashtags=tags)
