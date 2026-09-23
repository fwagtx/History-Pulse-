# Creator Code BAD — Operating Rules

## ⛔ ACCOUNT ISOLATION — read this first

This project touches **@usecodebad ONLY**.

- Metricool brand ID **7066444** — TikTok `usecodebad`, YouTube `UCA9fkJZbLeR5uXTU82Ur74Q`
- Every scheduled post, every analytics call, every account action uses that brand id and no other.
- The account holder has a separate, unrelated venture in the same Metricool account. **Never read
  it, never write to it, never schedule to it, never reference it.** If a task seems to call for
  it, stop and ask instead.
- Before any post is scheduled, confirm the brand id is 7066444. If it is not, do not proceed.

This is not a preference. Treat it as a hard boundary.

These are the guardrails the scripts in `scripts/cc_*.py` are built against. They exist because
**the code is the asset.** A revoked code earns $0 permanently, which is strictly worse than a
slower compliant ramp. Don't trade the asset for a short-term spike.

Epic's Support-A-Creator Terms prohibit **spam, scams, and deceptive practices**, and require
**disclosure** of your commercial relationship with Epic.

---

## Green — automate freely

These touch only channels you own, or your own content.

| Action | Notes |
|---|---|
| Auto-generate unlimited content (cards, Shorts, captions, pages) | Production is never the problem |
| Auto-publish to **your own** YouTube / TikTok / IG / X / Telegram | Your channels, your rules |
| Auto-post to **your own** Discord server and subreddit | Ownership is the distinction |
| Auto-rebuild your own website | GitHub Pages, daily |
| Re-entry reminders to people who **opted in** | The highest-ROI system you have |
| Show the code on every asset you make | Overlays, bios, outros, pinned comments |
| Alert your own channels during 2x/3x boost windows | Free multiplier |
| Run giveaways with clear, honest rules | Keep entry genuinely voluntary |

## Red — never automate, never do

These are the ones that get codes revoked and accounts banned.

| Action | Why not |
|---|---|
| Mass DMs on any platform | Textbook spam; ban on both platform and SAC |
| Comment-spam under other people's videos | Same, and it's the most-reported behaviour there is |
| Posting into Discords/subreddits **you don't own** | Not your space; mods report it, Epic acts on it |
| Bot accounts, sockpuppets, purchased engagement | Deceptive practice; also destroys your analytics |
| Claiming the code is free / gives the buyer a discount | **It does not.** That's a deceptive claim |
| Implying Epic endorses you | False affiliation |
| Hiding the commercial relationship | Epic requires disclosure; so does consumer law in most places |
| Entering your own code on your own purchases | Self-referral |
| Scraping/automating behind a login or against a ToS | Separate legal problem |

## Amber — human judgement required, keep the volume low

- **Creator co-promos** — fine when it's a real relationship, spam when it's a mass template.
- **Answering "what's a good creator code?" threads** — fine occasionally as a genuine
  participant, spam if you automate it or do it constantly.
- **Paid ads** — allowed but costs money, so it's out of scope for this free-tier build.

---

## Mandatory disclosure

Every promotional post needs it: **#EpicPartner**, on screen and in the description. The
generators (`scripts/cc_formats.py`, `scripts/cc_quiz.py`) end every description with
`💚 Creator Code: BAD · #EpicPartner` and keep #EpicPartner on screen for the whole video —
don't strip either out. TikTok posts also carry TikTok's branded-content label.

On 2026-09-23 the owner dropped the longer "I get a commission from purchases made with code
BAD" sentence and the "costs you nothing extra" line from the posts. Don't add them back.

In a filmed script, a short spoken form works: "Use code BAD in the Item Shop — I'm an Epic
partner."

It is **not a discount**. Never imply otherwise.

---

## If something goes wrong

- **Code stops attributing** → check the creator portal first; supporters' codes silently expire
  at 14 days, so a drop is usually expiry, not a ban.
- **Warning from Epic** → stop the relevant automation immediately, keep the rest running.
- **Platform strike** → that channel's automation pauses until resolved; don't migrate the same
  behaviour to another platform.
