# Style catalogue

Distilled from the 86-image *Premium AI Backgrounds* library. Every style lists: what it looks like, which
projects it fits, the engine (**code** = `render.py` family, **ai** = Codex gpt-image-2 → `family: image`),
a starting point, and the finishing stack. Reference thumbnails live in `assets/refs/<name>.jpg`;
attach 1–3 of them to every AI generation, and look at them yourself before you choose.

## What makes the library "premium" (apply to every option)

1. **One idea per frame.** A single luminous form, one landscape, one flow. Never collage.
2. **A quiet zone for the headline.** Usually the centre band or upper 40% (scenes: the sky). The form
   frames the copy; it never sits behind it at full intensity. Record it as `text_zone`.
3. **Texture always.** Film grain at minimum (0.03–0.06). Many add a print/digital layer: ASCII glyphs,
   halftone dots, Bayer dither, pixel-art. Flat vector-smooth gradients read as cheap. Never skip grain.
4. **Light from darkness or air.** Either a near-black field with light in it, or a pale/white field with
   prismatic colour at the edges. Mid-grey muddy middles are rare.
5. **Restrained palette.** 2–4 hues plus the base. Derive it from the brand: base = page background, one or two
   brand hues for the form, white-hot or cream for the core.
6. **No text, logos or UI inside the image.** Brand objects only when the brief calls for it (see *brand scenes*).
7. **Wide frame, edge-to-edge, and it must melt into the page.** The bottom edge usually fades to the page
   background (`fade_edges`) so the hero flows into the next section.

## Choosing: project → style

| Project signal | First picks |
|---|---|
| Dev tools, infra, AI, API, security, fintech dark UI | glow-arc, glow-hourglass, glow-ribbon (+ascii), particle terrain, plasma edge |
| AI / LLM product, "intelligence", data | ascii-glow variants, dome, prism bolt, dither aurora |
| Consumer app, creator tools, social, music | mesh, dither liquid, thermal, iridescent |
| Design tools, agencies, portfolios, fashion | dither liquid, halftone, duotone dunes, abstract paint |
| Light / clean SaaS, productivity, health | iridescent ribbon/arch, light mesh, sky-clouds scene |
| Climate, outdoors, travel, wellness, education | painted landscapes, pixel landscapes, photo-minimal scenes |
| Gaming, web3, entertainment, kids | pixel-art scenes, brand scenes (objects in clouds), thermal, prism bolt |
| Space, hardware, deep tech | glow-arc ("planet horizon"), mars-like brand scene, mono mountain |
| Calm, premium, luxury | duotone dunes, cutout minimal scenes, mono mountain, sepia |

Always offer **range** in the 3–4 options: e.g. two code styles in different families plus one AI scene, or
one dark and one light option when the theme is unknown. Never four variations of the same thing.

---

## A. Abstract (code engine)

### glow-arc ("planet horizon")
Black field with a luminous circular rim rising from the bottom. The hero copy sits in the darkness above it.
- Refs: `glow-arc-navy-band`, `glow-arc-blue-bottom`, `ascii-arc-ember`, `glass-rim-arc-dark`
- Preset: `presets/nova-arc.json`, `presets/ember-dome-ascii.json`
- Params: `shape: arc`, `radius` 1.5–2.2, `edge_y` 0.1–0.4 (rim height; + = lower), `rim_out` 0.06–0.15,
  `rim_in` 0.25–0.5, `fill` 0.2–0.6, `dispersion` 0.01–0.04 (prism fringe), `intensity` 1.3–1.9.
  Use `shape: horizon` for a nearly flat band, and `flip: true` to hang it from the top.
- Finish: `grain 0.04`. Add `ascii {cell 9–12, strength .6–.9, threshold .12}` for the ASCII Magic look.

### glow-dome (sky dome)
Light pouring down from a huge curved edge at the top: white-pink core, saturated rim, black below.
- Refs: `glow-dome-violet-pink`, `ascii-dome-violet-pink`
- Preset: `presets/violet-sky-dome.json` (`shape: dome, flip: true, radius ~3`)
- Text goes in the lower dark half. Pair with `ascii` at low strength.

### glow-hourglass (pinched light)
Two dark circles leave a glowing band that pinches at the centre. Good behind a centred headline.
- Refs: `glow-hourglass-violet`, `ascii-hourglass-lavender`
- Preset: `presets/hourglass-lavender.json`. `gap` 0.1–0.25 controls the band height.

### glow-ribbon / glow-bolt (prism light)
A single curved ribbon or jagged bolt of light crossing the frame, with spectral fringes.
`palette2` gives the bolt two colours, one on each side (blue|orange).
- Refs: `glow-ribbon-prism-diagonal`, `ascii-ribbon-magenta`, `glow-bolt-prism`, `ascii-bolt-prism`
- Presets: `magenta-ribbon.json`, `prism-bolt.json`. Put text on the darker side (`text_zone`), and use
  `mirror: true` to swap sides. You can pass explicit `points` as normalised [x, y] (x in -1..1).

### mesh (soft blob gradient)
Airy, blurred colour blobs. Friendly and consumer-facing. It must have strong grain or it looks like 2019 CSS.
- Refs: `mesh-pink-orange-blue`, `mesh-pink-blob-blue`, `mesh-blur-coral-navy`, `mesh-liquid-pastel-swirl`
- Preset: `sunset-mesh.json`. palette[0] = base, others = blobs. Optional `blobs: [[x,y,r],...]`.
- Finish: `grain 0.05–0.07 size 1.2`. Optionally a light `dither {levels 8, strength .4}`.

### liquid — dither aurora / dither liquid / halftone
Domain-warped flowing colour (`mode: field` = marbled, `mode: ridge` = aurora ribbons on dark), printed through
a retro texture. This is the library's biggest group (940–978).
- Refs: `dither-aurora-*`, `dither-liquid-*`, `halftone-violet-peach`, `dither-noise-teal-white`
- Presets: `dusk-dither.json` (ridge + dither), `peach-halftone.json` (field + halftone)
- Finish: `dither {levels 4–6, pixel 2–4}` **or** `halftone {cell 8–12, angle 15–30}`. Pick one, not both.

### thermal (heat-map fluid)
Psychedelic iso-bands. `mode: full` fills the frame (lilac/mint/acid). `mode: edge` gives a glowing "coastline"
on black (fire / acid / magenta).
- Refs: `thermal-*`, `plasma-edge-*`
- Presets: `acid-thermal.json`, `plasma-edge.json`. Loud: use it for creative, music or web3 brands, and
  always add a `scrim` behind the text.
- Finish: `dither {levels 6, pixel 2, strength .6}` or `pixelate {pixel 3, colors 0}`.

### iridescent (light prism)
White or pale base with thin holographic rainbow bands. This is the light-mode answer to glow.
- Refs: `iridescent-light-ribbon`, `iridescent-rainbow-arch`, `iridescent-light-stage`, `light-mint-layered-arches`
- Presets: `prism-light.json` (ribbon), `rainbow-arch.json` (arch). `period` = band spacing,
  `saturation` 0.4–0.9.
- Finish: `grain 0.02–0.03`. A white `ascii` at low strength gives the "Saas hero" look.

### waves (glowing ridge)
Luminous wave line(s) across a black field with a dusk fill below. Calm and cinematic.
- Refs: `waves-ember-dusk`, `waves-ember-line`
- Preset: `ember-waves.json`. `horizon` = line height, `amplitude`, `layers` 1–3.

### terrain (particle hills)
A point-cloud heightfield rolling into a black void. "Data meets nature": good for AI, climate and analytics.
- Refs: `terrain-particle-green`, `terrain-particle-green-mist`
- Preset: `meadow-particles.json`. Swap the palette for brand hues (cyan / violet terrain works).

---

## B. Scenes (AI engine → `family: image`)

Generate with `scripts/codex_image.py` (see `references/prompting.md` for prompt anatomy), then finish and
export with `render.py` using `{"family": "image", "source": "raw.png", ...}`.

| Style | Refs to attach | Notes |
|---|---|---|
| painted anime-style landscape | `painted-hill-flowers-golden`, `painted-alpine-river-cabin`, `painted-coast-sunset`, `painted-pines-airy-sky` | Hand-painted look, huge sky, warm light. Text sits in the sky. |
| painted figure-and-vista | `painted-cliffs-sea-of-clouds-figure`, `painted-sunset-canyon-figure`, `painted-night-figure` | Tiny lone figure, epic vista: "journey" and "possibility" brands. |
| painted canyon / valley glow | `painted-canyon-bright-center`, `painted-green-valley-glow` | Bright centre gap that frames the headline. |
| pixel-art landscape | `pixel-valley-river`, `pixel-meadow-rock-pond`, `pixel-hills-dither-sky`, `sky-clouds-blue-dither` | Finish with `pixelate {pixel 4–6, colors 32–48}` to make it crisp and consistent. |
| sky & clouds | `sky-clouds-blue-moon-arc`, `sky-clouds-blue-dither` | Clouds along the bottom 35%, empty gradient sky above. Most versatile light hero. |
| photo-minimal | `photo-lake-dusk-mountains`, `cutout-dunes-white`, `cutout-cove-white`, `photo-wildflowers-on-black` | Real-photo feel, lots of negative space. Cutouts fade to white or black. |
| duotone dunes | `dunes-duotone-blue`, `dunes-duotone-magenta`, `dunes-sepia`, `dunes-red-teal-sky` | Generate the dunes, then `grade {colors: [dark, brand, light]}` in code, so you get exact brand colours. |
| dark mountain | `mono-mountain-silhouette-grey`, `mountain-dark-lava-light-sky` | Monochrome or lava-lit ridge with a light sky: premium and austere. |
| glowing grass / flower field on black | `terrain-flower-field-black`, `terrain-grass-waves-black`, `photo-wildflowers-on-black` | Upper half pure black for copy. |
| abstract paint | `abstract-paint-pink-gold` | Impasto strokes. Fashion, beauty, art. |
| flat illustration | `flat-illustration-camping-dark` | Bold flat vector scene on a dark field. |
| **brand scene** | `brand-consoles-on-clouds`, `brand-mars-domes`, `painted-city-park` | Product or iconic objects placed into the world. Use **only** when the project has physical or iconic objects (hardware, consoles, food, devices, a mascot). Objects sit in the lower third, and the sky stays clear. No readable logos or text. |

Dunes, sky and terrain-on-black also have code fallbacks (`grade` on any photo, `mesh` sky, `terrain`).
Use them if Codex is unavailable or rate-limited.

---

## C. Finishing stacks (copy, then tune)

```jsonc
// dark glow, standard
[{"op":"grain","amount":0.045}]
// ASCII Magic look (glyphs ride the light; dark stays clean)
[{"op":"ascii","cell":10,"strength":0.8,"threshold":0.14,"knockout":0.45,"jitter":0.45},{"op":"grain","amount":0.04}]
// retro print: dither
[{"op":"dither","levels":5,"pixel":3},{"op":"grain","amount":0.03}]
// retro print: halftone
[{"op":"halftone","cell":10,"angle":25,"strength":0.9},{"op":"grain","amount":0.03}]
// pixel-art (AI scenes)
[{"op":"pixelate","pixel":5,"colors":40}]
// brand-exact duotone on an AI photo
[{"op":"grade","colors":["#0b1020","#3b5bff","#e9edff"]},{"op":"grain","amount":0.04}]
// melt the hero into the next section + guarantee headline contrast
[{"op":"fade_edges","bottom":0.22,"color":"#05050a"},{"op":"scrim","rect":[0.2,0.3,0.8,0.62],"amount":0.25}]
```

All sizes are authored for a 1920×1200 frame and scale with the short side, so previews, 4K finals and
portrait mobile renders all have the same physical texture.
