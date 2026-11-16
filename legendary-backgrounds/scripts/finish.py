#!/usr/bin/env python3
"""Finishing pass: the texture layer that makes the library look 'premium' instead of 'CSS gradient'.

Works on any image (procedural or Codex output). Every size is expressed relative to a 1920 px
wide frame and scaled to the real width, so a 960 px preview looks like the 5760 px final.

Ops (applied in order, each a dict with "op"):
  grade      {"colors": [hex...], "amount": 1}        map luminance onto a palette (duotone/tritone)
  levels     {"black": 0, "white": 1, "gamma": 1, "saturation": 1}
  bloom      {"radius": 40, "amount": 0.35, "threshold": 0.6}
  chroma     {"shift": 2}                             lateral chromatic aberration (px @1920)
  ascii      {"cell": 10, "strength": 0.6, "threshold": 0.18, "charset": " .:-=+*#%@", "color": "source"|"#hex"}
  halftone   {"cell": 9, "angle": 22, "strength": 1, "background": "auto"|"#hex"}
  dither     {"levels": 4, "pixel": 3, "strength": 1}  ordered Bayer posterise (retro print look)
  pixelate   {"pixel": 6, "colors": 48}               pixel-art
  grain      {"amount": 0.05, "size": 1.0, "mono": true}
  vignette   {"amount": 0.35, "softness": 0.6}
  scrim      {"rect": [x0,y0,x1,y1], "amount": 0.35, "feather": 0.25, "color": "#000"}  text safe-zone
  fade_edges {"top": 0, "bottom": 0.25, "color": "#000"}  blend into page background colour
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbg_core import (apply_lut, from_pil, gaussian_blur, hex_to_rgb, luminance, palette_lut,  # noqa: E402
                      smoothstep, to_pil)

FONT_CANDIDATES = [
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "C:/Windows/Fonts/consola.ttf",
]


def _px(v, img):
    """Sizes are authored for a 1920x1200 frame; scale by the short side so a portrait
    mobile render gets the same physical texture size as desktop."""
    H, W = img.shape[:2]
    return max(1.0, float(v) * min(W, H) / 1200.0)


def _rng(op):
    return np.random.default_rng(int(op.get("seed", 1234)))


# ------------------------------------------------------------------------------------------ ops


def op_grade(img, op):
    lut = palette_lut(op["colors"])
    g = apply_lut(luminance(img), lut)
    a = float(op.get("amount", 1.0))
    return img * (1 - a) + g * a


def op_levels(img, op):
    b, wt = float(op.get("black", 0)), float(op.get("white", 1))
    img = np.clip((img - b) / max(1e-6, wt - b), 0, 1) ** (1 / float(op.get("gamma", 1)))
    s = float(op.get("saturation", 1))
    if s != 1:
        L = luminance(img)[..., None]
        img = np.clip(L + (img - L) * s, 0, 1)
    return img


def op_bloom(img, op):
    W = img.shape[1]
    thr = float(op.get("threshold", 0.6))
    hi = np.clip((img - thr) / (1 - thr + 1e-6), 0, 1)
    b = gaussian_blur(hi, _px(op.get("radius", 40), img))
    return np.clip(img + b * float(op.get("amount", 0.35)), 0, 1)


def op_chroma(img, op):
    s = int(round(_px(op.get("shift", 2), img)))
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], s, axis=1)
    out[..., 2] = np.roll(img[..., 2], -s, axis=1)
    return out


def _font(size):
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except OSError:
                pass
    return ImageFont.load_default()


def op_ascii(img, op):
    """Glyphs whose density follows brightness, visible mostly inside the light (ASCII Magic look)."""
    H, W = img.shape[:2]
    cell = int(round(_px(op.get("cell", 10), img)))
    cw, ch = max(3, int(cell * 0.62)), max(4, cell)
    charset = op.get("charset", " .:-=+*#%@")
    font = _font(ch)
    atlas = np.zeros((len(charset), ch, cw), np.float32)
    for i, c in enumerate(charset):
        tile = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(tile).text((cw / 2, ch / 2), c, fill=255, font=font, anchor="mm")
        atlas[i] = np.asarray(tile, np.float32) / 255
    rows, cols = H // ch + 1, W // cw + 1
    small = np.asarray(to_pil(img).resize((cols, rows), Image.BOX), np.float32) / 255
    L = luminance(small)
    thr = float(op.get("threshold", 0.18))
    lv = np.clip((L - thr) / (1 - thr + 1e-6), 0, 1)
    # jitter per cell so flat gradients scatter into mixed glyphs instead of rows of "====="
    jit = (_rng(op).random(lv.shape).astype(np.float32) - 0.5) * float(op.get("jitter", 0.45))
    idx = np.clip(((lv + jit * (lv > 0.02)) * (len(charset) - 1)).round().astype(int), 0, len(charset) - 1)
    mask = atlas[idx].transpose(0, 2, 1, 3).reshape(rows * ch, cols * cw)[:H, :W]
    if op.get("color", "source") == "source":
        col = np.repeat(np.repeat(small, ch, 0), cw, 1)[:H, :W]
        col = np.clip(col * 1.35 + 0.08, 0, 1)
    else:
        col = np.broadcast_to(hex_to_rgb(op["color"]), img.shape)
    # glyphs ride on the light: strength scales with local brightness, dark stays clean
    weight = (smoothstep(thr * 0.6, 0.75, luminance(img)) * float(op.get("strength", 0.6)))[..., None]
    m = mask[..., None]
    mode = op.get("blend", "screen")
    if mode == "replace":  # pure ascii render: glyphs only
        return col * m * weight + img * (1 - weight)
    glyph = 1 - (1 - img) * (1 - col * m)  # screen the glyph colour on
    k = float(op.get("knockout", 0.35))     # darken the gaps between glyphs so the light reads as type
    out = img * (1 - weight * k * (1 - m))
    return out * (1 - weight * m) + glyph * weight * m


def op_halftone(img, op):
    """Rotated dot screen; dot radius follows brightness. Dots carry the image colour."""
    H, W = img.shape[:2]
    cell = _px(op.get("cell", 9), img)
    ang = np.deg2rad(float(op.get("angle", 22)))
    Yg, Xg = np.mgrid[0:H, 0:W].astype(np.float32)
    ca, sa = np.cos(ang), np.sin(ang)
    u = (Xg * ca + Yg * sa) / cell
    v = (-Xg * sa + Yg * ca) / cell
    cu, cv = np.round(u), np.round(v)
    du, dv = u - cu, v - cv
    dist = np.sqrt(du * du + dv * dv)
    cx = (cu * ca - cv * sa) * cell
    cy = (cu * sa + cv * ca) * cell
    blur = gaussian_blur(img, cell * 0.5)
    xi = np.clip(cx, 0, W - 1).astype(np.int32)
    yi = np.clip(cy, 0, H - 1).astype(np.int32)
    samp = blur[yi, xi]
    L = luminance(samp)
    r = np.sqrt(np.clip(L, 0, 1)) * 0.62 * float(op.get("gain", 1.1))
    aa = 1.0 / cell
    dot = smoothstep(r + aa, r - aa, dist)[..., None]
    bgc = op.get("background", "auto")
    bg = samp * 0.18 if bgc == "auto" else np.broadcast_to(hex_to_rgb(bgc), img.shape)
    out = bg * (1 - dot) + np.clip(samp * 1.15, 0, 1) * dot
    s = float(op.get("strength", 1.0))
    return img * (1 - s) + out * s


BAYER8 = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
                   [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
                   [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                   [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]], np.float32) / 64.0


def op_dither(img, op):
    H, W = img.shape[:2]
    px = max(1, int(round(_px(op.get("pixel", 3), img))))
    levels = max(2, int(op.get("levels", 4)))
    small = np.asarray(to_pil(img).resize((W // px + 1, H // px + 1), Image.BOX), np.float32) / 255
    h, w = small.shape[:2]
    t = np.tile(BAYER8, (h // 8 + 1, w // 8 + 1))[:h, :w][..., None] - 0.5
    q = np.floor(small * (levels - 1) + 0.5 + t) / (levels - 1)
    q = np.clip(q, 0, 1)
    big = np.repeat(np.repeat(q, px, 0), px, 1)[:H, :W]
    s = float(op.get("strength", 1.0))
    return img * (1 - s) + big * s


def op_pixelate(img, op):
    H, W = img.shape[:2]
    px = max(1, int(round(_px(op.get("pixel", 6), img))))
    im = to_pil(img).resize((max(1, W // px), max(1, H // px)), Image.BOX)
    n = int(op.get("colors", 48))
    if n:
        im = im.quantize(n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).convert("RGB")
    return from_pil(im.resize((W, H), Image.NEAREST))


def op_grain(img, op):
    H, W = img.shape[:2]
    rng = _rng(op)
    size = float(op.get("size", 1.0)) * min(W, H) / 1200
    gh, gw = max(1, int(H / max(size, 1))), max(1, int(W / max(size, 1)))
    if op.get("mono", True):
        n = rng.standard_normal((gh, gw)).astype(np.float32)
        n = np.asarray(Image.fromarray(n, "F").resize((W, H), Image.BILINEAR))[..., None]
    else:
        n = np.stack([np.asarray(Image.fromarray(rng.standard_normal((gh, gw)).astype(np.float32), "F")
                                 .resize((W, H), Image.BILINEAR)) for _ in range(3)], 2)
    L = luminance(img)[..., None]
    # film-like: strongest in the mid-tones, still present in the blacks
    env = 0.45 + 0.55 * (1 - np.abs(L * 2 - 1))
    return np.clip(img + n * float(op.get("amount", 0.05)) * env, 0, 1)


def op_vignette(img, op):
    H, W = img.shape[:2]
    Yg, Xg = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((Xg / W) - 0.5) ** 2 * 1.2 + ((Yg / H) - 0.5) ** 2 * 1.6)
    v = 1 - float(op.get("amount", 0.35)) * smoothstep(0.75 - float(op.get("softness", 0.6)), 0.85, d)
    return img * v[..., None]


def op_scrim(img, op):
    H, W = img.shape[:2]
    x0, y0, x1, y1 = op.get("rect", [0.15, 0.25, 0.85, 0.65])
    f = float(op.get("feather", 0.25))
    Yg, Xg = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = Xg / W, Yg / H
    m = smoothstep(x0 - f, x0 + f * 0.3, u) * smoothstep(x1 + f, x1 - f * 0.3, u) * \
        smoothstep(y0 - f, y0 + f * 0.3, v) * smoothstep(y1 + f, y1 - f * 0.3, v)
    c = hex_to_rgb(op.get("color", "#000000"))
    a = (m * float(op.get("amount", 0.35)))[..., None]
    return img * (1 - a) + c * a


def op_fade_edges(img, op):
    H = img.shape[0]
    c = hex_to_rgb(op.get("color", "#000000"))
    v = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    a = np.zeros_like(v)
    if op.get("top", 0):
        a = np.maximum(a, smoothstep(float(op["top"]), 0, v))
    if op.get("bottom", 0):
        a = np.maximum(a, smoothstep(1 - float(op["bottom"]), 1, v))
    return img * (1 - a) + c * a


OPS = {k[3:]: v for k, v in globals().items() if k.startswith("op_")}


def apply_finish(img: np.ndarray, ops) -> np.ndarray:
    for op in ops or []:
        name = op["op"]
        if name not in OPS:
            raise ValueError(f"unknown finish op '{name}'. Known: {sorted(OPS)}")
        img = np.clip(OPS[name](img, op), 0, 1).astype(np.float32)
    return img


def main():
    ap = argparse.ArgumentParser(description="Apply a finishing stack to any image.")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--ops", required=True, help="JSON list of ops, or path to a .json file")
    ap.add_argument("--width", type=int, help="resize to this width first (keeps aspect)")
    a = ap.parse_args()
    ops = json.load(open(a.ops)) if os.path.exists(a.ops) else json.loads(a.ops)
    if isinstance(ops, dict):
        ops = ops.get("finish", [])
    im = Image.open(a.input).convert("RGB")
    if a.width and im.width != a.width:
        im = im.resize((a.width, round(im.height * a.width / im.width)), Image.LANCZOS)
    out = apply_finish(from_pil(im), ops)
    to_pil(out).save(a.output, quality=95)
    print(a.output, out.shape[1], "x", out.shape[0])


if __name__ == "__main__":
    main()
