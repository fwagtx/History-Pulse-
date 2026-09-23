# The daily Routine — set this up once in claude.ai

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
Daily job for @usecodebad (Fortnite creator code BAD). Write today's video script, and
schedule today's shop video into Metricool.

=== ACCOUNT ISOLATION - NON-NEGOTIABLE ===
This account has TWO Metricool brands. You may ONLY touch brand id 7066444
(TikTok usecodebad, YouTube UCA9fkJZbLeR5uXTU82Ur74Q).
The other brand belongs to an unrelated venture. NEVER read it, write to it,
schedule to it, or mention it. Before ANY scheduling call, verify the brandId is
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

STEP 3 - SCHEDULE THE SHOP VIDEO.
A GitHub Action builds a shop video nightly and publishes it as a release at:
    https://github.com/fwagtx/History-Pulse-/releases/download/shop-YYYY-MM-DD/bad-shop-YYYY-MM-DD.mp4
Check that release exists. If it does NOT, skip this step entirely and say so in your
summary - never schedule a post with no video, and never substitute a different video.

If it exists, schedule it with Metricool createScheduledPost:
  brandId: "7066444"        <- verify before calling
  date: tomorrow 17:00 America/Chicago
  providers: [{"network":"tiktok"}]
  media: [the release .mp4 URL]
  draft: true               <- always a draft; a human reviews before anything publishes
  tiktokData: {"privacyOption":"PUBLIC_TO_EVERYONE","commercialContentOwnBrand":true,
               "title":"<short title>"}
  text: caption, which MUST include the #EpicPartner disclosure

Never claim the code gives a discount - "costs you nothing extra" is the honest phrasing.

STEP 4 - SUMMARY. Four lines: format used, hook line, did the script push, was the video
scheduled (or why not).
```

---

## Why `draft: true`

Every post lands as a **draft** in Metricool. Nothing publishes on its own until you look at
it and press go.

Once you've watched a few come through and they look right, tell me and I'll change it to
publish automatically. Worth earning that trust before letting it post unattended to a public
account.
