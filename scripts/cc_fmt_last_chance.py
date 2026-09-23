"""
LAST CHANCE -- slot 3 (value / urgency) for @usecodebad.

Everything in today's shop whose listing ends at the next reset, biggest offers
first. Each offer gets ~6 seconds in front of a giant clock:

    0:00  hook      LAST CHANCE / GONE AT 8 PM ET, two real cosmetics sliding in
    0:03  offers    up to 8, price high to low. Per offer: a caution-stripe wipe,
                    Epic's tile colours, a clock face swings in behind the cosmetic,
                    the cosmetic enters and idles, the name slams, a red/amber
                    LEAVING AT RESET ribbon unfurls, the price rolls up on a
                    crooked card. The clock's red arc ticks down one step a second
                    (a stopwatch bubble counts 5..0 with it); on the last tick the
                    frame flashes red, the cosmetic greys out and the next wipe
                    carries it away.
    0:53  outro     code BAD + "WHICH ONE ARE YOU GRABBING?"

Truth rules this format keeps:
  - an offer is only here when its `out_day` is today's shop day, i.e. it leaves
    at the next reset. The wording is "leaving at reset" / "scheduled to leave";
    nothing says or implies it won't come back.
  - the clock is decoration: it paces the video, it is not a claim about how long
    anything has left. The only time on screen is the reset time, computed.
  - prices are the row's `price`. Only bundles ever show a regular price, and only
    when Epic lists one above today's price ("regular price", nothing else).
  - "in the shop since Sep 20" / "added today" come from `in_day`; a bundle's
    contents come from `member_names`.
Nothing about popularity, ratings, rarity-as-scarcity, "back" or "first time".
"""

from datetime import date

from cc_formats import (Ctx, Video, BRAND_TAGS, rng, _pad, _hook_scene, _outro_scene,
                        _hashtags, _caption)
from cc_motion import (ACCENT, INK, RARITY, W, SAFE_RIGHT, RAIL_TOP, Comp, an, burst,
                       character, code_badge, disclosure, esc, hexcol, label, price_roll,
                       progress, sticker, style_anim, tile_bg, words, EASE_BACK, EASE_OUT)

FORMAT = "last_chance"
MIN_OFFERS = 4          # fewer than this leaving today: not enough for an honest video
MAX_OFFERS = 8
MAX_BUNDLES = 3         # keep room for single cosmetics; relaxed on a thin day
SECTION_CAP = 2         # same shop section at most twice; relaxed on a thin day

HOOK = 3.0              # hook length
R = 6.2                 # one offer

RED = "#FF3B3B"
AMBER = "#FFB21A"

# Beats inside an offer, seconds from its start.
T_CLOCK = .05           # clock face swings in
T_CHAR = .15            # cosmetic enters
T_PILL = .3             # rarity/type pill
T_NAME = .35            # name slams
T_INCL = .75            # bundle contents line
T_BUBBLE = .6           # stopwatch bubble pops on
T_CD = .8               # clock starts ticking: 5 steps, one a second
CD = 5
T_RIB = .9              # LEAVING AT RESET ribbon unfurls
T_CARD = 1.3            # price card rises
T_ROLL = 1.5            # price counts up
ROLL = 1.0
T_END = T_CD + CD       # the last tick: red flash, cosmetic greys out

# Layout (px). Important content stays in y 190..1480; below y=880 it stays left of
# x=960 (TikTok's like/comment rail). Code badge + disclosure own the top-left
# y 190..300, the pips the top-right.
TEXT_X = 60
PILL_Y = 322
NAME_Y = 382
NAME_W = 960
CX = 470                # cosmetic + clock centre x
ART_BOTTOM = 1238       # the cosmetic's feet, clear of the price card
CARD_X, CARD_BOTTOM = 46, 1458

# Anton advance widths (em) at letter-spacing 0, measured in headless Chromium.
_ANTON = {
    " ": .244, "!": .239, '"': .439, "#": .556, "$": .472, "%": 1.067, "&": .53, "'": .224,
    "(": .301, ")": .301, "*": .462, "+": .365, ",": .246, "-": .321, ".": .239, "/": .415,
    "0": .504, "1": .341, "2": .504, "3": .504, "4": .504, "5": .504, "6": .504, "7": .504,
    "8": .504, "9": .504, ":": .252, ";": .255, "?": .502, "@": .874, "A": .495, "B": .489,
    "C": .484, "D": .503, "E": .422, "F": .409, "G": .495, "H": .509, "I": .237, "J": .476,
    "K": .482, "L": .407, "M": .756, "N": .508, "O": .496, "P": .482, "Q": .504, "R": .487,
    "S": .472, "T": .406, "U": .484, "V": .479, "W": .722, "X": .494, "Y": .456, "Z": .42,
    "·": .244, "’": .242,
}


def _em(text: str) -> float:
    """Width of Anton text in em (the .d class adds .01em letter-spacing)."""
    return sum(_ANTON.get(ch, .5) + .01 for ch in text.upper())


def _lines(text: str, size: float, width: float) -> int:
    """How many lines words() wraps `text` into (each word carries a .18em margin)."""
    n, cur = 1, 0.0
    for w in text.split():
        ww = (_em(w) + .18) * size
        if cur and cur + ww > width:
            n, cur = n + 1, ww
        else:
            cur += ww
    return n


def _fit(text: str, width: float, big: int = 150, one_min: int = 100, two_max: int = 118,
         small: int = 70):
    """Largest size that keeps `text` on one line (down to one_min), else the
    largest two-line size (capped at two_max). Returns (size, lines)."""
    for s in range(big, one_min - 1, -2):
        if _lines(text, s, width) == 1:
            return s, 1
    for s in range(two_max, small - 1, -2):
        if _lines(text, s, width) <= 2:
            return s, 2
    return small, _lines(text, small, width)


def _price_w(value: int, size: float) -> float:
    """Rendered width of price_roll's settled '1,200 V-BUCKS'."""
    return _em(f"{value:,}") * size + (_em("V-BUCKS") + .2) * .38 * size


def _clean_name(name: str) -> str:
    """'Kingdom Hearts (19 items)' -> 'Kingdom Hearts'."""
    return name.split(" (")[0].strip() if name.endswith(" items)") else name


def _shown_name(it: dict) -> str:
    return _clean_name(it["name"]) if it.get("is_bundle") else it["name"]


def _mon_d(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%b %-d")


def _members(it: dict) -> list:
    seen, out = set(), []
    for n in it.get("member_names") or []:
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out


def _regular(it: dict) -> int:
    """Epic's regular price when it's above today's -- bundles only, by rule."""
    if not it.get("is_bundle"):
        return 0
    reg, price = int(it.get("regular_price") or 0), int(it.get("price") or 0)
    return reg if reg > price else 0


def _since(it: dict, ctx: Ctx) -> str:
    """The listing's start, from in_day. '' when unknown."""
    d = it.get("in_day") or ""
    if not d:
        return ""
    if d == ctx.day.isoformat():
        return "ADDED TODAY"
    return f"IN THE SHOP SINCE {_mon_d(d).upper()}"


def _meta(it: dict) -> str:
    if it.get("is_bundle"):
        n = int(it.get("bundle_size") or 0) or len(it.get("member_names") or [])
        return f"BUNDLE · {n} ITEMS" if n else "BUNDLE"
    return f'{it.get("rarity_label") or it["rarity"]} {it["type"]}'.upper()


def _ink_on(bg: str) -> str:
    """Dark text on light fills, white on dark ones."""
    h = hexcol(bg, "#777777").lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return INK if .2126 * r + .7152 * g + .0722 * b > .42 else "#fff"


# ---------------------------------------------------------------- selection

def _leaving(ctx: Ctx) -> list:
    day = ctx.day.isoformat()
    return [i for i in ctx.shop.get("items", [])
            if i.get("out_day") == day and int(i.get("price") or 0) > 0]


def _pick(ctx: Ctx, leaving: list) -> list:
    """Up to 8 leaving offers, price high to low. Ties break by a seeded shuffle.
    Variety caps (bundles, one shop section, repeated names) apply first and are
    relaxed only when the day is too thin to fill the video without them."""
    with_art = [i for i in leaving if ctx.art(i)]
    pool = with_art if len(with_art) >= MIN_OFFERS else list(leaving)
    r = rng(ctx, 41)
    tie = {id(i): r.random() for i in pool}
    pool.sort(key=lambda i: (-int(i["price"]), tie[id(i)]))
    rank = {id(i): k for k, i in enumerate(pool)}

    picked = []
    key = lambda i: _shown_name(i).strip().lower()
    sec = lambda i: (i.get("section") or "").strip().lower()

    def ok(it, sec_cap, b_cap, uniq):
        if any(p is it for p in picked):
            return False
        if uniq and key(it) in {key(p) for p in picked}:
            return False
        if it.get("is_bundle") and sum(1 for p in picked if p.get("is_bundle")) >= b_cap:
            return False
        if sec(it) and sum(1 for p in picked if sec(p) == sec(it)) >= sec_cap:
            return False
        return True

    for caps in ((SECTION_CAP, MAX_BUNDLES, True), (99, MAX_BUNDLES, True),
                 (99, 99, True), (99, 99, False)):
        for it in pool:
            if len(picked) >= MAX_OFFERS:
                break
            if ok(it, *caps):
                picked.append(it)
    picked.sort(key=lambda i: rank[id(i)])
    return picked


def _showcase(picked: list) -> list:
    """Offers in the order they look best as big characters: outfits, other
    singles, then bundles."""
    return sorted(picked, key=lambda i: (bool(i.get("is_bundle")), i.get("type") != "Outfit"))


# ---------------------------------------------------------------- components

def _ring_mask(th: float) -> str:
    """Show only an outer ring `th` px thick of a square element."""
    g = (f"radial-gradient(closest-side,transparent calc(100% - {th:.0f}px),#000 calc(100% - {th - 1:.0f}px),"
         f"#000 calc(100% - 1px),transparent 100%)")
    return f"-webkit-mask:{g};mask:{g};"


def _css() -> list:
    """Keyframes for this format. Offsets are relative, so every offer shares them."""
    span = CD + .5
    pct = lambda s: f"{max(0.0, min(100.0, s / span * 100)):.3f}%"
    arc, hand = ["0%{--p:1}"], ["0%{transform:rotate(0deg)}"]
    for k in range(1, CD + 1):
        a0, a1 = 360 * (k - 1) / CD, 360 * k / CD
        arc += [f"{pct(k - .001)}{{--p:{1 - (k - 1) / CD:.3f}}}", f"{pct(k + .14)}{{--p:{1 - k / CD:.3f}}}"]
        hand += [f"{pct(k - .001)}{{transform:rotate({a0:.1f}deg)}}",
                 f"{pct(k + .08)}{{transform:rotate({a1 + 7:.1f}deg)}}",
                 f"{pct(k + .22)}{{transform:rotate({a1:.1f}deg)}}"]
    arc.append("100%{--p:0}")
    hand.append(f"100%{{transform:rotate(360deg)}}")
    return [
        "@keyframes lcarc{" + "".join(arc) + "}",
        "@keyframes lchand{" + "".join(hand) + "}",
        "@keyframes lcnum{from{--n:%d}to{--n:0}}" % CD,
        "@keyframes lcclockin{0%{transform:scale(.55) rotate(-40deg);opacity:0}"
        "70%{transform:scale(1.03) rotate(3deg);opacity:1}100%{transform:none;opacity:1}}",
        "@keyframes lcbeat{0%{transform:scale(1.16)}35%{transform:scale(.98)}60%,100%{transform:scale(1)}}",
        "@keyframes lcunfurl{0%{transform:scaleX(0)}65%{transform:scaleX(1.04)}100%{transform:scaleX(1)}}",
        "@keyframes lcshine{from{transform:translateX(-200%) skewX(-20deg)}to{transform:translateX(900%) skewX(-20deg)}}",
        "@keyframes lcblink{0%,45%{opacity:1}55%,100%{opacity:.15}}",
        "@keyframes lcgone{to{filter:grayscale(1) brightness(.5);transform:scale(.9)}}",
        "@keyframes lcflash{0%{opacity:0}18%{opacity:1}100%{opacity:0}}",
        "@keyframes lcheat{from{opacity:0}to{opacity:1}}",
        "@keyframes lcwipe{from{transform:translateX(-2760px) skewX(-14deg)}"
        "to{transform:translateX(2040px) skewX(-14deg)}}",
        "@keyframes lcgrow{from{transform:scaleX(0)}to{transform:scaleX(1)}}",
    ]


def _from(t: float, inner: str) -> str:
    """Hidden until `t`. price_roll's counter and burst's confetti both show their
    first keyframe before they start (fill: both), so they wait behind this."""
    return f'<div class="abs" style="left:0;top:0;{style_anim(an("fadein", t, .01))}">{inner}</div>'


def _scrim() -> str:
    """Darkens the top and bottom bands so white type holds on pale tile colours."""
    return ('<div class="full" style="background:linear-gradient(180deg,rgba(0,0,0,.55) 0,'
            'rgba(0,0,0,.2) 22%,rgba(0,0,0,0) 36%,rgba(0,0,0,0) 58%,rgba(0,0,0,.4) 76%,'
            'rgba(0,0,0,.62) 100%)"></div>')


def _heat(t0: float) -> str:
    """Red creeps in from the edges while the clock runs, then flashes on the
    last tick."""
    edge = ('radial-gradient(ellipse 80% 70% at 50% 45%,transparent 45%,'
            'rgba(255,40,40,.34) 88%,rgba(255,40,40,.5) 100%)')
    return (f'<div class="full" style="background:{edge};'
            f'{style_anim(an("lcheat", t0 + T_CD, CD, "cubic-bezier(.5,0,.9,.6)"))}"></div>'
            f'<div class="full" style="background:radial-gradient(ellipse 90% 80% at 50% 45%,'
            f'rgba(255,59,59,.12) 30%,rgba(255,40,40,.6) 100%);'
            f'{style_anim(an("lcflash", t0 + T_END, .55, "ease-out"))}"></div>')


def _clock(cx: float, cy: float, d: float, t0: float) -> str:
    """A clock face behind the cosmetic: hour and minute ticks, a red-to-amber arc
    that steps down once a second, and a second hand that snaps round with it.
    Decoration and pacing only -- it says nothing about the shop."""
    r = d / 2
    t_cd = t0 + T_CD
    arc_bg = ("conic-gradient(transparent 0deg calc((1 - var(--p)) * 360deg),"
              f"{RED} calc((1 - var(--p)) * 360deg),{AMBER} 360deg)")
    parts = [
        # a dark backplate so the cosmetic separates from busy tile colours
        '<div class="abs" style="inset:0;border-radius:50%;background:radial-gradient(closest-side,'
        'rgba(8,8,10,.42) 0%,rgba(8,8,10,.3) 70%,rgba(8,8,10,.12) 92%,transparent 100%)"></div>',
        # track + arc
        f'<div class="abs" style="inset:0;border-radius:50%;background:rgba(255,255,255,.16);{_ring_mask(22)}"></div>',
        f'<div class="abs" style="inset:0;border-radius:50%;background:{arc_bg};{_ring_mask(22)}'
        f'{style_anim(an("lcarc", t_cd, CD + .5, EASE_OUT))}"></div>',
        # minute and hour ticks
        f'<div class="abs" style="inset:40px;border-radius:50%;background:repeating-conic-gradient(from -.4deg,'
        f'rgba(255,255,255,.5) 0 .8deg,transparent .8deg 6deg);{_ring_mask(14)}"></div>',
        f'<div class="abs" style="inset:40px;border-radius:50%;background:repeating-conic-gradient(from -1.3deg,'
        f'#fff 0 2.6deg,transparent 2.6deg 30deg);{_ring_mask(32)}"></div>',
        # second hand, pivoting on the centre
        f'<div class="abs" style="left:{r - 5:.0f}px;top:{r - (r - 30):.0f}px;width:10px;height:{r - 30 + 60:.0f}px;'
        f'transform-origin:5px {r - 30:.0f}px;{style_anim(an("lchand", t_cd, CD + .5, "linear"))}">'
        f'<div style="position:absolute;left:0;top:0;width:10px;height:100%;border-radius:5px;'
        f'background:linear-gradient(180deg,{RED},{RED} 60%,#b81f1f);box-shadow:0 0 18px rgba(255,59,59,.7)"></div>'
        f'<div style="position:absolute;left:-9px;top:{r - 30 - 14:.0f}px;width:28px;height:28px;border-radius:50%;'
        f'background:{RED};border:6px solid {INK}"></div></div>',
    ]
    return (f'<div class="abs" style="left:{cx - r:.0f}px;top:{cy - r:.0f}px;width:{d:.0f}px;height:{d:.0f}px">'
            f'<div class="abs" style="inset:0;{style_anim(an("lcclockin", t0 + T_CLOCK, .7, EASE_OUT))}">'
            + "".join(parts) + "</div></div>")


def _bubble(cx: float, cy: float, size: float, t0: float) -> str:
    """A stopwatch bubble on the clock's rim counting 5..0 with the ticks: a
    crown on top, a thump on every second."""
    t_cd = t0 + T_CD
    crown = (f'<div class="abs" style="left:50%;top:-{size * .2:.0f}px;width:{size * .26:.0f}px;'
             f'height:{size * .16:.0f}px;margin-left:-{size * .13:.0f}px;border-radius:8px 8px 3px 3px;'
             f'background:{AMBER};box-shadow:0 4px 0 rgba(0,0,0,.35)"></div>')
    face = (f'<div class="abs" style="inset:0;border-radius:50%;background:{INK};'
            f'border:{size * .075:.0f}px solid {RED};box-shadow:0 10px 0 rgba(0,0,0,.35),0 0 40px rgba(255,59,59,.45);'
            f'display:flex;align-items:center;justify-content:center">'
            f'<span class="d count" style="font-size:{size * .6:.0f}px;line-height:1;color:#fff;padding-top:.06em;'
            f'{style_anim(an("lcnum", t_cd, CD, f"steps({CD},end)"))}"></span></div>')
    beat = style_anim(an("lcbeat", t_cd, 1.0, EASE_OUT, str(CD + 1)))
    pop = style_anim(an("pop", t0 + T_BUBBLE, .5, EASE_BACK))
    return (f'<div class="abs" style="left:{cx - size / 2:.0f}px;top:{cy - size / 2:.0f}px;width:{size:.0f}px;'
            f'height:{size:.0f}px;transform:rotate(8deg)"><div class="abs" style="inset:0;{pop}">'
            f'<div class="abs" style="inset:0;{beat}">{crown}{face}</div></div></div>')


def _ribbon(x: float, y: float, start: float, reset_et: str) -> tuple:
    """A red ribbon with a caution-striped amber tab and a swallow tail:
    LEAVING AT RESET, then the reset time. Returns (html, height)."""
    size = 54
    text = "LEAVING AT RESET"
    tw = _em(text) * size
    tab = 70
    body_w = tab + 30 + tw + 70
    h = 84
    unfurl = style_anim(an("lcunfurl", start, .55, EASE_BACK))
    shine = style_anim(an("lcshine", start + .7, .9, "ease-in-out"))
    blink = style_anim(an("lcblink", start + .5, .9, "linear", "infinite"))
    html = (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;transform:rotate(-3deg)">'
            f'<div style="position:relative;width:{body_w:.0f}px;height:{h}px;transform-origin:0 50%;{unfurl}">'
            # shadow copy for depth
            f'<div class="abs" style="left:6px;top:10px;width:{body_w:.0f}px;height:{h}px;background:rgba(0,0,0,.35);'
            f'clip-path:polygon(0 0,100% 0,calc(100% - 34px) 50%,100% 100%,0 100%)"></div>'
            f'<div class="abs" style="left:0;top:0;width:{body_w:.0f}px;height:{h}px;overflow:hidden;'
            f'background:linear-gradient(180deg,#ff5a4f,{RED} 55%,#d92a2a);'
            f'clip-path:polygon(0 0,100% 0,calc(100% - 34px) 50%,100% 100%,0 100%)">'
            f'<div class="abs" style="left:0;top:0;width:{tab}px;height:{h}px;background:repeating-linear-gradient('
            f'-45deg,{AMBER} 0 14px,{INK} 14px 28px)"></div>'
            f'<div class="abs" style="left:{tab}px;top:0;width:6px;height:{h}px;background:{INK}"></div>'
            f'<div class="abs" style="left:{tab + 22}px;top:{h / 2 - 8:.0f}px;width:16px;height:16px;border-radius:50%;'
            f'background:#fff;box-shadow:0 0 12px #fff;{blink}"></div>'
            f'<div class="abs d" style="left:{tab + 52}px;top:{(h - size * .9) / 2 + 3:.0f}px;font-size:{size}px;'
            f'color:#fff;white-space:nowrap;text-shadow:0 4px 0 rgba(0,0,0,.25)">{esc(text)}</div>'
            f'<div class="abs" style="left:0;top:0;width:90px;height:100%;background:linear-gradient(90deg,'
            f'transparent,rgba(255,255,255,.45),transparent);{shine}"></div>'
            f'</div></div>'
            # the reset time hangs off the tail on an amber tag
            f'<div class="abs" style="left:{body_w - 10:.0f}px;top:{h - 8}px;transform:rotate(5deg)">'
            f'<div class="d" style="background:{AMBER};color:{INK};font-size:34px;padding:.16em .4em .08em;'
            f'border-radius:8px;white-space:nowrap;box-shadow:0 6px 0 rgba(0,0,0,.35);'
            f'{style_anim(an("pop", start + .45, .5, EASE_BACK))}">{esc(reset_et)}</div></div>'
            f'</div>')
    return html, h, body_w


def _wipe(comp: Comp, t: float):
    """A dark-red panel with a caution-stripe leading edge sweeps across each cut,
    so it lands like an edit, not a dissolve."""
    a = style_anim(an("lcwipe", t - .32, .64, "cubic-bezier(.75,0,.25,1)"))
    comp.add(f'<div class="abs" style="left:0;top:-200px;width:1800px;height:2320px;z-index:30;{a}">'
             f'<div style="position:absolute;inset:0;background:linear-gradient(90deg,#140404,#4a0b0b 55%,#1c0505)"></div>'
             f'<div style="position:absolute;top:0;bottom:0;right:-90px;width:90px;background:repeating-linear-gradient('
             f'45deg,{AMBER} 0 26px,{INK} 26px 52px)"></div>'
             f'<div style="position:absolute;top:0;bottom:0;left:-14px;width:14px;background:{RED}"></div>'
             f'</div>')
    comp.cue(t - .2, "whoosh")


def _includes(it: dict, x: float, y: float, width: float, start: float) -> tuple:
    """'INCLUDES Hana · Skull of Keleritas · ...' for bundles, at most two lines.
    Returns (html, height)."""
    names = _members(it)
    if not names:
        return "", 0
    size = 28
    per_line = width / (size * .56)          # Inter 600, generous average advance
    budget = per_line * 2 - 12 - 10
    shown, used = [], 0
    for n in names:
        extra = len(n) + 3
        if shown and used + extra > budget - 8:
            break
        shown.append(n)
        used += extra
    more = len(names) - len(shown)
    body = " · ".join(esc(n) for n in shown) + (f" · +{more} more" if more else "")
    lines = 1 if (12 + len(" · ".join(shown)) + (9 if more else 0)) <= per_line else 2
    html = (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{width:.0f}px;font-size:{size}px;'
            f'font-weight:600;line-height:1.3;color:rgba(255,255,255,.92);text-shadow:0 2px 8px rgba(0,0,0,.8);'
            f'{style_anim(an("rise", start, .45))}"><span style="font-weight:800;letter-spacing:.16em;'
            f'color:{AMBER};margin-right:.5em">INCLUDES</span>{body}</div>')
    return html, lines * size * 1.3


def _price_card(comp: Comp, ctx: Ctx, it: dict, t0: float) -> str:
    price = int(it["price"])
    reg = _regular(it)
    col = RARITY.get(it["rarity"], "#777")
    since = _since(it, ctx)
    size = 118
    t_card, t_roll = t0 + T_CARD, t0 + T_ROLL
    if reg:
        top = (f'<div class="abs" style="left:34px;top:24px;white-space:nowrap;font-size:22px;font-weight:800;'
               f'letter-spacing:.16em;color:#9AA0A6;{style_anim(an("rise", t_card + .1, .45))}">REGULAR PRICE '
               f'<span class="d" style="position:relative;display:inline-block;font-size:40px;letter-spacing:.01em;'
               f'color:rgba(255,255,255,.85);margin-left:.3em;vertical-align:-4px">{reg:,}'
               f'<span style="position:absolute;left:-6px;right:-6px;top:46%;height:6px;border-radius:4px;'
               f'background:{RED};transform:rotate(-5deg);transform-origin:0 50%;'
               f'{style_anim(an("lcgrow", t_roll + ROLL + .05, .25, "cubic-bezier(.6,0,.3,1)"))}"></span></span></div>')
        top_w = (13 * 22 * .78) + _em(f"{reg:,}") * 40 + 30
        comp.cue(t_roll + ROLL + .05, "slam")
    elif since:
        top = label(since, 34, 24, 22, t_card + .1, "#9AA0A6", 800, spacing=".16em")
        top_w = len(since) * 22 * .78
    else:
        top, top_w = "", 0
    py = 64 if top else 18
    card_w = max(_price_w(price, size) + 70, top_w + 70)
    card_h = py + size + 16
    shine = (f'<div class="abs" style="left:0;top:-20%;width:200px;height:140%;background:linear-gradient(90deg,'
             f'transparent,rgba(255,255,255,.2),transparent);{style_anim(an("lcshine", t_roll + ROLL, .8, "ease-in-out"))}"></div>')
    card = (f'<div class="abs" style="left:0;top:0;width:{card_w:.0f}px;height:{card_h:.0f}px;border-radius:22px;'
            f'background:rgba(10,10,11,.9);border:3px solid rgba(255,255,255,.12);overflow:hidden;'
            f'box-shadow:0 14px 0 rgba(0,0,0,.35)">{shine}</div>'
            f'<div class="abs" style="left:0;top:0;width:12px;height:{card_h:.0f}px;border-radius:22px 0 0 22px;'
            f'background:{col}"></div>' + top
            + _from(t_roll, price_roll(price, 34, py, size, t_roll, ROLL)))
    y = CARD_BOTTOM - card_h
    out = (f'<div class="abs" style="left:{CARD_X}px;top:{y:.0f}px;width:{card_w:.0f}px;height:{card_h:.0f}px;'
           f'transform:rotate(-2deg)"><div class="abs" style="left:0;top:0;width:{card_w:.0f}px;height:{card_h:.0f}px;'
           f'{style_anim(an("rise", t_card, .45))}">{card}</div></div>')
    comp.cue(t_card, "whoosh"); comp.cue(t_roll, "reveal"); comp.cue(t_roll + ROLL, "cash")
    if reg:
        t_save = t_roll + ROLL + .35
        text = f"SAVE {reg - price:,}"
        sw = (_em(text) + .84) * 58
        sx, sy = CARD_X + card_w + 22, y + 34                 # beside the card...
        if sx + sw > SAFE_RIGHT - 16:                         # ...or on its top corner
            sx, sy = min(CARD_X + card_w - 90, SAFE_RIGHT - 16 - sw), y - 62
        out += sticker(text, sx, sy, 58, t_save, rot=6)
        out += _from(t_save, burst(sx + sw / 2, sy + 40, t_save, ctx.seed + int(t0 * 10), n=20))
        comp.cue(t_save, "pop")
    return out


ENTRIES = ("drop", "fromL", "pop", "fromR")


def _offer(comp: Comp, ctx: Ctx, it: dict, k: int, n: int, t0: float, t1: float, enter: str):
    name = _shown_name(it)
    size, nl = _fit(name, NAME_W)
    name_bottom = NAME_Y + nl * size * .92
    col = RARITY.get(it["rarity"], "#777")

    inner = tile_bg(it.get("tile_colors") or [], it["rarity"], t0) + _scrim()

    y = name_bottom + 18
    incl = ""
    if it.get("is_bundle"):
        incl, ih = _includes(it, TEXT_X, y, 900, t0 + T_INCL)
        y += ih + (14 if ih else 0)
    rib_y = y + 4
    rib, rib_h, _ = _ribbon(TEXT_X - 22, rib_y, t0 + T_RIB, ctx.reset_et)

    # The cosmetic fills the space between the ribbon and the price card; the
    # clock is centred on it and a little bigger, so the art reads as framed.
    art_top = max(rib_y + rib_h + 34, 640)
    art_h = max(470, min(640, ART_BOTTOM - art_top))
    cy = ART_BOTTOM - art_h / 2
    d = min(760, art_h + 150)
    inner += _clock(CX, cy, d, t0)
    rim = d / 2 - 10
    bx, by = CX + rim * .87, cy - rim * .5          # two o'clock on the rim
    by = min(by, RAIL_TOP - 90)                     # right of x=960 would be rail: stay above it
    char = character(ctx.art(it), CX, cy, art_h, t0 + T_CHAR, enter, .7,
                     "float" if k % 2 else "sway", it["rarity"], name)
    inner += (f'<div class="full" style="transform-origin:{CX}px {cy:.0f}px;'
              f'{style_anim(an("lcgone", t0 + T_END, .4, "ease-in"))}">{char}</div>')
    inner += _bubble(bx, by, 138, t0)

    inner += label(_meta(it), TEXT_X, PILL_Y, 26, t0 + T_PILL, _ink_on(col), 800, bg=col,
                   pad="8px 16px 7px", rot=-2, spacing=".14em")
    inner += words(name, TEXT_X, NAME_Y, size, t0 + T_NAME, "#fff", .08, "slam", "left", NAME_W)
    inner += incl + rib
    inner += _price_card(comp, ctx, it, t0)
    inner += _heat(t0)
    inner += progress(t0, t1, k, n).replace(">ROUND ", ">OFFER ", 1)

    if enter == "drop":
        comp.cue(t0 + T_CHAR + .42, "slam")
    elif enter == "pop":
        comp.cue(t0 + T_CHAR, "pop")
    comp.cue(t0 + T_NAME, "slam")
    comp.cue(t0 + T_BUBBLE, "pop")
    comp.cue(t0 + T_RIB, "whoosh")
    for s in range(CD):
        comp.cue(t0 + T_CD + s, "tick")
    comp.cue(t0 + T_END, "slam")
    comp.scene(t0, t1, inner, fade_in=.2, fade_out=.2)


# ---------------------------------------------------------------- build

def build(ctx: Ctx):
    leaving = _leaving(ctx)
    if len(leaving) < MIN_OFFERS:
        return None
    picked = _pick(ctx, leaving)
    if len(picked) < MIN_OFFERS:
        return None
    n = len(picked)
    content_end = HOOK + n * R
    comp = Comp(content_end + _pad(content_end))
    for rule in _css():
        comp.css(rule)

    show = _showcase(picked)
    a_item = show[0]
    b_item = show[1] if len(show) > 1 else None
    _hook_scene(comp, ctx, "LAST CHANCE", "LEAVING THE SHOP AT THE NEXT RESET",
                f"GONE AT {ctx.reset_et}", HOOK + .3, a_item, b_item,
                colors=["#6a1010", "#140405"])
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.3, "whoosh"); comp.cue(.9, "pop")

    off = rng(ctx, 42).randrange(len(ENTRIES))
    for k, it in enumerate(picked, 1):
        t0 = HOOK + (k - 1) * R
        _wipe(comp, t0)
        _offer(comp, ctx, it, k, n, t0, t0 + R, ENTRIES[(k + off) % len(ENTRIES)])

    _wipe(comp, content_end)
    comp.cue(content_end + .25, "slam"); comp.cue(content_end + .5, "reveal")
    comp.cue(content_end + 1.1, "pop")
    _outro_scene(comp, ctx, content_end, comp.duration, "WHICH ONE ARE YOU GRABBING?", show[:3])
    comp.add(code_badge(.4))
    comp.add(disclosure())
    comp.cues.sort()

    # ---- words for the post
    def line(it):
        if it.get("is_bundle"):
            bn = int(it.get("bundle_size") or 0) or len(_members(it))
            s = f"• {_shown_name(it)} bundle ({bn} items) — {int(it['price']):,} V-Bucks"
            reg = _regular(it)
            return s + (f" (regular price {reg:,})" if reg else "")
        s = f"• {it['name']} — {it.get('rarity_label') or it['rarity']} {it['type']}, {int(it['price']):,} V-Bucks"
        d = it.get("in_day") or ""
        if d and d != ctx.day.isoformat():
            s += f" (in the shop since {_mon_d(d)})"
        elif d:
            s += " (added today)"
        return s

    head = (f"LAST CHANCE ⏰ {n} offers leaving the Fortnite item shop at the next reset "
            f"({ctx.reset_et}, {ctx.day_label})")
    tail = (f"All of these are scheduled to leave the shop at the next reset ({ctx.reset_et}). "
            f"{len(leaving)} offers in today's shop leave at that reset; these are {n} of them, "
            f"priciest first.")
    names = [_shown_name(i) for i in picked]
    tags = _hashtags("lastchance", *names)
    tags = BRAND_TAGS + [t for t in tags if t not in BRAND_TAGS]      # brand tags always lead
    lines = [line(i) for i in picked]
    ask = "Which one are you grabbing? 👇"
    caption = _caption(head, "\n".join(lines) + "\n\n" + tail, ask, tags)
    # _caption trims to the platform limit from the end, where the hashtags are:
    # drop offer lines rather than ever losing the brand tags.
    while lines and not all(f"#{t}" in caption.split() for t in BRAND_TAGS):
        lines.pop()
        caption = _caption(head, "\n".join(lines) + "\n\n" + tail, ask, tags)

    title = f"Last Chance — Fortnite shop {ctx.day_label}"
    yt = f"Last Chance: Leaving the Fortnite Item Shop at Reset ({ctx.day_label}) #shorts"
    if len(yt) > 100:
        yt = f"Last Chance: Fortnite Item Shop {ctx.day_label} #shorts"
    return Video(FORMAT, comp, title=title[:60], yt_title=yt, caption=caption, hashtags=tags)
