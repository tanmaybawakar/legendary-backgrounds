---
name: legendary-backgrounds
description: Generate premium landing-page hero backgrounds from a project's own context (brand colours, copy, product, theme) in the style of a curated 86-image library of glows, ASCII and dither gradients, thermal fluids, iridescent light and painted, pixel and photo landscapes. Reads the project, shows a 3-4 option contact sheet with a mock headline, renders the pick as 4K desktop plus portrait mobile AVIF/WebP, wires it into the hero (art-directed picture, contrast-checked text), and adds a live animated WebGL version. Uses code for abstract styles and Codex CLI (gpt-image-2, ChatGPT login) for painted or photo scenes. Use when asked for a hero/landing background, a "legendary background", a hero image, or to make a landing page look premium.
---

# Legendary Backgrounds

You are the art director and the renderer. The output must look like it came from the library in
`assets/refs/`: one idea per frame, a quiet headline zone, light out of darkness (or prism out of white),
restrained brand palette, and **always** texture (grain, ASCII, halftone, dither or pixel). Read
`references/styles.md` before choosing anything. It is the distilled library.

`SKILL_DIR` below means this skill's folder, the one containing this file.

## Python setup

Before running scripts, read `SKILL_DIR/PYTHON_PATH.txt` if it exists and use that absolute Python
interpreter in place of `python3` in every command below. The one-command installer creates it;
no shell activation is needed. If the file is absent or its interpreter no longer exists, create a
virtual environment in `SKILL_DIR/.venv` and install `SKILL_DIR/requirements.txt` with its Python.
Use that interpreter for all scripts. Never install dependencies into the system Python.
All 86 reference thumbnails in `assets/refs/` ship with this skill. The full repository also includes
the original-resolution images in `Premium AI Backgrounds Assets/` and the filename map `assets/refmap.tsv`.

## Engines (decided — don't re-litigate)

- **Code** (`scripts/render.py`, numpy): every abstract style. Exact brand hex, any resolution, about 1 s per
  preview, 10 s for a 4K + mobile export, deterministic (same recipe gives the same image), and no quota.
  It also drives the live animation from the same recipe.
- **Codex** (`scripts/codex_image.py` → `codex exec` → built-in gpt-image-2): painted, pixel, photo and brand
  scenes. Uses the ChatGPT login. Never call the OpenAI REST API with that token (it 401s).
  40–90 s per image, so run the options in parallel in the background.
- **Both** go through the same finishing pass (`scripts/finish.py` ops in the recipe), so AI art gets the
  library's grain, dither and grade, and exact brand colour.

## Workflow

### 1. Read the project (no questions yet)
```bash
python3 "$SKILL_DIR/scripts/scan_project.py" <project_root>
```
Then open the hero candidate file(s), the global CSS or Tailwind theme, and the README. Write a 6-line brief
for yourself:
product, audience · 3 mood words · theme (dark/light; follow the site, don't guess) · palette
(base = page bg, 1–2 brand hues, a hot or cream highlight) · the headline that will sit on it · where
the copy sits (centred / left / top) → the `text_zone`.
If there's no project (a bare request), take the brief from the conversation. Ask only if theme **and** brand
are both unknowable.

### 2. Pick 3–4 directions with range
Use the *project → style* table in `references/styles.md`. Mix families: typically 2–3 code options and
0–2 AI scenes. Brand scenes (objects in the world) only when the product has physical or iconic objects.
Look at the relevant `assets/refs/*.jpg` yourself before committing, and copy what makes them work.

### 3. Make the options
Work folder: `<project>/.legendary-backgrounds/` (add it to `.gitignore`). One recipe per option:
`options/a.json` … Start from the closest `presets/*.json`, then put the brand palette in, set `text_zone`,
`page_bg`, `seed`, and a `mobile` override if the portrait composition needs it (for example a higher `edge_y`).

```bash
R="$SKILL_DIR/scripts/render.py"
python3 "$R" options/a.json --preview options/a.jpg --size 1280x800
python3 "$R" options/a.json --preview options/a-m.jpg --size 1280x800 --portrait   # check mobile too
```
AI options: write the brief per `references/prompting.md` and start them **all at once, in the background**:
```bash
python3 "$SKILL_DIR/scripts/codex_image.py" --prompt-file options/c.txt --out options/c-raw.png \
  --aspect landscape --ref "$SKILL_DIR/assets/refs/painted-hill-flowers-golden.jpg" &
```
Then the recipe `{"family":"image","source":"c-raw.png","finish":[...],...}` → `--preview` as above.
If codex_image exits non-zero, replace that option with a code style and tell the user why in one line:
3 = usage limit (it gives the reset time) · 4 = not installed or not logged in · 5 = image tool unavailable ·
6 = no file produced · 7 = timeout.

**Look at every preview yourself** (Read the jpg) and iterate on params before the user sees anything.
Reject: muddy midtones, the form colliding with the text zone, flat untextured areas, AI text artefacts,
everything the same brightness.

### 4. Present the contact sheet and let the user choose
```bash
python3 "$SKILL_DIR/scripts/contact_sheet.py" options/sheet.jpg options/a.jpg options/b.jpg options/c.jpg \
  --labels "A · Nova arc (code)" "B · Dusk dither (code)" "C · Golden meadow (AI)" \
  --headline "<their real headline>" --sub "<their subhead>"
```
Show it to the user (send the file), with one line per option on *why it fits this brand*. Then ask which one,
plus any tweak (colour, intensity, texture). Apply tweaks by editing the recipe and re-previewing, then confirm.

### 5. Final render
AI pick: generate a **portrait** version with the same brief (`--aspect portrait`), set as `mobile_source`.
```bash
python3 "$R" options/a.json --export <public>/backgrounds --masters .legendary-backgrounds/masters
```
Web files (AVIF + WebP at 3840/2560/1920/1280, mobile at 1290/860, poster jpg, recipe) go to the public dir.
Masters and `<name>.manifest.json` stay in `.legendary-backgrounds/`. Read the manifest `analysis`:
if `needs_scrim` is true (worst-case contrast below 4.5), add a `scrim` over `text_zone` and/or a darker
`levels`, then re-export. Look at the desktop and mobile masters yourself.

### 6. Wire it into the hero
```bash
python3 "$SKILL_DIR/scripts/wire.py" .legendary-backgrounds/masters/<name>.manifest.json \
  --framework react|astro|html --public-url /backgrounds --component-dir src/components --live-dir src/lib
```
Then edit the existing hero by hand. **Keep their copy and layout.**
- Make the hero section `position: relative; isolation: isolate; overflow: hidden` and place
  `<NameBackground />` (or the snippet) as its first child. Remove the old background (image, gradient or
  bg colour) only if it's the same layer.
- Set the headline colour from `analysis.text_color`, and make sure the section below starts on `page_bg`
  so the seam disappears (the recipe can `fade_edges` to it).
- Vue / Svelte / other frameworks: use the `html` output as the pattern and port it. Plain
  `mountLegendaryBackground(el, {recipe, image})` works anywhere.
- `live` defaults on. It respects reduced-motion, pauses offscreen, and keeps the static image as LCP. Users
  can pass `live={false}`.

### 7. Verify like a user
Start their dev server (or open the HTML) in the browser. Screenshot desktop (1440×900) and mobile (390×844).
Check: headline readable, no layout shift, the picture serves AVIF, the live layer fades in and matches the
still, the console is clean. Fix before reporting.

### 8. Report
What was made (style + one-line rationale), file sizes of the 1920 AVIF and mobile AVIF, where everything
lives, and how to tweak: "edit `.legendary-backgrounds/options/a.json` → re-run the export command".

## Recipe reference (summary — full params in `references/styles.md`)
`family`: glow (shape: arc · dome · horizon · hourglass · ribbon · bolt) · mesh · liquid (field|ridge) ·
thermal (full|edge) · iridescent (ribbon|arch) · waves · terrain · image.
`finish` ops: grade · levels · bloom · chroma · ascii · halftone · dither · pixelate · grain · vignette ·
scrim · fade_edges. Sizes are authored at 1920×1200 and scale with the short side.

## Rules
- Never put text, logos or UI in the image. Never ship a background without texture.
- Never make 4 variations of one idea. Range is the point of the contact sheet.
- Brand colour comes from the project, not your taste. If the brand is beige, the glow is beige.
- Don't commit masters to `public/`. Don't overwrite an existing background without saying so.
- Codex quota is the user's. Generate AI options only for directions you'd actually stand behind.
