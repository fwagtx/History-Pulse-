"""
COUNTDOWN, as an edit: the cut behind cc_edit_most_common, made reusable for
any list counted down from #N to #1 -- the rarest skins, the ones gone the
longest, today's comebacks, the oldest items in the shop, what leaves at
reset. A format picks its rows with its classic's own data functions, turns
each into an Entry, and gets back the finished edit (cc_edit's kit, cut to a
real track).

    cut(ctx, entries, salt=, title=, sub=, tease=, ask=, crown="👑") -> Comp | None

  entries  #1 first. Entry(item, stat, facts, react, name="", tag="", label="")
  stat     Stat(kicker, value=None, unit="", text="", guess="?"): a count with
           its unit that rolls up on the beat ("2,931 days", "1,500 v-bucks"),
           or, when the stat isn't a count, big words ("chapter 1, season 3",
           "only once") that stand as `guess` ("chapter ?, season ?") while
           the ticks run and slam in on the hit. `kicker` is the line above
           it: "gone for", "in the item shop", "back after".

  hook    frame 0 is the cover: `title` over the entries' tiles, `sub` under
          it; half-way through the hook "wait for #1 👀"
  items   #N to #2, the same whole number of bars each, cut on a bar line
          with a whip or a zoom-through (alternating): the rank in outline top
          right (it gives a little on every bar), the name under it, the
          kicker and the stat (rolling from the screen's second unit, landing
          on its sixth with a hit, a shake and a flash), then the facts one at
          a time in one caption slot and one line about it (`react`)
  #1      a bar (two on a long cut) of "and #1 is… 🥁" and `tease` over its
          silhouette with a riser, then the drop: flash, boom, shake, the rank
          in lime and `crown` on its tile
  outro   the entries lined up with their labels ("#1 · 2,931 days"), `ask`,
          "use code BAD in the item shop 💚"

Every screen is a whole number of bars and every cut lands on a bar line of
the track (cc_edit.music_for with the format's own `salt`, so two formats on
one day get different tracks). The units per item are chosen per track --
about 10 s an item, the content 57-84 s (the caller's end card adds 5.1 s) --
and so is how many of an entry's facts get a turn: each one stays up at
least 1.1 s, the line about it at least 2 s, and facts that don't fit that
are left off the screen (put the ones that matter first).

The layout is the reference's: the tile in the column beside the button rail
(x 150-810, y 540-1300), the rank and the name top right beside the code
sticker (which owns x 66-~400, y 283-~515 on every frame), the kicker and
the stat across the tile's foot, the caption slot above them. Captions never
stack: each fact goes a frame before the next one comes in; the outro's
tiles end above the "use code BAD" line (the reference's bottom row ran
under it).

Also here, for the formats: listed_today(ctx) -- the cosmetic ids in today's
shop listing --, day_str / span_str / years_since for the words, and
credit(comp) for the post's music line.
"""

import math
from dataclasses import dataclass, field
from datetime import date

import cc_edit as ED
import cc_rarity as R
from cc_edit_on_this_day import _em, _title
from cc_motion import FPS, esc, trim_for

MIN_CONTENT = 57.0              # + the 5.1 s end card = 62.1 s
MAX_CONTENT = 84.0              # + 5.1 s = 89.1 s (Facebook Reels stop at 90)

# The item screen (cc_edit_most_common's).
TILE_X, TILE_Y, TILE_W, TILE_H = 150, 540, 660, 760
TILE_CX = TILE_X + TILE_W / 2
TOP_R = 1010                    # right edge of the rank and the name (beside the code sticker)
MID = 480                       # the middle of x 60-900 (the column beside the button rail)
RANK_R, RANK_Y, RANK_F = TOP_R - 8, 250, 176     # its digits' ink ends about y 437
NAME_Y, NAME_W, NAME_F = 462, 600, 58
NAME2_Y = 448                   # a name on two lines starts here, under the rank, above the tile
KICK_Y, KICK_F = 1234, 36
STAT_Y, STAT_F = 1290, 86
STAT_W = 820
FACT_FOOT, FACT_F, FACT_W = 1218, 40, 780         # one line of a fact sits at y 1164
REACT_Y, REACT_F, REACT_W = 1060, 50, 780
HOOK_TILES = 790               # the top of the hook's tiles
FRAME = 1 / FPS
SILHOUETTE = "filter:brightness(0) drop-shadow(0 0 20px rgba(255,255,255,.4))"
TRANSITIONS = ["whip_up", "zoom", "whip_left", "zoom"]
HOOK_ROT = [-2, 3, -3, 2, -1, 1, -2, 2]

# (hook, #1's build-up, outro) in units, and how much less we like the shape;
# the units per item, a whole number of bars.
SHAPES = [((8, 4, 12), 0.0), ((8, 8, 12), .5), ((8, 8, 16), 1.0)]
KS = (12, 16, 20, 24, 28, 32, 36, 40)
PER_ITEM = 10.0                 # seconds an item, about
FACT_MIN, REACT_MIN = 1.1, 2.0   # seconds a fact / the line about it stays up, at least


@dataclass
class Stat:
    """The big number (or words) on an item's screen and the line above it."""
    kicker: str                 # "gone for", "in the item shop", "back after", "introduced in"
    value: int | None = None    # a count that rolls up on the beat...
    unit: str = ""              # ...and its unit ("days", "times", "v-bucks")
    text: str = ""              # big words when the stat isn't a count
    guess: str = "?"            # what the words stand as until the hit


@dataclass
class Entry:
    item: dict                  # the cosmetic on the tile (art, colours, type)
    stat: Stat
    facts: list = field(default_factory=list)   # one at a time in the caption slot, most important first
    react: str = ""             # one true line about it, after the facts
    name: str = ""              # on screen; default item["name"]
    tag: str = ""               # a little lime tag by the rank ("tied")
    label: str = ""             # under its tile in the outro: "#1 · <label>"


# ------------------------------------------------------------------ words

def day_str(d: date) -> str:
    """'sep 15, 2018' -- the captions' dates."""
    return f"{d:%b} {d.day}, {d.year}".lower()


def span_str(a: date, b: date) -> str:
    """'jul 26–28, 2019', 'feb 27 – mar 1, 2019', 'dec 31, 2021 – jan 1, 2022'."""
    if a == b:
        return day_str(a)
    if a.year != b.year:
        return f"{day_str(a)} – {day_str(b)}"
    if a.month != b.month:
        return f"{a:%b} {a.day} – {b:%b} {b.day}, {b.year}".lower()
    return f"{a:%b} {a.day}–{b.day}, {b.year}".lower()


def years_since(then: date, day: date) -> tuple:
    """(whole years from `then` to `day`, whether it's exactly that many)."""
    y = day.year - then.year - ((day.month, day.day) < (then.month, then.day))
    try:
        exact = then.replace(year=then.year + y) == day
    except ValueError:                                  # Feb 29
        exact = False
    return max(0, y), exact


def years_line(then: date, day: date, lead: str = "that's", tail: str = "") -> str:
    """'that's over 8 years 😭' / 'that was exactly 3 years ago 😭' -- '' under a year."""
    y, exact = years_since(then, day)
    if y < 1:
        return ""
    return f"{lead} {'exactly' if exact else 'over'} {y} year{'s' if y > 1 else ''}{tail} 😭"


def choose(options: list, rnd) -> list:
    """One line per entry from its true options [(kind, text), ...] (#1's
    first), picked in the order the screens play (#N first): a kind no screen
    has used yet when there is one, else one the screen before didn't use --
    in each case a specific line before a plain one (kind "~..."), so a video
    never says "welcome back 👋" three times."""
    out, used, prev = [""] * len(options), set(), None
    plain = lambda o: o[0].startswith("~")                # noqa: E731
    for i in range(len(options) - 1, -1, -1):
        opts = [o for o in options[i] if o[1]]
        if not opts:
            continue
        fresh = [o for o in opts if o[0] not in used]
        other = [o for o in opts if o[0] != prev]
        pool = ([o for o in fresh if not plain(o)] or fresh or [o for o in other if not plain(o)] or other
                or opts)
        kind, out[i] = pool[rnd.randrange(len(pool))]
        used.add(kind)
        prev = kind
    return out


def credit(comp) -> str:
    """The post's music line, when the track has an artist (the reference's)."""
    music = getattr(comp, "music", None) or {}
    return f"\n🎵 {music['title']} by {music['artist']} (public domain, CC0)" if music.get("artist") else ""


def listed_today(ctx) -> set:
    """The cosmetic ids (lower case) in today's shop listing. Empty when ctx.shop
    is another day's shop (a preview of an old day): it can't speak for that day."""
    shop = ctx.shop or {}
    if shop.get("shop_day") and shop["shop_day"] != ctx.day.isoformat():
        return set()
    return {i.lower() for row in shop.get("items", []) for i in R.shop_ids(row)}


# ------------------------------------------------------------------ fitting

def _fit(text: str, width: float, most: float, least: float) -> float:
    """The biggest size (least..most) at which `text` fits one line of `width`."""
    return max(least, min(most, width / max(1.0, _em(text))))


def _nlines(text: str, size: float, width: float) -> int:
    return max(1, math.ceil(_em(text) * size / (width * .94)))


def _fit_lines(text: str, width: float, most: float, least: float, lines: int = 2) -> tuple:
    """(size, lines): one line as big as fits down to `least`; else `lines` lines."""
    one = width / max(1.0, _em(text))
    if one >= least:
        return min(most, one), 1
    size = max(least * .85, min(most, lines * width * .9 / max(1.0, _em(text))))
    return size, _nlines(text, size, width)


def _name_fit(name: str) -> tuple:
    """(size, y) for the name under the rank: one line of 600 px as big as fits
    (up to 58 px, down to 34), else two lines of up to 34 px from y 448 -- clear
    of the rank's digits above (their edge ends ~y 437) and the tile's top edge
    (y 540) below."""
    one = NAME_W / max(1.0, _em(name))
    if one >= 34 or " " not in name.strip():
        return max(28.0, min(NAME_F, one)), NAME_Y
    return max(26.0, min(34.0, 2 * NAME_W * .9 / max(1.0, _em(name)))), NAME2_Y


def _title_html(text: str, width: float = 940, most: float = 72) -> tuple:
    """(html for raw=True, size, lines): two balanced lines (the emoji stays
    with the last word), or one line when it's short."""
    parts = text.split()
    if len(parts) >= 2 and parts[-1] and ord(parts[-1][0]) >= 0x2190:
        parts = parts[:-2] + [parts[-2] + " " + parts[-1]]
    if _em(text) * most <= width * .8 or len(parts) < 3:
        return esc(text), _fit(text, width, most, 40), 1
    try:
        return _title(parts, width, most, 44)
    except ValueError:
        size = _fit(text, 2 * width * .9, most, 36)
        return esc(text), size, _nlines(text, size, width)


# ------------------------------------------------------------------ timing

def _plan(beat: ED.Beat, n: int) -> dict | None:
    """Units per part: every item the same whole number of bars, about
    PER_ITEM seconds each, the content between MIN_CONTENT and MAX_CONTENT."""
    u, per = beat.unit, beat.period
    best = None
    for (hook, build, outro), pen in SHAPES:
        for k in KS:
            total = hook + n * k + build + outro
            if not MIN_CONTENT <= u(total) <= MAX_CONTENT:
                continue
            score = abs(k * per - PER_ITEM) + pen + (.8 if k == 12 else 0)
            if best is None or score < best[0]:
                best = (score, dict(k=k, hook=hook, build=build, outro=outro, total=total))
    return best[1] if best else None


def _slots(k: int, m: int, per: float) -> tuple:
    """(the units where each shown fact comes in, the unit of the line about
    it) within a screen of k units whose stat lands on unit 6. Up to two
    facts keep the reference's rhythm (k=20: 9, 12, then the line on 15); more
    spread evenly from unit 8. Facts that can't stay up FACT_MIN are dropped
    from the end."""
    f_min = max(2, math.ceil(FACT_MIN / per - 1e-9))
    r_min = max(3, math.ceil(REACT_MIN / per - 1e-9))
    while True:
        if m == 0:
            return [], max(7, min(round(.45 * k), k - r_min))
        if m <= 2:
            a = max(8, round(.45 * k)) if k >= 16 else 7
            r = max(a + f_min * m, round(.75 * k))
        else:
            a = 8
            r = max(a + f_min * m, round(a + (k - a) * m / (m + 1.6)))
        if k - r >= r_min:
            return [a + round((r - a) * i / m) for i in range(m)], r
        m -= 1


# ------------------------------------------------------------------ layout

def _grid(n: int, top: float, bottom: float, one_row_h: float = 420) -> list:
    """(x, y, w, h) of n tiles in rank order (#1 first), inside x 60-900: one
    row up to three, else two rows (the top one takes the odd one); in a
    three-wide row #1 is in the middle with #2 and #3 beside it, as in the
    reference."""
    if n <= 3:
        rows = [n]
    else:
        rows = [-(-n // 2), n // 2]
    cols = max(rows)
    gap = 45 if cols <= 3 else 24
    w = min(250.0, (840 - (cols - 1) * gap) / cols)
    if len(rows) == 1:
        h = min(one_row_h, bottom - top)
    else:
        h = min(w * 1.2, (bottom - top - 24) / 2)
    y0 = top
    spots = []
    for r, c in enumerate(rows):
        g = gap if c == cols else gap / 2
        row_w = c * w + (c - 1) * g
        x0 = MID - row_w / 2
        spots.append([(x0 + j * (w + g), y0 + r * (h + 24)) for j in range(c)])
    order = []
    for r, row in enumerate(spots):
        if r == 0 and len(row) == 3:
            row = [row[1], row[0], row[2]]
        order += row
    return [(x, y, w, h) for x, y in order]


# ------------------------------------------------------------------ the cut

def cut(ctx, entries: list, *, salt: str, title: str, sub: str, tease: str, ask: str, crown: str = "👑",
        wait: str = "wait for #1 👀"):
    """The countdown edit of `entries` (#1 first), or None when no cut of them
    fits 57-84 s on the day's track."""
    n = len(entries)
    if n < 2:
        return None
    beat = ED.music_for(ctx.seed, "hype", day=ctx.day, salt=salt)
    plan = _plan(beat, n)
    if plan is None:
        return None
    u, per = beat.unit, beat.period
    k = plan["k"]
    content_end = u(plan["total"])
    ed = ED.Edit(beat, content_end, ctx.seed)
    cam, rnd = ed.cam, ed.rnd
    arts = [ctx.art(e.item) for e in entries]
    names = [" ".join((e.name or e.item.get("name") or "").split()) for e in entries]

    def tile_for(i, x, y, w, h, fig=.95, **kw):
        iid = ed.uid("t")
        it = entries[i].item
        return iid, ED.tile(ed.src(arts[i]), it, x, y, w, h, iid, trim=trim_for(it), fig=fig, name=names[i], **kw)

    # ------------------------------------------------------------ hook
    t_items = u(plan["hook"])
    t_wait = u(plan["hook"] // 2)
    html, tsize, tlines = _title_html(title)
    # the words sit right above the tiles (y 790): "wait for #1" ends ~y 782
    sub_y = HOOK_TILES - 8 - 48 * 1.36 + 6
    title_y = sub_y - 10 - tlines * tsize * 1.36
    hook_tiles, first_id = "", ""
    for i, (x, y, w, h) in enumerate(_grid(n, HOOK_TILES, 1400)):
        iid, tl = tile_for(i, x, y, w, h, extra=f"transform:rotate({HOOK_ROT[i % len(HOOK_ROT)]}deg)")
        first_id = first_id or iid
        hook_tiles += tl
    ed.scene(0, t_items, ED.canvas(first_id, ED.tile_colors(entries[0].item), 1.0, .55) + hook_tiles)
    ed.over(0, t_items,
            ED.caption(html, 540, title_y, tsize, -1, width=960, weight=800, rot=-1.5, raw=True)
            + ED.caption(sub, MID, sub_y, _fit(sub, 800, 36, 28), -1, t_wait - FRAME, style="dark", weight=700,
                         width=820)
            + ED.caption(wait, MID, sub_y - 6, _fit(wait, 800, 48, 30), t_wait, style="dark", weight=800,
                         width=820))
    cam.push(0, t_items, 1.0, 1.05, MID, 1050)
    ed.cue(0, "impact")
    cam.punch(t_wait, .06)
    ed.cue(t_wait, "impact")

    # ------------------------------------------------------------ the countdown
    ui = plan["hook"]
    for idx, rank in enumerate(range(n, 0, -1)):
        i = rank - 1
        e = entries[i]
        if rank == 1:
            # a bar (or two) of suspense over its silhouette, a riser into the drop
            kb = plan["build"]
            t_pre, t_hit = u(ui), u(ui + kb)
            _, sil = tile_for(i, TILE_X, TILE_Y, TILE_W, TILE_H, fig_style=SILHOUETTE)
            ed.scene(t_pre, t_hit, ED.canvas("", ("#2a2a33", "#07070a"), 1.0, .2) + sil)
            ed.over(t_pre, t_hit,
                    ED.caption("and #1 is… 🥁", TOP_R, 300, 84, t_pre + .03, style="out", align="right",
                               width=620, weight=900, lh=1.1)
                    + ED.caption(tease, MID, 1110, _fit(tease, 800, 44, 32), u(ui + 1), style="dark", weight=700,
                                 width=820))
            ed.cue(t_pre, "glitch")
            ed.cue(u(ui + 1), "pop2")
            cam.flash(t_pre, .35, .12)
            cam.push(t_pre, t_hit, 1.0, 1.1, TILE_CX, 900)
            if kb >= 8:
                cam.punch(u(ui + 4), .03, .25)
            ed.cue(t_hit - 2.0, "riser")
            ui += kb
        s0 = ui
        start, end = u(s0), u(s0 + k)
        bu = lambda j, s0=s0: u(s0 + j)                   # noqa: E731 -- unit j of this screen

        iid, main = tile_for(i, TILE_X, TILE_Y, TILE_W, TILE_H)
        ed.scene(start, end, ED.canvas(iid, ED.tile_colors(e.item), 1.25, .45) + main)
        cam.push(start, end, 1.0, 1.05, TILE_CX, 920)

        over = ED.outline(f"#{rank}", RANK_R, RANK_Y, RANK_F, start, lime=rank == 1, width=520,
                          pulses=tuple(bu(b) for b in range(4, k, 4)))
        nsize, ny = _name_fit(names[i])
        over += ED.caption(names[i], TOP_R, ny, nsize, bu(1), align="right", width=NAME_W, weight=800,
                           lh=1.36 if ny == NAME_Y else 1.3)
        if e.tag:
            over += ED.caption(e.tag, TOP_R - 230, 312, 34, bu(1), style="lime", align="right", width=140,
                               weight=800, rot=4)
        # the stat rolls up (or stands as its guess) on the beat and lands with a hit
        c0, c1 = bu(2), bu(6)
        st = e.stat
        over += ED.caption(st.kicker, MID, KICK_Y, _fit(st.kicker, 800, KICK_F, 28), c0, style="dark", weight=700,
                           rot=-1, width=820)
        if st.value is not None:
            fin = f"{int(st.value):,} {st.unit}".strip()
            over += ED.caption(f"{ED.counter(int(st.value), c0, c1 - c0)} {esc(st.unit)}".strip(), MID, STAT_Y,
                               _fit(fin, STAT_W - 40, STAT_F, 48), c0, width=STAT_W, weight=900, rot=-1, raw=True,
                               lh=1.28)
        else:
            size = _fit(st.text, STAT_W - 40, STAT_F, 44)
            over += ED.caption(st.guess, MID, STAT_Y, min(size, _fit(st.guess, STAT_W - 40, STAT_F, 44)), c0,
                               c1 - FRAME, width=STAT_W, weight=900, rot=-1, lh=1.28)
            over += ED.caption(st.text, MID, STAT_Y, size, c1, width=STAT_W, weight=900, rot=-1, lh=1.28,
                               anim="edslam")
        for j in range(2, 6):
            ed.cue(bu(j), "tick2")
        ed.cue(c1, "boom" if rank <= 2 else "impact")
        cam.shake(c1, 16 if rank > 1 else 24, .4)
        cam.punch(c1, .05)
        cam.flash(c1, .25 if rank > 1 else .45, .18)
        # one caption slot over the lower half of the tile: the facts, then the line about it
        f_units, r_unit = _slots(k, len(e.facts), per)
        times = [bu(f) for f in f_units] + [bu(r_unit)]
        for j, fu in enumerate(f_units):
            text = e.facts[j]
            size, lines = _fit_lines(text, FACT_W - 30, FACT_F, 34)
            over += ED.caption(text, MID, FACT_FOOT - lines * size * 1.36, size, times[j], times[j + 1] - FRAME,
                               style="dark", width=FACT_W, weight=700)
        if e.react:
            size, lines = _fit_lines(e.react, REACT_W - 40, REACT_F, 40)
            over += ED.caption(e.react, MID, REACT_Y, size, times[-1], width=REACT_W, weight=800,
                               rot=rnd.choice([-3, -2, 2, 3]))
        for tt in times if e.react else times[:-1]:
            ed.cue(tt, "pop2")
        if rank == 1 and crown:
            over += ED.emoji(crown, TILE_X + TILE_W - 70, TILE_Y + 70, 140, bu(1), rot=14)
        ed.over(start, end, over)

        # the cut into this screen
        if rank == 1:
            ed.cue(start, "boom")
            cam.flash(start, .9, .3)
            cam.shake(start, 30, .5, 2)
            cam.punch(start, .12, .45)
        else:
            ed.cue(start, "impact")
            cam.punch(start, .08)
            move = TRANSITIONS[idx % len(TRANSITIONS)]
            if move == "zoom":
                cam.zoom(start, .45)
            else:
                cam.whip(start, *((0, -1) if move == "whip_up" else (-1, 0)), px=560 if move == "whip_up" else 480)
            ed.cue(start - .16, "swoosh")
        # a light punch on each bar with nothing else on it
        busy = [c1] + times
        for b in range(4, k, 4):
            tb = bu(b)
            if all(abs(tb - x) > .2 for x in busy):
                cam.punch(tb, .025, .25)
        ui += k

    # ------------------------------------------------------------ outro
    s0 = ui
    t_out, t_code = u(s0), u(s0 + 4)
    tiles, labels, first = "", "", ""
    for i, (x, y, w, h) in enumerate(_grid(n, 722, 1306, one_row_h=440)):
        iid, tl = tile_for(i, x, y, w, h, fig=.92)
        first = first or iid
        tiles += tl
        text = f"#{i + 1} · {entries[i].label}" if entries[i].label else f"#{i + 1}"
        at = t_out + .1 + .12 * i
        labels += ED.caption(text, x + w / 2, y + h - 46, _fit(text, w - 10, 32, 20), at, width=w + 20, weight=800)
        ed.cue(at, "pop2")
    ed.scene(t_out, content_end, ED.canvas(first, ED.tile_colors(entries[0].item), 1.0, .6) + tiles)
    asize, alines = _fit_lines(ask, 860, 60, 44)
    ed.over(t_out, content_end,
            ED.caption(ask, 540, 548 if alines > 1 else 600, asize, t_out, width=900, weight=800, rot=-1.5)
            + labels
            + ED.caption("use code BAD in the item shop 💚", MID, 1346, 44, t_code, style="lime", width=820,
                         weight=800))
    cam.whip(t_out, 0, -1, 560)
    ed.cue(t_out - .16, "swoosh")
    ed.cue(t_out, "impact")
    cam.push(t_out, content_end, 1.0, 1.04, MID, 1000)
    cam.punch(t_code, .05)
    ed.cue(t_code, "pop2")
    for b in range(8, plan["outro"], 4):
        cam.punch(u(s0 + b), .025, .25)

    return ed.finish()
