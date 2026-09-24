"""
The videos beside the quizzes, built from creator-code/quiz/plan.json (planned
by cc_series_plan.py and cc_quiz_plan.py):

    On This Day         every day: one outfit from the Item Shop on this date, for
                        every year since 2018, oldest first, on a timeline
    Fortnitemares       every day in October: throwbacks to each year's
                        Fortnitemares, and Fortnitemares editions of Who's That
                        Skin?, Zoomed In, Which Came First? and Which Fortnitemares?
    Winterfest          every day in December: throwbacks to what came out during
                        each year's winter event, and Winterfest editions of the quizzes
    Build Your Loadout  in the quiz rotation: outfit, back bling, pickaxe, glider,
                        emote, three choices each, and people comment their combo

Same frame as every other video: the first frame is the thumbnail with the big
CREATOR CODE BAD stamp, the corner badge and #EpicPartner stay up the whole way,
and the USE CREATOR CODE BAD outro closes it.

Truth rules: every date and "first time in the shop" comes from the item's shop
history, every Fortnitemares year from the Fortnite Wiki's lists checked against
that history (see cc_series_plan). Nothing else is claimed.
"""

import random

import cc_quiz as Q
from cc_series_plan import FAMOUS_SERIES, FIRST_SURE
from cc_formats import BRAND_TAGS, Ctx, Video, num, _caption, _hook_scene, _tag
from cc_motion import (ACCENT, INK, RARITY, W, SAFE_TOP, SAFE_RIGHT, an, anton_em, burst, character,
                       countdown, esc, label, progress, sticker, style_anim, tile_bg, words)

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _tags(base: list, *extra) -> list:
    """Brand tags first, always, then the series' own, then up to 3 specific."""
    seen, out = set(), []
    for t in list(BRAND_TAGS) + list(base):
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


def _short_date(iso: str) -> str:
    """'2018-10-26' -> 'OCT 26, 2018'."""
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{MONTHS[m - 1]} {d}, {y}"


def _when(it: dict) -> str:
    """When it first hit the Item Shop, as exactly as the records can say. They
    start on 2017-10-30, so for anything first seen before FIRST_SURE the day
    might be the start of the records rather than its debut: only the year."""
    first = it.get("first_shop") or ""
    return _short_date(first) if first >= FIRST_SURE else first[:4]


def _debut(it: dict) -> str:
    """'SHOP DEBUT OCT 26, 2018', or 'IN THE SHOP IN 2017'."""
    first = it.get("first_shop") or ""
    return f"SHOP DEBUT {_when(it)}" if first >= FIRST_SURE else f"IN THE SHOP IN {_when(it)}"


# ================================================================ On This Day

R_OTD = 6.5
OTD_TAGS = ["fortnite", "fortniteitemshop", "fortniteskins", "onthisday"]


def _timeline(years: list, k: int, t0: float) -> str:
    """The years along the bottom, this one lit, the ones before it ticked off."""
    step = 840 / len(years)
    pills = []
    for j, y in enumerate(years):
        cur, past = j == k, j < k
        bg = ACCENT if cur else ("rgba(255,255,255,.9)" if past else "rgba(10,10,11,.7)")
        fg = INK if cur or past else "rgba(255,255,255,.55)"
        pop = style_anim(an("pop", t0 + .2, .45)) if cur else ""
        pills.append(f'<div class="abs d" style="left:{60 + j * step:.0f}px;top:0;width:{step - 10:.0f}px;'
                     f'height:58px;border-radius:12px;background:{bg};color:{fg};font-size:31px;display:flex;'
                     f'align-items:center;justify-content:center;{pop}">{y}</div>')
    return f'<div class="abs" style="left:0;top:1400px;width:{W}px;height:60px">{"".join(pills)}</div>'


def _years_ago(n: int) -> str:
    return "1 YEAR AGO TODAY" if n == 1 else f"{n} YEARS AGO TODAY"


def _big_year(year, t0: float) -> str:
    """The year, huge and faint, behind the cosmetic."""
    return (f'<div class="abs d" style="left:0;right:0;top:470px;text-align:center;font-size:380px;'
            f'color:rgba(255,255,255,.1);letter-spacing:.02em;{style_anim(an("punch", t0, .6))}">{year}</div>')


def on_this_day(spec: dict, items: dict, ctx: Ctx):
    rounds = []
    for rd in spec["rounds"]:
        pick = next((p for p in rd["picks"] if ctx.art(items[p["item"]])), None)
        if pick:
            rounds.append((rd, items[pick["item"]], pick["debut"]))
    if len(rounds) < 6:
        return None
    bday = spec.get("birthday")
    day = ctx.day
    when = day.strftime("%B %-d")                               # "September 25"
    years = ([bday["year"]] if bday else []) + [rd["year"] for rd, _, _ in rounds]
    n = len(years)
    content_end = Q.HOOK + n * R_OTD
    comp = Q._comp(content_end)

    # The thumbnail: the two strongest picks, first times in the shop first.
    lead = sorted(rounds, key=lambda r: (not r[2], r[1]["rarity"] != "legendary"
                                         and r[1]["series"] not in FAMOUS_SERIES, -r[0]["year"]))[:2]
    span = f"{years[0]}–{years[-1]}"
    if bday:
        _hook_scene(comp, ctx, f"FORTNITE TURNS {bday['age']}", "BATTLE ROYALE CAME OUT ON THIS DAY IN 2017",
                    span, Q.HOOK + .3, lead[0][1], lead[1][1], kicker=f"ON THIS DAY · {when.upper()}")
    else:
        _hook_scene(comp, ctx, "ON THIS DAY", "THE ITEM SHOP ON THIS DATE, EVERY YEAR", span, Q.HOOK + .3,
                    lead[0][1], lead[1][1], kicker=f"FORTNITE ITEM SHOP · {when.upper()}")
    comp.cue(.2, "airhorn"); comp.cue(.9, "pop")

    k = 0
    if bday:
        t0 = Q.HOOK
        inner = tile_bg(["#2b3200", "#0b0c05"], "", t0)
        inner += _big_year(bday["year"], t0)
        inner += label(f"{when.upper()}, {bday['year']}", W / 2, 300, 34, t0, ACCENT, 800, anim="none",
                       align="center", spacing=".14em")
        inner += words(_years_ago(bday["age"]), W / 2, 360, 96, t0 + .15, "#fff", .06, "slam", "center", 1000)
        for i, line in enumerate(("FORTNITE", "BATTLE ROYALE", "COMES OUT")):
            inner += words(line, W / 2, 640 + i * 128, 120, t0 + .5 + i * .15, "#fff", .06, "slam", "center")
        inner += label("PC · PLAYSTATION 4 · XBOX ONE", W / 2, 1190, 36, t0 + 1.2, ACCENT, 800, align="center",
                       bg="rgba(10,10,11,.8)", pad="12px 26px")
        inner += sticker("HAPPY BIRTHDAY!", 330, 1260, 60, t0 + 1.6, rot=-4)
        inner += burst(W / 2, 900, t0 + .6, ctx.seed)
        inner += _timeline(years, 0, t0)
        comp.scene(t0, t0 + R_OTD, inner, fade_in=.25, fade_out=.25)
        comp.cue(t0 + .15, "slam"); comp.cue(t0 + .6, "reveal"); comp.cue(t0 + 1.6, "clap")
        k = 1

    for j, (rd, it, debut) in enumerate(rounds):
        t0 = Q.HOOK + (k + j) * R_OTD
        y = rd["year"]
        inner = tile_bg(Q._colors(it), it["rarity"], t0)
        inner += _big_year(y, t0)
        inner += label(f"{when.upper()}, {y}", W / 2, 300, 34, t0, ACCENT, 800, anim="none", align="center",
                       spacing=".14em")
        inner += words(_years_ago(day.year - y), W / 2, 360, 96, t0 + .15, "#fff", .06, "slam", "center", 1000)
        inner += character(ctx.art(it), 500, 830, 620, t0 + .1, "pop", .6, "float", it["rarity"], it["name"])
        size = min(96, 860 / max(anton_em(it["name"]), .1))
        inner += words(it["name"], 60, 1180, size, t0 + .45, "#fff", .06, "slam", "left", 880)
        line = "FIRST TIME IN THE ITEM SHOP" if debut else "IN THE ITEM SHOP THAT DAY"
        inner += label(line, 64, 1180 + size + 16, 34, t0 + .7, ACCENT if debut else "#fff", 800)
        if debut:
            inner += sticker("NEW THAT DAY!", 590, 560, 54, t0 + .9, rot=6)
        inner += _timeline(years, k + j, t0)
        comp.scene(t0, t0 + R_OTD, inner, fade_in=.25, fade_out=.25)
        comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .15, "slam"); comp.cue(t0 + .45, "pop")
        if debut:
            comp.cue(t0 + .9, "ding")

    # The two thumbnail picks, and the newest one that isn't already among them.
    third = next((r[1] for r in reversed(rounds) if all(r[1] is not x[1] for x in lead)), None)
    Q._outro(comp, ctx, content_end, "WHICH YEAR HAD THE BEST SHOP?", [r[1] for r in lead] + ([third] if third else []))

    body = "\n".join(f"{rd['year']} · {it['name']}" + (" 🆕" if debut else "") for rd, it, debut in rounds)
    if any(d for _, _, d in rounds):
        body += "\n\n🆕 = its first time in the Item Shop"
    tags = _tags(OTD_TAGS, "fortnite" + day.strftime("%B").lower(), *(it["name"] for _, it, _ in lead))
    if bday:
        hook = (f"🎂 FORTNITE BATTLE ROYALE TURNS {bday['age']} — On This Day, {when}\n"
                f"Battle Royale came out on {when}, {bday['year']}. Here's one outfit from the Item Shop "
                f"on this date, every year since 👇")
        title = f"On This Day: Fortnite Battle Royale Turns {bday['age']} ({when})"
        yt = f"Fortnite Battle Royale Turns {bday['age']}: The Item Shop Every {when} #shorts"
        tags = _tags(OTD_TAGS, "fortnitebirthday", *(it["name"] for _, it, _ in lead))
    else:
        hook = (f"📅 ON THIS DAY — Fortnite Item Shop, {when}\n"
                f"One outfit from the Item Shop on this date, every year since {rounds[0][0]['year']} 👇")
        title = f"On This Day in the Fortnite Item Shop: {when}"
        yt = f"Fortnite Item Shop On This Day: {when} ({span}) #shorts"
    return Video("on_this_day", comp, title=title, yt_title=yt,
                 caption=_caption(hook, body, "Which year had the best shop? Tell us below", tags),
                 hashtags=tags)


# ============================================================== Fortnitemares

FM_ORANGE = "#FF8A1E"
FM_BG = ["#3d1360", "#0b0610"]
FM_BG2 = ["#5a2208", "#0b0610"]
FM_TAGS = ["fortnite", "fortnitemares", "fortnitehalloween", "halloween"]

# A bat, 40x20, for the Fortnitemares scenes.
BAT = ('<svg viewBox="0 0 40 20" width="{w}" height="{h}"><path d="M20 6 C18 2 16 1 14 3 C11 0 5 0 0 6 '
       'C5 5 8 7 9 11 C11 8 13 9 14 12 C16 10 18 11 20 15 C22 11 24 10 26 12 C27 9 29 8 31 11 C32 7 35 5 40 6 '
       'C35 0 29 0 26 3 C24 1 22 2 20 6Z" fill="rgba(8,4,12,.85)"/></svg>')


def _spooky(t0: float) -> str:
    """Bats drifting across the top, and a low orange glow: behind everything."""
    bats = []
    for i, (y, w, dur, delay, flip) in enumerate([(560, 120, 9.0, 0, 1), (640, 80, 11.0, 2.5, -1),
                                                  (500, 64, 13.0, 5.0, 1)]):
        start = -200 if flip > 0 else W + 60
        end = W + 60 if flip > 0 else -200
        name = f"bat{int(t0 * 100)}_{i}"
        bats.append(f'<style>@keyframes {name}{{from{{transform:translate({start}px,0) scaleX({flip})}}'
                    f'50%{{transform:translate({(start + end) / 2:.0f}px,-40px) scaleX({flip})}}'
                    f'to{{transform:translate({end}px,0) scaleX({flip})}}}}</style>'
                    f'<div class="abs" style="left:0;top:{y}px;'
                    f'{style_anim(an(name, t0 + delay * .2, dur, "linear", "infinite"))}">'
                    f'<div style="{style_anim(an("wobble", t0, .35, "ease-in-out", "infinite", "alternate"))}">'
                    f'{BAT.format(w=w, h=w // 2)}</div></div>')
    glow = ('<div class="abs" style="left:0;right:0;bottom:0;height:760px;background:linear-gradient(to top,'
            'rgba(255,138,30,.28),rgba(255,138,30,0))"></div>')
    return glow + "".join(bats)


# ================================================================ Winterfest

WF_ICE = "#8BE3FF"
WF_BG = ["#0f3f75", "#040a16"]
WF_BG2 = ["#136f86", "#040a16"]
WF_TAGS = ["fortnite", "fortnitewinterfest", "winterfest", "fortnitechristmas"]


def _snow(t0: float) -> str:
    """Soft snow falling through the frame, and a cold glow low down: behind everything."""
    flakes = []
    for i in range(16):
        x = (i * 67 + 23) % 1040 + 20
        size = 6 + (i * 5) % 12
        dur = 6.0 + (i * 7) % 5
        delay = (i * .37) % dur
        name = f"snow{int(t0 * 100)}_{i}"
        flakes.append(f'<style>@keyframes {name}{{from{{transform:translate(0,-60px)}}'
                      f'to{{transform:translate({(-1) ** i * 60}px,1980px)}}}}</style>'
                      f'<div class="abs" style="left:{x}px;top:0;width:{size}px;height:{size}px;border-radius:50%;'
                      f'background:rgba(255,255,255,.85);filter:blur({size / 8:.1f}px);'
                      f'{style_anim(an(name, t0 - delay, dur, "linear", "infinite"))}"></div>')
    glow = ('<div class="abs" style="left:0;right:0;bottom:0;height:760px;background:linear-gradient(to top,'
            'rgba(139,227,255,.26),rgba(139,227,255,0))"></div>')
    return glow + "".join(flakes)


# How each seasonal series looks and talks. `era` labels an item with the event
# it comes from; `span` names a throwback's years.
SEASON_LOOKS = {
    "fortnitemares": {
        "name": "Fortnitemares", "bg": FM_BG, "bg2": FM_BG2, "color": FM_ORANGE, "deco": _spooky,
        "tags": FM_TAGS, "emoji": "🎃",
        "era": lambda it: f"FORTNITEMARES {it['fm_year']}",
        "span": lambda spec, group: f"Fortnitemares {spec['fm_span']}",
        "from": lambda span: f"from {span}, and when each first hit the Item Shop",
        "past": "every skin from a past Fortnitemares",
    },
    "winterfest": {
        "name": "Winterfest", "bg": WF_BG, "bg2": WF_BG2, "color": WF_ICE, "deco": _snow,
        "tags": WF_TAGS, "emoji": "❄️",
        "era": lambda it: f"{it['wf_event']} {it['wf_year']}".upper(),
        "span": lambda spec, group: f"{group[0]['wf_event']} {spec['fm_span']}",
        "from": lambda span: f"that first hit the Item Shop during {span}",
        "past": "every skin first sold during a past Fortnite winter event",
    },
}


def _season_theme(spec: dict, items: dict, ctx: Ctx) -> dict:
    look = SEASON_LOOKS[spec["series"]]
    series = look["name"]
    day = spec["episode"]
    of = spec.get("of", 31)
    fmt = spec["format"]
    kicker = f"{series.upper()} · DAY {day} OF {of}"
    era = look["era"]

    theme = {"bg": look["bg"], "bg2": look["bg2"], "color": look["color"], "kicker": kicker, "deco": look["deco"],
             "era": era, "when": _when, "debut": _debut, "fact": lambda it: f"{it['name']} · {era(it)}".upper(),
             "sub": "PAUSE AND GUESS", "stick": f"{series.upper()} EDITION"}
    if fmt == "throwback":
        group = [items[i] for i in spec["items"]]
        theme["title"] = look["span"](spec, group).upper()
        theme["sub"] = "HOW MANY DO YOU REMEMBER?"
        theme["stick"] = f"PART {spec['part']}" if spec.get("part") else "THROWBACK"
    elif fmt == "which_first":
        theme["sub"] = "WHICH CAME OUT FIRST: A OR B?"

    def video(kind: str, comp, n: int, group: list, answers: str = ""):
        tail = f"Day {day} of {of}"
        tags_base = look["tags"]
        if kind == "throwback":
            span = look["span"](spec, group)
            part = f", Part {spec['part']}" if spec.get("part") else ""
            title = f"{span} Throwback{part} — {tail}"
            yt = f"{span} Throwback{part}: Remember These? #shorts"
            hook = (f"{look['emoji']} {span.upper()} THROWBACK{part.upper()} — Day {day} of {of}\n"
                    f"{n} cosmetics {look['from'](span)}. How many do you remember? 👇")
            body = "\n".join(f"{num(k)} {it['name']} · {it['type']} · {_debut(it).capitalize()}"
                             for k, it in enumerate(group, 1))
            ask = "Which one did you own? Tell us below"
            tags = _tags(tags_base, "ogfortnite", "fortnitethrowback")
        elif kind == "which_first":
            title = f"Which Came First? {series} Edition — {tail}"
            yt = f"Which {series} Skin Came First? Day {day} #shorts"
            hook = (f"⏳ WHICH CAME FIRST? {series} Edition — Day {day} of {of}\n"
                    f"{n} rounds, {look['past']}. Which one hit the shop first, A or B? 👇")
            body = "\n".join(f"{num(k)} {group[2 * k - 2]['name']} 🆚 {group[2 * k - 1]['name']}"
                             for k in range(1, n + 1))
            example = next(e[:n] for e in ("ABBAB", "BABBA", "AABAB") if e[:n] != answers)
            ask = f"Comment your answers in order, like {example}"
            tags = _tags(tags_base, "whichcamefirst", "fortnitequiz")
        else:
            name = {"whos_that": "Who's That Skin?", "zoomed_in": "Zoomed In",
                    "which_year": f"Which {series}?"}[kind]
            emoji = {"whos_that": "👤", "zoomed_in": "🔍", "which_year": look["emoji"]}[kind]
            ed = " Halloween Quiz" if kind == "which_year" else f" {series} Edition"
            title = f"{name}{ed} — {tail}"
            yt = {"whos_that": f"Who's That {series} Skin? Day {day} #shorts",
                  "zoomed_in": f"Zoomed In: Guess the {series} Skin, Day {day} #shorts",
                  "which_year": f"Which {series} Was It From? Day {day} #shorts"}[kind]
            what = {"whos_that": f"{n} silhouettes, 4 names each. Pause and guess 👇",
                    "zoomed_in": "We start up close. Name the skin before the camera pulls back 👇",
                    "which_year": f"{n} skins from past {series}. Which year's is each one from? 👇"}[kind]
            hook = f"{emoji} {name.upper()}{ed} — Day {day} of {of}\n{what}"
            body = f"{n} rounds · 4 choices each · no spoilers here, answers are in the video 🎥"
            ask = f"How many did you get out of {n}? Comment your score"
            tags = _tags(tags_base, "fortnitequiz", "guesstheskin")
        return Video(kind, comp, title=title, yt_title=yt, caption=_caption(hook, body, ask, tags),
                     hashtags=tags)

    theme["video"] = video
    return theme


def which_year(spec: dict, items: dict, ctx: Ctx, theme: dict):
    """Which Fortnitemares was it from? A skin, four years to pick from."""
    rounds = Q._usable(ctx, spec["rounds"], ("item",), items, 6)
    if len(rounds) < 5:
        return None
    n = len(rounds)
    content_end = Q.HOOK + n * Q.R1
    comp = Q._comp(content_end)
    first = [items[rd["item"]] for rd in rounds[:2]]
    _hook_scene(comp, ctx, "WHICH FORTNITEMARES?", "GUESS THE YEAR", f"{n} ROUNDS", Q.HOOK + .3, *first,
                colors=theme["bg"], kicker=theme["kicker"], kicker_color=theme["color"],
                extra=Q._deco(theme, 0))
    comp.cue(.2, "airhorn"); comp.cue(.9, "pop")
    for k, rd in enumerate(rounds, 1):
        it = items[rd["item"]]
        Q._picture_round(comp, ctx, Q.HOOK + (k - 1) * Q.R1, k, n, it, "WHICH FORTNITEMARES?", rd["options"],
                         rd["answer"], theme=theme,
                         reveal_fact=f"{it['name']} · {_debut(it)}".upper())
    Q._outro(comp, ctx, content_end, f"HOW MANY DID YOU GET OUT OF {n}?", [items[rd["item"]] for rd in rounds])
    return theme["video"]("which_year", comp, n, [items[rd["item"]] for rd in rounds])


def seasonal(spec: dict, items: dict, ctx: Ctx):
    """A Fortnitemares or Winterfest video: a throwback or a series edition of a quiz."""
    theme = _season_theme(spec, items, ctx)
    fmt = spec["format"]
    if fmt == "which_year":
        return which_year(spec, items, ctx, theme)
    if fmt in ("whos_that", "zoomed_in"):
        return Q._name_quiz(spec, items, ctx, fmt, theme)
    if fmt == "which_first":
        return Q.which_first(spec, items, ctx, theme)
    if fmt == "throwback":
        return Q.throwback(spec, items, ctx, theme)
    raise ValueError(f"no {spec['series']} {fmt}")


# ========================================================= Build Your Loadout

R_LO = 10.4
T_LO_CD = 2.6
LO_KINDS = {"outfit": ("OUTFIT", "PICK YOUR OUTFIT"), "backpack": ("BACK BLING", "PICK YOUR BACK BLING"),
            "pickaxe": ("PICKAXE", "PICK YOUR PICKAXE"), "glider": ("GLIDER", "PICK YOUR GLIDER"),
            "emote": ("EMOTE", "PICK YOUR EMOTE")}
LO_TAGS = ["fortnite", "fortniteskins", "fortniteloadout", "fortnitecombos"]
CARD_X, CARD_Y, CARD_W, CARD_H = (50, 385, 720), 420, 310, 450


def _card(it: dict, art: str, x: float, j: int, t0: float) -> str:
    col = RARITY.get(it["rarity"], "#3a3a44")
    fs = min(30, 280 / max(len(it["name"]) * .56, 1))
    return (f'<div class="abs" style="left:{x}px;top:{CARD_Y}px;width:{CARD_W}px;height:{CARD_H}px;'
            f'{style_anim(an("pop", t0 + .15 + j * .12, .5))}">'
            f'<div class="abs" style="inset:0;border-radius:24px;overflow:hidden;background:radial-gradient('
            f'circle at 50% 36%,{col},#101014 88%);border:4px solid rgba(255,255,255,.22)">'
            f'<img src="{art}" style="position:absolute;left:6%;top:5%;width:88%;height:72%;object-fit:contain;'
            f'filter:drop-shadow(0 16px 20px rgba(0,0,0,.5))">'
            f'<div class="abs" style="left:0;right:0;bottom:0;height:92px;padding:0 12px;background:rgba(10,10,11,.84);'
            f'display:flex;align-items:center;justify-content:center;text-align:center;font-size:{fs:.0f}px;'
            f'font-weight:800;line-height:1.1;color:#fff">{esc(it["name"])}</div></div>'
            f'<div class="abs d" style="left:12px;top:12px;width:66px;height:66px;border-radius:14px;'
            f'background:{INK};border:3px solid {ACCENT};color:{ACCENT};font-size:44px;display:flex;'
            f'align-items:center;justify-content:center">{"ABC"[j]}</div></div>')


def _locker(k: int, t0: float) -> str:
    """The five locker slots, this round's lit."""
    out = []
    for j, kind in enumerate(LO_KINDS):
        cur, done = j == k, j < k
        bg = ACCENT if cur else ("rgba(255,255,255,.88)" if done else "rgba(10,10,11,.72)")
        fg = INK if cur or done else "rgba(255,255,255,.55)"
        out.append(f'<div class="abs" style="left:{60 + j * 170}px;top:0;width:158px;height:74px;border-radius:14px;'
                   f'background:{bg};color:{fg};font-size:20px;font-weight:900;letter-spacing:.08em;display:flex;'
                   f'align-items:center;justify-content:center;text-align:center;line-height:1.05">'
                   f'{LO_KINDS[kind][0]}</div>')
    return f'<div class="abs" style="left:0;top:1360px;width:{W}px">{"".join(out)}</div>'


def loadout(spec: dict, items: dict, ctx: Ctx):
    rounds = []
    for rd in spec["rounds"]:
        got = [items[i] for i in rd["items"] if ctx.art(items[i])][:3]
        if len(got) < 3:
            return None
        rounds.append((rd["kind"], got))
    n = len(rounds)
    content_end = Q.HOOK + n * R_LO
    comp = Q._comp(content_end)
    ep = spec["episode"]
    outfits = rounds[0][1]
    _hook_scene(comp, ctx, "BUILD YOUR LOADOUT", "PICK 1 OF 3 IN EVERY ROUND", f"{n} ROUNDS", Q.HOOK + .3,
                outfits[0], outfits[1], kicker=f"FORTNITE GAME #{ep}")
    comp.cue(.2, "airhorn"); comp.cue(.9, "pop")
    for k, (kind, three) in enumerate(rounds):
        t0 = Q.HOOK + k * R_LO
        inner = tile_bg(["#1f2533", "#08090c"], "", t0)
        q = LO_KINDS[kind][1]
        inner += words(q, W / 2, 290, min(88, 900 / anton_em(q)), t0 + .1, "#fff", .06, "slam", "center", 1000)
        for j, (it, x) in enumerate(zip(three, CARD_X)):
            inner += _card(it, ctx.art(it), x, j, t0)
        inner += countdown(5, W / 2, 1080, 200, t0 + T_LO_CD, "PICK A, B OR C")
        inner += sticker("LOCK IT IN!", 560, 1268, 54, t0 + T_LO_CD + 5.1, rot=-4)
        inner += _locker(k, t0)
        inner += progress(t0, t0 + R_LO, k + 1, n)
        comp.scene(t0, t0 + R_LO, inner, fade_in=.25, fade_out=.25)
        comp.cue(t0 + .1, "whoosh")
        for j in range(3):
            comp.cue(t0 + .15 + j * .12, "pop")
        for s in range(3):
            comp.cue(t0 + T_LO_CD + 2 + s, "tick")
        comp.cue(t0 + T_LO_CD + 5.1, "slam")

    r = random.Random(ctx.seed * 13 + ep)
    example = "".join(r.choice("ABC") for _ in range(n))
    Q._outro(comp, ctx, content_end, f"COMMENT YOUR LOADOUT: {example}", outfits)
    body = "\n".join(f"{num(k)} {LO_KINDS[kind][0].title()}: " + " · ".join(f"{'ABC'[j]} {it['name']}"
                                                                           for j, it in enumerate(three))
                     for k, (kind, three) in enumerate(rounds, 1))
    tags = _tags(LO_TAGS, "buildyourloadout", "fortnitegame")
    return Video("loadout", comp, title=f"Build Your Loadout — Fortnite Game #{ep}",
                 yt_title=f"Build Your Fortnite Loadout: Pick 1 of 3, Game #{ep} #shorts",
                 caption=_caption(f"🎒 BUILD YOUR LOADOUT — Fortnite Game #{ep}\n"
                                  f"One pick per round: outfit, back bling, pickaxe, glider, emote 👇",
                                  body, f"Comment your loadout in order, like {example}", tags),
                 hashtags=tags)


# ================================================================== dispatch

BUILDERS = {"on_this_day": on_this_day, "loadout": loadout}


def build(spec: dict, items: dict, ctx: Ctx):
    if spec.get("series") in SEASON_LOOKS:
        return seasonal(spec, items, ctx)
    return BUILDERS[spec["format"]](spec, items, ctx)
