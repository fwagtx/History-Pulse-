# The daily Routine — set this up once in claude.ai

> **Already done.** The Routine `Daily @usecodebad script + shop video` is live (7:00 AM
> Central) and its prompt matches the one below. This page is the record of what it runs.

I can't attach the Metricool connector to a Routine from inside Claude Code (this org doesn't
allow it), so this one has to be created from the website. It's a few clicks.

## Steps

1. Go to **claude.ai** → **Routines** (sidebar)
2. **Create Routine**
3. Schedule: **daily at 7:00 AM** (your time — America/Chicago)
4. Under connectors, tick **Metricool Social Media Management** ← the part I can't do for you
5. Paste the prompt below as the Routine's instructions
6. Save

Then tell me it's set up and I'll delete the older script-only Routine so you don't get two.

---

## Paste this as the prompt

```
Daily job for @usecodebad (Fortnite creator code BAD). Write today's filming script, and
schedule today's THREE auto-made shop videos in Metricool to post automatically to TikTok,
YouTube Shorts and Facebook.

=== ACCOUNT ISOLATION - NON-NEGOTIABLE ===
This account has TWO Metricool brands. You may ONLY touch brand id 7066444
(TikTok usecodebad, YouTube UCA9fkJZbLeR5uXTU82Ur74Q, and the usecodebad Facebook Page
connected to it on 2026-09-23).
The other brand belongs to an unrelated venture. NEVER read it, write to it,
schedule to it, or mention it. Before ANY Metricool call, verify the brandId/blogId is
exactly 7066444. If it is not, stop and do nothing.
==========================================

STEP 0 - GET THE REPO. You start with nothing on disk:
    git clone https://github.com/fwagtx/History-Pulse-.git /home/user/hp
    cd /home/user/hp && git checkout claude/creator-code-bad-automation-0jjc1k
If that fails, use add_repo (owner fwagtx, repo History-Pulse-). Do not continue
without a working clone.

STEP 1 - READ THE RULES. Read creator-code/RULES.md in full and follow it without
exception.

STEP 2 - WRITE TODAY'S SCRIPT.
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
Save to creator-code/scripts/YYYY-MM-DD.md, commit, push to
claude/creator-code-bad-automation-0jjc1k, and confirm the push succeeded.

STEP 3 - SCHEDULE TODAY'S 3 SHOP VIDEOS TO POST AUTOMATICALLY.
The owner asked (2026-09-23) for these to go live on their own at their times, with no
manual approval. Nobody reviews them before they are public, so every check below is
mandatory: if anything about a video is off, skip that video and say why in the summary
- never guess, never substitute.
A GitHub Action builds three videos every night right after the shop resets (00:00 UTC)
and publishes them with a manifest at:
    https://github.com/fwagtx/History-Pulse-/releases/download/shop-YYYY-MM-DD/manifest.json
where YYYY-MM-DD is TODAY's date in UTC (that is the shop day).
3a. Download it: curl -fsSL "<that url>". If it is missing, or its "shop_day" is not
    today's UTC date, schedule NOTHING and say so in the summary. Never schedule a video
    about another day's shop.
3b. For each entry in "videos", check before using it: its url answers
    (curl -fsSIL "<url>" succeeds), its duration is at least 60, and its caption contains
    "#EpicPartner" and "#usecodebad". Skip any entry that fails a check.
3c. Call getScheduledPosts for brandId "7066444", timezone "America/Chicago", from today
    00:00 to today 23:59. Skip any manifest video whose "title" already equals the
    tiktokData.title of a post in that list (no duplicates). Compare titles, not video
    links: Metricool stores its own copy of each video, so the links never match.
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
  Every post time in the manifest is before the shop resets (7 PM CDT / 6 PM CST). Never
  move a post later. If a slot's time has already passed, skip it.
  Do not add videoThumbnailUrl or videoCoverMilliseconds: each video's first frame is its
  designed thumbnail, and TikTok uses the first frame as the cover when none is set.
  Never claim the code gives a discount, and never add wording to the caption.
3e. Call getScheduledPosts again and confirm each new post is there with the right time
    and title, draft false, and all three networks (tiktok, youtube, facebook).
3f. Call getScheduledPosts for brandId "7066444" for yesterday (00:00 to 23:59
    America/Chicago). Anything from yesterday still in that list did not fully publish -
    name it, and which network shows the error, in the summary so the owner knows.

STEP 4 - SUMMARY. Short and plain: format used for the script and its hook line, whether
the script pushed, for each of the 3 videos its time, format and the networks it is
scheduled on (or why not), and any of yesterday's posts that did not go out.
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
