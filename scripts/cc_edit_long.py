"""
Long videos for YouTube in the edit style: 16:9 (1920x1080), narrated,
8-10 minutes, with the shorts' look -- the cosmetic on its tile over a blurred
copy of itself, TikTok Sans captions, a camera that pushes and punches -- a
narrator (cc_voice: Kokoro, free and open source), real music under the voice
(cc_music, a new track every chapter, ducked while the narrator speaks),
burned-in subtitles, YouTube chapters, and the lime code-entry card at the end.

    lv = LongEdit(seed, title)
    lv.segment(["line", "line"], draw, chapter="Intro")     # draw(lv, seg)
    comp, wav, chapters = lv.build(out_dir, wall_arts)
    render(comp, out_dir / "video.mp4", wav)                # cc_long.render

A segment lasts as long as its narration; draw(lv, seg) places its scenes with
lv.scene / lv.over and times things to seg.lines_at [(start, end)] per line,
so a number lands on the line that says it. Frame rules (YouTube's player
draws its controls over the bottom ~10% and, fullscreen and in the phone app,
a title and buttons over the top ~8%): text, the cosmetics and the code stay
inside x 96-1824, y 100-960 (cc_safe.LONG; check() verifies every video); the
code sticker sits at the top-left of that box, so nothing else goes in
x 96-310, y 96-260.
"""

import random
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import cc_audio as A
import cc_code_entry as CE
import cc_edit as ED
import cc_voice as V
from cc_motion import esc

W, H, FPS = 1920, 1080, 30
END_CARD = 6.2
SUB_BOTTOM = 960                  # the subtitles' last line ends here (one line: from 903, two: 846)
DUCK = .2                         # the music under the voice (1 = full level)
MUSIC_EVERY = 58.0                # a new track about every minute (a library cut is 75 s)
STICKER = (100, 100, .66)         # the code sticker: x, y, scale
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]")

CSS = """
.lv-sub{position:absolute;left:160px;width:1600px;text-align:center;z-index:45;
  font:700 44px/1.3 'TikTok Sans','Noto Color Emoji',sans-serif;color:#fff;
  -webkit-text-stroke:.14em #000;paint-order:stroke fill;text-wrap:balance}
"""


@dataclass
class Seg:
    lines: list
    draw: object
    chapter: str = ""
    lead: float = .45
    gap: float = .32
    tail: float = .6
    min_len: float = 0.0
    cue: str = "swoosh"
    t0: float = 0.0
    t1: float = 0.0
    lines_at: list = field(default_factory=list)
    voice: list = field(default_factory=list)
    data: dict = field(default_factory=dict)


class LongEdit:
    def __init__(self, seed: int, title: str, voice: str = V.VOICE, speed: float = V.SPEED, day=None):
        self.seed, self.title, self.voice, self.speed, self.day = seed, title, voice, speed, day
        self.segs = []
        self.rnd = random.Random(seed)
        self._inner, self._over, self._arts = [], [], {}
        self.comp = None
        self.cam = None
        self._n = 0

    # ------------------------------------------------------------ authoring

    def segment(self, lines: list, draw, chapter: str = "", **kw) -> Seg:
        """lines: text, or (spoken, shown) pairs -- the narrator reads the first
        ("August seventeenth, twenty eighteen"), the subtitles show the second
        ("Aug 17, 2018")."""
        s = Seg([ln for ln in lines if ln], draw, chapter, **kw)
        self.segs.append(s)
        return s

    def uid(self, prefix: str = "L") -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    def src(self, uri: str) -> str:
        if not uri:
            return ""
        if uri not in self._arts:
            self._arts[uri] = f"a{len(self._arts)}"
        return f'data-edsrc="{self._arts[uri]}"'

    def _vis(self, start: float, end: float) -> str:
        d = self.comp.duration
        pct = lambda t: max(0.0, min(100.0, t / d * 100))   # noqa: E731
        name = self.comp.uid("lvv")
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
        """Inside the camera, from start to end, hard cuts."""
        self._inner.append(f'<div class="scene" style="z-index:{z};{self._vis(start, end)}">{inner}</div>')

    def over(self, start: float, end: float, inner: str, z: int = 40):
        """Over the camera (captions), from start to end."""
        self._over.append(f'<div class="scene" style="z-index:{z};{self._vis(start, end)}">{inner}</div>')

    def cue(self, t: float, kind: str):
        self.comp.cue(t, kind)

    # ------------------------------------------------------------ build

    def build(self, out_dir: Path, wall_arts: list):
        """Voice every line, lay the segments end to end, draw them, add the
        subtitles, chapters, code sticker and end card, and mix the soundtrack.
        Returns (comp, wav path, chapters)."""
        t = 0.0
        for s in self.segs:
            s.voice = V.say([speakable(ln[0] if isinstance(ln, tuple) else ln) for ln in s.lines], out_dir / "voice",
                            self.voice, self.speed)
            s.t0, s.lines_at, cur = t, [], t + s.lead
            for _, secs in s.voice:
                s.lines_at.append((cur, cur + secs))
                cur += secs + s.gap
            s.t1 = max(cur - s.gap + s.tail, s.t0 + s.min_len)
            t = s.t1
        end0 = t
        self.comp = CE.Frame(end0 + END_CARD, W, H, "#0A0A0B")
        self.comp.use_fonts(ED.FONT, "Liberation Sans")
        self.comp.css(ED.CSS + CE.CSS + CSS)
        self.cam = ED.Camera(end0, seed=self.seed, w=W, h=H)
        for i, s in enumerate(self.segs):
            s.draw(self, s)
            if s.cue and i:
                self.cue(max(0, s.t0 - .16), s.cue)
            for (a, b), line in zip(s.lines_at, s.lines):
                shown = line[1] if isinstance(line, tuple) else line
                self.over(a, b + min(s.gap, .25),
                          f'<div class="lv-sub" style="bottom:{H - SUB_BOTTOM}px">{esc(shown)}</div>', z=45)
        from cc_looks import PREP_JS
        css, anim, fanim = self.cam.css()
        self.comp.css(css)
        self.comp.add(PREP_JS)
        self.comp.add(ED.PREP)
        self.comp.add(f'<div class="full" style="transform-origin:0 0;{anim}">{"".join(self._inner)}</div>')
        self.comp.add(f'<div class="ed-flash" style="{fanim}"></div>')
        for o in self._over:
            self.comp.add(o)
        import cc_long as L
        L.end_card(self.comp, end0, wall_arts)
        self.comp.add(code_sticker())
        if self._arts:
            import json
            table = json.dumps({k: u for u, k in self._arts.items()})
            self.comp.add("<script>(() => { const A = " + table + "; for (const i of "
                          "document.querySelectorAll('img[data-edsrc]')) { i.src = A[i.dataset.edsrc]; } })();</script>")
        self.comp.cues.sort()
        chapters = [(s.t0, s.chapter) for s in self.segs if s.chapter]
        wav = mix(self.comp, self.segs, out_dir / "soundtrack.wav", self.seed, self.day)
        return self.comp, wav, chapters


def speakable(text: str) -> str:
    """What the narrator reads: the line without its emojis."""
    return re.sub(r"\s+", " ", EMOJI.sub("", text)).strip()


def code_sticker() -> str:
    """The shorts' USE CODE: BAD sticker, smaller, at the top-left of the safe
    box, on every frame and over the end card."""
    x, y, k = STICKER
    return (f'<div class="abs" data-name="code" style="left:{x}px;top:{y}px;width:0;height:0;z-index:110;'
            f'transform:scale({k});transform-origin:0 0">' + ED.code(0, 6) + '</div>')


# ------------------------------------------------------------------ sound

def _to_sr(x: np.ndarray, sr: int) -> np.ndarray:
    if sr == A.SR:
        return x
    n = int(len(x) * A.SR / sr)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def mix(comp, segs: list, path: Path, seed: int, day=None) -> Path:
    """The narrator on top; real music under it (a new track about every
    minute, at a segment boundary, crossfaded), dipping while he speaks; the
    scene effects; -14 LUFS, peak-limited."""
    import cc_music
    n = int(comp.duration * A.SR)
    voice = np.zeros(n)
    for s in segs:
        for (start, _), (wav, _) in zip(s.lines_at, s.voice):
            x, sr = V.read(wav)
            x = _to_sr(x, sr)
            a = int(start * A.SR)
            b = min(n, a + len(x))
            voice[a:b] += x[:b - a]
    bounds = [0.0]
    for s in segs:
        if s.t0 > 0 and (s.t0 - bounds[-1] >= MUSIC_EVERY or (s.chapter and s.t0 - bounds[-1] >= 20)):
            bounds.append(s.t0)
    bounds.append(comp.duration)
    music = np.zeros((n, 2))
    xf = int(2.0 * A.SR)
    used = []
    for i, (a_s, b_s) in enumerate(zip(bounds, bounds[1:])):
        a, b = int(a_s * A.SR), min(n, int(b_s * A.SR) + xf)
        track = cc_music.pick("drive" if i % 2 else "hype", seed + i * 7919, avoid=tuple(used), day=day)
        if track:
            used.append(track["id"])
            bed = A.track_audio(dict(track, offset=0), (b - a) / A.SR + .1, seed + i)[: b - a]
        else:
            bed = A.music((b - a) / A.SR + .1, seed + i * 7919)[: b - a]
        bed = bed * 10 ** ((-16 - A.loudness(bed)) / 20)
        ramp = np.ones(b - a)
        if i:
            ramp[:xf] = np.linspace(0, 1, xf)
        if b < n:
            ramp[-xf:] = np.minimum(ramp[-xf:], np.linspace(1, 0, xf))
        music[a:b] += bed * ramp[:, None]
    comp.music_used = used
    env = np.convolve(np.abs(voice), np.ones(int(.05 * A.SR)) / int(.05 * A.SR), mode="same")
    active = (env > .01).astype(float)
    k = int(.4 * A.SR)
    active = np.convolve(active, np.ones(k) / k, mode="same")
    gain = 1 - (1 - DUCK) * np.clip(active * 3, 0, 1)
    voice *= 10 ** ((-16 - A.loudness(voice)) / 20) if np.any(voice) else 1
    fx = np.zeros((n, 2))
    rs = np.random.RandomState(seed % (2 ** 32))
    cache = {}
    for t, kind in comp.cues:
        if kind not in cache:
            cache[kind] = A.edit_sfx(kind, rs)
        s0 = int(t * A.SR)
        if s0 >= n:
            continue
        sig = cache[kind] * A.EDIT_GAINS.get(kind, .4) * .6
        e = min(n, s0 + len(sig))
        fx[s0:e] += sig[:e - s0]
    out = music * gain[:, None] + voice[:, None] * 1.0 + fx
    out *= 10 ** ((-14 - A.loudness(out)) / 20)
    # The limiter takes some loudness off the narrator's peaks: measure after it
    # and make up the difference (YouTube plays everything at -14 LUFS at most).
    for _ in range(6):
        final = A.limit(out, .84)
        gap = -14 - A.loudness(final)
        if abs(gap) < .2:
            break
        out *= 10 ** (gap * 1.2 / 20)
    return A.write_wav(final, path)


def check(comp) -> dict:
    """cc_safe's check with the long videos' box (every half second)."""
    import cc_safe as S
    return S.check(comp, step=.5, min_hold=.9, zone=S.LONG, cover_zone=None)
