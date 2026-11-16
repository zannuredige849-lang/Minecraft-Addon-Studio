# Minotaur

Built by eye to match the project's two reference screenshots (front 3/4 and back). No files from other packs were used. Resource pack only for now.

## Files
- `RP/models/entity/minotaur.geo.json`, identifier `geometry.minotaur`, texture 128×128
- `RP/textures/entity/minotaur.png`, base texture
- `RP/textures/entity/minotaur_glow.png`, emissive layer (red eyes, pauldron gem). Not wired to a render controller yet.
- Axe: `RP/models/entity/minotaur_axe.geo.json`, `RP/textures/attachables/minotaur_axe.png`, `minotaur_axe_glow.png` (unchanged in this pass)

## Shape (units, 16 = 1 block)
- **Total height:** about 61 to the top of the head, about 68 with horns.
- **Legs:** 8×20×8 each with dark hooves; legs are about 42% of the height.
- **Hips and belt:** pelvis 16 wide, belt 20×4×12 with a square gold buckle at the front and a gold cross at the back.
- **Torso:** waist 16×7×11, deep chest 20×17×15, trapezius slab on top. Slight forward lean (5°).
- **Head:** 10×8×9 at the top front of the chest; muzzle 7×6×5 with nostrils and a gold nose ring; red eyes on the front corners and sides; thin striped horns 2×9×2 tilted forward and outward.
- **Arms:** upper arm 10×20×10, forearm 10×16×10, gold bracer 11×8×11 flush below the elbow, white claws at the bottom. Hands end about a third of the way up the body. Arms splay outward about 10° (plus 3° at the forearm).
- **Armor:** one gold pauldron 11×5×11 on the right shoulder with an orange gem.
- **Loincloth:** one front panel of white fur 10×13 with three ragged strands below. No back panel.
- **Tail:** thin brown tail with a white tuft, swinging toward the right leg.

## Paint (big-model rule, see `TEXTURE_GUIDE.md`)
- 34 colors: fur 5, muzzle 5, gold 8, belt 4, white fur 4 of 5, horn 3 of 5, hoof 3 of 4, red 2 of 4. Palettes are measured from the references (see `REFERENCE_STUDY.md`).
- Fur is mottled in clusters (no single-pixel noise); abs, pecs and back muscles are shade blocks with dark lines.
- Gold is a gold-block look: orange rims, yellow panel, light blotches.
- About 1.4% isolated pixels.

## Bones
`root` > `leg_r`, `leg_l`, `hips` > (`tail`), (`torso` > `head` > `horn_r`, `horn_l`), (`arm_r` > `forearm_r`), (`arm_l` > `forearm_l`).
Rest-pose rotations (degrees): torso X 5, horns X 14 / Z ±24, arms X -4 / Z ±10, forearms X -4 / Z ±3, tail X 10 / Z -14.

## Notes
- The entity's right side is -x (Bedrock convention), so the pauldron sits at -x.
- Left and right limbs share UVs through `mirror: true`.
- Previews come from a custom renderer, mirrored to match in-game handedness. Confirm in Blockbench.
