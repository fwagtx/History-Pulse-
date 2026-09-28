"""
RARITY TIER LIST -- one season's Item Shop skins on an S / A / B / C / D tier
board, placed by how many times each has been in the Item Shop (cc_rarity).

    build(ctx, chapter="1", season="3", count=12, thresholds="auto")

    0:00  hook     frame 0 is the thumbnail: CHAPTER 1 / SEASON 3 SKINS and
                   RARITY TIER LIST over the empty board (every tier's range on
                   its label), two of the video's skins in front of it, WHICH
                   TIER IS YOUR SKIN? and the USE CODE: BAD stamp. The stamp
                   flies into the corner badge, the skins step out, the title
                   shrinks into the header and the board grows into place.
    0:03  skins    one at a time (8-12, ~4 s each): the board dims, the skin
                   comes up big on its tile with its name, IN THE ITEM SHOP
                   N TIMES rolls up and its tier pops, then the tile flies into
                   its row and lands with a count badge. The last two are held
                   back -- WHERE WILL <NAME> LAND? -- the best known of the
                   picks, then the one sold the fewest times.
    ~0:54 board    the finished board holds for three seconds.
    ~0:57 outro    WHICH TIER IS YOURS? and the code, with the board below.

Tiers are the number of separate times a skin has been in the Item Shop, up to
the video's day (cc_rarity.History.times -- consecutive days are ONE time):
S 1-3, A 4-10, B 11-25, C 26-50, D 51 or more. When a season's counts don't
fill all five of those (newer seasons have had less time), the tiers are cut
from the season's own counts instead -- five groups as even as the counts
allow -- and the board shows those ranges; every label always carries its
range, and the line under the board says what the numbers are.

Picks: every outfit introduced in that chapter and season that has been in the
Item Shop and has art; a set whose skins were always sold together (the same
days, every time) counts once, and so does a name with variants ("Alpine Ace
(CAN)"). Up to `count`: the one sold the fewest times, then every tier's best
known skin (rarity, or a series, is the fame signal; more times in the shop
breaks ties), then the best known of the rest, at most four to a row. Fewer
than six: None.

Truth rules: cc_rarity's. On screen and in the caption only what was
computed: "in the Item Shop N times", the tier ranges, the records' last day.
Never why, never a prediction, nothing about the future of any skin, no
"rarest ever": S is simply the tier for the fewest times in the shop.

Layout: everything a viewer reads, the tiles and the code stay inside the
apps' safe box (cc_safe). The board's rows run below y 740, so the whole board
sits between x 60 and 900; the header sits right of the corner badge.
"""

import re
from collections import defaultdict

from cc_fmt_last_chance import _em
from cc_fmt_rarity import _item, _label_w, history
from cc_formats import Ctx, Video, _caption, _hashtags
from cc_looks import PREP_JS, pad_to, tex
from cc_motion import (ACCENT, BADGE_X, BADGE_Y, EASE_BACK, EASE_OUT, INK, RARITY, SAFE_LEFT, SAFE_RIGHT,
                       SAFE_RIGHT_TOP, Comp, code_badge, disclosure, esc, hexcol)

# ------------------------------------------------------------------ timing

HOOK = 3.0
HOLD = 3.0                      # the finished board, after the last tile lands
MIN_TOTAL = 57.0                # content + outro; the end card (5.1 s) takes it past 62
OUTRO = 7.5
R_MIN, R_MAX = 4.0, 5.2         # one skin
EXTRA = 1.7                     # a held-back skin: WHERE WILL <NAME> LAND? first
HELD = 2                        # how many are held back for the end
FLY = .55                       # the tile's flight into its row
T_DOCK = (1.65, 2.15)           # the hook's code stamp flies into the corner badge
T_GROW = (2.15, 2.75)           # the board grows into place, the title into the header
T_EXIT = 2.02                   # the hook's skins step out

# ------------------------------------------------------------------ tiers

TIERS = "SABCD"
FIXED = ((1, 3), (4, 10), (11, 25), (26, 50), (51, None))
TIER_COL = {"S": "#FF6B6B", "A": "#FFA24C", "B": "#FFD24A", "C": "#7FD67A", "D": "#63A4FF"}
TIER_EMOJI = {"S": "🟥", "A": "🟧", "B": "🟨", "C": "🟩", "D": "🟦"}
RANK = {"common": 1, "uncommon": 2, "rare": 3, "epic": 4, "legendary": 5, "mythic": 5, "exotic": 5}
CAP = 4                         # tiles a row takes at full size

# ------------------------------------------------------------------ layout (px)

BX0, BX1 = SAFE_LEFT, SAFE_RIGHT            # the board: 60 .. 900, beside the button rail
BY0 = 388                                   # its top, under the header
BOARD_H = 940                               # rows and the gaps between them
ROW_GAP = 10
LAB_W = 150                                 # a row's tier label
PAD = 12                                    # around the tiles in a row
TGAP = 12                                   # between tiles
AREA_W = BX1 - BX0 - LAB_W - 2 * PAD        # 666: where a row's tiles go
MID = (BX0 + BX1) / 2                       # 480
LEGEND_GAP = 16

CARD = 450                                  # a skin's tile, big, while it's being placed
CARD_X, CARD_Y = MID - CARD / 2, 452
NAME_W = BX1 - BX0 - 4                      # names are centred on the board, below y 740

HEAD_R = SAFE_RIGHT_TOP                     # the header, right of the corner badge
HEAD_KICK_Y, HEAD_TITLE_Y, HEAD_TITLE = 240, 274, 78

HOOK_SCALE, HOOK_BY = .8, 626               # the board on the thumbnail: smaller, lower
HOOK_TITLE, HOOK_TITLE_Y = 132, 478
STAMP_K, STAMP_X, STAMP_Y = 1.4, SAFE_LEFT, 292
FIG_FEET = 1402                             # the hook's two skins: (height, width box, centre x)
FIGS = ((720, 340, 522), (800, 360, SAFE_RIGHT - 182))

OUT_SCALE, OUT_TOP = .6, 818               # the board under the outro

BLANK = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

CSS = """
.tl-bg{position:absolute;inset:0;background:radial-gradient(ellipse 85% 62% at 45% 50%,#1c1c21 0%,#121215 52%,#09090a 100%)}
.tl-grain{position:absolute;inset:0;background:url('@grain@') 0 0/256px 256px repeat;opacity:.055;pointer-events:none}
.tl-panel{position:absolute;border-radius:22px;background:linear-gradient(180deg,#17171b,#111114);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 2px 4px rgba(0,0,0,.5),0 36px 70px rgba(0,0,0,.55)}
.tl-row{position:absolute;border-radius:12px;overflow:hidden;background:linear-gradient(180deg,#202026,#1a1a1f);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05),inset 0 -1px 0 rgba(0,0,0,.4)}
.tl-lab{position:absolute;left:0;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;
  justify-content:center;color:#141414;box-shadow:inset -2px 0 0 rgba(0,0,0,.18)}
.tl-lab b{display:block;font-family:'Anton',Impact,sans-serif;font-weight:400;line-height:.9;transform-origin:50% 60%}
.tl-lab i{display:block;font-style:normal;font-weight:800;letter-spacing:.02em;opacity:.8;white-space:nowrap}
.tl-face{position:relative;overflow:hidden}
.tl-fig{position:absolute;left:0;right:0;margin:0 auto;top:5%;height:170%;max-width:106%;
  object-fit:contain;object-position:50% 0}
.tl-shade{position:absolute;left:0;right:0;bottom:0;height:38%;
  background:linear-gradient(180deg,rgba(0,0,0,0),rgba(0,0,0,.34))}
.tl-rim{position:absolute;inset:0;box-shadow:inset 0 0 0 2px rgba(255,255,255,.17),inset 0 2px 0 rgba(255,255,255,.12)}
.tl-badge{position:absolute;right:-7px;bottom:-7px;background:#0c0c0e;color:#fff;border-radius:.26em;
  padding:.13em .3em .05em;line-height:.9;white-space:nowrap;border:2px solid rgba(255,255,255,.2);
  box-shadow:0 4px 10px rgba(0,0,0,.55)}
.tl-x{font-family:'Inter',sans-serif;font-weight:900;font-size:.62em;margin-left:.05em;position:relative;top:-.08em}
.tl-chip{display:inline-block;color:#121212;border-radius:14px;padding:.12em .42em .04em;
  box-shadow:0 8px 0 rgba(0,0,0,.34),0 16px 30px rgba(0,0,0,.4)}
.tl-sticker{display:inline-block;background:#fff;color:#121212;border-radius:12px;padding:.13em .4em .05em;
  box-shadow:0 9px 0 rgba(0,0,0,.36),0 20px 36px rgba(0,0,0,.4)}
.tl-code{display:inline-flex;align-items:center;background:@lime@;color:@ink@}
@keyframes tlon{from{visibility:hidden}to{visibility:visible}}
@keyframes tloff{from{visibility:visible}to{visibility:hidden}}
@keyframes tlin{from{opacity:0}to{opacity:1}}
@keyframes tlout{from{opacity:1}to{opacity:0}}
@keyframes tlrise{from{opacity:0;transform:translateY(34px)}to{opacity:1;transform:none}}
@keyframes tlcard{0%{opacity:0;transform:translateY(90px) scale(.9) rotate(2deg)}
  60%{opacity:1;transform:translateY(-6px) scale(1.01) rotate(-.4deg)}100%{opacity:1;transform:none}}
@keyframes tlsettle{0%{transform:scale(1.06)}45%{transform:scale(.975)}100%{transform:scale(1)}}
@keyframes tlpop{0%{transform:scale(0)}60%{transform:scale(1.18)}100%{transform:scale(1)}}
@keyframes tlchip{0%{opacity:0;transform:scale(1.9) rotate(-8deg)}55%{opacity:1;transform:scale(.94) rotate(-3deg)}
  100%{opacity:1;transform:scale(1) rotate(-3deg)}}
@keyframes tlthump{0%{transform:scale(1)}35%{transform:scale(1.2)}100%{transform:scale(1)}}
@keyframes tlhover{from{transform:none}to{transform:translateY(-12px) rotate(-1.2deg)}}
@keyframes tltilt{0%{transform:rotate(0)}45%{transform:rotate(-7deg)}100%{transform:rotate(0)}}
@keyframes tlslam{0%{opacity:0;transform:scale(1.7)}60%{opacity:1;transform:scale(.96)}100%{opacity:1;transform:none}}
@keyframes tlhop{0%,100%{transform:none}35%{transform:translateY(-30px) rotate(-1.5deg)}70%{transform:translateY(4px)}}
@keyframes tlboing{0%,100%{transform:scale(1)}40%{transform:scale(1.12)}70%{transform:scale(.97)}}
@keyframes tlexit{from{opacity:1;transform:none}to{opacity:0;transform:translateY(170px)}}
@keyframes tlshrink{from{opacity:1;transform:none}to{opacity:0;transform:scale(.6)}}
"""

# Once PREP_JS has cut each cosmetic out of its square (the hidden sources, one
# per skin), every picture of that skin takes the finished image: each art is
# embedded and trimmed once, however many times it's on screen.
SHARE_JS = """<script>(() => {
  const prev = window.__ready;
  window.__ready = (async () => {
    try {
      if (prev) { await prev; }
      if (document.readyState === 'loading') {
        await new Promise(r => document.addEventListener('DOMContentLoaded', r, {once: true}));
      }
      const jobs = [];
      for (const img of document.querySelectorAll('img[data-art]')) {
        const src = document.getElementById(img.dataset.art);
        if (!src) continue;
        img.src = src.src;
        if (img.decode) jobs.push(img.decode().catch(() => {}));
      }
      await Promise.all(jobs);
    } catch (e) {}
  })();
})();</script>"""


def _a(name: str, t: float, dur: float, ease: str = "linear", fill: str = "both") -> str:
    return f"{name} {dur:.3f}s {ease} {t:.3f}s 1 normal {fill}"


def _anim(*entries) -> str:
    return "animation:" + ",".join(e for e in entries if e) + ";"


def _mix(c1: str, c2: str, t: float) -> str:
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


# ------------------------------------------------------------------ data

def _junk(name: str) -> bool:
    """Placeholder entries in the cosmetics list, not skins anyone bought: a
    code name ("Set_01_OA") or the default Recruit outfits."""
    return not name or "_" in name or name.lower().startswith("recruit") or name.upper() in {"TBD", "NULL"}


def _fame(e: dict) -> tuple:
    """How well known a skin is likely to be: a series (Icon, Marvel, Star Wars...)
    or its rarity; more times in the shop breaks ties."""
    it = e["it"]
    return (6 if it["series"] else RANK.get(it["rarity"], 3), e["times"], -len(e["it"]["name"]))


def _pool(hist, ctx: Ctx, chapter: str, season: str) -> tuple:
    """(entries, skins): the season's outfits that have been in the Item Shop, one
    entry per set sold always together and per name with variants; and how many
    skins that is before merging."""
    groups, skins = {}, 0
    for key, days in hist.days.items():
        raw = hist.items[key]
        intro = raw.get("introduction") or {}
        if ((raw.get("type") or {}).get("value") != "outfit" or str(intro.get("chapter")) != chapter
                or str(intro.get("season")) != season or _junk(raw.get("name") or "")):
            continue
        past = tuple(d for d in days if d <= ctx.day)
        if not past:
            continue
        it = _item(raw)
        if not it["images"]:
            continue
        skins += 1
        e = {"key": key, "it": it, "times": hist.times(key, until=ctx.day), "with": []}
        # Same set, same days in the shop every time: sold together, one entry.
        gk = (it["set"], past) if it["set"] else (key,)
        groups.setdefault(gk, []).append(e)
    pool = []
    for g in groups.values():
        g.sort(key=lambda e: (_fame(e), e["it"]["name"]), reverse=True)
        g[0]["with"] = [x["it"]["name"] for x in g[1:]]
        pool.append(g[0])
    by_base = {}
    for e in pool:
        base = re.sub(r"\s*\([^)]*\)\s*$", "", e["it"]["name"]).strip().lower()
        cur = by_base.get(base)
        plain = e["it"]["name"].strip().lower() == base
        if cur is None or (plain, _fame(e)) > (cur["it"]["name"].strip().lower() == base, _fame(cur)):
            by_base[base] = e
    return sorted(by_base.values(), key=lambda e: (e["times"], e["it"]["name"])), skins


def _cuts(counts: list, k: int) -> list | None:
    """k groups of the sorted counts, as even as possible without splitting a
    value between two groups: the ranges [(lo, hi), ..., (lo, None)]."""
    vals = sorted(set(counts))
    k = min(k, len(vals))
    if k < 3:
        return None
    n = [sum(1 for c in counts if c == v) for v in vals]
    pre = [0]
    for x in n:
        pre.append(pre[-1] + x)
    goal = len(counts) / k
    INF = float("inf")
    # best[j][i]: the first i distinct values in j groups; cost = squared distance from even
    best = [[INF] * (len(vals) + 1) for _ in range(k + 1)]
    back = [[0] * (len(vals) + 1) for _ in range(k + 1)]
    best[0][0] = 0
    for j in range(1, k + 1):
        for i in range(j, len(vals) + 1):
            for p in range(j - 1, i):
                if best[j - 1][p] == INF:
                    continue
                c = best[j - 1][p] + (pre[i] - pre[p] - goal) ** 2
                if c < best[j][i]:
                    best[j][i], back[j][i] = c, p
    ends, i = [], len(vals)
    for j in range(k, 0, -1):
        ends.append(i)
        i = back[j][i]
    ends.reverse()
    # Each tier runs up to where the next one starts, so the ranges leave no gaps.
    lows = [vals[0]] + [vals[e] for e in ends[:-1]]
    return [(lo, None if j == k - 1 else lows[j + 1] - 1) for j, lo in enumerate(lows)]


def _ranges(pool: list, mode: str) -> tuple:
    """(ranges, fixed?): the fixed tiers when the season's counts fill all five
    (or when asked), else tiers cut from the season's own counts."""
    counts = [e["times"] for e in pool]
    filled = {_tier(c, FIXED) for c in counts}
    if mode == "fixed" or (mode == "auto" and len(filled) == len(FIXED)):
        return list(FIXED), True
    return _cuts(counts, len(TIERS)), False


def _tier(times: int, ranges) -> int:
    for i, (lo, hi) in enumerate(ranges):
        if hi is None or times <= hi:
            return i
    return len(ranges) - 1


def _pick(pool: list, ranges: list, ctx: Ctx, count: int) -> list:
    """Up to `count` skins: the one sold the fewest times, every tier's best known,
    then the best known of the rest, at most CAP to a row (more only when that's
    the only way to reach eight). A skin without art is skipped."""
    for e in pool:
        e["tier"] = _tier(e["times"], ranges)
    picks, seen = [], set()

    def take(e):
        if e["key"] in seen:
            return False
        seen.add(e["key"])
        e["art"] = ctx.art(e["it"])
        if not e["art"]:
            return False
        picks.append(e)
        return True

    for e in sorted(pool, key=lambda e: (e["times"], tuple(-x for x in _fame(e)))):
        if take(e):
            break
    for t in range(len(ranges)):
        if any(p["tier"] == t for p in picks):
            continue
        for e in sorted((e for e in pool if e["tier"] == t), key=_fame, reverse=True):
            if take(e):
                break
    known = sorted(pool, key=lambda e: (_fame(e), e["it"]["name"]), reverse=True)
    for cap in (CAP, CAP + 1, CAP + 2):
        for e in known:
            if len(picks) >= count:
                break
            if e["key"] in seen or sum(1 for p in picks if p["tier"] == e["tier"]) >= cap:
                continue
            take(e)
        if len(picks) >= min(count, 8):
            break
    return picks


def _order(picks: list) -> list:
    """The order they're placed in: round the rows (B, D, A, C, S) from each row's
    least known up, then the best known of the rest, then the one sold the fewest
    times -- the last two held back."""
    last = min(picks, key=lambda e: (e["times"], tuple(-x for x in _fame(e))))
    rest = [p for p in picks if p is not last]
    second = max(rest, key=lambda e: (_fame(e), e["it"]["name"]))
    body = [p for p in rest if p is not second]
    queues = {t: sorted((p for p in body if p["tier"] == t), key=lambda e: (_fame(e), e["it"]["name"]))
              for t in range(len(TIERS))}
    seq = []
    while any(queues.values()):
        for t in (2, 4, 1, 3, 0):
            if queues.get(t):
                seq.append(queues[t].pop(0))
    return seq + [second, last]


def _range_text(lo: int, hi) -> str:
    if hi is None:
        return f"{lo}+"
    return f"{lo}×" if lo == hi else f"{lo}–{hi}×"


# ------------------------------------------------------------------ drawing: pieces

def _face(e: dict, size: float, art_id: str) -> str:
    """A skin's tile at `size` px: its rarity's colour, the figure head to thigh.
    Every size is drawn the same way, so the big one lands on the small one."""
    col = hexcol(RARITY.get(e["it"]["rarity"], ""), "#6d7380")
    hi, lo = _mix(col, "#ffffff", .2), _mix(col, "#08080a", .62)
    r = size * .075
    bg = f"radial-gradient(circle at 50% 22%,{hi} 0%,{col} 36%,{lo} 100%)"
    if e.get("art"):
        fig = f'<img class="tl-fig" data-art="{art_id}" data-name="{esc(e["it"]["name"])}" src="{BLANK}" alt="">'
    else:
        fig = (f'<div class="d" style="position:absolute;inset:8%;display:flex;align-items:center;'
               f'justify-content:center;text-align:center;font-size:{size * .14:.0f}px;line-height:.95;'
               f'color:rgba(255,255,255,.9)">{esc(e["it"]["name"])}</div>')
    return (f'<div class="tl-face" style="width:{size:.1f}px;height:{size:.1f}px;border-radius:{r:.1f}px;'
            f'background:{bg};box-shadow:0 {size * .04:.1f}px {size * .09:.1f}px rgba(0,0,0,.5)">'
            f'{fig}<i class="tl-shade"></i><i class="tl-rim" style="border-radius:{r:.1f}px"></i></div>')


def _geom(n_tiers: int, rows: dict) -> dict:
    """Row tops, row height and the tile size, for the board at rest."""
    row_h = min(206.0, (BOARD_H - (n_tiers - 1) * ROW_GAP) / n_tiers)
    most = max([len(v) for v in rows.values()] + [1])
    tile = min(row_h - 2 * PAD, (AREA_W - (most - 1) * TGAP) / most)
    tops = [BY0 + i * (row_h + ROW_GAP) for i in range(n_tiers)]
    return {"row_h": row_h, "tile": tile, "tops": tops, "bottom": tops[-1] + row_h}


def _slot(g: dict, tier: int, j: int) -> tuple:
    x = BX0 + LAB_W + PAD + j * (g["tile"] + TGAP)
    y = g["tops"][tier] + (g["row_h"] - g["tile"]) / 2
    return x, y


def _board(g: dict, ranges: list, picks: list, lands: dict, roll_call: float) -> str:
    """The panel, the rows and their labels, and every tile, each hidden until it
    lands (lands: pick key -> landing time)."""
    out = [f'<div class="tl-panel" style="left:{BX0 - 14}px;top:{BY0 - 14}px;width:{BX1 - BX0 + 28}px;'
           f'height:{g["bottom"] - BY0 + 28:.0f}px"></div>']
    letter = min(124, g["row_h"] * .64)
    for i, (lo, hi) in enumerate(ranges):
        t = TIERS[i]
        col = TIER_COL[t]
        thumps = [_a("tlthump", lands[p["key"]], .42, EASE_OUT, "none") for p in picks if p["tier"] == i]
        thumps.append(_a("tlthump", roll_call + i * .14, .42, EASE_OUT, "none"))
        out.append(
            f'<div class="tl-row" style="left:{BX0}px;top:{g["tops"][i]:.1f}px;width:{BX1 - BX0}px;'
            f'height:{g["row_h"]:.1f}px">'
            f'<div class="tl-lab" style="width:{LAB_W}px;background:linear-gradient(180deg,'
            f'{_mix(col, "#ffffff", .12)},{col} 55%,{_mix(col, "#000000", .1)})">'
            f'<b style="font-size:{letter:.0f}px;{_anim(*thumps)}">{t}</b>'
            f'<i style="font-size:25px;margin-top:{g["row_h"] * .035:.0f}px">{esc(_range_text(lo, hi))}</i>'
            f'</div></div>')
    counts = defaultdict(int)
    for p in picks:
        j = counts[p["tier"]]
        counts[p["tier"]] += 1
        x, y = _slot(g, p["tier"], j)
        T = g["tile"]
        t = lands[p["key"]]
        bs = max(26, T * .21)
        out.append(
            f'<div class="abs" style="left:{x:.1f}px;top:{y:.1f}px;width:{T:.1f}px;height:{T:.1f}px;'
            f'{_anim(_a("tlon", t, .01, "steps(1,end)"), _a("tlsettle", t, .34, EASE_OUT, "none"))}">'
            f'{_face(p, T, p["art_id"])}'
            f'<div class="tl-badge d" style="font-size:{bs:.0f}px;{_anim(_a("tlpop", t + .07, .3, EASE_BACK))}">'
            f'{p["times"]}<span class="tl-x">×</span></div></div>')
    return "".join(out)


def _fit_name(name: str, width: float = NAME_W, big: int = 104, one_min: int = 76, two_max: int = 82,
              small: int = 56) -> tuple:
    """(size, text with a <br> where a two-line name breaks most evenly)."""
    up = name.upper()
    for s in range(big, one_min - 1, -2):
        if _em(up) * s <= width:
            return s, esc(up)
    ws = up.split()
    if len(ws) > 1:
        j = min(range(1, len(ws)), key=lambda j: max(_em(" ".join(ws[:j])), _em(" ".join(ws[j:]))))
        a, b = " ".join(ws[:j]), " ".join(ws[j:])
        for s in range(two_max, small - 1, -2):
            if max(_em(a), _em(b)) * s <= width:
                return s, f"{esc(a)}<br>{esc(b)}"
    return max(small - 10, min(small, int(width / max(_em(up), 1)))), esc(up)


def _roll(comp: Comp, value: int, y: float, size: float, t: float, dur: float) -> str:
    """N TIMES, the number rolling up to it; the digits sit in a fixed box, so
    nothing moves when the count grows a digit."""
    name = comp.uid("tlroll")
    comp.css(f"@keyframes {name}{{from{{--n:1}}to{{--n:{int(value)}}}}}")
    digits = len(str(int(value)))
    word = "TIME" if value == 1 else "TIMES"
    return (f'<div class="abs d" style="left:{MID - 500:.0f}px;width:1000px;top:{y:.0f}px;display:flex;'
            f'justify-content:center;align-items:baseline;font-size:{size:.0f}px;color:{ACCENT};'
            f'text-shadow:0 6px 0 rgba(0,0,0,.35);{_anim(_a("tlin", t, .12))}">'
            f'<span class="count" style="display:inline-block;width:{digits * .514:.3f}em;text-align:right;'
            f'{_anim(_a(name, t, dur, "cubic-bezier(.12,.7,.2,1)"))}"></span>'
            f'<span style="font-size:.42em;margin-left:.2em;color:#fff">{word}</span></div>')


def _code_block(k: float, style: str = "", tag: bool = True) -> str:
    """USE CODE: BAD exactly as the corner badge draws it (cc_motion.code_badge),
    at k times its size, with #EpicPartner under it (tag)."""
    block = (f'<div class="tl-code" style="gap:{12 * k:.1f}px;border-radius:{16 * k:.1f}px;'
             f'padding:{8 * k:.1f}px {20 * k:.1f}px {6 * k:.1f}px {18 * k:.1f}px;'
             f'box-shadow:0 {8 * k:.1f}px 0 rgba(0,0,0,.38),0 {18 * k:.0f}px {36 * k:.0f}px rgba(0,0,0,.35)">'
             f'<div style="font-size:{23 * k:.1f}px;font-weight:900;line-height:1.02;letter-spacing:.12em">'
             f'USE<br>CODE:</div>'
             f'<div class="d" style="font-size:{80 * k:.1f}px;line-height:.9;letter-spacing:.02em">BAD</div></div>')
    note = (f'<div style="margin:{4 * k:.1f}px 0 0 {4 * k:.1f}px;font-size:{23 * k:.1f}px;font-weight:700;'
            f'line-height:1.3;color:rgba(255,255,255,.92);text-shadow:0 2px 8px rgba(0,0,0,.9)">#EpicPartner</div>')
    return f'<div style="{style}">{block}{note if tag else ""}</div>'


# ------------------------------------------------------------------ drawing: scenes

def _hook(comp: Comp, ctx: Ctx, a: dict, b: dict, kick: tuple, g: dict) -> str:
    """Frame 0, complete: the stamp and the season at the top, RARITY TIER LIST,
    the empty board below (drawn by the board layer, small), two skins in front
    of it and the question. Then everything moves into the working layout."""
    out = []
    # USE CODE: BAD, big, flying into the corner badge; the badge takes over as it lands.
    dock = comp.uid("tldock")
    d0, d1 = T_DOCK
    comp.css(f"@keyframes {dock}{{0%{{transform:scale({STAMP_K})}}"
             f"99.9%{{transform:translate({BADGE_X - STAMP_X}px,{BADGE_Y - STAMP_Y}px) scale(1);opacity:1}}"
             f"100%{{transform:translate({BADGE_X - STAMP_X}px,{BADGE_Y - STAMP_Y}px) scale(1);opacity:0}}}}")
    comp.css(f".codebadge,.codetag{{animation:tlin .01s linear {d1 - .01:.3f}s both paused !important}}")
    out.append(f'<div class="abs" style="left:{STAMP_X}px;top:{STAMP_Y}px;transform-origin:0 0;z-index:5;'
               f'{_anim(_a(dock, d0, d1 - d0, "cubic-bezier(.6,0,.4,1)"))}">'
               f'<div style="transform-origin:0 0;{_anim(_a("tlboing", .2, .45, EASE_OUT, "none"))}">'
               f'{_code_block(1)}</div></div>')
    # The season, right of the stamp: two lines that fade as the header's kicker takes over.
    kx = STAMP_X + 258 * STAMP_K + 34
    ks = min(58, (SAFE_RIGHT_TOP - kx) / max(_em(kick[0]), _em(kick[1])))
    out.append(f'<div class="abs d" style="left:{kx:.0f}px;top:{STAMP_Y + 4}px;font-size:{ks:.0f}px;line-height:.98;'
               f'color:#fff;white-space:nowrap;{_anim(_a("tlout", T_GROW[0], .25))}">'
               f'{esc(kick[0])}<br><span style="color:{ACCENT}">{esc(kick[1])}</span></div>')
    # The title: big, then shrinking into the header's (same words, same font).
    title = "RARITY TIER LIST"
    w_hook = _em(title) * HOOK_TITLE
    w_head = _em(title) * HEAD_TITLE
    k = HEAD_TITLE / HOOK_TITLE
    dx, dy = (HEAD_R - w_head) - SAFE_LEFT, HEAD_TITLE_Y - HOOK_TITLE_Y
    mv = comp.uid("tltitle")
    comp.css(f"@keyframes {mv}{{from{{transform:none}}to{{transform:translate({dx:.1f}px,{dy:.1f}px) scale({k:.4f})}}}}")
    out.append(f'<div class="abs" style="left:{SAFE_LEFT}px;top:{HOOK_TITLE_Y}px;transform-origin:0 0;'
               f'{_anim(_a(mv, T_GROW[0], T_GROW[1] - T_GROW[0], "cubic-bezier(.6,0,.3,1)"), _a("tlout", T_GROW[1] - .02, .06))}">'
               f'<div class="d" style="font-size:{HOOK_TITLE}px;white-space:nowrap;color:#fff;'
               f'text-shadow:0 8px 0 rgba(0,0,0,.35);transform-origin:{w_hook / 2:.0f}px 60%;'
               f'{_anim(_a("tlthump", .2, .4, EASE_OUT, "none"))}">{title}</div></div>')
    # The two skins, standing in front of the board's empty right side: the one
    # placed last (the fewest times in the shop) in front.
    for it, (fh, fw, cx), start in ((a, FIGS[0], .15), (b, FIGS[1], .3)):
        out.append(
            f'<div class="abs" style="left:{cx - fw / 2:.0f}px;top:{FIG_FEET - fh}px;width:{fw}px;'
            f'height:{fh}px;{_anim(_a("tlexit", T_EXIT + (start - .15) * .6, .42, "cubic-bezier(.5,0,.9,.4)"))}">'
            f'<div class="abs" style="left:{fw * .1:.0f}px;right:{fw * .1:.0f}px;bottom:-18px;height:44px;'
            f'border-radius:50%;background:radial-gradient(closest-side,rgba(0,0,0,.62),rgba(0,0,0,0))"></div>'
            f'<div class="abs" style="inset:0;transform-origin:50% 100%;{_anim(_a("tlhop", start, .5, EASE_OUT, "none"))}">'
            f'<img data-art="{it["art_id"]}" data-name="{esc(it["it"]["name"])}" src="{BLANK}" alt="" '
            f'style="position:absolute;left:0;top:0;width:100%;height:100%;object-fit:contain;'
            f'object-position:50% 100%;filter:drop-shadow(0 26px 30px rgba(0,0,0,.55))"></div></div>')
    # The question, slapped on the board's empty rows.
    q1, q2 = "WHICH TIER IS", "YOUR SKIN?"
    qs = 60
    out.append(f'<div class="abs" style="left:{BX0 + LAB_W * HOOK_SCALE + 22:.0f}px;top:{HOOK_BY + 292}px;'
               f'transform:rotate(-4deg);{_anim(_a("tlshrink", T_GROW[0] - .05, .3, "ease-in"))}">'
               f'<div class="tl-sticker d" style="font-size:{qs}px;line-height:.98;text-align:left;'
               f'{_anim(_a("tlboing", .9, .5, EASE_OUT, "none"))}">{q1}<br>'
               f'<span style="color:#121212">{q2}</span></div></div>')
    comp.cue(.15, "whoosh"); comp.cue(.2, "slam"); comp.cue(.3, "whoosh"); comp.cue(.9, "pop")
    comp.cue(d0, "whoosh"); comp.cue(T_GROW[0] + .05, "whoosh")
    return "".join(out)


def _header(kicker: str, t_in: float) -> str:
    """Right of the corner badge: the season (lime) and RARITY TIER LIST."""
    ks = 26
    kw = _label_w(kicker, ks) + .12 * ks * len(kicker)
    if kw > HEAD_R - 400:
        ks = ks * (HEAD_R - 400) / kw
    return (f'<div class="abs" style="right:{1080 - HEAD_R}px;top:{HEAD_KICK_Y}px;text-align:right;'
            f'{_anim(_a("tlin", t_in, .25))}"><div style="font-size:{ks:.1f}px;font-weight:800;'
            f'letter-spacing:.12em;color:{ACCENT};white-space:nowrap">{esc(kicker)}</div></div>'
            f'<div class="abs d" style="right:{1080 - HEAD_R}px;top:{HEAD_TITLE_Y}px;font-size:{HEAD_TITLE}px;'
            f'white-space:nowrap;color:#fff;text-shadow:0 6px 0 rgba(0,0,0,.35);'
            f'{_anim(_a("tlin", T_GROW[1] - .04, .04))}">RARITY TIER LIST</div>')


def _beat(comp: Comp, e: dict, k: int, n: int, t0: float, length: float, held: bool, slot: tuple, T: float) -> float:
    """One skin: the board dims, its tile comes up big with the name and the
    count, its tier pops, and the tile flies into its row. Returns the landing time."""
    t_fly = t0 + length - 1.4
    t_land = t_fly + FLY
    tier = TIERS[e["tier"]]
    name_s, name_html = _fit_name(e["it"]["name"])
    lines = 2 if "<br>" in name_html else 1
    y_name = CARD_Y + CARD + 24
    y_lbl = y_name + name_s * .92 * lines + 18
    y_count = y_lbl + 40
    count_s = 116
    y_chip = y_count + count_s * .9 + 24
    if held:
        t_q, t_reveal = t0 + .35, t0 + 2.25
        t_roll = t_reveal + .08
    else:
        t_q = t_reveal = None
        t_roll = t0 + .72
    roll_d = .45 if e["times"] < 4 else (.75 if e["times"] < 20 else .95)
    t_chip = t_roll + roll_d + .14
    out_a = _a("tlout", t_fly, .16, fill="forwards")
    inner = [f'<div class="full" style="background:rgba(8,8,10,.86);{_anim(_a("tlout", t_fly + .05, .4))}"></div>']
    top_label = f"SKIN {k} OF {n}"
    lab = (f'<div class="abs" style="left:{MID - 500:.0f}px;width:1000px;top:{CARD_Y - 46}px;text-align:center;'
           f'font-size:26px;font-weight:800;letter-spacing:.16em;color:{ACCENT};white-space:nowrap;{{a}}">{{t}}</div>')
    if held:
        inner.append(f'<div class="abs d" style="left:{MID - 500:.0f}px;width:1000px;top:{CARD_Y - 76}px;'
                     f'text-align:center;font-size:62px;color:#fff;text-shadow:0 6px 0 rgba(0,0,0,.4);white-space:nowrap;'
                     f'{_anim(_a("tlslam", t0 + .12, .45, EASE_OUT), _a("tlout", t_reveal - .1, .16, fill="forwards"))}">'
                     f'WHERE WILL</div>')
        inner.append(lab.format(a=_anim(_a("tlrise", t_reveal, .3, EASE_OUT), out_a), t=top_label))
    else:
        inner.append(lab.format(a=_anim(_a("tlrise", t0 + .1, .35, EASE_OUT), out_a), t=top_label))
    # The big tile, and its flight: X and Y on separate wrappers with different
    # easing, so it travels on a slight curve; it lands 6% over size, and the
    # board's tile settles from there.
    sx, sy = slot
    kf = 1.06 * T / CARD
    dx = sx - .03 * T - CARD_X
    dy = sy - .03 * T - CARD_Y
    # While the question hangs (held back), the card hovers: twice up and back.
    hover = (f"tlhover {(t_reveal - t0 - .75) / 2:.3f}s ease-in-out {t0 + .6:.3f}s 2 alternate none"
             if held else "")
    fx, fy = comp.uid("tlfx"), comp.uid("tlfy")
    comp.css(f"@keyframes {fx}{{from{{transform:none}}to{{transform:translateX({dx:.1f}px)}}}}"
             f"@keyframes {fy}{{from{{transform:none}}to{{transform:translateY({dy:.1f}px) scale({kf:.4f})}}}}")
    inner.append(
        f'<div class="abs" style="left:{CARD_X:.0f}px;top:{CARD_Y}px;width:{CARD}px;height:{CARD}px;z-index:3;'
        f'{_anim(_a(fx, t_fly, FLY, "cubic-bezier(.45,0,.25,1)"))}">'
        f'<div style="width:100%;height:100%;transform-origin:0 0;{_anim(_a(fy, t_fly, FLY, "cubic-bezier(.6,0,.3,1)"))}">'
        f'<div style="width:100%;height:100%;{_anim(_a("tlcard", t0 + .02, .5, EASE_OUT))}">'
        f'<div style="width:100%;height:100%;{_anim(hover, _a("tltilt", t_fly, FLY, "ease-in-out", "none"))}">'
        f'{_face(e, CARD, e["art_id"])}</div></div></div></div>')
    inner.append(f'<div class="abs d" style="left:{BX0 + 2}px;width:{NAME_W}px;top:{y_name:.0f}px;'
                 f'font-size:{name_s}px;line-height:.92;text-align:center;color:#fff;'
                 f'text-shadow:0 6px 0 rgba(0,0,0,.4);white-space:nowrap;'
                 f'{_anim(_a("tlslam", t0 + .3, .45, EASE_OUT), out_a)}">{name_html}</div>')
    shop = (f'<div class="abs" style="left:{MID - 500:.0f}px;width:1000px;top:{y_lbl:.0f}px;text-align:center;'
            f'font-size:30px;font-weight:800;letter-spacing:.1em;color:rgba(255,255,255,.8);white-space:nowrap;'
            f'{_anim(_a("tlrise", t_roll - .1, .3, EASE_OUT), out_a)}">IN THE ITEM SHOP</div>')
    if held:
        inner.append(f'<div class="abs d" style="left:{MID - 500:.0f}px;width:1000px;top:{y_count - 10:.0f}px;'
                     f'text-align:center;font-size:{count_s + 10}px;color:{ACCENT};text-shadow:0 6px 0 rgba(0,0,0,.35);'
                     f'{_anim(_a("tlslam", t_q + .45, .45, EASE_OUT), _a("tlout", t_reveal - .12, .14, fill="forwards"))}">LAND?</div>')
    inner.append(shop)
    inner.append(f'<div class="abs" style="left:0;top:0;{_anim(out_a)}">'
                 + _roll(comp, e["times"], y_count, count_s, t_roll, roll_d) + "</div>")
    inner.append(f'<div class="abs" style="left:{MID - 500:.0f}px;width:1000px;top:{y_chip:.0f}px;text-align:center;'
                 f'{_anim(out_a)}"><div class="tl-chip d" style="background:{TIER_COL[tier]};font-size:62px;'
                 f'{_anim(_a("tlchip", t_chip, .42, EASE_OUT))}">{tier} TIER</div></div>')
    comp.scene(t0, t_land + .04, "".join(inner), fade_in=.2, fade_out=.01, z=5)
    comp.cue(t0 + .04, "whoosh")
    if held:
        comp.cue(t0 + .32, "slam")
        comp.cue(t_q + .45, "pop")
        comp.cue(t_reveal - 1.62, "drumroll")
        comp.cue(t_roll, "reveal")
    else:
        comp.cue(t0 + .32, "pop")
        comp.cue(t_roll + roll_d, "tick")
    comp.cue(t_chip, "pin")
    comp.cue(t_fly, "whoosh")
    comp.cue(t_land, "stamp")
    return t_land


def _outro(comp: Comp, start: float, end: float) -> str:
    """WHICH TIER IS YOURS? and the code, big; the board has shrunk below them."""
    ask_s = 116
    inner = (f'<div class="abs d" style="left:{MID - 500:.0f}px;width:1000px;top:392px;text-align:center;'
             f'font-size:{ask_s}px;line-height:.92;color:#fff;text-shadow:0 8px 0 rgba(0,0,0,.35)">'
             f'<div style="{_anim(_a("tlslam", start + .35, .45, EASE_OUT))}">WHICH TIER</div>'
             f'<div style="{_anim(_a("tlslam", start + .55, .45, EASE_OUT))}">IS <span style="color:{ACCENT}">YOURS?</span>'
             f'</div></div>')
    k = 1.9
    w = 258 * k
    inner += (f'<div class="abs" data-safe="key" data-name="code" style="left:{MID - w / 2:.0f}px;top:628px;'
              f'transform-origin:50% 40%;{_anim(_a("tlslam", start + .9, .5, EASE_OUT))}">'
              + _code_block(k, tag=False) + "</div>")
    comp.scene(start, end, inner, fade_in=.2, fade_out=.01, z=7)
    comp.cue(start + .1, "whoosh"); comp.cue(start + .35, "slam"); comp.cue(start + .9, "slam")
    comp.cue(start + 1.3, "reveal")
    return inner


# ------------------------------------------------------------------ the builder

def _season_words(chapter: str, season: str) -> tuple:
    """("CHAPTER 1", "SEASON 3 SKINS") for the hook; the caption's words too."""
    s = season.strip()
    if s.lower() == "remix":
        return f"CHAPTER {chapter}", "REMIX SKINS"
    return f"CHAPTER {chapter}", f"SEASON {s.upper()} SKINS"


def build(ctx: Ctx, chapter: str = "1", season: str = "3", count: int = 12, thresholds: str = "auto"):
    """A tier list of one season's Item Shop skins; None when the season can't
    fill an honest board (fewer than six skins, or counts too alike to tier)."""
    chapter, season = str(chapter), str(season)
    hist = history()
    pool, skins = _pool(hist, ctx, chapter, season)
    if len(pool) < 6:
        return None
    ranges, fixed = _ranges(pool, thresholds)
    if not ranges:
        return None
    picks = _pick(pool, ranges, ctx, max(6, min(12, count)))
    if len(picks) < 6 or len({p["tier"] for p in picks}) < 3:
        return None
    seq = _order(picks)
    n = len(seq)
    for k, p in enumerate(seq):
        p["art_id"] = f"tlart{k}"

    # How long each skin gets: 4 s, stretched on a short list so the video still runs a minute.
    held = min(HELD, n - 1)
    R = max(R_MIN, min(R_MAX, (MIN_TOTAL - OUTRO - HOOK - HOLD - held * EXTRA) / n))
    t, starts = HOOK, []
    for k in range(n):
        starts.append(t)
        t += R + (EXTRA if k >= n - held else 0)
    last_land = starts[-1] + R + EXTRA * (held > 0) - 1.4 + FLY
    content_end = last_land + HOLD
    comp = Comp(pad_to(content_end, minimum=MIN_TOTAL, outro=OUTRO))
    comp.css(CSS.replace("@grain@", tex("card-grain.png")).replace("@lime@", ACCENT).replace("@ink@", INK))

    rows = defaultdict(list)
    for p in seq:
        rows[p["tier"]].append(p)
    g = _geom(len(ranges), rows)
    slots, lands = {}, {}
    for tier, members in rows.items():
        for j, p in enumerate(members):
            slots[p["key"]] = _slot(g, tier, j)

    # Each skin's art, embedded once (hidden) and cut out once (PREP_JS).
    comp.add(PREP_JS)
    comp.add('<div style="display:none">' + "".join(
        f'<img id="{p["art_id"]}" data-trim="figure" src="{p["art"]}" alt="">' for p in seq) + "</div>")
    comp.add(SHARE_JS)
    comp.add('<div class="full" style="z-index:0"><div class="tl-bg"></div></div>')

    kick = _season_words(chapter, season)
    hook = _hook(comp, ctx, seq[-2], seq[-1], kick, g)
    for k, p in enumerate(seq):
        is_held = k >= n - held
        length = R + (EXTRA if is_held else 0)
        lands[p["key"]] = _beat(comp, p, k + 1, n, starts[k], length, is_held, slots[p["key"]], g["tile"])
    roll_call = last_land + .45

    # The board: small and low on the thumbnail, growing into place; shrinking
    # under the outro's question and code.
    grow, shrink = comp.uid("tlgrow"), comp.uid("tlshr")
    comp.css(f"@keyframes {grow}{{from{{transform:translate(0px,{HOOK_BY - BY0}px) scale({HOOK_SCALE})}}"
             f"to{{transform:none}}}}")
    out_w = (BX1 - BX0) * OUT_SCALE
    comp.css(f"@keyframes {shrink}{{from{{transform:none}}to{{transform:translate("
             f"{MID - out_w / 2 - BX0:.1f}px,{OUT_TOP - BY0}px) scale({OUT_SCALE})}}}}")
    # The records' last day: the video's day, or the data's last day if that's earlier.
    asof = min(ctx.day, hist.latest) if hist.latest else ctx.day
    legend = f"TIER = TIMES IN THE ITEM SHOP · RECORDS TO {asof.strftime('%b %-d, %Y').upper()}"
    leg_y = g["bottom"] + LEGEND_GAP
    leg_hook = HOOK_BY + (g["bottom"] - BY0) * HOOK_SCALE + 10
    legmv = comp.uid("tllegmv")
    comp.css(f"@keyframes {legmv}{{from{{transform:translateY({leg_hook - leg_y:.1f}px)}}to{{transform:none}}}}")
    legend_html = (f'<div class="abs" style="left:{BX0}px;width:{BX1 - BX0}px;top:{leg_y:.0f}px;text-align:center;'
                   f'font-size:24px;font-weight:700;letter-spacing:.06em;color:rgba(255,255,255,.66);white-space:nowrap;'
                   f'{_anim(_a(legmv, T_GROW[0], T_GROW[1] - T_GROW[0], "cubic-bezier(.6,0,.3,1)"), _a("tlin", T_GROW[1] - .1, .3), _a("tlout", content_end, .3, fill="forwards"))}">'
                   f'{esc(legend)}</div>')
    board = (f'<div class="full" style="transform-origin:{BX0}px {BY0}px;'
             f'{_anim(_a(shrink, content_end, .7, "cubic-bezier(.6,0,.3,1)"))}">'
             f'<div class="full" style="transform-origin:{BX0}px {BY0}px;'
             f'{_anim(_a(grow, T_GROW[0], T_GROW[1] - T_GROW[0], "cubic-bezier(.6,0,.3,1)"))}">'
             f'{_board(g, ranges, seq, lands, roll_call)}</div></div>')
    comp.scene(0, comp.duration, board + legend_html, fade_in=.01, fade_out=.01, z=1)
    comp.scene(0, HOOK + .04, hook, fade_in=.01, fade_out=.02, z=8)
    comp.scene(T_GROW[0] + .3, comp.duration, _header(f"{kick[0]} · {kick[1]}", T_GROW[0] + .35),
               fade_in=.01, fade_out=.01, z=6)
    for i in range(len(ranges)):
        comp.cue(roll_call + i * .14, "tick")
    _outro(comp, content_end, comp.duration)
    comp.add('<div class="full" data-safe="ignore" style="z-index:9;pointer-events:none"><div class="tl-grain"></div></div>')
    comp.add(code_badge(0))
    comp.add(disclosure())
    comp.cues.sort()

    # ---- words
    season_txt = f"Chapter {chapter} " + ("Remix" if season.lower() == "remix" else f"Season {season.upper()}")
    by_tier = sorted(seq, key=lambda p: (p["tier"], p["times"], p["it"]["name"]))

    def line(p):
        t = TIERS[p["tier"]]
        times = "1 time" if p["times"] == 1 else f"{p['times']} times"
        more = f" (+{len(p['with'])} more from its set, always sold together)" if p["with"] else ""
        return f"{TIER_EMOJI[t]} {t} · {p['it']['name']}{more} · in the Item Shop {times}"
    legend_txt = " · ".join(f"{TIERS[i]} {_range_text(lo, hi).replace('×', '')}" for i, (lo, hi) in enumerate(ranges))
    how = "Tiers by times in the Item Shop" if fixed else "Tiers cut from this season's own counts, times in the Item Shop"
    hook_txt = (f"🏆 {season_txt.upper()} SKINS — RARITY TIER LIST, by the Item Shop's own records "
                f"(as of {asof.strftime('%B %-d, %Y')})\n"
                f"{how}: {legend_txt}. {n} of the season's {skins} Item Shop skins 👇")
    tags = _hashtags("tierlist", "ogfortnite", f"chapter{chapter}season{season}")
    return Video(
        f"tier_list_c{chapter}s{season.lower()}", comp,
        title=f"{season_txt} Skins: Rarity Tier List (Item Shop Records)",
        yt_title=f"{season_txt} Fortnite Skins — Rarity Tier List by Item Shop Records #shorts",
        caption=_caption(hook_txt, "\n".join(line(p) for p in by_tier), "Which tier is your skin?", tags),
        hashtags=tags)
