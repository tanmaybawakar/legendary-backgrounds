"""Shared primitives for the legendary-backgrounds engine.

Everything works on float32 numpy arrays in linear-ish sRGB [0, 1], shape (H, W, 3).
All randomness is seeded so a recipe renders identically every time.
"""
from __future__ import annotations

import math
import numpy as np
from PIL import Image

# ----------------------------------------------------------------------------- colour


def hex_to_rgb(h: str) -> np.ndarray:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


def rgb_to_hex(c) -> str:
    c = np.clip(np.asarray(c, dtype=np.float32), 0, 1)
    return "#" + "".join(f"{int(round(v * 255)):02x}" for v in c)


def _srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _lin_to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def srgb_to_oklab(c):
    l = _srgb_to_lin(np.asarray(c, dtype=np.float32))
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]], dtype=np.float32)
    lms = np.cbrt(l @ m1.T)
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]], dtype=np.float32)
    return lms @ m2.T


def oklab_to_srgb(c):
    m2i = np.array([[1.0, 0.3963377774, 0.2158037573],
                    [1.0, -0.1055613458, -0.0638541728],
                    [1.0, -0.0894841775, -1.2914855480]], dtype=np.float32)
    lms = (np.asarray(c, dtype=np.float32) @ m2i.T) ** 3
    m1i = np.array([[4.0767416621, -3.3077115913, 0.2309699292],
                    [-1.2684380046, 2.6097574011, -0.3413193965],
                    [-0.0041960863, -0.7034186147, 1.7076147010]], dtype=np.float32)
    return np.clip(_lin_to_srgb(lms @ m1i.T), 0, 1)


def palette_lut(colors, n: int = 1024, stops=None) -> np.ndarray:
    """Perceptually smooth gradient LUT (n, 3) through the given hex colours (OKLab)."""
    cols = np.stack([hex_to_rgb(c) if isinstance(c, str) else np.asarray(c, np.float32) for c in colors])
    if len(cols) == 1:
        return np.repeat(cols, n, axis=0)
    lab = srgb_to_oklab(cols)
    pos = np.linspace(0, 1, len(cols)) if stops is None else np.asarray(stops, np.float32)
    t = np.linspace(0, 1, n, dtype=np.float32)
    out = np.stack([np.interp(t, pos, lab[:, k]) for k in range(3)], axis=1)
    return oklab_to_srgb(out).astype(np.float32)


def apply_lut(field: np.ndarray, lut: np.ndarray) -> np.ndarray:
    idx = np.clip(field, 0, 1) * (len(lut) - 1)
    i0 = np.floor(idx).astype(np.int32)
    i1 = np.minimum(i0 + 1, len(lut) - 1)
    f = (idx - i0)[..., None]
    return lut[i0] * (1 - f) + lut[i1] * f


def luminance(img: np.ndarray) -> np.ndarray:
    return img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722


def spectrum(t: np.ndarray) -> np.ndarray:
    """Smooth rainbow (iridescent) colour for t in any range (periodic, 1 = full cycle)."""
    t = t[..., None] * 2 * math.pi
    ph = np.array([0.0, 2.094, 4.188], dtype=np.float32)
    return (0.5 + 0.5 * np.cos(t + ph)).astype(np.float32)


def thermal_lut(n: int = 1024) -> np.ndarray:
    return palette_lut(["#0b0630", "#2a1fd6", "#7a2cff", "#ff2bd6", "#ff3b1f", "#ffb000", "#fff6a8"], n)


# ----------------------------------------------------------------------------- geometry


def coords(w: int, h: int):
    """Normalised coordinates: y in [-1, 1] (down is +), x scaled by aspect."""
    a = w / h
    xs = np.linspace(-a, a, w, dtype=np.float32)
    ys = np.linspace(-1, 1, h, dtype=np.float32)
    return np.meshgrid(xs, ys)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


def polyline_distance(X, Y, pts):
    """Unsigned distance from every (X, Y) to a polyline, plus signed side (+/-)."""
    pts = np.asarray(pts, dtype=np.float32)
    best = np.full(X.shape, np.inf, dtype=np.float32)
    side = np.zeros(X.shape, dtype=np.float32)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy + 1e-12
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        px, py = ax + t * dx - X, ay + t * dy - Y
        d = np.sqrt(px * px + py * py)
        cross = dx * (Y - ay) - dy * (X - ax)
        m = d < best
        best = np.where(m, d, best)
        side = np.where(m, np.sign(cross), side)
    return best, side


def catmull_rom(points, samples: int = 24):
    p = np.asarray(points, dtype=np.float32)
    p = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, samples, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.asarray(out, dtype=np.float32)


# ----------------------------------------------------------------------------- noise


def resize_field(a: np.ndarray, w: int, h: int, resample=Image.BICUBIC) -> np.ndarray:
    if a.ndim == 2:
        return np.asarray(Image.fromarray(a.astype(np.float32), mode="F").resize((w, h), resample), dtype=np.float32)
    return np.stack([resize_field(a[..., k], w, h, resample) for k in range(a.shape[2])], axis=2)


def value_fbm(w: int, h: int, rng: np.random.Generator, base: float = 3.0, octaves: int = 5,
              gain: float = 0.5, lacunarity: float = 2.0) -> np.ndarray:
    """Smooth fractal noise in [0, 1] built from bicubically upsampled random grids."""
    acc = np.zeros((h, w), dtype=np.float32)
    amp, freq, tot = 1.0, base, 0.0
    a = w / h
    for _ in range(octaves):
        gh = max(2, int(round(freq)) + 2)
        gw = max(2, int(round(freq * a)) + 2)
        grid = rng.random((gh, gw)).astype(np.float32)
        # oversize then crop so the grid border does not show
        big = resize_field(grid, int(w * gw / (gw - 1.5)), int(h * gh / (gh - 1.5)))
        oy, ox = (big.shape[0] - h) // 2, (big.shape[1] - w) // 2
        acc += amp * big[oy:oy + h, ox:ox + w]
        tot += amp
        amp *= gain
        freq *= lacunarity
    acc /= tot
    lo, hi = np.percentile(acc, 0.5), np.percentile(acc, 99.5)
    return np.clip((acc - lo) / (hi - lo + 1e-9), 0, 1)


def bilinear_sample(field: np.ndarray, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Sample a 2-D field at fractional pixel coords (clamped)."""
    h, w = field.shape[:2]
    X = np.clip(X, 0, w - 1.001)
    Y = np.clip(Y, 0, h - 1.001)
    x0 = np.floor(X).astype(np.int32)
    y0 = np.floor(Y).astype(np.int32)
    fx, fy = X - x0, Y - y0
    if field.ndim == 3:
        fx, fy = fx[..., None], fy[..., None]
    a = field[y0, x0]
    b = field[y0, x0 + 1]
    c = field[y0 + 1, x0]
    d = field[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def domain_warp(w: int, h: int, rng, base=2.0, octaves=5, warp=0.35, iterations=2) -> np.ndarray:
    """Inigo-Quilez style warped fbm: organic liquid / marble fields in [0, 1]."""
    f = value_fbm(w, h, rng, base, octaves)
    Xg, Yg = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    for _ in range(iterations):
        qx = value_fbm(w, h, rng, base, octaves) - 0.5
        qy = value_fbm(w, h, rng, base, octaves) - 0.5
        f = bilinear_sample(f, Xg + qx * warp * w, Yg + qy * warp * h)
    lo, hi = np.percentile(f, 0.5), np.percentile(f, 99.5)
    return np.clip((f - lo) / (hi - lo + 1e-9), 0, 1)


# ----------------------------------------------------------------------------- image io


def to_pil(img: np.ndarray) -> Image.Image:
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")


def from_pil(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0


def gaussian_blur(img: np.ndarray, radius: float) -> np.ndarray:
    from scipy.ndimage import gaussian_filter
    if radius <= 0:
        return img
    if img.ndim == 2:
        return gaussian_filter(img, radius, mode="nearest")
    return np.stack([gaussian_filter(img[..., k], radius, mode="nearest") for k in range(img.shape[2])], 2)


def tonemap(x: np.ndarray, exposure: float = 1.0) -> np.ndarray:
    """Soft filmic shoulder so glows bloom to white without clipping harshly."""
    return 1 - np.exp(-np.clip(x, 0, None) * exposure)
