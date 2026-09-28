#!/usr/bin/env python3
"""
Approval samples: the new formats rendered with real art and today's data, for
the owner to watch before any of them goes live. Nothing schedules these.

    python3 scripts/cc_samples.py --out creator-code/out/samples [--what all] [--day YYYY-MM-DD]

--what is a comma list of:
  back_after   short: BACK AFTER N DAYS from today's shop
  rarest       short: RAREST SKINS RIGHT NOW
  og           short: CHAPTER 1 SEASON 3 -- WHERE ARE THEY NOW?
  long         long video: THE RAREST SKINS, an excerpt (intro, how it works,
               three picks, the ask, the end card), plus its thumbnail
  voices       the same line in four narration voices, to choose one
  styles       the day's On This Day in each new look (STYLES), one video each;
               or style_<name> for one (e.g. style_calendar)
  topics       each new topic (TOPICS), one video each; or topic_<name>
  edits        the formats cut as edits to real music (EDITS, cc_edit.py), one
               video each; or edit_<name>

The new looks and topics are switched on for this process only: looks.json, the
quiz plan and the nightly builds never see them.
"""

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cc_end_card as E  # noqa: E402
import cc_fmt_rarity as FR  # noqa: E402
import cc_safe as S  # noqa: E402
from cc_build import COVER_T, _render_one, art_fn, fetch_today, post_problems  # noqa: E402
from cc_common import CC_DIR, log  # noqa: E402
from cc_formats import Ctx, ig_caption  # noqa: E402

VOICES = ["am_michael", "am_fenrir", "af_heart", "bm_george"]
VOICE_LINE = ("This skin has been in the Item Shop exactly once. The last time was September fifteenth, "
              "twenty eighteen. These are the rarest skins in Fortnite, going by the Item Shop's own records.")

# New looks for On This Day: name -> module (scripts/cc_look_<name>.py).
STYLES = {"calendar": "cc_look_calendar", "arcade": "cc_look_arcade", "comic": "cc_look_comic",
          "metro": "cc_look_metro", "magazine": "cc_look_magazine", "postcard": "cc_look_postcard"}
# New topics: name -> (module, builder, kwargs for the sample episode).
TOPICS = {"higher_lower": ("cc_fmt_higher_lower", "build", {"pool": "ch1"}),
          "overdue": ("cc_fmt_overdue", "build", {}),
          "most_common": ("cc_fmt_most_common", "build", {}),
          "then_now": ("cc_fmt_then_now", "build", {}),
          "tier_list": ("cc_fmt_tier_list", "build", {}),
          "battle_pass": ("cc_fmt_battle_pass", "build", {})}
# The same formats cut as edits to real music (cc_edit.py): name -> (module, builder, kwargs).
# ("look": a look for On This Day, drawn through the quiz plan's episode like STYLES.)
EDITS = {"most_common": ("cc_edit_most_common", "build", {}),
         "higher_lower": ("cc_edit_higher_lower", "build", {"pool": "ch1"}),
         "on_this_day": ("cc_edit_on_this_day", "look", {})}


def short(name, make, ctx, out, seed, index, stem="") -> dict:
    v = E.finish(make, ctx)
    if v is None:
        log(f"{name}: today's data can't support it")
        return {"name": name, "built": False}
    safe = S.check(v.comp)
    stem = stem or f"sample-{index}-{name.replace('_', '-')}"
    qa = [COVER_T, 1.2] + [float(t) for t in range(4, int(v.comp.duration), 4)] + [round(v.comp.duration - .3, 2)]
    _render_one((v.comp, out, stem, "mp4", qa, seed, False, False))
    rep = {"name": name, "built": True, "file": f"{stem}.mp4", "duration": round(v.comp.duration, 2),
           "title": v.title, "yt_title": v.yt_title, "caption": v.caption, "ig_caption": ig_caption(v.caption),
           "safe_zones": S.note(safe), "problems": post_problems(v)}
    music = getattr(v.comp, "music", None)
    if music:
        rep["music"] = {k: music[k] for k in ("artist", "title", "license", "page", "bpm", "synth") if k in music}
    return rep


def style(name, module, day, art, out, seed, kind: str = "style") -> dict:
    """The day's On This Day, drawn by a new look that is switched on for this
    process only. A look that fails is reported, never swapped for the classic."""
    import cc_looks as LK
    import cc_quiz as Q
    plan = json.loads((CC_DIR / "quiz" / "plan.json").read_text())
    spec = next((s for s in plan["videos"] if s["date"] == day.isoformat() and s["format"] == "on_this_day"), None)
    if spec is None:
        log(f"{kind} {name}: no On This Day on {day} in the quiz plan")
        return {"name": f"{kind}_{name}", "built": False}
    LK.LOOKS["on_this_day"] = module
    os.environ["CC_LOOKS"] = "on_this_day"
    ctx = Ctx(shop={"items": []}, art=art, day=day, seed=int(day.strftime("%Y%m%d")))
    LK.draw.last = None
    try:
        rep = short(f"{kind}_{name}", lambda c: Q.build(spec, plan["items"], c), ctx, out, seed, 0,
                    stem=f"sample-{kind}-{name.replace('_', '-')}")
    except Exception as e:  # noqa: BLE001 - one broken sample must not cost the others
        log(f"{kind} {name}: failed: {e!r}")
        return {"name": f"{kind}_{name}", "built": False, "error": repr(e)}
    rep["look"] = LK.draw.last
    if LK.draw.last != module:
        log(f"::warning::{kind} {name}: drawn by {LK.draw.last}, not {module}")
    return rep


def topic(name, spec, ctx, out, seed, kind: str = "topic") -> dict:
    module, fn, kw = spec
    try:
        mod = importlib.import_module(module)
        rep = short(f"{kind}_{name}", lambda c: getattr(mod, fn)(c, **kw), ctx, out, seed, 0,
                    stem=f"sample-{kind}-{name.replace('_', '-')}")
    except Exception as e:  # noqa: BLE001 - one broken sample must not cost the others
        import traceback
        traceback.print_exc()
        log(f"{kind} {name}: failed: {e!r}")
        return {"name": f"{kind}_{name}", "built": False, "error": repr(e)}
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="creator-code/out/samples")
    ap.add_argument("--what", default="back_after,rarest,og,long,voices")
    ap.add_argument("--art", default="", help="stand-in art folder (offline); default: real art")
    ap.add_argument("--shop", default="", help="a saved shop.json (offline); default: today's shop")
    ap.add_argument("--day", default="", help="the samples' day (YYYY-MM-DD); default: today (UTC)")
    ap.add_argument("--voice", default="am_michael")
    a = ap.parse_args()
    what = {w.strip() for w in a.what.split(",") if w.strip()}
    if "all" in what:
        what = {"back_after", "rarest", "og", "long", "voices"}
    if "styles" in what:
        what |= {f"style_{k}" for k in STYLES}
    if "topics" in what:
        what |= {f"topic_{k}" for k in TOPICS}
    if "edits" in what:
        what |= {f"edit_{k}" for k in EDITS}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    shop = {"items": []}
    if a.shop:
        shop = json.loads(Path(a.shop).read_text())
        day = date.fromisoformat(shop["shop_day"])
    else:
        day = date.fromisoformat(a.day) if a.day else datetime.now(timezone.utc).date()
        if what & {"back_after", "rarest", "og"}:
            shop = fetch_today(day, 0)
    art = art_fn(a.art or None)
    ctx = Ctx(shop=shop, art=art, day=day, seed=int(day.strftime("%Y%m%d")))
    seed = int(day.strftime("%Y%m%d")) * 10
    report = {"day": day.isoformat(), "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "shorts": [], "long": None, "voices": [], "styles": [], "topics": [], "edits": [],
              "long_series": None}

    # BACK AFTER needs three comebacks of 180+ days; on a quiet day the sample
    # drops to 90+ so there's still something to look at.
    jobs = [("back_after", lambda c: FR.back_after(c) or FR.back_after(c, min_days=90)),
            ("rarest", lambda c: FR.rarest(c, "outfits")),
            ("og", lambda c: FR.og_where(c, "1", "3"))]
    for i, (name, make) in enumerate(jobs, 1):
        if name in what:
            report["shorts"].append(short(name, make, ctx, out, seed + i, i))

    for i, (name, module) in enumerate(STYLES.items()):
        if f"style_{name}" in what:
            report["styles"].append(style(name, module, day, art, out, seed + 20 + i))
    for i, (name, spec) in enumerate(TOPICS.items()):
        if f"topic_{name}" in what:
            report["topics"].append(topic(name, spec, ctx, out, seed + 40 + i))
    for i, (name, spec) in enumerate(EDITS.items()):
        if f"edit_{name}" in what:
            if spec[1] == "look":
                rep = style(name, spec[0], day, art, out, seed + 60 + i, kind="edit")
            else:
                rep = topic(name, spec, ctx, out, seed + 60 + i, kind="edit")
            report["edits"].append(rep)

    if "long" in what:
        import cc_long as L
        import cc_long_rarest as LR
        hist = FR.history()

        def art_of(item):
            imgs = item.get("images") or {}
            return art({"id": item["id"], "name": item["name"],
                        "images": [imgs[k] for k in ("featured", "icon") if imgs.get(k)]})
        lv, wall, title, picks = LR.build(hist, day, "outfit", 10, art_of, seed, excerpt=3, voice=a.voice)
        comp, wav, chapters = lv.build(out / "long", wall)
        L.render(comp, out / "sample-4-long-rarest-excerpt.mp4", wav, workers=3)
        thumb = LR.thumbnail(picks, art_of, day, "outfit", out / "sample-4-long-thumbnail.jpg")
        report["long"] = {"file": "sample-4-long-rarest-excerpt.mp4", "thumbnail": thumb.name, "title": title,
                          "duration": round(comp.duration, 2), "chapters": L.chapters_text(chapters),
                          "voice": a.voice, "picks": [{"name": p[0]["name"], "last": p[1].isoformat(),
                                                       "days": p[2], "times": p[3], "same_day_set": p[4]}
                                                      for p in picks]}

    if "long_series" in what:
        # A whole weekday long video exactly as the nightly job makes it
        # (cc_long_build.py): the sample day's series, or Monday's at a weekend.
        import cc_long_build as LB
        d = day
        while d.weekday() > 4:
            d += timedelta(days=1)
        t0 = time.time()
        entry = LB.make(d, out / "long", "", art)
        if entry:
            stem = f"sample-long-{d.isoformat()}-{entry['series']}"
            for src, dst in ((entry["file"], f"{stem}.mp4"), (entry["thumbnail"], f"{stem}-thumbnail.png"),
                             (entry["file"].replace(".mp4", "-qa.jpg"), f"{stem}-qa.jpg")):
                (out / "long" / src).rename(out / dst)
            entry.update(file=f"{stem}.mp4", thumbnail=f"{stem}-thumbnail.png", seconds_to_build=round(time.time() - t0),
                         megabytes=round((out / f"{stem}.mp4").stat().st_size / 1e6, 1))
        report["long_series"] = entry

    if "voices" in what:
        import cc_voice as V
        for voice in VOICES:
            (wav, secs), = V.say([VOICE_LINE], out / "voices", voice)
            m4a = out / f"voice-{voice}.m4a"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "aac", "-b:a", "128k",
                            str(m4a)], check=True)
            report["voices"].append({"voice": voice, "file": m4a.name, "seconds": round(secs, 1)})

    # Runs for styles and topics can publish to the same release at once: each
    # keeps its own report.
    parts = [k for k in ("styles", "topics", "edits") if report[k]] + (
        [f"long-{report['long_series']['day']}"] if report["long_series"] else [])
    name = f"samples-{'-'.join(parts)}.json" if parts else "samples.json"
    (out / name).write_text(json.dumps(report, indent=1, ensure_ascii=False))
    log(f"samples: {[s.get('file') for s in report['shorts'] + report['styles'] + report['topics'] + report['edits']]} "
        f"long={bool(report['long'])} voices={len(report['voices'])} "
        f"long_series={(report['long_series'] or {}).get('file')}")


if __name__ == "__main__":
    main()
