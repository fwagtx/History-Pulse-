"""
OG CHECK, as an edit: the oldest items in today's shop, by the season Epic
says each came out in, counted down on the countdown edit (cc_edit_countdown)
to a real track, the oldest last. The same data and truth rules as the
classic cc_fmt_og_check.

    build(ctx)          (ctx.shop is today's shop)

  hook    frame 0: "how old is today's item shop? 👴" over the five on their
          tiles, "by the season each one came out in 🗓️"; a bar later "wait
          for #1 👀"
  items   #5 to #2, cut on bar lines: the rank, the name, "introduced in" over
          "chapter ?, season ?" while the ticks run, then Epic's own season
          ("chapter 1, season 3") slamming in on the hit; then its rarity and
          type, today's price, and one line ("the oldest glider in today's
          shop 👀", "same season as Googly 🤝", else "an og in today's shop 👀"),
          "tied" by the rank when another of the five shares its season
  #1      "and #1 is… 🥁" over its silhouette, "the oldest in today's shop 👀"
          ("one of the oldest…" on a tie), the drop, 👴 -- "the oldest in
          today's shop 👴", or "tied for the oldest in today's shop 🤝" when
          another single in the shop shares its season
  outro   the five with their seasons ("#1 · ch1 s1"), "how og is your
          locker? 👇", use code BAD

Data and truth -- cc_fmt_og_check's own pick (_pick, _season, _order): today's
single offers at least MIN_AGE seasons older than the newest one, oldest
first, one per name, six or more of them or no video (the classic's rule; the
edit shows the oldest five):
  - "introduced in chapter 1, season 3" <- Epic's own `introduction` text
  - the order is the season's number in release order; items that share a
    season carry "tied" and are never called older than each other
  - "the oldest <type> in today's shop" only when every other single of that
    type in today's shop has a known, later season; "same season as X" only
    when X's season is the same
  - prices are the rows' own
It never says how many years old anything is, how rare it is, or that it's
"back". (The classic's pick asks ctx.art for every single in the shop, so the
end card's wall shows the first of today's singles, as the classic's does.)
"""

import random
import re

import cc_edit_countdown as CD
from cc_fmt_og_check import _order, _pick, _season
from cc_formats import Ctx, Video, _caption, _hashtags, kind_word, num, singles

COUNT = 5


def _said(it: dict) -> str:
    """Epic's own words: 'Chapter 1, Season 3', 'Chapter 4, Season OG'."""
    return ((it.get("introduction") or {}).get("text") or "").replace("Introduced in ", "").strip().rstrip(".")


def _words(it: dict) -> str:
    """Epic's season in the captions' case: 'chapter 1, season 3', 'chapter 1,
    season X', 'chapter 4, season OG', 'chapter 2, season Remix'."""
    return re.sub(r"\b(Chapter|Season)\b", lambda m: m.group(1).lower(), _said(it))


def _short(it: dict) -> str:
    """'ch1 s3' for the outro's labels."""
    ch, _, se = _said(it).partition(", ")
    return f"ch{ch.split()[-1]} s{se.split()[-1]}" if ch and se else _words(it)


def _options(it: dict, rank: int, shown: list, pool: list, tied_top: bool, ctx: Ctx) -> list:
    """The true lines about it, [(kind, text)] for CD.choose (a "~" kind is a
    plain one); #1 gets one."""
    o = _order(it)
    if rank == 1:
        return [("top", "tied for the oldest in today's shop 🤝" if tied_top else "the oldest in today's shop 👴")]
    opts = [("~og", "an og in today's shop 👀")]
    # every other single of its type must have a known season, and a later one
    same_type = [p for p in singles(ctx, need_art=False) if p is not it and p["type"] == it["type"]]
    if same_type and all(_order(p) and _season(p) and _order(p) > o for p in same_type):
        opts.append(("type", f"the oldest {it['type'].lower()} in today's shop 👀"))
    mate = next((p for p in shown if p is not it and _order(p) == o), None)
    if mate is None:
        mate = next((p for p in pool if p is not it and _order(p) == o and p["name"] != it["name"]), None)
    if mate is not None:
        opts.append(("mate", f"same season as {mate['name']} 🤝"))
    return opts


def build(ctx: Ctx, **_):
    picks = _pick(ctx)                          # the classic's rule: six or more, or nothing
    if not picks:
        return None
    shown = picks[:COUNT]
    # every single in today's shop with a known season (art or not), for the ties and "same season as"
    pool = [i for i in singles(ctx, need_art=False) if _order(i) and _season(i)]
    tied_top = sum(1 for p in pool if _order(p) == _order(shown[0]) and p["name"] != shown[0]["name"]) > 0
    rnd = random.Random(ctx.seed * 7 + 13)
    lines = CD.choose([_options(it, rank, shown, pool, tied_top, ctx) for rank, it in enumerate(shown, 1)], rnd)
    entries = []
    for rank, it in enumerate(shown, 1):
        tied = any(p is not it and _order(p) == _order(it) for p in shown)
        what = f"{it.get('rarity_label') or it['rarity']} {it['type']}".strip().lower()
        entries.append(CD.Entry(
            it, CD.Stat("introduced in", text=_words(it), guess="chapter ?, season ?"),
            [what, f"{int(it['price']):,} v-bucks in today's shop"],
            lines[rank - 1], tag="tied" if tied and rank > 1 else "",
            label=_short(it)))
    comp = CD.cut(ctx, entries, salt="og_check", title="how old is today's item shop? 👴",
                  sub="by the season each one came out in 🗓️",
                  tease="one of the oldest in today's shop 👀" if tied_top else "the oldest in today's shop 👀",
                  ask="how og is your locker? 👇", crown="👴")
    if comp is None:
        return None

    # ------------------------------------------------------------ the post (the classic's lines)
    oldest = shown[0]
    # Epic's own wording, as written: "Chapter 1, Season 3", "Chapter 4, Season OG".
    body = "\n".join(f"{num(k)} {it['name']} {kind_word(it)} · {_said(it)} · {int(it['price']):,} V-Bucks"
                     for k, it in enumerate(shown, 1))
    tags = _hashtags("ogfortnite", "ogcheck", oldest["name"])
    return Video(
        "edit_og_check", comp,
        title=f"OG Check — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"The Oldest Items in Today's Fortnite Shop: {ctx.day_label} #shorts",
        caption=_caption(f"How old is today's Item Shop? 👴\n"
                         f"The oldest stuff in the shop on {ctx.day:%B} {ctx.day.day}, by the season Epic says each came out",
                         body, "How OG is your locker?", tags),
        hashtags=tags)
