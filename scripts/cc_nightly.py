"""The nightly build, run in a scheduled Claude session instead of GitHub
Actions: today's shop videos, the quiz day two weeks out (with that day's long
video), each published to its folder in the R2 bucket (cc_store) that Metricool
picks the videos up from. A step that's already published is skipped, so the
same run can be fired again after a failure or a lagging shop.

Each published folder is then checked file by file in the bucket and a copy of
its manifest and file list is committed to creator-code/published/<tag>.json,
for the 7 AM Routine, which reads without the bucket's keys. Every run leaves
its outcome in the bucket at _status/nightly.json (and its log beside it).

    python3 scripts/cc_nightly.py                 # shop + quiz, whatever isn't out yet
    python3 scripts/cc_nightly.py shop            # just today's shop videos
    python3 scripts/cc_nightly.py quiz [DAY]      # just a quiz day (default: 14 days out)
    python3 scripts/cc_nightly.py records         # refresh the records' copy in the bucket
    python3 scripts/cc_nightly.py music DIR       # put a music library (catalog.json + mp3s) in the bucket

Needs the R2 settings (cc_store.py) and network access to fortnite-api.com.
Exit code 0 when everything asked for is published.
"""
import gzip
import json
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

BRANCH = "claude/creator-code-bad-automation-0jjc1k"

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


def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "user.name=usecodebad-bot",
                           "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com", *args],
                          cwd=ROOT, capture_output=True, text=True, timeout=300,
                          env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))


def _push(path: Path, message: str) -> bool:
    """Commit one file and push it to the branch the Routines read (best effort)."""
    try:
        _git("add", str(path.relative_to(ROOT)))
        if _git("diff", "--cached", "--quiet").returncode == 0:
            return True
        if _git("commit", "-m", message).returncode != 0:
            return False
        for _ in range(3):
            if _git("push", "origin", f"HEAD:{BRANCH}").returncode == 0:
                return True
            _git("pull", "--rebase", "--autostash", "origin", BRANCH)
    except (OSError, subprocess.SubprocessError):
        pass
    return False


def _can_push() -> str:
    """Whether this session may push to the branch: 'yes', or git's reason."""
    try:
        r = _git("push", "--dry-run", "origin", f"HEAD:{BRANCH}")
    except (OSError, subprocess.SubprocessError) as e:
        return repr(e)[:200]
    if r.returncode == 0:
        return "yes"
    lines = r.stderr.strip().splitlines() or ["no"]
    return next((x for x in lines if x.startswith(("fatal:", "error:", "remote:"))), lines[-1])[:200]


def publish(out: Path, tag: str, patterns) -> bool:
    """Upload a built folder, then check it in the bucket and commit the repo's copy."""
    urls = STORE.put_dir(out, tag, patterns)
    log(f"{tag}: uploaded {len(urls)} files, e.g. {urls[-1]}")
    return _commit_copy(tag, out, {u.rsplit("/", 1)[-1] for u in urls})


def _commit_copy(tag: str, local: Path | None = None, uploaded: set = frozenset()) -> bool:
    """The repo's copy of tag/ (what the 7 AM Routine reads), committed and pushed."""
    copy = STORE.record(tag, local)
    rec = json.loads(copy.read_text())
    missing = sorted(set(uploaded) - set(rec["files"]))
    if missing:
        log(f"{tag}: not in the bucket at the built size: {', '.join(missing)}")
    pushed = _push(copy, f"Published {tag}: {len(rec['files'])} files (automatic)")
    log(f"{tag}: {len(rec['files'])} files checked in the bucket; repo copy "
        + ("committed" if pushed else "NOT pushed - the 7 AM Routine can't see this folder"))
    NOTES.setdefault("published", {})[tag] = len(rec["files"])
    if not pushed:
        NOTES.setdefault("problems", []).append(f"couldn't push creator-code/published/{tag}.json")
    return pushed and not missing and "manifest" in rec


def _already(tag: str) -> bool:
    """A folder published by an earlier run: make sure its repo copy got pushed too."""
    log(f"{tag}: already published")
    if (STORE.PUBLISHED / f"{tag}.json").exists():
        return True
    return _commit_copy(tag)


NOTES: dict = {}


def status(what: str, ok: bool, problems: list, t0: float):
    """The run's outcome (and its log) in the bucket, for whoever checks on it."""
    now = datetime.now(timezone.utc)
    doc = {"at": now.isoformat(timespec="seconds"), "what": what, "ok": ok,
           "minutes": round((time.time() - t0) / 60, 1), "problems": problems + NOTES.get("problems", []),
           "published": NOTES.get("published", {}), "can_push": _can_push()}
    logfile = os.environ.get("CC_LOG") or os.path.realpath("/proc/self/fd/1")
    try:
        if os.path.isfile(logfile) and os.path.getsize(logfile) < 20_000_000:
            key = f"_status/nightly-{now:%Y-%m-%d-%H%M}.log"
            doc["log"] = STORE.put(Path(logfile), key)
            doc["log_tail"] = Path(logfile).read_text(errors="replace").splitlines()[-40:]
        tmp = OUT_DIR / "_status.json"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(doc, indent=1))
        STORE.put(tmp, "_status/nightly.json")
    except Exception as e:  # noqa: BLE001 - the bucket itself may be what's wrong
        log(f"couldn't leave the status in the bucket: {e!r}"[:300])


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
        return _already(tag)
    out = OUT_DIR / day.isoformat()
    shutil.rmtree(out, ignore_errors=True)
    if _run(["scripts/cc_build.py", "--wait", "50"], timeout=150 * 60) != 0 or not (out / "manifest.json").exists():
        log(f"{tag}: the build failed (a shop that hasn't rotated yet gets retried by the next run)")
        return False
    return publish(out, tag, SHOP_FILES)


def quiz(day: date | None = None) -> bool:
    day = day or _utc_today() + timedelta(days=14)
    tag = f"quiz-{day.isoformat()}"
    if STORE.exists(f"{tag}/manifest.json"):
        return _already(tag)
    out = OUT_DIR / f"quiz-{day.isoformat()}"
    shutil.rmtree(out, ignore_errors=True)
    if _run(["scripts/cc_quiz_build.py", "--date", day.isoformat()], timeout=180 * 60) != 0:
        log(f"{tag}: the build failed")
        return False
    if not (out / "manifest.json").exists():
        log(f"{tag}: nothing planned for that day")
        return True
    return publish(out, tag, QUIZ_FILES)


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
    t0 = time.time()
    problems = preflight() if what in ("all", "shop", "quiz", "records") else STORE.check()
    if problems:
        print("Not building:\n  " + "\n  ".join(problems), flush=True)
        if what in ("all", "shop", "quiz"):
            status(what, False, problems, t0)
        return 2
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
    if what in ("all", "shop", "quiz"):
        status(what, ok, [], t0)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
