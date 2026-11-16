# Prompting Codex gpt-image-2 for hero backgrounds

`scripts/codex_image.py` wraps your brief with the non-negotiables: one image, no text/logos/UI, edge-to-edge,
frame size, save path, and how to use the references. You write only the **brief**: 4–7 sentences in this order.

1. **Medium + style**: "Hand-painted anime-style landscape painting, soft gouache, film-still quality" /
   "Minimal fine-art photograph, medium format" / "16-bit pixel art, limited palette, crisp pixels".
2. **Subject + setting**, specific and singular: "a single rolling hill of tall grass and pink cosmos flowers".
3. **Composition with the copy zone named**: "The subject occupies only the lower 35% of the frame. The upper
   60% is open sky with soft cumulus clouds: a calm, empty area for a headline." Always say where emptiness is.
4. **Light + time + palette**, tied to the brand: "warm golden-hour backlight; palette of cream, peach, sage green
   and a deep teal sky that echoes the brand colour #0f766e".
5. **Mood in one phrase**: "hopeful, spacious, quiet".
6. *(brand scenes only)* **Objects**: "three white game consoles and controllers resting on the cloud bank in
   the lower third, product-photography lighting, no visible logos or text".
7. **Negative**: anything specific to avoid for this style ("no people", "no buildings", "no lens flare").

## Do
- Name the empty zone explicitly every time. gpt-image-2 fills space unless told not to.
- Echo 1–2 brand hexes as colour words plus the hex. Then fix exact colour in code (`grade` or `levels`).
- Attach 1–3 references from `assets/refs/` of the **same style** (never mix painted and photo refs).
- Generate landscape for desktop. For the mobile hero, generate a **separate portrait** image with the same
  brief, adding "vertical composition, subject in the lower 30%, sky above". Set it as `mobile_source`.
  Cropping a landscape to 9:19.5 rarely keeps the subject.
- Run the options in parallel (one `codex_image.py` per option, in the background). Each takes about 40–90 s.

## Don't
- Don't ask for "a website", "hero section", "landing page", or "UI". You get mockups. Say "background artwork".
- Don't ask for text, a logo, or a product name in the image.
- Don't put the subject dead-centre behind where the headline goes.
- Don't rely on AI for exact brand colour, grain or dither. That's the code finishing pass's job.

## Example briefs

**Painted, climate startup (light)**
> Hand-painted anime-style landscape painting with soft gouache textures and film-still quality. A wide valley
> of wildflower meadows with a slow river winding toward distant blue mountains. The land fills only the lower
> 35% of the frame; the upper 60% is a vast, calm sky with a few soft cumulus clouds, an empty area for a
> headline. Fresh morning light; palette of mint, sage, cream and a clear sky blue near #38bdf8. Mood: hopeful,
> spacious. No people, no buildings.

**Photo-minimal, premium fintech (dark)**
> Minimal fine-art landscape photograph, medium format, long exposure. A still alpine lake at blue hour with
> dark mountain silhouettes on both sides leaving a bright gap in the centre. Mountains and lake occupy the
> lower 40%; the upper half is a smooth gradient sky from deep navy to a faint peach horizon glow, empty for a
> headline. Palette: navy #0b1229, slate, a whisper of peach. Mood: quiet, assured. No people, no boats.

**Brand scene, gaming hardware**
> Bright, stylised 3D render with soft studio lighting. A sea of fluffy white clouds fills the lower third
> under a saturated blue gradient sky. Resting on the clouds: a white game console, two controllers and a
> few playful floating geometric shapes in purple and orange. Objects stay in the lower third, slightly
> off-centre; the sky above is empty for a headline. Mood: joyful, premium. No logos, no text, no screens.

**Pixel art, indie dev tool**
> 16-bit pixel-art landscape, limited palette, crisp pixels, gentle dithering in the sky. Green rolling hills
> with a stream and small white flowers across the bottom 35%; a large clear blue sky with chunky pixel clouds
> above, empty for a headline. Palette: grass greens, sky blue, cream. Mood: cosy, nostalgic. No characters.

## After generation
1. Look at the raw image. If it has text artefacts, a cluttered copy zone, or the wrong composition,
   regenerate. Don't fix it in post.
2. Write the recipe: `{"family":"image","source":"raw-a.png","mobile_source":"raw-a-portrait.png",
   "focus":[0.5,0.6],"finish":[...],"text_zone":[...],"page_bg":"#..."}`
3. The finishing stack makes AI art match the library: `grain` always. `pixelate` for pixel styles.
   `grade` for duotone. `fade_edges` so it melts into the page.
