# Going live on TikTok — the efficient play

You already have LIVE access, which makes this the best use of your time. Here's why,
then how.

## Why streaming beats making shorts

It's counterintuitive, but **streaming is less work than edited short-form**:

- No editing, no captions, no thumbnails, no hook-writing. You just play.
- A 2-hour stream is **2 hours of continuous code exposure**. A 20-second clip is 20 seconds.
- TikTok's LIVE tab is a **discovery surface** — people who don't follow you get shown it.
- Live viewers are the most engaged audience you can get. Engaged viewers actually enter codes.

**And the real unlock: clip the stream afterward.** One session of playing — something you'd
do anyway — produces the live exposure *and* a week of short-form clips. One activity, two
outputs. That's the efficiency problem solved, legitimately.

Bad news up front, so you don't waste time on it: **24/7 unattended "looping live" is banned.**
TikTok's 2026 rules explicitly prohibit blank screens, static images, and pre-recorded video
looping for extended periods, enforced with content removal and account bans. Live has to be
actually live.

---

## Setup, by what you play on

### You play on a Windows PC → easiest
Install **TikTok LIVE Studio** (Windows 10/11 only, free, official). It authenticates your
account and handles everything. Lowest friction by far.

### Xbox + Mac — your setup. Three routes, pick by what you're optimising for.

**Route A — Xbox clips → Mac (free, best gameplay feel, no live)**
Your Xbox records clips natively. No lag, no cost, no extra gear, and you play normally on
your TV.
1. Record clips on Xbox as you play (guide button → capture)
2. They sync to your Xbox account; grab them on the Mac via the Xbox web app or OneDrive
3. `python3 scripts/cc_video.py --clip thatclip.mp4` → vertical + branded end card
4. Post

**Start here.** It's free, gameplay quality is unaffected, and it gets content flowing this
week. You lose live, that's the only trade.

**Route B — Xbox Remote Play → Mac → TikTok LIVE (free, enables live, some lag)**
There's no Xbox app for macOS, but Microsoft moved Remote Play to a web app:
1. On the Mac, open **xbox.com/play** in Safari or Chrome, sign in, install it as a web app
2. Start Remote Play to your own Xbox (up to 1080p)
3. **OBS** (free, Mac native) → capture that browser window
4. Stream Key + Server URL from **livecenter.tiktok.com/producer** → OBS → Settings → Stream
5. Canvas **1080×1920 vertical**

**Honest caveat:** Remote Play adds input lag, and Fortnite is a shooter. Your aim will feel
worse than playing straight to the TV. Fine for casual/creative modes, rough for ranked. Good
for *testing* whether live is worth it to you — at zero cost.

**Route C — capture card (best of both, costs money)**
Xbox → HDMI → capture card → Mac → OBS. You play directly on the Xbox with zero added lag,
and the Mac gets a clean feed.
**Cost flag: $30–100.** Only buy one once Route A or B has shown you this is worth investing in.

### Bonus: Fortnite runs on the Mac itself, sort of
Fortnite is free on **Xbox Cloud Gaming** at xbox.com/play — no Game Pass needed, just a free
Microsoft account, in a browser on the Mac. **Free tier caps sessions at one hour**, then you
requeue. Not a main setup, but it means you can play on the Mac in a pinch.

---

## Two gotchas that catch everyone

**1. Set your canvas to 1080×1920 — vertical.**
Not 1920×1080. TikTok expects vertical input. Get this wrong and your stream is a tiny
letterboxed strip. In OBS: Settings → Video → set both Base and Output resolution.

**2. Stream keys expire after every session.**
If OBS won't connect, that's almost always why. Go back to LIVE Center and generate a new one.
Not a bug — expect to do it each time.

---

## The overlay

`creator-code/overlay/obs_overlay.html` — drop it into OBS as a **Browser Source**:

1. Sources → + → Browser
2. Tick **Local file**, choose `obs_overlay.html`
3. Set Width **1080**, Height **1920**
4. Drag it above your gameplay source

You get a persistent corner badge with the code, plus a lower-third that sweeps in for about
7 seconds every 45 — present without nagging. The disclosure line is built into the banner, so
you stay compliant with Epic's disclosure requirement without thinking about it.

Positions dodge TikTok's own UI: the badge sits below the top bar, the banner above the comment
feed. If your region's layout differs, adjust `top` on `.badge` and `bottom` on `.banner`.

To change the code or wording, edit the text at the bottom of the file — no code knowledge needed.

---

## Do this on stream

- **Put the code in the stream title.** Free, permanent, seen in the LIVE tab before anyone clicks.
- **Say it naturally, occasionally.** "Code BAD if you're shopping, I'm an Epic partner" — once
  every 20 minutes or so, not every two minutes.
- **Rename your Fortnite display name to `usecodebad`.** ~99 players see it every match whether
  you're streaming or not. Passive, permanent, free.
- **Record locally while you stream** (OBS does this in one click) so you have footage to clip.
