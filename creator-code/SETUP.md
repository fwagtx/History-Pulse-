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

---

## Mac setup (start here if you're on a Mac)

Everything in this pipeline runs fine on macOS. You only need to do this once.

### 1. Open Terminal
`Cmd + Space`, type `Terminal`, press Enter.

### 2. Get the developer tools (gives you git and python3)
```bash
xcode-select --install
```
A dialog pops up — click Install, wait a few minutes. If it says they're already
installed, you're fine.

Check it worked:
```bash
python3 --version
```
You want 3.10 or higher.

### 3. Install Homebrew (free package manager), then ffmpeg
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install ffmpeg
```
Homebrew prints a couple of extra commands at the end about your PATH — copy and run
those, it tells you exactly what to paste.

Check it worked:
```bash
ffmpeg -version
```

### 4. Get this repo onto your Mac
```bash
cd ~/Documents
git clone https://github.com/fwagtx/History-Pulse-.git
cd History-Pulse-
git checkout claude/creator-code-bad-automation-0jjc1k
```

### 5. Configure
```bash
cp creator-code/config.example.json creator-code/config.json
open -e creator-code/config.json
```
That opens it in TextEdit. Fill in:
- `fortnite_api_key` — free, no card, from https://dash.fortnite-api.com/
- `video_out_dir` — e.g. `/Users/YOURNAME/Library/CloudStorage/GoogleDrive-you@gmail.com/My Drive/BAD-drafts`
  (or any iCloud/Dropbox folder — easiest is to make the folder first, then drag it into
  Terminal to get its exact path)

Save and close.

### 6. Test it — no API key or internet needed
```bash
python3 scripts/cc_daily.py --fixture --png
python3 scripts/cc_video.py
```

You should get an MP4 in your synced folder. **Actually watch it** — this is the first
time the encoder has run anywhere, so if something's wrong this is where we find out.
If ffmpeg throws an error, copy the whole thing and send it to me.

### 7. Go live
```bash
python3 scripts/cc_daily.py --png
python3 scripts/cc_video.py
```

### Posting from here
Either post from the Mac (tiktok.com in a browser handles uploads fine), or let the
folder sync to your phone and post from the app. Phone is usually less friction.

### What does NOT work on a Mac
**UEFN.** Fortnite hasn't been supported on macOS since the 2020 Epic/Apple dispute, so
there is no Mac version of the editor to install. Writing Verse and moving it to your Mac
doesn't help, because there's nothing on the Mac to open it with. See `uefn/CHECK_SPECS.md`.
