# Legendary Backgrounds

**Give your AI coding agent an art director, a renderer, and the complete reference library.**

Generate landing-page hero backgrounds from your existing brand colors, copy, layout, and theme.
Explore distinct directions, choose a contact sheet option, and export desktop + mobile artwork with
an optional animated WebGL layer.

[Set up the skill](#one-command-setup) · [Copy a setup prompt](#paste-a-setup-prompt-instead) · [Explore the gallery](#more-background-directions)

![Five featured backgrounds: crimson pencil hills, a fox in a sketched meadow, an autumn valley, glowing red hills at night, and misty watercolor mountains](docs/featured-backgrounds.png)

**a** Crimson pencil hills · **b** Fox in a sketched meadow · **c** Autumn valley ·
**d** Midnight crimson · **e** Watercolor mountains

Five featured art directions, with the full preset and reference gallery below setup.
For illustrated scenes like these, use the skill’s optional AI workflow.

**The whole folder ships:** original-resolution artwork, 86 reference thumbnails, 15 ready-to-render
presets, Python generators, finishing tools, prompt guides, React/Astro/HTML templates, and the live demo.

## Download everything

[Download the complete ZIP](https://github.com/tanmaybawakar/legendary-backgrounds/archive/refs/heads/main.zip),
extract it, and open a terminal in the extracted folder. Or clone it:

```bash
git clone --depth 1 https://github.com/tanmaybawakar/legendary-backgrounds.git
cd legendary-backgrounds
```

The complete library is approximately **1.7 GB**, including the original images. Download time depends
on your connection. **Setup aims for under two minutes after download** on a typical machine with
Python already installed; the installer downloads its Python dependencies and checks a first render.

## One-command setup

Requires **Python 3.10+** with pip/venv support. No Node.js, API key, or paid AI account is needed for
the procedural styles. On Debian/Ubuntu, install `python3-venv` if your Python reports it missing.

**macOS / Linux — install for Claude Code, Codex, and Cursor together:**

```bash
python3 setup.py all
```

**Windows — from PowerShell in the extracted folder:**

```powershell
py -3 setup.py all
```

For one agent, replace `all` with the name below:

| Agent | Command | Installed skill folder |
| --- | --- | --- |
| Claude Code | `python3 setup.py claude` | `~/.claude/skills/legendary-backgrounds/` |
| Codex | `python3 setup.py codex` | `~/.agents/skills/legendary-backgrounds/` |
| Cursor | `python3 setup.py cursor` | `~/.cursor/skills/legendary-backgrounds/` |
| Agents that discover `.agents/skills` | `python3 setup.py agents` | `~/.agents/skills/legendary-backgrounds/` |

The installer creates an isolated `.venv`, installs NumPy/SciPy/Pillow, copies the complete skill
including its reference images, records the Python interpreter for your agent, and renders a test
image at `.legendary-backgrounds/setup-preview.jpg`. You do not need to activate an environment.
It updates files in an existing skill of the same name; back up your own edits before reinstalling.
Keep the downloaded folder in place because installed skills use its `.venv`.

Restart your agent if the skill is not listed. Then ask:

```text
Use legendary-backgrounds to make a hero background for this project.
Read my brand colors, theme, headline, and layout. Show me 3 genuinely different
directions as a contact sheet, including mobile previews. Use procedural styles
first. After I choose, export responsive AVIF/WebP and integrate the result
without changing my copy or layout. Verify desktop and mobile readability.
```

Claude Code also accepts `/legendary-backgrounds`; in Codex you can mention `$legendary-backgrounds`.
The folder locations and invocation conventions follow the official
[Claude Code](https://code.claude.com/docs/en/skills),
[Codex](https://developers.openai.com/codex/skills/), and
[Cursor](https://cursor.com/docs/skills) skill documentation.

## Paste a setup prompt instead

Paste the appropriate prompt into an agent with terminal and filesystem access. If you already
downloaded this repo, open that folder first and the agent can skip downloading it.

**Claude Code**

```text
Install Legendary Backgrounds from https://github.com/tanmaybawakar/legendary-backgrounds.
Use the local checkout if this folder already contains setup.py and legendary-backgrounds/SKILL.md;
otherwise clone the complete repository into a permanent local folder. Read README.md and setup.py,
then run python3 setup.py claude (Windows: py -3 setup.py claude).
Verify the installed SKILL.md, all 86 reference thumbnails, and the generated setup-preview.jpg.
Use the interpreter recorded in the installed skill's PYTHON_PATH.txt for its Python scripts.
Tell me when /legendary-backgrounds is ready, or if I need to restart Claude Code.
```

**Codex**

```text
Install Legendary Backgrounds from https://github.com/tanmaybawakar/legendary-backgrounds.
Use the local checkout if this folder already contains setup.py and legendary-backgrounds/SKILL.md;
otherwise clone the complete repository into a permanent local folder. Read README.md and setup.py,
then run python3 setup.py codex (Windows: py -3 setup.py codex).
Verify ~/.agents/skills/legendary-backgrounds/SKILL.md, all 86 reference thumbnails,
and the generated setup-preview.jpg. Use the interpreter recorded in PYTHON_PATH.txt.
Tell me when $legendary-backgrounds is ready, or if I need to restart Codex.
```

**Cursor**

```text
Install Legendary Backgrounds from https://github.com/tanmaybawakar/legendary-backgrounds.
Use the local checkout if this folder already contains setup.py and legendary-backgrounds/SKILL.md;
otherwise clone the complete repository into a permanent local folder. Read README.md and setup.py,
then run python3 setup.py cursor (Windows: py -3 setup.py cursor).
Verify ~/.cursor/skills/legendary-backgrounds/SKILL.md, all 86 reference thumbnails,
and the generated setup-preview.jpg. Use the interpreter recorded in PYTHON_PATH.txt.
Tell me when the skill is ready, or if I need to restart Cursor.
```

**Other coding agents — Gemini CLI, OpenCode, Copilot, Windsurf, Cline, Antigravity, and others**

```text
Set up the complete Legendary Backgrounds repository:
https://github.com/tanmaybawakar/legendary-backgrounds
Reuse the local checkout if present; otherwise clone it into a permanent local folder.
Read README.md and setup.py. Run python3 setup.py agents (Windows: py -3 setup.py agents).
If your agent discovers ~/.agents/skills, load legendary-backgrounds from there.
Otherwise use your documented native skill directory, copying the entire installed
legendary-backgrounds folder, including references, presets, templates, and PYTHON_PATH.txt.
If native skills are unsupported, read legendary-backgrounds/SKILL.md directly and follow it
when I ask for a hero background. Use the recorded Python interpreter for all scripts.
Verify the 86 reference thumbnails and the setup-preview.jpg before reporting readiness.
Do not claim native skill support unless your agent actually supports it.
```

Agents need to be able to read local files and run Python. This package uses the portable `SKILL.md`
format; native discovery and cloud-agent availability depend on the host. Local installation does
not automatically upload the library to a remote agent.

## More background directions

### 15 ready-to-render presets

These are the actual included demo stills, not reference targets. Click an image to inspect it;
the matching recipe lives in [`legendary-backgrounds/presets/`](legendary-backgrounds/presets/).
Choose a direction, then let the skill adapt its palette, text zone, and finish to your project.

| | | |
| --- | --- | --- |
| **Nova arc**<br>![Violet-blue luminous horizon on black](legendary-backgrounds/templates/demo-stills/nova-arc.jpg) | **ASCII ember dome**<br>![Orange glowing dome with horizontal ASCII texture](legendary-backgrounds/templates/demo-stills/ember-dome-ascii.jpg) | **Violet sky dome**<br>![Pink-violet light pouring down from a curved rim](legendary-backgrounds/templates/demo-stills/violet-sky-dome.jpg) |
| **Prism bolt**<br>![Electric blue and golden zigzag light on black](legendary-backgrounds/templates/demo-stills/prism-bolt.jpg) | **Magenta ribbon**<br>![Single violet-pink luminous ribbon](legendary-backgrounds/templates/demo-stills/magenta-ribbon.jpg) | **Lavender hourglass**<br>![Lavender light pinched between two dark curves](legendary-backgrounds/templates/demo-stills/hourglass-lavender.jpg) |
| **Dusk dither**<br>![Gold and violet flowing aurora with dither texture](legendary-backgrounds/templates/demo-stills/dusk-dither.jpg) | **Peach halftone**<br>![Peach and purple liquid field printed through halftone dots](legendary-backgrounds/templates/demo-stills/peach-halftone.jpg) | **Acid thermal**<br>![Mint and lilac psychedelic thermal bands](legendary-backgrounds/templates/demo-stills/acid-thermal.jpg) |
| **Plasma edge**<br>![Orange and purple thermal contours floating on black](legendary-backgrounds/templates/demo-stills/plasma-edge.jpg) | **Particle meadow**<br>![Green point-cloud hills fading into darkness](legendary-backgrounds/templates/demo-stills/meadow-particles.jpg) | **Ember waves**<br>![Warm luminous waves above a purple dusk field](legendary-backgrounds/templates/demo-stills/ember-waves.jpg) |
| **Prism light**<br>![Thin holographic ribbon on an airy pale field](legendary-backgrounds/templates/demo-stills/prism-light.jpg) | **Rainbow arch**<br>![Rainbow arch framing a white center](legendary-backgrounds/templates/demo-stills/rainbow-arch.jpg) | **Sunset mesh**<br>![Grainy blue coral and violet mesh gradient](legendary-backgrounds/templates/demo-stills/sunset-mesh.jpg) |

Try: `Use legendary-backgrounds with the prism-bolt preset. Adapt it to my brand colors and keep the headline area dark.`

<details>
<summary><strong>Explore 9 more reference directions — painted worlds, pixel art, dunes, photography, and print</strong></summary>

These are curated references bundled with the skill, not generated preset outputs. Scene creation
uses the optional AI workflow; the references also guide composition, palette, and texture.

| | | |
| --- | --- | --- |
| **Painted coast**<br>![Warm painted sunset over a flower-lined coastline](legendary-backgrounds/assets/refs/painted-coast-sunset.jpg) | **Sea of clouds**<br>![Lone figure facing an epic mountain vista above clouds](legendary-backgrounds/assets/refs/painted-cliffs-sea-of-clouds-figure.jpg) | **Pixel valley**<br>![Retro pixel-art landscape with a winding river](legendary-backgrounds/assets/refs/pixel-valley-river.jpg) |
| **Blue dunes**<br>![Minimal sculptural dunes in icy blue duotone](legendary-backgrounds/assets/refs/dunes-duotone-blue.jpg) | **White-space cove**<br>![Turquoise cove beneath a large white headline area](legendary-backgrounds/assets/refs/cutout-cove-white.jpg) | **Midnight lake**<br>![Photographic mountain lake under a dark starry sky](legendary-backgrounds/assets/refs/photo-lake-dusk-mountains.jpg) |
| **Liquid print**<br>![Dithered peach and cyan liquid flow](legendary-backgrounds/assets/refs/dither-liquid-peach-blue.jpg) | **Prismatic glow**<br>![Soft spectral light streak against black](legendary-backgrounds/assets/refs/glow-bolt-prism.jpg) | **Pink and gold paint**<br>![Textured impasto brushstrokes in pink and gold](legendary-backgrounds/assets/refs/abstract-paint-pink-gold.jpg) |

Try: `Use legendary-backgrounds to explore a painted coast, a pixel valley, and blue duotone dunes. Use the bundled references and show a contact sheet before integrating anything.`

</details>

See the [full style catalogue](legendary-backgrounds/references/styles.md) for more directions and
finishing recipes, or [try the live demo locally](#try-the-included-live-demo) to explore animation.

## What it makes

- **Procedural artwork:** glow arcs, domes, ribbons, bolts, mesh gradients, liquid fields, thermal
  colors, iridescent light, waves, and particle terrain. Repeatable recipes, no generation quota.
- **Texture and finishing:** grain, ASCII, halftone, dithering, pixelation, grading, bloom, scrims,
  and edge fades.
- **Responsive exports:** desktop up to 3840 pixels wide; separately composed portrait variants;
  AVIF + WebP, a JPEG poster, source recipes, master PNGs, and contrast analysis.
- **Integration:** React, Astro, and plain HTML scaffolding plus a WebGL animation layer that respects
  reduced motion and pauses offscreen. Other frameworks can adapt the HTML pattern.
- **Optional AI scenes:** painted, pixel, photographic, and object-based backgrounds through an
  installed, signed-in Codex CLI. Image-tool availability and account limits vary; procedural styles
  remain available if generation fails. AI outputs can use the same finishing pass.

## Render without an agent

After setup, run these commands from the repository root. On Windows, use `.venv\Scripts\python.exe`
instead of `.venv/bin/python`.

```bash
# Preview a preset.
.venv/bin/python legendary-backgrounds/scripts/render.py \
  legendary-backgrounds/presets/nova-arc.json --preview nova-arc.jpg --size 1280x800

# Export responsive web assets, keeping masters separate.
.venv/bin/python legendary-backgrounds/scripts/render.py \
  legendary-backgrounds/presets/nova-arc.json \
  --export public/backgrounds --masters .legendary-backgrounds/masters

# Generate a React component; Astro and HTML are also supported.
.venv/bin/python legendary-backgrounds/scripts/wire.py \
  .legendary-backgrounds/masters/nova-arc.manifest.json \
  --framework react --public-url /backgrounds \
  --component-dir src/components --live-dir src/lib
```

Component generation creates the files; the agent or developer then places the component into the
existing hero and verifies the page. Edit a copy of a preset to change its palette, seed, composition,
or finish stack. See the [style catalogue](legendary-backgrounds/references/styles.md) and
[AI prompting guide](legendary-backgrounds/references/prompting.md).

## Try the included live demo

```bash
python3 -m http.server 8000
```

Open [the local demo](http://localhost:8000/legendary-backgrounds/templates/demo.html).
The 15 demo stills are included, so there is no build step. WebGL needs a compatible browser/device.

## Everything in the download

```text
Premium AI Backgrounds Assets/       Original-resolution Gradients/ and Nature/ artwork
legendary-backgrounds/
  SKILL.md                          Agent workflow
  requirements.txt                  Python dependencies
  assets/refs/                      All 86 reference thumbnails
  assets/refmap.tsv                 Original filenames → reference names
  presets/                          15 JSON recipes
  scripts/                          Render, finish, contact sheet, project scan, AI helper, wiring
  references/                       Style and prompting guides
  templates/                        React, Astro, HTML, WebGL, demo + all demo stills
legendary-backgrounds-test-contact-sheet.jpg
setup.py                            Cross-platform setup + first-render check
install.sh                          Claude Code compatibility entry point
LICENSE
```

## Privacy and data flow

Machine-specific launch configs, OS metadata files, credentials, virtual environments, caches, and
generated interpreter paths are excluded from version control. The public package contains no
account login or API key. `setup.py` downloads packages from the configured Python package index;
the renderer and contact sheet run locally and contain no telemetry.

The project scanner reads project context locally and prints it for your agent. Your chosen agent's
own data handling still applies. The optional Codex image helper sends its prompt and supplied
references to the configured AI service and uses your existing Codex login; it does not extract tokens.
Image discovery is limited to that invocation's working folder.

## License

[MIT](LICENSE) · Copyright 2026 TANGENIX Pvt. Ltd. Keep the copyright and license notice with copies
or substantial portions of this project. Third-party trademark rights are not granted by this license.
