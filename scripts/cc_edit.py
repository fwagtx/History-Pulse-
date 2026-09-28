"""
The edit kit: short videos cut the way a person cuts them in an editing app,
to a real track, instead of laid out by a template.

The template looks read as machine-made: a still layout, things popping in on
a timer, one synthesized bed under everything. What reads as made by a person
on TikTok is the apps' own vocabulary -- the picture over a blurred copy of
itself (CapCut's canvas blur), captions in the app's font in white boxes,
lower case with emojis, and every cut, zoom punch and shake on the music's
beat. This kit builds that on the same engine (cc_motion).

  music_for()  the track (cc_music, CC0 music by human producers) and its
               beat grid; `unit` is the beat, or two beats for a fast track,
               so a bar (4 units) is always 1.7-3 s
  Camera       one transform over the whole video, computed frame by frame
               in Python and written as keyframes: a slow push, zoom punches,
               shakes, whip pans and zoom-throughs, with motion blur
  Edit         scenes inside the camera (hard cuts on the beat); captions and
               the code sticker outside it, so they stay still while the
               picture moves, as an app's text track does
  caption()    TikTok's text styles in TikTok Sans (OFL): "box" (white, black
               text), "dark" (translucent black), "lime", "out" (outline)
  tile()       a cosmetic on its rarity / series colours, like a locker tile
  canvas()     the blurred copy of a tile that fills the frame behind it
  code()       USE CODE: BAD in a lime box, on screen in every frame

comp.music tells cc_audio.soundtrack to mix the track (or the synthesized bed
at the grid's tempo, where the library can't be had) under the effects.
"""

import math
import random

import cc_music
from cc_motion import (ACCENT, FPS, H, SAFE_LEFT, W, Comp, esc)
from cc_safe import COVER_TOP

FONT = "TikTok Sans"
FAMILY = "'TikTok Sans','Noto Color Emoji',sans-serif"
LIME = ACCENT

# In-game tile colours by rarity / series: (centre, edge).
TILE = {
    "common": ("#C4C4C4", "#5E5E5E"), "uncommon": ("#8BE33E", "#1C7A1C"), "rare": ("#3FD2FF", "#1257C4"),
    "epic": ("#E26BFF", "#6A20B8"), "legendary": ("#FFA85E", "#B8420F"), "mythic": ("#FFE46E", "#B98B0B"),
    "exotic": ("#7CF6FF", "#1B7FA0"), "icon": ("#5FF3F0", "#1F6F86"), "marvel": ("#F0393B", "#6E1414"),
    "dc": ("#6E8CFF", "#20349A"), "starwars": ("#F3D23A", "#2A2A2A"), "gaminglegends": ("#B865FF", "#35187F"),
    "dark": ("#E545FF", "#2B0A3D"), "frozen": ("#C9EBFF", "#3E7FB4"), "lava": ("#FF9C3A", "#7A1606"),
    "shadow": ("#8F8F9A", "#141418"), "slurp": ("#43F5E6", "#0E6FA8"), "lego": ("#FFD23F", "#C41F1F"),
}

CSS = f"""
.ed-cap{{position:absolute;font-family:{FAMILY};text-wrap:balance;line-height:1.36;z-index:40}}
.ed-cap>div{{transform-origin:50% 60%}}
.ed-box,.ed-dark,.ed-lime{{display:inline;padding:.06em .32em .1em;border-radius:.26em;
  -webkit-box-decoration-break:clone;box-decoration-break:clone}}
.ed-box{{background:#fff;color:#111}}
.ed-dark{{background:rgba(0,0,0,.62);color:#fff}}
.ed-lime{{background:{LIME};color:#0A0A0B}}
.ed-out{{color:#fff;-webkit-text-stroke:.15em #000;paint-order:stroke fill}}
.ed-out.lm{{color:{LIME}}}
.ed-emo{{position:absolute;font-family:'Noto Color Emoji',sans-serif;line-height:1;z-index:41}}
.ed-tile{{position:absolute;overflow:hidden;border-radius:30px;
  box-shadow:0 26px 60px rgba(0,0,0,.55),0 0 0 3px rgba(255,255,255,.14) inset}}
.ed-tile::after{{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;
  background:linear-gradient(180deg,rgba(255,255,255,.16) 0,rgba(255,255,255,0) 22%,rgba(0,0,0,0) 62%,rgba(0,0,0,.34) 100%)}}
.ed-fig{{position:absolute;left:50%;bottom:0;transform:translateX(-50%);display:block;
  object-fit:contain;object-position:50% 100%;filter:drop-shadow(0 18px 24px rgba(0,0,0,.35))}}
.ed-canvas{{position:absolute;left:-30%;top:-30%;width:160%;height:160%;object-fit:fill;max-width:none}}
.ed-code{{display:inline-block;background:{LIME};color:#0A0A0B;border-radius:24px;padding:12px 24px 14px 22px;
  font-family:{FAMILY};box-shadow:0 9px 0 rgba(0,0,0,.34),0 16px 34px rgba(0,0,0,.34);transform-origin:0 0}}
.ed-code-a{{font-size:40px;font-weight:800;line-height:1.05;letter-spacing:.02em}}
.ed-code-b{{font-size:128px;font-weight:900;line-height:.86;letter-spacing:-.01em;margin:2px 0 0 -4px}}
.ed-tag{{margin:16px 0 0 8px;font:700 25px/1 {FAMILY};color:#fff;-webkit-text-stroke:6px #000;paint-order:stroke fill}}
.ed-flash{{position:absolute;inset:0;background:#fff;pointer-events:none;opacity:0;z-index:90}}
@keyframes edpop{{0%{{transform:scale(.62);opacity:0}}45%{{transform:scale(1.07);opacity:1}}
  70%{{transform:scale(.98)}}100%{{transform:none;opacity:1}}}}
@keyframes edslam{{0%{{transform:scale(1.9);opacity:0}}55%{{transform:scale(.95);opacity:1}}100%{{transform:none;opacity:1}}}}
@keyframes edrise{{0%{{transform:translateY(34px);opacity:0}}100%{{transform:none;opacity:1}}}}
@keyframes edtype{{from{{clip-path:inset(-20% 100% -20% -2%)}}to{{clip-path:inset(-20% -2% -20% -2%)}}}}
@keyframes edhide{{from{{opacity:1}}to{{opacity:0}}}}
@keyframes edbeat{{0%{{transform:scale(1.09)}}100%{{transform:none}}}}
@keyframes edin{{0%{{transform:scale(1.18)}}100%{{transform:none}}}}
@keyframes edcount{{from{{--n:0}}to{{--n:var(--to)}}}}
"""


# ------------------------------------------------------------------ the music

class Beat:
    """The beat grid a video is cut to. `unit` is one beat, or two for a fast
    track; unit(i) is the time of unit i (extrapolated past the grid)."""

    def __init__(self, beats: list, bpm: float, music: dict, downbeat: int = 0):
        self.beats = list(beats)
        self.bpm = float(bpm)
        self.music = music
        per = 60.0 / self.bpm
        self.step = 2 if per < .42 else 1                 # beats per unit
        self.period = per * self.step
        k0 = downbeat % self.step if self.step > 1 else 0
        self.units = self.beats[k0::self.step] if self.beats else [0.0]

    def unit(self, i: float) -> float:
        """The time of unit i; fractional i interpolates, past the grid extrapolates."""
        n = len(self.units)
        k = int(math.floor(i))
        if 0 <= k < n - 1:
            return self.units[k] + (i - k) * (self.units[k + 1] - self.units[k])
        if k < 0:
            return self.units[0] + i * self.period
        return self.units[-1] + (i - (n - 1)) * self.period

    def bar(self, i: float) -> float:
        return self.unit(4 * i)


def music_for(seed: int, mood: str = "hype", want: str = "", avoid: tuple = (), day=None) -> Beat:
    """A library track for a video, with its beat grid starting on a downbeat;
    where the library can't be had, the synthesized bed's own grid. `day`
    lets a Christmas or Halloween track play in its month."""
    tr = cc_music.pick(mood, seed, want, avoid, day)
    if tr:
        grid = cc_music.beat_grid(tr["beats"], tr["cut"], 240.0)
        down = cc_music.downbeat(tr)
        grid = grid[down:]
        start = grid[0] if grid else 0.0
        music = {k: tr[k] for k in ("id", "path", "beats", "cut", "bpm", "artist", "title", "license", "page")}
        music["offset"] = start
        return Beat([b - start for b in grid], tr["bpm"], music)
    import cc_audio
    bpm = random.Random(seed).choice(cc_audio.BPMS)
    per = 60.0 / bpm
    return Beat([k * per for k in range(int(240 / per))], bpm, {"synth": bpm, "seed": seed})


# ------------------------------------------------------------------ the camera

def _smooth(p: float) -> float:
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


class Camera:
    """One transform for everything inside the camera, sampled on every frame."""

    def __init__(self, duration: float, fps: int = FPS, seed: int = 0):
        self.duration, self.fps = duration, fps
        self.pushes, self.punches, self.shakes, self.whips, self.zooms = [], [], [], [], []
        self.flashes = []
        self.rnd = random.Random(seed)

    def push(self, t0: float, t1: float, s0: float = 1.0, s1: float = 1.06, fx: float = W / 2, fy: float = H / 2):
        """A slow zoom from s0 to s1 between t0 and t1 around (fx, fy)."""
        self.pushes.append((t0, t1, s0, s1, fx, fy))

    def punch(self, t: float, amount: float = .07, dur: float = .32):
        """A zoom-in hit on a beat that eases back out."""
        self.punches.append((t, amount, dur))

    def shake(self, t: float, px: float = 18, dur: float = .38, deg: float = 1.2):
        r = self.rnd
        self.shakes.append((t, px, dur, deg, [r.uniform(0, 6.28) for _ in range(5)], r.uniform(38, 46)))

    def whip(self, t: float, dx: float = 0, dy: float = -1, px: float = 520, dur: float = .15, blur: float = 22):
        """A whip pan through a cut at t: out one side before, in from the other after."""
        self.whips.append((t, dx, dy, px, dur, blur))

    def zoom(self, t: float, amount: float = .5, dur: float = .17, blur: float = 14):
        """A zoom-through transition centred on the cut at t."""
        self.zooms.append((t, amount, dur, blur))

    def flash(self, t: float, strength: float = .85, dur: float = .22):
        self.flashes.append((t, strength, dur))

    def sample(self, t: float) -> tuple:
        s, fx, fy, tx, ty, rot, blur = 1.0, W / 2, H / 2, 0.0, 0.0, 0.0, 0.0
        for t0, t1, s0, s1, px, py in self.pushes:
            if t0 <= t < t1:
                s = s0 + (s1 - s0) * _smooth((t - t0) / max(1e-6, t1 - t0))
                fx, fy = px, py
                break
        for tp, amount, dur in self.punches:
            x = t - tp
            if 0 <= x < dur:
                s *= 1 + amount * (1 - x / dur) ** 3
        for tz, amount, dur, bl in self.zooms:
            x = t - tz
            if -dur <= x < dur:
                e = ((x + dur) / dur) ** 2 if x < 0 else (1 - x / dur) ** 2
                s *= 1 + amount * e
                blur = max(blur, bl * e)
        for tw, dx, dy, px, dur, bl in self.whips:
            x = t - tw
            if -dur <= x < dur:
                if x < 0:
                    e = ((x + dur) / dur) ** 2.2
                    tx -= dx * px * e
                    ty -= dy * px * e
                else:
                    e = (1 - x / dur) ** 2.2
                    tx += dx * px * e
                    ty += dy * px * e
                blur = max(blur, bl * e)
        for ts, px, dur, deg, ph, w in self.shakes:
            x = t - ts
            if 0 <= x < dur:
                e = (1 - x / dur) ** 2
                tx += px * e * (math.sin(w * x + ph[0]) + .5 * math.sin(2.3 * w * x + ph[1])) / 1.5
                ty += px * e * (math.sin(1.1 * w * x + ph[2]) + .5 * math.sin(2.7 * w * x + ph[3])) / 1.5
                rot += deg * e * math.sin(.9 * w * x + ph[4])
        return s, rot, tx, ty, blur, fx, fy

    def flash_at(self, t: float) -> float:
        o = 0.0
        for tf, strength, dur in self.flashes:
            x = t - tf
            if 0 <= x < dur:
                o = max(o, strength * (1 - x / dur) ** 2)
        return o

    @staticmethod
    def _track(values: list, tol: tuple, longest: int = 90) -> list:
        """The frames worth a keyframe: a straight line between kept frames
        stays within `tol` of every frame it skips (and skips at most
        `longest` frames), since the animation is linear between keyframes."""
        n = len(values)
        keep, anchor, i = [0], 0, 2
        while i < n:
            a, c = values[anchor], values[i]
            span = i - anchor
            ok = span <= longest
            j = anchor + 1
            while ok and j < i:
                p = (j - anchor) / span
                b = values[j]
                ok = all(abs(a[k] + (c[k] - a[k]) * p - b[k]) <= tol[k] for k in range(len(b)))
                j += 1
            if ok:
                i += 1
                continue
            anchor = i - 1
            keep.append(anchor)
            i = anchor + 2
        if keep[-1] != n - 1:
            keep.append(n - 1)
        return keep

    def css(self) -> tuple:
        """(keyframes css, the camera's animation style, the flash's animation style)."""
        n = int(round(self.duration * self.fps))
        cam, fl = [], []
        for i in range(n + 1):
            t = min(self.duration, i / self.fps)
            s, rot, tx, ty, blur, fx, fy = self.sample(t)
            r = math.radians(rot)
            a, b = s * math.cos(r), s * math.sin(r)
            e = fx + tx - (a * fx - b * fy)
            f = fy + ty - (b * fx + a * fy)
            cam.append((round(a, 5), round(b, 5), round(e, 2), round(f, 2), round(blur, 2)))
            fl.append((round(self.flash_at(t), 3),))
        d = self.duration

        def pct(i):
            return min(100.0, i / self.fps / d * 100)
        frames = []
        for i in self._track(cam, (2e-4, 2e-4, .15, .15, .15)):
            a, b, e, f, bl = cam[i]
            filt = f"blur({bl}px)" if bl > .05 else "none"
            frames.append(f"{pct(i):.5f}%{{transform:matrix({a},{b},{-b},{a},{e},{f});filter:{filt}}}")
        flash = []
        for i in self._track(fl, (.004,)):
            flash.append(f"{pct(i):.5f}%{{opacity:{fl[i][0]}}}")
        css = (f"@keyframes edcam{{{''.join(frames)}}}@keyframes edflash{{{''.join(flash)}}}")
        anim = f"animation:edcam {d:.3f}s linear 0s 1 normal both"
        fanim = f"animation:edflash {d:.3f}s linear 0s 1 normal both"
        return css, anim, fanim


# ------------------------------------------------------------------ pieces

def _anim(name: str, start: float, dur: float, ease: str = "cubic-bezier(.2,.8,.2,1)", fill: str = "both") -> str:
    return f"{name} {dur:.3f}s {ease} {start:.3f}s 1 normal {fill}"


def caption(text: str, x: float, y: float, size: float, start: float, end: float | None = None,
            style: str = "box", align: str = "center", width: float = 840, weight: int = 800,
            rot: float = 0.0, anim: str = "edpop", lh: float = 1.36, extra: str = "", name: str = "",
            raw: bool = False) -> str:
    """A caption the way the app sets one: `style` box / dark / lime / out /
    outlm (lime outline). x is the centre for align=center, the right edge for
    align=right, else the left edge; y the top. Shown from `start` until `end` (None: to the scene's end).
    `text` is escaped unless raw=True (then it is HTML, e.g. with a counter())."""
    text = text if raw else esc(text)
    cls = {"box": "ed-box", "dark": "ed-dark", "lime": "ed-lime", "out": "ed-out", "outlm": "ed-out lm"}[style]
    left = {"center": x - width / 2, "right": x - width}.get(align, x)
    anims = [_anim(anim, start, .34 if anim == "edpop" else .3)]
    if end is not None:
        anims.append(_anim("edhide", end, .04, "linear", "forwards"))
    nm = f' data-name="{esc(name)}"' if name else ""
    return (f'<div class="ed-cap"{nm} style="left:{left:.0f}px;top:{y:.0f}px;width:{width:.0f}px;text-align:{align};'
            f'transform:rotate({rot:.2f}deg);line-height:{lh}">'
            f'<div style="font-size:{size:.0f}px;font-weight:{weight};animation:{",".join(anims)};{extra}">'
            f'<span class="{cls}">{text}</span></div></div>')


def emoji(ch: str, cx: float, cy: float, size: float, start: float, end: float | None = None,
          rot: float = 0.0) -> str:
    """A big emoji sticker, popped on (decoration: the checker ignores it)."""
    anims = [_anim("edpop", start, .36)]
    if end is not None:
        anims.append(_anim("edhide", end, .04, "linear", "forwards"))
    return (f'<div class="ed-emo" data-safe="ignore" style="left:{cx - size / 2:.0f}px;top:{cy - size / 2:.0f}px;'
            f'font-size:{size:.0f}px;transform:rotate({rot:.1f}deg)"><div style="animation:{",".join(anims)}">'
            f"{ch}</div></div>")


def counter(value: int, start: float, dur: float, steps: int = 0) -> str:
    """A number that counts up from 0 to `value` between start and start + dur,
    then shows the exact figure with its thousands comma."""
    steps = steps or min(int(value), 40)
    k = f"edc{int(start * 1000)}_{int(value)}"
    roll = (f"<style>@keyframes {k}{{from{{--n:0}}to{{--n:{int(value)}}}}}</style>"
            f'<span class="count" style="position:absolute;left:0;right:0;animation:{k} {dur:.3f}s '
            f'steps({steps},end) {start:.3f}s 1 normal both,{_anim("edhide", start + dur, .01, "linear", "forwards")}"></span>')
    final = (f'<span style="opacity:0;animation:{_anim("fadein", start + dur, .01, "linear")},'
             f'{_anim("edbeat", start + dur, .3)}">{int(value):,}</span>')
    return f'<span style="position:relative;display:inline-block">{roll}{final}</span>'


def tile_colors(item: dict) -> tuple:
    """The (centre, edge) colours of an item's tile: its series' own colours
    when the data has them, else its rarity's."""
    raw = item.get("raw") or item
    series = raw.get("series") if isinstance(raw.get("series"), dict) else None
    cols = [c for c in ((series or {}).get("colors") or []) if isinstance(c, str) and len(c) >= 6]
    if len(cols) >= 3:
        return "#" + cols[0][:6], "#" + cols[min(3, len(cols) - 1)][:6]
    rar = item.get("rarity")
    rar = rar.get("value") if isinstance(rar, dict) else rar
    return TILE.get(str(rar or "rare").lower(), TILE["rare"])


def tile(src: str, item: dict, x: float, y: float, w: float, h: float, iid: str,
         trim: str | bool = "figure", fig: float = .95, name: str = "", extra: str = "",
         fig_style: str = "") -> str:
    """A cosmetic on its tile. `src` is the picture's attribute (Edit.src(uri),
    or '' for none). The art is cropped to the cosmetic (data-trim) and stands
    on the tile's bottom edge, `fig` of the tile's height."""
    c1, c2 = tile_colors(item)
    bg = (f"radial-gradient(ellipse 80% 70% at 50% 36%,{c1} 0%,{c2} 78%,{_shade(c2, .55)} 100%)")
    tr = ' data-trim="figure"' if trim == "figure" else (" data-trim" if trim else "")
    art = (f'<img id="{iid}" class="ed-fig"{tr} data-name="{esc(name or item.get("name", ""))}" {src} '
           f'style="height:{h * fig:.0f}px;max-width:{w * .96:.0f}px;{fig_style}">') if src else ""
    return (f'<div class="ed-tile" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px;'
            f'background:{bg};{extra}">{art}</div>')


def _shade(hexc: str, k: float) -> str:
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


def canvas(of: str, colors: tuple, scale: float = 1.0, dim: float = .5, blur: float = 7) -> str:
    """The blurred copy of a tile filling the frame (and the camera's margins),
    made before frame 0 from the tile's own (trimmed) art -- see PREP."""
    return (f'<img class="ed-canvas" data-safe="ignore" data-canvas="{of}" data-colors="{colors[0]},{colors[1]}" '
            f'data-scale="{scale}" data-dim="{dim}" data-blur="{blur}" '
            f'src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">')


# Runs after cc_looks.PREP_JS (which trims the art): paints each canvas.
PREP = """<script>window.__ready = (async (prev) => {
  try { if (prev) { await prev; } } catch (e) {}
  if (document.readyState === 'loading') {
    await new Promise(r => document.addEventListener('DOMContentLoaded', r, {once: true}));
  }
  for (const img of document.querySelectorAll('img[data-canvas]')) {
    try {
      const src = document.getElementById(img.dataset.canvas);
      const [c1, c2] = (img.dataset.colors || '#333333,#111111').split(',');
      const w = 216, h = 384;
      const c = document.createElement('canvas'); c.width = w; c.height = h;
      const g = c.getContext('2d');
      const grad = g.createRadialGradient(w / 2, h * .4, 4, w / 2, h * .4, h * .62);
      grad.addColorStop(0, c1); grad.addColorStop(1, c2);
      g.fillStyle = grad; g.fillRect(0, 0, w, h);
      if (src) {
        if (src.decode) { await src.decode().catch(() => {}); }
        const s = +(img.dataset.scale || 1);
        const ah = h * .62 * s, aw = ah * (src.naturalWidth || 1) / (src.naturalHeight || 1);
        g.filter = `blur(${+(img.dataset.blur || 7)}px) saturate(1.3)`;
        g.drawImage(src, (w - aw) / 2, h * .47 - ah / 2, aw, ah);
        g.filter = 'none';
      }
      g.fillStyle = `rgba(0,0,0,${+(img.dataset.dim || .5)})`; g.fillRect(0, 0, w, h);
      img.src = c.toDataURL('image/jpeg', .92);
      if (img.decode) { await img.decode().catch(() => {}); }
    } catch (e) {}
  }
})(window.__ready);</script>"""


def code(x: float = SAFE_LEFT + 6, y: float = COVER_TOP + 2, rot: float = -3.0) -> str:
    """USE CODE: BAD on the channel's lime, in a box like the app's own text
    boxes, #EpicPartner under it. On screen and at rest in every frame (it
    sits outside the camera); inside the safe box, below the cover crop line."""
    return (f'<div class="abs" data-safe="key" data-name="code" style="left:{x:.0f}px;top:{y:.0f}px;z-index:60">'
            f'<div class="ed-code" style="transform:rotate({rot:.1f}deg)"><div class="ed-code-a">USE CODE:</div>'
            f'<div class="ed-code-b">BAD</div></div><div class="ed-tag">#EpicPartner</div></div>')


# ------------------------------------------------------------------ the edit

class Edit:
    """Scenes inside the camera, captions and the code sticker over it."""

    def __init__(self, beat: Beat, duration: float, seed: int):
        self.beat = beat
        self.comp = Comp(duration)
        self.comp.music = beat.music
        self.comp.use_fonts(FONT)
        self.comp.css(CSS)
        self.cam = Camera(duration, seed=seed)
        self.rnd = random.Random(seed)
        self._inner, self._over = [], []
        self._arts = {}

    def src(self, uri: str) -> str:
        """An img's picture attribute: each picture is embedded once in the page
        (a skin is on the hook, its own screen and the outro) and set by a
        script before the art is trimmed."""
        if not uri:
            return ""
        if uri not in self._arts:
            self._arts[uri] = f"a{len(self._arts)}"
        return f'data-edsrc="{self._arts[uri]}"'

    def uid(self, prefix: str = "e") -> str:
        return self.comp.uid(prefix)

    @property
    def duration(self) -> float:
        return self.comp.duration

    def cue(self, t: float, kind: str):
        self.comp.cue(t, kind)

    def _vis(self, start: float, end: float) -> str:
        """Visible from start to end with hard cuts: step-end keyframes (two
        keyframes at one offset would merge in CSS and fade instead)."""
        d = self.comp.duration
        pct = lambda t: max(0.0, min(100.0, t / d * 100))   # noqa: E731
        name = self.comp.uid("edv")
        a, b = pct(start), pct(end)
        frames = [f"0%{{opacity:{1 if start <= 0 else 0}}}"]
        if a > 0:
            frames.append(f"{a:.5f}%{{opacity:1}}")
        if b < 100:
            frames.append(f"{b:.5f}%{{opacity:0}}")
            frames.append("100%{opacity:0}")
        else:
            frames.append("100%{opacity:1}")
        self.comp.css(f"@keyframes {name}{{{''.join(frames)}}}")
        return f"animation:{name} {d:.3f}s step-end 0s 1 normal both"

    def scene(self, start: float, end: float, inner: str, z: int = 1):
        """Inside the camera, visible from start to end, hard cuts both ways."""
        self._inner.append(f'<div class="scene" style="z-index:{z};{self._vis(start, end)}">{inner}</div>')

    def over(self, start: float, end: float, inner: str, z: int = 40):
        """Over the camera (captions): visible from start to end."""
        self._over.append(f'<div class="scene" style="z-index:{z};{self._vis(start, end)}">{inner}</div>')

    def finish(self) -> Comp:
        from cc_looks import PREP_JS
        css, anim, fanim = self.cam.css()
        self.comp.css(css)
        self.comp.add(PREP_JS)
        self.comp.add(PREP)
        self.comp.add(f'<div class="full" style="transform-origin:0 0;{anim}">{"".join(self._inner)}</div>')
        self.comp.add(f'<div class="ed-flash" style="{fanim}"></div>')
        for o in self._over:
            self.comp.add(o)
        self.comp.add(code())
        if self._arts:
            import json
            table = json.dumps({k: u for u, k in self._arts.items()})
            # Last in the page, so it runs as the page is parsed: before the
            # trimming (PREP_JS) that waits for the whole page.
            self.comp.add("<script>(() => { const A = " + table + "; for (const i of "
                          "document.querySelectorAll('img[data-edsrc]')) { i.src = A[i.dataset.edsrc]; } })();</script>")
        self.comp.cues.sort()
        return self.comp
