# Creator Code BAD — Setup & Cron

Standard library Python only, so there is nothing to install. You need Python 3.10+ and
(optionally) Chromium for PNG rendering.

## One-time setup

1. **Get a free Fortnite API key** — https://dash.fortnite-api.com/ (free, no credit card).

2. **Create your config:**
   ```bash
   cp creator-code/config.example.json creator-code/config.json
   ```
   Fill in `fortnite_api_key`. Reuse the History Pulse Telegram bot token/chat ID, or make a
   second bot via @BotFather so the two pipelines don't share a thread.
   `creator-code/config.json` is gitignored — your keys never get committed.

3. **Install Chromium** (optional, free — only needed for automatic PNG export):
   ```bash
   sudo apt install chromium          # Debian/Ubuntu
   brew install --cask chromium       # macOS
   ```
   Without it you still get `card.html`, which you can screenshot by hand.

4. **Verify it works with no network and no key:**
   ```bash
   python3 scripts/cc_daily.py --fixture --png
   ```
   That runs the whole chain against the bundled sample shop. Check
   `creator-code/out/<today>/` for `card.html`, `card.png`, `captions.json` and
   `publish_queue.json`.

5. **Then try it live:**
   ```bash
   python3 scripts/cc_daily.py --png
   ```

## Cron

The Fortnite shop rotates at **00:00 UTC**. Run shortly after so you're early on the day's
search traffic — being first matters for a query people search once per day.

```cron
# Item shop package, 00:10 UTC daily
10 0 * * * cd /path/to/History-Pulse- && /usr/bin/python3 scripts/cc_daily.py --png >> logs/cc_daily.log 2>&1

# Re-entry reminders, 17:00 UTC daily (evening = better open rates)
0 17 * * * cd /path/to/History-Pulse- && /usr/bin/python3 scripts/cc_remind.py >> logs/cc_remind.log 2>&1
```

Cron needs the machine powered on — same caveat as the History Pulse pipeline. If you don't
have an always-on box, a **GitHub Actions scheduled workflow** covers it on the free tier
(store the API key as a repo secret; note Actions' schedule can run several minutes late).

## Daily manual step (until Phase 3)

`cc_daily.py` stops at "assets ready" on purpose — it never publishes. Each morning:

1. Open `creator-code/out/<today>/publish_queue.json`.
2. Turn `card.png` into a 20–40s Short (CapCut/DaVinci/Shotcut, all free) — a slow zoom over
   the card with music is enough, and consistency beats production value here.
3. Copy captions from `captions.json` and upload.

Automating step 3 for YouTube is Phase 3 in `PLAN.md`, and it's the highest-value thing to
build next: `videos.insert` now costs 1 unit/call with a 100/day cap (changed June 2026), so
daily auto-upload fits inside the free quota with enormous room to spare.

## Reminder commands

```bash
python3 scripts/cc_remind.py --add <handle> --channel discord   # they told you they entered
python3 scripts/cc_remind.py --confirm <handle>                 # they re-entered; reset clock
python3 scripts/cc_remind.py --remove <handle>                  # permanent opt-out
python3 scripts/cc_remind.py --list                             # who's tracked
python3 scripts/cc_remind.py                                    # notify everyone due
```

Opt-in only, and `--remove` is permanent: a removed handle is refused by `--add`. Keep it that
way — unsolicited reminders are spam under Epic's terms, and the code is the asset.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `config.json not found` | Step 2 above |
| `shop fetch failed` | Check the key at dash.fortnite-api.com; free tier has rate limits |
| `normalized shop is empty` | Upstream changed shape — `cc_shop.py::normalize` handles both known shapes; add the new one there |
| No `card.png` | Chromium missing — HTML still written |
| No Telegram message | Token/chat ID blank in config; the pipeline logs and continues by design |
