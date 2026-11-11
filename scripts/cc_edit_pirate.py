#!/usr/bin/env python3
"""
PIRATE SHOP ACCESS, as countdown edits (cc_edit_countdown): the owner asked on
2026-11-09 for videos about it, queued through the week beside the daily
lineup. Pirate Shop Access is the rare drop from Treasure Hunters chests in the
One Piece mini-season (from November 1, 2026) that lets you claim Item Shop
cosmetics free for 14 days.

    explainer   5 things to know: where it drops, 14 days, two uses, Epic's
                odds, the squad gets it
    odds        the math on Epic's 1 in 137,500
    onepiece    what the One Piece bundles in the shop cost
    dates       the dates: Nov 1, Dec 5, Dec 15, 2027

Truth: the facts below were checked against several outlets on 2026-11-09
(VGC, Dexerto, Vice, Fortnite Tracker, Dot Esports, games.gg, esports.gg);
only what they agree on is said:
  - it drops from Treasure Hunters chests (Battle Royale), the One Piece
    mini-season that started November 1, 2026
  - one use = 14 days of free Item Shop claims from when you activate it
  - two uses: one in 2026 (activate by December 15), one in 2027
  - Epic's own odds, posted November 7: 1 in 137,500 per chest in a normal
    match. The math from it is exact: 1 - (1 - p)^n
  - when one squad member finds it, the whole squad gets it
Never said, because the outlets disagree: the Treasure Hours boost, the
mini-season's last day (December 4 or 5), what's excluded (passes, gifting,
bundles). Never says a bundle is free.
Prices, bundle contents and the day the One Piece offers leave are the shop's
own rows (cc_shop); an offer whose out_day is D leaves at the next 00:00 UTC.

    python3 scripts/cc_edit_pirate.py --shop shop.json --out DIR [--only explainer,odds] [--no-video]
    python3 scripts/cc_edit_pirate.py --daily --shop shop.json --out DIR [--at 9:30,14:30,20:00]

--daily makes the shop day's three (see "three a day" below): the nightly build
runs it for every day up to END and adds them to that day's manifest.
"""

import argparse
import json
import math
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cc_edit_countdown as CD  # noqa: E402
from cc_common import OUT_DIR, log  # noqa: E402
from cc_formats import Ctx, Video, _caption, _hashtags  # noqa: E402

ODDS = 137_500                      # Epic's: 1 in 137,500 per chest in a normal match (posted Nov 7, 2026)
POSTED = "Nov 7"
CREW = ["Monkey D. Luffy", "Roronoa Zoro", "Sanji", "Nami", "Usopp"]   # #1 first
TAGS = ("pirateshopaccess", "pirateshop", "onepiece")
# The Battle Royale map as it is right now (fortnite-api.com/v1/map, cropped to
# the island): the owner asked on 2026-11-09 for the actual current map in these.
MAP = {"name": "The map right now", "type": "map", "rarity": "rare", "images": [], "image": ""}


def crew(records: list) -> dict:
    """The One Piece outfits from the cosmetics list, shaped like shop rows for
    the tiles: {name: item}."""
    out = {}
    for r in records:
        if r.get("name") in CREW and (r.get("type") or {}).get("value") == "outfit":
            imgs = r.get("images") or {}
            out[r["name"]] = {
                "name": r["name"], "type": "Outfit", "rarity": (r.get("rarity") or {}).get("value", "epic"),
                "rarity_label": (r.get("rarity") or {}).get("displayValue", "Epic"),
                "images": [u for u in (imgs.get("featured"), imgs.get("icon")) if u],
                "image": imgs.get("icon") or "",
            }
    return out


def _chance(n: int) -> float:
    """The chance of at least one find in n chests at Epic's odds."""
    return 1 - (1 - 1 / ODDS) ** n


def _post(fmt: str, comp, title: str, yt_title: str, hook: str, body: str, ask: str,
          narration: dict | None = None) -> Video:
    tags = _hashtags(*TAGS)
    v = Video(fmt, comp, title=title, yt_title=yt_title,
              caption=_caption(hook + CD.credit(comp), body, ask, tags), hashtags=tags)
    v.narration = narration or {}           # the voiceover's lines, per screen (cc_voiceover.narrate)
    return v


# ------------------------------------------------------------------ the voiceover's words
# Written to be said: numbers and dates in words, short sentences, a comma or
# "..." where a person would breathe; the code said as a word ("code bad").

ODDS_SAID = "one in a hundred and thirty-seven thousand, five hundred"
ORDINAL = ("first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth "
           "fourteenth fifteenth sixteenth seventeenth eighteenth nineteenth twentieth").split()


def _said_num(n: int) -> str:
    from cc_ingame import _num_words
    return _num_words(n).replace(" thousand ", " thousand, ")


def _said_vb(n: int) -> str:
    """1,600 -> 'sixteen hundred', 4,000 -> 'four thousand' (how people say prices)."""
    from cc_ingame import _num_words
    if n % 1000 == 0:
        return f"{_num_words(n // 1000)} thousand"
    if n % 100 == 0 and n < 10000:
        return f"{_num_words(n // 100)} hundred"
    return _said_num(n)


def _said_day(d: date) -> str:
    n = d.day
    word = ORDINAL[n - 1] if n <= 20 else ("twenty-" + ORDINAL[n - 21] if n < 30 else
                                             "thirtieth" if n == 30 else "thirty-first")
    return f"{d:%B} {word}"


def _short(name: str) -> str:
    return name.split()[-1]                 # "Monkey D. Luffy" -> "Luffy", "Roronoa Zoro" -> "Zoro"


def _and(names: list) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


# ------------------------------------------------------------------ the videos

def explainer(ctx: Ctx, cast: dict) -> Video | None:
    if len(cast) < 5:
        return None
    c = [cast[n] for n in CREW]
    entries = [
        CD.Entry(c[0], CD.Stat("if one teammate finds it", text="the whole squad gets it", guess="???"),
                 ["every teammate gets access", "so squad up"], "squad up 🏴‍☠️",
                 name="squad bonus", label="squad gets it"),
        CD.Entry(c[1], CD.Stat("epic's odds per chest", text=f"1 in {ODDS:,}", guess="1 in ?"),
                 ["in a normal match", f"posted by epic on {POSTED.lower()}"], "that's insanely rare 😭",
                 name="the odds", label=f"1 in {ODDS:,}"),
        CD.Entry(c[2], CD.Stat("you can use it", value=2, unit="times"),
                 ["once in 2026", "once in 2027"], "activate the 2026 one by dec 15 ⏰",
                 name="two uses", label="2 uses"),
        CD.Entry(c[3], CD.Stat("one use gives you", value=14, unit="days"),
                 ["of free item shop claims", "from when you activate it"], "the item shop, free 😳",
                 name="what it does", label="14 days"),
        CD.Entry(MAP, CD.Stat("it drops from", text="treasure hunters chests", guess="??? chests"),
                 ["in battle royale", "on the map right now 🗺️"], "a random drop: keep looting 🏴‍☠️",
                 name="where it drops", label="treasure chests"),
    ]
    comp = CD.cut(ctx, entries, salt="pirate_explainer", title="pirate shop access: 5 things to know 🏴‍☠️",
                  sub="fortnite's free item shop, explained", tease="the best part 👀",
                  ask="have you found it yet? 👇", crown="🏴‍☠️")
    if comp is None:
        return None
    body = ("1️⃣ If one teammate finds it, the whole squad gets it\n"
            f"2️⃣ Epic's odds: 1 in {ODDS:,} per chest in a normal match (posted {POSTED})\n"
            "3️⃣ Two uses: one in 2026 (activate by Dec 15) and one in 2027\n"
            "4️⃣ One use = 14 days of free Item Shop claims\n"
            "5️⃣ It drops from Treasure Hunters chests (the One Piece mini-season, since Nov 1)")
    return _post("edit_pirate_explainer", comp,
                 title="Pirate Shop Access — 5 Things to Know (Fortnite)",
                 yt_title="Fortnite Pirate Shop Access: 5 Things to Know #shorts",
                 hook="🏴‍☠️ PIRATE SHOP ACCESS — 5 things to know\n"
                      "Fortnite's free Item Shop, from the Treasure Hunters chests 👇",
                 body=body, ask="Have you found it yet?", narration={
                     "hook": "Pirate Shop Access. Here's what you need to know.",
                     5: "Number five. It drops from Treasure Hunters chests in Battle Royale, "
                        "so every one you open is a shot at it.",
                     4: "Number four. One use gives you fourteen days of free Item Shop claims, "
                        "starting the moment you activate it.",
                     3: "Number three. You actually get two uses. One this year, and one in twenty twenty-seven. "
                        "Just activate this year's by December fifteenth.",
                     2: f"Number two. The odds. Epic says it's {ODDS_SAID}, per chest. Yeah... it's rare.",
                     "build": "And number one...",
                     1: "If one teammate finds it, your whole squad gets it. So squad up!",
                     "outro": "Have you found it yet? Let me know in the comments.",
                     "end": "And if you're buying anything in the shop, use code bad!",
                 })


def odds(ctx: Ctx, cast: dict) -> Video | None:
    if len(cast) < 5:
        return None
    c = [cast[n] for n in CREW]
    half = math.log(2) / -math.log(1 - 1 / ODDS)             # chests for a 50% chance
    half = int(round(half, -2))                               # 95,300
    after = round(_chance(ODDS) * 100)                        # 63
    night = _chance(200)                                      # a squad of 4 opening 50 chests each
    per_night = f"{night * 100:.2f}%"                         # 0.15%
    one_in = int(round(1 / night, -1))                        # about 1 in 690 nights
    entries = [
        CD.Entry(c[0], CD.Stat("if one teammate finds it", text="everyone gets it", guess="???"),
                 ["the whole squad gets access", "every teammate's chests count for you"], "squad up 🏴‍☠️",
                 name="the good news", label="squad gets it"),
        CD.Entry(c[1], CD.Stat("chance in one night", text=per_night, guess="?%"),
                 ["4 players, 50 chests each", f"about 1 in {one_in:,} nights"], "squad up anyway 🏴‍☠️",
                 name="one squad night", label=f"{per_night} a night"),
        CD.Entry(MAP, CD.Stat("you'd need about", value=half, unit="chests"),
                 ["for a 50/50 chance", "every chest is its own roll"], "that's a lot of chests 😭",
                 name="a coin flip", label=f"~{half:,} chests"),
        CD.Entry(c[3], CD.Stat("your chance would be about", text=f"{after}%", guess="?%"),
                 ["not 100%", "the odds don't add up like that"], "still no guarantee 💀",
                 name=f"{ODDS:,} chests", label=f"{after}%"),
        CD.Entry(c[4], CD.Stat("epic's odds", text=f"1 in {ODDS:,}", guess="1 in ?"),
                 ["per chest, in a normal match", f"posted {POSTED.lower()}"], "rarer than you think 😭",
                 name="per chest", label=f"1 in {ODDS:,}"),
    ]
    comp = CD.cut(ctx, entries, salt="pirate_odds", title="how rare is pirate shop access? 🏴‍☠️",
                  sub="the math on epic's odds 🧮", tease="the good news 👀",
                  ask="how many chests have you opened? 👇", crown="🏴‍☠️")
    if comp is None:
        return None
    body = ("1️⃣ If one teammate finds it, the whole squad gets it\n"
            f"2️⃣ A squad opening 200 chests a night: about a {per_night} chance a night\n"
            f"3️⃣ For a 50/50 chance: about {half:,} chests\n"
            f"4️⃣ After {ODDS:,} chests: still only about a {after}% chance\n"
            f"5️⃣ Epic's odds: 1 in {ODDS:,} per chest in a normal match (posted {POSTED})")
    narration = {
        "hook": "How rare is Pirate Shop Access? Let's do the math.",
        5: f"Number five. Epic says the odds are {ODDS_SAID}, per chest, in a normal match.",
        4: f"Number four. Open {ODDS_SAID.replace('one in a', 'a')} chests... "
           f"and you'd still only have about a {_said_num(after)} percent chance.",
        3: f"Number three. For a coin flip, a fifty-fifty shot, you'd need about {_said_num(half)} chests.",
        2: "Number two. Say your squad opens two hundred chests a night. "
           "That's about a zero point one five percent chance... per night.",
        "build": "But here's the good news...",
        1: "If anyone in your squad finds it, everyone gets it!",
        "outro": "So, how many chests have you opened so far?",
        "end": "And if you're shopping today, use code bad!",
    }
    if per_night != "0.15%":
        narration[2] = (f"Number two. Say your squad opens two hundred chests a night. That's about a "
                        f"{per_night.rstrip('%')} percent chance... per night.")
    return _post("edit_pirate_odds", comp,
                 title="How Rare Is Pirate Shop Access? The Math (Fortnite)",
                 yt_title=f"How Rare Is Fortnite's Pirate Shop Access? The Math on 1 in {ODDS:,} #shorts",
                 hook="🏴‍☠️ HOW RARE IS PIRATE SHOP ACCESS? The math on Epic's odds\n"
                      f"Epic's posted odds: 1 in {ODDS:,} per chest in a normal match 👇",
                 body=body, ask="How many chests have you opened?", narration=narration)


def _bundle_bits(row: dict) -> str:
    kinds = []
    for t in row.get("member_types") or []:
        t = str(t).lower()
        if t not in kinds:
            kinds.append(t)
    return ", ".join(kinds)


def onepiece(ctx: Ctx, cast: dict) -> Video | None:
    """The One Piece bundles in the shop, priciest first: the outfit bundles
    and the two big ones."""
    rows = [r for r in ctx.shop.get("items", []) if r.get("section") == "One Piece" and r.get("is_bundle")]
    if not rows or len(cast) < 5:
        return None
    out_days = {r.get("out_day") for r in rows}
    if len(out_days) != 1 or not next(iter(out_days)):
        return None
    leaves = date.fromisoformat(next(iter(out_days)))
    picks = []
    for r in sorted(rows, key=lambda r: (-(r.get("price") or 0), -(r.get("bundle_size") or 0))):
        outfits = [n for n, t in zip(r.get("member_names") or [], r.get("member_types") or [])
                   if str(t).lower() == "outfit"]
        if not outfits or any(set(outfits) == set(p[1]) for p in picks):
            continue
        picks.append((r, outfits))
    all_picks, picks = picks, picks[:5]
    if len(picks) < 5:
        return None
    prices = [r["price"] for r, _ in picks]
    entries = []
    for rank, (r, outfits) in enumerate(picks, 1):
        face = cast.get(outfits[0]) or cast[CREW[0]]
        who = " + ".join(o.split()[-1] for o in outfits) if len(outfits) > 1 else outfits[0]
        reg = r.get("regular_price") or r["price"]
        facts = [f"{r.get('bundle_size')} items: {_bundle_bits(r)}"]
        if reg > r["price"]:
            facts.append(f"regular {reg:,} v-bucks")
        facts.append(f"in the shop until {leaves:%b} {leaves.day}".lower())
        also = [o for rr, outs in all_picks[5:] if rr["price"] == r["price"] for o in outs]
        if rank == 5 and also:
            facts.insert(1, f"also {r['price']:,}: " + " and ".join(o.lower() for o in also))
        tied = prices.count(r["price"]) > 1 or (rank == 5 and bool(also))
        entries.append(CD.Entry(face, CD.Stat("the bundle costs", value=r["price"], unit="v-bucks"), facts,
                                "the biggest one piece bundle 🏴‍☠️" if rank == 1 else f"the {who.lower()} bundle 🏴‍☠️",
                                name=(f"{r.get('bundle_size')}-item bundle" if len(outfits) > 1 else outfits[0]),
                                tag="tied" if tied and rank > 1 else "", label=f"{r['price']:,} v-bucks"))
    comp = CD.cut(ctx, entries, salt="pirate_onepiece", title="what the one piece skins cost 🏴‍☠️",
                  sub="every one piece bundle in the item shop", tease="the biggest one 👀",
                  ask="would you use pirate shop access on these? 👇", crown="🏴‍☠️")
    if comp is None:
        return None
    lines = []
    for k, (r, outs) in enumerate(all_picks, 1):
        what = f"{r.get('bundle_size')}-item bundle with {', '.join(outs)}" if len(outs) > 1 else f"{outs[0]} bundle"
        reg = r.get("regular_price") or 0
        lines.append(f"▸ {what} · {r['price']:,} V-Bucks" + (f" (regular {reg:,})" if reg > r["price"] else ""))
    body = "\n".join(lines)
    body += f"\n\nIn the Item Shop until {leaves:%b} {leaves.day} (the 7 PM ET reset)."
    words = ["one", "two", "three", "four", "five"]
    narration = {"hook": "Here's what every One Piece bundle costs.",
                 "build": "And number one...",
                 "outro": "Would you spend your Pirate Shop Access on these?",
                 "end": "And if you're buying them, use code bad!"}
    cap = lambda t: t[0].upper() + t[1:]                       # noqa: E731
    for rank, (r, outs) in enumerate(picks, 1):
        who = [_short(o) for o in outs]
        price, reg = r["price"], r.get("regular_price") or 0
        size = _said_num(r.get("bundle_size"))
        if len(outs) > 1 and rank == 1:
            line = f"The {size}-item bundle! {_and(who)}, for {_said_vb(price)} V-Bucks."
        elif len(outs) > 1:
            line = f"The {size}-item bundle with {_and(who)} is {_said_vb(price)} V-Bucks."
        else:
            line = f"{who[0]}'s bundle is {_said_vb(price)} V-Bucks, with {size} items."
            also = [_short(o) for rr, os in all_picks[5:] if rr["price"] == price for o in os]
            if rank == 5 and also:
                line += f" And {_and(also)}? {cap(_said_vb(price))} too."
        if reg > price:
            line += f" Regular price? {cap(_said_vb(reg))}."
        narration[rank] = line if rank == 1 else f"Number {words[rank - 1]}. {line}"
    return _post("edit_pirate_onepiece", comp,
                 title="What the One Piece Skins Cost — Fortnite Item Shop",
                 yt_title="What Fortnite's One Piece Skins Cost: Every Bundle #shorts",
                 hook="🏴‍☠️ WHAT THE ONE PIECE SKINS COST — every One Piece bundle in the Fortnite Item Shop 👇",
                 body=body, ask="Would you use Pirate Shop Access on these?", narration=narration)


def dates(ctx: Ctx, cast: dict) -> Video | None:
    rows = [r for r in ctx.shop.get("items", []) if r.get("section") == "One Piece"]
    out_days = {r.get("out_day") for r in rows}
    if len(cast) < 5 or len(out_days) != 1 or not next(iter(out_days)):
        return None
    leaves = date.fromisoformat(next(iter(out_days)))
    c = [cast[n] for n in CREW]
    entries = [
        CD.Entry(c[0], CD.Stat("your second use comes in", text="2027", guess="20??"),
                 ["another 14 days", "of free item shop claims"], "two free shops 😳",
                 name="use #2", label="2027"),
        CD.Entry(c[1], CD.Stat("activate your 2026 use by", text="dec 15", guess="dec ?"),
                 ["then you get 14 days", "of free item shop claims"], "don't sit on it ⏰",
                 name="the 2026 deadline", label="dec 15"),
        CD.Entry(c[2], CD.Stat("one piece leaves the shop", text=f"{leaves:%b} {leaves.day}".lower(), guess="??"),
                 ["at the 7 pm et reset", "every one piece bundle"], "grab them before they go ⏰",
                 name="one piece skins", label=f"{leaves:%b} {leaves.day}".lower()),
        CD.Entry(c[3], CD.Stat("one use lasts", value=14, unit="days"),
                 ["from when you activate it", "pick your moment"], "time it right 🧠",
                 name="your window", label="14 days"),
        CD.Entry(MAP, CD.Stat("treasure hunters started", text="nov 1", guess="nov ?"),
                 ["the one piece mini-season", "on the map right now 🗺️"], "the hunt is on 🏴‍☠️",
                 name="it started", label="nov 1"),
    ]
    comp = CD.cut(ctx, entries, salt="pirate_dates", title="pirate shop access: the dates ⏰",
                  sub="don't miss these 🏴‍☠️", tease="the best one 👀",
                  ask="when would you use yours? 👇", crown="🏴‍☠️")
    if comp is None:
        return None
    body = ("1️⃣ Your second use comes in 2027: another 14 days\n"
            "2️⃣ Activate your 2026 use by Dec 15\n"
            f"3️⃣ The One Piece bundles leave the Item Shop {leaves:%b} {leaves.day} (7 PM ET reset)\n"
            "4️⃣ One use lasts 14 days from when you activate it\n"
            "5️⃣ Treasure Hunters, the One Piece mini-season, started Nov 1")
    return _post("edit_pirate_dates", comp,
                 title="Pirate Shop Access — The Dates (Fortnite)",
                 yt_title="Fortnite Pirate Shop Access: The Dates You Can't Miss #shorts",
                 hook="⏰ PIRATE SHOP ACCESS — the dates you can't miss 👇", body=body,
                 ask="When would you use yours?", narration={
                     "hook": "Pirate Shop Access dates you can't miss.",
                     5: "Number five. It all started November first, with Treasure Hunters, the One Piece mini-season.",
                     4: "Number four. Each use lasts fourteen days from the moment you activate it, "
                        "so pick your moment.",
                     3: f"Number three. The One Piece bundles leave the Item Shop on {_said_day(leaves)}, "
                        "at the seven PM Eastern reset.",
                     2: "Number two. Activate your twenty twenty-six use by December fifteenth. Don't sit on it.",
                     "build": "And number one...",
                     1: "You get a second use in twenty twenty-seven! Another fourteen days of free Item Shop claims.",
                     "outro": "So, when would you use yours?",
                     "end": "And if you're buying anything, use code bad!",
                 })


BUILDERS = {"explainer": explainer, "odds": odds, "onepiece": onepiece, "dates": dates}


# ------------------------------------------------------------------ three a day, until it leaves the shop
# The owner, 2026-11-11: "make about 3 extra videos for today and everyday until it
# gets removed from the shop regarding this topic". Each day D gets two about D's
# shop (what to claim with it) and one about Pirate Shop Access itself, with that
# day's numbers. The nightly build (cc_nightly.pirate) makes them right after the
# five daily videos and adds them to D's folder and manifest, so the posting
# Routine schedules them with the rest. The last day is END, the One Piece offers'
# last day in the shop (their out_day; most outlets also end the mini-season then),
# and a day whose shop has no One Piece offers gets none.
#
# On claiming, they say only what the guides agree on (checked 2026-11-11: Vice,
# Dot Esports, Beebom, Yahoo, GameRant): single cosmetics sold for V-Bucks -- outfits,
# emotes, pickaxes, gliders, back blings, wraps, contrails -- and nothing about
# bundles (disputed), sidekicks (said to be limited) or shoes; never "free" about a
# bundle. Treasure Hours odds stay out: the outlets' multipliers disagree.

END = date(2026, 12, 5)
STARTED = date(2026, 11, 1)
ACTIVATE_BY = date(2026, 12, 15)
ANCHOR = date(2026, 11, 11)                 # the first day: the rotations count from it
CLAIMABLE = ("Outfit", "Emote", "Pickaxe", "Glider", "Back Bling", "Wrap", "Contrail")
KIND = {"Outfit": "outfit", "Emote": "emote", "Pickaxe": "pickaxe", "Glider": "glider",
        "Back Bling": "back bling", "Wrap": "wrap", "Contrail": "contrail"}
WORDS = ["one", "two", "three", "four", "five"]
NUM = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
REACTS = ["would you claim it? 🏴‍☠️", "big pickup 😳", "a clean one 🔥", "worth a claim 👀", "don't sleep on it 💤"]
MAP_API = "https://fortnite-api.com/v1/map"
ISLAND = (450 / 2048, 512 / 2048, 1690 / 2048, 1752 / 2048)    # the island in map_en.png (Nov 2026)
HAVE_MAP = False                            # main() sets it when the map's picture is there


def fetch_map(dest: Path) -> Path | None:
    """The Battle Royale map as it is now, with its place names (fortnite-api.com's
    map_en.png), cropped to the island. None when it can't be had."""
    import io
    import urllib.request
    try:
        def get(url):
            req = urllib.request.Request(url, headers={"User-Agent": "usecodebad"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        from PIL import Image
        im = Image.open(io.BytesIO(get(json.loads(get(MAP_API))["data"]["images"]["pois"]))).convert("RGB")
        w, h = im.size
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.crop(tuple(round(f * s) for f, s in zip(ISLAND, (w, h, w, h)))).save(dest)
        return dest
    except Exception as e:  # noqa: BLE001 - the videos work without it
        log(f"map: couldn't get the current map ({e!r})"[:200])
        return None


def _claimable(shop: dict) -> list:
    """D's single offers of the kinds every guide agrees it covers, one per name:
    priciest first, then the one leaving soonest."""
    rows = [r for r in shop.get("items", []) if not r.get("is_bundle") and r.get("price")
            and r.get("type") in CLAIMABLE and r.get("name") and (r.get("images") or r.get("image"))]
    out, seen = [], set()
    for r in sorted(rows, key=lambda r: (-r["price"], r.get("out_day") or "9999-12-31",
                                         CLAIMABLE.index(r["type"]), r["name"])):
        if r["name"] not in seen:
            seen.add(r["name"])
            out.append(r)
    return out


def _spoken(name: str) -> str:
    """An item's name the way it's said: no brackets ("Rush (Mega Man)" -> "Rush")."""
    n = re.sub(r"\s*\([^)]*\)", "", name).replace("$", "S").replace("&", " and ")
    return re.sub(r"\s+", " ", n).strip() or name


def _a(word: str) -> str:
    return ("an " if word[:1] in "aeiou" else "a ") + word


def _leaves(r: dict, day: date) -> str:
    out = r.get("out_day")
    if not out:
        return "in today's item shop"
    d = date.fromisoformat(out)
    if d <= day:
        return "leaves the shop tonight"
    if d == day + timedelta(days=1):
        return "leaves the shop tomorrow"
    return f"in the shop until {d:%b} {d.day}".lower()


def _said_leaves(r: dict, day: date) -> str:
    out = date.fromisoformat(r["out_day"]) if r.get("out_day") else None
    if out and out <= day:
        return " It leaves the shop tonight."
    if out and out == day + timedelta(days=1):
        return " It leaves tomorrow."
    if r.get("in_day") == day.isoformat():
        return " It's new today."
    return ""


def _crew(cast: dict, day: date) -> list:
    """The five One Piece outfits, a different one up front each day."""
    k = (day - ANCHOR).days % len(CREW)
    return [cast[n] for n in CREW[k:] + CREW[:k]]


def _pick(ctx: Ctx, rows: list, *, fmt: str, salt: str, on_title: str, sub: str, tease: str, on_ask: str,
          title: str, yt_title: str, hook: str, said_hook, said_build, ask: str, said_ask,
          said_end="And if you're buying instead, use code bad!") -> Video | None:
    """A countdown of five items from the shop, priciest last, for someone holding
    Pirate Shop Access: each one's kind, price and when it leaves."""
    if len(rows) < 5:
        return None
    day, picks = ctx.day, rows[:5]
    entries, narration = [], {"hook": said_hook, "build": said_build, "outro": said_ask, "end": said_end}
    for rank, r in enumerate(picks, 1):
        kind = KIND[r["type"]]
        where = (r.get("section") or "").strip().lower()
        facts = [f"{kind} · {where}" if where else kind, _leaves(r, day)]
        react = ("last chance ⏰" if facts[1].endswith("tonight") else
                 "brand new 👀" if r.get("in_day") == day.isoformat() else
                 REACTS[(rank + (day - ANCHOR).days) % len(REACTS)])
        entries.append(CD.Entry(r, CD.Stat("worth", r["price"], "v-bucks"), facts, react,
                                name=r["name"], label=f"{r['price']:,} v-bucks"))
        name, worth = _spoken(r["name"]), f"worth {_said_vb(r['price'])} V-Bucks."
        ways = ((f"{name}! {_a(kind).capitalize()}, {worth}",) if rank == 1 else
                (f"Number {WORDS[rank - 1]}. {name}, {_a(kind)}, {worth}",))
        narration[rank] = tuple(dict.fromkeys(tuple(w + _said_leaves(r, day) for w in ways) + ways))  # w/o "it leaves..." if need be
    comp = CD.cut(ctx, entries, salt=salt, title=on_title, sub=sub, tease=tease, ask=on_ask, crown="🏴‍☠️")
    if comp is None:
        return None
    body = "\n".join(f"{NUM[i]} {r['name']} · {r['type']} · {r['price']:,} V-Bucks"
                     + ("" if _leaves(r, day).startswith("in ") else f" · {_leaves(r, day)}")
                     for i, r in enumerate(picks))
    return _post(fmt, comp, title=title, yt_title=yt_title, hook=hook, body=body, ask=ask, narration=narration)


def _dates(day: date) -> tuple:
    return f"{day:%B} {day.day}", f"{day:%B} {day.day}, {day.year}"


def grabs(ctx: Ctx, cast: dict) -> Video | None:
    """Got Pirate Shop Access? Today's five best grabs: the priciest outfit, emote,
    pickaxe, glider and back bling in the shop (another kind when one is missing)."""
    d, full = _dates(ctx.day)
    rows = _claimable(ctx.shop)
    picks, used = [], set()
    for kind in CLAIMABLE:                    # the priciest of each kind...
        r = next((r for r in rows if r["type"] == kind), None)
        if r and len(picks) < 5:
            picks.append(r)
            used.add(r["name"])
    picks += [r for r in rows if r["name"] not in used][:5 - len(picks)]   # ...topped up if a kind is missing
    picks.sort(key=rows.index)
    kinds = _and(sorted({KIND[r["type"]] for r in picks}, key=lambda k: list(KIND.values()).index(k)))
    return _pick(ctx, picks, fmt="edit_pirate_grabs", salt=f"pirate_grabs_{ctx.day}",
                 on_title="got pirate shop access? today's 5 best grabs 🏴‍☠️",
                 sub=f"the priciest of each kind in the item shop, {ctx.day:%b} {ctx.day.day}".lower(),
                 tease="the priciest one 👀", on_ask="what are you claiming first? 👇",
                 title=f"Pirate Shop Access: Today's 5 Best Grabs — Fortnite Item Shop, {d}",
                 yt_title=f"Got Pirate Shop Access? Today's 5 Best Fortnite Shop Grabs ({d}) #shorts",
                 hook=f"🏴‍☠️ GOT PIRATE SHOP ACCESS? Today's 5 best grabs — Fortnite Item Shop, {full}\n"
                      f"The priciest of each kind in today's shop: {kinds} 👇",
                 said_hook=("Got Pirate Shop Access? Here are today's five best grabs.",
                            "Pirate Shop Access? Today's five best grabs.", "Today's five best grabs!"),
                 said_build=("And the priciest one today...", "And number one..."),
                 ask="What are you claiming first?", said_ask="So, which one are you claiming first?")


# (key, kinds or None, on screen, in titles, said)
SPOTLIGHT = [
    ("skins", ("Outfit",), "skins", "Skins", "skins"),
    ("emotes", ("Emote",), "emotes", "Emotes", "emotes"),
    ("leaving", None, "", "", ""),
    ("pickaxes", ("Pickaxe",), "pickaxes", "Pickaxes", "pickaxes"),
    ("backblings", ("Back Bling",), "back blings", "Back Blings", "back blings"),
    ("gliders", ("Glider", "Wrap", "Contrail"), "gliders & wraps", "Gliders & Wraps", "gliders and wraps"),
]


def spotlight(ctx: Ctx, cast: dict) -> Video | None:
    """Got Pirate Shop Access? One kind of item from today's shop, a different kind
    each day (or what leaves tonight and tomorrow); the next kind when there
    aren't five."""
    day, everything = ctx.day, _claimable(ctx.shop)
    d, full = _dates(day)
    k = (day - ANCHOR).days % len(SPOTLIGHT)
    for key, kinds, on, in_title, said in SPOTLIGHT[k:] + SPOTLIGHT[:k]:
        if key == "leaving":
            rows = [r for r in everything if r.get("out_day")
                    and date.fromisoformat(r["out_day"]) <= day + timedelta(days=1)]
            if len(rows) < 5:
                continue
            return _pick(ctx, rows, fmt="edit_pirate_leaving", salt=f"pirate_leaving_{day}",
                         on_title="got pirate shop access? claim these before they leave ⏰",
                         sub="leaving the item shop tonight and tomorrow", tease="the priciest one 👀",
                         on_ask="which one are you grabbing? 👇",
                         title=f"Pirate Shop Access: Claim These Before They Leave — Fortnite Item Shop, {d}",
                         yt_title=f"Got Pirate Shop Access? Claim These Before They Leave ({d}) #shorts",
                         hook=f"⏰ GOT PIRATE SHOP ACCESS? Claim these before they leave — Fortnite Item Shop, {full}\n"
                              "The priciest items leaving the shop tonight and tomorrow 👇",
                         said_hook=("Got Pirate Shop Access? Claim these before they leave the shop.",
                                    "Claim these before they leave!"),  # (short already)
                         said_build=("And the priciest one...", "And number one..."),
                         ask="Which one are you grabbing?", said_ask="Which one are you grabbing?")
        rows = [r for r in everything if r["type"] in kinds]
        if len(rows) < 5:
            continue
        return _pick(ctx, rows, fmt=f"edit_pirate_{key}", salt=f"pirate_{key}_{day}",
                     on_title=f"got pirate shop access? today's best {on} 🏴‍☠️",
                     sub=f"the priciest {on} in the item shop, {day:%b} {day.day}".lower(),
                     tease="the priciest one 👀", on_ask="which one would you grab? 👇",
                     title=f"Pirate Shop Access: Today's Best {in_title} — Fortnite Item Shop, {d}",
                     yt_title=f"Got Pirate Shop Access? Today's Best Fortnite {in_title} ({d}) #shorts",
                     hook=f"🏴‍☠️ GOT PIRATE SHOP ACCESS? Today's best {on} — Fortnite Item Shop, {full}\n"
                          f"The priciest {on} in today's shop 👇",
                     said_hook=(f"Got Pirate Shop Access? Here are today's best {said}.",
                                f"Pirate Shop Access? Today's best {said}.", f"Today's best {said}!"),
                     said_build="And number one...",
                     ask="Which one would you grab?", said_ask="Which one would you grab?")
    return None


def _one_piece_leaves(shop: dict) -> date | None:
    outs = {r.get("out_day") for r in shop.get("items", []) if r.get("section") == "One Piece"}
    return date.fromisoformat(next(iter(outs))) if len(outs) == 1 and next(iter(outs)) else None


def _in_days(n: int) -> str:
    return "today" if n == 0 else "tomorrow" if n == 1 else f"in {_said_num(n)} days"


def countdown(ctx: Ctx, cast: dict) -> Video | None:
    """Pirate Shop Access: the countdown -- the day of the mini-season, the days
    left for the One Piece offers and to activate this year's use."""
    day = ctx.day
    leaves = _one_piece_leaves(ctx.shop)
    if len(cast) < 5 or leaves is None:
        return None
    n_day, n_shop, n_act = (day - STARTED).days + 1, (leaves - day).days, (ACTIVATE_BY - day).days
    if n_shop < 0 or n_act < 1:
        return None
    c = _crew(cast, day)
    shop_stat = (CD.Stat("one piece leaves the shop", text="today", guess="??") if n_shop == 0 else
                 CD.Stat("one piece leaves the shop in", n_shop, "days" if n_shop > 1 else "day"))
    entries = [
        CD.Entry(c[0], CD.Stat("your second use comes in", text="2027", guess="20??"),
                 ["another 14 days", "of free item shop claims"], "two free shops 😳", name="use #2", label="2027"),
        CD.Entry(c[1], CD.Stat("activate your 2026 use within", n_act, "days" if n_act > 1 else "day"),
                 ["the deadline is dec 15", "then you get 14 days"], "don't sit on it ⏰",
                 name="the 2026 deadline", label=f"{n_act} days left"),
        CD.Entry(c[2], shop_stat, [f"on {leaves:%b} {leaves.day}".lower(), "at the 7 pm et reset"],
                 "grab them before they go ⏰", name="one piece skins", label=f"{leaves:%b} {leaves.day}".lower()),
        CD.Entry(c[3], CD.Stat("one use lasts", 14, "days"), ["from when you activate it", "pick your moment"],
                 "time it right 🧠", name="one use", label="14 days"),
        CD.Entry(MAP if HAVE_MAP else c[4], CD.Stat("treasure hunters", text=f"day {n_day}", guess="day ?"),
                 ["the one piece mini-season", "started nov 1"], "keep looting 🏴‍☠️",
                 name="the mini-season", label=f"day {n_day}"),
    ]
    comp = CD.cut(ctx, entries, salt=f"pirate_countdown_{day}", title="pirate shop access: the countdown ⏳",
                  sub=f"where things stand on {day:%b} {day.day}".lower(), tease="don't miss #1 👀",
                  ask="when are you using yours? 👇", crown="🏴‍☠️")
    if comp is None:
        return None
    d, full = _dates(day)
    left = "today" if n_shop == 0 else "tomorrow" if n_shop == 1 else f"in {n_shop} days"
    body = ("1️⃣ Your second use comes in 2027: another 14 days\n"
            f"2️⃣ Activate your 2026 use within {n_act} day{'s' if n_act > 1 else ''} (by Dec 15)\n"
            f"3️⃣ The One Piece skins leave the Item Shop {left} ({leaves:%b} {leaves.day}, the 7 PM ET reset)\n"
            "4️⃣ One use lasts 14 days from when you activate it\n"
            f"5️⃣ Day {n_day} of Treasure Hunters, the One Piece mini-season (since Nov 1)")
    return _post("edit_pirate_countdown", comp,
                 title=f"Pirate Shop Access: The Countdown — {d} (Fortnite)",
                 yt_title=f"Fortnite Pirate Shop Access: {n_act} Days Left to Activate ({d}) #shorts",
                 hook=f"⏳ PIRATE SHOP ACCESS — the countdown, {full} 👇",
                 body=body, ask="When are you using yours?", narration={
                     "hook": ("Pirate Shop Access. Here's your countdown.", "Your Pirate Shop Access countdown."),
                     5: f"Number five. It's day {_said_num(n_day)} of Treasure Hunters, the One Piece mini-season.",
                     4: "Number four. One use lasts fourteen days, from the moment you activate it.",
                     3: (f"Number three. The One Piece skins leave the Item Shop {_in_days(n_shop)}"
                         + (f", on {_said_day(leaves)}." if n_shop > 1 else ".")),
                     2: (f"Number two. You've got {_said_num(n_act)} day{'s' if n_act > 1 else ''} to activate "
                         "this year's use. The deadline is December fifteenth."),
                     "build": "And number one...",
                     1: "You get a second use in twenty twenty-seven! Another fourteen days of free Item Shop claims.",
                     "outro": "So, when are you using yours?",
                     "end": "And if you're buying anything, use code bad!",
                 })


def _one_in(n: int) -> int:
    """1 / the chance of a find in n chests, to three significant figures."""
    x = 1 / _chance(n)
    return int(round(x, -max(0, int(math.log10(x)) - 2)))


def _pct(n: int) -> str:
    p = 100 * _chance(n)
    return f"{p:.2f}%" if p < 1 else f"{p:.1f}%"


def sofar(ctx: Ctx, cast: dict) -> Video | None:
    """Pirate Shop Access: your odds so far -- Epic's odds, worked out for a few
    ways of playing since the mini-season began (exact: 1 - (1 - p)^n)."""
    day = ctx.day
    if len(cast) < 5:
        return None
    days = (day - STARTED).days + 1
    n10, n30, nsq = 10 * days, 30 * days, 4 * 30 * days
    c = _crew(cast, day)
    entries = [
        CD.Entry(c[0], CD.Stat("if anyone in your squad finds it", text="everyone gets it", guess="???"),
                 ["the whole squad gets access", "so squad up"], "squad up 🏴‍☠️", name="squad bonus",
                 label="squad gets it"),
        CD.Entry(c[1], CD.Stat("a squad of 4, 30 chests each a day", text=f"1 in {_one_in(nsq):,}", guess="1 in ?"),
                 [f"{nsq:,} chests since nov 1", f"about a {_pct(nsq)} chance"], "better together 🤝",
                 name="squad of 4", label=f"1 in {_one_in(nsq):,}"),
        CD.Entry(c[2], CD.Stat("30 chests a day since nov 1", text=f"1 in {_one_in(n30):,}", guess="1 in ?"),
                 [f"that's {n30:,} chests", f"about a {_pct(n30)} chance"], "still rare 😭",
                 name="30 a day", label=f"1 in {_one_in(n30):,}"),
        CD.Entry(c[3], CD.Stat("10 chests a day since nov 1", text=f"1 in {_one_in(n10):,}", guess="1 in ?"),
                 [f"that's {n10:,} chests", f"about a {_pct(n10)} chance"], "keep looting 🏴‍☠️",
                 name="10 a day", label=f"1 in {_one_in(n10):,}"),
        CD.Entry(MAP if HAVE_MAP else c[4], CD.Stat("epic's odds per chest", text=f"1 in {ODDS:,}", guess="1 in ?"),
                 ["in a normal match", f"posted by epic on {POSTED.lower()}"], "that's insanely rare 😭",
                 name="the odds", label=f"1 in {ODDS:,}"),
    ]
    comp = CD.cut(ctx, entries, salt=f"pirate_sofar_{day}", title="pirate shop access: your odds so far 🏴‍☠️",
                  sub=f"day {days} of treasure hunters, the math", tease="the good news 👀",
                  ask="how many chests have you opened? 👇", crown="🏴‍☠️")
    if comp is None:
        return None
    d, full = _dates(day)
    body = ("1️⃣ If anyone in your squad finds it, everyone gets it\n"
            f"2️⃣ A squad of 4, 30 chests each a day since Nov 1: {nsq:,} chests, about 1 in {_one_in(nsq):,}\n"
            f"3️⃣ 30 chests a day since Nov 1: {n30:,} chests, about 1 in {_one_in(n30):,}\n"
            f"4️⃣ 10 chests a day since Nov 1: {n10:,} chests, about 1 in {_one_in(n10):,}\n"
            f"5️⃣ Epic's odds: 1 in {ODDS:,} per chest in a normal match (posted {POSTED})")
    return _post("edit_pirate_sofar", comp,
                 title=f"Pirate Shop Access: Your Odds So Far — Day {days} (Fortnite)",
                 yt_title=f"Fortnite Pirate Shop Access: Your Odds After {days} Days #shorts",
                 hook=f"🏴‍☠️ PIRATE SHOP ACCESS — your odds so far, {full}\n"
                      f"Epic's odds, 1 in {ODDS:,} per chest, worked out 👇",
                 body=body, ask="How many chests have you opened?", narration={
                     "hook": ("Pirate Shop Access. Here are your odds so far.", "Your odds, so far."),
                     5: f"Number five. Epic says it's {ODDS_SAID}, per chest, in a normal match.",
                     4: (f"Number four. Ten chests a day since November first? "
                         f"About one in {_said_num(_one_in(n10))}."),
                     3: f"Number three. Thirty a day? About one in {_said_num(_one_in(n30))}.",
                     2: f"Number two. A squad of four, thirty each a day? About one in {_said_num(_one_in(nsq))}.",
                     "build": "The good news?",
                     1: "If anyone in your squad finds it, everyone gets it!",
                     "outro": "So, how many chests have you opened?",
                     "end": "And if you're shopping today, use code bad!",
                 })


def op_items(ctx: Ctx, cast: dict) -> Video | None:
    """Got Pirate Shop Access? The One Piece items to claim (the single ones,
    not the bundles), while they're in the shop."""
    day = ctx.day
    rows = [r for r in _claimable(ctx.shop) if r.get("section") == "One Piece"]
    leaves = _one_piece_leaves(ctx.shop)
    if leaves is None:
        return None
    d, full = _dates(day)
    return _pick(ctx, rows, fmt="edit_pirate_op_items", salt=f"pirate_op_items_{day}",
                 on_title="got pirate shop access? the one piece items to claim 🏴‍☠️",
                 sub=f"in the item shop until {leaves:%b} {leaves.day}".lower(), tease="the priciest one 👀",
                 on_ask="which one are you claiming? 👇",
                 title=f"Pirate Shop Access: The One Piece Items to Claim — Fortnite, {d}",
                 yt_title=f"Got Pirate Shop Access? The One Piece Items to Claim in Fortnite ({d}) #shorts",
                 hook=f"🏴‍☠️ GOT PIRATE SHOP ACCESS? The One Piece items to claim — Fortnite Item Shop, {full}\n"
                      f"The priciest single One Piece items, in the shop until {leaves:%b} {leaves.day} 👇",
                 said_hook=("Got Pirate Shop Access? Here are the One Piece items to claim.",
                            "Pirate Shop Access? Claim these One Piece items.", "One Piece items to claim!"),
                 said_build=("And the priciest one...", "And number one..."),
                 ask="Which one are you claiming?", said_ask="Which one are you claiming?",
                 said_end="And if you're buying them, use code bad!")


EVENING = [sofar, countdown, op_items]       # Nov 11 sofar, Nov 12 countdown, Nov 13 op_items, ...


def daily(day: date) -> list:
    """D's three: [(name, builders to try in order, (hour, minute) in Chicago,
    about D's shop)]. The evening one isn't about D's shop (it may post after the
    reset); op_items is about the One Piece offers, which stay until END."""
    k = (day - ANCHOR).days % len(EVENING)
    evening = EVENING[k:] + EVENING[:k]
    return [("grabs", [grabs], (9, 30), True),
            ("spotlight", [spotlight], (14, 30), True),
            ("evening", evening, (20, 0), False)]


def _post_time(day: date, at: tuple, about_shop: bool) -> datetime:
    """Chicago time on D; one about D's shop is kept 45 minutes clear of the reset."""
    from zoneinfo import ZoneInfo
    local = datetime(day.year, day.month, day.day, *at, tzinfo=ZoneInfo("America/Chicago"))
    latest = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(days=1, minutes=-45)
    if about_shop and local > latest:
        local = latest.astimezone(ZoneInfo("America/Chicago"))
    return local


def make_daily(shop: dict, cast: dict, art, out: Path, voice: str = "michael", at: list | None = None,
               no_video: bool = False) -> list:
    """Build D's three into `out` and return their manifest entries (cc_build's
    shape, with "series": "pirate"); [] past END or with no One Piece offers."""
    import cc_end_card as E
    import cc_formats as F
    import cc_safe as S
    import cc_store as STORE
    from cc_build import COVER_T, _render_one, post_problems
    day = date.fromisoformat(shop["shop_day"])
    if day > END or _one_piece_leaves(shop) is None:
        log(f"{day}: no Pirate Shop Access videos (after {END}, or no One Piece offers in the shop)")
        return []
    if voice:
        import cc_bootstrap
        cc_bootstrap.ensure_tts()
    tag, made, jobs = f"shop-{day.isoformat()}", [], []
    base = STORE.base_url(tag)
    for k, (name, tries, when, about) in enumerate(daily(day)):
        when = at[k] if at and k < len(at) else when
        v = None
        for fn in tries:
            ctx = Ctx(shop=shop, art=art, day=day, seed=int(day.strftime("%Y%m%d")) + 307 * (k + 1))
            try:
                v = E.finish(lambda c, f=fn: f(c, cast), ctx)
            except Exception as e:  # noqa: BLE001 - one bad format must not sink the others
                log(f"pirate {name} ({fn.__name__}) crashed: {e!r}"[:300])
                v = None
            if v is not None:
                break
            log(f"pirate {name}: {fn.__name__} can't be made today")
        if v is None:
            continue
        if voice and getattr(v, "narration", None):
            import cc_voiceover
            try:
                cc_voiceover.narrate(v.comp, v.narration, voice=voice, strict=False)
            except ValueError as e:
                log(f"pirate {name}: the voiceover doesn't fit ({e}); this one goes out without it"[:400])
        dur, safe, problems = v.comp.duration, S.check(v.comp), post_problems(v)
        log(f"pirate {name} ({v.format}): {dur:.1f}s, safe zones {'OK' if safe['ok'] else S.summary(safe, 4)}, "
            f"music {v.comp.music.get('title') or 'synth'}")
        if not (F.MIN_SECONDS - .01 <= dur <= 90) or not safe["ok"] or problems:
            log(f"pirate {name}: not published ({'; '.join(problems) or 'length or safe zones'})")
            continue
        stem = f"bad-{day.isoformat()}-pirate-{name}"
        qa = [COVER_T, 1.2] + [float(t) for t in range(4, int(dur), 6)] + [round(dur - 2, 2)]
        jobs.append((v.comp, out, stem, "mp4", qa, int(day.strftime("%Y%m%d")) * 10 + 6 + k, False, no_video))
        post = _post_time(day, when, about)
        th = F.threads_caption(v.caption)
        made.append({
            "slot": 6 + k, "slot_name": f"pirate_{name}", "series": "pirate", "kind": "short",
            "about_shop": about, "format": v.format,
            "file": f"{stem}.mp4", "url": base + f"{stem}.mp4",
            "cover": f"{stem}-cover.png", "cover_url": base + f"{stem}-cover.png", "cover_ms": int(COVER_T * 1000),
            "duration": round(dur, 2),
            "post_at_local": post.strftime("%Y-%m-%dT%H:%M:%S"),
            "post_at_iso": post.isoformat(timespec="seconds"),
            "post_at_utc": post.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": v.title, "yt_title": v.yt_title, "caption": v.caption,
            "ig_caption": F.ig_caption(v.caption), "threads": False, "threads_caption": th,
            "hashtags": v.hashtags, "safe_zones": S.note(safe),
        })
    import os
    workers = 2 if len(jobs) > 1 and (os.cpu_count() or 2) >= 4 else 1
    log(f"Rendering {len(jobs)} Pirate Shop Access videos, {workers} at a time")
    if workers == 1:
        for j in jobs:
            _render_one(j)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(workers) as ex:
            list(ex.map(_render_one, jobs))
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shop", required=True)
    ap.add_argument("--records", default=str(OUT_DIR / "_data" / "br-fresh.json"))
    ap.add_argument("--out", default=str(OUT_DIR / "pirate"))
    ap.add_argument("--only", default=",".join(BUILDERS))
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--map", help="the current map, cropped to the island (PNG); --daily fetches it")
    ap.add_argument("--voice", default="michael", help="the narrator (cc_ingame.VOICES); '' for none")
    ap.add_argument("--daily", action="store_true",
                    help="the shop day's three (make_daily) -> OUT/videos.json, manifest entries")
    ap.add_argument("--at", help="--daily: post times instead of the usual, e.g. 14:15,16:45,20:00")
    args = ap.parse_args()
    global HAVE_MAP
    import cc_end_card as E
    import cc_formats as F
    import cc_safe as S
    from cc_build import _render_one, art_fn
    shop = json.loads(Path(args.shop).read_text())
    day = date.fromisoformat(shop["shop_day"])
    if not Path(args.records).exists():
        import cc_rarity
        cc_rarity.load(fresh=True)
    records = json.loads(Path(args.records).read_text())["data"]
    cast = crew(records)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    made = []
    from cc_images import data_uri
    shop_art = art_fn(None)
    if args.daily and not args.map:
        args.map = fetch_map(out / "map_island.png")
    map_uri = data_uri(Path(args.map)) if args.map else ""
    HAVE_MAP = bool(map_uri)

    def art(item):
        return map_uri if item is MAP else shop_art(item)

    if args.daily:
        at = [tuple(int(x) for x in t.split(":")) for t in args.at.split(",")] if args.at else None
        made = make_daily(shop, cast, art, out, voice=args.voice, at=at, no_video=args.no_video)
        (out / "videos.json").write_text(json.dumps(made, indent=1, ensure_ascii=False))
        log(f"{len(made)} Pirate Shop Access videos for {day} -> {out}")
        for m in made:
            log(f"  {m['post_at_local']}  {m['format']:<22} {m['file']}")
        return

    for k, name in enumerate(args.only.split(",")):
        if not map_uri and name in ("explainer", "odds", "dates"):
            log(f"{name}: needs --map")
            continue
        ctx = Ctx(shop=shop, art=art, day=day, seed=int(day.strftime("%Y%m%d")) + 101 * (k + 1))
        v = E.finish(lambda c, f=BUILDERS[name]: f(c, cast), ctx)
        if v is None:
            log(f"{name}: can't be made")
            continue
        if args.voice and getattr(v, "narration", None):
            import cc_voiceover
            cc_voiceover.narrate(v.comp, v.narration, voice=args.voice)
        dur = v.comp.duration
        safe = S.check(v.comp)
        log(f"{name}: {dur:.1f}s, safe zones {'OK' if safe['ok'] else S.summary(safe, 4)}, "
            f"music {v.comp.music.get('title') or 'synth'}")
        if not (F.MIN_SECONDS - .01 <= dur <= 90) or not safe["ok"]:
            log(f"{name}: not published (length or safe zones)")
            continue
        stem = f"bad-pirate-{name}"
        qa = [0.0, 1.2] + [float(t) for t in range(4, int(dur), 6)] + [round(dur - 2, 2)]
        _render_one((v.comp, out, stem, "mp4", qa, int(day.strftime("%Y%m%d")) * 10 + 50 + k, False, args.no_video))
        made.append({"name": name, "format": v.format, "file": f"{stem}.mp4", "duration": round(dur, 2),
                     "title": v.title, "yt_title": v.yt_title, "caption": v.caption,
                     "ig_caption": F.ig_caption(v.caption), "hashtags": v.hashtags})
    index = out / "videos.json"
    have = [v for v in (json.loads(index.read_text()) if index.exists() else [])
            if v["name"] not in {m["name"] for m in made}]
    index.write_text(json.dumps(have + made, indent=1, ensure_ascii=False))
    log(f"{len(made)} videos -> {out}")


if __name__ == "__main__":
    main()
