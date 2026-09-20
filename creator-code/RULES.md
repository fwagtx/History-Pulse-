# Creator Code BAD — Operating Rules

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

Every promotional post needs it. `scripts/cc_captions.py` appends this automatically — don't
strip it out.

> `#EpicPartner — I get a commission from purchases made with code BAD.`

Say it in the video too, not just the description. Short forms that work:
- "Use code BAD in the item shop — I get a cut, costs you nothing extra."
- "#EpicPartner"

Note the honest framing: it costs the buyer nothing extra, but it is **not a discount**. Never
imply otherwise.

---

## If something goes wrong

- **Code stops attributing** → check the creator portal first; supporters' codes silently expire
  at 14 days, so a drop is usually expiry, not a ban.
- **Warning from Epic** → stop the relevant automation immediately, keep the rest running.
- **Platform strike** → that channel's automation pauses until resolved; don't migrate the same
  behaviour to another platform.
