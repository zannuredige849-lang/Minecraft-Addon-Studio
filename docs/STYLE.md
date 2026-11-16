# Fantasy Pack Style: Heroic Chunky

Original art only. Reference images and packs are for learning, never for copying.

## Direction
Not vanilla. Big, bold, readable creatures with heroic proportions and strong accents.

## Proportions
- Bosses and brutes: oversized chest and shoulders, long heavy arms, small head set low and forward, short thick legs.
- Limbs are thick blocks (8–12 units wide on big mobs). Hands and fists are separate cubes.
- Horns, tusks and armor stick out of the silhouette so the mob reads from far away.

## Texture rules
All textures follow `TEXTURE_GUIDE.md`: 4 shades per material, 7–8 for metal, no random noise, no gradients, shading follows the shape.
- 1 texel per model unit. Atlas sized to fit (128×128, 256×128 or 256×256).
- Fur: base shade with small shadow clumps (1×2) and a few highlight pairs on upper areas.
- Muscles (pecs, abs, biceps, knees): highlight blocks with a shadow line under them; deep shadow in creases.
- Contact shadows where parts meet (under belts, above and below bracers, under hips).
- Armor: gold panels with rim shadows, lit top edges and a small glint. One engraved labyrinth icon is our signature mark.
- Cloth and fur gear: directional strands; uneven strips instead of transparency.
- Eyes: glowing red or ember. Every boss has a separate `_glow.png` emissive layer.

## Weapons
- Large heads (about 40% of total length), chunky collars with coloured bands, patterned hafts (twisted wood, wraps).

## Code and files
- Namespace `studio:`; one model, one texture, one glow texture per mob.
- Left/right parts mirror with `mirror: true`.
- Small rest-pose rotations only (lean, open jaw, horn tilt), documented per mob.
