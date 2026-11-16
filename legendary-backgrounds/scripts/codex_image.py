#!/usr/bin/env python3
"""Generate one image with Codex CLI's built-in image tool (gpt-image-2) via `codex exec`.

Uses the user's ChatGPT login (no API key). Never call the OpenAI REST API with that OAuth
token — it 401s; always go through `codex exec`.

  codex_image.py --prompt-file p.txt --out public/bg/raw-a.png [--aspect landscape] \
      [--ref refs/a.jpg --ref refs/b.jpg] [--timeout 420]

Runs in a throwaway workdir with --ignore-user-config (keeps auth, skips the user's MCP servers
and hooks, which are slow and noisy). Safe to run several in parallel (one per option).

Exit codes: 0 ok · 2 bad args · 3 usage limit · 4 not logged in / codex missing ·
            5 image tool unavailable · 6 no image produced · 7 timeout
Prints one JSON line: {"ok": true, "path": ..., "width": ..., "height": ..., "seconds": ...}
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image

ASPECT_HINT = {
    "landscape": "a wide LANDSCAPE frame (use the widest landscape size the image tool offers, e.g. 1536x1024 or larger)",
    "portrait": "a tall PORTRAIT frame (use the tallest portrait size the image tool offers, e.g. 1024x1536 or larger)",
    "square": "a SQUARE frame (1024x1024 or larger)",
}

GUARDRAILS = (
    "This is a landing-page hero BACKGROUND, so: absolutely no text, letters, numbers, logos, "
    "watermarks, signatures, UI, buttons, frames or borders anywhere in the image. "
    "Keep the composition calm where the headline will sit (described above). "
    "Deliver edge-to-edge artwork, not a mockup or a picture-in-picture."
)


def fail(code, msg, **extra):
    print(json.dumps({"ok": False, "code": code, "error": msg, **extra}))
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--aspect", default="landscape", choices=sorted(ASPECT_HINT))
    ap.add_argument("--ref", action="append", default=[], help="style reference image (repeatable, max 4)")
    ap.add_argument("--timeout", type=int, default=420)
    ap.add_argument("--model", help="override the Codex agent model (rarely needed)")
    a = ap.parse_args()

    if not shutil.which("codex"):
        fail(4, "codex CLI not found. Install: npm i -g @openai/codex, then run `codex` once and sign in with ChatGPT.")
    st = subprocess.run(["codex", "login", "status"], capture_output=True, text=True)
    if "Logged in" not in (st.stdout + st.stderr):
        fail(4, "Codex is not logged in. Run `codex login` (choose Sign in with ChatGPT).")

    brief = a.prompt if a.prompt else open(a.prompt_file).read()
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    wd = tempfile.mkdtemp(prefix="lbg-codex-")
    refs = []
    for i, r in enumerate(a.ref[:4]):
        im = Image.open(r).convert("RGB")
        im.thumbnail((1024, 1024))
        p = os.path.join(wd, f"ref{i + 1}.jpg")
        im.save(p, quality=90)
        refs.append(p)

    ref_note = ""
    if refs:
        ref_note = (f"\n\nAttached are {len(refs)} STYLE REFERENCE image(s). Match their art style, rendering "
                    "technique, texture, lighting quality and colour mood — but create a NEW, original "
                    "composition for the brief. Do not copy them.")
    prompt = (
        "Use your built-in image generation tool to create exactly ONE image. Do not write code to draw it, "
        "and do not ask questions.\n\n"
        f"BRIEF:\n{brief.strip()}\n\nFRAME: {ASPECT_HINT[a.aspect]}.\n{GUARDRAILS}{ref_note}\n\n"
        "When the image is generated, save/copy it into the current working directory as ./out.png. "
        "Reply with only the path and pixel size. If the image tool is unavailable, reply exactly IMAGEGEN_UNAVAILABLE."
    )

    cmd = ["codex", "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
           "-C", wd, "-s", "workspace-write", "-o", os.path.join(wd, "last.txt")]
    if a.model:
        cmd += ["-m", a.model]
    # The prompt goes before the images: `-i` takes several files and would swallow a prompt after it.
    cmd.append(prompt)
    for p in refs:
        cmd += ["-i", p]

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout, stdin=subprocess.DEVNULL)
        log = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as e:
        log = str(e.stdout or "") + str(e.stderr or "")
        open(os.path.join(wd, "codex.log"), "w").write(log)
        fail(7, f"codex exec timed out after {a.timeout}s", workdir=wd)
    open(os.path.join(wd, "codex.log"), "w").write(log)

    if re.search(r"usage limit|rate limit|quota", log, re.I) and not glob.glob(os.path.join(wd, "out.*")):
        when = re.search(r"try again at ([^\n.]+)", log, re.I)
        fail(3, "Codex/ChatGPT usage limit reached" + (f"; resets {when.group(1).strip()}" if when else ""),
             retry_at=when.group(1).strip() if when else None)
    last = open(os.path.join(wd, "last.txt")).read() if os.path.exists(os.path.join(wd, "last.txt")) else ""
    if "IMAGEGEN_UNAVAILABLE" in last:
        fail(5, "Codex reports the image generation tool is unavailable for this account/model.", workdir=wd)

    # Only this invocation's folder is safe: shared stores can contain unrelated private images.
    cands = [p for p in glob.glob(os.path.join(wd, "**", "*"), recursive=True)
             if p.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and not os.path.basename(p).startswith("ref")]
    cands.sort(key=lambda p: (os.path.basename(p) != "out.png", -os.path.getmtime(p)))
    if not cands:
        fail(6, "codex finished but no image file was produced", workdir=wd, last_message=last[-500:])
    src = cands[0]
    im = Image.open(src)
    im.load()
    if out.lower().endswith(".png"):
        im.convert("RGB").save(out)
    else:
        im.convert("RGB").save(out, quality=95)
    print(json.dumps({"ok": True, "path": out, "width": im.width, "height": im.height,
                      "seconds": round(time.time() - t0, 1), "workdir": wd}))


if __name__ == "__main__":
    main()
