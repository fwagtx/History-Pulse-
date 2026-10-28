"""
BACK AFTER, as an edit: today's comebacks -- items back in the Item Shop after
the longest time away -- counted down on the countdown edit (cc_edit_countdown)
to a real track, the longest wait last. The same data and truth rules as the
classic cc_fmt_rarity.back_after.

    build(ctx)          (ctx.shop is today's shop)

  hook    frame 0: "back in the shop after 1,299 days 😭" over the comebacks'
          tiles, "today's longest comebacks 🛒"; a bar later "wait for #1 👀"
  items   #N to #2, cut on bar lines: the rank, the name (a group's shop
          section or set when several came back together), "back after" and
          the days rolling up on the beat, landing with a hit; then "last in
          the shop: feb 28, 2023", how many times it was in the shop before
          (or what came back with it), its rarity, type and price, and one
          line ("that's over 3 years 😭")
  #1      "and #1 is… 🥁" over its silhouette, "the longest wait 👀", the
          drop, 🎉 -- "the longest wait in today's shop 🎉" when it is
  outro   the comebacks with their days, "which one were you waiting for? 👇",
          use code BAD

Data and truth -- cc_rarity.back_in_shop through the classic's own pieces
(cc_fmt_rarity.history, SHOWN, TYPE_ORDER, _group_title):
  - "back after N days"   <- the item is in today's shop and N days passed
                             between its previous day in the shop and the day
                             this listing started (the row's in_day)
  - one card per comeback: items last in the shop the same day that came back
    the same day are one comeback (the classic's grouping), named by their
    shop section or set when they share one, else by the lead item
  - at least 180 days away, or -- when that leaves fewer than three
    comebacks -- at least 90 (as cc_samples does); fewer than three either
    way: None, the slot makes something else. Up to five, longest last.
  - "in the item shop N times before" <- separate runs before this listing
  - prices are the rows' own.
  - "the longest wait in today's shop" only when nothing in today's shop, of
    any type, bundles' contents included, came back after longer.
Never why it was gone, never "rare" beyond the days.
"""

import random
from datetime import date

import cc_edit_countdown as CD
import cc_rarity as R
from cc_fmt_rarity import SHOWN, TYPE_ORDER, _group_title, history
from cc_formats import Ctx, Video, _caption, _hashtags, num

MIN_CARDS, MAX_CARDS = 3, 5


def cards(ctx: Ctx, min_days: int) -> tuple:
    """([(gone, last, members, title)] longest wait first, the longest gap of
    any single offer in today's shop) -- members are (row, item id, times
    before), the lead (the one on the tile) first. A member without art can't
    lead a card; a card with no member that has art is left out."""
    hist = history()
    rows = R.back_in_shop(hist, ctx.shop, ctx.day, min_days)
    groups, seen = {}, set()
    for row, iid, gone, last, times in rows:
        if row["name"].lower() in seen or row.get("type") not in SHOWN:
            continue
        seen.add(row["name"].lower())
        groups.setdefault((gone, last), []).append((row, iid, times))
    out = []
    for (gone, last), members in sorted(groups.items(), key=lambda g: (-g[0][0], g[0][1])):
        members.sort(key=lambda m: (TYPE_ORDER.get(m[0]["type"], 9), -int(m[0].get("price") or 0)))
        lead = next((m for m in members if ctx.art(m[0])), None)
        if lead is None:
            continue
        members.remove(lead)
        members.insert(0, lead)
        out.append((gone, last, members, _group_title(hist, members) if len(members) > 1 else ""))
        if len(out) == MAX_CARDS:
            break
    return out, _longest(hist, ctx)


def _longest(hist: R.History, ctx: Ctx) -> int:
    """The longest gap of anything in today's shop, bundles' contents too
    (History.back_after on each id, from the day its listing started)."""
    best = 0
    for row in ctx.shop.get("items", []):
        start = date.fromisoformat(row["in_day"]) if row.get("in_day") else ctx.day
        for iid in R.shop_ids(row):
            ba = hist.back_after(iid, start) if hist.has(iid) else None
            if ba:
                best = max(best, ba[0])
    return best


def _names(names: list, room: int = 34) -> str:
    """As many names as fit one line, then '+N more'."""
    for keep in range(len(names), 0, -1):
        more = len(names) - keep
        text = " · ".join(names[:keep]) + (f" +{more} more" if more else "")
        if len(text) <= room or keep == 1:
            return text
    return ""


def _options(gone: int, last, times: int, single: bool, rank: int, longest: int, day) -> list:
    """The true lines about it, [(kind, text)] for CD.choose (a "~" kind is a
    plain one, used when nothing else is fresh); #1 gets one."""
    years = CD.years_line(last, day)
    wait = ("years", years) if years else ("months", f"that's about {max(3, round(gone / 30.44))} months 👀")
    if rank == 1:
        return [("top", "the longest wait in today's shop 🎉")] if gone >= longest else [wait]
    opts = [wait, ("~welcome", "welcome back 👋"), ("~over", "the wait is over 🎉")]
    if single and times == 1:
        opts.append(("second", "only its second time in the shop 👀"))
    return opts


def build(ctx: Ctx, **_):
    got, longest = cards(ctx, 180)
    if len(got) < MIN_CARDS:
        got, longest = cards(ctx, 90)
    if len(got) < MIN_CARDS:
        return None
    rnd = random.Random(ctx.seed * 7 + 11)
    lines = CD.choose([_options(gone, last, members[0][2], len(members) == 1, rank, longest, ctx.day)
                       for rank, (gone, last, members, _) in enumerate(got, 1)], rnd)
    entries = []
    for rank, (gone, last, members, title) in enumerate(got, 1):
        row, _, times = members[0]
        tied = any(c[0] == gone for k, c in enumerate(got, 1) if k != rank and abs(k - rank) == 1)
        single = len(members) == 1
        what = f"{row.get('rarity_label') or row['rarity']} {row['type']}".strip().lower()
        if single:
            facts = [f"last in the shop: {CD.day_str(last)}",
                     "in the item shop once before" if times == 1 else f"in the item shop {times} times before",
                     f"{what} · {int(row['price']):,} v-bucks"]
        else:
            names = [m[0]["name"] for m in members]
            facts = [f"{len(members)} items back together" if title else f"+{len(members) - 1} more back with it",
                     f"last in the shop: {CD.day_str(last)}",
                     _names(names if title else names[1:])]
        entries.append(CD.Entry(
            row, CD.Stat("back after", gone, "days"), facts,
            lines[rank - 1], name=title or row["name"], tag="tied" if tied and rank > 1 else "",
            label=f"{gone:,} days"))
    top = got[0][0]
    comp = CD.cut(ctx, entries, salt="back_after", title=f"back in the shop after {top:,} days 😭",
                  sub="today's longest comebacks 🛒", tease="the longest wait 👀",
                  ask="which one were you waiting for? 👇", crown="🎉")
    if comp is None:
        return None

    # ------------------------------------------------------------ the post (the classic's lines)
    def line(k, gone, last, members, title):
        when = f"back after {gone:,} days (last in the shop {last:%b %-d, %Y})"
        if len(members) == 1:
            row = members[0][0]
            return f"{num(k)} {row['name']} · {when} · {int(row['price']):,} V-Bucks"
        names = ", ".join(m[0]["name"] for m in members[:6]) + (f" +{len(members) - 6} more" if len(members) > 6 else "")
        return f"{num(k)} {f'{title} ({len(members)} items): ' if title else ''}{names} · {when}"
    body = "\n".join(line(k, *c) for k, c in enumerate(got, 1))
    tags = _hashtags("fortniteitemshop", "rareskins", got[0][3] or got[0][2][0][0]["name"])
    return Video(
        "edit_back_after", comp,
        title=f"Back After {top:,} Days — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"Back in the Fortnite Shop After {top:,} Days: {ctx.day_label} #shorts",
        caption=_caption(f"Back in the Item Shop after {top:,} days 😭\n"
                         f"Today's longest comebacks ({ctx.day:%B} {ctx.day.day}), by how long each one was gone",
                         body, "Which one were you waiting for?", tags),
        hashtags=tags)
