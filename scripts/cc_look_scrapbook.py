"""
SCRAPBOOK -- On This Day, drawn as a page someone glued together by hand.

    0:00  hook      the page: kraft header "on this day", a red rubber stamp with
                    the date, the two lead cosmetics as die-cut stickers, the
                    span of years in marker, and the lime USE CODE: BAD sticker
    0:03  years     one page per year (6.5 s): the cosmetic slaps on as a
                    sticker, a strip of tape, the year is written and circled,
                    a typed label with its name, a handwritten note (and a red
                    NEW THAT DAY stamp when it was its first day in the shop),
                    an arrow; the year's tag lights up along the bottom. The
                    next page's sticker lands while the last one slides away.
    0:55  outro     "which year had the best shop?" and a big code sticker

Facts on screen are the classic format's: the year, the date, the name, the
rarity and type, and "first day in the shop" only when the plan says so.
The lime code sticker is on screen in every frame.
"""

from cc_looks import (KIT_CSS, LIME, PREP_JS, diecut_filter, pad_to, rough_arrow, rough_ellipse,
                      stroke_static, stroke_svg, tex, write_on)
from cc_motion import Comp, esc

HOOK = 3.0
R = 6.5
LEAD = .35                         # the next page starts this early, over the last one leaving
INK_RED = "#c8232a"
MARK_RED = "#d9262c"
FONTS = ("Permanent Marker", "Caveat", "Special Elite", "Oswald")
BAKE = "url(#sbcut) drop-shadow(0 3px 2px rgba(0,0,0,.28)) drop-shadow(0 14px 16px rgba(0,0,0,.14))"

# Where things sit (TikTok's safe area is y 190-1480, nothing below y 880 right of x 960).
STICK_X, STICK_Y, STICK_H, STICK_WMAX = 96, 548, 770, 470
COL_X, COL_W = 596, 356            # the right-hand column
CODE_X, CODE_Y, CODE_D = 676, 1118, 252
OUTRO_CODE_D = 312                 # the outro's code: covers the small one, still left of x 950
TAG_Y = 1392

CSS = """
.sb-marker{font-family:'Permanent Marker',cursive;color:#161514;line-height:1}
.sb-hand{font-family:'Caveat',cursive;color:#1d1c1a;font-weight:700;line-height:1.02}
.sb-type{font-family:'Special Elite',monospace;color:#2b2926}
@keyframes sbout{to{transform:translate(-1250px,90px) rotate(-12deg)}}
@keyframes sbslap{0%{opacity:0;transform:translate(30px,-50px) scale(1.16) rotate(calc(var(--r,0deg) + 6deg))}
  1%{opacity:1;transform:translate(30px,-50px) scale(1.16) rotate(calc(var(--r,0deg) + 6deg))}
  55%{opacity:1;transform:translate(0,0) scale(.985) rotate(var(--r,0deg))}
  100%{opacity:1;transform:translate(0,0) scale(1) rotate(var(--r,0deg))}}
@keyframes sbthump{0%,100%{transform:scale(1)}40%{transform:scale(1.06)}}
@keyframes sbwiggle{0%,100%{transform:rotate(0)}35%{transform:rotate(-2.5deg)}70%{transform:rotate(1.5deg)}}
@keyframes sbtape{0%{opacity:0;transform:rotate(var(--r,0deg)) scaleX(.6)}100%{opacity:1;transform:rotate(var(--r,0deg)) scaleX(1)}}
@keyframes sbin{from{opacity:0;transform:translateY(24px) rotate(var(--r,0deg))}to{opacity:1;transform:rotate(var(--r,0deg))}}
.sb-tape{background:repeating-linear-gradient(-45deg,rgba(232,255,58,.82) 0 16px,rgba(214,240,40,.72) 16px 32px);
  clip-path:polygon(0 8%,4% 0,8% 10%,12% 1%,16% 9%,20% 0,100% 0,96% 9%,100% 18%,96% 30%,100% 42%,96% 55%,
  100% 68%,96% 80%,100% 92%,97% 100%,0 100%,4% 90%,0 78%,4% 66%,0 54%,4% 42%,0 30%,4% 18%);
  box-shadow:0 1px 2px rgba(0,0,0,.12);mix-blend-mode:multiply}
"""


def _a(name: str, t: float, dur: float, ease: str = "cubic-bezier(.2,.9,.25,1)", extra: str = "") -> str:
    return f"animation:{name} {dur:.2f}s {ease} {t:.3f}s 1 normal both;{extra}"


def _sticker(art: str, x: float, y: float, h: float, rot: float, t=None, label: str = "",
             wmax: float = STICK_WMAX) -> str:
    """A cosmetic as a die-cut sticker. t=None: already on the page."""
    anim = _a("lkslap", t, .55) if t is not None else ""
    if art:
        img = (f'<img data-trim data-bake="{BAKE}" data-pad="64" src="{art}" style="display:block;height:{h:.0f}px;'
               f'max-width:{wmax:.0f}px;object-fit:contain;filter:{BAKE}">')
    else:
        img = (f'<div class="sb-type" style="height:{h * .8:.0f}px;width:{wmax * .8:.0f}px;display:flex;'
               f'align-items:center;justify-content:center;text-align:center;font-size:40px;padding:20px;'
               f'border:5px dashed #9a8f7a;border-radius:30px;background:#fffdf6">{esc(label)}</div>')
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;--r:{rot}deg;transform:rotate({rot}deg);'
            f'transform-origin:50% 40%;{anim}">{img}</div>')


def _tape(x: float, y: float, rot: float, t=None, w: int = 190) -> str:
    anim = _a("sbtape", t, .25, "ease-out") if t is not None else ""
    return (f'<div class="abs sb-tape" style="left:{x:.0f}px;top:{y:.0f}px;width:{w}px;height:58px;'
            f'--r:{rot}deg;transform:rotate({rot}deg);{anim}"></div>')


def _stamp(text: str, sub: str, x: float, y: float, w: int, h: int, rot: float, size: int = 76) -> str:
    """A red rubber stamp: bordered, slightly uneven ink."""
    mask = tex("ink-stamp.png")
    return (f'<div class="abs sb-type" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
            f'transform:rotate({rot}deg);opacity:.88;border:9px solid {INK_RED};border-radius:18px;color:{INK_RED};'
            f'display:flex;flex-direction:column;align-items:center;justify-content:center;'
            f'-webkit-mask:url({mask}) center/cover;mask:url({mask}) center/cover">'
            f'<div style="font-family:Oswald,sans-serif;font-weight:700;font-size:{size}px;line-height:.9;'
            f'letter-spacing:.04em;white-space:nowrap">{esc(text)}</div>'
            + (f'<div style="font-family:Oswald,sans-serif;font-weight:500;font-size:{size * .33:.0f}px;'
               f'letter-spacing:.3em;white-space:nowrap">{esc(sub)}</div>' if sub else "")
            + '</div>')


def _code(x: float = CODE_X, y: float = CODE_Y, d: float = CODE_D, rot: float = -8, anim: str = "") -> str:
    """USE CODE: BAD as a big round lime price sticker."""
    k = d / CODE_D
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{d:.0f}px;height:{d:.0f}px;'
            f'border-radius:50%;background:{LIME};transform:rotate({rot}deg);display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;box-shadow:0 3px 3px rgba(0,0,0,.28),'
            f'0 12px 20px rgba(0,0,0,.14);--r:{rot}deg;{anim}">'
            f'<div style="font-family:Oswald,sans-serif;font-weight:700;font-size:{38 * k:.0f}px;letter-spacing:.06em;'
            f'color:#111;line-height:1">USE CODE:</div>'
            f'<div style="font-family:Anton,Impact,sans-serif;font-size:{124 * k:.0f}px;line-height:.92;'
            f'color:#111">BAD</div>'
            f'<div class="sb-type" style="font-size:{19 * k:.0f}px;color:#2a2a1a;margin-top:2px">#EpicPartner</div>'
            f'</div>')


def _tag_geom(n: int):
    step = min(112, 886 / max(n, 1))
    return step, step - 8


def _tag(i: int, yr: int, n: int, on: bool) -> str:
    step, w = _tag_geom(n)
    rot = [-3, 2, -1, 3, -2, 1, -3, 2, -1][i % 9]
    return (f'<div class="abs sb-type" style="left:{52 + i * step:.0f}px;top:{TAG_Y}px;width:{w:.0f}px;height:62px;'
            f'background:{"#fffdf6" if on else "#efe6d2"};transform:rotate({rot}deg);display:flex;'
            f'align-items:center;justify-content:center;font-size:{min(30, w * .29):.0f}px;'
            f'box-shadow:0 2px 3px rgba(0,0,0,.18);color:{"#161514" if on else "#8a8373"}">{yr}</div>')


def _tag_on(years: list, i: int, t: float) -> str:
    """The active year's tag, white, circled in red marker as the page lands."""
    step, w = _tag_geom(len(years))
    ring = rough_ellipse(52 + i * step + w / 2, TAG_Y + 31, w * .68, 44, seed=i + 3)
    return _tag(i, years[i], len(years), True) + stroke_svg([ring], MARK_RED, 7, t, .35)


def _name_strip(name: str, kind: str, x: float, y: float, rot: float, t) -> str:
    """The cosmetic's name typed on a strip of paper, its rarity and type under it."""
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{COL_W}px;--r:{rot}deg;'
            f'transform:rotate({rot}deg);{_a("sbin", t, .4, "cubic-bezier(.2,.8,.2,1)")}">'
            f'<div style="background:#fffdf6;padding:14px 18px 12px;box-shadow:0 2px 3px rgba(0,0,0,.2),'
            f'0 8px 14px rgba(0,0,0,.08)">'
            f'<div class="sb-type" data-fit="{COL_W - 36}" data-lines="2" style="width:{COL_W - 36}px;'
            f'font-size:46px;line-height:1.05;color:#161514">{esc(name)}</div>'
            f'<div class="sb-type" data-fit="{COL_W - 36}" style="width:{COL_W - 36}px;white-space:nowrap;'
            f'font-size:22px;letter-spacing:.08em;color:#6d675c;margin-top:6px">{esc(kind.upper())}</div>'
            f'</div></div>')


def _header(when_short: str) -> str:
    kraft = tex("kraft-strip.jpg")
    return (f'<div class="abs" style="left:-20px;top:170px;width:1120px;height:330px;'
            f'background:url({kraft}) center/cover;clip-path:polygon(0 6%,5% 2%,11% 7%,17% 1%,24% 6%,31% 2%,'
            f'38% 8%,45% 3%,52% 7%,60% 1%,67% 6%,74% 2%,81% 8%,88% 3%,94% 7%,100% 2%,100% 93%,94% 99%,88% 94%,'
            f'81% 100%,74% 95%,67% 99%,60% 93%,52% 98%,45% 94%,38% 100%,31% 95%,24% 99%,17% 93%,11% 98%,5% 94%,'
            f'0 99%);filter:drop-shadow(0 4px 4px rgba(0,0,0,.2));transform:rotate(-1.2deg)"></div>'
            f'<div class="abs sb-marker" style="left:66px;top:232px;font-size:104px;transform:rotate(-2deg);'
            f'color:#111">on this day</div>'
            f'<div class="abs sb-hand" style="left:76px;top:368px;font-size:54px;font-weight:600;'
            f'transform:rotate(-2deg)">...in the Fortnite Item Shop</div>'
            f'<div class="abs" style="left:0;top:0;transform-origin:870px 320px;{_a("sbthump", .2, .35, "ease-out")}">'
            + _stamp(when_short.upper(), "EVERY YEAR", 724, 250, 290, 146, 8) + '</div>')


def _page_year(ctx, rd, it, debut, t0: float, idx: int, years: list, r: float = R) -> tuple:
    """One year's page; t0 is when it has the frame to itself, for r seconds. Returns (html, sounds)."""
    rot = [-3, 2.5, -2, 3, -2.5, 2, -3.5, 2.5, -2][idx % 9]
    y = rd["year"]
    yx, yy = COL_X + 44, 604
    circle = rough_ellipse(yx + 150, yy + 74, 196, 100, seed=y, overshoot=.2)
    note = "its very first day in the shop!" if debut else "in the Item Shop that day"
    note_y = 996
    arrow = rough_arrow(COL_X - 8, note_y + 44, STICK_X + 330, note_y - 30, seed=y + 1, head=28, curve=.3)
    kind = " ".join(x for x in (it.get("rarity_label") or "", it.get("type") or "") if x).strip()
    s = t0 - .25                    # the sticker lands while the last page slides away
    html = [f'<div class="abs" style="inset:0;{_a("sbout", t0 + r - .5, .5, "cubic-bezier(.6,0,.8,.4)")}">',
            _sticker(ctx.art(it), STICK_X, STICK_Y, STICK_H, rot, s, it["name"]),
            _tape(STICK_X + 150, STICK_Y - 20, rot - 8, s + .45),
            f'<div class="abs sb-marker" style="left:{yx}px;top:{yy}px;font-size:132px;white-space:nowrap;'
            f'{write_on(t0 + .35, .45)}">{y}</div>',
            stroke_svg([circle], MARK_RED, 10, t0 + .8, .45),
            _name_strip(it["name"], kind, COL_X, 800, -1.5, t0 + .6),
            f'<div class="abs sb-hand" data-fit="{COL_W}" data-lines="2" style="left:{COL_X}px;top:{note_y}px;'
            f'width:{COL_W}px;font-size:58px;{write_on(t0 + 1.25, .9)}">{esc(note)}</div>',
            stroke_svg(arrow, "#161514", 6, t0 + 2.1, .3, gap=.02)]
    sounds = [(s, "paper"), (s + .45, "paper"), (t0 + .35, "pen"), (t0 + .8, "pen"), (t0 + 1.25, "pen"),
              (t0 + r - .5, "whoosh")]
    if debut:
        html.append(f'<div class="abs" style="left:0;top:0;'
                    f'{_a("lkstamp", t0 + 1.9, .28, "cubic-bezier(.3,1.6,.5,1)", "--r:0deg;")}">'
                    + _stamp("NEW THAT DAY", "", STICK_X - 24, STICK_Y + STICK_H - 190, 330, 96, -9, 44) + '</div>')
        sounds.append((t0 + 1.9, "stamp"))
    html.append('</div>')
    html.append(_tag_on(years, idx, t0 + .2))
    return "".join(html), sounds


def _page_birthday(bday: dict, t0: float, years: list, when: str, r: float = R) -> tuple:
    html = (f'<div class="abs" style="inset:0;{_a("sbout", t0 + r - .5, .5, "cubic-bezier(.6,0,.8,.4)")}">'
            f'<div class="abs sb-marker" data-fit="900" data-lines="2" style="left:80px;top:560px;width:900px;'
            f'font-size:100px;line-height:1.08;{write_on(t0 - .1, 1.1, 24)}">Fortnite Battle Royale comes out!</div>'
            f'<div class="abs sb-hand" style="left:84px;top:800px;font-size:66px;{write_on(t0 + 1.1, .8)}">'
            f'{esc(when)}, {bday["year"]}</div>'
            f'<div class="abs sb-hand" style="left:84px;top:880px;font-size:54px;color:#4a4540;'
            f'{write_on(t0 + 1.8, .8)}">PC · PlayStation 4 · Xbox One</div>'
            f'<div class="abs" style="left:0;top:0;'
            f'{_a("lkstamp", t0 + 2.6, .28, "cubic-bezier(.3,1.6,.5,1)", "--r:0deg;")}">'
            + _stamp("HAPPY BIRTHDAY", f"{bday['age']} YEARS TODAY", 110, 1000, 520, 150, -7, 62) + '</div>'
            '</div>')
    html += _tag_on(years, 0, t0 + .2)
    sounds = [(t0 - .1, "pen"), (t0 + 1.1, "pen"), (t0 + 1.8, "pen"), (t0 + 2.6, "stamp"), (t0 + 2.8, "clap"),
              (t0 + r - .5, "whoosh")]
    return html, sounds


def on_this_day(ctx, rounds: list, bday: dict, lead: list, third) -> Comp:
    day = ctx.day
    when = day.strftime("%B %-d")
    when_short = day.strftime("%b %-d")
    years = ([bday["year"]] if bday else []) + [rd["year"] for rd, _, _ in rounds]
    n = len(years)
    # Fewer years get longer pages, so a short day doesn't end on a long still card.
    r = max(R, (62.0 - 7.5 - HOOK) / n)
    content_end = HOOK + n * r
    comp = Comp(pad_to(content_end))
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(CSS)

    # The page itself, the header, the year tags and the code: on screen the whole time.
    comp.add(f'<div class="full" style="z-index:0;background:url({tex("paper.jpg")}) center/cover"></div>')
    comp.add(diecut_filter("sbcut", 15))
    comp.add(f'<div class="full" style="z-index:5">{_header(when_short)}</div>')
    comp.add(f'<div class="full" style="z-index:6">{"".join(_tag(i, y, n, False) for i, y in enumerate(years))}</div>')
    comp.add(f'<div class="full" style="z-index:4">'
             f'<div class="abs" style="left:60px;top:1540px;width:430px;height:170px;background:#f3e7c9;'
             f'transform:rotate(-5deg);box-shadow:0 3px 4px rgba(0,0,0,.18);border-left:3px dashed #b9a57a">'
             f'<div class="sb-type" style="position:absolute;left:34px;top:22px;font-size:26px;letter-spacing:.2em;'
             f'color:#9b3b2e">ADMIT ONE</div><div style="position:absolute;left:34px;top:54px;font-family:Oswald,'
             f'sans-serif;font-weight:700;font-size:50px;line-height:1;color:#3a2f24;letter-spacing:.04em">'
             f'ITEM SHOP</div><div class="sb-type" style="position:absolute;left:34px;top:120px;font-size:22px;'
             f'color:#6d5a44">{esc(when_short.upper())} · EVERY YEAR</div></div></div>')
    # The small code sticker stays until the outro's big one has landed on top of it.
    comp.add(f'<div class="full" style="z-index:30;{_a("lkout", content_end + .45, .01, "linear")}">{_code()}</div>')
    comp.add(PREP_JS)

    # ---- hook (frame 0 is the thumbnail: everything already on the page)
    a, b = lead[0][1], lead[1][1]
    span = f"{years[0]}–{years[-1]}"
    hook = (f'<div class="abs" style="inset:0;{_a("sbout", HOOK - .5, .5, "cubic-bezier(.6,0,.8,.4)")}">'
            + _sticker(ctx.art(a), 40, 560, 700, -6, None, a["name"], wmax=340)
            + f'<div class="abs" style="left:0;top:0;transform-origin:460px 980px;'
              f'{_a("sbwiggle", .35, .5, "ease-in-out")}">'
            + _sticker(ctx.art(b), 300, 660, 640, 5, None, b["name"], wmax=320) + '</div>'
            + _tape(120, 548, -14) + _tape(380, 648, 9, w=160))
    if bday:
        hook += (f'<div class="abs sb-marker" data-fit="340" data-lines="3" style="left:{COL_X + 30}px;top:600px;'
                 f'width:340px;font-size:84px;line-height:1.05">Fortnite turns {bday["age"]}!</div>'
                 f'<div class="abs sb-hand" data-fit="340" data-lines="3" style="left:{COL_X + 30}px;top:900px;'
                 f'width:340px;font-size:56px">Battle Royale came out on this day in {bday["year"]}</div>')
    else:
        hook += (f'<div class="abs sb-marker" data-fit="330" style="left:{COL_X + 30}px;top:620px;font-size:74px;'
                 f'white-space:nowrap">{esc(span)}</div>'
                 + stroke_static([rough_ellipse(COL_X + 196, 660, 205, 76, seed=7)], MARK_RED, 10)
                 + f'<div class="abs sb-hand" data-fit="{COL_W}" data-lines="3" style="left:{COL_X + 20}px;'
                   f'top:790px;width:{COL_W}px;font-size:58px">one outfit from the shop on this date, '
                   f'every year</div>')
    hook += '</div>'
    comp.scene(0, HOOK, f'<div class="full">{hook}</div>', fade_in=.01, fade_out=.05, z=10)
    comp.cue(.2, "stamp"); comp.cue(.35, "paper")

    # ---- one page per year, each starting just before its turn
    k = 0
    pages = []
    if bday:
        pages.append(_page_birthday(bday, HOOK, years, when, r))
        k = 1
    for j, (rd, it, debut) in enumerate(rounds):
        pages.append(_page_year(ctx, rd, it, debut, HOOK + (k + j) * r, k + j, years, r))
    for i, (html, sounds) in enumerate(pages):
        t0 = HOOK + i * r
        comp.scene(t0 - LEAD, t0 + r, f'<div class="full">{html}</div>', fade_in=.01, fade_out=.05, z=10)
        for s in sounds:
            comp.cue(*s)

    # ---- outro: the question, the three picks, and the code, big
    picks = [r[1] for r in lead] + ([third] if third else [])
    t = content_end
    out = (f'<div class="abs sb-marker" style="left:70px;top:560px;width:900px;font-size:88px;line-height:1.08;'
           f'{write_on(t - .2, 1.0, 22)}">which year had<br>the best shop?</div>')
    for i, (x, y, h, rot) in enumerate([(40, 800, 460, -6), (330, 850, 420, 4), (650, 760, 320, -3)][:len(picks)]):
        out += _sticker(ctx.art(picks[i]), x, y, h, rot, t + .6 + i * .25, picks[i]["name"], wmax=280)
    comp.scene(t - LEAD, comp.duration, f'<div class="full">{out}</div>', fade_in=.01, fade_out=.01, z=12)
    # The big code is slapped down right over the small one, covering it: the code
    # never shows twice and is never missing. (sbslap: a sticker drops, it doesn't fade.)
    cx, cy = CODE_X + CODE_D / 2 - 14, CODE_Y + CODE_D / 2 - 4
    big = _code(cx - OUTRO_CODE_D / 2, cy - OUTRO_CODE_D / 2, OUTRO_CODE_D, -7,
                _a("sbslap", t - .1, .55, extra="--r:-7deg;"))
    comp.scene(t - LEAD, comp.duration, f'<div class="full">{big}</div>', fade_in=.01, fade_out=.01, z=31)
    comp.cue(t - .1, "paper"); comp.cue(t - .2, "pen")
    for i in range(len(picks)):
        comp.cue(t + .6 + i * .25, "paper")
    comp.cues.sort()
    return comp
