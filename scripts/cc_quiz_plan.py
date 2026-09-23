"""
Plan @usecodebad's quiz videos: three a day for months, from the cosmetics database.

    python3 scripts/cc_quiz_plan.py [--start 2026-09-24] [--days 180] [--db br.json]

Writes creator-code/quiz/plan.json: every video's date, post time, format, episode
number and the exact items and answer options it will show. cc_quiz_build.py
renders a day's three videos from it; nothing is picked at render time, so a
video can be re-made later and come out the same.

Every answer comes from the database (the keyless Fortnite-Datamining mirror of
fortnite-api.com, the same source as the daily shop):
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
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cc_common import CC_DIR, log, http_get_json  # noqa: E402

DB_URL = ("https://raw.githubusercontent.com/Fortnite-Datamining/"
          "Fortnite-Datamining/main/data/cosmetics/br.json")
PLAN = CC_DIR / "quiz" / "plan.json"

# Post times, America/Chicago, between the shop videos (10:00, 13:30, 17:00).
# Quizzes don't go stale when the shop rotates, so the evening slot is fine.
SLOTS = [(1, "08:00"), (2, "15:30"), (3, "20:00")]
FORMATS = ["guess_season", "whos_that", "which_first", "zoomed_in", "odd_one_out", "throwback"]
REUSE_DAYS = 60
SPARES = 2          # extra rounds per video, used if an item's artwork won't download

# The collab and icon lines: characters people know on sight.
FAMOUS_SERIES = {"Icon Series", "MARVEL SERIES", "DC SERIES", "Star Wars Series",
                 "Gaming Legends Series"}
BAD_NAMES = {"tbd", "null", "npc", ""}


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
    }


class Pools:
    def __init__(self, raw_items: list):
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

    # ------------------------------------------------------------ calendar

    def plan(self, start: date, days: int) -> dict:
        videos, used_items = [], {}
        block = []
        for d in range(days):
            self.day = d
            if not block:
                block = FORMATS[:]
                self.r.shuffle(block)
            today, block = block[:3], block[3:]
            for (slot, at), fmt in zip(SLOTS, today):
                got = None
                for f in [fmt] + [x for x in FORMATS if x not in today]:
                    got = getattr(self, f)()
                    if got:
                        fmt = f
                        break
                if not got:
                    log(f"{start + timedelta(d)} slot {slot}: nothing plannable")
                    continue
                spec, items = got
                self.take(items)
                self.episodes[fmt] += 1
                for it in items:
                    used_items[it["id"]] = it
                videos.append({"date": (start + timedelta(d)).isoformat(), "slot": slot, "at": at,
                               "format": fmt, "episode": self.episodes[fmt], **spec})
        return {"start": start.isoformat(), "days": days, "timezone": "America/Chicago",
                "source": DB_URL, "items": used_items, "videos": videos}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=(date.today() + timedelta(days=1)).isoformat())
    ap.add_argument("--days", type=int, default=180)
    ap.add_argument("--db", help="a local copy of the mirror's br.json (default: download it)")
    ap.add_argument("--seed", type=int, default=7066444)
    args = ap.parse_args()

    raw = json.loads(Path(args.db).read_text()) if args.db else http_get_json(DB_URL, timeout=120)
    pools = Pools(raw["data"])
    log(f"{len(pools.items)} usable cosmetics: {len(pools.outfits)} outfits "
        f"({len(pools.famous)} famous), {len(pools.gear)} gear, {len(pools.by_set)} sets")
    plan = Planner(pools, args.seed).plan(date.fromisoformat(args.start), args.days)
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    counts = {}
    for v in plan["videos"]:
        counts[v["format"]] = counts.get(v["format"], 0) + 1
    log(f"{len(plan['videos'])} videos over {args.days} days -> {PLAN}")
    log("  " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
