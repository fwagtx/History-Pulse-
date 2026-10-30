#!/usr/bin/env python3
"""
The in-game look: every video plays as if you're inside Fortnite -- the Item
Shop screen, a match's HUD (players left, the storm, the Victory Royale) --
with a voice from the first frame, captions that land word by word as it
speaks, and code BAD as the game's own Support-A-Creator code. Asked for by
the owner on 2026-10-30 ("make the content like we are actually in the
fortnite game, make everything fortnite themed"); these are the previews.

  voice    Kokoro-82M (Apache-2.0) through cc_voice, one voice or a blend
           (VOICES). A copy of the model reports how long each sound lasts
           (_timed_model), so every caption word lands when it is spoken.
  type     Barlow Condensed (OFL), black italic caps: the closest free match
           to the game's condensed italic lettering.
  code     the CREATOR CODE: BAD panel in the corner of every frame, said
           once out loud, and the Support-A-Creator card it ends on.

Truth: the same rules as the edits. Prices, sections and leave days are the
shop's own rows; "back after N days" is cc_rarity's (the gap to the day this
listing started); a leave day is the row's out_day, which ends at the next
00:00 UTC rotation (7 PM CDT / 6 PM CST).

  python3 scripts/cc_ingame.py --shop shop.json --out DIR [--voice bella] [--only shop,comebacks]
"""

import argparse
import json
import math
import random
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cc_common import OUT_DIR, log  # noqa: E402
from cc_motion import (ACCENT, EASE_BACK, EASE_OUT, H, W, Comp, an, burst, esc,  # noqa: E402
                       style_anim)

FAMILY = "'Barlow Condensed','Inter',sans-serif"
LIME = ACCENT                  # the code's colour, the channel's own
GOLD = "#FFE34A"               # the game's highlight yellow
NAVY = "#070E33"
INK = "#0A0F2A"

# The voice: a Kokoro voice, or a blend {voice: weight}. The owner picks from
# the voice lab; ItemShopBad speaks with af_heart, so this channel doesn't.
VOICES = {
    "bella": {"af_bella": 1.0},
    "puck": {"am_puck": 1.0},
    "fenrir": {"am_fenrir": 1.0},
    "michael": {"am_michael": 1.0},
    "puck-fenrir": {"am_puck": .6, "am_fenrir": .4},
    "michael-puck": {"am_michael": .5, "am_puck": .5},
    "bella-nicole": {"af_bella": .7, "af_nicole": .3},
    "george": {"bm_george": 1.0},
}
VOICE = "bella"
SPEED = 1.08
VSR = 24000                    # Kokoro's sample rate

# Where things sit (cc_safe): the code panel and the screen's title across the
# top (below Instagram's grid crop, COVER_TOP), the picture between them and
# the captions, the captions above the apps' caption and handle (y 1420).
TOP_Y = 288
VIEW_TOP, VIEW_BOTTOM = 430, 1188
CAP_Y = 1226
CAP_X, CAP_W = 480, 840        # centred in x 60..900 (the button rail is right of 900)

CSS = f"""
.fx{{font-family:{FAMILY};font-weight:900;font-style:italic;text-transform:uppercase;line-height:.86;
  letter-spacing:.004em}}
.fxs{{-webkit-text-stroke:.085em {INK};paint-order:stroke fill;text-shadow:0 .07em 0 rgba(0,0,0,.38)}}
.ui{{font-family:{FAMILY};font-weight:800;text-transform:uppercase;letter-spacing:.06em}}
.ig-code{{position:absolute;z-index:120}}
.ig-code-box{{background:{LIME};color:#0A0A0B;transform:skewX(-9deg);border-radius:8px;padding:8px 26px 6px 20px;
  box-shadow:0 8px 0 rgba(0,0,0,.4),0 0 0 4px rgba(10,10,11,.85)}}
.ig-code-in{{transform:skewX(9deg);display:flex;align-items:center;gap:14px}}
.ig-code-l{{font-family:{FAMILY};font-weight:800;font-size:25px;line-height:1.0;letter-spacing:.1em}}
.ig-code-v{{font-family:{FAMILY};font-weight:900;font-style:italic;font-size:88px;line-height:.84}}
.ig-tag{{margin:10px 0 0 4px;font:700 23px/1.2 'Inter',sans-serif;color:rgba(255,255,255,.92);
  text-shadow:0 2px 6px rgba(0,0,0,.9)}}
.ig-title{{position:absolute;right:{W - 1020}px;top:{TOP_Y}px;text-align:right;z-index:100}}
.ig-chip{{display:inline-block;font-family:{FAMILY};font-weight:800;font-size:28px;letter-spacing:.08em;
  padding:6px 16px 4px;border-radius:6px;transform:skewX(-9deg);box-shadow:0 5px 0 rgba(0,0,0,.35)}}
.ig-tile{{position:absolute;border-radius:14px;overflow:hidden;box-shadow:0 10px 0 rgba(0,0,0,.35)}}
.ig-tile>.bg{{position:absolute;inset:0}}
.ig-tile>.art{{position:absolute;left:50%;bottom:24%;transform:translateX(-50%);display:block;
  filter:drop-shadow(0 14px 18px rgba(0,0,0,.45))}}
.ig-plate{{position:absolute;left:0;right:0;bottom:0;padding:0 14px 12px;
  background:linear-gradient(180deg,transparent 0%,rgba(0,0,0,.55) 38%,rgba(0,0,0,.82) 100%)}}
.ig-name{{font-family:{FAMILY};font-weight:900;font-style:italic;text-transform:uppercase;color:#fff;
  line-height:.9;padding-top:30px}}
.ig-price{{display:flex;align-items:center;gap:8px;font-family:{FAMILY};font-weight:800;color:#fff;margin-top:4px}}
.ig-vb{{display:inline-block;background-size:contain;background-repeat:no-repeat;background-position:center}}
.ig-flag{{position:absolute;left:10px;top:10px;font-family:{FAMILY};font-weight:900;font-style:italic;
  text-transform:uppercase;padding:4px 12px 2px;border-radius:6px;transform:skewX(-9deg);
  box-shadow:0 4px 0 rgba(0,0,0,.35)}}
.ig-focus{{position:absolute;border-radius:18px;border:7px solid #fff;
  box-shadow:0 0 0 5px {GOLD},0 0 44px 10px rgba(255,227,74,.55)}}
.ig-sec{{position:absolute;left:60px;display:flex;align-items:center;gap:18px}}
.ig-cap{{position:absolute;left:{CAP_X - CAP_W / 2:.0f}px;width:{CAP_W}px;top:{CAP_Y}px;text-align:center;z-index:90}}
.ig-cap .w{{display:inline-block;margin:0 .1em;color:#fff}}
.ig-btn{{display:inline-flex;align-items:center;justify-content:center;gap:14px;font-family:{FAMILY};
  font-weight:900;font-style:italic;text-transform:uppercase;border-radius:10px;transform:skewX(-9deg)}}
@keyframes igin{{0%{{transform:scale(1.32) rotate(-3deg);opacity:0}}60%{{transform:scale(.96) rotate(.5deg);opacity:1}}
  100%{{transform:none;opacity:1}}}}
@keyframes ighl{{0%,100%{{color:{LIME}}}}}
@keyframes igfoc{{0%{{transform:scale(1.18);opacity:0}}100%{{transform:scale(1);opacity:1}}}}
@keyframes igpress{{0%,100%{{transform:skewX(-9deg) scale(1)}}40%{{transform:skewX(-9deg) scale(.9)}}}}
@keyframes igdrop{{0%{{transform:translateY(-1500px) rotate(-8deg)}}62%{{transform:translateY(26px) rotate(1.5deg)}}
  80%{{transform:translateY(-10px) rotate(-.6deg)}}100%{{transform:none}}}}
@keyframes igcaret{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@keyframes igstreak{{from{{transform:translateX(0)}}to{{transform:translateX(-460px)}}}}
@keyframes igcloud{{0%{{transform:translate(0,0) scale(1)}}100%{{transform:translate(-120px,40px) scale(1.12)}}}}
@keyframes igshrink{{from{{transform:translate(-50%,-50%) scale(1)}}to{{transform:translate(-50%,-50%) scale(.42)}}}}
@keyframes igflash{{0%{{opacity:.85}}100%{{opacity:0}}}}
@keyframes igtick{{0%{{transform:scale(1.5);color:{GOLD}}}100%{{transform:scale(1);color:#fff}}}}
@keyframes igrays{{to{{transform:translate(-50%,-50%) rotate(360deg)}}}}
"""


# ------------------------------------------------------------------ the voice

def _timed_model() -> Path:
    """kokoro-v1.0.onnx with the duration predictor's frames per sound exposed
    as a second output, "duration" (what kokoro-onnx reads timings from). The
    model is unchanged otherwise: same voice, same speed."""
    import cc_voice as V
    src = V._fetch(V.MODEL)
    dst = src.with_name("kokoro-v1.0-timed.onnx")
    if dst.exists():
        return dst
    try:
        import onnx
    except ModuleNotFoundError:
        import cc_bootstrap
        cc_bootstrap.ensure_pip({"onnx": "onnx"})
        import onnx
    from onnx import TensorProto, helper
    m = onnx.load(str(src))
    # Round -> Clip(min 1) -> Cast(int64) -> Gather: the frames per token that
    # the decoder repeats each token for (Kokoro's pred_dur).
    m.graph.node.append(helper.make_node("Identity", ["/encoder/Gather_output_0"], ["duration"],
                                         name="duration_out"))
    m.graph.output.append(helper.make_tensor_value_info("duration", TensorProto.INT64, ["tokens"]))
    tmp = dst.with_suffix(".tmp")
    onnx.save(m, str(tmp))
    tmp.replace(dst)
    return dst


_engine = None


def engine():
    global _engine
    if _engine is None:
        import cc_voice as V
        from kokoro_onnx import Kokoro
        _engine = Kokoro(str(_timed_model()), str(V._fetch(V.VOICES)))
    return _engine


def _style(voice: str):
    mix = VOICES.get(voice, {voice: 1.0})
    k = engine()
    if len(mix) == 1:
        return next(iter(mix))
    return sum(w * k.get_voice_style(v) for v, w in mix.items()).astype(np.float32)


MARK = re.compile(r"\{([^{}|]*)\|([^{}]*)\}")


def _parse(text: str) -> tuple:
    """'Back after {745|seven hundred and forty-five} days' -> the words to say,
    and the caption words with how many spoken words each one covers."""
    spoken, shown = [], []
    pos = 0
    for m in list(MARK.finditer(text)) + [None]:
        plain = text[pos:m.start()] if m else text[pos:]
        for w in plain.split():
            spoken.append(w)
            shown.append((w, 1))
        if m:
            said = m.group(2).split()
            spoken += said
            shown.append((m.group(1), len(said)))
            pos = m.end()
    # Punctuation standing alone ("{...}!") belongs to the word before it.
    for i in range(len(spoken) - 1, 0, -1):
        if re.fullmatch(r"[^\w']+", spoken[i]):
            spoken[i - 1] += spoken.pop(i)
    for i in range(len(shown) - 1, 0, -1):
        if re.fullmatch(r"[^\w']+", shown[i][0]):
            w, n = shown.pop(i)
            shown[i - 1] = (shown[i - 1][0] + w, shown[i - 1][1])
    return " ".join(spoken), shown


def _plen(ph: str) -> int:
    """How many sounds a phoneme string has (stress and length marks aside)."""
    return len(re.sub(r"[\W_ˈˌːˑ]", "", ph))


def _align(wl: list, gl: list) -> list:
    """Which sound groups each said word covers, [(first, last)]. The
    phonemizer sometimes runs two words together ("in the" -> one group) or
    splits one; the alignment that best matches their lengths wins."""
    n, m = len(wl), len(gl)
    INF = float("inf")
    best = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if best[i][j] == INF:
                continue
            for a in (1, 2, 3):                 # a words share one group
                if i + a <= n and j + 1 <= m:
                    c = best[i][j] + abs(sum(wl[i:i + a]) - gl[j]) + (a - 1) * .5
                    if c < best[i + a][j + 1]:
                        best[i + a][j + 1], back[i + a][j + 1] = c, (i, j)
            for b in (2, 3):                    # one word spread over b groups
                if i + 1 <= n and j + b <= m:
                    c = best[i][j] + abs(wl[i] - sum(gl[j:j + b])) + (b - 1) * .5
                    if c < best[i + 1][j + b]:
                        best[i + 1][j + b], back[i + 1][j + b] = c, (i, j)
    if best[n][m] == INF:
        return []
    steps, i, j = [], n, m
    while (i, j) != (0, 0):
        pi, pj = back[i][j]
        steps.append((pi, i, pj, j))
        i, j = pi, pj
    out = [None] * n
    for wi0, wi1, g0, g1 in reversed(steps):
        if wi1 - wi0 == 1:
            out[wi0] = (g0, g1 - 1, 0.0, 1.0)
        else:                                   # words sharing a group split it by length
            tot = sum(wl[wi0:wi1]) or 1
            acc = 0
            for k in range(wi0, wi1):
                out[k] = (g0, g0, acc / tot, (acc + wl[k]) / tot)
                acc += wl[k]
    return out


class Line:
    """One spoken line: its audio (Kokoro's rate), its length, and each caption
    word's (word, start, end) from the line's start."""

    def __init__(self, text: str, voice: str = VOICE, speed: float = SPEED):
        self.text = text
        said, shown = _parse(text)
        first = next(iter(VOICES.get(voice, {voice: 1.0})))
        lang = "en-gb" if first.startswith("b") else "en-us"
        audio, sr, timings = engine().create_timed(said, voice=_style(voice), speed=speed, lang=lang)
        assert sr == VSR
        self.audio = audio.astype(np.float32)
        self.dur = len(self.audio) / VSR
        groups, cur = [], []
        for t in timings:
            if t.phoneme.strip() == "":           # a space: the next word starts
                if cur:
                    groups.append(cur)
                cur = []
            elif not re.fullmatch(r"[\W_]+", t.phoneme):   # punctuation makes no sound of its own
                cur.append(t)
        if cur:
            groups.append(cur)
        n_said = len(said.split())
        al = []
        if groups and len(groups) != n_said:
            tok = engine().tokenizer
            al = _align([_plen(tok.phonemize(w, lang)) for w in said.split()],
                        [_plen("".join(t.phoneme for t in g)) for g in groups])
        if len(groups) == n_said:
            spans = [(g[0].start, g[-1].end) for g in groups]
        elif al:
            spans = []
            for g0, g1, f0, f1 in al:
                a, b = groups[g0][0].start, groups[g1][-1].end
                spans.append((a + (b - a) * f0, a + (b - a) * f1) if g0 == g1 and (f0, f1) != (0.0, 1.0)
                             else (a, b))
        else:                                      # nothing lines up: share the line by length
            lens = [max(1, len(re.sub(r"\W", "", w))) for w in said.split()]
            t0, t1 = (timings[0].start, timings[-1].end) if timings else (0.0, self.dur)
            tot, acc, spans = sum(lens), 0, []
            for n in lens:
                a = t0 + (t1 - t0) * acc / tot
                acc += n
                spans.append((a, t0 + (t1 - t0) * acc / tot))
            log(f"  captions: {len(groups)} sound groups for {n_said} words in {said!r}; timed by length")
        self.words, k = [], 0
        for w, n in shown:
            self.words.append((w, spans[k][0], spans[k + n - 1][1]))
            k += n
        self.start = 0.0                           # set when placed on the timeline

    def at(self, words: str) -> float:
        """When these caption words (a name, a number; case and punctuation
        ignored) start being said, on the video's clock. A caption word that
        only starts with the last one counts ("745 days" for "745")."""
        norm = lambda s: re.sub(r"[^\w]", "", s.lower())   # noqa: E731
        want = [norm(w) for w in words.split()]
        have = [norm(w) for w, _, _ in self.words]
        for i in range(len(have) - len(want) + 1):
            if have[i:i + len(want) - 1] == want[:-1] and have[i + len(want) - 1].startswith(want[-1]):
                return self.start + self.words[i][1]
        log(f"  {words!r} isn't in {self.text!r}; timed to the line's start")
        return self.start

    @property
    def end(self) -> float:
        return self.start + self.dur


class Script:
    """Lines placed one after another on the video's clock."""

    def __init__(self, voice: str = VOICE, speed: float = SPEED, lead: float = .08):
        self.voice, self.speed = voice, speed
        self.lines, self.t = [], lead

    def say(self, text: str, gap: float = .14, speed: float | None = None) -> Line:
        ln = Line(text, self.voice, speed or self.speed)
        ln.start = self.t
        self.lines.append(ln)
        self.t = ln.end + gap
        return ln

    def pause(self, s: float):
        self.t += s

    def track(self, duration: float) -> np.ndarray:
        """The voice on the video's clock, mono at Kokoro's rate."""
        out = np.zeros(int(duration * VSR) + 1, dtype=np.float32)
        for ln in self.lines:
            a = int(ln.start * VSR)
            seg = ln.audio[:max(0, len(out) - a)]
            out[a:a + len(seg)] += seg
        return out


# ------------------------------------------------------------------ captions

def captions(comp: Comp, script: Script, size: int = 104, per_page: int = 3, max_chars: int = 16):
    """Word-by-word captions: a page of up to `per_page` words; each word pops
    in as it's said and is lime while it's said, white after."""
    words = []
    for ln in script.lines:
        for i, (w, s, e) in enumerate(ln.words):
            words.append((w, ln.start + s, ln.start + e, i == len(ln.words) - 1))
    pages, cur = [], []
    for w in words:
        chars = sum(len(x[0]) + 1 for x in cur) + len(w[0])
        if cur and (len(cur) >= per_page or chars > max_chars):
            pages.append(cur)
            cur = []
        cur.append(w)
        if w[3] or re.search(r"[.!?…]$", w[0]):
            pages.append(cur)
            cur = []
    if cur:
        pages.append(cur)
    for i, pg in enumerate(pages):
        start = pg[0][1]
        nxt = pages[i + 1][0][1] if i + 1 < len(pages) else comp.duration
        end = min(nxt, pg[-1][2] + .7)
        spans = []
        for w, s, e, _ in pg:
            a = style_anim(an("igin", s, .2, EASE_OUT), an("ighl", s, max(.05, e - s), "linear", fill="none"))
            spans.append(f'<span class="w" style="{a}">{esc(w.upper())}</span>')
        comp.scene(start, end + .001, f'<div class="ig-cap fx fxs" style="font-size:{size}px">{"".join(spans)}</div>',
                   fade_in=.01, fade_out=.06, z=90)


# ------------------------------------------------------------------ the screens

def to_end(comp: Comp, start: float, inner: str, z: int, fade: float = .12):
    """A screen from `start` to the last frame, fading in. (Comp.scene ends a
    scene with a fade, which a scene that reaches the last frame would spread
    over its whole length.)"""
    d = comp.duration
    name = comp.uid("igend")
    a, b = min(100.0, start / d * 100), min(100.0, (start + fade) / d * 100)
    comp.css(f"@keyframes {name}{{0%{{opacity:0}}{a:.4f}%{{opacity:0}}{b:.4f}%{{opacity:1}}100%{{opacity:1}}}}")
    comp.add(f'<div class="scene" style="z-index:{z};animation:{name} {d:.3f}s linear 0s 1 normal both">{inner}</div>')


def lobby_bg(start: float = 0) -> str:
    """The lobby's blue: a sky-lit gradient, slow light streaks, grain."""
    streaks = (f'<div class="abs" style="left:0;top:0;width:{W + 460}px;height:{H}px;opacity:.55;'
               f'background:repeating-linear-gradient(112deg,rgba(255,255,255,.06) 0 3px,transparent 3px 46px);'
               f'{style_anim(an("igstreak", start, 9, "linear", "infinite"))}"></div>')
    return (f'<div class="full" style="background:radial-gradient(ellipse 130% 72% at 50% 4%,#4FB0FF 0%,'
            f'#1F62E0 34%,#0E2A8C 66%,#060C3D 100%)"></div>{streaks}<div class="grain"></div><div class="vig"></div>')


def storm_bg(start: float, shrink_end: float) -> str:
    """The storm: purple cloud banks drifting, and the safe circle's white edge
    closing in until `shrink_end`."""
    clouds = []
    rnd = random.Random(7)
    for i in range(7):
        x, y, r = rnd.uniform(-200, W), rnd.uniform(-200, H), rnd.uniform(420, 820)
        col = rnd.choice(["rgba(170,90,255,.42)", "rgba(110,40,220,.5)", "rgba(220,140,255,.28)"])
        clouds.append(f'<div class="abs" style="left:{x:.0f}px;top:{y:.0f}px;width:{r:.0f}px;height:{r:.0f}px;'
                      f'border-radius:50%;background:radial-gradient(closest-side,{col},transparent);'
                      f'{style_anim(an("igcloud", start - i, 7 + i, "ease-in-out", "infinite", "alternate"))}"></div>')
    ring = (f'<div class="abs" style="left:50%;top:46%;width:1500px;height:1500px;border-radius:50%;'
            f'box-shadow:0 0 0 2000px rgba(120,40,230,.30),inset 0 0 60px rgba(255,255,255,.35);'
            f'border:6px solid rgba(255,255,255,.75);'
            f'{style_anim(an("igshrink", start, max(1, shrink_end - start), "linear"))}"></div>')
    return (f'<div class="full" style="background:radial-gradient(ellipse 120% 80% at 50% 40%,#5E2BD6 0%,'
            f'#35118E 45%,#170548 75%,#08021F 100%)"></div>{"".join(clouds)}{ring}'
            f'<div class="grain"></div><div class="vig"></div>')


def code_panel() -> str:
    """CREATOR CODE: BAD, in every frame, with the #EpicPartner disclosure."""
    return (f'<div class="ig-code" data-safe="key" data-name="code" style="left:60px;top:{TOP_Y}px">'
            f'<div class="ig-code-box"><div class="ig-code-in"><div class="ig-code-l">CREATOR<br>CODE</div>'
            f'<div class="ig-code-v">BAD</div></div></div><div class="ig-tag">#EpicPartner</div></div>')


def title(text: str, chip: str = "", chip_bg: str = GOLD, chip_fg: str = NAVY) -> str:
    c = (f'<div style="margin-top:8px"><span class="ig-chip" style="background:{chip_bg};color:{chip_fg}">'
         f'{esc(chip)}</span></div>') if chip else ""
    return (f'<div class="ig-title" data-safe="key" data-name="title"><div class="fx fxs" style="font-size:66px;color:#fff">'
            f'{esc(text)}</div>{c}</div>')


def vbuck(px: int, uri: str) -> str:
    return (f'<span class="ig-vb" style="width:{px}px;height:{px}px;background-image:url({uri})"></span>'
            if uri else '<span style="font-weight:900">V</span>')


def _hex(c: str, fb: str) -> str:
    c = (c or "").strip()
    if not c.startswith("#"):
        c = "#" + c
    return c[:7] if re.fullmatch(r"#[0-9a-fA-F]{6}", c[:7]) else fb


def _lum(c: str) -> float:
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return .2126 * r + .7152 * g + .0722 * b


def _shade(c: str, k: float) -> str:
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


RARITY_BG = {"common": "#8A8F98", "uncommon": "#3E9C35", "rare": "#2E7CE0", "epic": "#9A3DD6",
             "legendary": "#D9792A", "mythic": "#D4AF1F", "icon": "#2BA9B8", "marvel": "#C2272D",
             "dc": "#3550B8", "starwars": "#B8960A", "gaminglegends": "#6B2FD6", "dark": "#A12FC4"}


def tile_bg(row: dict) -> str:
    """The tile's own in-game colours (the shop row's), lit from the top."""
    cols = [_hex(c, "") for c in (row.get("tile_colors") or [])]
    cols = [c for c in cols if c]
    if len(cols) >= 2:
        a, b = sorted(cols[:2], key=_lum, reverse=True)
    else:
        a = RARITY_BG.get(str(row.get("rarity") or "rare").lower(), "#2E7CE0")
        b = _shade(a, .45)
    return (f"radial-gradient(ellipse 95% 75% at 50% 30%,{a} 0%,{b} 72%,{_shade(b, .55)} 100%)")


def tile(row: dict, art: str, x: float, y: float, w: float, h: float, vb: str,
         flag: str = "", flag_bg: str = GOLD, flag_fg: str = NAVY, extra: str = "") -> str:
    """A shop tile as the game draws it: the item on its colours, its name and
    price on a dark plate, a flag in the corner."""
    t = str(row.get("type") or "").lower()
    trim = ' data-trim="figure"' if t == "outfit" else " data-trim"
    pic = (f'<img class="art"{trim} data-name="{esc(row.get("name", ""))}" src="{art}" '
           f'style="height:{h * .74:.0f}px;max-width:{w * .94:.0f}px">') if art else ""
    name_px = round(min(96, w * .167) if len(row.get("name", "")) <= 14 else min(80, w * .136))
    price = row.get("price")
    p = (f'<div class="ig-price" style="font-size:{h * .085:.0f}px">{vbuck(int(h * .085), vb)}'
         f'{int(price):,}</div>') if price else ""
    fl = (f'<div class="ig-flag" style="font-size:{h * .075:.0f}px;background:{flag_bg};color:{flag_fg}">'
          f'{esc(flag)}</div>') if flag else ""
    return (f'<div class="ig-tile" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px;{extra}">'
            f'<div class="bg" style="background:{tile_bg(row)}"></div>{pic}'
            f'<div class="ig-plate"><div class="ig-name" style="font-size:{name_px}px">{esc(row.get("name", ""))}</div>'
            f'{p}</div>{fl}</div>')


def focus(x: float, y: float, w: float, h: float, start: float, end: float, comp: Comp) -> str:
    """The controller's focus frame on a tile while the voice is on it."""
    name = comp.uid("igf")
    d = comp.duration
    pct = lambda t: max(0.0, min(100.0, t / d * 100))   # noqa: E731
    comp.css(f"@keyframes {name}{{0%{{opacity:0}}{pct(start):.4f}%{{opacity:0}}{pct(start + .01):.4f}%{{opacity:1}}"
             f"{pct(end):.4f}%{{opacity:1}}{pct(end + .01):.4f}%{{opacity:0}}100%{{opacity:0}}}}")
    return (f'<div class="abs" style="left:{x - 9:.0f}px;top:{y - 9:.0f}px;width:{w + 18:.0f}px;height:{h + 18:.0f}px;'
            f'z-index:5;animation:{name} {d:.3f}s step-end 0s 1 normal both">'
            f'<div class="ig-focus" style="inset:0;{style_anim(an("igfoc", start, .22, EASE_BACK))}"></div></div>')


def person_icon(px: int, color: str = "#fff") -> str:
    return (f'<svg width="{px}" height="{px}" viewBox="0 0 24 24" aria-hidden="true">'
            f'<circle cx="12" cy="7" r="4.2" fill="{color}"/>'
            f'<path d="M3.5 22c.6-5.2 4-8.2 8.5-8.2s7.9 3 8.5 8.2z" fill="{color}"/></svg>')


def support_card(start: float, comp: Comp, cx: float = 480, top: float = 560) -> str:
    """The game's SUPPORT A CREATOR box: BAD typed in, ACCEPT pressed, and the
    SUPPORTING: BAD confirmation."""
    w = 800
    letters = "".join(
        f'<span style="{style_anim(an("fadein", start + .45 + i * .16, .01, "linear"))}">{c}</span>'
        for i, c in enumerate("BAD"))
    for i in range(3):
        comp.cue(start + .45 + i * .16, "tick")
    press = start + 1.25
    comp.cue(press, "click")
    comp.cue(press + .3, "ding")
    caret = (f'<span style="display:inline-block;width:6px;height:.8em;background:{NAVY};margin-left:6px;'
             f'vertical-align:-.05em;{style_anim(an("igcaret", start, .5, "steps(1)", "infinite"))}"></span>')
    ok = (f'<div class="abs" style="left:0;right:0;top:100%;margin-top:26px;text-align:center;'
          f'{style_anim(an("igin", press + .25, .35, EASE_BACK))}">'
          f'<span class="ig-chip fx" style="font-size:52px;background:{LIME};color:#0A0A0B;padding:10px 26px 6px">'
          f'&#10003; SUPPORTING: BAD</span></div>')
    return (f'<div class="abs" style="left:{cx - w / 2:.0f}px;top:{top:.0f}px;width:{w}px;'
            f'{style_anim(an("igin", start, .35, EASE_BACK))}">'
            f'<div style="background:{NAVY};border-radius:16px 16px 0 0;padding:20px 30px 14px">'
            f'<div class="fx" style="font-size:62px;color:#fff">SUPPORT A CREATOR</div></div>'
            f'<div style="background:#E9EEF8;border-radius:0 0 16px 16px;padding:28px 30px 30px;'
            f'box-shadow:0 14px 0 rgba(0,0,0,.35)">'
            f'<div class="ui" style="font-size:26px;color:#3A4466;margin-bottom:10px">ENTER CREATOR CODE</div>'
            f'<div style="background:#fff;border:4px solid {NAVY};border-radius:10px;padding:14px 22px 8px">'
            f'<span class="fx" style="font-size:96px;color:{NAVY}">{letters}</span>{caret}</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:22px">'
            f'<div class="ui" style="font-size:24px;color:#3A4466">#EpicPartner</div>'
            f'<div class="ig-btn" style="font-size:54px;padding:10px 40px 6px;background:{GOLD};color:{NAVY};'
            f'box-shadow:0 7px 0 rgba(0,0,0,.35);{style_anim(an("igpress", press, .25))}">ACCEPT</div></div>'
            f'</div>{ok}</div>')


def end_card(start: float) -> str:
    """The last screen: the code, big, and where it goes."""
    a = lambda d: style_anim(an("igin", start + d, .32, EASE_BACK))   # noqa: E731
    return (f'{lobby_bg(start)}'
            f'<div class="abs" style="left:60px;width:840px;top:540px;text-align:center">'
            f'<div class="fx fxs" style="font-size:118px;color:#fff;{a(0)}">USE CODE</div>'
            f'<div class="fx fxs" style="font-size:330px;color:{LIME};margin-top:-6px;{a(.12)}">BAD</div>'
            f'<div style="margin-top:22px;{a(.3)}"><span class="ig-chip" style="font-size:40px;background:{GOLD};'
            f'color:{NAVY};padding:10px 22px 6px">ITEM SHOP &#8594; SUPPORT A CREATOR</span></div></div>')


# ------------------------------------------------------------------ data

def _art(row: dict) -> str:
    from cc_images import candidates, fetch_first
    return fetch_first(candidates(row))


def _vbuck_uri() -> str:
    from cc_images import data_uri, fetch
    return data_uri(fetch("https://fortnite-api.com/images/vbuck.png"))


def _num_words(n: int) -> str:
    """745 -> 'seven hundred and forty-five' (what the voice says)."""
    ones = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen " \
           "sixteen seventeen eighteen nineteen".split()
    tens = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()

    def two(k):
        return ones[k] if k < 20 else tens[k // 10] + ("-" + ones[k % 10] if k % 10 else "")

    def three(k):
        h, r = divmod(k, 100)
        if not h:
            return two(r)
        return ones[h] + " hundred" + (" and " + two(r) if r else "")
    if n < 1000:
        return three(n)
    th, r = divmod(n, 1000)
    return three(th) + " thousand" + ((" and " if r < 100 else " ") + three(r) if r else "")


def say_num(n: int, suffix: str = "") -> str:
    """Caption markup: the caption shows '745 days' while the voice says
    'seven hundred and forty-five days'."""
    return "{" + f"{n:,}{suffix}" + "|" + _num_words(n) + suffix + "}"


def kind_label(row: dict) -> str:
    t = str(row.get("type") or "item")
    r = str(row.get("rarity_label") or row.get("rarity") or "")
    return f"{r} {t}".strip().upper()


# ------------------------------------------------------------------ video 1: today's shop

def shop_today(shop: dict, hist, day: date, voice: str = VOICE):
    """Today's Item Shop, browsed like in the game: what leaves tonight, the
    big sections, the longest comeback, then the code."""
    import cc_rarity as R
    rows = [r for r in shop["items"] if not r.get("is_bundle")]
    by_sec = {}
    for r in rows:
        by_sec.setdefault(r.get("section") or "", []).append(r)
    outfit = lambda r: str(r.get("type") or "").lower() == "outfit"   # noqa: E731
    leaving = sorted([r for r in rows if r.get("out_day") == day.isoformat() and outfit(r)],
                     key=lambda r: -(r.get("price") or 0))
    back = R.back_in_shop(hist, shop, day, min_days=180)
    if not leaving or not back:
        return None
    star = leaving[0]
    secs = [s for s, rs in sorted(by_sec.items(), key=lambda kv: -len(kv[1]))
            if s and sum(outfit(r) for r in rs) >= 2 and s != star.get("section")][:2]
    if len(secs) < 2:
        return None
    picks = {s: sorted([r for r in by_sec[s] if outfit(r)], key=lambda r: (r.get("in_day") != day.isoformat(),
                                                                          -(r.get("price") or 0)))[:3]
             for s in secs}
    brow, bid, gone, last, times = back[0]

    sc = Script(voice)
    l1 = sc.say(f"{star['name']} leaves the Item Shop tonight...", gap=.1)
    l2 = sc.say("so here's what else is in today's shop.", gap=.2)
    a, b = secs
    pa, pb = picks[a], picks[b]
    l3 = sc.say(f"{a} is still here, with {pa[0]['name']} and {pa[1]['name']}.", gap=.2)
    new_b = [r for r in pb if r.get("in_day") == day.isoformat()]
    if len(new_b) >= 2:
        l4 = sc.say(f"{b} just dropped {new_b[0]['name']} and {new_b[1]['name']}.", gap=.2)
        pb = new_b + [r for r in pb if r not in new_b]
    else:
        l4 = sc.say(f"And {b} has {pb[0]['name']} and {pb[1]['name']}.", gap=.2)
    l5 = sc.say(f"Plus, {brow['name']} is back... after {say_num(gone, ' days')}!", gap=.3)
    l6 = sc.say("If you're grabbing anything, use code BAD.", gap=1.5)   # the code gets typed in
    l7 = sc.say("See you in the lobby!", gap=.1)
    dur = round(l7.end + .9, 2)

    comp = Comp(dur)
    comp.use_fonts("Barlow Condensed")
    comp.css(CSS)
    vb = _vbuck_uri()
    art = {r["name"]: _art(r) for r in [star, brow] + pa[:2] + pb[:2] + leaving[1:3]}

    # The shop page: sections of three tiles, scrolled to whatever the voice is on.
    tw, th, gap = 264, 352, 24
    page, y, spots = [], 0, {}

    def section(name: str, chip: str, chip_bg: str, items: list, flags: dict):
        nonlocal y
        page.append(f'<div class="ig-sec" style="top:{y:.0f}px"><div class="fx fxs" style="font-size:56px;color:#fff">'
                    f'{esc(name)}</div><span class="ig-chip" style="background:{chip_bg};color:#fff">{esc(chip)}</span></div>')
        y += 84
        for i, r in enumerate(items[:3]):
            x = 60 + i * (tw + gap)
            fl, fbg = flags.get(r["name"], ("", GOLD))
            page.append(tile(r, art.get(r["name"]) or _art(r), x, y, tw, th, vb, fl, fbg,
                             "#fff" if fbg != GOLD else NAVY))
            spots[r["name"]] = (x, y)
        top = y - 84
        y += th + 56
        return top

    leave_row = [star] + [r for r in leaving[1:3]]
    s0 = section("LEAVING TONIGHT", "ENDS AT RESET", "#E23B3B", leave_row, {star["name"]: ("LAST DAY", "#E23B3B")})
    s1 = section(a, "LIMITED", "#2B4DB8", pa, {})
    s2 = section(b, "NEW TODAY" if len(new_b) >= 2 else "LIMITED", "#2B4DB8", pb,
                 {r["name"]: ("NEW!", GOLD) for r in new_b})
    page.append(f'<div class="ig-sec" style="top:{y:.0f}px"><div class="fx fxs" style="font-size:56px;color:#fff">'
                f'BACK IN THE SHOP</div><span class="ig-chip" style="background:#7A2BD6;color:#fff">'
                f'{gone:,} DAYS</span></div>')
    s3 = y
    y += 84
    big_w, big_h = 840, 560
    page.append(tile(brow, art.get(brow["name"]) or _art(brow), 60, y, big_w, big_h, vb, "BACK!", GOLD, NAVY))
    spots[brow["name"]] = (60, y)
    y += big_h + 56

    # Scroll: the section the voice is on sits at the top of the view, moving
    # there in .45 s as its line starts.
    d = dur
    pct = lambda t: min(100.0, max(0.0, t / d * 100))   # noqa: E731
    kf, prev = [f"0%{{transform:translateY({-s0}px)}}"], -s0
    for t, top in ((l3.start, s1), (l4.start, s2), (l5.start, s3)):
        kf.append(f"{pct(t - .05):.4f}%{{transform:translateY({prev}px);"
                  f"animation-timing-function:cubic-bezier(.6,0,.2,1)}}")
        kf.append(f"{pct(t + .4):.4f}%{{transform:translateY({-top}px)}}")
        prev = -top
        comp.cue(t - .05, "swoosh")
    kf.append(f"100%{{transform:translateY({prev}px)}}")
    comp.css("@keyframes igscroll{" + "".join(kf) + "}")
    shop_end = l6.start
    foc = []
    for ln, items, nxt in ((l1, [star], l2.end), (l3, pa[:2], l4.start), (l4, pb[:2], l5.start),
                           (l5, [brow], shop_end)):
        for i, r in enumerate(items):
            t = ln.at(r["name"])
            end = ln.at(items[i + 1]["name"]) if i + 1 < len(items) else nxt
            x, yy = spots[r["name"]]
            fw, fh = (big_w, big_h) if r is brow else (tw, th)
            foc.append(focus(x, yy, fw, fh, t, end - .02, comp))
            comp.cue(t, "pop2")
    view = (f'<div class="abs" style="left:0;right:0;top:{VIEW_TOP}px;height:{VIEW_BOTTOM - VIEW_TOP}px;overflow:hidden;'
            f'-webkit-mask-image:linear-gradient(180deg,#000 0,#000 88%,transparent 100%)">'
            f'<div class="abs" style="left:0;right:0;top:0;height:{y:.0f}px;animation:igscroll {d:.3f}s linear 0s 1 normal both">'
            f'{"".join(page)}{"".join(foc)}</div></div>')
    comp.scene(0, shop_end + .25, lobby_bg() + view, fade_in=0, fade_out=.2)
    comp.cue(.02, "swoosh")

    # The purchase: the star on its own screen, PURCHASE pressed, then the code.
    p0 = l6.start - .05
    sart = art.get(star["name"])
    trim = ' data-trim="figure"' if outfit(star) else " data-trim"
    fig = (f'<img{trim} src="{sart}" style="max-height:700px;max-width:520px;'
           f'filter:drop-shadow(0 20px 30px rgba(0,0,0,.5))">') if sart else ""
    buy = (f'<div class="full" style="background:{tile_bg(star)}"></div><div class="grain"></div><div class="vig"></div>'
           f'<div class="abs" style="left:40px;top:470px;width:520px;height:720px;display:flex;align-items:flex-end;'
           f'justify-content:center">{fig}</div>'
           f'<div class="abs" style="left:540px;top:520px;width:360px">'
           f'<div class="fx fxs" style="font-size:{86 if len(star["name"]) <= 12 else 64}px;color:#fff">{esc(star["name"])}</div>'
           f'<div class="ui" style="font-size:28px;color:{GOLD};margin-top:12px">{esc(kind_label(star))}</div>'
           f'<div class="ig-price fx" style="font-size:72px;margin-top:18px">{vbuck(64, vb)}{int(star.get("price") or 0):,}</div>'
           f'<div class="ig-btn" style="margin-top:30px;font-size:62px;padding:14px 34px 8px;background:{GOLD};color:{NAVY};'
           f'box-shadow:0 8px 0 rgba(0,0,0,.35);{style_anim(an("igpress", l6.at("anything"), .25))}">PURCHASE</div></div>')
    comp.cue(l6.at("anything"), "click")
    comp.cue(l6.at("anything") + .12, "cash")
    card_t = l6.at("BAD") - .5                       # B is typed as the voice says it
    comp.scene(p0, card_t + .15, buy, fade_in=.12, fade_out=.12, z=2)
    comp.scene(card_t, l7.start + .05, lobby_bg(card_t) + support_card(card_t, comp, top=560), fade_in=.1, fade_out=.1, z=3)
    to_end(comp, l7.start, end_card(l7.start), z=4)
    comp.cue(l7.start, "boom")

    comp.add(code_panel())
    comp.add(title("ITEM SHOP", f"{day.strftime('%a').upper()} · {day.strftime('%b').upper()} {day.day}"))
    captions(comp, sc)
    return comp, sc, f"Today's Item Shop ({day:%b %-d})"


# ------------------------------------------------------------------ video 2: players left

def comebacks(shop: dict, hist, day: date, voice: str = VOICE, n: int = 5):
    """Today's five longest comebacks as a match: PLAYERS LEFT counts down as
    each one lands, and #1 gets the Victory Royale."""
    import cc_rarity as R
    back = [b for b in R.back_in_shop(hist, shop, day, min_days=200)
            if str(b[0].get("type") or "").lower() not in ("wrap", "shoes", "jam track", "music")]
    if len(back) < n:
        return None
    top = back[:n][::-1]                                   # #5 first
    least = top[0][2]
    away = ("after more than a year away." if least >= 366 else
            "after almost a year, or way longer." if least >= 330 else
            f"after {say_num(least, ' days')} or more.")
    sc = Script(voice)
    sc.say("These items are back in the Item Shop...", gap=.06)
    sc.say(away, gap=.3)
    lines = []
    for i, (row, iid, gone, last, times) in enumerate(top):
        rank = n - i
        if rank == 1:
            sc.pause(.2)
            ln = sc.say(f"And number one... {row['name']}! {say_num(gone, ' days')}!", gap=.5)
        else:
            ln = sc.say(f"{{#{rank}|Number {_num_words(rank)}}}: {row['name']}. {say_num(gone, ' days')}.", gap=.22)
        lines.append((rank, row, gone, ln))
    lc = sc.say("Which one are you grabbing? Use code BAD!", gap=.1)
    dur = round(lc.end + 1.5, 2)

    comp = Comp(dur)
    comp.use_fonts("Barlow Condensed")
    comp.css(CSS)
    vb = _vbuck_uri()
    arts = {row["name"]: _art(row) for _, row, _, _ in lines}
    comp.add(f'<div class="full">{storm_bg(0, dur)}</div>')

    # The hook: all five drop in, the way a squad lands.
    first = lines[0][3].start
    tw, th = 248, 330
    spots = [(60, 450), (356, 450), (652, 450), (208, 808), (504, 808)]
    hook = []
    for i, (rank, row, gone, ln) in enumerate(lines[::-1]):
        x, yy = spots[i]
        t = .1 + i * .12
        hook.append(tile(row, arts[row["name"]], x, yy, tw, th, vb, "BACK!", GOLD, NAVY,
                         extra=f"transform-origin:50% 60%;{style_anim(an('thump', t, .35))}"))
        comp.cue(t, "pop2")
    comp.scene(0, first, "".join(hook), fade_in=0, fade_out=.15, z=2)

    for k, (rank, row, gone, ln) in enumerate(lines):
        end = lines[k + 1][3].start if k + 1 < len(lines) else lc.start
        t0, num_t = ln.start, ln.at(f"{gone:,}")
        comp.cue(t0, "whoosh")
        comp.cue(t0 + .34, "impact")
        comp.cue(num_t, "ding")
        if rank == 1:
            vt = ln.at(row["name"])
            comp.cue(vt - .9, "riser")
            comp.cue(vt, "boom")
            body = winner(row, arts[row["name"]], gone, t0, vt, num_t, comp)
        else:
            body = ranked(row, arts[row["name"]], rank, gone, t0, num_t)
        comp.scene(t0, end + .05, body, fade_in=.05, fade_out=.12, z=3)

    # PLAYERS LEFT: five before the first lands, one fewer as each one does.
    counts = [(0.0, n)] + [(ln.start + .3, max(1, rank - 1)) for rank, _, _, ln in lines]
    for i, (t, c) in enumerate(counts):
        t1 = counts[i + 1][0] if i + 1 < len(counts) else dur
        comp.scene(t, t1 + .001, f'<div class="abs" style="right:{W - 1020}px;top:{TOP_Y}px;display:flex;'
                   f'align-items:center;gap:12px;background:rgba(7,14,51,.8);border-radius:12px;padding:6px 20px 2px 16px">'
                   f'{person_icon(46)}<span class="fx" style="font-size:76px;color:#fff;display:inline-block;'
                   f'{style_anim(an("igtick", t, .35))}">{c}</span><span class="ui" style="font-size:26px;'
                   f'color:#C9D3FF;margin-left:2px">LEFT</span></div>', fade_in=.01, fade_out=.01, z=100)
    comp.add(f'<div class="abs" style="right:{W - 1020}px;top:{TOP_Y + 100}px;z-index:100">'
             f'<span class="ig-chip" style="background:#7A2BD6;color:#fff">TODAY\'S COMEBACKS</span></div>')
    card_t = lc.at("BAD") - .5
    to_end(comp, lc.start, f'<div class="full" style="background:rgba(7,14,51,.6)"></div>'
           + support_card(card_t, comp, top=560), z=6)
    comp.add(code_panel())
    captions(comp, sc)
    return comp, sc, f"Players Left: today's comebacks ({day:%b %-d})"


def ranked(row: dict, art: str, rank: int, gone: int, t0: float, num_t: float) -> str:
    """#5..#2: the item's card drops in, its rank top left, the days it was
    gone top right."""
    trim = ' data-trim="figure"' if str(row.get("type") or "").lower() == "outfit" else " data-trim"
    fig = (f'<img{trim} src="{art}" style="max-height:440px;max-width:600px;'
           f'filter:drop-shadow(0 24px 30px rgba(0,0,0,.55))">' if art else "")
    name_px = 70 if len(row["name"]) <= 16 else 54
    return (f'<div class="abs" style="left:60px;top:{VIEW_TOP + 20}px;width:840px;'
            f'{style_anim(an("igdrop", t0, .55, EASE_OUT))}">'
            f'<div style="position:relative;height:700px;border-radius:22px;overflow:hidden;'
            f'box-shadow:0 14px 0 rgba(0,0,0,.4)"><div class="full" style="background:{tile_bg(row)}"></div>'
            f'<div class="grain"></div>'
            f'<div class="abs" style="left:0;right:0;bottom:150px;display:flex;justify-content:center">{fig}</div>'
            f'<div class="abs fx fxs" style="left:26px;top:20px;font-size:150px;color:#fff">#{rank}</div>'
            f'<div class="abs" style="right:24px;top:28px;text-align:right;{style_anim(an("igin", num_t, .3, EASE_BACK))}">'
            f'<span class="ig-chip" style="font-size:34px;background:{GOLD};color:{NAVY}">BACK AFTER</span>'
            f'<div class="fx fxs" style="font-size:112px;color:#fff;margin-top:8px">{gone:,}'
            f'<span style="font-size:.42em"> DAYS</span></div></div>'
            f'<div class="ig-plate" style="padding:0 26px 24px"><div class="ig-name" style="font-size:{name_px}px">'
            f'{esc(row["name"])}</div><div class="ui" style="font-size:26px;color:{GOLD};margin-top:6px">'
            f'{esc(kind_label(row))}</div></div></div></div>')


def winner(row: dict, art: str, gone: int, t0: float, vt: float, num_t: float, comp: Comp) -> str:
    """#1: VICTORY ROYALE across the top, the item in the light, the days under it."""
    trim = ' data-trim="figure"' if str(row.get("type") or "").lower() == "outfit" else " data-trim"
    fig = (f'<img{trim} src="{art}" style="max-height:330px;max-width:600px;'
           f'filter:drop-shadow(0 0 40px rgba(255,227,74,.55)) drop-shadow(0 24px 30px rgba(0,0,0,.5))">' if art else "")
    rays = (f'<div class="abs" style="left:50%;top:50%;width:2600px;height:2600px;'
            f'background:repeating-conic-gradient(from 0deg,rgba(255,227,74,.12) 0 7deg,transparent 7deg 20deg);'
            f'transform:translate(-50%,-50%);{style_anim(an("fadein", vt, .3), an("igrays", vt, 30, "linear", "infinite"))}"></div>')
    flash = (f'<div class="full" style="background:#fff;opacity:0;'
             f'{style_anim(an("igflash", vt, .45, "ease-out", fill="none"))}"></div>')
    gold = ("background:linear-gradient(180deg,#FFF7B0 0%,#FFE34A 45%,#F2A900 100%);-webkit-background-clip:text;"
            "background-clip:text;color:transparent;filter:drop-shadow(0 7px 0 #4A2200) "
            "drop-shadow(0 0 24px rgba(255,200,40,.55))")
    banner = (f'<div class="abs" style="left:60px;width:840px;top:{VIEW_TOP + 6}px;text-align:center;'
              f'{style_anim(an("igin", vt + .05, .45, EASE_BACK))}">'
              f'<div class="fx" style="font-size:66px;color:#fff;letter-spacing:.06em">#1</div>'
              f'<div class="fx" style="font-size:148px;line-height:.8;{gold}">VICTORY ROYALE</div></div>')
    item = (f'<div class="abs" style="left:60px;width:840px;top:748px;height:336px;display:flex;align-items:flex-end;'
            f'justify-content:center;{style_anim(an("igdrop", t0, .55, EASE_OUT))}">{fig}</div>')
    name_px = 84 if len(row["name"]) <= 14 else 62
    under = (f'<div class="abs" style="left:60px;width:840px;top:1092px;text-align:center">'
             f'<span class="fx fxs" style="font-size:{name_px}px;color:#fff">{esc(row["name"])}</span>'
             f'<span style="display:inline-block;margin-left:18px;vertical-align:.4em;'
             f'{style_anim(an("igin", num_t, .3, EASE_BACK))}"><span class="ig-chip" style="font-size:36px;'
             f'background:{GOLD};color:{NAVY}">BACK AFTER {gone:,} DAYS</span></span></div>')
    return (rays + flash + item + banner + under
            + burst(480, 640, vt + .05, 11, n=36, colors=(GOLD, "#fff", LIME, "#7A2BD6", "#3FA2FF")))


# ------------------------------------------------------------------ sound

def soundtrack(comp: Comp, sc: Script, seed: int, path: Path, day: date) -> Path:
    """The voice on top, a library track (CC0) under it that dips while the
    voice speaks, the UI sounds on their cues; the mix at the edits' loudness."""
    import cc_audio as A
    import cc_edit as ED
    n = int(comp.duration * A.SR)
    v = sc.track(comp.duration).astype(np.float64)
    # Kokoro's 24 kHz to 44.1 kHz, band-limited (FFT resampling).
    m = int(round(len(v) * A.SR / VSR))
    spec = np.fft.rfft(v)
    out = np.zeros(m // 2 + 1, dtype=complex)
    k = min(len(spec), len(out))
    out[:k] = spec[:k]
    voice = np.fft.irfft(out, m) * (m / len(v))
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    voice *= 10 ** ((-16.0 - A.loudness(voice)) / 20)
    beat = ED.music_for(seed, "hype", day=day, salt="ingame")
    bed = A.track_audio(beat.music, comp.duration, seed)[:n]
    if len(bed) < n:
        bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    bed *= 10 ** ((-21.0 - A.loudness(bed)) / 20)
    # Duck the music under the voice: an envelope of the voice's level, smoothed.
    hop = int(.02 * A.SR)
    lev = np.sqrt(np.convolve(voice ** 2, np.ones(hop) / hop, mode="same"))
    on = (lev > .01).astype(float)
    kern = np.ones(int(.25 * A.SR)) / int(.25 * A.SR)
    on = np.clip(np.convolve(on, kern, mode="same") * 1.6, 0, 1)
    bed *= (1 - .5 * on)[:, None]
    fx = np.zeros((n, 2))
    rs = np.random.RandomState(seed % (2 ** 31))
    cache = {}
    for t, kind in sorted(comp.cues):
        if kind not in cache:
            cache[kind] = A.edit_sfx(kind, rs)
        s = int(t * A.SR)
        if s >= n:
            continue
        sig = cache[kind] * A.EDIT_GAINS.get(kind, .4) * .55
        e = min(n, s + len(sig))
        fx[s:e] += sig[:e - s]
    mix = bed + fx + np.stack([voice, voice], axis=1) * .9
    mix *= 10 ** ((A.LUFS - A.loudness(mix)) / 20)
    comp.music = beat.music
    return A.write_wav(A.limit(mix, .84), path)


# ------------------------------------------------------------------ main

BUILDERS = {"shop": shop_today, "comebacks": comebacks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shop", required=True, help="a shop.json (cc_shop.normalize)")
    ap.add_argument("--records", default=str(OUT_DIR / "_data" / "br-fresh.json"))
    ap.add_argument("--out", default=str(OUT_DIR / "ingame-preview"))
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--only", default=",".join(BUILDERS))
    ap.add_argument("--stills", default="", help="comma-separated seconds: stills only, no video")
    args = ap.parse_args()
    import cc_motion as M
    import cc_rarity as R
    shop = json.loads(Path(args.shop).read_text())
    day = date.fromisoformat(shop["shop_day"])
    hist = R.History(R.load(args.records))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in args.only.split(","):
        got = BUILDERS[name](shop, hist, day, args.voice)
        if not got:
            log(f"{name}: can't be made from today's shop")
            continue
        comp, sc, label = got
        log(f"{name}: {label}, {comp.duration:.1f}s, {len(sc.lines)} lines")
        for ln in sc.lines:
            log(f"   {ln.start:5.2f}-{ln.end:5.2f}  {ln.text}")
        if args.stills:
            M.snapshot(comp, [float(s) for s in args.stills.split(",")], out / f"{name}-{args.voice}")
            continue
        wav = soundtrack(comp, sc, int(day.strftime("%Y%m%d")), out / f"{name}-{args.voice}.wav", day)
        M.render(comp, out / f"{name}-{args.voice}.mp4", audio=wav)
        log(f"   -> {out / f'{name}-{args.voice}.mp4'}")


if __name__ == "__main__":
    main()
