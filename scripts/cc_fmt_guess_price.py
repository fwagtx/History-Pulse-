"""
GUESS THE PRICE -- slot 2 (interactive) for @usecodebad.

Six single items from today's shop, one at a time. Each round the cosmetic pops in
on its own Epic tile colours, a price tag swings on its string showing "? ? ?", a
four-second ring drains while the viewer guesses, then the tag rolls up to the real
price with confetti. An answer key recaps all six so people can count their score,
and the outro asks "HOW MANY DID YOU GET?".

Truth rules this format keeps:
  - the price is the row's `price` (single items are never discounted, so there is
    no "regular price" talk here at all)
  - the kicker is the row's own `type` (plus its series label, e.g. "Icon Series")
  - the post-reveal card is the row's `introduction` chapter/season
  - "LEAVES AT THE NEXT RESET" only when `out_day` is today's shop day
Nothing else is claimed: no "most people guessed", no rating, no "back"/"rare".
"""

import math
from datetime import date

from cc_motion import (ACCENT, INK, RARITY, EASE_BACK, EASE_OUT, Comp, an, burst, character,
                       code_badge, countdown, disclosure, esc, hexcol, price_roll, progress, sticker,
                       style_anim, tile_bg, words)
from cc_formats import (Ctx, Video, num, _caption, _hashtags, _hook_scene, _outro_scene, _pad, rng,
                        singles)

FORMAT = "guess_price"
ROUNDS = 6
MIN_SINGLES = 5

HOOK, R, KEY = 3.0, 9.5, 4.0     # hook, one round, answer key (seconds)

# Beats inside a round, in seconds from the round's start.
T_CHAR = .1                      # cosmetic pops in
T_KICK = .35                     # type · rarity kicker
T_NAME = .45                     # name slams
T_TAG = .95                      # price tag drops in on its string
T_CD, CD = 1.5, 4                # the guessing ring
T_REV = T_CD + CD                # ring done: "? ? ?" goes
T_ROLL, ROLL = T_REV + .05, .9   # price counts up
T_LAND = T_ROLL + ROLL           # exact price lands: burst, flash, shake
T_GOT = T_LAND + .35             # "GOT IT?"
T_FACT = T_LAND + .55            # introduction card / leaving sticker

# Layout (px). Everything important sits in y 190..1480; below y=880 it stays left
# of x=960 (TikTok's like/comment rail).
NAME_X, NAME_Y, NAME_W = 60, 384, 880
CHAR_CX, CHAR_BOTTOM = 380, 1172
RING_CX, RING_CY, RING = 835, 640, 200          # upper right, clear of the face, above the rail
TAG_X, TAG_Y, TAG_W, TAG_H, TAG_ROT = 72, 1210, 600, 214, -3
TAG_NOTCH = 64

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
@keyframes gpSwing{{0%{{transform:rotate(-2.2deg)}}100%{{transform:rotate(2.2deg)}}}}
@keyframes gpOut{{0%{{transform:scale(1);opacity:1}}100%{{transform:scale(.35) rotate(-20deg);opacity:0}}}}
@keyframes gpFlash{{0%{{opacity:0}}25%{{opacity:.24}}100%{{opacity:0}}}}
@keyframes gpShine{{0%{{transform:translateX(-160%) skewX(-18deg)}}100%{{transform:translateX(260%) skewX(-18deg)}}}}
/* burst() pieces are opaque at 0%, so with fill "both" they sat stacked at the
   origin until they flew (visible as a small block under the tag and in the outro).
   Same motion, but invisible until launch. This document only. */
@keyframes burst{{0%{{transform:translate(0,0) rotate(0) scale(1);opacity:0}}3%{{opacity:1}}
  100%{{transform:translate(var(--dx),var(--dy)) rotate(var(--r)) scale(.35);opacity:0}}}}
/* The shared hook sets its title at 170px, which puts "GUESS THE PRICE" edge to
   edge (and a word-gap off centre). Scoped to the hook scene of this video only. */
body>.scene:first-child>.abs.d[style*="font-size:170px"]{{font-size:154px!important}}
body>.scene:first-child>.abs.d[style*="font-size:170px"]>span:last-child{{margin-right:0!important}}
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
    """(lines, font size). One line when it can be set at 74px or more, else the
    two-line break that allows the biggest type (preferring to keep a quoted
    colourway on its own line)."""
    one = _fit(name, width, 112)
    ws = name.split()
    if one >= 74 or len(ws) < 2:
        return [name], one
    splits = []
    for i in range(1, len(ws)):
        a, b = " ".join(ws[:i]), " ".join(ws[i:])
        splits.append((min(92, width / max(_em(a), _em(b))), ws[i][:1] in "'\"(", [a, b]))
    top = max(s[0] for s in splits)
    # Among near-equal breaks, keep a quoted colourway together:
    # "Crocs Classic Clog / 'Slate Grey'" beats "Crocs Classic / Clog 'Slate Grey'".
    size, _, lines = max((s for s in splits if s[0] >= top * .92), key=lambda s: (s[1], s[0]))
    return lines, size


def _pick(ctx: Ctx) -> list:
    """Up to six singles with a spread of prices: the cheapest and priciest price
    points always, the rest sampled, one item per price when the shop allows, and
    a mix of types. Deterministic for the day."""
    seen, pool = set(), []
    for it in singles(ctx):
        if it["name"] not in seen and it.get("price"):
            seen.add(it["name"])
            pool.append(it)
    if len(pool) < MIN_SINGLES:
        return []
    r = rng(ctx, 2)
    r.shuffle(pool)
    n = min(ROUNDS, len(pool))

    by_price = {}
    for it in pool:
        by_price.setdefault(it["price"], []).append(it)
    levels = sorted(by_price)
    if len(levels) > n:
        chosen = [levels[0], levels[-1]] + r.sample(levels[1:-1], n - 2)
    else:
        chosen = list(levels)
    r.shuffle(chosen)

    picked, types = [], {}

    def take(cands):
        names = {p["name"] for p in picked}
        cands = [c for c in cands if c["name"] not in names]
        if not cands:
            return
        # Least-used type first; among those an outfit (up to two), since a full
        # character reads best on screen. Ties keep the shuffled order.
        best = min(cands, key=lambda c: (types.get(c["type"], 0),
                                         c["type"] != "Outfit" or types.get("Outfit", 0) >= 2))
        picked.append(best)
        types[best["type"]] = types.get(best["type"], 0) + 1

    for p in chosen:
        take(by_price[p])
    while len(picked) < n:                      # fewer price points than rounds: top up
        take(pool)

    # Play order: shuffled, but never a straight cheap-to-pricey (or reverse) run,
    # and open on an outfit when there is one -- it's the strongest first frame.
    for _ in range(12):
        r.shuffle(picked)
        outfits = [i for i, p in enumerate(picked) if p["type"] == "Outfit"]
        if outfits and outfits[0] != 0:
            picked.insert(0, picked.pop(outfits[0]))
        prices = [p["price"] for p in picked]
        if prices not in (sorted(prices), sorted(prices, reverse=True)):
            break
    return picked


def _leaves_today(ctx: Ctx, it: dict) -> bool:
    try:
        return date.fromisoformat(it.get("out_day") or "") == ctx.day
    except ValueError:
        return False


# --------------------------------------------------------------- components

def _kicker(it: dict, x: float, y: float, start: float) -> str:
    """TYPE chip with a rarity-coloured dot, straight from the row. A series label
    ("ICON SERIES") is added; plain rarity tiers are not, so the word "RARE" never
    appears on screen where it could read as a scarcity claim."""
    col = RARITY.get(it.get("rarity", ""), "#9AA0A6")
    kind = esc((it.get("type") or "").upper())
    series = (it.get("rarity_label") or "").strip()
    rest = (f'<span style="color:rgba(255,255,255,.72)">·&nbsp;{esc(series.upper())}</span>'
            if series.lower().endswith("series") else "")
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;transform:rotate(-1.5deg)">'
            f'<div style="display:inline-flex;align-items:center;gap:12px;background:rgba(10,10,11,.8);'
            f'border-radius:12px;padding:9px 18px 9px 14px;font-size:24px;font-weight:800;'
            f'letter-spacing:.16em;white-space:nowrap;{style_anim(an("rise", start, .45))}">'
            f'<i style="width:16px;height:16px;border-radius:50%;background:{col};'
            f'box-shadow:0 0 14px {col}"></i><span>{kind}</span>{rest}</div></div>')


def _price_tag(price: int, t0: float) -> str:
    """A hanging price tag: notched end, punched hole, string, perforation. It
    swings the whole time; "? ? ?" wobbles until the ring runs out, then the
    real price counts up, lands with a thump and a shine sweeps across."""
    w, h, n = TAG_W, TAG_H, TAG_NOTCH
    shape = f"polygon({n}px 0,100% 0,100% 100%,{n}px 100%,0 50%)"
    inner = f"polygon({n - 3}px 0,100% 0,100% 100%,{n - 3}px 100%,0 50%)"
    hx, hy = 40, h / 2                           # hole centre
    s_len, s_ang = 190, -38                      # string, leaning up-left
    ox = hx + s_len * math.sin(math.radians(s_ang))
    oy = hy - s_len * math.cos(math.radians(s_ang))
    cx = (n + 30 + w - 22) / 2                   # centre of the writing area
    t_in, t_rev, t_roll, t_land = t0 + T_TAG, t0 + T_REV, t0 + T_ROLL, t0 + T_LAND

    string = (f'<div class="abs" style="left:{hx - 2:.0f}px;top:{hy - s_len:.0f}px;width:4px;height:{s_len}px;'
              f'border-radius:2px;background:linear-gradient(to top,rgba(255,255,255,.85),rgba(255,255,255,.35));'
              f'transform-origin:50% 100%;transform:rotate({s_ang}deg)"></div>')
    body = (f'<div class="abs" style="inset:0;clip-path:{shape};background:{ACCENT}"></div>'
            f'<div class="abs" style="inset:7px;clip-path:{inner};overflow:hidden;'
            f'background:linear-gradient(165deg,#1d1e25 0%,#0b0b0e 70%)">'
            f'<div class="abs" style="left:{n + 14}px;top:14px;bottom:14px;'
            f'border-left:3px dashed rgba(232,255,58,.3)"></div>'
            f'<div class="abs" style="top:-20%;bottom:-20%;left:0;width:34%;'
            f'background:linear-gradient(90deg,transparent,rgba(255,255,255,.28),transparent);'
            f'{style_anim(an("gpShine", t_land + .05, .7, "cubic-bezier(.3,0,.2,1)"))}"></div></div>'
            f'<div class="abs" style="left:{hx - 15:.0f}px;top:{hy - 15:.0f}px;width:30px;height:30px;'
            f'border-radius:50%;background:#050507;border:5px solid {ACCENT};'
            f'box-shadow:inset 0 3px 6px rgba(0,0,0,.8)"></div>')
    qs = (f'<div class="abs d" style="left:{cx - 300:.0f}px;width:600px;top:14px;text-align:center;'
          f'font-size:128px;color:#fff;text-shadow:0 8px 0 rgba(0,0,0,.35);'
          f'{style_anim(an("fadeout", t_rev, .15))}">'
          f'<span style="display:inline-block;'
          f'{style_anim(an("wobble", t_in + .3, .42, "ease-in-out", "infinite", "alternate"))}">'
          f'? ? ?</span></div>')
    # price_roll's counter shows "0" before it starts, so it only appears on cue.
    roll = (f'<div class="full" style="{style_anim(an("fadein", t_roll, .06))}">'
            f'{price_roll(price, cx, 14, 128, t_roll, ROLL, ACCENT, "center", "")}</div>')
    unit = (f'<div class="abs" style="left:{cx - 200:.0f}px;width:400px;top:{h - 54}px;text-align:center;'
            f'font-size:22px;font-weight:800;letter-spacing:.34em;color:rgba(255,255,255,.72)">V-BUCKS</div>')

    return (f'<div class="abs" style="left:{TAG_X}px;top:{TAG_Y}px;width:{w}px;height:{h}px;'
            f'transform:rotate({TAG_ROT}deg)">'
            f'<div class="full" style="{style_anim(an("drop", t_in, .7), an("fadein", t_in, .12))}">'
            f'<div class="full" style="{style_anim(an("pulse", t_land, .4))}">'
            f'<div class="full" style="transform-origin:{ox:.0f}px {oy:.0f}px;'
            f'filter:drop-shadow(0 14px 0 rgba(0,0,0,.35));'
            f'{style_anim(an("gpSwing", t_in + .6, 1.25, "ease-in-out", "infinite", "alternate"))}">'
            f'{string}{body}{qs}{roll}{unit}</div></div></div></div>')


def _intro_card(it: dict, start: float) -> str:
    """'INTRODUCED / CHAPTER 2 / SEASON 1' from the row's own introduction field."""
    intro = it.get("introduction") or {}
    ch, se = str(intro.get("chapter") or "").strip(), str(intro.get("season") or "").strip()
    if not ch or not se:
        return ""
    col = RARITY.get(it.get("rarity", ""), "#9AA0A6")
    a = style_anim(an("pop", start, .55, EASE_BACK))
    lines = [f"CHAPTER {ch}", f"SEASON {se}"]
    size = min(46, 190 / max(_em(s) for s in lines))
    return (f'<div class="abs" style="left:{RING_CX - 118}px;top:{RING_CY - 96}px;width:236px;'
            f'transform:rotate(4deg)"><div style="background:rgba(10,10,11,.86);border:3px solid {col};'
            f'border-radius:18px;padding:14px 10px 16px;text-align:center;'
            f'box-shadow:0 10px 0 rgba(0,0,0,.35);{a}">'
            f'<div style="font-size:18px;font-weight:800;letter-spacing:.24em;color:#9AA0A6;'
            f'margin-bottom:8px">INTRODUCED</div>'
            f'<div class="d" style="font-size:{size:.0f}px;line-height:1">{esc(lines[0])}</div>'
            f'<div class="d" style="font-size:{size:.0f}px;line-height:1;color:{ACCENT}">{esc(lines[1])}</div>'
            f'</div></div>')


def _round(comp: Comp, ctx: Ctx, it: dict, k: int, n: int, t0: float):
    art = ctx.art(it)
    lines, size = _name_lines(it["name"])
    name_bottom = NAME_Y + len(lines) * size * .92
    top = name_bottom + 26
    h = min(720 if it["type"] == "Outfit" else 620, CHAR_BOTTOM - top)
    cy = CHAR_BOTTOM - h / 2 if it["type"] == "Outfit" else (top + CHAR_BOTTOM) / 2

    land = t0 + T_LAND
    inner = tile_bg(it.get("tile_colors") or [], it["rarity"], t0)
    # Everything but the backdrop shakes on the landing, so no frame edge shows.
    inner += f'<div class="full" style="{style_anim(an("shake", land, .35, "linear"))}">'
    inner += character(art, CHAR_CX, cy, h, t0 + T_CHAR, "pop", .8,
                       "float" if k % 2 else "sway", it["rarity"], it["name"])
    inner += _kicker(it, NAME_X, 322, t0 + T_KICK)
    for i, line in enumerate(lines):
        inner += words(line, NAME_X, NAME_Y + i * size * .92, size, t0 + T_NAME + i * .12,
                       "#fff", .07, "slam", "left", NAME_W + 40)

    # The guessing ring, upper right: clear of the face, above the rail. It pops
    # in as it starts (countdown() alone shows its disc from the scene's start)
    # and shrinks away when the time is up.
    origin = f"transform-origin:{RING_CX}px {RING_CY}px;"
    inner += (f'<div class="full" style="{origin}'
              f'{style_anim(an("gpOut", t0 + T_REV, .3, "cubic-bezier(.5,0,.8,.3)"))}">'
              f'<div class="full" style="{origin}{style_anim(an("pop", t0 + T_CD, .5, EASE_BACK))}">'
              f'{countdown(CD, RING_CX, RING_CY, RING, t0 + T_CD, "GUESS!")}</div></div>')

    inner += _price_tag(it["price"], t0)
    inner += burst(TAG_X + TAG_W / 2, TAG_Y + TAG_H / 2, land, ctx.seed + k * 17)
    inner += sticker("GOT IT?", TAG_X + TAG_W - 70, TAG_Y - 44, 42, t0 + T_GOT, "#ffffff", INK, 7)

    inner += _intro_card(it, t0 + T_FACT)
    if _leaves_today(ctx, it):
        inner += sticker("LEAVES AT THE NEXT RESET", RING_CX - 210, RING_CY + 118, 28,
                         t0 + T_FACT + .25, ACCENT, INK, -3)
    inner += "</div>"
    inner += (f'<div class="full" style="background:#fff;opacity:0;pointer-events:none;'
              f'{style_anim(an("gpFlash", land, .45, "ease-out"))}"></div>')
    inner += progress(t0, t0 + R, k, n)
    comp.scene(t0, t0 + R + .25, inner, fade_in=.25, fade_out=.25)

    comp.cue(t0 + T_CHAR, "whoosh")
    comp.cue(t0 + T_NAME, "slam")
    comp.cue(t0 + T_TAG + .35, "pop")
    for s in range(CD):
        comp.cue(t0 + T_CD + s, "tick")
    comp.cue(t0 + T_ROLL, "reveal")
    comp.cue(land, "cash")
    comp.cue(t0 + T_GOT, "pop")


def _key_row(ctx: Ctx, it: dict, k: int, y: float, start: float) -> str:
    """One answer-key line: numbered thumbnail on the item's tile colours, name,
    type, and the price."""
    x, w, h = 60, 880, 128
    col = RARITY.get(it.get("rarity", ""), "#777")
    tc = it.get("tile_colors") or []
    c1 = hexcol(tc[0] if tc else "", col)
    c2 = hexcol(tc[1] if len(tc) > 1 else "", "#101014")
    uri = ctx.art(it)
    img = (f'<img src="{uri}" style="width:100%;height:100%;object-fit:contain;display:block">'
           if uri else "")
    price = f'{it["price"]:,}'
    name_w = w - 150 - 190
    nsize = _fit(it["name"], name_w, 50)
    a_row = style_anim(an("fromL", start, .55, EASE_OUT))
    a_price = style_anim(an("slam", start + .3, .4))
    return (f'<div class="abs" style="left:{x}px;top:{y:.0f}px;width:{w}px;height:{h}px">'
            f'<div class="full" style="background:rgba(10,10,11,.74);border-radius:22px;'
            f'border-left:8px solid {col};{a_row}">'
            f'<div class="abs" style="left:14px;top:{(h - 106) / 2:.0f}px;width:106px;height:106px;'
            f'border-radius:16px;overflow:hidden;background:radial-gradient(circle at 50% 38%,{c1},{c2})">'
            f'{img}</div>'
            f'<div class="abs d" style="left:4px;top:4px;width:40px;height:40px;border-radius:50%;'
            f'background:{ACCENT};color:{INK};font-size:26px;line-height:40px;text-align:center">{k}</div>'
            f'<div class="abs d" style="left:146px;top:{h / 2 - nsize * .78:.0f}px;width:{name_w}px;'
            f'font-size:{nsize:.0f}px;white-space:nowrap">{esc(it["name"])}</div>'
            f'<div class="abs" style="left:148px;top:{h / 2 + 12:.0f}px;font-size:21px;font-weight:700;'
            f'letter-spacing:.14em;color:rgba(255,255,255,.62);white-space:nowrap">'
            f'{esc((it.get("type") or "").upper())}</div>'
            f'<div class="abs" style="right:26px;top:{h / 2 - 46:.0f}px;text-align:right">'
            f'<div class="d" style="font-size:58px;color:{ACCENT};white-space:nowrap;{a_price}">{price}</div>'
            f'<div style="font-size:15px;font-weight:800;letter-spacing:.3em;color:rgba(255,255,255,.7);'
            f'margin-top:14px;margin-right:-.3em">V-BUCKS</div></div>'
            f'</div></div>')


def _answer_key(comp: Comp, ctx: Ctx, items: list, t0: float):
    inner = tile_bg(["#262a36", "#0b0b0e"], "", t0)
    inner += words("ANSWER KEY", 60, 330, 124, t0 + .1, "#fff", .1, "slam", "left", 900)
    inner += sticker("COUNT YOUR SCORE", 64, 458, 34, t0 + .45, ACCENT, INK, -3)
    step = 146
    y0 = 548
    for i, it in enumerate(items):
        inner += _key_row(ctx, it, i + 1, y0 + i * step, t0 + .55 + i * .16)
        comp.cue(t0 + .55 + i * .16 + .3, "tick")
    comp.scene(t0, t0 + KEY + .25, inner, fade_in=.25, fade_out=.25)
    comp.cue(t0 + .05, "whoosh")
    comp.cue(t0 + .1, "slam")


# -------------------------------------------------------------------- build

def build(ctx: Ctx):
    items = _pick(ctx)
    if len(items) < MIN_SINGLES:
        return None
    n = len(items)

    content_end = HOOK + n * R + KEY
    comp = Comp(content_end + _pad(content_end))
    comp.css(CSS)

    outfits = [i for i in items if i["type"] == "Outfit"]
    a_item = outfits[0] if outfits else items[0]
    b_item = next((i for i in outfits[1:] + items if i is not a_item), None)
    _hook_scene(comp, ctx, "GUESS THE PRICE", "COMMENT YOUR GUESSES", "PAUSE & GUESS",
                HOOK + .3, a_item, b_item)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop")

    for k, it in enumerate(items, 1):
        _round(comp, ctx, it, k, n, HOOK + (k - 1) * R)

    _answer_key(comp, ctx, items, HOOK + n * R)

    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    _outro_scene(comp, ctx, content_end, comp.duration, "HOW MANY DID YOU GET?", items)
    comp.add(code_badge(.4))
    comp.add(disclosure())

    rounds = "\n".join(f"{num(k)} {it['name']} · {it['type']}" for k, it in enumerate(items, 1))
    body = rounds          # no prices here: they're the answers
    tags = _hashtags("guesstheprice", *(it["name"] for it in items[:2]))
    return Video(
        FORMAT, comp,
        title=f"Guess the Price — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"Guess the Price: Fortnite Item Shop {ctx.day_label} #shorts",
        caption=_caption(f"💸 GUESS THE PRICE — Fortnite Item Shop, {ctx.day_label}\n"
                         f"{n} items from today's shop. Pause, guess, then watch the reveal 👇",
                         body, f"How many did you get out of {n}? Comment your score", tags),
        hashtags=tags)
