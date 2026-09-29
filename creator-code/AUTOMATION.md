# How the videos get posted, automatically

**Nothing to set up. It runs by itself every day, and posts by itself, for years.**

From **October 1, 2026**: **5 short videos every day** (TikTok, YouTube Shorts, Facebook Reels,
Instagram Reels) and, from **September 30, 2026**, **1 long video every weekday** on YouTube — all
in the edit style picked on 2026-09-28: real music cut to the beat, big app-style
captions, a camera that moves with the music, each cosmetic on its tile over a blurred
copy of itself, and **USE CODE: BAD** on screen the whole time.

---

## Every day: 5 short videos

**Right after the shop resets (7 PM Central now, 6 PM after Nov 1)** GitHub builds the
day's five from fresh data and puts them online as a release (`shop-YYYY-MM-DD`).
**7:00 AM Central** the daily Routine schedules them in Metricool for brand **7066444**
(`usecodebad`), and they **post by themselves**:

| Time (Central) | What it is |
|---|---|
| 8:00 AM | **Quiz** — Who's That Skin?, Zoomed In, Which Came First?, Guess the Season or a Season Throwback, from the quiz plan. **Every day in October: the Fortnitemares edition; in December: Winterfest** |
| 11:00 AM | **Today's shop** — Shop Recap (or OG Check / Last Chance on a thin day) |
| 1:00 PM | **On This Day** — the Item Shop on today's date, a year per beat, every year since 2018 |
| 4:00 PM | **A game on today's shop**, rotating: Back After · OG Check · Guess the Price · Last Chance · This or That |
| 7:00 PM | **From the shop's history**, rotating: Higher or Lower · Most Common · Rarest · Gone the Longest (skins, pickaxes, emotes, back blings, gliders) |

Both shop videos post before the shop resets, so none ever shows items that are gone. The
7 PM video isn't about the day's shop.

**Quality gate — a video is only published when all of these hold** (otherwise that slot
tries its next format, and if none passes it stays empty rather than posting something
worse):

- every frame keeps its text, cosmetics and the code clear of the apps' buttons,
  captions and headers (checked automatically, 4 times a second, on the real video)
- 62–90 seconds long (TikTok's one-minute bar, Facebook's 90-second Reel limit)
- it has its music, its words are postable (titles, hashtags, disclosure)
- every fact comes from Epic's item data or the Item Shop's own records

If the whole five-video build ever fails (say the emoji font can't be installed), that
day falls back to three classic shop videos instead of posting nothing.

## Weekdays: 1 long video on YouTube (3:00 PM Central)

About 8–10 minutes, 16:9, narrated by a free open-source voice (Kokoro), with subtitles,
YouTube chapters, a custom thumbnail, a new public-domain music track about every minute,
a "use code BAD" moment before the top ten and the code-entry card at the end.

| Day | Series |
|---|---|
| Monday | **This Week in the Item Shop** — last week's biggest comebacks |
| Tuesday | **The 30 …** — a countdown that rotates weekly: gone the longest · the rarest · the most common, for skins, pickaxes, emotes, back blings, gliders |
| Wednesday | **<Season>: where are they now?** — one season's shop skins, down to the rarest |
| Thursday | **The Item Shop in <this month, an earlier year>** — every skin new that month, then and now |
| Friday | **The rarest <Icon Series / Marvel / DC / Star Wars / Gaming Legends / a big set> skins** |

Built every night by GitHub (inside the quiz job, from that morning's shop records), put
in that night's `quiz-…` release, and scheduled for 3 PM by the same 7 AM Routine —
YouTube only. The same quality gate applies, with YouTube's frame: nothing under the
player's controls or title bar, 3–14.5 minutes, title/description/tags within YouTube's
limits, valid chapters, thumbnail under 2 MB. A topic that can't pass falls back to
another one.

**One thing only you can do:** verify the YouTube channel with a phone number
(YouTube Studio → Settings → Channel → Feature eligibility, or youtube.com/verify). Until
then YouTube ignores custom thumbnails (the video still posts, with a frame YouTube picks).

## Why it never runs out

- The quizzes, On This Day and the seasonal series come from a plan
  (`creator-code/quiz/plan.json`) that **extends itself** 180 days at a time before it
  runs out.
- Everything else is computed from each day's shop and the Item Shop's records, which grow
  every day, so the rotations keep producing new numbers.
- The music is a library of 102 public-domain (CC0) tracks by human producers, rotated so
  consecutive videos don't repeat; Halloween tracks only in October, Christmas ones only
  in December.

## Before the switch (until September 30)

Three shop videos a day from the nightly shop build, plus the quiz releases' quizzes, On
This Day and the seasonal videos (built two weeks ahead). Quiz posts were already queued
in Metricool through October 11 when the switch was made. From October 1, each morning
the Routine first schedules the day's five new videos and **then** sets that day's old
queued quiz posts to **draft**, so no day gets more than five — and if the new videos
ever fail to build, the old ones still go out and the day is never empty.

---

## Every post includes

- **A cover on the first frame**: the title, the video's own items and **USE CODE: BAD**.
  TikTok uses a video's first frame as its cover when none is picked, so this is what
  shows on the profile grid. (Long videos get their own 1280x720 thumbnail.)
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
- On Instagram, each video goes out as a **Reel** in its own post, because Instagram allows
  only **5 hashtags** (since December 2025) and #EpicPartner is one of them: the same
  description, with the hashtags cut to `#EpicPartner #usecodebad #creatorcodebad #codebad
  #fortnite`. So in Metricool's planner every video shows twice at the same time, and
  that's intended: don't tick Instagram on the main post, or Instagram gets it twice
- Never the word "discount" — the code isn't one
- No "Made with AI" labels: TikTok's AI-generated flag, YouTube's "altered or synthetic
  content" flag and Instagram's "AI info" flag are all off on every post (checked on
  2026-09-29 across the whole queue), no caption mentions AI, and the files carry no AI
  metadata the apps could read. None of it is needed: the art is Epic's, the facts are the
  shop's records, and the long videos' narrator is a generic voice, not anyone real's

---

## Test it right now

1. **[Actions → Daily shop video](https://github.com/fwagtx/History-Pulse-/actions/workflows/daily-shop-video.yml)** → **Run workflow** → **Run**
2. Wait ~30 minutes
3. **[Releases](https://github.com/fwagtx/History-Pulse-/releases)** — the day's videos, their covers,
   a quick-look sheet per video (`-qa.jpg`) and `manifest.json` (times + captions)

To see a long video without posting it: **[Actions → Quiz videos](https://github.com/fwagtx/History-Pulse-/actions/workflows/quiz-videos.yml)**
→ **Run workflow** → sample `long_series` (and a weekday date) → it lands in a `samples-…`
release that nothing schedules.

---

## Draft or live?

**Live.** On 2026-09-23 the owner asked for posts to go out automatically, with no
approval step. Because nobody looks at a video before it's public, the Routine only
schedules a video when all of these hold, and skips it otherwise:

- the manifest exists and is for **today's** shop
- the video link works, it's at least 60 seconds long, and its caption carries
  `#EpicPartner` and `#usecodebad`
- its time hasn't passed, and a video about the shop posts before the shop resets
- it isn't already scheduled (checked by title)
- a long video: its link and thumbnail work, it's 3–14.5 minutes, its YouTube title is
  within 100 characters and its description carries `#EpicPartner` and `#usecodebad`;
  it goes to YouTube only

Each morning it also reports any of yesterday's posts that didn't go out. To go back to
drafts, say so and the Routine's `draft` setting flips back to `true`.

---

## If something breaks

| Symptom | What it means |
|---|---|
| The Cosmetics data run fails | Nothing stops: every video already planned still builds. Only extending the plan needs it; it retries next Monday |
| Build step says "Shop source still shows …" | Neither shop source had the new day yet. Each run waits 50 min before giving up, on purpose, so it never posts yesterday's shop, and GitHub tries again four more times through the night (last try about 4 AM Central). Nothing to do unless every try fails. |
| Fewer than 5 videos | A slot had no format that passed the quality gate that day (rare: each slot has several fallbacks). |
| Only 3 videos, in the old look | The five-video build failed as a whole that night, so it fell back to the classic three. The run's log names why |
| No long video on a weekday | Its build didn't pass the gate or the nightly quiz job failed. Open **Actions → Quiz videos** for that night; the Routine's summary says which day is missing |
| No release appears | The build failed — open the run, read the red step, send it to me |
| Nothing scheduled in Metricool | The release didn't exist at 7 AM; the Routine skips rather than guessing |
| A post shows an error in Metricool | TikTok or YouTube refused it; the next morning's Routine summary names it |
| A video went to TikTok and YouTube but not Facebook | Facebook refused it, or the Page came unlinked in Metricool. The Routine posts to the other two anyway and names the error; if it says the Page is disconnected, reconnect it in Metricool |
