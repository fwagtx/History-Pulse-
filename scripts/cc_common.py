"""
Shared helpers for the creator-code BAD automation pipeline.

Standard library only — same constraint as the rest of this repo, so there is nothing to
`pip install` and nothing that can break on a machine you haven't touched in a month.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CC_DIR = ROOT / "creator-code"
OUT_DIR = CC_DIR / "out"
STATE_DIR = ROOT / "state"
CONFIG_PATH = CC_DIR / "config.json"

# The code itself. Everything downstream reads it from here so it is never hardcoded twice.
DEFAULT_CODE = "BAD"


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}", flush=True)


def today_stamp() -> str:
    """Shop rotates at 00:00 UTC, so dating by UTC keeps filenames aligned with the rotation."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_config(required: tuple = ()) -> dict:
    if not CONFIG_PATH.exists():
        log(f"ERROR: {CONFIG_PATH} not found.")
        log("Copy creator-code/config.example.json to creator-code/config.json and fill it in.")
        sys.exit(1)
    cfg = json.loads(CONFIG_PATH.read_text())
    missing = [k for k in required if not cfg.get(k) or str(cfg[k]).startswith("PASTE_")]
    if missing:
        log(f"ERROR: config.json is missing values for: {', '.join(missing)}")
        sys.exit(1)
    return cfg


def creator_code(cfg: dict) -> str:
    return (cfg.get("creator_code") or DEFAULT_CODE).upper()


def http_get_json(url: str, headers: dict | None = None, timeout: int = 20) -> dict:
    """GET returning parsed JSON. Raises on failure so callers can decide how loud to be."""
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return path


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        log(f"WARN: {path} is not valid JSON, treating as empty.")
        return default


def notify(cfg: dict, message: str):
    """Send a Telegram message, reusing the repo's existing helper. Never fatal."""
    token = cfg.get("telegram_bot_token", "")
    chat_id = cfg.get("telegram_chat_id", "")
    if not token or not chat_id or token.startswith("PASTE_"):
        log("Telegram not configured — skipping notification.")
        return
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from telegram_utils import send_message
        send_message(token, chat_id, message)
    except Exception as e:  # noqa: BLE001 - notification must never kill the pipeline
        log(f"WARN: Telegram notification failed: {e}")
