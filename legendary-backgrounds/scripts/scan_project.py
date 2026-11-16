#!/usr/bin/env python3
"""Scan a project for the context a landing-page background should be built from.

  scan_project.py [project_dir]   -> JSON on stdout

Reports: framework + where the hero lives, public/static dir, brand colours (CSS custom properties,
Tailwind config, theme files, frequency-ranked hex/rgb/hsl/oklch literals), fonts, light/dark
default, product name + tagline + headline candidates (README, package.json, meta tags, <h1>),
logo/brand assets, and any existing hero background images. Read-only; skips node_modules etc.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

SKIP = {"node_modules", ".git", ".next", "dist", "build", ".turbo", ".vercel", ".svelte-kit", "out",
        "coverage", ".cache", "vendor", "Pods", ".expo", "target", "__pycache__", ".venv", "venv"}
TEXT_EXT = {".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".astro",
            ".html", ".md", ".mdx", ".json", ".toml", ".yaml", ".yml", ".liquid", ".erb", ".php"}
HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
VAR = re.compile(r"--([\w-]*(?:primary|accent|brand|secondary|background|foreground|bg|fg|ring|highlight)[\w-]*)\s*:\s*([^;]+);", re.I)
FONT = re.compile(r"(?:font-family\s*:\s*|fontFamily[^\[]*\[\s*|next/font/google['\"];?[\s\S]{0,40}?import\s*\{\s*)([\"']?[\w \-]+)", re.I)
GOOGLE_FONT = re.compile(r"import\s*\{\s*([\w_, ]+)\}\s*from\s*['\"]next/font/google['\"]")


def walk(root, max_files=4000):
    n = 0
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP and not x.startswith(".")]
        for f in files:
            n += 1
            if n > max_files:
                return
            yield os.path.join(d, f)


def read(p, limit=400_000):
    try:
        with open(p, "r", errors="ignore") as fh:
            return fh.read(limit)
    except OSError:
        return ""


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    out = {"root": root, "framework": None, "hero_candidates": [], "public_dir": None, "styling": [],
           "brand_vars": {}, "colors_ranked": [], "fonts": [], "theme_hint": None, "name": None,
           "description": None, "headlines": [], "logos": [], "existing_backgrounds": [], "readme_excerpt": None}
    pkg = {}
    if os.path.exists(os.path.join(root, "package.json")):
        try:
            pkg = json.load(open(os.path.join(root, "package.json")))
        except Exception:
            pkg = {}
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    for fw, key in (("next", "next"), ("astro", "astro"), ("sveltekit", "@sveltejs/kit"), ("nuxt", "nuxt"),
                    ("remix", "@remix-run/react"), ("gatsby", "gatsby"), ("vite-react", "vite"), ("vue", "vue")):
        if key in deps:
            out["framework"] = fw
            break
    if not out["framework"]:
        if os.path.exists(os.path.join(root, "index.html")):
            out["framework"] = "static-html"
        elif any(os.path.exists(os.path.join(root, f)) for f in ("Gemfile", "config.ru")):
            out["framework"] = "rails"
    if "tailwindcss" in deps:
        out["styling"].append("tailwind" + ("-v4" if str(deps["tailwindcss"]).lstrip("^~").startswith("4") else ""))
    for k in ("styled-components", "@emotion/react", "sass", "@vanilla-extract/css", "framer-motion", "motion", "gsap"):
        if k in deps:
            out["styling"].append(k)
    out["name"] = pkg.get("name")
    out["description"] = pkg.get("description")
    for pd in ("public", "static", "assets", "src/assets", "app/assets/images"):
        if os.path.isdir(os.path.join(root, pd)):
            out["public_dir"] = pd
            break

    hexes = collections.Counter()
    fonts = collections.Counter()
    dark_votes = 0
    for p in walk(root):
        rel = os.path.relpath(p, root)
        ext = os.path.splitext(p)[1].lower()
        low = rel.lower()
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg"):
            b = os.path.basename(low)
            if "logo" in b or "brand" in b or "icon" in b and ext == ".svg" or b.startswith("favicon"):
                out["logos"].append(rel)
            if any(k in b for k in ("hero", "background", "bg-", "-bg", "backdrop", "banner")):
                out["existing_backgrounds"].append(rel)
            continue
        if ext not in TEXT_EXT:
            continue
        txt = read(p)
        if not txt:
            continue
        if re.search(r"(^|/)(page|index|home|landing|hero)[^/]*\.(tsx|jsx|astro|vue|svelte|html)$", low) or \
                re.search(r"hero", os.path.basename(low)):
            score = 3 * bool(re.search(r"hero", low)) + 2 * ("<h1" in txt or "h1" in txt) + (low.count("/") < 4)
            out["hero_candidates"].append((score, rel))
        if ext in (".css", ".scss", ".sass", ".less") or "tailwind.config" in low or "theme" in low or "tokens" in low:
            for m in VAR.finditer(txt):
                out["brand_vars"].setdefault(m.group(1), m.group(2).strip()[:60])
            for h in HEX.findall(txt):
                hexes[h.lower()] += 3
        elif ext in (".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html"):
            for h in HEX.findall(txt):
                hexes[h.lower()] += 1
            for m in re.finditer(r"<h1[^>]*>([\s\S]{3,160}?)</h1>", txt):
                t = re.sub(r"<[^>]+>|\{[^}]*\}", " ", m.group(1))
                t = re.sub(r"\s+", " ", t).strip()
                if len(t) > 3:
                    out["headlines"].append(t)
            for m in re.finditer(r"<meta[^>]+(?:name|property)=[\"'](?:og:)?description[\"'][^>]+content=[\"']([^\"']+)", txt):
                out["description"] = out["description"] or m.group(1)
            m = re.search(r"description:\s*[\"'`]([^\"'`]{10,200})", txt)
            if m and not out["description"]:
                out["description"] = m.group(1)
        for m in GOOGLE_FONT.finditer(txt):
            for f in m.group(1).split(","):
                if f.strip():
                    fonts[f.strip().replace("_", " ")] += 5
        for m in re.finditer(r"font-family\s*:\s*([^;]+);", txt):
            fonts[m.group(1).split(",")[0].strip(" '\"")] += 1
        if re.search(r"class(Name)?=[\"'][^\"']*\bdark\b|colorScheme:\s*['\"]dark|bg-(black|zinc-9|neutral-9|slate-9|gray-9)", txt):
            dark_votes += 1
        if re.search(r"bg-white|background:\s*#fff\b|colorScheme:\s*['\"]light", txt):
            dark_votes -= 1
    for f in ("README.md", "readme.md", "README.mdx"):
        if os.path.exists(os.path.join(root, f)):
            r = read(os.path.join(root, f), 6000)
            out["readme_excerpt"] = re.sub(r"\n{3,}", "\n\n", r)[:1800]
            t = re.search(r"^#\s+(.+)$", r, re.M)
            if t and not out["name"]:
                out["name"] = t.group(1).strip()
            break
    neutral = {"#fff", "#ffffff", "#000", "#000000"}
    out["colors_ranked"] = [h for h, _ in hexes.most_common(24) if h not in neutral][:14]
    out["fonts"] = [f for f, _ in fonts.most_common(6) if f and not f.startswith("var(")]
    bgv = next((v for k, v in out["brand_vars"].items() if re.fullmatch(r"(color-)?(background|bg)", k, re.I)), None)
    m = HEX.search(bgv or "")
    if m:  # the declared page background is the strongest signal
        h = m.group(0).lstrip("#")
        h = "".join(c * 2 for c in h) if len(h) == 3 else h
        lum = sum(int(h[i:i + 2], 16) * w for i, w in ((0, .2126), (2, .7152), (4, .0722))) / 255
        dark_votes += 3 if lum < 0.35 else -3
    out["theme_hint"] = "dark" if dark_votes > 1 else "light" if dark_votes < -1 else "unknown"
    out["hero_candidates"] = [r for _, r in sorted(out["hero_candidates"], reverse=True)[:6]]
    out["headlines"] = list(dict.fromkeys(out["headlines"]))[:6]
    out["logos"] = out["logos"][:10]
    out["existing_backgrounds"] = out["existing_backgrounds"][:10]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
