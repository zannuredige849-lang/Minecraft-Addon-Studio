# Texture Creation Guidelines – Minecraft Style

Universal rules for any texture in this project: mobs, items, blocks, armor and weapons. They are not tied to a specific model, character or color.

---

## 1. Color structure and shade variation

Every material uses one consistent palette of **4 clearly distinguishable shades of the same base color**.

The four shades must belong to the same color family. They should read as one material under different lighting, never as four unrelated colors.

| Shade | Role | Where it goes |
|---|---|---|
| **1 – Deep shadow** | Darkest value | Deep creases, joints, undersides, areas hidden from direct light |
| **2 – Secondary shadow** | Soft shadow | Transitions between surfaces, areas with less light |
| **3 – Base color** | Dominant value | Most of the texture |
| **4 – Highlight** | Lightest value | Exposed edges, upper surfaces, areas receiving more light |

## 2. Example of a four-shade palette

One base color, four variations:

| Shade | Role | Hex |
|---|---|---|
| 1 | Deep shadow | `#35231B` |
| 2 | Secondary shadow | `#513426` |
| 3 | Base color | `#754B34` |
| 4 | Highlight | `#A47755` |

- The difference between shades must be visible, but not excessively strong.
- Do not create four completely different colors. The result must look like one material under different lighting conditions.

## 3. Texture application and pixel distribution

Place details intentionally.

- Use **larger groups of pixels** to establish the primary color distribution.
- Use **smaller pixel clusters** to add secondary details.
- Place darker pixels in natural shadow areas.
- Use highlights selectively, not spread randomly.
- Avoid isolated pixels that do not contribute to the material's appearance.
- Keep the texture readable at the real in-game viewing distance.

**Variation follows the shape and structure of the model:**

- Rounded surfaces: gradual shade transitions.
- Flat surfaces: relatively consistent coloring.
- Edges: controlled highlights.
- Deep gaps: darker shades.

## 4. Material definition

Every material has its own visual character.

| Material | Texture treatment |
|---|---|
| Skin | Controlled tonal variation and subtle surface details |
| Stone | Larger irregular pixel clusters and mineral-like variation |
| Wood | Directional grain patterns following the structure |
| Metal | Strong contrast between shadows and highlights |
| Leather | Matte appearance with subtle tonal irregularities |
| Cloth | Simple folds and directional shading |
| Bone | Smooth ivory tonal transitions |
| Organic surfaces | Controlled natural variation without random noise |

Do not apply the same texture pattern to every material.

## 5. Lighting and shading

Use the same lighting on every texture.

- Upper-facing surfaces are generally lighter.
- Undersides are darker.
- Recessed areas get deeper shadows.
- Protruding elements get visible edge highlights.
- Overlapping body parts create subtle contact shadows.

Avoid excessive contrast that makes the model look dirty, damaged or noisy.

## 6. Quality requirements

**Required**

- Clean pixel-art appearance.
- Consistent color palettes.
- Four shades per base material color.
- Clearly readable separation between materials.

**Not allowed**

- Blurry gradients.
- Photographic textures.
- Random visual noise.
- Excessive pixel scattering.
- Unnecessary black outlines.
- Excessive highlights.
- Inconsistent lighting.
- Accidental color contamination between materials.

## 7. Final production rule

The texture communicates volume through **deliberate pixel placement**, not through excessive detail.

Every pixel serves a purpose: defining the material, creating depth, separating surfaces or emphasizing the shape.

The result should look like an official high-quality Minecraft texture: clean, recognizable, dimensional and consistent with the vanilla art direction.

---

## Review checklist

Use this before a texture is accepted.

- [ ] Each material uses exactly 4 shades of one color family.
- [ ] Base color covers most of each material; highlights are the smallest group.
- [ ] Shadows sit where the shape creates them (undersides, joints, gaps, contact areas).
- [ ] Highlights sit on upper surfaces and exposed edges only.
- [ ] No isolated pixels without a purpose.
- [ ] No random noise, blur, photo texture or unneeded black outline.
- [ ] Materials are clearly separated, with no color bleeding between them.
- [ ] Lighting direction matches the rest of the pack.
- [ ] Readable at in-game distance.
