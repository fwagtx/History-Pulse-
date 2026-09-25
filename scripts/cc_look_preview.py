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
still every few seconds, TikTok-zone copies of them, a contact sheet, and prints
a QA summary: length, post checks and how much of the lime code is on screen in
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
    """Pixels close to the code's lime inside TikTok's safe area."""
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return -1
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lime = (r > 190) & (g > 215) & (b < 140) & (r - b > 110)
    lime[:190] = False
    lime[1480:] = False
    lime[880:, 960:] = False
    return int(lime.sum())


def zones(png: Path, out: Path):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    im = Image.open(png).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle((0, 0, 1080, 190), fill=(255, 0, 0, 70))
    d.rectangle((0, 1480, 1080, 1920), fill=(255, 0, 0, 70))
    d.rectangle((960, 880, 1080, 1480), fill=(255, 0, 0, 70))
    Image.alpha_composite(im, ov).convert("RGB").save(out, quality=85)


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
    os.environ["CC_LOOKS"] = args.looks

    from cc_formats import Ctx
    from cc_build import post_problems
    import cc_looks as LK
    art = stand_in_art(args.art)
    if args.shop:
        from cc_build import builder
        shop = json.loads(Path(args.shop).read_text())
        day = date.fromisoformat(shop["shop_day"])
        ctx = Ctx(shop=shop, art=art, day=day, seed=int(day.strftime("%Y%m%d")))
        fn = builder(args.format)
        v = fn(ctx) if fn else None
    else:
        import cc_quiz as Q
        plan = json.loads(PLAN.read_text())
        day = date.fromisoformat(args.date)
        spec = next((s for s in plan["videos"] if s["date"] == args.date and s["format"] == args.format
                     and s.get("series", "") == args.series), None)
        if not spec:
            raise SystemExit(f"No {args.format} {args.series} on {args.date} in the plan.")
        ctx = Ctx(shop={"items": []}, art=art, day=day, seed=int(day.strftime("%Y%m%d")))
        v = Q.build(spec, plan["items"], ctx)
    if v is None:
        raise SystemExit("The format returned nothing for this data (it would fall back).")

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
    except Exception as e:  # noqa: BLE001 - QA extra
        print("contact sheet skipped:", e)

    probs = post_problems(v)
    lime = {p.stem: lime_pixels(p) for p in stills}
    print(json.dumps({
        "format": v.format, "look": LK.draw.last or "classic",
        "duration": round(dur, 2), "length_ok": 62 - .01 <= dur <= 90,
        "post_problems": probs, "title": v.title, "yt_title": v.yt_title,
        "lime_code_pixels_min": min(lime.values()) if lime else None,
        "lime_code_pixels": lime, "out": str(out),
    }, indent=1))


if __name__ == "__main__":
    main()
