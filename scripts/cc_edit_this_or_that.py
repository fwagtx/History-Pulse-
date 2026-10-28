"""
THIS OR THAT, as an edit: pairs of today's shop items, cut the way a person
cuts a "this or that" TikTok, to a real track (cc_edit) -- the same pairs and
truth rules as the classic cc_formats.this_or_that. No right answers.

    build(ctx)

  cover   frame 0: "this or that? 🤔", "item shop · sep 23" top right, the
          first pair on tiles side by side with their names and prices,
          "comment A or B 👇"; a bar later "5 rounds, no wrong answers 🤝"
  rounds  four or five, each cut on a bar line (a zoom or a whip through it):
          the two on their tiles, names and prices on them; "which outfit are
          you picking? 🤔" above them; A and B pop in under them on the beat;
          a 3-2-1 between the tiles; "lock it in 🔒" lands on the downbeat
          (flash, hit); then a line true to the data -- the one that leaves at
          the next reset, the one new in today's shop, the price gap -- and
          "comment A or B 👇"
  outro   every pair lined up, the A's over the B's, "comment your picks 👇
          like ABBAB", "use code BAD in the item shop 💚"

The pairs are the classic's (_pairs mirrors its rule exactly: today's singles
shuffled by the day, like with like -- the same type -- within 500 V-Bucks,
up to five, the first outfit pair first; fewer than four: None). Prices are
the rows' own; the facts are cc_fmt_shop_recap._facts'. We never say which
one people pick or which one is better.
"""

import math

import cc_edit as ED
from cc_fmt_shop_recap import _facts
from cc_formats import Ctx, Video, _caption, _hashtags, num, rng, singles
from cc_motion import FPS, trim_for

MIN_CONTENT = 57.0              # + the 5.1 s end card = 62.1 s
MAX_CONTENT = 84.0
HOOK, OUTRO = 8, 12             # units
# Bars of question and of what follows in a round of k units (the countdown is one bar).
PLAN = {12: (1, 1), 16: (2, 1), 20: (2, 2), 24: (3, 2), 28: (3, 3)}
FRAME = 1 / FPS

# higher or lower's round screen: two tiles side by side in the column beside
# the button rail (x 60-900 below y 740), the question above, A / B under them
TW, TH, TY = 400, 556, 706
TX = (70, 490)
TCX = (TX[0] + TW / 2, TX[1] + TW / 2)          # 270, 690
MID_X = 480
CAM_Y = TY + TH / 2
Q_Y, Q_H, Q_W = 526, 152, 940
COUNT_SIZE = 56
COUNT_Y = TY + TH - 38
BTN_Y, BTN_SIZE = 1330, 58
TOP_R = 1010
CD_SIZE = 200


def _w(text: str, size: float) -> float:
    return len(text) * .56 * size


def _fit(text: str, width: float, size: float, lo: float = 24, lines: int = 1) -> float:
    return max(lo, min(size, lines * width * .92 / max(1.0, len(text) * .56)))


def _nlines(text: str, size: float, width: float) -> int:
    return max(1, math.ceil(_w(text, size) / (width * .92)))


def _pairs(ctx: Ctx) -> list:
    """The classic's pairs (cc_formats.this_or_that, whose rule lives inside
    that function): today's singles shuffled by the day, each paired with the
    first unused one of the same type within 500 V-Bucks, up to five pairs,
    the first outfit pair moved to the front. [] when fewer than four."""
    pool = singles(ctx)
    r = rng(ctx, 1)
    r.shuffle(pool)
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
        return []
    lead = next((k for k, (a, _) in enumerate(pairs) if a["type"] == "Outfit"), 0)
    pairs.insert(0, pairs.pop(lead))
    return pairs


def _question(a: dict) -> str:
    typ = (a.get("type") or "item").strip().lower()
    return f"which {typ} are you picking? 🤔"


def _fact(a: dict, b: dict, ctx: Ctx) -> str:
    """One line after the lock-in, true to the data: the one leaving at the
    next reset, the one new in today's shop, an OG, else the price gap."""
    kinds = [{k for k, _ in _facts(it, ctx)} for it in (a, b)]
    has = [i for i in (0, 1) if "leaves" in kinds[i]]
    if len(has) == 1:
        return f"{'AB'[has[0]]} leaves at the next reset ⏰"
    intro = [((a, b)[i].get("introduction") or {}) for i in (0, 1)]
    og = [i for i in (0, 1) if "og" in kinds[i] and str(intro[i].get("chapter")) == "1"]
    if len(og) == 1:                                     # the classic recap's OG · CH1 S4
        se = str(intro[og[0]].get("season") or "")
        return f"{'AB'[og[0]]} is og · chapter 1" + (f", season {se}" if se else "") + " 🔥"
    new = [i for i in (0, 1) if (a, b)[i].get("in_day") == ctx.day.isoformat()]
    if len(new) == 1:
        return f"{'AB'[new[0]]} is new in today's shop 🆕"
    pa, pb = int(a["price"]), int(b["price"])
    if pa == pb:
        return f"same price: {pa:,} V-Bucks each 🤝"
    hi = "A" if pa > pb else "B"
    return f"{hi} costs {abs(pa - pb):,} V-Bucks more 👀"


def build(ctx: Ctx, **_):
    pairs = _pairs(ctx)
    if not pairs:
        return None
    n = len(pairs)
    beat = ED.music_for(ctx.seed, "hype", day=ctx.day, salt="this_or_that")
    u = beat.unit
    k, outro = next(((k, o) for k in sorted(PLAN) for o in (OUTRO, OUTRO + 4)
                     if u(HOOK + n * k + o) >= MIN_CONTENT), (max(PLAN), OUTRO))
    total = HOOK + n * k + outro
    content_end = u(total)
    if content_end > MAX_CONTENT:
        return None
    nq, nr = PLAN[k]
    ed = ED.Edit(beat, content_end, ctx.seed)
    ed.say(.25, "This or that? Today's Item Shop edition!")
    cam, rnd = ed.cam, ed.rnd
    arts = {id(it): ctx.art(it) for pr in pairs for it in pr}

    def tile_for(it, x, y, w, h, **kw):
        iid = ed.uid("t")
        return iid, ED.tile(ed.src(arts[id(it)]), it, x, y, w, h, iid, trim=trim_for(it), **kw)

    def name_cap(it, side, start, rot=0.0):
        nm = it["name"]
        size, lines = _fit(nm, TW - 30, 34, 10), 1
        if size < 28:
            size, lines = min(32.0, _fit(nm, TW - 30, 34, 22, lines=2)), 2
        y = COUNT_Y - 4 - lines * 1.36 * size
        return ED.caption(nm, TCX[side], y, size, start, style="dark", width=TW - 10, weight=700, rot=rot)

    def price_cap(it, side, start, rot=0.0):
        size = _fit("0,000 V-Bucks", TW - 40, COUNT_SIZE, 36)
        return ED.caption(f"{int(it['price']):,} V-Bucks", TCX[side], COUNT_Y, size, start, width=TW, weight=900,
                          rot=rot, lh=1.28)

    def slot(text, start, end, size=52, rot=0.0, style="box"):
        size = _fit(text, Q_W - 60, size, 38, lines=2)
        lines = _nlines(text, size, Q_W - 60)
        y = Q_Y + max(0.0, (Q_H - lines * 1.36 * size) / 2)
        return ED.caption(text, 540, y, size, start, end, style=style, width=Q_W, weight=800, rot=rot)

    def letter(side, start):
        """A / B under its tile, like higher or lower's buttons."""
        return ED.caption("AB"[side], TCX[side], BTN_Y, BTN_SIZE, start, width=200, weight=900, rot=(-4, 4)[side],
                          lh=1.1)

    # ------------------------------------------------------------ cover: units 0-8
    t_game = u(HOOK)
    a0, b0 = pairs[0]
    id0, tl = tile_for(a0, TX[0], TY, TW, TH, extra="transform:rotate(-2deg)")
    _, tr = tile_for(b0, TX[1], TY, TW, TH, extra="transform:rotate(2deg)")
    ed.scene(0, t_game, ED.canvas(id0, ED.tile_colors(a0), 1.2, .5) + tl + tr)
    ed.over(0, t_game,
            ED.caption(f"item shop · {ctx.day:%b} {ctx.day.day}".lower(), TOP_R, 298, 44, -1, style="dark",
                       align="right", width=560, weight=800)
            + ED.caption("this or that? 🤔", 540, 546, 88, -1, width=980, weight=900, rot=-2)
            + name_cap(a0, 0, -1, -2) + name_cap(b0, 1, -1, 2)
            + price_cap(a0, 0, -1, -2) + price_cap(b0, 1, -1, 2)
            + ED.caption("comment A or B 👇", MID_X, BTN_Y + 6, 40, -1, u(4) - FRAME, style="dark", width=820,
                         weight=800)
            + ED.caption(f"{n} rounds, no wrong answers 🤝", MID_X, BTN_Y + 2, 46, u(4), width=820, weight=800,
                         rot=2))
    cam.push(0, t_game, 1.0, 1.05, MID_X, CAM_Y)
    cam.punch(u(4), .06)
    ed.cue(u(4), "impact")
    ed.cue(u(4), "pop2")

    # ------------------------------------------------------------ the rounds
    ui = HOOK
    for r, (a, b) in enumerate(pairs):
        last = r == n - 1
        s0 = ui
        start, end = u(s0), u(s0 + k)
        bu = lambda i, s0=s0: u(s0 + i)                   # noqa: E731
        ida, tl = tile_for(a, TX[0], TY, TW, TH)
        _, tr = tile_for(b, TX[1], TY, TW, TH)
        ed.scene(start, end, ED.canvas(ida, ED.tile_colors(a), 1.2, .5) + tl + tr)
        cam.push(start, end, 1.0, 1.04, MID_X, CAM_Y)

        ab = (2, 3) if nq == 1 else (4, 6)                # A, then B
        vs = 8 if nq >= 3 else None
        cd = 4 * nq
        land = cd + 4
        after = {1: [land, land + 2], 2: [land, land + 2, land + 5], 3: [land, land + 2, land + 5, land + 8]}[nr]
        lines = [("lock it in 🔒", "lime"), (_fact(a, b, ctx), "box"), ("comment A or B 👇", "box")]
        if nr == 1:
            lines = [lines[0], lines[2]]
        if nr == 3:
            lines.append((f"{r + 1} down, {n - r - 1} to go 👀" if not last else "last one 😤", "box"))

        over = ED.caption("final round 😤" if last else f"round {r + 1}/{n}", TOP_R, 300, 36, start - 1,
                          style="lime" if last else "dark", align="right", width=440, weight=800)
        over += name_cap(a, 0, start - 1) + name_cap(b, 1, start - 1)
        over += price_cap(a, 0, start - 1) + price_cap(b, 1, start - 1)
        over += slot(_question(a), bu(1), bu(land) - FRAME, rot=rnd.choice([-2, -1.5, 1.5, 2]))
        for j, (t, (text, style)) in enumerate(zip(after, lines)):
            nxt = after[j + 1] if j + 1 < min(len(after), len(lines)) else None
            over += slot(text, bu(t), None if nxt is None else bu(nxt) - FRAME, 60 if style == "lime" else 54,
                         rot=rnd.choice([-3, -2, 2, 3]), style=style)
        over += letter(0, bu(ab[0])) + letter(1, bu(ab[1]))
        if vs is not None:
            over += ED.outline("vs", MID_X, CAM_Y - 70, 110, bu(vs), bu(cd) - FRAME, align="center", width=300)
        for j, word in enumerate("321"):
            over += ED.caption(word, MID_X, CAM_Y - CD_SIZE / 2, CD_SIZE, bu(cd + j), bu(cd + j + 1) - FRAME,
                               style="outlm" if word == "1" else "out", width=320, weight=900, lh=1.0,
                               anim="edslam")
        over += ED.emoji("🔒", MID_X, CAM_Y, 150, bu(land), bu(land + 2) - FRAME)
        ed.over(start, end, over)

        # sound and camera
        ed.cue(bu(1), "pop2")
        for t in ab:
            ed.cue(bu(t), "pop2")
            cam.punch(bu(t), .03, .22)
        if vs is not None:
            ed.cue(bu(vs), "impact")
            cam.punch(bu(vs), .05, .3)
        for j, amt in enumerate((.03, .04, .05)):
            ed.cue(bu(cd + j), "tick2")
            cam.punch(bu(cd + j), amt, .22)
        ed.cue(bu(land), "boom" if last else "impact")
        ed.cue(bu(land), "shutter")
        cam.shake(bu(land), 20 if last else 14, .4, 1.4 if last else 1)
        cam.punch(bu(land), .08 if last else .05, .35)
        cam.flash(bu(land), .45 if last else .3, .2)
        for t in after[1:len(lines)]:
            ed.cue(bu(t), "pop2")
        # the cut into this round
        ed.cue(start, "impact")
        if r % 2 == 0:
            cam.zoom(start, .45)
            cam.punch(start, .06)
        else:
            cam.whip(start, 1, 0, 480)
            cam.punch(start, .05)
        ed.cue(start - .16, "swoosh")
        if last:
            ed.cue(start, "glitch")
            cam.flash(start, .35, .12)
        busy = {0, 1, *ab, cd, cd + 1, cd + 2, land, *after[:len(lines)]} | ({vs} if vs is not None else set())
        for bb in range(4, k, 4):
            if all(abs(bb - x) >= 1 for x in busy):
                cam.punch(bu(bb), .025, .25)
        ui += k

    # ------------------------------------------------------------ outro: every pair, A's over B's
    t_out = u(ui)
    top, bottom, gap = 722, 1300, 14
    w = (840 - (n - 1) * gap) / n
    h = (bottom - top - 44) / 2
    tiles, labels, first = "", "", ""
    for i, (a, b) in enumerate(pairs):
        x = 60 + i * (w + gap)
        for row, it in enumerate((a, b)):
            y = top + row * (h + 44)
            iid, html = tile_for(it, x, y, w, h, fig=.92)
            first = first or iid
            tiles += html
            at = u(ui + i + row / 2)                      # round by round on the beat, A then B
            labels += ED.caption(f"{i + 1}{'AB'[row]}", x + w / 2, y + h - 44, 30, at, width=w + 10, weight=900)
            ed.cue(at, "pop2")
    example = "ABBAB"[:n]
    t_code = u(ui + n + 1)
    ed.scene(t_out, content_end, ED.canvas(first, ED.tile_colors(pairs[0][0]), 1.0, .6) + tiles)
    ed.over(t_out, content_end,
            ED.caption("no wrong answers 🤝", TOP_R, 300, 36, t_out - 1, style="dark", align="right", width=440,
                       weight=800)
            + ED.caption(f"comment your picks like {example} 👇", 540, 548, 56, t_out, width=940, weight=800,
                         rot=-1.5)
            + labels
            + ED.caption("use code BAD in the item shop 💚", MID_X, 1340, 44, t_code, style="lime", width=820,
                         weight=800))
    cam.whip(t_out, 0, 1, 560)
    ed.cue(t_out - .16, "swoosh")
    ed.cue(t_out, "impact")
    cam.push(t_out, content_end, 1.0, 1.04, MID_X, 1000)
    cam.punch(t_code, .05)
    ed.cue(t_code, "pop2")
    for bb in range(8, outro, 4):
        if abs(bb - (n + 1)) >= 1:
            cam.punch(u(ui + bb), .025, .25)

    comp = ed.finish()

    # ------------------------------------------------------------ the post: the classic's words
    rounds = "\n".join(f"{num(i)} {a['name']} vs {b['name']}" for i, (a, b) in enumerate(pairs, 1))
    tags = _hashtags("thisorthat", *(p[0]["name"] for p in pairs[:2]))
    return Video(
        "edit_this_or_that", comp,
        title=f"This or That — Fortnite Item Shop, {ctx.day_label}",
        yt_title=f"This or That: Fortnite Item Shop {ctx.day_label} #shorts",
        caption=_caption(f"This or that, Item Shop edition ⚔️\n"
                         f"{n} rounds, all from today's shop ({ctx.day:%B} {ctx.day.day}). A or B?",
                         rounds, f"Drop your picks in order, like {example}", tags),
        hashtags=tags)
