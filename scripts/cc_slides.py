"""
Render one full-screen slide per item, for the animated shop video.

The static grid card is a thumbnail. This is the actual video: each cosmetic
gets its own moment on screen, with its real art big and centred. cc_video.py
then adds the motion (a slow push-in per slide) and crossfades them together.

Usage:
    python3 scripts/cc_slides.py [--date YYYY-MM-DD]
"""

import html
import shutil
import subprocess
import sys
from pathlib import Path

from cc_common import OUT_DIR, log, load_config, creator_code, read_json, today_stamp
from cc_render import ACCENT, BG, RARITY_COLORS, find_chromium

VIDEO_ITEMS = 8          # 8 items x 6s + intro + outro clears 60s comfortably
W, H = 1080, 1920

_BASE = f'''
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ width:{W}px; height:{H}px; background:{BG}; color:#fff; overflow:hidden;
    font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;
    display:flex; flex-direction:column; align-items:center;
    justify-content:center; padding:90px 70px; position:relative; }}
  .badge {{ position:absolute; top:80px; left:50%; transform:translateX(-50%);
    display:flex; align-items:center; gap:12px; background:rgba(10,10,11,.8);
    border:2px solid {ACCENT}; border-radius:14px; padding:10px 20px; }}
  .badge .l {{ color:#9AA0A6; font-size:17px; font-weight:700; letter-spacing:.2em; }}
  .badge .c {{ color:{ACCENT}; font-size:30px; font-weight:850; line-height:1; }}
  .disc {{ position:absolute; bottom:96px; left:0; right:0; text-align:center;
    font-size:24px; line-height:1.5; color:#9AA0A6; font-weight:600; }}
'''


def _item_slide(item: dict, uri: str, code: str, idx: int, total: int) -> str:
    color = RARITY_COLORS.get(item["rarity"], "#9AA0A6")
    name = html.escape(item["name"])
    kind = html.escape(item["type"])
    rar = html.escape(item["rarity_label"])
    if item.get("discounted"):
        price = (f'<span class="was">{item["regular_price"]}</span>'
                 f'<span class="now">{item["price"]}</span>')
    else:
        price = f'<span class="now">{item["price"]}</span>'
    art = (f'<img src="{uri}" alt="">' if uri
           else f'<div class="noart">{kind.upper()}</div>')

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>{_BASE}
  body {{ background-image:
    radial-gradient(ellipse 80% 55% at 50% 42%, {color}38, transparent 68%),
    radial-gradient(circle at 50% 100%, {color}1f, transparent 60%); }}
  .count {{ position:absolute; top:172px; left:0; right:0; text-align:center;
    color:#6B7079; font-size:25px; font-weight:700; letter-spacing:.24em; }}
  .art {{ height:840px; display:flex; align-items:center; justify-content:center;
    margin-bottom:34px; }}
  .art img {{ height:840px; width:auto; max-width:920px; object-fit:contain;
    filter:drop-shadow(0 26px 60px rgba(0,0,0,.7)); }}
  .noart {{ font-size:46px; color:{color}; font-weight:800; letter-spacing:.2em; }}
  .rar {{ color:{color}; font-size:28px; font-weight:800; letter-spacing:.26em;
    text-transform:uppercase; margin-bottom:16px; }}
  .name {{ font-size:78px; font-weight:850; letter-spacing:-.03em; text-align:center;
    line-height:1.06; margin-bottom:26px; max-width:940px; }}
  .price {{ display:flex; align-items:baseline; gap:14px; font-weight:850; }}
  .was {{ font-size:42px; color:#6B7079; text-decoration:line-through; font-weight:700; }}
  .now {{ font-size:78px; color:{ACCENT}; }}
  .vb {{ font-size:34px; color:#8A8F98; font-weight:800; }}
</style></head><body>
  <div class="badge"><span class="l">CODE</span><span class="c">{html.escape(code)}</span></div>
  <div class="count">{idx} / {total}</div>
  <div class="art">{art}</div>
  <div class="rar">{rar} {kind}</div>
  <div class="name">{name}</div>
  <div class="price">{price}<span class="vb">V-BUCKS</span></div>
  <div class="disc">#EpicPartner</div>
</body></html>'''


def _intro_slide(shop: dict, code: str) -> str:
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>{_BASE}
  .kick {{ font-size:34px; letter-spacing:.44em; color:{ACCENT}; font-weight:700;
    text-transform:uppercase; margin-bottom:22px; }}
  h1 {{ font-size:152px; font-weight:850; letter-spacing:-.04em; line-height:.94;
    text-align:center; }}
  .date {{ font-size:48px; color:#8A8F98; font-weight:700; margin-top:26px; }}
  .n {{ font-size:32px; color:#6B7079; font-weight:700; margin-top:40px;
    letter-spacing:.14em; }}
</style></head><body>
  <div class="kick">Fortnite</div>
  <h1>ITEM<br>SHOP</h1>
  <div class="date">{html.escape(shop["fetched"])}</div>
  <div class="n">{shop["item_count"]} ITEMS TODAY</div>
  <div class="disc">#EpicPartner</div>
</body></html>'''


def _outro_slide(code: str) -> str:
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>{_BASE}
  body {{ background-image:radial-gradient(ellipse 70% 45% at 50% 50%,
    rgba(232,255,58,.16), transparent 68%); }}
  .use {{ font-size:40px; color:#8A8F98; letter-spacing:.26em; font-weight:700;
    text-transform:uppercase; margin-bottom:14px; }}
  .code {{ font-size:270px; font-weight:850; color:{ACCENT}; line-height:1;
    letter-spacing:-.05em; text-shadow:0 0 90px rgba(232,255,58,.45); }}
</style></head><body>
  <div class="use">Use creator code</div>
  <div class="code">{html.escape(code)}</div>
  <div class="disc">#EpicPartner</div>
</body></html>'''


def shoot(binary: str, html_path: Path, png_path: Path) -> bool:
    cmd = [binary, "--headless", "--disable-gpu", "--no-sandbox",
           f"--window-size={W},{H}", "--hide-scrollbars",
           f"--screenshot={png_path}", f"file://{html_path}"]
    try:
        subprocess.run(cmd, capture_output=True, timeout=90, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        log(f"slide render failed: {e}")
        return False
    return png_path.exists()


def main():
    stamp = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else today_stamp()
    cfg = load_config()
    code = creator_code(cfg)

    shop = read_json(OUT_DIR / stamp / "shop.json")
    if not shop:
        log(f"ERROR: no shop.json for {stamp}. Run cc_shop.py first.")
        sys.exit(1)

    binary = find_chromium()
    if not binary:
        log("ERROR: Chromium not found (free: brew install --cask chromium).")
        sys.exit(1)

    from cc_images import fetch_all
    images = fetch_all(shop["items"], VIDEO_ITEMS)

    slides_dir = OUT_DIR / stamp / "slides"
    if slides_dir.exists():
        shutil.rmtree(slides_dir)
    slides_dir.mkdir(parents=True)

    items = shop["items"][:VIDEO_ITEMS]
    pages = [("00_intro", _intro_slide(shop, code))]
    for i, item in enumerate(items, start=1):
        pages.append((f"{i:02d}_item", _item_slide(item, images.get(item["name"], ""),
                                                   code, i, len(items))))
    pages.append((f"{len(items)+1:02d}_outro", _outro_slide(code)))

    made = 0
    for name, markup in pages:
        hp = slides_dir / f"{name}.html"
        hp.write_text(markup, encoding="utf-8")
        if shoot(binary, hp, slides_dir / f"{name}.png"):
            made += 1
        hp.unlink(missing_ok=True)

    log(f"Rendered {made}/{len(pages)} slides -> {slides_dir}")
    if made != len(pages):
        sys.exit(1)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
