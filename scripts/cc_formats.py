"""
Video formats for @usecodebad -- three posts a day, all generated from the day's
real shop data.

    Slot 1 (morning)   Shop Recap           every day
    Slot 2 (midday)    INTERACTIVE          rotates: This or That / Guess the Price /
                                            Which Costs More / Cop or Drop
    Slot 3 (afternoon) VALUE / URGENCY      rotates: Last Chance / Bundle Math /
                                            OG Check / New This Week

Truthfulness is a hard rule, not a style choice. Every claim on screen or in a
caption comes straight from the shop data:
  - "leaving at the next reset"  <- outDate is today's shop day
  - "added Sep 22"                <- inDate
  - "introduced Chapter 2 S3"    <- the cosmetic's introduction field
  - "save 5,800"                  <- Epic's own regular vs final price
We never claim what "most people picked", never rate an item on our behalf, and
never say an item is "back" (we have no reliable history for that).

Each builder returns a Video, or None when the day's data can't support it
honestly (e.g. fewer than 4 items leaving) -- the slot then falls back.
"""

import random
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from cc_motion import (ACCENT, INK, RARITY, W, H, SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT, RAIL_TOP, Comp, an, burst,
                       anton_em, character, code_badge, countdown, disclosure, esc, label, price_roll,
                       progress, sticker, style_anim, tile_bg, words, EASE_BACK)

MIN_SECONDS = 62.0      # over TikTok's 1-minute Creator Rewards bar, with margin
DISCLOSE = "#EpicPartner — I get a commission from purchases made with code BAD."
CODE_CREDIT = "💚 Creator Code: BAD"
# TikTok's API takes captions up to 2,200 UTF-16 units (an emoji counts as 2);
# YouTube descriptions allow 5,000. Stay under the smaller with room to spare.
CAPTION_MAX = 2150


@dataclass
class Video:
    format: str
    comp: Comp
    title: str              # short, for TikTok's title field
    yt_title: str           # <= 100 chars, for YouTube
    caption: str            # full caption, disclosure included
    hashtags: list = field(default_factory=list)


@dataclass
class Ctx:
    shop: dict
    art: callable           # art(item) -> data URI, or '' when unavailable
    day: date               # the shop day (UTC)
    seed: int

    @property
    def day_label(self) -> str:
        """The video's date, in full: "September 23, 2026"."""
        return self.day.strftime("%B %-d, %Y")

    @property
    def day_short(self) -> str:
        """For tight spots only: "Sep 23"."""
        return self.day.strftime("%b %-d")

    @property
    def reset_et(self) -> str:
        """When today's shop rotates, in US Eastern -- the reference time US
        Fortnite players know. Computed, so DST is always right."""
        from zoneinfo import ZoneInfo
        reset = datetime(self.day.year, self.day.month, self.day.day, tzinfo=timezone.utc) + timedelta(days=1)
        return reset.astimezone(ZoneInfo("America/New_York")).strftime("%-I %p ET").replace(" 0", " ")


# ------------------------------------------------------------------ helpers

def _tag(s: str) -> str:
    """A hashtag-safe slug. Bundle names like 'Kingdom Hearts (19 items)' used to
    produce '#kingdomhearts(19items)', which TikTok breaks at the bracket."""
    s = re.sub(r"\([^)]*\)", "", s)          # "Kingdom Hearts (19 items)" -> "Kingdom Hearts"
    out = "".join(ch for ch in s.lower() if ch.isalnum())
    return out[:28]


# Our own tags go on EVERY post, first, and are never trimmed -- building volume
# on them is how people find the account by searching the code.
BRAND_TAGS = ["usecodebad", "creatorcodebad", "codebad"]
TOPIC_TAGS = ["fortnite", "fortniteitemshop", "itemshop", "fortnitebr"]


def _hashtags(*extra) -> list:
    """Brand tags always, then topic tags, then up to 3 item-specific tags."""
    seen, out = set(BRAND_TAGS), list(BRAND_TAGS)
    specific = []
    for t in extra:
        t = _tag(t)
        if t and t not in seen:
            seen.add(t)
            specific.append(t)
    for t in TOPIC_TAGS:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out + specific[:3]


def _u16(s: str) -> int:
    """Length the way TikTok counts it: UTF-16 units, so an emoji is 2."""
    return len(s.encode("utf-16-le")) // 2


KEYCAPS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def num(k: int) -> str:
    """1️⃣ .. 🔟 for list numbers, plain "11." after that."""
    return KEYCAPS[k - 1] if 1 <= k <= len(KEYCAPS) else f"{k}."


def _caption(hook: str, body: str, ask: str, tags: list) -> str:
    """Every post's description, one layout for all formats:

        <hook: what it is + the full date>      <- all TikTok shows before "more"
        <body: short lines, one item per line>
        💬 <the ask>
        💚 Creator Code: BAD
        #EpicPartner disclosure
        #hashtags

    Blank lines between the blocks. If it's ever too long, whole lines drop from
    the end of the body -- never the ask, the code, the disclosure or the tags."""
    ask = ask if ask.startswith("💬") else f"💬 {ask}"
    foot = f"{CODE_CREDIT}\n{DISCLOSE}\n\n" + " ".join("#" + t for t in tags)
    lines = [ln.rstrip() for ln in body.strip().split("\n")]

    def build(ls, cut):
        b = "\n".join(ls) + ("\n…and more in the video 🎥" if cut else "")
        text = f"{hook.strip()}\n\n{b}\n\n{ask}\n\n{foot}"
        return re.sub(r"\n{3,}", "\n\n", text)

    text, cut = build(lines, False), False
    while _u16(text) > CAPTION_MAX and len(lines) > 1:
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()
        cut = True
        text = build(lines, cut)
    return text


def singles(ctx: Ctx, need_art: bool = True) -> list:
    rows = [i for i in ctx.shop["items"] if not i["is_bundle"] and i.get("price")]
    if need_art:
        with_art = [i for i in rows if ctx.art(i)]
        if with_art:
            return with_art
    return rows


def bundles(ctx: Ctx) -> list:
    return [i for i in ctx.shop["items"] if i["is_bundle"]]


def rng(ctx: Ctx, salt: int) -> random.Random:
    return random.Random(ctx.seed * 1000 + salt)


def _pad(content_end: float) -> float:
    """Outro length that brings the video to at least MIN_SECONDS."""
    return max(7.5, MIN_SECONDS - content_end)


# The hook's beats. Every format cues its opening sounds at these times (whoosh
# .15 and .3, slam .2, pop .9), so the motion lands on the sound.
HOOK_WHOOSH_A, HOOK_SLAM, HOOK_WHOOSH_B, HOOK_POP, HOOK_SUB = .15, .2, .3, .9, 1.1


# The CREATOR CODE stamp. Measured in the render browser with the embedded
# fonts: the stamp is 408x123 px, the corner badge (code_badge) 181x60.
STAMP_X, STAMP_Y, STAMP_ROT = 60, 590, 3
STAMP_TO_BADGE = 181 / 408


def _code_stamp(comp: Comp, end: float) -> str:
    """CREATOR CODE BAD, big, in the gap between the title and the cosmetics.

    It's the thing the whole account exists to sell, so on the thumbnail it
    gets real size: BAD at 112px on a lime block. Near the end of the hook it
    shrinks and flies into the top-left corner, and the small corner badge that
    stays up for the rest of the video takes over as it lands."""
    dock_end = min(2.6, end - .7)          # clear of the first scene's wipe at 2.7s
    dock_start = dock_end - .5
    dock = comp.uid("dock")
    comp.css(f"@keyframes {dock}{{0%{{transform:rotate({STAMP_ROT}deg);opacity:1}}55%{{opacity:1}}"
             f"100%{{transform:translate({48 - STAMP_X}px,{SAFE_TOP - STAMP_Y}px) "
             f"scale({STAMP_TO_BADGE:.3f}) rotate(0deg);opacity:0}}}}")
    # The corner badge waits until the stamp gets there.
    # ("paused" like every animation: the renderer moves them, real time never does)
    comp.css(f".codebadge{{animation:fadein .15s linear {dock_end - .12:.3f}s both paused !important}}")
    comp.cue(dock_start, "whoosh")
    beats = style_anim(an("thump", HOOK_SLAM, .4, fill="none"),
                       an("pulse", 1.5, .5, "ease-in-out", fill="none"))
    return (f'<div class="abs" style="left:{STAMP_X}px;top:{STAMP_Y}px;transform-origin:0 0;z-index:5;'
            f'{style_anim(an(dock, dock_start, dock_end - dock_start, "cubic-bezier(.6,0,.4,1)"))}">'
            f'<div style="{beats}">'
            f'<div class="stamp" style="display:flex;align-items:center;gap:16px;background:{ACCENT};'
            f'color:{INK};border-radius:18px;padding:12px 26px 10px 24px;'
            f'box-shadow:0 12px 0 rgba(0,0,0,.38),0 0 60px rgba(232,255,58,.25)">'
            f'<div style="font-size:30px;font-weight:900;line-height:1.02;letter-spacing:.14em">'
            f'CREATOR<br>CODE</div>'
            f'<div class="d" style="font-size:112px;line-height:.9;letter-spacing:.02em">BAD</div>'
            f'</div></div></div>')


def _hook_scene(comp: Comp, ctx: Ctx, title: str, sub: str, stick: str, end: float,
                a_item: dict = None, b_item: dict = None, colors: list = None):
    """The first 3 seconds decide everything: big words, motion, a reason to stay.

    Frame 0 IS the thumbnail. TikTok shows the first frame as a video lands in
    the feed and, on a personal account, as its cover, so the finished picture
    is already there on frame 0: title, date, the video's own cosmetics, the
    sticker and code BAD. Nothing flies in from off screen. The motion comes
    from beats that start and end at rest -- the cosmetics hop, the title thumps,
    the sticker boings -- each on its sound cue."""
    inner = tile_bg(colors or ["#232329", "#0d0d10"], "", 0)
    if a_item:
        inner += character(ctx.art(a_item), 270, 1150, 760, HOOK_WHOOSH_A, "hop", .45, "float",
                           a_item["rarity"], a_item["name"])
    if b_item:
        inner += character(ctx.art(b_item), 810, 1150, 760, HOOK_WHOOSH_B, "hop", .45, "sway",
                           b_item["rarity"], b_item["name"])
    inner += _code_stamp(comp, end)
    inner += label(f"FORTNITE ITEM SHOP · {ctx.day_label.upper()}", W / 2, 330, 30, 0,
                   ACCENT, 800, anim="none", align="center", spacing=".17em")
    # Sized to fit on one line with room for the thump, so a long title
    # ("GUESS THE PRICE") never runs off the sides.
    size = min(170, 960 / anton_em(title))
    inner += (f'<div class="full" style="transform-origin:50% 480px;'
              f'{style_anim(an("thump", HOOK_SLAM, .4))}">'
              + words(title, W / 2, 400 + (170 - size) * .45, size, 0, "#fff", 0, "none", "center", 1000)
              + "</div>")
    # Long stickers ("GONE AT 8 PM ET") shift left so they never touch the edge.
    # White, so the lime of the CREATOR CODE stamp is the one brand colour block.
    stick_w = (anton_em(stick) + .84) * 56
    inner += sticker(stick, min(640, W - 56 - stick_w), 700, 56, HOOK_POP, bg="#ffffff",
                     rot=-5, anim="boing")
    inner += label(sub, W / 2, 1330, 36, HOOK_SUB, "#fff", 700, align="center",
                   bg="rgba(10,10,11,.78)", pad="14px 26px")
    comp.scene(0, end, inner, fade_in=.01)


def _outro_scene(comp: Comp, ctx: Ctx, start: float, end: float, ask: str, items: list):
    inner = tile_bg(["#2b3200", "#0b0c05"], "", start)
    xs = [(210, 1050, 520, "float"), (870, 1080, 520, "sway"), (540, 1180, 600, "float")]
    for (x, y, h, idle), it in zip(xs, items[:3]):
        inner += character(ctx.art(it), x, y, h, start + .2, "drop", .8, idle, it["rarity"], it["name"])
    inner += label("USE CREATOR CODE", W / 2, 360, 44, start + .1, "#fff", 800, align="center",
                   spacing=".26em")
    inner += (f'<div class="abs d" style="left:0;right:0;top:420px;text-align:center;font-size:330px;'
              f'color:{ACCENT};text-shadow:0 0 90px rgba(232,255,58,.45),0 14px 0 rgba(0,0,0,.35);'
              f'{style_anim(an("slam", start + .25, .6))}">BAD</div>')
    inner += label("costs you nothing extra", W / 2, 790, 40, start + .7, "#fff", 700, align="center")
    inner += sticker(ask, 110, 1300, 50, start + 1.1, rot=-3)
    inner += burst(W / 2, 560, start + .5, ctx.seed)
    comp.scene(start, end, inner, fade_out=.01, z=2)


# ============================================================ THIS OR THAT

def this_or_that(ctx: Ctx):
    pool = singles(ctx)
    r = rng(ctx, 1)
    r.shuffle(pool)
    # Pair like with like at similar prices, so each round is a real choice.
    pairs, used = [], set()
    for a in pool:
        if a["name"] in used:
            continue
        for b in pool:
            if b["name"] in used or b["name"] == a["name"]:
                continue
            if b["type"] == a["type"] and abs(b["price"] - a["price"]) <= 500:
                pairs.append((a, b))
                used.update({a["name"], b["name"]})
                break
        if len(pairs) == 5:
            break
    if len(pairs) < 4:
        return None
    # Round 1 is the pair on the thumbnail, and two full characters sell it best,
    # so the first outfit pair (if any) moves to the front; the rest keep their mix.
    lead = next((k for k, (a, _) in enumerate(pairs) if a["type"] == "Outfit"), 0)
    pairs.insert(0, pairs.pop(lead))

    HOOK, R = 3.0, 10.4
    content_end = HOOK + len(pairs) * R
    outro = _pad(content_end)
    comp = Comp(content_end + outro)
    _hook_scene(comp, ctx, "THIS OR THAT", "COMMENT A OR B FOR EVERY ROUND",
                f"{len(pairs)} ROUNDS", HOOK + .3, pairs[0][0], pairs[0][1])
    comp.cue(.2, "slam"); comp.cue(.9, "pop")

    for k, (a, b) in enumerate(pairs, 1):
        t0 = HOOK + (k - 1) * R
        ca = (a.get("tile_colors") or [RARITY.get(a["rarity"], "#444")])
        cb = (b.get("tile_colors") or [RARITY.get(b["rarity"], "#444")])
        shake = style_anim(an("shake", t0 + .75, .35, "linear"))
        inner = (f'<div class="full" style="{shake}">'
                 f'<div class="abs" style="left:0;top:0;width:{W/2+60}px;height:{H}px;'
                 f'clip-path:polygon(0 0,100% 0,calc(100% - 120px) 100%,0 100%)">{tile_bg(ca, a["rarity"], t0)}</div>'
                 f'<div class="abs" style="right:0;top:0;width:{W/2+60}px;height:{H}px;'
                 f'clip-path:polygon(120px 0,100% 0,100% 100%,0 100%)">{tile_bg(cb, b["rarity"], t0)}</div>')
        inner += character(ctx.art(a), 285, 900, 700, t0 + .1, "fromL", .7, "float", a["rarity"], a["name"])
        inner += character(ctx.art(b), 800, 960, 700, t0 + .25, "fromR", .7, "sway", b["rarity"], b["name"])
        inner += sticker("A", 70, 420, 120, t0 + .5, rot=-8)
        inner += sticker("B", 880, 420, 120, t0 + .6, bg="#ffffff", rot=7)
        inner += (f'<div class="abs d" style="left:50%;top:560px;margin-left:-110px;width:220px;height:220px;'
                  f'border-radius:50%;background:{INK};border:8px solid {ACCENT};display:flex;align-items:center;'
                  f'justify-content:center;font-size:120px;color:{ACCENT};'
                  f'{style_anim(an("slam", t0 + .65, .45))}">VS</div>')
        inner += words(a["name"], 50, 1250, 64, t0 + .8, "#fff", .06, "rise", "left", 440)
        inner += label(f'{a["price"]:,} V-Bucks · {a["type"]}', 50, 1380, 30, t0 + 1.0, ACCENT, 800)
        inner += words(b["name"], SAFE_RIGHT - 10, 1250, 64, t0 + .9, "#fff", .06, "rise", "right", 440)
        inner += (f'<div class="abs" style="right:{W - SAFE_RIGHT + 10}px;top:1380px;text-align:right">'
                  f'<div style="font-size:30px;font-weight:800;color:{ACCENT};'
                  f'{style_anim(an("rise", t0 + 1.1, .45))}">{esc(b["type"])} · {b["price"]:,} V-Bucks</div></div>')
        # The ring takes over the VS badge and drains around it: one focal point,
        # nothing covering the characters.
        inner += countdown(5, W / 2, 670, 250, t0 + 2.8, "COMMENT A OR B")
        comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .65, "slam")
        for sec in range(5):
            comp.cue(t0 + 2.8 + sec, "tick")
        inner += "</div>"
        inner += progress(t0, t0 + R, k, len(pairs))
        comp.scene(t0, t0 + R, inner, fade_in=.25, fade_out=.25)

    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    _outro_scene(comp, ctx, content_end, comp.duration,
                 "DROP YOUR 5 PICKS LIKE: ABBAB" if len(pairs) == 5 else "DROP YOUR PICKS BELOW",
                 [p[0] for p in pairs] + [p[1] for p in pairs])
    comp.add(code_badge(.4))
    comp.add(disclosure())

    rounds = "\n".join(f"{num(k)} {a['name']} 🆚 {b['name']}" for k, (a, b) in enumerate(pairs, 1))
    tags = _hashtags("thisorthat", *(p[0]["name"] for p in pairs[:2]))
    example = "ABBAB"[:len(pairs)]
    return Video(
        "this_or_that", comp,
        title=f"This or That — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"This or That: Fortnite Item Shop {ctx.day_label} #shorts",
        caption=_caption(f"⚔️ THIS OR THAT — Fortnite Item Shop, {ctx.day_label}\n"
                         f"{len(pairs)} rounds, every item from today's shop. Pick A or B 👇",
                         rounds, f"Comment your picks in order, like {example}", tags),
        hashtags=tags)
