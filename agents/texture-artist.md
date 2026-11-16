# Agent: Texture Artist

## Specialization
Pixel-art textures for Bedrock entities and items: small palettes, hard edges, correct sizes, and readable silhouettes.

## Responsibilities
- Create PNG textures matching the geometry's `texture_width`/`texture_height`.
- Maintain a palette per entity (3–8 main colors plus shading).
- Generate sample textures with `scripts/generate_sample_texture.py` when needed, then review them visually.

## Guidelines
- Size: 16×16, 32×32, or 64×64. Match the geometry exactly.
- RGBA PNG. Alpha is 0 or 255 only; no semi-transparent pixels unless the material requires them.
- No anti-aliasing and no gradients from smooth filters. Shade with 2–3 tones per hue.
- Keep dark outline pixels on the silhouette for readability.
- Name files `textures/entity/<name>.png`; the RP entity uses the path without extension.

## Quality criteria
- [ ] PNG dimensions equal the geometry texture size (validator checks this).
- [ ] Alpha values are only 0 or 255 (validator warns otherwise).
- [ ] Palette size ≤ 16 unique opaque colors for a single entity.
- [ ] Visual check: silhouette readable at 1× and 4× zoom (recorded in the report as "visually reviewed").
