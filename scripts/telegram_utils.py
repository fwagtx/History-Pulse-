"""
Minimal Telegram Bot API client using only the Python standard library —
no `pip install` needed, keeps the whole pipeline dependency-free.

Setup (one-time, free):
1. In Telegram, message @BotFather -> /newbot -> follow prompts -> copy the token it gives you.
2. Message your new bot anything (e.g. "hi") so it can see your chat.
3. Run: python3 scripts/telegram_utils.py --find-chat-id <YOUR_BOT_TOKEN>
   This prints your chat_id. Put both values in config.json (copy config.example.json first).
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _call(token: str, method: str, params: dict | None = None, timeout: int = 15):
    url = API_BASE.format(token=token, method=method)
    data = None
    if params:
        data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.URLError as e:
        return {"ok": False, "error": str(e)}


def send_message(token: str, chat_id: str, text: str):
    """Send a Telegram message. Splits long messages since Telegram caps at 4096 chars."""
    chunks = [text[i:i + 3800] for i in range(0, len(text), 3800)] or [text]
    results = []
    for chunk in chunks:
        results.append(_call(token, "sendMessage", {
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": "true",
        }))
    return results


def get_updates(token: str, offset: int | None = None, timeout: int = 0):
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    return _call(token, "getUpdates", params, timeout=timeout + 10)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--find-chat-id":
        token = sys.argv[2]
        result = get_updates(token)
        if not result.get("ok"):
            print("Error calling Telegram:", result)
            sys.exit(1)
        chats = {}
        for update in result.get("result", []):
            msg = update.get("message") or update.get("channel_post")
            if msg:
                chat = msg["chat"]
                chats[chat["id"]] = chat.get("username") or chat.get("first_name", "unknown")
        if not chats:
            print("No messages found yet. Send your bot a message in Telegram first, then rerun this.")
        else:
            print("Found chat IDs:")
            for cid, name in chats.items():
                print(f"  chat_id={cid}  ({name})")
    else:
        print("Usage: python3 scripts/telegram_utils.py --find-chat-id <BOT_TOKEN>")
