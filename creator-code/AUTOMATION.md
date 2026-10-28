# How the videos get posted, automatically

**Nothing to set up. It runs by itself every day, and posts by itself, for years.**

From **October 1, 2026**: **5 short videos every day** (TikTok, YouTube Shorts, Facebook
Reels, Instagram Reels, and the two shop videos on **Threads** too) and, from **September
30, 2026**, **1 long video every weekday** on YouTube — all in the edit style picked on
2026-09-28: real music cut to the beat, big app-style captions, a camera that moves with the
music, each cosmetic on its tile over a blurred copy of itself, and **USE CODE: BAD** on
screen the whole time.

---

## Every day: 5 short videos

**Right after the shop resets (7 PM Central now, 6 PM after Nov 1)** the nightly build
makes the next day's five from fresh data and puts them online in the video bucket (folder
`shop-YYYY-MM-DD`).
**The same evening, about two hours after the reset (9:10 PM Central now, 8:10 PM after
Nov 1)**, the posting job schedules them in Metricool for brand **7066444** (`usecodebad`),
so the whole next day is queued the night before. At **6:53 AM Central** it runs again as a
backup and adds anything the evening run missed. They **post by themselves**:

| Time (Central) | What it is |
|---|---|
| 8:00 AM | **Quiz** — Who's That Skin?, Zoomed In, Which Came First?, Guess the Season or a Season Throwback, from the quiz plan. **Every day in October: the Fortnitemares edition; in December: Winterfest** |
| 11:00 AM | **Today's shop** — Shop Recap (or OG Check / Last Chance on a thin day). *Also on Threads* |
| 1:00 PM | **On This Day** — the Item Shop on today's date, a year per beat, every year since 2018 |
| 4:00 PM | **A game on today's shop**, rotating: Back After · OG Check · Guess the Price · Last Chance · This or That. *Also on Threads* |
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

Built every night by the nightly build (with the quiz day two weeks out, from that
morning's shop records), put in that night's `quiz-…` folder, and scheduled for 3 PM by
the same posting job, the evening before —
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

Three shop videos a day from the nightly shop build, plus the quiz folders' quizzes, On
This Day and the seasonal videos (built two weeks ahead). Threads started on September 29
with the day's shop game and Last Chance; on September 30 it gets the 10 AM shop video and
the 1:30 PM game. Quiz posts were already queued in Metricool through October 11 when the
switch was made. From October 1, each morning the Routine first schedules the day's five new
videos and **then** sets that day's old queued quiz posts to **draft**, so no day gets more
than five — and if the new videos ever fail to build, the old ones still go out and the day
is never empty. The old posts are listed by their Metricool ids in
`creator-code/published/old-quiz-posts.json` (their folders never made it into the new
bucket), so the Routine retires exactly those and never mistakes one for a new video with
the same title.

---

## Every post includes

- **A cover on the first frame**: the title, the video's own items and **USE CODE: BAD**.
  TikTok uses a video's first frame as its cover when none is picked, so this is what
  shows on the profile grid. (Long videos get their own 1280x720 thumbnail.)
- **The date** in the titles, the description and on screen
- **A spoken hook in the first second** (since 2026-10-28; the owner: the first three
  seconds decide whether people stay). The shop video opens with "This is today's Item
  Shop for October 29th!", the others with their cover's line ("Higher or lower?…"), in
  the long videos' free voice (cc_voice), the music dipping under it. A build that can't
  make the voice posts the video without it.
- **A description written the way a person posts** (rewritten 2026-10-28: no legal
  paragraph, no music credit, no headings in capitals):

  ```
  This or that, Item Shop edition ⚔️
  5 rounds, all from today's shop (September 23). A or B?

  1️⃣ ISuperSpeed vs Aeronaut
  2️⃣ PAC-MAN's Gloves vs Bow of the Vanquisher
  …

  Drop your picks in order, like ABBAB 👇

  Use code BAD in the Item Shop 💚 #EpicPartner

  #usecodebad #creatorcodebad #codebad #fortnite …
  ```

  The line before the hashtags sells the code and carries the disclosure; it changes from
  post to post (`cc_formats.CODE_LINES`: "Shopping today? Use code BAD 💚", "Support-A-Creator
  resets every 14 days, so pop BAD back in 💚", …). Epic's fan-content notice is the small
  print on every video's end card instead.

  Games never list prices in the description (they're the answers). If a description
  ever runs long, list lines drop from the end — the disclosure and hashtags never do.
- `#usecodebad #creatorcodebad #codebad` first in the hashtags, every time
- `#EpicPartner` on screen and in every description (the owner dropped the longer
  "I get a commission…" sentence on 2026-09-23)
- TikTok's **branded content** switch on (the rules require it for a creator code)
- On Facebook, each video goes out as a **Reel** (a normal video post if one is ever over
  90 seconds, Facebook's Reel limit)
- **Each network is its own post, at its own best time** (since 2026-10-28): Metricool's
  best-time-to-post scores for the brand (creator-code/post_times.json) give each network
  its five best hours of the day, two hours apart, and the day's videos take them in order
  of importance (the shop video first, by noon; the shop game before the shop rotates).
  `python3 scripts/cc_post_times.py 2026-11-02` prints a day's times
- On Instagram, each video goes out as a **Reel**, with the hashtags cut to `#EpicPartner
  #usecodebad #creatorcodebad #codebad #fortnite` because Instagram allows only **5
  hashtags** (since December 2025) and #EpicPartner is one of them
- On **Threads** (added 2026-09-29), the two videos about today's shop go out in their own
  posts too, with a shorter copy because Threads allows only **500 characters**: the title
  lines, the first items of the list, the question, `#fortnite #usecodebad #creatorcodebad
  #codebad` (Threads makes the first hashtag, #fortnite, the post's topic), then the post's
  code line with #EpicPartner. Quizzes, On This Day, the history videos and the long videos
  don't go to Threads
- **Built ahead**: each day's quiz and On This Day don't need that day's shop, so the
  nightly build makes them up to a week early (`cc_nightly.py ahead`, two days a run,
  into `shop-ahead-YYYY-MM-DD`) and the posting job schedules them as soon as they're
  built (step 3g); that day's own build then skips them. A day with nothing planned for a
  slot is left to its own night, whose fallbacks use that day's data
- Never the word "discount" — the code isn't one
- No "Made with AI" labels: TikTok's AI-generated flag, YouTube's "altered or synthetic
  content" flag and Instagram's "AI info" flag are all off on every post (checked on
  2026-09-29 across the whole queue), no caption mentions AI, and the files carry no AI
  metadata the apps could read. None of it is needed: the art is Epic's, the facts are the
  shop's records, and the long videos' narrator is a generic voice, not anyone real's

---

## Where it runs (since September 30, 2026)

GitHub no longer builds or hosts anything: its Actions and releases stopped working for
this account on September 29. Three pieces do the job now, all free:

| Piece | What it does | Where |
|---|---|---|
| **Video bucket** | Holds every video, cover and list. When a post is scheduled, Metricool copies its video through a signed link to that one file (the posting job gets a day's links with one command, `python3 scripts/cc_store.py links FOLDER`), valid for 6 hours: since October 1 it often can't fetch from the public link, which Cloudflare rate-limits | Cloudflare R2 (free tier): bucket `usecodebad-media`, public link `https://pub-3f1b6462fa8a4a69aeb545c6ece93d92.r2.dev` (for looking at things). Keeps each day's folder for 7 days (see below) |
| **Nightly build** | Makes the day's shorts and long video and uploads them, at 00:22, 03:22 and 06:22 UTC, right after the shop resets (7:22 PM, 10:22 PM and 1:22 AM Central; an hour earlier after November 1). Each run finishes what an earlier one couldn't | The Claude Code session *usecodebad · nightly build (automatic, keep)*, woken by the Routine *Nightly @usecodebad video build* |
| **Posting** | Writes the day's filming script and schedules what the nightly build made, in Metricool: the evening before at 02:10 UTC (9:10 PM Central; 8:10 PM after November 1), and again at 6:53 AM Central as a backup that adds only what's missing | The Claude Code session *usecodebad · daily posting (automatic, keep)*, woken by the Routines *usecodebad · evening posting (queues the next day)* and *usecodebad · morning posting backup (6:53 AM Central)* (since October 12, 2026; the old *usecodebad · daily posting 7 AM Central* is paused) |

Both sessions run in the **USECODEBAD** workspace with this project attached, so they
have the bucket's key and the project's own settings. **Keep both sessions: don't archive
or delete them.** The Routines wake them up; without them nothing runs.

The project's permission file, `.claude/settings.json` (added by the owner on September
30), lets them run exactly two commands without stopping to ask: the nightly build
(`python3 scripts/cc_nightly.py`) and the storage tool (`python3 scripts/cc_store.py`).
Keep it as it is.

The old jobs are paused, not deleted: the Cowork task *Daily @usecodebad script + shop
video* (it had no key and could no longer download the project) and the Routine *Nightly
@usecodebad video build (R2)*.

The workspace (**USECODEBAD**: cloud icon above the message box → hover
**USECODEBAD** → gear) needs two settings:

- **Environment variables:** only Code Bad's key, from the `usecodebad-pipelineR2` token:
  `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or the clearer
  `CODEBAD_R2_ACCESS_KEY_ID` and `CODEBAD_R2_SECRET_ACCESS_KEY`, which win when both pairs
  are there). They're secrets: they live only there. Code Bad reads no other storage
  variable: `R2_BUCKET`, `R2_PUBLIC_URL`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID` and
  `R2_SECRET_ACCESS_KEY` are ignored, so another project's settings in the same workspace
  can never point it at another bucket. (Since September 30, 2026; `python3
  scripts/cc_store.py where` shows what it uses.)
- **Network access:** **Custom**, with the default list included, plus `fortnite-api.com`
  (the item pictures), `*.r2.cloudflarestorage.com` (uploading to the bucket), `*.r2.dev`
  (the bucket's public link), `archive.org` and `*.archive.org` (the music library).

The bucket's name, account and public link aren't secrets; they're in
`creator-code/storage.json`.

**The bucket stays inside the free 10 GB by itself.** Each day adds about 0.24 GB, so on
September 30, 2026 the owner added two lifecycle rules in Cloudflare (R2 → `usecodebad-media`
→ Settings → Object Lifecycle Rules): **Delete old shop videos** (prefix `shop-`) and
**Delete old long videos** (prefix `quiz-`), each deleting files 7 days after upload. Nothing
is lost: every video is scheduled within hours of being made, and Metricool plays each post
from its own copy, made when it was scheduled. The music (`music-library/`), the item data
(`cosmetics-data/`) and the status note (`_status/`) don't start with those names, so the
rules never touch them. The third rule there, *Default Multipart Abort Rule*, is
Cloudflare's own: it only clears half-finished uploads. Leave all three as they are.

## Check on it

- **Last night's build:** open `https://pub-3f1b6462fa8a4a69aeb545c6ece93d92.r2.dev/_status/nightly.json`. `"ok": true` with a count per
  folder under `"published"` means it worked. Otherwise `"problems"` says why in plain
  words, and `"log"` links the full log.
- **A day's videos** (the last 7 days): open `https://pub-3f1b6462fa8a4a69aeb545c6ece93d92.r2.dev/shop-YYYY-MM-DD/manifest.json` (the date in UTC). It lists
  the videos with their links, times and captions. Each video's `-qa.jpg` quick-look sheet
  sits beside it.
- **Build again now:** ask Claude to run the nightly build Routine. It skips anything
  that's already published.

To see a long video without posting it, ask Claude for a sample. It's rendered and sent
to you, and nothing schedules it.

---

## Draft or live?

**Live.** On 2026-09-23 the owner asked for posts to go out automatically, with no
approval step. Because nobody looks at a video before it's public, the Routine only
schedules a video when all of these hold, and skips it otherwise:

- the manifest exists and is for **that day's** shop
- the video is in the bucket, it's at least 60 seconds long, and its caption carries
  `#EpicPartner` and `#usecodebad`
- its time hasn't passed, and a video about the shop posts before the shop resets
- it isn't already scheduled (checked by title)
- a long video: its video and thumbnail are in the bucket, it's 3–14.5 minutes, its YouTube title is
  within 100 characters and its description carries `#EpicPartner` and `#usecodebad`;
  it goes to YouTube only
- a Threads post: only for the two videos the build marks for Threads, and only when its
  copy fits in 500 characters with `#EpicPartner` and `#usecodebad` in it

Each run also reports any of the previous day's posts that didn't go out. To go back to
drafts, say so and the Routine's `draft` setting flips back to `true`.

---

## If something breaks

| Symptom | What it means |
|---|---|
| The Cosmetics data run fails | Nothing stops: every video already planned still builds. Only extending the plan needs it; it retries next Monday |
| Build step says "Shop source still shows …" | Neither shop source had the new day yet. Each run waits 50 min before giving up, on purpose, so it never posts yesterday's shop, and the nightly build tries again at 03:22 and 06:22 UTC (the last about 1:22 AM Central). Nothing to do unless every try fails. |
| Fewer than 5 videos | A slot had no format that passed the quality gate that day (rare: each slot has several fallbacks). |
| Only 3 videos, in the old look | The five-video build failed as a whole that night, so it fell back to the classic three. The run's log names why |
| No long video on a weekday | Its build didn't pass the gate or the nightly build failed. The status note (Check on it, above) says why; the Routine's summary says which day is missing |
| No folder for the day | The nightly build didn't finish. The status note's `"problems"` says why; send it to me |
| Status note: "fortnite-api.com isn't reachable" | The workspace's network access is missing `fortnite-api.com`, so nothing was built (videos without pictures never go out). Add it back (Where it runs, above) |
| Status note: `"can_push"` isn't `"yes"` | The nightly build couldn't save its copy of the day's list into the project. Posting still works (the posting job reads the bucket itself), but send it to me |
| Nothing ran at all (no status note from last night, no posts, no script) | One of the two sessions marked *(automatic, keep)* was archived or deleted, or its Routine was paused. Tell me and I'll set it up again |
| Nothing scheduled in Metricool | The day's folder wasn't there for the evening run or the 6:53 AM backup; the Routine skips rather than guessing |
| Tomorrow's posts aren't in Metricool by bedtime | The evening run found the day's folder not built yet (the nightly build retries at 03:22 and 06:22 UTC), or it stopped. The 6:53 AM backup schedules whatever is missing before the first post at 8 AM |
| The day's script is in the project but no new videos were scheduled, and the posting session says the link step was blocked | The job couldn't get the signed links Metricool needs (this happened October 4–6, 2026; only older queued posts went out). Since October 7 it gets each folder's links with one plain command that the permission file allows. If it happens again, tell me: I'll schedule that day by hand and find what changed |
| You get "Allow Claude to use Create Scheduled Post?" (or Update / Get Scheduled Posts) | The Metricool connector is set to ask before those actions, which also stops the posting job, since nobody is there to tap Allow (this was why posts waited for a tap until October 12, 2026). Set them to always allowed: open https://claude.ai/customize/connectors, choose Metricool, and under its tool permissions allow Create Scheduled Post, Update Scheduled Post and Get Scheduled Posts |
| A video is missing and the Routine's summary says "Failed to normalize media" | Metricool couldn't copy the video. The Routine already tried a second fresh link; if it keeps happening, send it to me (on October 1 the cause was Metricool being unable to reach the bucket's public link) |
| A post shows an error in Metricool | TikTok or YouTube refused it; the next posting run's summary names it |
| A video went to TikTok and YouTube but not Facebook | Facebook refused it, or the Page came unlinked in Metricool. The Routine posts to the other two anyway and names the error; if it says the Page is disconnected, reconnect it in Metricool |
| A shop video is everywhere except Threads | Threads refused it, or the Threads account came unlinked in Metricool. Nothing else is affected; the next posting run's summary names the error. If it says Threads is disconnected, reconnect it in Metricool |
