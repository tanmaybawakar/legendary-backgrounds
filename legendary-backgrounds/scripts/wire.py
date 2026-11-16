#!/usr/bin/env python3
"""Generate the hero-background component for a project from an export manifest.

  wire.py <export_dir>/<name>.manifest.json --framework react|html|astro \
      --public-url /backgrounds --component-dir src/components --live-dir src/lib [--no-live]

Writes:
  react : <component-dir>/<Component>.tsx + <name>.recipe.json, copies lbg-live.js (+ .d.ts) to <live-dir>
  astro : <component-dir>/<Component>.astro + recipe json, lbg-live.js to <live-dir>
  html  : prints the snippet (paste into the hero) and copies lbg-live.js to <live-dir>
The images themselves must already be in the public dir that serves --public-url (render.py --export there).
Prints a JSON summary incl. the text colour/contrast advice from the manifest.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "..", "templates")

DTS = """export function mountLegendaryBackground(container: HTMLElement, opts: {
  recipe: unknown; image?: string; speed?: number; maxDpr?: number; scale?: number; fadeMs?: number;
}): () => void;
export function recipeToUniforms(recipe: unknown): unknown;
"""


def pascal(name):
    return "".join(p.capitalize() for p in re.split(r"[^a-zA-Z0-9]+", name) if p) + "Background"


def prefixed(srcset, url):
    return ", ".join(f"{url}/{part.strip()}" for part in srcset.split(",") if part.strip())


def rel_import(from_dir, to_file):
    r = os.path.relpath(to_file, from_dir).replace(os.sep, "/")
    return r if r.startswith(".") else "./" + r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--framework", required=True, choices=["react", "html", "astro"])
    ap.add_argument("--public-url", required=True, help="URL prefix the exported files are served from, e.g. /backgrounds")
    ap.add_argument("--component-dir", default=".")
    ap.add_argument("--live-dir", default=None, help="where to copy lbg-live.js (default: component dir)")
    ap.add_argument("--live-import", default=None, help="override the import specifier (e.g. @/lib/lbg-live)")
    ap.add_argument("--component", default=None)
    ap.add_argument("--no-live", action="store_true")
    a = ap.parse_args()

    m = json.load(open(a.manifest))
    name = m["name"]
    url = a.public_url.rstrip("/")
    comp = a.component or pascal(name)
    cdir = os.path.abspath(a.component_dir)
    ldir = os.path.abspath(a.live_dir or a.component_dir)
    os.makedirs(cdir, exist_ok=True)
    os.makedirs(ldir, exist_ok=True)
    live_js = os.path.join(ldir, "lbg-live.js")
    if not a.no_live:
        shutil.copy(os.path.join(TPL, "lbg-live.js"), live_js)
        with open(os.path.join(ldir, "lbg-live.d.ts"), "w") as f:
            f.write(DTS)
    focus = m["recipe"].get("focus", [0.5, 0.5])
    tokens = {
        "__NAME__": name,
        "__COMPONENT__": comp,
        "__PUBLIC_URL__": url,
        "__PAGE_BG__": m.get("page_bg") or "#000",
        "__BLUR_DATA_URL__": m["blur_data_url"],
        "__OBJECT_POSITION__": f"{focus[0] * 100:.0f}% {focus[1] * 100:.0f}%",
        "__DESKTOP_AVIF_SRCSET__": prefixed(m["desktop"]["srcset"]["avif"], url),
        "__DESKTOP_WEBP_SRCSET__": prefixed(m["desktop"]["srcset"]["webp"], url),
        "__MOBILE_AVIF_SRCSET__": prefixed(m["mobile"]["srcset"]["avif"], url),
        "__MOBILE_WEBP_SRCSET__": prefixed(m["mobile"]["srcset"]["webp"], url),
        "__RECIPE_URL__": f"{url}/{name}.recipe.json",
    }
    # the 1920 fallback may not exist for small masters
    if f"{name}-desktop-1920.webp" not in m["desktop"]["srcset"]["webp"]:
        first = m["desktop"]["files"]["webp"][0][0]
        tokens["__PUBLIC_URL__/__NAME__-desktop-1920.webp"] = f"{url}/{first}"

    tpl = {"react": "LegendaryBackground.tsx", "astro": "LegendaryBackground.astro", "html": "hero-snippet.html"}[a.framework]
    s = open(os.path.join(TPL, tpl)).read()
    if a.framework == "html":
        imp = a.live_import or "/" + os.path.basename(live_js)
    else:
        imp = a.live_import or rel_import(cdir, live_js)
    tokens["__LIVE_IMPORT__"] = imp
    for k in sorted(tokens, key=len, reverse=True):
        s = s.replace(k, tokens[k])
    if a.no_live:
        s = re.sub(r"<script[\s\S]*?</script>\s*", "", s)
        s = s.replace("live = true", "live = false")
    left = sorted(set(re.findall(r"__[A-Z_]+__", s)))
    out = {"framework": a.framework, "component": comp, "live_js": None if a.no_live else live_js,
           "unfilled_tokens": left, "advice": m["analysis"]}
    if a.framework == "html":
        snip = os.path.join(cdir, f"{name}.hero-snippet.html")
        open(snip, "w").write(s)
        out["snippet"] = snip
    else:
        ext = "tsx" if a.framework == "react" else "astro"
        path = os.path.join(cdir, f"{comp}.{ext}")
        open(path, "w").write(s)
        with open(os.path.join(cdir, f"{name}.recipe.json"), "w") as f:
            json.dump(m["recipe"], f, indent=2)
        out["component_file"] = path
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
