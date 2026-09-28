"""
Build one day's videos from creator-code/quiz/plan.json: the quizzes, On This Day
and, in their season, the seasonal series (see cc_quiz.py and cc_series.py).

    python3 scripts/cc_quiz_build.py --date 2026-09-24 [--art DIR] [--no-video]
                                     [--jobs N] [--release TAG]

Writes creator-code/out/quiz-YYYY-MM-DD/: the videos, their covers and QA sheets,
and manifest.json in the same shape as the shop's, so the daily Routine schedules
them the same way. They're published as the release quiz-YYYY-MM-DD.

A video is left out, never swapped for another, if its artwork won't download,
it runs under 62 s (TikTok's one-minute bar) or over 90 s (Facebook's Reel
limit), or its words wouldn't post cleanly.

From creator-code/lineup.json's "edit_from" day on, the shop job's daily
lineup (cc_lineup.py) makes all five shorts, so a quiz day from then on builds
no shorts here. From its "long_from" day on, the nightly run (quiz day = today
+ 14) also makes today's long YouTube video (cc_long_build.py), listed under
"long_videos" in the same manifest.

It never posts anything itself.
"""

import argparse
import base64
import glob
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cc_end_card as E  # noqa: E402
import cc_quiz as Q  # noqa: E402
import cc_safe as S  # noqa: E402
import cc_long_build as LB  # noqa: E402
from cc_build import COVER_T, REPO, _render_one, edit_lineup, post_problems  # noqa: E402
from cc_common import CC_DIR, OUT_DIR, log, write_json  # noqa: E402
from cc_formats import MIN_SECONDS, Ctx, ig_caption  # noqa: E402

PLAN = CC_DIR / "quiz" / "plan.json"
LOCAL_TZ = ZoneInfo("America/Chicago")
MAX_SECONDS = 90.0          # Facebook Reels


def art_fn(art_dir: str | None):
    """art(item) -> data URI, cached per item id (names can repeat across types)."""
    cache = {}
    if art_dir:
        uris = ["data:image/png;base64," + base64.b64encode(open(f, "rb").read()).decode()
                for f in sorted(glob.glob(f"{art_dir}/*.png"))]

        def art(item):
            if item["id"] not in cache:
                cache[item["id"]] = uris[len(cache) % len(uris)] if uris else ""
            return cache[item["id"]]
        return art

    from cc_images import fetch_first

    def art(item):
        if item["id"] not in cache:
            cache[item["id"]] = fetch_first(item["images"])
        return cache[item["id"]]
    return art


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="the day to build, YYYY-MM-DD")
    ap.add_argument("--art", help="use PNGs in this folder as stand-in art (offline QA)")
    ap.add_argument("--no-video", action="store_true", help="QA stills only")
    ap.add_argument("--jobs", type=int, default=0, help="videos to render at once (default: cores/2)")
    ap.add_argument("--release", help="release tag (default quiz-DATE)")
    args = ap.parse_args()

    plan = json.loads(PLAN.read_text())
    day = date.fromisoformat(args.date)
    entries = sorted((v for v in plan["videos"] if v["date"] == args.date), key=lambda v: v["at"])
    if entries and edit_lineup(day):
        log(f"{args.date} is in the edit lineup: the shop job makes its shorts; no quiz shorts here.")
        entries = []
    long_day = LB.due(day)
    if not entries and not long_day:
        # Past the end of the plan: nothing to do, and not an error for the
        # nightly run. Extend the plan with cc_quiz_plan.py.
        log(f"Nothing to build for {args.date}.")
        return
    items = plan["items"]
    ctx = Ctx(shop={"items": []}, art=art_fn(args.art), day=day, seed=int(day.strftime("%Y%m%d")))

    built = []
    for spec in entries:
        name = f"slot {spec['slot']} {spec.get('series', '')} {spec['format']} #{spec['episode']}".replace("  ", " ")
        try:
            # Held to the apps' safe box (cc_safe): a look that puts something
            # under TikTok/Instagram/YouTube/Facebook UI falls back to the classic.
            # Every video ends on the code-entry card (cc_end_card).
            v, safe = S.gate(lambda: E.finish(lambda c: Q.build(spec, items, c), ctx), name, log)
        except Exception as e:  # noqa: BLE001 - one bad video must not sink the day
            log(f"  {name} crashed: {e!r}")
            continue
        if v is None:
            log(f"  {name}: artwork missing, left out")
            continue
        if not safe["ok"]:
            print(f"::warning::{name}: something sits under the apps' UI -- {S.summary(safe, 3)}",
                  file=sys.stderr)
        if not MIN_SECONDS - .01 <= v.comp.duration <= MAX_SECONDS:
            log(f"  {name}: {v.comp.duration:.1f}s is outside {MIN_SECONDS:.0f}-{MAX_SECONDS:.0f}s, left out")
            continue
        problems = post_problems(v)
        if problems:
            log(f"  {name} left out: {'; '.join(problems)}")
            continue
        log(f"  {name}: {v.comp.duration:.1f}s, safe zones {'OK' if safe['ok'] else 'NOT OK'}")
        built.append((spec, v, safe))
    if entries and not built and not long_day:
        raise SystemExit("No quiz video could be built for this day.")

    out = OUT_DIR / f"quiz-{day.isoformat()}"
    out.mkdir(parents=True, exist_ok=True)
    tag = args.release or f"quiz-{day.isoformat()}"
    base = f"https://github.com/{REPO}/releases/download/{tag}/"
    jobs = []
    for spec, v, _ in built:
        stem = f"bad-quiz-{day.isoformat()}-{spec['slot']}-{v.format.replace('_', '-')}"
        qa_times = ([COVER_T, 1.2] + [float(t) for t in range(4, int(v.comp.duration), 6)]
                    + [round(v.comp.duration - 2, 2)])
        seed = int(day.strftime("%Y%m%d")) * 10 + 5 + spec["slot"]
        jobs.append((v.comp, out, stem, "mp4", qa_times, seed, False, args.no_video))

    workers = max(1, min(len(jobs), args.jobs or (os.cpu_count() or 2) // 2))
    log(f"Rendering {len(jobs)} quiz videos, {workers} at a time")
    if not jobs:
        pass
    elif workers == 1:
        for j in jobs:
            _render_one(j)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(workers) as ex:
            list(ex.map(_render_one, jobs))

    videos = []
    for (spec, v, safe), job in zip(built, jobs):
        stem = job[2]
        hh, mm = (int(x) for x in spec["at"].split(":"))
        post = datetime(day.year, day.month, day.day, hh, mm, tzinfo=LOCAL_TZ)
        videos.append({
            "slot": spec["slot"],
            "format": v.format,
            "episode": spec["episode"],
            "file": f"{stem}.mp4",
            "url": base + f"{stem}.mp4",
            "cover": f"{stem}-cover.png",
            "cover_url": base + f"{stem}-cover.png",
            "cover_ms": int(COVER_T * 1000),
            "duration": round(v.comp.duration, 2),
            "post_at_local": post.strftime("%Y-%m-%dT%H:%M:%S"),
            "post_at_iso": post.isoformat(timespec="seconds"),
            "post_at_utc": post.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": v.title,
            "yt_title": v.yt_title,
            "caption": v.caption,
            "ig_caption": ig_caption(v.caption),       # Instagram allows 5 hashtags
            "hashtags": v.hashtags,
            "safe_zones": S.note(safe),
        })
    longs = []
    if long_day:
        try:
            entry = LB.make(long_day, out, base, ctx.art, args.no_video)
        except Exception as e:  # noqa: BLE001 - the shorts still publish
            print(f"::error::long video {long_day} failed: {e!r}", file=sys.stderr)
            entry = None
        if entry:
            longs.append(entry)
    if not videos and not longs:
        log("Nothing was built.")
        return
    manifest = {
        "kind": "quiz",
        "quiz_day": day.isoformat(),
        "timezone": "America/Chicago",
        "release": tag,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "videos": videos,
        "long_videos": longs,
    }
    write_json(out / "manifest.json", manifest)
    log(f"Wrote {out / 'manifest.json'} with {len(videos)} videos and {len(longs)} long video(s)")
    for v in videos:
        log(f"  {v['post_at_local']}  {v['format']:<13} {v['title']}")
    for v in longs:
        log(f"  {v['post_at_local']}  YouTube (long)  {v['youtube']['title']}")


if __name__ == "__main__":
    main()
