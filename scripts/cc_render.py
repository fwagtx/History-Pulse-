"""
Render a branded vertical (1080x1920) item-shop card for the day.

Outputs self-contained HTML. Convert to PNG for free with headless Chromium:

    chromium --headless --disable-gpu --window-size=1080,1920 \
      --screenshot=card.png --hide-scrollbars card.html

The brand is deliberately word-first, not face-first: black + acid yellow with the code set
huge. That is what makes the pipeline automatable — no one has to appear on camera for the
asset to be recognisably yours.

Usage:
    python3 scripts/cc_render.py [--date YYYY-MM-DD] [--png]
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


def _card_row(item: dict) -> str:
    color = RARITY_COLORS.get(item["rarity"], "#9AA0A6")
    name = html.escape(item["name"])
    kind = html.escape(item["type"])
    if item.get("discounted"):
        price = (f'<span class="was">{item["regular_price"]}</span> '
                 f'<span class="now">{item["price"]}</span>')
    else:
        price = f'<span class="now">{item["price"]}</span>'
    return f'''
      <li class="row" style="--r:{color}">
        <span class="bar"></span>
        <span class="meta"><span class="name">{name}</span><span class="kind">{kind}</span></span>
        <span class="price">{price}<span class="vb">V</span></span>
      </li>'''


def build_html(shop: dict, code: str) -> str:
    items = shop["items"][:10]
    rows = "".join(_card_row(i) for i in items)
    extra = len(shop["items"]) - len(items)
    more = f'<p class="more">+{extra} more in today\'s shop</p>' if extra > 0 else ""
    date_label = html.escape(shop["fetched"])

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Item Shop {date_label}</title>
<style>
  @font-face {{ font-family: fallback; src: local("Arial"); }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    width:1080px; height:1920px; background:{BG}; color:#fff; overflow:hidden;
    font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;
    display:flex; flex-direction:column; padding:70px 64px 96px;
    background-image:
      radial-gradient(circle at 15% 8%, rgba(232,255,58,.13), transparent 42%),
      radial-gradient(circle at 85% 92%, rgba(232,255,58,.07), transparent 46%);
  }}
  header {{ flex:0 0 auto; }}
  .kicker {{ font-size:30px; letter-spacing:.42em; color:{ACCENT};
             text-transform:uppercase; font-weight:700; }}
  h1 {{ font-size:104px; line-height:.95; font-weight:800; margin:18px 0 10px;
        letter-spacing:-.03em; }}
  .date {{ font-size:36px; color:#8A8F98; font-weight:600; letter-spacing:.02em; }}
  .rule {{ height:5px; background:{ACCENT}; width:132px; margin:34px 0 14px; border-radius:3px; }}
  ul {{ list-style:none; flex:1 1 auto; min-height:0; overflow:hidden;
        display:flex; flex-direction:column; justify-content:center;
        gap:15px; margin-top:14px; }}
  .row {{ display:flex; align-items:center; gap:26px; background:rgba(255,255,255,.045);
          border-radius:18px; padding:23px 30px; }}
  .bar {{ width:9px; align-self:stretch; background:var(--r); border-radius:6px;
          box-shadow:0 0 22px var(--r); }}
  .meta {{ display:flex; flex-direction:column; gap:5px; flex:1; min-width:0; }}
  .name {{ font-size:45px; font-weight:750; letter-spacing:-.018em;
           white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .kind {{ font-size:26px; color:#8A8F98; text-transform:uppercase; letter-spacing:.16em; }}
  .price {{ display:flex; align-items:baseline; gap:9px; font-weight:800; white-space:nowrap; }}
  .was {{ font-size:31px; color:#6B7079; text-decoration:line-through; font-weight:600; }}
  .now {{ font-size:47px; color:{ACCENT}; }}
  .vb {{ font-size:27px; color:#8A8F98; font-weight:700; }}
  .more {{ flex:0 0 auto; text-align:center; color:#8A8F98; font-size:29px;
          margin-top:16px; font-weight:600; }}
  footer {{ flex:0 0 auto; margin-top:30px; border-top:2px solid rgba(255,255,255,.1);
            padding-top:30px; text-align:center; }}
  .use {{ font-size:34px; color:#8A8F98; letter-spacing:.24em;
          text-transform:uppercase; font-weight:700; }}
  .code {{ font-size:148px; font-weight:850; color:{ACCENT}; line-height:1.02;
           letter-spacing:-.035em; margin:8px 0 12px;
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
  <ul>{rows}</ul>
  {more}
  <footer>
    <div class="use">Use creator code</div>
    <div class="code">{html.escape(code)}</div>
    <div class="disc">#EpicPartner · commission earned on purchases</div>
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
    html_path = day_dir / "card.html"
    html_path.write_text(build_html(shop, code), encoding="utf-8")
    log(f"Wrote {html_path}")

    if "--png" in sys.argv:
        png_path = day_dir / "card.png"
        if to_png(html_path, png_path):
            log(f"Wrote {png_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    main()
