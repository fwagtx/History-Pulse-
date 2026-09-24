"""
BUNDLE MATH -- slot 3 (value) for @usecodebad: today's bundles against buying
the same items one by one, today.

    0:00  hook      BUNDLE MATH / IS THE BUNDLE WORTH IT?, two of the items
    0:03  bundles   3-5 bundles, ~10-17 s each: the bundle's art and name, a
                    receipt that prints each item with its own price today, the
                    total rolls up, the bundle's price slams in under it, and a
                    stamp says how many V-Bucks the bundle saves
    0:55  outro     code BAD + "WHICH BUNDLE WOULD YOU GET?"

Truth rules this format keeps:
  - a bundle is only used when EVERY item in it is also sold on its own in
    today's shop (matched by item id), so the "one by one" total is a real sum
    of today's prices, never an estimate;
  - only when that total is more than the bundle's price;
  - "saves" is that total minus the bundle's price, nothing else.
It never uses Epic's "regular price", never says "discount", never rates a bundle.
"""

import cc_looks as LK
from cc_fmt_last_chance import _em, _fit, _from
from cc_formats import Ctx, Video, _pad, _hook_scene, _outro_scene, _hashtags, _caption, num
from cc_motion import (ACCENT, INK, RARITY, Comp, an, burst, character, code_badge, disclosure, esc,
                       label, price_roll, progress, sticker, style_anim, tile_bg, words)

FORMAT = "bundle_math"
HOOK = 3.0
MIN_BUNDLES, MAX_BUNDLES = 3, 5
CONTENT = 52.0
SHOW_LINES = 6            # receipt lines; the rest share one "+N more" line


def _eligible(ctx: Ctx) -> list:
    """[(bundle, parts, total)], biggest saving first. parts: [{name, price}]."""
    items = ctx.shop.get("items", [])
    prices = ctx.shop.get("single_prices") or {}
    out, seen = [], set()
    for b in items:
        ids = b.get("member_ids") or []
        if not b.get("is_bundle") or len(ids) < 2 or not all(int(prices.get(x) or 0) > 0 for x in ids):
            continue
        parts = [{"name": nm, "price": int(prices[x])} for x, nm in zip(ids, b.get("member_names") or [])]
        if len(parts) != len(ids):
            continue
        # Two items can share a name (a PAC-MAN back bling and a PAC-MAN companion):
        # then each says what it is.
        types = b.get("member_types") or []
        names = [p["name"].lower() for p in parts]
        for p, kind in zip(parts, types):
            if kind and names.count(p["name"].lower()) > 1:
                p["name"] = f"{p['name']} ({kind})"
        total = sum(p["price"] for p in parts)
        if total <= int(b["price"]):
            continue
        name = _title(b).lower()
        if name in seen:
            continue
        seen.add(name)
        out.append((b, parts, total))
    with_art = [x for x in out if ctx.art(x[0])]
    out = with_art if len(with_art) >= MIN_BUNDLES else out
    out.sort(key=lambda x: (-(x[2] - int(x[0]["price"])), x[0]["name"]))
    return out[:MAX_BUNDLES] if len(out) >= MIN_BUNDLES else []


def _title(b: dict) -> str:
    """Epic's own bundle name ('PAC-MAN Bundle'), else the shop section's."""
    return b.get("bundle_name") or b["name"].split(" (")[0]


def _receipt(parts: list, total: int, price: int, t0: float, beat: float) -> tuple:
    """The receipt card: one line per item with its price today, then the total,
    then the bundle's price. Returns (html, when the bundle price lands)."""
    lines = parts[:SHOW_LINES]
    rest = parts[SHOW_LINES:]
    rows = [(p["name"], int(p["price"])) for p in lines]
    if rest:
        rows.append((f"+{len(rest)} more items", sum(int(p["price"]) for p in rest)))
    x, y, w = 70, 850, 820
    row_h = 46
    t_lines = t0 + 1.4 * beat
    step = min(.55, 2.6 * beat / max(len(rows), 1))
    html = [f'<div class="abs" style="left:{x}px;top:{y}px;width:{w}px;height:{110 + row_h * len(rows) + 150}px;'
            f'border-radius:18px;background:#f4f1e8;box-shadow:0 18px 0 rgba(0,0,0,.35);'
            f'{style_anim(an("rise", t0 + 1.0 * beat, .45))}"></div>',
            f'<div class="abs" style="left:{x + 30}px;top:{y + 22}px;font-size:26px;font-weight:900;color:#4a4a52;'
            f'letter-spacing:.14em;{style_anim(an("rise", t0 + 1.0 * beat, .45))}">BOUGHT ONE BY ONE TODAY</div>']
    for j, (name, cost) in enumerate(rows):
        ty = y + 70 + j * row_h
        a = style_anim(an("rise", t_lines + j * step, .3))
        html.append(f'<div class="abs" style="left:{x + 30}px;top:{ty}px;width:{w - 60}px;display:flex;'
                    f'justify-content:space-between;font-size:30px;font-weight:700;color:{INK};{a}">'
                    f'<span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:560px">'
                    f'{esc(name)}</span><span>{cost:,}</span></div>')
    t_total = t_lines + len(rows) * step + .3 * beat
    ty = y + 70 + len(rows) * row_h + 6
    html.append(f'<div class="abs" style="left:{x + 30}px;top:{ty}px;width:{w - 60}px;border-top:4px dashed #9a9aa2;'
                f'{style_anim(an("fadein", t_total - .1, .2))}"></div>')
    html.append(f'<div class="abs" style="left:{x + 30}px;top:{ty + 14}px;font-size:34px;font-weight:900;color:{INK};'
                f'{style_anim(an("rise", t_total, .3))}">TOTAL</div>')
    # Right-aligned with the prices above it.
    html.append(_from(t_total, price_roll(total, x + w - 30 - _em(f"{total:,}") * 48, ty + 8, 48, t_total, .8,
                                          color=INK, suffix="")))
    t_bundle = t_total + 1.3 * beat
    html.append(f'<div class="abs" style="left:{x - 10}px;top:{ty + 74}px;width:{w + 20}px;height:84px;'
                f'border-radius:16px;background:{INK};display:flex;align-items:center;justify-content:space-between;'
                f'padding:0 36px;{style_anim(an("slam", t_bundle, .5))}">'
                f'<span class="d" style="font-size:52px;color:#fff">BUNDLE</span>'
                f'<span class="d" style="font-size:60px;color:{ACCENT}">{price:,} V-BUCKS</span></div>')
    return "".join(html), t_total, t_bundle


def build(ctx: Ctx):
    picks = _eligible(ctx)
    if not picks:
        return None
    look = LK.get(FORMAT)
    if look:
        comp = look.bundle_math(ctx, picks)
    else:
        n = len(picks)
        R = max(10.4, min(17.0, CONTENT / n))
        beat = R / 13.0                          # the beats stretch with the scene
        content_end = HOOK + n * R
        comp = Comp(content_end + _pad(content_end))
        _hook_scene(comp, ctx, "BUNDLE MATH", "IS THE BUNDLE WORTH IT?", f"{n} BUNDLES", HOOK + .3,
                    picks[0][0], picks[1][0])
        comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop")

        for k, (b, parts, total) in enumerate(picks, 1):
            t0 = HOOK + (k - 1) * R
            price = int(b["price"])
            cols = b.get("tile_colors") or [RARITY.get(b["rarity"], "#3a3a44")]
            inner = tile_bg(cols, b["rarity"], t0)
            title = _title(b)
            size, lines = _fit(title, 940, big=92, one_min=66, two_max=72, small=52)
            inner += words(title, 60, 300, size, t0 + .2, "#fff", .06, "slam", "left", 940)
            top = 300 + size * .92 * lines + 10
            inner += label(f"{len(parts)} ITEMS · EVERY ONE ALSO SOLD ON ITS OWN TODAY", 64, top, 28, t0 + .45,
                           ACCENT, 800)
            inner += character(ctx.art(b), 540, 660, 380, t0 + .1, "pop", .6, "float", b["rarity"], title)
            receipt, t_total, t_bundle = _receipt(parts, total, price, t0, beat)
            inner += receipt
            t_save = t_bundle + 1.1 * beat
            inner += sticker(f"SAVES {total - price:,} V-BUCKS", 250, 760, 64, t_save, rot=-6)
            inner += _from(t_save, burst(560, 800, t_save, ctx.seed + k))
            inner += progress(t0, t0 + R, k, n).replace(f"ROUND {k}/{n}", f"BUNDLE {k}/{n}")
            comp.scene(t0, t0 + R, inner, fade_in=.25, fade_out=.25)
            comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .2, "slam")
            for j in range(min(len(parts), 7)):
                comp.cue(t0 + 1.4 * beat + j * min(.55, 2.6 * beat / max(min(len(parts), 7), 1)), "tick")
            comp.cue(t_total + .8, "cash"); comp.cue(t_bundle, "slam"); comp.cue(t_save, "reveal")

        comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
        _outro_scene(comp, ctx, content_end, comp.duration, "WHICH BUNDLE WOULD YOU GET?", [b for b, _, _ in picks][:3])
        comp.add(code_badge(.4))
        comp.add(disclosure())
        comp.cues.sort()

    body = "\n".join(f"{num(k)} {_title(b)}: {int(b['price']):,} V-Bucks · one by one {total:,} · "
                     f"saves {total - int(b['price']):,}" for k, (b, _, total) in enumerate(picks, 1))
    tags = _hashtags("fortnitebundles", "bundlemath", _title(picks[0][0]))
    return Video(
        FORMAT, comp,
        title=f"Bundle Math — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"Are Today's Fortnite Bundles Worth It? {ctx.day_label} #shorts",
        caption=_caption(f"🧮 BUNDLE MATH — Fortnite Item Shop, {ctx.day_label}\n"
                         f"Today's bundles against buying the same items one by one, at today's prices 👇",
                         body, "Which bundle would you get? Tell us below", tags),
        hashtags=tags)
