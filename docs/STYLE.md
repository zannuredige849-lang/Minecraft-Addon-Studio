# Fantasy Pack Style: Heroic Chunky

Original art only. Reference images and packs are for learning, never for copying.

## Direction
Not vanilla. Big, bold, readable creatures with heroic proportions and strong accents.

## Proportions
- Bosses and brutes: oversized chest and shoulders, long heavy arms, small head set low and forward, short thick legs.
- Limbs are thick blocks (8–12 units wide on big mobs). Hands and fists are separate cubes.
- Horns, tusks and armor stick out of the silhouette so the mob reads from far away.

## Texture rules
- 1 texel per model unit. Atlas sized to fit (128×128, 256×128 or 256×256).
- Fur and skin: mottled base with darker patches (2–3 px) and a few lighter ones. No fine per-pixel noise.
- Painted muscles: pecs, abs, biceps and knees as lighter blocks with a dark line under them.
- Gradient on every side face: lighter at the top, darker at the bottom.
- Armor: saturated gold with an orange rim and a lighter inner panel. One engraved labyrinth icon is our signature mark.
- Cloth and fur gear: off-white fur with dirt spots; uneven strips instead of transparency.
- Eyes: glowing red or ember. Every boss has a separate `_glow.png` emissive layer.

## Weapons
- Large heads (about 40% of total length), chunky collars with coloured bands, patterned hafts (twisted wood, wraps).

## Code and files
- Namespace `studio:`; one model, one texture, one glow texture per mob.
- Left/right parts mirror with `mirror: true`.
- Small rest-pose rotations only (lean, open jaw, horn tilt), documented per mob.
