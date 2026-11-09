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
"""

import argparse
import json
import math
import sys
from datetime import date
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shop", required=True)
    ap.add_argument("--records", default=str(OUT_DIR / "_data" / "br-fresh.json"))
    ap.add_argument("--out", default=str(OUT_DIR / "pirate"))
    ap.add_argument("--only", default=",".join(BUILDERS))
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--map", help="the current map, cropped to the island (PNG)")
    ap.add_argument("--voice", default="michael", help="the narrator (cc_ingame.VOICES); '' for none")
    args = ap.parse_args()
    import cc_end_card as E
    import cc_formats as F
    import cc_safe as S
    from cc_build import _render_one, art_fn
    shop = json.loads(Path(args.shop).read_text())
    day = date.fromisoformat(shop["shop_day"])
    records = json.loads(Path(args.records).read_text())["data"]
    cast = crew(records)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    made = []
    from cc_images import data_uri
    shop_art = art_fn(None)
    map_uri = data_uri(Path(args.map)) if args.map else ""

    def art(item):
        return map_uri if item is MAP else shop_art(item)

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
