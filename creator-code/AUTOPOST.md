# Automated posting for @usecodebad — Upload-Post setup

**Goal:** Claude schedules posts to `usecodebad` directly, completely separate from StreakPros.

---

## Do this (about 10 minutes)

### 1. Sign up — free, no card
Go to **upload-post.com** and create an account. The free plan gives you 10 uploads a month
and 2 profiles.

### 2. Connect YouTube first
Add a profile for `usecodebad` and connect your **YouTube** channel.

Start with YouTube on purpose — it works on the **free** plan, so you can prove the whole setup
works before paying for anything.

### 3. Add it to Claude
Go to **claude.ai/customize/connectors** → **Add custom connector**.

Get the server URL from **upload-post.com/mcp**, paste it in, name it `Upload-Post`.

When it asks how to sign in, choose the **OAuth / sign-in** option rather than pasting an API
key — Claude opens their login page and handles it for you. Less to get wrong.

### 4. Start a NEW chat
Connectors only load when a conversation starts. The existing one won't see it.

Say: **"Upload-Post is connected"** and Claude takes over from there.

---

## TikTok costs money — but wait until YouTube works

TikTok posting is **not** on the free plan. It needs a paid plan: **$16/month billed annually**,
or $24/month monthly.

This is true of every option — Metricool, Postiz, PostFast, all of them. TikTok requires these
services to be approved API partners, and that cost lands in their paid tiers. There is no free
automated TikTok posting anywhere.

**So: get YouTube working free first.** Once you've seen a post actually go out on schedule,
upgrade for TikTok. Don't pay for something unproven.

---

## Keeping it separate from StreakPros

Simple: **only `usecodebad` goes in Upload-Post.** StreakPros stays in Metricool.

Different services, different logins. There's no mechanism for a post to cross over — cleaner
than managing two brands inside one tool.

---

## What still needs solving

Upload-Post needs the video as a **public link** — it can't reach a file on your Mac. A shared
Google Drive folder is the likely answer, since Drive is already connected here.

Not a blocker. We'll sort it once the connector is live.

---

## Cost comparison, for the record

| Service | Cheapest plan with TikTok |
|---|---|
| **Upload-Post** | **$16/mo** (annual) — cheapest |
| Metricool | €16/mo |
| Postiz | $29/mo |

All three do the same job. Upload-Post wins on price and has a free tier you can test with.
