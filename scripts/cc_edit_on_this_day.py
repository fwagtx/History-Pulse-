"""
ON THIS DAY, as an edit: one outfit from the Item Shop on today's date, every
year, re-cut the way the "fortnite through the years" edits are cut -- one year
per screen, every cut on a bar line of a real track (cc_edit), the same facts
as the classic format (cc_series.on_this_day).

    on_this_day(ctx, rounds, bday, lead, third) -> Comp     (a cc_series look)

  cover   frame 0: "the item shop on september 28, every year 🗓️", the span of
          years top right ("2018 → 2025"), the two lead picks on their tiles
          with their years; a bar later "remember these? 👀". On Sep 26 it is
          "fortnite turns 9 today 🎂". (🗓️, not 📅: the emoji font's 📅 reads
          "July 17", beside another date.)
  bday    (Sep 26 only) "battle royale came out on this day in 2017 🎂": 2017 in
          lime outline over a cake on a gold tile, pc · playstation 4 · xbox one
  years   one screen per year, oldest first: the year huge in outline top right
          (it gives a little on every bar), the date under it, the skin on its
          tile over its blurred canvas, its name along the tile's foot, and one
          caption slot above the name that changes on the bars: "new that day!
          🆕" (lime: its first day in the Item Shop) or "in the item shop that
          day 🛒", then "N years ago today 👀", then its rarity and type. A whip
          or a zoom through every cut (alternating) with a swoosh into it and a
          hit on it; the camera pushes in slowly across each screen.
  build   a bar or two (whichever makes the length) over the newest skin's
          silhouette, "and last year… 🥁", a riser into the drop: flash, boom,
          shake, the newest year in lime.
  outro   the years lined up on small tiles, their years ticked off on the
          eighth notes, "which year had the best shop? 👇", "use code BAD in the
          item shop 💚". (`third` isn't needed: every year is on it.)

The flashes are on the picture, inside the camera (as CapCut's flash sits on
the clip), so the captions and the code sticker stay crisp over them; the
years are SVG text, whose black edge can have round joins.

Every screen is a whole number of bars and every year gets the same number of
units, chosen per track (about 6 s a year) so the content runs 57-84.8 s; the
caller's end card adds 5.1 s. On screen only what the data says: the date, each
year, the name, its rarity and type, "new that day" only when the plan says it
was the item's first day in the Item Shop (else "in the item shop that day"),
how many years ago, the span, the birthday. "every year" only when no year is
missing between the first and the last (else "through the years").
"""

from datetime import date

import cc_edit as ED
from cc_motion import Comp, esc, trim_for

MIN_CONTENT = 57.0              # + the 5.1 s end card = 62.1 s
MAX_CONTENT = 84.8              # + 5.1 s = 89.9 s (Facebook Reels stop at 90)

# The year screen (the reference's frame): the tile in the column beside the
# button rail, the year and the date top right beside the code sticker.
TILE_X, TILE_Y, TILE_W, TILE_H = 150, 540, 660, 760
TILE_CX = TILE_X + TILE_W / 2
MID = 480                       # centre of the column x 60-900
TOP_R = 1010                    # right edge of the date and the right-aligned captions
YEAR_R = 1000                   # right edge of the year's digits (its black edge reaches ~1017)
YEAR_Y, YEAR_F = 205, 224       # the year's line box from y 205: its digits at y ~265-429
DATE_Y = 462
NAME_FOOT = 1400                # the name's bottom edge (the apps' captions start at 1420)
SLOT_F = 44                     # the caption slot above the name
CAL = "🗓️"                      # not 📅: the emoji font's 📅 shows a date (July 17)
CAKE = 340                      # the birthday's cake (the emoji font is a bitmap: bigger is soft)

# Units for (cover, birthday, build-up, outro), and how much less we like the
# shape: the long ones for a quick track, the short ones for a slow one.
SHAPES = [((8, 8, 4, 12), 0.0), ((8, 8, 8, 12), .2), ((8, 8, 8, 16), .45),
          ((4, 4, 4, 12), .6), ((4, 4, 4, 8), .8)]
TRANSITIONS = ["whip_up", "zoom", "whip_left", "zoom"]
SILHOUETTE = "filter:brightness(0) drop-shadow(0 0 20px rgba(255,255,255,.4))"
GOLD = {"rarity": "mythic"}     # the birthday's tile


def _plan(beat: ED.Beat, n: int, bday: bool) -> dict:
    """Units per part: every year the same whole number of bars, about 6 s a
    year, the content between MIN_CONTENT and MAX_CONTENT."""
    u, per = beat.unit, beat.period
    best = None
    for k in (4, 8, 12, 16, 20, 24):
        for (hook, bd, build, outro), pen in SHAPES:
            bd = bd if bday else 0
            total = hook + bd + n * k + build + outro
            if not MIN_CONTENT <= u(total) <= MAX_CONTENT:
                continue
            if hook * per < 3.0 or outro * per < 5.0 or build * per < 1.6:
                continue
            score = abs(k * per - 6.0) + pen + (.4 if build * per < 2.0 else 0) + (.8 if k == 4 else 0)
            if best is None or score < best[0]:
                best = (score, dict(k=k, hook=hook, bday=bd, build=build, outro=outro, total=total))
    if best is None:
        raise ValueError(f"no cut of {n} years fits {MIN_CONTENT}-{MAX_CONTENT} s at {beat.bpm:.0f} bpm")
    return best[1]


def _slots(k: int) -> list:
    """The units (within a year's k) where the caption slot changes."""
    return {4: [2], 8: [2, 5]}.get(k, list(range(4, k, 4)))


def _a(name: str, start: float, dur: float, fill: str = "both") -> str:
    return f"{name} {dur:.3f}s cubic-bezier(.2,.8,.2,1) {start:.3f}s 1 normal {fill}"


def _outline(text: str, right: float, top: float, size: float, start: float, pulses: list = (),
             lime: bool = False, width: float = 640) -> str:
    """Numbers in the app's outline style (white or lime, a black edge) as SVG
    text, whose edge can have round joins (CSS's text stroke mitres a spike
    off every sharp corner of a digit at this size). Right-aligned at `right`;
    `top` is the top of its line box (TikTok Sans: ascent 1.0 em, descent .3,
    digits .73 em tall). It slams in at `start` and gives a little on each
    of `pulses` (the bars), like the app's text on the beat."""
    anims = [_a("edslam", start, .3)] + [_a("edbeat", t, .3, "none") for t in pulses]
    est = .56 * size * len(text)                               # its width, near enough to centre on
    ox = max(10.0, 100 - 50 * est / width)
    return (f'<div class="ed-cap" style="left:{right - width:.0f}px;top:{top:.0f}px;width:{width:.0f}px;'
            f'height:{1.3 * size:.0f}px"><div style="height:100%;transform-origin:{ox:.0f}% 50%;'
            f'animation:{",".join(anims)}"><svg width="{width:.0f}" height="{1.3 * size:.0f}" '
            f'style="display:block;overflow:visible"><text x="{width:.0f}" y="{size:.1f}" text-anchor="end" '
            f'font-family="TikTok Sans" font-weight="900" font-size="{size:.0f}" fill="{ED.LIME if lime else "#fff"}" '
            f'stroke="#000" stroke-width="{.15 * size:.1f}" stroke-linejoin="round" paint-order="stroke">'
            f'{esc(text)}</text></svg></div></div>')


def _em(text: str) -> float:
    """About how wide a white-box caption of `text` is, in em (TikTok Sans 800
    runs .45-.53 em a letter, an emoji about 1.3 with its space, the box's
    padding .64): a little over, so what fits here fits on the page."""
    w = .64
    for ch in text:
        o = ord(ch)
        if o in (0xFE0F, 0x200D):
            continue
        w += 1.3 if o >= 0x2190 else .53
    return w


def _title(parts: list, width: float = 940, most: float = 72, least: float = 50) -> tuple:
    """A two-line caption broken where it reads best: `parts` are the words
    that must stay together, in order. Returns (html for raw=True, font size,
    lines): the break that lets it be biggest, then the most even one."""
    best = None
    for i in range(1, len(parts)):
        a, b = " ".join(parts[:i]), " ".join(parts[i:])
        longest = max(_em(a), _em(b))
        size = min(most, width / longest)
        if best is None or (size, -longest) > (best[1], -best[3]):
            best = (a, size, b, longest)
    a, size, b, _ = best
    if size < least:
        raise ValueError(f"the title doesn't fit: {' '.join(parts)}")
    nb = lambda s: esc(s).replace(" ", "&nbsp;")               # noqa: E731
    return f"{nb(a)}<br>{nb(b)}", size, 2


def _name_fit(name: str) -> tuple:
    """(font size, lines) for a name along the tile's foot: one line as big as
    fits 800 px (TikTok Sans 800 runs about .53 em a letter), or, when that
    would be small, two balanced lines."""
    one = 800 / max(1, len(name) * .56)
    if one >= 52 or " " not in name.strip():
        return max(38.0, min(76.0, one)), 1
    return max(38.0, min(62.0, 800 / ((len(name) / 2 + 2) * .56))), 2


def _day(d: date) -> str:
    return f"{d:%b} {d.day}, {d.year}".lower()                 # "sep 28, 2019"


def _round_day(rd: dict, day: date) -> date:
    try:
        return date.fromisoformat(rd["day"])
    except (KeyError, TypeError, ValueError):
        return date(rd["year"], day.month, min(day.day, 28 if day.month == 2 else day.day))


def _ago(n: int) -> str:
    return {0: "today! 👀", 1: "1 year ago today 👀"}.get(n, f"{n} years ago today 👀")


def _tease(year: int, day: date) -> str:
    """The build-up's line before the newest year."""
    return {day.year - 1: "and last year… 🥁", day.year: "and today… 🥁"}.get(year, f"and in {year}… 🥁")


def _kind(it: dict) -> str:
    """'epic outfit', 'marvel series outfit' -- its rarity and type."""
    rar = str(it.get("rarity_label") or it.get("rarity") or "").strip().lower()
    typ = str(it.get("type") or "outfit").strip().lower()
    return f"{rar} {typ}".strip()


def _grid(n: int, top: float = 736, bottom: float = 1306) -> list:
    """(x, y, w, h) of n small tiles in two rows, in reading order, inside the
    column beside the button rail (x 60-900), centred between top and bottom."""
    cols = max(3, -(-n // 2))
    rows = -(-n // cols)
    gap = 16
    w = (840 - (cols - 1) * gap) / cols
    h = min(w * 1.3, (bottom - top - (rows - 1) * gap) / rows)
    y0 = top + (bottom - top - (rows * h + (rows - 1) * gap)) / 2
    out = []
    for i in range(n):
        r, c = divmod(i, cols)
        in_row = min(cols, n - r * cols)
        x0 = 60 + (840 - (in_row * w + (in_row - 1) * gap)) / 2
        out.append((x0 + c * (w + gap), y0 + r * (h + gap), w, h))
    return out


def on_this_day(ctx, rounds: list, bday: dict | None, lead: list, third) -> Comp:
    day = ctx.day
    n = len(rounds)
    years = [rd["year"] for rd, _, _ in rounds]
    span = ([bday["year"]] if bday else []) + years
    every = "every year" if all(b - a == 1 for a, b in zip(years, years[1:])) else "through the years"

    beat = ED.music_for(ctx.seed, "hype", day=day, salt="on_this_day")
    u = beat.unit
    plan = _plan(beat, n, bool(bday))
    K = plan["k"]
    content_end = u(plan["total"])
    ed = ED.Edit(beat, content_end, ctx.seed)
    ed.say(.25, f"Fortnite turns {bday['age']} today! Here's the Item Shop on this day, every year." if bday else
           f"Here's the Item Shop on {day:%B} {ED.ordinal(day.day)}, every year since {years[0]}!")
    cam, rnd = ed.cam, ed.rnd

    def tile_for(it, x, y, w, h, fig=.95, **kw):
        iid = ed.uid("t")
        return iid, ED.tile(ed.src(ctx.art(it)), it, x, y, w, h, iid, trim=trim_for(it), fig=fig, **kw)

    def flash(t: float, strength: float, dur: float = .3) -> str:
        """A white flash on the picture at t, for a scene's html: inside the
        camera like CapCut's flash on the clip, so the captions and the code
        sticker stay crisp over it (the camera's own flash covers them)."""
        name = ed.uid("otdfl")
        ed.comp.css(f"@keyframes {name}{{0%{{opacity:{strength}}}100%{{opacity:0}}}}")
        return (f'<div data-safe="ignore" style="position:absolute;left:-30%;top:-30%;width:160%;height:160%;'
                f'background:#fff;opacity:0;z-index:30;pointer-events:none;'
                f'animation:{name} {dur:.3f}s cubic-bezier(.25,.46,.45,.94) {t:.3f}s 1 normal none"></div>')

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
        """The name along the tile's foot (its top y, the caption)."""
        size, lines = _name_fit(text)
        lh = 1.3
        y = NAME_FOOT - lines * size * lh
        return y, ED.caption(text, MID, y, size, start, width=820, weight=800, rot=rnd.choice([-2, -1, 1, 2]),
                             lh=lh, extra="white-space:nowrap" if lines == 1 else "")

    def slot(lines: list, times: list, foot: float, first_hit: str = "pop2") -> str:
        """One caption slot, its bottom at `foot`: each line from its time to
        the next one's. A fact in a dark box; a lime one bigger and tilted."""
        html = ""
        for i, t in enumerate(times):
            text, style = lines[i % len(lines)]
            end = times[i + 1] if i + 1 < len(times) else None
            size = SLOT_F if style == "dark" else 54
            html += ED.caption(text, MID, foot - size * 1.36, size, t, end, style=style, width=820,
                               weight=700 if style == "dark" else 800,
                               rot=0 if style == "dark" else rnd.choice([-3, -2, 2, 3]))
            ed.cue(t, first_hit if i == 0 else "pop2")
            cam.punch(t, .05 if (i == 0 and first_hit == "ding") else .025, .25)
        return html

    # ------------------------------------------------------------ cover
    t1 = u(plan["hook"])
    t_hook2 = u(plan["hook"] // 2)
    if bday:
        title, tsize, tlines = _title(["fortnite", "turns", str(bday["age"]), "today 🎂"], 900, 88)
    else:
        md = f"{day:%B} {day.day}".lower()                  # "september 28"
        title, tsize, tlines = _title(["the", "item", "shop", "on", f"{md},", f"{every} {CAL}"], 940, 72)
    title_y = 532
    over = ED.caption(title, 540, title_y, tsize, -1, width=960, rot=-1.5, raw=True)
    over += _outline(f"{span[0]} → {span[-1]}", YEAR_R, 312, 92, -1)
    # the two lead picks, oldest first, on tiles with their years
    picks = sorted(lead[:2], key=lambda r: r[0]["year"])
    cy = title_y + tlines * tsize * 1.36 + 26
    chh = 1296 - cy
    cw = min(390, chh * .76)
    tiles, first = "", ""
    for (rd, it, _), (x, rot) in zip(picks, ((480 - 20 - cw, -3), (500, 3))):
        iid, html = tile_for(it, x, cy, cw, chh, extra=f"transform:rotate({rot}deg)")
        first = first or iid
        tiles += html
        over += ED.caption(str(rd["year"]), x + cw / 2, cy + chh - 86, 52, -1, width=300, weight=900, rot=rot)
    ed.scene(0, t1, ED.canvas(first, ED.tile_colors(picks[0][1]), 1.0, .55) + tiles)
    if bday:
        over += ED.caption(f"the item shop on this day, {every} {CAL}", MID, 1318, 42, -1, t_hook2,
                           style="dark", weight=700, width=840)
    over += ED.caption("remember these? 👀", MID, 1314, 52, t_hook2, width=820, rot=2)
    ed.over(0, t1, over)
    cam.push(0, t1, 1.0, 1.05, 480, 1030)
    cam.punch(t_hook2, .06)
    ed.cue(t_hook2, "impact")
    ui = plan["hook"]
    ci = 0                                               # cuts so far, for the transitions

    # ------------------------------------------------------------ birthday
    if bday:
        k = plan["bday"]
        s0 = ui
        start, end = u(s0), u(s0 + k)
        cake = ED.tile("", GOLD, TILE_X, TILE_Y, TILE_W, TILE_H, ed.uid("t"))
        cake += ED.emoji("🎂", TILE_CX, TILE_Y + 330, CAKE, start, rot=-6)
        ed.scene(start, end, ED.canvas("", ED.tile_colors(GOLD), 1.0, .5) + cake + flash(start, .6, .25))
        cam.push(start, end, 1.0, 1.05, TILE_CX, 920)
        over = _outline(str(bday["year"]), YEAR_R, YEAR_Y, YEAR_F, start, [u(s0 + b) for b in range(4, k, 4)],
                        lime=True)
        over += ED.caption(_day(date(bday["year"], day.month, day.day)), TOP_R, DATE_Y, 36, start, style="dark",
                           align="right", width=420, weight=700)
        size = 54
        y = NAME_FOOT - 2 * size * 1.3
        over += ED.caption(f"battle royale came out on this day in {bday['year']} 🎂", MID, y, size, u(s0 + 1),
                           width=820, weight=800, rot=-1.5, lh=1.3)
        ed.cue(u(s0 + 1), "pop2")
        facts = [("pc · playstation 4 · xbox one", "dark"), (_ago(bday["age"]).replace("👀", "🎂"), "dark")]
        over += slot(facts, [u(s0 + b) for b in _slots(k)], y - 16)
        over += ED.emoji("🎉", TILE_X + TILE_W - 60, TILE_Y + 80, 130, u(s0 + _slots(k)[0]), rot=14)
        ed.over(start, end, over)
        cut(start, TRANSITIONS[ci % len(TRANSITIONS)], "boom")
        ci += 1
        ui += k

    # ------------------------------------------------------------ the years
    for j, (rd, it, debut) in enumerate(rounds):
        last = j == n - 1
        when = _round_day(rd, day)
        if last:
            # a bar (or two) of suspense over its silhouette, a riser into the drop
            kb = plan["build"]
            t_pre, t_hit = u(ui), u(ui + kb)
            t_date = u(ui + (4 if kb >= 8 else 1))
            _, sil = tile_for(it, TILE_X, TILE_Y, TILE_W, TILE_H, fig_style=SILHOUETTE)
            ed.scene(t_pre, t_hit, ED.canvas("", ("#2a2a33", "#07070a"), 1.0, .2) + sil + flash(t_pre, .35, .12))
            tease = _tease(rd["year"], day)
            ed.over(t_pre, t_hit,
                    ED.caption(tease, TOP_R, 262, 84, t_pre + .03, style="out", align="right", width=600,
                               weight=900, lh=1.1)
                    + ED.caption(f"{_day(when)} 👀", MID, 1236, SLOT_F, t_date, style="dark", weight=700,
                                 width=820))
            ed.cue(t_pre, "glitch")
            ed.cue(t_date, "pop2")
            cam.punch(t_date, .03, .25)
            cam.push(t_pre, t_hit, 1.0, 1.1, TILE_CX, 900)
            ed.cue(t_hit - 2.0, "riser")
            ui += kb

        s0 = ui
        start, end = u(s0), u(s0 + K)
        iid, main = tile_for(it, TILE_X, TILE_Y, TILE_W, TILE_H)
        ed.scene(start, end, ED.canvas(iid, ED.tile_colors(it), 1.25, .45) + main
                 + (flash(start, .9, .3) if last else ""))
        cam.push(start, end, 1.0, 1.05, TILE_CX, 920)

        over = _outline(str(rd["year"]), YEAR_R, YEAR_Y, YEAR_F, start, [u(s0 + b) for b in range(4, K, 4)],
                        lime=last)
        over += ED.caption(_day(when), TOP_R, DATE_Y, 36, start, style="dark", align="right", width=420, weight=700)
        ny, name = name_line(it["name"], u(s0 + 1))
        over += name
        ed.cue(u(s0 + 1), "pop2")
        facts = [("new that day! 🆕", "lime") if debut else ("in the item shop that day 🛒", "dark"),
                 (_ago(day.year - rd["year"]), "dark"), (_kind(it), "dark")]
        over += slot(facts, [u(s0 + b) for b in _slots(K)], ny - 16, "ding" if debut else "pop2")

        if last:
            # the drop (its flash is in the scene)
            ed.cue(start, "boom")
            cam.shake(start, 30, .5, 2)
            cam.punch(start, .12, .45)
            over += ED.emoji("🔥", TILE_X + TILE_W - 60, TILE_Y + 70, 140, u(s0 + 1), rot=14)
        else:
            cut(start, TRANSITIONS[ci % len(TRANSITIONS)])
            ci += 1
        ed.over(start, end, over)
        ui += K

    # ------------------------------------------------------------ outro
    s0 = ui
    t_out = u(s0)
    tiles, labels, first, first_it = "", "", "", None
    geo = _grid(n)
    for i, ((rd, it, _), (x, y, w, h)) in enumerate(zip(rounds, geo)):
        iid, html = tile_for(it, x, y, w, h, fig=.92)
        if not first:
            first, first_it = iid, it
        tiles += html
        at = u(s0 + i / 2)                               # the years ticked off on the eighth notes
        labels += ED.caption(str(rd["year"]), x + w / 2, y + h - 46, 30, at, width=w + 20, weight=900)
        ed.cue(at, "pop2")
    ed.scene(t_out, content_end, ED.canvas(first, ED.tile_colors(first_it), 1.0, .6) + tiles)
    t_code = u(s0 + max(4, (n - 1) // 2 + 1))            # a unit after the last year
    ed.over(t_out, content_end,
            ED.caption("which year had the best shop? 👇", 540, 540, 60, t_out, width=900, rot=-1.5)
            + labels
            + ED.caption("use code BAD in the item shop 💚", MID, 1334, 44, t_code, style="lime", width=820))
    cut(t_out, "whip_up")
    cam.push(t_out, content_end, 1.0, 1.04, 480, 1000)
    ed.cue(t_code, "pop2")
    cam.punch(t_code, .04, .3)
    for b in range(8, plan["outro"], 4):
        cam.punch(u(s0 + b), .025, .25)

    return ed.finish()
