# The code-entry card

Item-shop YouTubers show a small card when they ask people to use their Support-A-Creator
code. It has a **CREATOR CODE** heading and a white box where the code is typed in letter by
letter. **#EpicPartner** sits under the box, and an **Accept** button appears once the code is
in. `scripts/cc_code_entry.py` draws that card from scratch with **BAD** typed in. It uses the
same engine as the daily videos.

The reference was I Talk's item-shop video of Sep 26, 2026 (youtu.be/OCF2uF2yJ9s), at its
start and end. Nothing from that video is reused. Its colours and proportions were measured
off the frames and the card was rebuilt:
- **Anton** stands in for Fortnite's heading font. It is widened 14%, and each letter gets a
  small tilt for the hand-cut look.
- **Liberation Sans** (a free Arial twin, `assets/fonts/LiberationSans-OFL.txt`) sets the text
  box and the button.

## In every video

The owner picked the **lime 16:9** version. Every daily video now ends on it: shop and quiz, all
formats and all looks (see `LOOKS.md`). It is sized for the vertical frame, beside the button
rail and under the corner badge, which stays on screen. `scripts/cc_end_card.py` adds it.

## The two looks

| Look | What it does |
|---|---|
| **classic** | The card as those videos show it: navy heading bar, white box, grey Accept button. The code is typed in and the card holds. |
| **lime** | The channel's colours: a lime ring around the box and a lime Accept button. A pointer clicks Accept, and the card turns into the **SUPPORT-A-CREATOR: BAD** confirmation, which is what the shop's own button reads once the code is in. |

## The files

Each look comes in two sizes:
- **16:9** (1920x1080): the card pops in over a blurred wall of item-shop tiles and pops out
  again, about 5–6 s. It also comes as overlays, to put the card over your own footage:
  - green screen (`-green.mp4`): any editor's chroma key, including CapCut's
  - transparent QuickTime (`-alpha.mov`): DaVinci Resolve, Premiere, Final Cut
  - transparent WebM (`-alpha.webm`): OBS
  - transparent PNG stills of each step
- **9:16** (1080x1920), for Shorts, Reels and TikTok: the card sits across the top of the safe
  box, with the three steps to use the code under it:
  1. Open the Item Shop
  2. Select SUPPORT-A-CREATOR
  3. Type BAD and confirm

  The safe-zone check passes, so no app's buttons or captions cover anything.

Every video has typing sounds. The stills are named after the step they show: `empty`, `B`,
`BA`, `BAD`, `accept` and `done`. `contact-sheet.jpg` shows them all side by side.

A copy of the finished files is kept in `creator-code/brand/code-entry/`: the four previews,
the green-screen and WebM overlays, the transparent stills of the final steps and the contact
sheet. The transparent `.mov` files are too big to keep in the repo. Render them again with the
command below.

## Making them again

```
python3 scripts/cc_code_entry.py --art <folder of cosmetic cut-outs with meta.json> --check
```

The files are written to `creator-code/out/code-entry/`. The options are:
- `--looks classic,lime` and `--sizes 16x9,9x16` pick the versions.
- `--no-overlays` skips the green-screen and transparent files.
- `--code` changes the code.

Without `--art`, the backdrop is plain rarity-coloured tiles.

The rules are the same as for every video: #EpicPartner is always on the card or under the
confirmation, and nothing says "discount".
