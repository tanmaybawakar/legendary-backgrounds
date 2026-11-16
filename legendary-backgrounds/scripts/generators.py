"""Procedural background families, distilled from the Premium AI Backgrounds library.

Each generator: fn(w, h, p, rng) -> float32 (h, w, 3) image in [0, 1].
`p` is the recipe's "params" dict; every key has a sensible default so a recipe can be tiny.
Geometry uses normalised coords (y in [-1, 1], x in [-aspect, aspect]) so a recipe recomposes
cleanly for desktop (16:10) and mobile (9:19.5) renders.
"""
from __future__ import annotations

import math
import numpy as np

from lbg_core import (apply_lut, bilinear_sample, catmull_rom, coords, domain_warp, gaussian_blur,
                      palette_lut, polyline_distance, resize_field, smoothstep, spectrum, thermal_lut,
                      tonemap, value_fbm)

DEFAULT_PALETTES = {
    "glow": ["#030308", "#0a1a5c", "#2f5bff", "#9b7bff", "#ffffff"],
    "mesh": ["#1a1f6b", "#ff5a8a", "#ff9e5e", "#5b6cff", "#7fe7ff"],
    "liquid": ["#1b1530", "#3c2a6e", "#c05bd6", "#ffb08a", "#fff3d6"],
    "thermal": ["#2a1fd6", "#7a2cff", "#ff2bd6", "#ff3b1f", "#ffb000", "#5cff7a"],
    "iridescent": ["#fbfaff", "#e9ecff"],
    "waves": ["#000000", "#2a0b4a", "#6a2a9c", "#ff4f6a", "#ff9a3c", "#ffe9a8"],
    "terrain": ["#020403", "#0f3d12", "#3f8f2a", "#a8e05a", "#f0ffd0"],
}


def _work_size(w, h, max_w):
    s = min(1.0, max_w / w)
    return max(8, int(w * s)), max(8, int(h * s))


def _per_channel(intensity_fn, disp, lut, lut2=None, side=None):
    """Evaluate intensity with a per-channel offset -> prismatic fringes, then colour via LUT."""
    out = []
    for k, off in enumerate((-disp, 0.0, disp)):
        I = intensity_fn(off)
        col = apply_lut(tonemap(I), lut)[..., k]
        if lut2 is not None and side is not None:
            col2 = apply_lut(tonemap(I), lut2)[..., k]
            col = col * (1 - side) + col2 * side
        out.append(col)
    return np.stack(out, axis=2)


# --------------------------------------------------------------------------------- glow


def glow(w, h, p, rng):
    """Dark field with one luminous form: arc / dome / hourglass / ribbon / bolt / horizon."""
    W, H = _work_size(w, h, p.get("work_width", 1400))
    X, Y = coords(W, H)
    a = W / H
    shape = p.get("shape", "arc")
    lut = palette_lut(p.get("palette", DEFAULT_PALETTES["glow"]))
    lut2 = palette_lut(p["palette2"]) if p.get("palette2") else None
    disp = float(p.get("dispersion", 0.02))
    gain = float(p.get("intensity", 1.6))
    side_mask = None

    if p.get("flip"):
        Y = -Y
    if p.get("mirror"):
        X = -X

    if shape in ("arc", "dome", "horizon"):
        # circle whose top edge is the luminous rim. dome = lit inside (seen from below).
        R = float(p.get("radius", 1.7 if shape == "arc" else 1.5))
        if shape == "horizon":
            R = float(p.get("radius", 8.0))
        top = float(p.get("edge_y", 0.15 if shape != "dome" else 0.35))
        cx = float(p.get("cx", 0.0))
        cy = top + R
        r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        rim_out = float(p.get("rim_out", 0.10))
        rim_in = float(p.get("rim_in", 0.30))
        fill = float(p.get("fill", 0.55 if shape == "dome" else 0.25))
        fill_w = float(p.get("fill_width", 0.9))
        spread = float(p.get("spread", 1.1)) * a
        hf = 0.35 + 0.65 * np.exp(-((X - cx) / spread) ** 2)

        dome = shape == "dome"

        def I(off):
            d = r - R + off
            rim = np.where(d > 0, np.exp(-(d / rim_out) ** 2), np.exp(-(d / rim_in) ** 2))
            if dome:  # seen from inside: brightest deep inside, coloured rim, black outside
                inside = np.where(d < 0, fill * (1 - np.exp(d / fill_w)) * 1.6, 0.0)
                return gain * hf * (rim * 0.75 + inside)
            inside = np.where(d < 0, fill * np.exp(d / fill_w), 0.0)
            return gain * hf * (rim + inside)

    elif shape == "hourglass":
        R = float(p.get("radius", 1.25))
        gap = float(p.get("gap", 0.14))
        cy = R + gap
        soft = float(p.get("softness", 0.22))
        d1 = np.sqrt(X ** 2 + (Y + cy) ** 2) - R
        d2 = np.sqrt(X ** 2 + (Y - cy) ** 2) - R
        g = np.minimum(d1, d2)

        def I(off):
            lit = smoothstep(-soft * 0.3, soft, g + off)
            core = 0.55 + 0.45 * np.exp(-(X / (0.9 * a)) ** 2)
            hot = 0.9 * np.exp(-(Y / 0.10) ** 2) * np.exp(-(X / (0.55 * a)) ** 2)
            return gain * lit * (core + hot)

    elif shape in ("ribbon", "bolt"):
        if "points" in p:
            pts = np.asarray(p["points"], np.float32) * np.array([a, 1.0], np.float32)
        elif shape == "ribbon":
            ys = rng.uniform(-0.6, 0.6, 3)
            pts = np.array([[-1.3 * a, 0.95], [-0.4 * a, ys[0]], [0.35 * a, ys[1] - 0.4],
                            [1.3 * a, -0.95]], np.float32)
        else:  # bolt: a jagged Z of light
            n = int(p.get("segments", 5))
            xs = np.linspace(-0.2, 0.6, n) * a + rng.uniform(-0.12, 0.12, n) * a
            ys = np.linspace(-1.15, 1.15, n)
            xs[1::2] -= 0.35 * a
            pts = np.stack([xs, ys], 1).astype(np.float32)
        curve = catmull_rom(pts, 40) if shape == "ribbon" else pts
        d, s = polyline_distance(X, Y, curve)
        width = float(p.get("width", 0.16 if shape == "ribbon" else 0.22))
        asym = float(p.get("asymmetry", 0.45))
        wa, wb = width * (1 + asym), width * (1 - asym)
        halo = float(p.get("halo", 0.5))
        # nearest-segment side flips at outer corners; blur it so neither colour split nor width cracks
        s_soft = np.clip(gaussian_blur(s.astype(np.float32), W * 0.025) * 1.5, -1, 1)
        side_mask = (0.5 - 0.5 * s_soft) if lut2 is not None else None
        ww = wb + (wa - wb) * (0.5 + 0.5 * s_soft)

        def I(off):
            k = 1 + off * 4  # per-channel width -> prismatic fringe on both edges
            return gain * (np.exp(-(d / (ww * k)) ** 2) + halo * 0.35 * np.exp(-d / (ww * k * 3)))
    else:
        raise ValueError(f"unknown glow shape {shape}")

    img = _per_channel(I, disp, lut, lut2, side_mask)
    if p.get("bloom", 0.35) > 0:
        img = img + float(p.get("bloom", 0.35)) * gaussian_blur(img, W * 0.03) * 0.6
    return resize_field(np.clip(img, 0, 1), w, h)


# --------------------------------------------------------------------------------- mesh


def mesh(w, h, p, rng):
    """Soft, airy blob gradient (Stripe / Apple-ish). Background = palette[0]."""
    W, H = _work_size(w, h, 480)
    X, Y = coords(W, H)
    a = W / H
    cols = [np.asarray(c, np.float32) for c in palette_lut(p.get("palette", DEFAULT_PALETTES["mesh"]),
                                                            len(p.get("palette", DEFAULT_PALETTES["mesh"])))]
    warp = float(p.get("warp", 0.35))
    nx = (value_fbm(W, H, rng, 1.6, 3) - 0.5) * warp * 2
    ny = (value_fbm(W, H, rng, 1.6, 3) - 0.5) * warp * 2
    Xw, Yw = X + nx * a, Y + ny
    blobs = p.get("blobs")
    if blobs is None:
        blobs = [[float(rng.uniform(-0.8, 0.8)), float(rng.uniform(-0.8, 0.8)), float(rng.uniform(0.5, 0.9))]
                 for _ in cols[1:]]
    num = np.zeros((H, W, 3), np.float32)
    den = np.zeros((H, W), np.float32)
    bg_w = float(p.get("background_weight", 0.25))
    num += cols[0] * bg_w
    den += bg_w
    for c, (bx, by, br) in zip(cols[1:] * 3, blobs):
        wgt = np.exp(-(((Xw - bx * a) ** 2 + (Yw - by) ** 2) / (br * br)) * 2.2)
        num += c * wgt[..., None]
        den += wgt
    img = num / den[..., None]
    return resize_field(img, w, h)


# --------------------------------------------------------------------------------- liquid


def liquid(w, h, p, rng):
    """Domain-warped flowing colour. mode=field (marbled) | ridge (aurora ribbons on dark)."""
    W, H = _work_size(w, h, p.get("work_width", 700))
    f = domain_warp(W, H, rng, float(p.get("scale", 1.6)), 5, float(p.get("warp", 0.35)), int(p.get("iterations", 2)))
    mode = p.get("mode", "field")
    if mode == "ridge":
        t = 1 - np.abs(2 * f - 1)
        t = np.clip(t, 0, 1) ** float(p.get("sharpness", 3.0))
    else:
        t = f
        c = float(p.get("contrast", 1.0))
        t = np.clip(0.5 + (t - 0.5) * c, 0, 1)
    lut = palette_lut(p.get("palette", DEFAULT_PALETTES["liquid"]))
    img = apply_lut(t, lut)
    return resize_field(img, w, h)


# --------------------------------------------------------------------------------- thermal


def thermal(w, h, p, rng):
    """Psychedelic heat-map fluid. mode=full (iso-bands everywhere) | edge (glowing coastline on black)."""
    W, H = _work_size(w, h, p.get("work_width", 800))
    f = domain_warp(W, H, rng, float(p.get("scale", 1.8)), 6, float(p.get("warp", 0.4)), 2)
    mode = p.get("mode", "full")
    if mode == "edge":
        thr = float(p.get("threshold", 0.55))
        wdt = float(p.get("width", 0.06))
        I = np.exp(-((f - thr) / wdt) ** 2) + 0.55 * np.exp(-((f - thr - wdt * 2.2) / (wdt * 0.6)) ** 2)
        lut = palette_lut(["#000000"] + p.get("palette", ["#1a0a6b", "#3d2bff", "#b63cff", "#ff2b6a", "#ff7a00", "#ffd200", "#fffbe0"]))
        img = apply_lut(tonemap(I, 1.4), lut)
    else:
        cyc = float(p.get("cycles", 1.6))
        pal = p.get("palette", DEFAULT_PALETTES["thermal"])
        lut = palette_lut(list(pal) + [pal[0]])  # cyclic
        img = apply_lut((f * cyc + float(p.get("offset", 0.0))) % 1.0, lut)
    return resize_field(img, w, h)


# --------------------------------------------------------------------------------- iridescent


def iridescent(w, h, p, rng):
    """Light, airy base with thin prismatic / holographic bands along a curve or arch."""
    X, Y = coords(*_work_size(w, h, 1600))
    H_, W_ = X.shape
    a = W_ / H_
    pal = p.get("palette", DEFAULT_PALETTES["iridescent"])
    base = apply_lut(np.clip((Y + 1) / 2, 0, 1), palette_lut(pal))
    shape = p.get("shape", "ribbon")
    if shape == "arch":
        R = float(p.get("radius", 1.9))
        cy = float(p.get("edge_y", -0.6)) + R
        sd = np.sqrt(X ** 2 + (Y - cy) ** 2) - R
        env = np.exp(-(np.maximum(sd, 0) / float(p.get("width", 0.5))) ** 1.4) * smoothstep(-0.25, 0.05, sd)
    else:
        if "points" in p:
            pts = np.asarray(p["points"], np.float32) * np.array([a, 1.0], np.float32)
        else:
            pts = np.array([[-1.2 * a, -0.2], [-0.45 * a, 0.55], [0.3 * a, 0.25], [1.25 * a, -0.85]], np.float32)
        d, s = polyline_distance(X, Y, catmull_rom(pts, 40))
        sd = d * s
        env = np.exp(-(d / float(p.get("width", 0.22))) ** 2)
    period = float(p.get("period", 0.45))
    spec = spectrum(sd / period + float(p.get("phase", 0.1)))
    sat = float(p.get("saturation", 0.55))
    band = 1 - sat + sat * spec
    strength = float(p.get("strength", 0.85))
    img = base * (1 - env[..., None] * strength) + band * base * env[..., None] * strength
    # soft cool haze so it never reads as flat white
    haze = gaussian_blur(env, W_ * 0.06)[..., None]
    img = img * (1 - 0.12 * haze) + np.array([0.75, 0.82, 1.0], np.float32) * 0.12 * haze
    return resize_field(np.clip(img, 0, 1), w, h)


# --------------------------------------------------------------------------------- waves


def waves(w, h, p, rng):
    """Glowing wave ridge(s) on black: a luminous horizon with a dusk fill beneath."""
    W, H = _work_size(w, h, 1400)
    X, Y = coords(W, H)
    a = W / H
    lut = palette_lut(p.get("palette", DEFAULT_PALETTES["waves"]))
    y0 = float(p.get("horizon", 0.05))
    amp = float(p.get("amplitude", 0.09))
    layers = int(p.get("layers", 2))
    I = np.zeros_like(X)
    for k in range(layers):
        ph = rng.uniform(0, 6.28, 3)
        fr = np.array([1.1, 2.3, 4.1]) * float(p.get("frequency", 1.0)) / a * 2.2
        ridge = y0 + k * 0.07 + amp * (np.sin(X * fr[0] + ph[0]) + 0.45 * np.sin(X * fr[1] + ph[1])
                                       + 0.18 * np.sin(X * fr[2] + ph[2])) / (1 + k * 0.4)
        d = Y - ridge
        line = np.where(d < 0, np.exp(d / 0.035), np.exp(-d / 0.05))
        fill = np.where(d > 0, np.exp(-d / float(p.get("fill_depth", 0.5))) * 0.55, 0)
        crest = 0.6 * np.exp(-((ridge - ridge.min()) / (amp * 0.6)) ** 2) * np.exp(-np.abs(d) / 0.03)
        I = np.maximum(I, (line * 1.2 + fill + crest) / (1 + k * 0.6))
    img = apply_lut(tonemap(I * float(p.get("intensity", 1.5))), lut)
    img = img + 0.4 * gaussian_blur(img, W * 0.02)
    return resize_field(np.clip(img, 0, 1), w, h)


# --------------------------------------------------------------------------------- terrain


def terrain(w, h, p, rng):
    """Particle heightfield rolling into a black void (point-cloud hills)."""
    lut = palette_lut(p.get("palette", DEFAULT_PALETTES["terrain"]))
    # densities are specified for a 960x600 frame; scale so finals look like previews
    nx = int(p.get("density_x", 1100) * w / 960)
    nz = int(p.get("density_z", 520) * h / 600)
    hf = value_fbm(512, 512, rng, 3.0, 5)
    Xw = np.linspace(-7, 7, nx, dtype=np.float32)
    Zw = np.geomspace(1.2, float(p.get("far", 16.0)), nz).astype(np.float32)
    amp = float(p.get("amplitude", 1.1))
    camY = float(p.get("camera_height", 1.6))
    horizon = float(p.get("horizon", -0.15))  # normalised screen y of the vanishing line
    focal = float(p.get("focal", 1.0)) * h * 0.5
    acc = np.zeros((h, w, 3), np.float32)
    sky = np.full(w, np.inf, np.float32)
    cols_x = np.arange(w, dtype=np.float32)
    for z in Zw:  # near -> far; per-column skyline gives cheap occlusion
        hx = (Xw / 14 + 0.5) * 511
        hz = np.full_like(Xw, (z / Zw[-1]) * 511)
        Hh = bilinear_sample(hf, hx, hz) * amp
        sx = w / 2 + Xw / z * focal
        sy = h / 2 + horizon * h / 2 + (camY - Hh) / z * focal
        order = np.argsort(sx)
        line = np.interp(cols_x, sx[order], sy[order], left=np.inf, right=np.inf)
        ix = np.clip(sx.astype(np.int32), 0, w - 1)
        iy = sy.astype(np.int32)
        vis = (sx >= 0) & (sx < w) & (iy >= 0) & (iy < h) & (sy <= sky[ix] + 1)
        if vis.any():
            fog = math.exp(-z / float(p.get("fog", 7.0)))
            c = apply_lut(np.clip(Hh[vis] / amp * 0.9 + 0.1, 0, 1), lut) * (fog * float(p.get("brightness", 1.6)))
            np.add.at(acc, (iy[vis], ix[vis]), c)
        sky = np.minimum(sky, line)
    img = acc + 0.9 * gaussian_blur(acc, w * 0.0025) + 0.35 * gaussian_blur(acc, w * 0.02)
    bg = np.asarray(lut[0], np.float32)
    return np.clip(bg + tonemap(img, 1.2), 0, 1)


GENERATORS = {
    "glow": glow,
    "mesh": mesh,
    "liquid": liquid,
    "thermal": thermal,
    "iridescent": iridescent,
    "waves": waves,
    "terrain": terrain,
}
