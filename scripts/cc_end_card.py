"""
The end card every video finishes on.

After a video's own ending, the CREATOR CODE card in the channel's lime
(cc_code_entry's "lime" look, the one the owner picked) pops in over a blurred
wall of the video's own cosmetics. BAD is typed in, a pointer clicks Accept,
and the card turns into SUPPORT-A-CREATOR: BAD with #EpicPartner. The lime
USE CODE: BAD badge stays in its corner the whole time, end card included.

finish(make, ctx) builds a video with make(ctx) and adds the card: LENGTH
seconds more, crossfading over the last .3 s of the old ending. Every build
(cc_build, cc_quiz_build, cc_look_preview) goes through it, so the safe-zone
check (cc_safe.gate) sees the card too. CC_END_CARD=0 leaves it off.
"""

import dataclasses
import os

import cc_code_entry as CE
from cc_common import log
from cc_motion import (BADGE_H, BADGE_Y, H, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, W, code_badge,
                       disclosure)

CODE = "BAD"
LENGTH = 5.1                # seconds the card adds to a video
FADE = .3                   # crossfade over the old ending
MAX_SECONDS = 90.0          # Facebook Reels
WALL_PICTURES = 5           # the video's cosmetics on the backdrop; each is embedded once

# Beside the button rail (x 60-900), centred between the corner badge with its
# #EpicPartner line (down to y ~350) and the caption zone (y 1420).
CARD_X = SAFE_LEFT
K = (SAFE_RIGHT - SAFE_LEFT) / CE.CARD_W
_TOP = BADGE_Y + BADGE_H + 34
CARD_Y = round((_TOP + SAFE_BOTTOM) / 2 - CE.CARD_H * K / 2)
FIELD_PX = 76               # the typed code: 50 px on screen, a little bigger than on the 16:9 card
PILL_SCALE = .8             # SUPPORT-A-CREATOR: BAD, 46 px, fits beside the rail


def finish(make, ctx, code: str = CODE):
    """make(ctx) -> Video or None, with the end card added. The cosmetics the
    video asks ctx.art for become the backdrop."""
    seen = {}
    real = ctx.art

    def art(item):
        uri = real(item)
        if uri and uri not in seen:
            seen[uri] = item.get("rarity", "") if isinstance(item, dict) else ""
        return uri

    video = make(dataclasses.replace(ctx, art=art))
    if video is None or os.environ.get("CC_END_CARD", "1") == "0":
        return video
    return add(video, list(seen.items())[:WALL_PICTURES], code)


def timeline(start: float, end: float, code: str = CODE) -> dict:
    """When everything happens (cc_code_entry.timeline's keys), for a card that
    starts fading in at `start` and holds its confirmation until `end`."""
    t = {"card": start + .35}
    t["keys"] = [round(start + 1.05 + i * .24, 3) for i in range(len(code))]
    t["accept"] = t["keys"][-1] + .42
    t["click"] = t["accept"] + 1.1
    t["done"] = t["click"] + .22
    t["pill"] = t["done"] + .22
    t["out"] = t["end"] = end           # holds to the last frame
    return t


def add(video, arts: list, code: str = CODE):
    """Add the end card after the video's current ending."""
    comp = video.comp
    old_end = comp.duration
    if old_end + LENGTH > MAX_SECONDS:
        log(f"  end card left off: {old_end:.1f}s + {LENGTH}s would pass {MAX_SECONDS:.0f}s")
        return video
    start = old_end - FADE
    # Scenes already placed keep their own timing; everything they show is gone
    # by old_end. The card is a new scene over all of them.
    comp.duration = round(old_end + LENGTH, 3)
    t = timeline(start, comp.duration, code)
    comp.use_fonts("Liberation Sans")
    comp.css(CE.CSS)
    L = CE.LOOKS["lime"]
    cx, cy = CARD_X + CE.CARD_W * K / 2, CARD_Y + CE.CARD_H * K / 2
    inner = (CE.shop_wall(comp, W, H, arts)
             + CE.card(L, code, t, CARD_X, CARD_Y, K, shadow=True, collapse=True, field_px=FIELD_PX)
             + CE.confirmation(code, t, cx, cy, PILL_SCALE, True, True)
             # The same corner badge the classic videos carry from frame 0, so the
             # code stays on screen through the card whatever look the video had.
             + code_badge() + disclosure())
    comp.scene(start, comp.duration, f'<div class="full">{inner}</div>', fade_in=FADE, fade_out=.01, z=100)

    comp.cue(t["card"], "pop")
    for key in t["keys"]:
        comp.cue(key, "tick")
    comp.cue(t["accept"], "pop")
    comp.cue(t["click"], "click")
    comp.cue(t["pill"], "ding")
    return video
