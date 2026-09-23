# How 3 videos a day get posted, automatically

**Nothing to set up. It runs by itself every day, and posts by itself.**

---

## What happens every day, without you

**Right after the shop resets (7 PM Central now, 6 PM after Nov 1)** — GitHub builds
**three** videos from the new shop, each over a minute long, with real cosmetic art, motion,
music and sound effects. It puts them online as a **release** (that gives each video a
public link Metricool can pull from).

**7:00 AM Central** — the daily Routine schedules all three in Metricool for brand
**7066444** (`usecodebad`), and they **post by themselves** to TikTok, YouTube Shorts and
Facebook:

| Time (Central) | Video | What it is |
|---|---|---|
| 8:00 AM | **Quiz** | One of the six quiz types below |
| 10:00 AM | Shop Recap | Today's shop: the headline items and prices |
| 1:30 PM | A game | Rotates daily: This or That · Guess the Price · Which Costs More · Cop or Drop |
| 3:30 PM | **Quiz** | |
| 5:00 PM | Value / urgency | Rotates daily: Last Chance · Bundle Math · OG Check · New This Week |
| 8:00 PM | **Quiz** | |

All three shop times are **before** the shop resets, so no shop video ever shows items that
are gone. The quizzes aren't about the day's shop, so they can go out in the evening.

If a day's shop can't honestly support a format (say, only 2 items are leaving), that slot
quietly switches to another format. Every word on screen comes from the real shop data.

**You** — nothing. Check the account when you like; to pull a video before it goes out,
delete or edit it in Metricool's planner before its time.

---

## Quiz videos (three more a day)

Added 2026-09-23. **540 are planned, three a day through March 22, 2027**, in
`creator-code/quiz/plan.json`:

- **Guess the Season** — six cosmetics; which season did each come out in?
- **Who's That Skin?** — six silhouettes, four names each
- **Which Came First?** — five pairs; which skin is older?
- **Zoomed In** — six extreme close-ups that pull back
- **Odd One Out** — five rounds of four skins; three share a set
- **Season Throwback** — eight skins from one season, starting at Chapter 1 Season 1

Every answer comes from Epic's own item data (the cosmetics mirror the shop uses), never
from memory. The descriptions never give answers away.

Each quiz promotes the code like the shop videos: the CREATOR CODE BAD sticker on the first
frame, the code badge and #EpicPartner the whole way through, the USE CREATOR CODE BAD
ending, and `💚 Creator Code: BAD · #EpicPartner` in the description. The sounds (drumroll,
ding, clapping, air horn) are made from scratch: real emote audio would draw copyright
strikes.

**How they get out:** every night GitHub builds the day two weeks ahead
(**[Actions → Quiz videos](https://github.com/fwagtx/History-Pulse-/actions/workflows/quiz-videos.yml)**,
one release per day called `quiz-YYYY-MM-DD`), and the 7 AM Routine keeps the next two weeks
scheduled in Metricool. Building only two weeks ahead means a design change still reaches the
upcoming videos. To go past March 2027, ask Claude to extend the plan.

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
- On Facebook, each video goes out as a **Reel** (a normal video post if one is ever over
  90 seconds, Facebook's Reel limit)
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
| A video went to TikTok and YouTube but not Facebook | Facebook refused it, or the Page came unlinked in Metricool. The Routine posts to the other two anyway and names the error; if it says the Page is disconnected, reconnect it in Metricool |
