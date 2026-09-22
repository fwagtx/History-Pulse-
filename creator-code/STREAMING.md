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

### You play on PS5/Xbox and have a Mac → use Remote Play, no capture card
1. Install **PS Remote Play** (or the Xbox app) on the Mac — free
2. Stream the console to the Mac
3. Install **OBS** (free), capture the Remote Play window
4. Get your Server URL + Stream Key from **livecenter.tiktok.com/producer**
5. Paste both into OBS → Settings → Stream → Custom

Some input lag, but it costs nothing and needs no extra hardware.

### You play on console and want best quality → capture card
Console → capture card → computer → OBS/LIVE Studio.
**Cost flag: a capture card is $30–100.** A real purchase, not free. Only worth it once
streaming is already working for you via Remote Play.

### Mac, no console
Fortnite doesn't run on macOS, so there's no gameplay to stream from the Mac itself.

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
- **Say it naturally, occasionally.** "Code BAD if you're shopping, costs you nothing" — once
  every 20 minutes or so, not every two minutes.
- **Rename your Fortnite display name to `usecodebad`.** ~99 players see it every match whether
  you're streaming or not. Passive, permanent, free.
- **Record locally while you stream** (OBS does this in one click) so you have footage to clip.
