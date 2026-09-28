"""
What the builds need beyond what the nightly workflows install (ffmpeg,
Chromium, numpy): installed at the start of a build, so the workflow files
never have to change for it.

  ensure_emoji_font()   the edits' captions use emojis, as people's do: the
                        system's Noto Color Emoji (fonts-noto-color-emoji)
  ensure_tts()          the long videos' narration: kokoro-onnx + soundfile
                        (free, open source; the voice model is fetched by
                        cc_voice on first use)
  ensure_pillow()       the long videos' thumbnail and QA sheet

Both do nothing when what they install is already there, and never fail a
build by themselves: a missing emoji font is caught by the caller's check.
"""

import importlib.util
import subprocess
import sys

from cc_common import log


def _fonts() -> str:
    try:
        return subprocess.run(["fc-list"], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def has_emoji_font() -> bool:
    return "Noto Color Emoji" in _fonts()


def ensure_emoji_font() -> bool:
    if has_emoji_font():
        return True
    log("Installing the emoji font (fonts-noto-color-emoji)")
    for cmd in (["sudo", "-n", "apt-get", "install", "-y", "-qq", "fonts-noto-color-emoji"],
                ["sudo", "-n", "sh", "-c", "apt-get update -qq && apt-get install -y -qq fonts-noto-color-emoji"]):
        try:
            subprocess.run(cmd, check=False, timeout=600)
        except (OSError, subprocess.SubprocessError) as e:
            log(f"  {e!r}")
        if has_emoji_font():
            return True
    log("  the emoji font is still missing")
    return False


def ensure_pip(modules: dict) -> bool:
    """{import name: pip package}: installs whatever isn't importable."""
    missing = [pkg for mod, pkg in modules.items() if not importlib.util.find_spec(mod)]
    if not missing:
        return True
    log(f"Installing {', '.join(missing)}")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", *missing], check=False, timeout=900)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"  {e!r}")
    importlib.invalidate_caches()
    return all(importlib.util.find_spec(mod) for mod in modules)


def ensure_tts() -> bool:
    return ensure_pip({"kokoro_onnx": "kokoro-onnx", "soundfile": "soundfile"})


def ensure_pillow() -> bool:
    """The long videos' thumbnail and QA sheet."""
    return ensure_pip({"PIL": "pillow"})
