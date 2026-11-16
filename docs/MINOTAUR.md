# Minotaur: Hunched Warden

Original design in the Mythforge style (see `STYLE.md`, `STYLE_ANALYSIS.md`). Resource pack only for now.

## Files
- `RP/models/entity/minotaur.geo.json`, identifier `geometry.minotaur`, 128×128
- `RP/textures/entity/minotaur.png`, base texture
- `RP/textures/entity/minotaur_glow.png`, emissive layer (eyes, chest glyph, forearm runes). Not wired to a render controller yet.
- `RP/models/entity/minotaur_axe.geo.json`, identifier `geometry.minotaur_axe`, 64×64
- `RP/textures/attachables/minotaur_axe.png` and `minotaur_axe_glow.png`

## Design
- Hunched brute: torso leans 22° forward, thick neck, heavy shoulder mass, long arms.
- Digitigrade legs: thigh forward, shin back, flat hoof.
- Bull head: wide skull, brow ridge, long muzzle with nose pad, jaw with two tusks.
- Horns: three segments per side (base, mid, tip) with rotation, bone fading to a dark tip.
- Gear: leather chest band, belt with gold buckle, bronze shoulder plate (left), bronze bracer (right), broken iron shackle with chain (left wrist), maroon loincloth.
- Accent colour: gold. Glow colour: ember orange.

## Bones
`root` > `hips` > `torso` > (`neck` > `head` > `jaw`), (`arm_l` > `forearm_l`), (`arm_r` > `forearm_r`);
`hips` > (`leg_*` > `shin_*` > `hoof_*`), `tail`.
Rest-pose rotations: torso 22, neck -10, head -10, arms -30, forearms -20, legs -25, shins 50, hoofs -25, tail 15, jaw 6 (degrees, X axis).

## Notes
- Left and right sides share UVs through `mirror: true` (arms, forearms, fists, thighs, shins, hoofs, ears, horns, tusks).
- Geometry is shifted so the hooves touch y = 0.
- Rotation signs follow the Bedrock file convention (X and Y inverted against standard math). Confirm in Blockbench.
- Previews were rendered with a custom script, not the game.
