"""
14-day re-entry reminder scheduler — the highest-ROI system in this pipeline.

Fortnite creator codes expire 14 days after a supporter enters one. Most creators chase new
viewers and silently lose the supporters they already converted. One supporter who re-enters
all year is worth ~26 windows instead of one, so even a modest re-entry rate multiplies
lifetime value several times over for effectively zero cost.

Consent model: **opt-in only.** People are added when they tell you they entered the code
(a Discord command, a Telegram message). There is no scraping and no cold outreach here —
that would be spam under Epic's terms and would put the code at risk. `--remove` is honoured
permanently via an opt-out list, so a removed person is never re-added by a later import.

Usage:
    python3 scripts/cc_remind.py --add <handle> --channel discord
    python3 scripts/cc_remind.py --remove <handle>
    python3 scripts/cc_remind.py --confirm <handle>     # they re-entered; restart their clock
    python3 scripts/cc_remind.py                        # emit everyone due now
    python3 scripts/cc_remind.py --list
"""

import sys
from datetime import datetime, timedelta, timezone

from cc_common import STATE_DIR, log, load_config, creator_code, read_json, write_json, notify

SUPPORTERS = STATE_DIR / "cc_supporters.json"
OPTOUTS = STATE_DIR / "cc_optouts.json"
CYCLE_DAYS = 14
# Nudge a day early so the reminder lands before the window lapses, not after.
LEAD_DAYS = 1


def _now():
    return datetime.now(timezone.utc)


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def load_all() -> tuple[list, list]:
    return read_json(SUPPORTERS, []) or [], read_json(OPTOUTS, []) or []


def add(handle: str, channel: str):
    supporters, optouts = load_all()
    key = handle.lower()
    if key in optouts:
        log(f"'{handle}' previously opted out — not re-adding. Remove them from "
            f"{OPTOUTS.name} by hand only if they ask to rejoin.")
        return
    for s in supporters:
        if s["handle"].lower() == key:
            s["last_entered"] = _now().isoformat()
            s["reminders_sent"] = 0
            write_json(SUPPORTERS, supporters)
            log(f"'{handle}' already tracked — clock restarted.")
            return
    supporters.append({
        "handle": handle, "channel": channel,
        "added": _now().isoformat(), "last_entered": _now().isoformat(),
        "reminders_sent": 0, "confirmed_reentries": 0,
    })
    write_json(SUPPORTERS, supporters)
    log(f"Added '{handle}' ({channel}). First reminder in {CYCLE_DAYS - LEAD_DAYS} days.")


def remove(handle: str):
    supporters, optouts = load_all()
    key = handle.lower()
    remaining = [s for s in supporters if s["handle"].lower() != key]
    write_json(SUPPORTERS, remaining)
    if key not in optouts:
        optouts.append(key)
        write_json(OPTOUTS, optouts)
    log(f"Removed '{handle}' and recorded a permanent opt-out.")


def confirm(handle: str):
    supporters, _ = load_all()
    key = handle.lower()
    for s in supporters:
        if s["handle"].lower() == key:
            s["last_entered"] = _now().isoformat()
            s["reminders_sent"] = 0
            s["confirmed_reentries"] = s.get("confirmed_reentries", 0) + 1
            write_json(SUPPORTERS, supporters)
            log(f"'{handle}' re-entry #{s['confirmed_reentries']} confirmed — clock restarted.")
            return
    log(f"'{handle}' not tracked. Use --add first.")


def due_now(supporters: list) -> list:
    threshold = _now() - timedelta(days=CYCLE_DAYS - LEAD_DAYS)
    return [s for s in supporters if _parse(s["last_entered"]) <= threshold]


def main():
    args = sys.argv[1:]

    def flag(name):
        return args[args.index(name) + 1] if name in args and len(args) > args.index(name) + 1 else None

    if "--add" in args:
        add(flag("--add"), flag("--channel") or "unknown")
        return
    if "--remove" in args:
        remove(flag("--remove"))
        return
    if "--confirm" in args:
        confirm(flag("--confirm"))
        return

    supporters, optouts = load_all()

    if "--list" in args:
        log(f"{len(supporters)} tracked, {len(optouts)} opted out.")
        for s in supporters:
            age = (_now() - _parse(s["last_entered"])).days
            n = s.get('confirmed_reentries', 0)
            log(f"  {s['handle']:<24} {s['channel']:<10} {age:>3}d since entry, "
                f"{n} re-{'entry' if n == 1 else 'entries'}")
        return

    cfg = load_config()
    code = creator_code(cfg)
    batch = due_now(supporters)

    if not batch:
        log(f"Nobody due. {len(supporters)} supporters tracked.")
        return

    by_channel: dict[str, list] = {}
    for s in batch:
        by_channel.setdefault(s["channel"], []).append(s["handle"])
        s["reminders_sent"] = s.get("reminders_sent", 0) + 1
        s["last_reminded"] = _now().isoformat()
    write_json(SUPPORTERS, supporters)

    message = (
        f"⏰ {len(batch)} supporter(s) due a code re-entry nudge.\n\n"
        + "\n".join(f"  {ch}: {', '.join(h)}" for ch, h in by_channel.items())
        + f"\n\nSuggested copy:\n"
          f"\"Heads up — creator codes expire after 14 days, so {code} has probably "
          f"lapsed on your account. Re-entering takes about five seconds and costs "
          f"you nothing. Thanks for the support 💛\"\n\n"
          f"Confirm re-entries with: python3 scripts/cc_remind.py --confirm <handle>"
    )
    log(message)
    notify(cfg, message)


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    main()
