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

import cc_looks as LK
from cc_fmt_last_chance import _em, _fit, _from
from cc_formats import (MIN_SECONDS, Ctx, Video, singles, _pad, _hook_scene, _outro_scene, _hashtags, _caption,
                        num)
from cc_motion import (ACCENT, RARITY, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, Comp, burst,
                       character, code_badge, disclosure, label, price_roll, progress, sticker, tile_bg, words)

FORMAT = "og_check"
HOOK = 3.0
R = 6.6
MAX_ITEMS = 8
MIN_ITEMS = 6
MIN_AGE = 4          # at least this many seasons older than the newest item in the shop

# Classic layout (px), inside the apps' safe box (cc_safe): x 60-1020 above y 740,
# x 60-900 (left of the button rail) below it, y 230-1420. The code badge and
# #EpicPartner own the top-left corner down to y ~350, the item counter the
# top-right down to y ~292.
#
#   y 366-620    INTRODUCED IN / CHAPTER 1 / SEASON 3 (left), the #N sticker (right)
#   y 640-1150   the cosmetic, centred on the band beside the rail
#   y ...-1404   name, type and today's price, bottom-aligned
TOP_Y = 366
SEASON_W = 720
TEXT_W = SAFE_RIGHT - SAFE_LEFT                  # 840: the name block sits beside the rail
INFO_BOTTOM = SAFE_BOTTOM - 16
PRICE_SIZE = 80                                  # its V-BUCKS is .38 of this: 30 px


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


def _scrim() -> str:
    """Darkens the bands the words sit on, so white type and the lime code badge
    hold on pale tile colours (some are acid yellow-green themselves)."""
    return ('<div class="full" style="background:linear-gradient(180deg,rgba(0,0,0,.5) 0,'
            'rgba(0,0,0,.36) 20%,rgba(0,0,0,.2) 30%,rgba(0,0,0,0) 42%,rgba(0,0,0,0) 58%,'
            'rgba(0,0,0,.3) 70%,rgba(0,0,0,.55) 100%)"></div>')


def build(ctx: Ctx):
    picks = _pick(ctx)
    if not picks:
        return None
    outfits = [i for i in picks if i["type"] == "Outfit"] or picks
    look = LK.get(FORMAT)
    comp = LK.draw(look, "og_check", ctx, picks)
    if comp is None:
        n = len(picks)
        show = list(reversed(picks))            # count down: the oldest comes last
        # Eight items make a 63 s video. Six or seven stretch a little rather than
        # leave an end card longer than 10 s.
        rlen = max(R, min(1.35 * R, (MIN_SECONDS - 10 - HOOK) / n))
        content_end = HOOK + n * rlen
        comp = Comp(content_end + _pad(content_end))
        _hook_scene(comp, ctx, "OG CHECK", "THE OLDEST ITEMS IN TODAY'S SHOP", "HOW OLD?", HOOK + .3,
                    outfits[0], outfits[1] if len(outfits) > 1 else picks[1])
        comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop")

        for k, it in enumerate(show, 1):
            t0 = HOOK + (k - 1) * rlen
            rank = n - k + 1
            last = rank == 1
            ch, se = _season(it)
            cols = it.get("tile_colors") or [RARITY.get(it["rarity"], "#3a3a44")]
            inner = tile_bg(cols, it["rarity"], t0) + _scrim()

            # The season, top left, as big as it fits beside the #N sticker.
            tag = f"#{rank}"
            tag_w = (_em(tag) + .84) * 110
            s1 = min(104, SEASON_W / max(_em(ch) + .18, .1))
            s2 = min(104, SEASON_W / max(_em(se) + .18, .1))
            inner += label("INTRODUCED IN", SAFE_LEFT, TOP_Y, 30, t0, ACCENT, 800, anim="none", spacing=".16em")
            y_ch = TOP_Y + 44
            y_se = y_ch + s1 * .92 + 2
            season_bottom = y_se + s2 * .92
            inner += words(ch, SAFE_LEFT, y_ch, s1, t0 + .15, "#fff", .06, "slam", "left", SEASON_W + 40)
            inner += words(se, SAFE_LEFT, y_se, s2, t0 + .3, ACCENT, .06, "slam", "left", SEASON_W + 40)
            inner += sticker(tag, SAFE_RIGHT_TOP - 26 - tag_w, TOP_Y - 10, 110, t0 + .35, rot=7)

            # Name, type and today's price, bottom-aligned above the caption zone.
            size, lines = _fit(it["name"], TEXT_W, big=96, one_min=70, two_max=76, small=56)
            info_h = size * .92 * lines + 16 + 30 * 1.25 + 10 + PRICE_SIZE * .9
            y_name = INFO_BOTTOM - info_h
            y_type = y_name + size * .92 * lines + 16
            y_price = y_type + 30 * 1.25 + 10

            # The cosmetic between the season and the name.
            art_top = season_bottom + 24
            art_h = max(360, min(560, y_name - 18 - art_top))
            cy = y_name - 18 - art_h / 2
            inner += character(ctx.art(it), (SAFE_LEFT + SAFE_RIGHT) / 2, cy, art_h, t0 + .1, "pop", .6, "float",
                               it["rarity"], it["name"], maxw=700, trim=True)
            inner += words(it["name"], SAFE_LEFT, y_name, size, t0 + .5, "#fff", .06, "slam", "left", TEXT_W)
            inner += label(f"{it.get('rarity_label') or it['rarity']} {it['type']}".upper(), SAFE_LEFT + 4, y_type,
                           30, t0 + .7, "#fff", 800)
            inner += _from(t0 + .9, price_roll(int(it["price"]), SAFE_LEFT, y_price, PRICE_SIZE, t0 + .9, .8))
            if last:
                # Several items can share the oldest season: then it's a tie, not "the" oldest.
                # The sticker lands beside the season, clear of the cosmetic's face.
                tied = sum(1 for p in picks if _order(p) == _order(it)) > 1
                text = "TIED FOR OLDEST!" if tied else "THE OLDEST TODAY!"
                st = min(58, 440 / (_em(text) + .84))
                sw = (_em(text) + .84) * st
                sx = SAFE_RIGHT_TOP - 20 - sw
                sy = min(TOP_Y + 150, season_bottom - st * 1.3)
                inner += _from(t0 + 1.6, burst(sx + sw / 2, sy + 30, t0 + 1.6, ctx.seed + k))
                inner += sticker(text, sx, sy, st, t0 + 1.6, rot=-5)
            inner += progress(t0, t0 + rlen, k, n).replace(f"ROUND {k}/{n}", f"ITEM {k}/{n}")
            # The next item fades in on top while this one holds: a crossfade, no dip to black.
            comp.scene(t0, t0 + rlen + .3, inner, fade_in=.25, fade_out=.05)
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
    # Epic's own wording, as written: "Chapter 1, Season 3", "Chapter 4, Season OG".
    said = lambda it: ((it.get("introduction") or {}).get("text") or "").replace("Introduced in ", "").rstrip(".")
    body = "\n".join(f"{num(k)} {it['name']} · {it['type']} · {said(it)} · {int(it['price']):,} V-Bucks"
                     for k, it in enumerate(picks, 1))
    tags = _hashtags("ogfortnite", "ogcheck", oldest["name"])
    return Video(
        FORMAT, comp,
        title=f"OG Check — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"The Oldest Items in Today's Fortnite Shop: {ctx.day_label} #shorts",
        caption=_caption(f"👴 OG CHECK — Fortnite Item Shop, {ctx.day_label}\n"
                         f"The oldest items in today's shop, by the season Epic says each came out in 👇",
                         body, "How OG is your locker? Tell us below", tags),
        hashtags=tags)
