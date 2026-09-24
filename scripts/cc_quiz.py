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
first frame is the thumbnail with the big CREATOR CODE BAD stamp, the corner
badge and #EpicPartner stay up the whole way, and the USE CREATOR CODE BAD outro
closes it.

Truth rules: every answer is a field of the item in the plan (its introduction
season, its name or its set). Descriptions and thumbnails never give an answer
away: silhouettes stay black on the first frame, and the name quizzes list no
names.

Every round ends on the same beat: the ring drains, a drumroll builds, then the
answer lands with a ding and a clap -- all synthesized in cc_audio.
"""

import cc_looks as LK
from cc_formats import (BRAND_TAGS, SILHOUETTE, Ctx, Video, num, _caption, _hook_scene, _outro_scene,
                        _pad, _tag)
from cc_motion import (ACCENT, INK, RARITY, W, H, SAFE_TOP, SAFE_RIGHT, Comp, an, anton_em, burst,
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

# Layout (px). Everything important sits in y 190..1480; below y=880 it stays
# left of x=960, clear of TikTok's like/comment rail.
ART_CX, ART_CY, ART_H = 450, 690, 520
RING_CX, RING_CY, RING = 890, 520, 170
FACT_Y = 968
OPT_X, OPT_Y, OPT_W, OPT_H, OPT_STEP = 60, 1040, 840, 96, 108

# burst() pieces are opaque at their first keyframe, so with fill "both" they would
# sit on the right answer before the reveal -- a spoiler. Same motion, invisible
# until launch (as cc_fmt_guess_price does, in these documents only).
BURST_FIX = ("@keyframes burst{0%{transform:translate(0,0) rotate(0) scale(1);opacity:0}3%{opacity:1}"
             "100%{transform:translate(var(--dx),var(--dy)) rotate(var(--r)) scale(.35);opacity:0}}")

CHECK_SVG = (f'<svg width="54" height="54" viewBox="0 0 30 30"><path d="M5 16 L12 23 L25 7" fill="none" '
             f'stroke="{INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>')


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
    return comp


def _colors(item: dict, theme: dict = None) -> list:
    """A round's background: the item's rarity colour, or a series' own palette."""
    if theme:
        return theme["bg"]
    return [RARITY.get(item["rarity"], "#3a3a44"), "#101014"]


def _deco(theme: dict, t0: float) -> str:
    """A series' decorations for a scene starting at t0 (nothing otherwise)."""
    return theme["deco"](t0) if theme else ""


def _question(text: str, t0: float) -> str:
    size = min(92, 900 / anton_em(text))
    return words(text, W / 2, 300, size, t0 + T_Q, "#fff", .06, "slam", "center", 1000)


def _fact(text: str, start: float, color: str = ACCENT) -> str:
    return label(text, W / 2, FACT_Y, 34, start, color, 800, align="center",
                 bg="rgba(10,10,11,.82)", pad="10px 24px", spacing=".06em")


def _round_cues(comp: Comp, t0: float, reveal: float, cd_start: float):
    comp.cue(t0 + T_ART, "whoosh")
    comp.cue(t0 + T_OPT, "pop")
    for s in range(3):
        comp.cue(cd_start + s, "tick")
    comp.cue(reveal - 1.6, "drumroll")
    comp.cue(reveal, "ding")
    comp.cue(reveal + .12, "clap")


def _options(comp: Comp, opts: list, answer: int, t0: float, reveal: float) -> str:
    """Four answer pills, A to D. On the reveal the right one turns lime with a
    tick, and the other three fall back."""
    dim = comp.uid("qdim")
    comp.css(f"@keyframes {dim}{{to{{opacity:.28;transform:scale(.97)}}}}")
    out = []
    for k, text in enumerate(opts):
        y = OPT_Y + k * OPT_STEP
        fs = min(50, (OPT_W - 190) / max(anton_em(text), .1))
        right = k == answer
        enter = style_anim(an("rise", t0 + T_OPT + k * .07, .4))
        after = style_anim(an("pulse", reveal, .45) if right else an(dim, reveal, .35))
        txt = lambda c, a: (f'<div class="abs d" style="left:112px;right:80px;top:0;height:{OPT_H}px;'
                            f'display:flex;align-items:center;font-size:{fs:.0f}px;line-height:1;'
                            f'white-space:nowrap;color:{c};{a}">{esc(text.upper())}</div>')
        win = ""
        if right:
            win = (f'<div class="abs" style="inset:0;border-radius:18px;background:{ACCENT};'
                   f'box-shadow:0 0 50px rgba(232,255,58,.5);{style_anim(an("fadein", reveal, .15))}"></div>'
                   + txt(INK, style_anim(an("fadein", reveal, .15)))
                   + f'<div class="abs" style="right:18px;top:21px;{style_anim(an("pop", reveal + .05, .4))}">'
                     f'{CHECK_SVG}</div>')
        plain = txt("#fff", style_anim(an("fadeout", reveal, .15)) if right else "")
        out.append(
            f'<div class="abs" style="left:{OPT_X}px;top:{y}px;width:{OPT_W}px;height:{OPT_H}px;{enter}">'
            f'<div class="full" style="transform-origin:0 50%;{after}">'
            f'<div class="abs" style="inset:0;border-radius:18px;background:rgba(10,10,11,.86);'
            f'border:3px solid rgba(255,255,255,.22)"></div>{plain}{win}'
            f'<div class="abs d" style="left:14px;top:13px;width:70px;height:70px;border-radius:14px;'
            f'background:{INK};border:3px solid {ACCENT};color:{ACCENT};font-size:48px;display:flex;'
            f'align-items:center;justify-content:center">{LETTERS[k]}</div></div></div>')
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
                   theme: dict = None, reveal_fact: str = ""):
    """One round: the cosmetic, a question, four options and a ring.

    mode "plain" shows the cosmetic as is; "silhouette" blacks it out until the
    reveal; "zoom" starts in close on `focus` and pulls back as the ring
    drains, then all the way out on the reveal. `reveal_fact` replaces the
    line that lands with the answer."""
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
        inner += (f'<div class="abs" style="left:60px;top:410px;width:740px;height:540px;border-radius:28px;'
                  f'overflow:hidden;border:6px solid {ACCENT};background:radial-gradient(circle at 50% 40%,'
                  f'{RARITY.get(item["rarity"], "#3a3a44")},#101014 80%);{style_anim(an("pop", t0 + T_ART, .5))}">'
                  f'<div class="full" style="transform-origin:{fx * 100:.1f}% {fy * 100:.1f}%;'
                  f'{style_anim(an(zk, start, end - start, "linear"))}">'
                  f'<img src="{art}" style="width:100%;height:100%;object-fit:contain"></div></div>')
    else:
        pic = character(art, ART_CX, ART_CY, ART_H, t0 + T_ART, "pop", .6, "float", item["rarity"], item["name"])
        if mode == "silhouette":
            unsil = comp.uid("unsil")
            comp.css(f"@keyframes {unsil}{{from{{filter:{SILHOUETTE}}}to{{filter:brightness(1) "
                     f"drop-shadow(0 0 0 rgba(255,255,255,0)) drop-shadow(0 0 0 rgba(232,255,58,0))}}}}")
            pic = f'<div class="full" style="{style_anim(an(unsil, reveal, .35))}">{pic}</div>'
        inner += pic
    inner += _question(question, t0)
    inner += countdown(CD, RING_CX, RING_CY, RING, t0 + T_CD)
    if show_name:
        first = _fact(f"{item['name']} · {item['type']}".upper(), t0 + T_OPT, "#fff")
        if reveal_fact:         # the answer's line takes its place
            first = f'<div style="{style_anim(an("fadeout", reveal, .15))}">{first}</div>'
        inner += first
    if reveal_fact or not show_name:
        inner += _fact(reveal_fact or f"{item['name']} · {item['season_label']}".upper(), reveal + .15)
    inner += _options(comp, opts, answer, t0, reveal)
    inner += burst(OPT_X + OPT_W / 2, OPT_Y + answer * OPT_STEP + OPT_H / 2, reveal, ctx.seed + k)
    inner += sticker("GOT IT?", 700, 860, 46, reveal + .45, bg="#ffffff", rot=6)
    inner += progress(t0, t0 + R1, k, n)
    comp.scene(t0, t0 + R1, inner, fade_in=.25, fade_out=.25)
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
    if look:
        comp = look.guess_season(ctx, spec, [(items[rd["item"]], rd["options"], rd["answer"]) for rd in rounds])
    else:
        content_end = HOOK + n * R1
        comp = _comp(content_end)
        first = [items[rd["item"]] for rd in rounds[:2]]
        _hook_scene(comp, ctx, "GUESS THE SEASON", "WHEN DID EACH ONE COME OUT?", f"{n} ROUNDS", HOOK + .3,
                    *first, kicker=f"FORTNITE QUIZ #{spec['episode']}")
        comp.cue(.2, "airhorn"); comp.cue(.9, "pop")
        for k, rd in enumerate(rounds, 1):
            it = items[rd["item"]]
            _picture_round(comp, ctx, HOOK + (k - 1) * R1, k, n, it, "WHAT SEASON?", rd["options"], rd["answer"])
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
    if look:
        comp = look.whos_that(ctx, spec, [(items[rd["item"]], rd["options"], rd["answer"]) for rd in rounds])
    else:
        content_end = HOOK + n * R1
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
            _picture_round(comp, ctx, HOOK + (k - 1) * R1, k, n, it, "WHO IS THIS?" if zoom else "WHO'S THAT SKIN?",
                           rd["options"], rd["answer"], mode="zoom" if zoom else "silhouette",
                           focus=rd.get("focus"), show_name=False, theme=theme,
                           reveal_fact=theme["fact"](it) if theme else "")
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


def which_first(spec: dict, items: dict, ctx: Ctx, theme: dict = None):
    rounds = _usable(ctx, spec["rounds"], ("a", "b"), items, 5)
    if len(rounds) < 4:
        return None
    n = len(rounds)
    content_end = HOOK + n * R2
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
        t0 = HOOK + (k - 1) * R2
        reveal = t0 + T2_REV
        a, b = items[rd["a"]], items[rd["b"]]
        first_is_a = rd["answer"] == "a"
        dim = comp.uid("qdim")
        comp.css(f"@keyframes {dim}{{to{{opacity:.35;filter:grayscale(.8)}}}}")
        side = lambda is_first, ox, oy: (f"transform-origin:{ox}px {oy}px;"
                                          + style_anim(an("pulse", reveal, .45) if is_first else an(dim, reveal, .4)))
        bg_b = theme["bg2"] if theme else _colors(b)
        inner = (f'<div class="abs" style="left:0;top:0;width:{W / 2 + 60}px;height:{H}px;'
                 f'clip-path:polygon(0 0,100% 0,calc(100% - 120px) 100%,0 100%)">'
                 f'{tile_bg(_colors(a, theme), a["rarity"], t0)}</div>'
                 f'<div class="abs" style="right:0;top:0;width:{W / 2 + 60}px;height:{H}px;'
                 f'clip-path:polygon(120px 0,100% 0,100% 100%,0 100%)">{tile_bg(bg_b, b["rarity"], t0)}</div>')
        inner += _deco(theme, t0)
        inner += _question("WHICH CAME FIRST?", t0)
        inner += (f'<div class="full" style="{side(first_is_a, 285, 860)}">'
                  + character(ctx.art(a), 285, 860, 620, t0 + .1, "fromL", .7, "float", a["rarity"], a["name"])
                  + words(a["name"], 50, 1210, min(60, 820 / anton_em(a["name"])), t0 + .8, "#fff", .06,
                          "rise", "left", 440)
                  + "</div>")
        inner += (f'<div class="full" style="{side(not first_is_a, 800, 900)}">'
                  + character(ctx.art(b), 800, 900, 620, t0 + .25, "fromR", .7, "sway", b["rarity"], b["name"])
                  + words(b["name"], SAFE_RIGHT - 10, 1210, min(60, 820 / anton_em(b["name"])), t0 + .9,
                          "#fff", .06, "rise", "right", 440)
                  + "</div>")
        inner += sticker("A", 70, 420, 110, t0 + .5, rot=-8)
        inner += sticker("B", 880, 420, 110, t0 + .6, bg="#ffffff", rot=7)
        # After the reveal: when each came out, the older in lime with FIRST!.
        for it, is_first, x, align in ((a, first_is_a, 50, "left"), (b, not first_is_a, SAFE_RIGHT - 10, "right")):
            when = theme["when"](it) if theme else it["season_label"].upper()
            inner += label(when, x, 1370, 32, reveal + .1, ACCENT if is_first else "#fff",
                           800, align=align, bg="rgba(10,10,11,.82)", pad="8px 18px", width=0)
        fx = 150 if first_is_a else 640
        inner += sticker("FIRST!", fx, 560, 84, reveal + .05, rot=-6 if first_is_a else 6)
        inner += burst(285 if first_is_a else 800, 700, reveal, ctx.seed + k)
        inner += countdown(CD, W / 2, 680, 230, t0 + T2_CD, "A OR B?")
        inner += progress(t0, t0 + R2, k, n)
        comp.scene(t0, t0 + R2, inner, fade_in=.25, fade_out=.25)
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

GRID = [(60, 390), (520, 390), (60, 850), (520, 850)]
CARD = 420


def odd_one_out(spec: dict, items: dict, ctx: Ctx):
    rounds = [rd for rd in spec["rounds"] if all(ctx.art(items[i]) for i in rd["items"])][:5]
    if len(rounds) < 4:
        return None
    n = len(rounds)
    look = LK.get("odd_one_out")
    if look:
        comp = look.odd_one_out(ctx, spec, [([items[i] for i in rd["items"]], rd["answer"], rd["set"])
                                           for rd in rounds])
    else:
        content_end = HOOK + n * R2
        comp = _comp(content_end)
        r0 = [items[i] for i in rounds[0]["items"]]
        _hook_scene(comp, ctx, "ODD ONE OUT", "3 SHARE A SET. 1 DOESN'T", f"{n} ROUNDS", HOOK + .3, r0[0], r0[1],
                    kicker=f"FORTNITE QUIZ #{spec['episode']}")
        comp.cue(.2, "airhorn"); comp.cue(.9, "pop")

        for k, rd in enumerate(rounds, 1):
            t0 = HOOK + (k - 1) * R2
            reveal = t0 + T2_REV
            four = [items[i] for i in rd["items"]]
            dim = comp.uid("qdim")
            comp.css(f"@keyframes {dim}{{to{{opacity:.45}}}}")
            inner = tile_bg(["#2a2d36", "#0c0d10"], "", t0)
            inner += _question("ODD ONE OUT?", t0)
            for j, (it, (x, y)) in enumerate(zip(four, GRID)):
                odd = j == rd["answer"]
                enter = style_anim(an("pop", t0 + .1 + j * .12, .5))
                after = style_anim(an("pulse", reveal, .45) if odd else an(dim, reveal + 1.2, .5))
                ring = (f'<div class="abs" style="inset:-8px;border-radius:30px;border:8px solid {ACCENT};'
                        f'box-shadow:0 0 50px rgba(232,255,58,.6);{style_anim(an("fadein", reveal, .15))}"></div>'
                        if odd else "")
                name_fs = min(28, 360 / max(len(it["name"]) * .55, 1))
                inner += (f'<div class="abs" style="left:{x}px;top:{y}px;width:{CARD}px;height:{CARD}px;{enter}">'
                          f'<div class="full" style="{after}">'
                          f'<div class="abs" style="inset:0;border-radius:24px;overflow:hidden;'
                          f'background:radial-gradient(circle at 50% 38%,{RARITY.get(it["rarity"], "#3a3a44")},'
                          f'#101014 85%);border:3px solid rgba(255,255,255,.2)">'
                          f'<img src="{ctx.art(it)}" style="position:absolute;left:10%;top:4%;width:80%;height:78%;'
                          f'object-fit:contain;filter:drop-shadow(0 16px 20px rgba(0,0,0,.5))">'
                          f'<div class="abs" style="left:0;right:0;bottom:0;padding:10px 12px;background:rgba(10,10,11,.8);'
                          f'text-align:center;font-size:{name_fs:.0f}px;font-weight:800;color:#fff;white-space:nowrap;'
                          f'overflow:hidden;text-overflow:ellipsis">{esc(it["name"])}</div></div>'
                          f'<div class="abs d" style="{"left" if j % 2 == 0 else "right"}:14px;top:14px;width:62px;'
                          f'height:62px;border-radius:14px;background:{INK};border:3px solid {ACCENT};color:{ACCENT};'
                          f'font-size:42px;display:flex;align-items:center;justify-content:center">{LETTERS[j]}</div>'
                          f'{ring}</div></div>')
            ox, oy = GRID[rd["answer"]]
            inner += sticker("ODD ONE OUT", ox + 30, oy + CARD - 150, 44, reveal + .1, rot=-5)
            inner += burst(ox + CARD / 2, oy + CARD / 2, reveal, ctx.seed + k)
            other = f"THE OTHER 3: {rd['set'].upper()} SET"
            inner += label(other, 500, 1300, min(38, 800 / (len(other) * .62)), reveal + .3, ACCENT, 800,
                           align="center", bg="rgba(10,10,11,.85)", pad="12px 26px")
            inner += countdown(CD, 500, 830, 150, t0 + T2_CD)
            inner += progress(t0, t0 + R2, k, n)
            comp.scene(t0, t0 + R2, inner, fade_in=.25, fade_out=.25)
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


def throwback(spec: dict, items: dict, ctx: Ctx, theme: dict = None):
    group = [items[i] for i in spec["items"] if ctx.art(items[i])][:8]
    if len(group) < 6:
        return None
    n = len(group)
    gear = spec.get("edition") == "gear"
    season = theme["title"] if theme else spec["season"]      # "Chapter 1 · Season 5"
    look = LK.get("throwback", spec.get("series", ""))
    if look:
        comp = look.throwback(ctx, spec, group, theme)
    else:
        content_end = HOOK + n * R3
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
            t0 = HOOK + (k - 1) * R3
            inner = tile_bg(_colors(it, theme), it["rarity"], t0) + _deco(theme, t0)
            top = theme["era"](it) if theme else season.upper()
            inner += label(top, W / 2, 300, 34, t0, theme["color"] if theme else ACCENT, 800, anim="none",
                           align="center", spacing=".14em")
            inner += character(ctx.art(it), 500, 740, 740, t0 + .1, "pop", .6, "float", it["rarity"], it["name"])
            size = min(96, 860 / max(anton_em(it["name"]), .1))
            inner += words(it["name"], 60, 1180, size, t0 + .45, "#fff", .06, "slam", "left", 880)
            kind = f"{it['rarity_label']} {it['type']}".strip() if it.get("rarity_label") else it["type"]
            if theme:           # when it first came out, from its shop history
                kind = f"{kind} · {theme['debut'](it)}"
            inner += label(kind.upper(), 64, 1190 + size + 18, 34, t0 + .7, ACCENT, 800)
            inner += _pips(k, n, "GEAR" if gear else "SKIN")
            comp.scene(t0, t0 + R3, inner, fade_in=.25, fade_out=.25)
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


def build(spec: dict, items: dict, ctx: Ctx):
    """The Video for one planned entry, or None if its artwork won't load.
    On This Day, the seasonal series and Build Your Loadout live in cc_series."""
    if spec.get("series") or spec["format"] not in BUILDERS:
        import cc_series
        return cc_series.build(spec, items, ctx)
    return BUILDERS[spec["format"]](spec, items, ctx)
