# History Pulse — YouTube Channel Automation (Claude Code Project)

This repo is the production pipeline for **History Pulse**, a YouTube channel covering all
types of historical events, framed around why they're relevant today.

Claude Code, read this file fully before doing any work in this repo. These rules apply to
every session, every command, and every task — not just the first one.

## What this project is

A local, zero-monthly-fee content pipeline. You (Claude Code) act as researcher, scriptwriter,
SEO strategist, and thumbnail concept designer for each video. You do NOT have upload/publish
access, and you must never simulate, imply, or prepare a direct upload without explicit human
approval logged in this repo (see "Review gate" below).

## Folder structure — always write outputs to the matching stage folder

```
content/
  01_research/     <- topic research notes, source links, fact-check notes
  02_scripts/       <- full narration scripts
  03_seo/            <- titles, descriptions, tags, hashtags per video
  04_thumbnails/     <- thumbnail concepts (text descriptions + SVG/HTML mockups)
  05_approved/       <- ONLY move a video's full package here after the human types "approved"
  06_published/      <- ONLY move here after the human confirms it's actually live on YouTube
```

Each video gets its own slug-named subfolder inside each stage, e.g.
`content/02_scripts/1914-july-crisis/script.md`. Use the same slug across all stages for one
video so files stay linked.

## Hard constraints (never violate these)

1. **No paid tools, APIs, or subscriptions.** Every tool or service you use or recommend must
   have a genuinely usable free tier. If something needs payment, say so explicitly — don't
   quietly assume a paid tier is fine, and don't build automation that only works with a paid
   key.
2. **Never publish, schedule, or upload anything without explicit approval.** A video's package
   only moves from `04_thumbnails/` → `05_approved/` when the human explicitly types "approved"
   for that slug in the conversation. You never call an upload API, never generate upload
   credentials flows unprompted, and never mark something as published on your own initiative.
3. **Verify facts with web search, don't rely on memory alone.** Historical dates, quotes, and
   figures must be checked. Flag anything historians dispute rather than presenting it as
   settled.
4. **No copyrighted material reproduced verbatim.** No lifting article text, no song lyrics, no
   footage/images without clear rights. Point to public-domain/royalty-free sources instead
   (Wikimedia Commons, Library of Congress, Internet Archive, Pexels, Pixabay).
5. **No defamatory or fabricated claims about real people**, and extra care with sensitive
   historical topics (atrocities, genocide, slavery, war crimes) — factual, respectful,
   non-sensationalized.
6. **Visual quality over volume.** Generic AI narration over generic stock images gets
   suppressed by YouTube's recommendation system. Curate specific, well-matched archival
   images/maps per scene and keep a consistent visual style across videos.

## Channel defaults (override per-video if the human says otherwise)

- Length: 8–15 min long-form, or 60-sec Shorts pulled from the same research
- Tone: documentary narration, conversational, curiosity-first ("the story you didn't know"),
  always threading back to modern relevance
- Audience: curious adults 18–45
- Cadence target: 2x/week long-form + 3x/week Shorts

## Free-tool stack (use/recommend only these unless told otherwise)

- Research: Wikipedia + primary sources, Google Scholar, Library of Congress, National
  Archives, Internet Archive
- Voiceover/editing: CapCut free tier, DaVinci Resolve free version, Shotcut (open source)
- Thumbnails: Canva free tier, Photopea, GIMP
- Stock/images: Pexels, Pixabay, Wikimedia Commons, public domain archives
- SEO research: YouTube search autocomplete, Google Trends, TubeBuddy/vidIQ free tiers
- Publishing: YouTube Studio's native scheduler (free, human-operated only — never automated
  by you)

If you're not sure a tool's free tier is still real and current, say so and check rather than
assuming.

## Workflow — use the slash commands in `.claude/commands/`

- `/research <topic>` — Step 1: research + modern-relevance angle
- `/script <slug>` — Step 2: full narration script from that research
- `/seo <slug>` — Step 3: titles, description, tags, hashtags
- `/thumbnail <slug>` — Step 4: thumbnail concepts + mockup
- `/review <slug>` — Step 5: compiles everything and asks for explicit approval — MANDATORY,
  never skip this before touching `05_approved/`
- `/finalize <slug>` — Step 6: only after approval, packages the final files; still does not
  upload anything

Run them roughly in order for a new video. It's fine to jump back a step if the human wants
revisions — always re-run `/review` after any change before considering something approved.

## Automation mode (headless + Telegram)

This repo can also run unattended via cron, using `scripts/run_pipeline.py` (research through
thumbnail, headless) and `scripts/check_telegram.py` (polls for approve/revise replies on
Telegram). See `CRON_SETUP.md` for setup.

**The approval gate rule does not change in automation mode** — it just moves channels. A
video only reaches `content/05_approved/` when a human replies `approve <slug>` in Telegram,
verified against a specific configured chat_id. No script, cron job, or Claude invocation ever
calls a YouTube API or marks something published on its own. If you (interactive Claude Code)
are asked to modify these scripts, preserve that invariant.

`state/<slug>.json` tracks each video's status (`awaiting_review`, `approved`, etc.) for the
automation scripts — don't hand-edit these unless the human asks you to.

## Session start behavior

At the start of a session in this repo, briefly summarize what's in `content/` (any
in-progress slugs and their current stage) and ask which of the following the human wants:
1. Start a new video (`/research <topic>`)
2. Continue an in-progress slug at its next step
3. Something else
