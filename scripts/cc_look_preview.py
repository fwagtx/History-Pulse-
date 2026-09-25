"""
Render one video with the new looks switched on, locally, for checking.

    # a quiz-plan video (On This Day, Guess the Season, a Fortnitemares throwback...)
    python3 scripts/cc_look_preview.py --date 2026-10-02 --format on_this_day --art DIR
    # a shop video, from a saved shop.json
    python3 scripts/cc_look_preview.py --shop creator-code/out/2026-09-23/shop.json --format og_check --art DIR

--art DIR    stand-in art (this machine can't download Fortnite's images): a PNG
             named after the item (e.g. rex.png) is used for that item, the rest
             cycle through the folder.
--looks X    what CC_LOOKS should be: "all" (default), "none" for the classic
             version, or a list of formats.
--no-video   stills only (fast).

Writes creator-code/out/preview/<format>-<day>/: the mp4 (with its soundtrack), a
still every few seconds, copies of them with the apps' UI zones shaded (see
cc_safe.py), a contact sheet, an apps.jpg sheet showing key stills under the
TikTok / Instagram / YouTube / Facebook UI, and prints a QA summary: length,
post checks, the safe-zone check and how much of the lime code is on screen in
each still.
"""

import argparse
import base64
import glob
import hashlib
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cc_common import CC_DIR, OUT_DIR  # noqa: E402

PLAN = CC_DIR / "quiz" / "plan.json"


def slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-")


def stand_in_art(art_dir: str):
    files = sorted(glob.glob(f"{art_dir}/*.png"))
    by_name = {Path(f).stem: f for f in files}
    cache = {}

    def art(item):
        key = item.get("id") or item["name"]
        if key not in cache:
            f = by_name.get(slug(item["name"]))
            if not f and files:
                f = files[int(hashlib.md5(key.encode()).hexdigest(), 16) % len(files)]
            cache[key] = ("data:image/png;base64," + base64.b64encode(open(f, "rb").read()).decode()) if f else ""
        return cache[key]
    return art


def lime_pixels(png: Path) -> int:
    """Pixels close to the code's lime inside the apps' safe box (cc_safe)."""
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return -1
    import cc_safe as S
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lime = (r > 190) & (g > 215) & (b < 140) & (r - b > 110)
    lime[:S.TOP] = False
    lime[S.BOTTOM:] = False
    lime[:, :S.LEFT] = False
    lime[:, S.RIGHT_TOP:] = False
    lime[S.RAIL_TOP:, S.RIGHT:] = False
    return int(lime.sum())


def zones(png: Path, out: Path):
    try:
        from PIL import Image
    except ImportError:
        return
    import cc_safe as S
    S.shaded(Image.open(png)).save(out, quality=85)


def build_video(fmt: str, day_s: str | None, series: str, shop_path: str | None, art_dir: str,
                looks: str = ""):
    """The Video for one format: a quiz-plan entry (day_s, series) or a shop
    format from a saved shop.json. `looks` sets CC_LOOKS when given."""
    if looks:
        os.environ["CC_LOOKS"] = looks
    from cc_formats import Ctx
    art = stand_in_art(art_dir)
    if shop_path:
        from cc_build import builder
        shop = json.loads(Path(shop_path).read_text())
        day = date.fromisoformat(shop["shop_day"])
        ctx = Ctx(shop=shop, art=art, day=day, seed=int(day.strftime("%Y%m%d")))
        fn = builder(fmt)
        v = fn(ctx) if fn else None
    else:
        import cc_quiz as Q
        plan = json.loads(PLAN.read_text())
        day = date.fromisoformat(day_s)
        spec = next((s for s in plan["videos"] if s["date"] == day_s and s["format"] == fmt
                     and s.get("series", "") == series), None)
        if not spec:
            raise SystemExit(f"No {fmt} {series} on {day_s} in the plan.")
        ctx = Ctx(shop={"items": []}, art=art, day=day, seed=int(day.strftime("%Y%m%d")))
        v = Q.build(spec, plan["items"], ctx)
    if v is None:
        raise SystemExit("The format returned nothing for this data (it would fall back).")
    v.day = day
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", required=True)
    ap.add_argument("--date", help="quiz plan day, YYYY-MM-DD")
    ap.add_argument("--series", default="", help="for a series entry, e.g. fortnitemares")
    ap.add_argument("--shop", help="a saved shop.json, for shop formats")
    ap.add_argument("--art", required=True, help="folder of stand-in PNGs")
    ap.add_argument("--looks", default="all")
    ap.add_argument("--every", type=float, default=3.0, help="seconds between QA stills")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--out", help="output folder (default creator-code/out/preview/...)")
    args = ap.parse_args()

    from cc_build import post_problems
    import cc_looks as LK
    import cc_safe as S
    v = build_video(args.format, args.date, args.series, args.shop, args.art, args.looks)
    day = v.day

    tag = f"{args.format}{'-' + args.series if args.series else ''}-{day.isoformat()}"
    if args.looks == "none":
        tag += "-classic"
    out = Path(args.out) if args.out else OUT_DIR / "preview" / tag
    out.mkdir(parents=True, exist_ok=True)
    dur = v.comp.duration
    times = sorted({0.0, *[round(t, 2) for t in [i * args.every for i in range(1, int(dur / args.every) + 1)]
                           if t < dur - .05], round(dur - 1.0, 2)})
    from cc_motion import render, snapshot
    if args.no_video:
        stills = snapshot(v.comp, times, out / "stills")
    else:
        from cc_audio import soundtrack
        wav = soundtrack(v.comp, int(day.strftime("%Y%m%d")), out / "audio.wav")
        render(v.comp, out / f"{tag}.mp4", audio=wav, stills=times, stills_dir=out / "stills")
        wav.unlink(missing_ok=True)
        stills = sorted((out / "stills").glob("t*.png"))
    for p in stills:
        zones(p, out / "stills" / (p.stem + "-zones.jpg"))
    try:
        from cc_build import contact_sheet
        contact_sheet(sorted((out / "stills").glob("t*.png")), out / "sheet.jpg")
        pick = [stills[0]] + [stills[i] for i in (len(stills) // 3, 2 * len(stills) // 3)] + [stills[-1]]
        S.app_sheet(pick, out / "apps.jpg")
    except Exception as e:  # noqa: BLE001 - QA extra
        print("contact sheet skipped:", e)

    safe = S.check(v.comp)
    (out / "safe.json").write_text(json.dumps(safe, indent=1))
    print(S.summary(safe, 40))
    probs = post_problems(v)
    lime = {p.stem: lime_pixels(p) for p in stills}
    print(json.dumps({
        "format": v.format, "look": LK.draw.last or "classic",
        "duration": round(dur, 2), "length_ok": 62 - .01 <= dur <= 90,
        "post_problems": probs, "title": v.title, "yt_title": v.yt_title,
        "safe_ok": safe["ok"], "safe_violations": len(safe["violations"]), "cover_problems": len(safe["cover"]),
        "lime_code_pixels_min": min(lime.values()) if lime else None,
        "lime_code_pixels": lime, "out": str(out),
    }, indent=1))


if __name__ == "__main__":
    main()
