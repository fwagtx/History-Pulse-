"""
THE QUIZZES, as edits: the quiz plan's formats (creator-code/quiz/plan.json)
cut the way a person cuts a quiz TikTok, to a real track (cc_edit) -- the same
rounds, answers, facts and post text as the classic quizzes (cc_quiz for the
quiz formats, cc_series for the Fortnitemares and Winterfest editions).

    build(spec, items, ctx) -> Video | None      like cc_quiz.build: `spec` is one
                                                  entry of plan.json's "videos",
                                                  `items` its "items"

A picture round (whos_that, zoomed_in, guess_season, which_year), cut on a bar
line: the round top right ("round 2/6", lime "final round 😤"), the question
under it, the cosmetic on its tile, the four choices popping in one a beat as
caption boxes (A-D) stacked over the tile's foot, a 3-2-1 on the beat over the
tile's corner, then the answer on the next downbeat: a hit, a ding, a flash and
a shake, the right choice lit lime with a ✅, the others dimmed, a sticker where
the 3-2-1 was, and what the classic says about the answer in the question's
place (the season it came out, its Fortnitemares year or winter event, its
first day in the Item Shop), then a nudge or how far in we are.

  whos_that     the silhouette on a plain canvas; the reveal cuts it to the
                real art (and the canvas to its blurred copy) on the downbeat
  zoomed_in     an extreme close-up on the plan's focus, bigger through the
                camera, stepping back on every beat; the reveal pulls all the
                way out
  guess_season  the cosmetic and its name (and type, in the gear edition),
                four seasons
  which_year    (Fortnitemares) the cosmetic and its name, four years
  which_first   two tiles, Higher or Lower's frame: the choices are the names
                ("A · name"), the 3-2-1 between the tiles, then the one that
                came first lit lime with a crown, the other shaded, and when
                each came out (its season, or its first day in the shop) under
                its tile
  throwback     one season's cosmetics (or one Fortnitemares / winter event's),
                one per screen, cut on the bars like On This Day: the season
                ("C1 S5", or the event's year) big top right, the name along the
                tile's foot, what it is above it; a silhouette, "and the last
                one… 🥁" and a riser before the last, which drops on a flash

  cover         frame 0: the quiz's name big, the edition top right ("fortnite
                quiz #12", "fortnitemares edition 🎃"), the first round's
                cosmetics on tiles (silhouettes, the close-up, "season ?",
                "20??", 🆚), a bar later "can you get all 6 right? 👀"
  outro         the answers on small tiles, one a beat, "how many did you get
                right? 👇" (the throwback: "which one did you own? 👇"), then the
                lime "use code BAD in the item shop 💚"

Seasonal entries (spec["series"] "fortnitemares" / "winterfest") use the same
builders on the series' colours -- purple and pumpkin tiles, or ice and deep
blue -- with its emojis (🎃🦇 / ❄️🎄) on the edition line, the round labels and
the reveals. The track is the day's (music_for with day=ctx.day: a Halloween
track can come up in October, a Christmas one in December), salted per format.

Every round is a whole number of bars and every event sits on a unit; the
rounds get the fewest units that make the content 57 s or more (84 s at most),
so the video is 62-89 s with the end card at any tempo from 70 to 180 bpm.

Truth rules are the classic's: every answer is the plan's (a field of the
item: its season, its name, its Fortnitemares year, which came out first),
every date its first day in the Item Shop as cc_series words it, and nothing
gives an answer away before its reveal: silhouettes and close-ups sit on plain
canvases (a blurred copy of the art would show its colours), the cover shows no
answer, and the post text is the classic's word for word (no answers in it),
with the track's credit line.
"""

import math
import re

import cc_edit as ED
import cc_quiz as Q
import cc_series as SR
from cc_formats import Video, _caption, num
from cc_motion import FPS, esc, trim_for

MIN_CONTENT = 57.0              # + the 5.1 s end card = 62.1 s
MAX_CONTENT = 84.0
FRAME = 1 / FPS                 # a caption that hands its place on goes a frame early
HOOK, OUTRO = 8, 12             # units
# Units per round -> (bars of question, bars of reveal); the 3-2-1 is one bar.
PLAN = {12: (1, 1), 16: (2, 1), 20: (2, 2), 24: (3, 2), 28: (3, 3), 32: (4, 3)}
TOP_R = 1010                    # right edge of the header, beside the code sticker (x 66-~400, y 283-~515)
MID = 480                       # the middle of the column beside the button rail (x 60-900)
SILHOUETTE = "filter:brightness(0) drop-shadow(0 0 20px rgba(255,255,255,.4))"
NUDGES = ["did you get it? 👀", "too easy? 😤", "be honest, did you get it? 👀", "who got this one? 🙋"]

# ------------------------------------------------------------------ layout
# A picture round: the round top right, the one changing header line under it
# (the question, the 3-2-1, what the answer was), the tile in the column, the
# four choices stacked over its foot, ending above the caption zone (y 1420).
ROUND_Y = 296
SLOT_Y, SLOT_W = 364, 590       # the header line: right-aligned at TOP_R, x 420-1010
PT_X, PT_Y, PT_W, PT_H = 170, 530, 620, 640
CD_X, CD_Y, CD_SIZE = PT_X + PT_W - 100, PT_Y + 120, 190    # the 3-2-1 over the tile's top corner
PT_CX = PT_X + PT_W / 2         # 480
CH_BOTTOM = 1400                # the last choice's box ends about here
CH_W = 840
ZOOM_IN = 3.4                   # the close-up, inside the tile (the classic starts at 3.6)
ZOOM_CAM = 1.4                  # and the camera on top of it, stepping back on the beat

# Two tiles side by side (the cover, Which Came First) -- Higher or Lower's frame.
TW, TH, TY = 400, 556, 706
TX = (70, 490)
TCX = (TX[0] + TW / 2, TX[1] + TW / 2)          # 270, 690
CAM_Y2 = TY + TH / 2                            # 984
Q_Y, Q_H, Q_W = 526, 152, 940                   # the caption slot above them
COUNT_Y = TY + TH - 38                          # across the tiles' foot
BTN_Y, BTN_SIZE = 1334, 46
CD2_SIZE = 200

# One cosmetic a screen (Throwback) -- On This Day's frame.
TB_X, TB_Y, TB_W, TB_H = 150, 540, 660, 760
TB_CX = TB_X + TB_W / 2
YEAR_R, YEAR_Y, YEAR_F = 1000, 205, 224
DATE_Y = 462
NAME_FOOT = 1400
SLOT_F = 44
TB_SHAPES = [((8, 4, 12), 0.0), ((8, 8, 12), .2), ((8, 8, 16), .45), ((4, 4, 12), .6), ((4, 4, 8), .8)]

TRANSITIONS = ["zoom", "whip_left", "zoom", "whip_up"]

# Each series' look: the two tile colours its rounds alternate (cc_edit.TILE
# keys), its emojis, and the edition line.
SEASONS = {
    "fortnitemares": {"tiles": ("dark", "lava"), "emoji": "🎃", "emoji2": "🦇",
                      "edition": "fortnitemares edition 🎃", "short": "fortnitemares"},
    "winterfest": {"tiles": ("frozen", "rare"), "emoji": "❄️", "emoji2": "🎄",
                   "edition": "winterfest edition ❄️", "short": "winterfest"},
}


# ------------------------------------------------------------------ text helpers

def _em(text: str) -> float:
    """About how wide a caption of `text` is, in em of TikTok Sans 800 with the
    box's padding: a little over, so what fits here fits on the page."""
    w = .64
    for ch in text:
        o = ord(ch)
        if o in (0xFE0F, 0x200D):
            continue
        w += 1.3 if o >= 0x2190 else .56
    return w


def _fit(text: str, width: float, most: float, least: float = 26, lines: int = 1) -> float:
    """The biggest size up to `most` at which `text` fits `width` in `lines` lines."""
    return max(least, min(most, lines * width * .9 / _em(text)))


def _lines(text: str, size: float, width: float) -> int:
    return max(1, math.ceil(_em(text) * size / (width * .92)))


def _season(label: str) -> str:
    """'Chapter 2 · Season 4' -> 'chapter 2 · season 4' (OG and Season X stay capitals)."""
    return re.sub(r"\b(og|x)\b", lambda m: m.group(1).upper(), label.lower())


def _short_season(label: str) -> str:
    """'Chapter 1 · Season 5' -> 'C1 S5', 'Chapter 4 · Season OG' -> 'C4 OG',
    'Chapter 2 · Remix' -> 'C2 REMIX'; '' when the label isn't one of those."""
    m = re.fullmatch(r"Chapter (\w+) · Season (\w+)", label.strip())
    if m:
        s = m.group(2)
        return f"C{m.group(1)} {'OG' if s.lower() == 'og' else 'S' + s}"
    m = re.fullmatch(r"Chapter (\w+) · (\w+)", label.strip())
    return f"C{m.group(1)} {m.group(2).upper()}" if m else ""


def _nb(text: str) -> str:
    return esc(text).replace(" ", "&nbsp;")


def _parts(parts: tuple, x: float, y: float, width: float, most: float, least: float, start: float,
           end: float | None, **kw) -> str:
    """A caption of `parts` on one line when that fits at `least` px or more,
    else broken after the first part (each part kept whole)."""
    text = " ".join(parts)
    one = min(most, width * .94 / _em(text))
    if one >= least or len(parts) == 1:
        return ED.caption(_nb(text), x, y, max(one, least if len(parts) > 1 else 24), start, end, width=width,
                          raw=True, **kw)
    size = min(most, width * .94 / max(_em(parts[0]), _em(" ".join(parts[1:]))))
    return ED.caption(_nb(parts[0]) + "<br>" + _nb(" ".join(parts[1:])), x, y, size, start, end, width=width,
                      raw=True, **kw)


def _title(groups: list, width: float = 940, most: float = 84, least: float = 46) -> tuple:
    """(html for raw=True, size, lines): the words of `groups` on one line when
    that sets them nearly as big as allowed, else on two lines broken between
    groups where that sets them biggest."""
    text = " ".join(groups)
    one = min(most, width * .94 / _em(text))
    if one >= most * .9 or len(groups) < 2:
        return _nb(text), max(least, one), 1
    # the break that sets it biggest, then the most even one
    size, longest, a, b = max((min(most, width * .94 / max(_em(a), _em(b))), -max(_em(a), _em(b)), a, b)
                              for a, b in ((" ".join(groups[:i]), " ".join(groups[i:]))
                                           for i in range(1, len(groups))))
    if size < one * 1.08:
        return _nb(text), max(least, one), 1
    return _nb(a) + "<br>" + _nb(b), max(least, size), 2


def _halves(text: str) -> tuple:
    """`text` in two lines broken at the space that makes them most even."""
    ws = text.split()
    if len(ws) < 2:
        return (text,)
    best = min(range(1, len(ws)), key=lambda i: max(_em(" ".join(ws[:i])), _em(" ".join(ws[i:]))))
    return " ".join(ws[:best]), " ".join(ws[best:])


def _groups(text: str) -> list:
    """Words that must stay together on a line: 'chapter 1', 'season 5',
    'fortnitemares 2019', an emoji with the word before it."""
    ws = text.split()
    out = []
    for w in ws:
        prev = out[-1].split()[-1].lower() if out else ""
        if out and ((w[0].isdigit() and prev in ("chapter", "season", "part", "day", "#")) or ord(w[0]) >= 0x2190
                    or w in ("·", "OG", "og")):
            out[-1] += " " + w
        else:
            out.append(w)
    return out


def _kind(it: dict) -> str:
    """'epic outfit', 'icon series outfit' -- its rarity and type."""
    rar = str(it.get("rarity_label") or it.get("rarity") or "").strip().lower()
    typ = str(it.get("type") or "outfit").strip().lower()
    return f"{rar} {typ}".strip()


def _debut(it: dict) -> str:
    """cc_series' shop debut, in the captions' words: 'shop debut: oct 26, 2018',
    or 'in the shop in 2017' (the records start 2017-10-30)."""
    first = it.get("first_shop") or ""
    if first >= SR.FIRST_SURE:
        return f"shop debut: {SR._when(it).lower()}"
    return f"in the shop in {first[:4]}"


def _chip(letter: str, dark: bool = False) -> str:
    """A choice's letter, on a small plate inside its caption box."""
    bg, fg = ("rgba(255,255,255,.92)", "#111") if dark else ("#0A0A0B", "#fff")
    return (f'<span style="display:inline-block;min-width:1.18em;margin:0 .32em 0 -.08em;padding:0 .14em;'
            f'border-radius:.2em;background:{bg};color:{fg};text-align:center;font-weight:900;'
            f'line-height:1.18">{letter}</span>')


# ------------------------------------------------------------------ the look

class Look:
    """The classic colours (each cosmetic's rarity) and words, or a series'
    theme: its tile colours, emojis and edition line, and cc_series' own text
    and facts for the edition."""

    def __init__(self, spec: dict, items: dict, ctx):
        self.series = spec.get("series") or ""
        self.s = SEASONS.get(self.series)
        self.theme = SR._season_theme(spec, items, ctx) if self.s else None
        self.emoji = self.s["emoji"] if self.s else ""

    def item(self, it: dict, i: int = 0) -> dict:
        """The item as the tile colours it: its own rarity, or the series' colour."""
        return dict(it, rarity=self.s["tiles"][i % 2]) if self.s else it

    def colors(self, it: dict, i: int = 0) -> tuple:
        return ED.tile_colors(self.item(it, i))

    def react(self, i: int = 0) -> str:
        """The sticker on a reveal."""
        if self.s:
            return (self.s["emoji"], self.s["emoji2"])[i % 2]
        return ("🔥", "👑", "🎯")[i % 3]

    def tag(self, text: str) -> str:
        """A caption with the series' emoji on the end (a round label, a title)."""
        return f"{text} {self.emoji}" if self.s else text


# ------------------------------------------------------------------ shared pieces

class Cut:
    """An edit and its helpers, shared by every format."""

    def __init__(self, ctx, beat, content_end: float, look: Look):
        self.ctx, self.beat, self.look = ctx, beat, look
        self.u = beat.unit
        self.ed = ED.Edit(beat, content_end, ctx.seed)
        self.cam, self.rnd = self.ed.cam, self.ed.rnd
        self.marks = []                                    # (t, what) for QA: cuts and reveals
        self.ci = 0

    def tile(self, it: dict, x, y, w, h, i: int = 0, fig: float = .95, **kw) -> tuple:
        iid = self.ed.uid("t")
        return iid, ED.tile(self.ed.src(self.ctx.art(it)), self.look.item(it, i), x, y, w, h, iid,
                            trim=trim_for(it), fig=fig, name=it["name"], **kw)

    def cut(self, t: float, hit: str = "impact", move: str = ""):
        """Into a screen at t: a zoom or a whip through the cut (alternating), a
        swoosh into it and a hit on it."""
        move = move or TRANSITIONS[self.ci % len(TRANSITIONS)]
        self.ci += 1
        ed, cam = self.ed, self.cam
        ed.cue(t - .16, "swoosh")
        ed.cue(t, hit)
        cam.punch(t, .07)
        if move == "zoom":
            cam.zoom(t, .45)
        else:
            cam.whip(t, *((0, -1) if move == "whip_up" else (-1, 0)), px=560 if move == "whip_up" else 480)
        self.marks.append((t, "cut"))

    def reveal(self, t: float, last: bool, big: bool = False):
        """The answer on a downbeat: a hit, a ding, a flash and a shake."""
        ed, cam = self.ed, self.cam
        if last:
            ed.cue(t - 2.0, "riser")
        ed.cue(t, "boom" if last or big else "impact")
        ed.cue(t, "ding")
        cam.shake(t, 26 if last else 18, .45 if last else .38, 2 if last else 1.2)
        cam.punch(t, .1 if last else .06, .38)
        cam.flash(t, .6 if last else .45, .22)
        self.marks.append((t, "reveal"))

    def idle(self, s0: int, k: int, busy: set):
        """A light punch on each bar with nothing else on it."""
        for b in range(4, k, 4):
            if b not in busy:
                self.cam.punch(self.u(s0 + b), .025, .25)


def _choose(beat, n: int, fixed: int) -> tuple | None:
    """(units a round, total units): the fewest a round that make the video long enough."""
    u = beat.unit
    for k in sorted(PLAN):
        total = fixed + n * k
        if u(total) >= MIN_CONTENT:
            return (k, total) if u(total) <= MAX_CONTENT else None
    return None


def _grid(n: int, top: float = 730, bottom: float = 1300) -> list:
    """(x, y, w, h) of n small tiles in two rows, in reading order, inside the
    column beside the button rail (x 60-900), centred between top and bottom."""
    cols = max(3, -(-n // 2))
    rows = -(-n // cols)
    gap = 18
    w = (840 - (cols - 1) * gap) / cols
    h = min(w * 1.18, (bottom - top - (rows - 1) * gap) / rows)
    y0 = top + (bottom - top - (rows * h + (rows - 1) * gap)) / 2
    out = []
    for i in range(n):
        r, c = divmod(i, cols)
        in_row = min(cols, n - r * cols)
        x0 = 60 + (840 - (in_row * w + (in_row - 1) * gap)) / 2
        out.append((x0 + c * (w + gap), y0 + r * (h + gap), w, h))
    return out


def _outro(c: Cut, s0: int, units: int, content_end: float, entries: list, ask: str, kicker: str):
    """The answers on small tiles, one a beat (eighth notes past six), the ask,
    then use code BAD. `entries`: (item, label, tile index)."""
    ed, cam, u = c.ed, c.cam, c.u
    t_out = u(s0)
    n = len(entries)
    step = 1 if n <= 6 else .5
    tiles, labels, first, first_it = "", "", "", None
    for i, ((it, label, ti), (x, y, w, h)) in enumerate(zip(entries, _grid(n))):
        iid, html = c.tile(it, x, y, w, h, ti, fig=.92, extra=f"transform:rotate({[-2, 1, -1, 2, -2, 1, 2, -1][i % 8]}deg)")
        if not first:
            first, first_it = iid, (it, ti)
        tiles += html
        at = u(s0 + i * step)
        size = min(30.0, (w - 4) * .94 / _em(label))
        parts = (label,)
        if size < 24:
            parts = _halves(label)
            size = max(18.0, min(28.0, (w - 4) * .94 / max(_em(p) for p in parts)))
        html = "<br>".join(_nb(p) for p in parts)
        labels += ED.caption(html, x + w / 2, y + h - 16 - len(parts) * 1.3 * size, size, at, width=w + 40,
                             weight=800, lh=1.3, raw=True)
        if i:
            ed.cue(at, "pop2")
    ed.scene(t_out, content_end, ED.canvas(first, c.look.colors(*first_it), 1.0, .6) + tiles)
    code_u = max(4, math.ceil(n * step) + (1 if step < 1 else 0))
    t_code = u(s0 + code_u)
    ed.over(t_out, content_end,
            ED.caption(kicker, TOP_R, 300, 36, t_out - 1, style="dark", align="right", width=560, weight=700)
            + ED.caption(ask, 540, 540, _fit(ask, 900, 60, 44), t_out, width=940, weight=800, rot=-1.5)
            + labels
            + ED.caption("use code BAD in the item shop 💚", MID, 1334, 44, t_code, style="lime", width=820,
                         weight=800))
    c.cut(t_out, move="whip_up")
    cam.push(t_out, content_end, 1.0, 1.04, MID, 1000)
    ed.cue(t_code, "pop2")
    cam.punch(t_code, .05)
    for b in range(4, units, 4):
        if b != code_u and not (b < n * step):
            cam.punch(u(s0 + b), .025, .25)


def _post(v: Video, music: dict) -> Video:
    """The classic's post, with the track's credit line at the end of its head."""
    if not music.get("artist"):
        return v
    credit = f"🎵 {music['title']} by {music['artist']} (public domain, CC0)"
    head, sep, rest = v.caption.partition("\n\n")
    cap = f"{head}\n{credit}{sep}{rest}"
    from cc_formats import CAPTION_MAX, _u16
    if _u16(cap) <= CAPTION_MAX:
        v.caption = cap
    return v


def _cover_bottom(c: Cut, first: str, second: str, t_end: float):
    """The cover's bottom line: `first` (a dark fact), then a bar in, `second`."""
    u = c.u
    return (ED.caption(first, MID, BTN_Y + 4, _fit(first, 800, 40, 32), -1, u(4) - FRAME, style="dark", width=820,
                       weight=800)
            + ED.caption(second, MID, BTN_Y, _fit(second, 800, BTN_SIZE, 34), u(4), width=820, weight=800, rot=2))


# ------------------------------------------------------------------ picture quizzes

class Fmt:
    """What differs between the four picture quizzes."""

    def __init__(self, fmt: str, look: Look, spec: dict):
        self.fmt, self.look = fmt, look
        s = look.s
        self.mode = {"whos_that": "silhouette", "zoomed_in": "zoom"}.get(fmt, "plain")
        self.show_name = fmt in ("guess_season", "which_year")
        emoji = look.emoji
        self.title = {"whos_that": f"who's that skin? {emoji or '🤔'}",
                      "zoomed_in": "zoomed in 🔍",
                      "guess_season": "guess the season 🤔",
                      "which_year": "which fortnitemares? 🎃"}[fmt]
        self.question = {"whos_that": "who's that skin? 🤔", "zoomed_in": "who is this? 🔍",
                         "guess_season": "what season? 🤔",
                         "which_year": f"which {s['short'] if s else 'year'}? {emoji or '🤔'}"}[fmt]
        self.cover_line = {"whos_that": "4 names each, pause and guess 👀",
                           "zoomed_in": "name it before it zooms out 🔍",
                           "guess_season": "4 seasons each, pause and guess 👀",
                           "which_year": "guess the year 👀"}[fmt]
        self.kicker = s["edition"] if s else f"fortnite quiz #{spec['episode']}"
        self.gear = spec.get("edition") == "gear"

    def label(self, it: dict) -> str:
        """The name shown when it isn't the answer (with its type in the gear edition, as the classic)."""
        return it["name"] + (f" · {str(it.get('type') or '').lower()}" if self.gear else "")

    def option(self, text: str) -> str:
        if self.fmt == "guess_season":
            return _season(text)
        if self.fmt == "which_year":
            return text.lower()
        return text

    def fact(self, it: dict) -> tuple:
        """The line that lands with the answer, as the classic words it: the
        words that may go on a line of their own, then the rest."""
        lk = self.look
        if self.fmt in ("whos_that", "zoomed_in"):
            if lk.series == "fortnitemares":
                return ("from", f"fortnitemares {it['fm_year']} 🎃")
            if lk.series == "winterfest":
                return ("first in the shop:", f"{it['wf_event'].lower()} {it['wf_year']} ❄️")
            return ("came out in", f"{_season(it['season_label'])} 👀")
        if self.fmt == "which_year":
            lead, _, rest = _debut(it).partition(": ")
            return (lead + ":", rest) if rest else (lead,)
        return ()

    def recap(self, it: dict, rd: dict) -> str:
        """Its answer, for the outro: the choice that lit ("2019" for a year)."""
        right = self.option(rd["options"][rd["answer"]])
        if self.fmt == "which_year":
            return right.split()[-1]
        return right


def _choices_geometry(opts: list) -> tuple:
    """(font size, row tops) for the four choices stacked above y CH_BOTTOM."""
    longest = max(_em(o) + 1.5 for o in opts)                  # + the letter's plate
    size = max(30.0, min(44.0, CH_W * .92 / longest))
    step = size * 1.46 + 14                                     # a box is about 1.46 em tall
    top = CH_BOTTOM - 3 * step - size * 1.41
    return size, [top + j * step for j in range(4)]


def _picture_quiz(spec: dict, items: dict, ctx, look: Look):
    fmt = spec["format"]
    rounds = Q._usable(ctx, spec["rounds"], ("item",), items, 6)
    if len(rounds) < 5:
        return None
    n = len(rounds)
    F = Fmt(fmt, look, spec)
    beat = ED.music_for(ctx.seed, "hype", day=ctx.day, salt=f"quiz_{fmt}")
    got = _choose(beat, n, HOOK + OUTRO)
    if not got:
        return None
    k, total = got
    u = beat.unit
    content_end = u(total)
    nq, nr = PLAN[k]
    c = Cut(ctx, beat, content_end, look)
    ed, cam, rnd = c.ed, c.cam, c.rnd
    its = [items[rd["item"]] for rd in rounds]
    nudges = list(NUDGES)
    rnd.shuffle(nudges)

    # ------------------------------------------------------------ cover: units 0-8
    t_game = u(HOOK)
    over = ED.caption(F.kicker, TOP_R, 298, _fit(F.kicker, 560, 44, 34), -1, style="dark", align="right", width=580,
                      weight=800)
    over += ED.caption(_nb(F.title), 540, 546, min(92.0, 960 * .94 / _em(F.title)), -1, width=980, weight=900,
                       rot=-2, raw=True)
    if F.mode == "zoom":
        # the first close-up, big: nothing on the cover names it
        it = its[0]
        zx, zy = _focus(rounds[0])
        _, tl = c.tile(it, 170, 700, 620, 600, 0, extra="transform:rotate(-1.5deg)",
                       fig_style=f"transform-origin:{zx * 100:.1f}% {zy * 100:.1f}%;"
                                 f"transform:translateX(-50%) scale({ZOOM_IN})")
        ed.scene(0, t_game, ED.canvas("", look.colors(it, 0), 1.0, .55) + tl)
        over += ED.caption("who is this? 🤔", MID, 1226, 50, -1, width=700, weight=800, rot=2)
        cam.push(0, t_game, 1.0, 1.05, MID, 1000)
    else:
        sil = F.mode == "silhouette"
        a, b = its[0], its[1]
        ida, tla = c.tile(a, TX[0], TY, TW, TH, 0, extra="transform:rotate(-2deg)",
                          fig_style=SILHOUETTE if sil else "")
        _, tlb = c.tile(b, TX[1], TY, TW, TH, 1, extra="transform:rotate(2deg)", fig_style=SILHOUETTE if sil else "")
        ed.scene(0, t_game, ED.canvas("" if sil else ida, look.colors(a, 0), 1.2, .5) + tla + tlb)
        for side, it in enumerate((a, b)):
            rot = -2 if side == 0 else 2
            if F.show_name:
                over += _name_on_tile(F.label(it), TCX[side], COUNT_Y - 4, -1, rot)
            unknown = {"silhouette": "???", "plain": "season ?" if fmt == "guess_season" else "20??"}[F.mode]
            over += ED.caption(unknown, TCX[side], COUNT_Y, 64, -1, width=TW, weight=900, rot=rot, lh=1.28)
        cam.push(0, t_game, 1.0, 1.05, MID, CAM_Y2)
    over += _cover_bottom(c, F.cover_line, f"can you get all {n} right? 👀", t_game)
    ed.over(0, t_game, over)
    cam.punch(u(4), .06)
    ed.cue(u(4), "impact")
    ed.cue(u(4), "pop2")

    # ------------------------------------------------------------ the rounds
    ui = HOOK
    for r, (rd, it) in enumerate(zip(rounds, its), 1):
        last = r == n
        s0 = ui
        start, end = u(s0), u(s0 + k)
        bu = lambda i, s0=s0: u(s0 + i)                    # noqa: E731 -- unit i of this round
        c0, cstep = {1: (1, .5), 2: (2, 1), 3: (2, 2)}.get(nq, (4, 2))
        cd = 4 * nq
        land = cd + 4
        t_q = start if nq == 1 else bu(1)
        t_ch = [bu(c0 + j * cstep) for j in range(4)]
        t_land = bu(land)
        t_f1 = bu(land + 1)
        t_f2 = bu(land + 4) if nr >= 2 else None
        opts = [F.option(o) for o in rd["options"]]
        ans = rd["answer"]
        ti = r - 1

        # the picture
        if F.mode == "plain":
            iid, tl = c.tile(it, PT_X, PT_Y, PT_W, PT_H, ti)
            ed.scene(start, end, ED.canvas(iid, look.colors(it, ti), 1.25, .45) + tl)
            cam.push(start, end, 1.0, 1.04, PT_CX, PT_Y + PT_H / 2)
        elif F.mode == "silhouette":
            _, sil = c.tile(it, PT_X, PT_Y, PT_W, PT_H, ti, fig_style=SILHOUETTE)
            ed.scene(start, t_land, ED.canvas("", look.colors(it, ti), 1.25, .45) + sil)
            iid, tl = c.tile(it, PT_X, PT_Y, PT_W, PT_H, ti)
            ed.scene(t_land, end, ED.canvas(iid, look.colors(it, ti), 1.25, .45) + tl)
            cam.push(start, end, 1.0, 1.04, PT_CX, PT_Y + PT_H / 2)
        else:
            zx, zy = _focus(rd)
            org = f"transform-origin:{zx * 100:.1f}% {zy * 100:.1f}%;"
            _, zt = c.tile(it, PT_X, PT_Y, PT_W, PT_H, ti,
                           fig_style=org + f"transform:translateX(-50%) scale({ZOOM_IN})")
            ed.scene(start, t_land, ED.canvas("", look.colors(it, ti), 1.25, .45) + zt)
            name = ed.uid("qzout")
            ed.comp.css(f"@keyframes {name}{{0%{{transform:translateX(-50%) scale({ZOOM_IN})}}"
                        f"100%{{transform:translateX(-50%) scale(1)}}}}")
            iid, tl = c.tile(it, PT_X, PT_Y, PT_W, PT_H, ti,
                             fig_style=org + f"animation:{name} .42s cubic-bezier(.2,.8,.2,1) {t_land:.3f}s 1 normal both")
            ed.scene(t_land, end, ED.canvas(iid, look.colors(it, ti), 1.25, .45) + tl)
            # the camera: in close on the focus, a step back on every beat, then all the way out
            fy = PT_Y + PT_H * (.05 + .95 * zy)
            steps = t_ch + [bu(cd + j) for j in range(3)]
            s_now, prev = ZOOM_CAM, start
            per = (ZOOM_CAM - 1.12) / len(steps)
            for t in steps:
                cam.push(prev, t, s_now, s_now, PT_CX, fy)
                cam.push(t, t + .16, s_now, s_now - per, PT_CX, fy)
                s_now, prev = s_now - per, t + .16
            cam.push(prev, t_land, s_now, s_now, PT_CX, fy)
            cam.push(t_land, t_land + .42, s_now, 1.0, PT_CX, fy)
            cam.push(t_land + .42, end, 1.0, 1.03, PT_CX, PT_Y + PT_H / 2)

        # the header: the round, then one line that changes on the beat
        over = ED.caption("final round 😤" if last else look.tag(f"round {r}/{n}"), TOP_R, ROUND_Y, 36, start - 1,
                          style="lime" if last else "dark", align="right", width=440, weight=800)
        qs = _fit(F.question, SLOT_W, 54, 40)
        over += ED.caption(F.question, TOP_R, SLOT_Y, qs, t_q, t_land - FRAME, align="right", width=SLOT_W,
                           weight=800, rot=rnd.choice([-1.5, 1.5]))
        for j, word in enumerate("321"):
            t_end = bu(cd + j + 1) - FRAME if j < 2 else t_land - FRAME
            over += ED.outline(word, CD_X, CD_Y - .63 * CD_SIZE, CD_SIZE, bu(cd + j), t_end, align="center",
                               lime=word == "1", width=320)
        fact = F.fact(it)                                 # (lead, rest) or ()
        two = _second(r, n, nudges)
        if fact:
            over += _parts(fact, TOP_R, SLOT_Y + 4, SLOT_W, 44, 34, t_f1, None if t_f2 is None else t_f2 - FRAME,
                           style="dark", align="right", weight=700)
            if t_f2 is not None:
                over += ED.caption(two, TOP_R, SLOT_Y, _fit(two, SLOT_W, 50, 36), t_f2, align="right",
                                   width=SLOT_W, weight=800, rot=rnd.choice([-2, 2]))
        else:
            over += ED.caption(two, TOP_R, SLOT_Y, _fit(two, SLOT_W, 50, 36), t_f1, align="right", width=SLOT_W,
                               weight=800, rot=rnd.choice([-2, 2]))
        # the name over the tile's foot, when it isn't the answer
        size, tops = _choices_geometry(opts)
        if F.show_name:
            over += _name_on_tile(F.label(it), MID, tops[0] - 14, -1, 0, width=PT_W + 60, most=46)
        # the four choices, one a beat, until the reveal
        for j, (o, t) in enumerate(zip(opts, t_ch)):
            rot = (-1, 1, -1.5, 1)[j]
            over += ED.caption(_chip("ABCD"[j]) + esc(o), MID, tops[j], size, t, t_land - FRAME, width=CH_W,
                               weight=800, rot=rot, raw=True, lh=1.36)
        ed.over(start, end, over)
        # the reveal: the right one lit, the others dimmed
        lit = ""
        for j, o in enumerate(opts):
            rot = (-1, 1, -1.5, 1)[j]
            if j == ans:
                lit += ED.caption(_chip("ABCD"[j]) + esc(o) + " ✅", MID, tops[j], size, t_land, style="lime",
                                  width=CH_W, weight=900, rot=rot, raw=True, anim="edin")
            else:
                lit += ED.caption(f'<span style="opacity:.5">{_chip("ABCD"[j], True)}{esc(o)}</span>', MID, tops[j],
                                  size, t_land, style="dark", width=CH_W, weight=800, rot=rot, raw=True, anim="edin")
        lit += ED.emoji(look.react(r), CD_X + 20, CD_Y - 20, 124, t_land, rot=12)
        ed.over(t_land, end, lit)

        # sound and camera
        ed.cue(t_q, "pop2")
        for t in t_ch:
            ed.cue(t, "pop2")
        for j, amt in enumerate((.03, .04, .05)):
            ed.cue(bu(cd + j), "tick2")
            if F.mode != "zoom":
                cam.punch(bu(cd + j), amt, .22)
        if F.mode == "zoom":
            ed.cue(t_land - .16, "swoosh")
        c.reveal(t_land, last)
        for t in (t_f1, t_f2):
            if t is not None:
                ed.cue(t, "pop2")
        c.cut(start, "impact")
        if last:
            ed.cue(start, "glitch")
            cam.flash(start, .35, .12)
        if F.mode != "zoom":
            busy = {0, 1, cd, cd + 1, cd + 2, land, land + 1, land + 4}
            busy |= {int(round(c0 + j * cstep)) for j in range(4)}
            c.idle(s0, k, busy)
        ui += k

    # ------------------------------------------------------------ outro
    entries = [(it, F.recap(it, rd), r) for r, (rd, it) in enumerate(zip(rounds, its))]
    _outro(c, ui, OUTRO, content_end, entries, "how many did you get right? 👇", F.kicker)
    comp = ed.finish()
    comp.qa_marks = c.marks
    comp.qa_plan = {"units_per_round": k, "rounds": n, "unit": round(beat.period, 3)}

    # ------------------------------------------------------------ the post: the classic's words
    return _post(_picture_post(spec, look, F, comp, rounds, items, n), comp.music or {})


def _second(r: int, n: int, nudges: list) -> str:
    """The line after an answer: how far in we are, or a nudge -- never the
    same kind twice running, never the same nudge twice."""
    if r == n - 1:
        return "one more to go 👀"
    if r == n:
        return nudges[0]
    return f"{r} down, {n - r} to go 👀" if r % 2 == 0 else nudges[r % len(nudges)]


def _focus(rd: dict) -> tuple:
    f = rd.get("focus") or (.5, .3)
    return min(.75, max(.25, float(f[0]))), min(.6, max(.1, float(f[1])))


def _name_on_tile(name: str, cx: float, foot: float, start: float, rot: float = 0.0, width: float = TW - 10,
                  most: float = 34) -> str:
    """A name in a dark box whose bottom sits at `foot`: one line, or two even
    ones when long."""
    size = min(most, (width - 20) * .94 / _em(name))
    parts = (name,)
    if size < most * .76:
        parts = _halves(name)
        size = max(20.0, min(most * .94, (width - 20) * .94 / max(_em(p) for p in parts)))
    return ED.caption("<br>".join(_nb(p) for p in parts), cx, foot - len(parts) * 1.36 * size, size, start,
                      style="dark", width=width + 40, weight=700, rot=rot, raw=True)


def _picture_post(spec, look, F, comp, rounds, items, n) -> Video:
    """The classic's post for the picture quizzes (cc_quiz.guess_season /
    _name_quiz, cc_series.which_year), word for word."""
    fmt = spec["format"]
    group = [items[rd["item"]] for rd in rounds]
    if look.theme:
        v = look.theme["video"](fmt, comp, n, group)
        v.format = f"edit_{fmt}_{look.series}"
        return v
    ep = spec["episode"]
    if fmt == "guess_season":
        gear = spec.get("edition") == "gear"
        what = "pickaxes, gliders and back blings" if gear else "skins"
        body = "\n".join(f"{num(k)} {items[rd['item']]['name']} · {items[rd['item']]['type']}"
                         for k, rd in enumerate(rounds, 1))
        tags = Q._tags("guesstheseason", "ogfortnite")
        return Video("edit_guess_season", comp, title=f"Guess the Season — Fortnite Quiz #{ep}",
                     yt_title=f"Guess the Season: Fortnite Quiz #{ep} #shorts",
                     caption=_caption(f"🗓️ GUESS THE SEASON — Fortnite Quiz #{ep}\n"
                                      f"{n} {what}. When did each one come out? Pause, guess, then watch 👇",
                                      body, f"How many did you get out of {n}? Comment your score", tags),
                     hashtags=tags)
    if fmt == "zoomed_in":
        hook = (f"🔍 ZOOMED IN — Fortnite Quiz #{ep}\n"
                f"We start up close. Name the skin before the camera pulls back 👇")
        title_t, yt = f"Zoomed In — Fortnite Quiz #{ep}", f"Zoomed In: Guess the Fortnite Skin #{ep} #shorts"
        tags = Q._tags("guesstheskin", "zoomedin")
    else:
        hook = (f"👤 WHO'S THAT SKIN? — Fortnite Quiz #{ep}\n"
                f"{n} silhouettes, 4 choices each. Pause and guess 👇")
        title_t, yt = f"Who's That Skin? — Fortnite Quiz #{ep}", f"Who's That Fortnite Skin? Quiz #{ep} #shorts"
        tags = Q._tags("whosthatskin", "guesstheskin")
    body = f"{n} rounds · 4 choices each · no spoilers here, answers are in the video 🎥"
    return Video(f"edit_{fmt}", comp, title=title_t, yt_title=yt,
                 caption=_caption(hook, body, f"How many did you get out of {n}? Comment your score", tags),
                 hashtags=tags)


# ------------------------------------------------------------------ which came first

def _which_first(spec: dict, items: dict, ctx, look: Look):
    rounds = Q._usable(ctx, spec["rounds"], ("a", "b"), items, 5)
    if len(rounds) < 4:
        return None
    n = len(rounds)
    beat = ED.music_for(ctx.seed, "hype", day=ctx.day, salt="quiz_which_first")
    got = _choose(beat, n, HOOK + OUTRO)
    if not got:
        return None
    k, total = got
    u = beat.unit
    content_end = u(total)
    nq, nr = PLAN[k]
    c = Cut(ctx, beat, content_end, look)
    ed, cam, rnd = c.ed, c.cam, c.rnd
    pairs = [(items[rd["a"]], items[rd["b"]], rd["answer"] == "a") for rd in rounds]
    kicker = look.s["edition"] if look.s else f"fortnite quiz #{spec['episode']}"
    when = (lambda it: SR._when(it).lower()) if look.s else (lambda it: _season(it["season_label"]))
    nudges = list(NUDGES)
    rnd.shuffle(nudges)

    def name_cap(it, side, start, letter, end=None, rot=0.0, state=""):
        """The choice: 'A  name' in a box over its tile's foot (two even lines
        when long). `state` "right" lights it lime, "wrong" dims it."""
        size = min(40.0, (TW - 24) * .94 / (_em(it["name"]) + 1.6))
        parts = (it["name"],)
        if size < 30:
            parts = _halves(it["name"])
            size = max(22.0, min(36.0, (TW - 24) * .94 / (max(_em(p) for p in parts) + 1.6)))
        text = "<br>".join(_nb(p) for p in parts)
        y = TY + TH - 10 - len(parts) * 1.36 * size
        if state == "right":
            return ED.caption(_chip(letter) + text + "&nbsp;✅", TCX[side], y, size, start, end, style="lime",
                              width=TW + 40, weight=900, rot=rot, raw=True, anim="edin")
        if state == "wrong":
            return ED.caption(f'<span style="opacity:.5">{_chip(letter, True)}{text}</span>', TCX[side], y, size,
                              start, end, style="dark", width=TW + 40, weight=800, rot=rot, raw=True, anim="edin")
        return ED.caption(_chip(letter) + text, TCX[side], y, size, start, end, width=TW + 40, weight=800, rot=rot,
                          raw=True)

    def when_cap(it, side, start):
        """When it came out, under its tile: its season in two lines, or its first day in the shop."""
        parts = tuple(x.strip() for x in when(it).split(" · ", 1))         # "chapter 1" / "season 6"
        size = min(42.0, (TW - 30) * .94 / max(_em(x) for x in parts))
        return ED.caption("<br>".join(_nb(x) for x in parts), TCX[side], TY + TH + 16, size, start, style="dark",
                          width=TW + 20, weight=800, raw=True, lh=1.3, anim="edslam")

    def slot(text, start, end, size=52, rot=0.0, style="box"):
        size = _fit(text, Q_W - 60, size, 36, 2)
        lines = _lines(text, size, Q_W - 60)
        y = Q_Y + max(0.0, (Q_H - lines * 1.36 * size) / 2)
        return ED.caption(text, 540, y, size, start, end, style=style, width=Q_W, weight=800, rot=rot)

    # ------------------------------------------------------------ cover: units 0-8
    t_game = u(HOOK)
    a, b, _ = pairs[0]
    ida, tla = c.tile(a, TX[0], TY, TW, TH, 0, extra="transform:rotate(-2deg)")
    _, tlb = c.tile(b, TX[1], TY, TW, TH, 1, extra="transform:rotate(2deg)")
    ed.scene(0, t_game, ED.canvas(ida, look.colors(a, 0), 1.2, .5) + tla + tlb)
    title = f"which came first? {look.emoji or '⏳'}"
    over = (ED.caption(kicker, TOP_R, 298, _fit(kicker, 560, 44, 34), -1, style="dark", align="right", width=580,
                       weight=800)
            + ED.caption(_nb(title), 540, 546, min(92.0, 960 * .94 / _em(title)), -1, width=980, weight=900,
                         rot=-2, raw=True)
            + name_cap(a, 0, -1, "A", rot=-2) + name_cap(b, 1, -1, "B", rot=2)
            + ED.emoji("🆚", MID, CAM_Y2 - 40, 130, -1, rot=-6))
    over += _cover_bottom(c, "older skin: A or B? 👀" if not look.s else "first in the shop: A or B? 👀",
                          f"can you get all {n} right? 👀", t_game)
    ed.over(0, t_game, over)
    cam.push(0, t_game, 1.0, 1.05, MID, CAM_Y2)
    cam.punch(u(4), .06)
    ed.cue(u(4), "impact")
    ed.cue(u(4), "pop2")

    # ------------------------------------------------------------ the rounds
    ui = HOOK
    for r, (a, b, a_first) in enumerate(pairs, 1):
        last = r == n
        s0 = ui
        start, end = u(s0), u(s0 + k)
        bu = lambda i, s0=s0: u(s0 + i)                    # noqa: E731
        cd = 4 * nq
        land = cd + 4
        hi = 2 if nq == 1 else 4
        t_q, t_a = bu(1), bu(hi)
        t_land = bu(land)
        t_v1 = bu(land + 1)
        t_v2 = bu(land + 4) if nr >= 2 else None
        older = a if a_first else b
        side_old = 0 if a_first else 1

        ida, tla = c.tile(a, TX[0], TY, TW, TH, 0)
        idb, tlb = c.tile(b, TX[1], TY, TW, TH, 1)
        bg = ED.canvas(ida if r % 2 else idb, look.colors(a if r % 2 else b, 0 if r % 2 else 1), 1.2, .5)
        ed.scene(start, end, bg + tla + tlb)
        # after the reveal the newer one goes dark (a layer over it, in the camera)
        ed.scene(t_land, end, f'<div data-safe="ignore" style="position:absolute;left:{TX[1 - side_old]}px;'
                              f'top:{TY}px;width:{TW}px;height:{TH}px;border-radius:30px;'
                              f'background:rgba(0,0,0,.52)"></div>', z=2)
        cam.push(start, end, 1.0, 1.04, MID, CAM_Y2)

        over = ED.caption("final round 😤" if last else look.tag(f"round {r}/{n}"), TOP_R, ROUND_Y, 36, start - 1,
                          style="lime" if last else "dark", align="right", width=440, weight=800)
        over += name_cap(a, 0, start - 1, "A", t_land - FRAME) + name_cap(b, 1, start - 1, "B", t_land - FRAME)
        q = "which came out first? ⏳" if not look.s else f"which hit the shop first? {look.emoji}"
        over += slot(q, t_q, t_v1 - FRAME, rot=rnd.choice([-2, -1.5, 1.5, 2]))
        v1 = f"{older['name']} came first! 👑"
        over += slot(v1, t_v1, None if t_v2 is None else t_v2 - FRAME, 50, rot=rnd.choice([-3, -2, 2, 3]))
        if t_v2 is not None:
            two = _second(r, n, nudges)
            over += slot(two, t_v2, None, 54, rot=rnd.choice([-3, -2, 2, 3]))
        over += ED.caption("A or B? 👇", MID, BTN_Y, 44, t_a, t_land - FRAME, style="dark", width=500, weight=800)
        for j, word in enumerate("321"):
            over += ED.caption(word, MID, CAM_Y2 - CD2_SIZE / 2, CD2_SIZE, bu(cd + j), bu(cd + j + 1) - FRAME,
                               style="outlm" if word == "1" else "out", width=320, weight=900, lh=1.0, anim="edslam")
        ed.over(start, end, over)
        # the reveal: the older one's box lit, the other dimmed, when each came out under it
        lit = (name_cap(a, 0, t_land, "A", state="right" if a_first else "wrong")
               + name_cap(b, 1, t_land, "B", state="wrong" if a_first else "right")
               + when_cap(a, 0, t_land) + when_cap(b, 1, t_land)
               + ED.emoji("👑" if not look.s else look.react(r), TX[side_old] + TW - 70, TY + 76, 124, t_land,
                          rot=12 if side_old else -12))
        ed.over(t_land, end, lit)

        ed.cue(t_q, "pop2")
        ed.cue(t_a, "pop2")
        for j, amt in enumerate((.03, .04, .05)):
            ed.cue(bu(cd + j), "tick2")
            cam.punch(bu(cd + j), amt, .22)
        c.reveal(t_land, last)
        for t in (t_v1, t_v2):
            if t is not None:
                ed.cue(t, "pop2")
        c.cut(start, "impact")
        if last:
            ed.cue(start, "glitch")
            cam.flash(start, .35, .12)
        c.idle(s0, k, {0, 1, hi, hi + 1, cd, cd + 1, cd + 2, land, land + 1, land + 4})
        ui += k

    # ------------------------------------------------------------ outro
    entries = [((a if af else b), f"{r} · {'A' if af else 'B'} came first", 0 if af else 1)
               for r, (a, b, af) in enumerate(pairs, 1)]
    _outro(c, ui, OUTRO, content_end, entries, "how many did you get right? 👇", kicker)
    comp = ed.finish()
    comp.qa_marks = c.marks
    comp.qa_plan = {"units_per_round": k, "rounds": n, "unit": round(beat.period, 3)}

    answers = "".join("A" if af else "B" for _, _, af in pairs)
    if look.theme:
        v = look.theme["video"]("which_first", comp, n, [it for a, b, _ in pairs for it in (a, b)], answers=answers)
        v.format = f"edit_which_first_{look.series}"
        return _post(v, comp.music or {})
    ep = spec["episode"]
    body = "\n".join(f"{num(i)} {items[rd['a']]['name']} 🆚 {items[rd['b']]['name']}" for i, rd in enumerate(rounds, 1))
    example = next(e[:n] for e in ("ABBAB", "BABBA", "AABAB") if e[:n] != answers)
    tags = Q._tags("whichcamefirst", "ogfortnite")
    v = Video("edit_which_first", comp, title=f"Which Came First? — Fortnite Quiz #{ep}",
              yt_title=f"Which Fortnite Skin Came First? Quiz #{ep} #shorts",
              caption=_caption(f"⏳ WHICH CAME FIRST? — Fortnite Quiz #{ep}\n"
                               f"{n} rounds. Which skin is older, A or B? 👇",
                               body, f"Comment your answers in order, like {example}", tags),
              hashtags=tags)
    return _post(v, comp.music or {})


# ------------------------------------------------------------------ throwback

def _tb_plan(beat, n: int) -> dict | None:
    """Units per part: every cosmetic the same whole number of bars, about 6 s
    each, the content between MIN_CONTENT and MAX_CONTENT."""
    u, per = beat.unit, beat.period
    best = None
    for k in (8, 12, 16, 20):
        for (hook, build, outro), pen in TB_SHAPES:
            total = hook + n * k + build + outro
            if not MIN_CONTENT <= u(total) <= MAX_CONTENT:
                continue
            if hook * per < 3.0 or outro * per < 5.0 or build * per < 1.6:
                continue
            score = abs(k * per - 6.0) + pen + (.4 if build * per < 2.0 else 0)
            if best is None or score < best[0]:
                best = (score, dict(k=k, hook=hook, build=build, outro=outro, total=total))
    return best[1] if best else None


def _throwback(spec: dict, items: dict, ctx, look: Look):
    group = [items[i] for i in spec["items"] if ctx.art(items[i])][:8]
    if len(group) < 6:
        return None
    n = len(group)
    gear = spec.get("edition") == "gear"
    beat = ED.music_for(ctx.seed, "hype", day=ctx.day, salt="quiz_throwback")
    plan = _tb_plan(beat, n)
    if not plan:
        return None
    u = beat.unit
    K = plan["k"]
    content_end = u(plan["total"])
    c = Cut(ctx, beat, content_end, look)
    ed, cam, rnd = c.ed, c.cam, c.rnd
    seasonal = bool(look.s)

    if seasonal:
        event = "fortnitemares" if look.series == "fortnitemares" else group[0]["wf_event"].lower()
        title_words = f"{event} throwback {look.emoji}"         # the years are big beside it
        big = spec.get("fm_span", "")                            # "2017–2018"
        kicker = (f"throwback · day {spec['episode']} of {spec.get('of', 31)}"
                  + (f" · part {spec['part']}" if spec.get("part") else ""))
    else:
        label = spec["season"]                                   # "Chapter 1 · Season 5"
        title_words = f"{_season(label).replace(' · ', ' ')} {'gear' if gear else 'skins'} 📼"
        big = _short_season(label)
        kicker = "fortnite throwback"

    def year_of(it):
        return str(it.get("fm_year") or it.get("wf_year") or "")

    def event_of(it):
        if look.series == "fortnitemares":
            return "fortnitemares 🎃"
        if look.series == "winterfest":
            return f"{it['wf_event'].lower()} ❄️"
        return _season(spec["season"])

    def name_line(text: str, start: float) -> tuple:
        one = 800 / max(1, len(text) * .56)
        if one >= 52 or " " not in text.strip():
            size, lines = max(38.0, min(76.0, one)), 1
        else:
            size, lines = max(38.0, min(62.0, 800 / ((len(text) / 2 + 2) * .56))), 2
        y = NAME_FOOT - lines * size * 1.3
        return y, ED.caption(text, MID, y, size, start, width=820, weight=800, rot=rnd.choice([-2, -1, 1, 2]),
                             lh=1.3, extra="white-space:nowrap" if lines == 1 else "")

    def slot(lines: list, times: list, foot: float) -> str:
        html = ""
        for i, t in enumerate(times):
            text, style = lines[i % len(lines)]
            end = times[i + 1] if i + 1 < len(times) else None
            size = SLOT_F if style == "dark" else 50
            html += ED.caption(text, MID, foot - size * 1.36, size, t, end, style=style, width=820,
                               weight=700 if style == "dark" else 800,
                               rot=0 if style == "dark" else rnd.choice([-3, -2, 2, 3]))
            ed.cue(t, "pop2")
            cam.punch(t, .025, .25)
        return html

    # ------------------------------------------------------------ cover
    t1 = u(plan["hook"])
    t_hook2 = u(plan["hook"] // 2)
    groups = _groups(title_words)
    thtml, tsize, title_lines = _title(groups, 940, 80, 46)
    over = ED.caption(kicker, TOP_R, 470, 34, -1, style="dark", align="right", width=560, weight=700)
    if big:
        bsize = min(150.0, 560 / max(1.0, .62 * len(big)))
        over += ED.outline(big, YEAR_R, 312, bsize, -1)
    over += ED.caption(thtml, 540, 532, tsize, -1, width=980, weight=900, rot=-1.5, raw=True)
    lead = group[:2]
    cy = 532 + title_lines * tsize * 1.36 + 26
    chh = 1290 - cy
    cw = min(390, chh * .76)
    tiles, first, first_it = "", "", None
    for i, (it, (x, rot)) in enumerate(zip(lead, ((480 - 20 - cw, -3), (500, 3)))):
        iid, html = c.tile(it, x, cy, cw, chh, i, extra=f"transform:rotate({rot}deg)")
        if not first:
            first, first_it = iid, it
        tiles += html
        over += _name_on_tile(it["name"], x + cw / 2, cy + chh - 20, -1, rot, width=cw)
    ed.scene(0, t1, ED.canvas(first, look.colors(first_it, 0), 1.0, .55) + tiles)
    over += ED.caption(f"{n} {'gear' if gear else 'skins' if not seasonal else 'cosmetics'} 👀", MID, 1318, 42, -1,
                       t_hook2 - FRAME, style="dark", width=820, weight=800)
    over += ED.caption("how many do you remember? 👀", MID, 1314, 50, t_hook2, width=820, weight=800, rot=2)
    ed.over(0, t1, over)
    cam.push(0, t1, 1.0, 1.05, 480, 1030)
    cam.punch(t_hook2, .06)
    ed.cue(t_hook2, "impact")
    ed.cue(t_hook2, "pop2")
    ui = plan["hook"]

    # ------------------------------------------------------------ the cosmetics
    reacts = ["remember this one? 👀", "who had this one? 🙋", "still in your locker? 👀", "be honest, did you own it? 👀"]
    rnd.shuffle(reacts)
    for j, it in enumerate(group):
        last = j == n - 1
        if last:
            kb = plan["build"]
            t_pre, t_hit = u(ui), u(ui + kb)
            _, sil = c.tile(it, TB_X, TB_Y, TB_W, TB_H, j, fig_style=SILHOUETTE)
            ed.scene(t_pre, t_hit, ED.canvas("", ("#2a2a33", "#07070a"), 1.0, .2) + sil)
            ed.over(t_pre, t_hit, ED.caption("and the last one… 🥁", TOP_R, 262, 80, t_pre + .03, style="out",
                                             align="right", width=620, weight=900, lh=1.1))
            ed.cue(t_pre, "glitch")
            cam.flash(t_pre, .35, .12)
            cam.push(t_pre, t_hit, 1.0, 1.1, TB_CX, 900)
            ed.cue(t_hit - 2.0, "riser")
            c.marks.append((t_pre, "build"))
            ui += kb
        s0 = ui
        start, end = u(s0), u(s0 + K)
        iid, main = c.tile(it, TB_X, TB_Y, TB_W, TB_H, j)
        ed.scene(start, end, ED.canvas(iid, look.colors(it, j), 1.25, .45) + main)
        cam.push(start, end, 1.0, 1.05, TB_CX, 920)
        pulses = [u(s0 + b) for b in range(4, K, 4)]
        head = year_of(it) if seasonal else big
        over = ""
        if head:
            hs = min(YEAR_F, 580 / max(1.0, .62 * len(head)))
            over += ED.outline(head, YEAR_R, YEAR_Y + (YEAR_F - hs) * .6, hs, start, lime=last, width=640,
                               pulses=tuple(pulses))
        over += ED.caption(event_of(it), TOP_R, DATE_Y, 36, start, style="dark", align="right", width=560, weight=700)
        ny, name = name_line(it["name"], u(s0 + 1))
        over += name
        ed.cue(u(s0 + 1), "pop2")
        if seasonal:
            facts = [(_debut(it), "dark"), (_kind(it), "dark")]
        else:
            facts = [(_kind(it), "dark"), (reacts[j % len(reacts)], "box")]
        times = [u(s0 + b) for b in ({8: [2, 5]}.get(K, list(range(4, K, 4))))]
        over += slot(facts, times, ny - 16)
        if last:
            ed.cue(start, "boom")
            cam.shake(start, 30, .5, 2)
            cam.punch(start, .12, .45)
            cam.flash(start, .9, .3)
            over += ED.emoji(look.react(0) if seasonal else "🔥", TB_X + TB_W - 60, TB_Y + 70, 140, u(s0 + 1), rot=14)
            c.marks.append((start, "drop"))
        else:
            c.cut(start)
        ed.over(start, end, over)
        ui += K

    # ------------------------------------------------------------ outro
    entries = [(it, it["name"], i) for i, it in enumerate(group)]
    _outro(c, ui, plan["outro"], content_end, entries, "which one did you own? 👇", kicker)
    comp = ed.finish()
    comp.qa_marks = c.marks
    comp.qa_plan = dict(plan, unit=round(beat.period, 3))

    if look.theme:
        v = look.theme["video"]("throwback", comp, n, group)
        v.format = f"edit_throwback_{look.series}"
        return _post(v, comp.music or {})
    season = spec["season"]
    body = "\n".join(f"{num(i)} {it['name']} · {it['type']}" for i, it in enumerate(group, 1))
    short = season.replace(" · ", " ")
    tags = Q._tags("ogfortnite", short.replace(" ", ""), "fortnitethrowback")
    noun = "gear" if gear else "skins"
    v = Video("edit_throwback", comp, title=f"Throwback: Fortnite {short} {'Gear' if gear else 'Skins'}",
              yt_title=f"Fortnite {short} Throwback: Remember These {noun.title()}? #shorts",
              caption=_caption(f"📼 SEASON THROWBACK — Fortnite {short}\n"
                               f"{n} {noun} from this season. How many do you remember? 👇",
                               body, "Which one did you own? Tell us below", tags),
              hashtags=tags)
    return _post(v, comp.music or {})


# ------------------------------------------------------------------ dispatch

BUILDERS = {"whos_that": _picture_quiz, "zoomed_in": _picture_quiz, "guess_season": _picture_quiz,
            "which_year": _picture_quiz, "which_first": _which_first, "throwback": _throwback}


def build(spec: dict, items: dict, ctx):
    """The edit of one planned entry, or None: a format this module doesn't cut
    (odd_one_out, loadout, on_this_day), or artwork that won't load for enough
    rounds (the plan carries spares), or a track no cut of it fits."""
    fmt = spec.get("format")
    if fmt not in BUILDERS:
        return None
    series = spec.get("series") or ""
    if series and series not in SEASONS:
        return None
    if fmt == "which_year" and series != "fortnitemares":
        return None                     # its choices are Fortnitemares years
    spec = Q._clean(spec, items)
    return BUILDERS[fmt](spec, items, ctx, Look(spec, items, ctx))
