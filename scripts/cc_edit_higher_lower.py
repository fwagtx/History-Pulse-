"""
HIGHER OR LOWER, as an edit: the Item Shop game cut the way a person cuts a
"higher or lower" TikTok, to a real track (cc_edit) -- the same six skins,
counts and truth rules as cc_fmt_higher_lower.

    build(ctx, pool="all")      pool: "all" | "ch1" | "icon" | "collab"

  cover   frame 0: "higher or lower? 🤔", the edition, the first two skins
          on tiles side by side -- "32 times" against "? times" -- and
          "which was in the item shop more? 🛒"; a bar later "can you get
          all 5 right? 👀"
  rounds  five, each cut on a bar line: the skin you know on the left with
          its count, the next one on the right with "?"; the question, then
          higher ▲ / lower ▼; a 3-2-1 on the beat, the count rolls up and
          lands on the downbeat (the right answer lights lime, ding, flash,
          shake); a line about it; then a whip or zoom through the cut and
          the skin just revealed is the one you know
  outro   all six in the order played with their counts, "how many did you
          get right? 👇", use code BAD
Every number is cc_fmt_higher_lower.pick's: History.times up to ctx.day --
separate runs in the Item Shop, consecutive days counted once -- said as
"N times", with the video saying once on screen (and the caption) that the
counts go back to when the records began, in 2017.
"""

import math

import cc_edit as ED
from cc_fmt_higher_lower import POOLS, pick
from cc_formats import Ctx, Video, _caption, _hashtags, num
from cc_motion import trim_for

MIN_CONTENT = 57.0              # + the 5.1 s end card = 62.1 s
MAX_CONTENT = 84.0
HOOK, OUTRO = 8, 12             # units
# Bars of question and of reveal in a round of k units (the countdown is one bar).
PLAN = {12: (1, 1), 16: (2, 1), 20: (2, 2), 24: (3, 2), 28: (3, 3), 32: (4, 3)}

# The round screen: the skin you know on the left, the next one on the right,
# inside the button rail (x <= 900 below y 740).
TW, TH, TY = 400, 556, 706
TX = (70, 490)
TCX = (TX[0] + TW / 2, TX[1] + TW / 2)          # 270, 690
MID_X = 480                     # the middle of x 60..900
CAM_Y = TY + TH / 2             # 980: where the camera pushes in
Q_Y, Q_H, Q_W = 526, 152, 940   # the caption slot above the tiles: the question, then the verdict
COUNT_SIZE = 64
COUNT_Y = TY + TH - 38          # the counts sit across the tiles' bottom edge
BTN_Y, BTN_SIZE = 1334, 46
TOP_R = 1010                    # right edge of the round label, beside the code sticker
CD_SIZE = 200                   # the 3-2-1


def _w(text: str, size: float) -> float:
    """About how wide `text` is in TikTok Sans 800 (.56 em a letter)."""
    return len(text) * .56 * size


def _fit(text: str, width: float, size: float, lo: float = 24, lines: int = 1) -> float:
    """A font size at which `text` fits `width` in `lines` lines."""
    return max(lo, min(size, lines * width * .92 / max(1.0, len(text) * .56)))


def _nlines(text: str, size: float, width: float) -> int:
    return max(1, math.ceil(_w(text, size) / (width * .92)))


def _tri(up: bool) -> str:
    """▲ / ▼ drawn in the text's colour (a font may not have the glyph)."""
    pts = "5,0 10,8.6 0,8.6" if up else "0,0 10,0 5,8.6"
    return (f'<svg viewBox="0 0 10 8.6" style="display:inline-block;width:.62em;height:.53em;'
            f'vertical-align:.02em;fill:currentColor"><polygon points="{pts}"/></svg>')


def _answer(up: bool) -> str:
    return f"{'higher' if up else 'lower'} {_tri(up)}"


Q_MAX = 58                      # characters: two lines of the slot


def _questions(chain: list) -> list:
    """Each round's question, one wording for the whole video: "has X been in
    the shop more or less than Y? 🤔" where every round's fits, else "X: more
    or less than Y? 🤔" (and "X: higher or lower? 🤔" where even that won't)."""
    pairs = [(chain[r][0]["name"], chain[r - 1][0]["name"]) for r in range(1, len(chain))]
    long = [f"has {a} been in the shop more or less than {b}? 🤔" for a, b in pairs]
    if all(len(q) <= Q_MAX for q in long):
        return long
    out = []
    for a, b in pairs:
        q = f"{a}: more or less than {b}? 🤔"
        out.append(q if len(q) <= Q_MAX else f"{a}: higher or lower? 🤔")
    return out


PART = {2: "half", 3: "a third", 4: "a quarter"}


def _ratio_line(a: int, b: int) -> str:
    """How b compares with a when one is at least double the other, else ''."""
    hi, lo = max(a, b), min(a, b)
    k = hi // lo
    if k < 2:
        return ""
    if b > a:
        word = "double" if k == 2 else f"{k}x"
        return f"that's {'exactly' if hi == k * lo else 'more than'} {word} 🤯"
    k = min(k, 4)
    return f"that's {'exactly' if hi == k * lo else 'less than'} {PART[k]} 💀"


def _verdicts(chain: list, rnd) -> list:
    """Two lines per reveal, true to the numbers: the answer with how many more
    or fewer times, then one more -- how the two compare, how close it was, how
    far into the game we are, or a nudge -- never the same kind twice running."""
    n = len(chain) - 1
    nudges = ["did you get it? 👀", "too easy? 😤", "be honest, did you get it? 👀", "who got this one? 🙋"]
    rnd.shuffle(nudges)
    out, prev = [], ""
    for r in range(1, n + 1):
        a, b = chain[r - 1][1], chain[r][1]
        d, ratio = abs(b - a), max(a, b) / min(a, b)
        if b > a:
            one = (f"higher! just {d} more 😅" if ratio < 1.35 else
                   f"higher! {d} more times {'😭' if ratio >= 1.6 else '👀'}")
        else:
            one = (f"lower! just {d} fewer 😅" if ratio < 1.35 else
                   f"lower! {d} fewer times {'💀' if ratio >= 1.6 else '👀'}")
        cands = [("ratio", _ratio_line(a, b))] if _ratio_line(a, b) else []
        if ratio < 1.35:
            cands.append(("close", "that was a close one 😬"))
        if r < n:
            cands.append(("progress", f"{r} down, {n - r} to go 👀"))
        cands.append(("nudge", nudges[r % len(nudges)]))
        prev, two = next(c for c in cands if c[0] != prev)
        out.append((one, two))
    return out


def build(ctx: Ctx, pool: str = "all", **_):
    if pool not in POOLS:
        return None
    chain = pick(ctx, pool)
    if not chain:
        return None
    _, _, edition, cap_word = POOLS[pool]
    n = len(chain) - 1                                  # rounds
    ups = [chain[r][1] > chain[r - 1][1] for r in range(1, n + 1)]
    questions = _questions(chain)

    beat = ED.music_for(ctx.seed, "hype", day=ctx.day, salt="higher_lower")
    u = beat.unit
    # Units per round: the fewest that make the video long enough.
    for k in sorted(PLAN):
        total = HOOK + n * k + OUTRO
        if u(total) >= MIN_CONTENT:
            break
    content_end = u(total)
    if content_end > MAX_CONTENT:
        return None
    nq, nr = PLAN[k]
    ed = ED.Edit(beat, content_end, ctx.seed)
    cam = ed.cam
    rnd = ed.rnd
    verdicts = _verdicts(chain, rnd)
    arts = [ctx.art(it) for it, _ in chain]

    def tile_for(i, x, y, w, h, **kw):
        iid = ed.uid("t")
        it = chain[i][0]
        return iid, ED.tile(ed.src(arts[i]), it, x, y, w, h, iid, trim=trim_for(it), **kw)

    def name_cap(i, side, start, rot=0.0):
        """The skin's name over the lower part of its tile, just above its count."""
        nm = chain[i][0]["name"]
        size, lines = _fit(nm, TW - 30, 34, 10), 1
        if size < 28:                                     # a long name: two lines rather than tiny
            size, lines = min(32.0, _fit(nm, TW - 30, 34, 22, lines=2)), 2
        y = COUNT_Y - 4 - lines * 1.36 * size
        return ED.caption(nm, TCX[side], y, size, start, style="dark", width=TW - 10, weight=700, rot=rot)

    def count_cap(text, side, start, end=None, raw=False, rot=0.0):
        """A count (or "? times") across the bottom edge of its tile."""
        size = _fit("000 times", TW - 40, COUNT_SIZE, 40)
        return ED.caption(text, TCX[side], COUNT_Y, size, start, end, width=TW, weight=900, rot=rot, raw=raw,
                          lh=1.28)

    def slot(text, start, end, size=52, rot=0.0, style="box"):
        """The one changing line above the tiles."""
        size = _fit(text, Q_W - 60, size, 38, lines=2)
        lines = _nlines(text, size, Q_W - 60)
        y = Q_Y + max(0.0, (Q_H - lines * 1.36 * size) / 2)
        return ED.caption(text, 540, y, size, start, end, style=style, width=Q_W, weight=800, rot=rot)

    # ------------------------------------------------------------ cover: units 0-8
    t_game = u(HOOK)
    id0, tl = tile_for(0, TX[0], TY, TW, TH, extra="transform:rotate(-2deg)")
    _, tr = tile_for(1, TX[1], TY, TW, TH, extra="transform:rotate(2deg)")
    ed.scene(0, t_game, ED.canvas(id0, ED.tile_colors(chain[0][0]), 1.2, .5) + tl + tr)
    ed_line = f"{edition.lower()} edition" if edition else "item shop edition"
    ed.over(0, t_game,
            ED.caption(ed_line, TOP_R, 298, 44, -1, style="dark", align="right", width=560, weight=800)
            + ED.caption("higher or lower? 🤔", 540, 546, 88, -1, width=980, weight=900, rot=-2)
            + name_cap(0, 0, -1, -2) + name_cap(1, 1, -1, 2)
            + count_cap(f"{chain[0][1]:,} times", 0, -1, rot=-2)
            + count_cap("? times", 1, -1, rot=2)
            + ED.caption("which was in the item shop more? 🛒", MID_X, BTN_Y + 4, 40, -1, u(4), style="dark",
                         width=820, weight=800)
            + ED.caption(f"can you get all {n} right? 👀", MID_X, BTN_Y, BTN_SIZE, u(4), width=820,
                         weight=800, rot=2))
    cam.push(0, t_game, 1.0, 1.05, MID_X, CAM_Y)
    cam.punch(u(4), .06)
    ed.cue(u(4), "impact")
    ed.cue(u(4), "pop2")

    # ------------------------------------------------------------ the rounds
    ui = HOOK
    for r in range(1, n + 1):
        (_, a), (new, b) = chain[r - 1], chain[r]
        up = ups[r - 1]
        last = r == n
        s0 = ui
        start, end = u(s0), u(s0 + k)
        bu = lambda i, s0=s0: u(s0 + i)                    # noqa: E731 -- unit i of this round

        _, tl = tile_for(r - 1, TX[0], TY, TW, TH)
        idr, tr = tile_for(r, TX[1], TY, TW, TH)
        ed.scene(start, end, ED.canvas(idr, ED.tile_colors(new), 1.2, .5) + tl + tr)
        cam.push(start, end, 1.0, 1.04, MID_X, CAM_Y)

        # when things happen, in units of this round
        hi = 2 if nq == 1 else 4                          # higher ▲, then lower ▼ a unit later
        cd = 4 * nq                                       # 3, 2, 1, then the roll
        land = cd + 4                                     # the reveal, on a bar line
        t_q, t_hi, t_lo = bu(1), bu(hi), bu(hi + 1)
        t_roll, t_land = bu(cd + 3), bu(land)
        t_v1 = bu(land + 1)
        t_v2 = bu(land + 4) if nr >= 2 else None
        one, two = verdicts[r - 1]

        over = ED.caption("final round 😤" if last else f"round {r}/{n}", TOP_R, 300, 36, start - 1,
                          style="lime" if last else "dark", align="right", width=440, weight=800)
        over += name_cap(r - 1, 0, start - 1) + name_cap(r, 1, start - 1)
        # the count you know, and the one you don't
        over += count_cap(f"{a:,} times", 0, start - 1)
        over += count_cap("? times", 1, start - 1, t_roll)
        over += count_cap(f"{ED.counter(b, t_roll, t_land - t_roll)} times", 1, t_roll, raw=True)
        # the question, then what it was
        over += slot(questions[r - 1], t_q, t_v1, rot=rnd.choice([-2, -1.5, 1.5, 2]))
        over += slot(one, t_v1, t_v2, 54, rot=rnd.choice([-3, -2, 2, 3]))
        if t_v2 is not None:
            over += slot(two, t_v2, None, 54, rot=rnd.choice([-3, -2, 2, 3]))
        # higher ▲ / lower ▼, until the reveal
        over += ED.caption(_answer(True), MID_X - 14, BTN_Y, BTN_SIZE, t_hi, t_land, align="right",
                           width=400, weight=800, rot=-2, raw=True)
        over += ED.caption(_answer(False), MID_X + 14, BTN_Y, BTN_SIZE, t_lo, t_land, align="left",
                           width=400, weight=800, rot=2, raw=True)
        # 3, 2, 1 between the two tiles
        for j, word in enumerate("321"):
            over += ED.caption(word, MID_X, CAM_Y - CD_SIZE / 2, CD_SIZE, bu(cd + j), bu(cd + j + 1),
                               style="outlm" if word == "1" else "out", width=320, weight=900, lh=1.0,
                               anim="edslam")
        ed.over(start, end, over)
        # the reveal: the right answer lit, the other one dimmed
        right = ED.caption(_answer(up), MID_X + (-14 if up else 14), BTN_Y, BTN_SIZE, t_land,
                           align="right" if up else "left", width=400, weight=900, rot=-2 if up else 2,
                           style="lime", raw=True, anim="edin")
        wrong = ED.caption(f'<span style="opacity:.5">{_answer(not up)}</span>', MID_X + (14 if up else -14),
                           BTN_Y, BTN_SIZE, t_land, align="left" if up else "right", width=400, weight=800,
                           rot=2 if up else -2, style="dark", raw=True, anim="edin")
        ed.over(t_land, end, right + wrong
                + ED.emoji("📈" if up else "📉", TX[1] + TW - 80, TY + 84, 120, t_land, rot=12 if up else -12))

        # sound and camera
        ed.cue(t_q, "pop2")
        ed.cue(t_hi, "pop2")
        ed.cue(t_lo, "pop2")
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
        for tt in (t_v1, t_v2):
            if tt is not None:
                ed.cue(tt, "pop2")

        # the cut into this round: the known skin makes room
        ed.cue(start, "impact")
        if r % 2:                                         # zoom through (rounds 1, 3, 5)
            cam.zoom(start, .45)
            cam.punch(start, .06)
        else:                                             # whip: the chain slides left
            cam.whip(start, 1, 0, 480)
            cam.punch(start, .05)
        ed.cue(start - .16, "swoosh")
        if last:
            ed.cue(start, "glitch")
            cam.flash(start, .35, .12)
        # a light punch on each bar with nothing else on it
        busy = {0, 1, hi, hi + 1, cd, cd + 1, cd + 2, cd + 3, land, land + 1} | ({land + 4} if nr >= 2 else set())
        for bb in range(4, k, 4):
            if bb not in busy:
                cam.punch(bu(bb), .025, .25)
        ui += k

    # ------------------------------------------------------------ outro: 12 units
    t_out, t_code = u(ui), u(ui + len(chain))
    gw, gh, gap = 250, 280, 30
    x0 = MID_X - (3 * gw + 2 * gap) / 2
    spots = [(x0 + (i % 3) * (gw + gap), 722 + (i // 3) * (gh + 24)) for i in range(len(chain))]
    tiles, labels, first = "", "", ""
    for i, (x, y) in enumerate(spots):
        iid, html = tile_for(i, x, y, gw, gh, extra=f"transform:rotate({[-2, 1, -1, 2, -2, 1][i % 6]}deg)")
        first = first or iid
        tiles += html
        cnt = chain[i][1]
        text = f"{cnt:,} times" if i == 0 else f"{_tri(ups[i - 1])} {cnt:,} times"
        # the first count comes with the cut, then one answer per beat
        at = u(ui + i)
        labels += ED.caption(text, x + gw / 2, y + gh - 46, 32, at, width=gw + 20, weight=800, raw=True)
        if i:
            ed.cue(at, "pop2")
    ed.scene(t_out, content_end, ED.canvas(first, ED.tile_colors(chain[0][0]), 1.0, .6) + tiles)
    ed.over(t_out, content_end,
            ED.caption("counts since the records began in 2017 📅", TOP_R, 300, 30, t_out - 1, style="dark",
                       align="right", width=440, weight=700)
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
    cam.punch(u(ui + 8), .025, .25)

    comp = ed.finish()

    # ------------------------------------------------------------ the post
    body = "\n".join(
        f"{num(i + 1)} {it['name']} · in the Item Shop {cnt:,} times"
        + ("" if i == 0 else f" ({'HIGHER' if ups[i - 1] else 'LOWER'})")
        for i, (it, cnt) in enumerate(chain))
    tags = _hashtags("higherorlower", "fortniteskins", chain[0][0]["name"])
    music = comp.music or {}
    credit = (f"\n🎵 {music['title']} by {music['artist']} (public domain, CC0)" if music.get("artist") else "")
    head = (f"🔼🔽 HIGHER OR LOWER? Fortnite Item Shop edition — {ctx.day_label}\n"
            f"Which {cap_word}skin has been in the Item Shop more times? "
            f"Counts since the records began in 2017 👇")
    return Video(
        f"edit_higher_lower_{pool}", comp,
        title=f"Higher or Lower: Fortnite {cap_word.title()}Item Shop Edition — {ctx.day_label}",
        yt_title=f"Higher or Lower? Which Fortnite {cap_word.title() if cap_word else ''}Skin Was in the Item Shop "
                 f"More? #shorts",
        caption=_caption(head + credit, body, "How many did you get right? 5/5?", tags),
        hashtags=tags)
