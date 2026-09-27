"""
Rarity shorts for @usecodebad, from the Item Shop's own history (cc_rarity).

  back_after(ctx)          BACK AFTER N DAYS -- today's shop, the offers that came
                           back after the longest time away (a shop slot); items
                           that left and came back together share one card
  rarest(ctx, variant)     RAREST <KIND> RIGHT NOW -- the five gone the longest,
                           counting down (any day; variants by kind, series, chapter)
  og_where(ctx, season)    <CHAPTER 1 SEASON 3>: WHERE ARE THEY NOW? -- that
                           season's skins, and how long each has been gone

Each item gets one screen: a counter rolling up to the days, the cosmetic, its
name, and when it was last in the Item Shop. The standard opening (with the USE
CODE: BAD stamp) and ending, the corner badge, and cc_end_card's card close
them like every other video. All of it inside the apps' safe box (cc_safe).

Truth rules: cc_rarity's. On screen and in captions: "back after N days", "gone
N days", "last in the Item Shop <date>", "in the Item Shop N times" -- all
from shopHistory -- and Epic's own introduction text for the season. Never why
something is gone, never that it won't return, never "rarest ever" beyond "gone
the longest", which is what the ranking is.
"""

import os
from datetime import date

import cc_rarity as R
from cc_fmt_last_chance import _em, _fit, _from
from cc_formats import Ctx, Video, _caption, _hashtags, _hook_scene, _outro_scene, _pad, num
from cc_motion import (ACCENT, RARITY, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, Comp, burst, character,
                       code_badge, disclosure, label, price_roll, progress, sticker, tile_bg, words)

HOOK = 3.0
SHOWN = {"Outfit", "Back Bling", "Pickaxe", "Glider", "Emote"}   # types with a cosmetic to show
R_LEN = 8.4                      # seconds per item
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
TOP_Y = 366
TEXT_W = SAFE_RIGHT - SAFE_LEFT  # 840, beside the button rail
INFO_BOTTOM = SAFE_BOTTOM - 16
RED = "#ff5a5a"
TYPE_ORDER = {"Outfit": 0, "Pickaxe": 1, "Glider": 2, "Back Bling": 3, "Emote": 4}   # which one leads a card
# Shop sections that say where an item sits, not what it is: never a card's title.
GENERIC_SECTIONS = {"", "front page", "fit check", "no sweat", "hype squad", "featured", "daily", "specials",
                    "special offers", "bestsellers", "best sellers", "new", "just in", "top picks", "jam tracks",
                    "trending", "spotlight", "picks for you", "kicks", "cars", "instruments", "gear", "emotes",
                    "outfits", "bundles", "wraps", "lego", "lego kits", "sidekicks"}
# Inter 800 widths in em (capitals, digits, the separators we use), for fitting info lines.
_INTER = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ·,.'-+&:!?()/", (
    .77, .665, .744, .723, .61, .585, .752, .749, .286, .59, .738, .565, .943, .766, .773, .652, .782, .662,
    .66, .677, .727, .77, 1.059, .761, .752, .679, .692, .441, .638, .657, .688, .634, .662, .588, .664, .662,
    .219, .352, .352, .352, .355, .471, .686, .683, .352, .358, .579, .382, .382, .4)))

_hist = None


def history() -> R.History:
    """The shop history, loaded once: fresh from fortnite-api.com on GitHub's
    runners (claims about today need today's data), else CC_HISTORY or the weekly copy."""
    global _hist
    if _hist is None:
        if os.environ.get("CC_HISTORY"):
            _hist = R.History(R.load(os.environ["CC_HISTORY"]))
        else:
            _hist = R.History(R.load(fresh=os.environ.get("GITHUB_ACTIONS") == "true"))
    return _hist


def _d(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def _item(raw: dict) -> dict:
    """A cosmetic from the history list, shaped like the rows the drawing helpers take."""
    imgs = raw.get("images") or {}
    urls = [imgs[k] for k in ("featured", "icon") if imgs.get(k)]
    return {"id": raw["id"], "name": raw["name"], "images": urls, "image": urls[0] if urls else "",
            "rarity": ((raw.get("rarity") or {}).get("value") or "rare").lower(),
            "rarity_label": (raw.get("rarity") or {}).get("displayValue") or "",
            "type": (raw.get("type") or {}).get("displayValue") or "Item",
            "introduction": raw.get("introduction") or {}, "set": (raw.get("set") or {}).get("value") or "",
            "series": (raw.get("series") or {}).get("value") or ""}


def _season_text(it: dict) -> str:
    return ((it.get("introduction") or {}).get("text") or "").replace("Introduced in ", "").rstrip(".")


def _scrim() -> str:
    return ('<div class="full" style="background:linear-gradient(180deg,rgba(0,0,0,.58) 0,'
            'rgba(0,0,0,.34) 22%,rgba(0,0,0,0) 36%,rgba(0,0,0,0) 56%,rgba(0,0,0,.42) 72%,'
            'rgba(0,0,0,.66) 100%)"></div>')


def _label_w(text: str, size: float) -> float:
    """Rendered width of an info line (label(), Inter 800, upper case)."""
    return sum(_INTER.get(ch, .8) for ch in text.upper()) * size


def _names_line(names: list, size: float = 30, width: float = TEXT_W - 8) -> str:
    """As many names as fit on one info line, then +N MORE."""
    names = [nm.upper() for nm in names]
    for keep in range(len(names), 0, -1):
        more = len(names) - keep
        text = " · ".join(names[:keep]) + (f" +{more} MORE" if more else "")
        if _label_w(text, size) <= width:
            return text
    return f"{len(names)} ITEMS"


def _arts(ctx: Ctx, items: list, cy: float, art_h: float, t0: float) -> str:
    """The cosmetic, or up to three side by side, the first in the middle and in
    front. They share the floor line (bottom at cy + art_h / 2) and stay between
    SAFE_LEFT and SAFE_RIGHT."""
    cx = (SAFE_LEFT + SAFE_RIGHT) / 2

    def one(it, x, h, start, maxw):
        return character(ctx.art(it), x, cy + (art_h - h) / 2, h, start, "pop", .6, "float",
                         it["rarity"], it["name"], maxw=maxw, trim=True)
    if len(items) == 1:
        return one(items[0], cx, art_h, t0 + .1, 700)
    if len(items) == 2:
        return one(items[0], cx - 212, art_h * .9, t0 + .1, 400) + one(items[1], cx + 212, art_h * .9, t0 + .24, 400)
    mid, left, right = items[:3]
    return (one(left, cx - 290, art_h * .74, t0 + .1, 260) + one(right, cx + 290, art_h * .74, t0 + .22, 260)
            + one(mid, cx, art_h * .96, t0 + .34, 340))


def _card(comp: Comp, ctx: Ctx, it: dict, t0: float, k: int, n: int, head: str, days: int | None, info: list,
          price: int = 0, tag: str = "", flag: str = "", counter_color: str = ACCENT, big: str = "",
          title: str = "", arts: list = (), unit: str = "ITEM"):
    """One item's screen (or one group's: `arts` up to three cosmetics, `title`
    in place of the name).
      y 366-600   HEAD label, the days rolling up, DAYS (and the #N tag at the right)
      y ...       the cosmetic(s), beside the button rail
      ...-1404    name, then `info` lines (30 px), then the price if any"""
    cols = it.get("tile_colors") or [RARITY.get(it["rarity"], "#3a3a44")]
    inner = tile_bg(cols, it["rarity"], t0) + _scrim()
    inner += label(head, SAFE_LEFT, TOP_Y, 32, t0, ACCENT, 800, anim="none", spacing=".16em")
    num_size = 150
    if big:           # words instead of a count, e.g. TODAY
        inner += words(big, SAFE_LEFT, TOP_Y + 44, num_size, t0 + .25, counter_color, .06, "slam", "left", 700)
    else:
        inner += _from(t0 + .25, price_roll(days, SAFE_LEFT, TOP_Y + 44, num_size, t0 + .25, 1.2, counter_color,
                                            suffix="DAY" if days == 1 else "DAYS"))
    if tag:
        tw = (_em(tag) + .84) * 104
        inner += sticker(tag, SAFE_RIGHT_TOP - 26 - tw, TOP_Y - 8, 104, t0 + .35, rot=7)
    head_bottom = TOP_Y + 44 + num_size * .95

    name = title or it["name"]
    size, lines = _fit(name, TEXT_W, big=96, one_min=70, two_max=76, small=56)
    info_h = size * .92 * lines + 14 + len(info) * 30 * 1.3 + (12 + 80 * .9 if price else 0)
    y_name = INFO_BOTTOM - info_h
    art_top = head_bottom + 30
    art_h = max(340, min(560, y_name - 20 - art_top))
    cy = y_name - 20 - art_h / 2
    inner += _arts(ctx, list(arts) or [it], cy, art_h, t0)
    inner += words(name, SAFE_LEFT, y_name, size, t0 + .5, "#fff", .06, "slam", "left", TEXT_W)
    y = y_name + size * .92 * lines + 14
    for j, line in enumerate(info):
        inner += label(line.upper(), SAFE_LEFT + 4, y, 30, t0 + .7 + j * .15, "#fff", 800)
        y += 30 * 1.3
    if price:
        inner += _from(t0 + 1.2, price_roll(int(price), SAFE_LEFT, y + 12, 80, t0 + 1.2, .7))
    if flag:
        fs = min(56, 420 / (_em(flag) + .84))
        fw = (_em(flag) + .84) * fs
        fx, fy = SAFE_RIGHT_TOP - 20 - fw, head_bottom - fs * 1.4
        inner += _from(t0 + 1.7, burst(fx + fw / 2, fy + 30, t0 + 1.7, ctx.seed + k))
        inner += sticker(flag, fx, fy, fs, t0 + 1.7, rot=-5)
    inner += progress(t0, t0 + R_LEN, k, n).replace(f"ROUND {k}/{n}", f"{unit} {k}/{n}")
    comp.scene(t0, t0 + R_LEN + .3, inner, fade_in=.25, fade_out=.05)
    comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .25, "tick"); comp.cue(t0 + .5, "slam"); comp.cue(t0 + 1.45, "pop")
    if flag:
        comp.cue(t0 + 1.7, "reveal")


def _frame(ctx: Ctx, n: int, title: str, sub: str, stick: str, a: dict, b: dict, kicker: str = ""):
    rlen_total = HOOK + n * R_LEN
    comp = Comp(rlen_total + _pad(rlen_total))
    _hook_scene(comp, ctx, title, sub, stick, HOOK + .3, a, b, kicker=kicker)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop")
    return comp, rlen_total


def _close(comp: Comp, ctx: Ctx, content_end: float, ask: str, items: list):
    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    _outro_scene(comp, ctx, content_end, comp.duration, ask, items[:3])
    comp.add(code_badge(.4))
    comp.add(disclosure())


# ------------------------------------------------------------------ BACK AFTER

def _group_title(hist: R.History, section: str, members: list) -> str:
    """A comeback card's title when several items came back together: the shop
    section when it names something (Resident Evil, not Front Page), else the
    set they all share. Empty when neither does; the lead item names the card."""
    if section.strip().lower() not in GENERIC_SECTIONS:
        return section.strip()
    sets = {((hist.items.get(iid.lower()) or {}).get("set") or {}).get("value") or "" for _, iid, _ in members}
    return sets.pop() if len(sets) == 1 else ""


def back_after(ctx: Ctx, min_days: int = 180, max_cards: int = 6, min_cards: int = 3):
    """Today's offers that came back after at least `min_days` away, one card per
    comeback, longest wait last. Items that were last in the shop the same day
    and came back the same day in the same section are one comeback: one card
    that shows up to three of them and names the rest. Fewer than `min_cards`
    comebacks today: None (the slot makes something else)."""
    hist = history()
    groups, seen = {}, set()
    for row, iid, gone, last, times in R.back_in_shop(hist, ctx.shop, ctx.day, min_days):
        if row["name"].lower() in seen or row.get("type") not in SHOWN or not ctx.art(row):
            continue
        seen.add(row["name"].lower())
        groups.setdefault((gone, last, row.get("section") or ""), []).append((row, iid, times))
    if len(groups) < min_cards:
        return None
    cards = []            # (gone, last, members, title) -- longest wait first
    for (gone, last, section), members in sorted(groups.items(), key=lambda g: (-g[0][0], g[0][1]))[:max_cards]:
        members.sort(key=lambda m: (TYPE_ORDER.get(m[0]["type"], 9), -int(m[0].get("price") or 0)))
        cards.append((gone, last, members, _group_title(hist, section, members) if len(members) > 1 else ""))
    n = len(cards)
    top = cards[0][0]
    comp, content_end = _frame(ctx, n, f"BACK AFTER {top:,} DAYS", "RARE RETURNS IN TODAY'S SHOP",
                               "FINALLY!", cards[0][2][0][0], cards[1][2][0][0])
    for k, (gone, last, members, title) in enumerate(reversed(cards), 1):
        t0 = HOOK + (k - 1) * R_LEN
        row, _, times = members[0]
        flag = "LONGEST WAIT TODAY!" if k == n else ""
        if len(members) == 1:
            info = [f"{row.get('rarity_label') or row['rarity']} {row['type']}",
                    f"LAST IN THE SHOP {_d(last)}",
                    f"IN THE ITEM SHOP {times}× BEFORE" if times > 1 else "IN THE ITEM SHOP ONCE BEFORE"]
            _card(comp, ctx, row, t0, k, n, "BACK AFTER", gone, info, price=int(row["price"]), flag=flag,
                  unit="COMEBACK")
            continue
        names = [m[0]["name"] for m in members]
        if title:
            info = [f"{len(members)} ITEMS BACK TOGETHER", f"LAST IN THE SHOP {_d(last)}", _names_line(names)]
        else:         # no name for the group: the lead item's card, and what came back with it
            info = [f"+ {len(members) - 1} MORE BACK WITH IT", f"LAST IN THE SHOP {_d(last)}",
                    _names_line(names[1:])]
        _card(comp, ctx, row, t0, k, n, "BACK AFTER", gone, info, flag=flag, title=title,
              arts=[m[0] for m in members[:3]], unit="COMEBACK")
    _close(comp, ctx, content_end, "WHICH ONE WERE YOU WAITING FOR?", [c[2][0][0] for c in cards])

    def line(k, gone, last, members, title):
        when = f"back after {gone:,} days (last in the shop {last:%b %-d, %Y})"
        if len(members) == 1:
            row = members[0][0]
            return f"{num(k)} {row['name']} · {when} · {int(row['price']):,} V-Bucks"
        names = ", ".join(m[0]["name"] for m in members[:6]) + (f" +{len(members) - 6} more" if len(members) > 6 else "")
        return f"{num(k)} {f'{title} ({len(members)} items): ' if title else ''}{names} · {when}"
    body = "\n".join(line(k, *c) for k, c in enumerate(cards, 1))
    tags = _hashtags("fortniteitemshop", "rareskins", cards[0][3] or cards[0][2][0][0]["name"])
    return Video(
        "back_after", comp,
        title=f"Back After {top:,} Days — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"Back in the Fortnite Shop After {top:,} Days: {ctx.day_label} #shorts",
        caption=_caption(f"⏳ BACK AFTER {top:,} DAYS — Fortnite Item Shop, {ctx.day_label}\n"
                         f"Today's rare returns, by how long they were gone (the Item Shop's own history) 👇",
                         body, "Which one were you waiting for?", tags),
        hashtags=tags)


# ------------------------------------------------------------------ RAREST

VARIANTS = {
    # key: (kind, filter, title word, caption word)
    "outfits": ("outfit", None, "SKINS", "skins"),
    "pickaxes": ("pickaxe", None, "PICKAXES", "pickaxes"),
    "emotes": ("emote", None, "EMOTES", "emotes"),
    "gliders": ("glider", None, "GLIDERS", "gliders"),
    "backblings": ("backpack", None, "BACK BLINGS", "back blings"),
    "icon": ("outfit", lambda i: (i.get("series") or {}).get("value") == "Icon Series", "ICON SKINS", "Icon Series skins"),
    "ch1": ("outfit", lambda i: str((i.get("introduction") or {}).get("chapter")) == "1", "CHAPTER 1 SKINS", "Chapter 1 skins"),
}


def rarest(ctx: Ctx, variant: str = "outfits", count: int = 5):
    kind, keep, word, cap = VARIANTS[variant]
    hist = history()
    rows, seen_sets = [], set()
    for raw, last, days, times in hist.longest_gone(ctx.day, kind, count * 6, keep):
        it = _item(raw)
        key = (it["set"], last)
        if it["set"] and key in seen_sets:
            continue          # a whole set that left together counts once
        if not ctx.art(it):
            continue
        seen_sets.add(key)
        rows.append((it, last, days, times))
        if len(rows) == count:
            break
    if len(rows) < count:
        return None
    n = len(rows)
    comp, content_end = _frame(ctx, n, f"RAREST {word}", "GONE FROM THE SHOP THE LONGEST", "RIGHT NOW",
                               rows[0][0], rows[1][0], kicker=f"AS OF {ctx.day_label.upper()}")
    for k, (it, last, days, times) in enumerate(reversed(rows), 1):
        t0 = HOOK + (k - 1) * R_LEN
        rank = n - k + 1
        info = [f"{it['rarity_label']} {it['type']} · {_season_text(it)}".replace("Chapter ", "CH ").replace(", Season ", " S"),
                f"LAST IN THE SHOP {_d(last)}",
                "IN THE ITEM SHOP ONLY ONCE" if times == 1 else f"IN THE ITEM SHOP {times}× IN TOTAL"]
        _card(comp, ctx, it, t0, k, n, "GONE FOR", days, info, tag=f"#{rank}",
              flag="GONE THE LONGEST!" if rank == 1 else "", counter_color=RED)
    _close(comp, ctx, content_end, "WHICH ONE DO YOU WANT BACK?", [r[0] for r in rows])
    body = "\n".join(f"{num(k)} {it['name']} · last in the Item Shop {last:%b %-d, %Y} ({days:,} days)"
                     for k, (it, last, days, times) in enumerate(rows, 1))
    tags = _hashtags("rareskins", "ogfortnite", rows[0][0]["name"])
    return Video(
        f"rarest_{variant}", comp,
        title=f"Rarest Fortnite {cap.title()} Right Now — {ctx.day_label}",
        yt_title=f"The Rarest Fortnite {cap.title()} Right Now (Gone {rows[0][2]:,} Days) #shorts",
        caption=_caption(f"💎 RAREST {word} — gone from the Item Shop the longest, as of {ctx.day_label}\n"
                         f"From the Item Shop's own history 👇", body, "Which one do you want back?", tags),
        hashtags=tags)


# ------------------------------------------------------------------ OG: WHERE ARE THEY NOW?

def og_where(ctx: Ctx, chapter: str = "1", season: str = "3", count: int = 6):
    """One season's outfits: each one's days since it was last in the shop, or
    IN THE SHOP TODAY when it's in today's shop. Half are the ones gone the
    longest, half the season's best known (legendary, then the most often
    sold); shortest gap first, so the one gone the longest is the finale."""
    hist = history()
    today_ids = {i.lower() for row in ctx.shop.get("items", []) for i in R.shop_ids(row)}
    pool = []
    for key, days in hist.days.items():
        raw = hist.items[key]
        intro = raw.get("introduction") or {}
        if (raw.get("type") or {}).get("value") != "outfit" or str(intro.get("chapter")) != chapter \
                or str(intro.get("season")) != season:
            continue
        it = _item(raw)
        if not ctx.art(it):
            continue
        past = [d for d in days if d < ctx.day]
        if not past:
            continue
        pool.append((it, past[-1], (ctx.day - past[-1]).days, len(R._runs(past)), key in today_ids))
    if len(pool) < count:
        return None
    longest, sets = [], set()
    for r in sorted((r for r in pool if not r[4]), key=lambda r: -r[2]):
        if r[0]["set"] and (r[0]["set"], r[1]) in sets:
            continue          # a whole set that left together counts once
        sets.add((r[0]["set"], r[1]))
        longest.append(r)
        if len(longest) == count // 2:
            break
    famous = sorted((r for r in pool if r not in longest), key=lambda r: (-(r[0]["rarity"] == "legendary"), -r[3]))
    picks = sorted(longest + famous[:count - len(longest)], key=lambda r: (not r[4], r[2]))
    n = len(picks)
    title = f"CHAPTER {chapter} SEASON {season}"
    comp, content_end = _frame(ctx, n, title, "WHERE ARE THEY NOW?", "OG", picks[-1][0], picks[-2][0],
                               kicker="OG FORTNITE")
    for k, (it, last, days, times, now) in enumerate(picks, 1):
        t0 = HOOK + (k - 1) * R_LEN
        info = [f"{it['rarity_label']} {it['type']}", f"LAST IN THE SHOP {_d(last)}",
                f"IN THE ITEM SHOP {times}× SO FAR" if times > 1 else "IN THE ITEM SHOP ONLY ONCE"]
        flag = "" if now else ("GONE THE LONGEST!" if k == n else "")
        if now:
            info[1] = "BACK IN THE ITEM SHOP RIGHT NOW"
            _card(comp, ctx, it, t0, k, n, "IN THE ITEM SHOP", None, info, big="TODAY")
        else:
            _card(comp, ctx, it, t0, k, n, "LAST SEEN", days, info, flag=flag,
                  counter_color=ACCENT if days < 365 else RED)
    _close(comp, ctx, content_end, "WHICH ONE DID YOU OWN?", [p[0] for p in picks])
    body = "\n".join(f"{num(k)} {it['name']} · last in the Item Shop {last:%b %-d, %Y} ({days:,} days ago)"
                     for k, (it, last, days, times, now) in enumerate(picks, 1))
    tags = _hashtags("ogfortnite", f"chapter{chapter}season{season}", "fortnitenostalgia")
    return Video(
        f"og_where_c{chapter}s{season}", comp,
        title=f"Chapter {chapter} Season {season}: Where Are They Now?",
        yt_title=f"OG Fortnite Chapter {chapter} Season {season} Skins: Where Are They Now? #shorts",
        caption=_caption(f"🕹️ OG FORTNITE — Chapter {chapter} Season {season}: where are they now?\n"
                         f"When each was last in the Item Shop 👇", body, "Which one did you own?", tags),
        hashtags=tags)
