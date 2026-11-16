#!/usr/bin/env python3
"""Lay out option previews as a labelled contact sheet, optionally with a mock hero headline
on each so the user judges the background *as a landing page*, not as wallpaper.

  contact_sheet.py out.jpg a.jpg b.jpg c.jpg --labels "A · Nova arc" "B · Dither dusk" ... \
      --headline "Ship faster with Acme" --sub "The deploy platform for teams" [--cols 2]
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbg_core import from_pil, luminance  # noqa: E402

SANS = ["/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/segoeuib.ttf"]


def font(size):
    for f in SANS:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except OSError:
                pass
    return ImageFont.load_default()


def mock_hero(im: Image.Image, headline: str, sub: str | None, zone_y=0.42) -> Image.Image:
    im = im.copy()
    W, H = im.size
    d = ImageDraw.Draw(im)
    L = luminance(from_pil(im.crop((int(W * .2), int(H * .3), int(W * .8), int(H * .6))))).mean()
    fg = (255, 255, 255) if L < 0.55 else (12, 12, 14)
    f1 = font(int(W * 0.052))
    d.text((W / 2, H * zone_y), headline, fill=fg, font=f1, anchor="mm")
    if sub:
        d.text((W / 2, H * zone_y + W * 0.05), sub, fill=fg + (200,), font=font(int(W * 0.018)), anchor="mm")
    # pill CTA
    bw, bh = W * 0.13, W * 0.032
    cy = H * zone_y + W * (0.095 if sub else 0.06)
    d.rounded_rectangle((W / 2 - bw / 2, cy - bh / 2, W / 2 + bw / 2, cy + bh / 2), radius=bh / 2,
                        fill=fg)
    d.text((W / 2, cy), "Get started", fill=(12, 12, 14) if fg[0] > 128 else (255, 255, 255),
           font=font(int(W * 0.014)), anchor="mm")
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--labels", nargs="*")
    ap.add_argument("--headline")
    ap.add_argument("--sub")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--tile", type=int, default=960)
    a = ap.parse_args()
    tiles = []
    for i, p in enumerate(a.images):
        im = Image.open(p).convert("RGB")
        im = im.resize((a.tile, round(im.height * a.tile / im.width)), Image.LANCZOS)
        if a.headline:
            im = mock_hero(im, a.headline, a.sub)
        tiles.append(im)
    th = max(t.height for t in tiles)
    pad, lab = 24, 44
    cols = min(a.cols, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * a.tile + (cols + 1) * pad, rows * (th + lab) + (rows + 1) * pad), (18, 18, 20))
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(tiles):
        x = pad + (i % cols) * (a.tile + pad)
        y = pad + (i // cols) * (th + lab + pad)
        sheet.paste(t, (x, y))
        label = (a.labels[i] if a.labels and i < len(a.labels) else os.path.basename(a.images[i]))
        d.text((x + 2, y + th + 10), label, fill=(235, 235, 240), font=font(22))
    sheet.save(a.out, quality=88)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
