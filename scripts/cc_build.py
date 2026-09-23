"""
Build the day's three @usecodebad videos from the live item shop.

    python3 scripts/cc_build.py [--art DIR] [--preview] [--only FORMAT,...]
                                [--wait MINUTES] [--no-video]

What it does, in order:
  1. Fetches the shop and checks it is TODAY's shop. The mirror can lag the
     00:00 UTC rotation by a few minutes, so it re-checks for up to --wait
     minutes rather than making videos about yesterday's items.
  2. Picks three formats -- one per slot -- rotating by weekday, skipping any
     format the day's data can't support honestly.
  3. Renders each to MP4 with its synthesized soundtrack, plus a cover still
     and QA stills.
  4. Writes manifest.json: the post time for each video (all before the shop
     rotates), titles, captions and hashtags. The daily Routine reads this to
     schedule the drafts in Metricool.

It never posts anything itself.
"""

import argparse
import base64
import glob
import importlib
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cc_formats as F
from cc_common import OUT_DIR, load_config, log, today_stamp, write_json

LOCAL_TZ = ZoneInfo("America/Chicago")
REPO = os.environ.get("GITHUB_REPOSITORY", "fwagtx/History-Pulse-")

# Post times, local (America/Chicago). All must stay before the shop rotation
# (19:00 CDT, 18:00 CST) -- a video about today's shop is wrong after it.
SLOTS = [
    {"slot": 1, "name": "morning",   "at": (10, 0)},
    {"slot": 2, "name": "midday",    "at": (13, 30)},
    {"slot": 3, "name": "afternoon", "at": (17, 0)},
]

# What each slot tries, in order. The first entry rotates by weekday; the rest
# are fallbacks when the day's data can't support a format.
MORNING = ["shop_recap", "new_this_week", "this_or_that"]
INTERACTIVE = ["this_or_that", "guess_price", "costs_more", "cop_or_drop"]
VALUE = ["last_chance", "bundle_math", "og_check", "new_this_week"]


def _rotate(pool: list, k: int) -> list:
    k %= len(pool)
    return pool[k:] + pool[:k]


def plan(day: date) -> list:
    """Candidate formats per slot for this day: primary first, then fallbacks."""
    k = day.toordinal()
    return [
        MORNING,
        _rotate(INTERACTIVE, k),
        # k // 4 shifts the pairing, so the same two formats don't always share a day.
        _rotate(VALUE, k + k // 4) + _rotate(INTERACTIVE, k + 2),   # last resort: another game
    ]


def builder(name: str):
    fn = getattr(F, name, None)
    if fn is not None:
        return fn
    try:
        return importlib.import_module(f"cc_fmt_{name}").build
    except ModuleNotFoundError:
        return None


# ------------------------------------------------------------------ shop

def fetch_today(expect: date, wait_min: float) -> dict:
    from cc_shop import fetch_shop, normalize
    cfg = load_config()
    deadline = time.time() + wait_min * 60
    while True:
        shop = normalize(fetch_shop(cfg))
        got = shop.get("shop_day")
        if got == expect.isoformat():
            return shop
        if time.time() >= deadline:
            raise SystemExit(f"Shop source still shows {got}, expected {expect}. Not building "
                             "videos about the wrong day's shop.")
        log(f"Shop source still on {got}, want {expect}; checking again in 2 min")
        time.sleep(120)


def art_fn(art_dir: str | None):
    cache = {}
    if art_dir:
        uris = ["data:image/png;base64," + base64.b64encode(open(f, "rb").read()).decode()
                for f in sorted(glob.glob(f"{art_dir}/*.png"))]

        def art(item):
            if item["name"] not in cache:
                cache[item["name"]] = uris[len(cache) % len(uris)] if uris else ""
            return cache[item["name"]]
        return art

    from cc_images import candidates, fetch_first

    def art(item):
        if item["name"] not in cache:
            cache[item["name"]] = fetch_first(candidates(item))
        return cache[item["name"]]
    return art


# ------------------------------------------------------------------ timing

def rotation(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(days=1)


def slot_time(day: date, hm: tuple) -> datetime:
    """The local post time on the shop day, pulled earlier if DST or a future
    edit would put it at or after the rotation."""
    local = datetime(day.year, day.month, day.day, hm[0], hm[1], tzinfo=LOCAL_TZ)
    latest = rotation(day) - timedelta(minutes=45)
    if local > latest:
        local = latest.astimezone(LOCAL_TZ).replace(second=0, microsecond=0)
    return local


# ------------------------------------------------------------------ build

COVER_T = 1.2       # everything has landed on screen by here


def _render_one(job):
    """Render one video with its soundtrack, plus QA stills and a cover."""
    from cc_audio import soundtrack
    from cc_motion import render, snapshot
    comp, out, stem, ext, qa_times, seed, preview, no_video = job
    qa_dir = out / "qa" / stem
    if no_video:
        snapshot(comp, qa_times, qa_dir)
    else:
        wav = soundtrack(comp, seed, out / f"{stem}.wav")
        log(f"Rendering {stem}.{ext} ({comp.duration:.1f}s)")
        t0 = time.time()
        render(comp, out / f"{stem}.{ext}", audio=wav, preview=preview,
               stills=qa_times, stills_dir=qa_dir)
        log(f"  {stem} done in {time.time() - t0:.0f}s")
        wav.unlink(missing_ok=True)
    cover = qa_dir / f"t{COVER_T:06.2f}.png"
    if cover.exists():
        (out / f"{stem}-cover.png").write_bytes(cover.read_bytes())
    contact_sheet(sorted(qa_dir.glob("t*.png")), out / f"{stem}-qa.jpg")
    return stem


def contact_sheet(pngs: list, dest: Path, cols: int = 6) -> Path | None:
    """All QA stills of one video on one image, for a quick look at the release."""
    import subprocess
    from cc_motion import find_ffmpeg
    ff = find_ffmpeg()
    if not ff or not pngs:
        return None
    w, h = 270, 480
    rows = -(-len(pngs) // cols)
    inputs, chains, layout = [], [], []
    for i, p in enumerate(pngs):
        inputs += ["-i", str(p)]
        chains.append(f"[{i}:v]scale={w}:{h}[s{i}]")
        layout.append(f"{(i % cols) * w}_{(i // cols) * h}")
    graph = ";".join(chains) + ";" + "".join(f"[s{i}]" for i in range(len(pngs)))
    graph += (f"xstack=inputs={len(pngs)}:layout={'|'.join(layout)}:fill=black" if len(pngs) > 1
              else "null")
    cmd = [ff, "-y", "-loglevel", "error", *inputs, "-filter_complex", graph,
           "-frames:v", "1", "-q:v", "4", str(dest)]
    try:
        subprocess.run(cmd, check=True, timeout=120)
        return dest
    except Exception as e:  # noqa: BLE001 - QA aid only
        log(f"  contact sheet failed: {e}")
        return None


def build_all(shop: dict, art, day: date, only: list | None) -> list:
    ctx = F.Ctx(shop=shop, art=art, day=day, seed=int(day.strftime("%Y%m%d")))
    chosen, used = [], set()
    plans = [[n] for n in only] if only else plan(day)
    for slot, candidates in zip(SLOTS, plans):
        video = None
        for name in candidates:
            if name in used:
                continue
            fn = builder(name)
            if fn is None:
                log(f"  slot {slot['slot']}: {name} not available, skipping")
                continue
            try:
                video = fn(ctx)
            except Exception as e:  # noqa: BLE001 - one bad format must not sink the day
                log(f"  slot {slot['slot']}: {name} crashed: {e!r}")
                video = None
            if video is None:
                log(f"  slot {slot['slot']}: {name} can't be made honestly today, trying next")
                continue
            if video.comp.duration < F.MIN_SECONDS - .01:
                log(f"  slot {slot['slot']}: {name} is only {video.comp.duration:.1f}s, skipping")
                video = None
                continue
            used.add(name)
            break
        if video is None:
            log(f"  slot {slot['slot']}: nothing buildable")
            continue
        log(f"  slot {slot['slot']} ({slot['name']}): {video.format}, {video.comp.duration:.1f}s")
        chosen.append((slot, video))
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", help="use PNGs in this folder as stand-in art (offline QA)")
    ap.add_argument("--preview", action="store_true", help="WebM instead of MP4")
    ap.add_argument("--only", help="comma-separated formats to build instead of the plan")
    ap.add_argument("--wait", type=float, default=50, help="minutes to wait for the new shop")
    ap.add_argument("--shop", help="use this shop.json instead of fetching (QA)")
    ap.add_argument("--no-video", action="store_true", help="plan + stills only")
    ap.add_argument("--jobs", type=int, default=0, help="videos to render at once (default: cores/2)")
    args = ap.parse_args()

    import json
    if args.shop:
        shop = json.loads(Path(args.shop).read_text())
        day = date.fromisoformat(shop["shop_day"])
    else:
        day = date.fromisoformat(today_stamp())
        shop = fetch_today(day, args.wait)

    out = OUT_DIR / day.isoformat()
    write_json(out / "shop.json", shop)
    log(f"Shop {day}: {shop['item_count']} offers, {shop['bundle_count']} bundles")

    only = [s.strip() for s in args.only.split(",")] if args.only else None
    chosen = build_all(shop, art_fn(args.art), day, only)
    if not chosen:
        raise SystemExit("No video could be built today.")

    tag = f"shop-{day.isoformat()}"
    base = f"https://github.com/{REPO}/releases/download/{tag}/"
    rot = rotation(day)
    ext = "webm" if args.preview else "mp4"
    jobs = []
    for slot, v in chosen:
        stem = f"bad-{day.isoformat()}-{slot['slot']}-{v.format.replace('_', '-')}"
        qa_times = ([COVER_T] + [float(t) for t in range(4, int(v.comp.duration), 6)]
                    + [round(v.comp.duration - 2, 2)])
        seed = int(day.strftime("%Y%m%d")) * 10 + slot["slot"]
        jobs.append((v.comp, out, stem, ext, qa_times, seed, args.preview, args.no_video))

    # One Chromium per video, in parallel when the machine has the cores.
    workers = max(1, min(len(jobs), args.jobs or (os.cpu_count() or 2) // 2))
    log(f"Rendering {len(jobs)} videos, {workers} at a time")
    if workers == 1:
        for j in jobs:
            _render_one(j)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(workers) as ex:
            list(ex.map(_render_one, jobs))

    videos = []
    for (slot, v), (_, _, stem, *_rest) in zip(chosen, jobs):
        post = slot_time(day, slot["at"])
        videos.append({
            "slot": slot["slot"],
            "slot_name": slot["name"],
            "format": v.format,
            "file": f"{stem}.{ext}",
            "url": base + f"{stem}.{ext}",
            "cover": f"{stem}-cover.png",
            "cover_url": base + f"{stem}-cover.png",
            "cover_ms": int(COVER_T * 1000),
            "duration": round(v.comp.duration, 2),
            "post_at_local": post.strftime("%Y-%m-%dT%H:%M:%S"),
            "post_at_utc": post.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": v.title,
            "yt_title": v.yt_title,
            "caption": v.caption,
            "hashtags": v.hashtags,
        })

    manifest = {
        "shop_day": day.isoformat(),
        "timezone": "America/Chicago",
        "rotation_utc": rot.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rotation_local": rot.astimezone(LOCAL_TZ).strftime("%Y-%m-%dT%H:%M:%S"),
        "release": tag,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "videos": videos,
    }
    write_json(out / "manifest.json", manifest)
    log(f"Wrote {out / 'manifest.json'} with {len(videos)} videos")
    for v in videos:
        log(f"  {v['post_at_local']}  {v['format']:<14} {v['file']}")


if __name__ == "__main__":
    main()
