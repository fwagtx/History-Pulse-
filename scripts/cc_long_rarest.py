"""
THE RAREST SKINS -- a long video (cc_long): a countdown of the cosmetics that
have been gone from the Item Shop the longest, straight from the shop's own
records (cc_rarity).

    cold open   "This skin has been in the Item Shop exactly once..."
    how         ranked by days since each was last in the Item Shop
    #N .. #1    each: rank, the cosmetic, when it was last sold, how many days
                ago (the counter rolls on the line that says it), how many times
                it has been in the shop, and its whole shop history as a strip
                from 2017 to today
    mid-roll    use code BAD (#EpicPartner)
    outro       every pick on one screen, "which one do you want back?",
                then the lime code-entry card

Truth rules: cc_rarity's. "Last in the Item Shop on <date>", "<n> days ago" and
"<n> times" come from shopHistory; the season is Epic's own introduction text.
It never says why something is gone or that it will never return.

    python3 scripts/cc_long_rarest.py --kind outfit --count 10 --day 2026-09-24 \
        --db br-full.json.gz [--art DIR] [--excerpt 2] --out DIR
"""

import argparse
import json
import random
from datetime import date
from pathlib import Path

import cc_long as L
import cc_rarity as R
from cc_common import log
from cc_motion import ACCENT, RARITY, an, esc, hexcol, style_anim

KINDS = {"outfit": ("skin", "skins", "Outfit"), "pickaxe": ("pickaxe", "pickaxes", "Pickaxe"),
         "emote": ("emote", "emotes", "Emote"), "glider": ("glider", "gliders", "Glider"),
         "backpack": ("back bling", "back blings", "Back Bling")}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]

# ------------------------------------------------------------------ words for the voice

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
        "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
ORD = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth",
       "nine": "ninth", "twelve": "twelfth"}


def words(n: int) -> str:
    """0..999999 in words: 2931 -> 'two thousand nine hundred thirty-one'."""
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")
    if n < 1000:
        return ONES[n // 100] + " hundred" + (" " + words(n % 100) if n % 100 else "")
    return words(n // 1000) + " thousand" + (" " + words(n % 1000) if n % 1000 else "")


def ordinal(n: int) -> str:
    w = words(n)
    head, _, last = w.rpartition(" ") if " " in w else ("", "", w)
    pre, dash, tail = last.rpartition("-")
    tail = ORD.get(tail, tail[:-1] + "ieth" if tail.endswith("y") else tail + "th")
    last = pre + dash + tail if dash else tail
    return (head + " " + last).strip()


def year_words(y: int) -> str:
    return f"twenty {words(y % 100)}" if y % 100 >= 10 else f"two thousand {words(y % 100)}"


def date_words(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {ordinal(d.day)}, {year_words(d.year)}"


def date_short(d: date) -> str:
    return f"{MONTHS[d.month - 1][:3]} {d.day}, {d.year}"


# ------------------------------------------------------------------ pictures

def art_block(uri: str, x: float, y: float, h: float, t: float, rarity: str) -> str:
    c = RARITY.get(rarity, "#3a3a44")
    stage = (f'<div class="abs" style="left:{x - h * .42:.0f}px;top:{y - h * .92:.0f}px;width:{h * .84:.0f}px;'
             f'height:{h * .98:.0f}px;border-radius:28px;background:radial-gradient(ellipse 90% 70% at 50% 35%,'
             f'{c} 0%,{hexcol("", "#101014")} 100%);box-shadow:0 30px 80px rgba(0,0,0,.55);'
             f'{style_anim(an("lvpop", t, .5))}"></div>')
    img = (f'<img class="abs" src="{uri}" style="left:{x - h * .5:.0f}px;top:{y - h:.0f}px;width:{h:.0f}px;'
           f'height:{h:.0f}px;object-fit:contain;object-position:50% 100%;'
           f'filter:drop-shadow(0 26px 34px rgba(0,0,0,.6));{style_anim(an("lvin", t + .12, .55))}">') if uri else ""
    return stage + img


def counter(value: int, x: float, y: float, size: float, t: float, dur: float = 1.4, color: str = ACCENT,
            steps: int = 26) -> str:
    """A number rolling up from 0 (with thousands commas) when its line is said:
    `steps` values, each shown in turn, easing out onto the real one."""
    vals = sorted({round(value * (1 - (1 - k / steps) ** 3)) for k in range(1, steps + 1)} | {value})
    dt = dur / len(vals)
    out = []
    for i, v in enumerate(vals):
        show = an("fadein", t + i * dt, .001, "linear")
        hide = an("fadeout", t + (i + 1) * dt, .001, "linear", fill="forwards") if v != value else ""
        out.append(f'<div class="abs" style="left:0;top:0;{style_anim(show)}"><div style="white-space:nowrap;'
                   f'{style_anim(hide) if hide else ""}">{v:,}</div></div>')
    return (f'<div class="abs d" style="left:{x:.0f}px;top:{y:.0f}px;font-size:{size:.0f}px;line-height:1;color:{color};'
            f'text-shadow:0 8px 0 rgba(0,0,0,.35)">{"".join(out)}</div>')


def timeline(runs: list, today: date, x: float, y: float, w: float, t: float, last: date | None) -> str:
    """Every run in the shop as a tick on a 2017-to-today strip; the gap since the
    last one in red."""
    start = R.RECORDS_START
    span = (today - start).days

    def px(d):
        return x + (d - start).days / span * w
    ticks = "".join(
        f'<div class="abs" style="left:{px(a):.1f}px;top:{y - 20}px;width:{max(4, px(b) - px(a)):.1f}px;height:40px;'
        f'background:{ACCENT};border-radius:3px"></div>' for a, b in runs)
    years = "".join(
        f'<div class="abs" style="left:{px(date(yy, 1, 1)):.0f}px;top:{y + 30}px;transform:translateX(-50%);'
        f'font:700 22px Inter;color:rgba(255,255,255,.55)">{yy}</div>'
        for yy in range(2018, today.year + 1))
    gap = ""
    if last:
        gx = px(last)
        gap = (f'<div class="abs" style="left:{gx:.0f}px;top:{y - 5}px;width:{x + w - gx:.0f}px;height:10px;'
               f'background:repeating-linear-gradient(90deg,#ff4d4d 0 18px,transparent 18px 30px);'
               f'transform-origin:0 50%;{style_anim(an("lvbar", t + .6, 1.2))}"></div>')
    return (f'<div class="abs" style="left:0;top:0;{style_anim(an("fadein", t, .4))}">'
            f'<div class="abs" style="left:{x}px;top:{y - 1}px;width:{w}px;height:2px;background:rgba(255,255,255,.3)"></div>'
            f'{ticks}{gap}{years}'
            f'<div class="abs" style="left:{x + w + 16}px;top:{y - 16}px;font:800 24px Inter;color:#fff">TODAY</div></div>')


def stat(label: str, value: str, x: float, y: float, t: float, color: str = "#fff") -> str:
    return (f'<div class="abs" style="left:{x}px;top:{y}px;{style_anim(an("lvin", t, .45))}">'
            f'<div style="font:800 24px Inter;letter-spacing:.18em;color:rgba(255,255,255,.62)">{esc(label)}</div>'
            f'<div class="d" style="font-size:64px;line-height:1.05;color:{color}">{esc(value)}</div></div>')


# ------------------------------------------------------------------ the episode

def plan(hist: R.History, day: date, kind: str, count: int) -> list:
    """The `count` longest-gone items, but when several from one set left the shop
    on the same day (a whole set, gone together), only the first of them, with
    how many others share its date: [(item, last, days, times, others)]."""
    rows, seen = [], {}
    for it, last, days, times in hist.longest_gone(day, kind, count * 6):
        key = ((it.get("set") or {}).get("value") if isinstance(it.get("set"), dict) else "", last)
        if key[0] and key in seen:
            seen[key][4] += 1
            continue
        row = [it, last, days, times, 0]
        rows.append(row)
        if key[0]:
            seen[key] = row
        if len(rows) == count:
            break
    return [tuple(r) for r in rows]


def build(hist: R.History, day: date, kind: str, count: int, art, seed: int, excerpt: int = 0,
          voice: str = L.V.VOICE):
    one, many, type_label = KINDS[kind]
    picks = plan(hist, day, kind, count)
    if len(picks) < count:
        raise SystemExit(f"only {len(picks)} {many} with a shop history")
    rnd = random.Random(seed)
    lv = L.LongVideo(seed, voice=voice)
    hook = next((p for p in picks if p[3] == 1), picks[0])
    h_item, h_last, h_days, h_times, _ = hook

    # ---- cold open
    def draw_open(comp, s):
        (a, _), (b, _), (c, _) = s.lines_at[0], s.lines_at[1], s.lines_at[2]
        inner = art_block(art(h_item), 1510, 960, 820, a, h_item["rarity"]["value"] if isinstance(h_item.get("rarity"), dict) else "")
        once = "IN THE SHOP ONCE." if h_times == 1 else f"IN THE SHOP {h_times}×."
        inner += (f'<div class="abs d" style="left:{L.MARGIN}px;top:250px;font-size:124px;color:#fff;'
                  f'{style_anim(an("lvin", a, .5))}">{esc(once)}</div>')
        inner += (f'<div class="abs" style="left:{L.MARGIN + 6}px;top:420px;font:800 34px Inter;letter-spacing:.14em;'
                  f'color:rgba(255,255,255,.7);{style_anim(an("lvin", b, .4))}">LAST IN THE ITEM SHOP {esc(date_short(h_last).upper())}</div>')
        inner += counter(h_days, L.MARGIN, 470, 230, b + .5)
        inner += (f'<div class="abs d" style="left:{L.MARGIN + 8}px;top:700px;font-size:70px;color:{ACCENT};'
                  f'{style_anim(an("lvin", b + .9, .4))}">DAYS AGO</div>')
        inner = f'<div class="full" style="{style_anim(an("fadeout", c, .3, fill="forwards"))}">{inner}</div>'
        title = (f'<div class="abs" style="left:0;top:0;width:{L.W}px;height:{L.H}px;background:rgba(10,10,11,.55);'
                 f'{style_anim(an("fadein", c, .35))}"></div>'
                 f'<div class="abs d" style="left:0;right:0;top:330px;text-align:center;font-size:190px;color:#fff;'
                 f'{style_anim(an("lvpop", c + .1, .55))}">THE RAREST {esc(many.upper())}</div>'
                 f'<div class="abs d" style="left:0;right:0;top:560px;text-align:center;font-size:96px;color:{ACCENT};'
                 f'{style_anim(an("lvpop", c + .45, .5))}">IN FORTNITE · {day.year}</div>'
                 f'<div class="abs" style="left:0;right:0;top:720px;text-align:center;font:700 36px Inter;'
                 f'color:rgba(255,255,255,.75);{style_anim(an("lvin", c + .8, .4))}">RANKED BY THE ITEM SHOP\'S OWN RECORDS</div>')
        comp.scene(s.t0, s.t1, f'<div class="full">{inner}{title}</div>', fade_in=.01, fade_out=.25, z=5)

    once_line = ("has been in the Item Shop exactly once." if h_times == 1
                 else f"has been in the Item Shop only {words(h_times)} times.")
    lv.segment([f"This {one} {once_line}",
                f"The last time was {date_words(h_last)}. That's {words(h_days)} days ago.",
                f"These are the rarest {many} in Fortnite, going by the Item Shop's own records."],
               draw_open, chapter="Intro", lead=.2)

    # ---- how it works
    def draw_how(comp, s):
        a = s.lines_at[0][0]
        inner = (f'<div class="abs d" style="left:{L.MARGIN}px;top:230px;font-size:120px;color:#fff;'
                 f'{style_anim(an("lvin", a, .45))}">HOW THIS WORKS</div>'
                 f'<div class="abs" style="left:{L.MARGIN}px;top:400px;width:1200px;font:600 46px/1.35 Inter;'
                 f'color:rgba(255,255,255,.88);{style_anim(an("lvin", a + .3, .45))}">Ranked by the days since each '
                 f'{esc(one)} was last in the Item Shop, from Epic\'s shop history. Every lime tick is a time it was for sale.</div>')
        runs = hist.runs(h_item["id"], until=day)
        inner += timeline(runs, day, L.MARGIN + 40, 840, L.W - 2 * L.MARGIN - 180, s.lines_at[1][0], h_last)
        if len(s.lines_at) > 2:
            c = s.lines_at[2][0]
            inner += (f'<div class="abs" style="left:1420px;top:250px;width:420px;{style_anim(an("lvpop", c, .5))}">'
                      f'<div class="d" style="font-size:170px;line-height:.9;color:{ACCENT}">{five:,}</div>'
                      f'<div style="font:800 30px/1.3 Inter;color:#fff;letter-spacing:.06em">OF {len(sold):,} {esc(many.upper())} '
                      f'EVER SOLD</div><div style="font:800 30px/1.3 Inter;color:#ff5a5a;letter-spacing:.06em">'
                      f'GONE 5+ YEARS</div></div>')
        comp.scene(s.t0, s.t1, f'<div class="full">{inner}</div>', fade_in=.2, fade_out=.25, z=5)

    # A number nobody else has, from the records: how many of this kind the Item
    # Shop has ever sold, and how few have been gone for five years or more.
    sold = [k for k, d in hist.days.items() if (hist.items[k].get("type") or {}).get("value") == kind
            and any(x < day for x in d)]
    five = sum(1 for k in sold if max(x for x in hist.days[k] if x < day) <= date(day.year - 5, day.month, min(day.day, 28))
               and hist.days[k][-1] < day)
    lv.segment(["Here's how this works. Every pick is ranked by how long it's been since it was last for sale.",
                "Each lime mark is a time it was in the shop, and the red line is how long it's been gone.",
                f"Out of {words(len(sold))} {many} the Item Shop has ever sold, only {words(five)} have been gone "
                f"for five years or more."],
               draw_how, chapter="How it works")

    # ---- the code break: the lime card, typing BAD, over the countdown so far
    def draw_break(comp, s):
        import cc_code_entry as CE
        a = s.lines_at[1][0]
        t = {"card": s.t0 + .1}
        t["keys"] = [round(a + .2 + i * .24, 3) for i in range(3)]
        t["accept"] = t["keys"][-1] + .42
        t["click"] = t["accept"] + .9
        t["done"] = t["click"] + .22
        t["pill"] = t["done"] + .22
        t["out"] = t["end"] = s.t1
        L_ = CE.LOOKS["lime"]
        inner = (CE.card(L_, "BAD", t, (L.W - CE.CARD_W * .9) / 2, (L.H - CE.CARD_H * .9) / 2, .9, True, True)
                 + CE.confirmation("BAD", t, L.W / 2, L.H / 2, 1.1, True, True))
        comp.scene(s.t0, s.t1, f'<div class="full" style="background:rgba(10,10,11,.55)">{inner}</div>',
                   fade_in=.2, fade_out=.25, z=6)
        for k in t["keys"]:
            comp.cue(k, "tick")
        comp.cue(t["click"], "click")
        comp.cue(t["pill"], "ding")

    # ---- the countdown
    order = list(reversed(list(enumerate(picks, 1))))
    if excerpt:
        order = order[:excerpt]
    half = len(order) // 2 if not excerpt and len(order) >= 8 else -1
    for i_pick, (rank, (item, last, days, times, others)) in enumerate(order):
        if i_pick == half:
            lv.segment([rnd.choice(["Quick one before the top half.", "Quick break before we keep going."]),
                        "If you're buying anything in the Item Shop, use code BAD. Hashtag Epic Partner. "
                        "It's the easiest way to support the channel."],
                       draw_break, chapter="", min_len=6.5, cue="whoosh")
        rar = item["rarity"]["value"] if isinstance(item.get("rarity"), dict) else ""
        intro = (item.get("introduction") or {}).get("text", "").replace("Introduced in ", "").rstrip(".")
        set_name = (item.get("set") or {}).get("value", "") if isinstance(item.get("set"), dict) else ""
        name = item["name"]
        opener = rnd.choice([f"Number {words(rank)}: {name}.", f"At number {words(rank)}, {name}.",
                             f"Number {words(rank)} is {name}."])
        when = rnd.choice([f"It was last in the Item Shop on {date_words(last)}.",
                           f"Its last day in the Item Shop was {date_words(last)}."])
        gone = f"That's {words(days)} days without it."
        count = ("In its whole history, it's been in the Item Shop exactly once." if times == 1 else
                 f"In its whole history, it's been in the Item Shop {words(times)} times.")
        extra = f"It first showed up in {intro}." if intro else ""
        if others:
            extra += (f" And it didn't leave alone: {words(others)} other {many if others > 1 else one} from the "
                      f"{set_name} set {'were' if others > 1 else 'was'} last in the shop that same day.")
        lines = [opener, when + " " + gone, count] + ([extra] if extra else [])

        def draw_pick(comp, s, item=item, last=last, days=days, times=times, rank=rank, rar=rar,
                      intro=intro, set_name=set_name, name=name):
            t1, t2, t3 = s.lines_at[0][0], s.lines_at[1][0], s.lines_at[2][0]
            inner = (f'<div class="abs d" style="left:{L.MARGIN - 10}px;top:150px;font-size:300px;line-height:1;'
                     f'color:transparent;-webkit-text-stroke:4px {ACCENT};opacity:.9;{style_anim(an("lvpop", t1, .5))}">#{rank}</div>')
            inner += art_block(art(item), 1530, 880, 720, t1 + .1, rar)
            inner += (f'<div class="abs d" style="left:{L.MARGIN}px;top:470px;max-width:960px;font-size:{min(112, 1500 / (len(name) * .5 + 1)):.0f}px;line-height:.95;'
                      f'color:#fff;{style_anim(an("lvin", t1 + .2, .45))}">{esc(name.upper())}</div>')
            chips = [x for x in (item["type"]["displayValue"] if isinstance(item.get("type"), dict) else "", set_name,
                                 intro.replace("Chapter ", "CH").replace(", Season ", " S")) if x]
            inner += (f'<div class="abs" style="left:{L.MARGIN}px;top:596px;display:flex;gap:14px;'
                      f'{style_anim(an("lvin", t1 + .35, .4))}">' + "".join(
                          f'<div style="padding:8px 18px;border-radius:12px;background:rgba(255,255,255,.1);'
                          f'font:800 26px Inter;letter-spacing:.08em;color:#fff">{esc(c.upper())}</div>' for c in chips) + '</div>')
            inner += stat("LAST IN THE SHOP", date_short(last).upper(), L.MARGIN, 690, t2)
            inner += (f'<div class="abs" style="left:{L.MARGIN + 440}px;top:690px;{style_anim(an("lvin", t2 + .2, .4))}">'
                      f'<div style="font:800 24px Inter;letter-spacing:.18em;color:rgba(255,255,255,.62)">DAYS GONE</div></div>')
            inner += counter(days, L.MARGIN + 440, 722, 76, t2 + .25, 1.3, "#ff5a5a")
            inner += stat("TIMES IN THE SHOP", str(times), L.MARGIN + 760, 690, t3, ACCENT)
            inner += timeline(hist.runs(item["id"], until=day), day, L.MARGIN + 20, 972, L.W - 2 * L.MARGIN - 150, t3, last)
            comp.scene(s.t0, s.t1, f'<div class="full">{inner}</div>', fade_in=.15, fade_out=.2, z=5)

        lv.segment(lines, draw_pick, chapter=f"#{rank} {name}", min_len=9)

    # ---- the ask (full videos); the excerpt ends here
    def draw_ask(comp, s):
        a = s.lines_at[0][0]
        grid = "".join(
            f'<img src="{art(p[0])}" style="width:230px;height:230px;object-fit:contain;'
            f'filter:drop-shadow(0 12px 16px rgba(0,0,0,.6))">' for p in picks[:12] if art(p[0]))
        inner = (f'<div class="abs d" style="left:0;right:0;top:170px;text-align:center;font-size:130px;color:#fff;'
                 f'{style_anim(an("lvin", a, .45))}">WHICH ONE DO YOU WANT BACK?</div>'
                 f'<div class="abs" style="left:{L.MARGIN}px;right:{L.MARGIN}px;top:400px;display:flex;flex-wrap:wrap;'
                 f'justify-content:center;gap:10px;{style_anim(an("lvin", a + .3, .5))}">{grid}</div>')
        comp.scene(s.t0, s.t1, f'<div class="full">{inner}</div>', fade_in=.2, fade_out=.2, z=5)

    lv.segment(["That's the list. Which one do you want back the most? Tell me in the comments.",
                "And if you're buying anything in the Item Shop, use code BAD. Hashtag Epic Partner."],
               draw_ask, chapter="Your pick")
    wall = [(art(p[0]), (p[0].get("rarity") or {}).get("value", "")) for p in picks[:5] if art(p[0])]
    title = f"The Rarest Fortnite {many.title()} in {day.year} (Item Shop Records)"
    return lv, wall, title, picks


def thumbnail(picks: list, art, day: date, kind: str, out: Path) -> Path:
    """The YouTube thumbnail, 1280x720: the title in huge type, the two longest-gone
    cosmetics, and the days sticker. No logos (Epic's aren't ours to use)."""
    import cc_code_entry as CE
    from playwright.sync_api import sync_playwright
    import cc_motion as M
    one, many, _ = KINDS[kind]
    (a, _, a_days, _, _), (b, _, _, _, _) = picks[0], picks[1]
    comp = CE.Frame(1.0, 1280, 720, "#0A0A0B")
    rar = lambda it: (it.get("rarity") or {}).get("value", "") if isinstance(it.get("rarity"), dict) else ""
    glow = lambda it, x: (f'<div class="abs" style="left:{x - 330}px;top:40px;width:660px;height:660px;border-radius:50%;'
                          f'background:radial-gradient(closest-side,{RARITY.get(rar(it), "#555")}cc,transparent)"></div>')
    img = lambda it, x, h, z: (f'<img src="{art(it)}" style="position:absolute;left:{x - h / 2:.0f}px;top:{720 - h + 30:.0f}px;'
                               f'width:{h:.0f}px;height:{h:.0f}px;object-fit:contain;object-position:50% 100%;z-index:{z};'
                               f'filter:drop-shadow(0 18px 24px rgba(0,0,0,.7))">' if art(it) else "")
    inner = ('<div class="full" style="background:radial-gradient(ellipse 70% 90% at 75% 50%,#1d2410,#0A0A0B 70%)"></div>'
             + glow(b, 1110) + glow(a, 900) + img(b, 1120, 640, 2) + img(a, 900, 760, 3)
             + f'<div class="abs d" style="left:44px;top:70px;font-size:190px;line-height:.86;color:#fff;z-index:5;'
               f'text-shadow:0 10px 0 rgba(0,0,0,.5)">RAREST<br><span style="color:{ACCENT}">{esc(many.upper())}</span></div>'
             + f'<div class="abs d" style="left:50px;top:420px;font-size:74px;color:#fff;z-index:5;'
               f'text-shadow:0 6px 0 rgba(0,0,0,.5)">IN FORTNITE {day.year}</div>'
             + f'<div class="abs" style="left:46px;top:540px;z-index:6;transform:rotate(-5deg)"><div class="d" '
               f'style="background:#ff3b3b;color:#fff;font-size:92px;padding:.08em .3em .02em;border-radius:14px;'
               f'box-shadow:0 10px 0 rgba(0,0,0,.45)">{a_days:,} DAYS</div></div>'
             + '<div class="grain"></div>')
    comp.add(f'<div class="full">{inner}</div>')
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=M.CHROME_ARGS)
        pg = br.new_page(viewport={"width": 1280, "height": 720})
        pg.set_content(comp.document(), wait_until="load")
        pg.evaluate(M.READY_JS)
        png = CE._stable(pg, 0, True, False)
        br.close()
    from io import BytesIO
    from PIL import Image
    try:
        Image.open(BytesIO(png)).convert("RGB").save(out, quality=92)
    except Exception:                      # no Pillow: keep the PNG
        out = out.with_suffix(".png")
        out.write_bytes(png)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="outfit", choices=list(KINDS))
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--day", default=date.today().isoformat())
    ap.add_argument("--db", default="")
    ap.add_argument("--art", default="")
    ap.add_argument("--excerpt", type=int, default=0, help="only this many picks (a preview)")
    ap.add_argument("--voice", default=L.V.VOICE)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from cc_quiz_build import art_fn
    day = date.fromisoformat(a.day)
    hist = R.History(R.load(a.db or None))
    art = art_fn(a.art or None)

    def art_of(item):
        return art({"id": item["id"], "name": item["name"],
                    "images": [v for k, v in (item.get("images") or {}).items() if k in ("featured", "icon") and v]})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lv, wall, title, picks = build(hist, day, a.kind, a.count, art_of, int(day.strftime("%Y%m%d")), a.excerpt, a.voice)
    comp, wav, chapters = lv.build(out, wall)
    stem = f"rarest-{a.kind}-{day.isoformat()}" + ("-excerpt" if a.excerpt else "")
    (out / f"{stem}.json").write_text(json.dumps({
        "title": title, "duration": round(comp.duration, 2), "chapters": L.chapters_text(chapters),
        "picks": [{"name": p[0]["name"], "last": p[1].isoformat(), "days": p[2], "times": p[3], "same_day_set": p[4]}
                  for p in picks],
    }, indent=1))
    log(f"{title}: {comp.duration:.1f}s")
    L.render(comp, out / f"{stem}.mp4", wav, workers=a.workers)


if __name__ == "__main__":
    main()
