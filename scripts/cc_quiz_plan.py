"""
Plan @usecodebad's quiz videos (three a day) and the series beside them (On This
Day every day, Fortnitemares every day in October; see cc_series_plan.py), for
months ahead, from the cosmetics database.

    python3 scripts/cc_quiz_plan.py [--start 2026-09-24] [--days 180] [--db br-full.json.gz]
                                    [--from 2026-10-09]

Writes creator-code/quiz/plan.json: every video's date, post time, format, episode
number and the exact items and answer options it will show. cc_quiz_build.py
renders a day's videos from it; nothing is picked at render time, so a video can
be re-made later and come out the same.

--from keeps the current plan before that day exactly as it is (those videos
are built and scheduled) and re-plans from it. The series are planned over
their whole run either way, and take their slot over from a quiz there.

The database is fortnite-api.com's full cosmetics list with shop history, kept
on this repo's "cosmetics-data" release by .github/workflows/cosmetics-data.yml.
Every answer comes from it:
  - "Introduced in Chapter 1, Season 5"  <- the cosmetic's `introduction`
  - which came first                     <- introduction.backendValue, which counts
                                            seasons in release order (Chapter 2 Remix
                                            is 32: after Chapter 5, before Chapter 6)
  - "3 of these are from the X set"      <- the cosmetic's `set`
Nothing is claimed that the data doesn't hold: no prices, no "rarest", no "most
popular", no Battle Pass or shop history (the mirror doesn't carry those).

Names that more than one outfit shares (or "TBD" placeholders) are left out, so a
name is always a single, unambiguous answer. An item isn't reused within 60 days.
"""

import argparse
import gzip
import json
import random
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cc_common import CC_DIR, OUT_DIR, log  # noqa: E402
import cc_series_plan as S  # noqa: E402

DB_URL = "https://github.com/fwagtx/History-Pulse-/releases/download/cosmetics-data/br-full.json.gz"
PLAN = CC_DIR / "quiz" / "plan.json"
SEASONS = CC_DIR / "quiz" / "seasons.json"

# Post times, America/Chicago, between the shop videos (10:00, 13:30, 17:00).
# Quizzes don't go stale when the shop rotates, so the evening slot is fine.
SLOTS = [(1, "08:00"), (2, "15:30"), (3, "20:00")]
FORMATS = ["guess_season", "whos_that", "which_first", "zoomed_in", "odd_one_out", "throwback", "loadout"]
REUSE_DAYS = 60
SPARES = 2          # extra rounds per video, used if an item's artwork won't download

# The collab and icon lines: characters people know on sight.
FAMOUS_SERIES = {"Icon Series", "MARVEL SERIES", "DC SERIES", "Star Wars Series",
                 "Gaming Legends Series"}
BAD_NAMES = {"tbd", "null", "npc", ""}
# Build Your Loadout: one round per slot of the locker, three choices each.
LOADOUT = ["outfit", "backpack", "pickaxe", "glider", "emote"]
NICE = {"legendary", "epic", "marvel", "dc", "icon", "starwars", "gaminglegends"}


def season_label(chapter: str, season: str) -> str:
    """'Chapter 1 · Season X', 'Chapter 4 · Season OG', 'Chapter 2 · Remix'."""
    if season.lower() == "remix":
        return f"Chapter {chapter} · Remix"
    return f"Chapter {chapter} · Season {season}"


def normalize(raw: dict) -> dict | None:
    intro = raw.get("introduction") or {}
    images = raw.get("images") or {}
    urls = [images[k] for k in ("featured", "icon", "smallIcon") if images.get(k)]
    name = (raw.get("name") or "").strip()
    if not intro.get("backendValue") or not urls or name.lower() in BAD_NAMES:
        return None
    return {
        "id": raw["id"],
        "name": name,
        "type": (raw.get("type") or {}).get("displayValue") or "Item",
        "kind": (raw.get("type") or {}).get("value") or "",
        "rarity": ((raw.get("rarity") or {}).get("value") or "common").lower(),
        "rarity_label": (raw.get("rarity") or {}).get("displayValue") or "",
        "series": ((raw.get("series") or {}).get("value") or "").strip(),
        "set": ((raw.get("set") or {}).get("value") or "").strip(),
        "chapter": str(intro["chapter"]),
        "season": str(intro["season"]),
        "season_label": season_label(str(intro["chapter"]), str(intro["season"])),
        "order": int(intro["backendValue"]),
        "has_featured": bool(images.get("featured")),
        "images": urls,
        "first_shop": min((d[:10] for d in raw.get("shopHistory") or []), default=""),
    }


class Pools:
    def __init__(self, raw_items: list):
        history = {r["id"]: r.get("shopHistory") or [] for r in raw_items if r.get("id")}
        items = [n for n in (normalize(r) for r in raw_items) if n]
        # A name two outfits share can't be a quiz answer.
        count = {}
        for it in items:
            key = (it["kind"], it["name"].lower())
            count[key] = count.get(key, 0) + 1
        self.items = [it for it in items if count[(it["kind"], it["name"].lower())] == 1]
        self.outfits = [it for it in self.items if it["kind"] == "outfit"]
        self.famous = [it for it in self.outfits if it["has_featured"]
                       and (it["rarity"] == "legendary" or it["series"] in FAMOUS_SERIES)]
        self.gear = [it for it in self.items if it["kind"] in ("pickaxe", "glider", "backpack")]
        # The days each outfit was in the Item Shop, for On This Day.
        self.shop_days = {it["id"]: sorted({d[:10] for d in history.get(it["id"], [])})
                          for it in self.outfits if it["has_featured"]}
        self.loadout = {k: [it for it in self.items if it["kind"] == k and it["rarity"] in NICE]
                        for k in LOADOUT}
        self.loadout["outfit"] = self.famous
        self.labels = {}
        for it in self.items:
            self.labels.setdefault(it["order"], it["season_label"])
        self.by_set = {}
        for it in self.outfits:
            if it["set"]:
                self.by_set.setdefault(it["set"], []).append(it)
        self.by_season, self.gear_by_season = {}, {}
        for it in self.outfits:
            self.by_season.setdefault(it["order"], []).append(it)
        for it in self.gear:
            self.gear_by_season.setdefault(it["order"], []).append(it)


class Planner:
    def __init__(self, pools: Pools, seed: int):
        self.p = pools
        self.r = random.Random(seed)
        self.last_used = {}         # item id -> day index
        self.episodes = {f: 0 for f in FORMATS}
        self.throwback_seasons = []
        self.throwback_cycle = 0     # 0: outfits, 1: gear, then around again
        self.day = 0

    def free(self, items: list) -> list:
        return [it for it in items if self.day - self.last_used.get(it["id"], -10 ** 6) >= REUSE_DAYS]

    def take(self, items: list):
        for it in items:
            self.last_used[it["id"]] = self.day

    def pick(self, pool: list, n: int, avoid: set = frozenset()) -> list:
        cands = [it for it in self.free(pool) if it["id"] not in avoid]
        if len(cands) < n:
            return []
        out = self.r.sample(cands, n)
        return out

    # ------------------------------------------------------------ formats

    def guess_season(self):
        """Six cosmetics, four seasons each. Mostly outfits; every third
        episode is a gear edition (pickaxes, gliders, back blings)."""
        gear = self.episodes["guess_season"] % 3 == 2
        pool = self.p.gear if gear else self.p.outfits
        items = []
        seasons = set()
        for it in self.r.sample(self.free(pool), min(len(self.free(pool)), 400)):
            if it["order"] in seasons:          # six different right answers
                continue
            items.append(it)
            seasons.add(it["order"])
            if len(items) == 6 + SPARES:
                break
        if len(items) < 6 + SPARES:
            return None
        rounds = []
        for it in items:
            near = [o for o in self.p.labels if o != it["order"] and abs(o - it["order"]) <= 6]
            opts = sorted(self.r.sample(near, 3) + [it["order"]])      # oldest first, like a timeline
            rounds.append({"item": it["id"], "options": [self.p.labels[o] for o in opts],
                           "answer": opts.index(it["order"])})
        return {"edition": "gear" if gear else "outfits", "rounds": rounds}, items

    def _name_rounds(self, pool: list, n: int):
        """Rounds whose answer is the item's name, with three decoy names
        from the same line (Marvel with Marvel, Icons with Icons)."""
        items = self.pick(pool, n)
        if not items:
            return None
        rounds, chosen = [], {it["id"] for it in items}
        for it in items:
            same = [o for o in pool if o["id"] not in chosen and o["series"] == it["series"]]
            if len(same) < 3:
                same = [o for o in pool if o["id"] not in chosen]
            decoys = self.r.sample(same, 3)
            names = [d["name"] for d in decoys] + [it["name"]]
            self.r.shuffle(names)
            rounds.append({"item": it["id"], "options": names, "answer": names.index(it["name"])})
        return rounds, items

    def whos_that(self):
        got = self._name_rounds(self.p.famous, 6 + SPARES)
        return ({"rounds": got[0]}, got[1]) if got else None

    def zoomed_in(self):
        got = self._name_rounds(self.p.famous, 6 + SPARES)
        if not got:
            return None
        for rd in got[0]:
            # Where the camera starts, as a fraction of the artwork: around the
            # upper body, where a character is most recognisable.
            rd["focus"] = [round(self.r.uniform(.38, .62), 3), round(self.r.uniform(.2, .36), 3)]
        return {"rounds": got[0]}, got[1]

    def which_first(self):
        n = 5 + SPARES
        items = self.pick(self.p.outfits, n * 2)
        if not items:
            return None
        rounds, used, spare = [], [], list(items)
        while spare and len(rounds) < n:
            a = spare.pop()
            # A clear answer: at least three seasons apart.
            b = next((x for x in spare if abs(x["order"] - a["order"]) >= 3), None)
            if b is None:
                continue
            spare.remove(b)
            if self.r.random() < .5:
                a, b = b, a
            rounds.append({"a": a["id"], "b": b["id"], "answer": "a" if a["order"] < b["order"] else "b"})
            used += [a, b]
        if len(rounds) < n:
            return None
        return {"rounds": rounds}, used

    def odd_one_out(self):
        n = 5 + SPARES
        sets = [(s, self.free(v)) for s, v in self.p.by_set.items()]
        sets = [(s, v) for s, v in sets if len(v) >= 3]
        if len(sets) < n:
            return None
        rounds, used = [], []
        for s, members in self.r.sample(sets, n):
            members = [m for m in members if m["id"] not in {u["id"] for u in used}]
            if len(members) < 3:
                return None
            three = self.r.sample(members, 3)
            others = [o for o in self.free(self.p.outfits)
                      if o["set"] and o["set"] != s and o["id"] not in {u["id"] for u in used}]
            if not others:
                return None
            odd = self.r.choice(others)
            four = three + [odd]
            self.r.shuffle(four)
            rounds.append({"items": [x["id"] for x in four], "answer": four.index(odd), "set": s,
                           "odd_set": odd["set"]})
            used += four
        return {"rounds": rounds}, used

    def throwback(self):
        """Eight cosmetics from one season, oldest season first. The first pass
        through the seasons is outfits; the next is gear (pickaxes, gliders,
        back blings), so no season's episode repeats."""
        gear = self.throwback_cycle % 2 == 1
        by_season = self.p.gear_by_season if gear else self.p.by_season
        art_ok = (lambda x: True) if gear else (lambda x: x["has_featured"])
        done = set(self.throwback_seasons)
        seasons = sorted(o for o, v in by_season.items() if o not in done
                         and len([x for x in self.free(v) if art_ok(x)]) >= 8)
        if not seasons:
            self.throwback_seasons = []
            self.throwback_cycle += 1
            return None
        order = seasons[0]
        pool = [x for x in self.free(by_season[order]) if art_ok(x)]
        # Lead with the showpieces: legendaries and collabs, then the rest.
        pool.sort(key=lambda x: (x["rarity"] != "legendary", x["series"] not in FAMOUS_SERIES,
                                 self.r.random()))
        items = pool[:8]
        self.throwback_seasons.append(order)
        return ({"season": self.p.labels[order], "order": order, "edition": "gear" if gear else "outfits",
                 "items": [x["id"] for x in items]}, items)

    def loadout(self):
        """Build Your Loadout: outfit, back bling, pickaxe, glider, emote, three
        choices each. No right answers: people comment their combo. A fourth
        item per round stands in if one's artwork won't load."""
        rounds, items = [], []
        for kind in LOADOUT:
            # Sets share names across types (a "Dopamine Blades" back bling and
            # pickaxe): one name per video, so no round looks like a repeat.
            names = {it["name"].lower() for it in items}
            got = self.pick([it for it in self.p.loadout[kind] if it["name"].lower() not in names], 4)
            if not got:
                return None
            rounds.append({"kind": kind, "items": [it["id"] for it in got]})
            items += got
        return {"rounds": rounds}, items

    # ------------------------------------------------------------ calendar

    def replay(self, kept: list, start: date):
        """Pick up where already-planned quiz videos left off: their items count
        as used on their days, and episode numbers carry on after theirs."""
        for v in sorted(kept, key=lambda v: (v["date"], v["slot"])):
            day = (date.fromisoformat(v["date"]) - start).days
            ids = [rd[k] for rd in v.get("rounds", []) for k in ("item", "a", "b") if k in rd]
            ids += [i for rd in v.get("rounds", []) for i in rd.get("items", [])] + v.get("items", [])
            for i in ids:
                self.last_used[i] = day
            self.episodes[v["format"]] = max(self.episodes[v["format"]], v["episode"])
            if v["format"] == "throwback":
                self.throwback_cycle = 1 if v.get("edition") == "gear" else 0
                self.throwback_seasons.append(v["order"])

    def _todays(self, block: list, n: int) -> tuple:
        """The next n different formats. Each format comes round equally often:
        they're dealt from shuffled decks of all of them."""
        today = []
        while len(today) < n:
            if not [f for f in block if f not in today]:
                deck = FORMATS[:]
                self.r.shuffle(deck)
                block = block + deck
            f = next(f for f in block if f not in today)
            block.remove(f)
            today.append(f)
        return today, block

    def plan(self, start: date, first: date, last: date, reserved: set) -> tuple:
        """Quizzes for every day from `first` to `last`, in every slot a series
        hasn't taken (`reserved`: (date, slot) pairs)."""
        videos, used_items = [], {}
        block = []
        d = first
        while d <= last:
            self.day = (d - start).days
            slots = [(s, at) for s, at in SLOTS if (d.isoformat(), s) not in reserved]
            today, block = self._todays(block, len(slots))
            done_today = set()
            for (slot, at), fmt in zip(slots, today):
                got = None
                # If a format has run out of fresh items, fall back to one the day
                # hasn't had yet, so no day shows the same quiz twice.
                for f in [fmt] + [x for x in FORMATS if x not in today] + [x for x in today if x != fmt]:
                    if f in done_today:
                        continue
                    got = getattr(self, f)()
                    if got:
                        fmt = f
                        break
                if not got:
                    log(f"{d} slot {slot}: nothing plannable")
                    continue
                spec, items = got
                done_today.add(fmt)
                self.take(items)
                self.episodes[fmt] += 1
                for it in items:
                    used_items[it["id"]] = it
                videos.append({"date": d.isoformat(), "slot": slot, "at": at,
                               "format": fmt, "episode": self.episodes[fmt], **spec})
            d += timedelta(days=1)
        return videos, used_items


def load_db(path: str | None) -> list:
    """The cosmetics list: a local file (.json or .json.gz), or the release copy."""
    if not path:
        cache = OUT_DIR / "_data" / "br-full.json.gz"
        cache.parent.mkdir(parents=True, exist_ok=True)
        log(f"Downloading {DB_URL}")
        with urllib.request.urlopen(DB_URL, timeout=180) as resp:
            cache.write_bytes(resp.read())
        path = str(cache)
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)["data"]


def item_ids(v: dict) -> list:
    """Every item id a planned video uses."""
    ids = list(v.get("items", []))
    for rd in v.get("rounds", []):
        ids += [rd[k] for k in ("item", "a", "b") if k in rd] + list(rd.get("items", []))
        ids += [p["item"] for p in rd.get("picks", [])]
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=(date.today() + timedelta(days=1)).isoformat(),
                    help="first day of a new plan (ignored with --from: the plan keeps its start)")
    ap.add_argument("--days", type=int, default=180)
    ap.add_argument("--from", dest="from_day",
                    help="keep the current plan before this day as it is, and re-plan from it")
    ap.add_argument("--otd-start", help="first On This Day video (default: the plan's first day)")
    ap.add_argument("--db", help="a local copy of br-full.json(.gz) (default: download it)")
    ap.add_argument("--seed", type=int, default=7066444)
    args = ap.parse_args()

    old = json.loads(PLAN.read_text()) if args.from_day and PLAN.exists() else None
    start = date.fromisoformat(old["start"] if old else args.start)
    last = start + timedelta(days=args.days - 1)
    first = date.fromisoformat(args.from_day) if args.from_day else start
    kept = [v for v in (old or {}).get("videos", []) if v["date"] < first.isoformat()]

    pools = Pools(load_db(args.db))
    log(f"{len(pools.items)} usable cosmetics: {len(pools.outfits)} outfits "
        f"({len(pools.famous)} famous), {len(pools.gear)} gear, {len(pools.by_set)} sets, "
        f"{sum(1 for d in pools.shop_days.values() if d)} outfits with shop history")

    # The series first: they take their slot over from a quiz. Videos of theirs
    # that are already built stay exactly as they are.
    seasons = json.loads(SEASONS.read_text())
    # On This Day counts its episodes from its first day, so a re-plan keeps that day.
    kept_otd = sorted(v["date"] for v in kept if v["format"] == "on_this_day")
    otd_start = date.fromisoformat(kept_otd[0] if kept_otd else args.otd_start or start.isoformat())
    otd, otd_items = S.plan_otd(pools, otd_start, last, args.seed,
                                {v["date"]: v for v in kept if v["format"] == "on_this_day"})
    fm, fm_items = [], {}
    for year in range(start.year, last.year + 1):
        for plan_season, name in ((S.plan_fortnitemares, "fortnitemares"), (S.plan_winterfest, "winterfest")):
            got = plan_season(pools, seasons, year, start, last, args.seed,
                              {v["date"]: v for v in kept if v.get("series") == name})
            fm += got[0]
            fm_items.update(got[1])
    series = otd + fm
    reserved = {(v["date"], v["slot"]) for v in series}

    kept_quiz = [v for v in kept if v["format"] != "on_this_day" and not v.get("series")
                 and (v["date"], v["slot"]) not in reserved]
    dropped = [v for v in kept if v["format"] != "on_this_day" and not v.get("series")
               and (v["date"], v["slot"]) in reserved]
    for v in dropped:
        log(f"  {v['date']} slot {v['slot']}: {v['format']} #{v['episode']} gives way to a series")
    planner = Planner(pools, args.seed)
    planner.replay(kept_quiz, start)
    quiz, quiz_items = planner.plan(start, first, last, reserved)

    videos = sorted(kept_quiz + quiz + series, key=lambda v: (v["date"], v["slot"]))
    items = {}
    for v in videos:
        for i in item_ids(v):
            # A series' copy first: it carries the item's Fortnitemares or Winterfest year.
            it = fm_items.get(i) or otd_items.get(i) or quiz_items.get(i) or (old or {}).get("items", {}).get(i)
            if it is None:
                it = next((x for x in pools.items if x["id"] == i), None)
            if it is None:
                raise SystemExit(f"item {i} is in the plan but not in the database")
            items[i] = it
    plan = {"start": start.isoformat(), "days": args.days, "timezone": "America/Chicago",
            "source": DB_URL, "items": items, "videos": videos}
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    counts = {}
    for v in videos:
        k = f"{v['series']}:{v['format']}" if v.get("series") else v["format"]
        counts[k] = counts.get(k, 0) + 1
    log(f"{len(videos)} videos from {start} to {last} ({len(kept)} kept as they were) -> {PLAN}")
    log("  " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
