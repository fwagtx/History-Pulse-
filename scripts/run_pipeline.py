#!/usr/bin/env python3
"""
Runs one video through research -> script -> seo -> thumbnail using Claude Code's
headless mode (no terminal interaction needed), then messages the human on Telegram
for approval. Intended to be triggered by cron, e.g. nightly.

It does NOT ever call /review's approval or /finalize — those only happen after a human
replies on Telegram, handled by check_telegram.py. This script's job stops at "package is
ready, please review."

Usage: python3 scripts/run_pipeline.py
(run from the project root, or cron will `cd` there first — see CRON_SETUP.md)
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = ROOT / "state" / "pipeline.lock"
COMPLETED_FILE = ROOT / "state" / "completed_topics.txt"
STATE_DIR = ROOT / "state"


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}", flush=True)


def load_config():
    cfg_path = ROOT / "config.json"
    if not cfg_path.exists():
        log("ERROR: config.json not found. Copy config.example.json to config.json and fill it in.")
        sys.exit(1)
    return json.loads(cfg_path.read_text())


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:60].strip("-")


def next_topic():
    queue_path = ROOT / "queue.txt"
    completed = set()
    if COMPLETED_FILE.exists():
        completed = set(l.strip() for l in COMPLETED_FILE.read_text().splitlines() if l.strip())
    for line in queue_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line not in completed:
            return line
    return None


def mark_completed(topic: str):
    with open(COMPLETED_FILE, "a") as f:
        f.write(topic + "\n")


def render_command(cmd_name: str, arguments: str) -> str:
    """Read a .claude/commands/<cmd_name>.md template and substitute $ARGUMENTS.
    Avoids depending on whether slash commands resolve identically in headless mode."""
    cmd_path = ROOT / ".claude" / "commands" / f"{cmd_name}.md"
    template = cmd_path.read_text()
    return template.replace("$ARGUMENTS", arguments)


def run_claude_headless(prompt: str, config: dict, timeout_seconds: int = 900) -> tuple[bool, str]:
    cmd = [
        config.get("claude_binary", "claude"),
        "-p", prompt,
        "--permission-mode", "acceptEdits",
        "--allowedTools", config.get("allowed_tools", "Bash,Read,Write,Edit,WebSearch,WebFetch"),
        "--max-turns", str(config.get("max_pipeline_turns", 40)),
    ]
    log(f"Running: claude -p <prompt of {len(prompt)} chars> (timeout {timeout_seconds}s)")
    try:
        result = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout_seconds
        )
    except subprocess.TimeoutExpired:
        return False, "Claude Code call timed out."
    if result.returncode != 0:
        return False, f"Claude Code exited {result.returncode}.\nSTDERR:\n{result.stderr[-2000:]}"
    return True, result.stdout


def read_if_exists(path: Path, max_chars: int = 1200) -> str:
    if not path.exists():
        return "(missing)"
    text = path.read_text()
    return text if len(text) <= max_chars else text[:max_chars] + "\n...[truncated]"


def build_review_message(slug: str) -> str:
    research = read_if_exists(ROOT / "content/01_research" / slug / "notes.md", 800)
    seo = read_if_exists(ROOT / "content/03_seo" / slug / "seo.md", 1200)
    thumb = read_if_exists(ROOT / "content/04_thumbnails" / slug / "concepts.md", 800)
    return (
        f"🎬 Video ready for review: {slug}\n\n"
        f"— RESEARCH / RELEVANCE HOOK —\n{research}\n\n"
        f"— SEO PACKAGE —\n{seo}\n\n"
        f"— THUMBNAIL CONCEPTS —\n{thumb}\n\n"
        f"Full script: content/02_scripts/{slug}/script.md\n\n"
        f"Reply with:\n"
        f"  approve {slug}\n"
        f"  revise {slug} <what to change>\n"
    )


def main():
    if LOCK_FILE.exists():
        log("Lock file present — another run may be in progress. Exiting.")
        sys.exit(0)
    LOCK_FILE.write_text(str(os.getpid()))
    try:
        config = load_config()
        topic = next_topic()
        if not topic:
            log("No new topics in queue.txt. Nothing to do.")
            return

        slug = slugify(topic)
        log(f"Processing topic: '{topic}' -> slug '{slug}'")

        steps = [
            ("research", f"{topic}\n\nMANDATORY: use exactly this slug for every file/folder "
                          f"in this pipeline: {slug} (do not invent a different one)."),
            ("script", slug),
            ("seo", slug),
            ("thumbnail", slug),
        ]

        for cmd_name, args in steps:
            prompt = render_command(cmd_name, args)
            ok, output = run_claude_headless(prompt, config)
            log(f"Step '{cmd_name}' {'OK' if ok else 'FAILED'}. Output tail:\n{output[-800:]}")
            if not ok:
                from telegram_utils import send_message
                send_message(config["telegram_bot_token"], config["telegram_chat_id"],
                             f"⚠️ Pipeline failed on step '{cmd_name}' for '{slug}'. Check logs/pipeline.log.")
                return

        # Record pending-review state so check_telegram.py knows what "approve <slug>" means
        STATE_DIR.mkdir(exist_ok=True)
        (STATE_DIR / f"{slug}.json").write_text(json.dumps({
            "slug": slug, "topic": topic, "status": "awaiting_review",
            "created": datetime.now(timezone.utc).isoformat()
        }, indent=2))

        from telegram_utils import send_message
        message = build_review_message(slug)
        send_message(config["telegram_bot_token"], config["telegram_chat_id"], message)
        log(f"Sent review request to Telegram for '{slug}'.")

        mark_completed(topic)
    finally:
        LOCK_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
