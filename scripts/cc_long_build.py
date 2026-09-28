"""
The weekday long video for YouTube (cc_long_series.py): built, checked and
rendered by the nightly quiz job, never posted by anything here.

When: the quiz job that builds quiz day D+14 runs at 01:40 UTC on day D. It
also makes day D's long video (Monday to Friday), from the Item Shop's records
as of that morning (fresh from fortnite-api.com), to post at 3 PM Chicago time
the same day. The video rides in that night's release (quiz-<D+14>), listed
under "long_videos" in its manifest.json -- a list the daily Routine reads and
older Routines ignore -- so a manual run of other days never makes one.

    creator-code/lineup.json  "long_from": "2026-10-05"   the first day with a
                                                          long video (null: off)

Quality gate: nothing that fails is published; the next topic is tried.
  * every frame's text, cosmetics and code inside YouTube's safe box
    (cc_safe.LONG: clear of the player's controls, title bar and edges)
  * 3 to 14.5 minutes (an unverified YouTube account can't post over 15)
  * YouTube's limits: title 100 characters, no < or >; description 5000;
    tags 500 in all; chapters valid (from 0:00, 10 s or more each)
  * a 1280x720 thumbnail under 2 MB

    python3 scripts/cc_long_build.py --day 2026-09-29 --out DIR [--art DIR] [--no-video]
"""

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cc_common import CC_DIR, log  # noqa: E402

LINEUP = CC_DIR / "lineup.json"
LOCAL_TZ = ZoneInfo("America/Chicago")
MIN_S, MAX_S = 180.0, 870.0
ENC = ("-crf", "21", "-maxrate", "4500k", "-bufsize", "9000k")     # about 330 MB at most for 10 minutes


def long_from() -> date | None:
    try:
        v = json.loads(LINEUP.read_text()).get("long_from")
    except (OSError, ValueError):
        return None
    return date.fromisoformat(v) if v else None


def due(build_day: date) -> date | None:
    """The day whose long video this run makes, if any: the nightly run (quiz
    day = today + 14, UTC) makes today's, on a weekday from long_from on.
    CC_LONG_DAY=YYYY-MM-DD forces one (samples, a manual re-run)."""
    forced = os.environ.get("CC_LONG_DAY", "").strip()
    if forced:
        return date.fromisoformat(forced)
    today = datetime.now(timezone.utc).date()
    start = long_from()
    if build_day != today + timedelta(days=14) or not start or today < start or today.weekday() > 4:
        return None
    return today


def problems(out: dict, meta: dict) -> list:
    """What would stop this video from posting cleanly (before the safe check)."""
    p = []
    d = out["comp"].duration
    if not MIN_S <= d <= MAX_S:
        p.append(f"{d / 60:.1f} minutes long (3-14.5 allowed)")
    t = meta["title"]
    if not t or len(t) > 100 or "<" in t or ">" in t:
        p.append(f"title not postable ({len(t)} characters)")
    if len(meta["description"]) > 5000 or "<" in meta["description"] or ">" in meta["description"]:
        p.append("description not postable")
    if sum(len(x) + 1 for x in meta["tags"]) > 500:
        p.append("tags over 500 characters")
    if len(meta["chapters"]) < 3:
        p.append("fewer than 3 valid chapters")
    return p


def _png_under(jpg: Path, dest: Path, limit: int = 1_950_000) -> Path:
    """The thumbnail as a PNG (the release keeps covers as *-cover.png), under
    YouTube's 2 MB: full colour if it fits, else a 256-colour palette."""
    from PIL import Image
    img = Image.open(jpg).convert("RGB")
    img.save(dest, "PNG", optimize=True)
    if dest.stat().st_size > limit:
        img.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(
            dest, "PNG", optimize=True)
    if dest.stat().st_size > limit:
        raise RuntimeError(f"thumbnail is {dest.stat().st_size} bytes")
    return dest


def _qa_sheet(comp, times: list, dest: Path) -> Path:
    """Stills of the video on one image, for a quick look at the release."""
    import cc_motion as M
    from io import BytesIO
    from PIL import Image
    from playwright.sync_api import sync_playwright
    w, h, cols = 480, 270, 4
    shots = []
    with sync_playwright() as p:
        br = p.chromium.launch(args=M.CHROME_ARGS)
        pg = br.new_page(viewport={"width": comp.w, "height": comp.h}, device_scale_factor=1)
        pg.set_content(comp.document(), wait_until="load")
        pg.evaluate(M.READY_JS)
        for t in times:
            shots.append(Image.open(BytesIO(M.stable_shot(pg, t * 1000, "jpeg"))).convert("RGB").resize((w, h)))
        br.close()
    rows = -(-len(shots) // cols)
    sheet = Image.new("RGB", (cols * w, rows * h))
    for i, im in enumerate(shots):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(dest, "JPEG", quality=82)
    return dest


def make(day: date, out_dir: Path, base_url: str, art, no_video: bool = False) -> dict | None:
    """Build, check and render `day`'s long video into out_dir; its manifest
    entry, or None (a weekend, or nothing passed the gate)."""
    import cc_bootstrap as B
    import cc_edit_long as LE
    import cc_fmt_rarity as FR
    import cc_long as L
    import cc_long_series as SER
    import cc_safe as S
    if day.weekday() > 4:
        log(f"{day} is a weekend: no long video")
        return None
    t0 = time.time()
    if not B.ensure_tts() or not B.ensure_pillow():
        print("::error::long video: the narration voice (kokoro-onnx) or Pillow couldn't be installed",
              file=sys.stderr)
        return None
    if not B.ensure_emoji_font():
        print("::error::long video: the emoji font couldn't be installed", file=sys.stderr)
        return None
    hist = FR.history()
    work = out_dir / "long-work"
    work.mkdir(parents=True, exist_ok=True)
    checked = {}

    def accept(o):
        meta = SER.describe(o, day)
        bad = problems(o, meta)
        if bad:
            log(f"  {'; '.join(bad)}")
            return False
        safe = LE.check(o["comp"])
        if not safe["ok"]:
            log("  " + S.summary(safe, 6).replace("\n", "\n  "))
            return False
        checked.update(meta=meta, safe=safe)
        return True

    log(f"Long video for {day:%A %Y-%m-%d}")
    out = SER.build(day, hist, art, work, accept=accept)
    if not out:
        print(f"::warning::long video {day}: no topic passed the quality gate", file=sys.stderr)
        return None
    comp, meta = out["comp"], checked["meta"]
    log(f"  {meta['title']} -- {comp.duration / 60:.1f} min, {len(out['rows'])} items, safe zones OK "
        f"({time.time() - t0:.0f}s so far)")
    stem = f"bad-quiz-long-{day.isoformat()}"
    SER.thumbnail(out, work / "thumb.jpg")
    _png_under(work / "thumb.jpg", out_dir / f"{stem}-cover.png")
    times = [0.0, 4.0] + [round(comp.duration * k / 10, 2) for k in range(1, 10)] + [round(comp.duration - 1, 2)]
    _qa_sheet(comp, times, out_dir / f"{stem}-qa.jpg")
    if not no_video:
        t1 = time.time()
        L.render(comp, out_dir / f"{stem}.mp4", out["wav"], workers=max(2, min(4, os.cpu_count() or 2)), enc=ENC)
        mb = (out_dir / f"{stem}.mp4").stat().st_size / 1e6
        log(f"  rendered in {(time.time() - t1) / 60:.1f} min, {mb:.0f} MB")
    hh, mm = SER.POST_AT
    post = datetime(day.year, day.month, day.day, hh, mm, tzinfo=LOCAL_TZ)
    return {
        "kind": "long",
        "day": day.isoformat(),
        "series": out["episode"]["series"],
        "topic": out["topic"],
        "file": f"{stem}.mp4",
        "url": base_url + f"{stem}.mp4",
        "thumbnail": f"{stem}-cover.png",
        "thumbnail_url": base_url + f"{stem}-cover.png",
        "duration": round(comp.duration, 2),
        "post_at_local": post.strftime("%Y-%m-%dT%H:%M:%S"),
        "post_at_iso": post.isoformat(timespec="seconds"),
        "post_at_utc": post.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "youtube": {"title": meta["title"], "description": meta["description"], "tags": meta["tags"],
                    "category": "GAMING", "made_for_kids": False, "privacy": "public"},
        "chapters": [[round(t, 2), name] for t, name in meta["chapters"]],
        "music": getattr(comp, "music_used", []),
        "safe_zones": S.note(checked["safe"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", required=True, help="the long video's day, YYYY-MM-DD (a weekday)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--art", help="use PNGs in this folder as stand-in art (offline QA)")
    ap.add_argument("--no-video", action="store_true", help="layout, checks, thumbnail and QA sheet only")
    ap.add_argument("--base-url", default="")
    a = ap.parse_args()
    from cc_quiz_build import art_fn
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    entry = make(date.fromisoformat(a.day), out, a.base_url, art_fn(a.art), a.no_video)
    if entry:
        (out / f"bad-quiz-long-{a.day}.json").write_text(json.dumps(entry, indent=1, ensure_ascii=False))
        print(json.dumps({k: v for k, v in entry.items() if k != "youtube"}, indent=1))
        print(entry["youtube"]["title"])
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
