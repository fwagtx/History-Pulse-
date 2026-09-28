"""
MOST COMMON, as an edit: the five skins that have been in the Item Shop the
most times, counted down to a real track (cc_edit), the way a fan account cuts
it in an app -- the same data and truth rules as cc_fmt_most_common.

    build(ctx, kind="outfit", since=None, count=5)

  hook    frame 0 is the cover: "the most common skins in fortnite 😭" over
          the five on their tiles; a bar later "wait for #1 👀"
  items   #5 to #2, a few bars each, cut on the downbeat: the rank, the name,
          the count rolling up on the beat and landing with a hit, then the
          facts (first time in the shop, last seen) and one line about it
  #1      a bar of "and #1 is..." over its silhouette with a riser, then the
          drop: flash, hit, shake, the reveal
  outro   the five lined up with their counts, "how many of these do you
          own? 👇", USE CODE: BAD
Every number is cc_fmt_most_common's: times in the shop (consecutive days
count once), first time in the shop (only from 2018, when the records can
vouch for it), last seen, all up to ctx.day.
"""

from datetime import date

import cc_edit as ED
import cc_rarity as R
from cc_fmt_most_common import KINDS, _period, _pick, _ranked
from cc_fmt_rarity import history
from cc_formats import Ctx, Video, _caption, _hashtags, num
from cc_motion import trim_for

MIN_CONTENT = 57.0              # + the 5.1 s end card = 62.1 s
MAX_CONTENT = 84.0

# the item screen
TILE_X, TILE_Y, TILE_W, TILE_H = 150, 540, 660, 760
TILE_CX = TILE_X + TILE_W / 2
TOP_R = 1010                    # right edge of the rank and name (beside the code sticker)


def _day(d: date) -> str:
    return f"{d:%b} {d.day}, {d.year}".lower()


def _ago(last: date, day: date) -> str:
    n = (day - last).days
    if n <= 0:
        return "today"
    if n == 1:
        return "yesterday"
    return f"{n} days ago" if n < 100 else _day(last)


def _fit(text: str, width: float, size: float, lo: float = 34) -> float:
    """A font size at which `text` (TikTok Sans 800, about .56 em a letter)
    fits `width`."""
    return max(lo, min(size, width / max(1, len(text) * .56)))


def _every(r: dict, day: date) -> str:
    """How often, on average, it has come back: "about once a month"."""
    first = r["first"] or R.RECORDS_START
    per = (day - first).days / max(1, r["times"])
    if per < 10:
        return f"about once every {max(1, round(per))} days"
    if per < 45:
        weeks = round(per / 7)
        return "about once a month" if 26 <= per <= 35 else f"about once every {weeks} weeks"
    return f"about once every {round(per / 30.4)} months"


def _react(r: dict, rank: int, rows: list, day: date, rnd) -> str:
    """One line about the item, true to the data."""
    last_days = (day - r["last"]).days
    lines = [f"that's {_every(r, day)} 👀"]
    if last_days <= 21:
        lines.append(f"and it was just in the shop {_ago(r['last'], day)} 👀" if last_days > 1
                     else f"and it's in the shop {'today' if last_days == 0 else 'since yesterday'} 👀")
    if rank == 1:
        return "tied for the most in fortnite 🤝" if r.get("tied") else "no skin has been in the shop more 👑"
    if r.get("tied"):
        other = next((o for o in rows if o is not r and o["times"] == r["times"]), None)
        if other:
            return f"tied with {other['item']['name']} on {r['times']} 🤝"
    return lines[rnd.randrange(len(lines))]


def build(ctx: Ctx, kind: str = "outfit", since: int | None = None, count: int = 5, **_):
    if kind not in KINDS:
        return None
    count = 5
    hist = history()
    period = _period(int(since) if since else None, ctx.day)
    rows = _pick(ctx, _ranked(hist, ctx.day, kind, period["start"]), count)
    if not rows or rows[-1]["times"] < 2:
        return None
    word, cap, one = KINDS[kind]
    n = len(rows)

    beat = ED.music_for(ctx.seed, "hype", day=ctx.day, salt="most_common")
    u = beat.unit
    # Units per item: the fewest that make the video long enough.
    for k in (16, 20, 24, 28, 32):
        total = 8 + n * k + 4 + 12
        if u(total) >= MIN_CONTENT:
            break
    content_end = u(total)
    if content_end > MAX_CONTENT:
        return None
    ed = ED.Edit(beat, content_end, ctx.seed)
    cam = ed.cam
    rnd = ed.rnd
    arts = {r["key"]: ctx.art(r["item"]) for r in rows}

    def tile_for(r, x, y, w, h, fig=.95, **kw):
        iid = ed.uid("t")
        return iid, ED.tile(ed.src(arts[r["key"]]), r["item"], x, y, w, h, iid,
                            trim=trim_for(r["item"]), fig=fig, **kw)

    def grid(x0: float, y0: float, w: float, h: float) -> list:
        """Five tiles, 3 over 2, inside the button rail (x <= 900 below y 740)."""
        gap = (840 - 3 * w) / 2
        top = [(60 + i * (w + gap), y0) for i in range(3)]
        bot = [(480 - w - gap / 4, y0 + h + 24), (480 + gap / 4, y0 + h + 24)]
        # #1 in the middle of the top row, #2 and #3 beside it, #4 and #5 below
        return [top[1], top[0], top[2], bot[0], bot[1]]

    # ------------------------------------------------------------ hook: units 0-8
    t_items = u(8)
    gw, gh = 250, 300
    spots = grid(60, 800, gw, gh)
    hook_tiles, first_id = "", ""
    for i, (r, (x, y)) in enumerate(zip(rows, spots)):
        iid, html = tile_for(r, x, y, gw, gh, extra=f"transform:rotate({[-2, 3, -3, 2, -1][i]}deg)")
        first_id = first_id or iid
        hook_tiles += html
    ed.scene(0, t_items, ED.canvas(first_id, ED.tile_colors(rows[0]["item"]), 1.0, .55) + hook_tiles)
    title = (f"the most common {cap} in fortnite 😭" if not period["start"] else
             f"the most common {cap} in fortnite {period['short'].lower()} 😭")
    ed.over(0, t_items,
            ED.caption(title, 540, 528, 72, -1, width=940, weight=800, rot=-1.5)
            + ED.caption("ranked by times in the item shop 🛒", 480, 726, 36, -1, u(4), style="dark",
                         weight=700, width=820)
            + ED.caption("wait for #1 👀", 480, 720, 48, u(4), style="dark", weight=800, width=820))
    cam.push(0, t_items, 1.0, 1.05, 480, 1050)
    ed.cue(0, "impact")
    cam.punch(u(4), .06)
    ed.cue(u(4), "impact")

    # ------------------------------------------------------------ the countdown
    ui = 8
    transitions = ["whip_up", "zoom", "whip_left", "zoom"]
    for idx, (rank, r) in enumerate(reversed(list(enumerate(rows, 1)))):
        it = r["item"]
        if rank == 1:
            # a bar of suspense over its silhouette, a riser into the drop
            t_pre, t_hit = u(ui), u(ui + 4)
            _, sil = tile_for(r, TILE_X, TILE_Y, TILE_W, TILE_H,
                              fig_style="filter:brightness(0) drop-shadow(0 0 20px rgba(255,255,255,.4))")
            ed.scene(t_pre, t_hit, ED.canvas("", ("#2a2a33", "#07070a"), 1.0, .2) + sil)
            ed.over(t_pre, t_hit,
                    ED.caption("and #1 is… 🥁", TOP_R, 300, 84, t_pre + .03, style="out", align="right",
                               width=620, weight=900, lh=1.1)
                    + ED.caption("the most times in the item shop 👀", 480, 1110, 44, u(ui + 1),
                                 style="dark", weight=700, width=820))
            ed.cue(t_pre, "glitch")
            cam.flash(t_pre, .35, .12)
            cam.push(t_pre, t_hit, 1.0, 1.1, TILE_CX, 900)
            ed.cue(t_hit - 2.0, "riser")
            ui += 4
        s0 = ui
        start, end = u(s0), u(s0 + k)
        bu = lambda i, s0=s0: u(s0 + i)                    # noqa: E731 -- unit i of this screen

        iid, main = tile_for(r, TILE_X, TILE_Y, TILE_W, TILE_H)
        ed.scene(start, end, ED.canvas(iid, ED.tile_colors(it), 1.25, .45) + main)
        cam.push(start, end, 1.0, 1.05, TILE_CX, 920)

        over = (ED.outline(f"#{rank}", TOP_R - 8, 250, 176, start, lime=rank == 1, width=520,
                           pulses=tuple(bu(b) for b in range(4, k, 4)))
                + ED.caption(it["name"], TOP_R, 462, _fit(it["name"], 600, 58), bu(1), align="right",
                             width=600, weight=800))
        if r.get("tied") and rank > 1:
            over += ED.caption("tied", TOP_R - 230, 312, 34, bu(1), style="lime", align="right", width=140,
                               weight=800, rot=4)
        # the count rolls up on the beat and lands with a hit
        c0, c1 = bu(2), bu(6)
        over += ED.caption("in the item shop", 480, 1234, 36, c0, style="dark", weight=700, rot=-1, width=820)
        over += ED.caption(f"{ED.counter(r['times'], c0, c1 - c0)} times", 480, 1290, 86, c0,
                           width=820, weight=900, rot=-1, raw=True, lh=1.28)
        for j in range(2, 6):
            ed.cue(bu(j), "tick2")
        ed.cue(c1, "boom" if rank <= 2 else "impact")
        cam.shake(c1, 16 if rank > 1 else 24, .4)
        cam.punch(c1, .05)
        cam.flash(c1, .25 if rank > 1 else .45, .18)
        # one caption slot over the lower half of the tile: the facts, then a line about it
        f1, f2, rx = bu(max(8, round(k * .45))), bu(max(10, round(k * .6))), bu(max(12, round(k * .75)))
        fact1 = (f"first time in the shop: {_day(r['first'])}" if r["first"] else "in the shop since 2017")
        over += ED.caption(fact1, 480, 1164, 40, f1, f2, style="dark", width=780, weight=700)
        over += ED.caption(f"last seen: {_ago(r['last'], ctx.day)}", 480, 1164, 40, f2, rx, style="dark",
                           width=780, weight=700)
        over += ED.caption(_react(r, rank, rows, ctx.day, rnd), 480, 1060, 50, rx, width=780, weight=800,
                           rot=rnd.choice([-3, -2, 2, 3]))
        for tt in (f1, f2, rx):
            ed.cue(tt, "pop2")
        if rank == 1:
            over += ED.emoji("👑", TILE_X + TILE_W - 70, TILE_Y + 70, 140, bu(1), rot=14)
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
            move = transitions[idx % len(transitions)]
            if move == "zoom":
                cam.zoom(start, .45)
            else:
                cam.whip(start, *((0, -1) if move == "whip_up" else (-1, 0)), px=560 if move == "whip_up" else 480)
            ed.cue(start - .16, "swoosh")
        # a light punch on each bar with nothing else on it
        for b in range(4, k, 4):
            tb = bu(b)
            if all(abs(tb - x) > .2 for x in (c1, f1, f2, rx)):
                cam.punch(tb, .025, .25)
        ui += k

    # ------------------------------------------------------------ outro: 12 units
    t_out = u(ui)
    gw2, gh2 = 250, 300
    spots2 = grid(60, 760, gw2, gh2)
    outro_tiles, first2, labels = "", "", ""
    for i, (r, (x, y)) in enumerate(zip(rows, spots2)):
        iid, html = tile_for(r, x, y, gw2, gh2)
        first2 = first2 or iid
        outro_tiles += html
        at = t_out + .1 + .12 * i
        labels += ED.caption(f"#{i + 1} · {r['times']}x", x + gw2 / 2, y + gh2 - 48, 32, at, width=gw2 + 20,
                             weight=800)
        ed.cue(at, "pop2")
    ed.scene(t_out, content_end, ED.canvas(first2, ED.tile_colors(rows[0]["item"]), 1.0, .6) + outro_tiles)
    ed.over(t_out, content_end,
            ED.caption("how many of these do you own? 👇", 540, 540, 60, t_out, width=900, weight=800, rot=-1.5)
            + labels
            + ED.caption("use code BAD in the item shop 💚", 480, 1400 - 66, 44, u(ui + 4),
                         style="lime", width=820, weight=800))
    cam.whip(t_out, 0, -1, 560)
    ed.cue(t_out - .16, "swoosh")
    ed.cue(t_out, "impact")
    cam.push(t_out, content_end, 1.0, 1.04, 480, 1000)
    ed.cue(u(ui + 4), "pop2")

    comp = ed.finish()

    # ------------------------------------------------------------ the post
    top = rows[0]
    per = period["cap"]
    title_kind = cap.title() if kind != "backpack" else "Back Blings"
    body = "\n".join(
        f"{num(i)} {r['item']['name']} · in the Item Shop {r['times']:,} times{per}"
        f" · last seen {r['last']:%b %-d, %Y}" for i, r in enumerate(rows, 1))
    ties = any(r.get("tied") for r in rows)
    how = ("Ranked by separate times in the Item Shop (consecutive days count once"
           + ("; ties go to more days in the shop" if ties else "") + ") 👇")
    when = f"as of {ctx.day_label}" if not period["start"] else f"{period['start']:%b %-d, %Y} – {ctx.day:%b %-d, %Y}"
    head = (f"🔁 The most common {cap} in Fortnite {period['short'].lower() or ''}".rstrip()
            + f" — the {cap} that have been in the Item Shop the most times, {when}\n{how}")
    tags = _hashtags("mostcommonskins" if kind == "outfit" else f"fortnite{cap.replace(' ', '')}",
                     "fortniteskins", top["item"]["name"])
    span = f" {period['short'].title()}" if period["start"] else ""
    music = comp.music or {}
    credit = (f"\n🎵 {music['title']} by {music['artist']} (public domain, CC0)" if music.get("artist") else "")
    return Video(
        f"edit_most_common_{kind}{'_' + str(since) if since else ''}", comp,
        title=f"The Most Common Fortnite {title_kind}{span} — Item Shop History, {ctx.day_label}",
        yt_title=f"The Most Common Fortnite {title_kind}{span}: #1 Was in the Item Shop {top['times']:,} Times #shorts",
        caption=_caption(head + credit, body, "How many of these do you own?", tags),
        hashtags=tags)
