# Setting up unattended runs (cron)

This assumes macOS/Linux. Needs a machine that's actually on at the scheduled times —
your main computer left running, or a spare always-on box. No cloud subscription required,
but if you later move this to a cloud VM, check whether that VM is actually free long-term;
most "free tier" cloud servers are free for a limited time or with usage caps, not forever.

## 1. One-time setup

```bash
cd /path/to/history-pulse-claude-code
cp config.example.json config.json
```

Edit `config.json` and fill in:
- `telegram_bot_token` — from @BotFather (see scripts/telegram_utils.py header for steps)
- `telegram_chat_id` — run:
  ```bash
  python3 scripts/telegram_utils.py --find-chat-id <YOUR_BOT_TOKEN>
  ```
  (after messaging your bot at least once so it has a chat to find)

Add a few topics to `queue.txt`, one per line.

Confirm `claude` is on your PATH and logged in:
```bash
claude auth status
```

## 2. Add the cron jobs

Run `crontab -e` and add:

```cron
# Nightly: research -> script -> seo -> thumbnail for the next queued topic, then notify Telegram
0 2 * * * cd /path/to/history-pulse-claude-code && /usr/bin/python3 scripts/run_pipeline.py >> logs/pipeline.log 2>&1

# Every 10 minutes: check Telegram for approve/revise replies
*/10 * * * * cd /path/to/history-pulse-claude-code && /usr/bin/python3 scripts/check_telegram.py >> logs/telegram.log 2>&1
```

Adjust the schedule to however often you actually want new videos queued — nightly is a
starting point, not a requirement. Running the pipeline less often (e.g. twice a week) is
just as valid and cheaper on your Claude usage.

## 3. Test it manually first

Before trusting cron, run both scripts by hand once to make sure they work and you get a
Telegram message:

```bash
python3 scripts/run_pipeline.py
python3 scripts/check_telegram.py
```

## 4. A note on cost

This setup has no monthly subscription fees for Telegram or cron. It does use your existing
Claude usage/plan for every headless `claude -p` call — running the pipeline nightly means
4 headless calls per video, every video. If you're on a metered API key rather than a Claude
subscription, keep an eye on usage; consider a lighter schedule (e.g. 2–3x/week) if that
matters to you.
