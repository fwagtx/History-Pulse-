# History Pulse — Claude Code Project

## Setup (one-time)

1. Unzip this into a folder on your machine, e.g. `~/history-pulse/`.
2. Open a terminal in that folder and run `claude` to start Claude Code there. (Requires
   Claude Code installed — see https://claude.com/product/claude-code — the CLI itself is
   free to install; usage runs on your existing Claude plan.)
3. Claude Code will automatically read `CLAUDE.md` in this folder every session — that's
   where all the rules, constraints, and free-tool stack live. You don't need to paste
   anything in manually.

## Day-to-day use

Run the slash commands in order for each new video:

```
/research World War I origins
/script july-crisis-1914
/seo july-crisis-1914
/thumbnail july-crisis-1914
/review july-crisis-1914       <- Claude will ask for your explicit approval here
/finalize july-crisis-1914     <- only after you approve, gives you a copy-paste checklist
```

Replace `july-crisis-1914` with whatever slug Claude suggests or you choose — keep it
consistent across all steps for one video.

## Optional: fully automated mode (Telegram approvals)

Instead of running slash commands yourself, you can let cron run the pipeline nightly and
approve videos remotely from Telegram. See `CRON_SETUP.md` for the full walkthrough. Short
version:

1. Create a free Telegram bot via @BotFather, get your chat ID (steps in
   `scripts/telegram_utils.py`).
2. Copy `config.example.json` to `config.json` and fill in your bot token, chat ID, and topics
   in `queue.txt`.
3. Set up two cron jobs: one runs `scripts/run_pipeline.py` (e.g. nightly) to research/script/
   SEO/thumbnail the next queued topic and message you on Telegram; the other runs
   `scripts/check_telegram.py` every 5–10 minutes to catch your `approve <slug>` or
   `revise <slug> <notes>` replies.
4. Approval still only unlocks the finalize/checklist step — actual YouTube upload stays
   entirely manual, same as interactive mode.

This needs a machine that's actually powered on at the scheduled times (your computer, or a
spare always-on box) — it's free of subscription costs, but not free of "something has to be
running."

## What's automated vs. what stays manual

**Automated by Claude Code:** research, fact-checking, scriptwriting, SEO metadata,
thumbnail concepts/mockups, and organizing everything into the `content/` folder.

**Stays manual (by design, and because it's the free-tier path):** actually recording/
generating voiceover, editing the video in CapCut/DaVinci Resolve/Shotcut, building the real
thumbnail image in Canva/Photopea/GIMP, and uploading/scheduling in YouTube Studio. None of
this requires a monthly fee, but none of it is something Claude Code does for you — YouTube
upload access is never granted to the agent, on purpose.

## Folder guide

- `content/01_research/<slug>/` — research notes + sources
- `content/02_scripts/<slug>/` — narration script
- `content/03_seo/<slug>/` — titles, description, tags
- `content/04_thumbnails/<slug>/` — thumbnail concepts + mockup
- `content/05_approved/<slug>/` — only populated after you explicitly approve in `/review`
- `content/06_published/<slug>/` — only populated after you confirm a video is actually live
