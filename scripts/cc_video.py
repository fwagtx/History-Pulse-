"""
Turn assets into TikTok-ready 1080x1920 MP4s.

Two modes:

  Shop video   python3 scripts/cc_video.py
               Today's shop card -> ~18s slow-zoom clip.

  Gameplay     python3 scripts/cc_video.py --clip raw.mp4
               Your gameplay clip, normalized to 1080x1920, with the branded
               BAD end card appended.

Add --dry-run to print the ffmpeg command without running it.

Output goes to `video_out_dir` from config (point that at a synced Google Drive /
Dropbox / iCloud folder and finished videos land on your phone automatically).

Needs a standard ffmpeg with libx264 + the zoompan filter — that is what apt/brew
install. The preflight below checks and tells you exactly what's missing.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from cc_common import OUT_DIR, log, load_config, read_json, today_stamp

FFMPEG_CANDIDATES = ("ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg",
                     "/opt/homebrew/bin/ffmpeg")

W, H = 1080, 1920
SHOP_SECONDS = 18
ENDCARD_SECONDS = 3
FPS = 30
ZOOM_TO = 1.15


def find_ffmpeg(cfg: dict) -> str | None:
    configured = cfg.get("ffmpeg_path", "")
    if configured and Path(configured).exists():
        return configured
    for c in FFMPEG_CANDIDATES:
        found = shutil.which(c)
        if found:
            return found
    return None


def preflight(binary: str) -> list[str]:
    """Return a list of missing capabilities. Empty list means good to go."""
    missing = []
    try:
        encoders = subprocess.run([binary, "-hide_banner", "-encoders"],
                                  capture_output=True, text=True, timeout=30).stdout
        filters = subprocess.run([binary, "-hide_banner", "-filters"],
                                 capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        return [f"could not run ffmpeg ({e})"]
    if "libx264" not in encoders:
        missing.append("libx264 encoder (H.264 video)")
    if " aac " not in encoders:
        missing.append("aac encoder (audio track)")
    if "zoompan" not in filters:
        missing.append("zoompan filter (the slow-zoom effect)")
    return missing


def shop_command(binary: str, card: Path, out: Path) -> list[str]:
    frames = SHOP_SECONDS * FPS
    # Pre-scale 2x so the zoom crops into real pixels instead of upscaling mush.
    # Driving z off the output frame number (`on`) with d=1 is the reliable idiom
    # for a smooth continuous zoom over a single still image.
    step = (ZOOM_TO - 1.0) / frames
    vf = (f"scale={W*2}:{H*2},"
          f"zoompan=z='min(1+{step:.6f}*on,{ZOOM_TO})'"
          f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d=1:s={W}x{H}:fps={FPS},"
          f"format=yuv420p")
    return [
        binary, "-y",
        "-loop", "1", "-framerate", str(FPS), "-t", str(SHOP_SECONDS), "-i", str(card),
        # Silent track: TikTok handles mute uploads, but a well-formed audio stream
        # avoids odd behaviour in some uploaders, and you'll add sound in-app anyway.
        "-f", "lavfi", "-t", str(SHOP_SECONDS),
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-shortest",
        "-movflags", "+faststart",
        str(out),
    ]


def clip_command(binary: str, clip: Path, card: Path, out: Path) -> list[str]:
    # Scale-then-crop keeps the gameplay full-bleed at 9:16 instead of pillarboxing it.
    fc = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,fps={FPS}[v0];"
        f"[1:v]scale={W}:{H},setsar=1,fps={FPS}[v1];"
        f"[v0][v1]concat=n=2:v=1:a=0[outv]"
    )
    return [
        binary, "-y",
        "-i", str(clip),
        "-loop", "1", "-t", str(ENDCARD_SECONDS), "-i", str(card),
        "-filter_complex", fc,
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out),
    ]


def run(cmd: list[str], dry: bool) -> bool:
    if dry:
        print(" ".join(f"'{c}'" if " " in c else c for c in cmd))
        return True
    log("Encoding (this takes a few seconds)...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        log(f"ffmpeg failed:\n{result.stderr[-2000:]}")
        return False
    return True


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    stamp = args[args.index("--date") + 1] if "--date" in args else today_stamp()
    clip = args[args.index("--clip") + 1] if "--clip" in args else None

    cfg = load_config()
    binary = find_ffmpeg(cfg)
    if not binary:
        log("ERROR: ffmpeg not found. Install it (free):")
        log("  macOS:  brew install ffmpeg")
        log("  Ubuntu: sudo apt install ffmpeg")
        log("  Or set \"ffmpeg_path\" in creator-code/config.json")
        sys.exit(1)
    log(f"Using ffmpeg: {binary}")

    if not dry:
        missing = preflight(binary)
        if missing:
            log("ERROR: this ffmpeg build is missing:")
            for m in missing:
                log(f"  - {m}")
            log("Install a standard build (brew/apt) rather than a minimal one.")
            sys.exit(1)

    card = OUT_DIR / stamp / "card.png"
    if not card.exists():
        log(f"ERROR: no card.png for {stamp}. Run: python3 scripts/cc_daily.py --png")
        sys.exit(1)

    out_dir = Path(cfg.get("video_out_dir") or (OUT_DIR / stamp))
    out_dir.mkdir(parents=True, exist_ok=True)

    if clip:
        clip_path = Path(clip)
        if not clip_path.exists():
            log(f"ERROR: clip not found: {clip_path}")
            sys.exit(1)
        out = out_dir / f"bad-gameplay-{stamp}.mp4"
        ok = run(clip_command(binary, clip_path, card, out), dry)
    else:
        out = out_dir / f"bad-shop-{stamp}.mp4"
        ok = run(shop_command(binary, card, out), dry)

    if not ok:
        sys.exit(1)
    if dry:
        log("(dry run — nothing written)")
        return

    size = out.stat().st_size / 1024 / 1024
    log(f"Wrote {out} ({size:.1f} MB)")
    log("It'll sync to your phone if video_out_dir is a cloud-synced folder.")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
