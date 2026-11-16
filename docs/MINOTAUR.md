# Minotaur: Heroic Brute

Original model in the chunky, heroic style (see `STYLE.md`). Resource pack only for now.

## Files
- `RP/models/entity/minotaur.geo.json`, identifier `geometry.minotaur`, texture 256×128
- `RP/textures/entity/minotaur.png`, base texture
- `RP/textures/entity/minotaur_glow.png`, emissive layer (red eyes, pauldron gem, buckle gem). Not wired to a render controller yet.
- `RP/models/entity/minotaur_axe.geo.json`, identifier `geometry.minotaur_axe`, 64×64
- `RP/textures/attachables/minotaur_axe.png` and `minotaur_axe_glow.png` (collar rune)

## Design
- **Proportions:** massive chest (24 wide) and shoulder hump, gorilla arms that reach the knees, small head pushed low and forward, short thick legs.
- **Head:** big bull head, dark brow ridge, light muzzle with nostrils, gold nose ring, open jaw with fangs, glowing red eyes, scar on the forehead.
- **Horns:** L-shaped bone horns (out, then up), with gold bands under the tips.
- **Armor:** gold bracers on both forearms with an engraved labyrinth icon, gold pauldron on the left shoulder with a red gem.
- **Gear:** dark studded belt with gold buckle, white fur loincloth in uneven strips (front and back), tufted tail.
- **Paint:** follows `TEXTURE_GUIDE.md`. 38 colors in total: 4 shades each for fur, skin, mouth, bone, hoof, leather, white fur and red; 7 of 8 gold shades. Muscles are shade blocks with crease shadows, contact shadows sit where parts meet, white claws on the fists. Under 2% isolated pixels.
- **Axe:** double-crescent blades with curled tips, twisted wooden haft, blue-steel collar with red bands and a glowing rune.

## Bones
`root` > `leg_l`, `leg_r`, `hips` > (`tail`), (`torso` > `head` > `jaw`, `horn_l`, `horn_r`), (`arm_l` > `forearm_l`), (`arm_r` > `forearm_r`).
Rest-pose rotations (degrees): torso X 10, head X -10, jaw X 18, horns X 10 / Z ±12, arms X -10 / Z ±6, forearms X -15, tail X 20.

## Notes
- Left and right share UVs through `mirror: true`.
- Geometry is shifted so the hooves touch y = 0.
- Rotation signs follow the Bedrock file convention (X and Y inverted against standard math). Confirm in Blockbench.
- Previews were rendered with a custom script, not the game.
