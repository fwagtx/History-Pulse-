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
put today's THREE auto-made shop videos into Metricool as drafts.

=== ACCOUNT ISOLATION - NON-NEGOTIABLE ===
This account has TWO Metricool brands. You may ONLY touch brand id 7066444
(TikTok usecodebad, YouTube UCA9fkJZbLeR5uXTU82Ur74Q).
The other brand belongs to an unrelated venture. NEVER read it, write to it,
schedule to it, or mention it. Before ANY scheduling call, verify the brandId/blogId is
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

STEP 3 - PUT TODAY'S 3 SHOP VIDEOS INTO METRICOOL AS DRAFTS.
A GitHub Action builds three videos every night right after the shop resets (00:00 UTC)
and publishes them with a manifest at:
    https://github.com/fwagtx/History-Pulse-/releases/download/shop-YYYY-MM-DD/manifest.json
where YYYY-MM-DD is TODAY's date in UTC (that is the shop day).
3a. Download it: curl -fsSL "<that url>". If it is missing, or its "shop_day" is not
    today's UTC date, schedule NOTHING and say so in the summary. Never schedule a video
    about another day's shop, and never substitute a different video.
3b. Call getScheduledPosts for brandId "7066444", timezone "America/Chicago", from today
    00:00 to today 23:59. Skip any manifest video whose "title" already equals the
    tiktokData.title of a post in that list (no duplicates). Compare titles, not video
    links: Metricool stores its own copy of each video, so the links never match.
3c. For each remaining entry in "videos" whose post_at_local is still at least 15 minutes
    in the future in America/Chicago, call createScheduledPost with:
  blogId: "7066444"   <- verify before calling
  date: the entry's "post_at_iso" (if absent, post_at_local plus the Chicago UTC offset
        in effect that day)
  info: {
    "publicationDate": {"dateTime": <post_at_local>, "timezone": "America/Chicago"},
    "providers": [{"network": "tiktok"}, {"network": "youtube"}],
    "media": [<the entry's url>],
    "text": <the entry's caption, exactly as given - it already carries the #EpicPartner
             disclosure and the #usecodebad #creatorcodebad #codebad tags>,
    "draft": true,
    "autoPublish": true,
    "tiktokData": {"privacyOption": "PUBLIC_TO_EVERYONE", "commercialContentThirdParty": true,
                   "commercialContentOwnBrand": false, "title": <the entry's title>,
                   "autoAddMusic": false, "isAigc": false},
    "youtubeData": {"title": <the entry's yt_title>, "type": "short", "privacy": "public",
                    "madeForKids": false, "category": "GAMING", "tags": <the entry's hashtags>,
                    "isAiGeneratedContent": false}
  }
  draft MUST be true - a human reviews every post before it goes live.
  commercialContentThirdParty is true because code BAD earns a commission from Epic;
  TikTok requires that to be labelled as branded content.
  Every post time in the manifest is before the shop resets (7 PM CDT / 6 PM CST). Never
  move a post later. If a slot's time has already passed, skip it.
  Do not add videoThumbnailUrl or videoCoverMilliseconds.
  Never claim the code gives a discount - "costs you nothing extra" is the honest phrasing.
3d. Call getScheduledPosts again and confirm each new draft is there with the right time
    and title.

STEP 4 - SUMMARY. Short and plain: format used for the script and its hook line, whether
the script pushed, and for each of the 3 videos its time and format and whether it was
added as a draft (or why not).
```

---

## Why `draft: true`

Every post lands as a **draft** in Metricool. Nothing publishes on its own until you look at
it and press go.

Once you've watched a few come through and they look right, tell me and I'll change it to
publish automatically. Worth earning that trust before letting it post unattended to a public
account.
