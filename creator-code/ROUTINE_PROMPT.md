# The daily posting job

> **Already done, nothing to set up.** Since 2026-09-30 the Routine
> `usecodebad · daily posting 7 AM Central` wakes the Claude Code session
> `usecodebad · daily posting (automatic, keep)` every day at 6:53 AM Central and sends it
> the prompt below. That session runs in the owner's **USECODEBAD** workspace with this
> project attached, so it has the bucket's key and the project's permission file
> (`.claude/settings.json`), and it reaches Metricool through the account's Metricool
> connector. Keep the session: the Routine needs it.
>
> The earlier Cowork task `Daily @usecodebad script + shop video` (7:00 AM) is paused: it
> ran without the project or the key, and stopped working when GitHub stopped letting it
> download the project. This page is the record of what the job runs (updated 2026-09-28
> for the five short videos a day and the weekday long YouTube video, 2026-09-29 for
> Threads, and 2026-09-30 for the Cloudflare R2 bucket and the move to the attached
> session).

To change what it does, ask Claude to update the Routine's prompt and this page together.

---

## The prompt

```
(Scheduled daily run. Do today's whole job from STEP 0, even if this conversation
already holds earlier days' runs; dates below mean today's date.)

Daily job for @usecodebad (Fortnite creator code BAD). Write today's filming script,
schedule today's auto-made short videos (FIVE a day in the edit style from the switch day
in creator-code/lineup.json, three before it; two a day also go to Threads), keep the
auto-made quiz videos scheduled, and schedule each weekday's LONG YouTube video - all in
Metricool, posting automatically.

=== ACCOUNT ISOLATION - NON-NEGOTIABLE ===
This account has TWO Metricool brands. You may ONLY touch brand id 7066444
(TikTok usecodebad, YouTube UCA9fkJZbLeR5uXTU82Ur74Q, the usecodebad Facebook Page and
Instagram account connected to it on 2026-09-23, and the Threads account connected to it
on 2026-09-29).
The other brand belongs to an unrelated venture. NEVER read it, write to it,
schedule to it, or mention it. Before ANY Metricool call, verify the brandId/blogId is
exactly 7066444. If it is not, stop and do nothing.
==========================================

STEP 0 - THE PROJECT. This session has the project attached (this repository) in the
owner's USECODEBAD workspace; every command below runs from the repository root (your
working directory). First bring it up to date:
    git pull origin claude/creator-code-bad-automation-0jjc1k
Do not continue if that fails. Read creator-code/lineup.json: "edit_from" is the first day
of the five-a-day edit shorts (null = not yet), "long_from" the first day with long videos.
Run the project's storage commands exactly as written below (python3 scripts/cc_store.py
...): the project's settings allow exactly those.

STEP 1 - READ THE RULES. Read creator-code/RULES.md in full and follow it without
exception.

STEP 2 - WRITE TODAY'S SCRIPT.
If creator-code/scripts/YYYY-MM-DD.md (today's date) is already in the repository from an
earlier run today, keep it as it is and go on to STEP 3.
Check today's weekday. Read creator-code/DAILY_VIDEOS.md and use THAT weekday's format
(Mon = Shop Verdict, Tue = Challenge Run, Wed = Is It Actually Good?, Thu = 5 Things
You're Doing Wrong, Fri = Ranked Worst to Best, Sat = The Match, Sun = The Stitch).
Web-search first for the current season, meta, patch notes and today's shop - these
change, so re-check rather than trusting the doc.
NEVER invent shop contents, prices, patch notes or cosmetic names. If you cannot verify
something, mark it clearly as a placeholder and say so in your summary.
Write a complete filmable script: word-for-word lines with timestamps, shot list,
on-screen text, full caption, pinned comment, editing notes. Target 75-90 seconds. Read
creator-code/scripts/2026-09-23.md first and match its depth and tone.
Put the creator code mention ONCE, around 55 seconds in. Never in the opening 3 seconds.
Save to creator-code/scripts/YYYY-MM-DD.md, commit, and push it with
    git push origin HEAD:claude/creator-code-bad-automation-0jjc1k
(the checkout may be on a detached HEAD, so always push HEAD to that branch), and
confirm the push succeeded.

STEP 3 - SCHEDULE TODAY'S SHORT VIDEOS TO POST AUTOMATICALLY.
The owner asked (2026-09-23) for these to go live on their own at their times, with no
manual approval. Nobody reviews them before they are public, so every check below is
mandatory: if anything about a video is off, skip that video and say why in the summary
- never guess, never substitute.
The nightly build (a scheduled Claude session since 2026-09-30; GitHub releases are no
longer used) makes them right after the shop resets (00:00 UTC) and publishes them to the
Cloudflare R2 bucket, in the folder shop-YYYY-MM-DD, with a manifest you read (from
the repository root) with:
    python3 scripts/cc_store.py cat shop-YYYY-MM-DD/manifest.json
where YYYY-MM-DD is TODAY's date in UTC (that is the shop day). Its "lineup" is "edit"
(five videos: 8 AM, 11 AM, 1 PM, 4 PM, 7 PM Central) or "classic" (three); schedule
whatever "videos" it lists, each at its own time.
3a. Read it with that command. If the command fails (no such file), or its "shop_day" is not
    today's UTC date, schedule NOTHING and say so in the summary. Never schedule a video
    about another day's shop.
3b. For each entry in "videos", check before using it: its file is in the bucket
    (python3 scripts/cc_store.py has FOLDER/NAME exits 0, where FOLDER is the manifest's
    folder and NAME the file name at the end of the entry's url; the url itself is the
    bucket's public r2.dev link, which Metricool fetches; don't curl it), its duration is at least 60, and its caption contains "#EpicPartner" and
    "#usecodebad". Skip any entry that fails a check.
3c. Call getScheduledPosts for brandId "7066444", timezone "America/Chicago", from today
    00:00 to today 23:59. Skip any manifest video whose "title" already equals the
    tiktokData.title of a post in that list (no duplicates). Compare titles, not video
    links: Metricool stores its own copy of each video, so the links never match.
    Likewise skip a video's Instagram post (3d) if a post in the list has instagram among
    its providers and its text equals the entry's "ig_caption", and its Threads post (3d)
    if a post in the list has threads among its providers and its text equals the entry's
    "threads_caption".
    From edit_from on, leave out of these duplicate checks every post listed under today's
    date in creator-code/published/old-quiz-posts.json (compare by id): those are the
    old versions queued before the switch, often with the same title as today's new
    video, and 3f retires them.
3d. For each remaining entry whose post_at_local is still at least 15 minutes in the
    future in America/Chicago, call createScheduledPost with:
  blogId: "7066444"   <- verify before calling
  date: the entry's "post_at_iso" (if absent, post_at_local plus the Chicago UTC offset
        in effect that day)
  info: {
    "publicationDate": {"dateTime": <post_at_local>, "timezone": "America/Chicago"},
    "providers": [{"network": "tiktok"}, {"network": "youtube"}, {"network": "facebook"}],
    "media": [<the entry's url>],
    "text": <the entry's caption, exactly as given - it already carries the #EpicPartner
             disclosure and the #usecodebad #creatorcodebad #codebad tags>,
    "draft": false,
    "autoPublish": true,
    "tiktokData": {"privacyOption": "PUBLIC_TO_EVERYONE", "commercialContentThirdParty": true,
                   "commercialContentOwnBrand": false, "title": <the entry's title>,
                   "autoAddMusic": false, "isAigc": false},
    "youtubeData": {"title": <the entry's yt_title>, "type": "short", "privacy": "public",
                    "madeForKids": false, "category": "GAMING", "tags": <the entry's hashtags>,
                    "isAiGeneratedContent": false},
    "facebookData": {"type": "REEL"}   <- "POST" instead if the entry's duration is over 90
  }
  draft is false and autoPublish is true, so each post goes live by itself at its time.
  Facebook Reels can be at most 90 seconds, so a longer video goes to Facebook as a normal
  video post (type POST). If createScheduledPost fails and the error is about Facebook,
  create the same post again without the facebook provider and facebookData, so TikTok
  and YouTube still post, and name the Facebook error in the summary.
  commercialContentThirdParty is true because code BAD earns a commission from Epic;
  TikTok requires that to be labelled as branded content.
  Post times come from the manifest. Every video about today's shop ("about_shop" true,
  or no "about_shop" field) is timed before the shop resets (7 PM CDT / 6 PM CST); a video
  with "about_shop": false (the 7 PM slot) is not about the shop and may post after the
  reset. Never move a post later. If a slot's time has already passed, skip it.
  Do not add videoThumbnailUrl or videoCoverMilliseconds: each video's first frame is its
  designed thumbnail, and TikTok uses the first frame as the cover when none is set.
  Never claim the code gives a discount, and never add wording to the caption.
  INSTAGRAM gets its own post for each video, because Instagram allows only 5 hashtags
  (#EpicPartner is one) and the main caption has about ten. Call createScheduledPost a
  second time with the same blogId "7066444", date and publicationDate, and info:
    {"providers": [{"network": "instagram"}], "media": [<the entry's url>],
     "text": <the entry's "ig_caption", exactly as given>, "draft": false, "autoPublish": true,
     "instagramData": {"type": "REEL", "showReelOnFeed": true, "isAiGenerated": false}}
  If the entry has no "ig_caption", skip Instagram for it and say so in the summary. If
  the Instagram call fails, the main post is unaffected: name the error in the summary.
  THREADS (owner's go-ahead 2026-09-29) gets its own post for each entry whose "threads"
  is true - two a day: today's shop video and the game on it - because Threads allows
  only 500 characters. Call createScheduledPost once more with the same blogId
  "7066444", date and publicationDate, and info:
    {"providers": [{"network": "threads"}], "media": [<the entry's url>],
     "text": <the entry's "threads_caption", exactly as given>, "draft": false,
     "autoPublish": true, "threadsData": {"allowedCountryCodes": []}}
  Skip Threads for an entry whose "threads" is not true, or whose "threads_caption" is
  missing or lacks "#EpicPartner" or "#usecodebad" (the build sets "threads" true only
  when that copy fits Threads' limit). Never put a quiz video or a long video on
  Threads. If the Threads call fails, the other posts are unaffected: name the error in
  the summary.
3e. Call getScheduledPosts again and confirm each new post is there with the right time
    and title, draft false, all three networks (tiktok, youtube, facebook) on the main
    post, its Instagram post beside it, and - for entries with "threads" true - its
    Threads post.
3f. FROM edit_from ON, RETIRE TODAY'S OLD QUIZ POSTS. Posts queued before the switch
    would make today more than five. Do this only if today is on or after edit_from AND
    the shop manifest's "lineup" is "edit" AND at least 3 of today's shop videos are now
    scheduled as their own posts (3e; an old listed post with the same title doesn't
    count); otherwise leave them, so the day is never empty. Read
    creator-code/published/old-quiz-posts.json: its "days" lists, for each date, the old
    posts queued for it before the switch, each by its Metricool "id" and "uuid". If
    today's date isn't there, there is nothing to retire. For each post listed under
    today's date that is in the 3e list and still draft false, call updateScheduledPost
    with blogId "7066444", its id and uuid, and its full existing content unchanged
    except "draft": true. Never touch any post that isn't listed under today's date.
    Say in the summary how many old posts you set to draft.
3g. Call getScheduledPosts for brandId "7066444" for yesterday (00:00 to 23:59
    America/Chicago). Posts stay in that list after they go out: a network that posted
    shows status "PUBLISHED" under "providers". Name any post where a network shows any
    other status, with its detailedStatus, in the summary so the owner knows it did not go
    out there.

STEP 4 - QUIZ VIDEOS AND LONG VIDEOS FROM THE QUIZ FOLDERS.
Quiz videos (three a day before the switch) and the long YouTube videos are published one
bucket folder per quiz day, read with:
    python3 scripts/cc_store.py cat quiz-YYYY-MM-DD/manifest.json
4a. For each day D from today to today + 14 (YYYY-MM-DD in UTC, like the shop), download
    that day's quiz manifest with that command. If it fails (no such file), that day isn't built yet:
    skip it (mention it in the summary only if D is within the next 3 days and D is
    before edit_from). Use a manifest only if its "quiz_day" equals D.
4b. QUIZ SHORTS: use a manifest's "videos" only if D is BEFORE edit_from (or edit_from is
    null). From edit_from on, the five daily shorts come from the shop folder (STEP 3),
    so never schedule a quiz manifest's "videos" for such a day, even if some are listed.
    Check every usable video like 3b (its file is in the bucket, duration at least 60, caption
    contains "#EpicPartner" and "#usecodebad") and also that its duration is at most 90.
    Skip any video that fails.
4c. Call getScheduledPosts ONCE for brandId "7066444", timezone "America/Chicago", from
    today 00:00 to today + 15 at 23:59. Skip any quiz video whose "title" already equals
    the tiktokData.title of a post in that list (no duplicates).
4d. For each remaining quiz video whose post_at_local is at least 15 minutes in the future,
    call createScheduledPost exactly as in 3d - same blogId "7066444", providers,
    tiktokData, youtubeData, facebookData ("REEL"), draft false, autoPublish true - with
    date = its "post_at_iso" and publicationDate.dateTime = its "post_at_local", and give
    it its Instagram post exactly as in 3d (ig_caption; skip it if a post in the 4c list
    already has instagram among its providers and that exact text). Quiz videos are not
    tied to the shop reset, so the 8:00 PM slot is fine.
4e. LONG VIDEOS (YouTube only, Monday to Friday at 3 PM Central): a manifest may list
    "long_videos" (the video for day X rides in folder quiz-(X+14), which is why 4a goes
    to today + 14). For each entry with "kind" "long" whose post_at_local is at least 15
    minutes in the future, check before using it: its "url" and its "thumbnail_url" files are
    in the bucket (as in 3b), its duration is between 180 and 870, youtube.title is not empty
    and at most 100 characters, and youtube.description contains "#usecodebad" and
    "#EpicPartner". Skip it if a post in the 4c list has youtube among its providers and
    its youtubeData.title equals the entry's youtube.title. Otherwise call
    createScheduledPost with:
  blogId: "7066444"   <- verify before calling
  date: the entry's "post_at_iso"
  info: {
    "publicationDate": {"dateTime": <post_at_local>, "timezone": "America/Chicago"},
    "providers": [{"network": "youtube"}],
    "media": [<the entry's url>],
    "videoThumbnailUrl": <the entry's thumbnail_url>,
    "text": <the entry's youtube.description, exactly as given - it carries the chapters,
             the code line with #EpicPartner, the music credits and Epic's notice>,
    "draft": false,
    "autoPublish": true,
    "youtubeData": {"title": <youtube.title>, "type": "video", "privacy": "public",
                    "madeForKids": false, "category": "GAMING", "tags": <youtube.tags>,
                    "isAiGeneratedContent": false}
  }
  YouTube ONLY: never add TikTok, Facebook, Instagram or Threads to a long video. If the
  call is rejected because of the thumbnail (for example VIDEO_THUMBNAIL_NOT_APPLICABLE),
  make it once more without videoThumbnailUrl and say so in the summary (custom thumbnails
  need a verified YouTube channel). isAiGeneratedContent is false: the narrator is a
  generic text-to-speech voice, not anyone's real voice, over graphics - YouTube only asks
  for the label on realistic content that could be mistaken for real people or events.
4f. Call getScheduledPosts again and confirm each quiz post you added is there with its
    Instagram post, and each long video is there on YouTube only, at 3 PM Central, draft
    false.

STEP 5 - SUMMARY. Short and plain: format used for the script and its hook line, whether
the script pushed, for each of today's short videos its time, format and the networks it
is scheduled on, Threads included (or why not), how many old quiz posts you set to draft
(3f), how many quiz posts you added and the furthest day now queued, each long video
scheduled (its day, title and time) or why a weekday's long video is missing, and any of
yesterday's posts that did not go out.
```

---

## Why it posts on its own now

Until 2026-09-23 every post landed as a **draft** that waited for a tap. That day the owner
asked for posting to be fully automatic, so the Routine now schedules with `draft: false`.
The checks in step 3 are what stand in for a human look: a video that fails any of them
is skipped, never swapped for another. To go back to drafts, set `"draft": true` in step 3d
(and ask Claude to update the live Routine to match).

On 2026-09-23 the owner connected a Facebook Page to the usecodebad brand and asked for
it to get the same three posts a day. Each video goes to Facebook as a Reel (a normal
video post if it is ever over 90 seconds, Facebook's Reel limit). If Facebook refuses a
post, TikTok and YouTube still get it, and the summary says what Facebook said.
