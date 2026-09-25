"""
MUSEUM -- OG Check, as a walk through a quiet gallery after hours.

    0:00  hook      the gallery's entrance, lit: THE OG MUSEUM on the wall, the
                    oldest outfit on a plinth under its spot, a panel that says
                    what today's exhibition is, and the guide's lime paddle
                    (Support the museum / USE CODE: BAD)
    0:03  items     the camera pans from exhibit to exhibit, counting down to the
                    oldest (6.6 s each, a little longer when there are fewer):
                    each one waits in the dark, its spot clicks on, then its
                    label light; outfits stand on a plinth, everything else sits
                    in a glass case. No. 1 gets "The oldest today" (or "Tied for
                    oldest") on the wall.
    0:56  outro     the exit wall: "How OG is your locker?", postcards of three
                    exhibits, and the guide holds the paddle up

The placard carries only the format's facts: the name, rarity and type, Epic's
own "Introduced in Chapter 1, Season 3", and today's price. The lime paddle is
carried by the tour guide, so it stays in frame while the camera walks: it is on
screen, whole and readable, in every frame.
"""

import math
import re

from cc_fmt_og_check import _order, _season
from cc_looks import KIT_CSS, LIME, PREP_JS, pad_to, tex, write_on
from cc_motion import W, H, Comp, esc

HOOK = 3.0
R_MIN, R_MAX = 6.6, 8.4           # seconds per exhibit (the classic's 6.6, stretched when there are fewer)
CONTENT = 52.8                    # what 8 exhibits take at 6.6 s
PAN_D = 1.75                      # a pan from one bay to the next
PAN_LEAD = .55                    # it starts this long before the exhibit's slot
CLICK = 1.25                      # the spot comes on this long after the slot starts
LABEL = 1.7                       # then the label light
EASE_PAN = "cubic-bezier(.55,0,.35,1)"
FONTS = ("Cormorant Garamond",)

# The room. Every bay is one screen wide; the camera frames one bay at a time.
BAY = 1080
FX = 300                          # the exhibit's centre in its bay
CEIL, WALL_LINE = 118, 1352
FOCUS = (540, 760)                # the dolly pushes in toward here
PL_W, PL_D, PL_H, PL_FRONT = 300, 72, 278, 1152           # an outfit's plinth
OB_W, OB_D, OB_FRONT = 380, 60, 1080                       # a glass case's plinth
OB_H = PL_FRONT + PL_H - OB_FRONT
VT_TOP, VT_D = 560, 48            # the glass case: front face top, depth of its lid
FIG_H, FIG_W = 740, 420           # an outfit, head to sole
OBJ_W, OBJ_H = 318, 430           # anything else, inside its case
OBJ_MID = 800                     # ... mounted with its middle here
COL_X, COL_W = 524, 430           # the right-hand column: header and placard
HDR_Y, PLACARD_Y = 196, 440
PLACARD_MAXH = 478                # it ends above the paddle
ROPE_K, ROPE_P = 1480 / 1080, 1480       # the rope is nearer: it moves faster
# The guide's paddle (the creator code): board top-left, in frame pixels.
PAD_X, PAD_Y, PAD_W = 613, 948, 304
PIVOT = (PAD_X + PAD_W / 2, 2350)        # the guide's hand, below the frame

CSS = """
.mz-cam{position:absolute;inset:0;transform-origin:%(fx)dpx %(fy)dpx;will-change:transform}
.mz-pan{position:absolute;left:0;top:0;height:1920px;will-change:transform;font-variant-numeric:lining-nums}
.mz-nw{white-space:nowrap}
.mz-wall{position:absolute;left:-400px;top:0;height:%(wl)dpx;
  background:linear-gradient(rgba(26,21,16,.74),rgba(26,21,16,.5) 20%%,rgba(26,21,16,.44) 70%%,rgba(26,21,16,.56)),
    url('%(wall)s') 0 0/1440px 1360px repeat-x}
.mz-floor{position:absolute;left:-400px;top:%(wl)dpx;height:%(fh)dpx;
  background:linear-gradient(rgba(143,131,115,.86),rgba(123,111,97,.86) 14%%,rgba(95,85,74,.9) 55%%,rgba(69,61,53,.94)),
    url('%(floor)s') 0 0/1440px 640px repeat-x}
.mz-gap{position:absolute;left:-400px;top:%(wl3)dpx;height:6px;background:#221d18;box-shadow:0 2px 3px rgba(0,0,0,.35)}
.mz-ceil{position:absolute;left:-400px;top:0;height:%(ceil)dpx;background:linear-gradient(#141210,#2a2621);
  box-shadow:0 1px 0 rgba(255,236,210,.10)}
.mz-track{position:absolute;left:-400px;top:%(track)dpx;height:8px;background:linear-gradient(#0b0a09,#24201c)}
.mz-pool{position:absolute;width:880px;height:1240px;margin:-620px 0 0 -440px;
  background:radial-gradient(ellipse 50%% 50%% at 50%% 50%%,rgba(255,231,196,.70),rgba(255,231,196,.58) 42%%,
    rgba(255,231,196,.40) 58%%,rgba(255,231,196,.10) 74%%,rgba(255,231,196,0) 86%%)}
.mz-wash{position:absolute;width:660px;height:640px;margin:-320px 0 0 -330px;
  background:radial-gradient(ellipse 50%% 50%% at 50%% 50%%,rgba(255,236,210,.42),rgba(255,236,210,.14) 60%%,rgba(255,236,210,0))}
.mz-fpool{position:absolute;width:820px;height:230px;margin:-115px 0 0 -410px;
  background:radial-gradient(ellipse 50%% 50%% at 50%% 50%%,rgba(255,228,190,.30),rgba(255,228,190,0))}
.mz-title{position:absolute;font-family:'Inter';font-weight:250;font-size:64px;letter-spacing:.3em;color:#231f1b;line-height:1}
.mz-sub{position:absolute;font-family:'Cormorant Garamond';font-style:italic;font-weight:500;font-size:44px;color:#3a332c;line-height:1.08}
.mz-sc{position:absolute;font-family:'Inter';font-weight:500;font-size:26px;letter-spacing:.2em;color:#4a4239;line-height:1}
.mz-hair{position:absolute;height:1.5px;background:#5e554b}
.mz-hdr-k{font-family:'Inter';font-weight:500;font-size:24px;letter-spacing:.36em;color:#4f473e;line-height:1}
.mz-hdr-n{font-family:'Cormorant Garamond';font-weight:500;font-size:124px;color:#1f1b17;line-height:.9;margin-top:8px;
  letter-spacing:.01em}
.mz-hdr-x{font-family:'Cormorant Garamond';font-style:italic;font-weight:500;font-size:52px;color:#2a241e;line-height:1;
  margin-top:8px}

.mz-card{position:absolute;width:%(colw)dpx;padding:30px 32px 32px;background:#f7f4ee;
  box-shadow:0 1px 1px rgba(0,0,0,.24),0 6px 12px rgba(0,0,0,.16),inset 0 0 0 1px rgba(0,0,0,.04)}
.mz-card .n{font-family:'Cormorant Garamond';font-weight:700;font-size:50px;letter-spacing:.04em;color:#1d1a17;line-height:1;
  text-transform:uppercase}
.mz-card .k{font-family:'Cormorant Garamond';font-style:italic;font-weight:500;font-size:38px;color:#4b443c;margin-top:8px;
  line-height:1.05;white-space:nowrap}
.mz-card .r{width:46px;height:1.5px;background:#b2a898;margin:18px 0 15px}
.mz-card .l{font-family:'Inter';font-weight:500;font-size:29px;font-variant-caps:all-small-caps;letter-spacing:.08em;
  color:#665d53;line-height:1.1;white-space:nowrap}
.mz-card .v{font-family:'Cormorant Garamond';font-weight:700;font-size:48px;color:#1d1a17;line-height:1.08;margin-top:1px;
  white-space:nowrap}
.mz-card .v+.l{margin-top:14px}
.mz-card .p{font-family:'Cormorant Garamond';font-weight:500;font-size:37px;color:#2b2520;line-height:1.14}
.mz-card .dim{position:absolute;inset:0;background:rgba(20,16,12,.6)}

.mz-fix{position:absolute;width:34px;height:54px;border-radius:5px 5px 8px 8px;transform-origin:50%% 0;
  background:linear-gradient(90deg,#0b0a09,#2e2a26 55%%,#0f0e0d);box-shadow:0 2px 2px rgba(0,0,0,.4)}
.mz-fix::before{content:"";position:absolute;left:13px;top:-8px;width:8px;height:10px;background:#121110}
.mz-fix::after{content:"";position:absolute;left:4px;bottom:-3px;width:26px;height:7px;border-radius:50%%;
  background:radial-gradient(ellipse,#5d564c,#39342d 60%%,#1f1c19)}
.mz-lens{position:absolute;width:26px;height:7px;border-radius:50%%;background:radial-gradient(ellipse,#fff6e2,#f0d6a4 60%%,#6d5a3a)}
.mz-conew{position:absolute;filter:blur(16px)}
.mz-cone{position:absolute;inset:0;background:linear-gradient(rgba(255,238,210,.26),rgba(255,238,210,.11) 40%%,
  rgba(255,238,210,.05) 75%%,rgba(255,238,210,.02))}
.mz-pbase{position:absolute;border-radius:50%%;filter:blur(7px);background:rgba(14,10,6,.62)}
.mz-refl{position:absolute;background:linear-gradient(rgba(235,228,214,.16),rgba(235,228,214,0));filter:blur(3px)}
.mz-cast{position:absolute;border-radius:50%%;filter:blur(6px);background:rgba(40,30,20,.22)}
.mz-art{position:absolute;width:0;height:0}
.mz-art img{position:absolute;visibility:hidden}
.mz-img{position:absolute;display:block}
.mz-img.flat{box-shadow:0 0 0 10px #fbf8f1,0 0 0 13px #2a2520,0 8px 14px 10px rgba(0,0,0,.28)}
.mz-slot{position:absolute;width:0;height:0}
.mz-rod{position:absolute;width:6px;background:linear-gradient(90deg,#5c4318,#e2c27a 45%%,#8a6a2a 75%%,#4d3812)}
.mz-rodbase{position:absolute;width:64px;height:12px;border-radius:50%%;
  background:radial-gradient(ellipse at 45%% 40%%,#e8cf8e,#a67d34 60%%,#5b4419);box-shadow:0 4px 7px rgba(0,0,0,.4)}
.mz-wsh canvas{opacity:.3}
.mz-feet{position:absolute;border-radius:50%%;height:20px;margin-top:-10px;
  background:radial-gradient(ellipse 50%% 50%% at 50%% 50%%,rgba(22,15,8,.62),rgba(22,15,8,0))}
.mz-glass{position:absolute}
.mz-tent{position:absolute;width:290px;padding:26px 20px 24px;background:#fbf8f1;text-align:center;
  box-shadow:0 2px 3px rgba(0,0,0,.25),0 8px 14px rgba(0,0,0,.12)}
.mz-tent .t{font-family:'Cormorant Garamond';font-style:italic;font-weight:500;font-size:46px;color:#2a241e;line-height:1.05}
.mz-tent .u{font-family:'Inter';font-weight:500;font-size:21px;letter-spacing:.14em;color:#6a6157;margin-top:12px}

.mz-post{position:absolute;width:236px;padding:11px 11px 0;background:#fbf8f1;
  box-shadow:0 2px 3px rgba(0,0,0,.3),0 10px 16px rgba(0,0,0,.18)}
.mz-post .ph{position:relative;width:214px;height:214px;overflow:hidden}
.mz-post .cap{font-family:'Cormorant Garamond';font-style:italic;font-weight:500;font-size:28px;color:#2a241e;
  text-align:center;height:46px;line-height:46px;white-space:nowrap;overflow:hidden}
.mz-ledge{position:absolute;height:18px;background:linear-gradient(#6b4a2e,#4a321f);box-shadow:0 6px 10px rgba(0,0,0,.35)}

.mz-walk{position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:%(px)dpx %(py)dpx}
.mz-paddle{position:absolute;width:%(pw)dpx;font-variant-numeric:lining-nums}
.mz-pole{position:absolute;left:%(pole)dpx;width:12px;height:900px;
  background:linear-gradient(90deg,#1b1714,#6e6255 40%%,#3a332c 70%%,#141210);box-shadow:2px 0 4px rgba(0,0,0,.35)}
.mz-board{position:relative;width:%(pw)dpx;padding:14px 12px 12px;background:%(lime)s;text-align:center;color:#111;
  box-shadow:0 0 0 7px #2a2520,0 0 0 8px #4d4238,0 8px 14px 6px rgba(0,0,0,.30)}
.mz-board::after{content:"";position:absolute;inset:0;pointer-events:none;opacity:.08;
  background:url('%(grain)s') 0 0/256px 256px}
.mz-board .s1{font-family:'Cormorant Garamond';font-style:italic;font-weight:500;font-size:30px;color:#26261a;line-height:1}
.mz-board .s2{font-family:'Inter';font-weight:800;font-size:40px;letter-spacing:.06em;line-height:1;margin:10px 0 0 .06em}
.mz-board .s3{font-family:'Inter';font-weight:800;font-size:118px;letter-spacing:.02em;line-height:.9;margin:2px 0 4px .02em}
.mz-board .s4{font-family:'Inter';font-weight:500;font-size:19px;letter-spacing:.04em;color:#2d2d20}

.mz-vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 92%% 68%% at 44%% 43%%,rgba(0,0,0,0) 52%%,rgba(8,5,2,.46) 100%%)}
.mz-grain{position:absolute;inset:-64px;pointer-events:none;background:url('%(grain)s') 0 0/256px 256px;opacity:.06;
  animation:mzgrain .6s steps(6) 0s infinite normal both}
@keyframes mzgrain{0%%{transform:translate(0,0)}17%%{transform:translate(-37px,21px)}33%%{transform:translate(18px,-44px)}
  50%%{transform:translate(-22px,-13px)}67%%{transform:translate(41px,30px)}83%%{transform:translate(-9px,47px)}
  100%%{transform:translate(0,0)}}
@keyframes mzon{0%%{opacity:0}10%%{opacity:.92}16%%{opacity:.38}24%%{opacity:1}32%%{opacity:.78}45%%{opacity:1}100%%{opacity:1}}
@keyframes mzoff{0%%{opacity:1}10%%{opacity:.08}16%%{opacity:.62}24%%{opacity:0}32%%{opacity:.22}45%%{opacity:0}100%%{opacity:0}}
@keyframes mzfig{0%%{filter:brightness(.3) saturate(.55)}10%%{filter:brightness(.93) saturate(.95)}
  16%%{filter:brightness(.55) saturate(.7)}24%%{filter:brightness(1.02) saturate(1)}32%%{filter:brightness(.86) saturate(.95)}
  45%%,100%%{filter:brightness(1) saturate(1)}}
@keyframes mzblip{0%%,100%%{opacity:1}30%%{opacity:.55}55%%{opacity:.9}70%%{opacity:.7}}
@keyframes mzfade{from{opacity:0}to{opacity:1}}
@keyframes mzunfade{from{opacity:1}to{opacity:0}}
@keyframes mzrule{from{transform:scaleX(0)}to{transform:scaleX(1)}}
"""

# The prep step (before frame 0): each piece of art is trimmed to what's actually
# in it, fitted to its exhibit (an outfit stands on its plinth, anything else sits
# in its case), lit from the spot above and to the left, and given a soft shadow
# on the wall and contact shadows under its feet. Real shop images come with
# different padding; this is what makes them all stand on the plinth the same way.
ART_JS = """<script>(() => {
  const prev = window.__ready;
  async function prep(box) {
    const img = box.querySelector('img');
    if (!img) return;
    if (img.decode) { try { await img.decode(); } catch (e) {} }
    const w = img.naturalWidth, h = img.naturalHeight;
    if (!w || !h) return;
    const mode = box.dataset.mode, bw = +box.dataset.w, bh = +box.dataset.h;
    const k = Math.min(1, 420 / Math.max(w, h));
    const aw = Math.max(1, Math.round(w * k)), ah = Math.max(1, Math.round(h * k));
    const c = document.createElement('canvas'); c.width = aw; c.height = ah;
    const g = c.getContext('2d', {willReadFrequently: true});
    g.drawImage(img, 0, 0, aw, ah);
    const px = g.getImageData(0, 0, aw, ah).data;
    let x0 = aw, y0 = ah, x1 = -1, y1 = -1;
    const low = new Int32Array(aw).fill(-1);
    for (let y = 0; y < ah; y++) for (let x = 0; x < aw; x++) {
      if (px[(y * aw + x) * 4 + 3] > 40) {
        if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; y1 = y; low[x] = y;
      }
    }
    if (x1 < 0) return;
    const A = i => px[i * 4 + 3];
    const flat = A(0) > 245 && A(aw - 1) > 245 && A((ah - 1) * aw) > 245 && A(ah * aw - 1) > 245;
    let sx = 0, sy = 0, sw = w, sh = h;
    if (!flat) {
      sx = Math.max(0, (x0 - 1) / k); sy = Math.max(0, (y0 - 1) / k);
      sw = Math.min(w, (x1 + 2) / k) - sx; sh = Math.min(h, (y1 + 2) / k) - sy;
    }
    const s = Math.min(bw / sw, bh / sh, +(box.dataset.up || 3));
    const dw = Math.max(1, Math.round(sw * s)), dh = Math.max(1, Math.round(sh * s));
    const out = document.createElement('canvas'); out.width = dw; out.height = dh;
    const o = out.getContext('2d');
    o.imageSmoothingEnabled = true; o.imageSmoothingQuality = 'high';
    if (mode !== 'card') o.filter = 'sepia(.07) saturate(1.04)';
    o.drawImage(img, sx, sy, sw, sh, 0, 0, dw, dh);
    o.filter = 'none';
    if (mode !== 'card' && !flat) {
      o.globalCompositeOperation = 'source-atop';
      let gr = o.createLinearGradient(0, 0, dw, 0);
      gr.addColorStop(0, 'rgba(255,232,196,.10)'); gr.addColorStop(.45, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(8,5,2,.16)');
      o.fillStyle = gr; o.fillRect(0, 0, dw, dh);
      gr = o.createLinearGradient(0, 0, 0, dh);
      gr.addColorStop(0, 'rgba(255,236,204,.08)'); gr.addColorStop(.36, 'rgba(0,0,0,0)');
      gr.addColorStop(.68, 'rgba(10,6,2,.10)'); gr.addColorStop(1, 'rgba(10,6,2,.30)');
      o.fillStyle = gr; o.fillRect(0, 0, dw, dh);
      o.globalCompositeOperation = 'source-over';
    }
    out.className = 'mz-img' + (flat ? ' flat' : '');
    out.style.left = (-dw / 2) + 'px';
    // An outfit stands on its plinth. Anything else is mounted at the middle of its
    // case on a slim brass rod, unless it's tall enough to stand on the case floor.
    let top = -dh, mounted = false;
    const lift = +(box.dataset.lift || 0);
    if (mode === 'object' && !flat && lift - dh / 2 > 14) {
      top = -(lift + dh / 2);
      mounted = true;
      const cxa = Math.round((x0 + x1) / 2);
      let best = -1;
      for (let d = 0; d < aw && best < 0; d++) {
        for (const x of [cxa - d, cxa + d]) { if (x >= 0 && x < aw && low[x] >= 0) { best = x; break; } }
      }
      const yLow = ((low[best] + 1) / k - sy) * s, rx = ((best + .5) / k - sx) * s - dw / 2;
      const rodTop = top + yLow - 10;
      const rod = document.createElement('div');
      rod.className = 'mz-rod';
      rod.style.left = (rx - 3) + 'px'; rod.style.top = rodTop + 'px'; rod.style.height = (-rodTop) + 'px';
      const base = document.createElement('div');
      base.className = 'mz-rodbase';
      base.style.left = (rx - 32) + 'px'; base.style.top = '-6px';
      box.insertBefore(base, img); box.insertBefore(rod, img);
    }
    out.style.top = top + 'px';
    img.replaceWith(out);
    const id = box.dataset.id;
    const wsh = id && document.getElementById('mzwsh-' + id);
    if (wsh && !flat) {
      const P = 36, sc = document.createElement('canvas');
      sc.width = dw + 2 * P; sc.height = dh + 2 * P;
      const q = sc.getContext('2d');
      q.filter = 'brightness(0) blur(10px)';
      q.drawImage(out, P, P);
      sc.className = 'mz-img';
      sc.style.left = (-dw / 2 - P + 40) + 'px'; sc.style.top = (-dh - P + 16) + 'px';
      wsh.appendChild(sc);
    }
    const feet = id && document.getElementById('mzfeet-' + id);
    if (feet && !flat && !mounted) {
      const tall = Math.max(1, y1 - y0), near = mode === 'figure' ? tall * .025 + 1 : tall * .04 + 1;
      const mid = (x0 + x1) / 2, halves = mode === 'figure' ? [[x0, mid], [mid, x1 + 1]] : [[x0, x1 + 1]];
      for (const [a, b] of halves) {
        let lo = -1, hi = -1;
        for (let x = Math.floor(a); x < b; x++) if (low[x] >= y1 - near) { if (lo < 0) lo = x; hi = x; }
        if (lo < 0) continue;
        const L = ((lo / k) - sx) * s - dw / 2, Rr = ((hi + 1) / k - sx) * s - dw / 2;
        const ww = Math.max(18, (Rr - L) * 1.3), cx = (L + Rr) / 2;
        const e = document.createElement('div');
        e.className = 'mz-feet';
        e.style.left = (cx - ww / 2) + 'px'; e.style.top = '0px'; e.style.width = ww + 'px';
        feet.appendChild(e);
      }
    }
  }
  window.__ready = (async () => {
    try { if (prev) await prev; } catch (e) {}
    if (document.readyState === 'loading') {
      await new Promise(r => document.addEventListener('DOMContentLoaded', r, {once: true}));
    }
    for (const box of document.querySelectorAll('.mz-art')) { try { await prep(box); } catch (e) {} }
    // Names: shrink until no word runs past the edge and it takes at most N lines.
    for (const el of document.querySelectorAll('[data-mzfit]')) {
      const maxW = +el.dataset.mzfit, lines = +(el.dataset.mzlines || 1), one = +(el.dataset.mzone || 0);
      let size = parseFloat(getComputedStyle(el).fontSize), guard = 90;
      if (one) {
        const size0 = size;
        el.style.whiteSpace = 'nowrap';
        while (guard-- > 0 && size > size0 * one && el.scrollWidth > maxW + 2) { size *= 0.97; el.style.fontSize = size + 'px'; }
        if (el.scrollWidth <= maxW + 2) continue;
        el.style.whiteSpace = 'normal';
      }
      const bad = () => {
        if (el.scrollWidth > maxW + 2) return true;
        const lh = parseFloat(getComputedStyle(el).lineHeight) || size * 1.1;
        return el.offsetHeight > lh * lines + 2;
      };
      while (guard-- > 0 && size > 12 && bad()) { size *= 0.96; el.style.fontSize = size + 'px'; }
    }
    // A placard never grows past its space on the wall.
    for (const card of document.querySelectorAll('[data-mzmaxh]')) {
      const maxH = +card.dataset.mzmaxh;
      let guard = 40;
      while (guard-- > 0 && card.offsetHeight > maxH) {
        for (const el of card.querySelectorAll('.n,.k,.v,.l,.p')) {
          el.style.fontSize = (parseFloat(getComputedStyle(el).fontSize) * 0.96) + 'px';
        }
      }
    }
  })();
})();</script>"""


def _a(name: str, t: float, dur: float, ease: str = "linear", extra: str = "") -> str:
    return f"animation:{name} {dur:.3f}s {ease} {t:.3f}s 1 normal both;{extra}"


def _kind(it: dict) -> str:
    rarity = it.get("rarity_label") or (it.get("rarity") or "").title()
    return " ".join(x for x in (rarity, it.get("type") or "") if x).strip()


def _intro(it: dict) -> str:
    """Epic's own words, as written ("Chapter 1, Season 3"), checked against the
    format's parse of them."""
    ch, se = _season(it)
    raw = ((it.get("introduction") or {}).get("text") or "").strip().rstrip(".").replace("Introduced in ", "")
    if raw.upper() == f"{ch}, {se}":
        return raw
    return f"{ch.title()}, {se.title()}"


def _nb(text: str) -> str:
    """Keep "Chapter 1" and "Season 3" together if the line has to wrap."""
    return re.sub(r"\b(Chapter|Season) ", r"\1&nbsp;", text)


def _is_figure(it: dict) -> bool:
    return (it.get("type") or "").lower() == "outfit"


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


# ------------------------------------------------------------------ the room

def _plinth(uid: str, x: float, y_front: float, w: int, d: int, h: int) -> str:
    """A white plinth: the top face in perspective (the vanishing point to the right),
    lit by the spot above; the front face with light fall-off. (x, y_front) is the
    front face's top-left corner."""
    sl, sr = int(d * .36), 4
    Wd, Hd = w + 40, d + h + 30
    return (f'<svg class="abs" style="left:{x:.0f}px;top:{y_front - d:.0f}px" width="{Wd}" height="{Hd}" '
            f'viewBox="0 0 {Wd} {Hd}"><defs>'
            f'<linearGradient id="tf{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ddd7cc"/>'
            f'<stop offset=".55" stop-color="#f3f0ea"/><stop offset="1" stop-color="#fdfcf9"/></linearGradient>'
            f'<radialGradient id="th{uid}" cx=".47" cy=".55" r=".55"><stop offset="0" stop-color="#fff" stop-opacity=".55"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="ff{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eeeae2"/>'
            f'<stop offset=".25" stop-color="#dcd6ca"/><stop offset=".65" stop-color="#bdb5a7"/>'
            f'<stop offset=".93" stop-color="#9f9789"/><stop offset="1" stop-color="#857d70"/></linearGradient>'
            f'<linearGradient id="fs{uid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity=".10"/>'
            f'<stop offset=".35" stop-color="#fff" stop-opacity="0"/><stop offset=".8" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity=".10"/></linearGradient></defs>'
            f'<path d="M0,{d} L{w},{d} L{w + sr},0 L{sl},0 Z" fill="url(#tf{uid})"/>'
            f'<path d="M0,{d} L{w},{d} L{w + sr},0 L{sl},0 Z" fill="url(#th{uid})"/>'
            f'<rect x="0" y="{d}" width="{w}" height="{h}" fill="url(#ff{uid})"/>'
            f'<rect x="0" y="{d}" width="{w}" height="{h}" fill="url(#fs{uid})"/>'
            f'<path d="M0,{d + .75} L{w},{d + .75}" stroke="#fff" stroke-opacity=".9" stroke-width="1.5"/>'
            f'<path d="M{sl},0.5 L{w + sr},0.5" stroke="#b9b2a5" stroke-width="1"/></svg>')


def _glass(x: float, top: float, w: int, bottom: float, d: int) -> str:
    """A glass case: faint panes, bright edges, a lid in perspective and a soft
    diagonal reflection."""
    sl = int(d * .46)
    h = bottom - top
    Wd, Hd = w + sl + 6, h + d + 4
    return (f'<svg class="mz-glass" style="left:{x:.0f}px;top:{top - d:.0f}px" width="{Wd}" height="{Hd:.0f}" '
            f'viewBox="0 0 {Wd} {Hd:.0f}"><defs>'
            f'<linearGradient id="gr{int(x)}" x1="0" y1="0" x2="1" y2=".55">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".30" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset=".38" stop-color="#fff" stop-opacity=".13"/><stop offset=".47" stop-color="#fff" stop-opacity=".03"/>'
            f'<stop offset=".62" stop-color="#fff" stop-opacity=".07"/><stop offset=".68" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
            f'<path d="M{sl},0 L{w + sl},0 L{w + sl},{h:.0f} " fill="none" stroke="#fff" stroke-opacity=".16" stroke-width="2"/>'
            f'<path d="M0,{d} L{w},{d} L{w + sl},0 L{sl},0 Z" fill="#fff" fill-opacity=".07" stroke="#fff" '
            f'stroke-opacity=".45" stroke-width="2"/>'
            f'<rect x="0" y="{d}" width="{w}" height="{h:.0f}" fill="#dfe8e6" fill-opacity=".05"/>'
            f'<rect x="0" y="{d}" width="{w}" height="{h:.0f}" fill="url(#gr{int(x)})"/>'
            f'<path d="M{w},{d} L{w + sl},0 M{w},{d + h:.0f} L{w + sl},{h:.0f}" stroke="#fff" stroke-opacity=".22" stroke-width="2"/>'
            f'<rect x="1" y="{d + 1}" width="{w - 2}" height="{h - 2:.0f}" fill="none" stroke="#fff" stroke-opacity=".42" '
            f'stroke-width="2.5"/></svg>')


def _lights(x0: float, t_on, placard: bool = True) -> str:
    """The pools of light an exhibit's spot and label light throw on the wall and
    floor. t_on=None: already on."""
    on = "" if t_on is None else _a("mzon", t_on, .62)
    wash = "" if t_on is None else _a("mzfade", t_on + (LABEL - CLICK), .45, "ease-out")
    out = (f'<div class="mz-pool" style="left:{x0 + FX + 26:.0f}px;top:700px;{on}"></div>'
           f'<div class="mz-fpool" style="left:{x0 + FX + 10:.0f}px;top:{PL_FRONT + PL_H + 16}px;{on}"></div>')
    if placard:
        out += (f'<div class="mz-wash" style="left:{x0 + COL_X + COL_W / 2:.0f}px;top:{PLACARD_Y + 210}px;{wash}">'
                f'</div>')
    return out


def _fixture(x0: float, t_on) -> str:
    fx = x0 + FX - 64
    lens = "" if t_on is None else _a("mzon", t_on, .62)
    return (f'<div class="mz-fix" style="left:{fx - 17:.0f}px;top:{CEIL + 12}px;transform:rotate(-16deg)">'
            f'<div class="mz-lens" style="left:4px;bottom:-3px;{lens}"></div></div>')


def _cone(x0: float, t_on, bottom: float) -> str:
    fx = x0 + FX - 64
    cl, cr, ctop, cbot = x0 + FX - 214, x0 + FX + 196, CEIL + 70, bottom - 30
    lens = (fx + 6 - cl) / (cr - cl) * 100
    on = "" if t_on is None else _a("mzon", t_on, .62)
    return (f'<div class="mz-conew" style="left:{cl:.0f}px;top:{ctop}px;width:{cr - cl:.0f}px;height:{cbot - ctop:.0f}px;'
            f'{on}"><div class="mz-cone" style="clip-path:polygon({lens - 1.5:.1f}% 0,{lens + 1.5:.1f}% 0,100% 100%,'
            f'0 100%)"></div></div>')


def _exhibit(ctx, it: dict, uid: str, x0: float, t_on, fig_h: int = FIG_H) -> str:
    """The plinth and what's on it: an outfit standing on a plinth, or anything
    else inside a glass case; a card with the name when there's no art."""
    art = ctx.art(it)
    figure = _is_figure(it) and bool(art)
    dim = "" if t_on is None else _a("mzoff", t_on, .62)
    dimfig = "" if t_on is None else _a("mzfig", t_on, .62)
    cx = x0 + FX
    html = []
    if figure:
        top = PL_FRONT - PL_D
        html.append(f'<div class="mz-slot mz-wsh" id="mzwsh-{uid}" style="left:{cx:.0f}px;top:{PL_FRONT - 10}px;'
                    f'{_a("mzon", t_on, .62) if t_on is not None else ""}"></div>')
        html.append(_cone(x0, t_on, PL_FRONT))
        pb = PL_FRONT + PL_H
        html.append(f'<div class="mz-pbase" style="left:{cx - PL_W // 2 - 26:.0f}px;top:{pb - 22}px;width:{PL_W + 58}px;'
                    f'height:40px"></div>')
        html.append(f'<div class="mz-refl" style="left:{cx - PL_W // 2:.0f}px;top:{pb + 4}px;width:{PL_W}px;height:120px;'
                    f'{_a("mzon", t_on, .62) if t_on is not None else ""}"></div>')
        html.append(_plinth(uid, cx - PL_W // 2, PL_FRONT, PL_W, PL_D, PL_H))
        if t_on is not None:
            html.append(f'<div class="abs" style="left:{cx - PL_W // 2 - 2:.0f}px;top:{top - 2}px;width:{PL_W + 10}px;'
                        f'height:{PL_D + PL_H + 4}px;background:rgba(16,12,9,.62);clip-path:polygon(0 {PL_D + 2}px,'
                        f'8.5% 0,100% 0,100% 100%,0 100%);{dim}"></div>')
        html.append(f'<div class="mz-cast" style="left:{cx - 40:.0f}px;top:{top + 8}px;width:150px;height:40px;'
                    f'{_a("mzon", t_on, .62) if t_on is not None else ""}"></div>')
        html.append(f'<div class="mz-slot" id="mzfeet-{uid}" style="left:{cx:.0f}px;top:{PL_FRONT - 10}px"></div>')
        html.append(f'<div class="mz-art" data-id="{uid}" data-mode="figure" data-w="{FIG_W}" data-h="{fig_h}" '
                    f'data-up="2.6" style="left:{cx:.0f}px;top:{PL_FRONT - 10}px;{dimfig}">'
                    f'<img src="{art}" alt=""></div>')
        return "".join(html)

    # a glass case on a plinth
    top = OB_FRONT - OB_D
    floor_y = OB_FRONT - 22
    html.append(_cone(x0, t_on, OB_FRONT))
    pb = OB_FRONT + OB_H
    html.append(f'<div class="mz-pbase" style="left:{cx - OB_W // 2 - 26:.0f}px;top:{pb - 22}px;width:{OB_W + 58}px;'
                f'height:40px"></div>')
    html.append(f'<div class="mz-refl" style="left:{cx - OB_W // 2:.0f}px;top:{pb + 4}px;width:{OB_W}px;height:120px;'
                f'{_a("mzon", t_on, .62) if t_on is not None else ""}"></div>')
    html.append(_plinth(uid, cx - OB_W // 2, OB_FRONT, OB_W, OB_D, OB_H))
    html.append(f'<div class="mz-slot" id="mzfeet-{uid}" style="left:{cx - 8:.0f}px;top:{floor_y}px"></div>')
    if art:
        html.append(f'<div class="mz-art" data-id="{uid}" data-mode="object" data-w="{OBJ_W}" data-h="{OBJ_H}" '
                    f'data-up="2.4" data-lift="{floor_y - OBJ_MID}" style="left:{cx - 8:.0f}px;top:{floor_y}px;{dimfig}">'
                    f'<img src="{art}" alt=""></div>')
    else:
        # no picture of it: a card with its name stands in the case
        html.append(f'<div class="abs" style="left:{cx - 8 - 150:.0f}px;top:{floor_y - 2}px;width:300px;height:0;'
                    f'{dimfig}"><div class="mz-tent" style="left:5px;bottom:0;transform:rotate(-2deg);'
                    f'transform-origin:50% 100%"><div class="t" data-mzfit="250" data-mzlines="3" '
                    f'style="width:250px;margin:0 auto">{esc(it["name"])}</div>'
                    f'<div class="u">{esc(_kind(it).upper())}</div></div></div>')
    html.append(_glass(cx - OB_W // 2 + 4, VT_TOP, OB_W - 8, OB_FRONT - 4, VT_D))
    if t_on is not None:
        html.append(f'<div class="abs" style="left:{cx - OB_W // 2 - 2:.0f}px;top:{VT_TOP - VT_D - 2}px;'
                    f'width:{OB_W + 30}px;height:{OB_FRONT + OB_H - VT_TOP + VT_D + 4}px;background:rgba(16,12,9,.55);'
                    f'{dim}"></div>')
    return "".join(html)


def _placard(it: dict, x: float, y: float, t_label) -> str:
    dim = "" if t_label is None else f'<div class="dim" style="{_a("mzunfade", t_label, .45, "ease-out")}"></div>'
    iw = COL_W - 64
    return (f'<div class="mz-card" data-mzmaxh="{PLACARD_MAXH}" style="left:{x:.0f}px;top:{y:.0f}px">'
            f'<div class="n" data-mzfit="{iw}" data-mzlines="2" style="width:{iw}px">{esc(it["name"])}</div>'
            f'<div class="k" data-fit="{iw}">{esc(_kind(it))}</div><div class="r"></div>'
            f'<div class="l">Introduced in</div><div class="v" data-mzfit="{iw}" data-mzlines="2" data-mzone=".82" '
            f'style="width:{iw}px;white-space:normal">{_nb(esc(_intro(it)))}</div>'
            f'<div class="l">In the shop today</div><div class="v" data-fit="{iw}">{int(it["price"]):,} V-Bucks</div>'
            f'{dim}</div>')


def _bay_exhibit(ctx, it: dict, k: int, n: int, x0: float, t0: float, last_note: str) -> tuple:
    """One exhibit's bay; t0 is the start of its slot. Returns (html, sounds)."""
    rank = n - k
    t_on, t_label = t0 + CLICK, t0 + LABEL
    uid = f"e{k}"
    html = [_lights(x0, t_on), _fixture(x0, t_on), _exhibit(ctx, it, uid, x0, t_on),
            f'<div class="abs" style="left:{x0 + COL_X:.0f}px;top:{HDR_Y}px">'
            f'<div class="mz-hdr-k mz-nw">EXHIBIT</div><div class="mz-hdr-n mz-nw">No. {rank}</div></div>',
            _placard(it, x0 + COL_X, PLACARD_Y, t_label)]
    sounds = [(t0 - PAN_LEAD + .08, "whoosh"), (t_on, "click")]
    if last_note:
        # No. 1: the wall says so, in the museum's hand, and a gold rule draws under it.
        tw = t0 + 2.25
        html.append(f'<div class="abs mz-hdr-x mz-nw" data-fit="{COL_W}" style="left:{x0 + COL_X + 2:.0f}px;'
                    f'top:{HDR_Y + 152}px;{write_on(tw, .7, 16)}">{esc(last_note)}</div>'
                    f'<div class="abs" style="left:{x0 + COL_X + 4:.0f}px;top:{HDR_Y + 214}px;width:230px;height:3px;'
                    f'background:linear-gradient(90deg,#9a7a32,#e4c77e 45%,#a8843a);transform-origin:0 50%;'
                    f'{_a("mzrule", tw + .55, .45, "cubic-bezier(.3,0,.2,1)")}"></div>')
        sounds.append((tw, "reveal"))
    return "".join(html), sounds


def _bay_hook(ctx, hero: dict, n: int, x0: float = 0) -> str:
    day = ctx.day
    when = day.strftime("%B %-d, %Y").upper()
    html = [_lights(x0, None), f'<div class="mz-wash" style="left:{x0 + 420}px;top:300px;opacity:.8"></div>',
            _fixture(x0, None), _exhibit(ctx, hero, "hero", x0, None, FIG_H - 44),
            f'<div class="mz-title mz-nw" style="left:{x0 + 84}px;top:212px">THE OG MUSEUM</div>'
            f'<div class="mz-hair" style="left:{x0 + 88}px;top:294px;width:86px"></div>'
            f'<div class="mz-sub mz-nw" style="left:{x0 + 86}px;top:310px">The oldest items in today\'s Item Shop</div>'
            f'<div class="mz-sc mz-nw" style="left:{x0 + 88}px;top:374px">FORTNITE · {esc(when)}</div>']
    words = {6: "Six", 7: "Seven", 8: "Eight"}.get(n, str(n))
    html.append(f'<div class="mz-card" style="left:{x0 + COL_X}px;top:{PLACARD_Y + 30}px">'
                f'<div class="l">Today\'s exhibition</div>'
                f'<div class="p" style="margin-top:10px">{words} items from today\'s shop, counting down to the '
                f'oldest.</div><div class="r"></div>'
                f'<div class="l" style="white-space:normal;line-height:1.25">Each is dated by the season Epic says it '
                f'was introduced in.</div></div>')
    return "".join(html)


def _postcard(ctx, it: dict, x: float, y: float, rot: float) -> str:
    art = ctx.art(it)
    cols = [c for c in (it.get("tile_colors") or []) if isinstance(c, str) and c.startswith("#") and len(c) == 7]
    c1, c2 = (cols + ["#6b6b73", "#2a2a30"])[:2] if cols else ("#6b6b73", "#2a2a30")
    bg = f"radial-gradient(ellipse 80% 70% at 50% 40%,{c1},{c2})"
    inner = (f'<div class="mz-art" data-mode="card" data-w="190" data-h="198" data-up="2.4" '
             f'style="left:107px;top:208px"><img src="{art}" alt=""></div>' if art else
             f'<div class="abs" style="inset:0;display:flex;align-items:center;justify-content:center;padding:14px;'
             f'font-family:\'Cormorant Garamond\';font-style:italic;font-size:34px;color:#fff;text-align:center">'
             f'{esc(it["name"])}</div>')
    return (f'<div class="mz-post" style="left:{x:.0f}px;top:{y:.0f}px;transform:rotate({rot}deg)">'
            f'<div class="ph" style="background:{bg}">{inner}</div>'
            f'<div class="cap" data-fit="206">{esc(it["name"])}</div></div>')


def _bay_exit(ctx, picks: list, x0: float) -> str:
    outfits = [i for i in picks if _is_figure(i)]
    three = (outfits + [i for i in picks if i not in outfits])[:3]
    html = [f'<div class="mz-pool" style="left:{x0 + 540}px;top:760px;opacity:.9"></div>',
            f'<div class="mz-wash" style="left:{x0 + 540}px;top:420px;opacity:.9"></div>',
            f'<div class="mz-title mz-nw" style="left:{x0 + 84}px;top:212px;font-size:48px;letter-spacing:.28em">'
            f'THANK YOU FOR VISITING</div>'
            f'<div class="mz-hair" style="left:{x0 + 88}px;top:280px;width:86px"></div>'
            f'<div class="mz-sub" style="left:{x0 + 84}px;top:296px;font-size:90px;line-height:1">How OG is<br>'
            f'your locker?</div>'
            f'<div class="mz-sc mz-nw" style="left:{x0 + 90}px;top:516px">TELL US IN THE COMMENTS</div>'
            f'<div class="mz-sc mz-nw" style="left:{x0 + 90}px;top:574px;font-size:21px;letter-spacing:.3em;'
            f'color:#5e554b">POSTCARDS · TODAY\'S EXHIBITS</div>']
    for j, it in enumerate(three):
        x, rot = [(84, -3), (372, 2), (660, -2)][j]
        html.append(_postcard(ctx, it, x0 + x, 606, rot))
    html.append(f'<div class="mz-ledge" style="left:{x0 + 60}px;top:880px;width:900px"></div>')
    return "".join(html)


def _paddle() -> str:
    return (f'<div class="mz-paddle" style="left:{PAD_X}px;top:{PAD_Y}px">'
            f'<div class="mz-pole" style="top:200px"></div>'
            f'<div class="mz-board"><div class="s1 mz-nw">Support the museum</div><div class="s2 mz-nw">USE CODE:</div>'
            f'<div class="s3">BAD</div><div class="s4">#EpicPartner</div></div></div>')


# ------------------------------------------------------------------ camera

def _camera(comp: Comp, pans: list, pushes: list, dur: float):
    """The room's pan (translateX) and dolly (scale), the rope's faster pan, and the
    guide's walk: the paddle tips back as the guide sets off, bobs with the steps,
    swings forward as they stop, and settles."""
    room, rope, dol, dolr, walk = [(0, "transform:translateX(0)", "linear")], \
        [(0, "transform:translateX(0)", "linear")], [], [], []
    for k, (s, e) in enumerate(pans):
        room += [(s, f"transform:translateX({-k * BAY}px)", EASE_PAN), (e, f"transform:translateX({-(k + 1) * BAY}px)",
                                                                      "linear")]
        rope += [(s, f"transform:translateX({-k * ROPE_P}px)", EASE_PAN),
                 (e, f"transform:translateX({-(k + 1) * ROPE_P}px)", "linear")]
    room.append((dur, f"transform:translateX({-len(pans) * BAY}px)", ""))
    rope.append((dur, f"transform:translateX({-len(pans) * ROPE_P}px)", ""))

    # dolly: a slow push while an exhibit holds, easing back out as the camera moves on
    prev_end, prev_scale = 0.0, 1.0
    dol.append((0, "transform:scale(1)", "cubic-bezier(.35,0,.45,1)"))
    dolr.append((0, "transform:scale(1)", "cubic-bezier(.35,0,.45,1)"))
    for (s, e), push in zip(pans, pushes):
        dol += [(s, f"transform:scale({push:.4f})", "cubic-bezier(.45,0,.3,1)"),
                (e, "transform:scale(1)", "cubic-bezier(.35,0,.45,1)")]
        pr = 1 + (push - 1) * 2.2
        dolr += [(s, f"transform:scale({pr:.4f})", "cubic-bezier(.45,0,.3,1)"),
                 (e, "transform:scale(1)", "cubic-bezier(.35,0,.45,1)")]
    dol.append((dur, f"transform:scale({pushes[-1]:.4f})", ""))
    dolr.append((dur, f"transform:scale({1 + (pushes[-1] - 1) * 2.2:.4f})", ""))

    walk.append((0, "transform:rotate(0deg) translateY(0)", "ease-in-out"))
    for s, e in pans:
        walk.append((s, "transform:rotate(0deg) translateY(0)", "ease-out"))
        walk.append((s + .22, "transform:rotate(-1.3deg) translateY(2px)", "ease-in-out"))
        t, up = s + .22, True
        while t + .3 < e - .2:
            t += .3
            walk.append((t, f"transform:rotate({-.9 if up else -1.2}deg) translateY({-5 if up else 3}px)", "ease-in-out"))
            up = not up
        walk.append((e - .02, "transform:rotate(.9deg) translateY(-2px)", "ease-in-out"))
        walk.append((e + .3, "transform:rotate(-.35deg) translateY(1px)", "ease-in-out"))
        walk.append((e + .62, "transform:rotate(.12deg) translateY(0)", "ease-in-out"))
        walk.append((e + .95, "transform:rotate(0deg) translateY(0)", "ease-in-out"))
    walk.append((dur, "transform:rotate(0deg) translateY(0)", ""))
    for name, pts in (("mzroom", room), ("mzrope", rope), ("mzdolly", dol), ("mzdollyr", dolr), ("mzwalk", walk)):
        comp.css(_kf(name, pts, dur))


# ------------------------------------------------------------------ the video

def og_check(ctx, picks: list) -> Comp:
    n = len(picks)
    R = min(R_MAX, max(R_MIN, CONTENT / n))
    show = list(reversed(picks))                  # count down: the oldest comes last
    content_end = HOOK + n * R
    comp = Comp(pad_to(content_end))
    dur = comp.duration
    comp.use_fonts(*FONTS)
    comp.css(KIT_CSS)
    comp.css(CSS % dict(fx=FOCUS[0], fy=FOCUS[1], wl=WALL_LINE, wl3=WALL_LINE - 3, fh=H - WALL_LINE + 260,
                        ceil=CEIL, track=CEIL + 4, wall=tex("museum-wall.jpg"), floor=tex("museum-floor.jpg"),
                        grain=tex("museum-grain.png"), colw=COL_W, px=PIVOT[0], py=PIVOT[1], pw=PAD_W,
                        pole=PAD_W // 2 - 6, lime=LIME))

    outfits = [i for i in picks if _is_figure(i)]
    hero = (outfits or picks)[0]
    tied = sum(1 for p in picks if _order(p) == _order(picks[0])) > 1
    bays = n + 2
    width = bays * BAY + 800

    # ---- the room: one long wall, a bay per exhibit
    room = [f'<div class="mz-wall" style="width:{width}px"></div>',
            f'<div class="mz-floor" style="width:{width}px"></div>',
            f'<div class="mz-gap" style="width:{width}px"></div>',
            f'<div class="mz-ceil" style="width:{width}px"></div>',
            f'<div class="mz-track" style="width:{width}px"></div>',
            _bay_hook(ctx, hero, n, 0)]
    sounds = [(.3, "click")]
    for k, it in enumerate(show):
        t0 = HOOK + k * R
        note = ("Tied for oldest" if tied else "The oldest today") if k == n - 1 else ""
        html, snd = _bay_exhibit(ctx, it, k, n, (k + 1) * BAY, t0, note)
        room.append(html)
        sounds += snd
    room.append(_bay_exit(ctx, picks, (n + 1) * BAY))

    pans = [(HOOK + k * R - PAN_LEAD, HOOK + k * R - PAN_LEAD + PAN_D) for k in range(n + 1)]
    pushes = [1.03] * n + [1.055]                 # No. 1 gets a closer look
    _camera(comp, pans, pushes, dur)

    comp.add(f'<div class="full" style="z-index:0;background:#1d1915">'
             f'<div class="mz-cam" style="{_a("mzdolly", 0, dur)}">'
             f'<div class="mz-pan" style="width:{width}px;{_a("mzroom", 0, dur)}">{"".join(room)}</div></div></div>')
    # the velvet rope, nearest the camera, out of focus
    rope_w = (bays + 1) * ROPE_P + 1080
    comp.add(f'<div class="full" style="z-index:8;pointer-events:none">'
             f'<div class="mz-cam" style="{_a("mzdollyr", 0, dur)}">'
             f'<div class="mz-pan" style="width:{rope_w}px;{_a("mzrope", 0, dur)}">'
             f'<div class="abs" style="left:0;top:1180px;width:{rope_w}px;height:600px;'
             f'background:url({tex("museum-rope.png")}) 0 0/{ROPE_P}px 600px repeat-x"></div></div></div></div>')
    comp.add('<div class="full" style="z-index:9;pointer-events:none;overflow:hidden">'
             '<div class="mz-vig"></div><div class="mz-grain"></div></div>')

    # ---- the guide's paddle: the creator code, in every frame
    t_out = content_end - .2
    bx, by = PAD_X + PAD_W / 2, PAD_Y + 125           # the board's centre
    lift = (f"animation:mzlift 1.2s cubic-bezier(.45,0,.25,1) {t_out:.3f}s 1 normal both;"
            f"transform-origin:{bx:.0f}px {by:.0f}px")
    comp.css(f"@keyframes mzlift{{from{{transform:translate(0,0) scale(1)}}"
             f"to{{transform:translate({540 - bx:.0f}px,{1190 - by:.0f}px) scale(1.3)}}}}")
    comp.add(f'<div class="full" style="z-index:30;pointer-events:none"><div class="abs" style="inset:0;{lift}">'
             f'<div class="mz-walk" style="{_a("mzwalk", 0, dur)}">{_paddle()}</div></div></div>')
    comp.add(PREP_JS)
    comp.add(ART_JS)

    sounds.append((content_end + 1.3, "clap"))
    for t, kind in sounds:
        comp.cue(t, kind)
    comp.cues.sort()
    return comp
