"""
YEARBOOK -- Guess the Season and Season Throwback as pages of a school
yearbook ("Locker High"): class photos on the mottled blue school backdrop,
names in serif, notes in blue ballpoint, and a lime USE CODE: BAD sticky note
on every frame, in the page's bottom right corner (it stays put while the
pages turn under it).

The paper runs to the frame's edges; the page's type, photos, pen and the note
sit inside the apps' safe box (cc_safe), so no app's header, buttons or
caption ever covers them. Only the page number sits below it, as decoration.

Guess the Season
    0:00  hook      the class page: every round's photo with "SEASON ?" under
                    it, "which season??" in pen -- then the page turns
    0:03  rounds    one page per round (9.5 s): the photo big, its name and
                    rarity, a ballot with the four seasons. The pen writes the
                    round number, counts 3-2-1 in the margin, ticks the right
                    box, greys the others and writes the season under the name.
                    The page turns to the next.
    outro           back on the class page, the pen fills in the answer key and
                    asks how many you got

Season Throwback
    0:00  hook      the season's cover page: two of the class, big, and
                    "8 skins. how many do you remember?" -- the page turns
    0:03  the class page, every slot "not pictured" at first. Each cosmetic's
                    print is laid over the page big, with its name and rarity
                    and type (6.5 s), then set into its slot. The page fills
                    photo by photo.
    outro           the finished page, "which one did you own?"

Facts on screen are the classic formats': names, rarity and type, the four
season options and the season each was introduced in.

Photo lab (cc_look_caseboard uses it too): the art becomes photos in the
browser, once, before frame 0 -- the renderer has no PIL. A canvas finds the
figure in the render (the biggest connected shape, measured on the opaque area
only, so props, floating bits and the real files' wide margins don't fool it),
its head and height, then draws a head-and-shoulders crop (or the whole item,
for gear and for anything that isn't a standing figure) onto a backdrop with a
flash shadow, a light film grade and grain, and swaps it in as the <img>.
Missing or broken art gets the yearbook's "photo not available" silhouette.
"""

import math

from cc_looks import KIT_CSS, LIME, PREP_JS, pad_to, rough_arrow, rough_check, stroke_static, stroke_svg, tex, write_on
from cc_motion import RARITY, SAFE_BOTTOM, SAFE_LEFT, SAFE_RIGHT, SAFE_RIGHT_TOP, SAFE_TOP, W, Comp, esc
from cc_safe import COVER_TOP

# ------------------------------------------------------------------ photo lab

PHOTO_JS = r"""<script>(() => {
  const prev = window.__ready;
  const BACKDROP = "%BACKDROP%";
  const loadImg = (src) => new Promise((res) => {
    if (!src) return res(null);
    const im = new Image();
    im.onload = () => res(im.naturalWidth ? im : null);
    im.onerror = () => res(null);
    im.src = src;
  });
  const rand = (seed) => {            // mulberry32: the same photo every render
    let a = (seed * 2654435761) >>> 0;
    return () => {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = Math.imul(a ^ (a >>> 15), a | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  // Where the figure is: the biggest connected opaque shape (after closing
  // small gaps), its top, height, head centre and head width, in image pixels.
  // Measured on the opaque region only, so wide transparent margins (the real
  // files are squares) change nothing.
  function grid(im, sx, sy, sw, sh) {
    const N = 240, k = N / Math.max(sw, sh);
    const w = Math.max(8, Math.round(sw * k)), h = Math.max(8, Math.round(sh * k));
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const g = c.getContext('2d', {willReadFrequently: true});
    g.drawImage(im, sx, sy, sw, sh, 0, 0, w, h);
    const px = g.getImageData(0, 0, w, h).data;
    const A = new Uint8Array(w * h);
    let clear = 0;
    for (let i = 0; i < w * h; i++) {
      const a = px[i * 4 + 3];
      if (a < 24) clear++;
      A[i] = a > 90 ? 1 : 0;
    }
    return {w, h, kx: w / sw, ky: h / sh, A, clear};
  }

  function measure(im) {
    const nw = im.naturalWidth, nh = im.naturalHeight;
    const M = {nw, nh};
    const G0 = grid(im, 0, 0, nw, nh);
    M.opaque = G0.clear < G0.w * G0.h * .02;
    if (M.opaque) return M;
    let bx0 = G0.w, by0 = G0.h, bx1 = -1, by1 = -1;
    for (let i = 0; i < G0.w * G0.h; i++) {
      if (!G0.A[i]) continue;
      const x = i % G0.w, y = (i / G0.w) | 0;
      if (x < bx0) bx0 = x; if (x > bx1) bx1 = x; if (y < by0) by0 = y; if (y > by1) by1 = y;
    }
    if (bx1 < 0) { M.empty = true; return M; }
    M.cut = by1 >= G0.h - 2;           // the render stops at the image's bottom edge
    // the opaque region, with a cell of margin, measured again at full resolution
    const ox = Math.max(0, (bx0 - 1) / G0.kx), oy = Math.max(0, (by0 - 1) / G0.ky);
    const ow = Math.min(nw, (bx1 + 2) / G0.kx) - ox, oh = Math.min(nh, (by1 + 2) / G0.ky) - oy;
    const G = grid(im, ox, oy, ow, oh);
    const w = G.w, h = G.h, A = G.A;
    const r = 2, T = new Uint8Array(w * h), D = new Uint8Array(w * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let v = 0;
      for (let d = -r; d <= r && !v; d++) { const xx = x + d; if (xx >= 0 && xx < w && A[y * w + xx]) v = 1; }
      T[y * w + x] = v;
    }
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let v = 0;
      for (let d = -r; d <= r && !v; d++) { const yy = y + d; if (yy >= 0 && yy < h && T[yy * w + x]) v = 1; }
      D[y * w + x] = v;
    }
    const L = new Int32Array(w * h).fill(-1), stack = new Int32Array(w * h), sizes = [];
    for (let i = 0; i < w * h; i++) {
      if (!D[i] || L[i] >= 0) continue;
      const id = sizes.length;
      let n = 0, sp = 0;
      stack[sp++] = i; L[i] = id;
      while (sp) {
        const j = stack[--sp];
        if (A[j]) n++;
        const x = j % w, y = (j / w) | 0;
        if (x > 0 && D[j - 1] && L[j - 1] < 0) { L[j - 1] = id; stack[sp++] = j - 1; }
        if (x < w - 1 && D[j + 1] && L[j + 1] < 0) { L[j + 1] = id; stack[sp++] = j + 1; }
        if (y > 0 && D[j - w] && L[j - w] < 0) { L[j - w] = id; stack[sp++] = j - w; }
        if (y < h - 1 && D[j + w] && L[j + w] < 0) { L[j + w] = id; stack[sp++] = j + w; }
      }
      sizes.push(n);
    }
    const total = sizes.reduce((s, v) => s + v, 0);
    if (!sizes.length || total < 40) { M.empty = true; return M; }
    let best = 0;
    for (let i = 1; i < sizes.length; i++) if (sizes[i] > sizes[best]) best = i;
    // every shape that matters (for whole items), and the main figure
    let ax0 = w, ay0 = h, ax1 = -1, ay1 = -1, x0 = w, y0 = h, x1 = -1, y1 = -1;
    const rows = new Int32Array(h), xs = [];
    for (let i = 0; i < w * h; i++) {
      if (!A[i]) continue;
      const x = i % w, y = (i / w) | 0;
      if (sizes[L[i]] >= total * .015) {
        if (x < ax0) ax0 = x; if (x > ax1) ax1 = x; if (y < ay0) ay0 = y; if (y > ay1) ay1 = y;
      }
      if (L[i] !== best) continue;
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      rows[y]++; xs.push(x);
    }
    const fh0 = y1 - y0 + 1;
    // the top of the head: skip thin things above it (antennae, blades, spikes)
    const thr = Math.max(2, fh0 * .045);
    let top = y0;
    while (top < y1 && rows[top] < thr) top++;
    if (top - y0 > fh0 * .25) top = y0;
    // the head: the heaviest run of columns in the band just under the top
    const band = Math.max(3, Math.round(fh0 * .12));
    const hist = new Float64Array(w);
    for (let y = top; y < Math.min(h, top + band); y++)
      for (let x = x0; x <= x1; x++) if (A[y * w + x] && L[y * w + x] === best) hist[x]++;
    let bestRun = null, run = null, gap = 0;
    for (let x = x0; x <= x1 + 1; x++) {
      const v = x <= x1 ? hist[x] : 0;
      if (v > 0) {
        if (!run) run = {a: x, b: x, s: 0, m: 0};
        run.b = x; run.s += v; run.m += v * x; gap = 0;
      } else if (run && ++gap > 3) {
        if (!bestRun || run.s > bestRun.s) bestRun = run;
        run = null; gap = 0;
      }
    }
    if (run && (!bestRun || run.s > bestRun.s)) bestRun = run;
    xs.sort((p, q) => p - q);
    const bodyX = xs[xs.length >> 1];
    const headX = bestRun ? bestRun.m / bestRun.s : bodyX;
    const headW = bestRun ? bestRun.b - bestRun.a + 1 : (x1 - x0) * .3;
    const X = (v) => ox + v / G.kx, Y = (v) => oy + v / G.ky;
    Object.assign(M, {top: Y(top), fh: fh0 / G.ky, fw: (x1 - x0 + 1) / G.kx, headX: X(headX + .5),
      bodyX: X(bodyX + .5), headW: headW / G.kx, x0: X(x0), x1: X(x1 + 1), y0: Y(y0), y1: Y(y1 + 1),
      all: {x: X(ax0), y: Y(ay0), w: (ax1 - ax0 + 1) / G.kx, h: (ay1 - ay0 + 1) / G.ky}});
    return M;
  }

  // The part of the image the photo shows, in image pixels.
  function framing(M, crop, aspect) {
    if (M.opaque) {                    // a finished picture: keep its upper middle
      let ch = M.nh * (crop === 'fit' ? 1 : .7), cw = ch * aspect;
      if (cw > M.nw) { cw = M.nw; ch = cw / aspect; }
      return {x: (M.nw - cw) / 2, y: crop === 'fit' ? (M.nh - ch) / 2 : M.nh * .02, w: cw, h: ch};
    }
    // Not a standing figure (a scythe, a creature wider than tall, a bust):
    // show all of it.
    if (crop !== 'fit' && M.fh < M.fw * 1.25) crop = 'fit';
    if (crop === 'fit') {              // the whole item, with a margin
      const a = M.all, pad = 1.24;
      let cw = a.w * pad, ch = a.h * pad;
      if (cw / ch > aspect) ch = cw / aspect; else cw = ch * aspect;
      // a render cut off at the bottom stays on the photo's bottom edge
      const y = M.cut ? a.y + a.h - ch * .98 : a.y + a.h / 2 - ch / 2;
      return {x: a.x + a.w / 2 - cw / 2, y, w: cw, h: ch};
    }
    const head = crop === 'head' || crop === 'close';
    const kf = crop === 'close' ? .38 : head ? .43 : .64;
    // never so tight that the head fills the photo (busts, bulky suits)
    let ch = Math.max(M.fh * kf, Math.min(M.headW * (head ? 2.2 : 3.2), M.fh * (head ? .6 : .8)));
    const cw = ch * aspect;
    const cx = head ? M.headX : M.headX * .6 + M.bodyX * .4;
    const y = M.top - ch * (head ? .1 : .07);
    return {x: cx - cw / 2, y, w: cw, h: ch};
  }

  let back = null, grainTile = null;
  function grain(g, W, H, amount, seed) {
    if (!grainTile) {
      grainTile = document.createElement('canvas'); grainTile.width = grainTile.height = 160;
      const q = grainTile.getContext('2d'), d = q.createImageData(160, 160), R = rand(7);
      for (let i = 0; i < d.data.length; i += 4) {
        const v = 128 + (R() + R() + R() - 1.5) * 120;
        d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255;
      }
      q.putImageData(d, 0, 0);
    }
    g.save();
    g.globalCompositeOperation = 'overlay'; g.globalAlpha = amount;
    const R = rand(seed), ox = -R() * 160, oy = -R() * 160;
    for (let y = oy; y < H; y += 160) for (let x = ox; x < W; x += 160) g.drawImage(grainTile, x, y);
    g.restore();
  }

  function backdrop(g, W, H, kind, seed, bg) {
    const R = rand(seed);
    if (kind === 'school' && back) {
      const s = Math.max(W / back.width, H / back.height) * (1.1 + R() * .5);
      g.drawImage(back, -R() * (back.width * s - W), -R() * (back.height * s - H), back.width * s, back.height * s);
      let l = g.createRadialGradient(W * .5, H * .38, 0, W * .5, H * .38, Math.max(W, H) * .62);
      l.addColorStop(0, 'rgba(255,250,240,.26)'); l.addColorStop(1, 'rgba(255,250,240,0)');
      g.fillStyle = l; g.fillRect(0, 0, W, H);
    } else {
      const [c0, c1] = bg || ['#ddd6c8', '#78706a'];
      const l = g.createRadialGradient(W * .5, H * .36, 0, W * .5, H * .36, Math.max(W, H) * .8);
      l.addColorStop(0, c0); l.addColorStop(1, c1);
      g.fillStyle = l; g.fillRect(0, 0, W, H);
    }
  }

  function vignette(g, W, H, amount) {
    const v = g.createRadialGradient(W * .5, H * .45, Math.min(W, H) * .35, W * .5, H * .45, Math.hypot(W, H) * .62);
    v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, `rgba(12,10,8,${amount})`);
    g.fillStyle = v; g.fillRect(0, 0, W, H);
  }

  function silhouette(g, W, H, label) {
    // "photo not available": a plain head-and-shoulders outline, as yearbooks print it
    g.save();
    g.fillStyle = 'rgba(30,40,60,.38)';
    const cx = W / 2, u = Math.min(W, H * .85);
    g.beginPath(); g.ellipse(cx, H * .40, u * .17, u * .21, 0, 0, Math.PI * 2); g.fill();
    g.beginPath();
    g.moveTo(cx - u * .42, H + 2);
    g.bezierCurveTo(cx - u * .42, H * .74, cx - u * .2, H * .66, cx, H * .66);
    g.bezierCurveTo(cx + u * .2, H * .66, cx + u * .42, H * .74, cx + u * .42, H + 2);
    g.fill();
    g.fillStyle = 'rgba(255,255,255,.85)';
    g.font = `500 ${Math.round(u * .075)}px Oswald, sans-serif`;
    g.textAlign = 'center';
    g.fillText(label, cx, H * .14);
    g.restore();
  }

  async function develop(img) {
    const W = +img.dataset.w, H = +img.dataset.h, S = +(img.dataset.s || 1);
    const kind = img.dataset.ph, crop = img.dataset.crop || 'head', seed = +(img.dataset.seed || 1);
    const film = img.dataset.film || 'school';
    const bg = img.dataset.bg ? img.dataset.bg.split('|') : null;
    const cw = Math.round(W * S), ch = Math.round(H * S);
    const c = document.createElement('canvas'); c.width = cw; c.height = ch;
    const g = c.getContext('2d');
    g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
    backdrop(g, cw, ch, kind, seed, bg);
    const im = await loadImg(img.dataset.src);
    const M = im ? measure(im) : null;
    if (!M || M.empty) {
      if (img.dataset.none !== '-') silhouette(g, cw, ch, img.dataset.none || '');
    } else {
      const f = framing(M, crop, cw / ch), sc = cw / f.w;
      g.save();
      if (!M.opaque) {                 // the flash throws a soft shadow on the backdrop
        g.shadowColor = kind === 'school' ? 'rgba(14,22,40,.5)' : 'rgba(30,22,14,.45)';
        g.shadowBlur = 22 * S * (cw / (W * S)) + cw * .02;
        g.shadowOffsetX = cw * .025; g.shadowOffsetY = cw * .012;
      }
      g.drawImage(im, -f.x * sc, -f.y * sc, M.nw * sc, M.nh * sc);
      g.restore();
    }
    // print the photo: a slight film grade, fall-off and grain
    const out = document.createElement('canvas'); out.width = cw; out.height = ch;
    const o = out.getContext('2d');
    const blank = !M || M.empty;
    o.filter = film === 'instant'
      ? `contrast(.86) brightness(1.06) saturate(.84) sepia(.16) blur(${(.45 * S).toFixed(2)}px)`
      : blank && img.dataset.none !== 'PHOTO NOT AVAILABLE'
        ? 'grayscale(.65) brightness(1.16) contrast(.72)'   // an empty slot: quieter than any photo
        : 'contrast(.96) saturate(.94) sepia(.07)';
    o.drawImage(c, 0, 0);
    o.filter = 'none';
    vignette(o, cw, ch, film === 'instant' ? .34 : .22);
    grain(o, cw, ch, film === 'instant' ? .16 : .11, seed);
    img.src = out.toDataURL('image/jpeg', .9);
    if (img.decode) { try { await img.decode(); } catch (e) {} }
    img.dataset.done = M ? (M.empty ? 'empty' : (M.opaque ? 'opaque' : 'cut')) : 'none';
  }

  window.__ready = (async () => {
    try {
      back = await loadImg(BACKDROP);
      await document.fonts.ready;
      try { await document.fonts.load('500 40px Oswald'); } catch (e) {}
      for (const img of document.querySelectorAll('img[data-ph]')) {
        try { await develop(img); } catch (e) { img.dataset.done = 'error'; }
      }
    } catch (e) {}
    if (prev) { await prev; }
  })();
})();</script>"""

BLANK = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"


def photo_lab() -> str:
    """The photo lab script. Add it with comp.add() AFTER PREP_JS: it chains
    onto window.__ready, so frame 0 waits for every photo."""
    return PHOTO_JS.replace("%BACKDROP%", tex("school-backdrop.jpg"))


def photo(art: str, w: float, h: float, crop: str = "head", seed: int = 1, kind: str = "school",
          film: str = "school", scale: float = 1.0, bg: str = "", none: str = "PHOTO NOT AVAILABLE",
          style: str = "") -> str:
    """An <img> the photo lab develops: crop 'head' (head and shoulders),
    'three' (head to thigh) or 'fit' (the whole item). Until it's developed it
    shows the backdrop colour, so nothing half-made can reach a frame."""
    return (f'<img data-ph="{kind}" data-crop="{crop}" data-film="{film}" data-w="{w:.0f}" data-h="{h:.0f}" '
            f'data-s="{scale:g}" data-seed="{seed}" data-none="{esc(none)}"'
            + (f' data-bg="{bg}"' if bg else "")
            + f' data-src="{art}" src="{BLANK}" style="display:block;width:{w:.0f}px;height:{h:.0f}px;'
              f'background:#5d7391;{style}">')


# ------------------------------------------------------------------ the page

HOOK = 3.0
R1 = 9.5            # Guess the Season: one round, as cc_quiz.R1
T_REV = 6.3         # the answer lands this far into a round, as cc_quiz.T_REV
R3 = 6.5            # Season Throwback: one item's turn, as cc_quiz.R3
FLIP = .6           # a page turn
INK, PEN = "#1f2430", "#1d3fa8"
FONTS = ("Old Standard TT", "Oswald", "Caveat", "Permanent Marker")

# The paper, the spine's shadow and the folio run to the frame's edges. The
# page's type, photos, pen and the code note stay inside the apps' safe box
# (cc_safe): x 60-1020 above y 740, x 60-900 below it, y 230-1420 -- and on
# frame 0, the cover, text starts at y 285.
X0 = SAFE_LEFT + 10              # 70: the page's left margin
X1 = SAFE_RIGHT - 4              # 896: the body's right edge, beside the apps' buttons
XH = SAFE_RIGHT_TOP - 10         # 1010: the head's right edge, above them
BODY_W = X1 - X0                 # 826
TOP = SAFE_TOP + 14              # 244: a page's first line
TOP0 = COVER_TOP + 7             # 292: the same on frame 0
FOOT = SAFE_BOTTOM - 6           # 1414: the lowest thing on the page ends here


def _outline(w: float, h: float, rot: float) -> tuple:
    """Width and height of a w x h box turned rot degrees."""
    c, s = math.cos(math.radians(rot)), abs(math.sin(math.radians(rot)))
    return w * c + h * s, w * s + h * c


def _at(w: float, h: float, rot: float, right: float, bottom: float) -> tuple:
    """left, top of a w x h box turned rot degrees whose outline ends at right, bottom."""
    bw, bh = _outline(w, h, rot)
    return right - (bw + w) / 2, bottom - (bh + h) / 2


# The lime sticky note (w, h, tilt), in the page's bottom right corner on every
# frame, and the bigger one the outro slaps on over it. Everything else on the
# pages stays above NOTE_TOP where it could meet them (left of NOTE_LEFT it can
# go lower).
NOTE, BIG = (300, 196, 3), (336, 204, 3)
NOTE_LEFT = X1 - 2 - _outline(*NOTE)[0]          # 584
NOTE_TOP = FOOT - _outline(*BIG)[1]              # 1193: the big one's top

CSS = """
.yb-page{position:absolute;inset:0;overflow:hidden;background:#eeeae1 url(%(paper)s) center/cover}
.yb-serif{font-family:'Old Standard TT',Georgia,serif;color:#1f2430}
.yb-sc{font-family:Oswald,sans-serif;font-weight:500;letter-spacing:.16em;text-transform:uppercase;color:#555c6b;
  line-height:1;white-space:nowrap}
.yb-it{font-family:'Old Standard TT',Georgia,serif;font-style:italic;color:#474e5c;white-space:nowrap;line-height:1.1}
.yb-pen{font-family:Caveat,cursive;font-weight:700;color:#1d3fa8;line-height:1;white-space:nowrap}
.yb-blank{color:#6f7480}
.yb-photo{position:absolute;box-shadow:0 1px 1px rgba(0,0,0,.25),0 2px 5px rgba(0,0,0,.08)}
.yb-turn{position:absolute;inset:0;transform-origin:0 50%%;backface-visibility:hidden}
.yb-cam{position:absolute;inset:0;perspective:3400px;perspective-origin:540px 820px}
@keyframes ybflip{0%%{transform:rotateY(0deg)}100%%{transform:rotateY(-100deg)}}
@keyframes ybdark{from{opacity:0}to{opacity:.5}}
@keyframes ybshade{from{opacity:.6}to{opacity:0}}
@keyframes ybfade{to{opacity:.3}}
@keyframes ybgone{to{opacity:0}}
@keyframes ybwipe{from{clip-path:inset(-25%% 100%% -25%% 0)}to{clip-path:inset(-25%% -2%% -25%% 0)}}
"""


def _a(name: str, t: float, dur: float, ease: str = "cubic-bezier(.2,.8,.2,1)", extra: str = "") -> str:
    return f"animation:{name} {dur:.2f}s {ease} {t:.3f}s 1 normal both;{extra}"


def _setup(comp: Comp):
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(CSS % {"paper": tex("yearbook-page.jpg")})


def _paper(page_no: int = 0) -> str:
    """The page itself: paper, the shadow of the book's spine, and the page
    number at the foot (decoration, down where the apps put their captions)."""
    return ('<div class="abs" style="left:0;top:0;width:120px;height:1920px;background:linear-gradient(90deg,'
            'rgba(58,44,28,.24),rgba(58,44,28,.08) 38%,rgba(58,44,28,0))"></div>'
            '<div class="abs" style="right:0;top:0;width:26px;height:1920px;background:linear-gradient(270deg,'
            'rgba(0,0,0,.07),rgba(0,0,0,0))"></div>'
            + (f'<div class="abs yb-serif" data-safe="ignore" style="left:0;width:1080px;top:1596px;'
               f'text-align:center;font-size:30px;color:#9aa0aa">{page_no}</div>' if page_no else ""))


def _code_note(big: bool = False, t: float = 0) -> str:
    """USE CODE: BAD on a lime sticky note stuck to the page, #EpicPartner on it.
    big=True: the outro's bigger note, slapped on over it at t. Either way the
    whole note sits inside the safe box, in the page's bottom right corner."""
    w, h, rot = BIG if big else NOTE
    x, y = _at(w, h, rot, X1 - 2, FOOT)
    uc, bad, ep = (48, 132, 25) if big else (44, 124, 24)
    anim = _a("lkslap", t, .5, extra=f"--r:{rot}deg;") if big else ""
    return (f'<div class="abs" data-safe="key" data-name="code" style="left:{x:.1f}px;top:{y:.1f}px;width:{w}px;'
            f'height:{h}px;transform:rotate({rot}deg);'
            f'background:linear-gradient(180deg,#e2f63a 0%,{LIME} 22%,#e6fd3c 70%,#d9ef33 100%);'
            f'box-shadow:0 2px 2px rgba(0,0,0,.18),0 14px 16px -8px rgba(0,0,0,.35);display:flex;'
            f'flex-direction:column;align-items:center;justify-content:center;padding-top:2px;{anim}">'
            f'<div style="font-family:\'Permanent Marker\';font-size:{uc}px;line-height:1;color:#111">USE CODE:</div>'
            f'<div style="font-family:\'Permanent Marker\';font-size:{bad}px;line-height:.84;color:#111;'
            f'margin-top:2px">BAD</div>'
            f'<div style="font-family:Oswald,sans-serif;font-weight:500;font-size:{ep}px;line-height:1.2;'
            f'letter-spacing:.06em;color:#353b0c;margin-top:5px">#EpicPartner</div></div>')


def _code(comp: Comp, t_big: float):
    """The note on every frame; in the outro a bigger one is slapped on over it."""
    comp.add(f'<div class="full" style="z-index:60;{_a("lkout", t_big + .35, .1, "linear")}">{_code_note()}</div>')
    comp.add(f'<div class="full" style="z-index:61">{_code_note(True, t_big)}</div>')
    comp.cue(t_big, "paper")


def _header(top: float, title: str, right: str = "", size: int = 88, over: str = "", sub: str = "") -> tuple:
    """The page's head: the yearbook's name (and `right`) in small caps, an
    italic line over the title or under it, the serif title, a double rule.
    Returns (html, the y under the rule)."""
    out = [f'<div class="abs yb-sc" style="left:{X0}px;top:{top:.0f}px;font-size:30px;letter-spacing:.3em">'
           f'Locker High Yearbook</div>']
    if right:
        out.append(f'<div class="abs yb-sc" style="right:{W - XH}px;top:{top:.0f}px;font-size:30px;'
                   f'letter-spacing:.16em">{esc(right)}</div>')
    y = top + 38
    if over:
        out.append(f'<div class="abs yb-it" style="left:{X0}px;top:{y:.0f}px;font-size:40px">{esc(over)}</div>')
        y += 44
    out.append(f'<div class="abs yb-serif" data-fit="{XH - X0 + 4}" style="left:{X0 - 4}px;top:{y:.0f}px;'
               f'font-size:{size}px;font-weight:700;line-height:1;white-space:nowrap">{esc(title)}</div>')
    y += size + 6
    if sub:
        out.append(f'<div class="abs yb-it" data-fit="520" style="left:{X0}px;top:{y:.0f}px;font-size:36px">'
                   f'{esc(sub)}</div>')
        y += 40
    y += 10
    out.append(f'<div class="abs" style="left:{X0}px;top:{y:.0f}px;width:{XH - X0}px;height:3px;background:{INK}">'
               f'</div><div class="abs" style="left:{X0}px;top:{y + 7:.0f}px;width:{XH - X0}px;height:1px;'
               f'background:{INK}"></div>')
    return "".join(out), y + 8


def _turn(inner: str, t_end: float) -> str:
    """A page that turns over at t_end (FLIP seconds before it, the turn starts),
    darkening as it leaves the light."""
    t = t_end - FLIP
    return (f'<div class="yb-cam"><div class="yb-turn" style="{_a("ybflip", t, FLIP, "cubic-bezier(.42,.06,.58,.94)")}">'
            f'{inner}<div class="full" style="background:linear-gradient(90deg,rgba(0,0,0,.05),rgba(0,0,0,.5));'
            f'{_a("ybdark", t, FLIP, "ease-in")}"></div></div></div>')


def _landing(t: float) -> str:
    """The shadow the turning page throws on the page under it."""
    return (f'<div class="full" style="background:linear-gradient(90deg,rgba(30,22,12,.5),rgba(30,22,12,.12) 70%,'
            f'rgba(30,22,12,0));{_a("ybshade", t, FLIP, "ease-in")}"></div>')


def _kind(it: dict) -> str:
    """"Epic Outfit", "MARVEL SERIES Outfit": rarity and type, as the classic shows them."""
    return " ".join(x for x in ((it.get("rarity_label") or "").strip(), (it.get("type") or "").strip()) if x)


def _season(label: str) -> str:
    """"Chapter 1 · Season 5" -> "Chapter 1, Season 5"; "Chapter 2 · Remix" -> "Chapter 2 Remix"."""
    a, _, b = (label or "").partition(" · ")
    if not b:
        return label or ""
    return f"{a}, {b}" if b.lower().startswith("season") else f"{a} {b}"


def _gear(items: list) -> bool:
    return any((it.get("type") or "").lower() not in ("outfit", "character") for it in items)


def _noun(items: list) -> str:
    """What the items are, in plain words: "skins", or "pickaxes, gliders & back blings"."""
    kinds = []
    for it in items:
        t = (it.get("type") or "").strip().lower()
        p = {"outfit": "skins", "character": "skins", "pickaxe": "pickaxes", "glider": "gliders",
             "back bling": "back blings", "emote": "emotes"}.get(t, "items")
        if p not in kinds:
            kinds.append(p)
    if len(kinds) == 1:
        return kinds[0]
    order = ["skins", "pickaxes", "gliders", "back blings", "emotes", "items"]
    kinds.sort(key=order.index)
    return ", ".join(kinds[:-1]) + " & " + kinds[-1]


def _caption(x: float, y: float, w: float, name: str, name_px: int, lines: str, gap: int = 6,
             style: str = "") -> str:
    """Name in serif (two lines at most, shrinking to fit) with whatever goes under it."""
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;display:flex;'
            f'flex-direction:column;gap:{gap}px;{style}">'
            f'<div class="yb-serif" data-fit="{w:.0f}" data-lines="2" style="width:{w:.0f}px;font-size:{name_px}px;'
            f'font-weight:700;line-height:1.04">{esc(name)}</div>{lines}</div>')


# ------------------------------------------------------------------ Guess the Season

# The class page: three photos a row, two rows, under the head; room under each
# for a two-line name and the season line, and the bottom of the page free for
# the pen and the note.
CELL_W, CELL_H, CELL_NAME = 250, 210, 40
CELL_GAP = (BODY_W - 3 * CELL_W) / 2                               # 38
GRID_Y = 496
ROW = CELL_H + 8 + round(CELL_NAME * 1.04 * 2) + 4 + 34 + 13       # 351


def _cell(art: str, x: float, y: float, it: dict, seed: int, crop: str, answer: str = "",
          t_answer: float = 0) -> str:
    """A class photo with the name under it and "SEASON ?"; with an answer,
    the pen writes it over that line at t_answer."""
    line = '<div class="yb-sc yb-blank" style="font-size:30px;height:34px">Season ?</div>'
    if answer:
        line = (f'<div style="position:relative;height:34px">'
                f'<div class="yb-sc yb-blank" style="font-size:30px;{_a("ybgone", t_answer, .2, "linear")}">'
                f'Season ?</div>'
                f'<div class="yb-pen" data-fit="{CELL_W - 6}" style="position:absolute;left:0;top:-8px;'
                f'font-size:42px;transform:rotate(-2deg);transform-origin:0 50%;'
                f'{write_on(t_answer + .05, .5, 14)}">{esc(answer)}</div></div>')
    return (f'<div class="yb-photo" style="left:{x:.0f}px;top:{y:.0f}px">'
            f'{photo(art, CELL_W, CELL_H, crop, seed)}</div>'
            + _caption(x, y + CELL_H + 8, CELL_W, it["name"], CELL_NAME, line, 4))


def _class_grid(ctx, items: list, crop: str, answers: list = None, t_answer: float = 0,
                step: float = .45) -> str:
    out = []
    for i, it in enumerate(items):
        r, c = divmod(i, 3)
        out.append(_cell(ctx.art(it), X0 + c * (CELL_W + CELL_GAP), GRID_Y + r * ROW, it, 11 + i, crop,
                         answers[i] if answers else "", t_answer + i * step))
    return "".join(out)


def _quiz_no(spec: dict) -> str:
    return f"Quiz No. {spec['episode']}" if spec.get("episode") else ""


def _gs_class_page(ctx, spec, items: list, crop: str, answers: list = None, content_end: float = 0) -> tuple:
    """The quiz's class page: at the start (the thumbnail) and again at the end,
    when the pen fills in the answer key (answers given). Returns (html, sounds,
    the time the pen is done)."""
    n = len(items)
    final = bool(answers)
    head, _ = _header(TOP0, "Guess the Season", _quiz_no(spec), 88, sub="When did each one come out?")
    sounds, done = [], .45 + .6
    t = content_end + .3
    html = [_paper(40), head, _class_grid(ctx, items, crop, answers, t)]
    # The pen: a word at the head's right, and a note in the free space -- the
    # empty sixth photo's place when there are five rounds, else the page's
    # bottom left, beside the code note.
    spare = n % 3
    fx, fy = X0 + spare * (CELL_W + CELL_GAP) + 6, GRID_Y + ROW + 24      # the empty place
    word = lambda anim, text: (f'<div class="abs yb-pen" style="right:{W - XH + 6}px;top:402px;font-size:60px;'
                               f'transform:rotate(-4deg);transform-origin:100% 50%;{anim}">{text}</div>')
    if final:
        html.append(word(write_on(content_end + .05, .45, 12), "answer key!"))
        sounds.append((content_end + .05, "pen"))
        sounds += [(t + i * .45, "pen") for i in range(n)]
        t_q = t + n * .45 + .25
        q = f"how many did you get out of {n}?"
        if spare:
            html.append(f'<div class="abs yb-pen" data-fit="{CELL_W}" data-lines="4" style="left:{fx}px;top:{fy}px;'
                        f'width:{CELL_W}px;font-size:56px;line-height:1.05;white-space:normal;'
                        f'transform:rotate(-3deg);{write_on(t_q, 1.1, 22)}">{esc(q)}</div>')
        else:
            html.append(f'<div class="abs yb-pen" data-fit="440" data-lines="2" style="left:{X0 + 4}px;'
                        f'top:{NOTE_TOP + 30}px;width:440px;font-size:60px;line-height:1.05;white-space:normal;'
                        f'transform:rotate(-3deg);{write_on(t_q, 1.1, 22)}">{esc(q)}</div>')
        sounds.append((t_q, "pen"))
        done = t_q + 1.1
    else:
        html.append(word("", "which season??"))
        html.append(stroke_static(rough_arrow(XH - 40, 474, X1 - CELL_W * .3, GRID_Y + 22, seed=8,
                                              head=20, curve=.3), PEN, 5))
        # "6 rounds." is on the page from frame 0; "no peeking!" gets written as it starts
        x, y = (fx, fy) if spare else (X0 + 6, NOTE_TOP + 24)
        fit = CELL_W - 10 if spare else 440
        html.append(f'<div class="abs yb-pen" data-fit="{fit}" style="left:{x}px;top:{y}px;font-size:70px;'
                    f'transform:rotate(-3deg)">{n} rounds.</div>'
                    f'<div class="abs yb-pen" data-fit="{fit}" style="left:{x + 4}px;top:{y + 86}px;font-size:70px;'
                    f'transform:rotate(-4deg);{write_on(.45, .6, 12)}">no peeking!</div>')
        sounds.append((.45, "pen"))
    return "".join(html), sounds, done


# the round page: the photo on the left, the ballot beside it, the name, its
# rarity and type and the season line under the photo
PH_X, PH_Y, PH_W, PH_H = X0, 400, 470, 670
BAL_X = PH_X + PH_W + 40                                   # 580
BAL_Y, BAL_PITCH, BAL_W = 490, 120, X1 - BAL_X             # four boxes, all left of the buttons
COUNT_Y = 962


def _gs_round(ctx, spec, it: dict, opts: list, answer: int, k: int, n: int, t0: float, crop: str) -> tuple:
    """One round's page. Printed: the photo, the name, the ballot. In pen: the
    round number as the page opens, the countdown, the tick in the right box
    and the season under the name."""
    rev = t0 + T_REV
    head, _ = _header(TOP, "Guess the Season", _quiz_no(spec), 80)
    html = [_paper(40 + k), head,
            f'<div class="abs yb-pen" style="right:{W - XH + 4}px;top:292px;font-size:64px;transform:rotate(-5deg);'
            f'transform-origin:100% 50%;{write_on(t0 + .2, .5, 12)}">round {k}/{n}</div>',
            f'<div class="yb-photo" style="left:{PH_X}px;top:{PH_Y}px">'
            f'{photo(ctx.art(it), PH_W, PH_H, "close" if crop == "head" else crop, 20 + k)}'
            f'</div>']
    answer_line = (f'<div style="position:relative;height:60px;margin-top:6px">'
                   f'<div class="yb-sc yb-blank" style="position:absolute;left:0;top:12px;font-size:30px;'
                   f'{_a("ybgone", rev + .3, .2, "linear")}">Introduced in: ?</div>'
                   f'<div class="yb-pen" data-fit="{NOTE_LEFT - PH_X - 14:.0f}" style="position:absolute;left:-2px;'
                   f'top:-6px;font-size:70px;transform:rotate(-2deg);transform-origin:0 50%;'
                   f'{write_on(rev + .35, .8, 20)}">{esc(_season(opts[answer]))}!</div></div>')
    html.append(_caption(PH_X, PH_Y + PH_H + 14, PH_W, it["name"], 54,
                         f'<div class="yb-sc" data-fit="{PH_W}" style="font-size:30px;margin-top:2px">'
                         f'{esc(_kind(it))}</div>' + answer_line))
    # the ballot
    html.append(f'<div class="abs yb-sc" style="left:{BAL_X}px;top:{PH_Y + 2}px;font-size:30px;color:{INK}">'
                f'Introduced in</div>'
                f'<div class="abs yb-it" style="left:{BAL_X}px;top:{PH_Y + 40}px;font-size:32px">tick one:</div>')
    for i, o in enumerate(opts):
        y = BAL_Y + i * BAL_PITCH
        chap, _, seas = o.partition(" · ")
        if not seas:                    # a label without a chapter part: one big line
            chap, seas = "", o
        fade = "" if i == answer else _a("ybfade", rev + .1, .35, "ease-out")
        html.append(f'<div class="abs" style="left:{BAL_X}px;top:{y}px;width:{BAL_W}px;height:96px;{fade}">'
                    f'<div class="abs" style="left:0;top:16px;width:48px;height:48px;border:3px solid {INK};'
                    f'background:rgba(255,255,255,.35)"></div>'
                    f'<div class="abs yb-sc" data-fit="{BAL_W - 66}" style="left:66px;top:0;font-size:30px;'
                    f'color:#4b5261">{esc(chap)}</div>'
                    f'<div class="abs yb-serif" data-fit="{BAL_W - 66}" style="left:64px;top:34px;font-size:52px;'
                    f'font-weight:700;line-height:1;white-space:nowrap">{esc(seas or chap)}</div></div>')
    by = BAL_Y + answer * BAL_PITCH
    html.append(stroke_svg(rough_check(BAL_X + 4, by + 60, 66, seed=k), PEN, 8, rev, .24))
    # the pen counts down under the ballot
    for j, d in enumerate("321"):
        html.append(f'<div class="abs yb-pen" style="left:{BAL_X + 20 + j * 100}px;top:{COUNT_Y}px;font-size:120px;'
                    f'transform:rotate({(-4, 2, -2)[j]}deg);{write_on(rev - 3 + j, .28, 8)}">{d}</div>')
    sounds = ([(t0 + .2, "pen")] + [(rev - 3 + j, "tick") for j in range(3)]
              + [(rev, "ding"), (rev, "pen"), (rev + .35, "pen")])
    return "".join(html), sounds


def guess_season(ctx, spec: dict, rounds: list) -> Comp:
    """rounds: [(item, options, answer index)], 5 or 6 of them."""
    n = len(rounds)
    items = [r[0] for r in rounds]
    crop = "fit" if spec.get("edition") == "gear" or _gear(items) else "head"
    content_end = HOOK + n * R1
    comp = Comp(pad_to(content_end))
    _setup(comp)

    # Under everything: the class page the last round turns over to (the answer key).
    answers = [_season(opts[ans]) for _, opts, ans in rounds]     # what the ballots marked
    base, sounds, done = _gs_class_page(ctx, spec, items, crop, answers, content_end)
    comp.add(f'<div class="yb-page" style="z-index:1">{base}{_landing(content_end - FLIP)}</div>')
    for s in sounds:
        comp.cue(*s)
    # frame 0: the class page with every photo, "which season??"
    hook, sounds, _ = _gs_class_page(ctx, spec, items, crop)
    for s in sounds:
        comp.cue(*s)
    comp.scene(0, HOOK, _turn(f'<div class="yb-page">{hook}</div>', HOOK), fade_in=.01, fade_out=.01, z=40)
    comp.cue(HOOK - FLIP, "flip")

    for k, (it, opts, ans) in enumerate(rounds, 1):
        t0 = HOOK + (k - 1) * R1
        page, sounds = _gs_round(ctx, spec, it, opts, ans, k, n, t0, crop)
        comp.scene(t0 - FLIP, t0 + R1, _turn(f'<div class="yb-page">{page}{_landing(t0 - FLIP)}</div>', t0 + R1),
                   fade_in=.01, fade_out=.01, z=40 - k)
        comp.cue(t0 + R1 - FLIP, "flip")
        for s in sounds:
            comp.cue(*s)

    _code(comp, done + .4)
    comp.add(PREP_JS)
    comp.add(photo_lab())
    comp.cues.sort()
    return comp


# ------------------------------------------------------------------ Season Throwback

# the print of the photo whose turn it is: laid over the page, big, centred on
# the page's body and clear of the code note
PR_B, PR_PW, PR_PH, PR_CAP = 22, 500, 560, 168
PR_W, PR_H = PR_PW + 2 * PR_B, PR_B + PR_PH + PR_CAP
PR_X, PR_Y = round(X0 + (BODY_W - PR_W) / 2), 444
T_IN, T_HOLD, T_PLACE = .05, .7, .55        # in each turn: lands; leaves for its slot this long before
                                             # the turn ends; takes this long to get there
SLOT_Y, SLOT_W, SLOT_NAME, SLOT_KIND = 446, 190, 34, 30


def _slots(n: int) -> tuple:
    """The class page's photo grid: (photo w, photo h, [(x, y)]). Four a row
    (three when there are six), inside the page's body and above the code note,
    with room under each photo for a two-line name and a two-line rarity and
    type. The photos have the print's shape, so a print laid into its slot
    lands exactly on it."""
    cols = 3 if n <= 6 else 4
    pw = SLOT_W
    ph = round(pw * PR_PH / PR_PW)
    gap = 60 if cols == 3 else (BODY_W - cols * pw) / (cols - 1)
    x0 = X0 + (BODY_W - cols * pw - (cols - 1) * gap) / 2
    pitch = ph + 8 + round(SLOT_NAME * 1.04 * 2) + 4 + round(SLOT_KIND * 1.12 * 2) + 12
    return pw, ph, [(x0 + (i % cols) * (pw + gap), SLOT_Y + (i // cols) * pitch) for i in range(n)]


def _print(comp: Comp, ctx, it: dict, i: int, t0: float, r: float, slot: tuple, pw: float, crop: str, kind: str,
           col: str) -> str:
    """The portrait as a print: slid in over the page, held, then laid into its
    slot on the page (where the page's own copy of the photo takes over). Its
    turn starts at t0 and lasts r seconds."""
    x, y = slot
    rot = (-2.2, 1.6, -1.4, 2.0)[i % 4]
    k = pw / PR_PW
    dx, dy = x - (PR_X + PR_B), y - (PR_Y + PR_B)
    name = comp.uid("ybprint")
    t1, t2, t3 = t0 + T_IN, t0 + r - T_HOLD, t0 + r - T_HOLD + T_PLACE
    d = comp.duration
    pct = lambda t: f"{t / d * 100:.4f}%"
    comp.css(f"@keyframes {name}{{0%{{transform:translate(640px,40px) rotate(9deg);opacity:0}}"
             f"{pct(t1 - .001)}{{transform:translate(640px,40px) rotate(9deg);opacity:0}}"
             f"{pct(t1)}{{transform:translate(640px,40px) rotate(9deg);opacity:1;"
             f"animation-timing-function:cubic-bezier(.2,.75,.25,1)}}"
             f"{pct(t1 + .5)}{{transform:translate(0,0) rotate({rot}deg);opacity:1;"
             f"animation-timing-function:ease-in-out}}"
             f"{pct(t2)}{{transform:translate(0,-8px) rotate({rot * .6:.2f}deg);opacity:1;"
             f"animation-timing-function:cubic-bezier(.5,0,.3,1)}}"
             f"{pct(t3 - .06)}{{transform:translate({dx:.1f}px,{dy:.1f}px) scale({k:.4f}) rotate(0deg);opacity:1}}"
             f"{pct(t3)}{{transform:translate({dx:.1f}px,{dy:.1f}px) scale({k:.4f}) rotate(0deg);opacity:0}}"
             f"100%{{transform:translate({dx:.1f}px,{dy:.1f}px) scale({k:.4f});opacity:0}}}}")
    comp.cue(t1 + .32, "paper")
    comp.cue(t3 - .05, "paper")
    return (f'<div class="abs" style="left:{PR_X}px;top:{PR_Y}px;width:{PR_W}px;height:{PR_H}px;'
            f'transform-origin:{PR_B}px {PR_B}px;animation:{name} {d:.3f}s linear 0s 1 normal both;'
            f'background:#fbfaf6;box-shadow:0 2px 3px rgba(0,0,0,.2),0 18px 30px -6px rgba(0,0,0,.38)">'
            f'<div class="abs" style="left:{PR_B}px;top:{PR_B}px">{photo(ctx.art(it), PR_PW, PR_PH, crop, 31 + i)}</div>'
            + _caption(PR_B, PR_B + PR_PH + 14, PR_PW, it["name"], 52,
                       f'<div class="yb-sc" data-fit="{PR_PW}" style="font-size:30px;display:flex;align-items:center">'
                       f'<i style="display:inline-block;width:.6em;height:.6em;background:{col};margin-right:.45em;'
                       f'flex:none"></i>{esc(kind)}</div>', 4)
            + '</div>')


def throwback(ctx, spec: dict, group: list, theme: dict = None) -> Comp:
    """group: 6 to 8 cosmetics from one season (spec["season"]), skins or gear."""
    n = len(group)
    gear = spec.get("edition") == "gear" or _gear(group)
    crop = "fit" if gear else "head"
    season = _season(theme["title"] if theme else spec.get("season", ""))
    noun = _noun(group)
    # Eight get R3 each, as the classic. Six or seven get a little longer each,
    # so the video doesn't end on a long still page (it runs at least 62 s).
    r3 = max(R3, (62.0 - 7.5 - HOOK) / n)
    content_end = HOOK + n * r3
    comp = Comp(pad_to(content_end))
    _setup(comp)

    # ---- the class page: "not pictured" until each print is laid into its slot
    pw, ph, slots = _slots(n)
    head, _ = _header(TOP, season, "Throwback", 84, over="Class of")
    page, prints = [_paper(12), head], []
    for i, (it, (x, y)) in enumerate(zip(group, slots)):
        t0 = HOOK + i * r3
        placed = t0 + r3 - T_HOLD + T_PLACE
        kind = _kind(it) + (f" · {theme['debut'](it)}" if theme and theme.get("debut") else "")
        col = RARITY.get(it.get("rarity", ""), "#9aa0a6")
        page.append(f'<div class="yb-photo" style="left:{x:.0f}px;top:{y:.0f}px">'
                    f'{photo("", pw, ph, crop, 61 + i, none="-" if gear else "")}</div>'
                    f'<div class="yb-photo" style="left:{x:.0f}px;top:{y:.0f}px;{_a("lkin", placed - .07, .05, "linear")}">'
                    f'{photo(ctx.art(it), pw, ph, crop, 31 + i)}</div>'
                    + _caption(x, y + ph + 8, pw, it["name"], SLOT_NAME,
                               f'<div class="yb-sc" data-fit="{pw}" data-lines="2" style="width:{pw}px;'
                               f'font-size:{SLOT_KIND}px;line-height:1.12;letter-spacing:.06em;'
                               f'white-space:normal"><i style="display:inline-block;width:.62em;height:.62em;'
                               f'background:{col};margin-right:.4em"></i>{esc(kind)}</div>', 4,
                               _a("ybwipe", placed, .4, "cubic-bezier(.3,.6,.4,1)")))
        prints.append(_print(comp, ctx, it, i, t0, r3, (x, y), pw, crop, kind, col))
    t_out = content_end + .35
    page.append(f'<div class="abs yb-pen" style="left:{X0 + 6}px;top:{NOTE_TOP + 12}px;font-size:68px;'
                f'line-height:1.02;transform:rotate(-3deg);{write_on(t_out, 1.0, 20)}">which one<br>did you own?</div>'
                f'<div class="abs yb-pen" style="left:{X0 + 26}px;top:{NOTE_TOP + 156}px;font-size:44px;'
                f'color:#2a4bb0;transform:rotate(-4deg);{write_on(t_out + 1.5, .8, 18)}">'
                f'stay legendary :) &ndash; BAD</div>')
    comp.cue(t_out, "pen")
    comp.cue(t_out + 1.5, "pen")
    # (It's under the cover until the cover turns, so it only shows from then:
    # on frame 0 nothing of it is there, not even hidden.)
    comp.add(f'<div class="yb-page" style="z-index:1;{_a("lkin", HOOK - FLIP - .02, .01, "linear")}">'
             f'{"".join(page)}{"".join(prints)}{_landing(HOOK - FLIP)}</div>')

    # ---- frame 0: the cover -- two of the class, big, and the question
    head, y = _header(TOP0, season, "Throwback", 88, over="Class of")
    cover = [_paper(11), head]
    cw, chh = (BODY_W - 26) / 2, 452
    for j, it in enumerate(group[:2]):
        x = X0 + j * (cw + 26)
        cover.append(f'<div class="yb-photo" style="left:{x:.0f}px;top:{y + 4:.0f}px">'
                     f'{photo(ctx.art(it), cw, chh, crop, 51 + j)}</div>'
                     + _caption(x, y + chh + 16, cw, it["name"], 48,
                                f'<div class="yb-sc" data-fit="{cw:.0f}" style="font-size:30px">'
                                f'{esc(_kind(it))}</div>'))
    # "8 skins." is there on frame 0; the question gets written as the video starts
    cover.append(f'<div class="abs" style="left:{X0 + 2}px;top:{y + chh + 150:.0f}px;width:480px;display:flex;'
                 f'flex-direction:column;gap:4px;transform:rotate(-3deg);transform-origin:0 0">'
                 f'<div class="yb-pen" data-fit="480" data-lines="2" style="width:480px;font-size:76px;'
                 f'line-height:1.02;white-space:normal">{n} {esc(noun)}.</div>'
                 f'<div class="yb-pen" data-fit="480" data-lines="2" style="width:480px;font-size:62px;'
                 f'line-height:1.04;white-space:normal;{write_on(.4, 1.0, 20)}">how many do you remember?</div></div>')
    comp.cue(.4, "pen")
    comp.scene(0, HOOK, _turn(f'<div class="yb-page">{"".join(cover)}</div>', HOOK), fade_in=.01, fade_out=.01, z=40)
    comp.cue(HOOK - FLIP, "flip")

    _code(comp, t_out + 2.6)
    comp.add(PREP_JS)
    comp.add(photo_lab())
    comp.cues.sort()
    return comp
