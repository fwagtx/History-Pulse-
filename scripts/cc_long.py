"""
Long videos for YouTube: 16:9 (1920x1080), narrated, 8-12 minutes.

Same engine as the shorts (cc_motion's seek-and-capture, at 16:9 through
cc_code_entry.Frame), a voice from cc_voice (free, open-source TTS), cc_audio's
music ducked under the voice (a new bed every chapter), and the lime
code-entry card the owner picked at the end.

A long video is a list of segments: narration lines plus a function that draws
them. Segments play end to end; each one lasts as long as its lines take.

    lv = LongVideo(seed=20260927)
    lv.segment(["line", "line"], draw_intro, chapter="Intro")
    comp, wav, chapters = lv.build(out_dir, wall_arts)
    render(comp, out_dir / "video.mp4", wav)

draw(comp, seg) gets seg.t0 / seg.t1 and seg.lines_at -- each line's (start, end)
in seconds -- so a counter can roll on the line that says the number.
"""

import multiprocessing as mp
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import cc_audio as A
import cc_code_entry as CE
import cc_motion as M
import cc_voice as V
from cc_common import log
from cc_motion import ACCENT, INK, an, style_anim

W, H, FPS = 1920, 1080, 30
MARGIN = 96                   # text stays 5% in from every edge (YouTube's player chrome)
END_CARD = 6.2                # the lime code-entry card, as rendered for the owner
DUCK = .16                    # music level under the voice (1 = full)

CSS = """
@keyframes lvwipe{0%{transform:translateX(-120%) skewX(-12deg)}100%{transform:translateX(120%) skewX(-12deg)}}
@keyframes lvin{from{opacity:0;transform:translateY(34px)}to{opacity:1;transform:none}}
@keyframes lvpop{0%{opacity:0;transform:scale(.6)}60%{opacity:1;transform:scale(1.06)}100%{opacity:1;transform:none}}
@keyframes lvgrid{from{background-position:0 0}to{background-position:-240px -120px}}
@keyframes lvzoom{from{transform:scale(1)}to{transform:scale(1.06)}}
@keyframes lvbar{from{transform:scaleX(0)}to{transform:scaleX(1)}}
"""


@dataclass
class Seg:
    lines: list
    draw: object
    chapter: str = ""
    lead: float = .35             # quiet before the first line
    gap: float = .3               # between lines
    tail: float = .55             # after the last line
    min_len: float = 0.0          # visuals that need longer than the voice
    cue: str = "whoosh"           # the sound on the segment's first frame
    t0: float = 0.0
    t1: float = 0.0
    lines_at: list = field(default_factory=list)       # [(start, end)] per line
    voice: list = field(default_factory=list)          # [(wav, seconds)] per line


def badge(start: float = 0) -> str:
    """USE CODE: BAD in the top-left corner, on screen the whole video, with #EpicPartner."""
    return (f'<div class="abs" data-name="code badge" style="left:{MARGIN - 40}px;top:44px;z-index:90">'
            f'<div style="display:flex;align-items:center;gap:12px;background:{ACCENT};color:{INK};'
            f'border-radius:14px;padding:7px 18px 5px 16px;box-shadow:0 7px 0 rgba(0,0,0,.35)">'
            f'<div style="font-size:20px;font-weight:900;line-height:1.02;letter-spacing:.12em">USE<br>CODE:</div>'
            f'<div class="d" style="font-size:66px;line-height:.9;letter-spacing:.02em">BAD</div></div>'
            f'<div style="margin:8px 0 0 4px;font-size:20px;font-weight:700;color:rgba(255,255,255,.9);'
            f'text-shadow:0 2px 6px rgba(0,0,0,.9)">#EpicPartner</div></div>')


def backdrop() -> str:
    """The channel's dark stage: a slow lime grid, a glow, grain and a vignette."""
    grid = ("background-image:linear-gradient(rgba(232,255,58,.06) 2px,transparent 2px),"
            "linear-gradient(90deg,rgba(232,255,58,.06) 2px,transparent 2px);background-size:120px 120px;")
    return (f'<div class="full" style="background:radial-gradient(ellipse 80% 70% at 50% 40%,#1a1c12 0%,{INK} 70%)"></div>'
            f'<div class="full" style="{grid}{style_anim(an("lvgrid", 0, 60, "linear", "infinite"))}"></div>'
            f'<div class="grain"></div><div class="vig"></div>')


def wipe(t: float) -> str:
    """A lime bar sweeping across between segments."""
    return (f'<div class="abs" style="left:0;top:-10%;width:100%;height:120%;z-index:80;pointer-events:none">'
            f'<div class="full" style="background:{ACCENT};transform:translateX(-120%);'
            f'{style_anim(an("lvwipe", t - .22, .44, "cubic-bezier(.7,0,.3,1)", fill="both"))}"></div></div>')


class LongVideo:
    def __init__(self, seed: int, voice: str = V.VOICE, speed: float = V.SPEED):
        self.segs, self.seed, self.voice, self.speed = [], seed, voice, speed

    def segment(self, lines: list, draw, chapter: str = "", **kw) -> Seg:
        s = Seg(list(lines), draw, chapter, **kw)
        self.segs.append(s)
        return s

    def build(self, out_dir: Path, wall_arts: list, code: str = CE.CODE):
        """Voice every line, lay the segments end to end, draw them, add the end
        card, and mix the soundtrack. Returns (comp, wav path, chapters)."""
        t = 0.0
        for s in self.segs:
            s.voice = V.say(s.lines, out_dir / "voice", self.voice, self.speed)
            s.t0, s.lines_at, cur = t, [], t + s.lead
            for _, secs in s.voice:
                s.lines_at.append((cur, cur + secs))
                cur += secs + s.gap
            s.t1 = max(cur - s.gap + s.tail, s.t0 + s.min_len)
            t = s.t1
        end0 = t
        comp = CE.Frame(end0 + END_CARD, W, H, INK)
        comp.use_fonts("Liberation Sans")
        comp.css(CE.CSS + CSS)
        comp.add(backdrop())
        for i, s in enumerate(self.segs):
            s.draw(comp, s)
            if i:
                comp.add(wipe(s.t0))
            if s.cue:
                comp.cue(max(0, s.t0 - .15), s.cue)
        comp.add(badge())
        end_card(comp, end0, wall_arts, code)
        chapters = [(s.t0, s.chapter) for s in self.segs if s.chapter]
        wav = mix(comp, self.segs, out_dir / "soundtrack.wav", self.seed)
        return comp, wav, chapters


def end_card(comp, start: float, arts: list, code: str = CE.CODE):
    """The lime 16:9 code-entry card, exactly as the owner approved it, over a
    blurred wall of the video's cosmetics; it holds to the last frame."""
    t = {"card": start + .12}
    t["keys"] = [round(t["card"] + .8 + i * .24, 3) for i in range(len(code))]
    t["accept"] = t["keys"][-1] + .42
    t["click"] = t["accept"] + 1.1
    t["done"] = t["click"] + .22
    t["pill"] = t["done"] + .22
    t["out"] = t["end"] = comp.duration
    L = CE.LOOKS["lime"]
    inner = (CE.shop_wall(comp, W, H, arts)
             + CE.card(L, code, t, (W - CE.CARD_W) / 2, (H - CE.CARD_H) / 2, 1.0, True, True)
             + CE.confirmation(code, t, W / 2, H / 2, 1.15, True, True))
    comp.scene(start, comp.duration, f'<div class="full">{inner}</div>', fade_in=.25, fade_out=.01, z=85)
    comp.cue(t["card"], "pop")
    for k in t["keys"]:
        comp.cue(k, "tick")
    comp.cue(t["accept"], "pop")
    comp.cue(t["click"], "click")
    comp.cue(t["pill"], "ding")


# ------------------------------------------------------------------ sound

def _to_sr(x: np.ndarray, sr: int) -> np.ndarray:
    if sr == A.SR:
        return x
    n = int(len(x) * A.SR / sr)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def mix(comp, segs: list, path: Path, seed: int) -> Path:
    """Voice on top; music under it, ducked while anyone speaks and changing
    with every chapter; the scene sounds (comp.cues) as in the shorts."""
    n = int(comp.duration * A.SR)
    voice = np.zeros(n)
    for s in segs:
        for (start, _), (wav, _) in zip(s.lines_at, s.voice):
            x, sr = V.read(wav)
            x = _to_sr(x, sr)
            a = int(start * A.SR)
            b = min(n, a + len(x))
            voice[a:b] += x[:b - a]
    # a new music bed per chapter, crossfaded over 1.5 s
    bounds = [s.t0 for s in segs if s.chapter] or [0.0]
    bounds = sorted(set([0.0] + bounds[1:])) + [comp.duration]
    music = np.zeros((n, 2))
    xf = int(1.5 * A.SR)
    for i, (a_s, b_s) in enumerate(zip(bounds, bounds[1:])):
        a, b = int(a_s * A.SR), min(n, int(b_s * A.SR) + xf)
        bed = A.music((b - a) / A.SR + .1, seed + i * 7919)[: b - a]
        bed = bed / (np.max(np.abs(bed)) or 1)
        ramp = np.ones(b - a)
        if i:
            ramp[:xf] = np.linspace(0, 1, xf)
        if b < n:
            ramp[-xf:] = np.minimum(ramp[-xf:], np.linspace(1, 0, xf))
        music[a:b] += bed * ramp[:, None]
    # duck: follow the voice's loudness, with a quick attack and a slow release
    env = np.abs(voice)
    win = int(.05 * A.SR)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    active = (env > .01).astype(float)
    k = int(.35 * A.SR)
    active = np.convolve(active, np.ones(k) / k, mode="same")
    gain = .42 - (.42 - DUCK) * np.clip(active * 3, 0, 1)
    fx = A.mix(comp.duration, comp.cues, seed, music_gain=0)
    fx = fx[:n] if len(fx) >= n else np.pad(fx, ((0, n - len(fx)), (0, 0)))
    out = music * gain[:, None] + voice[:, None] * .92 + fx * .55
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    return A.write_wav(A._norm(out, .89), path)


# ------------------------------------------------------------------ render

def _render_chunk(args):
    doc, w, h, a, b, fps, out, enc = args
    from playwright.sync_api import sync_playwright
    ff = M.find_ffmpeg() or "ffmpeg"
    cmd = [ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", *enc, "-pix_fmt", "yuv420p", "-r", str(fps), str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=M.CHROME_ARGS)
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        page.set_content(doc, wait_until="load")
        page.evaluate(M.READY_JS)
        for i in range(a, b):
            if i == a:
                proc.stdin.write(CE._stable(page, i / fps * 1000, False, False))
            else:
                page.evaluate(M.SEEK_JS, i / fps * 1000)
                proc.stdin.write(page.screenshot(type="jpeg", quality=90))
        browser.close()
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError(f"ffmpeg failed on frames {a}-{b}")
    return str(out)


def render(comp, out: Path, wav: Path, workers: int = 3, fps: int = FPS, enc: tuple = ("-crf", "18")) -> Path:
    """Render in `workers` parallel chunks, join them, add the soundtrack.
    `enc`: the x264 rate options (quality, and a bitrate cap for big videos)."""
    n = int(round(comp.duration * fps))
    doc = comp.document()
    step = -(-n // workers)
    parts = [(doc, comp.w, comp.h, a, min(n, a + step), fps, out.parent / f".{out.stem}.part{k}.mp4", tuple(enc))
             for k, a in enumerate(range(0, n, step))]
    log(f"Rendering {out.name}: {n} frames in {len(parts)} parts")
    with mp.get_context("spawn").Pool(len(parts)) as pool:
        done = pool.map(_render_chunk, parts)
    lst = out.parent / f".{out.stem}.parts.txt"
    lst.write_text("".join(f"file '{Path(p).name}'\n" for p in done))
    ff = M.find_ffmpeg() or "ffmpeg"
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-t", f"{comp.duration:.3f}", "-movflags", "+faststart", str(out)], check=True)
    for p in done:
        Path(p).unlink(missing_ok=True)
    lst.unlink(missing_ok=True)
    return out


def chapters_text(chapters: list) -> str:
    """YouTube chapters for the description: '0:00 Intro' lines (the first must be 0:00)."""
    lines = []
    for i, (t, name) in enumerate(chapters):
        s = 0 if i == 0 else int(t)
        lines.append(f"{s // 60}:{s % 60:02d} {name}")
    return "\n".join(lines)
