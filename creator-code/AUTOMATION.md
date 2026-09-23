# How 3 videos a day get posted, automatically

**Nothing to set up. It runs by itself every day, and posts by itself.**

---

## What happens every day, without you

**Right after the shop resets (7 PM Central now, 6 PM after Nov 1)** — GitHub builds
**three** videos from the new shop, each over a minute long, with real cosmetic art, motion,
music and sound effects. It puts them online as a **release** (that gives each video a
public link Metricool can pull from).

**7:00 AM Central** — the daily Routine schedules all three in Metricool for brand
**7066444** (`usecodebad`), and they **post by themselves** to TikTok and YouTube Shorts:

| Time (Central) | Video | What it is |
|---|---|---|
| 10:00 AM | Shop Recap | Today's shop: the headline items and prices |
| 1:30 PM | A game | Rotates daily: This or That · Guess the Price · Which Costs More · Cop or Drop |
| 5:00 PM | Value / urgency | Rotates daily: Last Chance · Bundle Math · OG Check · New This Week |

All three times are **before** the shop resets, so no video ever shows items that are gone.

If a day's shop can't honestly support a format (say, only 2 items are leaving), that slot
quietly switches to another format. Every word on screen comes from the real shop data.

**You** — nothing. Check the account when you like; to pull a video before it goes out,
delete or edit it in Metricool's planner before its time.

---

## Every post includes

- **A thumbnail on the first frame**: title, the full date, the video's own items, the
  format's sticker and a big **CREATOR CODE BAD**. TikTok uses a video's first frame as its
  cover when none is picked, so this is what shows on the profile grid.
- **The full date with the year** ("September 23, 2026") in the titles, the description
  and on screen
- **A clean description**, same layout every time:

  ```
  ⚔️ THIS OR THAT — Fortnite Item Shop, September 23, 2026
  5 rounds, every item from today's shop. Pick A or B 👇

  1️⃣ ISuperSpeed 🆚 Aeronaut
  2️⃣ PAC-MAN's Gloves 🆚 Bow of the Vanquisher
  …

  💬 Comment your picks in order, like ABBAB

  💚 Creator Code: BAD · #EpicPartner

  #usecodebad #creatorcodebad #codebad #fortnite …
  ```

  Games never list prices in the description (they're the answers). If a description
  ever runs long, list lines drop from the end — the disclosure and hashtags never do.
- `#usecodebad #creatorcodebad #codebad` first in the hashtags, every time
- `#EpicPartner` on screen and in every description (the owner dropped the longer
  "I get a commission…" sentence on 2026-09-23)
- TikTok's **branded content** switch on (the rules require it for a creator code)
- Never the word "discount" — the code isn't one

---

## Test it right now

1. **[Actions → Daily shop video](https://github.com/fwagtx/History-Pulse-/actions/workflows/daily-shop-video.yml)** → **Run workflow** → **Run**
2. Wait ~25 minutes
3. **[Releases](https://github.com/fwagtx/History-Pulse-/releases)** — three videos, their covers,
   a quick-look sheet per video (`-qa.jpg`) and `manifest.json` (times + captions)

---

## Draft or live?

**Live.** On 2026-09-23 the owner asked for posts to go out automatically, with no
approval step. Because nobody looks at a video before it's public, the Routine only
schedules a video when all of these hold, and skips it otherwise:

- the manifest exists and is for **today's** shop
- the video link works, it's at least 60 seconds long, and its caption carries
  `#EpicPartner` and `#usecodebad`
- its time hasn't passed, and it posts before the shop resets
- it isn't already scheduled (checked by title)

Each morning it also reports any of yesterday's posts that didn't go out. To go back to
drafts, say so and the Routine's `draft` setting flips back to `true`.

---

## If something breaks

| Symptom | What it means |
|---|---|
| Build step says "Shop source still shows …" | The shop mirror hadn't updated yet. It waits 50 min before giving up, on purpose, so it never posts yesterday's shop. Re-run it. |
| Fewer than 3 videos | Some formats couldn't be made honestly from that day's shop. Normal on thin days. |
| No release appears | The build failed — open the run, read the red step, send it to me |
| Nothing scheduled in Metricool | The release didn't exist at 7 AM; the Routine skips rather than guessing |
| A post shows an error in Metricool | TikTok or YouTube refused it; the next morning's Routine summary names it |
