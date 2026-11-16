#!/usr/bin/env python3
"""Render a background recipe to a preview, or to a full production export.

Recipe (JSON) — the single source of truth shared by the static render and the live version:
{
  "name": "nova-arc",
  "family": "glow" | "mesh" | "liquid" | "thermal" | "iridescent" | "waves" | "terrain" | "image",
  "seed": 7,
  "params": {...family params...},          # see references/styles.md
  "mobile": {"params": {...overrides...}},  # optional: recomposition for portrait
  "source": "path/to/codex.png",            # family=image only (AI output)
  "mobile_source": "path/to/portrait.png",  # family=image only, optional
  "focus": [0.5, 0.45],                     # focal point used when cropping image sources
  "finish": [{"op": "grain", "amount": 0.05}, ...],
  "text_zone": [0.2, 0.3, 0.8, 0.62],       # where the headline sits (fractions of the frame)
  "page_bg": "#05050a"                      # colour the hero must melt into
}

Usage:
  render.py recipe.json --preview out.jpg [--size 1280x800]
  render.py recipe.json --export public/backgrounds --masters .legendary-backgrounds/masters
            [--desktop 3840x2400] [--mobile 1290x2796]
"""
from __future__ import annotations

import argparse
import base64
import copy
import io
import json
import os
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finish import apply_finish  # noqa: E402
from generators import GENERATORS  # noqa: E402
from lbg_core import from_pil, luminance, rgb_to_hex, to_pil  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def parse_size(s):
    w, h = s.lower().split("x")
    return int(w), int(h)


def _merge(a, b):
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def cover_crop(im: Image.Image, w: int, h: int, focus=(0.5, 0.5)) -> Image.Image:
    sw, sh = im.size
    s = max(w / sw, h / sh)
    nw, nh = max(w, round(sw * s)), max(h, round(sh * s))
    im = im.resize((nw, nh), Image.LANCZOS)
    fx, fy = focus
    x = int(min(max(fx * nw - w / 2, 0), nw - w))
    y = int(min(max(fy * nh - h / 2, 0), nh - h))
    return im.crop((x, y, x + w, y + h))


def render(recipe: dict, w: int, h: int, portrait: bool = False) -> np.ndarray:
    r = _merge(recipe, recipe.get("mobile")) if portrait and recipe.get("mobile") else recipe
    fam = r.get("family", "glow")
    if fam == "image":
        src = r.get("mobile_source") if portrait and r.get("mobile_source") else r["source"]
        im = Image.open(src).convert("RGB")
        img = from_pil(cover_crop(im, w, h, tuple(r.get("focus", [0.5, 0.5]))))
    else:
        if fam not in GENERATORS:
            raise SystemExit(f"unknown family '{fam}'. Known: {sorted(GENERATORS)} or 'image'")
        rng = np.random.default_rng(int(r.get("seed", 1)))
        img = GENERATORS[fam](w, h, r.get("params", {}), rng)
    return apply_finish(img, r.get("finish", []))


def _contrast(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _rel_lum(img):
    c = np.where(img <= 0.04045, img / 12.92, ((img + 0.055) / 1.055) ** 2.4)
    return c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722


def analyse(img: np.ndarray, zone):
    H, W = img.shape[:2]
    x0, y0, x1, y1 = zone
    z = img[int(y0 * H):max(int(y0 * H) + 1, int(y1 * H)), int(x0 * W):max(int(x0 * W) + 1, int(x1 * W))]
    L = _rel_lum(z)
    worst_light, worst_dark = float(np.percentile(L, 95)), float(np.percentile(L, 5))
    white, black = _contrast(1.0, worst_light), _contrast(0.0, worst_dark)
    text = "#ffffff" if white >= black else "#0a0a0a"
    small = to_pil(img).resize((64, 40), Image.BOX).quantize(5, method=Image.Quantize.MEDIANCUT)
    pal = small.getpalette()[:15]
    counts = sorted(small.getcolors(), reverse=True)
    dominant = [rgb_to_hex(np.array(pal[i * 3:i * 3 + 3]) / 255) for _, i in counts]
    return {
        "text_color": text,
        "text_contrast_worst_case": round(max(white, black), 2),
        "needs_scrim": max(white, black) < 4.5,
        "zone_mean_luminance": round(float(L.mean()), 3),
        "dominant_colors": dominant,
        "average_color": rgb_to_hex(img.reshape(-1, 3).mean(0)),
    }


def save_variants(im: Image.Image, base: str, widths, out_dir: str, formats=("avif", "webp")):
    files = {}
    for fmt in formats:
        entries = []
        for wd in widths:
            if wd > im.width:
                continue
            v = im if wd == im.width else im.resize((wd, round(im.height * wd / im.width)), Image.LANCZOS)
            fn = f"{base}-{wd}.{fmt}"
            kw = {"quality": 62} if fmt == "avif" else {"quality": 82, "method": 6}
            v.save(os.path.join(out_dir, fn), **kw)
            entries.append((fn, wd))
        files[fmt] = entries
    return files


def export(recipe, out_dir, desktop, mobile, masters_dir=None):
    """Web files -> out_dir (ship these). Masters + manifest -> masters_dir (keep out of public/)."""
    os.makedirs(out_dir, exist_ok=True)
    masters_dir = masters_dir or out_dir
    os.makedirs(masters_dir, exist_ok=True)
    name = recipe.get("name", "hero")
    t0 = time.time()
    d = to_pil(render(recipe, *desktop))
    m = to_pil(render(recipe, *mobile, portrait=True))
    d.save(os.path.join(masters_dir, f"{name}-desktop-master.png"))
    m.save(os.path.join(masters_dir, f"{name}-mobile-master.png"))
    d.resize((1920, round(d.height * 1920 / d.width)), Image.LANCZOS).save(
        os.path.join(out_dir, f"{name}-poster.jpg"), quality=86, progressive=True)
    dw = [w for w in (3840, 2560, 1920, 1280) if w <= d.width] or [d.width]
    mw = [w for w in (1290, 860) if w <= m.width] or [m.width]
    df = save_variants(d, f"{name}-desktop", dw, out_dir)
    mf = save_variants(m, f"{name}-mobile", mw, out_dir)
    tiny = d.resize((24, max(1, round(24 * d.height / d.width))), Image.LANCZOS)
    buf = io.BytesIO()
    tiny.save(buf, "WEBP", quality=50)
    zone = recipe.get("text_zone", [0.15, 0.28, 0.85, 0.65])
    mzone = recipe.get("mobile_text_zone", [0.06, 0.22, 0.94, 0.52])
    rel = lambda fs: ", ".join(f"{fn} {w}w" for fn, w in fs)  # noqa: E731
    manifest = {
        "name": name,
        "recipe": recipe,
        "desktop": {"size": list(d.size), "srcset": {k: rel(v) for k, v in df.items()}, "files": df},
        "mobile": {"size": list(m.size), "srcset": {k: rel(v) for k, v in mf.items()}, "files": mf},
        "poster": f"{name}-poster.jpg",
        "blur_data_url": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode(),
        "analysis": {"desktop": analyse(from_pil(d), zone), "mobile": analyse(from_pil(m), mzone)},
        "page_bg": recipe.get("page_bg") or analyse(from_pil(d), [0, 0.9, 1, 1])["average_color"],
        "render_seconds": round(time.time() - t0, 1),
    }
    manifest["public_dir"] = os.path.abspath(out_dir)
    with open(os.path.join(masters_dir, f"{name}.manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(out_dir, f"{name}.recipe.json"), "w") as f:
        json.dump(recipe, f, indent=2)
    print(json.dumps({k: manifest[k] for k in ("name", "analysis", "page_bg", "render_seconds")}, indent=2))
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recipe")
    ap.add_argument("--preview", help="write a single preview image here")
    ap.add_argument("--size", default="1280x800")
    ap.add_argument("--portrait", action="store_true", help="preview the mobile composition")
    ap.add_argument("--export", help="output directory for the production set")
    ap.add_argument("--masters", help="where master PNGs + manifest go (default: --export dir). Keep out of public/")
    ap.add_argument("--desktop", default="3840x2400")
    ap.add_argument("--mobile", default="1290x2796")
    a = ap.parse_args()
    recipe = json.load(open(a.recipe))
    if recipe.get("source") and not os.path.isabs(recipe["source"]):
        recipe["source"] = os.path.join(os.path.dirname(os.path.abspath(a.recipe)), recipe["source"])
    if recipe.get("mobile_source") and not os.path.isabs(recipe["mobile_source"]):
        recipe["mobile_source"] = os.path.join(os.path.dirname(os.path.abspath(a.recipe)), recipe["mobile_source"])
    if a.preview:
        w, h = parse_size(a.size)
        if a.portrait:
            w, h = h * 9 // 19, h
        t = time.time()
        to_pil(render(recipe, w, h, portrait=a.portrait)).save(a.preview, quality=90)
        print(f"{a.preview} {w}x{h} in {time.time() - t:.1f}s")
    if a.export:
        export(recipe, a.export, parse_size(a.desktop), parse_size(a.mobile), a.masters)
    if not (a.preview or a.export):
        ap.error("pass --preview and/or --export")


if __name__ == "__main__":
    main()
