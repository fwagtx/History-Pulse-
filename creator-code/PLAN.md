# Creator Code "BAD" — Automated Promotion Plan

Goal: get the maximum number of people entering creator code **BAD**, using only free tools,
with as much of the machine running unattended as the platforms legally allow.

> Scope note: this lives in the History Pulse repo but is a **separate venture**. It reuses the
> repo's proven patterns (stdlib-only Python, `config.json`, cron, Telegram approval gate) but
> writes to `creator-code/`, never to `content/`. The History Pulse pipeline is untouched.

---

## 1. The numbers you're actually playing for

Verified against Epic's program terms (sources at the bottom). Read this before building
anything — it sets the required scale.

| Fact | Value | Why it matters |
|---|---|---|
| Commission | **5%** — $5.00 per 10,000 V-Bucks | You need **$20,000** of attributed spend per **$1,000** of income |
| Payout minimum | **$100 in a rolling 12 months** | Below it you are paid **nothing** |
| Minimum reset | Unmet balance **resets to zero** every 12 months | A slow trickle can earn you $0 forever |
| Code lifetime | **14 days**, then expires | Supporters must **re-enter** — this is the whole game |
| Payment | Monthly via Hyperwallet, ~30 days after period close | Plan cashflow accordingly |
| Boost windows | Epic runs 2x/3x rev-share events | Free multiplier if you're watching for them |

### The funnel, with realistic conversion

Per 1,000 *engaged* views (someone who watched, not a scroll-past):

```
1,000 views
  → ~1–3% act on the code            = 10–30 entries
  → ~30% of those buy in the window  = 3–9 purchases
  → ~$12 average purchase            = $36–108 attributed spend
  → × 5%                             = $1.80–$5.40
```

**≈ $2–5 per 1,000 engaged views.** That's competitive with gaming ad RPM, and it *stacks* on
top of ad revenue rather than replacing it.

**So: ~200k–500k views/month ≈ ~$1,000/month.** That is the honest bar. Any plan that doesn't
put real view volume through the funnel is a plan to earn $0 and have it reset annually.

### The lever everyone ignores

One supporter who re-enters every 14 days for a year is worth **26 windows**, not one. Even a
20% re-entry rate multiplies lifetime value roughly **5x**.

Chasing new eyeballs is expensive and competitive. Reminding people who *already used your code*
is nearly free and converts far better. **The re-entry reminder system is the highest-ROI thing
in this entire document.** Build it first, not last.

---

## 2. Why "BAD" is a real asset

This is genuine, and it's the strategic foundation — not a vanity observation.

Almost every creator code is an unmemorable username (`ninja_ttv_2019`). "BAD" is:

- **Three letters, one syllable, zero ambiguity.** Nobody mishears it or misspells it. The gap
  between "they saw it" and "they typed it" is where creator codes die, and BAD has almost no gap.
- **Imperative-ready.** "Use code BAD" is already a sentence. "Be BAD." "Buy it BAD." "Support a
  BAD creator." It's a slogan you don't have to invent.
- **Chantable and printable.** Works as an overlay, a merch print, a bio line, an outro card, a
  Discord role, a pinned comment.
- **Brand-first, not person-first.** This is the key one for automation: a code tied to *a
  personality* needs that personality to show up on camera daily. A code tied to a *word* does
  not. **BAD can be a faceless brand**, which is precisely what makes the pipeline automatable.

**Strategic consequence:** build the brand around the word, not around you. Consistent black/acid
-yellow visual identity, the word BAD huge on every asset, same handle everywhere. You are
building a recognizable stamp that can be applied automatically to unlimited content.

The one weakness: "bad" is a generic English word, so it's near-impossible to *search* for.
Never rely on someone googling "BAD creator code" to find you — always pair it with a
qualifier you control (`@badshop`, `badcode.gg`, "code BAD in the item shop").

---

## 3. The one rule that keeps the money

Epic's Support-A-Creator Terms **explicitly prohibit spam, scams, and deceptive practices**, and
separately **require you to disclose** that you have Creator terms with Epic and can receive
payouts.

This is not a footnote. Mass DMs, comment-spam under other people's videos, bot accounts,
auto-posting into Discords you don't own, and engagement farms are the fastest route to having
the code revoked — and the code *is* the asset. A banned code earns $0 forever, which makes it
strictly worse than a slow, compliant ramp.

**The operating principle for this whole build:**

> **Automate the machine, not the spam.**
> Fully automate production, publishing, and reminders **on channels you own**.
> Keep anything that touches *other people's* spaces human-approved and low-volume.

What that buys you is still enormous: unlimited daily content, unattended publishing to your own
channels, a compounding SEO surface, and an automated retention loop. See `RULES.md` for the
precise green/red line list the scripts are built against.

Every caption template in `scripts/cc_captions.py` emits the disclosure line automatically, so
you cannot forget it.

---

## 4. Channel strategy

Ranked by leverage. Do them in this order.

### Tier 1 — Owned + fully automatable (build these)

**A. Daily "Item Shop Today" Shorts — the engine**

The single best free-distribution opportunity here. The Fortnite item shop refreshes **every day,
forever**, and "fortnite item shop today" carries recurring search demand every single day. That
is a permanent, renewable content well that requires no creativity to fill.

- Fetch shop → render branded card → 20–40s Short → auto-upload.
- YouTube's `videos.insert` now bills **1 unit/call, 100 calls/day** (changed June 2026, down
  from 1,600 units). Daily auto-upload is now genuinely free and viable — this was the blocker
  until recently.
- Every frame carries `CODE: BAD`. Purchase intent is *already high* on a shop video — this is the
  moment of maximum conversion, which is why this beats generic gaming content by a wide margin.

**B. The 14-day re-entry reminder loop — the money**

Build a list you own (Discord + Telegram), then remind it on a 14-day cycle.

- Discord server with a bot: daily shop post, `/code` slash command, a 14-day re-entry ping.
- Telegram channel mirroring it.
- This is the one system that compounds. Everything else is top-of-funnel; this is retention.

**C. A static SEO site on GitHub Pages**

Free hosting, and it compounds while you sleep.

- Auto-generated daily: today's shop page, one page per cosmetic, historical shop archive.
- Plus evergreen: "how to use a Fortnite creator code", "why did my creator code expire".
- Thousands of long-tail pages, each carrying the code. Search traffic is the closest thing to
  free money in this plan because it arrives with intent.
- **Cost flag:** `*.github.io` is free. A custom domain (`badcode.gg`) is **~$10–15/year — a real
  cost, not free.** Start on the free subdomain; only buy a domain once revenue justifies it.

**D. Your own subreddit + X/Telegram mirrors**

Automated posting to a subreddit *you own* is fine. Posting across subreddits you don't is the
spam line. X's free API tier allows a limited posting volume (currently ~500 posts/month) —
enough for daily, not for spam.

### Tier 2 — Produce automatically, publish semi-manually

- **TikTok:** the Content Posting API keeps all posts **private-only until your app passes an
  audit**. So: auto-*generate* the video and caption, upload by hand until audited. Don't let this
  block you.
- **Instagram Reels:** needs a Business account + Graph API. Same pattern.

### Tier 3 — Manual, high-value, never automated

- Co-promo with other small creators (offer genuine value, not code swaps).
- Answering real questions in communities as a participant, not a poster.

---

## 5. Build sequence

Each phase is independently useful — you're never waiting on the whole thing to work.

### Phase 0 — Foundation (day 1)
- [ ] Confirm the code **BAD** is actually issued to you and active in the creator portal.
- [ ] Set up Hyperwallet payout so you're not blocked at the $100 threshold.
- [ ] Lock the brand: black + acid yellow, the word BAD, one handle across all platforms.
- [ ] `cp creator-code/config.example.json creator-code/config.json` and fill it in.

### Phase 1 — The daily engine (week 1) ✅ scaffolded in this branch
- [x] `cc_shop.py` — fetch + normalize the item shop
- [x] `cc_render.py` — branded SVG/HTML card, PNG via headless Chromium
- [x] `cc_captions.py` — per-platform titles/captions/hashtags, disclosure baked in
- [x] `cc_daily.py` — orchestrator, writes a dated publish queue + Telegram ping
- [ ] Add your free `fortnite-api.com` key, run it, eyeball the output
- [ ] Wire the cron job (see `CRON.md`)

### Phase 2 — Retention (week 2) ✅ scaffolded in this branch
- [x] `cc_remind.py` — 14-day re-entry reminder scheduler
- [ ] Create the Discord server + bot, point the reminders at it
- [ ] Add the `/code` command and a pinned "how to enter BAD" message

### Phase 3 — Publishing automation (weeks 2–4)
- [ ] YouTube OAuth + `videos.insert` auto-upload (100/day free — this is the unlock)
- [ ] Telegram channel auto-post
- [ ] X free-tier auto-post
- [ ] TikTok/IG: generate automatically, upload manually until audited

### Phase 4 — Compounding SEO (weeks 3–8)
- [ ] Static site generator → GitHub Pages, daily rebuild from the same shop data
- [ ] Evergreen guides, especially "why did my creator code expire" (captures re-entry intent)

### Phase 5 — Optimize (ongoing)
- [ ] **Shop history tracking** (`shop_history.json`): append each day's item IDs, so you can
      compute *true* "first time in N days" hooks. Right now the caption hooks deliberately
      avoid "is BACK" / "RETURNS" claims because we can't verify them — once history has
      accumulated, those become accurate *and* they're among the strongest hooks available.
      This is the highest-value content upgrade after Phase 3.
- [ ] Epic's portal has no public stats API — export CSV monthly, track per-channel conversion
- [ ] Alerting on 2x/3x rev-share windows; blast owned channels when they open
- [ ] Double down on whichever channel shows the best entries-per-view

---

## 6. What "fully automated" honestly means here

Being straight with you, because the difference matters for what you should expect:

**Genuinely unattended once built:** shop fetching, card/video generation, caption and hashtag
writing, YouTube upload, site rebuild, Discord/Telegram posting, re-entry reminders, boost-window
alerts. That's the large majority of the daily labour, and it's real.

**Needs a human, by platform rule or by law:** TikTok/IG publishing until audited, the disclosure
being accurate, partnership outreach, and any judgement call about whether a post is promotion or
spam.

**Also worth knowing:** cron needs a machine that is actually powered on — same caveat as the
History Pulse pipeline. A spare always-on box, or a free-tier GitHub Actions scheduled workflow,
covers it.

The honest summary: you can automate ~85% of the *work*, but the growth still depends on the
content being good enough that people watch it. **Automation removes the labour, not the need for
quality.** A daily shop Short that looks sharp and loads fast will beat a thousand spam comments,
and it won't get your code revoked.

---

## Sources

- [Support-A-Creator Terms — Epic Games](https://sac.epicgames.com/eula/sac/?lang=en-US)
- [Support-A-Creator overview](https://sac.epicgames.com/overview)
- [When will I receive my payout awards? — Epic](https://www.epicgames.com/help/c-34406160/c-32910640/a17142000?lang=en-US)
- [Support-A-Creator — Fortnite Wiki](https://fortnite.fandom.com/wiki/Support-A-Creator) (14-day expiry)
- [Epic's Support-A-Creator pays 5% — AppleInsider](https://appleinsider.com/articles/22/06/27/epics-support-a-creator-program-pays-out-only-5-of-game-content-makers-sales)
- [Is the YouTube API free in 2026? — Phyllo](https://www.getphyllo.com/post/is-the-youtube-api-free-in-2026-quota-limits-costs-when-to-pay) (videos.insert quota change)
- [TikTok Content Posting API — Get Started](https://developers.tiktok.com/docs/en/content-posting-api-get-started) (audit requirement)
- [Fortnite-API — free REST API](https://fortnite-api.com/)
