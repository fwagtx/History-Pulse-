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
USE CODE: BAD stamp, the corner badge and #EpicPartner stay up the whole way,
and the USE CREATOR CODE BAD outro closes it.

Truth rules: every date and "first time in the shop" comes from the item's shop
history, every Fortnitemares year from the Fortnite Wiki's lists checked against
that history (see cc_series_plan). Nothing else is claimed.
"""

import random

import cc_looks as LK
import cc_quiz as Q
from cc_series_plan import FAMOUS_SERIES, FIRST_SURE
from cc_formats import BRAND_TAGS, Ctx, Video, num, _caption, _hook_scene, _tag
from cc_motion import (ACCENT, INK, RARITY, W, SAFE_LEFT, SAFE_RIGHT_TOP, SAFE_RIGHT, an, anton_em,
                       burst, character, countdown, esc, label, progress, sticker, style_anim, tile_bg, words)

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


def _debut_words(it: dict) -> str:
    """The same for a description: 'Shop debut Oct 26, 2018', 'In the shop in 2017'."""
    first = it.get("first_shop") or ""
    if first >= FIRST_SURE:
        y, m, d = (int(x) for x in first.split("-"))
        return f"Shop debut {MONTHS[m - 1].title()} {d}, {y}"
    return f"In the shop in {first[:4]}"


# ================================================================ On This Day

R_OTD = 6.5
OTD_TAGS = ["fortnite", "fortniteitemshop", "fortniteskins", "onthisday"]

# The classic scenes, composed for the apps' safe box (cc_safe): the date and
# "N YEARS AGO TODAY" in the wide band under the code badge, the cosmetic, its
# name and the timeline of years in the column beside the button rail (x 60-900,
# centred on MID), the timeline's pills ending above the caption zone at y 1420.
MID = (SAFE_LEFT + SAFE_RIGHT) / 2                      # 480
COL_W = SAFE_RIGHT - SAFE_LEFT                          # 840
OTD_DATE_Y, OTD_HEAD_Y = 366, 420                       # under #EpicPartner (y 320-350)
OTD_ART_CY, OTD_ART_H = 826, 580                        # the cosmetic: y 536-1116
OTD_NAME_Y = 1146
OTD_TL_Y, OTD_TL_H = 1330, 60                           # the timeline: y 1330-1390


def _timeline(years: list, k: int, t0: float) -> str:
    """The years along the bottom, this one lit, the ones before it ticked off."""
    step = (COL_W + 10) / len(years)
    size = min(32, (step - 22) / (anton_em("2020") - .18))
    pills = []
    for j, y in enumerate(years):
        cur, past = j == k, j < k
        bg = ACCENT if cur else ("rgba(255,255,255,.9)" if past else "rgba(10,10,11,.72)")
        fg = INK if cur or past else "rgba(255,255,255,.6)"
        pop = style_anim(an("pop", t0 + .2, .45)) if cur else ""
        edge = "box-shadow:0 6px 0 rgba(0,0,0,.35);" if cur else "border:2px solid rgba(255,255,255,.14);"
        pills.append(f'<div class="abs d" style="left:{j * step:.0f}px;top:0;width:{step - 10:.0f}px;'
                     f'height:{OTD_TL_H}px;border-radius:12px;background:{bg};color:{fg};font-size:{size:.0f}px;'
                     f'display:flex;align-items:center;justify-content:center;{edge}{pop}">{y}</div>')
    return (f'<div class="abs" style="left:{SAFE_LEFT}px;top:{OTD_TL_Y}px;width:{COL_W}px;height:{OTD_TL_H}px">'
            f'{"".join(pills)}</div>')


def _comp(content_end: float):
    """cc_quiz's Comp, with cc_looks.PREP_JS in the page: it crops every
    img[data-trim] to the cosmetic before the first frame. Fortnite's art is a
    square with wide transparent margins; cropped, a size means the cosmetic."""
    comp = Q._comp(content_end)
    if LK.PREP_JS not in comp._layers:
        comp.add(LK.PREP_JS)
    return comp


def _trim(html: str) -> str:
    """character()'s art, marked to be cropped to the cosmetic (see _comp)."""
    return html.replace('<img class="art" ', '<img class="art" data-trim ', 1)


def _years_ago(n: int) -> str:
    return "1 YEAR AGO TODAY" if n == 1 else f"{n} YEARS AGO TODAY"


def _otd_top(date: str, ago: str, t0: float) -> str:
    """The date, then N YEARS AGO TODAY, centred on the column."""
    size = min(96, (COL_W - 20) / anton_em(ago))
    return (label(date, MID, OTD_DATE_Y, 34, t0, ACCENT, 800, anim="none", align="center", spacing=".14em")
            + words(ago, MID, OTD_HEAD_Y + (96 - size) * .5, size, t0 + .15, "#fff", .06, "slam", "center"))


def _big_year(year, t0: float) -> str:
    """The year, huge and faint, behind the cosmetic (inside the column too)."""
    return (f'<div class="abs d" style="left:{MID - W:.0f}px;width:{2 * W}px;top:590px;text-align:center;'
            f'font-size:380px;color:rgba(255,255,255,.1);letter-spacing:.02em;{style_anim(an("punch", t0, .6))}">'
            f'{year}</div>')


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
    # The thumbnail: the two strongest picks, first times in the shop first.
    lead = sorted(rounds, key=lambda r: (not r[2], r[1]["rarity"] != "legendary"
                                         and r[1]["series"] not in FAMOUS_SERIES, -r[0]["year"]))[:2]
    span = f"{years[0]}–{years[-1]}"
    # The two thumbnail picks, and the newest one that isn't already among them.
    third = next((r[1] for r in reversed(rounds) if all(r[1] is not x[1] for x in lead)), None)
    look = LK.get("on_this_day")
    comp = LK.draw(look, "on_this_day", ctx, rounds, bday, lead, third)
    if comp is None:
        content_end = Q.HOOK + n * R_OTD
        comp = _comp(content_end)
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
            inner += _otd_top(f"{when.upper()}, {bday['year']}", _years_ago(bday["age"]), t0)
            for i, line in enumerate(("FORTNITE", "BATTLE ROYALE", "COMES OUT")):
                inner += words(line, MID, 574 + i * 122, 120, t0 + .5 + i * .15, "#fff", .06, "slam", "center")
            inner += label("PC · PLAYSTATION 4 · XBOX ONE", MID, 978, 36, t0 + 1.2, ACCENT, 800, align="center",
                           bg="rgba(10,10,11,.8)", pad="12px 26px", spacing=".04em")
            cake = "HAPPY BIRTHDAY!"
            inner += sticker(cake, MID - (anton_em(cake) + .84) * 72 / 2, 1134, 72, t0 + 1.6, rot=-4)
            inner += burst(MID, 780, t0 + .6, ctx.seed)
            inner += _timeline(years, 0, t0)
            comp.scene(t0, t0 + R_OTD, inner, fade_in=.25, fade_out=.25)
            comp.cue(t0 + .15, "slam"); comp.cue(t0 + .6, "reveal"); comp.cue(t0 + 1.6, "clap")
            k = 1

        for j, (rd, it, debut) in enumerate(rounds):
            t0 = Q.HOOK + (k + j) * R_OTD
            y = rd["year"]
            inner = tile_bg(Q._colors(it), it["rarity"], t0)
            inner += _big_year(y, t0)
            inner += _otd_top(f"{when.upper()}, {y}", _years_ago(day.year - y), t0)
            inner += _trim(character(ctx.art(it), MID, OTD_ART_CY, OTD_ART_H, t0 + .1, "pop", .6, "float",
                                     it["rarity"], it["name"], maxw=COL_W - 40))
            # The name on one line, as big as fits the column (a 30-letter name
            # comes down to about 55 px), and what that day was under it.
            size = min(92, (COL_W - 20) / max(anton_em(it["name"]), .1))
            inner += words(it["name"], MID, OTD_NAME_Y + (92 - size) * .5, size, t0 + .45, "#fff", .06, "slam",
                           "center")
            line = "FIRST TIME IN THE ITEM SHOP" if debut else "IN THE ITEM SHOP THAT DAY"
            inner += label(line, MID, OTD_NAME_Y + 110, 36, t0 + .7, ACCENT if debut else "#fff", 800,
                           align="center", spacing=".05em")
            if debut:
                # Up in the wide band, right of where a cosmetic's head is.
                new = "NEW THAT DAY!"
                inner += sticker(new, SAFE_RIGHT_TOP - 26 - (anton_em(new) + .84) * 50, 566, 50, t0 + .9, rot=6)
            inner += _timeline(years, k + j, t0)
            comp.scene(t0, t0 + R_OTD, inner, fade_in=.25, fade_out=.25)
            comp.cue(t0 + .1, "whoosh"); comp.cue(t0 + .15, "slam"); comp.cue(t0 + .45, "pop")
            if debut:
                comp.cue(t0 + .9, "ding")

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
    """Bats flitting across the frame, rim-lit orange so they read on the dark
    purple, and a low orange glow. Every scene draws it straight over its
    background (cc_formats._hook_scene's `extra`, cc_quiz._deco), so it stays
    behind the words and the cosmetics; it carries no text or image for the
    safe-box check to hold. At a scene's first frame (the thumbnail too) two
    bats are just coming in at the frame's edges, clear of the words; the third
    follows."""
    bats = []
    # (y, width, seconds to cross, share of the crossing done at t0, direction)
    for i, (y, w, dur, ahead, flip) in enumerate([(560, 120, 9.0, .1, 1), (610, 80, 11.0, .08, -1),
                                                  (500, 64, 13.0, 0, 1)]):
        start = -200 if flip > 0 else W + 60
        end = W + 60 if flip > 0 else -200
        name = f"bat{int(t0 * 100)}_{i}"
        bats.append(f'<style>@keyframes {name}{{from{{transform:translate({start}px,0) scaleX({flip})}}'
                    f'50%{{transform:translate({(start + end) / 2:.0f}px,-40px) scaleX({flip})}}'
                    f'to{{transform:translate({end}px,0) scaleX({flip})}}}}</style>'
                    f'<div class="abs" style="left:0;top:{y}px;'
                    f'{style_anim(an(name, t0 - ahead * dur, dur, "linear", "infinite"))}">'
                    f'<div style="filter:drop-shadow(0 0 7px rgba(255,138,30,.55));'
                    f'{style_anim(an("wobble", t0, .35, "ease-in-out", "infinite", "alternate"))}">'
                    f'{BAT.format(w=w, h=w // 2)}</div></div>')
    glow = ('<div class="abs" style="left:0;right:0;bottom:0;height:760px;background:linear-gradient(to top,'
            'rgba(255,138,30,.28),rgba(255,138,30,0))"></div>')
    return glow + "".join(bats)


# ================================================================ Winterfest

WF_ICE = "#8BE3FF"
WF_BG = ["#0f3f75", "#040a16"]
WF_BG2 = ["#136f86", "#040a16"]
WF_TAGS = ["fortnite", "fortnitewinterfest", "winterfest", "fortnitechristmas"]


# Snow in three depths: (flakes, smallest and biggest px, opacity, blur px,
# seconds to fall 2000 px, sideways drift px). Far flakes are small, dim and
# slow; near ones big, soft and quick, so it reads as falling snow, not specks.
SNOW = [(14, 4, 6, .5, 0, 13.0, 20), (10, 8, 11, .75, .8, 9.0, 35), (5, 14, 18, .85, 2.4, 6.5, 55)]
# It falls through the top of the frame and melts away by SNOW_FADE[1]: lower
# down sit the answers and the names, which fade out on a reveal, and snow
# behind a faded answer would show through it as if it sat on the words.
SNOW_FADE = (560, 800)


def _snow(t0: float) -> str:
    """Snow falling through the top of the frame, and a cold glow low down.
    Like the bats, every scene draws it straight over its background, so it
    stays behind the words and the cosmetics, and it carries nothing for the
    safe-box check to hold. Deterministic: the same flakes in every render."""
    flakes, i = [], 0
    drop = SNOW_FADE[1] + 60                              # from y -60 to where it has melted away
    for count, small, big, alpha, blur, fall, drift in SNOW:
        for j in range(count):
            x = (i * 157 + 41) % 1060 + 10
            size = small + (j * 3) % (big - small + 1)
            dur = fall * (1 + (j * 5) % 7 / 20) * drop / 2000
            ahead = (i * .618) % 1 * dur                  # already falling at the first frame
            side = drift if i % 2 else -drift
            name = f"snow{int(t0 * 100)}_{i}"
            flakes.append(f'<style>@keyframes {name}{{from{{transform:translate(0,-60px)}}'
                          f'to{{transform:translate({side}px,{SNOW_FADE[1]}px)}}}}</style>'
                          f'<div class="abs" style="left:{x}px;top:0;width:{size}px;height:{size}px;'
                          f'border-radius:50%;background:rgba(255,255,255,{alpha});'
                          f'{f"filter:blur({blur}px);" if blur else ""}'
                          f'{style_anim(an(name, t0 - ahead, dur, "linear", "infinite"))}"></div>')
            i += 1
    fade = f"linear-gradient(#000 {SNOW_FADE[0]}px,transparent {SNOW_FADE[1]}px)"
    glow = ('<div class="abs" style="left:0;right:0;bottom:0;height:760px;background:linear-gradient(to top,'
            'rgba(139,227,255,.26),rgba(139,227,255,0))"></div>')
    return (glow + f'<div class="full" style="-webkit-mask-image:{fade};mask-image:{fade}">'
            + "".join(flakes) + "</div>")


FACT_MIN = 34            # px: an answer line smaller than this drops the name (see _fact_line)


def _fact_line(it: dict, tail: str) -> str:
    """The line that lands with an answer, "NAME · TAIL" (TAIL: the event it is
    from, or its shop debut). cc_quiz._fact shrinks the line to fit the band
    beside the apps' button rail, so for a name so long that the line would go
    under FACT_MIN px, TAIL goes alone: the name is on screen anyway, in the lit
    answer or on the line before the reveal."""
    full = f"{it['name']} · {tail}".upper()
    return full if anton_em(full) + .9 <= (COL_W - 40) / FACT_MIN else tail.upper()


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
             "era": era, "when": _when, "debut": _debut, "fact": lambda it: _fact_line(it, era(it)),
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
            body = "\n".join(f"{num(k)} {it['name']} · {it['type']} · {_debut_words(it)}"
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
            if not name.endswith("?"):
                name += ":"                 # "Zoomed In: Fortnitemares Edition"
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
    comp = _comp(content_end)
    first = [items[rd["item"]] for rd in rounds[:2]]
    _hook_scene(comp, ctx, "WHICH FORTNITEMARES?", "GUESS THE YEAR", f"{n} ROUNDS", Q.HOOK + .3, *first,
                colors=theme["bg"], kicker=theme["kicker"], kicker_color=theme["color"],
                extra=Q._deco(theme, 0))
    comp.cue(.2, "airhorn"); comp.cue(.9, "pop")
    for k, rd in enumerate(rounds, 1):
        it = items[rd["item"]]
        Q._picture_round(comp, ctx, Q.HOOK + (k - 1) * Q.R1, k, n, it, "WHICH FORTNITEMARES?", rd["options"],
                         rd["answer"], theme=theme, reveal_fact=_fact_line(it, _debut(it)))
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

# A round, in the apps' safe box (cc_safe): the question in the wide band under
# the code badge, then everything in the column beside the button rail (x 60-900,
# centred on MID): the three cards side by side, the ring, and the five locker
# slots ending above the caption zone at y 1420.
LO_Q_Y = 368
CARD_W, CARD_GAP = 266, 21
CARD_X = tuple(SAFE_LEFT + j * (CARD_W + CARD_GAP) for j in range(3))     # 60, 347, 634: right edge 900
CARD_Y, CARD_H = 470, 560                                                   # y 470-1030
LO_RING_Y, LO_RING = 1138, 150                                              # ring y 1063-1213, caption to ~1271
LOCKER_Y, LOCKER_H, LOCKER_GAP = 1318, 76, 10                               # y 1318-1394
NAME_BIG, NAME_PAD = 50, 14
NAME_W = CARD_W - 8 - 2 * NAME_PAD                  # inside the card's border and the plate's padding


def _cuts(ws: list, n: int):
    """Every way to break the words `ws` into n lines."""
    if n == 1:
        yield [" ".join(ws)]
        return
    for i in range(1, len(ws) - n + 2):
        for rest in _cuts(ws[i:], n - 1):
            yield [" ".join(ws[:i])] + rest


def _fit_name(name: str, width: float = NAME_W) -> tuple:
    """(font size, lines) for a card's name in Anton caps: one, two or three
    evenly broken lines, whichever sets it biggest (up to NAME_BIG), taking
    fewer lines when that costs less than 15% of the size. "BLACK ADAM" stays
    on one line at 46 px, "DOPAMINE BLADES" takes two at 50, a 37-letter name
    three at about 34."""
    ws = name.upper().split() or [""]
    fits = []
    for n in range(1, min(3, len(ws)) + 1):
        lines = min(_cuts(ws, n), key=lambda ls: max(anton_em(s) for s in ls))
        fits.append((min(NAME_BIG, width / max(max(anton_em(s) for s in lines), .1)), lines))
    best = max(s for s, _ in fits)
    size, lines = next(f for f in fits if f[0] >= best * .85)
    return int(size), lines


def _card(it: dict, art: str, x: float, j: int, t0: float, fit: tuple, plate: int) -> str:
    """A choice: the cosmetic on its rarity colour, its letter, and its name
    (`fit` from _fit_name) on a plate `plate` px tall across the bottom."""
    col = RARITY.get(it["rarity"], "#3a3a44")
    fs, lines = fit
    name = "<br>".join(esc(s) for s in lines)
    pic = (f'<img data-trim src="{art}" data-name="{esc(it["name"])}" style="position:absolute;left:5%;top:18px;'
           f'width:90%;height:{CARD_H - plate - 30}px;object-fit:contain;'
           f'filter:drop-shadow(0 16px 20px rgba(0,0,0,.5))">' if art else "")
    return (f'<div class="abs" style="left:{x}px;top:{CARD_Y}px;width:{CARD_W}px;height:{CARD_H}px;'
            f'{style_anim(an("pop", t0 + .15 + j * .12, .5))}">'
            f'<div class="abs" style="inset:0;border-radius:24px;overflow:hidden;background:radial-gradient('
            f'circle at 50% 38%,{col},#101014 88%);border:4px solid rgba(255,255,255,.22)">{pic}'
            f'<div class="abs d" style="left:0;right:0;bottom:0;height:{plate}px;padding:0 {NAME_PAD}px;'
            f'background:rgba(10,10,11,.86);display:flex;align-items:center;justify-content:center;'
            f'text-align:center;font-size:{fs}px;line-height:.98;white-space:nowrap;color:#fff">{name}</div></div>'
            f'<div class="abs d" style="left:12px;top:12px;width:66px;height:66px;border-radius:14px;'
            f'background:{INK};border:3px solid {ACCENT};color:{ACCENT};font-size:44px;display:flex;'
            f'align-items:center;justify-content:center">{"ABC"[j]}</div></div>')


def _locker(kinds: list, k: int, t0: float) -> str:
    """The video's locker slots (outfit to emote), this round's lit, the ones
    before it filled: tabs across the column, each as wide as its word plus an
    equal share of the rest."""
    names = [LO_KINDS[kind][0] for kind in kinds]
    size = 32
    text = [anton_em(s) * size for s in names]
    extra = (COL_W - (len(names) - 1) * LOCKER_GAP - sum(text)) / len(names)
    out, x = [], 0.0
    for j, word in enumerate(names):
        cur, done = j == k, j < k
        w = text[j] + extra
        bg = ACCENT if cur else ("rgba(255,255,255,.88)" if done else "rgba(10,10,11,.72)")
        fg = INK if cur or done else "rgba(255,255,255,.6)"
        pop = style_anim(an("pop", t0 + .25, .45)) if cur else ""
        edge = "box-shadow:0 6px 0 rgba(0,0,0,.35);" if cur else "border:2px solid rgba(255,255,255,.14);"
        out.append(f'<div class="abs d" style="left:{x:.1f}px;top:0;width:{w:.1f}px;height:{LOCKER_H}px;'
                   f'border-radius:14px;background:{bg};color:{fg};font-size:{size}px;display:flex;'
                   f'align-items:center;justify-content:center;{edge}{pop}">{word}</div>')
        x += w + LOCKER_GAP
    return (f'<div class="abs" style="left:{SAFE_LEFT}px;top:{LOCKER_Y}px;width:{COL_W}px;height:{LOCKER_H}px">'
            f'{"".join(out)}</div>')


def loadout(spec: dict, items: dict, ctx: Ctx):
    rounds = []
    for rd in spec["rounds"]:
        got = [items[i] for i in rd["items"] if ctx.art(items[i])][:3]
        if len(got) < 3:
            return None
        rounds.append((rd["kind"], got))
    n = len(rounds)
    content_end = Q.HOOK + n * R_LO
    comp = _comp(content_end)
    ep = spec["episode"]
    outfits = rounds[0][1]
    _hook_scene(comp, ctx, "BUILD YOUR LOADOUT", "PICK 1 OF 3 IN EVERY ROUND", f"{n} ROUNDS", Q.HOOK + .3,
                outfits[0], outfits[1], kicker=f"FORTNITE GAME #{ep}")
    comp.cue(.2, "airhorn"); comp.cue(.9, "pop")
    for k, (kind, three) in enumerate(rounds):
        t0 = Q.HOOK + k * R_LO
        inner = tile_bg(["#1f2533", "#08090c"], "", t0)
        q = LO_KINDS[kind][1]
        size = min(84, (COL_W - 20) / anton_em(q))
        inner += words(q, MID, LO_Q_Y + (84 - size) * .5, size, t0 + .1, "#fff", .06, "slam", "center")
        # One plate height for the round's three cards, so the art and names line up.
        fits = [_fit_name(it["name"]) for it in three]
        plate = max(96, max(round(len(ls) * fs * .98 + 30) for fs, ls in fits))
        for j, (it, x, fit) in enumerate(zip(three, CARD_X, fits)):
            inner += _card(it, ctx.art(it), x, j, t0, fit, plate)
        inner += countdown(5, MID, LO_RING_Y, LO_RING, t0 + T_LO_CD, "PICK A, B OR C")
        # When the ring runs out: beside it, clear of the cards and the caption.
        lock = "LOCK IT IN!"
        inner += sticker(lock, SAFE_RIGHT - 30 - (anton_em(lock) + .84) * 50, LO_RING_Y - 40, 50,
                         t0 + T_LO_CD + 5.1, rot=-4)
        inner += _locker([kd for kd, _ in rounds], k, t0)
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
