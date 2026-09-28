"""
LONGEST GONE, as an edit: the cosmetics gone from the Item Shop the longest --
days since each was last sold -- counted down on the countdown edit
(cc_edit_countdown) to a real track. It is the metric of the classic
cc_fmt_rarity.rarest ("RAREST ... GONE FROM THE SHOP THE LONGEST"), with its
rows and truth rules; the fewest-times list is cc_edit_rarest.

    build(ctx, kind="outfit")       kind: outfit | pickaxe | emote | backpack | glider

  hook    frame 0: "the skins gone the longest 😭" over the five on their
          tiles, "days since each was last in the item shop 🛒"; a bar later
          "wait for #1 👀"
  items   #5 to #2, cut on bar lines: the rank, the name, "gone for" and the
          days rolling up on the beat, landing with a hit; then "last seen:
          sep 15, 2018", how many times it was in the shop (or how many of
          its set left with it), its rarity, type and season, and one line
          ("that's over 8 years 😭")
  #1      "and #1 is… 🥁" over its silhouette, "gone from the item shop the
          longest 👀", the drop, 👑 -- "no skin has been gone longer 👑"
  outro   the five with their days, "which one do you want back? 👇", use
          code BAD

Data and truth -- cc_rarity.History.longest_gone through cc_fmt_rarity.history,
the classic's rows exactly: items of `kind` not on sale on ctx.day (and not in
today's shop listing), by days since their last day in the Item Shop, a set
that left the shop together counted once:
  - "gone for N days"             <- ctx.day minus its last day in the shop
  - "last seen <date>"            <- that day
  - "in the item shop N times"    <- separate runs (consecutive days count once);
                                     "since oct 2017" when its first day is
                                     before 2018 (the records start Oct 30, 2017)
  - "+N more from its set, gone since that day" <- the rest of its set (same
                                     kind) whose last day is the same and who
                                     are still gone
  - "that's over N years"         <- whole years from that day to ctx.day
  - "no skin has been gone longer" only when nothing ties it; else "tied".
Every one of the five must have art, or no video (None): skipping one would
put the wrong rank on the next. Never why it's gone, never that it won't
come back.
"""

import random
from collections import Counter

import cc_edit_countdown as CD
from cc_edit_rarest import _what
from cc_fmt_most_common import KINDS
from cc_fmt_rarity import _item, history
from cc_formats import Ctx, Video, _caption, _hashtags, num

COUNT = 5


def _set(raw: dict) -> str:
    return (raw.get("set") or {}).get("value") or ""


def rows(ctx: Ctx, kind: str, count: int = COUNT) -> list | None:
    """The `count` gone the longest as of ctx.day (and the next one, for the
    tie check), longest first, or None."""
    hist = history()
    listed = CD.listed_today(ctx)
    gone = [g for g in hist.longest_gone(ctx.day, kind, len(hist.days)) if g[0]["id"].lower() not in listed]
    left = Counter((_set(raw), last) for raw, last, _, _ in gone)
    out, seen = [], set()
    for raw, last, days, times in gone:
        key = (_set(raw), last)
        if key[0] and key in seen:
            continue                      # a set that left together counts once
        seen.add(key)
        it = _item(raw)
        it["name"] = " ".join(it["name"].split())
        it["raw"] = raw                   # its series' tile colours
        out.append({"item": it, "last": last, "days": days, "times": times,
                    "vouched": hist.first_seen(raw["id"]) is not None, "with": left[key] - 1 if key[0] else 0})
        if len(out) == count + 1:
            break
    if len(out) < count:
        return None
    for k, r in enumerate(out[:count]):
        r["tied"] = any(o is not r and o["days"] == r["days"] for o in out[max(0, k - 1):k + 2])
    out = out[:count]
    if any(not ctx.art(r["item"]) for r in out):
        return None
    return out


def _options(r: dict, rank: int, day, one: str) -> list:
    """The true lines about it, [(kind, text)] for CD.choose; #1 gets one."""
    if rank == 1:
        return [("top", "tied for gone the longest 🤝" if r["tied"] else f"no {one} has been gone longer 👑")]
    return [("years", CD.years_line(r["last"], day)), ("since", f"not in the shop since {r['last'].year} 👀")]


def build(ctx: Ctx, kind: str = "outfit", **_):
    if kind not in KINDS:
        return None
    picked = rows(ctx, kind)
    if not picked:
        return None
    word, cap, one = KINDS[kind]
    rnd = random.Random(ctx.seed * 7 + 5)
    lines = CD.choose([_options(r, rank, ctx.day, one) for rank, r in enumerate(picked, 1)], rnd)
    entries = []
    for rank, r in enumerate(picked, 1):
        it = r["item"]
        facts = [f"last seen: {CD.day_str(r['last'])}"]
        if r["with"]:
            facts.append(f"+{r['with']} more from its set, gone since that day")
        # the records start Oct 30, 2017: before 2018 they can't vouch for the whole count
        since = "" if r["vouched"] else " since oct 2017"
        facts.append(f"in the item shop only once{since}" if r["times"] == 1
                     else f"in the item shop {r['times']} times{since or ' in all'}")
        facts.append(_what(it))
        entries.append(CD.Entry(
            it, CD.Stat("gone for", r["days"], "day" if r["days"] == 1 else "days"), facts,
            lines[rank - 1], tag="tied" if r["tied"] and rank > 1 else "",
            label=f"{r['days']:,} days"))
    comp = CD.cut(ctx, entries, salt="longest_gone", title=f"the {cap} gone the longest 😭",
                  sub="days since each was last in the item shop 🛒", tease="gone from the item shop the longest 👀",
                  ask="which one do you want back? 👇", crown="👑")
    if comp is None:
        return None

    # ------------------------------------------------------------ the post (the classic's lines)
    title_kind = cap.title() if kind != "backpack" else "Back Blings"
    body = "\n".join(f"{num(k)} {r['item']['name']} · last in the Item Shop {r['last']:%b %-d, %Y} ({r['days']:,} days)"
                     for k, r in enumerate(picked, 1))
    head = (f"⏳ Gone the longest — the {cap} gone from the Item Shop the longest, as of {ctx.day_label}\n"
            f"Ranked by days since each was last in the Item Shop, from the Item Shop's own history; "
            f"a set that left together counts once 👇")
    tags = _hashtags("rareskins", "ogfortnite", picked[0]["item"]["name"])
    return Video(
        f"edit_longest_gone_{kind}", comp,
        title=f"Fortnite {title_kind} Gone the Longest From the Item Shop — {ctx.day_label}",
        yt_title=f"Fortnite {title_kind} Gone the Longest: #1 Last in the Item Shop {picked[0]['days']:,} Days Ago #shorts",
        caption=_caption(head + CD.credit(comp), body, "Which one do you want back?", tags),
        hashtags=tags)
