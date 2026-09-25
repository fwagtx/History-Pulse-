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

from cc_motion import (ACCENT, INK, RARITY, W, H, SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT, RAIL_TOP, BADGE_H, BADGE_X, BADGE_Y,
                       SAFE_LEFT, SAFE_RIGHT_TOP, Comp, an, burst,
                       anton_em, character, code_badge, countdown, disclosure, esc, label, price_roll,
                       progress, sticker, style_anim, tile_bg, words, EASE_BACK)

MIN_SECONDS = 62.0      # over TikTok's 1-minute Creator Rewards bar, with margin
# The disclosure is the #EpicPartner tag, on screen and in every description, on
# top of TikTok's "Paid partnership" label (commercialContentThirdParty). The
# owner dropped the longer "I get a commission..." sentence on 2026-09-23.
DISCLOSE = "#EpicPartner"
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


# Instagram caps a post at five hashtags (since December 2025), and #EpicPartner
# is one of them. So Instagram gets its own copy of each description: the same
# words, with the hashtag line cut to our three brand tags and #fortnite, and
# any "#<number>" ("Quiz #3") written without the "#" so it can't count as one.
IG_TAGS = BRAND_TAGS + ["fortnite"]
IG_MAX_TAGS = 5


def ig_caption(caption: str) -> str:
    body, _, last = caption.rpartition("\n")
    if not last.startswith("#"):
        body = caption.rstrip() + "\n"
    body = re.sub(r"#(\d)", r"\1", body)
    return body + "\n" + " ".join("#" + t for t in IG_TAGS)


def hashtag_count(text: str) -> int:
    return len(re.findall(r"#\w*[^\W\d_]\w*", text))


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
        💚 Creator Code: BAD · #EpicPartner
        #hashtags

    Blank lines between the blocks. If it's ever too long, whole lines drop from
    the end of the body -- never the ask, the code, the disclosure or the tags."""
    ask = ask if ask.startswith("💬") else f"💬 {ask}"
    foot = f"{CODE_CREDIT} · {DISCLOSE}\n\n" + " ".join("#" + t for t in tags)
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


# The USE CODE: BAD stamp: the corner badge (cc_motion.code_badge) at 1.4x, so it
# shrinks into the badge exactly. Measured in the render browser with the
# embedded fonts: the stamp is 358x120 px, the badge 257x86.
STAMP_X, STAMP_Y, STAMP_ROT = SAFE_LEFT + 10, 560, 3

# The hook's two cosmetics: side by side in the band beside the apps' button
# rail (x 60-900, so centred on x 480), feet above the caption zone (y 1420).
HOOK_MID = (SAFE_LEFT + SAFE_RIGHT) / 2
HOOK_AX, HOOK_BX, HOOK_CY, HOOK_H, HOOK_MAXW = HOOK_MID - 205, HOOK_MID + 205, 1052, 600, 400
STAMP_TO_BADGE = BADGE_H / 120


def _dock_times(end: float) -> tuple:
    """When the hook's USE CODE: BAD stamp flies into the corner badge."""
    dock_end = min(2.6, end - .7)          # clear of the first scene's wipe at 2.7s
    return dock_end - .5, dock_end


def _code_stamp(comp: Comp, end: float) -> str:
    """USE CODE: BAD, big, in the gap between the title and the cosmetics.

    It's the thing the whole account exists to sell, so on the thumbnail it
    gets real size: BAD at 112px on a lime block. Near the end of the hook it
    shrinks and flies into the top-left corner, and the small corner badge that
    stays up for the rest of the video takes over as it lands."""
    dock_start, dock_end = _dock_times(end)
    dock = comp.uid("dock")
    # The stamp stays fully opaque all the way into the corner, and the badge
    # takes its place the moment it lands: the code is readable in every frame.
    comp.css(f"@keyframes {dock}{{0%{{transform:rotate({STAMP_ROT}deg);opacity:1}}"
             f"99.9%{{transform:translate({BADGE_X - STAMP_X}px,{BADGE_Y - STAMP_Y}px) "
             f"scale({STAMP_TO_BADGE:.3f}) rotate(0deg);opacity:1}}"
             f"100%{{transform:translate({BADGE_X - STAMP_X}px,{BADGE_Y - STAMP_Y}px) "
             f"scale({STAMP_TO_BADGE:.3f}) rotate(0deg);opacity:0}}}}")
    # The corner badge and its #EpicPartner wait until the stamp gets there.
    # ("paused" like every animation: the renderer moves them, real time never does)
    comp.css(f".codebadge,.codetag{{animation:fadein .01s linear {dock_end - .01:.3f}s both paused !important}}")
    comp.cue(dock_start, "whoosh")
    beats = style_anim(an("thump", HOOK_SLAM, .4, fill="none"),
                       an("pulse", 1.5, .5, "ease-in-out", fill="none"))
    return (f'<div class="abs" style="left:{STAMP_X}px;top:{STAMP_Y}px;transform-origin:0 0;z-index:5;'
            f'{style_anim(an(dock, dock_start, dock_end - dock_start, "cubic-bezier(.6,0,.4,1)"))}">'
            f'<div style="{beats}">'
            f'<div class="stamp" style="display:flex;align-items:center;gap:17px;background:{ACCENT};'
            f'color:{INK};border-radius:22px;padding:11px 28px 8px 25px;'
            f'box-shadow:0 11px 0 rgba(0,0,0,.38),0 0 60px rgba(232,255,58,.25)">'
            f'<div style="font-size:32px;font-weight:900;line-height:1.02;letter-spacing:.12em">'
            f'USE<br>CODE:</div>'
            f'<div class="d" style="font-size:112px;line-height:.9;letter-spacing:.02em">BAD</div>'
            f'</div>'
            # #EpicPartner under it, where the corner tag sits under the badge (x1.4),
            # so the pair shrinks into the corner together.
            f'<div style="margin:{4 * 1.4:.1f}px 0 0 {4 * 1.4:.1f}px;font-size:{23 * 1.4:.0f}px;font-weight:700;'
            f'line-height:1.3;color:rgba(255,255,255,.92);text-shadow:0 2px 8px rgba(0,0,0,.9)">#EpicPartner</div>'
            f'</div></div>')


# A cosmetic as a solid shape with a thin light rim, for quizzes that ask who it is.
SILHOUETTE = ("brightness(0) drop-shadow(0 0 4px rgba(255,255,255,.95)) "
              "drop-shadow(0 0 22px rgba(232,255,58,.45))")


def _hook_scene(comp: Comp, ctx: Ctx, title: str, sub: str, stick: str, end: float,
                a_item: dict = None, b_item: dict = None, colors: list = None,
                kicker: str = "", silhouette: bool = False, kicker_color: str = ACCENT, extra: str = ""):
    """The first 3 seconds decide everything: big words, motion, a reason to stay.

    Frame 0 IS the thumbnail. TikTok shows the first frame as a video lands in
    the feed and, on a personal account, as its cover, so the finished picture
    is already there on frame 0: title, date, the video's own cosmetics, the
    sticker and code BAD. Nothing flies in from off screen. The motion comes
    from beats that start and end at rest -- the cosmetics hop, the title thumps,
    the sticker boings -- each on its sound cue.

    `kicker` replaces the shop date line (the quizzes aren't about a day's
    shop); `silhouette` blacks the cosmetics out so a quiz's thumbnail never
    gives an answer away. `extra` is drawn over the background, under the
    cosmetics (a series' decorations)."""
    inner = tile_bg(colors or ["#232329", "#0d0d10"], "", 0) + extra
    # Everything sits in the apps' safe box (cc_safe): the words in the wide top
    # band, the cosmetics side by side in the band beside the button rail
    # (x 60-900), centred on it, and nothing below y 1420.
    chars = ""
    if a_item:
        chars += character(ctx.art(a_item), HOOK_AX, HOOK_CY, HOOK_H, HOOK_WHOOSH_A, "hop", .45, "float",
                           a_item["rarity"], a_item["name"], maxw=HOOK_MAXW, trim=True)
    if b_item:
        chars += character(ctx.art(b_item), HOOK_BX, HOOK_CY, HOOK_H, HOOK_WHOOSH_B, "hop", .45, "sway",
                           b_item["rarity"], b_item["name"], maxw=HOOK_MAXW, trim=True)
    inner += f'<div class="full" style="filter:{SILHOUETTE}">{chars}</div>' if silhouette else chars
    inner += _code_stamp(comp, end)
    # The kicker (the date line) is for the thumbnail; it steps aside as the stamp
    # flies up to the corner badge, which lands where it was.
    kick_out = style_anim(an("fadeout", _dock_times(end)[0], .3))
    inner += (f'<div class="full" style="{kick_out}">'
              + label(kicker or f"FORTNITE ITEM SHOP · {ctx.day_label.upper()}", W / 2, 300, 30, 0,
                      kicker_color, 800, anim="none", align="center", spacing=".17em") + "</div>")
    # Sized to fit on one line with room for the thump, so a long title
    # ("GUESS THE PRICE") never runs off the sides.
    size = min(170, 940 / anton_em(title))
    inner += (f'<div class="full" style="transform-origin:50% 430px;'
              f'{style_anim(an("thump", HOOK_SLAM, .4))}">'
              + words(title, W / 2, 350 + (170 - size) * .45, size, 0, "#fff", 0, "none", "center", 1000)
              + "</div>")
    # Long stickers ("GONE AT 8 PM ET") shift left so they never pass the safe
    # box's edge. White, so the lime of the USE CODE: BAD stamp is the one brand
    # colour block.
    stick_size = min(56, 360 / (anton_em(stick) + .84))
    stick_w = (anton_em(stick) + .84) * stick_size
    inner += sticker(stick, min(620, SAFE_RIGHT_TOP - 24 - stick_w), 598, stick_size, HOOK_POP, bg="#ffffff",
                     rot=-5, anim="boing")
    inner += label(sub, HOOK_MID, 1318, 34, HOOK_SUB, "#fff", 700, align="center",
                   bg="rgba(10,10,11,.78)", pad="13px 24px")
    comp.scene(0, end, inner, fade_in=.01)


def _outro_scene(comp: Comp, ctx: Ctx, start: float, end: float, ask: str, items: list):
    """USE CREATOR CODE BAD, big, with three of the video's cosmetics and the ask.
    All of it in the apps' safe box: the code in the wide top band, the line-up
    beside the button rail, the ask above the caption zone."""
    inner = tile_bg(["#2b3200", "#0b0c05"], "", start)
    mid = HOOK_MID
    xs = [(mid - 265, 1010, 470, "float"), (mid + 265, 1010, 470, "sway"), (mid, 1040, 560, "float")]
    for (x, y, h, idle), it in zip(xs, items[:3]):
        inner += character(ctx.art(it), x, y, h, start + .2, "drop", .8, idle, it["rarity"], it["name"],
                           maxw=300, trim=True)
    inner += label("USE CREATOR CODE", W / 2, 372, 44, start + .1, "#fff", 800, align="center",
                   spacing=".26em")
    inner += (f'<div class="abs d" style="left:0;right:0;top:428px;text-align:center;font-size:290px;'
              f'color:{ACCENT};text-shadow:0 0 90px rgba(232,255,58,.45),0 14px 0 rgba(0,0,0,.35);'
              f'{style_anim(an("slam", start + .25, .6))}">BAD</div>')
    ask_size = min(50, 800 / (anton_em(ask) + .84))
    inner += sticker(ask, SAFE_LEFT + 30, 1318, ask_size, start + 1.1, rot=-3)
    inner += burst(W / 2, 540, start + .5, ctx.seed)
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

    HOOK = 3.0
    n = len(pairs)
    example = "ABBAB"[:n]
    # Five rounds of 10.4 s make a 62.5 s video. With only four pairs the rounds
    # stretch a little (to 12 s) rather than leave a 17-second end card.
    R = max(10.4, min(12.0, (MIN_SECONDS - 7.5 - HOOK) / n))
    content_end = HOOK + n * R
    outro = _pad(content_end)
    comp = Comp(content_end + outro)
    _hook_scene(comp, ctx, "THIS OR THAT", "COMMENT A OR B FOR EVERY ROUND",
                f"{n} ROUNDS", HOOK + .3, pairs[0][0], pairs[0][1])
    comp.cue(.2, "slam"); comp.cue(.9, "pop")

    # Layout, all inside the apps' safe box (cc_safe). The A and B letters, the
    # category and the call to comment sit in the wide top band; the two
    # cosmetics stand side by side in the band beside the button rail (x 60-900),
    # one column each, with their names and prices centred under them and the
    # VS / countdown ring between their heads. The diagonal split between the two
    # colour panels runs through the ring and between the columns.
    COL_W = 372                                        # each column's text width
    AX = SAFE_LEFT + 4 + COL_W / 2                     # 250
    BX = SAFE_RIGHT - 4 - COL_W / 2                    # 710
    ART_TOP, ART_MAXW = 600, 380
    NAME_BOTTOM, PRICE_Y = 1338, 1352                  # the price pill ends ~1400
    RING_X, RING_Y = W / 2, 648
    SPLIT_TOP, SPLIT_BOTTOM = 570, 410                 # the split's x at y 0 and y 1920
    LETTER, LETTER_Y, LETTER_INSET = 110, 392, 32
    b_left = SAFE_RIGHT_TOP - LETTER_INSET - (anton_em("B") + .84 - .18) * LETTER

    def lines(text: str, size: float) -> int:
        """How many lines `text` wraps into at COL_W (each word carries .18em).
        A few px under the column, so a borderline name counts as the longer case."""
        k, cur = 1, 0.0
        for w in text.upper().split():
            ww = anton_em(w) * size
            if cur and cur + ww > COL_W - 8:
                k, cur = k + 1, ww
            else:
                cur += ww
        return k

    def name_size(*names) -> int:
        """One size for both names, so neither side looks like the favourite:
        both on one line if that holds at 56 px or more; else the largest size
        (64 down to 48 px) that keeps each on two lines at most; past that,
        48 px on as many lines as it takes."""
        for s in range(64, 55, -2):
            if all(lines(nm, s) == 1 for nm in names):
                return s
        for s in range(64, 47, -2):
            if all(lines(nm, s) <= 2 for nm in names):
                return s
        # One enormous word would run out of its column at any size: shrink until it fits.
        longest = max(anton_em(w) for nm in names for w in nm.upper().split())
        return min(48, int((COL_W - 8) / longest))

    def centred_name(text: str, cx: float, size: float, start: float) -> str:
        """words(), centred in a column and anchored by its last line, so both
        names end on the same line however many lines each takes. The lines are
        set here, not left to the browser: one line stays one line, and a
        two-line name breaks where its lines come out most even (no lone last
        word). Each line is at least 8 px narrower than the column."""
        ws = text.split()
        n_lines, brk = lines(text, size), 0
        if n_lines == 2:
            ww = [anton_em(w) * size for w in ws]
            brk = min(range(1, len(ws)), key=lambda j: max(sum(ww[:j]), sum(ww[j:])))
        parts = "".join(
            ("<br>" if i == brk and brk else "")
            + f'<span style="display:inline-block;margin:0 .09em;{style_anim(an("rise", start + i * .06, .5))}">'
            f'{esc(w)}</span>' for i, w in enumerate(ws))
        nowrap = "white-space:nowrap;" if n_lines <= 2 else ""
        return (f'<div class="abs d" style="left:{cx - COL_W / 2:.0f}px;bottom:{H - NAME_BOTTOM}px;width:{COL_W}px;'
                f'font-size:{size}px;line-height:.92;color:#fff;text-align:center;{nowrap}'
                f'text-shadow:0 6px 0 rgba(0,0,0,.4),0 0 30px rgba(0,0,0,.45)">{parts}</div>')

    def plural(kind: str) -> str:
        k = kind.strip()
        low = k.lower()
        if not k or low.endswith("s") or low == "music":
            return k
        if low.endswith("y") and len(k) > 1 and low[-2] not in "aeiou":
            return k[:-1] + "ies"                       # Car Body -> Car Bodies
        return k + ("es" if low.endswith(("x", "ch", "sh")) else "s")

    for k, (a, b) in enumerate(pairs, 1):
        t0 = HOOK + (k - 1) * R
        # The countdown fills the round after the names land: no dead air at 0.
        cd = int(R - 3.3)                               # 7 s in a 10.4 s round
        t_cd = t0 + R - .8 - cd
        ca = (a.get("tile_colors") or [RARITY.get(a["rarity"], "#444")])
        cb = (b.get("tile_colors") or [RARITY.get(b["rarity"], "#444")])
        shake = style_anim(an("shake", t0 + .75, .35, "linear"))
        # Each panel's stage is centred on its own column.
        aw, bl = 2 * (AX + 70), SPLIT_BOTTOM
        inner = (f'<div class="full" style="{shake}">'
                 f'<div class="abs" style="left:-70px;top:0;width:{aw:.0f}px;height:{H}px;clip-path:polygon('
                 f'0 0,{SPLIT_TOP + 70}px 0,{SPLIT_BOTTOM + 70}px 100%,0 100%)">{tile_bg(ca, a["rarity"], t0)}</div>'
                 f'<div class="abs" style="left:{bl}px;top:0;width:{W - bl}px;height:{H}px;clip-path:polygon('
                 f'{SPLIT_TOP - bl}px 0,100% 0,100% 100%,0 100%)">{tile_bg(cb, b["rarity"], t0)}</div>'
                 f'<div class="full" style="background:linear-gradient(180deg,rgba(0,0,0,.35) 0,'
                 f'rgba(0,0,0,0) 24%,rgba(0,0,0,0) 50%,rgba(0,0,0,.55) 64%,rgba(0,0,0,.6) 100%)"></div>')

        size = name_size(a["name"], b["name"])
        tops = [NAME_BOTTOM - lines(it["name"], size) * size * .92 for it in (a, b)]
        art_bottom = min(tops) - 22
        art_h = art_bottom - ART_TOP
        cy = (ART_TOP + art_bottom) / 2
        # data-trim (cc_looks.PREP_JS): Fortnite's art is a square with wide
        # transparent margins; cropped to the cosmetic, it fills its column.
        for it, x, t, enter, idle in ((a, AX, t0 + .1, "fromL", "float"), (b, BX, t0 + .25, "fromR", "sway")):
            inner += character(ctx.art(it), x, cy, art_h, t, enter, .7, idle, it["rarity"], it["name"],
                               maxw=ART_MAXW).replace('<img class="art"', '<img class="art" data-trim', 1)
        inner += sticker("A", SAFE_LEFT + LETTER_INSET, LETTER_Y, LETTER, t0 + .5, rot=-8)
        inner += sticker("B", b_left, LETTER_Y, LETTER, t0 + .6, bg="#ffffff", rot=7)
        # What both are (a pair is always one type), then the ask once the clock starts.
        kind = plural(a["type"]).upper()
        if kind:
            inner += label(kind, W / 2, LETTER_Y + 4, 30, t0 + .7, "#fff", 800, align="center",
                           bg="rgba(10,10,11,.72)", pad="7px 18px 6px", spacing=".18em")
        inner += (f'<div class="abs" style="left:0;width:{W}px;top:{LETTER_Y + 62}px;text-align:center">'
                  f'<div class="d" style="display:inline-block;font-size:46px;color:#fff;background:rgba(10,10,11,.86);'
                  f'padding:.16em .42em .1em;border-radius:12px;border-bottom:5px solid {ACCENT};'
                  f'box-shadow:0 8px 0 rgba(0,0,0,.3);{style_anim(an("pop", t_cd, .5, EASE_BACK))}">'
                  f'COMMENT <span style="color:{ACCENT}">A</span> OR B</div></div>')
        vs_out = style_anim(an("fadeout", t_cd + .15, .1))
        inner += (f'<div class="abs" style="left:{RING_X - 95:.0f}px;top:{RING_Y - 95:.0f}px;{vs_out}">'
                  f'<div class="d" style="width:190px;height:190px;border-radius:50%;background:{INK};'
                  f'border:8px solid {ACCENT};display:flex;align-items:center;justify-content:center;'
                  f'font-size:100px;color:{ACCENT};box-shadow:0 10px 0 rgba(0,0,0,.3);'
                  f'{style_anim(an("slam", t0 + .65, .45))}">VS</div></div>')
        for it, x, t in ((a, AX, t0 + .8), (b, BX, t0 + .9)):
            inner += centred_name(it["name"], x, size, t)
            inner += label(f'{it["price"]:,} V-Bucks', x, PRICE_Y, 32, t + .2, ACCENT, 800, align="center",
                           bg="rgba(10,10,11,.8)", pad="5px 18px 4px")
        # The ring takes over the VS badge and drains around it: one focal point,
        # between the two heads. (Its dark disc and number would cover the VS from
        # the start, so the whole ring waits for its moment.)
        inner += (f'<div class="abs" style="left:0;top:0;{style_anim(an("fadein", t_cd, .15))}">'
                  + countdown(cd, RING_X, RING_Y, 200, t_cd) + "</div>")
        comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .65, "slam")
        for sec in range(cd):
            comp.cue(t_cd + sec, "tick")
        inner += "</div>"
        inner += progress(t0, t0 + R, k, n)
        # Held .3 s past its slot while the next round (or the end card) fades in
        # over it: a cross-fade, not a dip to black.
        comp.scene(t0, t0 + R + .3, inner, fade_in=.25, fade_out=.05)

    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    _outro_scene(comp, ctx, content_end, comp.duration, f"DROP YOUR {n} PICKS LIKE: {example}",
                 [p[0] for p in pairs] + [p[1] for p in pairs])
    from cc_looks import PREP_JS
    comp.add(PREP_JS)
    comp.add(code_badge(.4))
    comp.add(disclosure())

    rounds = "\n".join(f"{num(k)} {a['name']} 🆚 {b['name']}" for k, (a, b) in enumerate(pairs, 1))
    tags = _hashtags("thisorthat", *(p[0]["name"] for p in pairs[:2]))
    return Video(
        "this_or_that", comp,
        title=f"This or That — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"This or That: Fortnite Item Shop {ctx.day_label} #shorts",
        caption=_caption(f"⚔️ THIS OR THAT — Fortnite Item Shop, {ctx.day_label}\n"
                         f"{len(pairs)} rounds, every item from today's shop. Pick A or B 👇",
                         rounds, f"Comment your picks in order, like {example}", tags),
        hashtags=tags)
