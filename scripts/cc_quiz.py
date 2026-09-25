"""
Quiz videos for @usecodebad: three a day on top of the shop videos, built from
creator-code/quiz/plan.json (see cc_quiz_plan.py).

    Guess the Season   six cosmetics, four seasons to pick from
    Who's That Skin?   six silhouettes, four names each
    Which Came First?  five pairs: which skin is older?
    Zoomed In          six extreme close-ups that pull back
    Odd One Out        five rounds of four: three share a set
    Throwback          eight skins from one season

Same frame as the shop videos, so the code gets the same push in every one: the
first frame is the thumbnail with the big USE CODE: BAD stamp, the corner
badge and #EpicPartner stay up the whole way, and the USE CREATOR CODE BAD outro
closes it.

Every round is laid out for the apps' UI (cc_safe): its words start under the
corner badge and the round counter, everything below y 740 stays left of the
like/comment rail, and nothing sits under the caption block at the bottom. The
artwork is cropped to the cosmetic before the first frame (_char), so a size
means the cosmetic, not Fortnite's square with its transparent margins.

Truth rules: every answer is a field of the item in the plan (its introduction
season, its name or its set). Descriptions and thumbnails never give an answer
away: silhouettes stay black on the first frame, and the name quizzes list no
names.

Every round ends on the same beat: the ring drains, a drumroll builds, then the
answer lands with a ding and a clap -- all synthesized in cc_audio.
"""

import re

import cc_looks as LK
from cc_formats import (BRAND_TAGS, MIN_SECONDS, SILHOUETTE, Ctx, Video, num, _caption, _hook_scene,
                        _outro_scene, _pad, _tag)
from cc_motion import (ACCENT, INK, RARITY, W, H, SAFE_LEFT, SAFE_RIGHT, Comp, an, anton_em, burst,
                       character, code_badge, countdown, disclosure, esc, label, progress, sticker,
                       style_anim, tile_bg, words)

QUIZ_TAGS = ["fortnite", "fortnitequiz", "fortnitetrivia", "fortniteskins"]
LETTERS = "ABCD"
HOOK = 3.0

# A single-picture round (Guess the Season, Who's That Skin?, Zoomed In), in
# seconds from the round's start.
R1 = 9.5
T_ART, T_Q, T_OPT = .1, .3, .55
T_CD, CD = 1.3, 5
T_REV = T_CD + CD

# Layout (px). All of it sits in the apps' safe box (cc_safe): x 60-1020 down to
# y 740, x 60-900 beside the like/comment rail below that, y 230-1420. The top of
# the box belongs to the corner badge (USE CODE: BAD, then #EpicPartner down to
# y 350) and the round counter, so a round's own words start at Q_Y.
Q_Y = 374
MID = (SAFE_LEFT + SAFE_RIGHT) / 2          # 480: the middle of the band beside the rail
NARROW = SAFE_RIGHT - SAFE_LEFT             # 840: that band's width
PLATE = "rgba(10,10,11,.84)"

# The picture round: the question; the picture with the ring beside it, in the
# wide band above the rail; the name line and the four answers beside the rail.
ART_CX, ART_CY, ART_H, ART_MAXW = 440, 712, 470, 600
ZOOM_X, ZOOM_Y, ZOOM_W, ZOOM_H = SAFE_LEFT, 468, 710, 476
RING_CX, RING_CY, RING = 900, 562, 170
FACT_Y = 958
OPT_X, OPT_Y, OPT_W, OPT_H, OPT_STEP = SAFE_LEFT, 1034, NARROW, 84, 94

# burst() pieces are opaque at their first keyframe, so with fill "both" they would
# sit on the right answer before the reveal -- a spoiler. Same motion, invisible
# until launch (as cc_fmt_guess_price does, in these documents only).
BURST_FIX = ("@keyframes burst{0%{transform:translate(0,0) rotate(0) scale(1);opacity:0}3%{opacity:1}"
             "100%{transform:translate(var(--dx),var(--dy)) rotate(var(--r)) scale(.35);opacity:0}}")

CHECK_SVG = (f'<svg width="54" height="54" viewBox="0 0 30 30"><path d="M5 16 L12 23 L25 7" fill="none" '
             f'stroke="{INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>')

# Inter 800 advance widths in em (caps, digits, punctuation), measured in the
# render browser, so a label can be sized to fit instead of running off.
INTER = {
    'A': .75, 'B': .647, 'C': .728, 'D': .706, 'E': .619, 'F': .593, 'G': .738, 'H': .722, 'I': .27,
    'J': .573, 'K': .706, 'L': .565, 'M': .909, 'N': .731, 'O': .747, 'P': .639, 'Q': .747, 'R': .658,
    'S': .668, 'T': .645, 'U': .705, 'V': .742, 'W': 1.033, 'X': .718, 'Y': .709, 'Z': .643, '0': .665,
    '1': .401, '2': .614, '3': .628, '4': .673, '5': .61, '6': .631, '7': .582, '8': .627, '9': .631,
    ' ': .2, '·': .254, ',': .254, ':': .254, '(': .345, ')': .345, '-': .452, "'": .278, '.': .254,
    '!': .258, '?': .585, '&': .663, '/': .379, '#': .635,
}


def _tags(*extra) -> list:
    """Brand tags first, always, then quiz topic tags, then up to 3 specific."""
    seen, out = set(BRAND_TAGS), list(BRAND_TAGS)
    for t in QUIZ_TAGS:
        if t not in seen:
            seen.add(t)
            out.append(t)
    spec = []
    for t in extra:
        t = _tag(t)
        if t and t not in seen:
            seen.add(t)
            spec.append(t)
    return out + spec[:3]


def _comp(content_end: float) -> Comp:
    comp = Comp(content_end + _pad(content_end))
    comp.css(BURST_FIX)
    comp.add(LK.PREP_JS)            # crops the artwork to the cosmetic before the first frame (see _char)
    return comp


def _colors(item: dict, theme: dict = None) -> list:
    """A round's background: the item's rarity colour, or a series' own palette."""
    if theme:
        return theme["bg"]
    return [RARITY.get(item["rarity"], "#3a3a44"), "#101014"]


def _deco(theme: dict, t0: float) -> str:
    """A series' decorations for a scene starting at t0 (nothing otherwise)."""
    return theme["deco"](t0) if theme else ""


def _round_scene(comp: Comp, start: float, end: float, inner: str):
    """A round as a scene. Each one fades in over the one before and that one
    stays up until it's covered (the end card fades in over the last round the
    same way), so the picture never dips to black between rounds."""
    comp.scene(start, end + .3, inner, fade_in=.25, fade_out=.01)


def _stretch(base: float, n: int, cap: float) -> float:
    """A round's length: `base`. Only when artwork that didn't download leaves
    fewer rounds than planned does each run a little longer (up to `cap`), so
    the video reaches its minimum length on rounds, not on a long end card."""
    return max(base, min(cap, (MIN_SECONDS - 7.5 - HOOK) / n))


def _char(uri: str, cx: float, cy: float, h: float, start: float, enter: str = "pop", enter_dur: float = .6,
          idle: str = "float", rarity: str = "rare", name: str = "", maxw: float = 0) -> str:
    """cc_motion.character(), with the artwork cropped to the cosmetic itself
    (cc_looks.PREP_JS, which _comp puts in every quiz). Fortnite's art is a
    square with wide transparent margins; cropped, `h` and `maxw` are the
    cosmetic's own size, so it fills its spot and never spreads past it. A
    wide one that `maxw` makes shorter stands on its shadow, not above it."""
    return (character(uri, cx, cy, h, start, enter, enter_dur, idle, rarity, name, maxw=maxw)
            .replace('<img class="art" ', '<img class="art" data-trim ', 1)
            .replace('style="height:', 'style="object-position:50% 100%;height:', 1))


def _fit(text: str, width: float, cap: float, lines: int = 1) -> float:
    """The biggest Anton size up to `cap` at which `text` fits `width` in at most
    `lines` lines, wrapping between words as the browser does."""
    ems = [anton_em(w) for w in text.split()] or [1.0]
    size = float(cap)
    while size > 16:
        rows, cur = 1, 0.0
        for e in ems:
            if cur and (cur + e) * size > width:
                rows, cur = rows + 1, e
            else:
                cur += e
        if rows <= lines and max(ems) * size <= width:
            break
        size -= 1
    return size


def _inter_em(text: str, spacing: float = 0.0) -> float:
    return sum(INTER.get(ch, .75) + spacing for ch in text.upper())


def _line(text: str, x: float, y: float, size: float, start: float, color: str = "#fff", spacing: float = 0.0,
          anim: str = "rise", maxw: float = NARROW - 20) -> str:
    """A centred line of Inter 800 caps, shrunk to fit `maxw` when it's long."""
    size = min(size, maxw / max(_inter_em(text, spacing), .1))
    return label(text.upper(), x, y, size, start, color, 800, anim=anim, align="center", spacing=f"{spacing}em")


def _plate(html: str, x: float, y: float, size: float, start: float, color: str = "#fff",
           align: str = "left") -> str:
    """Display words on a dark plate, readable over any art. `html` is escaped
    already; x is the plate's left edge, right edge or middle, by `align`."""
    if align == "center":
        pos = f"left:{x - W:.0f}px;width:{2 * W}px;"
    elif align == "right":
        pos = f"right:{W - x:.0f}px;"
    else:
        pos = f"left:{x:.0f}px;"
    return (f'<div class="abs" style="{pos}top:{y:.0f}px;text-align:{align}">'
            f'<div class="d" style="display:inline-block;font-size:{size:.1f}px;line-height:1;color:{color};'
            f'background:{PLATE};padding:.2em .45em .12em;border-radius:12px;white-space:nowrap;'
            f'{style_anim(an("rise", start, .45))}">{html}</div></div>')


def _plate_size(text: str, width: float, cap: float) -> float:
    """The Anton size at which `text` on a _plate fits `width`."""
    return min(cap, width / (anton_em(text) + .9))


def _question(text: str, t0: float, cx: float = W / 2) -> str:
    """The round's question, under the corner badge and the round counter."""
    size = min(80, (2 * (cx - SAFE_LEFT) - 40) / anton_em(text))
    return words(text, cx, Q_Y, size, t0 + T_Q, "#fff", .06, "slam", "center", 1000)


def _fact(text: str, start: float, accent: str = ACCENT) -> str:
    """The line under the picture, "NAME · WHAT IT IS": the name in white, the
    rest in `accent`, on a plate that fits the band beside the rail."""
    head, _, tail = text.partition(" · ")
    body = esc(head) + (f'<span style="color:{accent}"> · {esc(tail)}</span>' if tail else "")
    return _plate(body, MID, FACT_Y, _plate_size(text, NARROW - 40, 42), start, align="center")


def _round_cues(comp: Comp, t0: float, reveal: float, cd_start: float):
    comp.cue(t0 + T_ART, "whoosh")
    comp.cue(t0 + T_OPT, "pop")
    for s in range(3):
        comp.cue(cd_start + s, "tick")
    comp.cue(reveal - 1.6, "drumroll")
    comp.cue(reveal, "ding")
    comp.cue(reveal + .12, "clap")


def _options(comp: Comp, opts: list, answer: int, t0: float, reveal: float) -> str:
    """Four answer pills, A to D, in the band beside the rail. On the reveal the
    right one turns lime with a tick, and the other three fall back."""
    dim = comp.uid("qdim")
    comp.css(f"@keyframes {dim}{{to{{opacity:.28;transform:scale(.97)}}}}")
    out = []
    for k, text in enumerate(opts):
        y = OPT_Y + k * OPT_STEP
        fs = min(48, (OPT_W - 172) / max(anton_em(text), .1))
        right = k == answer
        enter = style_anim(an("rise", t0 + T_OPT + k * .07, .4))
        after = style_anim(an("pulse", reveal, .45) if right else an(dim, reveal, .35))
        txt = lambda c, a: (f'<div class="abs d" style="left:94px;right:72px;top:0;height:{OPT_H}px;'
                            f'display:flex;align-items:center;font-size:{fs:.0f}px;line-height:1;'
                            f'white-space:nowrap;color:{c};{a}">{esc(text.upper())}</div>')
        win = ""
        if right:
            win = (f'<div class="abs" style="inset:0;border-radius:18px;background:{ACCENT};'
                   f'box-shadow:0 0 50px rgba(232,255,58,.5);{style_anim(an("fadein", reveal, .15))}"></div>'
                   + txt(INK, style_anim(an("fadein", reveal, .15)))
                   + f'<div class="abs" style="right:14px;top:{(OPT_H - 54) // 2}px;'
                     f'{style_anim(an("pop", reveal + .05, .4))}">{CHECK_SVG}</div>')
        plain = txt("#fff", style_anim(an("fadeout", reveal, .15)) if right else "")
        out.append(
            f'<div class="abs" style="left:{OPT_X}px;top:{y}px;width:{OPT_W}px;height:{OPT_H}px;{enter}">'
            f'<div class="full" style="transform-origin:0 50%;{after}">'
            f'<div class="abs" style="inset:0;border-radius:18px;background:rgba(10,10,11,.86);'
            f'border:3px solid rgba(255,255,255,.22)"></div>{plain}{win}'
            f'<div class="abs d" style="left:12px;top:{(OPT_H - 60) // 2}px;width:60px;height:60px;'
            f'border-radius:13px;background:{INK};border:3px solid {ACCENT};color:{ACCENT};font-size:40px;'
            f'display:flex;align-items:center;justify-content:center">{LETTERS[k]}</div></div></div>')
    return "".join(out)


def _outro(comp: Comp, ctx: Ctx, start: float, ask: str, items: list):
    comp.cue(start + .25, "slam")
    comp.cue(start + .5, "reveal")
    _outro_scene(comp, ctx, start, comp.duration, ask, items)
    comp.add(code_badge(.4))
    comp.add(disclosure())


def _pips(k: int, n: int, word: str) -> str:
    """SKIN 3/8 pips, like progress() but with our own word."""
    return progress(0, 0, k, n).replace(f"ROUND {k}/{n}", f"{word} {k}/{n}")


# ======================================================= single-picture rounds

def _picture_round(comp: Comp, ctx: Ctx, t0: float, k: int, n: int, item: dict, question: str,
                   opts: list, answer: int, *, mode: str = "plain", focus=None, show_name: bool = True,
                   theme: dict = None, reveal_fact: str = "", dur: float = R1):
    """One round: the cosmetic, a question, four options and a ring.

    mode "plain" shows the cosmetic as is; "silhouette" blacks it out until the
    reveal; "zoom" starts in close on `focus` and pulls back as the ring
    drains, then all the way out on the reveal. `reveal_fact` replaces the
    line that lands with the answer. `dur` is the round's length."""
    reveal = t0 + T_REV
    inner = tile_bg(_colors(item, theme), item["rarity"], t0) + _deco(theme, t0)
    art = ctx.art(item)
    if mode == "zoom":
        start, end = t0 + T_ART, reveal + .5
        hold = (reveal - start) / (end - start) * 100
        zk = comp.uid("zoom")
        comp.css(f"@keyframes {zk}{{0%{{transform:scale(3.6)}}{hold:.2f}%{{transform:scale(2.3);"
                 f"animation-timing-function:cubic-bezier(.2,.8,.2,1)}}100%{{transform:scale(1)}}}}")
        fx, fy = focus or (.5, .3)
        inner += (f'<div class="abs" style="left:{ZOOM_X}px;top:{ZOOM_Y}px;width:{ZOOM_W}px;height:{ZOOM_H}px;'
                  f'border-radius:28px;overflow:hidden;border:6px solid {ACCENT};background:radial-gradient('
                  f'circle at 50% 40%,{_colors(item, theme)[0]},#101014 80%);'
                  f'{style_anim(an("pop", t0 + T_ART, .5))}">'
                  f'<div class="full" style="transform-origin:{fx * 100:.1f}% {fy * 100:.1f}%;'
                  f'{style_anim(an(zk, start, end - start, "linear"))}">'
                  f'<img data-trim data-name="{esc(item["name"])}" src="{art}" '
                  f'style="width:100%;height:100%;object-fit:contain"></div></div>')
    else:
        pic = _char(art, ART_CX, ART_CY, ART_H, t0 + T_ART, "pop", .6, "float", item["rarity"], item["name"],
                    maxw=ART_MAXW)
        if mode == "silhouette":
            unsil = comp.uid("unsil")
            comp.css(f"@keyframes {unsil}{{from{{filter:{SILHOUETTE}}}to{{filter:brightness(1) "
                     f"drop-shadow(0 0 0 rgba(255,255,255,0)) drop-shadow(0 0 0 rgba(232,255,58,0))}}}}")
            pic = f'<div class="full" style="{style_anim(an(unsil, reveal, .35))}">{pic}</div>'
        inner += pic
    inner += _question(question, t0)
    inner += countdown(CD, RING_CX, RING_CY, RING, t0 + T_CD)
    if show_name:
        first = _fact(f"{item['name']} · {item['type']}".upper(), t0 + T_OPT, "rgba(255,255,255,.72)")
        if reveal_fact:         # the answer's line takes its place
            first = f'<div style="{style_anim(an("fadeout", reveal, .15))}">{first}</div>'
        inner += first
    if reveal_fact or not show_name:
        inner += _fact(reveal_fact or f"{item['name']} · {item['season_label']}".upper(), reveal + .15)
    inner += _options(comp, opts, answer, t0, reveal)
    inner += burst(OPT_X + OPT_W / 2, OPT_Y + answer * OPT_STEP + OPT_H / 2, reveal, ctx.seed + k)
    inner += sticker("GOT IT?", 792, 668, 44, reveal + .45, bg="#ffffff", rot=6)
    inner += progress(t0, t0 + dur, k, n)
    _round_scene(comp, t0, t0 + dur, inner)
    _round_cues(comp, t0, reveal, t0 + T_CD)


def _usable(ctx: Ctx, rounds: list, keys: tuple, items: dict, want: int) -> list:
    """The first `want` rounds whose artwork all downloaded. The plan carries
    spares for exactly this."""
    out = []
    for rd in rounds:
        if all(ctx.art(items[rd[k]]) for k in keys if k in rd):
            out.append(rd)
        if len(out) == want:
            break
    return out


def guess_season(spec: dict, items: dict, ctx: Ctx):
    rounds = _usable(ctx, spec["rounds"], ("item",), items, 6)
    if len(rounds) < 5:
        return None
    n = len(rounds)
    gear = spec.get("edition") == "gear"
    look = LK.get("guess_season")
    comp = LK.draw(look, "guess_season", ctx, spec,
                   [(items[rd["item"]], rd["options"], rd["answer"]) for rd in rounds])
    if comp is None:
        r1 = _stretch(R1, n, 10.5)
        content_end = HOOK + n * r1
        comp = _comp(content_end)
        first = [items[rd["item"]] for rd in rounds[:2]]
        _hook_scene(comp, ctx, "GUESS THE SEASON", "WHEN DID EACH ONE COME OUT?", f"{n} ROUNDS", HOOK + .3,
                    *first, kicker=f"FORTNITE QUIZ #{spec['episode']}")
        comp.cue(.2, "airhorn"); comp.cue(.9, "pop")
        for k, rd in enumerate(rounds, 1):
            it = items[rd["item"]]
            _picture_round(comp, ctx, HOOK + (k - 1) * r1, k, n, it, "WHAT SEASON?", rd["options"], rd["answer"],
                           dur=r1)
        _outro(comp, ctx, content_end, f"HOW MANY DID YOU GET OUT OF {n}?", [items[rd["item"]] for rd in rounds])

    what = "pickaxes, gliders and back blings" if gear else "skins"
    body = "\n".join(f"{num(k)} {items[rd['item']]['name']} · {items[rd['item']]['type']}"
                     for k, rd in enumerate(rounds, 1))
    tags = _tags("guesstheseason", "ogfortnite")
    t = f"Guess the Season — Fortnite Quiz #{spec['episode']}"
    return Video("guess_season", comp, title=t,
                 yt_title=f"Guess the Season: Fortnite Quiz #{spec['episode']} #shorts",
                 caption=_caption(f"🗓️ GUESS THE SEASON — Fortnite Quiz #{spec['episode']}\n"
                                  f"{n} {what}. When did each one come out? Pause, guess, then watch 👇",
                                  body, f"How many did you get out of {n}? Comment your score", tags),
                 hashtags=tags)


def _name_quiz(spec: dict, items: dict, ctx: Ctx, fmt: str, theme: dict = None):
    rounds = _usable(ctx, spec["rounds"], ("item",), items, 6)
    if len(rounds) < 5:
        return None
    n = len(rounds)
    zoom = fmt == "zoomed_in"
    look = LK.get(fmt) if not theme else None
    comp = LK.draw(look, "whos_that", ctx, spec,
                   [(items[rd["item"]], rd["options"], rd["answer"]) for rd in rounds])
    if comp is None:
        r1 = _stretch(R1, n, 10.5)
        content_end = HOOK + n * r1
        comp = _comp(content_end)
        first = [items[rd["item"]] for rd in rounds[:2]]
        title = "ZOOMED IN" if zoom else "WHO'S THAT SKIN?"
        if theme:
            _hook_scene(comp, ctx, title, theme["sub"], theme["stick"], HOOK + .3, *first, colors=theme["bg"],
                        kicker=theme["kicker"], kicker_color=theme["color"], silhouette=True, extra=_deco(theme, 0))
        else:
            _hook_scene(comp, ctx, title, "PAUSE AND GUESS" if zoom else "4 CHOICES EACH",
                        f"{n} ROUNDS", HOOK + .3, *first, kicker=f"FORTNITE QUIZ #{spec['episode']}", silhouette=True)
        comp.cue(.2, "airhorn"); comp.cue(.9, "pop")
        for k, rd in enumerate(rounds, 1):
            it = items[rd["item"]]
            _picture_round(comp, ctx, HOOK + (k - 1) * r1, k, n, it, "WHO IS THIS?" if zoom else "WHO'S THAT SKIN?",
                           rd["options"], rd["answer"], mode="zoom" if zoom else "silhouette",
                           focus=rd.get("focus"), show_name=False, theme=theme,
                           reveal_fact=theme["fact"](it) if theme else "", dur=r1)
        _outro(comp, ctx, content_end, f"HOW MANY DID YOU GET OUT OF {n}?", [items[rd["item"]] for rd in rounds])

    ep = spec["episode"]
    if theme:
        return theme["video"](fmt, comp, n, [items[rd["item"]] for rd in rounds])
    if zoom:
        hook = (f"🔍 ZOOMED IN — Fortnite Quiz #{ep}\n"
                f"We start up close. Name the skin before the camera pulls back 👇")
        title_t, yt = f"Zoomed In — Fortnite Quiz #{ep}", f"Zoomed In: Guess the Fortnite Skin #{ep} #shorts"
        tags = _tags("guesstheskin", "zoomedin")
    else:
        hook = (f"👤 WHO'S THAT SKIN? — Fortnite Quiz #{ep}\n"
                f"{n} silhouettes, 4 choices each. Pause and guess 👇")
        title_t, yt = f"Who's That Skin? — Fortnite Quiz #{ep}", f"Who's That Fortnite Skin? Quiz #{ep} #shorts"
        tags = _tags("whosthatskin", "guesstheskin")
    body = f"{n} rounds · 4 choices each · no spoilers here, answers are in the video 🎥"
    return Video(fmt, comp, title=title_t, yt_title=yt,
                 caption=_caption(hook, body, f"How many did you get out of {n}? Comment your score", tags),
                 hashtags=tags)


def whos_that(spec, items, ctx):
    return _name_quiz(spec, items, ctx, "whos_that")


def zoomed_in(spec, items, ctx):
    return _name_quiz(spec, items, ctx, "zoomed_in")


# ============================================================ which came first

R2 = 10.4
T2_CD = 2.6
T2_REV = T2_CD + CD

# A's half and B's half of the band beside the rail, either side of x 480, with
# the A sticker, the ring and the B sticker in a row above the two skins, and
# each skin's name (and, on the reveal, when it came out) under it.
WF_X = (270, 690)
WF_CY, WF_H, WF_MAXW = 926, 540, 390
WF_ROW, WF_RING = 548, 160
WF_NAME_Y, WF_NAME_W = 1212, 400
WF_WHEN_Y = 1338
WF_SPLIT = 540                  # the backgrounds' diagonal runs from x 540 at the top to 420 at the bottom


def which_first(spec: dict, items: dict, ctx: Ctx, theme: dict = None):
    rounds = _usable(ctx, spec["rounds"], ("a", "b"), items, 5)
    if len(rounds) < 4:
        return None
    n = len(rounds)
    r2 = _stretch(R2, n, 12.0)
    content_end = HOOK + n * r2
    comp = _comp(content_end)
    if theme:
        _hook_scene(comp, ctx, "WHICH CAME FIRST?", theme["sub"], theme["stick"], HOOK + .3,
                    items[rounds[0]["a"]], items[rounds[0]["b"]], colors=theme["bg"], kicker=theme["kicker"],
                    kicker_color=theme["color"], extra=_deco(theme, 0))
    else:
        _hook_scene(comp, ctx, "WHICH CAME FIRST?", "OLDER SKIN: A OR B?", f"{n} ROUNDS", HOOK + .3,
                    items[rounds[0]["a"]], items[rounds[0]["b"]], kicker=f"FORTNITE QUIZ #{spec['episode']}")
    comp.cue(.2, "airhorn"); comp.cue(.9, "pop")

    for k, rd in enumerate(rounds, 1):
        t0 = HOOK + (k - 1) * r2
        reveal = t0 + T2_REV
        a, b = items[rd["a"]], items[rd["b"]]
        first_is_a = rd["answer"] == "a"
        dim = comp.uid("qdim")
        comp.css(f"@keyframes {dim}{{to{{opacity:.35;filter:grayscale(.8)}}}}")
        bg_b = theme["bg2"] if theme else _colors(b)
        inner = (f'<div class="abs" style="left:0;top:0;width:{WF_SPLIT}px;height:{H}px;'
                 f'clip-path:polygon(0 0,100% 0,calc(100% - 120px) 100%,0 100%)">'
                 f'{tile_bg(_colors(a, theme), a["rarity"], t0)}</div>'
                 f'<div class="abs" style="left:{WF_SPLIT - 120}px;top:0;width:{W - WF_SPLIT + 120}px;height:{H}px;'
                 f'clip-path:polygon(120px 0,100% 0,100% 100%,0 100%)">{tile_bg(bg_b, b["rarity"], t0)}</div>')
        inner += _deco(theme, t0)
        inner += _question("WHICH CAME FIRST?", t0, MID)
        sides = ((a, first_is_a, WF_X[0], "fromL", "float", t0 + .1, "left", SAFE_LEFT + 4),
                 (b, not first_is_a, WF_X[1], "fromR", "sway", t0 + .25, "right", SAFE_RIGHT - 4))
        for it, is_first, cx, enter, idle, t_in, align, tx in sides:
            # The older one pulses on the reveal, the newer one fades back.
            after = an("pulse", reveal, .45) if is_first else an(dim, reveal, .4)
            size = _fit(it["name"], WF_NAME_W, 58, 2)
            inner += (f'<div class="full" style="transform-origin:{cx}px {WF_CY}px;text-wrap:balance;'
                      f'{style_anim(after)}">'
                      + _char(ctx.art(it), cx, WF_CY, WF_H, t_in, enter, .7, idle, it["rarity"], it["name"],
                              maxw=WF_MAXW)
                      + words(it["name"], tx, WF_NAME_Y, size, t_in + .7, "#fff", .06, "rise", align, WF_NAME_W)
                      + "</div>")
            # After the reveal: when each came out, the older in lime.
            when = theme["when"](it) if theme else it["season_label"].upper()
            inner += _plate(esc(when), tx, WF_WHEN_Y, _plate_size(when, WF_NAME_W, 40), reveal + .1,
                            ACCENT if is_first else "#fff", align)
        inner += sticker("A", WF_X[0] - 73, WF_ROW - 64, 110, t0 + .5, rot=-8)
        inner += sticker("B", WF_X[1] - 73, WF_ROW - 64, 110, t0 + .6, bg="#ffffff", rot=7)
        inner += countdown(CD, MID, WF_ROW, WF_RING, t0 + T2_CD)
        # FIRST! lands across the older skin's legs: its face and outfit stay in view.
        fx = WF_X[0] if first_is_a else WF_X[1]
        inner += sticker("FIRST!", fx - 126, 1010, 80, reveal + .05, rot=-6 if first_is_a else 6)
        inner += burst(fx, 900, reveal, ctx.seed + k)
        inner += progress(t0, t0 + r2, k, n)
        _round_scene(comp, t0, t0 + r2, inner)
        comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .5, "pop")
        for s in range(3):
            comp.cue(t0 + T2_CD + s, "tick")
        comp.cue(reveal - 1.6, "drumroll"); comp.cue(reveal, "ding"); comp.cue(reveal + .12, "clap")

    answers = "".join("A" if rd["answer"] == "a" else "B" for rd in rounds)
    _outro(comp, ctx, content_end, f"COMMENT YOUR {n} ANSWERS", [items[rounds[0]["a"]], items[rounds[0]["b"]],
                                                                  items[rounds[1]["a"]]])
    if theme:
        return theme["video"]("which_first", comp, n, [items[rd[k]] for rd in rounds for k in ("a", "b")],
                              answers=answers)
    ep = spec["episode"]
    body = "\n".join(f"{num(k)} {items[rd['a']]['name']} 🆚 {items[rd['b']]['name']}"
                     for k, rd in enumerate(rounds, 1))
    example = next(e[:n] for e in ("ABBAB", "BABBA", "AABAB") if e[:n] != answers)
    tags = _tags("whichcamefirst", "ogfortnite")
    return Video("which_first", comp, title=f"Which Came First? — Fortnite Quiz #{ep}",
                 yt_title=f"Which Fortnite Skin Came First? Quiz #{ep} #shorts",
                 caption=_caption(f"⏳ WHICH CAME FIRST? — Fortnite Quiz #{ep}\n"
                                  f"{n} rounds. Which skin is older, A or B? 👇",
                                  body, f"Comment your answers in order, like {example}", tags),
                 hashtags=tags)


# ================================================================ odd one out

# Four cards, two by two, in the band beside the rail, with the ring in the
# middle. The top row's names sit along its top edge and the bottom row's along
# its bottom edge, so the middle -- the ring, the four letters -- stays clear.
OO_X, OO_Y = (66, 498), (462, 914)
OO_W, OO_H, OO_STRIP = 396, 416, 106
OO_RING = 120
OO_SET_Y = 1348


def _oo_card(it: dict, art: str, j: int, t0: float, reveal: float, odd: bool, dim: str) -> str:
    x, y = OO_X[j % 2], OO_Y[j // 2]
    top = j < 2
    side = "left" if j % 2 == 0 else "right"
    enter = style_anim(an("pop", t0 + .1 + j * .12, .5))
    after = style_anim(an("pulse", reveal, .45) if odd else an(dim, reveal + 1.2, .5))
    art_top, art_h = (OO_STRIP + 8, OO_H - OO_STRIP - 18) if top else (10, OO_H - OO_STRIP - 18)
    # One line when the name fits big; a long one goes to two even lines.
    size = _fit(it["name"], OO_W - 44, 52)
    if size < 46:
        size = _fit(it["name"], OO_W - 44, 48, 2)
    strip = (f'<div class="abs d" style="left:0;right:0;{"top" if top else "bottom"}:0;height:{OO_STRIP}px;'
             f'padding:0 18px;background:{PLATE};display:flex;align-items:center;justify-content:center;'
             f'text-align:center;text-wrap:balance;font-size:{size:.0f}px;line-height:1;'
             f'color:#fff">{esc(it["name"])}</div>')
    letter = (f'<div class="abs d" style="{side}:14px;{"bottom" if top else "top"}:14px;width:58px;height:58px;'
              f'border-radius:13px;background:{INK};border:3px solid {ACCENT};color:{ACCENT};font-size:40px;'
              f'display:flex;align-items:center;justify-content:center">{LETTERS[j]}</div>')
    ring = (f'<div class="abs" style="inset:-6px;border-radius:30px;border:6px solid {ACCENT};'
            f'box-shadow:0 0 50px rgba(232,255,58,.6);{style_anim(an("fadein", reveal, .15))}"></div>'
            if odd else "")
    return (f'<div class="abs" style="left:{x}px;top:{y}px;width:{OO_W}px;height:{OO_H}px;{enter}">'
            f'<div class="full" style="{after}">'
            f'<div class="abs" style="inset:0;border-radius:24px;overflow:hidden;background:radial-gradient('
            f'circle at 50% 44%,{RARITY.get(it["rarity"], "#3a3a44")},#101014 85%);'
            f'border:3px solid rgba(255,255,255,.2)">'
            f'<img data-trim data-name="{esc(it["name"])}" src="{art}" style="position:absolute;left:6%;'
            f'top:{art_top}px;width:88%;height:{art_h}px;object-fit:contain;object-position:50% 100%;'
            f'filter:drop-shadow(0 16px 20px rgba(0,0,0,.5))">{strip}</div>{letter}{ring}</div></div>')


def odd_one_out(spec: dict, items: dict, ctx: Ctx):
    rounds = [rd for rd in spec["rounds"] if all(ctx.art(items[i]) for i in rd["items"])][:5]
    if len(rounds) < 4:
        return None
    n = len(rounds)
    look = LK.get("odd_one_out")
    comp = LK.draw(look, "odd_one_out", ctx, spec, [([items[i] for i in rd["items"]], rd["answer"], rd["set"])
                                                   for rd in rounds])
    if comp is None:
        r2 = _stretch(R2, n, 12.0)
        content_end = HOOK + n * r2
        comp = _comp(content_end)
        r0 = [items[i] for i in rounds[0]["items"]]
        _hook_scene(comp, ctx, "ODD ONE OUT", "3 SHARE A SET. 1 DOESN'T", f"{n} ROUNDS", HOOK + .3, r0[0], r0[1],
                    kicker=f"FORTNITE QUIZ #{spec['episode']}")
        comp.cue(.2, "airhorn"); comp.cue(.9, "pop")

        for k, rd in enumerate(rounds, 1):
            t0 = HOOK + (k - 1) * r2
            reveal = t0 + T2_REV
            four = [items[i] for i in rd["items"]]
            dim = comp.uid("qdim")
            comp.css(f"@keyframes {dim}{{to{{opacity:.45}}}}")
            inner = tile_bg(["#2a2d36", "#0c0d10"], "", t0)
            inner += _question("ODD ONE OUT?", t0, MID)
            for j, it in enumerate(four):
                inner += _oo_card(it, ctx.art(it), j, t0, reveal, j == rd["answer"], dim)
            j = rd["answer"]
            ox, oy = OO_X[j % 2], OO_Y[j // 2]
            # ODD ONE OUT across the odd card's picture, clear of its name and letter.
            inner += sticker("ODD ONE OUT", ox + 74, oy + (262 if j < 2 else 176), 44, reveal + .1, rot=-5)
            inner += burst(ox + OO_W / 2, oy + OO_H / 2, reveal, ctx.seed + k)
            other = f"THE OTHER 3: {rd['set'].upper()} SET"
            inner += _plate(esc(other), MID, OO_SET_Y, _plate_size(other, NARROW - 40, 42), reveal + .3, ACCENT,
                            "center")
            inner += countdown(CD, MID, (OO_Y[0] + OO_H + OO_Y[1]) / 2, OO_RING, t0 + T2_CD)
            inner += progress(t0, t0 + r2, k, n)
            _round_scene(comp, t0, t0 + r2, inner)
            comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .5, "pop")
            for s in range(3):
                comp.cue(t0 + T2_CD + s, "tick")
            comp.cue(reveal - 1.6, "drumroll"); comp.cue(reveal, "ding"); comp.cue(reveal + .12, "clap")

        _outro(comp, ctx, content_end, f"COMMENT YOUR {n} ANSWERS", [items[i] for i in rounds[0]["items"]])
    ep = spec["episode"]
    answers = "".join(LETTERS[rd["answer"]] for rd in rounds)
    example = next(e[:n] for e in ("BDACB", "CADBD", "DBCAA") if e[:n] != answers)
    body = "\n".join(f"{num(k)} " + " · ".join(items[i]["name"] for i in rd["items"])
                     for k, rd in enumerate(rounds, 1))
    tags = _tags("oddoneout", "fortnitesets")
    return Video("odd_one_out", comp, title=f"Odd One Out — Fortnite Quiz #{ep}",
                 yt_title=f"Odd One Out: Fortnite Skin Quiz #{ep} #shorts",
                 caption=_caption(f"🧩 ODD ONE OUT — Fortnite Quiz #{ep}\n"
                                  f"3 skins in each round share a set. 1 doesn't. Spot it 👇",
                                  body, f"Comment your answers in order, like {example}", tags),
                 hashtags=tags)


# ================================================================== throwback

R3 = 6.5
# One cosmetic at a time, big, on the band beside the rail's middle line, its
# name and what it is under it.
TB_CY, TB_H, TB_MAXW = 792, 700, 780
TB_NAME_Y = 1166


def throwback(spec: dict, items: dict, ctx: Ctx, theme: dict = None):
    group = [items[i] for i in spec["items"] if ctx.art(items[i])][:8]
    if len(group) < 6:
        return None
    n = len(group)
    gear = spec.get("edition") == "gear"
    season = theme["title"] if theme else spec["season"]      # "Chapter 1 · Season 5"
    look = LK.get("throwback", spec.get("series", ""))
    comp = LK.draw(look, "throwback", ctx, spec, group, theme)
    if comp is None:
        r3 = _stretch(R3, n, 8.0)
        content_end = HOOK + n * r3
        comp = _comp(content_end)
        what = "GEAR" if gear else "SKINS"
        if theme:
            _hook_scene(comp, ctx, season.upper(), theme["sub"], theme["stick"], HOOK + .3, group[0], group[1],
                        colors=theme["bg"], kicker=theme["kicker"], kicker_color=theme["color"],
                        extra=_deco(theme, 0))
        else:
            _hook_scene(comp, ctx, season.upper().replace(" · ", " "), "HOW MANY DO YOU REMEMBER?",
                        f"{n} {what}", HOOK + .3, group[0], group[1], kicker="FORTNITE THROWBACK")
        comp.cue(.2, "airhorn"); comp.cue(.9, "pop")
        for k, it in enumerate(group, 1):
            t0 = HOOK + (k - 1) * r3
            inner = tile_bg(_colors(it, theme), it["rarity"], t0) + _deco(theme, t0)
            top = theme["era"](it) if theme else season.upper()
            inner += _line(top, MID, Q_Y, 34, t0, theme["color"] if theme else ACCENT, .14, "none")
            inner += _char(ctx.art(it), MID, TB_CY, TB_H, t0 + .1, "pop", .6, "float", it["rarity"], it["name"],
                           maxw=TB_MAXW)
            size = min(96, (NARROW - 20) / max(anton_em(it["name"]), .1))
            inner += words(it["name"], MID, TB_NAME_Y, size, t0 + .45, "#fff", .06, "slam", "center")
            kind = f"{it['rarity_label']} {it['type']}".strip() if it.get("rarity_label") else it["type"]
            y = TB_NAME_Y + size * .92 + 18
            inner += _line(kind, MID, y, 34, t0 + .7, ACCENT)
            if theme:           # when it first came out, from its shop history
                inner += _line(theme["debut"](it), MID, y + 50, 30, t0 + .8)
            inner += _pips(k, n, "GEAR" if gear else "SKIN")
            _round_scene(comp, t0, t0 + r3, inner)
            comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .45, "pop")

        _outro(comp, ctx, content_end, "WHICH ONE DID YOU OWN?", group)
    if theme:
        return theme["video"]("throwback", comp, n, group)
    body = "\n".join(f"{num(k)} {it['name']} · {it['type']}" for k, it in enumerate(group, 1))
    short = season.replace(" · ", " ")            # "Chapter 1 Season 5"
    tags = _tags("ogfortnite", short.replace(" ", ""), "fortnitethrowback")
    noun = "gear" if gear else "skins"
    return Video("throwback", comp,
                 title=f"Throwback: Fortnite {short} {'Gear' if gear else 'Skins'}",
                 yt_title=f"Fortnite {short} Throwback: Remember These {noun.title()}? #shorts",
                 caption=_caption(f"📼 SEASON THROWBACK — Fortnite {short}\n"
                                  f"{n} {noun} from this season. How many do you remember? 👇",
                                  body, "Which one did you own? Tell us below", tags),
                 hashtags=tags)


BUILDERS = {"guess_season": guess_season, "whos_that": whos_that, "zoomed_in": zoomed_in,
            "which_first": which_first, "odd_one_out": odd_one_out, "throwback": throwback}


# A few cosmetics in Epic's feed carry an internal code as their name
# ("Set_01_TA_SG"). One must never reach the screen, as an answer or a choice.
CODE_NAME = re.compile(r"[A-Za-z]+(?:_[A-Za-z0-9]+)+")


def code_name(name) -> bool:
    return isinstance(name, str) and bool(CODE_NAME.fullmatch(name.strip()))


def _clean(spec: dict, items: dict) -> dict:
    """The plan entry without the rounds, picks and items that would show a code
    name. Rounds with an answer are dropped whole (the plan carries spares);
    a pick list or a choice list just loses the bad entry."""
    def bad(i):
        return isinstance(i, str) and i in items and code_name(items[i]["name"])

    out = dict(spec)
    if isinstance(spec.get("rounds"), list):
        rounds = []
        for rd in spec["rounds"]:
            if "picks" in rd:                                   # On This Day
                picks = [p for p in rd["picks"] if not bad(p.get("item"))]
                if picks:
                    rounds.append(dict(rd, picks=picks))
            elif "answer" not in rd and isinstance(rd.get("items"), list):   # loadout slot
                rounds.append(dict(rd, items=[i for i in rd["items"] if not bad(i)]))
            elif not (any(bad(rd.get(k)) for k in ("item", "a", "b"))
                      or any(bad(i) for i in rd.get("items") or [])
                      or any(code_name(o) for o in rd.get("options") or [])):
                rounds.append(rd)
        out["rounds"] = rounds
    if isinstance(spec.get("items"), list):                   # throwbacks
        out["items"] = [i for i in spec["items"] if not bad(i)]
    return out


def build(spec: dict, items: dict, ctx: Ctx):
    """The Video for one planned entry, or None if its artwork won't load.
    On This Day, the seasonal series and Build Your Loadout live in cc_series."""
    spec = _clean(spec, items)
    if spec.get("series") or spec["format"] not in BUILDERS:
        import cc_series
        return cc_series.build(spec, items, ctx)
    return BUILDERS[spec["format"]](spec, items, ctx)
