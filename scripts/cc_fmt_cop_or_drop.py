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

from cc_motion import (ACCENT, INK, RARITY, EASE_BACK, RAIL_TOP, SAFE_RIGHT, W, Comp, an, burst, character,
                       code_badge, countdown, disclosure, esc, hexcol, price_roll, progress,
                       sticker, style_anim, tile_bg, words)
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

# Layout (px). Important content stays in y 190..1480; below y=880 it stays left of
# x=960 (TikTok's like/comment rail). Top-left 190..300 is the code badge.
KICK_Y = 322
NAME_X, NAME_Y, NAME_W = 60, 372, 920
CHAR_CX, CHAR_BOTTOM = 505, 1212
COIN_CX, COIN_D = 862, 240
CARD_X, CARD_W = 50, 212
TAG_XR = 1016                    # right edge of the leaves/since tag (it sits above y=880)
BTN_Y, BTN_H, BTN_W = 1250, 140, 340
COP_X, DROP_X = 60, 940 - BTN_W
RING_CX, RING_CY, RING_D = 500, BTN_Y + BTN_H / 2, 168
COP_COL, COP_LIGHT, COP_EDGE = "#3BD16F", "#7CF0A3", "#1C8A43"
DROP_COL, DROP_LIGHT, DROP_EDGE = "#FF4D4D", "#FF8A8A", "#B52323"

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

def _kicker(it: dict, x: float, y: float, start: float) -> str:
    """TYPE chip with a rarity-coloured dot. A series label ("ICON SERIES") is
    added; plain tiers are not, so "RARE" never reads as a scarcity claim."""
    col = RARITY.get(it.get("rarity", ""), "#9AA0A6")
    kind = esc((it.get("type") or "").upper())
    series = (it.get("rarity_label") or "").strip()
    rest = (f'<span style="color:rgba(255,255,255,.72)">·&nbsp;{esc(series.upper())}</span>'
            if series.lower().endswith("series") else "")
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;transform:rotate(-1.5deg)">'
            f'<div style="display:inline-flex;align-items:center;gap:12px;background:rgba(10,10,11,.82);'
            f'border-radius:12px;padding:9px 18px 9px 14px;font-size:24px;font-weight:800;'
            f'letter-spacing:.16em;white-space:nowrap;{style_anim(an("rise", start, .45))}">'
            f'<i style="width:16px;height:16px;border-radius:50%;background:{col};'
            f'box-shadow:0 0 14px {col}"></i><span>{kind}</span>{rest}</div></div>')


def _coin(price: int, cx: float, cy: float, t0: float) -> str:
    """A V-Bucks coin: pops in empty, the price counts up from 0 inside it, lands
    with a jolt, then the coin keeps a slow tilt-and-bob so it never sits dead."""
    d = COIN_D
    size = _fit(f"{price:,}", d * .7, 88)
    num_top = d / 2 - size * .9 / 2 - 13
    t_in, t_roll, t_land = t0 + T_COIN, t0 + T_ROLL, t0 + T_LAND
    face = (f'<div class="full" style="border-radius:50%;'
            f'background:radial-gradient(circle at 34% 28%,#34353f 0%,#121216 55%,#0a0a0b 100%);'
            f'border:8px solid {ACCENT};box-shadow:0 14px 0 rgba(0,0,0,.38),0 0 70px rgba(232,255,58,.28),'
            f'inset 0 0 0 7px #0a0a0b,inset 0 0 0 10px rgba(232,255,58,.38)"></div>')
    # price_roll's counter shows "0" before it starts; it only appears on cue.
    roll = (f'<div class="full" style="{style_anim(an("fadein", t_roll, .06))}">'
            f'{price_roll(price, d / 2, num_top, size, t_roll, ROLL, ACCENT, "center", "")}</div>')
    unit = (f'<div class="abs" style="left:0;right:0;top:{num_top + size * .9 + 8:.0f}px;text-align:center;'
            f'font-size:19px;font-weight:800;letter-spacing:.32em;text-indent:.32em;'
            f'color:rgba(255,255,255,.78)">V-BUCKS</div>')
    return (f'<div class="abs" style="left:{cx - d / 2:.0f}px;top:{cy - d / 2:.0f}px;width:{d}px;height:{d}px">'
            f'<div class="full" style="{style_anim(an("pop", t_in, .6, EASE_BACK))}">'
            f'<div class="full" style="{style_anim(an("cdCoin", t_in + .6, 2.8, "ease-in-out", "infinite"))}">'
            f'<div class="full" style="{style_anim(an("cdJolt", t_land, .4, "linear"))}">'
            f'{face}{roll}{unit}</div></div></div></div>')


def _intro_card(it: dict, x: float, cy: float, start: float) -> str:
    """'INTRODUCED / CHAPTER 2 / SEASON 1' from the row's own introduction field."""
    ch, se = _intro(it)
    if not ch or not se:
        return ""
    col = RARITY.get(it.get("rarity", ""), "#9AA0A6")
    lines = [f"CHAPTER {ch}", f"SEASON {se}"]
    size = min(46, (CARD_W - 40) / max(_em(s) for s in lines))
    a = style_anim(an("pop", start, .55, EASE_BACK))
    return (f'<div class="abs" style="left:{x:.0f}px;top:{cy - 78:.0f}px;width:{CARD_W}px;'
            f'transform:rotate(-5deg)"><div style="background:rgba(10,10,11,.86);border:3px solid {col};'
            f'border-radius:18px;padding:14px 10px 16px;text-align:center;'
            f'box-shadow:0 10px 0 rgba(0,0,0,.35);{a}">'
            f'<div style="font-size:17px;font-weight:800;letter-spacing:.24em;text-indent:.24em;'
            f'color:#9AA0A6;margin-bottom:8px">INTRODUCED</div>'
            f'<div class="d" style="font-size:{size:.0f}px;line-height:1">{esc(lines[0])}</div>'
            f'<div class="d" style="font-size:{size:.0f}px;line-height:1;color:{ACCENT}">{esc(lines[1])}</div>'
            f'</div></div>')


def _tag(text: str, xr: float, y: float, size: float, start: float, bg: str, fg: str,
         rot: float) -> str:
    """A crooked sticker anchored by its right edge."""
    a = style_anim(an("pop", start, .55, EASE_BACK))
    return (f'<div class="abs" style="right:{W - xr:.0f}px;top:{y:.0f}px;transform:rotate({rot}deg)">'
            f'<div class="d" style="background:{bg};color:{fg};font-size:{size:.0f}px;padding:.16em .42em .1em;'
            f'border-radius:10px;white-space:nowrap;box-shadow:0 8px 0 rgba(0,0,0,.35);{a}">{esc(text)}</div></div>')


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
    fs = 104
    wob = an("cdWob", start + .55, .95, "ease-in-out", "infinite",
             "alternate-reverse" if reverse else "alternate")
    face = (f'<div class="full" style="border-radius:32px;overflow:hidden;'
            f'background:linear-gradient(180deg,{light} 0%,{col} 46%,{col} 100%);'
            f'box-shadow:0 14px 0 {edge},0 28px 36px rgba(0,0,0,.45),inset 0 4px 0 rgba(255,255,255,.45),'
            f'inset 0 -8px 0 rgba(0,0,0,.14);display:flex;align-items:center;justify-content:center;gap:20px">'
            f'{_icon(icon, col)}'
            f'<span class="d" style="font-size:{fs}px;line-height:1;padding-top:.08em;color:#fff;'
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
    d = 116
    origin = f"transform-origin:{cx:.0f}px {cy:.0f}px;"
    gone = style_anim(an("cdOut", out, .2)) if out else ""
    return (f'<div class="full" style="{origin}{gone}">'
            f'<div class="abs d" style="left:{cx - d / 2:.0f}px;top:{cy - d / 2:.0f}px;width:{d}px;'
            f'height:{d}px;border-radius:50%;background:{INK};border:6px solid #fff;display:flex;'
            f'align-items:center;justify-content:center;font-size:54px;padding-top:4px;color:#fff;'
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
    size = 42
    cta_w = (_em("COMMENT IT!") + .84) * size
    cta = (f'<div class="abs" style="left:{cx - cta_w / 2:.0f}px;top:{BTN_Y + BTN_H + 24}px;'
           f'transform:rotate(-3deg)"><div class="d" style="background:#fff;color:{INK};font-size:{size}px;'
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
    top = name_bottom + 14
    outfit = it["type"] == "Outfit"
    h = min(780 if outfit else 560, CHAR_BOTTOM - top)
    cy = CHAR_BOTTOM - h / 2 if outfit else (top + CHAR_BOTTOM) / 2 + 10
    side_cy = max(652, name_bottom + 30 + COIN_D / 2)
    land = t0 + T_LAND

    inner = tile_bg(it.get("tile_colors") or [], it["rarity"], t0)
    inner += character(art, CHAR_CX, cy, h, t0 + T_CHAR, ENTER[(k - 1) % len(ENTER)], .75,
                       "float" if k % 2 else "sway", it["rarity"], it["name"])
    inner += _kicker(it, NAME_X, KICK_Y, t0 + T_KICK)
    for i, line in enumerate(lines):
        inner += words(line, NAME_X, NAME_Y + i * size * .92, size, t0 + T_NAME + i * .12,
                       "#fff", .07, "slam", "left", NAME_W + 40)

    inner += _intro_card(it, CARD_X, side_cy + 24, t0 + T_CARD)
    inner += _coin(it["price"], COIN_CX, side_cy, t0)
    inner += burst(COIN_CX, side_cy, land, ctx.seed + k * 23, 22)
    tag_y = side_cy + COIN_D / 2 + 34
    leaves = _leaves_today(ctx, it)
    tag_size = 32 if leaves else 28
    # Right of x=960 only while the whole tag stays above the like/comment rail.
    tag_xr = TAG_XR if tag_y + tag_size * 1.16 + 12 <= RAIL_TOP else SAFE_RIGHT - 2
    if leaves:
        inner += _tag("LEAVES AT THE NEXT RESET", tag_xr, tag_y, tag_size, t0 + T_TAG, ACCENT, INK, -3)
    else:
        since = _in_since(ctx, it)
        if since:
            inner += _tag(since, tag_xr, tag_y, tag_size, t0 + T_TAG, "rgba(10,10,11,.86)", "#fff", -3)

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


def _ballot_row(ctx: Ctx, it: dict, k: int, y: float, start: float) -> str:
    """One ballot line: numbered cosmetic on its tile colours, name, type and
    price, and two empty tick boxes -- the vote is the viewer's to fill in."""
    x, w, h = 60, 880, 118
    col = RARITY.get(it.get("rarity", ""), "#777")
    tc = it.get("tile_colors") or []
    c1 = hexcol(tc[0] if tc else "", col)
    c2 = hexcol(tc[1] if len(tc) > 1 else "", "#101014")
    thumb = 100
    fig = character(ctx.art(it), thumb / 2, thumb / 2 + 2, thumb - 8, start + .15, "pop", .5, "sway",
                    it["rarity"], it["name"])
    name_w = 430
    nsize = _fit(it["name"], name_w, 48)

    def box(label, bc):
        return (f'<div style="display:flex;align-items:center;gap:10px;height:54px;padding:0 16px 0 12px;'
                f'border:3px solid {bc};border-radius:14px;background:rgba(10,10,11,.5)">'
                f'<i style="display:block;width:24px;height:24px;border:3px solid {bc};border-radius:6px"></i>'
                f'<span class="d" style="font-size:32px;line-height:1;padding-top:3px;color:{bc}">{label}</span></div>')

    meta = f'{(it.get("type") or "").upper()} · {it["price"]:,} V-BUCKS'
    return (f'<div class="abs" style="left:{x}px;top:{y:.0f}px;width:{w}px;height:{h}px">'
            f'<div class="full" style="background:rgba(10,10,11,.76);border-radius:22px;'
            f'border-left:8px solid {col};{style_anim(an("fromL", start, .55))}">'
            f'<div class="abs" style="left:12px;top:{(h - thumb) / 2:.0f}px;width:{thumb}px;height:{thumb}px;'
            f'border-radius:16px;overflow:hidden;background:radial-gradient(circle at 50% 38%,{c1},{c2})">'
            f'{fig}</div>'
            f'<div class="abs d" style="left:2px;top:2px;width:40px;height:40px;border-radius:50%;'
            f'background:{ACCENT};color:{INK};font-size:26px;line-height:40px;text-align:center">{k}</div>'
            f'<div class="abs d" style="left:132px;top:{h / 2 - nsize * .8:.0f}px;width:{name_w}px;'
            f'font-size:{nsize:.0f}px;white-space:nowrap">{esc(it["name"])}</div>'
            f'<div class="abs" style="left:134px;top:{h / 2 + 12:.0f}px;font-size:20px;font-weight:700;'
            f'letter-spacing:.12em;color:rgba(255,255,255,.66);white-space:nowrap">{esc(meta)}</div>'
            f'<div class="abs" style="right:20px;top:{(h - 60) / 2:.0f}px;display:flex;gap:12px">'
            f'{box("COP", COP_COL)}{box("DROP", DROP_COL)}</div>'
            f'</div></div>')


def _ballot(comp: Comp, ctx: Ctx, items: list, t0: float):
    inner = tile_bg(["#262a36", "#0b0b0e"], "", t0)
    inner += words("YOUR BALLOT", 60, 322, 120, t0 + .1, "#fff", .1, "slam", "left", 900)
    inner += sticker(f"VOTE 1 TO {len(items)} IN THE COMMENTS", 64, 444, 34, t0 + .45, ACCENT, INK, -3)
    step = 130 if len(items) >= 7 else 146
    y0 = 530
    for i, it in enumerate(items):
        inner += _ballot_row(ctx, it, i + 1, y0 + i * step, t0 + .55 + i * .14)
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
