"""
TODAY'S ITEM SHOP, as an edit: the daily recap of today's shop cut the way a
fan account cuts "item shop today" on TikTok, to a real track (cc_edit) -- the
same picks, facts and truth rules as the classic cc_fmt_shop_recap.

    build(ctx)

  cover   frame 0: "this is today's item shop 🛒" in the white box, the day
          huge in outline top right ("sep 23"), three of the day's standout
          items on tiles with their prices, "N offers in the shop today"; a bar
          later "here's what's in it 👀". From the first beat a voice says
          "This is today's Item Shop for September 23rd" (the owner's opening,
          2026-10-28: the first three seconds decide whether people stay)
  bundle  (when the shop has one) the classic's headline bundle, on
          on_this_day's screen: when Epic lists a regular price above today's,
          the regular price huge in white, struck through on the beat, then
          rolling down to today's price in lime, which lands on a bar line
          (flash, boom, shake) and "save 5,800 V-Bucks 🔥"; else today's price
          counting up. Its kicker ("biggest bundle saving today") and what's
          in it ("19 items: Sora, Riku, Kairi & more") in the caption slot.
  items   the classic's standout singles, one a screen, every cut on a bar
          line with a whip or a zoom through it: the price counts up huge top
          right and lands with a hit, the name along the tile's foot, and one
          caption slot above it that changes on the beat with the facts the
          classic shows: "leaves at the next reset ⏰" and the reset time in
          ET, "new in today's shop 🆕" / "added sep 22 🆕", "og · chapter 1,
          season 8 🔥" / "from chapter 2, season 3", its rarity and type, its
          shop section
  outro   everything shown lined up with its price, "what are you buying?
          👇", "use code BAD in the item shop 💚"

Every screen is a whole number of bars (_plan picks them per track so the
content runs 57-84.8 s; the caller's end card adds 5.1 s). Everything on screen
comes from the classic's own data functions: _headline_bundle (the bundle and
its kicker), _pick_items (the items and their order), _facts (leaves at the
next reset / added / OG), ctx.reset_et (the reset time, computed). Singles are
never shown with a regular price; only a bundle carries one, and only when
Epic's regular price is above today's ("regular price", "save": never
"discount"). Nothing about popularity, ratings, "back" or "never again".
"""

import math
from datetime import date

import cc_edit as ED
from cc_edit_on_this_day import _em, _grid, _name_fit
from cc_fmt_shop_recap import _clean_name, _facts, _headline_bundle, _pick_items
from cc_formats import BRAND_TAGS, Ctx, Video, _caption, _hashtags, kind_word, singles
from cc_motion import FPS, H, esc, trim_for

MIN_CONTENT = 57.0              # + the 5.1 s end card = 62.1 s
MAX_CONTENT = 84.8              # + 5.1 s = 89.9 s (Facebook Reels stop at 90)
MAX_ITEMS = 8                   # the classic shows 7; a quick track can take one more
FRAME = 1 / FPS                 # a caption handing its place to the next goes a frame early

# on_this_day's year screen: the tile in the column beside the button rail,
# the price huge top right beside the code sticker (where the year is), the
# line under it where the date is, the name along the tile's foot.
TILE_X, TILE_Y, TILE_W, TILE_H = 150, 540, 660, 760
TILE_CX = TILE_X + TILE_W / 2
MID = 480                       # centre of the column x 60-900
TOP_R = 1010                    # right edge of the line under the price
PRICE_R = 1000                  # right edge of the price's digits (their black edge reaches ~1017)
PRICE_F = 224                   # the year's size; a long price gets smaller
PRICE_ROOM = 570                # x 430-1000: clear of the code sticker (x <= ~400)
DIGITS_FOOT = 429               # the digits' bottom edge (TikTok Sans: digits sit .27-.99 em down)
UNDER_Y = 462                   # the line under the price
NAME_FOOT = 1400                # the name's bottom edge (the apps' captions start at 1420)
SLOT_F, SLOT_LIME = 44, 54      # the caption slot above the name: a fact, a highlight
SLOT_W = 820
TRANSITIONS = ["whip_up", "zoom", "whip_left", "zoom"]
STRIKE = "#FF3B3B"              # the classic's red


# ------------------------------------------------------------------ timing

def _plan(beat: ED.Beat, n_max: int, bundle: bool) -> dict | None:
    """Units per part: every item the same whole number of bars, about 6 s an
    item, as many items as the classic shows (up to MAX_ITEMS), the content
    between MIN_CONTENT and MAX_CONTENT. None when the day's items can't fill
    it without dragging (a thin shop: the slot falls back)."""
    u, per = beat.unit, beat.period
    n_min = 4 if bundle else 5
    best = None
    for n in range(n_max, n_min - 1, -1):
        for k in (8, 12, 16):
            if not 4.4 <= k * per <= 8.4:
                continue
            for hook in (8, 4):
                if not 2.8 <= hook * per <= 5.8:
                    continue
                for kb in ((8, 12, 16) if bundle else (0,)):
                    if bundle and not 5.6 <= kb * per <= 10.0:
                        continue
                    for outro in (8, 12, 16):
                        if not 5.0 <= outro * per <= 9.0:
                            continue
                        total = hook + kb + n * k + outro
                        secs = u(total)
                        if not MIN_CONTENT <= secs <= MAX_CONTENT:
                            continue
                        score = (abs(k * per - 6.0) + .45 * (min(n_max, 7) - n) + .12 * max(0.0, secs - 66)
                                 + .15 * abs(outro * per - 6.5) + .1 * abs(kb * per - 8.0)
                                 + .15 * abs(hook * per - 4.0) + (.6 if n > 7 else 0))
                        if best is None or score < best[0]:
                            best = (score, dict(n=n, k=k, hook=hook, bundle=kb, outro=outro, total=total))
    return best[1] if best else None


def _marks(k: int) -> tuple:
    """For an item screen of k units: the unit its price lands on, and the
    units where the caption slot changes."""
    return {8: (2, [3, 5]), 12: (4, [5, 8]), 16: (4, [5, 8, 12])}[k]


# ------------------------------------------------------------------ the price

def _dig_em(text: str) -> float:
    """About how wide a price is in TikTok Sans 900, in em, with its black
    edge (measured: a digit ~.65 em, a 1 ~.45, the comma ~.2); a little over."""
    return sum(.45 if c == "1" else .2 if c in ",." else .66 for c in text) + .16


def _price_size(*texts: str) -> float:
    """One size for the price (and whatever it rolls from) that fits beside the code sticker."""
    return min(PRICE_F, min(PRICE_ROOM / _dig_em(t) for t in texts))


def _svg_num(text: str, width: float, size: float, lime: bool) -> str:
    """ED.outline's SVG text (round joins on the black edge), right-aligned."""
    return (f'<svg width="{width:.0f}" height="{1.3 * size:.0f}" style="display:block;overflow:visible">'
            f'<text x="{width:.0f}" y="{size:.1f}" text-anchor="end" font-family="TikTok Sans" font-weight="900" '
            f'font-size="{size:.0f}" fill="{ED.LIME if lime else "#fff"}" stroke="#000" '
            f'stroke-width="{.15 * size:.1f}" stroke-linejoin="round" paint-order="stroke">{esc(text)}</text></svg>')


def _roll(frm: int, to: int, size: float, start: float, land: float, lime: bool = False,
          pulses: tuple = (), steps: int = 12, width: float = 640, first: float | None = None) -> str:
    """The price in the outline style where on_this_day has its year: it rolls
    from `frm` to `to` between start and land (fast, then easing into it), and
    the exact figure lands on `land` with a beat, giving a little on each of
    `pulses` (the bars). A counter can't be SVG text, so each step is its own
    text, shown until the next one's start exactly (no frame without a
    number, none with two); the first step shows from `first` (default:
    start), e.g. before the scene's cut so it's there on the cut's frame."""
    top = DIGITS_FOOT - .99 * size
    left = PRICE_R - width
    html = ""
    dur = max(.05, land - start)
    for i in range(steps):
        # a count up never shows 0 (a price of "0 V-Bucks", even for a few frames, reads as free)
        p = (i + 1) / (steps + 1) if frm == 0 else i / steps
        v = frm + (to - frm) * (1 - (1 - p) ** 2)
        q = 10 if max(frm, to) >= 200 else 1
        v = int(round(v / q)) * q
        v = min(v, to - q) if frm < to else max(v, to + q)     # the landing always changes the figure
        a, b = start + dur * i / steps, start + dur * (i + 1) / steps
        if i == 0 and first is not None:
            a = first
        show = f'{ED._anim("fadein", a, .001, "linear")},{ED._anim("edhide", b, .001, "linear", "forwards")}'
        html += (f'<div class="ed-cap" style="left:{left:.0f}px;top:{top:.0f}px;width:{width:.0f}px;'
                 f'height:{1.3 * size:.0f}px"><div style="height:100%;animation:{show}">'
                 f'{_svg_num(f"{v:,}", width, size, lime)}</div></div>')
    return html + ED.outline(f"{to:,}", PRICE_R, top, size, land, lime=lime, width=width, pulses=pulses,
                             anim="edbeat")


def _regular(value: int, size: float, start: float, strike: float, end: float, width: float = 640) -> str:
    """Epic's regular price, huge in white, and the red line struck through it at `strike`."""
    top = DIGITS_FOOT - .99 * size
    text = f"{value:,}"
    html = ED.outline(text, PRICE_R, top, size, start, end, width=width)
    w = _dig_em(text) * size
    y = top + .6 * size
    html += (f'<div class="ed-cap" data-safe="ignore" style="left:{PRICE_R - w - 6:.0f}px;'
             f'top:{y - .065 * size:.0f}px;width:{w + 20:.0f}px;height:{.13 * size:.0f}px;transform:rotate(-7deg)">'
             f'<div style="width:100%;height:100%;border-radius:12px;background:{STRIKE};'
             f'box-shadow:0 0 0 5px #000,0 8px 16px rgba(0,0,0,.4);transform-origin:0 50%;'
             f'animation:{ED._anim("strike", strike, .2, "cubic-bezier(.6,0,.3,1)")},'
             f'{ED._anim("edhide", end, .001, "linear", "forwards")}"></div></div>')
    return html


# ------------------------------------------------------------------ words

def _day(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d:%b} {d.day}".lower()                     # "sep 22"


def _cap_up(text: str, x: float, foot: float, size: float, start: float, end: float | None = None, **kw) -> str:
    """ED.caption standing on `foot` (its bottom edge) instead of hanging from a
    top: however many lines the app's text wrapping gives it, it grows upward
    and never runs into what's under it."""
    html = ED.caption(text, x, -9999, size, start, end, **kw)
    up = html.replace("top:-9999px;", f"bottom:{H - foot:.0f}px;", 1)
    if up == html:                                       # the kit's markup changed: place it by an estimate
        lines = max(1, math.ceil(_em(text) * size / (kw.get("width", 840) - 10)))
        up = ED.caption(text, x, foot - lines * size * kw.get("lh", 1.36), size, start, end, **kw)
    return up


def _members(b: dict, room: int = 64) -> str:
    """What a bundle holds, like the classic's band: "19 items: Sora, Riku,
    Kairi & more" -- the names that fit two lines of the slot."""
    seen, names = set(), []
    for nm in b.get("member_names") or []:
        nm = (nm or "").strip()
        if nm and nm.lower() not in seen:
            seen.add(nm.lower())
            names.append(nm)
    count = int(b.get("bundle_size") or 0)
    head = f"{count} items" if count else "includes"
    if not names:
        return f"{head} in the bundle" if count else ""
    shown = []
    for i, nm in enumerate(names):
        more = " & more" if i + 1 < len(names) else ""
        if len(f"{head}: " + ", ".join(shown + [nm]) + more) > room:
            break
        shown.append(nm)
    if not shown:
        return f"{head} in the bundle"
    return f"{head}: " + ", ".join(shown) + (" & more" if len(shown) < len(names) else "")


def _kind(it: dict) -> str:
    """'legendary outfit', 'icon series outfit': the classic's pill, lower case."""
    return f'{it.get("rarity_label") or ""} {it.get("type") or ""}'.strip().lower()


def _lines(it: dict, ctx: Ctx, room: int) -> list:
    """The caption slot's lines for an item, as (text, style): every fact the
    classic's _facts finds, then its rarity and type, then its shop section,
    as many as the screen has slots for."""
    kinds = {k for k, _ in _facts(it, ctx)}
    intro = it.get("introduction") or {}
    ch, se = str(intro.get("chapter") or ""), str(intro.get("season") or "")
    cand = []                                            # (priority, order, text, style)
    if "leaves" in kinds:
        cand.append((0, 0, "leaves at the next reset ⏰", "lime"))
        cand.append((2, 1, f"the reset is at {ctx.reset_et} 👀", "dark"))
    if "og" in kinds:
        if ch == "1":
            cand.append((1, 2, f"og · chapter 1, season {se} 🔥" if se else "og · chapter 1 🔥", "lime"))
        else:
            cand.append((1, 2, f"from chapter {ch}, season {se}" if se else f"from chapter {ch}", "dark"))
    if "added" in kinds:
        # the classic's ADDED SEP 22 / "🆕 = new today" (shop days are UTC days, as the shop's own dates)
        cand.append((1, 3, "new in today's shop 🆕" if it.get("in_day") == ctx.day.isoformat()
                     else f"added {_day(it['in_day'])} 🆕", "lime"))
    if _kind(it):
        cand.append((3, 4, _kind(it), "dark"))
    sec = (it.get("section") or "").strip()
    if sec and len(sec) <= 28:
        cand.append((4, 5, f"shop section: {sec}", "dark"))
    keep = sorted(cand, key=lambda c: c[:2])[:room]
    # leaving, but no room for the reset time on its own line: say it in the same line
    if any(c[1] == 0 for c in keep) and not any(c[1] == 1 for c in keep):
        keep = [(p, o, f"leaves at the next reset ({ctx.reset_et}) ⏰" if o == 0 else t, s) for p, o, t, s in keep]
    return [(t, s) for _, _, t, s in sorted(keep, key=lambda c: c[1])]


# ------------------------------------------------------------------ build

def build(ctx: Ctx, **_):
    head, kicker = _headline_bundle(ctx)
    n_max = min(MAX_ITEMS, len({i["name"] for i in singles(ctx)}))
    beat = ED.music_for(ctx.seed, "hype", day=ctx.day, salt="shop_recap")
    u = beat.unit
    plan = _plan(beat, n_max, bool(head))
    if plan is None:
        return None                                      # too little in the shop for an honest recap
    items = _pick_items(ctx, head, plan["n"])
    if len(items) < plan["n"]:
        return None
    K = plan["k"]
    content_end = u(plan["total"])
    ed = ED.Edit(beat, content_end, ctx.seed)
    cam, rnd = ed.cam, ed.rnd
    offers = int(ctx.shop.get("item_count") or len(ctx.shop.get("items", [])))

    def tile_for(it, x, y, w, h, fig=.95, **kw):
        iid = ed.uid("t")
        return iid, ED.tile(ed.src(ctx.art(it)), it, x, y, w, h, iid, trim=trim_for(it), fig=fig, **kw)

    def cut(t: float, move: str, hit: str = "impact"):
        """Into a screen at t: a whip or a zoom through the cut, a swoosh into it, a hit on it."""
        ed.cue(t - .16, "swoosh")
        ed.cue(t, hit)
        cam.punch(t, .08)
        if move == "zoom":
            cam.zoom(t, .45)
        else:
            cam.whip(t, *((0, -1) if move == "whip_up" else (-1, 0)), px=560 if move == "whip_up" else 480)

    def name_line(text: str, start: float) -> tuple:
        """The name along the tile's foot: (its top y, the caption)."""
        size, lines = _name_fit(text)
        y = NAME_FOOT - lines * size * 1.3
        return y, ED.caption(text, MID, y, size, start, width=820, weight=800, rot=rnd.choice([-2, -1, 1, 2]),
                             lh=1.3, extra="white-space:nowrap" if lines == 1 else "")

    def slot(lines: list, times: list, foot: float) -> str:
        """One caption slot standing on `foot`: each line from its time to the
        next one's (a frame early, so two never show at once). A fact in a dark
        box; a highlight in lime, bigger and tilted."""
        html = ""
        n = min(len(times), len(lines))
        for i in range(n):
            t, (text, style) = times[i], lines[i]
            end = times[i + 1] - FRAME if i + 1 < n else None
            dark = style == "dark"
            html += _cap_up(text, MID, foot, SLOT_F if dark else SLOT_LIME, t, end, style=style, width=SLOT_W,
                            weight=700 if dark else 800, rot=0 if dark else rnd.choice([-3, -2, 2, 3]))
            ed.cue(t, "pop2")
            cam.punch(t, .02 if dark else .035, .25)
        return html

    def bar_punches(s0: int, k: int, busy: set):
        """A light punch on each bar of a screen with nothing else on it."""
        for b in range(4, k, 4):
            if all(abs(b - x) >= 1 for x in busy):
                cam.punch(u(s0 + b), .025, .25)

    # ------------------------------------------------------------ cover
    t1 = u(plan["hook"])
    t_half = u(plan["hook"] // 2)
    title = "this is today's item shop 🛒"
    ed.say(.25, f"This is today's Item Shop for {ctx.day:%B} {ED.ordinal(ctx.day.day)}!")
    tsize = min(86.0, 940 / _em(title))
    title_y = 530
    over = ED.caption(title, 540, title_y, tsize, -1, width=960, rot=-1.5)
    over += ED.outline(f"{ctx.day:%b} {ctx.day.day}".lower(), PRICE_R, 296, 132, -1, width=600)   # "sep 23"
    lead = [i for i in items if i["type"] == "Outfit"]
    lead = (lead + [i for i in items if i not in lead])[:3]
    cy = title_y + tsize * 1.36 + 34
    chh = 1286 - cy
    gap = 18
    cw = (840 - (len(lead) - 1) * gap) / len(lead)
    tiles, first = "", ""
    for i, it in enumerate(lead):
        x = 60 + i * (cw + gap)
        rot = (-2, 1.5, -1.5)[i % 3]
        iid, html = tile_for(it, x, cy, cw, chh, extra=f"transform:rotate({rot}deg)")
        first = first or iid
        tiles += html
        over += ED.caption(f"{int(it['price']):,}", x + cw / 2, cy + chh - 76, 44, -1, width=cw, weight=900, rot=rot)
    ed.scene(0, t1, ED.canvas(first, ED.tile_colors(lead[0]), 1.0, .55) + tiles)
    over += ED.caption(f"{offers} offers in the shop today", MID, 1318, 42, -1, t_half - FRAME, style="dark",
                       weight=700, width=840)
    over += ED.caption("here's what's in it 👀", MID, 1314, 50, t_half, width=840, rot=2)
    ed.over(0, t1, over)
    cam.push(0, t1, 1.0, 1.05, 480, 1030)
    cam.punch(t_half, .06)
    ed.cue(t_half, "impact")
    ed.cue(t_half, "pop2")
    ui = plan["hook"]
    ci = 0                                               # cuts so far, for the transitions
    shown = []                                           # (item, price) in order, for the outro

    # ------------------------------------------------------------ the bundle
    if head:
        kb = plan["bundle"]
        s0 = ui
        start, end = u(s0), u(s0 + kb)
        bu = lambda i, s0=s0: u(s0 + i)                   # noqa: E731 -- unit i of this screen
        price, reg = int(head["price"]), int(head.get("regular_price") or 0)
        deal = bool(head.get("discounted")) and reg > price
        iid, main = tile_for(head, TILE_X, TILE_Y, TILE_W, TILE_H)
        ed.scene(start, end, ED.canvas(iid, ED.tile_colors(head), 1.25, .45) + main)
        cam.push(start, end, 1.0, 1.05, TILE_CX, 920)
        t_name = 1 if kb >= 12 else 0
        ny, over = name_line(head.get("section") or _clean_name(head["name"]), bu(t_name))
        members = _members(head)
        if deal:
            # the regular price, struck through; today's price rolls down to land on a bar line
            land = {8: 4, 12: 6, 16: 8}[kb]
            roll0 = land - {8: 1.5, 12: 2, 16: 4}[kb]
            strike = roll0 - 1
            size = _price_size(f"{reg:,}", f"{price:,}")
            over += _regular(reg, size, start, bu(strike), bu(roll0))
            over += ED.caption("regular price", TOP_R, UNDER_Y, 36, start, bu(roll0), style="dark",
                               align="right", width=440, weight=700)
            over += _roll(reg, price, size, bu(roll0), bu(land), lime=True,
                          pulses=tuple(bu(b) for b in range(4, kb, 4) if b > land))
            over += ED.caption("V-Bucks today", TOP_R, UNDER_Y, 36, bu(roll0), style="dark", align="right",
                               width=440, weight=700)
            ed.cue(bu(strike), "impact")
            cam.shake(bu(strike), 10, .3, .6)
            for j in range(math.ceil(roll0), land):
                ed.cue(bu(j), "tick2")
            marks = [2 if kb >= 12 else 1, land + 1]
            lines = [(kicker.lower() + " 🔥", "dark"), (f"save {reg - price:,} V-Bucks 🔥", "lime")]
            if members and land + 4 <= kb - 2:
                lines.append((members, "dark"))
                marks.append(land + 4)
            over += ED.emoji("🔥", TILE_X + TILE_W - 60, TILE_Y + 70, 140, bu(land + 1), rot=14)
            busy = {0, strike, land, *marks}
        else:
            land = 4
            size = _price_size(f"{price:,}")
            over += _roll(0, price, size, start, bu(land), pulses=tuple(bu(b) for b in range(4, kb, 4) if b > land),
                          first=start - 1)
            over += ED.caption("V-Bucks", TOP_R, UNDER_Y, 36, start - 1, style="dark", align="right", width=440,
                               weight=700)
            for j in range(1, land):
                ed.cue(bu(j), "tick2")
            marks = [2]
            lines = [(kicker.lower() + (" 💸" if "PRICIEST" in kicker else " 🛒"), "dark")]
            if members:
                lines.append((members, "dark"))
                marks.append(land + 1)
            if any(k == "leaves" for k, _ in _facts(head, ctx)) and land + 4 <= kb - 2:
                lines.append((f"leaves at the next reset ({ctx.reset_et}) ⏰", "lime"))
                marks.append(land + 4)
            busy = {0, land, *marks}
        over += slot(lines, [bu(m) for m in marks], ny - 16)
        ed.over(start, end, over)
        # the landing
        ed.cue(bu(land), "boom" if deal else "impact")
        ed.cue(bu(land) + .03, "cash")
        cam.flash(bu(land), .5 if deal else .3, .22)
        cam.shake(bu(land), 24 if deal else 14, .45, 1.6 if deal else 1)
        cam.punch(bu(land), .1 if deal else .06, .38)
        cut(start, TRANSITIONS[ci % len(TRANSITIONS)])
        ci += 1
        bar_punches(s0, kb, busy)
        shown.append((head, price))
        ui += kb

    # ------------------------------------------------------------ the items
    land, marks = _marks(K)
    for it in items:
        s0 = ui
        start, end = u(s0), u(s0 + K)
        bu = lambda i, s0=s0: u(s0 + i)                   # noqa: E731
        price = int(it["price"])
        iid, main = tile_for(it, TILE_X, TILE_Y, TILE_W, TILE_H)
        ed.scene(start, end, ED.canvas(iid, ED.tile_colors(it), 1.25, .45) + main)
        cam.push(start, end, 1.0, 1.05, TILE_CX, 920)
        # the price counts up from the cut and lands with a hit
        size = _price_size(f"{price:,}")
        over = _roll(0, price, size, start, bu(land), pulses=tuple(bu(b) for b in range(4, K, 4) if b > land),
                     first=start - 1)
        over += ED.caption("V-Bucks", TOP_R, UNDER_Y, 36, start - 1, style="dark", align="right", width=440,
                           weight=700)
        ny, name = name_line(it["name"], bu(1))
        over += name
        lines = _lines(it, ctx, len(marks))
        over += slot(lines, [bu(m) for m in marks], ny - 16)
        if lines and lines[0][1] == "lime" and "reset" in lines[0][0]:
            over += ED.emoji("⏰", TILE_X + TILE_W - 60, TILE_Y + 70, 120, bu(marks[0]), rot=12)
        ed.over(start, end, over)
        for b in range(1, land):
            ed.cue(bu(b), "tick2")
        ed.cue(bu(land), "impact")
        ed.cue(bu(land) + .03, "cash")
        cam.punch(bu(land), .06, .32)
        cam.shake(bu(land), 12, .35, .8)
        cam.flash(bu(land), .22, .16)
        cut(start, TRANSITIONS[ci % len(TRANSITIONS)])
        ci += 1
        bar_punches(s0, K, {0, land, *marks[:len(lines)]})
        shown.append((it, price))
        ui += K

    # ------------------------------------------------------------ outro
    s0 = ui
    t_out = u(s0)
    tiles, labels, first, first_it = "", "", "", None
    for i, ((it, price), (x, y, w, h)) in enumerate(zip(shown, _grid(len(shown)))):
        iid, html = tile_for(it, x, y, w, h, fig=.92)
        if not first:
            first, first_it = iid, it
        tiles += html
        at = u(s0 + i / 2)                               # the prices ticked off on the eighth notes
        labels += ED.caption(f"{price:,}", x + w / 2, y + h - 46, 30, at, width=w + 20, weight=900)
        ed.cue(at, "pop2")
    ed.scene(t_out, content_end, ED.canvas(first, ED.tile_colors(first_it), 1.0, .6) + tiles)
    t_code = u(s0 + max(4, (len(shown) - 1) // 2 + 1))
    ed.over(t_out, content_end,
            ED.caption("what are you buying? 👇", 540, 540, 60, t_out, width=900, rot=-1.5)
            + labels
            + ED.caption("use code BAD in the item shop 💚", MID, 1334, 44, t_code, style="lime", width=820))
    cut(t_out, "whip_up")
    cam.push(t_out, content_end, 1.0, 1.04, 480, 1000)
    ed.cue(t_code, "pop2")
    cam.punch(t_code, .04, .3)
    for b in range(8, plan["outro"], 4):
        cam.punch(u(s0 + b), .025, .25)

    comp = ed.finish()
    return _post(ctx, comp, head, items, offers)


# ------------------------------------------------------------------ the post

def _post(ctx: Ctx, comp, head: dict | None, items: list, offers: int) -> Video:
    """The post's words for what this video shows, the way a person would write
    them: the opening the video speaks, the bundle, then one short line per item
    with the facts the classic shows (cc_fmt_shop_recap): its price, OG (from
    Chapter 1), new today, last day (leaves at the next reset)."""
    lead = f"{offers} offers in the shop today"
    deal = bool(head and head.get("discounted") and head["regular_price"] > head["price"])
    if head:
        hname = head.get("section") or _clean_name(head["name"])
        hsize = int(head.get("bundle_size") or 0)
        size = f" ({hsize} items)" if hsize else ""
        lead = (f"The {hname} bundle{size} is {head['price']:,} V-Bucks today, normally {head['regular_price']:,} 👀"
                if deal else f"The {hname} bundle{size} is in for {head['price']:,} V-Bucks")
    lines = []
    for it in items:
        notes = []
        if str((it.get("introduction") or {}).get("chapter") or "") == "1":
            notes.append("OG")
        if it.get("in_day") == ctx.day.isoformat():
            notes.append("new")
        if any(k == "leaves" for k, _ in _facts(it, ctx)):
            notes.append("last day")
        lines.append(f"{it['name']} {kind_word(it)} · {it['price']:,}" + (f" · {', '.join(notes)}" if notes else ""))

    names = ([head.get("section") or _clean_name(head["name"])] if head else []) + [i["name"] for i in items]
    tags = _hashtags("itemshoptoday", *names)
    tags = BRAND_TAGS + [t for t in tags if t not in BRAND_TAGS]      # brand tags always lead

    title = f"Today's Fortnite Item Shop — {ctx.day_label}"
    yt = f"Today's Fortnite Item Shop: {ctx.day_label} #shorts"
    if deal:
        cand = (f"Fortnite Item Shop {ctx.day_label}: {head.get('section') or _clean_name(head['name'])} "
                f"Bundle Saves {head['regular_price'] - head['price']:,} V-Bucks #shorts")
        if len(cand) <= 100:
            yt = cand
    return Video(
        "edit_shop_recap", comp,
        title=title[:60],
        yt_title=yt,
        caption=_caption(f"This is today's Item Shop for {ctx.day:%B} {ctx.day.day} 🛒\n{lead}",
                         "\n".join(lines), "What are you grabbing?", tags),
        hashtags=tags)
