"""The nightly build, run in a scheduled Claude session instead of GitHub
Actions: today's shop videos, the quiz day two weeks out (with that day's long
video), each published to its folder in the R2 bucket (cc_store) that Metricool
picks the videos up from. A step that's already published is skipped, so the
same run can be fired again after a failure or a lagging shop.

    python3 scripts/cc_nightly.py                 # shop + quiz, whatever isn't out yet
    python3 scripts/cc_nightly.py shop            # just today's shop videos
    python3 scripts/cc_nightly.py quiz [DAY]      # just a quiz day (default: 14 days out)
    python3 scripts/cc_nightly.py records         # refresh the records' copy in the bucket
    python3 scripts/cc_nightly.py music DIR       # put a music library (catalog.json + mp3s) in the bucket

Needs the R2 settings (cc_store.py) and network access to fortnite-api.com.
Exit code 0 when everything asked for is published.
"""
import gzip
import os
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cc_store as STORE  # noqa: E402
from cc_common import OUT_DIR, ROOT, log  # noqa: E402

SHOP_FILES = ("bad-*.mp4", "bad-*-cover.png", "bad-*-qa.jpg", "manifest.json")
QUIZ_FILES = ("bad-quiz-*.mp4", "bad-quiz-*-cover.png", "bad-quiz-*-qa.jpg", "manifest.json")


def _reachable(url: str) -> bool:
    import urllib.error
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "usecodebad"}, method="GET")
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status < 500
    except urllib.error.HTTPError as e:      # the site answered: it's reachable
        return e.code < 500
    except Exception:  # noqa: BLE001 - blocked or down
        return False


def preflight() -> list:
    """What would make tonight's videos wrong, in plain words ([] = go)."""
    problems = STORE.check()
    if not _reachable("https://fortnite-api.com/v2/cosmetics/br/search?name=Peely"):
        problems.append("fortnite-api.com isn't reachable from this environment (its network access): "
                        "the videos would have no item pictures, so nothing is built")
    return problems


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _run(args: list, timeout: int) -> int:
    env = dict(os.environ, CC_RUNNER="1", PYTHONUNBUFFERED="1")
    log("$ " + " ".join(args))
    try:
        return subprocess.run([sys.executable] + args, cwd=ROOT, env=env, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        log(f"  timed out after {timeout // 60} min")
        return 124


def shop(day: date | None = None) -> bool:
    day = day or _utc_today()
    tag = f"shop-{day.isoformat()}"
    if STORE.exists(f"{tag}/manifest.json"):
        log(f"{tag}: already published")
        return True
    out = OUT_DIR / day.isoformat()
    shutil.rmtree(out, ignore_errors=True)
    if _run(["scripts/cc_build.py", "--wait", "50"], timeout=150 * 60) != 0 or not (out / "manifest.json").exists():
        log(f"{tag}: the build failed (a shop that hasn't rotated yet gets retried by the next run)")
        return False
    urls = STORE.put_dir(out, tag, SHOP_FILES)
    log(f"{tag}: published {len(urls)} files, e.g. {urls[-1]}")
    return True


def quiz(day: date | None = None) -> bool:
    day = day or _utc_today() + timedelta(days=14)
    tag = f"quiz-{day.isoformat()}"
    if STORE.exists(f"{tag}/manifest.json"):
        log(f"{tag}: already published")
        return True
    out = OUT_DIR / f"quiz-{day.isoformat()}"
    shutil.rmtree(out, ignore_errors=True)
    if _run(["scripts/cc_quiz_build.py", "--date", day.isoformat()], timeout=180 * 60) != 0:
        log(f"{tag}: the build failed")
        return False
    if not (out / "manifest.json").exists():
        log(f"{tag}: nothing planned for that day")
        return True
    urls = STORE.put_dir(out, tag, QUIZ_FILES)
    log(f"{tag}: published {len(urls)} files, e.g. {urls[-1]}")
    return True


def records() -> bool:
    """Today's records, fresh from fortnite-api.com, as the bucket's weekly copy
    (what builds read when they don't fetch their own)."""
    import cc_rarity as R
    R.load(fresh=True)
    src = OUT_DIR / "_data" / "br-fresh.json"
    gz = OUT_DIR / "_data" / "br-full.json.gz"
    with open(src, "rb") as f, gzip.open(gz, "wb", compresslevel=9) as g:
        shutil.copyfileobj(f, g)
    url = STORE.put(gz, "cosmetics-data/br-full.json.gz")
    log(f"records: {gz.stat().st_size / 1e6:.1f} MB -> {url}")
    return True


def music(folder: Path) -> bool:
    """A music library (catalog.json + its mp3s) into the bucket; the catalog
    keeps only the tracks that are there."""
    import json
    cat = json.loads((folder / "catalog.json").read_text())
    have = [t for t in cat["tracks"] if (folder / t["file"]).exists()]
    for t in have:
        STORE.put(folder / t["file"], f"music-library/{t['file']}")
    trimmed = folder / "catalog.trimmed.json"
    trimmed.write_text(json.dumps({"tracks": have}, indent=1, ensure_ascii=False))
    STORE.put(trimmed, "music-library/catalog.json")
    trimmed.unlink()
    log(f"music: {len(have)} of {len(cat['tracks'])} tracks in the bucket")
    return True


def main(argv: list) -> int:
    what = argv[1] if len(argv) > 1 else "all"
    problems = preflight() if what in ("all", "shop", "quiz", "records") else STORE.check()
    if problems:
        print("Not building:\n  " + "\n  ".join(problems))
        return 2
    t0 = time.time()
    if what == "shop":
        ok = shop(date.fromisoformat(argv[2]) if len(argv) > 2 else None)
    elif what == "quiz":
        ok = quiz(date.fromisoformat(argv[2]) if len(argv) > 2 else None)
    elif what == "records":
        ok = records()
    elif what == "music":
        ok = music(Path(argv[2]))
    elif what == "all":
        ok = shop()
        ok = quiz() and ok
    else:
        print(__doc__)
        return 2
    log(f"nightly {what}: {'OK' if ok else 'FAILED'} in {(time.time() - t0) / 60:.0f} min")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
