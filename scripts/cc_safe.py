"""
Where the apps draw over a vertical video, and a check that nothing that
matters sits there.

Every video goes to TikTok, Instagram Reels, YouTube Shorts and Facebook Reels,
and each app lays its own UI over the picture: a header or tabs across the top,
the like/comment/share buttons down the right, and the handle, caption and
audio line across the bottom. Whatever sits under them is hard or impossible to
see. The safe box is the part of the 1080x1920 frame that none of the four
covers (checked September 2026; Facebook measured from Metricool's Reels
preview, the others from the apps' published templates):

    left    60     TikTok 44, Facebook ~65
    top     230    Instagram's Reels header ~210, Facebook ~200, YouTube ~180,
                   TikTok 130
    right   1020   above y 740 -- nothing on the right up there, just a margin
            900    from y 740 down: the button rail. Facebook's starts at ~770
                   and is the widest (~180 px); TikTok 140, YouTube ~120-190,
                   Instagram ~120
    bottom  1420   the caption block: TikTok's takes the bottom 484 px (from
                   1436), Facebook's starts ~1455, Instagram's ~1470,
                   YouTube's ~1500

Frame 0 is also the cover. Instagram's profile grid shows it cropped to 4:5
(y 285-1635) and TikTok's to 3:4 (y 240-1680), so on frame 0 the text sits at
y >= 285 as well.

Backgrounds and decoration may run to the edges. Text, the cosmetics and the
USE CODE: BAD element stay inside the box whenever they are at rest. `check()`
verifies that on the real page, in the same browser that renders the video:
it seeks every quarter second and measures each line of text, each image and
each element marked data-safe="key"; anything outside the box for longer than
a passing animation (0.6 s) is a violation.

Mark pure decoration data-safe="ignore" (a texture strip, a torn edge) -- never
text people are meant to read.

    python3 scripts/cc_safe.py --format which_first --date 2026-09-25 --art DIR
    python3 scripts/cc_safe.py --format og_check --shop PATH/shop.json --art DIR
"""

import json
import sys
from pathlib import Path

W, H = 1080, 1920
LEFT, TOP, RIGHT_TOP, RAIL_TOP, RIGHT, BOTTOM = 60, 230, 1020, 740, 900, 1420
COVER_TOP = 285                  # frame 0: Instagram's 4:5 grid crop starts here

ZONE = {"left": LEFT, "top": TOP, "rightTop": RIGHT_TOP, "rail": RAIL_TOP, "right": RIGHT,
        "bottom": BOTTOM, "minAlpha": .35, "textTol": .02, "imgTol": .12, "keyTol": .01}
COVER = dict(ZONE, top=COVER_TOP)

STEP = .25                       # seconds between samples
MIN_HOLD = .6                    # outside the box for at least this long = a violation

CHECK_JS = r"""(z) => {
  const W = 1080, H = 1920, out = [];
  const inside = (x, y) => x >= z.left && y >= z.top && y <= z.bottom &&
                           x <= (y < z.rail ? z.rightTop : z.right);
  // Share of the on-frame part of a box that falls outside the safe box
  // (-1 when none of it is on the frame: nobody can see it anyway).
  const outside = (r) => {
    const x0 = Math.max(0, r.left), x1 = Math.min(W, r.right);
    const y0 = Math.max(0, r.top), y1 = Math.min(H, r.bottom);
    if (x1 - x0 < 1 || y1 - y0 < 1) return -1;
    const n = 10; let bad = 0, tot = 0;
    for (let i = 0; i <= n; i++) for (let j = 0; j <= n; j++) {
      tot++; if (!inside(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * j / n)) bad++;
    }
    return bad / tot;
  };
  const alpha = (el) => {
    let o = 1;
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden') return 0;
      o *= parseFloat(cs.opacity);
      if (o < 0.02) return 0;
    }
    return o;
  };
  const skip = (el) => !!el.closest('[data-safe="ignore"],style,script');
  const box = (r) => [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const range = document.createRange();
  let idx = -1;
  for (let n; (n = tw.nextNode());) {
    idx++;                        // the node's place in the page: the same on every seek
    const s = n.textContent.replace(/\s+/g, ' ').trim();
    if (!s) continue;
    const el = n.parentElement;
    if (!el || skip(el)) continue;
    const a = alpha(el);
    if (a < z.minAlpha) continue;
    range.selectNodeContents(n);
    for (const rr of range.getClientRects()) {
      if (rr.width < 3 || rr.height < 3) continue;
      // A text box spans the font's whole ascent and descent; the letters fill
      // about its middle two thirds. Measure those.
      const r = {left: rr.left, right: rr.right, top: rr.top + rr.height * .18,
                 bottom: rr.bottom - rr.height * .18, width: rr.width, height: rr.height * .64};
      const f = outside(r);
      if (f > z.textTol) out.push({kind: 'text', key: s.slice(0, 60), id: 't' + idx, frac: +f.toFixed(2), box: box(r)});
    }
  }
  const imgs = [...document.images];
  imgs.forEach((img, i) => {
    if (skip(img)) return;
    if (alpha(img) < z.minAlpha) return;
    const r = img.getBoundingClientRect();
    if (r.width < 40 || r.height < 40 || r.width * r.height > 0.45 * W * H) return;
    const f = outside(r);
    const name = img.getAttribute('data-name') || img.alt || ('image ' + i);
    if (f > z.imgTol) out.push({kind: 'image', key: name, id: 'i' + i, frac: +f.toFixed(2), box: box(r)});
  });
  let ki = -1;
  for (const el of document.querySelectorAll('[data-safe="key"]')) {
    ki++;
    if (alpha(el) < z.minAlpha) continue;
    const r = el.getBoundingClientRect();
    const f = outside(r);
    const name = el.getAttribute('data-name') || el.textContent.replace(/\s+/g, ' ').trim().slice(0, 40);
    if (f > z.keyTol) out.push({kind: 'key', key: name, id: 'k' + ki, frac: +f.toFixed(2), box: box(r)});
  }
  return out;
}"""


def _spans(samples: list, step: float) -> list:
    """Group per-sample hits into spans of time per element."""
    spans = {}
    for t, hits in samples:
        for h in hits:
            # One span per element, so two elements that happen to say the same
            # thing (a leaving card and the recap's) never add up to one hold.
            k = (h["kind"], h["key"], h.get("id"))
            s = spans.get(k)
            if s and t - s["end"] <= step * 1.5:
                s["end"] = t
                if h["frac"] > s["frac"]:
                    s.update(frac=h["frac"], box=h["box"], at=t)
            else:
                if s:
                    spans.setdefault("_done", []).append(s)
                spans[k] = {"kind": h["kind"], "key": h["key"], "start": t, "end": t,
                            "frac": h["frac"], "box": h["box"], "at": t}
    done = spans.pop("_done", [])
    return done + list(spans.values())


def check(comp, step: float = STEP, min_hold: float = MIN_HOLD) -> dict:
    """Seek through the composition and report what sits outside the safe box.

    Returns {"ok": bool, "violations": [...], "cover": [...]}. A violation is an
    element outside the box for at least `min_hold` seconds (entrances and exits
    that cross the edge on their way in or out don't count); `cover` lists text
    outside Instagram's 4:5 grid crop on frame 0."""
    from playwright.sync_api import sync_playwright
    from cc_motion import CHROME_ARGS, READY_JS, SEEK_JS, SETTLE_JS

    n = int(comp.duration / step)
    times = [round(i * step, 3) for i in range(n + 1) if i * step < comp.duration - .02]
    samples = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=CHROME_ARGS)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_content(comp.document(), wait_until="load")
        page.evaluate(READY_JS)
        page.evaluate(SETTLE_JS, 0)
        cover = [h for h in page.evaluate(CHECK_JS, COVER) if h["kind"] == "text"]
        for t in times:
            page.evaluate(SEEK_JS, t * 1000)
            samples.append((t, page.evaluate(CHECK_JS, ZONE)))
        browser.close()
    spans = [s for s in _spans(samples, step) if s["end"] - s["start"] + step >= min_hold - 1e-6]
    spans.sort(key=lambda s: (s["start"], s["key"]))
    for s in spans:
        s["start"], s["end"] = round(s["start"], 2), round(s["end"] + step, 2)
    return {"ok": not spans and not cover, "violations": spans, "cover": cover}


def summary(res: dict, limit: int = 12) -> str:
    """One line per problem, for logs."""
    if res["ok"]:
        return "safe zones: OK"
    lines = [f"safe zones: {len(res['violations'])} element(s) under the apps' UI"
             + (f", {len(res['cover'])} outside the cover crop on frame 0" if res["cover"] else "")]
    for s in res["violations"][:limit]:
        x, y, w, h = s["box"]
        lines.append(f"  {s['start']:5.2f}-{s['end']:5.2f}s  {s['kind']:5}  {int(s['frac'] * 100):3d}% out"
                     f"  at x{x} y{y} {w}x{h}  {s['key']!r}")
    if len(res["violations"]) > limit:
        lines.append(f"  ... and {len(res['violations']) - limit} more")
    for h in res["cover"][:6]:
        x, y, w, h2 = h["box"]
        lines.append(f"  frame 0 cover  text at x{x} y{y} {w}x{h2}  {h['key']!r}")
    return "\n".join(lines)


def gate(make, name: str, log=print):
    """Build a video with make() and hold it to the safe box.

    If it fails the check and one of the new looks drew it, build the classic
    version (looks off for this one build) and take that if it passes. Returns
    (video, result) -- the version to publish and its check -- or (None, None)
    when make() gives nothing. A video that still fails is returned anyway with
    its result, so the caller decides (a shop slot can try another format)."""
    import os
    import cc_looks as LK
    LK.draw.last = None
    v = make()
    if v is None:
        return None, None
    res = check(v.comp)
    look = LK.draw.last if (LK.draw.last and not LK.draw.last.startswith("classic")) else None
    if res["ok"]:
        return v, res
    log(f"  {name}: {summary(res, 8)}")
    if not look:
        return v, res
    old = os.environ.get("CC_LOOKS")
    os.environ["CC_LOOKS"] = "none"
    try:
        v2 = make()
    finally:
        if old is None:
            os.environ.pop("CC_LOOKS", None)
        else:
            os.environ["CC_LOOKS"] = old
    if v2 is None:
        return v, res
    res2 = check(v2.comp)
    if res2["ok"]:
        print(f"::warning::{name}: the {look} look put something under the apps' UI; using the classic look",
              file=sys.stderr)
        return v2, res2
    return v, res


def note(res: dict | None) -> dict:
    """The check's result as a manifest field."""
    if res is None:
        return {"ok": None}
    return {"ok": res["ok"], "violations": len(res["violations"]), "cover": len(res["cover"])}


# ------------------------------------------------------------ app mock-ups

# Approximate positions of each app's UI on a 1080x1920 frame: ("bar", x, y, w, h)
# is a dark band, ("dot", x, y, r) a button, ("txt", x, y, w, h) a caption line.
APPS = {
    "TikTok": [("bar", 0, 0, W, 180), ("dot", 1000, 960, 44), ("dot", 1000, 1110, 40), ("dot", 1000, 1250, 40),
               ("dot", 1000, 1390, 40), ("dot", 1000, 1530, 40), ("dot", 1000, 1690, 40),
               ("txt", 40, 1540, 360, 44), ("txt", 40, 1606, 820, 34), ("txt", 40, 1656, 700, 34),
               ("txt", 40, 1726, 520, 32), ("bar", 0, 1800, W, 120)],
    "Instagram": [("bar", 0, 0, W, 210), ("dot", 1010, 1210, 38), ("dot", 1010, 1350, 38), ("dot", 1010, 1480, 38),
                  ("dot", 1010, 1610, 34), ("dot", 1010, 1730, 34), ("txt", 40, 1560, 460, 50),
                  ("txt", 40, 1640, 800, 34), ("txt", 40, 1700, 560, 34), ("bar", 0, 1790, W, 130)],
    "YouTube": [("bar", 0, 0, W, 180), ("dot", 990, 950, 44), ("dot", 990, 1110, 44), ("dot", 990, 1270, 44),
                ("dot", 990, 1430, 44), ("dot", 990, 1590, 44), ("dot", 990, 1740, 40),
                ("txt", 40, 1520, 520, 52), ("txt", 40, 1600, 860, 40), ("txt", 40, 1656, 700, 40),
                ("bar", 0, 1800, W, 120)],
    "Facebook": [("bar", 0, 0, W, 200), ("dot", 977, 822, 56), ("dot", 977, 1060, 56), ("dot", 977, 1300, 56),
                 ("dot", 977, 1540, 56), ("dot", 977, 1790, 56), ("txt", 40, 1470, 620, 70),
                 ("txt", 40, 1590, 820, 40), ("txt", 40, 1650, 700, 40), ("txt", 40, 1705, 260, 36),
                 ("txt", 40, 1780, 560, 70)],
}


def app_view(frame, app: str):
    """The frame as it looks in one app: its UI drawn over it (needs Pillow)."""
    from PIL import Image, ImageDraw
    im = frame.convert("RGBA")
    s = im.size[0] / W
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for it in APPS[app]:
        if it[0] == "bar":
            _, x, y, w, h = it
            d.rectangle([x * s, y * s, (x + w) * s, (y + h) * s], fill=(0, 0, 0, 120))
        elif it[0] == "dot":
            _, x, y, r = it
            d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=(255, 255, 255, 215))
        else:
            _, x, y, w, h = it
            d.rounded_rectangle([x * s, y * s, (x + w) * s, (y + h) * s], radius=h * s / 2,
                                fill=(255, 255, 255, 200))
    return Image.alpha_composite(im, ov).convert("RGB")


def shaded(frame):
    """The frame with everything outside the safe box tinted red and the box
    outlined in lime (needs Pillow)."""
    from PIL import Image, ImageDraw
    im = frame.convert("RGB")
    s = im.size[0] / W
    mask = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(mask)
    d.rectangle([0, 0, im.size[0], TOP * s], fill=255)
    d.rectangle([0, BOTTOM * s, im.size[0], im.size[1]], fill=255)
    d.rectangle([0, 0, LEFT * s, im.size[1]], fill=255)
    d.rectangle([RIGHT_TOP * s, 0, im.size[0], im.size[1]], fill=255)
    d.rectangle([RIGHT * s, RAIL_TOP * s, im.size[0], im.size[1]], fill=255)
    red = Image.new("RGB", im.size, (255, 0, 60))
    im = Image.composite(Image.blend(im, red, .42), im, mask)
    d = ImageDraw.Draw(im)
    pts = [(LEFT, TOP), (RIGHT_TOP, TOP), (RIGHT_TOP, RAIL_TOP), (RIGHT, RAIL_TOP), (RIGHT, BOTTOM),
           (LEFT, BOTTOM), (LEFT, TOP)]
    d.line([(x * s, y * s) for x, y in pts], fill=(232, 255, 58), width=max(2, int(3 * s)))
    return im


def app_sheet(pngs: list, dest: Path, width: int = 270):
    """Each still once per app, side by side: rows = stills, columns = apps."""
    from PIL import Image, ImageDraw
    apps = list(APPS)
    h = int(width * H / W)
    sheet = Image.new("RGB", (width * len(apps), (h + 26) * len(pngs) + 26), "white")
    d = ImageDraw.Draw(sheet)
    for c, app in enumerate(apps):
        d.text((c * width + 8, 6), app, fill=(0, 0, 0))
    for r, p in enumerate(pngs):
        fr = Image.open(p).resize((width, h))
        for c, app in enumerate(apps):
            sheet.paste(app_view(fr, app), (c * width, 26 + r * (h + 26)))
        d.text((8, 26 + r * (h + 26) + h + 6), Path(p).stem, fill=(0, 0, 0))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, quality=84)
    return dest


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", required=True)
    ap.add_argument("--date")
    ap.add_argument("--series", default="")
    ap.add_argument("--shop")
    ap.add_argument("--art", required=True)
    ap.add_argument("--looks", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    import cc_look_preview as P
    v = P.build_video(a.format, a.date, a.series, a.shop, a.art, a.looks)
    res = check(v.comp)
    print(json.dumps(res, indent=1) if a.json else summary(res, 40))
    sys.exit(0 if res["ok"] else 1)
