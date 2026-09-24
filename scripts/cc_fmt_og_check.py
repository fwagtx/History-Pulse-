"""
OG CHECK -- slot 3 (value) for @usecodebad: the oldest items in today's shop.

    0:00  hook      OG CHECK / HOW OLD IS TODAY'S SHOP?, two of the items
    0:03  items     up to 8 singles, counting down to the oldest: the season Epic
                    says it was introduced in slams in big, the cosmetic enters,
                    its name, type and today's price
    0:55  outro     code BAD + "HOW OG IS YOUR LOCKER?"

Truth rules this format keeps:
  - "Introduced in Chapter 1, Season 3" is Epic's own `introduction` text for the
    item; the order is its season number in release order (Chapter 2 Remix sits
    between Chapters 5 and 6).
  - "oldest in today's shop" compares only today's single offers, by that order.
  - prices are the row's `price`.
It never says how many years old anything is, how rare it is, or that it's "back".
"""

from cc_fmt_last_chance import _fit, _from
from cc_formats import Ctx, Video, singles, _pad, _hook_scene, _outro_scene, _hashtags, _caption, num
from cc_motion import (ACCENT, RARITY, W, Comp, an, burst, character, code_badge, disclosure, label,
                       price_roll, progress, sticker, style_anim, tile_bg, words)

FORMAT = "og_check"
HOOK = 3.0
R = 6.6
MAX_ITEMS = 8
MIN_ITEMS = 6
MIN_AGE = 4          # at least this many seasons older than the newest item in the shop


def _order(it: dict) -> int:
    return int((it.get("introduction") or {}).get("order") or 0)


def _season(it: dict) -> tuple:
    """('CHAPTER 1', 'SEASON 3') from Epic's own text: 'Introduced in Chapter 1, Season 3.'"""
    text = ((it.get("introduction") or {}).get("text") or "").strip().rstrip(".")
    text = text.replace("Introduced in ", "")
    if ", " not in text:
        return ()
    ch, se = text.split(", ", 1)
    return ch.upper(), se.upper()


def _pick(ctx: Ctx) -> list:
    rows = [i for i in singles(ctx) if _order(i) and _season(i)]
    if not rows:
        return []
    newest = max(_order(i) for i in rows)
    old = [i for i in rows if _order(i) <= newest - MIN_AGE]
    old.sort(key=lambda i: (_order(i), i["type"] != "Outfit", -int(i["price"])))
    out, seen = [], set()
    for it in old:
        if it["name"].lower() in seen:
            continue
        seen.add(it["name"].lower())
        out.append(it)
        if len(out) == MAX_ITEMS:
            break
    return out if len(out) >= MIN_ITEMS else []


def build(ctx: Ctx):
    picks = _pick(ctx)
    if not picks:
        return None
    n = len(picks)
    show = list(reversed(picks))            # count down: the oldest comes last
    content_end = HOOK + n * R
    comp = Comp(content_end + _pad(content_end))
    outfits = [i for i in picks if i["type"] == "Outfit"] or picks
    _hook_scene(comp, ctx, "OG CHECK", "THE OLDEST ITEMS IN TODAY'S SHOP", "HOW OLD?", HOOK + .3,
                outfits[0], outfits[1] if len(outfits) > 1 else picks[1])
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop")

    for k, it in enumerate(show, 1):
        t0 = HOOK + (k - 1) * R
        rank = n - k + 1
        last = rank == 1
        ch, se = _season(it)
        cols = it.get("tile_colors") or [RARITY.get(it["rarity"], "#3a3a44")]
        inner = tile_bg(cols, it["rarity"], t0)
        inner += label("INTRODUCED IN", 60, 300, 30, t0, ACCENT, 800, anim="none", spacing=".18em")
        inner += words(ch, 60, 346, 104, t0 + .15, "#fff", .06, "slam", "left", 700)
        inner += words(se, 60, 450, 104, t0 + .3, ACCENT, .06, "slam", "left", 700)
        inner += sticker(f"#{rank}", 790, 330, 110, t0 + .35, rot=7)
        inner += character(ctx.art(it), 560, 860, 560, t0 + .1, "pop", .6, "float", it["rarity"], it["name"])
        size, lines = _fit(it["name"], 900, big=96, one_min=70, two_max=76, small=56)
        inner += words(it["name"], 60, 1180, size, t0 + .5, "#fff", .06, "slam", "left", 900)
        y = 1180 + size * .92 * lines + 18
        inner += label(f"{it.get('rarity_label') or it['rarity']} {it['type']}".upper(), 64, y, 32, t0 + .7,
                       "#fff", 800)
        inner += _from(t0 + .9, price_roll(int(it["price"]), 60, y + 50, 64, t0 + .9, .8))
        if last:
            # Several items can share the oldest season: then it's a tie, not "the" oldest.
            tied = sum(1 for p in picks if _order(p) == _order(it)) > 1
            inner += sticker("TIED FOR OLDEST!" if tied else "THE OLDEST TODAY!", 480, 640, 58, t0 + 1.6, rot=-5)
            inner += _from(t0 + 1.6, burst(560, 820, t0 + 1.6, ctx.seed + k))
        inner += progress(t0, t0 + R, k, n).replace(f"ROUND {k}/{n}", f"ITEM {k}/{n}")
        comp.scene(t0, t0 + R, inner, fade_in=.25, fade_out=.25)
        comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .15, "slam"); comp.cue(t0 + .5, "pop")
        comp.cue(t0 + 1.7, "cash")
        if last:
            comp.cue(t0 + 1.6, "reveal")

    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    _outro_scene(comp, ctx, content_end, comp.duration, "HOW OG IS YOUR LOCKER?",
                 (outfits + [o for o in picks if o not in outfits])[:3])
    comp.add(code_badge(.4))
    comp.add(disclosure())

    oldest = picks[0]
    body = "\n".join(f"{num(k)} {it['name']} · {it['type']} · {', '.join(s.title() for s in _season(it))} · "
                     f"{int(it['price']):,} V-Bucks" for k, it in enumerate(picks, 1))
    tags = _hashtags("ogfortnite", "ogcheck", oldest["name"])
    return Video(
        FORMAT, comp,
        title=f"OG Check — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"The Oldest Items in Today's Fortnite Shop: {ctx.day_label} #shorts",
        caption=_caption(f"👴 OG CHECK — Fortnite Item Shop, {ctx.day_label}\n"
                         f"The oldest items in today's shop, by the season Epic says each came out in 👇",
                         body, "How OG is your locker? Tell us below", tags),
        hashtags=tags)
