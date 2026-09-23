# How the daily video reaches Metricool, automatically

**You do one thing, once. After that it runs by itself.**

---

## Setup: none

The shop data now comes from a public GitHub mirror that needs **no API key and no
Discord sign-up**. There is nothing to configure.

*(Optional: if you ever do get a fortnite-api.com key, add it as a repo secret named
`FORTNITE_API_KEY` and it'll be used as a backup source. Not needed.)*

---

## What happens every day, without you

**00:20 UTC** — GitHub Actions wakes up (free, unlimited on public repos), fetches the day's
shop, downloads every cosmetic's real artwork, renders the slides, builds the ~61-second video,
and publishes it as a **release**.

That last part is the trick: a GitHub release gives the video a **public URL**, which is exactly
what Metricool needs to pull it in. No Google Drive, no uploading, no your-Mac-being-on.

The URL is predictable:
```
https://github.com/fwagtx/History-Pulse-/releases/download/shop-YYYY-MM-DD/bad-shop-YYYY-MM-DD.mp4
```

**07:00 Central** — the daily routine fires, writes that day's script, and schedules the shop
video into Metricool against brand **7066444** (`usecodebad`).

**You** — film your gameplay video whenever you like. The shop video covers the days you don't.

---

## Test it right now, without waiting

1. Go to **[Actions → Daily shop video](https://github.com/fwagtx/History-Pulse-/actions/workflows/daily-shop-video.yml)**
2. Click **Run workflow** → pick the `claude/creator-code-bad-automation-0jjc1k` branch → **Run**
3. Wait ~3 minutes
4. Check **[Releases](https://github.com/fwagtx/History-Pulse-/releases)** — the video will be there

If it fails, open the run and read the red step. Send me what it says and I'll fix it.

---

## Draft or live?

Scheduled posts can be created as **drafts** (they sit in Metricool and publish nothing) or
**live** (they go out automatically at the scheduled time).

**Start with drafts.** Watch a few, confirm they look right, then switch to live. Once it's live
it is posting to a public account with no human in the loop, so it's worth earning that trust
first.

---

## If something breaks

| Symptom | Cause |
|---|---|
| Action fails at "Write config" | The `FORTNITE_API_KEY` secret isn't set |
| Action fails at "Build" | Shop API changed or key expired — send me the log |
| No release appears | The build step failed earlier in the run |
| Metricool post has no video | The release didn't exist when it was scheduled |
