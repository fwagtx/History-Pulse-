#!/usr/bin/env python3
"""
Polls Telegram for replies and acts on them. Run this on a schedule too (e.g. every
5-10 minutes via cron) — it's a short poll, not a long-running daemon, so it fits cleanly
alongside run_pipeline.py without needing a webhook server or public IP.

Recognized replies (must come from the configured chat_id — others are ignored):
  approve <slug>            -> runs /finalize for that slug (prepares upload checklist,
                                still never touches YouTube itself)
  revise <slug> <notes>      -> re-runs the seo/thumbnail/script steps with your notes,
                                then re-sends a fresh review request
  status                     -> lists videos currently awaiting review
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
from telegram_utils import send_message, get_updates
from run_pipeline import render_command, run_claude_headless, build_review_message, load_config, log

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "state"
OFFSET_FILE = STATE_DIR / "telegram_offset.txt"


def get_state(slug: str) -> dict | None:
    p = STATE_DIR / f"{slug}.json"
    return json.loads(p.read_text()) if p.exists() else None


def set_state(slug: str, data: dict):
    (STATE_DIR / f"{slug}.json").write_text(json.dumps(data, indent=2))


def awaiting_review_slugs() -> list[str]:
    slugs = []
    for p in STATE_DIR.glob("*.json"):
        data = json.loads(p.read_text())
        if data.get("status") == "awaiting_review":
            slugs.append(data["slug"])
    return slugs


def handle_approve(slug: str, config: dict):
    state = get_state(slug)
    if not state or state.get("status") != "awaiting_review":
        send_message(config["telegram_bot_token"], config["telegram_chat_id"],
                     f"'{slug}' isn't currently awaiting review — nothing to approve.")
        return
    prompt = render_command("finalize", slug)
    ok, output = run_claude_headless(prompt, config)
    if ok:
        state["status"] = "approved"
        state["approved_at"] = datetime.now(timezone.utc).isoformat()
        set_state(slug, state)
        checklist = ROOT / "content/05_approved" / slug / "upload_checklist.md"
        send_message(config["telegram_bot_token"], config["telegram_chat_id"],
                     f"✅ '{slug}' approved and finalized.\n"
                     f"Checklist ready at: {checklist}\n"
                     f"Upload/scheduling is still done by you in YouTube Studio.")
    else:
        send_message(config["telegram_bot_token"], config["telegram_chat_id"],
                     f"⚠️ Finalize failed for '{slug}'. Check logs/telegram.log.")


def handle_revise(slug: str, notes: str, config: dict):
    state = get_state(slug)
    if not state:
        send_message(config["telegram_bot_token"], config["telegram_chat_id"],
                     f"No pipeline record found for '{slug}'.")
        return
    revision_prompt = (
        f"Apply this revision feedback to the video package for slug '{slug}': {notes}\n\n"
        f"Update whichever of the script (content/02_scripts/{slug}/script.md), SEO package "
        f"(content/03_seo/{slug}/seo.md), or thumbnail concepts "
        f"(content/04_thumbnails/{slug}/concepts.md) the feedback applies to. Keep everything "
        f"else as-is. Follow all constraints in CLAUDE.md."
    )
    ok, output = run_claude_headless(revision_prompt, config)
    if not ok:
        send_message(config["telegram_bot_token"], config["telegram_chat_id"],
                     f"⚠️ Revision failed for '{slug}'. Check logs/telegram.log.")
        return
    state["status"] = "awaiting_review"
    set_state(slug, state)
    send_message(config["telegram_bot_token"], config["telegram_chat_id"],
                 f"Revised '{slug}'. Here's the updated package:\n\n" + build_review_message(slug))


def main():
    config = load_config()
    token, chat_id = config["telegram_bot_token"], str(config["telegram_chat_id"])

    offset = None
    if OFFSET_FILE.exists():
        offset = int(OFFSET_FILE.read_text().strip() or 0)

    result = get_updates(token, offset=offset)
    if not result.get("ok"):
        log(f"Telegram getUpdates failed: {result}")
        return

    updates = result.get("result", [])
    last_id = offset
    for update in updates:
        last_id = update["update_id"]
        msg = update.get("message")
        if not msg or "text" not in msg:
            continue
        if str(msg["chat"]["id"]) != chat_id:
            log(f"Ignoring message from unauthorized chat_id {msg['chat']['id']}")
            continue

        text = msg["text"].strip()
        log(f"Received: {text}")

        if text.lower() == "status":
            pending = awaiting_review_slugs()
            reply = ("Awaiting review: " + ", ".join(pending)) if pending else "Nothing awaiting review."
            send_message(token, chat_id, reply)
        elif text.lower().startswith("approve "):
            slug = text.split(" ", 1)[1].strip()
            handle_approve(slug, config)
        elif text.lower().startswith("revise "):
            rest = text.split(" ", 2)
            if len(rest) < 3:
                send_message(token, chat_id, "Usage: revise <slug> <what to change>")
            else:
                handle_revise(rest[1].strip(), rest[2].strip(), config)
        else:
            send_message(token, chat_id,
                         "Didn't recognize that. Try:\n  approve <slug>\n  revise <slug> <notes>\n  status")

    if last_id is not None:
        OFFSET_FILE.write_text(str(last_id + 1))


if __name__ == "__main__":
    main()
