"""
LAST CHANCE, as an edit: today's offers leaving the Item Shop at the next
reset, with their prices, counted down on the countdown edit
(cc_edit_countdown) to a real track, the priciest last. The same data and
truth rules as the classic cc_fmt_last_chance.

    build(ctx)          (ctx.shop is today's shop)

  hook    frame 0: "last chance before these leave the shop ⏰" over the
          offers' tiles, "leaving at the next reset: 8 PM ET 🛒"; a bar later
          "wait for #1 👀"
  items   #5 to #2, cut on bar lines: the rank, the name, "today's price" and
          the price rolling up in v-bucks, landing with a hit; then what it is
          ("epic outfit", "bundle · 9 items"), what a bundle includes, Epic's
          regular price for a bundle when it lists a higher one, how long it
          has been in the shop, and one line ("leaving at 8 PM ET ⏰")
          -- "tied" by the rank when a neighbour costs the same
  #1      "and #1 is… 🥁" over its silhouette, "the priciest one leaving 👀"
          ("one of the priciest leaving" on a tie), the drop, ⏰ -- "the
          priciest offer leaving at reset 💸" when it is
  outro   the offers with their prices, "which one are you grabbing? 👇",
          use code BAD

Data and truth -- cc_fmt_last_chance's own pick (_leaving, _pick): offers
whose out_day is today's shop day, priciest first, the classic's variety caps;
the edit shows the top five (four when that's all, the classic's minimum;
fewer: None):
  - "leaving at reset", "leaving at 8 PM ET" -- the reset time is computed
    (ctx.reset_et); nothing says or implies it won't come back
  - prices are the rows' `price`; only bundles show a regular price, and only
    when Epic lists one above today's price ("regular price", nothing else)
  - "in the shop since sep 20" / "added today" from in_day; a bundle's
    contents from member_names
  - "the priciest ... leaving" only when no offer leaving at this reset costs
    more ("tied for the priciest" when one costs the same)
Nothing about popularity, ratings, rarity, "back" or "first time"; never
"discount" or "save". (The classic's pick asks ctx.art for every offer
leaving, so the end card's wall shows the first of them, as the classic's does.)
"""

import random

import cc_edit_countdown as CD
from cc_fmt_last_chance import MIN_OFFERS, _leaving, _members, _meta, _pick, _regular, _shown_name, _since
from cc_formats import BRAND_TAGS, Ctx, Video, _caption, _hashtags, kind_word

COUNT = 5


def _includes(it: dict, room: int = 40) -> str:
    """'includes Sora · Riku +7 more' -- as many of a bundle's names as fit;
    '+N more' counts the bundle's items, so it adds up to "bundle · 9 items"
    even when two of them share a name."""
    names = _members(it)
    total = max(int(it.get("bundle_size") or 0), len(it.get("member_names") or []), len(names))
    for keep in range(len(names), 0, -1):
        more = total - keep
        text = "includes " + " · ".join(names[:keep]) + (f" +{more} more" if more > 0 else "")
        if len(text) <= room or keep == 1:
            return text
    return ""


def _options(it: dict, rank: int, top_all: int, n_top: int, ctx: Ctx) -> list:
    """The true lines about it, [(kind, text)] for CD.choose (a "~" kind is a
    plain one); #1 gets one when it's the priciest leaving."""
    if rank == 1 and int(it["price"]) >= top_all:
        return [("top", "tied for the priciest leaving 🤝" if n_top > 1 else "the priciest offer leaving at reset 💸")]
    opts = [("~reset", f"leaving at {ctx.reset_et} ⏰"), ("~last", "last chance to grab it ⏰")]
    if it.get("in_day") == ctx.day.isoformat():
        opts.append(("today", "added today, leaving at reset 😭"))
    if it.get("is_bundle"):
        n = int(it.get("bundle_size") or 0) or len(_members(it))
        if n > 1:
            opts.append(("bundle", f"{n} items in one bundle 👀"))
    return opts


def build(ctx: Ctx, **_):
    leaving = _leaving(ctx)
    if len(leaving) < MIN_OFFERS:
        return None
    picked = _pick(ctx, leaving)                 # priciest first
    if len(picked) < MIN_OFFERS:
        return None
    shown = picked[:COUNT]
    top_all = max(int(i["price"]) for i in leaving)
    n_top = sum(1 for i in leaving if int(i["price"]) == top_all)
    rnd = random.Random(ctx.seed * 7 + 17)
    lines = CD.choose([_options(it, rank, top_all, n_top, ctx) for rank, it in enumerate(shown, 1)], rnd)
    entries = []
    for rank, it in enumerate(shown, 1):
        tied = any(o is not it and int(o["price"]) == int(it["price"]) for o in picked[max(0, rank - 2):rank + 1])
        facts = [_meta(it).lower()]
        if it.get("is_bundle"):
            if _regular(it):
                facts.append(f"regular price {_regular(it):,} v-bucks")
            inc = _includes(it)
            if inc:
                facts.append(inc)
        since = _since(it, ctx).lower()
        if since:
            facts.append(since)
        entries.append(CD.Entry(
            it, CD.Stat("today's price", int(it["price"]), "v-bucks"), facts,
            lines[rank - 1], name=_shown_name(it), tag="tied" if tied and rank > 1 else "",
            label=f"{int(it['price']):,}"))
    first = shown[0]
    tease = ("the priciest one here 👀" if int(first["price"]) < top_all else
             "one of the priciest leaving 👀" if n_top > 1 else "the priciest one leaving 👀")
    comp = CD.cut(ctx, entries, salt="last_chance", title="last chance before these leave the shop ⏰",
                  sub=f"leaving at the next reset: {ctx.reset_et} 🛒", tease=tease,
                  ask="which one are you grabbing? 👇", crown="⏰")
    if comp is None:
        return None

    # ------------------------------------------------------------ the post (the classic's lines)
    def line(it):
        if it.get("is_bundle"):
            bn = int(it.get("bundle_size") or 0) or len(_members(it))
            s = f"{_shown_name(it)} bundle ({bn} items) · {int(it['price']):,}"
            reg = _regular(it)
            return s + (f", normally {reg:,}" if reg else "")
        s = f"{it['name']} {kind_word(it)} · {int(it['price']):,}"
        return s + (" · new today" if it.get("in_day") == ctx.day.isoformat() else "")

    n = len(shown)
    head = (f"Last chance ⏰ these leave the Item Shop tonight at {ctx.reset_et}\n"
            f"Fortnite Item Shop, {ctx.day:%B} {ctx.day.day}")
    tail = f"{len(leaving)} offers leave at this reset. Here are {n} of them, priciest first (prices in V-Bucks)."

    tags = _hashtags("lastchance", *[_shown_name(i) for i in shown])
    tags = BRAND_TAGS + [t for t in tags if t not in BRAND_TAGS]      # brand tags always lead
    caption = _caption(head, "\n".join(line(i) for i in shown) + "\n\n" + tail, "Which one are you grabbing?", tags)
    yt = f"Last Chance: Leaving the Fortnite Item Shop at Reset ({ctx.day_label}) #shorts"
    if len(yt) > 100:
        yt = f"Last Chance: Fortnite Item Shop {ctx.day_label} #shorts"
    return Video("edit_last_chance", comp, title=f"Last Chance — Fortnite Item Shop, {ctx.day_label}"[:60],
                 yt_title=yt, caption=caption, hashtags=tags)
