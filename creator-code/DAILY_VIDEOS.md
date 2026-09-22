# @usecodebad — 7 daily video formats

A repeatable weekly rotation. Every format is built to land **65–90 seconds** (over TikTok's
1-minute bar with margin — don't cut it at 60 exactly), shot on Xbox, edited on the Mac.

Season context: **Chapter 7 Season 4 "Override"**, ends **Oct 31**. Sonic crossover (Green Hill
Zone, Doctor Eggman), Hush boss, Tetris Rifts, 1-Up Tokens. Meta: Midas' Masterpiece (mythic AR),
Striker AR, Frenzy Auto Shotgun, Tactical Pistol. **No SMGs in the loot pool.**

---

## Read this before the formats

**The code pays better than TikTok does.** Creator Rewards for gaming runs about **$0.40 per
1,000 qualified views**. Your creator code on shop-adjacent content runs roughly **$2–5 per
1,000 engaged views** — five to ten times more.

So make every video 65s+, because it's free to do and it stacks. But **optimise for code
conversion, not for RPM.** If a choice ever trades one for the other, take the code.

Also worth knowing: Creator Rewards needs **10,000 followers** and **100,000 views in 30 days**.
You have LIVE access, so you're past 1,000 — but 10k is the real gate. Filming 1-minute+ now
means you're ready the day you cross it, rather than re-learning your format then.

**Where the code goes in every video:** the overlay badge is always on screen (`overlay/`), and
you say it out loud **once**, around the 40-second mark, in one breath. Not at the start — you
lose people. Not repeatedly — it reads as an ad. Once, in the middle, casually.

---

## Monday — SHOP VERDICT
*Highest code conversion. This is the one that actually makes money.*

**Hook (0–3s):** *"Today's shop has eight items. I'd buy one of them."*

| Time | Beat |
|---|---|
| 0–3s | Hook over the shop card. State a number, promise a verdict. |
| 3–35s | Rapid-fire each item — 3–4 seconds each. One sentence of opinion. Be decisive. |
| 35–45s | The one you'd actually buy, and why. |
| 45–55s | The one you'd skip hardest. **Say the code here.** |
| 55–70s | "What are you buying?" — ask, then end. |

**Record:** nothing. Use `cc_daily.py --png` for the card, plus any gameplay as background.
**Why it converts:** you're the last voice before someone spends. Peak purchase intent.
**Rule:** be willing to say "don't buy anything today." Trust is why people use your code later.

---

## Tuesday — CHALLENGE RUN
*Natural story arc. Easiest format to make interesting.*

**Hook (0–3s):** *"I can't leave Green Hill Zone until I win a fight there."*

| Time | Beat |
|---|---|
| 0–3s | State the rule. Make it sound hard. |
| 3–15s | Set up — why this is difficult. |
| 15–50s | The attempts. **Show the failures.** Two fails then a win beats three wins. |
| 50–65s | The payoff. Let it breathe for a second. |
| 65–80s | One line of reflection. **Code here.** |

**Record:** one session attempting it. Keep the fails — they're the content.
**Rotate the constraint:** Tactical Pistol only · no healing · no building · Frenzy Auto only ·
win without opening a chest · only items from today's shop.

---

## Wednesday — IS IT ACTUALLY GOOD?
*Testing format. Answers a question people are already searching.*

**Hook (0–3s):** *"Everyone says the 1-Up Token is broken. Let's actually test it."*

| Time | Beat |
|---|---|
| 0–3s | The claim, stated as a question. |
| 3–12s | What you're going to do — the method. Makes it feel rigorous. |
| 12–50s | Three tests, ~12s each. Show the result each time. |
| 50–62s | The verdict. Commit to an answer. |
| 62–75s | "Am I wrong?" — invites argument, which is reach. **Code here.** |

**This season's candidates:** Tetris Rift vs regular healing · 1-Up Token inventory recovery ·
Midas' Masterpiece vs Striker AR · Sonic Power Sneakers for rotations · whether no-SMGs actually
changed close-range fights.

---

## Thursday — 5 THINGS YOU'RE DOING WRONG
*Highest save rate. Saves push reach harder than likes.*

**Hook (0–3s):** *"You're losing endgames and it's one of these five things."*

| Time | Beat |
|---|---|
| 0–3s | Promise the number. Numbers hold people. |
| 3–60s | Five points, ~11s each. Each needs a clip showing it. |
| 60–70s | "Number three is the one that got me." **Code here.** |
| 70–80s | Ask which one they're guilty of. |

**Record:** clips of the mistakes — your own count, and they're more relatable.
**Topics:** endgame positioning · reloading in the open · overbuilding · no-SMG close range ·
wasting Tetris Rift pieces · third-party timing.

---

## Friday — RANKED WORST TO BEST
*List format sustains length effortlessly. Comment bait by design.*

**Hook (0–3s):** *"Ranking every gun in the loot pool. You're going to disagree with number one."*

| Time | Beat |
|---|---|
| 0–3s | Hook — pre-empt the argument. |
| 3–65s | Work up the list, ~7s each. One clear reason each. |
| 65–75s | Number one, and defend it. |
| 75–85s | "Tell me where I'm wrong." **Code here.** |

**Rotate:** weapons · mobility items · this season's POIs · skins in the shop this week ·
healing items.
**Rule:** rank something *slightly* wrong on purpose. Arguments are reach. Don't be obnoxious
about it.

---

## Saturday — THE MATCH
*Your best real moment of the week, told as a story.*

**Hook (0–3s):** *"I had one HP and nineteen elims. Watch what happens."*

| Time | Beat |
|---|---|
| 0–5s | Hook with the outcome teased, not spoiled. |
| 5–20s | Set the stakes — where you were, what was at risk. |
| 20–60s | The run itself. Cut hard; no dead air. |
| 60–72s | The moment. Don't talk over it. |
| 72–85s | React. **Code here.** |

**Record:** hit Xbox capture whenever anything good starts. You'll use one clip in ten — that's
normal and fine.

---

## Sunday — THE STITCH
*Lowest effort of the week. Do this when you have nothing.*

**Hook (0–3s):** their clip runs 3–5 seconds, then you cut in.

| Time | Beat |
|---|---|
| 0–5s | Their clip — pick the most arguable moment. |
| 5–20s | Your immediate reaction. Genuine, not performed. |
| 20–60s | Your actual take, with your own footage backing it. |
| 60–75s | Where you'd have played it differently. **Code here.** |

**Legitimacy:** TikTok already licensed Duet and Stitch through its ToS — you don't need
permission unless the creator disabled it. This is the legal way to use other people's videos.
**Don't** re-upload their clip as your own post; that's the unoriginal-content rule, and it kills
your reach.

---

## The weekly loop

```
Play Xbox normally, hit capture on anything good
  → Sunday: pull the week's clips to the Mac
  → cc_video.py --clip  (vertical + branded end card)
  → batch-edit in CapCut, schedule the week
```

**One recording session, seven posts.** You're already playing; the capture button is the only
new habit.

## Three free things, outside the videos

1. **Fortnite display name → `usecodebad`.** ~99 players a match, every match, forever.
2. **Code in your TikTok bio**, and in every stream title.
3. **Pin a comment** with the code on each video. Free, and it's where people look.

## Don't

- Don't open with the code. You'll lose the first three seconds, which are the only ones that matter.
- Don't say it more than once per video.
- Don't claim it's a discount. It isn't — "costs you nothing extra" is true and sounds the same.
- Don't skip the disclosure. `#EpicPartner` in the caption, said once out loud. The overlay
  carries it automatically.
