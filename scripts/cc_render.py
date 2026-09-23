"""
Render a branded vertical (1080x1920) item-shop card for the day.

Outputs self-contained HTML. Convert to PNG for free with headless Chromium:

    chromium --headless --disable-gpu --window-size=1080,1920 \
      --screenshot=card.png --hide-scrollbars card.html

The brand is deliberately word-first, not face-first: black + acid yellow with the code set
huge. That is what makes the pipeline automatable — no one has to appear on camera for the
asset to be recognisably yours.

Usage:
    python3 scripts/cc_render.py [--date YYYY-MM-DD] [--png] [--no-images]
"""

import html
import shutil
import subprocess
import sys

from cc_common import OUT_DIR, log, load_config, creator_code, read_json, today_stamp

ACCENT = "#E8FF3A"          # acid yellow — the BAD signature colour
BG = "#0A0A0B"

RARITY_COLORS = {
    "common": "#9AA0A6", "uncommon": "#5BC44A", "rare": "#4A9FF5",
    "epic": "#B451E8", "legendary": "#EE8B3D", "mythic": "#F7D94C",
    "icon": "#3DD6C9", "marvel": "#E5504F", "dc": "#4C5EAB",
    "starwars": "#C7A008", "gaminglegends": "#8E2CF5",
}

CHROMIUM_CANDIDATES = ("chromium", "chromium-browser", "google-chrome",
                       "/opt/pw-browsers/chromium")


GRID_ITEMS = 6          # 2 columns x 3 rows; 4 rows overflows 1920 and clips


def _tile(item: dict, uri: str) -> str:
    """One item tile. Uses the real cosmetic art when we have it, and falls
    back to a rarity-coloured plate when the image could not be fetched, so a
    missing download degrades one tile instead of breaking the card."""
    color = RARITY_COLORS.get(item["rarity"], "#9AA0A6")
    name = html.escape(item["name"])
    kind = html.escape(item["type"])
    if item.get("discounted"):
        price = (f'<span class="was">{item["regular_price"]}</span>'
                 f'<span class="now">{item["price"]}</span>')
    else:
        price = f'<span class="now">{item["price"]}</span>'

    art = (f'<img src="{uri}" alt="">' if uri
           else f'<span class="noart">{html.escape(kind.upper())}</span>')

    return f'''
      <li class="tile" style="--r:{color}">
        <span class="art">{art}</span>
        <span class="name">{name}</span>
        <span class="price">{price}<span class="vb">V</span></span>
      </li>'''


def build_html(shop: dict, code: str, images: dict | None = None) -> str:
    images = images or {}
    items = shop["items"][:GRID_ITEMS]
    tiles = "".join(_tile(i, images.get(i["name"], "")) for i in items)
    extra = len(shop["items"]) - len(items)
    more = f'<p class="more">+{extra} more in today\'s shop</p>' if extra > 0 else ""
    date_label = html.escape(shop["fetched"])

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Item Shop {date_label}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    width:1080px; height:1920px; background:{BG}; color:#fff; overflow:hidden;
    font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;
    display:flex; flex-direction:column; padding:58px 56px 92px;
    background-image:
      radial-gradient(circle at 15% 6%, rgba(232,255,58,.13), transparent 42%),
      radial-gradient(circle at 85% 94%, rgba(232,255,58,.07), transparent 46%);
  }}
  header {{ flex:0 0 auto; }}
  .kicker {{ font-size:27px; letter-spacing:.42em; color:{ACCENT};
             text-transform:uppercase; font-weight:700; }}
  h1 {{ font-size:92px; line-height:.95; font-weight:800; margin:14px 0 8px;
        letter-spacing:-.03em; }}
  .date {{ font-size:32px; color:#8A8F98; font-weight:600; }}
  .rule {{ height:5px; background:{ACCENT}; width:120px; margin:26px 0 0;
           border-radius:3px; }}

  ul {{ list-style:none; flex:1 1 auto; min-height:0; overflow:hidden;
        display:grid; grid-template-columns:1fr 1fr; gap:20px;
        align-content:center; margin-top:24px; }}
  .tile {{ background:rgba(255,255,255,.05); border-radius:20px;
           padding:18px 18px 20px; display:flex; flex-direction:column;
           align-items:center; border-top:5px solid var(--r);
           box-shadow:inset 0 42px 70px -42px var(--r); }}
  .art {{ width:100%; height:224px; display:flex; align-items:center;
          justify-content:center; margin-bottom:12px; }}
  .art img {{ max-width:100%; max-height:224px; object-fit:contain;
              filter:drop-shadow(0 8px 18px rgba(0,0,0,.55)); }}
  .noart {{ font-size:23px; color:var(--r); font-weight:800; letter-spacing:.16em;
            opacity:.85; }}
  .name {{ font-size:33px; font-weight:750; letter-spacing:-.018em; text-align:center;
           line-height:1.15; max-width:100%; overflow:hidden;
           display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }}
  .price {{ display:flex; align-items:baseline; gap:8px; font-weight:800;
            margin-top:9px; white-space:nowrap; }}
  .was {{ font-size:25px; color:#6B7079; text-decoration:line-through; font-weight:600; }}
  .now {{ font-size:38px; color:{ACCENT}; }}
  .vb {{ font-size:23px; color:#8A8F98; font-weight:700; }}

  .more {{ flex:0 0 auto; text-align:center; color:#8A8F98; font-size:27px;
           margin-top:16px; font-weight:600; }}
  footer {{ flex:0 0 auto; margin-top:26px; border-top:2px solid rgba(255,255,255,.1);
            padding-top:26px; text-align:center; }}
  .use {{ font-size:31px; color:#8A8F98; letter-spacing:.24em;
          text-transform:uppercase; font-weight:700; }}
  .code {{ font-size:132px; font-weight:850; color:{ACCENT}; line-height:1.02;
           letter-spacing:-.035em; margin:6px 0 10px;
           text-shadow:0 0 62px rgba(232,255,58,.42); }}
  .disc {{ font-size:24px; line-height:1.5; color:#9AA0A6; font-weight:600; }}
</style></head>
<body>
  <header>
    <div class="kicker">Fortnite</div>
    <h1>Item Shop</h1>
    <div class="date">{date_label}</div>
    <div class="rule"></div>
  </header>
  <ul>{tiles}</ul>
  {more}
  <footer>
    <div class="use">Use creator code</div>
    <div class="code">{html.escape(code)}</div>
    <div class="disc">#EpicPartner</div>
  </footer>
</body></html>'''


def find_chromium() -> str | None:
    for candidate in CHROMIUM_CANDIDATES:
        found = shutil.which(candidate) or (candidate if shutil.which(candidate) else None)
        if found:
            return found
    return None


def to_png(html_path, png_path) -> bool:
    binary = find_chromium()
    if not binary:
        log("Chromium not found — HTML written, convert it yourself or install chromium (free).")
        return False
    cmd = [binary, "--headless", "--disable-gpu", "--no-sandbox",
           "--window-size=1080,1920", "--hide-scrollbars",
           f"--screenshot={png_path}", f"file://{html_path}"]
    try:
        subprocess.run(cmd, capture_output=True, timeout=90, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        log(f"WARN: PNG render failed ({e}); HTML is still usable.")
        return False
    return png_path.exists()


def main():
    stamp = today_stamp()
    if "--date" in sys.argv:
        stamp = sys.argv[sys.argv.index("--date") + 1]

    cfg = load_config()
    code = creator_code(cfg)

    shop = read_json(OUT_DIR / stamp / "shop.json")
    if not shop:
        log(f"ERROR: no shop.json for {stamp}. Run cc_shop.py first.")
        sys.exit(1)

    day_dir = OUT_DIR / stamp
    day_dir.mkdir(parents=True, exist_ok=True)

    # Real cosmetic art, embedded so the render needs no network.
    images = {}
    if "--no-images" not in sys.argv:
        from cc_images import fetch_all
        images = fetch_all(shop["items"], GRID_ITEMS)

    html_path = day_dir / "card.html"
    html_path.write_text(build_html(shop, code, images), encoding="utf-8")
    log(f"Wrote {html_path}")

    if "--png" in sys.argv:
        png_path = day_dir / "card.png"
        if to_png(html_path, png_path):
            log(f"Wrote {png_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    main()
