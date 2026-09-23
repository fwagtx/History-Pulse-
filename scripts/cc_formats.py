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
                       character, code_badge, countdown, disclosure, esc, label, price_roll,
                       progress, sticker, style_anim, tile_bg, words, EASE_BACK)

MIN_SECONDS = 62.0      # over TikTok's 1-minute Creator Rewards bar, with margin
DISCLOSE = "#EpicPartner — I get a commission from purchases made with code BAD."
CODE_LINE = "Using code BAD in the item shop costs you nothing extra 💛"


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


def _caption(hook: str, body: str, ask: str, tags: list) -> str:
    return (f"{hook}\n\n{body}\n\n{ask}\n\n{CODE_LINE}\n\n{DISCLOSE}\n\n"
            + " ".join("#" + t for t in tags))[:2150]


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


def _hook_scene(comp: Comp, ctx: Ctx, title: str, sub: str, stick: str, end: float,
                a_item: dict = None, b_item: dict = None, colors: list = None):
    """The first 3 seconds decide everything: big words, motion, a reason to stay."""
    inner = tile_bg(colors or ["#232329", "#0d0d10"], "", 0)
    if a_item:
        inner += character(ctx.art(a_item), 270, 1150, 760, .15, "fromL", .7, "float",
                           a_item["rarity"], a_item["name"])
    if b_item:
        inner += character(ctx.art(b_item), 810, 1150, 760, .3, "fromR", .7, "sway",
                           b_item["rarity"], b_item["name"])
    # Title and date are on screen from frame 0 (they punch in, never fade up
    # from nothing): the first frame is the thumbnail in the feed.
    inner += label(f"FORTNITE ITEM SHOP · {ctx.day_label.upper()}", W / 2, 330, 30, 0,
                   ACCENT, 800, anim="punch", align="center", spacing=".24em")
    inner += (f'<div class="full" style="transform-origin:50% 480px;{style_anim(an("punch", 0, .55))}">'
              + words(title, W / 2, 400, 170, 0, "#fff", 0, "none", "center", 1000) + "</div>")
    inner += sticker(stick, 640, 700, 56, .9, rot=-5)
    inner += label(sub, W / 2, 1330, 36, 1.1, "#fff", 700, align="center",
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

    rounds = "\n".join(f"Round {k}: {a['name']} vs {b['name']}" for k, (a, b) in enumerate(pairs, 1))
    tags = _hashtags("thisorthat", *(p[0]["name"] for p in pairs[:2]))
    return Video(
        "this_or_that", comp,
        title=f"This or That — Fortnite shop {ctx.day_label}",
        yt_title=f"This or That: Fortnite Item Shop {ctx.day_label} #shorts",
        caption=_caption(f"THIS OR THAT — today's Fortnite item shop ({ctx.day_label})",
                         rounds, "Comment your picks in order, like ABBAB 👇", tags),
        hashtags=tags)
