"""
YEARBOOK -- Guess the Season and Season Throwback as pages of a school yearbook.

Photo lab (shared with cc_look_caseboard): the cosmetics' art is turned into
photos in the browser, once, before frame 0 -- the renderer has no PIL. A
canvas measures each render's opaque pixels, finds the figure (the biggest
connected shape, so floating bits and props don't fool it), its head and its
height, then draws a head-and-shoulders crop onto a backdrop with a flash
shadow, a slight film grade and grain, and swaps the result in as the <img>.
Gear (pickaxes, gliders, back blings) gets the whole item instead of a crop.
"""

from cc_looks import tex

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
    from cc_motion import esc
    return (f'<img data-ph="{kind}" data-crop="{crop}" data-film="{film}" data-w="{w:.0f}" data-h="{h:.0f}" '
            f'data-s="{scale:g}" data-seed="{seed}" data-none="{esc(none)}"'
            + (f' data-bg="{bg}"' if bg else "")
            + f' data-src="{art}" src="{BLANK}" style="display:block;width:{w:.0f}px;height:{h:.0f}px;'
              f'background:#5d7391;{style}">')


# ------------------------------------------------------------------ the page

import math  # noqa: E402

from cc_looks import (KIT_CSS, LIME, PREP_JS, pad_to, rough_arrow, rough_check, rough_line,  # noqa: E402
                      stroke_static, stroke_svg, write_on)
from cc_motion import RARITY, Comp, esc  # noqa: E402

HOOK = 3.0
R1 = 9.5            # Guess the Season: one round, as cc_quiz.R1
T_REV = 6.3         # the answer lands this far into a round, as cc_quiz.T_REV
R3 = 6.5            # Season Throwback: one item's turn, as cc_quiz.R3
FLIP = .6           # a page turn
INK, PEN, SOFT = "#1f2430", "#1d3fa8", "#5b6272"
FONTS = ("Old Standard TT", "Oswald", "Caveat", "Permanent Marker")
NOTE_X, NOTE_Y = 646, 1256      # the lime sticky note (below y 880, so all of it left of x 950)

CSS = """
.yb-page{position:absolute;inset:0;overflow:hidden;background:#eeeae1 url(%(paper)s) center/cover}
.yb-serif{font-family:'Old Standard TT',Georgia,serif;color:#1f2430}
.yb-sc{font-family:Oswald,sans-serif;font-weight:500;letter-spacing:.16em;text-transform:uppercase;color:#5b6272;
  line-height:1;white-space:nowrap}
.yb-it{font-family:'Old Standard TT',Georgia,serif;font-style:italic;color:#4b5261;white-space:nowrap}
.yb-pen{font-family:Caveat,cursive;font-weight:700;color:#1d3fa8;line-height:1;white-space:nowrap}
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
    """The page itself: paper, the shadow of the book's spine, the page number."""
    return ('<div class="abs" style="left:0;top:0;width:120px;height:1920px;background:linear-gradient(90deg,'
            'rgba(58,44,28,.24),rgba(58,44,28,.08) 38%,rgba(58,44,28,0))"></div>'
            '<div class="abs" style="right:0;top:0;width:26px;height:1920px;background:linear-gradient(270deg,'
            'rgba(0,0,0,.07),rgba(0,0,0,0))"></div>'
            + (f'<div class="abs yb-serif" style="left:0;width:1080px;top:1596px;text-align:center;font-size:30px;'
               f'color:#9aa0aa">{page_no}</div>' if page_no else ""))


def _code_note() -> str:
    """USE CODE: BAD on a lime sticky note stuck to the page, #EpicPartner on it, small."""
    return (f'<div class="abs" style="left:{NOTE_X}px;top:{NOTE_Y}px;width:292px;height:186px;transform:rotate(3deg);'
            f'background:linear-gradient(180deg,#e2f63a 0%,{LIME} 22%,#e6fd3c 70%,#d9ef33 100%);'
            f'box-shadow:0 2px 2px rgba(0,0,0,.18),0 14px 16px -8px rgba(0,0,0,.35);display:flex;'
            f'flex-direction:column;align-items:center;justify-content:center;padding-top:4px">'
            f'<div style="font-family:\'Permanent Marker\';font-size:42px;line-height:1;color:#111">USE CODE:</div>'
            f'<div style="font-family:\'Permanent Marker\';font-size:124px;line-height:.84;color:#111;'
            f'margin-top:2px">BAD</div>'
            f'<div style="font-family:Oswald,sans-serif;font-weight:500;font-size:19px;letter-spacing:.08em;'
            f'color:#3a4010;margin-top:6px">#EpicPartner</div></div>')


def _header(title: str, right: str = "", sub: str = "", size: int = 92, over: str = "") -> tuple:
    """Kicker, serif title (an italic line over it or under it), double rule.
    Returns (html, the y under the rule)."""
    top = 206
    out = [f'<div class="abs yb-sc" style="left:70px;top:{top}px;font-size:26px;letter-spacing:.34em">'
           f'Locker High Yearbook</div>']
    if right:
        out.append(f'<div class="abs yb-sc" style="right:70px;top:{top}px;font-size:26px;letter-spacing:.2em">'
                   f'{esc(right)}</div>')
    y = top + 40
    if over:
        out.append(f'<div class="abs yb-it" style="left:70px;top:{y}px;font-size:44px">{esc(over)}</div>')
        y += 52
    out.append(f'<div class="abs yb-serif" data-fit="940" style="left:66px;top:{y}px;font-size:{size}px;'
               f'font-weight:700;line-height:1;white-space:nowrap">{esc(title)}</div>')
    y += size * 1.04
    if sub:
        out.append(f'<div class="abs yb-it" data-fit="560" style="left:70px;top:{y + 8:.0f}px;font-size:32px">'
                   f'{esc(sub)}</div>')
        y += 50
    y += 16
    out.append(f'<div class="abs" style="left:70px;top:{y:.0f}px;width:940px;height:3px;background:{INK}"></div>'
               f'<div class="abs" style="left:70px;top:{y + 7:.0f}px;width:940px;height:1px;background:{INK}"></div>')
    return "".join(out), y + 30


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
    """Name in serif (two lines at most) with whatever goes under it."""
    return (f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;display:flex;'
            f'flex-direction:column;gap:{gap}px;{style}">'
            f'<div class="yb-serif" data-fit="{w:.0f}" data-lines="2" style="width:{w:.0f}px;font-size:{name_px}px;'
            f'font-weight:700;line-height:1.04">{esc(name)}</div>{lines}</div>')


def _cell(art: str, x: float, y: float, pw: float, ph: float, it: dict, seed: int, crop: str,
          label: str, answer: str = "", t_answer: float = 0) -> str:
    """A class photo with the name under it and a small grey line; with an
    answer, the pen writes it over that line at t_answer."""
    line = f'<div class="yb-sc" style="font-size:22px;color:#80858f">{esc(label)}</div>'
    if answer:
        line = (f'<div style="position:relative;height:22px">'
                f'<div class="yb-sc" style="font-size:22px;color:#80858f;{_a("ybgone", t_answer, .2, "linear")}">'
                f'{esc(label)}</div>'
                f'<div class="yb-pen" data-fit="{pw + 10:.0f}" style="position:absolute;left:-3px;top:-12px;'
                f'font-size:42px;transform:rotate(-2deg);{write_on(t_answer + .05, .5, 14)}">{esc(answer)}</div>'
                f'</div>')
    return (f'<div class="yb-photo" style="left:{x:.0f}px;top:{y:.0f}px">{photo(art, pw, ph, crop, seed)}</div>'
            + _caption(x, y + ph + 10, pw, it["name"], 34, line))


# ------------------------------------------------------------------ Guess the Season

GRID_X, GRID_Y, CELL, PITCH_X, PITCH_Y = 60, 430, 280, 306, 406


def _class_grid(ctx, items: list, crop: str, answers: list = None, t_answer: float = 0,
                step: float = .45) -> str:
    out = []
    for i, it in enumerate(items):
        r, c = divmod(i, 3)
        out.append(_cell(ctx.art(it), GRID_X + c * PITCH_X, GRID_Y + r * PITCH_Y, CELL, CELL, it, 11 + i, crop,
                         "Season ?", answers[i] if answers else "", t_answer + i * step))
    return "".join(out)


def _gs_class_page(ctx, spec, items: list, crop: str, final: bool, content_end: float = 0) -> tuple:
    """The quiz's class page: at the start (the thumbnail) and again at the end,
    when the pen fills in the answer key. Returns (html, sounds)."""
    n = len(items)
    head, _ = _header("Guess the Season", f"Quiz No. {spec.get('episode', '')}".strip(),
                      "When did each one come out?", 92)
    sounds = []
    t = content_end + .3
    answers = [_season(it["season_label"]) for it in items] if final else None
    html = [_paper(40), head, _class_grid(ctx, items, crop, answers, t)]
    # the pen: a question and an arrow at the top right, and a note in the free space
    if final:
        html.append(f'<div class="abs yb-pen" style="left:600px;top:322px;font-size:60px;transform:rotate(-4deg);'
                    f'{write_on(content_end + .05, .45, 12)}">answer key!</div>')
        sounds.append((content_end + .05, "pen"))
        sounds += [(t + i * .45, "pen") for i in range(n)]
        t_q = t + n * .45 + .25
        q = f"how many did you get out of {n}?"
        if n % 3:
            html.append(f'<div class="abs yb-pen" data-fit="270" data-lines="4" style="left:{GRID_X + (n % 3) * PITCH_X + 6}px;'
                        f'top:{GRID_Y + PITCH_Y + 30}px;width:270px;font-size:58px;line-height:1.05;white-space:normal;'
                        f'transform:rotate(-3deg);{write_on(t_q, 1.1, 22)}">{esc(q)}</div>')
        else:
            html.append(f'<div class="abs yb-pen" data-fit="540" data-lines="2" style="left:70px;top:1262px;'
                        f'width:540px;font-size:64px;line-height:1.05;white-space:normal;transform:rotate(-3deg);'
                        f'{write_on(t_q, 1.1, 22)}">{esc(q)}</div>')
        sounds.append((t_q, "pen"))
    else:
        html.append('<div class="abs yb-pen" style="left:600px;top:322px;font-size:60px;transform:rotate(-4deg)">'
                    'which season??</div>')
        html.append(stroke_static(rough_arrow(870, 392, GRID_X + 2 * PITCH_X + CELL * .55, GRID_Y - 4, seed=8,
                                              head=22, curve=.32), PEN, 5))
        # "6 rounds." is on the page from frame 0; "no peeking!" gets written as it starts
        if n % 3:
            x, y, px = GRID_X + (n % 3) * PITCH_X + 10, GRID_Y + PITCH_Y + 50, 70
            html.append(f'<div class="abs yb-pen" style="left:{x}px;top:{y}px;font-size:{px}px;transform:rotate(-3deg)">'
                        f'{n} rounds.</div><div class="abs yb-pen" style="left:{x + 4}px;top:{y + 84}px;font-size:{px}px;'
                        f'transform:rotate(-4deg);{write_on(.45, .6, 12)}">no peeking!</div>')
        else:
            html.append(f'<div class="abs yb-pen" style="left:70px;top:1290px;font-size:64px;transform:rotate(-3deg)">'
                        f'{n} rounds.</div><div class="abs yb-pen" style="left:318px;top:1276px;font-size:64px;'
                        f'transform:rotate(-3deg);{write_on(.45, .6, 12)}">no peeking!</div>')
        sounds.append((.45, "pen"))
    return "".join(html), sounds


# the round page
PH_X, PH_Y, PH_W, PH_H = 60, 378, 560, 720
BAL_X, BAL_Y, BAL_PITCH, BAL_W = 648, 470, 132, 300     # all of it left of x 950
COUNT_Y = 1016


def _gs_round(ctx, spec, it: dict, opts: list, answer: int, k: int, n: int, t0: float, crop: str) -> tuple:
    """One round's page. Printed: the photo, the name, the ballot. In pen: the
    round number as the page opens, the countdown, the tick in the right box
    and the season under the name."""
    rev = t0 + T_REV
    head, _ = _header("Guess the Season", f"Quiz No. {spec.get('episode', '')}".strip(), "", 80)
    html = [_paper(40 + k), head,
            f'<div class="abs yb-pen" style="left:742px;top:258px;font-size:66px;transform:rotate(-5deg);'
            f'{write_on(t0 + .2, .5, 12)}">round {k}/{n}</div>',
            f'<div class="yb-photo" style="left:{PH_X}px;top:{PH_Y}px">'
            f'{photo(ctx.art(it), PH_W, PH_H, "close" if crop == "head" else crop, 20 + k)}'
            f'</div>']
    answer_line = (f'<div style="position:relative;height:62px;margin-top:10px">'
                   f'<div class="yb-sc" style="position:absolute;left:0;top:18px;font-size:24px;color:#80858f;'
                   f'{_a("ybgone", rev + .3, .2, "linear")}">Introduced in: ?</div>'
                   f'<div class="yb-pen" data-fit="{PH_W}" style="position:absolute;left:-2px;top:0;font-size:72px;'
                   f'transform:rotate(-2deg);transform-origin:0 50%;{write_on(rev + .35, .8, 20)}">'
                   f'{esc(_season(opts[answer]))}!</div></div>')
    html.append(_caption(PH_X, PH_Y + PH_H + 16, PH_W, it["name"], 54,
                         f'<div class="yb-sc" style="font-size:24px;margin-top:4px">{esc(_kind(it))}</div>'
                         + answer_line))
    # the ballot
    html.append(f'<div class="abs yb-sc" style="left:{BAL_X}px;top:{PH_Y + 6}px;font-size:25px;color:{INK}">'
                f'Introduced in</div>'
                f'<div class="abs yb-it" style="left:{BAL_X}px;top:{PH_Y + 40}px;font-size:28px">tick one:</div>')
    for i, o in enumerate(opts):
        y = BAL_Y + i * BAL_PITCH
        chap, _, seas = o.partition(" · ")
        fade = "" if i == answer else _a("ybfade", rev + .1, .35, "ease-out")
        html.append(f'<div class="abs" style="left:{BAL_X}px;top:{y}px;width:{BAL_W}px;height:100px;{fade}">'
                    f'<div class="abs" style="left:0;top:16px;width:46px;height:46px;border:3px solid {INK};'
                    f'background:rgba(255,255,255,.35)"></div>'
                    f'<div class="abs yb-sc" data-fit="{BAL_W - 66}" style="left:66px;top:2px;font-size:26px;'
                    f'color:#4b5261">{esc(chap)}</div>'
                    f'<div class="abs yb-serif" data-fit="{BAL_W - 66}" style="left:64px;top:34px;font-size:48px;'
                    f'font-weight:700;line-height:1;white-space:nowrap">{esc(seas or chap)}</div></div>')
    by = BAL_Y + answer * BAL_PITCH
    html.append(stroke_svg(rough_check(BAL_X + 4, by + 58, 64, seed=k), PEN, 8, rev, .24))
    # the pen counts down under the ballot
    for j, d in enumerate("321"):
        html.append(f'<div class="abs yb-pen" style="left:{BAL_X + 12 + j * 100}px;top:{COUNT_Y}px;font-size:120px;'
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
    base, sounds = _gs_class_page(ctx, spec, items, crop, True, content_end)
    comp.add(f'<div class="yb-page" style="z-index:1">{base}{_landing(content_end - FLIP)}</div>')
    for s in sounds:
        comp.cue(*s)
    # frame 0: the class page with every photo, "which season??"
    hook, sounds = _gs_class_page(ctx, spec, items, crop, False)
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

    comp.add(f'<div class="full" style="z-index:60">{_code_note()}</div>')
    comp.add(PREP_JS)
    comp.add(photo_lab())
    comp.cues.sort()
    return comp


# ------------------------------------------------------------------ Season Throwback

def _slots(n: int) -> tuple:
    """The class page's photo grid: (photo w, photo h, name px, [(x, y)]). It
    stays left of x 950 and clear of the code note, and the photos have the
    print's shape, so a print laid into its slot lands exactly on it."""
    if n <= 6:
        pw, cols, name_px, pitch = 244, 3, 36, 386
    else:
        pw, cols, name_px, pitch = 202, 4, 30, 340
    ph = round(pw * PR_PH / PR_PW)
    gap = (886 - cols * pw) / (cols - 1)
    return pw, ph, name_px, [(64 + (i % cols) * (pw + gap), 470 + (i // cols) * pitch) for i in range(n)]


# the print of the photo whose turn it is: laid over the page, big
PR_X, PR_Y, PR_B, PR_PW, PR_PH, PR_CAP = 184, 446, 24, 512, 580, 172
PR_W, PR_H = PR_PW + 2 * PR_B, PR_B + PR_PH + PR_CAP
T_IN, T_OUT, T_PLACE = .05, 5.8, .55        # in each turn: lands, starts for its slot, takes this long


def _print(comp: Comp, ctx, it: dict, i: int, t0: float, slot: tuple, pw: float, crop: str, kind: str,
           col: str) -> str:
    """The portrait as a print: slid in over the page, held, then laid into its
    slot on the page (where the page's own copy of the photo takes over)."""
    x, y = slot
    rot = (-2.2, 1.6, -1.4, 2.0)[i % 4]
    k = pw / PR_PW
    dx, dy = x - (PR_X + PR_B), y - (PR_Y + PR_B)
    name = comp.uid("ybprint")
    t1, t2, t3 = t0 + T_IN, t0 + T_OUT, t0 + T_OUT + T_PLACE
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
                       f'<div class="yb-sc" data-fit="{PR_PW}" style="font-size:25px;display:flex;align-items:center">'
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
    content_end = HOOK + n * R3
    comp = Comp(pad_to(content_end))
    _setup(comp)

    # ---- the class page: "not pictured" until each print is laid into its slot
    pw, ph, name_px, slots = _slots(n)
    head, _ = _header(season, "Throwback", "", 84, over="Class of")
    page, prints = [_paper(12), head], []
    for i, (it, (x, y)) in enumerate(zip(group, slots)):
        t0 = HOOK + i * R3
        placed = t0 + T_OUT + T_PLACE
        kind = _kind(it) + (f" · {theme['debut'](it)}" if theme and theme.get("debut") else "")
        col = RARITY.get(it.get("rarity", ""), "#9aa0a6")
        page.append(f'<div class="yb-photo" style="left:{x:.0f}px;top:{y:.0f}px">'
                    f'{photo("", pw, ph, crop, 61 + i, none="-" if gear else "")}</div>'
                    f'<div class="yb-photo" style="left:{x:.0f}px;top:{y:.0f}px;{_a("lkin", placed - .07, .05, "linear")}">'
                    f'{photo(ctx.art(it), pw, ph, crop, 31 + i)}</div>'
                    + _caption(x, y + ph + 10, pw, it["name"], name_px,
                               f'<div class="yb-sc" data-fit="{pw}" data-lines="2" style="width:{pw}px;'
                               f'font-size:{name_px * .56:.0f}px;line-height:1.15;letter-spacing:.08em;'
                               f'white-space:normal"><i style="display:inline-block;width:.62em;height:.62em;'
                               f'background:{col};margin-right:.4em"></i>{esc(kind)}</div>', 4,
                               _a("ybwipe", placed, .4, "cubic-bezier(.3,.6,.4,1)")))
        prints.append(_print(comp, ctx, it, i, t0, (x, y), pw, crop, kind, col))
    t_out = content_end + .35
    page.append(f'<div class="abs yb-pen" data-fit="560" style="left:70px;top:1262px;font-size:68px;'
                f'transform:rotate(-3deg);{write_on(t_out, 1.0, 20)}">which one did you own?</div>'
                f'<div class="abs yb-pen" style="left:96px;top:1358px;font-size:50px;color:#2a4bb0;'
                f'transform:rotate(-4deg);{write_on(t_out + 1.6, .9, 18)}">stay legendary :) &ndash; BAD</div>')
    comp.cue(t_out, "pen")
    comp.cue(t_out + 1.6, "pen")
    comp.add(f'<div class="yb-page" style="z-index:1">{"".join(page)}{"".join(prints)}{_landing(HOOK - FLIP)}</div>')

    # ---- frame 0: the cover -- two of the class, big, and the question
    head, y = _header(season, "Throwback", "", 88, over="Class of")
    cover = [_paper(11), head]
    for j, it in enumerate(group[:2]):
        x = 64 + j * 448
        cover.append(f'<div class="yb-photo" style="left:{x}px;top:{y + 6:.0f}px">'
                     f'{photo(ctx.art(it), 424, 500, crop, 51 + j)}</div>'
                     + _caption(x, y + 522, 424, it["name"], 42,
                                f'<div class="yb-sc" data-fit="424" style="font-size:22px">{esc(_kind(it))}</div>'))
    # "8 skins." is there on frame 0; the question gets written as the video starts
    cover.append(f'<div class="abs" style="left:70px;top:{y + 690:.0f}px;width:560px;display:flex;'
                 f'flex-direction:column;gap:4px;transform:rotate(-3deg);transform-origin:0 0">'
                 f'<div class="yb-pen" data-fit="560" data-lines="2" style="width:560px;font-size:72px;'
                 f'line-height:1.02;white-space:normal">{n} {esc(noun)}.</div>'
                 f'<div class="yb-pen" data-fit="560" data-lines="2" style="width:560px;font-size:60px;'
                 f'line-height:1.04;white-space:normal;{write_on(.4, 1.0, 20)}">how many do you remember?</div></div>')
    comp.cue(.4, "pen")
    comp.scene(0, HOOK, _turn(f'<div class="yb-page">{"".join(cover)}</div>', HOOK), fade_in=.01, fade_out=.01, z=40)
    comp.cue(HOOK - FLIP, "flip")

    comp.add(f'<div class="full" style="z-index:60">{_code_note()}</div>')
    comp.add(PREP_JS)
    comp.add(photo_lab())
    comp.cues.sort()
    return comp
