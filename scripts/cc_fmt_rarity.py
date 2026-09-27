"""
Rarity shorts for @usecodebad, from the Item Shop's own history (cc_rarity).

  back_after(ctx)          BACK AFTER N DAYS -- today's shop, the offers that came
                           back after the longest time away (a shop slot)
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


def _card(comp: Comp, ctx: Ctx, it: dict, t0: float, k: int, n: int, head: str, days: int, info: list,
          price: int = 0, tag: str = "", flag: str = "", counter_color: str = ACCENT):
    """One item's screen.
      y 366-600   HEAD label, the days rolling up, DAYS (and the #N tag at the right)
      y ...       the cosmetic, beside the button rail
      ...-1404    name, then `info` lines (30 px), then the price if any"""
    cols = it.get("tile_colors") or [RARITY.get(it["rarity"], "#3a3a44")]
    inner = tile_bg(cols, it["rarity"], t0) + _scrim()
    inner += label(head, SAFE_LEFT, TOP_Y, 32, t0, ACCENT, 800, anim="none", spacing=".16em")
    num_size = 150
    inner += _from(t0 + .25, price_roll(days, SAFE_LEFT, TOP_Y + 44, num_size, t0 + .25, 1.2, counter_color,
                                        suffix="DAYS"))
    if tag:
        tw = (_em(tag) + .84) * 104
        inner += sticker(tag, SAFE_RIGHT_TOP - 26 - tw, TOP_Y - 8, 104, t0 + .35, rot=7)
    head_bottom = TOP_Y + 44 + num_size * .95

    size, lines = _fit(it["name"], TEXT_W, big=96, one_min=70, two_max=76, small=56)
    info_h = size * .92 * lines + 14 + len(info) * 30 * 1.3 + (12 + 80 * .9 if price else 0)
    y_name = INFO_BOTTOM - info_h
    art_top = head_bottom + 30
    art_h = max(340, min(560, y_name - 20 - art_top))
    cy = y_name - 20 - art_h / 2
    inner += character(ctx.art(it), (SAFE_LEFT + SAFE_RIGHT) / 2, cy, art_h, t0 + .1, "pop", .6, "float",
                       it["rarity"], it["name"], maxw=700, trim=True)
    inner += words(it["name"], SAFE_LEFT, y_name, size, t0 + .5, "#fff", .06, "slam", "left", TEXT_W)
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
    inner += progress(t0, t0 + R_LEN, k, n).replace(f"ROUND {k}/{n}", f"ITEM {k}/{n}")
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

def back_after(ctx: Ctx, min_days: int = 180, max_items: int = 6, min_items: int = 3):
    """Today's single offers that came back after at least `min_days` away."""
    hist = history()
    rows = R.back_in_shop(hist, ctx.shop, ctx.day, min_days)
    picks, seen = [], set()
    for row, iid, gone, last, times in rows:
        if row["name"].lower() in seen or row.get("type") not in SHOWN or not ctx.art(row):
            continue
        seen.add(row["name"].lower())
        picks.append((row, gone, last, times))
        if len(picks) == max_items:
            break
    if len(picks) < min_items:
        return None
    n = len(picks)
    top = picks[0]
    comp, content_end = _frame(ctx, n, f"BACK AFTER {top[1]:,} DAYS", "RARE RETURNS IN TODAY'S SHOP",
                               "FINALLY!", picks[0][0], picks[1][0])
    for k, (row, gone, last, times) in enumerate(reversed(picks), 1):
        t0 = HOOK + (k - 1) * R_LEN
        info = [f"{row.get('rarity_label') or row['rarity']} {row['type']}",
                f"LAST IN THE SHOP {_d(last)}",
                f"IN THE ITEM SHOP {times}× BEFORE" if times > 1 else "IN THE ITEM SHOP ONCE BEFORE"]
        flag = "LONGEST WAIT TODAY!" if k == n else ""
        _card(comp, ctx, row, t0, k, n, "BACK AFTER", gone, info, price=int(row["price"]), flag=flag)
    _close(comp, ctx, content_end, "WHICH ONE WERE YOU WAITING FOR?", [p[0] for p in picks])
    body = "\n".join(f"{num(k)} {row['name']} · back after {gone:,} days (last in the shop {last:%b %-d, %Y})"
                     f" · {int(row['price']):,} V-Bucks" for k, (row, gone, last, times) in enumerate(picks, 1))
    tags = _hashtags("fortniteitemshop", "rareskins", top[0]["name"])
    return Video(
        "back_after", comp,
        title=f"Back After {top[1]:,} Days — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"Back in the Fortnite Shop After {top[1]:,} Days: {ctx.day_label} #shorts",
        caption=_caption(f"⏳ BACK AFTER {top[1]:,} DAYS — Fortnite Item Shop, {ctx.day_label}\n"
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
    "marvel": ("outfit", lambda i: (i.get("series") or {}).get("value") == "MARVEL SERIES", "MARVEL SKINS", "Marvel skins"),
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
    IN THE SHOP TODAY when it's in today's shop."""
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
    # the famous (legendary / most sold) first, then show them longest-gone last
    pool.sort(key=lambda r: (-(r[0]["rarity"] == "legendary"), -r[3]))
    picks = sorted(pool[:count], key=lambda r: r[2])
    n = len(picks)
    title = f"CHAPTER {chapter} SEASON {season}"
    comp, content_end = _frame(ctx, n, title, "WHERE ARE THEY NOW?", "OG", picks[-1][0], picks[-2][0],
                               kicker="OG FORTNITE")
    for k, (it, last, days, times, now) in enumerate(picks, 1):
        t0 = HOOK + (k - 1) * R_LEN
        info = [f"{it['rarity_label']} {it['type']}", f"LAST IN THE SHOP {_d(last)}",
                f"IN THE ITEM SHOP {times}× SO FAR" if times > 1 else "IN THE ITEM SHOP ONLY ONCE"]
        flag = "IN THE SHOP TODAY!" if now else ("GONE THE LONGEST!" if k == n else "")
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
