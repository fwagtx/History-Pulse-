"""
Build one day's three quiz videos from creator-code/quiz/plan.json.

    python3 scripts/cc_quiz_build.py --date 2026-09-24 [--art DIR] [--no-video]
                                     [--jobs N] [--release TAG]

Writes creator-code/out/quiz-YYYY-MM-DD/: the videos, their covers and QA sheets,
and manifest.json in the same shape as the shop's, so the daily Routine schedules
them the same way. They're published as the release quiz-YYYY-MM-DD.

A video is left out, never swapped for another, if its artwork won't download,
it runs under 62 s (TikTok's one-minute bar) or over 90 s (Facebook's Reel
limit), or its words wouldn't post cleanly.

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

import cc_quiz as Q  # noqa: E402
from cc_build import COVER_T, REPO, _render_one, post_problems  # noqa: E402
from cc_common import CC_DIR, OUT_DIR, log, write_json  # noqa: E402
from cc_formats import MIN_SECONDS, Ctx  # noqa: E402

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
    entries = [v for v in plan["videos"] if v["date"] == args.date]
    if not entries:
        # Past the end of the plan: nothing to do, and not an error for the
        # nightly run. Extend the plan with cc_quiz_plan.py.
        log(f"The plan has nothing for {args.date}; nothing to build.")
        return
    items = plan["items"]
    ctx = Ctx(shop={"items": []}, art=art_fn(args.art), day=day, seed=int(day.strftime("%Y%m%d")))

    built = []
    for spec in entries:
        name = f"slot {spec['slot']} {spec['format']} #{spec['episode']}"
        try:
            v = Q.build(spec, items, ctx)
        except Exception as e:  # noqa: BLE001 - one bad video must not sink the day
            log(f"  {name} crashed: {e!r}")
            continue
        if v is None:
            log(f"  {name}: artwork missing, left out")
            continue
        if not MIN_SECONDS - .01 <= v.comp.duration <= MAX_SECONDS:
            log(f"  {name}: {v.comp.duration:.1f}s is outside {MIN_SECONDS:.0f}-{MAX_SECONDS:.0f}s, left out")
            continue
        problems = post_problems(v)
        if problems:
            log(f"  {name} left out: {'; '.join(problems)}")
            continue
        log(f"  {name}: {v.comp.duration:.1f}s")
        built.append((spec, v))
    if not built:
        raise SystemExit("No quiz video could be built for this day.")

    out = OUT_DIR / f"quiz-{day.isoformat()}"
    out.mkdir(parents=True, exist_ok=True)
    tag = args.release or f"quiz-{day.isoformat()}"
    base = f"https://github.com/{REPO}/releases/download/{tag}/"
    jobs = []
    for spec, v in built:
        stem = f"bad-quiz-{day.isoformat()}-{spec['slot']}-{v.format.replace('_', '-')}"
        qa_times = ([COVER_T, 1.2] + [float(t) for t in range(4, int(v.comp.duration), 6)]
                    + [round(v.comp.duration - 2, 2)])
        seed = int(day.strftime("%Y%m%d")) * 10 + 5 + spec["slot"]
        jobs.append((v.comp, out, stem, "mp4", qa_times, seed, False, args.no_video))

    workers = max(1, min(len(jobs), args.jobs or (os.cpu_count() or 2) // 2))
    log(f"Rendering {len(jobs)} quiz videos, {workers} at a time")
    if workers == 1:
        for j in jobs:
            _render_one(j)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(workers) as ex:
            list(ex.map(_render_one, jobs))

    videos = []
    for (spec, v), job in zip(built, jobs):
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
            "hashtags": v.hashtags,
        })
    manifest = {
        "kind": "quiz",
        "quiz_day": day.isoformat(),
        "timezone": "America/Chicago",
        "release": tag,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "videos": videos,
    }
    write_json(out / "manifest.json", manifest)
    log(f"Wrote {out / 'manifest.json'} with {len(videos)} videos")
    for v in videos:
        log(f"  {v['post_at_local']}  {v['format']:<13} {v['title']}")


if __name__ == "__main__":
    main()
