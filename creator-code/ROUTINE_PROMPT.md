# The daily posting job

> **Already done, nothing to set up.** Since 2026-10-12 two Routines wake the Claude Code
> session `usecodebad · daily posting (automatic, keep)` and send it the prompt below:
> `usecodebad · evening posting (queues the next day)` every day at 02:10 UTC (9:10 PM
> Central; 8:10 PM after November 1), about two hours after the Item Shop resets, so each
> day's posts are queued the night before, and `usecodebad · morning posting backup (6:53 AM
> Central)`, which adds anything the evening run missed. From 2026-09-30 to 2026-10-12 the
> Routine `usecodebad · daily posting 7 AM Central` ran it once a day at 6:53 AM; it is
> paused. That session runs in the owner's **USECODEBAD** workspace with this
> project attached, so it has the bucket's key and the project's permission file
> (`.claude/settings.json`), and it reaches Metricool through the account's Metricool
> connector. Keep the session: the Routines need it.
>
> The earlier Cowork task `Daily @usecodebad script + shop video` (7:00 AM) is paused: it
> ran without the project or the key, and stopped working when GitHub stopped letting it
> download the project. This page is the record of what the job runs (updated 2026-09-28
> for the five short videos a day and the weekday long YouTube video, 2026-09-29 for
> Threads, 2026-09-30 for the Cloudflare R2 bucket and the move to the attached session,
> 2026-10-01 for signed links: Metricool stopped importing videos from the bucket's
> r2.dev link that morning, so the job now gives it a signed link to each file, and
> 2026-10-06 for getting a folder's signed links with one plain command, after the job
> stopped at that step on October 4-6, and 2026-10-12 for the evening run: each step now
> works on one day, D, the shop day in UTC, and the steps for the old quiz posts, which
> ended on October 11, are gone).

To change what it does, ask Claude to update both Routines' prompt and this page together.

---

## The prompt

```
(Scheduled run. This job runs twice for each shop day: in the evening, about two hours
after the Fortnite Item Shop resets at 00:00 UTC, so the day's posts are queued the night
before, and again at 6:53 AM Central as a backup that adds only what the evening run
missed. Do the whole job from STEP 0, even if this conversation already holds earlier
runs. Earlier runs' prompts said "today": follow this version instead.)

THE DAY. Every step below works on ONE day, D: today's date in UTC, which is the shop day.
Get it fresh at the start of every run with
    date -u +%F
and never reuse a date from earlier in this conversation. In the evening run it is still
the evening before in Central time, so D's posts go out tomorrow by the owner's clock.
All post times below are on D, in America/Chicago. For the other dates the job needs, use
the same command, for example date -u -d "D + 14 days" +%F (D written as YYYY-MM-DD).

Daily job for @usecodebad (Fortnite creator code BAD). Write D's filming script, schedule
D's auto-made short videos (five a day; two of them also go to Threads) and, Monday to
Friday, D's LONG YouTube video - all in Metricool, posting automatically.

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
Do not continue if that fails.
Run the project's storage commands exactly as written below (python3 scripts/cc_store.py
...): the project's settings allow exactly those. Run each one as its own command with
nothing else on the line - no cd, &&, ;, pipes, redirects, loops, $(...) or python -c
around it - or it won't match those settings. If a storage command is still refused,
don't try another way: schedule nothing that needs it and say so in the summary.

STEP 1 - READ THE RULES. Read creator-code/RULES.md in full and follow it without
exception.

STEP 2 - WRITE D'S SCRIPT.
If creator-code/scripts/YYYY-MM-DD.md (D's date) is already in the repository from an
earlier run, keep it as it is and go on to STEP 3.
Check D's weekday. Read creator-code/DAILY_VIDEOS.md and use THAT weekday's format
(Mon = Shop Verdict, Tue = Challenge Run, Wed = Is It Actually Good?, Thu = 5 Things
You're Doing Wrong, Fri = Ranked Worst to Best, Sat = The Match, Sun = The Stitch).
Web-search first for the current season, meta, patch notes and D's shop (live since 00:00
UTC on D) - these change, so re-check rather than trusting the doc.
NEVER invent shop contents, prices, patch notes or cosmetic names. If you cannot verify
something, mark it clearly as a placeholder and say so in your summary.
Write a complete filmable script: word-for-word lines with timestamps, shot list,
on-screen text, full caption, pinned comment, editing notes. Target 75-90 seconds. Read
creator-code/scripts/2026-09-23.md first and match its depth and tone.
Put the creator code mention ONCE, around 55 seconds in. Never in the opening 3 seconds.
Save to creator-code/scripts/YYYY-MM-DD.md (D's date), commit, and push it with
    git push origin HEAD:claude/creator-code-bad-automation-0jjc1k
(the checkout may be on a detached HEAD, so always push HEAD to that branch), and
confirm the push succeeded.

STEP 3 - SCHEDULE D'S SHORT VIDEOS TO POST AUTOMATICALLY.
The owner asked (2026-09-23) for these to go live on their own at their times, with no
manual approval. Nobody reviews them before they are public, so every check below is
mandatory: if anything about a video is off, skip that video and say why in the summary
- never guess, never substitute.
The nightly build (a scheduled Claude session since 2026-09-30; GitHub releases are no
longer used) makes them right after the shop resets (00:00 UTC) and publishes them to the
Cloudflare R2 bucket, in the folder shop-YYYY-MM-DD, with a manifest you read (from
the repository root) with:
    python3 scripts/cc_store.py cat shop-YYYY-MM-DD/manifest.json
where YYYY-MM-DD is D (the shop day). Its "lineup" is "edit" (five videos: 8 AM, 11 AM,
1 PM, 4 PM, 7 PM Central) or "classic" (three); schedule whatever "videos" it lists, each
at its own time.
3a. Read it with that command. If the command fails (no such file), or its "shop_day" is not
    D, schedule NOTHING and say so in the summary (the next run for D tries again). Never
    schedule a video about another day's shop.
3b. For each entry in "videos", check before using it: its file is in the bucket
    (python3 scripts/cc_store.py has FOLDER/NAME exits 0, where FOLDER is the manifest's
    folder and NAME the file name at the end of the entry's url; don't curl the url),
    its duration is at least 60, and its caption contains "#EpicPartner" and
    "#usecodebad". Skip any entry that fails a check.
3c. Call getScheduledPosts for brandId "7066444", timezone "America/Chicago", from D
    00:00 to D 23:59. Skip any manifest video whose "title" already equals the
    tiktokData.title of a post in that list (no duplicates: an earlier run for D may
    already have scheduled it). Compare titles, not video links: Metricool stores its own
    copy of each video, so the links never match.
    Likewise skip a video's Instagram post (3d) if a post in the list has instagram among
    its providers and its text equals the entry's "ig_caption", and its Threads post (3d)
    if a post in the list has threads among its providers and its text equals the entry's
    "threads_caption".
3d. First get the links Metricool can import D's videos from, all at once, with ONE
    command, run exactly like this and on its own:
        python3 scripts/cc_store.py links FOLDER
    (FOLDER as in 3b). It prints a JSON map from each video and cover in that folder to a
    signed link to that one file through R2's main storage address, valid for 6 hours.
    For each remaining entry whose post_at_local is still at least 15 minutes in the
    future in America/Chicago, use the link for its NAME (as in 3b) as the media of the
    video's main, Instagram and Threads posts: Metricool copies the video when the post
    is scheduled, and since 2026-10-01 it often can't fetch the bucket's r2.dev link.
    Never put the r2.dev url in media. Then call createScheduledPost with:
  blogId: "7066444"   <- verify before calling
  date: the entry's "post_at_iso" (if absent, post_at_local plus the Chicago UTC offset
        in effect that day)
  info: {
    "publicationDate": {"dateTime": <post_at_local>, "timezone": "America/Chicago"},
    "providers": [{"network": "tiktok"}, {"network": "youtube"}, {"network": "facebook"}],
    "media": [<the signed link>],
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
  If createScheduledPost fails with "Failed to normalize media", run the same links
  command again for a fresh link and try once more; if it fails again, skip that video
  and name it in the summary.
  commercialContentThirdParty is true because code BAD earns a commission from Epic;
  TikTok requires that to be labelled as branded content.
  Post times come from the manifest. Every video about D's shop ("about_shop" true, or no
  "about_shop" field) is timed before that shop ends (7 PM CDT / 6 PM CST on D); a video
  with "about_shop": false (the 7 PM slot) is not about the shop and may post after the
  reset. Never move a post later. If a slot's time has already passed, skip it.
  Do not add videoThumbnailUrl or videoCoverMilliseconds: each video's first frame is its
  designed thumbnail, and TikTok uses the first frame as the cover when none is set.
  Never claim the code gives a discount, and never add wording to the caption.
  INSTAGRAM gets its own post for each video, because Instagram allows only 5 hashtags
  (#EpicPartner is one) and the main caption has about ten. Call createScheduledPost a
  second time with the same blogId "7066444", date and publicationDate, and info:
    {"providers": [{"network": "instagram"}], "media": [<the signed link>],
     "text": <the entry's "ig_caption", exactly as given>, "draft": false, "autoPublish": true,
     "instagramData": {"type": "REEL", "showReelOnFeed": true, "isAiGenerated": false}}
  If the entry has no "ig_caption", skip Instagram for it and say so in the summary. If
  the Instagram call fails, the main post is unaffected: name the error in the summary.
  THREADS (owner's go-ahead 2026-09-29) gets its own post for each entry whose "threads"
  is true - two a day: D's shop video and the game on it - because Threads allows
  only 500 characters. Call createScheduledPost once more with the same blogId
  "7066444", date and publicationDate, and info:
    {"providers": [{"network": "threads"}], "media": [<the signed link>],
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
3f. Call getScheduledPosts for brandId "7066444" for the day before D (00:00 to 23:59
    America/Chicago). Posts stay in that list after they go out: a network that posted
    shows status "PUBLISHED" under "providers". Name any post where a network shows any
    other status, with its detailedStatus, in the summary so the owner knows it did not go
    out there.

STEP 4 - D'S LONG YOUTUBE VIDEO (Monday to Friday at 3 PM Central).
If D is a Saturday or a Sunday there is none: go to STEP 5. The long video for D is built
the same night as D's shop folder, about half an hour after it, and published in the
bucket folder of the quiz day two weeks out: quiz-Q, where Q = D + 14 days (YYYY-MM-DD,
from the date command above). Read its manifest with:
    python3 scripts/cc_store.py cat quiz-Q/manifest.json
4a. If that command fails (no such file), D's long video isn't built yet: schedule no long
    video and say so in the summary (the next run for D tries again). Use the manifest only
    if its "quiz_day" equals Q. Ignore its "videos" list: quiz shorts ended on 2026-10-01,
    so never schedule them.
4b. In its "long_videos", take the entry with "kind" "long" and "day" equal to D. If its
    post_at_local is at least 15 minutes in the future, check before using it: its "url"
    and its "thumbnail_url" files are in the bucket (as in 3b), its duration is between 180
    and 870, youtube.title is not empty and at most 100 characters, and
    youtube.description contains "#usecodebad" and "#EpicPartner". Skip it if a post in
    D's latest getScheduledPosts list (3e, or call it now as in 3c) has youtube among its
    providers and its youtubeData.title equals the entry's youtube.title (an earlier run
    for D already scheduled it). Otherwise get signed links for its video and its
    thumbnail with one command, run on its own as in 3d:
        python3 scripts/cc_store.py links quiz-Q
    and call createScheduledPost with:
  blogId: "7066444"   <- verify before calling
  date: the entry's "post_at_iso"
  info: {
    "publicationDate": {"dateTime": <post_at_local>, "timezone": "America/Chicago"},
    "providers": [{"network": "youtube"}],
    "media": [<the video's signed link>],
    "videoThumbnailUrl": <the thumbnail's signed link>,
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
4c. Call getScheduledPosts again for D and confirm the long video is there on YouTube only,
    at 3 PM Central, draft false.

STEP 5 - SUMMARY. Short and plain: D and its weekday, the format used for the script and
its hook line (or that it was already there), whether the script pushed, for each of D's
short videos its time, format and the networks it is scheduled on, Threads included (or
why not), D's long video (title and time) or why a weekday's long video is missing, and
any of the previous day's posts that did not go out.
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
