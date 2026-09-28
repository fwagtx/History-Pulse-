#!/usr/bin/env python3
"""
Real music for the videos: tracks made by people and dedicated to the public
domain (CC0 1.0 -- free for any use, commercial included, no credit needed),
instead of the synthesized bed in cc_audio.music().

The sources can't be reached from every machine, so a GitHub runner builds the
library once and publishes it as the "music-library" release; renders fetch it
from there.

    python3 scripts/cc_music.py build --out DIR    # runner: search, download, measure, cut
    python3 scripts/cc_music.py fetch              # the library from the release (cached)
    python3 scripts/cc_music.py list               # what's in it

build: every archive.org upload by the ARTISTS below whose licence is CC0 is a
candidate. Each track is decoded with ffmpeg and measured with numpy -- tempo
and beat grid (onset autocorrelation), loudness, how busy it is -- and its
strongest 75 seconds, starting on a beat, is kept as a 192 kbps mp3. The
catalog (catalog.json) records the source, licence, tempo, the beat times
inside the cut, and a mood from the measurements ("hype", "drive", "chill").

A video picks a track with pick(mood, seed) when it's built, so its cuts can
land on that track's beats; cc_audio mixes the same track under the effects.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cc_common import OUT_DIR, log  # noqa: E402

REPO = "fwagtx/History-Pulse-"
TAG = "music-library"
CACHE = OUT_DIR / "_music"
ARTISTS = ["Loyalty Freak Music", "HoliznaCC0", "Juhani Junkala", "Komiku", "Monplaisir"]
CC0 = "publicdomain/zero"
SR = 22050                   # analysis rate
CUT = 75.0                   # seconds kept per track (a video is 62-90 s with the end card)
UA = {"User-Agent": "usecodebad-music/1.0 (+https://github.com/fwagtx/History-Pulse-)"}


# ------------------------------------------------------------------ fetch helpers

def _get(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def _json(url: str) -> dict:
    return json.loads(_get(url).decode("utf-8"))


def archive_items(artist: str) -> list:
    """[(identifier, title, licenseurl)] of the artist's audio uploads on archive.org."""
    q = f'creator:("{artist}") AND mediatype:(audio)'
    url = ("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        {"q": q, "fl[]": ["identifier", "title", "licenseurl"], "rows": 400, "output": "json"}, doseq=True))
    docs = _json(url).get("response", {}).get("docs", [])
    return [(d["identifier"], d.get("title") or d["identifier"], d.get("licenseurl") or "") for d in docs]


def archive_tracks(identifier: str) -> list:
    """[(file name, title, length s)] of an item's mp3s (one per track)."""
    meta = _json(f"https://archive.org/metadata/{identifier}")
    files = meta.get("files", [])
    mp3 = [f for f in files if f.get("name", "").lower().endswith(".mp3") and "_64kb" not in f["name"]
           and "sample" not in f["name"].lower()]
    # Prefer the originals over archive.org's derivatives of the same track.
    orig = [f for f in mp3 if f.get("source") == "original"] or mp3
    out = []
    for f in orig:
        try:
            length = float(f.get("length") or 0)
        except ValueError:                        # "3:25"
            parts = [float(x) for x in str(f.get("length")).split(":") if x]
            length = sum(p * 60 ** i for i, p in enumerate(reversed(parts)))
        out.append((f["name"], f.get("title") or Path(f["name"]).stem, length))
    return out


# ------------------------------------------------------------------ measuring

def decode(path: Path, sr: int = SR) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def onset_envelope(x: np.ndarray, sr: int = SR, n_fft: int = 1024, hop: int = 512) -> tuple:
    """Spectral flux (log magnitude, positive differences) per frame; frame rate."""
    if len(x) < n_fft * 2:
        return np.zeros(1), sr / hop
    win = np.hanning(n_fft).astype(np.float32)
    frames = np.lib.stride_tricks.sliding_window_view(x, n_fft)[::hop] * win
    mag = np.log1p(10 * np.abs(np.fft.rfft(frames, axis=1)))
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux -= np.convolve(flux, np.ones(16) / 16, mode="same")        # local mean removed
    return np.maximum(flux, 0), sr / hop


def tempo_and_beats(env: np.ndarray, fps: float) -> tuple:
    """(bpm, beat times s): the autocorrelation peak between 70 and 180 BPM
    (weighted toward 120), then the phase whose beats sit on the most onset energy."""
    if env.size < fps * 8:
        return 0.0, []
    e = env - env.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    lags = np.arange(len(ac))
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 70)
    bpms = 60 * fps / np.maximum(lags[lo:hi], 1)
    weight = np.exp(-0.5 * (np.log2(bpms / 120) / 0.9) ** 2)
    best = lo + int(np.argmax(ac[lo:hi] * weight))
    period = best
    # refine the period to sub-frame precision with a parabola
    if 1 <= best < len(ac) - 1:
        a, b, c = ac[best - 1], ac[best], ac[best + 1]
        denom = a - 2 * b + c
        period = best + (0.5 * (a - c) / denom if denom else 0)
    # Fine-tune the period against the whole track: the comb of beats that sits
    # on the most onset energy, over periods within 3% and every phase.
    def comb(per):
        ph = np.arange(0, per, .5)
        best_s, best_p = -1.0, 0.0
        for p0 in ph:
            idx = np.minimum(np.round(np.arange(p0, len(env), per)).astype(int), len(env) - 1)
            sc = env[idx].sum() / max(1, len(idx))
            if sc > best_s:
                best_s, best_p = sc, p0
        return best_s, best_p
    cands = np.linspace(period * .97, period * 1.03, 49)
    scores = [comb(c) for c in cands]
    k = int(np.argmax([sc for sc, _ in scores]))
    period, phase = float(cands[k]), scores[k][1]
    bpm = 60 * fps / period
    beats = []
    t = phase
    while t < len(env):
        i = int(round(t))
        lo_i, hi_i = max(0, i - 2), min(len(env), i + 3)
        j = lo_i + int(np.argmax(env[lo_i:hi_i]))          # snap to the local onset peak
        beats.append(j / fps)
        # follow the music when the snap is on a real onset; otherwise keep the grid
        t = (j if env[j] > env.mean() else t) + period
    return float(bpm), beats


def measure(path: Path) -> dict:
    x = decode(path)
    dur = len(x) / SR
    env, fps = onset_envelope(x)
    bpm, beats = tempo_and_beats(env, fps)
    # loudness per second, and the loudest CUT-second window starting on a beat
    sec = np.sqrt(np.convolve(x ** 2, np.ones(SR) / SR, mode="valid")[::SR // 2] + 1e-12)   # every .5 s
    win = int(CUT * 2)
    if len(sec) > win:
        csum = np.cumsum(np.concatenate([[0], sec]))
        means = (csum[win:] - csum[:-win]) / win
        start = float(np.argmax(means)) / 2
    else:
        start = 0.0
    if beats:
        start = min((b for b in beats if b >= start - 0.01), default=start)
    start = max(0.0, min(start, max(0.0, dur - CUT)))
    end = min(dur, start + CUT)
    seg = x[int(start * SR):int(end * SR)]
    rms = float(np.sqrt(np.mean(seg ** 2) + 1e-12))
    e = env[int(start * fps):int(end * fps)]
    density = float((e > env.mean() + env.std()).mean()) if e.size else 0.0
    # How hard the beat hits: onset strength on the beats against the average.
    on = [e[max(0, int(round((b - start) * fps)) - 1):int(round((b - start) * fps)) + 2].max()
          for b in beats if start <= b < end and int(round((b - start) * fps)) + 2 <= len(e)]
    salience = float(np.mean(on) / (e.mean() + 1e-9)) if on and e.size else 0.0
    # How much of it is bass and kick (below 150 Hz).
    spec = np.abs(np.fft.rfft(seg[: SR * 60])) ** 2 if len(seg) else np.zeros(2)
    f = np.fft.rfftfreq(min(len(seg), SR * 60), 1 / SR)
    low = float(spec[f < 150].sum() / (spec.sum() + 1e-12))
    return {"duration": round(dur, 2), "bpm": round(bpm, 2), "start": round(start, 3), "cut": round(end - start, 2),
            "rms": round(rms, 4), "density": round(density, 4), "salience": round(salience, 3),
            "flux": round(float(e.mean()) if e.size else 0.0, 3), "low": round(low, 4),
            "beats": [round(b - start, 3) for b in beats if start <= b < end]}


SEASONS = {
    "winter": ("holiday", "christmas", "xmas", "winter", "jingle", "carol", "snow", "santa", "noel"),
    "halloween": ("halloween", "hallowe", "spooky", "witch", "ghost", "graveyard", "monster", "batty", "zombie",
                  "haunt"),
}
IN_SEASON = {"winter": (12,), "halloween": (10,)}


def season(album: str, title: str) -> str:
    """"winter" or "halloween" for a seasonal track (by its album or title), else ""."""
    text = f"{album} {title}".lower()
    for name, words in SEASONS.items():
        if any(w in text for w in words):
            return name
    return ""


def moods(tracks: list) -> None:
    """Sort the library into "hype" (the most energetic third: loud, a beat
    that hits hard, busy, with bass), "chill" (the calmest quarter) and
    "drive" (the rest), relative to each other; sets t["energy"] and t["mood"]."""
    if not tracks:
        return
    def z(key):
        v = np.array([float(t.get(key, 0)) for t in tracks])
        return (v - v.mean()) / (v.std() + 1e-9)
    score = z("rms") + z("salience") + .5 * z("flux") + .3 * z("low")
    order = np.argsort(-score)
    n = len(tracks)
    for rank, i in enumerate(order):
        t = tracks[i]
        t["energy"] = round(float(score[i]), 3)
        t["mood"] = "hype" if rank < n * .34 else ("chill" if rank >= n * .75 else "drive")


# ------------------------------------------------------------------ build (runner)

def build(out: Path, per_item: int = 4, per_artist: int = 30, limit: int = 150):
    """Every artist's CC0 uploads, up to `per_item` tracks an album and
    `per_artist` an artist, so no one sound fills the library."""
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "_raw"
    raw_dir.mkdir(exist_ok=True)
    catalog, seen = [], set()
    for artist in ARTISTS:
        try:
            items = archive_items(artist)
        except Exception as e:  # noqa: BLE001
            log(f"{artist}: search failed ({e!r})")
            continue
        cc0 = [it for it in items if CC0 in (it[2] or "")]
        log(f"{artist}: {len(items)} uploads, {len(cc0)} CC0")
        mine = 0
        for ident, album, lic in cc0:
            if len(catalog) >= limit or mine >= per_artist:
                break
            try:
                tracks = archive_tracks(ident)
            except Exception as e:  # noqa: BLE001
                log(f"  {ident}: metadata failed ({e!r})")
                continue
            tracks = [t for t in tracks if 60 <= t[2] <= 600][:per_item]
            for name, title, length in tracks:
                key = (artist, title.lower())
                if key in seen or len(catalog) >= limit or mine >= per_artist:
                    continue
                seen.add(key)
                src = f"https://archive.org/download/{ident}/{urllib.parse.quote(name)}"
                slug = re.sub(r"[^a-z0-9]+", "-", f"{artist}-{title}".lower()).strip("-")[:70]
                raw = raw_dir / f"{slug}.mp3"
                try:
                    raw.write_bytes(_get(src, timeout=120))
                    m = measure(raw)
                except Exception as e:  # noqa: BLE001
                    log(f"  {title}: skipped ({e!r})")
                    raw.unlink(missing_ok=True)
                    continue
                if not m["bpm"] or len(m["beats"]) < 40:
                    log(f"  {title}: no steady beat, skipped")
                    raw.unlink(missing_ok=True)
                    continue
                cut = out / f"{slug}.mp3"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(m["start"]), "-t", str(m["cut"]),
                                "-i", str(raw), "-ac", "2", "-ar", "44100", "-b:a", "192k",
                                "-af", "afade=t=in:d=0.02", str(cut)], check=True)
                raw.unlink(missing_ok=True)
                entry = {"id": slug, "file": cut.name, "artist": artist, "album": album, "title": title,
                         "license": lic, "source": src, "page": f"https://archive.org/details/{ident}",
                         "season": season(album, title), **m}
                catalog.append(entry)
                mine += 1
                log(f"  + {artist} — {title}: {m['bpm']:.0f} bpm, rms {m['rms']:.3f}, salience {m['salience']:.2f}, "
                    f"low {m['low']:.2f}{' [' + entry['season'] + ']' if entry['season'] else ''}")
    moods(catalog)
    (out / "catalog.json").write_text(json.dumps({"tracks": catalog}, indent=1, ensure_ascii=False))
    for f in raw_dir.glob("*"):
        f.unlink()
    raw_dir.rmdir()
    by = {}
    for t in catalog:
        by.setdefault(t["artist"], []).append(t["mood"])
    log(f"music library: {len(catalog)} tracks " + ", ".join(
        f"{a}: {len(m)} ({m.count('hype')} hype)" for a, m in by.items()))
    return catalog


# ------------------------------------------------------------------ use (renders)

def catalog(dest: Path = CACHE, max_age: float = 6 * 3600) -> list:
    """The library's catalog, downloaded at most every `max_age` seconds. Each
    catalog's tracks are cached in their own folder (its "_dir"), so a rebuilt
    library never mixes with an older one's files."""
    import hashlib
    import time
    dest.mkdir(parents=True, exist_ok=True)
    cat = dest / "catalog.json"
    if not cat.exists() or time.time() - cat.stat().st_mtime > max_age:
        cat.write_bytes(_get(f"https://github.com/{REPO}/releases/download/{TAG}/catalog.json"))
    raw = cat.read_bytes()
    folder = str(dest / hashlib.sha1(raw).hexdigest()[:10])
    return [dict(t, _dir=folder) for t in json.loads(raw.decode("utf-8"))["tracks"]]


def ensure(t: dict, dest: Path | None = None) -> dict | None:
    """The track with its mp3 on disk ("path"), or None when it can't be had."""
    dest = Path(t.get("_dir") or dest or CACHE)
    dest.mkdir(parents=True, exist_ok=True)
    f = dest / t["file"]
    if not f.exists():
        try:
            f.write_bytes(_get(f"https://github.com/{REPO}/releases/download/{TAG}/{t['file']}", timeout=120))
        except Exception as e:  # noqa: BLE001
            log(f"music: {t['file']} unavailable ({e!r})")
            return None
    return dict(t, path=str(f))


def fetch(dest: Path = CACHE) -> list:
    """Every track, downloaded."""
    return [x for x in (ensure(t) for t in catalog(dest)) if x]


_LIB = None


def library() -> list:
    """The catalog, or [] where it can't be had (the edits then use the
    synthesized bed). CC_MUSIC=0 turns the library off."""
    global _LIB
    if _LIB is None:
        if os.environ.get("CC_MUSIC", "1") == "0":
            _LIB = []
        else:
            try:
                _LIB = catalog()
            except Exception as e:  # noqa: BLE001
                log(f"music library unavailable ({e!r}); using the synthesized bed")
                _LIB = []
    return _LIB


def pick(mood_: str = "hype", seed: int = 0, want: str = "", avoid: tuple = (), day=None) -> dict | None:
    """A track for a video, downloaded: `want` (an id) if given, else one of the
    mood's, chosen by seed (not one in `avoid` while there are others). A
    seasonal track (Christmas, Halloween) only plays in its month (`day`)."""
    lib = library()
    if not lib:
        return None
    if want:
        hit = [t for t in lib if t["id"] == want]
        if hit and ensure(hit[0]):
            return ensure(hit[0])
    month = day.month if day else 0
    lib = [t for t in lib if not t.get("season") or month in IN_SEASON.get(t["season"], ())] or lib
    pool = [t for t in lib if t["mood"] == mood_] or [t for t in lib if t["mood"] != "chill"] or lib
    pool = sorted(pool, key=lambda t: t["id"])
    fresh = [t for t in pool if t["id"] not in avoid] or pool
    for k in range(len(fresh)):
        got = ensure(fresh[(seed + k) % len(fresh)])
        if got:
            return got
    return None


def downbeat(t: dict) -> int:
    """Which of the track's first four beats starts a bar: the phase (beat
    number mod 4) whose beats carry the most low-end onset energy -- the kick
    drum. 0 when it can't be measured."""
    beats = t.get("beats") or []
    if len(beats) < 16 or not t.get("path"):
        return 0
    try:
        x = decode(Path(t["path"]))
    except Exception:  # noqa: BLE001
        return 0
    n_fft, hop = 2048, 512
    if len(x) < n_fft * 4:
        return 0
    frames = np.lib.stride_tricks.sliding_window_view(x, n_fft)[::hop] * np.hanning(n_fft).astype(np.float32)
    f = np.fft.rfftfreq(n_fft, 1 / SR)
    low = np.log1p(10 * np.abs(np.fft.rfft(frames, axis=1))[:, (f >= 30) & (f <= 160)]).sum(axis=1)
    flux = np.maximum(0, np.diff(low, prepend=low[0]))
    idx = np.minimum(np.round(np.array(beats) * SR / hop).astype(int), len(flux) - 1)
    vals = np.array([flux[max(0, i - 2):i + 3].max() for i in idx])
    return int(np.argmax([vals[k::4].mean() for k in range(4)]))


def extend(beats: list, cut: float, duration: float) -> list:
    """How a cut of `cut` seconds lies under a video of `duration` seconds:
    [(at, from, length)] -- the cut as it is up to its last beat, then its last
    four bars (16 beats) again and again, joined on the beat. A cut too short
    to know its bars is looped whole."""
    if duration <= cut:
        return [(0.0, 0.0, duration)]
    if len(beats) < 17:
        return [(k * cut, 0.0, cut) for k in range(int(duration // cut) + 1)]
    a, e = beats[-17], beats[-1]
    segs, at = [(0.0, 0.0, e)], e
    while at < duration:
        segs.append((at, a, e - a))
        at += e - a
    return segs


def beat_grid(beats: list, cut: float, duration: float) -> list:
    """The beat times under a video of `duration` seconds, as extend() lays the cut."""
    out = []
    for at, frm, length in extend(beats, cut, duration):
        out += [at + b - frm for b in beats if frm <= b < frm + length - 1e-6 and at + b - frm < duration]
    return sorted(set(round(b, 4) for b in out))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", default=str(OUT_DIR / "music-library"))
    b.add_argument("--limit", type=int, default=150)
    b.add_argument("--per-artist", type=int, default=30)
    sub.add_parser("fetch")
    sub.add_parser("list")
    a = ap.parse_args()
    if a.cmd == "build":
        build(Path(a.out), per_artist=a.per_artist, limit=a.limit)
    elif a.cmd == "fetch":
        print(len(fetch()), "tracks in", CACHE)
    else:
        for t in library():
            print(f"{t['mood']:6} {t['bpm']:6.1f} bpm  rms {t['rms']:.3f}  {t['artist']} — {t['title']}"
                  f"{'  [' + t['season'] + ']' if t.get('season') else ''}")


if __name__ == "__main__":
    main()
