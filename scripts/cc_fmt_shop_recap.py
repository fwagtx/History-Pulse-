"""
Shop Recap -- slot 1, every day.

    0:00  hook      TODAY'S SHOP / N OFFERS, two real cosmetics sliding in
    0:03  bundle    the bundle with the biggest saving vs Epic's regular price
                    (or the priciest bundle when nothing is discounted): art drops
                    in, members scroll past on a band, Epic's regular price gets
                    struck through, a 3-second countdown, then today's price rolls
                    up and the SAVE sticker slaps on
    0:12  items     6-7 single cosmetics, ~6s each: tile-coloured stage, the
                    cosmetic enters and idles, name slams in, rarity/type pill,
                    price rolls up, and every truthful tag that applies
                    (LEAVES AT RESET / ADDED SEP 22 / OG · CH2 S1)
    0:54  outro     code BAD + "WHAT ARE YOU BUYING?"

Every claim comes straight from the shop row. Singles are never shown as
discounted; only bundles carry a regular price above today's price, and that is
called "regular price", nothing else. A dark wipe carries each cut so the video
reads as one piece rather than a slideshow.
"""

from datetime import date, timedelta

from cc_formats import (Ctx, Video, bundles, singles, rng, _pad, _hook_scene,
                        _outro_scene, _hashtags, _caption, BRAND_TAGS)
from cc_motion import (ACCENT, INK, RARITY, W, RAIL_TOP, Comp,
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

_CSS = [
    "@keyframes srwipe{from{transform:translateX(-2760px) skewX(-14deg)}"
    "to{transform:translateX(2040px) skewX(-14deg)}}",      # fully covers the frame at mid-sweep
    "@keyframes srdrift{from{transform:translateX(80px)}to{transform:translateX(-80px)}}",
    "@keyframes srmarq{from{transform:translateX(0)}to{transform:translateX(-1300px)}}",
    "@keyframes srband{from{transform:scaleX(0)}to{transform:scaleX(1)}}",
    "@keyframes srshine{from{transform:translateX(-160%) skewX(-20deg)}to{transform:translateX(420%) skewX(-20deg)}}",
    # _hook_scene's sub pill is centred and sized for shorter lines: at 36px this
    # format's sub is 880px wide and its right edge pokes 20px under TikTok's
    # like/comment rail. Scoped to that one pill; matches nothing else here.
    '.scene div[style*="top:1330px;"] > div[style*="padding:14px 26px"]{font-size:33px !important}',
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
    """Giant outlined type drifting behind the cosmetic: depth, not information."""
    return (f'<div class="abs d" style="left:-30px;top:{y:.0f}px;white-space:nowrap;font-size:{size:.0f}px;'
            f'color:transparent;-webkit-text-stroke:3px rgba(255,255,255,.16);'
            f'{style_anim(an("srdrift", t0, dur, "linear"))}">{esc(text)}</div>')


def _tag(text: str, right: float, y: float, size: float, start: float, bg: str, fg: str,
         rot: float, pulse: bool = False) -> str:
    """A right-anchored crooked sticker; `pulse` makes it breathe after landing."""
    pop = style_anim(an("pop", start, .55, EASE_BACK))
    breathe = style_anim(an("pulse", start + .6, 1.1, "ease-in-out", "infinite")) if pulse else ""
    return (f'<div class="abs" style="right:{right:.0f}px;top:{y:.0f}px;transform:rotate({rot}deg)">'
            f'<div style="transform-origin:50% 50%;{breathe}"><div class="d" style="background:{bg};color:{fg};'
            f'font-size:{size:.0f}px;padding:.16em .42em .1em;border-radius:10px;white-space:nowrap;'
            f'box-shadow:0 10px 0 rgba(0,0,0,.35);{pop}">{esc(text)}</div></div></div>')


def _marquee(names: list, y: float, start: float, dur: float) -> str:
    """The bundle's members scrolling past on a tilted band behind the art."""
    seen, uniq = set(), []
    for n in names:
        if n and n.lower() not in seen:
            seen.add(n.lower())
            uniq.append(n)
    if not uniq:
        return ""
    sep = f'<span style="color:{ACCENT};margin:0 .5em">/</span>'
    one = (f'<span style="color:{ACCENT};margin-right:.6em">INCLUDES</span>'
           + sep.join(esc(n) for n in uniq) + sep)
    copies = max(2, int(3000 / max(1.0, (_em(" / ".join(uniq)) + 3) * 40)) + 1)
    band_in = style_anim(an("srband", start, .45, "cubic-bezier(.2,.8,.2,1)"))
    return (f'<div class="abs" style="left:-140px;top:{y:.0f}px;width:{W + 280}px;height:72px;'
            f'transform:rotate(-4deg)"><div style="position:absolute;inset:0;overflow:hidden;'
            f'background:rgba(10,10,11,.86);border-top:4px solid {ACCENT};border-bottom:4px solid {ACCENT};'
            f'transform-origin:0 50%;{band_in}">'
            f'<div class="d" style="position:absolute;left:180px;top:12px;white-space:nowrap;font-size:42px;'
            f'color:#fff;{style_anim(an("srmarq", start, dur, "linear"))}">{one * copies}</div></div></div>')


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


# ---------------------------------------------------------------- scenes

def _bundle_scene(comp, ctx: Ctx, b: dict, kicker: str, t0: float, t1: float):
    dur = t1 - t0
    title = b.get("section") or _clean_name(b["name"])
    price, reg = int(b["price"]), int(b.get("regular_price") or b["price"])
    discounted = bool(b.get("discounted")) and reg > price
    size, nl = _fit(title, 960, 150, 104, 116, 72)
    name_bottom = 382 + nl * size * .92

    inner = tile_bg(b.get("tile_colors") or [], b["rarity"], t0) + _scrim()
    inner += _ghost("BUNDLE", 540, 340, t0, dur)
    inner += _marquee(b.get("member_names") or [], 745, t0 + 1.2, dur - 1.2)
    art_top = max(name_bottom + 24, 560)
    art_h = min(680, 1190 - art_top)
    inner += character(ctx.art(b), 590, art_top + art_h / 2, art_h, t0 + .15, "drop", .8, "float",
                       b["rarity"], title)
    inner += label(kicker, 60, 326, 28, t0 + .1, ACCENT, 800, spacing=".22em")
    inner += words(title, 60, 382, size, t0 + .3, "#fff", .1, "slam", "left", 960)
    inner += _tag(f"{int(b.get('bundle_size') or 0)} ITEMS", 60, art_top + 10, 56, t0 + .95, "#fff", INK, 6)
    comp.cue(t0 + .3, "slam"); comp.cue(t0 + .63, "slam")
    comp.cue(t0 + .95, "pop")

    # The price tag: Epic's regular price struck through, a 3-second countdown,
    # then today's price rolls up. The whole card sits slightly crooked.
    t_panel, t_strike, t_cd, t_rev = t0 + 1.6, t0 + 2.55, t0 + 3.0, t0 + 6.0
    ch = 340 if discounted else 262
    card = (f'<div class="abs" style="left:0;top:0;width:620px;height:{ch}px;border-radius:24px;'
            f'background:rgba(10,10,11,.9);border:3px solid rgba(255,255,255,.12);'
            f'box-shadow:0 18px 0 rgba(0,0,0,.35),0 30px 60px rgba(0,0,0,.45)"></div>'
            f'<div class="abs" style="left:0;top:0;width:620px;height:12px;border-radius:24px 24px 0 0;'
            f'background:{ACCENT}"></div>')
    if discounted:
        card += label("REGULAR PRICE", 34, 36, 24, t0 + 1.9, "#9AA0A6", 800, spacing=".22em")
        strike = style_anim(an("strike", t_strike, .3, "cubic-bezier(.6,0,.3,1)"))
        card += (f'<div class="abs d" style="left:34px;top:74px;font-size:84px;color:rgba(255,255,255,.88);'
                 f'{style_anim(an("rise", t0 + 2.0, .45))}"><span style="position:relative;display:inline-block;'
                 f'white-space:nowrap">{reg:,}<span style="font-size:.38em;opacity:.75;margin-left:.2em">V-BUCKS</span>'
                 f'<span style="position:absolute;left:-10px;right:-10px;top:44%;height:10px;transform:rotate(-4deg)">'
                 f'<span style="display:block;height:100%;border-radius:6px;background:{LEAVE_RED};'
                 f'transform-origin:0 50%;box-shadow:0 3px 0 rgba(0,0,0,.4);{strike}"></span></span></span></div>')
        card += (f'<div class="abs" style="left:34px;right:34px;top:178px;border-top:3px dashed rgba(255,255,255,.2);'
                 f'{style_anim(an("fadein", t0 + 2.2, .3))}"></div>')
        comp.cue(t_strike, "slam")
        row2 = 198
    else:
        card += label(f"{int(b.get('bundle_size') or 0)} ITEMS IN ONE OFFER", 34, 36, 24, t0 + 1.9,
                      "#9AA0A6", 800, spacing=".22em")
        row2 = 84
    card += label("TODAY'S PRICE", 34, row2, 24, t_cd - .1, ACCENT, 800, spacing=".22em")
    card += _fade_between(f'<div class="abs d" style="left:34px;top:{row2 + 36}px;font-size:104px;'
                          f'color:{ACCENT};opacity:.9;{style_anim(an("pulse", t_cd, 1, "ease-in-out", "3"))}">???</div>',
                          t_cd - .1, t_rev)
    card += _fade_between(countdown(3, 520, row2 + 86, 128, t_cd), t_cd - .1, t_rev)
    card += _from(t_rev, price_roll(price, 34, row2 + 36, 104, t_rev, 1.1))
    for s in range(3):
        comp.cue(t_cd + s, "tick")
    comp.cue(t_rev, "reveal"); comp.cue(t_rev + 1.1, "cash")
    inner += (f'<div class="abs" style="left:50px;top:{1444 - ch}px;width:620px;height:{ch}px;transform:rotate(-2.5deg)">'
              f'<div class="abs" style="left:0;top:0;width:620px;height:{ch}px;{style_anim(an("rise", t_panel, .5))}">'
              f'{card}</div></div>')
    comp.cue(t_panel, "whoosh")
    if discounted:
        inner += sticker(f"SAVE {reg - price:,}", 392, 1056, 64, t_rev + 1.15, rot=7)
        inner += _from(t_rev + 1.1, burst(250, 1384, t_rev + 1.1, ctx.seed))
        comp.cue(t_rev + 1.2, "pop")
    comp.scene(t0, t1, inner, fade_in=.2, fade_out=.2)


ENTRIES = ("fromL", "drop", "fromR", "pop")


def _item_scene(comp, ctx: Ctx, it: dict, k: int, total: int, t0: float, t1: float, enter: str):
    dur = t1 - t0
    facts = _facts(it, ctx)
    col = RARITY.get(it["rarity"], "#777")
    size, nl = _fit(it["name"], 960, 150, 100, 118, 70)
    name_top = 394
    name_bottom = name_top + nl * size * .92

    inner = tile_bg(it.get("tile_colors") or [], it["rarity"], t0) + _scrim()
    inner += _ghost(it["type"], 548, 330, t0, dur)
    art_h = 660
    cx = 450 if facts else 540
    inner += character(ctx.art(it), cx, 1285 - art_h / 2, art_h, t0 + .15, enter, .7,
                       "float" if k % 2 else "sway", it["rarity"], it["name"])
    t_pill = t0 + .4 + .08 * len(it["name"].split()) + .3      # after the name has landed
    inner += label(f'{it["rarity_label"]} {it["type"]}'.upper(), 60, 330, 26, t_pill, _ink_on(col), 800,
                   bg=col, pad="8px 16px 7px", rot=-2, spacing=".14em")
    inner += words(it["name"], 60, name_top, size, t0 + .4, "#fff", .08, "slam", "left", 960)
    if enter == "drop":
        comp.cue(t0 + .15 + .42, "slam")        # the landing; the wipe already whooshed
    elif enter == "pop":
        comp.cue(t0 + .15, "pop")
    comp.cue(t0 + .4, "slam")

    # Stickers: a right-hand column that must end above the like/comment rail
    # (y 880), so they tighten up under a two-line name.
    y = max(name_bottom + 40, 590)
    n_f = len(facts)
    for ss, step in ((50, 88), (46, 80), (42, 72)):
        if y + (n_f - 1) * step + ss * 1.5 <= RAIL_TOP - 6:
            break
    style = {"leaves": (LEAVE_RED, "#fff"), "added": ("#fff", INK), "og": (ACCENT, INK)}
    rots = (5, -4, 3)
    for j, (kind, text) in enumerate(facts):
        bg, fg = style[kind]
        ts = t0 + .95 + j * .22
        inner += _tag(text, 56 + (j % 2) * 22, y, ss, ts, bg, fg, rots[j % 3], pulse=(kind == "leaves"))
        comp.cue(ts, "pop")
        y += step

    # The price sits on a dark, slightly crooked tag, so it reads on any tile
    # colour (Epic's yellows would swallow accent-coloured type).
    t_price = t0 + 1.4 + .15 * len(facts)
    price = int(it["price"])
    sec = (it.get("section") or "").strip()
    sec_txt = f"SHOP SECTION · {sec.upper()}" if sec else ""
    if len(sec_txt) * 16.8 > 780:                   # very long section: drop the prefix
        sec_txt = sec.upper()
    sec_size = min(22, 22 * 780 / max(1, len(sec_txt) * 16.8))   # and shrink if still too long
    card_w = max(_price_w(price, 118) + 64, len(sec_txt) * 16.8 * sec_size / 22 + 68 if sec_txt else 0)
    card_h = 190 if sec_txt else 146
    py = 58 if sec_txt else 18
    card = (f'<div class="abs" style="left:0;top:0;width:{card_w:.0f}px;height:{card_h}px;border-radius:22px;'
            f'background:rgba(10,10,11,.88);border:3px solid rgba(255,255,255,.12);overflow:hidden;'
            f'box-shadow:0 14px 0 rgba(0,0,0,.35)">{_shine(t_price + 1.05)}</div>'
            f'<div class="abs" style="left:0;top:0;width:10px;height:{card_h}px;border-radius:22px 0 0 22px;'
            f'background:{col}"></div>')
    if sec_txt:
        card += label(sec_txt, 34, 22, sec_size, t_price - .05, "#9AA0A6", 800, spacing=".16em")
    card += _from(t_price, price_roll(price, 32, py, 118, t_price, 1.0))
    inner += (f'<div class="abs" style="left:46px;top:{1458 - card_h}px;width:{card_w:.0f}px;height:{card_h}px;'
              f'transform:rotate(-2deg)"><div class="abs" style="left:0;top:0;width:{card_w:.0f}px;height:{card_h}px;'
              f'{style_anim(an("rise", t_price - .25, .45))}">{card}</div></div>')
    comp.cue(t_price + 1.0, "cash")
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
