"""
RECEIPT -- Bundle Math, as a thermal receipt printing on a shop counter.

    0:00  hook      a receipt already printed: BUNDLE MATH, how many bundles,
                    "every item also sold on its own today" and IS THE BUNDLE
                    WORTH IT?, the first bundle's photo on the counter, and the
                    printer's big lime USE CODE: BAD label. The pen underlines
                    the question; the receipt is torn off.
    0:03  bundles   one receipt per bundle (3-5, ~52 s in all): its photo lands on
                    the pile, then the printer prints a line per item with its
                    price alone today, ONE BY ONE ..... the total, the bundle
                    ..... its price, and YOU SAVE N V-BUCKS, which a blue pen
                    circles. The camera eases back as the paper grows. Tear.
    0:55  outro     a last short receipt: WHICH BUNDLE WOULD YOU GET?, the code
                    under a barcode, THANK YOU!

Facts are the format's: each item's price alone today, their sum, the bundle's
price and the difference. Never "discount". The lime label is on the printer, in
frame and readable in every frame (the camera zooms around it).

Everything with words on it, the label, the photos and the paper stay inside the
apps' safe box (cc_safe) with the counter's tilt and the camera's zoom counted
in: the receipt hangs left of the button rail and ends above the caption line,
the photo pile is above y 740, and the camera never pushes in past 1:1 (it only
leans in a touch at the end, on a short receipt). Only the counter, the
printer's body and the pen run to the edges. A line is on the paper only once
it has been printed.
"""

import html as _html
import math
import random

from cc_fmt_bundle_math import _title
from cc_looks import KIT_CSS, LIME, PREP_JS, pad_to, rough_check, rough_ellipse, rough_line, tex
from cc_motion import Comp, esc

HOOK = 3.0
CONTENT = 52.0
R_MIN, R_MAX = 10.4, 17.0
FONTS = ("IBM Plex Mono", "Archivo Black", "Barlow Condensed", "Caveat")

# The receipt: IBM Plex Mono on 26 columns (38 px: 33-38 px on screen as the
# camera pulls back).
FS, LH = 38, 53
CHW = FS * .6                     # Plex Mono's advance
COLS = 26
TW = COLS * CHW
PM = 20                           # side margin
PW = round(TW + 2 * PM)           # paper width
PX = 52                           # paper left (counter px, before its tilt)
HIDE = 6                          # paper hidden under the lip
ZZ = 12                           # zig-zag tooth height of a torn edge
SHOW_ITEMS = 7                    # item lines; more share one "+N more items" line
# How a long receipt is made to fit, one step at a time: (compact, item lines, clip names).
FIT_STEPS = [(0, 7, False), (1, 7, False), (2, 7, False), (3, 7, False),
             (3, 7, True), (3, 6, True), (3, 5, True), (3, 4, True), (3, 3, True)]
INK = "#2d2a26"
PEN = "#1f3b99"

# The printer's lime label: its centre and size (counter px). On frame 0 its
# words sit below Instagram's grid crop (y 285).
LBL_X, LBL_Y, LBL_W, LBL_H = 238, 366, 310, 156
LIP = LBL_Y + LBL_H // 2 + 40     # where the paper leaves the printer
# The printer (its top is off the frame).
PR_X, PR_W, PR_TOP = PX - 46, PW + 86, -120
PR_H = LIP - PR_TOP
LABEL = (LBL_X - LBL_W // 2 - PR_X, LBL_Y - LBL_H // 2 - PR_TOP, LBL_W, LBL_H)   # printer-local x, y, w, h
TILT = -1.2                       # the counter is turned a touch (.rc-rig), about (540, 700)


def _tilt(x: float, y: float) -> tuple:
    a = math.radians(TILT)
    dx, dy = x - 540, y - 700
    return 540 + dx * math.cos(a) - dy * math.sin(a), 700 + dx * math.sin(a) + dy * math.cos(a)


# The camera zooms about the label, so the label never moves: it is in frame and
# readable in every frame. It pulls back as a receipt grows, so the paper's torn
# edge stays above BOTTOM (inside the caption line once tilted), and never
# pushes in past Z_MAX, so the photo pile stays left of x 1020.
ZOX, ZOY = (round(v) for v in _tilt(LBL_X, LBL_Y))
Z_MAX, Z_MIN = 1.0, .88
Z_END = 1.02                      # the last lean in on the code
BOTTOM = 1398
# The pile of bundle photos on the counter, top right, above y 740.
PH_X, PH_Y, PH_W = PX + PW + 12, 250, 288
PH_IMG = PH_W - 24

CSS = """
.rc-cam{position:absolute;left:-80px;top:-80px;width:1240px;height:2080px}
.rc-zoom{position:absolute;inset:0;transform-origin:%(zox)dpx %(zoy)dpx;will-change:transform}
.rc-counter{position:absolute;left:-10px;top:-10px;width:1260px;height:2100px;background:url('%(counter)s') 0 0/1260px 2100px}
.rc-rig{position:absolute;left:80px;top:80px;width:1080px;height:1920px;transform:rotate(-1.2deg);transform-origin:540px 700px}
.rc-rcpt{position:absolute;left:%(px)dpx;top:%(ptop)dpx;width:%(pw)dpx}
.rc-pj{position:absolute;left:0;top:0;width:%(pw)dpx}
.rc-pshadow{position:absolute;left:0;top:0;width:%(pw)dpx;border-radius:2px;
  box-shadow:0 2px 2px rgba(40,22,8,.30),0 12px 22px rgba(40,22,8,.26)}
.rc-paper{position:absolute;left:0;top:0;width:%(pw)dpx;overflow:hidden;
  background:url('%(paper)s') 0 0/700px 1860px no-repeat;
  -webkit-mask:url("%(zzt)s") 0 0/24px %(zz)dpx repeat-x,linear-gradient(#000,#000) 0 %(zz)dpx/100%% calc(100%% - %(zz2)dpx) no-repeat,
    url("%(zzb)s") 0 100%%/24px %(zz)dpx repeat-x}
.rc-ink{position:absolute;left:0;top:0;width:700px;height:1860px;-webkit-mask:url('%(pmask)s') 0 0/700px 1860px no-repeat}
.rc-ln{position:absolute;white-space:pre;font-family:'IBM Plex Mono';font-weight:500;font-size:%(fs)dpx;color:%(ink)s;
  letter-spacing:0;filter:blur(.25px)}
.rc-ln.big{font-weight:700;transform:scale(2,1.9);transform-origin:0 50%%}
.rc-ln.tall{font-weight:700;transform:scaleY(1.95);transform-origin:0 50%%}
.rc-ln.dash{color:#57524b}
.rc-ln.small{color:#48443e}
.rc-printer{position:absolute;left:%(prx)dpx;top:%(prtop)dpx;width:%(prw)dpx;height:%(prh)dpx;border-radius:34px 34px 30px 30px;
  background:linear-gradient(172deg,#3b3b3e 0%%,#2a2a2d 34%%,#202023 70%%,#1a1a1c 100%%);
  box-shadow:0 22px 34px rgba(30,16,6,.55),0 6px 10px rgba(30,16,6,.45),inset 0 -3px 0 rgba(255,255,255,.07)}
.rc-printer .seam{position:absolute;left:44px;right:44px;height:3px;border-radius:2px;background:#101012;
  box-shadow:0 1px 0 rgba(255,255,255,.08)}
.rc-printer .lid{position:absolute;left:44px;right:44px;border-radius:14px;
  background:linear-gradient(170deg,rgba(255,255,255,.06),rgba(255,255,255,0) 45%%)}
.rc-printer .lip{position:absolute;left:0;right:0;bottom:0;height:34px;border-radius:0 0 30px 30px;
  background:linear-gradient(180deg,#2c2c2f,#161618 70%%,#0e0e0f)}
.rc-printer .slot{position:absolute;bottom:3px;height:9px;border-radius:3px;background:#050505}
.rc-printer .teeth{position:absolute;bottom:9px;height:8px;background:linear-gradient(180deg,#d7d7d4,#8d8d8a)}
.rc-printer .led{position:absolute;width:11px;height:11px;border-radius:50%%;
  background:radial-gradient(circle at 40%% 35%%,#e9ffe6,#46d45a 45%%,#1d7a2a);box-shadow:0 0 8px 2px rgba(80,230,100,.45)}
.rc-printer .btn{position:absolute;width:74px;height:40px;border-radius:9px;
  background:linear-gradient(180deg,#333336,#232326);box-shadow:0 2px 2px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.1);
  font-family:'Barlow Condensed';font-weight:600;font-size:17px;letter-spacing:.12em;color:#77777a;
  display:flex;align-items:center;justify-content:center}
.rc-printer .tex{position:absolute;inset:0;border-radius:inherit;opacity:.05;background:url('%(grain)s') 0 0/256px 256px}
.rc-lipshade{position:absolute;left:%(px)dpx;top:%(lip)dpx;width:%(pw)dpx;height:46px;pointer-events:none;
  background:linear-gradient(180deg,rgba(35,20,8,.34),rgba(35,20,8,.12) 40%%,rgba(35,20,8,0))}
.rc-code{position:absolute;border-radius:7px;background:%(lime)s;color:#111;text-align:center;
  box-shadow:0 2px 2px rgba(0,0,0,.55),0 9px 16px rgba(0,0,0,.42);overflow:hidden}
.rc-code::before{content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(172deg,rgba(255,255,255,.26) 0%%,rgba(255,255,255,0) 38%%),
             linear-gradient(0deg,rgba(0,0,0,.07),rgba(0,0,0,0) 30%%)}
.rc-code::after{content:"";position:absolute;inset:0;pointer-events:none;opacity:.10;background:url('%(grain)s') 0 0/256px 256px}
.rc-code .u{position:absolute;left:0;right:0;top:13px;font-family:'IBM Plex Mono';font-weight:700;font-size:40px;
  line-height:40px;letter-spacing:.02em}
.rc-code .b{position:absolute;left:0;right:0;top:53px;font-family:'Archivo Black';font-size:118px;line-height:96px;
  letter-spacing:-.01em}
.rc-ep{position:absolute;height:38px;padding:0 13px 0 14px;border-radius:4px;display:flex;align-items:center;
  background:linear-gradient(180deg,#34343a 0%%,#1d1d21 55%%,#141417 100%%);
  box-shadow:0 2px 2px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.18);
  font-family:'Barlow Condensed';font-weight:600;font-size:28px;letter-spacing:.06em;color:#e9e9e6;white-space:nowrap}
.rc-ep span{display:inline-block;text-shadow:0 1px 0 rgba(0,0,0,.7),0 -1px 0 rgba(255,255,255,.25)}
.rc-photo{position:absolute;width:%(phw)dpx;padding:12px 12px 0;background:#fbf9f3;
  box-shadow:0 2px 2px rgba(40,22,8,.35),0 12px 20px rgba(40,22,8,.30)}
.rc-photo .img{position:relative;width:%(phi)dpx;height:%(phi)dpx;overflow:hidden}
.rc-photo .img::after{content:"";position:absolute;inset:0;
  background:linear-gradient(160deg,rgba(255,255,255,.14),rgba(255,255,255,0) 40%%),
    radial-gradient(ellipse 90%% 80%% at 50%% 45%%,rgba(0,0,0,0) 60%%,rgba(0,0,0,.22))}
.rc-photo .cap{height:150px;padding:6px 6px 0;text-align:center;display:flex;flex-direction:column;align-items:center;
  justify-content:center}
.rc-photo .t{font-family:'Caveat';font-weight:700;font-size:38px;line-height:.95;color:#232220}
.rc-photo .q{font-family:'Caveat';font-weight:700;font-size:34px;line-height:1;color:%(pen)s;margin-top:5px}
.rc-pen{position:absolute;width:26px;height:400px;border-radius:13px 13px 6px 6px;
  box-shadow:6px 10px 12px rgba(40,22,8,.35),2px 3px 3px rgba(40,22,8,.35)}
.rc-art{position:absolute;width:0;height:0}
.rc-art img{position:absolute;visibility:hidden}
.rc-img{position:absolute;display:block;filter:drop-shadow(0 6px 8px rgba(0,0,0,.35))}
.rc-grain{position:absolute;left:-256px;top:-256px;width:1592px;height:2432px;pointer-events:none;opacity:.05;
  background:url('%(grain)s') 0 0/256px 256px repeat}
@keyframes rcgr{0%%{transform:translate(0,0)}20%%{transform:translate(-131px,77px)}40%%{transform:translate(53px,-173px)}
  60%%{transform:translate(-201px,-29px)}80%%{transform:translate(97px,149px)}}
.rc-vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(120%% 75%% at 42%% 38%%,rgba(0,0,0,0) 55%%,rgba(20,10,4,.5) 100%%)}
@keyframes rcon{from{visibility:hidden}to{visibility:visible}}
@keyframes rcland{0%%{opacity:0;transform:translate(60px,-90px) rotate(calc(var(--r) + 9deg)) scale(1.08)}
  60%%{opacity:1;transform:translate(0,0) rotate(calc(var(--r) - .6deg)) scale(.995)}
  100%%{opacity:1;transform:translate(0,0) rotate(var(--r)) scale(1)}}
"""

# Before frame 0: each bundle photo's art is trimmed to what's in it and fitted to
# the photo, standing on its bottom edge (real shop images come with wide margins).
ART_JS = """<script>(() => {
  const prev = window.__ready;
  async function fit(box) {
    const img = box.querySelector('img');
    if (!img) return;
    if (img.decode) { try { await img.decode(); } catch (e) {} }
    const w = img.naturalWidth, h = img.naturalHeight;
    if (!w || !h) return;
    const bw = +box.dataset.w, bh = +box.dataset.h;
    const k = Math.min(1, 420 / Math.max(w, h));
    const aw = Math.max(1, Math.round(w * k)), ah = Math.max(1, Math.round(h * k));
    const c = document.createElement('canvas'); c.width = aw; c.height = ah;
    const g = c.getContext('2d', {willReadFrequently: true});
    g.drawImage(img, 0, 0, aw, ah);
    const px = g.getImageData(0, 0, aw, ah).data;
    let x0 = aw, y0 = ah, x1 = -1, y1 = -1;
    for (let y = 0; y < ah; y++) for (let x = 0; x < aw; x++) {
      if (px[(y * aw + x) * 4 + 3] > 40) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; y1 = y; }
    }
    if (x1 < 0) return;
    const A = i => px[i * 4 + 3];
    const flat = A(0) > 245 && A(aw - 1) > 245 && A((ah - 1) * aw) > 245 && A(ah * aw - 1) > 245;
    let sx = 0, sy = 0, sw = w, sh = h;
    if (!flat) {
      sx = Math.max(0, (x0 - 1) / k); sy = Math.max(0, (y0 - 1) / k);
      sw = Math.min(w, (x1 + 2) / k) - sx; sh = Math.min(h, (y1 + 2) / k) - sy;
    }
    const s = flat ? Math.max(bw / sw, bh / sh) : Math.min(bw / sw, bh / sh, 3);
    const dw = Math.max(1, Math.round(sw * s)), dh = Math.max(1, Math.round(sh * s));
    const out = document.createElement('canvas'); out.width = dw; out.height = dh;
    const o = out.getContext('2d');
    o.imageSmoothingEnabled = true; o.imageSmoothingQuality = 'high';
    o.drawImage(img, sx, sy, sw, sh, 0, 0, dw, dh);
    out.className = 'rc-img';
    out.style.left = (-dw / 2) + 'px';
    out.style.top = (flat ? -dh / 2 : bh / 2 - dh) + 'px';
    if (flat) out.style.filter = 'none';
    img.replaceWith(out);
  }
  window.__ready = (async () => {
    try { if (prev) await prev; } catch (e) {}
    if (document.readyState === 'loading') {
      await new Promise(r => document.addEventListener('DOMContentLoaded', r, {once: true}));
    }
    for (const box of document.querySelectorAll('.rc-art')) { try { await fit(box); } catch (e) {} }
  })();
})();</script>"""


def _a(name: str, t: float, dur: float, ease: str = "linear", extra: str = "") -> str:
    return f"animation:{name} {dur:.3f}s {ease} {t:.3f}s 1 normal both;{extra}"


def _kf(name: str, pts: list, dur: float) -> str:
    """Keyframes over the whole video from [(t, css, easing to the next point)]."""
    out, last = [], -1.0
    for t, css, ease in sorted(pts, key=lambda p: p[0]):
        pct = max(0.0, min(100.0, t / dur * 100))
        if pct <= last:
            pct = last + .0005
        last = pct
        out.append(f"{pct:.4f}%{{{css}" + (f";animation-timing-function:{ease}" if ease else "") + "}")
    return f"@keyframes {name}{{{''.join(out)}}}"


def _zigzag(flip: bool) -> str:
    t, h = 24, ZZ
    pts = f"0,{h} {t / 2},0 {t},{h}" if not flip else f"0,0 {t / 2},{h} {t},0"
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{t}' height='{h}'>"
           f"<polygon points='{pts}' fill='black'/></svg>")
    return "data:image/svg+xml;utf8," + svg.replace("<", "%3C").replace(">", "%3E").replace("#", "%23")


# ------------------------------------------------------------------ receipt text

def _money(v: int) -> str:
    return f"{int(v):,}"


def _lead(left: str, right: str, cols: int = COLS):
    """'LEFT ....... RIGHT' in exactly `cols` columns, or None if it doesn't fit."""
    n = cols - len(left) - len(right) - 2
    return f"{left} {'.' * n} {right}" if n >= 2 else None


def _lr(left: str, right: str, cols: int = COLS):
    n = cols - len(left) - len(right)
    return left + " " * n + right if n >= 1 else None


def _wrap(text: str, width: int) -> list:
    """Word wrap to `width` columns; a word longer than that is cut."""
    lines, cur = [], ""
    for word in text.split():
        while len(word) > width:
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(word[:width])
            word = word[width:]
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def _priced(name: str, price: str, dots: bool) -> list:
    """A name and a price on one line, the name wrapping onto lines above the
    price when it's too long: real receipts do this."""
    one = _lead(name, price) if dots else _lr(name, price)
    if one:
        return [one]
    room = COLS - len(price) - (4 if dots else 1)
    parts = _wrap(name, COLS)
    last = parts[-1]
    if len(last) > room:
        tail = _wrap(last, room)
        parts = parts[:-1] + tail
        last = parts[-1]
    rows = parts[:-1]
    rows.append(_lead(last, price) if dots else _lr(last, price))
    return rows


class Doc:
    """A receipt's rows, laid out top to bottom in paper px."""

    def __init__(self, lh: int = LH):
        self.lh = lh
        self.y = HIDE + 26
        self.rows = []

    def add(self, kind: str, text: str = "", h: float = None, **kw) -> dict:
        h = h if h is not None else {"big": self.lh * 1.88, "tall": self.lh * 1.92, "dash": self.lh * .8,
                                     "bars": 104}.get(kind, self.lh)
        row = dict(kind=kind, text=text, y=self.y, h=h, **kw)
        self.rows.append(row)
        self.y += h
        return row

    def gap(self, h: float):
        self.y += h

    @property
    def height(self) -> float:
        return self.y


def _header(doc: Doc, when: str):
    doc.add("text", f"ITEM SHOP · {when}", align="c", group="head")
    doc.add("big", "BUNDLE MATH", group="head")


def _doc_intro(n: int, when: str) -> Doc:
    doc = Doc()
    _header(doc, when)
    doc.add("dash", "-" * COLS, group="a")
    doc.add("text", f"{n} OF TODAY'S BUNDLES", align="c", group="a")
    doc.add("text", "EVERY ITEM IN THEM IS", align="c", group="a", small=True)
    doc.add("text", "ALSO SOLD ALONE TODAY", align="c", group="a", small=True)
    doc.add("dash", "-" * COLS, group="a")
    doc.gap(10)
    doc.add("big", "IS THE BUNDLE", group="q")
    doc.add("big", "WORTH IT?", group="q", mark="q")
    doc.gap(30)
    return doc


def _doc_bundle(b: dict, parts: list, total: int, k: int, n: int, when: str, compact: int = 0,
                show: int = SHOW_ITEMS, clip: bool = False) -> Doc:
    """compact 0..3: drop the column heads, then the 'k OF n' line, then tighten the
    line height -- only as far as a long receipt needs. For the longest receipts,
    clip=True cuts item names to one line (as a till does), and `show` folds the
    last items into one "+N more items" line with their summed price."""
    doc = Doc(LH if compact < 3 else 44)
    _header(doc, when)
    if compact < 2:
        doc.add("text", f"BUNDLE {k} OF {n}", align="c", group="head", small=True)
    doc.add("dash", "-" * COLS, group="head")
    if compact < 1:
        doc.add("text", _lr("ITEM", "V-BUCKS"), group="cols", small=True)
    lines = parts if len(parts) <= show else parts[:show - 1]
    for i, p in enumerate(lines):
        price = _money(p["price"])
        rows = _priced(p["name"], price, dots=False)
        if clip and len(rows) > 1:
            room = COLS - len(price) - 1
            rows = [_lr(p["name"][:room - 1].rstrip() + "…", price)]
        for text in rows:
            doc.add("text", text, group=f"item{i}")
    if len(parts) > show:
        rest = parts[show - 1:]
        for text in _priced(f"+{len(rest)} more items", _money(sum(int(p['price']) for p in rest)), dots=False):
            doc.add("text", text, group=f"item{len(lines)}")
    doc.add("dash", "-" * COLS, group="total")
    doc.add("text", _lead("ONE BY ONE", _money(total)), group="total", mark="total")
    for text in _priced(_title(b).upper(), _money(int(b["price"])), dots=True):
        doc.add("text", text, group="bundle")
    doc.gap(30)
    save = total - int(b["price"])
    doc.add("tall", _lead("YOU SAVE", f"{_money(save)} V-BUCKS"), group="save", mark="save")
    doc.gap(48)
    return doc


CODE39 = {"*": "010010100", "B": "001001001", "A": "100001001", "D": "000011001"}


def _doc_close(when: str) -> Doc:
    doc = Doc()
    _header(doc, when)
    doc.add("dash", "-" * COLS, group="a")
    doc.gap(6)
    doc.add("tall", "WHICH BUNDLE", align="c", group="q")
    doc.add("tall", "WOULD YOU GET?", align="c", group="q", mark="q")
    doc.add("text", "TELL US BELOW", align="c", group="q2", small=True)
    doc.add("dash", "-" * COLS, group="c")
    doc.add("bars", group="c")
    doc.add("text", "SUPPORT-A-CREATOR", align="c", group="c2")
    doc.add("text", "CODE: BAD", align="c", group="c2")
    doc.add("text", "#EpicPartner", align="c", group="c2")
    doc.add("text", "THANK YOU!", align="c", group="c3")
    doc.gap(40)
    return doc


def _row_html(r: dict, rnd: random.Random, t_show=None) -> str:
    """One printed line. t_show: when it prints (None: already printed). Until
    then it isn't there at all, not just below the paper's torn edge."""
    kind, t = r["kind"], r["text"]
    show = f";animation:rcon .01s steps(1,end) {t_show - .01:.3f}s 1 normal both" if t_show is not None else ""
    if kind == "bars":
        return f'<div class="abs" style="left:0;top:0{show}">{_barcode(r["y"] + 10)}</div>'
    jit = rnd.uniform(-.6, .6)
    op = rnd.uniform(.9, 1.0)
    cls = "rc-ln"
    style = f"top:{r['y']:.1f}px;height:{r['h']:.1f}px;line-height:{r['h']:.1f}px;opacity:{op:.2f}{show}"
    if kind == "big":
        cls += " big"
        left = PM + (TW - len(t) * CHW * 2) / 2
    elif kind == "tall":
        cls += " tall"
        left = PM + ((COLS - len(t)) // 2 * CHW if r.get("align") == "c" else 0)
    else:
        left = PM + ((COLS - len(t)) // 2 * CHW if r.get("align") == "c" else 0)
        if kind == "dash":
            cls += " dash"
        if r.get("small"):
            cls += " small"
    return f'<div class="{cls}" style="{style};left:{left + jit:.1f}px">{_html.escape(t)}</div>'


def _barcode(y: float, h: int = 84) -> str:
    """Code 39 for *BAD*: a real, scannable pattern."""
    nw, ww = 4.4, 11.0
    seq = "*BAD*"
    total = sum(sum(ww if b == "1" else nw for b in CODE39[c]) + nw for c in seq) - nw
    x = PM + (TW - total) / 2
    rects = []
    for c in seq:
        for k, b in enumerate(CODE39[c]):
            wdt = ww if b == "1" else nw
            if k % 2 == 0:
                rects.append(f'<rect x="{x:.1f}" y="0" width="{wdt:.1f}" height="{h}"/>')
            x += wdt
        x += nw
    return (f'<svg class="abs" style="left:0;top:{y:.0f}px" width="{PW}" height="{h}" viewBox="0 0 {PW} {h}">'
            f'<g fill="{INK}">{"".join(rects)}</g></svg>')


# ------------------------------------------------------------------ printing

def _groups(doc: Doc) -> list:
    """Consecutive rows of one group print in one feed: [(group, bottom_y)]."""
    out = []
    for r in doc.rows:
        g = r.get("group", "")
        bottom = r["y"] + r["h"]
        if out and out[-1][0] == g:
            out[-1] = (g, bottom)
        else:
            out.append((g, bottom))
    return out


class Print:
    """One receipt on the timeline: when each feed happens, the paper's height over
    time, the pen, the tear."""

    def __init__(self, uid: str, doc: Doc, rnd: random.Random):
        self.uid, self.doc, self.rnd = uid, doc, rnd
        self.feeds = []          # (t, dur, paper_bottom)
        self.h0 = HIDE           # height already out at t=0
        self.extra = []          # html inside the paper (pen marks)
        self.tear = None         # (t_tear, t_gone)

    def feed(self, t: float, to_bottom: float, dur: float = .14):
        self.feeds.append((t, dur, to_bottom))

    def height_at(self, t: float) -> float:
        h = self.h0
        for (ft, d, b) in self.feeds:
            if t >= ft + d:
                h = b
            elif t > ft:
                h = h + (b - h) * (t - ft) / d
        return h

    def css(self, dur: float) -> str:
        pts = [(0.0, f"height:{self.h0 + ZZ + 2:.1f}px", "")]
        h = self.h0
        for (t, d, b) in self.feeds:
            pts.append((t, f"height:{h + ZZ + 2:.1f}px", "cubic-bezier(.3,.1,.3,1)"))
            pts.append((t + d, f"height:{b + ZZ + 2:.1f}px", ""))
            h = b
        pts.append((dur, f"height:{h + ZZ + 2:.1f}px", ""))
        jit = [(0.0, "transform:translate(0,0)", "")]
        for (t, d, _) in self.feeds:
            jit += [(t, "transform:translate(0,0)", ""), (t + .05, "transform:translate(.6px,2.2px)", ""),
                    (t + d + .06, "transform:translate(0,0)", "")]
        jit.append((dur, "transform:translate(0,0)", ""))
        out = _kf(f"rcg{self.uid}", pts, dur) + _kf(f"rcj{self.uid}", jit, dur)
        if self.tear:
            t0, t1 = self.tear
            dx = self.rnd.choice([-1, 1]) * self.rnd.uniform(60, 140)
            out += _kf(f"rct{self.uid}", [
                (0.0, "transform:translate(0,0) rotate(0deg)", ""),
                (t0, "transform:translate(0,0) rotate(0deg)", "cubic-bezier(.2,.9,.25,1.1)"),
                (t0 + .22, "transform:translate(3px,22px) rotate(.7deg)", "cubic-bezier(.5,0,.8,.4)"),
                (t1, f"transform:translate({dx:.0f}px,1650px) rotate({dx / 20:.1f}deg)", ""),
                (dur, f"transform:translate({dx:.0f}px,1650px) rotate({dx / 20:.1f}deg)", "")], dur)
        return out

    def html(self, dur: float) -> str:
        final = max([self.h0] + [b for (_, _, b) in self.feeds])
        feeds = sorted(self.feeds)

        def printed(r):
            if r["y"] + 1 < self.h0:
                return None
            return next((ft for ft, _, b in feeds if b > r["y"] + 1), None)
        rows = "".join(_row_html(r, self.rnd, printed(r)) for r in self.doc.rows if r["y"] < final)
        tear = f"animation:rct{self.uid} {dur:.3f}s linear 0s 1 normal both;" if self.tear else ""
        return (f'<div class="rc-rcpt" style="{tear}"><div class="rc-pj" style="animation:rcj{self.uid} {dur:.3f}s '
                f'linear 0s 1 normal both"><div class="rc-pshadow" style="height:{final + ZZ + 2:.0f}px;'
                f'animation:rcg{self.uid} {dur:.3f}s linear 0s 1 normal both"></div>'
                f'<div class="rc-paper" style="animation:rcg{self.uid} {dur:.3f}s linear 0s 1 normal both">'
                f'<div class="rc-ink">{rows}</div>{"".join(self.extra)}</div></div></div>')


def _pen_svg(paths: list, start: float, dur: float = .85, width: float = 4.6, gap: float = .05) -> str:
    """Blue ballpoint strokes in paper coordinates, drawing themselves on."""
    out = [f'<svg class="abs" style="left:0;top:0;overflow:visible" width="{PW}" height="1700" viewBox="0 0 {PW} 1700">']
    t = start
    for d, L in paths:
        L = int(L) + 4
        out.append(f'<path d="{d}" fill="none" stroke="{PEN}" stroke-width="{width}" stroke-linecap="round" '
                   f'stroke-linejoin="round" opacity=".9" style="stroke-dasharray:{L};stroke-dashoffset:{L};'
                   f'animation:lkdraw {dur:.2f}s cubic-bezier(.45,.05,.35,1) {t:.3f}s 1 normal both"/>')
        t += dur + gap
    out.append("</svg>")
    return "".join(out)


def _circle_row(r: dict, seed: int) -> tuple:
    cy = r["y"] + r["h"] / 2 + 2
    return rough_ellipse(PW / 2, cy, TW / 2 + 2, r["h"] * .56, seed=seed, overshoot=.14, wobble=.02, start=-160)


# ------------------------------------------------------------------ the counter

def _printer(dur: float) -> str:
    lx, ly, lw, lh = LABEL
    seam = ly - 12
    slot_l, slot_w = PX - PR_X - 14, PW + 28
    teeth = ",".join(f"{i / 60 * 100:.2f}% {0 if i % 2 == 0 else 100}%" for i in range(61))
    ep = "".join(f'<span style="transform:translateY({(i % 3 - 1) * .6:.1f}px) rotate({((i * 7) % 5 - 2) * .6:.1f}deg)">'
                 f'{_html.escape(c)}</span>' for i, c in enumerate("#EpicPartner"))
    return (f'<div class="rc-printer"><div class="tex"></div>'
            f'<div class="lid" style="top:30px;height:{seam - 34}px"></div>'
            f'<div class="seam" style="top:{seam}px"></div>'
            f'<div class="btn" data-safe="ignore" style="left:{PR_W - 118}px;top:{ly + 14}px">FEED</div>'
            f'<div class="led" style="left:{PR_W - 152}px;top:{ly + 28}px;'
            f'animation:rcled {dur:.3f}s linear 0s 1 normal both"></div>'
            f'<div class="lip"></div>'
            f'<div class="teeth" style="left:{slot_l}px;width:{slot_w}px;clip-path:polygon(0 0,{teeth},100% 0)"></div>'
            f'<div class="slot" style="left:{slot_l}px;width:{slot_w}px"></div>'
            f'<div class="rc-code" data-safe="key" data-name="code" style="left:{lx}px;top:{ly}px;width:{lw}px;'
            f'height:{lh}px;transform:rotate(-2deg)"><div class="u">USE CODE:</div><div class="b">BAD</div></div>'
            f'<div class="rc-ep" style="left:{lx + lw + 24}px;top:{ly + lh - 42}px;transform:rotate(1.5deg)">{ep}</div>'
            f'</div>')


def _pen(x: float, y: float, rot: float) -> str:
    """A blue ballpoint lying on the counter: clear hexagonal barrel with its ink
    tube, a blue cap and clip, a white cone and a metal point."""
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:26px;height:400px;transform:rotate({rot}deg)">'
            f'<div class="rc-pen" style="left:0;top:0;background:linear-gradient(90deg,rgba(214,222,230,.96),'
            f'rgba(255,255,255,.97) 28%,rgba(206,214,224,.94) 55%,rgba(150,160,172,.96))"></div>'
            f'<div class="abs" style="left:10px;top:70px;width:6px;height:268px;border-radius:3px;'
            f'background:linear-gradient(90deg,#16296e,#3450b8 50%,#16296e);opacity:.85"></div>'
            f'<div class="abs" style="left:-1px;top:-2px;width:28px;height:82px;border-radius:13px 13px 4px 4px;'
            f'background:linear-gradient(90deg,#132362,#3653c4 34%,#22389a 68%,#0f1b4d)"></div>'
            f'<div class="abs" style="left:21px;top:6px;width:7px;height:118px;border-radius:3px;'
            f'background:linear-gradient(90deg,#22389a,#4a67d6 50%,#172a70);box-shadow:1px 2px 2px rgba(0,0,0,.3)"></div>'
            f'<div class="abs" style="left:1px;top:338px;width:24px;height:46px;'
            f'clip-path:polygon(0 0,100% 0,62% 100%,38% 100%);background:linear-gradient(90deg,#d9d9d6,#fff 35%,'
            f'#c9c9c6 70%,#9d9d9a)"></div>'
            f'<div class="abs" style="left:10px;top:382px;width:6px;height:14px;border-radius:0 0 3px 3px;'
            f'background:linear-gradient(90deg,#8a8a88,#e8e8e6 50%,#7a7a78)"></div></div>')


def _photo(ctx, b: dict, k: int, t_land) -> str:
    """The bundle, photographed against its shop tile's colours, with its name and
    a question in pen. t_land=None: already on the pile."""
    art = ctx.art(b)
    cols = [c for c in (b.get("tile_colors") or []) if isinstance(c, str) and c.startswith("#") and len(c) == 7]
    c1, c2 = (cols + ["#2a2a30"])[:2] if cols else ("#6b6b73", "#2a2a30")
    # each photo lands a little lower than the last, so it covers the caption below
    # it and only a sliver of the older photo shows along the top
    rot = [3.5, -2.5, 3, -2, 2.5, -3][k % 6]
    dx, dy = [0, -6, 5, -4, 7, -3][k % 6], 10 * k
    anim = _a("rcland", t_land, .6, "cubic-bezier(.2,.8,.25,1)") if t_land is not None else ""
    name = _title(b)
    img = (f'<div class="rc-art" data-w="{PH_IMG - 16}" data-h="{PH_IMG - 10}" style="left:{PH_IMG // 2}px;'
           f'top:{PH_IMG // 2}px"><img src="{art}" alt=""></div>' if art else
           f'<div class="abs" style="inset:0;display:flex;align-items:center;justify-content:center;padding:18px;'
           f'text-align:center;font-family:Caveat;font-weight:700;font-size:48px;line-height:1;color:#fff;'
           f'text-shadow:0 2px 6px rgba(0,0,0,.4)">{esc(name)}</div>')
    return (f'<div class="rc-photo" style="left:{PH_X + dx}px;top:{PH_Y + dy}px;--r:{rot}deg;transform:rotate({rot}deg);'
            f'{anim}"><div class="img" style="background:radial-gradient(ellipse 85% 75% at 50% 40%,{c1},{c2})">'
            f'{img}</div><div class="cap"><div class="t" data-fit="{PH_W - 36}" data-lines="3" '
            f'style="width:{PH_W - 36}px">{esc(name)}</div>'
            f'<div class="q">worth it?</div></div></div>')


# ------------------------------------------------------------------ the video

def bundle_math(ctx, picks: list) -> Comp:
    n = len(picks)
    R = max(R_MIN, min(R_MAX, CONTENT / n))
    beat = R / 13.0
    content_end = HOOK + n * R
    comp = Comp(pad_to(content_end))
    dur = comp.duration
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(CSS % dict(dur=dur, zox=ZOX + 80, zoy=ZOY + 80, counter=tex("receipt-counter.jpg"),
                        paper=tex("receipt-paper.jpg"), pmask=tex("receipt-printmask.png"), grain=tex("receipt-grain.png"),
                        zzt=_zigzag(False), zzb=_zigzag(True), zz=ZZ, zz2=2 * ZZ, px=PX, ptop=LIP - HIDE, pw=PW,
                        fs=FS, ink=INK, prx=PR_X, prtop=PR_TOP, prw=PR_W, prh=PR_H, lip=LIP, lime=LIME, phw=PH_W,
                        phi=PH_IMG, pen=PEN))
    when = ctx.day.strftime("%b %-d, %Y").upper()
    rnd = random.Random(ctx.seed)
    prints, cues, zooms = [], [], []

    def fits(doc: Doc, z: float) -> bool:
        return ZOY + (LIP - HIDE + doc.height + ZZ - ZOY) * z <= BOTTOM

    def zoom_for(bottom: float) -> float:
        frame_bottom = LIP - HIDE + bottom + ZZ
        return max(Z_MIN, min(Z_MAX, (BOTTOM - ZOY) / max(1.0, frame_bottom - ZOY)))

    # ---- the hook: an intro receipt, already printed
    intro = Print("i", _doc_intro(n, when), rnd)
    intro.h0 = intro.doc.height
    q = next(r for r in intro.doc.rows if r.get("mark") == "q")
    qw = len(q["text"]) * CHW * 2
    x0 = PM + (TW - qw) / 2
    under = rough_line(x0 - 4, q["y"] + q["h"] - 4, x0 + qw + 6, q["y"] + q["h"] - 9, seed=5)
    intro.extra.append(_pen_svg([under], .9, .45, 5))
    intro.tear = (2.3, 2.95)
    prints.append(intro)
    cues += [(.9, "pen"), (2.3, "paper")]
    z_intro = zoom_for(intro.doc.height)
    zooms += [(0.0, z_intro), (2.6, z_intro)]

    # ---- one receipt per bundle
    for k, (b, parts, total) in enumerate(picks):
        s = HOOK + k * R
        doc = None
        for compact, show, clip in FIT_STEPS:
            doc = _doc_bundle(b, parts, total, k + 1, n, when, compact, show, clip)
            if fits(doc, Z_MIN + .02):
                break
        p = Print(f"b{k}", doc, rnd)
        groups = _groups(doc)
        items = [g for g in groups if g[0].startswith("item") or g[0] == "cols"]
        prices = [g for g in groups if g[0].startswith("item")]
        # Scheduled back from the tear, so every receipt holds about as long once
        # it's circled; when the slot is long the pen also ticks each price first.
        t_tear = s + R - .95
        hold = max(2.5, min(3.6, .24 * R))
        ticks = R >= 12
        t_tick_len = .2 * len(prices) + .15 if ticks else 0.0
        gap = max(.7, min(1.3, .9 * beat))
        t_circle = t_tear - hold - .85
        t_save = t_circle - .6 - (t_tick_len + .3 if ticks else 0.0)
        t_total = t_save - 2 * gap
        t_items = s + max(.85, 1.2 * beat)
        step = (t_total - .35 - t_items) / max(1, len(items))
        if not .28 <= step <= .95:
            # too few lines to fill the time, or too many: print at a steady pace from the top
            step = max(.28, min(.95, step))
            t_total = t_items + len(items) * step + .35
            t_save = t_total + 2 * gap
            t_circle = t_save + .6 + (t_tick_len + .3 if ticks else 0.0)
        t = s - .15
        cues.append((t, "printer"))
        k_item = 0
        for g, bottom in groups:
            if g == "head":
                p.feed(t, bottom, .32)
                t += .45
            elif g == "cols" or g.startswith("item"):
                t = max(t, t_items + k_item * step)
                p.feed(t, bottom, .13)
                if k_item % 3 == 0:
                    cues.append((t, "printer"))
                k_item += 1
            elif g == "total":
                p.feed(t_total, bottom, .22)
                cues += [(t_total, "printer"), (t_total + .3, "cash")]
            elif g == "bundle":
                p.feed(t_total + gap, bottom, .2)
            elif g == "save":
                p.feed(t_save, bottom, .38)
                cues.append((t_save, "printer"))
        if ticks:
            # the pen checks each price: a small tick beside it
            marks = []
            for j, (g, bottom) in enumerate(prices):
                last = [r for r in doc.rows if r.get("group") == g][-1]
                marks += rough_check(PM + TW + 3, last["y"] + last["h"] * .62, 15, seed=40 + 7 * k + j)
            t_tick = t_save + .6
            p.extra.append(_pen_svg(marks, t_tick, .15, 3.6, .05))
            for j in range(0, len(prices), 3):
                cues.append((t_tick + j * .2, "pen"))
        # the pen circles the saving
        save_row = next(r for r in doc.rows if r.get("mark") == "save")
        p.extra.append(_pen_svg([_circle_row(save_row, seed=11 + k)], t_circle, .85))
        cues.append((t_circle, "pen"))
        p.tear = (s + R - .95, s + R - .3)
        cues.append((s + R - .95, "paper"))
        prints.append(p)
        # the camera eases back as the paper grows, just ahead of each feed, holds,
        # and eases in again while the receipt is torn off
        for (ft, d, bottom) in p.feeds:
            zooms.append((ft - .05, zoom_for(bottom)))
        zooms.append((s + R - .95, zooms[-1][1]))

    # ---- the outro: a last, short receipt
    close = Print("c", _doc_close(when), rnd)
    t = content_end + .3
    cues.append((t, "printer"))
    for g, bottom in _groups(close.doc):
        close.feed(t, bottom, .3 if g in ("q", "c") else .16)
        t += .55 if g in ("q", "c") else .35
    q = next(r for r in close.doc.rows if r.get("mark") == "q")
    t_q = content_end + 2.6
    close.extra.append(_pen_svg([_circle_row(q, seed=3)], t_q, .9))
    cues.append((t_q, "pen"))
    prints.append(close)
    zooms += [(content_end + .1, Z_MAX)] + [(ft - .05, zoom_for(b)) for (ft, d, b) in close.feeds]
    # last, the camera leans in on the code (the label is the zoom's centre, so it
    # grows in place; the receipt still ends above BOTTOM)
    last_bottom = LIP - HIDE + max(b for (_, _, b) in close.feeds) + ZZ
    z_end = min(Z_END, (BOTTOM - ZOY) / max(1.0, last_bottom - ZOY))
    t_lean = max(t_q + 1.2, dur - 3.2)
    zooms += [(t_lean, zooms[-1][1]), (min(dur - .3, t_lean + 2.4), z_end), (dur, z_end)]

    for pr in prints:
        comp.css(pr.css(dur))
    # the printer's LED flickers while it feeds
    led = [(0.0, "opacity:1", "")]
    for pr in prints:
        for (ft, d, _) in pr.feeds:
            led += [(ft, "opacity:1", ""), (ft + .03, "opacity:.25", ""), (ft + d + .02, "opacity:.25", ""),
                    (ft + d + .08, "opacity:1", "")]
    led.append((dur, "opacity:1", ""))
    comp.css(_kf("rcled", led, dur))
    # zoom: ease between the points, never closer than a receipt's bottom allows
    comp.css(_kf("rczoom", [(t, f"transform:scale({z:.4f})", "cubic-bezier(.4,0,.3,1)") for t, z in sorted(zooms)],
                 dur))

    # ---- photos: the first is on the counter at frame 0, each next one lands on the pile
    photos = [_photo(ctx, picks[0][0], 0, None)]
    for k in range(1, n):
        s = HOOK + k * R
        photos.append(_photo(ctx, picks[k][0], k, s + .08))
        cues.append((s + .08, "paper"))

    # film grain and a soft vignette sit under the printer: nothing covers the label
    rig = (_pen(806, 990, 16) + "".join(photos) + "".join(pr.html(dur) for pr in prints)
           + '<div class="rc-lipshade"></div><div class="rc-grain"></div><div class="rc-vig"></div>' + _printer(dur))
    comp.add(f'<div class="full" style="z-index:0;background:#6b4a2e;overflow:hidden">'
             f'<div class="rc-cam"><div class="rc-zoom" style="{_a("rczoom", 0, dur)}">'
             f'<div class="rc-counter"></div><div class="rc-rig">{rig}</div>'
             f'</div></div></div>')
    comp.add(PREP_JS)
    comp.add(ART_JS)
    for t, kind in cues:
        comp.cue(t, kind)
    comp.cues.sort()
    return comp
