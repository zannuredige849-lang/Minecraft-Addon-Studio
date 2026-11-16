# Skill: Pixel-Art Textures

Use when creating or reviewing entity and item PNG textures.

## Rules
- Size 16×16, 32×32, or 64×64; must equal the geometry's `texture_width`/`texture_height`.
- RGBA PNG. Alpha only 0 or 255.
- Limited palette: aim for ≤16 opaque colors per entity; 2–3 tones per hue.
- No anti-aliasing, no smooth scaling. Scale up with nearest-neighbor only for previews.
- Dark outline on the silhouette for readability.

## Generating a sample
`npm run texture:sample` regenerates the demo slime with Python and Pillow. Requires Pillow installed locally; otherwise draw the PNG in an external pixel editor.

## Review
- Check at 1× and 4× (nearest-neighbor) zoom.
- Confirm palette count and alpha values (validator checks dimensions and alpha).

## Checklist
- [ ] Dimensions match geometry.
- [ ] Alpha binary.
- [ ] Palette within limit.
- [ ] Visually reviewed (state this in the report).
