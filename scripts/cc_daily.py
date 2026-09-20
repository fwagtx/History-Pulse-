"""
Daily orchestrator for the creator-code BAD pipeline.

Runs: fetch shop -> render card -> write captions -> build a publish queue -> ping Telegram.

Deliberately stops at "assets are ready". It does not upload anything. Auto-publishing is a
later addition and belongs behind its own explicit config flag — this mirrors the History
Pulse rule that the agent prepares packages but a human owns the publish decision.

Usage:
    python3 scripts/cc_daily.py [--fixture] [--png]
"""

import subprocess
import sys
from pathlib import Path

from cc_common import (OUT_DIR, ROOT, log, load_config, creator_code, read_json,
                       write_json, notify, today_stamp)

SCRIPTS = Path(__file__).resolve().parent
LOCK = ROOT / "state" / "cc_daily.lock"


def run_step(name: str, argv: list) -> bool:
    log(f"--- step: {name} ---")
    result = subprocess.run([sys.executable, str(SCRIPTS / argv[0])] + argv[1:],
                            cwd=str(ROOT), capture_output=True, text=True, timeout=300)
    if result.stdout:
        print(result.stdout.rstrip(), flush=True)
    if result.returncode != 0:
        log(f"STEP FAILED: {name}\n{result.stderr[-1500:]}")
        return False
    return True


def build_queue(stamp: str, code: str) -> dict:
    """A checklist of what to post where — the human-facing output of the run."""
    day_dir = OUT_DIR / stamp
    captions = read_json(day_dir / "captions.json", {})
    have_png = (day_dir / "card.png").exists()

    return {
        "date": stamp,
        "code": code,
        "assets": {
            "card_html": str((day_dir / "card.html").relative_to(ROOT)),
            "card_png": str((day_dir / "card.png").relative_to(ROOT)) if have_png else None,
            "captions": str((day_dir / "captions.json").relative_to(ROOT)),
        },
        "targets": [
            {"platform": "youtube_shorts", "status": "pending", "automatable": True,
             "note": "videos.insert is 1 unit/call, 100/day free since Jun 2026",
             "title": captions.get("short", {}).get("title", "")},
            {"platform": "youtube_long", "status": "pending", "automatable": True,
             "title": captions.get("youtube", {}).get("title", "")},
            {"platform": "discord", "status": "pending", "automatable": True},
            {"platform": "telegram", "status": "pending", "automatable": True},
            {"platform": "x", "status": "pending", "automatable": True,
             "note": "free tier ~500 posts/month — plenty for daily"},
            {"platform": "tiktok", "status": "pending", "automatable": False,
             "note": "private-only until your app passes TikTok's audit — upload manually"},
            {"platform": "instagram", "status": "pending", "automatable": False,
             "note": "needs Business account + Graph API"},
        ],
    }


def main():
    if LOCK.exists():
        log("Lock present — a run may already be in progress. Exiting.")
        sys.exit(0)
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text("running")
    try:
        cfg = load_config()
        code = creator_code(cfg)
        stamp = today_stamp()
        log(f"Daily run for {stamp}, code {code}")

        shop_args = ["cc_shop.py"] + (["--fixture"] if "--fixture" in sys.argv else [])
        render_args = ["cc_render.py"] + (["--png"] if "--png" in sys.argv else [])

        for name, argv in (("shop", shop_args),
                           ("render", render_args),
                           ("captions", ["cc_captions.py"])):
            if not run_step(name, argv):
                notify(cfg, f"⚠️ Creator-code pipeline failed at '{name}' for {stamp}.")
                sys.exit(1)

        queue = build_queue(stamp, code)
        out = write_json(OUT_DIR / stamp / "publish_queue.json", queue)
        log(f"Wrote publish queue -> {out}")

        captions = read_json(OUT_DIR / stamp / "captions.json", {})
        shop = read_json(OUT_DIR / stamp / "shop.json", {})
        auto = sum(1 for t in queue["targets"] if t["automatable"])
        notify(cfg, (
            f"🟡 Item shop package ready — {stamp}\n\n"
            f"Headline: {captions.get('headline', '?')}\n"
            f"Items: {shop.get('item_count', 0)}\n"
            f"Code: {code}\n\n"
            f"Title: {captions.get('youtube', {}).get('title', '')}\n\n"
            f"{auto} of {len(queue['targets'])} targets are auto-publishable.\n"
            f"Assets: creator-code/out/{stamp}/"
        ))
        log("Done.")
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
