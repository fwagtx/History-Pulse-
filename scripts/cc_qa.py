"""
Visual QA: render stills of one format at chosen timestamps, without encoding video.

    python3 scripts/cc_qa.py <format> <t1,t2,...> [--art DIR] [--out DIR]

--art DIR uses PNGs from DIR as stand-in cosmetic art (for machines that can't
reach the image CDN). Without it, real art is fetched.
"""
import base64, glob, importlib, json, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cc_formats as F
from cc_common import OUT_DIR
from cc_motion import snapshot


def main():
    fmt, times = sys.argv[1], [float(x) for x in sys.argv[2].split(",")]
    art_dir = sys.argv[sys.argv.index("--art") + 1] if "--art" in sys.argv else None
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else OUT_DIR / "_qa"
    shop_path = sorted(OUT_DIR.glob("20*/shop.json"))[-1]
    shop = json.loads(shop_path.read_text())
    cache = {}
    if art_dir:
        uris = ["data:image/png;base64," + base64.b64encode(open(f, "rb").read()).decode()
                for f in sorted(glob.glob(f"{art_dir}/*.png"))]
        def art(item):
            if item["name"] not in cache:
                cache[item["name"]] = uris[len(cache) % len(uris)] if uris else ""
            return cache[item["name"]]
    else:
        from cc_images import fetch_first, candidates
        def art(item):
            if item["name"] not in cache:
                cache[item["name"]] = fetch_first(candidates(item))
            return cache[item["name"]]
    d = date.fromisoformat(shop["shop_day"])
    ctx = F.Ctx(shop=shop, art=art, day=d, seed=int(d.strftime("%Y%m%d")))
    fn = getattr(F, fmt, None) or importlib.import_module(f"cc_fmt_{fmt}").build
    v = fn(ctx)
    if v is None:
        print(f"{fmt}: returned None (data can't support it today)"); return
    print(f"{fmt}: {v.comp.duration:.2f}s  cues={len(v.comp.cues)}  title={v.title!r}")
    print("tags:", " ".join("#" + t for t in v.hashtags))
    for p in snapshot(v.comp, times, out / fmt):
        print("  still", p)


if __name__ == "__main__":
    main()
