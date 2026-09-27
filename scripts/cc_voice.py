"""
Narration for the long videos: free, open-source text-to-speech running on the
CPU -- Kokoro-82M (Apache-2.0) through kokoro-onnx (MIT). No account, key or paid
service. The model files come from kokoro-onnx's GitHub release and are cached
under out/_voice/. About 0.3x real time on one CPU: a 10-minute script takes ~3.

    pip install kokoro-onnx soundfile

say(lines) turns a list of lines into WAV files and their lengths; the long-video
builder (cc_long.py) times every scene to the line it goes with.
"""

import hashlib
import urllib.request
import wave
from pathlib import Path

import numpy as np

from cc_common import OUT_DIR, log

RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
MODEL, VOICES = "kokoro-v1.0.onnx", "voices-v1.0.bin"
CACHE = OUT_DIR / "_voice"
SR = 24000
VOICE = "am_michael"        # the owner picks; see LONG_VIDEOS.md
SPEED = 1.05

_engine = None


def _fetch(name: str) -> Path:
    path = CACHE / name
    if not path.exists() or path.stat().st_size < 1_000_000:
        CACHE.mkdir(parents=True, exist_ok=True)
        log(f"Downloading {RELEASE + name}")
        with urllib.request.urlopen(RELEASE + name, timeout=600) as resp:
            path.write_bytes(resp.read())
    return path


def engine():
    global _engine
    if _engine is None:
        from kokoro_onnx import Kokoro
        _engine = Kokoro(str(_fetch(MODEL)), str(_fetch(VOICES)))
    return _engine


def _write(path: Path, samples: np.ndarray, sr: int):
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def say(lines: list, out_dir: Path, voice: str = VOICE, speed: float = SPEED) -> list:
    """Each line -> (wav path, seconds). Lines already spoken with the same voice
    and speed are reused from out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for text in lines:
        key = hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16]
        path = out_dir / f"line-{key}.wav"
        if not path.exists():
            lang = "en-gb" if voice.startswith("b") else "en-us"
            samples, sr = engine().create(text, voice=voice, speed=speed, lang=lang)
            _write(path, samples, sr)
        with wave.open(str(path)) as w:
            result.append((path, w.getnframes() / w.getframerate()))
    return result


def read(path: Path) -> tuple:
    """(mono float samples, sample rate) of a narration WAV."""
    with wave.open(str(path)) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32767
        return data, w.getframerate()
