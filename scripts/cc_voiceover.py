"""
A narrator over the edits: one line on each screen of a countdown edit
(cc_edit_countdown records when each screen runs, comp.timeline), mixed over
the edit's own track and effects. The owner picked voice #4, Michael (Kokoro
am_michael, Apache-2.0), on 2026-11-09 and asked for the sound of TikTok
voiceovers: quick, close and even, the music well under it, the lines
written the way people talk.

    narrate(comp, lines, voice="michael")   # lines: {"hook": ..., 5: ..., "build": ..., 1: ..., "outro": ..., "end": ...}
    cc_audio.soundtrack(comp, ...)          # mixes comp.voiceover in (voiced_mix)

Each line starts a beat after its screen's cut (LEAD) and has to end before
the next screen: one that runs long is said faster, up to MAX_SPEED, and a
line that still doesn't fit is an error, so nothing is ever talked over.
"end" goes on the end card, as BAD is typed in.

The voice: high-passed at 80 Hz, a little presence (+3 dB from 2.5 kHz) and
air, a gentle compressor so every word sits at the same level, at -14 LUFS.
The music and effects dip about 10 dB while it speaks, stay down through
the pauses between its sentences, and swell back smoothly between lines.

Posting a voiced video changes nothing about its labels: every platform's AI
flag stays off, as on every post (creator-code/RULES.md, "No made with AI
labels"; the owner, 2026-11-09: "never use it"). Michael is a generic voice,
not anyone's real one -- keep it that way: no cloned or real voices here.
"""

import numpy as np

from cc_common import log

VSR = 24000                 # Kokoro's rate
SPEED = 1.12                # TikTok-voiceover pace
MAX_SPEED = 1.32
LEAD = .22                  # after a screen's cut
GAP = .15                   # clear of the next screen
DUCK_DB = 10.0
DUCK_PRE = .12              # the music is already down when a line starts,
DUCK_HOLD = .6              # stays down through the pauses between sentences,
DUCK_ATTACK = .06
DUCK_RELEASE = .4           # and swells back smoothly between lines
VOICE_LUFS = -14.0


def _say(text: str, voice: str, speed: float) -> np.ndarray:
    import cc_ingame as G
    mix = G.VOICES.get(voice, {voice: 1.0})
    lang = "en-gb" if next(iter(mix)).startswith("b") else "en-us"
    audio, sr = G.engine().create(text, voice=G._style(voice), speed=speed, lang=lang)
    assert sr == VSR
    return audio.astype(np.float64)


def narrate(comp, lines: dict, voice: str = "michael", speed: float = SPEED) -> list:
    """Speak `lines` on the screens of `comp` (a countdown edit, end card
    added): comp.voiceover = [(start, samples)]. Returns [(key, start, seconds)]."""
    tl = dict(getattr(comp, "timeline", {}) or {})
    if not tl:
        raise ValueError("this edit doesn't record its screens (comp.timeline)")
    content_end = tl["outro"][1]
    if comp.duration > content_end + 1:                       # the end card (cc_end_card: from content_end - .3)
        tl["end"] = (content_end - .3 + .35, comp.duration)
    order = sorted(((k, se) for k, se in tl.items() if lines.get(k)), key=lambda kv: kv[1][0])
    out, said, long = [], [], []
    for i, (key, (a, b)) in enumerate(order):
        start = a + (LEAD if key != "end" else 0)
        stop = (order[i + 1][1][0] if i + 1 < len(order) else comp.duration) - GAP
        room = stop - start
        sp = speed
        audio = _say(lines[key], voice, sp)
        if len(audio) / VSR > room:
            sp = min(MAX_SPEED, speed * (len(audio) / VSR) / room * 1.03)
            audio = _say(lines[key], voice, sp)
        if len(audio) / VSR > room:
            long.append(f"the {key!r} line runs {len(audio) / VSR:.1f}s on a {room:.1f}s screen: {lines[key]!r}")
            continue
        out.append((start, audio))
        said.append((key, round(start, 2), round(len(audio) / VSR, 2)))
        log(f"  voice {key!s:>5} {start:6.2f}s {len(audio) / VSR:4.1f}s of {room:4.1f}s  x{sp:.2f}  {lines[key]}")
    if long:
        raise ValueError("; ".join(long))
    comp.voiceover = out
    return said


# ------------------------------------------------------------------ the sound

def _eq(x: np.ndarray, sr: int) -> np.ndarray:
    """High-pass at 80 Hz, +3 dB presence from 2.5 kHz, +1.5 dB air from 8 kHz (zero-phase)."""
    n = len(x)
    f = np.fft.rfftfreq(n, 1 / sr)
    hp = (f / 80) ** 4 / (1 + (f / 80) ** 4)
    shelf = lambda fc, db: 1 + (10 ** (db / 20) - 1) * ((f / fc) ** 2 / (1 + (f / fc) ** 2))   # noqa: E731
    return np.fft.irfft(np.fft.rfft(x) * hp * shelf(2500, 3) * shelf(8000, 1.5), n)


def _compress(x: np.ndarray, sr: int, ratio: float = 3.0, knee_db: float = -22.0) -> np.ndarray:
    """A gentle RMS compressor (5 ms blocks, 10 ms attack, 120 ms release)."""
    blk = int(.005 * sr)
    nb = -(-len(x) // blk)
    pad = np.zeros(nb * blk)
    pad[:len(x)] = x
    rms = np.sqrt((pad.reshape(nb, blk) ** 2).mean(axis=1) + 1e-12)
    peak = np.percentile(rms[rms > 1e-4], 95) if np.any(rms > 1e-4) else 1.0
    level = 20 * np.log10(rms / peak)
    over = np.maximum(0.0, level - knee_db)
    want = -over * (1 - 1 / ratio)                    # dB of gain
    a, r = 1 - np.exp(-blk / (.010 * sr)), 1 - np.exp(-blk / (.120 * sr))
    g, cur = np.empty(nb), 0.0
    for i in range(nb):
        cur += (want[i] - cur) * (a if want[i] < cur else r)
        g[i] = cur
    gain = np.repeat(10 ** (g / 20), blk)[:len(x)]
    return x * gain


def _resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    m = int(round(len(x) * sr_out / sr_in))
    spec = np.fft.rfft(x)
    out = np.zeros(m // 2 + 1, dtype=complex)
    k = min(len(spec), len(out))
    out[:k] = spec[:k]
    return np.fft.irfft(out, m) * (m / len(x))


def voiced_mix(comp, seed: int) -> np.ndarray:
    """The edit's track and effects (cc_audio.mix_track), dipping under the
    voice, and the voice on top; the whole at the edits' loudness."""
    import cc_audio as A
    n = int(comp.duration * A.SR)
    bed = A.mix_track(comp.duration, comp.cues, comp.music, seed)[:n]
    if len(bed) < n:
        bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    v24 = np.zeros(int(comp.duration * VSR) + VSR)
    for start, audio in comp.voiceover:
        a = int(start * VSR)
        seg = audio[:max(0, len(v24) - a)]
        v24[a:a + len(seg)] += seg
    v24 = _compress(_eq(v24, VSR), VSR)
    voice = _resample(v24, VSR, A.SR)[:n]
    if len(voice) < n:
        voice = np.pad(voice, (0, n - len(voice)))
    voice *= 10 ** ((VOICE_LUFS - A.loudness(voice)) / 20)
    out = bed * _duck(voice, A.SR)[:, None] * 10 ** (-2 / 20) + voice[:, None]
    out *= 10 ** ((A.LUFS - A.loudness(out)) / 20)
    return A.limit(out, .84)


def _duck(voice: np.ndarray, sr: int, fr: int = 100) -> np.ndarray:
    """The music's gain under `voice`: down DUCK_DB from DUCK_PRE before each
    line, held through pauses shorter than DUCK_HOLD (the ones between
    sentences), back up over DUCK_RELEASE once a line is done -- a ducker,
    worked out on a 10 ms grid."""
    hop = sr // fr
    nf = -(-len(voice) // hop)
    pad = np.zeros(nf * hop)
    pad[:len(voice)] = voice
    on = np.sqrt((pad.reshape(nf, hop) ** 2).mean(axis=1)) > 10 ** (-45 / 20)
    pre, hold = int(DUCK_PRE * fr), int(DUCK_HOLD * fr)
    # ducked at frame i when the voice speaks anywhere in [i - hold, i + pre]
    near = np.convolve(on.astype(float), np.ones(hold + pre + 1))[pre:pre + nf] > 0
    first = np.argmax(on) if on.any() else nf
    if first < .5 * fr:                       # a line right at the start: down from frame 0
        near[:first] = True
    target = np.where(near, -DUCK_DB, 0.0)
    att, rel = 1 - np.exp(-1 / (DUCK_ATTACK * fr)), 1 - np.exp(-1 / (DUCK_RELEASE * fr))
    db, cur = np.empty(nf), target[0]
    for i in range(nf):
        cur += (target[i] - cur) * (att if target[i] < cur else rel)
        db[i] = cur
    return np.interp(np.arange(len(voice)) / sr, (np.arange(nf) + .5) / fr, 10 ** (db / 20))
