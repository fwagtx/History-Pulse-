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
"""

from cc_fmt_last_chance import _fit, _from, _members, _mon_d, _shown_name
from cc_formats import Ctx, Video, _pad, _hook_scene, _outro_scene, _hashtags, _caption, num
from cc_motion import (ACCENT, RARITY, Comp, burst, character, code_badge, disclosure, esc, label,
                       price_roll, progress, sticker, style_anim, an, tile_bg, words)

FORMAT = "new_this_week"
HOOK = 3.0
MAX_OFFERS = 8
MIN_OFFERS = 4
CONTENT = 52.0          # the offers share this much time, 7 to 12 seconds each


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
        return "Includes " + ", ".join(shown) + (f" and {more} more" if more else "")
    return (it.get("description") or "").strip()


def build(ctx: Ctx):
    offers = _new(ctx)
    if not offers:
        return None
    n = len(offers)
    R = max(7.0, min(12.0, CONTENT / n))
    content_end = HOOK + n * R
    comp = Comp(content_end + _pad(content_end))
    outfits = [i for i in offers if i.get("type") == "Outfit"] or offers
    a = outfits[0]
    b = outfits[1] if len(outfits) > 1 else next(i for i in offers if i is not a)
    _hook_scene(comp, ctx, "NEW IN THE SHOP", "EVERYTHING EPIC TAGGED NEW TODAY", f"{n} NEW", HOOK + .3, a, b)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop")

    for k, it in enumerate(offers, 1):
        t0 = HOOK + (k - 1) * R
        cols = it.get("tile_colors") or [RARITY.get(it["rarity"], "#3a3a44")]
        inner = tile_bg(cols, it["rarity"], t0)
        inner += sticker("NEW", 60, 310, 104, t0 + .2, rot=-7)
        inner += character(ctx.art(it), 540, 810, 600, t0 + .1, "pop", .6, "float", it["rarity"], _shown_name(it))
        inner += _from(t0 + .25, burst(540, 720, t0 + .25, ctx.seed + k, n=18))
        since = _since(it, ctx)
        if since:
            inner += label(since, 64, 452, 30, t0 + .45, "#fff", 800, bg="rgba(10,10,11,.8)", pad="8px 18px")
        name = _shown_name(it)
        size, lines = _fit(name, 900, big=96, one_min=70, two_max=76, small=56)
        inner += words(name, 60, 1120, size, t0 + .5, "#fff", .06, "slam", "left", 900)
        y = 1120 + size * .92 * lines + 16
        kind = "BUNDLE" if it.get("is_bundle") else f"{it.get('rarity_label') or it['rarity']} {it['type']}"
        inner += label(kind.upper(), 64, y, 32, t0 + .7, ACCENT, 800)
        about = _about(it)
        if about:
            inner += (f'<div class="abs" style="left:64px;top:{y + 48:.0f}px;width:820px;font-size:28px;'
                      f'font-weight:600;line-height:1.3;color:rgba(255,255,255,.9);max-height:74px;overflow:hidden;'
                      f'{style_anim(an("rise", t0 + .9, .45))}">“{esc(about)}”</div>')
        inner += _from(t0 + 1.2, price_roll(int(it["price"]), 600, 336, 66, t0 + 1.2, .8))
        inner += progress(t0, t0 + R, k, n).replace(f"ROUND {k}/{n}", f"NEW {k}/{n}")
        comp.scene(t0, t0 + R, inner, fade_in=.25, fade_out=.25)
        comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .2, "pop"); comp.cue(t0 + .5, "slam")
        comp.cue(t0 + 2.0, "cash")

    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    _outro_scene(comp, ctx, content_end, comp.duration, "WHICH NEW ONE ARE YOU GETTING?",
                 (outfits + [o for o in offers if o not in outfits])[:3])
    comp.add(code_badge(.4))
    comp.add(disclosure())

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
