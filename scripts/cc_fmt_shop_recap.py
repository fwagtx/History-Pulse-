"""
Shop Recap -- slot 1, every day.

    0:00  hook      TODAY'S SHOP / N OFFERS, two real cosmetics sliding in
    0:03  bundle    the bundle with the biggest saving vs Epic's regular price
                    (or the priciest bundle when nothing is discounted): art drops
                    in, a band lists what it includes, Epic's regular price gets
                    struck through, a 3-second countdown, then today's price rolls
                    up beside it and the SAVE sticker slaps on
    0:12  items     6-7 single cosmetics, ~6s each: tile-coloured stage, the
                    cosmetic enters and idles, name slams in, rarity/type pill,
                    every truthful tag that applies as a row of stickers under
                    the name (LEAVES AT RESET / ADDED SEP 22 / OG · CH1 S8), and
                    the price rolls up on a card in the corner
    0:54  outro     code BAD + "WHAT ARE YOU BUYING?"

Every claim comes straight from the shop row. Singles are never shown as
discounted; only bundles carry a regular price above today's price, and that is
called "regular price", nothing else. A dark wipe carries each cut so the video
reads as one piece rather than a slideshow.
"""

from datetime import date, timedelta

from cc_formats import (Ctx, Video, bundles, singles, rng, _pad, _hook_scene,
                        _outro_scene, _hashtags, _caption, BRAND_TAGS)
from cc_looks import PREP_JS
from cc_motion import (ACCENT, INK, RARITY, W, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, Comp,
                       an, burst, character, code_badge, countdown, disclosure, esc, hexcol,
                       label, price_roll, progress, sticker, style_anim, tile_bg, words,
                       EASE_BACK)

FORMAT = "shop_recap"
HOOK = 3.0          # hook length
BUNDLE_LEN = 9.0    # scene A
ITEM_LEN = 6.0      # each single-item scene (stretched a little if there are few)
MAX_ITEMS = 7
CONTENT_TARGET = 54.0   # content end we aim for; the outro pads to MIN_SECONDS

LEAVE_RED = "#FF3B3B"

# Anton advance widths (em) at letter-spacing 0, measured in headless Chromium.
# Used to size display text so names fit on one or two lines, never clipped.
_ANTON = {
    " ": .244, "!": .239, '"': .439, "#": .556, "$": .472, "%": 1.067, "&": .53, "'": .224,
    "(": .301, ")": .301, "*": .462, "+": .365, ",": .246, "-": .321, ".": .239, "/": .415,
    "0": .504, "1": .341, "2": .504, "3": .504, "4": .504, "5": .504, "6": .504, "7": .504,
    "8": .504, "9": .504, ":": .252, ";": .255, "?": .502, "@": .874, "A": .495, "B": .489,
    "C": .484, "D": .503, "E": .422, "F": .409, "G": .495, "H": .509, "I": .237, "J": .476,
    "K": .482, "L": .407, "M": .756, "N": .508, "O": .496, "P": .482, "Q": .504, "R": .487,
    "S": .472, "T": .406, "U": .484, "V": .479, "W": .722, "X": .494, "Y": .456, "Z": .42,
    "·": .244, "’": .242,
}


def _em(text: str) -> float:
    """Width of Anton text in em (the .d class adds .01em letter-spacing)."""
    return sum(_ANTON.get(ch, .5) + .01 for ch in text.upper())


def _lines(text: str, size: float, width: float) -> int:
    """How many lines words() will wrap `text` into (each word carries a .18em margin)."""
    n, cur = 1, 0.0
    for w in text.split():
        ww = (_em(w) + .18) * size
        if cur and cur + ww > width:
            n, cur = n + 1, ww
        else:
            cur += ww
    return n


def _fit(text: str, width: float, big: int, one_min: int, two_max: int, small: int):
    """Largest size that keeps `text` on one line (down to one_min), else the
    largest two-line size (capped at two_max). Returns (size, lines)."""
    for s in range(big, one_min - 1, -2):
        if _lines(text, s, width) == 1:
            return s, 1
    for s in range(two_max, small - 1, -2):
        if _lines(text, s, width) <= 2:
            return s, 2
    return small, _lines(text, small, width)


FIT_SLACK = 12          # px: sizes are chosen for a line this much narrower than the box


def _balanced(html: str, text: str, size: float, width: float) -> str:
    """words() output with an even two-line split: a name that needs two lines
    breaks where both lines come out closest in length, instead of leaving one
    word alone on the second line. `width` is the box's width; like _fit's
    choices, every line leaves FIT_SLACK px spare, so the browser never wraps
    differently. One-line and 3+-line names are unchanged."""
    width -= FIT_SLACK
    ws = text.split()
    ww = [(_em(w) + .18) * size for w in ws]
    if sum(ww) <= width or len(ws) < 2:
        return html
    best, k_best = None, 0
    for k in range(1, len(ws)):
        a, b = sum(ww[:k]), sum(ww[k:])
        if max(a, b) <= width and (best is None or max(a, b) < best):
            best, k_best = max(a, b), k
    if not k_best:
        return html
    parts = html.split("</span><span")
    if len(parts) != len(ws):
        return html
    return "</span><span".join(parts[:k_best]) + "</span><br><span" + "</span><span".join(parts[k_best:])


def _mon_d(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%b %-d").upper()


def _clean_name(name: str) -> str:
    """'Kingdom Hearts (19 items)' -> 'Kingdom Hearts'."""
    return name.split(" (")[0].strip() if name.endswith(" items)") else name


def _facts(item: dict, ctx: Ctx) -> list:
    """Every truthful tag that applies to a row, as (kind, sticker text)."""
    day = ctx.day.isoformat()
    out = []
    if item.get("out_day") == day:
        out.append(("leaves", "LEAVES AT RESET"))
    if item.get("in_day") and item["in_day"] >= (ctx.day - timedelta(days=1)).isoformat():
        out.append(("added", f"ADDED {_mon_d(item['in_day'])}"))
    intro = item.get("introduction") or {}
    ch, se = str(intro.get("chapter") or ""), str(intro.get("season") or "")
    # "OG" means Chapter 1 to most players; Chapter 2 items just say where they're from.
    if ch == "1":
        out.append(("og", f"OG · CH1 S{se}" if se else "OG · CH1"))
    elif ch == "2":
        out.append(("og", f"FROM CH2 S{se}" if se else "FROM CH2"))
    return out


# ---------------------------------------------------------------- selection

TYPE_WEIGHT = {"Outfit": 3.0, "Sidekick": 2.2, "Pickaxe": 1.4, "Glider": 1.4, "Emote": 1.2,
               "Shoes": 1.0, "Back Bling": .6, "Wrap": .6, "Contrail": .4}


def _headline_bundle(ctx: Ctx):
    """Biggest saving vs Epic's regular price; else the priciest bundle; else None.
    Returns (bundle, kicker)."""
    bl = bundles(ctx)
    disc = [b for b in bl if b.get("discounted") and (b.get("regular_price") or 0) > (b.get("price") or 0)]
    if disc:
        diff = lambda b: b["regular_price"] - b["price"]
        best = max(disc, key=lambda b: (diff(b), b["price"], b["name"]))
        tied = sum(1 for b in disc if diff(b) == diff(best)) > 1
        return best, ("BUNDLE ON SALE TODAY" if tied else "BIGGEST BUNDLE SAVING TODAY")
    priced = [b for b in bl if b.get("price")]
    if priced:
        best = max(priced, key=lambda b: (b["price"], b["name"]))
        tied = sum(1 for b in priced if b["price"] == best["price"]) > 1
        return best, ("BUNDLE IN TODAY'S SHOP" if tied else "PRICIEST BUNDLE TODAY")
    return None, ""


def _pick_items(ctx: Ctx, head: dict | None, n: int) -> list:
    """6-7 singles that together say the most: something leaving at reset,
    something just added, an OG, mostly outfits, spread across types and
    sections. Deterministic per shop day."""
    r = rng(ctx, 71)
    pool = sorted(singles(ctx), key=lambda i: i["name"])
    score = {}
    for it in pool:
        kinds = {k for k, _ in _facts(it, ctx)}
        score[it["name"]] = (TYPE_WEIGHT.get(it["type"], .8) + 2.4 * ("leaves" in kinds)
                             + 1.8 * ("added" in kinds) + 1.8 * ("og" in kinds)
                             + min(it["price"], 2000) / 1000 + r.random() * 1.6)
    pool.sort(key=lambda i: -score[i["name"]])
    head_section = (head or {}).get("section") or ""

    picked, types, sections, palettes = [], {}, {}, {}
    pal = lambda it: tuple(it.get("tile_colors") or [it["rarity"]])

    def fits(it):
        if it in picked:
            return False
        if types.get(it["type"], 0) >= (3 if it["type"] == "Outfit" else 2):
            return False
        if palettes.get(pal(it), 0) >= 2:          # Epic reuses a default tile palette a lot
            return False
        sec = it.get("section") or ""
        if sec and sections.get(sec, 0) >= (1 if sec == head_section else 2):
            return False
        return True

    def take(it):
        picked.append(it)
        types[it["type"]] = types.get(it["type"], 0) + 1
        palettes[pal(it)] = palettes.get(pal(it), 0) + 1
        sec = it.get("section") or ""
        if sec:
            sections[sec] = sections.get(sec, 0) + 1

    # One of each kind of fact first, so the recap covers them all when they exist.
    for kind in ("leaves", "added", "og"):
        for it in pool:
            if fits(it) and kind in {k for k, _ in _facts(it, ctx)}:
                take(it)
                break
    for it in pool:
        if len(picked) >= n:
            break
        if fits(it):
            take(it)
    for it in pool:                      # caps too tight for a thin shop: relax them
        if len(picked) >= n:
            break
        if it not in picked:
            take(it)

    # Pace it: strongest first, and never the same type or the same backdrop twice
    # in a row when that can be avoided.
    picked.sort(key=lambda i: -score[i["name"]])
    order = []
    while picked:
        nxt = picked[0]
        if order:
            prev = order[-1]
            both = [i for i in picked if i["type"] != prev["type"] and pal(i) != pal(prev)]
            either = [i for i in picked if i["type"] != prev["type"] or pal(i) != pal(prev)]
            nxt = (both or either or picked)[0]
        order.append(nxt)
        picked.remove(nxt)
    return order


# ---------------------------------------------------------------- components

# Layout. Everything a viewer reads sits in the apps' safe box (cc_safe): the
# words in the wide top band, starting under the code badge and its
# #EpicPartner tag (which end at y 350); the cosmetic in the band beside the
# button rail (x 60-900, so centred on x 480); the price card in the bottom
# left, ending above the caption zone (y 1420). Backgrounds, light rays, the
# giant outlined type and the wipes run to the edges.
TEXT_X = SAFE_LEFT + 4                      # 64: labels, stickers
NAME_X = SAFE_LEFT + 2                      # 62: display names (Anton's side bearing)
TEXT_W = SAFE_RIGHT_TOP - NAME_X - 10       # 948: a line in the wide band
ROW1_Y = 368                                # the first line under the #EpicPartner tag
ART_X = (SAFE_LEFT + SAFE_RIGHT) / 2        # 480
ART_MAXW = 800
CARD_X, CARD_BOTTOM = SAFE_LEFT + 8, SAFE_BOTTOM - 20      # 68, 1400
CARD_MAXW = SAFE_RIGHT - 8 - CARD_X         # 824
LABEL = 30                                  # supporting text is never under 30 px

# Inter 800 advance widths (em) for capitals, digits and the punctuation the
# labels use, measured in the render browser like _ANTON.
_INTER = {
    "A": .75, "B": .647, "C": .728, "D": .706, "E": .619, "F": .593, "G": .738, "H": .722, "I": .27,
    "J": .573, "K": .706, "L": .565, "M": .909, "N": .731, "O": .747, "P": .639, "Q": .747, "R": .658,
    "S": .668, "T": .645, "U": .705, "V": .742, "W": 1.033, "X": .718, "Y": .709, "Z": .643,
    "0": .665, "1": .401, "2": .614, "3": .628, "4": .673, "5": .61, "6": .631, "7": .582, "8": .627,
    "9": .631, " ": .2, "·": .254, "'": .278, "’": .241, "&": .663, "-": .452, ":": .254, ".": .254,
    ",": .254, "!": .258, "?": .585, "(": .345, ")": .345, "/": .379, "#": .635, "+": .666,
}


def _inter_w(text: str, size: float, spacing: float) -> float:
    """Width of a letter-spaced Inter 800 label in capitals."""
    return sum(_INTER.get(ch, .75) + spacing for ch in text.upper()) * size


_CSS = [
    "@keyframes srwipe{from{transform:translateX(-2760px) skewX(-14deg)}"
    "to{transform:translateX(2040px) skewX(-14deg)}}",      # fully covers the frame at mid-sweep
    "@keyframes srdrift{from{transform:translateX(80px)}to{transform:translateX(-80px)}}",
    "@keyframes srband{from{transform:scaleX(0)}to{transform:scaleX(1)}}",
    "@keyframes srshine{from{transform:translateX(-160%) skewX(-20deg)}to{transform:translateX(420%) skewX(-20deg)}}",
]


def _wipe(comp, t: float, colors: list):
    """A skewed panel in the incoming scene's colours that sweeps across the cut
    at `t`, white and accent edges. It hides the cross-fade so each cut lands
    like an edit instead of a dissolve."""
    c1 = hexcol(colors[0] if colors else "", "#26262c")
    c2 = hexcol(colors[1] if len(colors) > 1 else "", INK)
    a = style_anim(an("srwipe", t - .32, .64, "cubic-bezier(.75,0,.25,1)"))
    comp.add(f'<div class="abs" style="left:0;top:-200px;width:1800px;height:2320px;z-index:30;{a}">'
             f'<div style="position:absolute;inset:0;background:linear-gradient(90deg,{c2},{c1} 70%,{c2})"></div>'
             f'<div style="position:absolute;top:0;bottom:0;left:-16px;width:16px;background:#fff"></div>'
             f'<div style="position:absolute;top:0;bottom:0;right:-30px;width:30px;background:{ACCENT}"></div>'
             f'</div>')
    comp.cue(t - .2, "whoosh")


def _ghost(text: str, y: float, size: float, t0: float, dur: float) -> str:
    """Giant outlined type drifting behind the cosmetic: depth, not information
    (the pill above the name says the same thing), so it may run off the edges."""
    return (f'<div class="abs d" data-safe="ignore" style="left:-30px;top:{y:.0f}px;white-space:nowrap;'
            f'font-size:{size:.0f}px;color:transparent;-webkit-text-stroke:3px rgba(255,255,255,.16);'
            f'{style_anim(an("srdrift", t0, dur, "linear"))}">{esc(text)}</div>')


def _stick(text: str, x: float, y: float, size: float, start: float, bg: str, fg: str,
           rot: float, pulse: bool = False) -> str:
    """A left-anchored crooked sticker; `pulse` makes it breathe after landing."""
    pop = style_anim(an("pop", start, .55, EASE_BACK))
    breathe = style_anim(an("pulse", start + .6, 1.1, "ease-in-out", "infinite")) if pulse else ""
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;transform:rotate({rot}deg)">'
            f'<div style="transform-origin:50% 50%;{breathe}"><div class="d" style="background:{bg};color:{fg};'
            f'font-size:{size:.0f}px;padding:.16em .42em .1em;border-radius:10px;white-space:nowrap;'
            f'box-shadow:0 8px 0 rgba(0,0,0,.35);{pop}">{esc(text)}</div></div></div>')


def _stick_w(text: str, size: float) -> float:
    return (_em(text) + .84) * size


def _includes(b: dict, y: float, start: float) -> tuple:
    """What the bundle holds, on a tilted band under its title: "19 ITEMS: SORA /
    RIKU / KAIRI & MORE". The names that fit on one line inside the safe box;
    the band itself runs off both edges. Returns (html, height)."""
    seen, names = set(), []
    for n in b.get("member_names") or []:
        n = (n or "").strip()
        if n and n.lower() not in seen:
            seen.add(n.lower())
            names.append(n)
    count = int(b.get("bundle_size") or 0)
    head = f"{count} ITEMS" if count else "INCLUDES"
    if not names and not count:
        return "", 0
    room = TEXT_W - 12
    size, shown = 38, []
    for size in (38, 34):
        shown = []
        for i, nm in enumerate(names):
            more = " & MORE" if i + 1 < len(names) else ""
            trial = f"{head}: " + " / ".join(shown + [nm]) + more
            if _em(trial) * size > room:
                break
            shown.append(nm)
        if shown:
            break
    sep = f'<span style="color:{ACCENT}"> / </span>'
    txt = f'<span style="color:{ACCENT}">{esc(head)}{":" if shown else ""}</span>'
    if shown:
        txt += " " + sep.join(esc(n) for n in shown)
        if len(shown) < len(names):
            txt += f'<span style="color:{ACCENT}"> &amp; MORE</span>'
    h = round(size * .9 + 26)
    band_in = style_anim(an("srband", start, .45, "cubic-bezier(.2,.8,.2,1)"))
    txt_in = style_anim(an("rise", start + .2, .45))
    return (f'<div class="abs" style="left:-60px;top:{y:.0f}px;width:{W + 120}px;height:{h}px;'
            f'transform:rotate(-1.5deg)"><div style="position:absolute;inset:0;background:rgba(10,10,11,.86);'
            f'border-top:4px solid {ACCENT};border-bottom:4px solid {ACCENT};transform-origin:0 50%;{band_in}"></div>'
            f'<div class="d" style="position:absolute;left:{TEXT_X + 60}px;top:{(h - size * .9) / 2:.0f}px;'
            f'white-space:nowrap;font-size:{size}px;color:#fff;{txt_in}">{txt}</div></div>'), h


def _from(t: float, inner: str) -> str:
    """Hidden until `t`. price_roll's counter and burst's confetti both show their
    first keyframe before they start (fill: both), so they wait behind this."""
    return f'<div class="abs" style="left:0;top:0;{style_anim(an("fadein", t, .01))}">{inner}</div>'


def _shine(t: float, w: float = 220) -> str:
    """One glint across a card as its price lands. Parent needs overflow:hidden."""
    return (f'<div class="abs" style="left:0;top:-20%;width:{w:.0f}px;height:140%;background:linear-gradient(90deg,'
            f'transparent,rgba(255,255,255,.22),transparent);{style_anim(an("srshine", t, .8, "ease-in-out"))}"></div>')


def _price_w(value: int, size: float) -> float:
    """Rendered width of price_roll's settled '1,200 V-BUCKS'."""
    return _em(f"{value:,}") * size + (_em("V-BUCKS") + .2) * .38 * size


def _scrim() -> str:
    """Darkens the top and bottom bands so white type holds up on pale tile colours."""
    return ('<div class="full" style="background:linear-gradient(180deg,rgba(0,0,0,.5) 0,'
            'rgba(0,0,0,.18) 22%,rgba(0,0,0,0) 34%,rgba(0,0,0,0) 60%,rgba(0,0,0,.42) 78%,'
            'rgba(0,0,0,.6) 100%)"></div>')


def _ink_on(bg: str) -> str:
    """Dark text on light fills, white on dark ones."""
    h = hexcol(bg, "#777777").lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return INK if .2126 * r + .7152 * g + .0722 * b > .42 else "#fff"


def _fade_between(inner: str, t_in: float, t_out: float) -> str:
    """Visible from t_in to t_out. Two wrappers, because two opacity animations on
    one element fight (the later one's backwards fill wins)."""
    return (f'<div class="abs" style="left:0;top:0;{style_anim(an("fadeout", t_out, .18))}">'
            f'<div class="abs" style="left:0;top:0;{style_anim(an("fadein", t_in, .2))}">{inner}</div></div>')


def _cosmetic(ctx: Ctx, it: dict, top: float, bottom: float, start: float, enter: str, idle: str,
              name: str) -> str:
    """The cosmetic, centred in the band beside the rail between `top` and
    `bottom`. data-trim (cc_looks.PREP_JS) crops Fortnite's square art to the
    cosmetic, so it fills the space instead of its transparent margins."""
    return character(ctx.art(it), ART_X, (top + bottom) / 2, bottom - top, start, enter, .7, idle,
                     it["rarity"], name, maxw=ART_MAXW).replace('<img class="art"', '<img class="art" data-trim', 1)


def _card(w: float, h: float, accent: str, t_rise: float, t_shine: float, body: str) -> str:
    """The dark, slightly crooked price card in the bottom-left corner."""
    card = (f'<div class="abs" style="left:0;top:0;width:{w:.0f}px;height:{h:.0f}px;border-radius:22px;'
            f'background:rgba(10,10,11,.9);border:3px solid rgba(255,255,255,.12);overflow:hidden;'
            f'box-shadow:0 14px 0 rgba(0,0,0,.35),0 26px 50px rgba(0,0,0,.4)">{_shine(t_shine)}</div>'
            f'<div class="abs" style="left:0;top:0;width:10px;height:{h:.0f}px;border-radius:22px 0 0 22px;'
            f'background:{accent}"></div>') + body
    return (f'<div class="abs" style="left:{CARD_X}px;top:{CARD_BOTTOM - h:.0f}px;width:{w:.0f}px;height:{h:.0f}px;'
            f'transform:rotate(-2deg)"><div class="abs" style="left:0;top:0;width:{w:.0f}px;height:{h:.0f}px;'
            f'{style_anim(an("rise", t_rise, .45))}">{card}</div></div>')


# ---------------------------------------------------------------- scenes

def _bundle_scene(comp, ctx: Ctx, b: dict, kicker: str, t0: float, t1: float):
    dur = t1 - t0
    title = b.get("section") or _clean_name(b["name"])
    price, reg = int(b["price"]), int(b.get("regular_price") or b["price"])
    discounted = bool(b.get("discounted")) and reg > price
    size, nl = _fit(title, TEXT_W - FIT_SLACK, 136, 100, 104, 72)
    title_y = ROW1_Y + 46
    title_bottom = title_y + nl * size * .92

    inner = tile_bg(b.get("tile_colors") or [], b["rarity"], t0) + _scrim()
    inner += _ghost("BUNDLE", 600, 340, t0, dur)
    band, band_h = _includes(b, title_bottom + 20, t0 + 1.2)
    inner += band
    art_top = max(560, title_bottom + 20 + band_h + 26)

    # The price card: Epic's regular price struck through beside today's price,
    # which waits behind ??? and a 3-second countdown, then rolls up.
    t_panel, t_strike, t_cd, t_rev = t0 + 1.6, t0 + 2.55, t0 + 3.0, t0 + 6.0
    P, LY, PY, PS = 34, 24, 66, 96             # padding, label row, price row, price size
    ring = 104
    wait_w = _em("???") * PS + 24 + ring        # ??? and the ring beside it
    today_w = max(_inter_w("TODAY'S PRICE", LABEL, .18), _price_w(price, PS), wait_w)
    body = ""
    x2 = P
    if discounted:
        rs = 76
        reg_w = max(_inter_w("REGULAR PRICE", LABEL, .18), _price_w(reg, rs) + 20)
        body += label("REGULAR PRICE", P, LY, LABEL, t0 + 1.9, "#A9AFB6", 800, spacing=".18em")
        strike = style_anim(an("strike", t_strike, .3, "cubic-bezier(.6,0,.3,1)"))
        body += (f'<div class="abs d" style="left:{P + 10}px;top:{PY + (PS - rs) * .55:.0f}px;font-size:{rs}px;'
                 f'color:rgba(255,255,255,.88);{style_anim(an("rise", t0 + 2.0, .45))}">'
                 f'<span style="position:relative;display:inline-block;white-space:nowrap">{reg:,}'
                 f'<span style="font-size:.38em;opacity:.75;margin-left:.2em">V-BUCKS</span>'
                 f'<span style="position:absolute;left:-10px;right:-10px;top:44%;height:9px;transform:rotate(-4deg)">'
                 f'<span style="display:block;height:100%;border-radius:6px;background:{LEAVE_RED};'
                 f'transform-origin:0 50%;box-shadow:0 3px 0 rgba(0,0,0,.4);{strike}"></span></span></span></div>')
        x2 = P + reg_w + 44
        body += (f'<div class="abs" style="left:{x2 - 24:.0f}px;top:22px;bottom:22px;'
                 f'border-left:3px dashed rgba(255,255,255,.22);{style_anim(an("fadein", t0 + 2.2, .3))}"></div>')
        comp.cue(t_strike, "slam")
    card_w = x2 + today_w + P
    card_h = PY + PS * .9 + 22
    # With nothing struck through first, today's side fills the card as it lands.
    t_today = t_cd - .1 if discounted else t0 + 1.9
    body += label("TODAY'S PRICE", x2, LY, LABEL, t_today, ACCENT, 800, spacing=".18em")
    body += _fade_between(f'<div class="abs d" style="left:{x2:.0f}px;top:{PY}px;font-size:{PS}px;'
                          f'color:{ACCENT};{style_anim(an("pulse", t_cd, 1, "ease-in-out", "3"))}">???</div>',
                          t_today, t_rev)
    body += _fade_between(countdown(3, x2 + _em("???") * PS + 24 + ring / 2, PY + PS * .45, ring, t_cd),
                          t_cd - .1, t_rev)
    body += _from(t_rev, price_roll(price, x2, PY, PS, t_rev, 1.1))
    for s in range(3):
        comp.cue(t_cd + s, "tick")
    comp.cue(t_rev, "reveal"); comp.cue(t_rev + 1.1, "cash")
    card_top = CARD_BOTTOM - card_h

    inner += _cosmetic(ctx, b, art_top, card_top - 16, t0 + .15, "drop", "float", title)
    inner += label(kicker, TEXT_X, ROW1_Y, LABEL, t0 + .1, ACCENT, 800, spacing=".2em")
    inner += _balanced(words(title, NAME_X, title_y, size, t0 + .3, "#fff", .1, "slam", "left", TEXT_W),
                       title, size, TEXT_W)
    comp.cue(t0 + .3, "slam"); comp.cue(t0 + .63, "slam")
    inner += _card(card_w, card_h, ACCENT, t_panel, t_rev + 1.05, body)
    comp.cue(t_panel, "whoosh")
    if discounted:
        save = f"SAVE {reg - price:,}"
        ss = 60
        sx = min(CARD_X + card_w - _stick_w(save, ss) + 16, SAFE_RIGHT - 10 - _stick_w(save, ss))
        inner += sticker(save, sx, card_top - ss * 1.16 - 14, ss, t_rev + 1.15, rot=5)
        inner += _from(t_rev + 1.1, burst(CARD_X + x2 + 160, card_top + 90, t_rev + 1.1, ctx.seed))
        comp.cue(t_rev + 1.2, "pop")
    comp.scene(t0, t1, inner, fade_in=.2, fade_out=.2)


ENTRIES = ("fromL", "drop", "fromR", "pop")
FACT_STYLE = {"leaves": (LEAVE_RED, "#fff"), "added": ("#fff", INK), "og": (ACCENT, INK)}


def _item_scene(comp, ctx: Ctx, it: dict, k: int, total: int, t0: float, t1: float, enter: str):
    dur = t1 - t0
    facts = _facts(it, ctx)
    col = RARITY.get(it["rarity"], "#777")
    size, nl = _fit(it["name"], TEXT_W - FIT_SLACK, 136, 100, 104, 70)
    name_y = ROW1_Y + 60
    name_bottom = name_y + nl * size * .92

    inner = tile_bg(it.get("tile_colors") or [], it["rarity"], t0) + _scrim()
    inner += _ghost(it["type"], 600, 330, t0, dur)
    t_pill = t0 + .4 + .08 * len(it["name"].split()) + .3      # after the name has landed
    inner += label(f'{it["rarity_label"]} {it["type"]}'.upper(), TEXT_X, ROW1_Y, LABEL, t_pill, _ink_on(col), 800,
                   bg=col, pad="6px 16px 5px", rot=-2, spacing=".12em")
    inner += _balanced(words(it["name"], NAME_X, name_y, size, t0 + .4, "#fff", .08, "slam", "left", TEXT_W),
                       it["name"], size, TEXT_W)
    if enter == "drop":
        comp.cue(t0 + .15 + .42, "slam")        # the landing; the wipe already whooshed
    elif enter == "pop":
        comp.cue(t0 + .15, "pop")
    comp.cue(t0 + .4, "slam")

    # The facts, as a row of crooked stickers under the name (all in the wide
    # band, clear of the button rail).
    row_bottom = name_bottom
    if facts:
        ss = 40
        while ss > 32 and sum(_stick_w(t, ss) for _, t in facts) + 22 * (len(facts) - 1) > TEXT_W:
            ss -= 2
        x, y = TEXT_X, name_bottom + 24
        for j, (kind, text) in enumerate(facts):
            bg, fg = FACT_STYLE[kind]
            ts = t0 + .95 + j * .22
            inner += _stick(text, x, y, ss, ts, bg, fg, (-3, 2.5, -2)[j % 3], pulse=(kind == "leaves"))
            comp.cue(ts, "pop")
            x += _stick_w(text, ss) + 22
        row_bottom = y + ss * 1.16 + 8

    # The price sits on a dark, slightly crooked card, so it reads on any tile
    # colour (Epic's yellows would swallow accent-coloured type).
    t_price = t0 + 1.4 + .15 * len(facts)
    price = int(it["price"])
    PS = 110
    sec = (it.get("section") or "").strip()
    sec_txt = f"SHOP SECTION · {sec}".upper() if sec else ""
    for cand in (sec_txt, sec.upper()):
        if cand and _inter_w(cand, LABEL, .1) + 70 <= CARD_MAXW:
            sec_txt = cand
            break
    else:
        sec_txt = ""                              # too long for the card even on its own: leave it out
    card_w = max(_price_w(price, PS) + 70, _inter_w(sec_txt, LABEL, .1) + 70 if sec_txt else 0)
    py = 64 if sec_txt else 20
    card_h = py + PS * .9 + 20
    body = label(sec_txt, 34, 20, LABEL, t_price - .05, "#A9AFB6", 800, spacing=".1em") if sec_txt else ""
    body += _from(t_price, price_roll(price, 32, py, PS, t_price, 1.0))
    comp.cue(t_price + 1.0, "cash")

    art_top = max(560, row_bottom + 24)
    inner += _cosmetic(ctx, it, art_top, CARD_BOTTOM - card_h - 16, t0 + .15, enter,
                       "float" if k % 2 else "sway", it["name"])
    inner += _card(card_w, card_h, col, t_price - .25, t_price + 1.05, body)
    inner += progress(t0, t1, k, total).replace(">ROUND ", ">ITEM ", 1)
    comp.scene(t0, t1, inner, fade_in=.2, fade_out=.2)


# ---------------------------------------------------------------- build

def build(ctx: Ctx):
    head, kicker = _headline_bundle(ctx)
    items = _pick_items(ctx, head, MAX_ITEMS)
    if not items and not head:
        return None             # an empty shop: nothing true to recap
    start = HOOK + (BUNDLE_LEN if head else 0)
    n = len(items)
    R = max(ITEM_LEN, min(7.5, (CONTENT_TARGET - start) / n)) if n else 0
    content_end = start + n * R
    comp = Comp(content_end + _pad(content_end))
    for rule in _CSS:
        comp.css(rule)

    offers = int(ctx.shop.get("item_count") or len(ctx.shop.get("items", [])))
    hook_pair = [i for i in items if i["type"] == "Outfit"][:2] or items[:2]
    a_item = hook_pair[0] if hook_pair else head
    b_item = hook_pair[1] if len(hook_pair) > 1 else (head if hook_pair else None)
    _hook_scene(comp, ctx, "TODAY'S SHOP", "EVERYTHING WORTH KNOWING IN 60 SECONDS",
                f"{offers} OFFERS", HOOK + .3, a_item, b_item)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop")

    rr = rng(ctx, 72)
    off = rr.randrange(len(ENTRIES))
    if head:
        _wipe(comp, HOOK, head.get("tile_colors") or [])
        _bundle_scene(comp, ctx, head, kicker, HOOK, HOOK + BUNDLE_LEN)
    for k, it in enumerate(items, 1):
        t0 = start + (k - 1) * R
        _wipe(comp, t0, it.get("tile_colors") or [RARITY.get(it["rarity"], "#444")])
        _item_scene(comp, ctx, it, k, n, t0, t0 + R, ENTRIES[(k + off) % len(ENTRIES)])

    _wipe(comp, content_end, ["#2b3200", "#0b0c05"])
    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    comp.cue(content_end + 1.1, "pop")
    outro_items = sorted(items, key=lambda i: i["type"] != "Outfit")[:3] or ([head] if head else [])
    _outro_scene(comp, ctx, content_end, comp.duration, "WHAT ARE YOU BUYING?", outro_items)
    comp.add(code_badge(.4))
    comp.add(disclosure())
    comp.add(PREP_JS)               # crops the art marked data-trim before frame 0
    comp.cues.sort()

    # ---- words for the post
    lines = []
    if head:
        hname = head.get("section") or _clean_name(head["name"])
        hsize = int(head.get("bundle_size") or 0)
        if head.get("discounted") and head["regular_price"] > head["price"]:
            lines += [f"🔥 BUNDLE DEAL: {hname} ({hsize} items)",
                      f"{head['price']:,} V-Bucks today · regular {head['regular_price']:,} · "
                      f"you save {head['regular_price'] - head['price']:,}", ""]
        else:
            lines += [f"🎁 BUNDLE: {hname} ({hsize} items) · {head['price']:,} V-Bucks", ""]
    lines.append("⭐ STANDOUT ITEMS")
    new_today = leaving = False
    for it in items:
        s = f"▸ {it['name']} · {it['rarity_label']} {it['type']} · {it['price']:,}"
        intro = it.get("introduction") or {}
        ch, se = str(intro.get("chapter") or ""), str(intro.get("season") or "")
        if ch in ("1", "2"):
            s += (" · OG" if ch == "1" else " ·") + f" Ch{ch}" + (f" S{se}" if se else "")
        if it.get("in_day") == ctx.day.isoformat():
            s += " 🆕"
            new_today = True
        if any(k == "leaves" for k, _ in _facts(it, ctx)):
            s += " ⏰"
            leaving = True
        lines.append(s)
    legend = "Prices in V-Bucks."
    if new_today:
        legend += " 🆕 = new today."
    if leaving:
        legend += f" ⏰ = leaves at the next reset ({ctx.reset_et})."
    lines += ["", legend]

    names = ([head.get("section") or _clean_name(head["name"])] if head else []) + [i["name"] for i in items]
    tags = _hashtags("itemshoptoday", *names)
    tags = BRAND_TAGS + [t for t in tags if t not in BRAND_TAGS]      # brand tags always lead

    title = f"Today's Fortnite Item Shop — {ctx.day_label}"
    yt = f"Fortnite Item Shop Today ({ctx.day_label}): Everything Worth Knowing #shorts"
    if head and head.get("discounted") and head["regular_price"] > head["price"]:
        cand = (f"Fortnite Item Shop {ctx.day_label}: {head.get('section') or _clean_name(head['name'])} "
                f"Bundle Saves {head['regular_price'] - head['price']:,} V-Bucks #shorts")
        if len(cand) <= 100:
            yt = cand
    return Video(
        FORMAT, comp,
        title=title[:60],
        yt_title=yt,
        caption=_caption(f"🛒 FORTNITE ITEM SHOP — {ctx.day_label}\n"
                         f"{offers} offers today. Here's everything worth knowing 👇",
                         "\n".join(lines), "What are you buying?", tags),
        hashtags=tags)
