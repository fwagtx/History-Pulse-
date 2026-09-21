# Getting videos onto your phone, ready to post

**Short version:** we generate finished MP4s into a cloud-synced folder, they appear on your
phone, you open TikTok and post. No API, no approval, working today.

## Why not the TikTok API

I told you last turn that the `video.upload` (inbox) scope needed no audit. **That was wrong,
and it matters** — multiple sources agree the private-only restriction applies to the inbox
upload flow too, not just Direct Post. Until your app passes TikTok's audit:

- every video is forced to **private view only**, whichever scope you use
- accounts posting through an unaudited client **must themselves be set to private**

So a fully-built integration would push invisible videos to a private account. On top of that,
registering the app requires **verified ownership of a domain** (hosting a signature file), a
Privacy Policy URL and a Terms of Service URL, plus a demo video — then a 1–4 week audit.

That's weeks of work and a domain purchase to save about a minute a day for one account. Not
worth it now. If you're posting 50+/day across accounts later, revisit it.

Also worth flagging: API uploads land in your **Inbox as a notification**, not in Saved Drafts.
They're different places. The folder-sync approach below actually gets you closer to what you
asked for, because you can save to Drafts yourself in the app.

---

## Setup (about 10 minutes, once)

### 1. Install ffmpeg (free)

```bash
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Ubuntu/Debian
```
Windows: download from ffmpeg.org, unzip, and put the path in `ffmpeg_path` below.

Install a **standard** build, not a minimal one — the script checks on startup and tells you
exactly what's missing if the build is stripped down.

### 2. Make a synced folder

Create a folder in Google Drive, Dropbox or iCloud — whichever you already have on your phone:

```
Google Drive/BAD-drafts/
```

Install that app on your phone if it isn't already. This is what replaces the API.

### 3. Configure

```bash
cp creator-code/config.example.json creator-code/config.json
```

Fill in:
- `fortnite_api_key` — free, no card, from https://dash.fortnite-api.com/
- `video_out_dir` — full path to the synced folder, e.g. `/Users/you/Google Drive/BAD-drafts`
- `ffmpeg_path` — leave empty unless it isn't auto-detected

`config.json` is gitignored, so nothing you paste there gets committed.

### 4. Test it without a key or network

```bash
python3 scripts/cc_daily.py --fixture --png
python3 scripts/cc_video.py
```

You should get `bad-shop-<date>.mp4` in your synced folder. Check it looks right on your phone.

### 5. Go live

```bash
python3 scripts/cc_daily.py --png    # real shop data
python3 scripts/cc_video.py
```

---

## Daily use

**Shop video (2–3x/week):**
```bash
python3 scripts/cc_daily.py --png && python3 scripts/cc_video.py
```

**Gameplay video (5–7x/week) — record your clip, then:**
```bash
python3 scripts/cc_video.py --clip ~/clips/my-clip.mp4
```
Normalizes it to 1080×1920 and appends the branded BAD end card.

**Then on your phone:** open the synced folder → save the video to your camera roll → TikTok →
upload → paste the caption from `captions.json` → post, or save to Drafts.

About 60 seconds. That's the whole thing the API would have saved you.

## Automate the shop half

Once it's working, cron the generation so videos are waiting each morning:

```cron
15 0 * * * cd /path/to/History-Pulse- && python3 scripts/cc_daily.py --png && python3 scripts/cc_video.py >> logs/cc.log 2>&1
```

## One honest expectation

This automates the **shop** videos — the 2–3 per week. Your 5–7 weekly **gameplay** videos still
need you to play, clip and post; `--clip` only handles the formatting and end card. Given
gameplay is the growth engine (see `PLAN.md`), most of the actual work stays manual by nature.
The automation removes the boring half, not the whole job.
