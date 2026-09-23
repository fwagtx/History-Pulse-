"""
The YouTube channel banner for @usecodebad.

    python3 scripts/cc_banner.py

Writes two colourways to creator-code/brand/, each 2560x1440 and under 6MB:
  youtube-banner-black.jpg   white and lime on black, like the videos
  youtube-banner-lime.jpg    black on the lime of the CODE BAD sticker

On purpose it is only words on a flat colour: glow, light rays, confetti and
drop shadows are what make a banner look auto-generated.

YouTube shows a different slice of one banner on each device: a TV shows all of
it, a computer a full-width 2560x423 strip through the middle, a phone only the
1546x423 box in the centre. Everything sits in that centre box, and the render
stops with an error if anything spills out of it.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cc_common import CC_DIR, log  # noqa: E402
from cc_motion import ACCENT, CHROME_ARGS, INK, READY_JS, _font_face, find_ffmpeg  # noqa: E402

OUT = CC_DIR / "brand"
BW, BH = 2560, 1440                              # YouTube's recommended upload size
SAFE_W, SAFE_H = 1546, 423                       # shown on every device, phones included
SX, SY = (BW - SAFE_W) / 2, (BH - SAFE_H) / 2    # 507, 508.5
INSET = 14                                       # breathing room inside the safe box
MAX_BYTES = 6 * 1024 * 1024

# name: (background, "USE CODE", "BAD", small line)
THEMES = {
    "black": (INK, "#FFFFFF", ACCENT, "#8A8F98"),
    "lime": (ACCENT, INK, INK, "rgba(10,10,11,.72)"),
}

FONTS = _font_face("Anton", "Anton-Regular.ttf", "400") + _font_face("Inter", "Inter-Variable.ttf", "100 900")


def banner_html(bg: str, fg: str, code: str, small: str) -> str:
    css = (f"{FONTS}*{{margin:0;padding:0;box-sizing:border-box}}"
           f"html,body{{width:{BW}px;height:{BH}px;overflow:hidden;background:{bg};"
           f"-webkit-font-smoothing:antialiased}}"
           f".wrap{{position:absolute;left:0;top:0;width:{BW}px;height:{BH}px;display:flex;"
           f"align-items:center;justify-content:center}}"
           f".head{{font-family:Anton;font-size:250px;line-height:.9;letter-spacing:.01em;color:{fg};"
           f"white-space:nowrap}}.head span{{color:{code}}}"
           f".row{{display:flex;justify-content:space-between;margin-top:30px;font-family:Inter;"
           f"font-size:33px;color:{small};white-space:nowrap}}"
           f".row b{{font-weight:800;letter-spacing:.24em}}.row i{{font-style:normal;font-weight:700}}")
    return (f"<html><head><meta charset='utf-8'><style>{css}</style></head><body><div class='wrap'><div>"
            f"<div class='head' data-check>USE CODE <span>BAD</span></div>"
            f"<div class='row' data-check><b>FORTNITE ITEM SHOP, EVERY DAY</b><i>#EpicPartner</i></div>"
            f"</div></div></body></html>")


CHECK_JS = """() => [...document.querySelectorAll('[data-check]')].map(e => {
  const r = e.getBoundingClientRect();
  return {text: e.textContent.trim().slice(0, 30), l: r.left, t: r.top, r: r.right, b: r.bottom};
})"""


def check_safe(boxes: list):
    lo_x, hi_x = SX + INSET, SX + SAFE_W - INSET
    lo_y, hi_y = SY + INSET, SY + SAFE_H - INSET
    bad = [b for b in boxes if b["l"] < lo_x or b["r"] > hi_x or b["t"] < lo_y or b["b"] > hi_y]
    for b in boxes:
        log(f"  {b['text']:<32} x {b['l']:.0f}-{b['r']:.0f}  y {b['t']:.0f}-{b['b']:.0f}")
    if bad:
        raise SystemExit(f"outside the phone-safe box {lo_x:.0f}-{hi_x:.0f} x {lo_y:.0f}-{hi_y:.0f}: "
                         + ", ".join(b["text"] for b in bad))


def shoot(html: str, path: Path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=CHROME_ARGS)
        page = browser.new_page(viewport={"width": BW, "height": BH})
        page.set_content(html, wait_until="load")
        page.evaluate(READY_JS)
        check_safe(page.evaluate(CHECK_JS))
        # The first capture after load can be a stale paint; keep the first
        # two captures that agree.
        prev = page.screenshot(type="png")
        for _ in range(6):
            cur = page.screenshot(type="png")
            if cur == prev:
                break
            prev = cur
        browser.close()
    path.write_bytes(prev)


def to_jpeg(png: Path, jpg: Path):
    # Full-resolution colour (4:4:4) so the lime edges stay crisp.
    subprocess.run([find_ffmpeg(), "-v", "error", "-y", "-i", str(png), "-q:v", "2",
                    "-pix_fmt", "yuvj444p", str(jpg)], check=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, colors in THEMES.items():
        png, jpg = OUT / f"youtube-banner-{name}.png", OUT / f"youtube-banner-{name}.jpg"
        log(f"{name}: checking the words sit inside the phone box")
        shoot(banner_html(*colors), png)
        to_jpeg(png, jpg)
        png.unlink()
        size = jpg.stat().st_size
        if size > MAX_BYTES:
            raise SystemExit(f"{jpg.name} is {size / 1e6:.1f}MB; YouTube's limit is 6MB")
        log(f"{jpg} ({BW}x{BH}, {size / 1e6:.2f}MB)")


if __name__ == "__main__":
    main()
