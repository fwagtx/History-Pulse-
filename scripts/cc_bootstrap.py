"""
What the builds need, installed on the machine that runs them.

  ensure_build_tools()  everything the nightly build needs in a fresh Claude
                        workspace (what GitHub's workflow steps used to set
                        up): creator-code/config.json, numpy, Pillow,
                        Playwright (Chromium comes with the workspace), ffmpeg
                        (imageio-ffmpeg's build), then a test launch of
                        Chromium and a test H.264 encode. Returns what's
                        still wrong, in plain words ([] = ready)

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
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from cc_common import CC_DIR, log


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


def ensure_config() -> None:
    """creator-code/config.json (not in git): the example's, with no keys, as
    the GitHub workflow wrote it. The shop comes from the keyless mirror."""
    cfg = CC_DIR / "config.json"
    if cfg.exists():
        return
    d = json.loads((CC_DIR / "config.example.json").read_text())
    d.update(fortnite_api_key=os.environ.get("FORTNITE_API_KEY", ""), telegram_bot_token="",
             telegram_chat_id="", video_out_dir="")
    cfg.write_text(json.dumps(d, indent=2))
    log("Wrote creator-code/config.json")


def ensure_ffmpeg() -> bool:
    """ffmpeg on the PATH: the system's, else imageio-ffmpeg's static build
    (from PyPI, with H.264 and AAC) linked in as `ffmpeg`."""
    if shutil.which("ffmpeg"):
        return True
    if not ensure_pip({"imageio_ffmpeg": "imageio-ffmpeg"}):
        return False
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    for d in ("/usr/local/bin", str(Path.home() / ".local" / "bin")):
        try:
            Path(d).mkdir(parents=True, exist_ok=True)
            if not os.path.lexists(os.path.join(d, "ffmpeg")):
                os.symlink(exe, os.path.join(d, "ffmpeg"))
        except OSError:
            continue
        if d not in os.environ.get("PATH", "").split(os.pathsep):  # the builds inherit it
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
        if shutil.which("ffmpeg"):
            log(f"ffmpeg: {exe}")
            return True
    return False


def ensure_build_tools() -> list:
    """What a fresh workspace needs for the nightly build ([] = ready)."""
    problems = []
    ensure_config()
    if not ensure_pip({"numpy": "numpy", "PIL": "pillow", "playwright": "playwright==1.56.0"}):
        problems.append("couldn't install numpy, Pillow or Playwright from PyPI")
    if not ensure_ffmpeg():
        problems.append("couldn't install ffmpeg")
    else:
        with tempfile.TemporaryDirectory() as t:
            r = subprocess.run([shutil.which("ffmpeg"), "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10",
                                "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", f"{t}/t.mp4"],
                               capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                problems.append(f"ffmpeg can't encode H.264: {r.stderr.strip()[-200:]}")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(args=["--no-sandbox"]).close()
    except Exception as e:  # noqa: BLE001
        problems.append(f"Chromium won't start: {e!r}"[:240])
    return problems

