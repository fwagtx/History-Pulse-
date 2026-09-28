"""
Soundtrack for @usecodebad videos, synthesized from scratch.

Every sound is generated here from sine waves and noise, so there is nothing to
license, nothing for TikTok's or YouTube's copyright matching to flag, and no
download that can break. Two layers:

  - a music bed: drums, bass and chords, with tempo and key varied per video so
    three posts a day don't share one identical track
  - sound effects placed exactly on the visual cues the formats record with
    comp.cue(t, kind): whoosh, slam, tick, pop, reveal, cash, and for the quizzes
    drumroll, ding, clap, airhorn

Needs numpy (pip install numpy). Writes a 44.1 kHz stereo 16-bit WAV that
cc_motion.render() muxes into the MP4 as AAC.
"""

import random
import wave
from pathlib import Path

import numpy as np

SR = 44100


# ------------------------------------------------------------------ building blocks

def _t(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def _env(n: int, attack: float, decay: float) -> np.ndarray:
    """Fast attack, exponential decay."""
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / max(decay, 1e-4))


def _noise(n: int, rs: np.random.RandomState) -> np.ndarray:
    return rs.uniform(-1, 1, n)


def _band(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Band-pass by FFT with soft edges. Fine for short one-shots."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    lo_gain = 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    hi_gain = 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * lo_gain * hi_gain, len(x))


def _saw(freq: float, t: np.ndarray, harmonics: int = 10, phase: float = 0.0) -> np.ndarray:
    """Band-limited sawtooth by additive synthesis: warm, no aliasing."""
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        if freq * k > SR / 2.2:
            break
        out += np.sin(2 * np.pi * freq * k * t + phase * k) / k
    return out * (2 / np.pi)


def _norm(x: np.ndarray, peak: float = 1.0) -> np.ndarray:
    m = np.max(np.abs(x)) if len(x) else 0
    return x * (peak / m) if m > 0 else x


def _midi(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


# ------------------------------------------------------------------ sound effects

def sfx(kind: str, rs: np.random.RandomState) -> np.ndarray:
    """One mono effect, peak-normalized. Unknown kinds are silent, never fatal."""
    if kind == "whoosh":
        n = int(.42 * SR)
        t = np.arange(n) / SR
        # Two noise bands crossfaded low -> high reads as air rushing past.
        low, high = _band(_noise(n, rs), 300, 1400), _band(_noise(n, rs), 1400, 6000)
        mix = np.clip(t / t[-1], 0, 1)
        shape = np.sin(np.pi * np.clip(t / t[-1], 0, 1)) ** 1.6
        return _norm((low * (1 - mix) + high * mix) * shape) * .8
    if kind == "slam":
        n = int(.7 * SR)
        t = np.arange(n) / SR
        pitch = 42 + 110 * np.exp(-t / .045)
        boom = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-t / .22)
        crack = _band(_noise(n, rs), 900, 7000) * np.exp(-t / .025)
        return _norm(np.tanh(2.4 * (boom + .55 * crack)))
    if kind == "tick":
        n = int(.09 * SR)
        t = np.arange(n) / SR
        click = (np.sin(2 * np.pi * 1850 * t) + .5 * np.sin(2 * np.pi * 3700 * t)) * np.exp(-t / .012)
        wood = _band(_noise(n, rs), 1500, 5000) * np.exp(-t / .006)
        return _norm(click + .6 * wood) * .55
    if kind == "pop":
        n = int(.14 * SR)
        t = np.arange(n) / SR
        f = 380 + 900 * (t / t[-1]) ** .5
        return _norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .045)) * .7
    if kind == "reveal":
        # A quick rising arpeggio with a shimmer tail.
        n = int(1.1 * SR)
        out = np.zeros(n)
        for i, semis in enumerate((0, 4, 7, 12, 16)):
            start = int(i * .06 * SR)
            m = n - start
            tt = np.arange(m) / SR
            f = _midi(72 + semis)
            tone = (np.sin(2 * np.pi * f * tt) + .3 * np.sin(2 * np.pi * 2 * f * tt)) * _env(m, .004, .35)
            out[start:] += tone
        shimmer = _band(_noise(n, rs), 5000, 12000) * _env(n, .2, .3) * .25
        return _norm(out + shimmer) * .75
    if kind == "cash":
        # Register "ka" (noise hit) then bell "ching" (inharmonic partials).
        n = int(.9 * SR)
        t = np.arange(n) / SR
        ka = _band(_noise(n, rs), 1200, 6000) * np.exp(-t / .02)
        bell = np.zeros(n)
        d = int(.07 * SR)
        tb = np.arange(n - d) / SR
        for f, a in ((2093, 1), (2637, .7), (4186, .45), (5274, .3)):
            bell[d:] += a * np.sin(2 * np.pi * f * tb) * np.exp(-tb / .32)
        return _norm(ka * .8 + bell) * .7
    # The quiz set: game-show sounds, made here like everything else. Real emote
    # audio is off limits -- many emotes carry licensed songs whose licence covers
    # the game only, not uploads, and they draw copyright strikes.
    if kind == "drumroll":
        # A snare roll that speeds up (13 -> 28 hits a second) and swells for
        # 1.6 s, straight into the answer.
        dur = 1.6
        n = int(dur * SR)
        out = np.zeros(n)
        ht = _t(.06)
        t = 0.0
        while t < dur - .03:
            p = t / dur
            hit = (_band(_noise(len(ht), rs), 1500, 9000) * np.exp(-ht / .018)
                   + .35 * np.sin(2 * np.pi * 210 * ht) * np.exp(-ht / .02))
            s = int(t * SR)
            e = min(n, s + len(hit))
            out[s:e] += hit[:e - s] * (.25 + .75 * p ** 1.5) * rs.uniform(.8, 1)
            t += 1 / (13 + 15 * p)
        return _norm(out) * .8
    if kind == "ding":
        # "Ding-ding": two bright bell strikes a major third apart (E6, G#6).
        n = int(1.2 * SR)
        out = np.zeros(n)
        for i, note in enumerate((88, 92)):
            s = int(i * .11 * SR)
            tt = np.arange(n - s) / SR
            f = _midi(note)
            bell = sum(a * np.sin(2 * np.pi * f * m * tt) * np.exp(-tt / d)
                       for m, a, d in ((1, 1, .45), (2.76, .35, .18), (5.4, .15, .08)))
            out[s:] += bell * np.minimum(1, tt / .002)
        return _norm(out) * .7
    if kind == "clap":
        # A small crowd clapping: seventy short noise claps, swelling then fading.
        dur = 1.6
        n = int(dur * SR)
        out = np.zeros(n)
        ct = _t(.03)
        base = _band(_noise(len(ct) * 4, rs), 900, 5000)
        for _ in range(70):
            s = int(rs.uniform(0, dur - .05) * SR)
            k = rs.randint(0, 3) * len(ct)
            clap = base[k:k + len(ct)] * np.exp(-ct / .006) * rs.uniform(.4, 1)
            out[s:s + len(clap)] += clap
        tt = _t(dur)
        return _norm(out * np.minimum(1, tt / .15) * np.exp(-tt / .7)) * .6
    if kind == "airhorn":
        # Three blasts on a brassy A-major chord: short, short, long.
        out = np.zeros(int(1.05 * SR))
        for start, length in ((0, .13), (.18, .13), (.36, .6)):
            tt = _t(length)
            env = np.minimum(1, tt / .01) * np.minimum(1, (length - tt) / .05)
            tone = sum(_saw(_midi(m) * d, tt, 14) for m in (57, 61, 64) for d in (.997, 1.003))
            s = int(start * SR)
            out[s:s + len(tt)] += np.tanh(2.2 * tone / 6) * env
        return _norm(out) * .75
    # Object sounds for the new looks: each look's motion lands on a sound that
    # matches the thing on screen (paper, stamps, pens, flaps, printers, tape).
    if kind == "paper":
        # A sheet or sticker slid and pressed down: a soft swish, then a light tap.
        n = int(.32 * SR)
        t = np.arange(n) / SR
        swish = _band(_noise(n, rs), 700, 5200) * np.sin(np.pi * np.clip(t / .22, 0, 1)) ** 2
        tap = _band(_noise(n, rs), 200, 1800) * np.exp(-np.maximum(t - .2, 0) / .015) * (t > .2)
        return _norm(.8 * swish + tap) * .55
    if kind == "stamp":
        # A rubber stamp: a dull thud with a papery slap on top.
        n = int(.35 * SR)
        t = np.arange(n) / SR
        thud = np.sin(2 * np.pi * np.cumsum(55 + 70 * np.exp(-t / .03)) / SR) * np.exp(-t / .08)
        slap = _band(_noise(n, rs), 500, 3500) * np.exp(-t / .02)
        return _norm(np.tanh(1.8 * (thud + .7 * slap))) * .8
    if kind == "pen":
        # A marker or ballpoint scribbling for about half a second.
        n = int(.5 * SR)
        t = np.arange(n) / SR
        am = .55 + .45 * np.sin(2 * np.pi * (11 + 6 * rs.rand()) * t + rs.rand() * 6) ** 2
        body = _band(_noise(n, rs), 1800, 7500) * am
        return _norm(body * np.minimum(1, t / .03) * np.minimum(1, (t[-1] - t) / .06)) * .35
    if kind == "flap":
        # A split-flap cell settling: a quick run of plastic clicks.
        n = int(.5 * SR)
        out = np.zeros(n)
        ct = _t(.012)
        k, at = 0, 0.0
        while at < .42:
            click = _band(_noise(len(ct), rs), 1800, 6500) * np.exp(-ct / .0025)
            s = int(at * SR)
            out[s:s + len(ct)] += click * rs.uniform(.5, 1)
            at += .028 + .012 * k / 14
            k += 1
        return _norm(out) * .5
    if kind == "printer":
        # A thermal printer feeding a few lines: a stepping buzz.
        n = int(.6 * SR)
        t = np.arange(n) / SR
        buzz = np.sign(np.sin(2 * np.pi * 430 * t)) * .5 + _band(_noise(n, rs), 900, 4000) * .5
        steps = (np.sin(2 * np.pi * 14 * t) > -.2).astype(float)
        return _norm(buzz * steps * np.minimum(1, t / .02) * np.minimum(1, (t[-1] - t) / .04)) * .3
    if kind == "tape":
        # A VCR taking a tape: a mechanical clunk, then the motor spinning up.
        n = int(.7 * SR)
        t = np.arange(n) / SR
        clunk = (_band(_noise(n, rs), 300, 2500) * np.exp(-t / .02)
                 + np.sin(2 * np.pi * 90 * t) * np.exp(-t / .06))
        motor = np.sin(2 * np.pi * np.cumsum(60 + 90 * np.clip((t - .15) / .4, 0, 1)) / SR) * (t > .15) * .25
        return _norm(clunk + motor * np.minimum(1, (t[-1] - t) / .1)) * .7
    if kind == "static":
        # TV static between tape cuts.
        n = int(.45 * SR)
        t = np.arange(n) / SR
        hiss = _band(_noise(n, rs), 900, 9000)
        return _norm(hiss * np.minimum(1, t / .01) * np.minimum(1, (t[-1] - t) / .08)) * .35
    if kind == "pin":
        # A push pin going into cork.
        n = int(.12 * SR)
        t = np.arange(n) / SR
        return _norm(_band(_noise(n, rs), 1500, 6000) * np.exp(-t / .008)
                     + .5 * np.sin(2 * np.pi * 180 * t) * np.exp(-t / .03)) * .55
    if kind == "flip":
        # A card flipped over: a short air swish and a tap as it lands.
        n = int(.3 * SR)
        t = np.arange(n) / SR
        swish = _band(_noise(n, rs), 1500, 7000) * np.sin(np.pi * np.clip(t / .18, 0, 1)) ** 2
        tap = _band(_noise(n, rs), 400, 3000) * np.exp(-np.maximum(t - .2, 0) / .01) * (t > .2)
        return _norm(.7 * swish + tap) * .55
    if kind == "click":
        # A mouse click or a light switch.
        n = int(.06 * SR)
        t = np.arange(n) / SR
        return _norm(np.sin(2 * np.pi * 2600 * t) * np.exp(-t / .004)
                     + _band(_noise(n, rs), 2000, 8000) * np.exp(-t / .003)) * .45
    return np.zeros(1)


# ------------------------------------------------------------------ music bed

PROGRESSIONS = [
    [0, -4, 3, -2],     # i  VI  III VII  (minor pop)
    [0, 3, -2, -4],     # i  III VII VI
    [0, -4, -2, 0],     # i  VI  VII i
]


BPMS = [112, 116, 120, 124, 128]


def music(duration: float, seed: int, bpm: float | None = None) -> np.ndarray:
    """A driving, loopable bed. Stereo (n, 2). Varies by seed. Its beats fall on
    k * 60 / bpm from 0; `bpm` fixes the tempo (default: one of BPMS by seed)."""
    r = random.Random(seed)
    rs = np.random.RandomState(seed % (2 ** 32))
    picked = r.choice(BPMS)
    bpm = bpm or picked
    key = r.choice([45, 46, 47, 48, 49, 50, 52])       # A2..E3 roots
    prog = r.choice(PROGRESSIONS)
    beat = 60 / bpm
    bar = beat * 4
    n = int(duration * SR)
    L, R = np.zeros(n), np.zeros(n)

    def put(buf, start_s, sig):
        s = int(start_s * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        buf[s:e] += sig[:e - s]

    # Drum one-shots, rendered once.
    kt = _t(.35)
    kick = np.sin(2 * np.pi * np.cumsum(48 + 120 * np.exp(-kt / .03)) / SR) * np.exp(-kt / .16)
    kick = np.tanh(1.8 * kick)
    st = _t(.25)
    snare = (_band(_noise(len(st), rs), 1200, 8000) * np.exp(-st / .07)
             + .4 * np.sin(2 * np.pi * 190 * st) * np.exp(-st / .05))
    ht = _t(.05)
    hat = np.diff(_noise(len(ht) + 1, rs)) * np.exp(-ht / .012)

    # Sidechain envelope: everything melodic ducks under each kick -- the pump
    # that makes short-form music feel alive.
    duck = np.ones(n)
    kicks = np.arange(0, duration, beat)
    for k in kicks:
        s = int(k * SR)
        m = min(n - s, int(beat * SR))
        tt = np.arange(m) / SR
        duck[s:s + m] = np.minimum(duck[s:s + m], 1 - .65 * np.exp(-tt / .11))

    # Drums
    fill_every = r.choice([4, 8])
    for i, k in enumerate(kicks):
        put(L, k, kick * .9); put(R, k, kick * .9)
        if i % 4 in (1, 3):
            put(L, k, snare * .38); put(R, k, snare * .42)
        for off in (0, .5):
            vel = .16 if off else .09
            put(L, k + off * beat, hat * vel * .8)
            put(R, k + off * beat, hat * vel)
        bar_i = i // 4
        if bar_i % fill_every == fill_every - 1 and i % 4 == 3:
            for f in (.25, .5, .75):
                put(L, k + f * beat, snare * .22); put(R, k + f * beat, snare * .24)

    # Bass: root on 8ths with an octave pop on the offbeat.
    mel_L, mel_R = np.zeros(n), np.zeros(n)
    bars = int(np.ceil(duration / bar))
    note8 = beat / 2
    for b in range(bars):
        root = key + prog[b % len(prog)]
        for s8 in range(8):
            t0 = b * bar + s8 * note8
            f = _midi(root + (12 if s8 % 2 else 0))
            tt = _t(note8 * .92)
            tone = _saw(f, tt, 6) * _env(len(tt), .004, .12) * .30
            put(mel_L, t0, tone); put(mel_R, t0, tone)

        # Chords: detuned saws, a minor triad voiced an octave up, whole bar.
        tt = _t(bar)
        env = np.minimum(1, tt / .03) * np.exp(-tt / (bar * 1.4))
        chord_root = root + 12
        for semis in (0, 3, 7, 12):
            f = _midi(chord_root + semis)
            put(mel_L, b * bar, _saw(f * 1.004, tt, 7) * env * .045)
            put(mel_R, b * bar, _saw(f * .996, tt, 7, phase=.7) * env * .045)

        # A plucked 16th arpeggio on the second half of each bar keeps motion.
        arp = [0, 7, 12, 15, 12, 7, 3, 7]
        for j, semis in enumerate(arp):
            t0 = b * bar + 2 * beat + j * beat / 4
            f = _midi(chord_root + 12 + semis)
            tt = _t(beat / 4)
            pl = np.sin(2 * np.pi * f * tt) * _env(len(tt), .002, .06) * .07
            put(mel_L if j % 2 else mel_R, t0, pl)
            put(mel_R if j % 2 else mel_L, t0 + .012, pl * .5)  # tiny ping-pong

    L += mel_L * duck
    R += mel_R * duck
    stereo = np.stack([L, R], axis=1)

    # Fade in fast, fade out over the last 1.5 s.
    fade = np.ones(n)
    fi, fo = int(.15 * SR), int(1.5 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    return stereo * fade[:, None]


# ------------------------------------------------------------------ mix

def mix(duration: float, cues: list, seed: int, music_gain: float = .34) -> np.ndarray:
    n = int(duration * SR)
    bed = music(duration, seed)
    bed = bed / (np.max(np.abs(bed)) or 1) * music_gain
    fx = np.zeros((n, 2))
    rs = np.random.RandomState((seed * 7 + 3) % (2 ** 32))
    cache = {}
    gains = {"whoosh": .5, "slam": .8, "tick": .5, "pop": .45, "reveal": .55, "cash": .6,
             "drumroll": .45, "ding": .55, "clap": .32, "airhorn": .5}
    for t, kind in cues:
        if kind not in cache:
            cache[kind] = sfx(kind, rs)
        s = int(t * SR)
        if s >= n:
            continue
        sig = cache[kind] * gains.get(kind, .5)
        e = min(n, s + len(sig))
        pan = .5 + .15 * np.sin(t * 1.7)        # slight movement between effects
        fx[s:e, 0] += sig[:e - s] * np.cos(pan * np.pi / 2) * 1.414
        fx[s:e, 1] += sig[:e - s] * np.sin(pan * np.pi / 2) * 1.414
    out = bed + fx
    # Soft limiter: gentle saturation, then peak to -1 dBFS.
    out = np.tanh(out * 1.2) / np.tanh(1.2)
    return _norm(out, .89)


# ------------------------------------------------------------------ real music (the edits)
#
# An edit (cc_edit.py) is cut to the beats of a real track. comp.music is then
# either a cc_music track -- {"path": mp3, "beats": [s, ...], "cut": s, ...} --
# or, where the library can't be had, {"synth": bpm, "seed": n}: the
# synthesized bed at that tempo, whose beats fall on k * 60 / bpm. The edits'
# effects (edit_sfx) are the ones short-form editors reach for -- booms,
# risers, swooshes -- and the music dips a little under the big hits.

# Set against the music (its loudest 100 ms vs the music's): hits about +5 to
# +8 dB, transitions about level with it, small sounds a few dB under.
EDIT_GAINS = {"boom": .9, "impact": .55, "riser": .45, "swoosh": .75, "pop2": .6, "tick2": .8,
              "buzz": .35, "shutter": .8, "glitch": .6, "ding": .75, "whoosh": .9, "pop": .7,
              "tick": .9, "clap": .45, "cash": .55, "reveal": .5, "slam": .6, "click": 1.2, "drumroll": .5}
DUCK = {"boom": .5, "impact": .3, "slam": .3, "buzz": .2}      # how far the music dips (fraction)
LUFS = -13.0                                               # the finished mix's loudness


def _pan(x: np.ndarray, pan: float = 0.0) -> np.ndarray:
    """Mono to stereo, constant power; pan -1 (left) .. 1 (right)."""
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * 1.414


def _ir(seconds: float, rs: np.random.RandomState, dark: float = 5000) -> np.ndarray:
    """A synthetic stereo room: decaying noise, darker as it fades."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 6.9 / seconds)
    out = []
    for _ in range(2):
        x = _noise(n, rs) * env
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(n, 1 / SR)
        X *= 1 / (1 + (f / dark) ** 2)
        out.append(np.fft.irfft(X, n))
    ir = np.stack(out, axis=1)
    ir[: int(.004 * SR)] *= np.linspace(0, 1, int(.004 * SR))[:, None]
    return ir / (np.sqrt((ir ** 2).sum(axis=0)).max() or 1)


def _verb(x: np.ndarray, seconds: float, wet: float, rs: np.random.RandomState,
          dark: float = 5000) -> np.ndarray:
    """Mono in, stereo out: the dry sound centred plus a synthetic room."""
    ir = _ir(seconds, rs, dark)
    n = len(x) + len(ir) - 1
    m = 1 << (n - 1).bit_length()
    X = np.fft.rfft(x, m)
    tail = np.stack([np.fft.irfft(X * np.fft.rfft(ir[:, c], m), m)[:n] for c in range(2)], axis=1)
    dry = np.zeros((n, 2))
    dry[: len(x)] = _pan(x) * .707
    return dry + wet * tail


def _sweep_noise(n: int, rs: np.random.RandomState, centre: np.ndarray, width: float = .6) -> np.ndarray:
    """Noise through a band-pass whose centre moves (Hz per sample), in 40 ms
    overlapping frames."""
    hop, size = int(.02 * SR), int(.04 * SR)
    x = _noise(n + size, rs)
    out = np.zeros(n + size)
    win = np.hanning(size)
    f = np.fft.rfftfreq(size, 1 / SR)
    for s in range(0, n, hop):
        c = float(centre[min(s, n - 1)])
        g = np.exp(-.5 * (np.log2(np.maximum(f, 1) / c) / width) ** 2)
        seg = np.fft.irfft(np.fft.rfft(x[s:s + size] * win) * g, size)
        out[s:s + size] += seg * win
    return out[:n]


def edit_sfx(kind: str, rs: np.random.RandomState) -> np.ndarray:
    """One stereo effect for the edits, peak-normalized. The quiz set's kinds
    come through sfx(), centred; unknown kinds are silent."""
    if kind == "boom":
        # The cinematic hit on a number or a reveal: a sub that drops in pitch,
        # a punchy body and a click, in a big dark room.
        n = int(1.4 * SR)
        t = np.arange(n) / SR
        f = 36 + 64 * np.exp(-t / .05)
        sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .5)
        body = _band(_noise(n, rs), 90, 800) * np.exp(-t / .06)
        click = _band(_noise(n, rs), 1800, 9000) * np.exp(-t / .005)
        x = _norm(np.tanh(1.7 * (sub + .4 * body)) + .3 * click)
        return _norm(_verb(x, 1.6, .16, rs, dark=2500)) * .95
    if kind == "impact":
        # A lighter punch for words landing.
        n = int(.6 * SR)
        t = np.arange(n) / SR
        kick = np.sin(2 * np.pi * np.cumsum(55 + 110 * np.exp(-t / .03)) / SR) * np.exp(-t / .12)
        snap = _band(_noise(n, rs), 900, 6500) * np.exp(-t / .03)
        x = _norm(np.tanh(1.5 * (kick + .6 * snap)))
        return _norm(_verb(x, .7, .12, rs, dark=4000)) * .85
    if kind == "riser":
        # Two seconds of rising noise and tone that stops dead on the drop.
        dur = 2.0
        n = int(dur * SR)
        t = np.arange(n) / SR
        p = t / dur
        air = _sweep_noise(n, rs, 350 * (9000 / 350) ** (p ** 1.3), .7)
        f = 170 * (1150 / 170) ** (p ** 1.6)
        ph = 2 * np.pi * np.cumsum(f) / SR
        trem = .75 + .25 * np.sin(2 * np.pi * np.cumsum(5 + 22 * p ** 2) / SR)
        L = (np.sin(ph) + .35 * np.sin(2 * ph + .3)) * trem
        R = (np.sin(ph * 1.006) + .35 * np.sin(2 * ph * 1.006)) * trem
        env = p ** 2.2 * np.minimum(1, (dur - t) / .012)
        x = np.stack([.55 * air + .45 * L, .55 * air + .45 * R], axis=1) * env[:, None]
        return _norm(x) * .9
    if kind == "swoosh":
        # A fast whoosh for a whip pan: the band rises then falls, left to right.
        n = int(.34 * SR)
        t = np.arange(n) / SR
        p = t / t[-1]
        centre = 600 + 3200 * np.sin(np.pi * np.clip(p / .75, 0, 1)) ** 1.5
        x = _sweep_noise(n, rs, centre, .5) * np.sin(np.pi * p) ** 1.8
        pan = -.7 + 1.4 * p
        a = (pan + 1) * np.pi / 4
        return _norm(np.stack([x * np.cos(a), x * np.sin(a)], axis=1)) * .85
    if kind == "pop2":
        # A bubbly pop for a caption appearing.
        n = int(.16 * SR)
        t = np.arange(n) / SR
        f = 1250 * np.exp(-t / .03) + 340
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .035)
        x += .25 * _band(_noise(n, rs), 2000, 8000) * np.exp(-t / .003)
        return _norm(_verb(_norm(x), .35, .08, rs)) * .75
    if kind == "tick2":
        # A soft woodblock tick for a counter.
        n = int(.07 * SR)
        t = np.arange(n) / SR
        x = (np.sin(2 * np.pi * 1850 * t) + .45 * np.sin(2 * np.pi * 3120 * t)) * np.exp(-t / .01)
        x += .4 * _band(_noise(n, rs), 2500, 7000) * np.exp(-t / .002)
        return _norm(_pan(x)) * .6
    if kind == "buzz":
        # Wrong: a short, low, detuned buzzer.
        n = int(.5 * SR)
        t = np.arange(n) / SR
        env = np.minimum(1, t / .01) * np.minimum(1, (t[-1] - t) / .06)
        x = np.tanh(2.5 * (_saw(98, t, 12) + _saw(104, t, 12))) * env
        return _norm(_pan(x)) * .7
    if kind == "shutter":
        # A camera shutter: two mechanical clicks and a thunk.
        n = int(.16 * SR)
        t = np.arange(n) / SR
        x = np.zeros(n)
        for at, a in ((0, 1), (.045, .7)):
            s = int(at * SR)
            m = n - s
            tt = np.arange(m) / SR
            x[s:] += a * (_band(_noise(m, rs), 2500, 9000) * np.exp(-tt / .004)
                          + .5 * np.sin(2 * np.pi * 180 * tt) * np.exp(-tt / .015))
        return _norm(_pan(x)) * .7
    if kind == "glitch":
        # Digital stutter: short crushed bursts at jumping pitches.
        n = int(.32 * SR)
        x = np.zeros(n)
        s = 0
        while s < n - int(.012 * SR):
            m = min(int(rs.uniform(.012, .03) * SR), n - s)
            tt = np.arange(m) / SR
            tone = np.sign(np.sin(2 * np.pi * rs.choice([220, 330, 440, 880, 1320]) * tt))
            crush = np.round(_noise(m, rs) * 4) / 4
            x[s:s + m] += (tone * .6 + crush * .4) * rs.uniform(.4, 1)
            s += m + int(rs.uniform(0, .015) * SR)
        return _norm(_pan(x, rs.uniform(-.4, .4))) * .6
    mono = sfx(kind, rs)
    return _pan(mono) * .707 if len(mono) > 1 else np.zeros((1, 2))


def loudness(x: np.ndarray) -> float:
    """Integrated loudness in LUFS (ITU-R BS.1770: K-weighting, 400 ms blocks,
    absolute and relative gates), with the K-filter applied as a zero-phase
    frequency response."""
    x = x[:, None] if x.ndim == 1 else x
    n = len(x)
    if n < int(.4 * SR):
        return -70.0
    f = np.fft.rfftfreq(n, 1 / SR)
    g = 10 ** (4 / 20)
    shelf = np.sqrt((1 + (f / 1500) ** 2 * g ** 2) / (1 + (f / 1500) ** 2))
    hp = (f / 38) ** 2 / np.sqrt(1 + (f / 38) ** 4)
    y = np.fft.irfft(np.fft.rfft(x, axis=0) * (shelf * hp)[:, None], n, axis=0)
    blk, hop = int(.4 * SR), int(.1 * SR)
    cs = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(y ** 2, axis=0)])
    st = np.arange(0, n - blk + 1, hop)
    z = ((cs[st + blk] - cs[st]) / blk).sum(axis=1)
    lk = -.691 + 10 * np.log10(z + 1e-12)
    z, lk = z[lk > -70], lk[lk > -70]
    if not len(z):
        return -70.0
    rel = -.691 + 10 * np.log10(z.mean()) - 10
    return float(-.691 + 10 * np.log10(z[lk > rel].mean()))


def limit(x: np.ndarray, ceiling: float = .89, release: float = .12) -> np.ndarray:
    """A peak limiter: the gain is already down when a peak arrives (a block
    of look-ahead) and comes back up over `release` seconds."""
    blk = 32
    n = len(x)
    nb = -(-n // blk)
    pad = np.zeros((nb * blk, x.shape[1]))
    pad[:n] = x
    need = np.minimum(1.0, ceiling / np.maximum(np.abs(pad).reshape(nb, blk, -1).max(axis=(1, 2)), 1e-9))
    need = np.minimum.reduce([need, np.r_[need[1:], 1.0], np.r_[1.0, need[:-1]]])
    step = 1 - np.exp(-blk / (release * SR))
    g, cur = np.empty(nb), 1.0
    for i in range(nb):
        cur = need[i] if need[i] < cur else cur + (need[i] - cur) * step
        g[i] = cur
    gs = np.interp(np.arange(nb * blk), np.arange(nb) * blk + blk / 2, g)[:n]
    return np.clip(x * gs[:, None], -ceiling, ceiling)


def decode(path, sr: int = SR) -> np.ndarray:
    """An audio file as float stereo (n, 2) at `sr`, via ffmpeg."""
    import subprocess
    from cc_motion import find_ffmpeg
    raw = subprocess.run([find_ffmpeg() or "ffmpeg", "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").reshape(-1, 2).astype(np.float64)


def track_audio(track: dict, duration: float, seed: int) -> np.ndarray:
    """The music under an edit, `duration` seconds, stereo: the library track
    (looped by whole bars if the video runs past its cut, see
    cc_music.extend) or the synthesized bed at the edit's tempo."""
    n = int(duration * SR)
    if track.get("synth"):
        bed = music(duration, int(track.get("seed", seed)), bpm=float(track["synth"]))
    else:
        import cc_music
        x = decode(track["path"])
        off = float(track.get("offset", 0))          # the edit starts this far into the cut
        full = int((duration + off) * SR)
        bed = np.zeros((full, 2))
        for dst, src, length in cc_music.extend(track["beats"], len(x) / SR, duration + off):
            a, b, m = int(round(dst * SR)), int(round(src * SR)), int(round(length * SR))
            m = min(m, full - a, len(x) - b)
            if m <= 0:
                continue
            seg = x[b:b + m].copy()
            k = min(int(.006 * SR), m // 2)
            if a > 0 and k:                      # 6 ms crossfade at a loop join
                seg[:k] *= np.linspace(0, 1, k)[:, None]
                bed[a:a + k] *= np.linspace(1, 0, k)[:, None]
            bed[a:a + m] += seg
        bed = bed[int(round(off * SR)):][:n]
        if len(bed) < n:
            bed = np.concatenate([bed, np.zeros((n - len(bed), 2))])
        fo = min(n, int(1.2 * SR))
        bed[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    fi = int(.005 * SR)
    bed[:fi] *= np.linspace(0, 1, fi)[:, None]
    return bed


def mix_track(duration: float, cues: list, track: dict, seed: int, music_lufs: float = -15.0) -> np.ndarray:
    """An edit's soundtrack: the track at a steady loudness, the effects on top
    (EDIT_GAINS), the music dipping under the big hits (DUCK), then the whole
    mix brought to LUFS and peak-limited to -1 dBFS."""
    n = int(duration * SR)
    bed = track_audio(track, duration, seed)[:n]
    bed *= 10 ** ((music_lufs - loudness(bed)) / 20)
    fx = np.zeros((n, 2))
    duck = np.ones(n)
    rs = np.random.RandomState((seed * 7 + 3) % (2 ** 32))
    cache = {}
    for t, kind in sorted(cues):
        if kind not in cache:
            cache[kind] = edit_sfx(kind, rs)
        s = int(t * SR)
        if s >= n:
            continue
        sig = cache[kind] * EDIT_GAINS.get(kind, .4)
        e = min(n, s + len(sig))
        fx[s:e] += sig[:e - s]
        depth = DUCK.get(kind, 0)
        if depth:
            m = min(n - s, int(.6 * SR))
            tt = np.arange(m) / SR
            env = 1 - depth * np.minimum(1, tt / .008) * np.exp(-np.maximum(tt - .08, 0) / .18)
            duck[s:s + m] = np.minimum(duck[s:s + m], env)
    out = bed * duck[:, None] + fx
    out *= 10 ** ((LUFS - loudness(out)) / 20)
    return limit(out, .89)


def write_wav(samples: np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def soundtrack(comp, seed: int, path: Path) -> Path:
    """Write the mixed soundtrack for a composition and return its path. A comp
    with a `music` track (the edits, cc_edit.py) gets that track under its
    effects; every other comp gets the synthesized bed, exactly as before."""
    track = getattr(comp, "music", None)
    if track:
        return write_wav(mix_track(comp.duration, comp.cues, track, seed), path)
    return write_wav(mix(comp.duration, comp.cues, seed), path)


if __name__ == "__main__":
    import sys
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 20
    demo = [(i * 1.0, k) for i, k in enumerate(["whoosh", "slam", "tick", "pop", "reveal", "cash"] * 3)]
    print(write_wav(mix(dur, demo, 20260923), Path(sys.argv[2] if len(sys.argv) > 2 else "demo.wav")))
