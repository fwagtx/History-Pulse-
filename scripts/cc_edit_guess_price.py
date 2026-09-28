"""
GUESS THE PRICE, as an edit: today's shop, one item a round, cut the way a
person cuts a "guess the price" TikTok, to a real track (cc_edit) -- the same
items and truth rules as the classic cc_fmt_guess_price.

    build(ctx)

  cover   frame 0: "guess the price 💸", "item shop · sep 23" top right, the
          first two rounds' items on tiles side by side, each "? V-Bucks",
          "comment your guesses 👇"; a bar later "can you get all 5 right? 👀"
  rounds  five, each cut on a bar line (a zoom or a whip through it): the item
          on its tile, its name on the tile's foot and "? V-Bucks" across its
          bottom edge; "how much is this outfit? 🤔" above it; three choices
          pop in under it on the beat (A / B / C, lowest first: the real price
          and two other prices in today's shop, the right one's letter shuffled
          round to round); a 3-2-1 on the beat; the price rolls up and lands
          on the downbeat with a ding (the right choice lights lime, the other
          two dim, flash, shake); then a line about it, true to the data: the
          priciest / cheapest one so far, the same price as an earlier round,
          "leaves at the next reset ⏰", "introduced in chapter 2, season 1"
  outro   the five in the order played with their answers ("B · 1,200"),
          "how many did you get right? 👇", "use code BAD in the item shop 💚"

The items are the classic's _pick (a spread of today's prices: the cheapest
and priciest price points, a mix of types, never a straight cheap-to-pricey
run, an outfit first), five of its six. The price is the row's own `price`
(singles are never discounted: no "regular price" here at all); the question
names the row's own type, and its series ("icon series") where it fits -- no
plain rarity tier, so "rare" never reads as a scarcity claim. Nothing gives an
answer away before its reveal: the captions before it name only the type, the
choices are always in price order, and the post never lists the prices.
"""

import math

import cc_edit as ED
from cc_fmt_guess_price import _leaves_today, _pick
from cc_formats import Ctx, Video, _caption, _hashtags, num, singles
from cc_motion import FPS, trim_for

MIN_CONTENT = 57.0              # + the 5.1 s end card = 62.1 s
MAX_CONTENT = 84.0
ROUNDS = 5
HOOK, OUTRO = 8, 12             # units
# Bars of question and of reveal in a round of k units (the countdown is one bar).
PLAN = {12: (1, 1), 16: (2, 1), 20: (2, 2), 24: (3, 2), 28: (3, 3)}
FRAME = 1 / FPS                 # a caption handing its place to another goes a frame early

# The round screen: the item on one tile in the column beside the button rail
# (x 60-900 below y 740), the question above it, the choices under it.
TW, TH, TY = 600, 556, 706
TX = 480 - TW / 2               # 180
MID_X = 480                     # the middle of x 60..900
CAM_Y = TY + TH / 2             # 984: where the camera pushes in
Q_Y, Q_H, Q_W = 526, 152, 940   # the caption slot above the tile: the question, then the verdicts
COUNT_Y = TY + TH - 38          # the price sits across the tile's bottom edge
COUNT_SIZE = 64
BTN_Y, BTN_SIZE = 1334, 46      # the choices
BTN_X = (MID_X - 250, MID_X, MID_X + 250)
TOP_R = 1010                    # right edge of the round label, beside the code sticker
CD_SIZE = 200                   # the 3-2-1
# the cover: two tiles side by side, like higher or lower's
CW, CH = 400, 556
CX = (70, 490)
CCX = (CX[0] + CW / 2, CX[1] + CW / 2)


def _w(text: str, size: float) -> float:
    """About how wide `text` is in TikTok Sans 800 (.56 em a letter)."""
    return len(text) * .56 * size


def _fit(text: str, width: float, size: float, lo: float = 24, lines: int = 1) -> float:
    """A font size at which `text` fits `width` in `lines` lines."""
    return max(lo, min(size, lines * width * .92 / max(1.0, len(text) * .56)))


def _nlines(text: str, size: float, width: float) -> int:
    return max(1, math.ceil(_w(text, size) / (width * .92)))


# ------------------------------------------------------------------ the data

def _five(picked: list) -> list:
    """Five of the classic's six: keep the opener (an outfit when there is
    one) and the cheapest and priciest price points, drop a repeated price
    or type first, and never leave a straight cheap-to-pricey run."""
    if len(picked) <= ROUNDS:
        return picked
    prices = [p["price"] for p in picked]
    lo, hi = min(prices), max(prices)

    def run(order):
        ps = [p["price"] for p in order]
        return ps in (sorted(ps), sorted(ps, reverse=True))

    best = None
    for i, p in enumerate(picked):
        if i == 0:
            continue
        rest = picked[:i] + picked[i + 1:]
        rp = [x["price"] for x in rest]
        if min(rp) != lo or max(rp) != hi:
            continue
        key = (run(rest), prices.count(p["price"]) < 2, sum(x["type"] == p["type"] for x in picked) < 2, -i)
        if best is None or key < best[0]:
            best = (key, rest)
    return (best[1] if best else picked[:-1])[:ROUNDS]


LETTERS = "ABC"


def _choices(items: list, levels: list, rnd) -> list:
    """Three choices a round, lowest first: the real price and two other
    price points in today's shop, next to it. Which letter is right is spread
    over the rounds (never the same three rounds running), so the order gives
    nothing away. Returns [(prices, index of the right one)]."""
    places = [0, 1, 2, 0, 1, 2][:len(items)]
    for _ in range(40):
        rnd.shuffle(places)
        if not any(places[i] == places[i + 1] == places[i + 2] for i in range(len(places) - 2)):
            break
    out = []
    for it, want in zip(items, places):
        p = it["price"]
        below = [v for v in levels if v < p][::-1]          # nearest first
        above = [v for v in levels if v > p]
        n_below = min(want, len(below))
        if 2 - n_below > len(above):
            n_below = 2 - len(above)
        opts = sorted(below[:n_below] + [p] + above[:2 - n_below])
        out.append((opts, opts.index(p)))
    return out


def _kind(it: dict) -> str:
    """'outfit', 'icon series outfit': the row's type, and its series when it
    has one (never a plain rarity tier)."""
    typ = (it.get("type") or "item").strip().lower()
    series = (it.get("rarity_label") or "").strip().lower()
    return f"{series} {typ}" if series.endswith("series") else typ


def _question(it: dict) -> str:
    kind = _kind(it)
    typ = (it.get("type") or "item").strip().lower()
    plural = typ.endswith("s") and not typ.endswith("ss")
    q = f"how much {'are these' if plural else 'is this'} {kind}? 🤔"
    if len(q) > 44:                                          # the series doesn't fit: just the type
        q = f"how much {'are these' if plural else 'is this'} {typ}? 🤔"
    return q


def _verdicts(items: list, rnd) -> list:
    """After each reveal, one to three lines true to the data: how it compares
    with the rounds before (the priciest / cheapest so far, the same price as
    one of them) or a nudge; then what the classic shows after its reveal
    (leaves at the next reset, the season it was introduced), or how far
    into the game we are."""
    nudges = ["did you get it? 👀", "too easy? 😤", "be honest, did you get it? 👀", "who got this one? 🙋"]
    rnd.shuffle(nudges)
    n = len(items)
    out = []
    for r, it in enumerate(items):
        p, before = it["price"], items[:r]
        one = nudges[r % len(nudges)]
        same = next((b for b in before if b["price"] == p), None)
        if before and p > max(b["price"] for b in before):
            one = "the priciest one so far 💸"
        elif len(before) >= 2 and p < min(b["price"] for b in before):
            one = "the cheapest one so far 😅"
        elif same and len(same["name"]) <= 24:
            one = f"same price as {same['name']} 🤝"
        facts = []
        if it.get("_leaves"):
            facts.append("leaves at the next reset ⏰")
        intro = it.get("introduction") or {}
        ch, se = str(intro.get("chapter") or "").strip(), str(intro.get("season") or "").strip()
        if ch and se:
            facts.append(f"introduced in chapter {ch}, season {se} 🗓️")
        if r < n - 1:
            facts.append(f"{r + 1} down, {n - r - 1} to go 👀")
        out.append([one] + facts)
    return out


# ------------------------------------------------------------------ build

def build(ctx: Ctx, **_):
    items = _five(_pick(ctx))
    if len(items) < ROUNDS:
        return None
    levels = sorted({i["price"] for i in singles(ctx) if i.get("price")})
    if len(levels) < 3:
        return None                                      # no honest three-way choice
    n = len(items)
    beat = ED.music_for(ctx.seed, "hype", day=ctx.day, salt="guess_price")
    u = beat.unit
    # Units per round: the fewest that make the video long enough (a bar more
    # of outro rather than a longer round).
    k, outro = next(((k, o) for k in sorted(PLAN) for o in (OUTRO, OUTRO + 4)
                     if u(HOOK + n * k + o) >= MIN_CONTENT), (max(PLAN), OUTRO))
    total = HOOK + n * k + outro
    content_end = u(total)
    if content_end > MAX_CONTENT:
        return None
    nq, nr = PLAN[k]
    ed = ED.Edit(beat, content_end, ctx.seed)
    cam, rnd = ed.cam, ed.rnd
    rows = [dict(it, _leaves=_leaves_today(ctx, it)) for it in items]      # the classic's own leaving test
    choices = _choices(rows, levels, rnd)
    verdicts = _verdicts(rows, rnd)
    arts = [ctx.art(it) for it in items]

    def tile_for(i, x, y, w, h, **kw):
        iid = ed.uid("t")
        return iid, ED.tile(ed.src(arts[i]), items[i], x, y, w, h, iid, trim=trim_for(items[i]), **kw)

    def name_cap(i, cx, w, start, rot=0.0):
        """The item's name over the lower part of its tile, just above its price."""
        nm = items[i]["name"]
        size, lines = _fit(nm, w - 30, 36, 10), 1
        if size < 28:                                     # a long name: two lines rather than tiny
            size, lines = min(34.0, _fit(nm, w - 30, 36, 22, lines=2)), 2
        y = COUNT_Y - 4 - lines * 1.36 * size
        return ED.caption(nm, cx, y, size, start, style="dark", width=w - 10, weight=700, rot=rot)

    def count_cap(text, cx, w, start, end=None, raw=False, rot=0.0):
        """The price (or "? V-Bucks") across the bottom edge of its tile."""
        size = _fit("0,000 V-Bucks", w - 40, COUNT_SIZE, 40)
        return ED.caption(text, cx, COUNT_Y, size, start, end, width=w, weight=900, rot=rot, raw=raw, lh=1.28)

    def slot(text, start, end, size=52, rot=0.0, style="box"):
        """The one changing line above the tile."""
        size = _fit(text, Q_W - 60, size, 38, lines=2)
        lines = _nlines(text, size, Q_W - 60)
        y = Q_Y + max(0.0, (Q_H - lines * 1.36 * size) / 2)
        return ED.caption(text, 540, y, size, start, end, style=style, width=Q_W, weight=800, rot=rot)

    def choice(j, prices, text_style, start, end=None, anim="edpop", dim=False, rot=0.0):
        label = (f'<span style="font-size:.72em;opacity:.62;margin-right:.3em">{LETTERS[j]}</span>'
                 f'{prices[j]:,}')
        if dim:
            label = f'<span style="opacity:.5">{label}</span>'
        return ED.caption(label, BTN_X[j], BTN_Y, BTN_SIZE, start, end, style=text_style, width=240,
                          weight=900 if text_style == "lime" else 800, rot=rot, raw=True, anim=anim)

    # ------------------------------------------------------------ cover: units 0-8
    t_game = u(HOOK)
    id0, t0_html = tile_for(0, CX[0], TY, CW, CH, extra="transform:rotate(-2deg)")
    _, t1_html = tile_for(1, CX[1], TY, CW, CH, extra="transform:rotate(2deg)")
    ed.scene(0, t_game, ED.canvas(id0, ED.tile_colors(items[0]), 1.2, .5) + t0_html + t1_html)
    ed.over(0, t_game,
            ED.caption(f"item shop · {ctx.day:%b} {ctx.day.day}".lower(), TOP_R, 298, 44, -1, style="dark",
                       align="right", width=560, weight=800)
            + ED.caption("guess the price 💸", 540, 546, 88, -1, width=980, weight=900, rot=-2)
            + name_cap(0, CCX[0], CW, -1, -2) + name_cap(1, CCX[1], CW, -1, 2)
            + count_cap("? V-Bucks", CCX[0], CW, -1, rot=-2)
            + count_cap("? V-Bucks", CCX[1], CW, -1, rot=2)
            + ED.caption("comment your guesses 👇", MID_X, BTN_Y + 4, 40, -1, u(4) - FRAME,
                         style="dark", width=820, weight=800)
            + ED.caption(f"can you get all {n} right? 👀", MID_X, BTN_Y, BTN_SIZE, u(4), width=820,
                         weight=800, rot=2))
    cam.push(0, t_game, 1.0, 1.05, MID_X, CAM_Y)
    cam.punch(u(4), .06)
    ed.cue(u(4), "impact")
    ed.cue(u(4), "pop2")

    # ------------------------------------------------------------ the rounds
    ui = HOOK
    for r in range(n):
        it = items[r]
        prices, right = choices[r]
        last = r == n - 1
        s0 = ui
        start, end = u(s0), u(s0 + k)
        bu = lambda i, s0=s0: u(s0 + i)                   # noqa: E731 -- unit i of this round

        idr, tile = tile_for(r, TX, TY, TW, TH)
        ed.scene(start, end, ED.canvas(idr, ED.tile_colors(it), 1.2, .5) + tile)
        cam.push(start, end, 1.0, 1.04, MID_X, CAM_Y)

        # when things happen, in units of this round
        picks = {1: [2, 2.5, 3], 2: [4, 5, 6], 3: [4, 6, 8]}[nq]
        cd = 4 * nq                                       # 3, 2, 1, then the roll
        land = cd + 4                                     # the reveal, on a bar line
        t_q = bu(1)
        t_roll, t_land = bu(cd + 3), bu(land)
        marks = [land + 1] + ([land + 4] if nr >= 2 else []) + ([land + 8] if nr >= 3 else [])
        lines = verdicts[r][:len(marks)]

        over = ED.caption("final round 😤" if last else f"round {r + 1}/{n}", TOP_R, 300, 36, start - 1,
                          style="lime" if last else "dark", align="right", width=440, weight=800)
        over += name_cap(r, MID_X, TW, start - 1)
        # "? V-Bucks" becomes the rolling price in place: an exact hand-off (the kit's
        # 1 ms fades show the old one on the boundary frame, the new one right after)
        over += count_cap("? V-Bucks", MID_X, TW, start - 1, t_roll)
        over += count_cap(f"{ED.counter(it['price'], t_roll, t_land - t_roll)} V-Bucks", MID_X, TW, t_roll, raw=True)
        # the question, then what it was
        over += slot(_question(it), t_q, bu(marks[0]) - FRAME, rot=rnd.choice([-2, -1.5, 1.5, 2]))
        for j, (a, b) in enumerate(zip(marks, marks[1:] + [None])):
            if j < len(lines):
                over += slot(lines[j], bu(a), None if (b is None or j + 1 >= len(lines)) else bu(b) - FRAME, 54,
                             rot=rnd.choice([-3, -2, 2, 3]))
        # the choices, until the reveal lights them in place (an exact hand-off: no frame without them)
        for j in range(3):
            over += choice(j, prices, "box", bu(picks[j]), t_land, rot=(-2, 1, 2)[j])
        # 3, 2, 1 in the middle of the tile
        for j, word in enumerate("321"):
            over += ED.caption(word, MID_X, CAM_Y - CD_SIZE / 2, CD_SIZE, bu(cd + j), bu(cd + j + 1) - FRAME,
                               style="outlm" if word == "1" else "out", width=320, weight=900, lh=1.0,
                               anim="edslam")
        ed.over(start, end, over)
        # the reveal: the right choice lit, the other two dimmed
        rev = ""
        for j in range(3):
            if j == right:
                rev += choice(j, prices, "lime", t_land, anim="edin", rot=(-2, 1, 2)[j])
            else:
                rev += choice(j, prices, "dark", t_land, anim="edin", dim=True, rot=(-2, 1, 2)[j])
        ed.over(t_land, end, rev + ED.emoji("💸", TX + TW - 70, TY + 80, 120, t_land, rot=12))

        # sound and camera
        ed.cue(t_q, "pop2")
        for j in range(3):
            ed.cue(bu(picks[j]), "pop2")
        for j, amt in enumerate((.03, .04, .05)):
            ed.cue(bu(cd + j), "tick2")
            cam.punch(bu(cd + j), amt, .22)
        ed.cue(t_roll, "tick2")
        if last:
            ed.cue(t_land - 2.0, "riser")
        ed.cue(t_land, "boom" if last else "impact")
        ed.cue(t_land, "ding")
        cam.shake(t_land, 26 if last else 18, .45 if last else .38, 2 if last else 1.2)
        cam.punch(t_land, .1 if last else .06, .38)
        cam.flash(t_land, .6 if last else .4, .22)
        for m in marks[:len(lines)]:
            ed.cue(bu(m), "pop2")

        # the cut into this round
        ed.cue(start, "impact")
        if r % 2 == 0:                                    # zoom through (rounds 1, 3, 5)
            cam.zoom(start, .45)
            cam.punch(start, .06)
        else:                                             # whip
            cam.whip(start, -1, 0, 480)
            cam.punch(start, .05)
        ed.cue(start - .16, "swoosh")
        if last:
            ed.cue(start, "glitch")
            cam.flash(start, .35, .12)
        # a light punch on each bar with nothing else on it
        busy = {0, 1, *picks, cd, cd + 1, cd + 2, cd + 3, land, *marks[:len(lines)]}
        for bb in range(4, k, 4):
            if all(abs(bb - x) >= 1 for x in busy):
                cam.punch(bu(bb), .025, .25)
        ui += k

    # ------------------------------------------------------------ outro: the answers
    t_out, t_code = u(ui), u(ui + n + 1)
    gw, gh, gap = 250, 280, 30
    x0 = MID_X - (3 * gw + 2 * gap) / 2
    spots = [(x0 + (i % 3) * (gw + gap), 722 + (i // 3) * (gh + 24)) for i in range(n)]
    if n == 5:                                            # 3 over 2, the two centred
        spots[3:] = [(MID_X - gw - gap / 2, spots[3][1]), (MID_X + gap / 2, spots[4][1])]
    tiles, labels, first = "", "", ""
    for i, (x, y) in enumerate(spots):
        iid, html = tile_for(i, x, y, gw, gh, extra=f"transform:rotate({[-2, 1, -1, 2, -2][i % 5]}deg)")
        first = first or iid
        tiles += html
        prices, right = choices[i]
        at = u(ui + 1 + i)                                # one answer per beat
        labels += ED.caption(f"{LETTERS[right]} · {items[i]['price']:,}", x + gw / 2, y + gh - 48, 32, at,
                             width=gw + 20, weight=900)
        ed.cue(at, "pop2")
    ed.scene(t_out, content_end, ED.canvas(first, ED.tile_colors(items[0]), 1.0, .6) + tiles)
    ed.over(t_out, content_end,
            ED.caption("the answers ✅", TOP_R, 300, 36, t_out - 1, style="dark", align="right", width=440,
                       weight=800)
            + ED.caption("how many did you get right? 👇", 540, 548, 58, t_out, width=900, weight=800, rot=-1.5)
            + labels
            + ED.caption("use code BAD in the item shop 💚", MID_X, 1346, 44, t_code, style="lime",
                         width=820, weight=800))
    cam.whip(t_out, 0, 1, 560)
    ed.cue(t_out - .16, "swoosh")
    ed.cue(t_out, "impact")
    cam.push(t_out, content_end, 1.0, 1.04, MID_X, 1000)
    cam.punch(t_code, .05)
    ed.cue(t_code, "pop2")
    for b in range(8, outro, 4):
        cam.punch(u(ui + b), .025, .25)

    comp = ed.finish()

    # ------------------------------------------------------------ the post: the classic's words, no prices
    body = "\n".join(f"{num(i)} {it['name']} · {it['type']}" for i, it in enumerate(items, 1))
    tags = _hashtags("guesstheprice", *(it["name"] for it in items[:2]))
    music = comp.music or {}
    credit = (f"\n🎵 {music['title']} by {music['artist']} (public domain, CC0)" if music.get("artist") else "")
    return Video(
        "edit_guess_price", comp,
        title=f"Guess the Price — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"Guess the Price: Fortnite Item Shop {ctx.day_label} #shorts",
        caption=_caption(f"💸 GUESS THE PRICE — Fortnite Item Shop, {ctx.day_label}\n"
                         f"{n} items from today's shop. Pick A, B or C, then watch the reveal 👇" + credit,
                         body, f"How many did you get out of {n}? Comment your score", tags),
        hashtags=tags)
