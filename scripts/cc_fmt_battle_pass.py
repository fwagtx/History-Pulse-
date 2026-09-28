"""
BATTLE PASS FLASHBACK -- every outfit from one season's Battle Pass, lit up one
display case at a time. Pure OG nostalgia, and a question everyone who played
that season can answer in the comments.

    build(ctx, chapter="1", season="4", feature=())

    0:00  hook      CHAPTER 1 · SEASON 4 / BATTLE PASS / WHICH ONE DID YOU UNLOCK?
                    -- two of the pass's outfits standing in lit display cases,
                    and USE CODE: BAD (frame 0 is the cover)
    0:03  cases     a dark room with a row of display cases, one per outfit. The
                    camera stops at each: its light flickers on, and there it is --
                    name, rarity and type, BATTLE PASS · CH1 S4, Epic's own line
                    for it, and the plate on the case: NEVER IN THE ITEM SHOP (or,
                    when it has been, how many times). A row of tiny cases in the
                    top-right corner fills up as they're revealed (the video's own
                    count, never a tier).
    ~0:46 line-up   the camera pulls back: every case lit at once, and the
                    finding -- NONE OF THESE HAS EVER BEEN IN THE ITEM SHOP (only
                    when that's true of every one; otherwise the real count)
    ~0:50 outro     WHICH ONE DID YOU UNLOCK? over the line-up, and the code, big

Which outfits: the cosmetics tagged Cosmetics.Source.Season<N>.BattlePass[.Paid|
.Free] whose own introduction field says the same season. The tags count
seasons from the start (Season4 = Chapter 1 Season 4, Season10 = Chapter 1
Season X, Season11 = Chapter 2 Season 1, ...): N is read from the data -- the
tag number that the season's cosmetics carry -- and an outfit is used only when
its tag and its introduction agree. Epic stopped tagging outfits this way after
Chapter 4 Season 1, so the episodes run from Chapter 1 Season 3 to Chapter 4
Season 1 (Chapter 1 Season 2 has only four pass outfits).

Truth rules (cc_rarity's, plus):
  - "NEVER IN THE ITEM SHOP"  <- no day in its shop history (records from
    2017-10-30, before the first Battle Pass) up to the video's day, and not in
    today's shop either. When one has been, its card says how many times
    ("IN THE ITEM SHOP ONCE", consecutive days = one time) and the blanket line
    becomes the exact count ("7 OF THESE 8 HAVE NEVER BEEN IN THE ITEM SHOP").
  - No tier numbers: the data doesn't have them. The order, the two outfits on
    the cover and the "3/8" counter are the video's own.
  - The line under each name is the cosmetic's own description, in quotes.
Fewer than five pass outfits with art: None.

Everything a viewer reads, the outfits and the code stay inside the apps' safe
box (cc_safe) at rest; the room runs to the edges.
"""

import os
import re
from collections import Counter, defaultdict

import cc_fmt_rarity as FR
import cc_rarity as R
from cc_common import OUT_DIR
from cc_formats import Ctx, Video, _caption, _hashtags, num
from cc_looks import KIT_CSS, PREP_JS, pad_to
from cc_motion import (ACCENT, RARITY, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, W, Comp, an, anton_em,
                       code_badge, disclosure, esc, style_anim)

FONTS = ("Barlow Condensed",)
LIME = ACCENT
INK = "#111"
BC = "'Barlow Condensed','Inter',sans-serif"

# ------------------------------------------------------------------ timing
HOOK = 3.0
LINEUP = 6.5                # the line-up, before the outro
OUTRO = 7.5
TARGET = 57.0               # content + outro; the end card (5.1 s) brings it past 62 s
R_MIN, R_MAX = 5.0, 8.0     # seconds per outfit
PAN = .8                    # the camera's move from one case to the next
T_ON, T_NAME, T_KIND, T_PLATE, T_DESC = .25, .5, .72, 1.2, 1.55     # after a case's slot starts
EASE_PAN = "cubic-bezier(.62,0,.32,1)"
MIN_OUTFITS, MAX_OUTFITS = 5, 12

# ------------------------------------------------------------------ the room
FLOOR_Y = 1070              # where the wall meets the floor
CX = (SAFE_LEFT + SAFE_RIGHT) / 2          # 480: the framed case's centre, beside the button rail
BAY = 760                   # one case per bay; the next case peeks in at the right edge
CASE_W, CASE_H = 600, 770   # a full-size case, its base included
CASE_TOP = 394
CAM_O = (CX, 1000)          # the slow push-in's centre (keeps the case clear of the name)
PUSH = 1.022
NAME_Y = 1184               # the name, under the case
TEXT_W = SAFE_RIGHT - SAFE_LEFT            # 840

# Rarity order for the reveal (collabs rank with legendaries).
RANK = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4, "mythic": 5,
        "marvel": 4, "dc": 4, "starwars": 4, "icon": 4, "gaminglegends": 4}
TAG = re.compile(r"^Cosmetics\.Source\.Season(\d+)\.BattlePass(?:\.(Paid|Free)(?:\.Additional)?)?$")
STD_ID = re.compile(r"^CID_(A_)?(\d+)_", re.I)

_RAW = None


# ================================================================== data

def _all_cosmetics() -> list:
    """Every cosmetic, sold or not. cc_rarity.History keeps only the ones with a
    shop history, and a Battle Pass reward usually has none -- so the full list
    is read from the same file FR.history() loads (which it has just fetched
    when it runs on a GitHub runner, so nothing downloads twice)."""
    global _RAW
    if _RAW is None:
        FR.history()
        if os.environ.get("CC_HISTORY"):
            path = os.environ["CC_HISTORY"]
        else:
            fresh = os.environ.get("GITHUB_ACTIONS") == "true"
            path = str(OUT_DIR / "_data" / ("br-fresh.json" if fresh else "br-full.json.gz"))
        _RAW = R.load(path)
    return _RAW


def _intro(raw: dict) -> tuple:
    i = raw.get("introduction") or {}
    return str(i.get("chapter") or "").upper(), str(i.get("season") or "").upper()


def _norm(chapter, season) -> tuple:
    ch, se = str(chapter).strip().upper(), str(season).strip().upper()
    if ch == "1" and se == "10":
        se = "X"                                  # Epic calls it Season X
    return ch, se


def _pass_tags(raw: dict) -> list:
    """[(season number, 'Paid'|'Free'|'')] from the cosmetic's Battle Pass tags."""
    out = []
    for t in raw.get("gameplayTags") or []:
        m = TAG.match(t)
        if m:
            out.append((int(m.group(1)), m.group(2) or ""))
    return out


def tag_season(chapter, season) -> int | None:
    """The tags' season number for this chapter/season: the one its own cosmetics
    carry most, provided most of that number's cosmetics say the same season."""
    want = _norm(chapter, season)
    carried, per_tag = Counter(), defaultdict(Counter)
    for raw in _all_cosmetics():
        tags = _pass_tags(raw)
        for n, _ in tags:
            per_tag[n][_intro(raw)] += 1
        if _intro(raw) == want:
            carried.update({n for n, _ in tags})
    if not carried:
        return None
    n = carried.most_common(1)[0][0]
    top, k = per_tag[n].most_common(1)[0]
    return n if top == want and 2 * k > sum(per_tag[n].values()) else None


def _id_order(cid: str) -> tuple:
    m = STD_ID.match(cid)
    return (1 if m.group(1) else 0, int(m.group(2))) if m else (2, 0)


def _fame(raw: dict) -> tuple:
    """For the cover's two outfits when none are named: the rarest first, then
    the ones with a progressive style, then the most styles, then the newest file."""
    variants = raw.get("variants") or []
    rarity = ((raw.get("rarity") or {}).get("value") or "").lower()
    return (RANK.get(rarity, 3), any(v.get("channel") == "Progressive" for v in variants),
            min(12, sum(len(v.get("options") or []) for v in variants)), _id_order(raw["id"]))


def pass_outfits(ctx: Ctx, chapter, season) -> tuple | None:
    """(tag number, [(item, raw, track, runs)]) -- the season's Battle Pass
    outfits, one per name, with their shop runs up to the video's day (today's
    shop included). None when the tags don't know the season."""
    ch, se = _norm(chapter, season)
    n = tag_season(ch, se)
    if n is None:
        return None
    hist = FR.history()
    today = {i.lower() for row in (ctx.shop or {}).get("items", []) for i in R.shop_ids(row)}
    by_name = {}
    for raw in _all_cosmetics():
        if (raw.get("type") or {}).get("value") != "outfit" or _intro(raw) != (ch, se):
            continue
        tracks = [kind for k, kind in _pass_tags(raw) if k == n]
        if not tracks or not raw.get("name"):
            continue
        key = raw["id"].lower()
        days = [d for d in hist.days.get(key, []) if d <= ctx.day]
        if key in today and ctx.day not in days:
            days.append(ctx.day)
        runs = R._runs(sorted(days))
        # One card per name: the game files keep a few copies (a cinematic Peely);
        # the standard CID_123_ one is the outfit people had.
        name = raw["name"].strip().lower()
        item = FR._item(raw)
        item["description"] = (raw.get("description") or "").strip()
        cand = (item, raw, "Free" if "Free" in tracks else "Paid", runs)
        old = by_name.get(name)
        if old is None or (_id_order(raw["id"])[0] < _id_order(old[1]["id"])[0]):
            by_name[name] = cand
    return n, list(by_name.values())


def _order(rows: list, feature) -> tuple:
    """(reveal order, the two cover outfits). The cover's two close the reveal
    (the first one last); the rest go by rarity, then by their place in the
    game files."""
    with_art = [r for r in rows if r[4]]
    names = [f.strip().lower() for f in (feature.split(",") if isinstance(feature, str) else feature or [])]
    picked = [next(r for r in with_art if r[0]["name"].lower() == nm) for nm in names
              if any(r[0]["name"].lower() == nm for r in with_art)]
    for r in sorted(with_art, key=lambda r: _fame(r[1]), reverse=True):
        if len(picked) >= 2:
            break
        if r not in picked:
            picked.append(r)
    picked = picked[:2]
    rest = sorted((r for r in rows if r not in picked),
                  key=lambda r: (RANK.get(r[0]["rarity"], 3), _id_order(r[1]["id"])))
    return rest + [picked[1], picked[0]], picked


# ================================================================== drawing kit

def _mix(a: str, b: str, k: float) -> str:
    """Hex colour a, k of the way to b."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * k):02x}" for x, y in zip(pa, pb))


def _tint(it: dict) -> str:
    return RARITY.get(it["rarity"], "#9AA0A6")


def _kf(name: str, pts: list, dur: float) -> str:
    """Keyframes over the whole video from [(t, css, easing to the next point)]."""
    out, last = [], -1.0
    for t, css, ease in pts:
        pct = max(0.0, min(100.0, t / dur * 100))
        if pct <= last:
            pct = last + .0005
        last = pct
        out.append(f"{pct:.4f}%{{{css}" + (f";animation-timing-function:{ease}" if ease else "") + "}")
    return f"@keyframes {name}{{{''.join(out)}}}"


def _track(name: str, dur: float) -> str:
    return f"animation:{name} {dur:.3f}s linear 0s 1 normal both;"


def _a(name: str, t: float, d: float, ease: str = "cubic-bezier(.2,.8,.2,1)", fill: str = "both") -> str:
    return an(name, t, d, ease, fill=fill)


CSS = """
.bp-room{position:absolute;inset:0;background:#0b0b0d}
.bp-wall{position:absolute;left:0;top:0;width:1080px;height:%(fy)dpx;
  background:linear-gradient(180deg,#0b0b0d 0,#131317 38%%,#141418 62%%,#0f0f12 100%%)}
.bp-slats{position:absolute;top:0;height:%(fy)dpx;opacity:.9;
  background:repeating-linear-gradient(90deg,rgba(255,255,255,.028) 0 2px,rgba(255,255,255,0) 2px 55px,
    rgba(0,0,0,.42) 55px 58px);
  -webkit-mask-image:linear-gradient(180deg,rgba(0,0,0,.35),#000 30%%,#000 80%%,rgba(0,0,0,.6))}
.bp-skirt{position:absolute;left:0;width:1080px;top:%(sk)dpx;height:24px;
  background:linear-gradient(#1b1b1f,#0c0c0e);box-shadow:0 -1px 0 rgba(255,255,255,.05),0 6px 10px rgba(0,0,0,.5)}
.bp-floor{position:absolute;left:0;top:%(fy)dpx;width:1080px;bottom:0;
  background:linear-gradient(180deg,#0d0d10 0,#111114 14%%,#0c0c0e 55%%,#08080a 100%%)}
.bp-top{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 88%% 70%% at 50%% 46%%,rgba(0,0,0,0) 58%%,rgba(0,0,0,.55) 100%%)}

.bp-case{position:absolute}
.bp-box{position:absolute;left:0;top:0;border-radius:5px;
  background:linear-gradient(180deg,#3a3b41 0,#222328 3%%,#18191c 60%%,#202126 100%%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.14),inset 0 -1px 0 rgba(0,0,0,.6),
    0 38px 46px -18px rgba(0,0,0,.85),0 12px 18px rgba(0,0,0,.45)}
.bp-in{position:absolute;overflow:hidden;background:#0e0e11}
.bp-strip{position:absolute;left:0;right:0;top:0;background:linear-gradient(180deg,#fffdf6,#f3ede0)}
.bp-fig{position:absolute}
.bp-fig img{position:absolute;left:0;top:0;width:100%%;height:100%%;object-fit:contain;object-position:50%% 100%%;
  filter:drop-shadow(0 16px 14px rgba(0,0,0,.30))}
.bp-contact{position:absolute;border-radius:50%%;
  background:radial-gradient(ellipse 50%% 50%% at 50%% 50%%,rgba(20,14,8,.5),rgba(20,14,8,0))}
.bp-off{position:absolute;inset:0;background:#08080a}
.bp-glass{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(112deg,rgba(255,255,255,0) 14%%,rgba(255,255,255,.085) 20%%,rgba(255,255,255,0) 27%%,
    rgba(255,255,255,0) 66%%,rgba(255,255,255,.045) 70%%,rgba(255,255,255,0) 74%%);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.07),inset 0 14px 20px rgba(0,0,0,.18)}
.bp-base{position:absolute;border-radius:3px;
  background:linear-gradient(180deg,#2c2d32 0,#1b1c20 10%%,#121316 100%%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 26px 30px -10px rgba(0,0,0,.9)}
.bp-slot{position:absolute;border-radius:4px;background:#0a0a0c;
  box-shadow:inset 0 3px 5px rgba(0,0,0,.85),0 1px 0 rgba(255,255,255,.07)}
.bp-plate{position:absolute;display:flex;align-items:center;justify-content:center;border-radius:4px;
  font-family:'Anton',Impact,sans-serif;text-transform:uppercase;letter-spacing:.02em;line-height:1;white-space:nowrap;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.55),inset 0 -2px 0 rgba(0,0,0,.18),0 2px 3px rgba(0,0,0,.5)}
.bp-pool{position:absolute;pointer-events:none;
  background:radial-gradient(ellipse 50%% 62%% at 50%% 0%%,rgba(255,246,232,.14),rgba(255,246,232,.05) 55%%,
    rgba(255,246,232,0) 100%%)}

.bp-bc{font-family:%(bc)s;font-weight:800;text-transform:uppercase;line-height:1;white-space:nowrap}
.bp-name{position:absolute;font-family:'Anton',Impact,sans-serif;text-transform:uppercase;color:#fff;line-height:.9;
  letter-spacing:.01em;white-space:nowrap;text-shadow:0 6px 0 rgba(0,0,0,.45)}
.bp-kind{position:absolute;display:flex;align-items:center;gap:.36em;white-space:nowrap}
.bp-kind .bp-bc{font-size:1em}
.bp-sw{display:inline-block;width:.52em;height:.52em;border-radius:.1em;box-shadow:0 0 0 2px rgba(0,0,0,.6)}
.bp-desc{position:absolute;font-family:'Inter';font-weight:500;font-style:italic;color:#c9c9d0;line-height:1.1;
  white-space:nowrap}
.bp-code{display:flex;align-items:center;gap:20px;background:%(lime)s;color:%(ink)s;border-radius:18px;
  padding:10px 32px 4px 28px;box-shadow:0 10px 0 rgba(0,0,0,.4),0 26px 40px rgba(0,0,0,.45)}
.bp-code .u{font-family:'Inter';font-weight:900;font-size:38px;line-height:1.02;letter-spacing:.1em}
.bp-code .b{font-family:'Anton',Impact,sans-serif;line-height:.92;letter-spacing:.02em}
.bp-mini{position:absolute;border-radius:3px}

@keyframes bpoff{0%%{opacity:.93}9%%{opacity:.18}15%%{opacity:.78}24%%{opacity:.06}33%%{opacity:.4}46%%{opacity:0}
  100%%{opacity:0}}
@keyframes bpfig{0%%{opacity:.3}9%%{opacity:1}100%%{opacity:1}}
@keyframes bpin{from{opacity:0}to{opacity:1}}
@keyframes bpout{from{opacity:1}to{opacity:0}}
@keyframes bprise{from{opacity:0;transform:translateY(34px)}to{opacity:1;transform:none}}
@keyframes bpdrop{0%%{opacity:0;transform:translateY(-26px) scale(1.04)}60%%{opacity:1}100%%{opacity:1;transform:none}}
@keyframes bpstamp{0%%{opacity:0;transform:scale(1.55) rotate(var(--r,0deg))}55%%{opacity:1;transform:scale(.97) rotate(var(--r,0deg))}
  100%%{opacity:1;transform:scale(1) rotate(var(--r,0deg))}}
@keyframes bpthump{0%%,100%%{transform:scale(1)}35%%{transform:scale(1.045)}}
@keyframes bpwipe{from{clip-path:inset(0 100%% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes bplit{from{background:#1a1a1f;border-color:#3b3b42}to{background:#f2ede3;border-color:#f2ede3}}
"""


def _css() -> str:
    return CSS % {"fy": FLOOR_Y, "sk": FLOOR_Y - 24, "bc": BC, "lime": LIME, "ink": INK}


def _room() -> str:
    """The dark room: a slatted wall, a skirting board and a floor. The slats are
    drawn by each scene (the shelf's move with the camera)."""
    return ('<div class="full bp-room" data-safe="ignore"><div class="bp-wall"></div><div class="bp-floor"></div>'
            '<div class="bp-skirt"></div></div>')


def _slats(x: float, w: float) -> str:
    return f'<div class="bp-slats" data-safe="ignore" style="left:{x:.0f}px;width:{w:.0f}px"></div>'


def _code_plate(bad: int = 132) -> str:
    """USE CODE: BAD on the channel's lime ("USE CODE:" 38 px, BAD >= 110 px)."""
    return (f'<div class="bp-code" data-safe="key" data-name="code"><div class="u">USE<br>CODE:</div>'
            f'<div class="b" style="font-size:{bad}px">BAD</div></div>')


def _plate_text(times: int) -> str:
    if times == 0:
        return "NEVER IN THE ITEM SHOP"
    return "IN THE ITEM SHOP ONCE" if times == 1 else f"IN THE ITEM SHOP {times}×"


def _case(uid: str, w: int, h: int, it: dict, uri: str, t_on: float | None, plate: str = "",
          plate_lime: bool = True, t_plate: float | None = None, t_plate_out: float | None = None,
          plate_font: float = 0, pool: bool = True) -> str:
    """A display case, w x h with its base, drawn from its top-left corner:
    a dark metal frame, a lit box inside (back panel, walls, ceiling light, floor,
    tinted a little by the outfit's rarity), the outfit standing in it, glass in
    front, and a base with a plate slot. t_on: when its light flickers on (None:
    lit from the start). `plate`: words on the base's plate (stamped in at
    t_plate, gone at t_plate_out)."""
    base_h = round(h * .096)
    box_h = h - base_h
    fr = max(6, round(w * .024))
    iw, ih = w - 2 * fr, box_h - fr
    si, ti, fd = round(iw * .062), round(ih * .042), round(ih * .19)
    bx0, by0, bx1, by1 = si, ti, iw - si, ih - fd
    tint = _tint(it)

    def m(c, k):
        return _mix(c, tint, k)
    svg = (f'<svg class="abs" style="left:0;top:0" width="{iw}" height="{ih}" viewBox="0 0 {iw} {ih}"><defs>'
           f'<radialGradient id="b{uid}" cx=".5" cy=".32" r=".82">'
           f'<stop offset="0" stop-color="{m("#fffbf4", .09)}"/><stop offset=".5" stop-color="{m("#ede7dc", .15)}"/>'
           f'<stop offset="1" stop-color="{m("#aaa396", .24)}"/></radialGradient>'
           f'<linearGradient id="c{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{m("#f4f0e8", .06)}"/>'
           f'<stop offset="1" stop-color="{m("#cdc7ba", .12)}"/></linearGradient>'
           f'<linearGradient id="l{uid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{m("#8c867a", .16)}"/>'
           f'<stop offset="1" stop-color="{m("#c9c2b5", .14)}"/></linearGradient>'
           f'<linearGradient id="r{uid}" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="{m("#827c71", .16)}"/>'
           f'<stop offset="1" stop-color="{m("#bfb8ab", .14)}"/></linearGradient>'
           f'<linearGradient id="f{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{m("#bdb6a9", .12)}"/>'
           f'<stop offset="1" stop-color="{m("#ddd7cb", .08)}"/></linearGradient>'
           f'<linearGradient id="v{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/>'
           f'<stop offset=".62" stop-color="#000" stop-opacity=".04"/><stop offset="1" stop-color="#000" stop-opacity=".2"/>'
           f'</linearGradient></defs>'
           f'<rect x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" fill="url(#b{uid})"/>'
           f'<rect x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" fill="url(#v{uid})"/>'
           f'<polygon points="0,0 {iw},0 {bx1},{by0} {bx0},{by0}" fill="url(#c{uid})"/>'
           f'<polygon points="0,0 {bx0},{by0} {bx0},{by1} 0,{ih}" fill="url(#l{uid})"/>'
           f'<polygon points="{iw},0 {bx1},{by0} {bx1},{by1} {iw},{ih}" fill="url(#r{uid})"/>'
           f'<polygon points="{bx0},{by1} {bx1},{by1} {iw},{ih} 0,{ih}" fill="url(#f{uid})"/>'
           f'<path d="M{bx0},{by0} V{by1} H{bx1} V{by0} M0,0 L{bx0},{by0} M{iw},0 L{bx1},{by0} M0,{ih} L{bx0},{by1} '
           f'M{iw},{ih} L{bx1},{by1}" fill="none" stroke="rgba(40,32,24,.16)" stroke-width="1.4"/></svg>')
    # The outfit stands on the case floor, a little in front of the back panel.
    feet = ih - round(fd * .38)
    fh = round((feet - ti * .5) * .95)
    fw = iw - 2 * max(6, round(si * .45))
    art = (f'<img data-trim="figure" data-name="{esc(it["name"])}" src="{uri}">' if uri else _placeholder(fw, fh))
    fig_anim = style_anim(_a("bpfig", t_on, .55, "linear")) if t_on is not None else ""
    off = (f'<div class="bp-off" data-safe="ignore" style="{style_anim(_a("bpoff", t_on, .55, "linear"))}"></div>'
           if t_on is not None else "")
    inner = (svg
             + f'<div class="bp-strip" style="height:{max(3, round(ih * .009))}px"></div>'
             + f'<div class="bp-contact" style="left:{iw / 2 - fw * .3:.0f}px;top:{feet - 11:.0f}px;width:{fw * .6:.0f}px;'
               f'height:24px"></div>'
             + f'<div class="bp-fig" style="left:{(iw - fw) / 2:.0f}px;top:{feet - fh:.0f}px;width:{fw}px;height:{fh}px;'
               f'{fig_anim}">{art}</div>'
             + off + '<div class="bp-glass"></div>')
    base_w = w + 8
    slot_w, slot_h = round(w * .76), round(base_h * .64)
    slot_x, slot_y = (base_w - slot_w) / 2, (base_h - slot_h) / 2 + 1
    plate_html = ""
    if plate:
        fs = plate_font or round(slot_h * .74)
        fg, bg = (INK, LIME) if plate_lime else ("#1b1b1f", "#d7d7dc")
        vis = style_anim(_a("bpstamp", t_plate, .42, "cubic-bezier(.3,1.4,.5,1)"),
                         _a("bpout", t_plate_out, .2, "linear", "forwards") if t_plate_out else "") \
            if t_plate is not None else ""
        plate_html = (f'<div class="bp-plate" style="left:{slot_x:.0f}px;top:{slot_y:.0f}px;width:{slot_w}px;'
                      f'height:{slot_h}px;font-size:{fs:.0f}px;color:{fg};background:{bg};--r:-1.2deg;{vis}">'
                      f'<span style="margin-top:.06em">{esc(plate)}</span></div>')
    pool_html = ""
    if pool:
        pv = style_anim(_a("bpin", t_on + .1, .5, "linear")) if t_on is not None else ""
        pool_html = (f'<div class="bp-pool" data-safe="ignore" style="left:{-w * .2:.0f}px;top:{h:.0f}px;'
                     f'width:{w * 1.4:.0f}px;height:{h * .42:.0f}px;{pv}"></div>')
    return (pool_html
            + f'<div class="bp-box" style="width:{w}px;height:{box_h}px"></div>'
            + f'<div class="bp-in" style="left:{fr}px;top:{fr}px;width:{iw}px;height:{ih}px">{inner}</div>'
            + f'<div class="bp-base" style="left:-4px;top:{box_h}px;width:{base_w}px;height:{base_h}px">'
              f'<div class="bp-slot" style="left:{slot_x:.0f}px;top:{slot_y:.0f}px;width:{slot_w}px;height:{slot_h}px">'
              f'</div>{plate_html}</div>')


def _placeholder(w: float, h: float) -> str:
    """No picture of this one: an outline where it would stand."""
    return (f'<svg class="abs" style="left:0;top:0" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 100 200" '
            f'preserveAspectRatio="xMidYMax meet"><g fill="none" stroke="rgba(40,34,28,.35)" stroke-width="1.6" '
            f'stroke-dasharray="4 3"><circle cx="50" cy="30" r="13"/><path d="M28 62 Q50 50 72 62 L76 118 L64 118 '
            f'L62 196 L53 196 L50 132 L47 196 L38 196 L36 118 L24 118 Z"/></g></svg>')


def _case_at(x: float, y: float, w: int, h: int, body: str, extra: str = "") -> str:
    return f'<div class="bp-case" style="left:{x:.0f}px;top:{y:.0f}px;width:{w}px;height:{h}px;{extra}">{body}</div>'


# ================================================================== text helpers

def _anton_size(text: str, width: float, big: float, small: float) -> float:
    return max(small, min(big, width / max(anton_em(text), .1)))


def _bc(text: str, size: float, color: str = "#fff", spacing: str = ".06em", fit: float = 0, extra: str = "") -> str:
    fit_attr = f' data-fit="{fit:.0f}"' if fit else ""
    return (f'<div class="bp-bc"{fit_attr} style="display:inline-block;font-size:{size:.0f}px;color:{color};'
            f'letter-spacing:{spacing};{extra}">{text}</div>')


def _at(x: float, y: float, inner: str, anim: str = "", align: str = "left", extra: str = "") -> str:
    if align == "right":
        pos = f"right:{W - x:.0f}px;text-align:right;"
    elif align == "center":
        pos = f"left:{x - W:.0f}px;width:{2 * W}px;text-align:center;"
    else:
        pos = f"left:{x:.0f}px;"
    return f'<div class="abs" style="{pos}top:{y:.0f}px;{anim}{extra}">{inner}</div>'


# ================================================================== the builder

def build(ctx: Ctx, chapter="1", season="4", feature=()) -> Video | None:
    got = pass_outfits(ctx, chapter, season)
    if got is None:
        return None
    _, found = got
    ch, se = _norm(chapter, season)
    rows = [(it, raw, track, runs, ctx.art(it)) for it, raw, track, runs in found]
    rows = [(it, raw, track, len(runs), uri, runs) for it, raw, track, runs, uri in rows]
    if sum(1 for r in rows if r[4]) < MIN_OUTFITS or len(rows) > MAX_OUTFITS:
        return None
    order, cover = _order(rows, feature)
    n = len(order)
    never = sum(1 for r in order if r[3] == 0)
    short = f"CH{ch} S{se}"

    per = max(R_MIN, min(R_MAX, (TARGET - HOOK - LINEUP - OUTRO) / n))
    t_line = HOOK + n * per
    content_end = t_line + LINEUP
    total = pad_to(content_end, minimum=TARGET, outro=OUTRO)
    comp = Comp(total)
    comp.use_fonts(*FONTS)
    comp.css(_css())
    comp.css(KIT_CSS)
    comp.add(_room())

    _hook(comp, ctx, ch, se, cover, n)
    _shelf(comp, ctx, ch, se, short, order, per, t_line)
    _lineup(comp, ctx, ch, se, order, never, t_line, content_end)
    _outro(comp, content_end, total)

    comp.add('<div class="full bp-top" data-safe="ignore" style="z-index:44"></div>'
             '<div class="grain" data-safe="ignore" style="z-index:45"></div>')
    comp.add(PREP_JS)
    comp.add(code_badge(0))
    comp.add(disclosure())

    # ---------------------------------------------------------------- words
    ask = "Which one did you unlock?"
    if never == n:
        claim = "none of them has ever been in the Item Shop"
    elif never:
        claim = f"{never} of the {n} have never been in the Item Shop"
    else:
        claim = "and how often each has been in the Item Shop"

    def line(k, r):
        it, raw, track, times, uri, runs = r
        shop = ("never in the Item Shop" if times == 0 else
                f"in the Item Shop {'once' if times == 1 else f'{times} times'} (last {runs[-1][1]:%b %-d, %Y})")
        free = " · free pass" if track == "Free" else ""
        return f"{num(k)} {it['name']} · {it['rarity_label'] or it['rarity'].title()} {it['type']}{free} · {shop}"
    body = "\n".join(line(k, r) for k, r in enumerate(order, 1))
    title_s = f"Chapter {ch} Season {se.title() if se.isalpha() else se}"
    tags = _hashtags("battlepass", f"chapter{ch}season{se.lower()}", "ogfortnite")
    return Video(
        f"battle_pass_c{ch}s{se.lower()}", comp,
        title=f"Every {title_s} Battle Pass Skin — Which Did You Unlock?",
        yt_title=f"Every Fortnite {title_s} Battle Pass Skin: Which One Did You Unlock? #shorts",
        caption=_caption(f"🎟️ EVERY {title_s.upper()} BATTLE PASS SKIN — {claim} (as of {ctx.day_label})\n"
                         f"All {n} outfits from its Battle Pass, checked against the Item Shop's own history 👇",
                         body, ask, tags),
        hashtags=tags)


# ------------------------------------------------------------------ 0:00 hook

def _hook(comp: Comp, ctx: Ctx, ch: str, se: str, cover: list, n: int):
    """Frame 0 is the cover: what it is, two outfits in lit cases, the code."""
    t_end = HOOK
    inner = _slats(0, W)
    # Two tall cases side by side, beside the button rail (x 60..900).
    cw, chh, top = 404, 612, 672
    xs = (SAFE_LEFT + 2, SAFE_RIGHT - 2 - cw)
    for k, (r, x) in enumerate(zip(cover, xs)):
        it, uri = r[0], r[4]
        body = _case(f"h{k}", cw, chh, it, uri, None, plate=it["name"], plate_lime=False,
                     plate_font=_anton_size(it["name"], cw * .76 - 30, 34, 20))
        inner += _case_at(x, top, cw, chh, body)
    # Title block: kicker, BATTLE PASS, the question.
    kick = f"CHAPTER {ch} · SEASON {se}"
    inner += _at(SAFE_LEFT + 2, 390, _bc(kick, 58, LIME, ".07em"))
    size = _anton_size("BATTLE PASS", 956, 178, 120)
    inner += (f'<div class="abs" style="left:{SAFE_LEFT - 4}px;top:450px;transform-origin:30% 50%;'
              f'{style_anim(_a("bpthump", .2, .42, "ease-out", "none"))}">'
              f'<div class="bp-name" style="position:relative;font-size:{size:.0f}px">BATTLE PASS</div></div>')
    inner += _at(SAFE_LEFT + 2, 450 + size * .9 + 14, _bc("WHICH ONE DID YOU UNLOCK?", 50, "#fff", ".04em"),
                 anim=style_anim(_a("bpthump", .9, .4, "ease-out", "none")))
    # The code, big, across the cases' bases; it flies to the corner badge as the hook ends.
    fly = comp.uid("bpfly")
    comp.css(f"@keyframes {fly}{{0%{{transform:none;opacity:1}}100%{{transform:translate(-190px,-1050px) "
             f"scale(.36);opacity:0}}}}")
    inner += (f'<div class="abs" style="left:0;width:{2 * CX:.0f}px;top:1236px;display:flex;justify-content:center;'
              f'{style_anim(_a(fly, t_end - .62, .5, "cubic-bezier(.6,0,.4,1)"))}">'
              f'<div style="transform:rotate(-2deg)"><div style="{style_anim(_a("bpthump", 1.45, .45, "ease-out", "none"))}">'
              f'{_code_plate(118)}</div></div></div>')
    comp.scene(0, t_end, inner, fade_in=.01, fade_out=.35, z=2)
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.9, "pop"); comp.cue(1.45, "pop")
    comp.cue(t_end - .62, "whoosh")


# ------------------------------------------------------------------ 0:03 the shelf

def _shelf(comp: Comp, ctx: Ctx, ch: str, se: str, short: str, order: list, per: float, t_line: float):
    """The row of cases and the camera moving along it, one stop per outfit; the
    words for each; the counter of tiny cases top right."""
    n = len(order)
    dur = comp.duration
    starts = [HOOK + k * per for k in range(n)]
    # Camera: hold on case k, pushing in a little, then move to the next; after
    # the last one, pull back as the line-up fades in.
    pan = comp.uid("bppan")
    pts = [(0, "transform:translateX(0px)", None)]
    for k, t0 in enumerate(starts[:-1]):
        pts.append((t0 + per - PAN, f"transform:translateX({-k * BAY}px)", EASE_PAN))
        pts.append((t0 + per, f"transform:translateX({-(k + 1) * BAY}px)", None))
    pts.append((dur, f"transform:translateX({-(n - 1) * BAY}px)", None))
    comp.css(_kf(pan, pts, dur))
    cam = comp.uid("bpcam")
    pts = [(0, "transform:scale(1)", None)]
    for k, t0 in enumerate(starts):
        pts.append((t0, "transform:scale(1)", "cubic-bezier(.35,0,.65,1)"))
        if k < n - 1:
            pts.append((t0 + per - PAN, f"transform:scale({PUSH})", EASE_PAN))
        else:
            pts.append((t_line - .55, f"transform:scale({PUSH})", "cubic-bezier(.5,0,.3,1)"))
            pts.append((t_line + .35, "transform:scale(.62)", None))
    pts.append((dur, "transform:scale(.62)", None))
    comp.css(_kf(cam, pts, dur))

    cases = _slats(-400, n * BAY + 1600)
    x0 = CX - CASE_W / 2
    for k, (r, t0) in enumerate(zip(order, starts)):
        it, raw, track, times, uri, runs = r
        t_out = t0 + per - PAN - .1 if k < n - 1 else t_line - .5
        body = _case(f"s{k}", CASE_W, CASE_H, it, uri, t0 + T_ON, plate=_plate_text(times), plate_lime=times == 0,
                     t_plate=t0 + T_PLATE, t_plate_out=t_out, plate_font=42 if times == 0 else 40)
        cases += _case_at(x0 + k * BAY, CASE_TOP, CASE_W, CASE_H, body)
        comp.cue(t0 + T_ON, "click"); comp.cue(t0 + T_NAME, "slam"); comp.cue(t0 + T_PLATE, "stamp")
        if k < n - 1:
            comp.cue(t0 + per - PAN, "whoosh")
    inner = (f'<div class="full" style="transform-origin:{CAM_O[0]:.0f}px {CAM_O[1]:.0f}px;{_track(cam, dur)}">'
             f'<div class="abs" style="left:0;top:0;width:{W}px;height:1920px;{_track(pan, dur)}">{cases}</div></div>')
    comp.scene(HOOK - .35, t_line + .45, inner, fade_in=.35, fade_out=.3, z=1)

    # The words for each outfit, in screen space under its case.
    for k, (r, t0) in enumerate(zip(order, starts)):
        it = r[0]
        t_end = t0 + per - PAN if k < n - 1 else t_line - .45
        comp.scene(t0, t_end + .05, _words(it, r[2], short, t0), fade_in=.01, fade_out=.28, z=3)

    # Top right: the season, and a tiny case for each outfit that lights up in turn.
    comp.scene(HOOK - .1, t_line + .1, _counter(ch, se, n, starts), fade_in=.3, fade_out=.3, z=4)


def _words(it: dict, track: str, short: str, t0: float) -> str:
    name = it["name"].upper()
    size = _anton_size(name, TEXT_W - 12, 112, 58)
    out = (f'<div class="bp-name" style="left:{SAFE_LEFT - 2}px;top:{NAME_Y}px;font-size:{size:.0f}px;'
           f'{style_anim(_a("bprise", t0 + T_NAME, .45))}">{esc(name)}</div>')
    y = NAME_Y + size * .9 + 16
    kind = f'{(it.get("rarity_label") or it["rarity"]).upper()} {it["type"].upper()}'
    src = f"BATTLE PASS · {short}" + (" · FREE" if track == "Free" else "")
    row = (f'<span class="bp-sw" style="background:{_tint(it)}"></span>'
           f'<span class="bp-bc" style="color:#fff;letter-spacing:.05em">{esc(kind)}</span>'
           f'<span class="bp-bc" style="color:#6d6d76">·</span>'
           f'<span class="bp-bc" style="color:#b7b7c0;letter-spacing:.05em">{esc(src)}</span>')
    out += (f'<div class="bp-kind" data-fit="{TEXT_W - 8}" style="left:{SAFE_LEFT + 2}px;top:{y:.0f}px;'
            f'font-size:38px;{style_anim(_a("bprise", t0 + T_KIND, .45))}">{row}</div>')
    desc = (it.get("description") or "").strip()
    if desc and len(desc) <= 70:
        out += (f'<div class="bp-desc" data-fit="{TEXT_W - 8}" style="left:{SAFE_LEFT + 2}px;top:{y + 54:.0f}px;'
                f'font-size:31px;{style_anim(_a("bpin", t0 + T_DESC, .5, "linear"))}">“{esc(desc)}”</div>')
    return out


def _counter(ch: str, se: str, n: int, starts: list) -> str:
    """CHAPTER 1 · SEASON 4 and a row of tiny cases, top right (clear of the corner badge)."""
    right = SAFE_RIGHT_TOP - 4
    out = _at(right, 250, _bc(f"CHAPTER {ch} · SEASON {se}", 34, LIME, ".08em"), align="right")
    out += _at(right, 290, _bc("BATTLE PASS", 34, "#fff", ".08em"), align="right")
    mw, mh, gap = 22, 34, 9
    row_w = n * mw + (n - 1) * gap
    x = right - row_w
    for k, t0 in enumerate(starts):
        out += (f'<div class="bp-mini" style="left:{x + k * (mw + gap):.0f}px;top:340px;width:{mw}px;height:{mh}px;'
                f'border:2px solid #3b3b42;background:#1a1a1f;box-shadow:0 3px 6px rgba(0,0,0,.5);'
                f'{style_anim(_a("bplit", t0 + T_ON, .2, "linear", "forwards"))}"></div>')
    # which one we're on: a lime bar under it
    return out


# ------------------------------------------------------------------ the line-up

def _grid(n: int) -> tuple:
    rows = 2 if n <= 10 else 3
    cols = -(-n // rows)
    return rows, cols


def _lineup(comp: Comp, ctx: Ctx, ch: str, se: str, order: list, never: int, t_line: float, end: float):
    n = len(order)
    rows, cols = _grid(n)
    top, bottom = 668, SAFE_BOTTOM - 8
    cell_w = TEXT_W / cols
    row_h = (bottom - top) / rows
    label_h = 64
    s = min(cell_w * .9 / CASE_W, (row_h - label_h) / CASE_H)
    cw, chh = CASE_W * s, CASE_H * s
    inner = _slats(0, W)
    grid = ""
    for k, r in enumerate(order):
        it, uri, times = r[0], r[4], r[3]
        row, col = divmod(k, cols)
        in_row = min(cols, n - row * cols)
        x = SAFE_LEFT + (TEXT_W - in_row * cell_w) / 2 + col * cell_w + (cell_w - cw) / 2
        y = top + row * row_h
        t_on = t_line + .35 + k * .11
        body = _case(f"l{k}", CASE_W, CASE_H, it, uri, t_on, plate=" ", plate_lime=times == 0, t_plate=t_on + .1,
                     pool=False)
        grid += (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{CASE_W}px;height:{CASE_H}px;'
                 f'transform:scale({s:.4f});transform-origin:0 0">{body}</div>')
        name = it["name"].upper()
        fs = min(30, (cell_w - 10) / max(anton_em(name) * .92, .1))
        tag = ("" if times == 0 else
               f'<div class="bp-bc" style="font-size:22px;color:#d7d7dc;letter-spacing:.06em;margin-top:4px">'
               f'IN THE SHOP {times}×</div>')
        grid += (f'<div class="abs" style="left:{x + cw / 2 - cell_w / 2:.0f}px;width:{cell_w:.0f}px;top:{y + chh + 10:.0f}px;'
                 f'text-align:center;{style_anim(_a("bpin", t_on + .15, .3, "linear"))}">'
                 f'<div class="bp-bc" data-fit="{cell_w - 6:.0f}" style="display:inline-block;font-size:{fs:.0f}px;'
                 f'color:#fff;letter-spacing:.03em">{esc(name)}</div>{tag}</div>')
        comp.cue(t_on, "tick")
    # The finding.
    if never == n:
        head = ["NONE OF THESE HAS EVER", "BEEN IN THE ITEM SHOP"]
    elif never:
        head = [f"{never} OF THESE {n} HAVE NEVER", "BEEN IN THE ITEM SHOP"]
    else:
        head = [f"ALL {n} HAVE BEEN", "IN THE ITEM SHOP"]
    hs = min(_anton_size(head[0], 950, 96, 60), _anton_size(head[1], 950, 96, 60))
    t_h = t_line + .5 + n * .11
    kick = f"EVERY CHAPTER {ch} · SEASON {se} BATTLE PASS OUTFIT"
    words = (_at(SAFE_LEFT + 2, 398, _bc(kick, 34, LIME, ".07em", fit=950), anim=style_anim(_a("bpin", t_line + .2, .4)))
             + f'<div class="abs" style="left:{SAFE_LEFT - 2}px;top:448px;{style_anim(_a("bprise", t_h, .5))}">'
             + "".join(f'<div class="bp-name" style="position:relative;font-size:{hs:.0f}px;margin-bottom:6px">'
                       f'{esc(h)}</div>' for h in head) + '</div>'
             + _at(SAFE_LEFT + 2, 448 + 2 * (hs * .9 + 6) + 10,
                   _bc(f"AS OF {ctx.day_label.upper()} · FROM THE ITEM SHOP'S OWN HISTORY", 26, "#9a9aa3", ".08em",
                       fit=950), anim=style_anim(_a("bpin", t_h + .3, .4))))
    comp.cue(t_line + .05, "whoosh"); comp.cue(t_h, "reveal"); comp.cue(t_h + .05, "slam")
    # In the outro the line-up steps back to make room for the ask and the code.
    shrink = comp.uid("bpshrink")
    comp.css(f"@keyframes {shrink}{{from{{transform:none}}to{{transform:translateY(-8px) scale(.74)}}}}")
    inner += (f'<div class="full" style="transform-origin:{CX:.0f}px {top - 30}px;'
              f'{style_anim(_a(shrink, end + .05, .7, "cubic-bezier(.6,0,.3,1)"))}">{grid}</div>')
    inner += f'<div class="full" style="{style_anim(_a("bpout", end, .3, "linear", "forwards"))}">{words}</div>'
    comp.scene(t_line - .35, comp.duration, inner, fade_in=.4, fade_out=.01, z=2)


# ------------------------------------------------------------------ outro

def _outro(comp: Comp, start: float, end: float):
    ask = ["WHICH ONE", "DID YOU UNLOCK?"]
    size = min(_anton_size(ask[1], 940, 124, 80), 124)
    inner = (f'<div class="abs" style="left:{SAFE_LEFT - 2}px;top:392px;{style_anim(_a("bprise", start + .25, .5))}">'
             + "".join(f'<div class="bp-name" style="position:relative;font-size:{size:.0f}px;margin-bottom:4px;'
                       f'{"color:" + LIME if i else ""}">{esc(a)}</div>' for i, a in enumerate(ask)) + '</div>')
    inner += (f'<div class="abs" style="left:0;width:{2 * CX:.0f}px;top:1238px;display:flex;justify-content:center;'
              f'{style_anim(_a("bprise", start + .55, .5))}"><div style="transform:rotate(-2deg)">'
              f'<div style="{style_anim(_a("bpthump", start + 1.3, .45, "ease-out", "none"))}">{_code_plate(132)}'
              f'</div></div></div>')
    comp.scene(start, end, inner, fade_in=.2, fade_out=.01, z=3)
    comp.cue(start + .25, "slam"); comp.cue(start + .55, "pop"); comp.cue(start + 1.3, "pop")
