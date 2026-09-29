"""
QUIZ NIGHT -- the Saturday long video (cc_long_v2): 40 levels, easy to
impossible, five seconds each, then the answer.

    whos_that     the skin as a black silhouette; four names; the reveal
                  brings the skin in full colour
    zoomed_in     a close-up of the skin's face; four names; the reveal zooms
                  out to the whole skin
    which_first   two skins side by side, A or B: which came out first (Epic's
                  own season data); the reveal stamps it and says both seasons
    guess_season  the skin and its name; four seasons; one is when it came out
    ...           and on the Saturday before Halloween, whos_that with only
                  Fortnitemares skins

Four tiers of ten (EASY, MEDIUM, HARD, IMPOSSIBLE). How hard a level is comes
from the records: a skin that's been in the Item Shop many times, or lately,
or is from a big collab is one more people know (easy); one that's been in
the shop a handful of times, long ago, is hard. which_first pairs get closer
in time as the tiers go up (ten seasons apart ... one); guess_season's wrong
answers get closer to the right one. A week's picks come from a fixed shuffle
of each tier, moved on every time that quiz comes round, so a skin isn't asked
again until the tier has been used up.

Frame (cc_safe.LONG): the header row (LEVEL n, the tier, the timer) at y
104-216, the question under it, the picture on the left from x 360 (the code
sticker keeps x 96-310, y 96-260), the choices on the right to x 1780,
everything above the subtitles (y 846).
"""

import random
import re
from datetime import date

import cc_edit as ED
import cc_edit_long as LE
import cc_long_series as SER
import cc_rarity as R
from cc_long_series import _entry, _intro_text, _raw_kind, _raw_value, cta_screen
from cc_motion import esc, trim_for

W, H = LE.W, LE.H
LEVELS_PER_TIER = 10
TIMER = 5
TIERS = [("easy", "EASY", "#5BC44A"), ("medium", "MEDIUM", "#F5C518"), ("hard", "HARD", "#EE8B3D"),
         ("impossible", "IMPOSSIBLE", "#FF3B30")]
CUTS = [0, .06, .20, .45, .80]              # the tiers, as shares of the skins ranked by how known they are
SMALL_CUTS = [0, .15, .35, .60, 1.0]        # a small pool (a seasonal edition)
FAMOUS = {"Icon Series", "MARVEL SERIES", "DC SERIES", "Star Wars Series", "Gaming Legends Series"}
CODE_NAME = re.compile(r"[A-Za-z]+(?:_[A-Za-z0-9]+)+")
BAD_NAMES = {"tbd", "null", "npc", "random", ""}
SEASON_GAP = {"which_first": [(10, 99), (5, 9), (2, 4), (1, 2)],      # seasons between the pair, per tier
              "guess_season": [(6, 99), (3, 99), (2, 99), (1, 99)]}    # the closest wrong season, per tier
ZOOM = [2.2, 2.8, 3.4, 4.0]
SIL = "filter:brightness(0) drop-shadow(0 0 3px #E8FF3A) drop-shadow(0 0 22px rgba(232,255,58,.7))"

FORMATS = {
    "whos_that": {"title": "Guess the Fortnite Skin by Its Silhouette: 40 Levels, Easy to IMPOSSIBLE",
                  "q": "who's that skin?", "head": "guess the\nskin", "sub": "40 levels · easy to impossible",
                  "how": "Every level, a skin's silhouette and four names. You get five seconds.",
                  "tags": ["guess the fortnite skin", "fortnite silhouette quiz", "fortnite skin quiz"]},
    "zoomed_in": {"title": "Zoomed In: Guess the Fortnite Skin (40 Levels, Easy to IMPOSSIBLE)",
                  "q": "who's this, up close?", "head": "zoomed\nin", "sub": "40 levels · easy to impossible",
                  "how": "Every level, we zoom right in on a skin. Four names, five seconds.",
                  "tags": ["guess the fortnite skin", "fortnite zoomed in quiz", "fortnite skin quiz"]},
    "which_first": {"title": "Which Fortnite Skin Came First? 40 Levels, Easy to IMPOSSIBLE",
                    "q": "which came out first?", "head": "which came\nfirst?", "sub": "40 levels · easy to impossible",
                    "how": "Every level, two skins. Which one came out first, A or B? Five seconds.",
                    "tags": ["which fortnite skin came first", "fortnite quiz", "og fortnite skins"]},
    "guess_season": {"title": "Guess the Season: 40 Fortnite Skins, Easy to IMPOSSIBLE",
                     "q": "which season is it from?", "head": "guess the\nseason", "sub": "40 levels · easy to impossible",
                     "how": "Every level, a skin and four seasons. Which one did it come out in? Five seconds.",
                     "tags": ["guess the fortnite season", "fortnite season quiz", "fortnite quiz"]},
}
HALLOWEEN = {"title": "Guess the Fortnitemares Skin by Its Silhouette: 40 Halloween Levels, Easy to IMPOSSIBLE",
             "head": "fortnitemares\nquiz", "sub": "40 halloween levels · easy to impossible"}

CSS = """
.qc{position:absolute;display:flex;align-items:center;background:rgba(10,10,11,.8);
  border:4px solid rgba(255,255,255,.22);border-radius:22px;padding:0 22px;box-sizing:border-box;
  font-family:'TikTok Sans','Noto Color Emoji',sans-serif;font-weight:800;color:#fff;white-space:nowrap;z-index:41}
.qc-l{flex:none;width:62px;height:62px;border-radius:14px;background:#fff;color:#0A0A0B;display:flex;
  align-items:center;justify-content:center;font:900 40px/1 'TikTok Sans',sans-serif;margin-right:22px}
.qc.ok{background:#E8FF3A;color:#0A0A0B;border-color:#000}
.qc.ok .qc-l{background:#0A0A0B;color:#E8FF3A}
.qdim{position:absolute;border-radius:22px;background:rgba(0,0,0,.6);z-index:42}
.qchip{position:absolute;font:900 38px/1 'TikTok Sans',sans-serif;color:#0A0A0B;padding:10px 18px 12px;
  border-radius:14px;border:4px solid #000;white-space:nowrap;z-index:41}
@keyframes qzo{from{transform:translateX(-50%) scale(var(--z))}to{transform:translateX(-50%) scale(1)}}
"""

# layout
HEAD_Y = 104
Q_Y = 236
PIC = (360, 318, 500, 510)                   # x, y, w, h of the picture's tile
CH_X, CH_W, CH_H = 960, 820, 104
CH_Y = [322, 452, 582, 712]
TIMER_C = (1718, 160, 112)                   # the ring: centre x, centre y, size
PAIR = [(330, 318, 560, 468), (1030, 318, 560, 468)]


def _norm(name: str) -> str:
    return " ".join((name or "").lower().split())


def _anim(name: str, start: float, dur: float, fill: str = "both", ease: str = "linear") -> str:
    return f"animation:{name} {dur:.3f}s {ease} {start:.3f}s 1 normal {fill}"


# ------------------------------------------------------------------ the pool

def pool(hist: R.History, day: date, keys: set | None = None) -> list:
    """Outfits that can be asked, most known first: shop art, a proper name no
    other outfit shares, in the shop at least once by `day`."""
    names = {}
    for key, raw in hist.items.items():
        if _raw_kind(raw) == "outfit":
            names[_norm(raw.get("name"))] = names.get(_norm(raw.get("name")), 0) + 1
    out = []
    for key, days in hist.days.items():
        raw = hist.items[key]
        if _raw_kind(raw) != "outfit" or (keys is not None and key not in keys):
            continue
        name = " ".join((raw.get("name") or "").split())
        if (not name or names.get(_norm(name), 0) != 1 or CODE_NAME.fullmatch(name)
                or name.lower() in BAD_NAMES or not (raw.get("images") or {}).get("featured")):
            continue
        upto = [d for d in days if d <= day]
        if not upto:
            continue
        times = len(R._runs(upto))
        series = _raw_value(raw, "series")
        season = int((raw.get("introduction") or {}).get("backendValue") or -1)
        score = times + (20 if (day - upto[-1]).days <= 365 else 0) + (10 if series in FAMOUS else 0)
        out.append({"key": key, "name": name, "score": score, "times": times, "series": series,
                    "rarity": ((raw.get("rarity") or {}).get("value") or "").lower(), "season": season,
                    "season_text": _intro_text(raw)})
    out.sort(key=lambda c: (-c["score"], c["key"]))
    return out


def tiers(cands: list) -> list:
    cuts = CUTS if len(cands) >= 400 else SMALL_CUTS
    n = len(cands)
    return [cands[int(a * n):int(b * n)] for a, b in zip(cuts, cuts[1:])]


def _shuffled(items: list, salt: str) -> list:
    out = list(items)
    random.Random(sum(ord(c) * (i + 1) for i, c in enumerate(salt))).shuffle(out)
    return out


def _take(tier_pool: list, k: int, n: int, salt: str, ok=lambda c: True) -> list:
    """The k-th week's n picks from a tier: a fixed shuffle, moved on n a week."""
    order = _shuffled(tier_pool, salt)
    if not order:
        return []
    start = (k * n) % len(order)
    ring = order[start:] + order[:start]
    return [c for c in ring if ok(c)]


# ------------------------------------------------------------------ levels

def _choices(answer: dict, same_tier: list, rnd: random.Random) -> list:
    """Four names: the answer and three from its tier, from the same collab
    when it has one, else of its rarity."""
    alike = [c for c in same_tier if c["key"] != answer["key"] and (
        (answer["series"] and c["series"] == answer["series"]) or
        (not answer["series"] and c["rarity"] == answer["rarity"]))]
    rest = [c for c in same_tier if c["key"] != answer["key"] and c not in alike]
    rnd.shuffle(alike)
    rnd.shuffle(rest)
    picks = (alike + rest)[:3]
    names = [answer["name"]] + [c["name"] for c in picks]
    rnd.shuffle(names)
    return names


def _season_choices(answer: dict, seasons: list, lo: int, rnd: random.Random) -> list | None:
    """The answer's season and three others at least `lo` seasons away."""
    order = [v for v, _ in seasons]
    if answer["season"] not in order:
        return None
    i = order.index(answer["season"])
    far = [(abs(j - i), t) for j, (v, t) in enumerate(seasons) if abs(j - i) >= lo and v != answer["season"]]
    far.sort()
    near = [t for _, t in far[:8]]
    if len(near) < 3:
        return None
    picks = rnd.sample(near, 3)
    out = [answer["season_text"]] + picks
    rnd.shuffle(out)
    return out


def _season_list(cands: list) -> list:
    by = {}
    for c in cands:
        if c["season"] >= 0 and c["season_text"]:
            by.setdefault(c["season"], c["season_text"])
    return sorted(by.items())


def plan(fmt: str, hist: R.History, day: date, art, k: int, keys: set | None = None, salt: str = "") -> list | None:
    """The 40 levels: [{tier, n, ...}], each with art."""
    cands = pool(hist, day, keys)
    if len(cands) < 80:
        return None
    ts = tiers(cands)
    seasons = _season_list(cands)
    rnd = random.Random(f"{fmt}{salt}{k}")
    levels, used = [], set()
    for t, tier_pool in enumerate(ts):
        got = []
        for c in _take(tier_pool, k, LEVELS_PER_TIER, f"{fmt}{salt}{t}"):
            if len(got) == LEVELS_PER_TIER:
                break
            if c["key"] in used:
                continue
            e = _entry(hist, c["key"], art)
            if not e:
                continue
            lvl = {"tier": t, "a": dict(c, **e)}
            if fmt in ("whos_that", "zoomed_in"):
                lvl["choices"] = _choices(c, tier_pool, rnd)
            elif fmt == "guess_season":
                ch = _season_choices(c, seasons, SEASON_GAP[fmt][t][0], rnd)
                if not ch:
                    continue
                lvl["choices"] = ch
            elif fmt == "which_first":
                lo, hi = SEASON_GAP[fmt][t]
                if c["season"] < 0:
                    continue
                mate = None
                for d in _take(tier_pool + (ts[t + 1] if t + 1 < len(ts) else []), k + 7, 400, f"{fmt}{salt}m{t}"):
                    if (d["key"] not in used and d["key"] != c["key"] and d["season"] >= 0
                            and lo <= abs(d["season"] - c["season"]) <= hi):
                        e2 = _entry(hist, d["key"], art)
                        if e2:
                            mate = dict(d, **e2)
                            break
                if not mate:
                    continue
                pair = [lvl["a"], mate]
                rnd.shuffle(pair)
                lvl["pair"] = pair
                used.add(mate["key"])
            used.add(c["key"])
            got.append(lvl)
        if len(got) < LEVELS_PER_TIER:
            return None
        levels += got
    for i, lv in enumerate(levels):
        lv["n"] = i + 1
    return levels


# ------------------------------------------------------------------ drawing

def _css_once(lv):
    if not getattr(lv, "_quiz_css", False):
        lv.comp.css(CSS)
        lv._quiz_css = True


def _bg(t: int) -> str:
    color = TIERS[t][2]
    return (f'<div class="full" style="background:radial-gradient(ellipse 60% 70% at 32% 55%,{color}55 0%,'
            f'#121722 55%,#07080b 100%)"></div>')


def _header(lv, seg, lvl: dict, q: str) -> str:
    t = lvl["tier"]
    label = f"LEVEL {lvl['n']}"
    size = 92
    width = LE.text_em(label, 900) * size + 40
    html = ED.outline(label, 360, HEAD_Y, size, seg.t0, align="left", width=width)
    chip_x = 360 + width + 6
    html += (f'<div class="qchip" style="left:{chip_x:.0f}px;top:{HEAD_Y + 30}px;background:{TIERS[t][2]};'
             f'{_anim("edpop", seg.t0 + .12, .34, ease="cubic-bezier(.2,.8,.2,1)")}">{TIERS[t][1]}</div>')
    html += ED.caption(q, 360, Q_Y, 44, seg.t0 + .2, style="box", align="left", width=1000, weight=900)
    return html


def _timer(start: float) -> str:
    cx, cy, size = TIMER_C
    k = f"qn{int(start * 1000)}"
    return (f'<style>@keyframes {k}{{from{{--n:{TIMER}}}to{{--n:0}}}}</style>'
            f'<div style="position:absolute;left:{cx - size / 2:.0f}px;top:{cy - size / 2:.0f}px;width:{size}px;'
            f'height:{size}px;z-index:41;{_anim("fadein", start - .25, .2)}">'
            f'<div class="ring" style="position:absolute;inset:0;{_anim("drain", start, TIMER)}"></div>'
            f'<div style="position:absolute;inset:11px;border-radius:50%;background:#0A0A0B;display:flex;'
            f'align-items:center;justify-content:center"><span class="count" style="font:900 58px/1 \'TikTok Sans\','
            f'sans-serif;color:#E8FF3A;{_anim(k, start, TIMER, ease=f"steps({TIMER},end)")}"></span></div></div>')


def _choice_boxes(names: list, correct: int, t_show: float, t_rev: float) -> str:
    html = ""
    for i, (name, y) in enumerate(zip(names, CH_Y)):
        size = LE.fit(name, CH_W - 44 - 84 - 10, 50, 26, 800, .1)
        box = (f'<div class="qc" style="left:{CH_X}px;top:{y}px;width:{CH_W}px;height:{CH_H}px;font-size:{size:.0f}px;'
               f'{_anim("edpop", t_show + .08 * i, .34, ease="cubic-bezier(.2,.8,.2,1)")}">'
               f'<div class="qc-l">{"ABCD"[i]}</div><div>{esc(name)}</div></div>')
        html += box
        if i == correct:
            html += (f'<div class="qc ok" style="left:{CH_X}px;top:{y}px;width:{CH_W}px;height:{CH_H}px;'
                     f'font-size:{size:.0f}px;z-index:43;{_anim("edpop", t_rev, .34, ease="cubic-bezier(.2,.8,.2,1)")}">'
                     f'<div class="qc-l">✓</div><div>{esc(name)}</div></div>')
        else:
            html += (f'<div class="qdim" data-safe="ignore" style="left:{CH_X}px;top:{y}px;width:{CH_W}px;'
                     f'height:{CH_H}px;{_anim("fadein", t_rev, .2)}"></div>')
    return html


def _tile(lv, e: dict, box: tuple, fig_style: str = "", extra: str = "") -> tuple:
    x, y, w, h = box
    iid = lv.uid("q")
    return iid, ED.tile(lv.src(e["uri"]), e["item"], x, y, w, h, iid, trim=trim_for(e["item"]), fig=.94,
                        fig_style=fig_style, extra=extra)


def level_screen(lv, seg, lvl: dict):
    """One level: the header, the picture and the choices; the timer from the
    end of 'Level n'; the reveal on the answer line."""
    _css_once(lv)
    fmt = lvl["fmt"]
    t_q = seg.lines_at[0][1] + .05                       # the timer starts as "Level n" ends
    t_rev = seg.lines_at[1][0] - .12 if len(seg.lines_at) > 1 else seg.t1 - 1.5
    over = _header(lv, seg, lvl, FORMATS[fmt]["q"])
    over += f'<div style="{_anim("edhide", t_rev, .001, "forwards")}">{_timer(t_q)}</div>'
    scene = _bg(lvl["tier"])
    a = lvl["a"]
    if fmt == "which_first":
        first = min(lvl["pair"], key=lambda e: e["season"])
        for i, (e, box) in enumerate(zip(lvl["pair"], PAIR)):
            iid, tile = _tile(lv, e, box, extra=f"transform:rotate({(-2, 2)[i]}deg)")
            scene += tile
            x, y, w, h = box
            over += ED.caption("AB"[i], x + 20, y + 16, 56, seg.t0 + .15 + .1 * i, style="lime", align="left",
                               width=120, weight=900)
            over += ED.caption(e["name"], x + w / 2, y + h - 74, LE.fit(e["name"], w - 60, 40, 24, 800, .64),
                               seg.t0 + .3 + .1 * i, style="box", width=w - 20, weight=800)
            over += ED.caption(e["season_text"].lower(), x + w / 2, y + h + 8,
                               LE.fit(e["season_text"], w - 40, 34, 22, 700, .64), t_rev + .15, style="dark",
                               width=w, weight=700)
            if e is first:
                over += (f'<div data-safe="ignore" style="position:absolute;left:{x - 8}px;top:{y - 8}px;'
                         f'width:{w + 16}px;height:{h + 16}px;border:10px solid #E8FF3A;border-radius:36px;'
                         f'z-index:43;{_anim("edpop", t_rev, .34, ease="cubic-bezier(.2,.8,.2,1)")}"></div>')
                over += ED.caption("first ✓", x + w - 20, y + 20, 52, t_rev, style="lime", align="right", width=320,
                                   weight=900, rot=6)
        over += ED.caption("vs", W / 2 + 0, 520, 60, seg.t0 + .4, style="out", width=160, weight=900)
    else:
        box = PIC
        x, y, w, h = box
        if fmt == "whos_that":
            _, sil = _tile(lv, a, box, fig_style=SIL, extra="background:#0e131b")
            iid, color = _tile(lv, a, box)
            scene += (f'<div style="{_anim("edhide", t_rev, .001, "forwards")}">{sil}</div>'
                      f'<div style="{_anim("fadein", t_rev, .15)}">'
                      f'{ED.canvas(iid, ED.tile_colors(a["item"]), 1.2, .6)}{color}</div>')
        elif fmt == "zoomed_in":
            z = ZOOM[lvl["tier"]]
            style = (f"transform-origin:50% 14%;--z:{z};"
                     f"{_anim('qzo', t_rev, .7, ease='cubic-bezier(.3,.1,.2,1)')}")
            iid, tile = _tile(lv, a, box, fig_style=style)
            scene += (f'<div style="{_anim("fadein", t_rev, .3)}">{ED.canvas(iid, ED.tile_colors(a["item"]), 1.2, .6)}'
                      f'</div>{tile}')
        else:                                            # guess_season: the skin and its name, no secret
            iid, tile = _tile(lv, a, box)
            scene += ED.canvas(iid, ED.tile_colors(a["item"]), 1.2, .62) + tile
            over += ED.caption(a["name"], x + w / 2, y + h - 74, LE.fit(a["name"], w - 60, 42, 24, 800, .64),
                               seg.t0 + .25, style="box", width=w - 20, weight=800)
        if fmt in ("whos_that", "zoomed_in"):
            over += ED.caption(a["name"], x + w / 2, y + h - 74, LE.fit(a["name"], w - 60, 42, 24, 800, .64),
                               t_rev + .1, style="lime", width=w - 20, weight=900)
        names = lvl["choices"]
        correct = names.index(a["season_text"] if fmt == "guess_season" else a["name"])
        over += _choice_boxes(names, correct, seg.t0 + .25, t_rev)
    lv.scene(seg.t0, seg.t1, scene)
    lv.over(seg.t0, seg.t1, over)
    for i in range(TIMER):
        lv.cue(t_q + i, "tick")
    lv.cue(t_rev, "reveal")
    lv.cue(t_rev + .05, "impact")
    lv.cam.punch(t_rev, .04, .3)
    lv.cam.flash(t_rev, .35, .18)
    lv.cam.push(seg.t0, seg.t1, 1.0, 1.03, W / 2, H / 2)
    if lvl["n"] % 2:
        lv.cam.zoom(seg.t0, .3)
    else:
        lv.cam.whip(seg.t0, -1, 0, 480)


def tier_screen(lv, seg, e: dict):
    """Between tiers: the tier's name big in its colour, the levels, the ask to keep score."""
    t = e["tier"]
    lv.scene(seg.t0, seg.t1, _bg(t))
    word = TIERS[t][1]
    size = LE.fit(word, 1300, 230, 90, 900, .25)
    over = ED.outline(word, W / 2, 250, size, seg.t0 + .05, align="center", width=1500)
    over = over.replace('fill="#fff"', f'fill="{TIERS[t][2]}"')
    over += ED.caption(e["levels"], W / 2, 260 + size * 1.3, 52, seg.t0 + .35, style="box", width=1200, weight=900)
    if e.get("score"):
        at = seg.lines_at[0][0] if seg.lines_at else seg.t0 + .6
        over += ED.caption(e["score"], W / 2, 400 + size * 1.3, 44, at + .2, style="lime", width=1300, weight=900,
                           rot=-2)
    lv.over(seg.t0, seg.t1, over)
    lv.cue(seg.t0 + .05, "boom")
    lv.cam.punch(seg.t0 + .05, .06, .35)
    lv.cam.push(seg.t0, seg.t1, 1.0, 1.05, W / 2, H / 2)


def intro_screen(lv, seg, fmt: str, head: str, sub: str, levels: list):
    """The title on the left; on the right three of the levels' pictures as
    they'll be asked (silhouettes, close-ups or plain)."""
    _css_once(lv)
    lv.scene(seg.t0, seg.t1, _bg(1))
    tiles = ""
    n = len(levels)
    picks = [levels[i]["a"] for i in (n // 12, n // 3, 2 * n // 3)]
    for e, (x, y, r) in zip(picks, [(1010, 290, -4), (1250, 230, 3), (1490, 310, -2)]):
        style = SIL if fmt in ("whos_that",) else ("transform-origin:50% 14%;transform:translateX(-50%) scale(2.6)"
                                                   if fmt == "zoomed_in" else "")
        _, tile = _tile(lv, e, (x, y, 300, 400), fig_style=style,
                        extra=f"transform:rotate({r}deg);" + ("background:#0e131b" if fmt == "whos_that" else ""))
        tiles += tile
    lv.scene(seg.t0, seg.t1, tiles, z=2)
    rows = head.upper().split("\n")
    size = min(LE.fit(r, 860, 150, 56, 900, .25) for r in rows)
    start = seg.t0 - 1 if seg.t0 <= 0 else seg.t0
    over, top = "", 300
    for r in rows:
        over += ED.outline(r, 120, top, size, start, align="left", width=860)
        top += size * 1.08
    sub_at = seg.lines_at[1][0] if len(seg.lines_at) > 1 else seg.t0 + .5
    over += ED.caption(sub, 124, top + 40, LE.fit(sub, 830, 40, 26, 800, .64), sub_at, style="box", align="left",
                       width=840, weight=800, rot=-1)
    lv.over(seg.t0, seg.t1, over)
    lv.cam.push(seg.t0, seg.t1, 1.0, 1.05, W / 2, H / 2)


# ------------------------------------------------------------------ the episode

def _answer_lines(lvl: dict, rnd: random.Random) -> list:
    fmt, a = lvl["fmt"], lvl["a"]
    if fmt == "which_first":
        first, second = sorted(lvl["pair"], key=lambda e: e["season"])
        return [(f"{first['name']} came first: {first['season_text']}.",
                 f"{first['name']} came first: {first['season_text']}."),
                (f"{second['name']} came out in {second['season_text']}.",
                 f"{second['name']} came out in {second['season_text']}.")]
    if fmt == "guess_season":
        return [f"{a['name']} came out in {a['season_text']}.",
                SER.two("It's been in the Item Shop {t}.", t=SER.Times(a["times"]))]
    lines = [f"It's {a['name']}!"]
    if a["season_text"] and rnd.random() < .5:
        lines.append(f"It came out in {a['season_text']}.")
    else:
        lines.append(SER.two("It's been in the Item Shop {t}.", t=SER.Times(a["times"])))
    return lines


def make(ep: dict, day: date, hist: R.History, art, rnd: random.Random, seed: int):
    """(LongEdit, rows, topic, hook, thumb) for a Quiz Night, or None."""
    import cc_long_v2 as V2
    fmt = ep["format"]
    info = dict(FORMATS[fmt])
    keys, salt, theme = None, "", ""
    if ep.get("event") == "fortnitemares":
        keys = V2._seasonal_keys(hist, "fortnitemares")
        salt, theme = "fm", "halloween"
        info.update(HALLOWEEN)
        fmt = "whos_that"
    k = max(0, V2._week(day)) // len(V2.QUIZ_CYCLE) if not salt else day.year
    levels = plan(fmt, hist, day, art, k, keys, salt)
    if not levels:
        return None
    for lvl in levels:
        lvl["fmt"] = fmt
    lv = LE.LongEdit(seed, info["title"], day=day)
    n = len(levels)
    hook = ("Level forty is almost impossible. 👀", "Level 40 is almost impossible. 👀")
    lv.segment([SER.two("Can you get all {n}?", n=n), info["how"],
                "They start easy and get harder. Keep score, and tell us yours in the comments.", hook,
                "Let's go. 👇"],
               lambda lv_, s: intro_screen(lv_, s, fmt, info["head"], info["sub"], levels), chapter="Intro", cue="",
               min_len=10)
    talk = [["Let's start easy.", "Ten levels. Five seconds each."],
            ["How many did you get? 👀", "Now it gets harder. Medium. Ten more."],
            ["Still with us? Write down your score.", "Hard levels now. Ten of them."],
            ["The last ten. Impossible. Good luck. 😈"]]
    for t in range(len(TIERS)):
        first, last = t * LEVELS_PER_TIER + 1, (t + 1) * LEVELS_PER_TIER
        if t == 3:
            lv.segment(["Quick one before the impossible levels.",
                        ("If you're buying anything in the Item Shop, you can support the channel with code B, A, D.",
                         "If you're buying anything in the Item Shop, you can support the channel with code BAD."),
                        "Just type it into the Support-A-Creator box. Thanks, it really helps. 💚"],
                       cta_screen, cue="swoosh", min_len=8)
        score = "" if t == 0 else f"your score so far: ?? / {first - 1}"
        lv.segment(talk[t], lambda lv_, s, t=t, score=score, a=first, b=last: tier_screen(
            lv_, s, {"tier": t, "levels": f"levels {a}–{b}", "score": score}),
            chapter=f"{TIERS[t][1].title()} (levels {first}–{last})", min_len=5, cue="swoosh")
        for lvl in levels[first - 1:last]:
            lines = [SER.two("Level {n}.", n=lvl["n"])] + _answer_lines(lvl, rnd)
            lv.segment(lines, lambda lv_, s, lvl=lvl: level_screen(lv_, s, lvl), pauses={0: TIMER + .35},
                       min_len=8, cue="whoosh")
    rows = [lvl["a"] for lvl in levels]
    last = levels[-LEVELS_PER_TIER:]
    lv.segment([SER.two("That's all {n} levels!", n=n), "How many did you get? Tell us your score in the comments.",
                f"If you want more like this, subscribe. {V2.CADENCE} 🔔",
                ("And if you're buying anything in the Item Shop, use code B, A, D. See you next time.",
                 "And if you're buying anything in the Item Shop, use code BAD. See you next time! 💚")],
               lambda lv_, s: SER.grid_screen(lv_, s, "the impossible ten", [x["a"] for x in last],
                                              [f"level {x['n']}" for x in last]),
               chapter="Outro", min_len=11)
    thumb = _thumb(fmt, levels, theme)
    return lv, rows, f"quiz: {fmt}", ("Can you get all 40? 👀", "Can you get all 40? 👀"), thumb


def _thumb(fmt: str, levels: list, theme: str) -> dict:
    easy = [lvl["a"] for lvl in levels[:20]]
    if fmt == "which_first":
        pair = levels[3]["pair"]
        return {"family": "versus", "words": ["WHICH CAME FIRST?", "40 LEVELS"], "pair": tuple(pair),
                "rows": easy, "theme": theme}
    if fmt == "zoomed_in":
        return {"family": "zoom", "words": ["ZOOMED", "IN"], "tag": "40 LEVELS", "rows": easy, "theme": theme}
    if fmt == "guess_season":
        return {"family": "hero_stat", "kicker": "GUESS THE", "stat": lambda r: "SEASON?", "stamp": "WHICH SEASON?",
                "rows": easy, "theme": theme}
    words = ["GUESS THE", "HALLOWEEN SKIN"] if theme else ["GUESS THE", "SKIN"]
    return {"family": "silhouette", "words": words, "tag": "40 LEVELS", "rows": easy, "theme": theme}


def tags(ep: dict) -> list:
    fmt = ep.get("format", "whos_that")
    base = list(FORMATS.get(fmt, FORMATS["whos_that"])["tags"])
    if ep.get("event") == "fortnitemares":
        base = ["fortnitemares quiz", "fortnite halloween skins", "guess the fortnite skin"]
    return base + ["fortnite quiz", "fortnite trivia"]


def describe_lines(out: dict) -> list:
    return ["Can you get all 40? Five seconds a level, from easy to impossible. 👀", "",
            "Keep score and tell us your total in the comments. The answers come from Epic's own item data and the "
            "Item Shop's records.", ""]
