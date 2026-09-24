"""
Plan the series that run beside the quizzes. cc_quiz_plan.py merges them into
creator-code/quiz/plan.json, and cc_quiz_build.py renders them with the quizzes.

    On This Day     every day at 12:00 Central: for every year since 2018, one
                    outfit that was in the Item Shop on that calendar date
    Fortnitemares   every day in October at 20:00, in place of that slot's quiz:
                    Halloween throwbacks, one Fortnitemares at a time, and
                    Halloween editions of the quizzes

Every claim comes from data, never memory:
  - "In the Item Shop on September 25, 2019"  <- the item's shop history has that day
  - "First time in the Item Shop"             <- that day is the first in its shop
                                                  history, and on or after FIRST_SURE:
                                                  the history starts 2017-10-30, so an
                                                  earlier "first" might just be the start
                                                  of the records
  - "From Fortnitemares 2019"                 <- the Fortnite Wiki lists it among that
                                                  year's Fortnitemares Item Shop cosmetics
                                                  (creator-code/quiz/seasons.json) AND its
                                                  first shop day is inside that year's
                                                  window. Both, or it isn't used.
  - "Fortnite Battle Royale came out on
     September 26, 2017"                      <- Epic's launch date (PlayStation Blog,
                                                  2017-09-12; Wikipedia)
"""

import random
from datetime import date, timedelta

FIRST_SURE = "2018-01-01"
OTD_SLOT, OTD_AT = 4, "12:00"
OTD_MIN_YEARS = 7            # fewer years than this and the day gets no video
OTD_REUSE = 60               # days before an outfit can lead a year again
OTD_PICKS = 3                # per year: the pick and two stand-ins if its art won't load
FAMOUS_SERIES = {"Icon Series", "MARVEL SERIES", "DC SERIES", "Star Wars Series",
                 "Gaming Legends Series"}
BIRTHDAY = {"md": "09-26", "year": 2017}      # Fortnite Battle Royale's launch day

SEASON_SLOT, SEASON_AT = 3, "20:00"
FM_REUSE = 7                 # days before a Halloween item can come back within the series
FM_QUIZZES = ["which_year", "whos_that", "zoomed_in", "which_first"]
SPARES = 2

TYPES = {"Outfit": "outfit", "Back Bling": "backpack", "Pickaxe": "pickaxe",
         "Harvesting Tool": "pickaxe", "Glider": "glider", "Emote": "emote"}


# =============================================================== On This Day

class OnThisDay:
    def __init__(self, pools, seed: int):
        self.p = pools
        self.r = random.Random(seed * 7 + 1)
        self.last = {}                          # item id -> ordinal of the day it led a year
        self.by_day = {}                        # "YYYY-MM-DD" -> outfits in the shop that day
        for it in pools.outfits:
            if not it["has_featured"]:
                continue
            for d in pools.shop_days.get(it["id"], ()):
                self.by_day.setdefault(d, []).append(it)

    def take(self, entry: dict, day: date):
        for rd in entry["rounds"]:
            if rd.get("picks"):
                self.last[rd["picks"][0]["item"]] = day.toordinal()

    def entry(self, day: date, episode: int):
        rounds, used, items = [], set(), []
        for y in range(2017, day.year):
            try:
                d = day.replace(year=y).isoformat()
            except ValueError:                  # February 29
                continue
            cands = [it for it in self.by_day.get(d, []) if it["id"] not in used]
            if not cands:
                continue

            def rank(it):
                debut = it["first_shop"] == d and d >= FIRST_SURE
                fresh = day.toordinal() - self.last.get(it["id"], -10 ** 6) >= OTD_REUSE
                return (fresh, 3 * debut + 2 * (it["series"] in FAMOUS_SERIES)
                        + (it["rarity"] == "legendary"), self.r.random())
            ranked = sorted(cands, key=rank, reverse=True)[:OTD_PICKS]
            used.update(it["id"] for it in ranked)
            items += ranked
            rounds.append({"year": y, "day": d,
                           "picks": [{"item": it["id"],
                                      "debut": it["first_shop"] == d and d >= FIRST_SURE}
                                     for it in ranked]})
        if len(rounds) < OTD_MIN_YEARS:
            return None
        spec = {"date": day.isoformat(), "slot": OTD_SLOT, "at": OTD_AT, "format": "on_this_day",
                "episode": episode, "md": day.strftime("%m-%d"), "rounds": rounds}
        if spec["md"] == BIRTHDAY["md"]:
            spec["birthday"] = {"year": BIRTHDAY["year"], "age": day.year - BIRTHDAY["year"]}
        return spec, items


def plan_otd(pools, start: date, end: date, seed: int, fixed: dict) -> tuple:
    """One On This Day entry per day from start to end. `fixed` holds entries
    already built (date -> entry): they're kept as they are."""
    otd = OnThisDay(pools, seed)
    out, used_items = [], {}
    d, episode = start, 0
    while d <= end:
        episode += 1
        keep = fixed.get(d.isoformat())
        if keep:
            otd.take(keep, d)
            out.append(keep)
        else:
            got = otd.entry(d, episode)
            if got:
                spec, items = got
                otd.take(spec, d)
                out.append(spec)
                for it in items:
                    used_items[it["id"]] = it
        d += timedelta(days=1)
    return out, used_items


# ============================================================== Fortnitemares

def fortnitemares_pool(pools, seasons: dict) -> dict:
    """Halloween items by Fortnitemares year, each checked two ways (see top)."""
    fm = seasons["fortnitemares"]
    lo, hi = fm["window"]
    by_name = {}
    for it in pools.items:
        by_name.setdefault((it["name"].lower(), it["kind"]), []).append(it)
    out = {}
    for year, rows in fm["years"].items():
        for name, typ in rows:
            kind = TYPES.get(typ)
            for it in by_name.get((name.lower(), kind), []) if kind else []:
                first = it["first_shop"]
                if first[:4] == year and lo <= first[5:] <= hi:
                    out.setdefault(int(year), []).append(dict(it, fm_year=int(year)))
                    break
    for y in out:
        out[y].sort(key=lambda x: (x["first_shop"], x["name"]))
    return out


class Fortnitemares:
    """31 days in October. Throwbacks every third day, oldest Fortnitemares
    first; the Halloween quizzes in between."""
    # (years it covers, part number or 0). 2017 had only three Item Shop
    # cosmetics, so it opens the series together with 2018.
    THROWBACKS = [((2017, 2018), 0), ((2018,), 0), ((2019,), 0), ((2020,), 0), ((2021,), 1),
                  ((2021,), 2), ((2022,), 0), ((2023,), 0), ((2024,), 0), ((2025,), 1), ((2025,), 2)]

    def __init__(self, by_year: dict, seed: int):
        self.by_year = by_year
        self.r = random.Random(seed * 11 + 3)
        self.all = [it for y in sorted(by_year) for it in by_year[y]]
        self.outfits = [it for it in self.all if it["kind"] == "outfit" and it["has_featured"]]
        self.last = {}                  # item id -> day of month last used
        self.shown = set()              # items already given a throwback round
        self.quiz_n = 0
        self.tb_n = 0

    def free(self, pool: list, day: int) -> list:
        return [it for it in pool if day - self.last.get(it["id"], -99) >= FM_REUSE]

    def take(self, items: list, day: int):
        for it in items:
            self.last[it["id"]] = day

    def throwback(self, day: int):
        years, part = self.THROWBACKS[self.tb_n]
        self.tb_n += 1
        # Oldest year first; within a year, outfits first, in the order they came out.
        pool = [it for y in years for it in self.by_year.get(y, []) if it["id"] not in self.shown]
        pool.sort(key=lambda x: (x["fm_year"], x["kind"] != "outfit", x["first_shop"]))
        items = pool[:8 + SPARES]
        if len(items) < 6:
            return None
        self.shown.update(it["id"] for it in items[:8])
        span = f"{years[0]}–{years[-1]}" if len(years) > 1 else str(years[0])
        return {"format": "throwback", "fm_span": span, "part": part,
                "items": [it["id"] for it in items]}, items

    def _names(self, day: int, n: int):
        items = self.r.sample(self.free(self.outfits, day), n) if len(self.free(self.outfits, day)) >= n else []
        if not items:
            return None
        chosen = {it["id"] for it in items}
        rounds = []
        for it in items:
            others = [o for o in self.outfits if o["id"] not in chosen]
            names = [d["name"] for d in self.r.sample(others, 3)] + [it["name"]]
            self.r.shuffle(names)
            rounds.append({"item": it["id"], "options": names, "answer": names.index(it["name"])})
        return rounds, items

    def quiz(self, fmt: str, day: int):
        if fmt in ("whos_that", "zoomed_in"):
            got = self._names(day, 6 + SPARES)
            if not got:
                return None
            rounds, items = got
            if fmt == "zoomed_in":
                for rd in rounds:
                    rd["focus"] = [round(self.r.uniform(.38, .62), 3), round(self.r.uniform(.2, .36), 3)]
            return {"format": fmt, "rounds": rounds}, items
        if fmt == "which_year":
            pool = self.free(self.outfits, day)
            if len(pool) < 6 + SPARES:
                return None
            items = self.r.sample(pool, 6 + SPARES)
            years = sorted(self.by_year)
            rounds = []
            for it in items:
                near = [y for y in years if y != it["fm_year"]]
                near.sort(key=lambda y: (abs(y - it["fm_year"]), self.r.random()))
                opts = sorted(near[:3] + [it["fm_year"]])
                rounds.append({"item": it["id"], "options": [f"FORTNITEMARES {y}" for y in opts],
                               "answer": opts.index(it["fm_year"])})
            return {"format": "which_year", "rounds": rounds}, items
        if fmt == "which_first":
            pool = self.free(self.outfits, day)
            self.r.shuffle(pool)
            rounds, used = [], []
            while pool and len(rounds) < 5 + SPARES:
                a = pool.pop()
                # A clear answer: different Fortnitemares years.
                b = next((x for x in pool if x["fm_year"] != a["fm_year"]), None)
                if b is None:
                    continue
                pool.remove(b)
                rounds.append({"a": a["id"], "b": b["id"],
                               "answer": "a" if a["first_shop"] < b["first_shop"] else "b"})
                used += [a, b]
            if len(rounds) < 5 + SPARES:
                return None
            return {"format": "which_first", "rounds": rounds}, used
        raise ValueError(fmt)

    def entry(self, d: date):
        day = d.day
        if day % 3 == 1 and self.tb_n < len(self.THROWBACKS):
            got = self.throwback(day)
        else:
            fmt = FM_QUIZZES[self.quiz_n % len(FM_QUIZZES)]
            self.quiz_n += 1
            got = self.quiz(fmt, day)
        if not got:
            return None
        spec, items = got
        self.take(items, day)
        return dict({"date": d.isoformat(), "slot": SEASON_SLOT, "at": SEASON_AT,
                     "series": "fortnitemares", "episode": day, "of": 31}, **spec), items


def plan_fortnitemares(pools, seasons: dict, year: int, start: date, end: date, seed: int,
                       fixed: dict) -> tuple:
    """One Fortnitemares video a day through October of `year`, within start..end."""
    by_year = fortnitemares_pool(pools, seasons)
    fm = Fortnitemares(by_year, seed)
    out, used_items = [], {}
    d = date(year, 10, 1)
    while d <= date(year, 10, 31):
        keep = fixed.get(d.isoformat())
        if keep and keep.get("series") == "fortnitemares":
            # Replay it so the rotation and reuse state stay the same.
            fm.entry(d)
            out.append(keep)
        else:
            got = fm.entry(d)
            if got and start <= d <= end:
                spec, items = got
                out.append(spec)
                for it in items:
                    used_items[it["id"]] = it
        d += timedelta(days=1)
    return out, used_items, by_year
