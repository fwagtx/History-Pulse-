"""
NEW IN THE SHOP -- slot 3 (value), and a stand-in for the recap in slot 1, for
@usecodebad: everything Epic tagged "New" in today's shop.

    0:00  hook      NEW IN THE SHOP / N NEW, two of the new items
    0:03  offers    each: Epic's NEW tag, the cosmetic, its name, type, Epic's
                    own description (or what a bundle includes), the price, and
                    how long it has been listed
    0:55  outro     code BAD + "WHICH NEW ONE ARE YOU GETTING?"

Truth rules this format keeps:
  - an offer is here only when Epic's own tile banner on it says "New"
    (banner.backendValue "New"); that's all "NEW" means on screen.
  - the description is the item's own `description`; a bundle's contents come
    from `member_names`.
  - "added today" / "in the shop since Sep 22" come from `in_day`; prices from `price`.
It never says "first time ever", "returning" or anything about popularity.

Layout: everything a viewer reads sits in the apps' safe box (cc_safe). The NEW
tag, how long it's been listed and the price make a header in the wide top band
(under the code badge and its #EpicPartner tag); the cosmetic stands in the band
beside the button rail (x 60-900); the name, type and description sit under it,
anchored to the bottom of the box, so a short text block gives the art more room.
"""

import re

from cc_fmt_shop_recap import FIT_SLACK, _balanced, _clean_name, _fit, _from, _mon_d, _price_w
from cc_formats import Ctx, Video, _pad, _hook_scene, _outro_scene, _hashtags, _caption, num
from cc_looks import PREP_JS
from cc_motion import (ACCENT, RARITY, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, Comp, burst,
                       character, code_badge, disclosure, esc, label, price_roll, progress, sticker,
                       style_anim, an, tile_bg, words, EASE_BACK)

FORMAT = "new_this_week"
HOOK = 3.0
MAX_OFFERS = 8
MIN_OFFERS = 4
CONTENT = 52.0          # the offers share this much time, 7 to 12 seconds each

HEAD_Y = 372                                # the header row, under the #EpicPartner tag
TEXT_X = SAFE_LEFT + 4                      # 64
NAME_X = SAFE_LEFT + 2                      # 62 (Anton's side bearing)
TEXT_W = SAFE_RIGHT - 6 - TEXT_X            # 830: the text under the art sits beside the rail
BLOCK_BOTTOM = SAFE_BOTTOM - 26             # 1394: where the text block ends
ART_X = (SAFE_LEFT + SAFE_RIGHT) / 2        # 480
ART_MAXW = 780                              # x 1.06 at the end of the push-in: still inside x 60-900
PUSH = 1.06
NEW_SIZE = 92
DESC = 30                                   # description: supporting text, 30 px
DESC_LH = 1.3
DESC_LINES = 3

# Inter 600 advance widths (em), measured in the render browser: for wrapping
# the description into whole lines.
_INTER600 = {
    "a": .541, "b": .587, "c": .544, "d": .587, "e": .553, "f": .309, "g": .587, "h": .573, "i": .232,
    "j": .233, "k": .536, "l": .232, "m": .869, "n": .573, "o": .57, "p": .587, "q": .587, "r": .361,
    "s": .505, "t": .314, "u": .573, "v": .54, "w": .796, "x": .527, "y": .54, "z": .508, "A": .704,
    "B": .643, "C": .725, "D": .697, "E": .599, "F": .572, "G": .734, "H": .715, "I": .25, "J": .553,
    "K": .668, "L": .55, "M": .882, "N": .72, "O": .748, "P": .625, "Q": .748, "R": .644, "S": .64,
    "T": .627, "U": .704, "V": .707, "W": .996, "X": .68, "Y": .674, "Z": .627, "0": .638, "1": .38,
    "2": .586, "3": .613, "4": .644, "5": .592, "6": .606, "7": .556, "8": .604, "9": .606, " ": .226,
    "·": .236, "'": .266, "’": .214, "&": .634, "-": .439, ":": .236, ".": .236, ",": .236, "!": .238,
    "?": .553, "(": .321, ")": .321, "/": .351, "#": .617, "+": .646, "“": .402, "”": .397, "…": .709,
    "—": 1.0, "\u00a0": .226,
}


def _w600(text: str, size: float) -> float:
    return sum(_INTER600.get(ch, .62) for ch in text) * size


def _members(it: dict) -> list:
    seen, out = set(), []
    for n in it.get("member_names") or []:
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out


def _shown_name(it: dict) -> str:
    return _clean_name(it["name"]) if it.get("is_bundle") else it["name"]


def _new(ctx: Ctx) -> list:
    rows = [i for i in ctx.shop.get("items", []) if i.get("banner") == "New" and int(i.get("price") or 0) > 0]
    with_art = [i for i in rows if ctx.art(i)]
    rows = with_art if len(with_art) >= MIN_OFFERS else rows
    # Outfits first, then the rest; the priciest first within each.
    rows.sort(key=lambda i: (bool(i.get("is_bundle")), i.get("type") != "Outfit", -int(i["price"])))
    out, seen = [], set()
    for it in rows:
        key = _shown_name(it).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
        if len(out) == MAX_OFFERS:
            break
    return out if len(out) >= MIN_OFFERS else []


def _since(it: dict, ctx: Ctx) -> str:
    d = it.get("in_day") or ""
    if not d:
        return ""
    return "ADDED TODAY" if d == ctx.day.isoformat() else f"IN THE SHOP SINCE {_mon_d(d).upper()}"


def _about(it: dict) -> str:
    """Epic's description for a single; what a bundle includes."""
    if it.get("is_bundle"):
        names = _members(it)
        shown = names[:4]
        more = len(names) - len(shown)
        return "Includes " + ", ".join(shown) + (f" and {more}\u00a0more" if more else "")
    return (it.get("description") or "").strip()


def _wrap(text: str, size: float, width: float, max_lines: int, quote: bool = True) -> list:
    """`text` (in quotes when they're Epic's own words), wrapped into whole lines
    of `width`. Past `max_lines` it ends at a whole word with an ellipsis, never
    mid-word or clipped."""
    text = re.sub(r"[ \t\r\n]+", " ", text).strip().strip('"“”')
    words_ = [w for w in text.split(" ") if w.strip()]             # keeps "10\u00a0more" whole
    if not words_:
        return []
    op, cl = ("“", "”") if quote else ("", "")
    lines, cur = [], ""
    for i, w in enumerate(words_):
        piece = (op if i == 0 else "") + w + (cl if i == len(words_) - 1 else "")
        trial = f"{cur} {piece}" if cur else piece
        if cur and _w600(trial, size) > width:
            lines.append(cur)
            cur = piece
        else:
            cur = trial
    lines.append(cur)
    if len(lines) <= max_lines:
        # No single word left alone on the last line: bring one down to join it.
        prev = lines[-2].split(" ") if len(lines) > 1 else []
        if len(prev) >= 3 and len(lines[-1].split(" ")) == 1:
            lines[-2:] = [" ".join(prev[:-1]), f"{prev[-1]} {lines[-1]}"]
        return lines
    keep = lines[:max_lines]
    last = keep[-1].split()
    while last and _w600(" ".join(last) + "…" + cl, size) > width:
        last.pop()
    keep[-1] = (" ".join(last) if last else keep[-1].split()[0]).rstrip(",.;:") + "…" + cl
    return keep


def _scrim() -> str:
    """Darkens the top band and the bottom text block, so white type holds on pale tiles."""
    return ('<div class="full" style="background:linear-gradient(180deg,rgba(0,0,0,.42) 0,'
            'rgba(0,0,0,.12) 22%,rgba(0,0,0,0) 32%,rgba(0,0,0,0) 50%,rgba(0,0,0,.5) 64%,'
            'rgba(0,0,0,.62) 100%)"></div>')


def _offer_scene(comp: Comp, ctx: Ctx, it: dict, k: int, n: int, t0: float, t1: float):
    cols = it.get("tile_colors") or [RARITY.get(it["rarity"], "#3a3a44")]
    inner = tile_bg(cols, it["rarity"], t0) + _scrim()
    name = _shown_name(it)

    # Header: Epic's NEW tag and how long it's been listed on the left, the price
    # on the right.
    inner += sticker("NEW", TEXT_X, HEAD_Y, NEW_SIZE, t0 + .2, rot=-6)
    since = _since(it, ctx)
    since_bottom = HEAD_Y + NEW_SIZE * 1.16 + 8
    if since:
        inner += label(since, TEXT_X + 4, since_bottom + 12, 30, t0 + .45, "#fff", 800,
                       bg="rgba(10,10,11,.82)", pad="7px 16px 6px", spacing=".06em")
        since_bottom += 12 + 50
    # The price on a dark tag, pinned crooked to the top-right corner.
    price = int(it["price"])
    ps = 76
    tag_w, tag_h = _price_w(price, ps) + 52, ps * .9 + 30
    inner += (f'<div class="abs" style="left:{SAFE_RIGHT_TOP - 22 - tag_w:.0f}px;top:{HEAD_Y + 8}px;width:{tag_w:.0f}px;'
              f'height:{tag_h:.0f}px;transform:rotate(4deg)"><div class="abs" style="inset:0;border-radius:18px;'
              f'background:rgba(10,10,11,.86);border:3px solid rgba(255,255,255,.12);border-bottom:6px solid {ACCENT};'
              f'box-shadow:0 10px 0 rgba(0,0,0,.3);{style_anim(an("pop", t0 + 1.0, .5, EASE_BACK))}">'
              + _from(t0 + 1.2, price_roll(price, 24, 14, ps, t0 + 1.2, .8)) + "</div></div>")

    # The text block, bottom-anchored: name, what it is, Epic's own words.
    size, lines = _fit(name, TEXT_W - FIT_SLACK, big=92, one_min=68, two_max=76, small=52)
    kind = "BUNDLE" if it.get("is_bundle") else f"{it.get('rarity_label') or it['rarity']} {it['type']}"
    about = _wrap(_about(it), DESC, TEXT_W - FIT_SLACK, DESC_LINES, quote=not it.get("is_bundle"))
    name_h = size * .92 * lines
    block = name_h + 14 + 40 + (12 + len(about) * DESC * DESC_LH if about else 0)
    top = BLOCK_BOTTOM - block
    inner += _balanced(words(name, NAME_X, top, size, t0 + .5, "#fff", .06, "slam", "left", TEXT_W),
                       name, size, TEXT_W)                             # two even lines, no orphan
    y = top + name_h + 14
    inner += label(kind.upper(), TEXT_X, y, 32, t0 + .7, ACCENT, 800, spacing=".06em")
    if about:
        inner += (f'<div class="abs" style="left:{TEXT_X}px;top:{y + 52:.0f}px;width:{TEXT_W}px;font-size:{DESC}px;'
                  f'font-weight:600;line-height:{DESC_LH};color:rgba(255,255,255,.92);white-space:nowrap;'
                  f'text-shadow:0 2px 10px rgba(0,0,0,.6);{style_anim(an("rise", t0 + .9, .45))}">'
                  + "<br>".join(esc(ln) for ln in about) + "</div>")

    # The cosmetic fills the space between the header and the text block, and
    # the camera pushes in on it slowly for the whole scene, so a long scene
    # never sits still. data-trim (cc_looks.PREP_JS) crops Fortnite's square art
    # to the cosmetic. The gaps leave room for the push (x1.06 about the centre).
    art_top, art_bottom = max(since_bottom + 30, HEAD_Y + 150), top - 40
    cy = (art_top + art_bottom) / 2
    push = style_anim(an("ntwpush", t0, t1 - t0, "linear"))
    inner += (f'<div class="full" style="transform-origin:{ART_X:.0f}px {cy:.0f}px;{push}">'
              + character(ctx.art(it), ART_X, cy, art_bottom - art_top, t0 + .1, "pop", .6, "float",
                          it["rarity"], name, maxw=ART_MAXW).replace('<img class="art"', '<img class="art" data-trim', 1)
              + "</div>")
    inner += _from(t0 + .25, burst(ART_X, cy - 60, t0 + .25, ctx.seed + k, n=18))
    inner += progress(t0, t1, k, n).replace(f"ROUND {k}/{n}", f"NEW {k}/{n}")
    # Held .3 s past its slot while the next offer (or the end card) fades in
    # over it: a cross-fade, not a dip to black.
    comp.scene(t0, t1 + .3, inner, fade_in=.25, fade_out=.05)
    comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .2, "pop"); comp.cue(t0 + .5, "slam")
    comp.cue(t0 + 2.0, "cash")


def build(ctx: Ctx):
    offers = _new(ctx)
    if not offers:
        return None
    n = len(offers)
    R = max(7.0, min(12.0, CONTENT / n))
    content_end = HOOK + n * R
    comp = Comp(content_end + _pad(content_end))
    comp.css(f"@keyframes ntwpush{{from{{transform:scale(1)}}to{{transform:scale({PUSH})}}}}")
    outfits = [i for i in offers if i.get("type") == "Outfit"] or offers
    a = outfits[0]
    b = outfits[1] if len(outfits) > 1 else next(i for i in offers if i is not a)
    _hook_scene(comp, ctx, "NEW IN THE SHOP", "EVERYTHING EPIC TAGGED NEW TODAY", f"{n} NEW", HOOK + .3, a, b)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop")

    for k, it in enumerate(offers, 1):
        t0 = HOOK + (k - 1) * R
        _offer_scene(comp, ctx, it, k, n, t0, t0 + R)

    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    _outro_scene(comp, ctx, content_end, comp.duration, "WHICH NEW ONE ARE YOU GETTING?",
                 (outfits + [o for o in offers if o not in outfits])[:3])
    comp.add(code_badge(.4))
    comp.add(disclosure())
    comp.add(PREP_JS)               # crops the art marked data-trim before frame 0

    body = "\n".join(f"{num(k)} {_shown_name(it)} · {'Bundle' if it.get('is_bundle') else it['type']} · "
                     f"{int(it['price']):,} V-Bucks" for k, it in enumerate(offers, 1))
    tags = _hashtags("newfortniteskins", "newinshop", a["name"])
    return Video(
        FORMAT, comp,
        title=f"New in the Fortnite Item Shop — {ctx.day_label}",
        yt_title=f"New in the Fortnite Item Shop: {ctx.day_label} #shorts",
        caption=_caption(f"🆕 NEW IN THE SHOP — Fortnite Item Shop, {ctx.day_label}\n"
                         f"Everything Epic tagged NEW in today's shop 👇",
                         body, "Which new one are you getting? Tell us below", tags),
        hashtags=tags)
