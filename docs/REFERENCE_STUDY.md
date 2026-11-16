# Reference study: measuring models and textures from screenshots

What I learned from the two Minotaur reference screenshots (front 3/4 and back), and the method to repeat for any future reference. Measurements only; no files from other packs were used.

## 1. Method

1. **Texel size.** Scan rows and columns of a flat area (chest, back, legs) for sharp brightness edges. The gaps between edges cluster at multiples of one texel. Here they were 14 / 28 / 42 / 56 px on the upper back and 11 / 22 / 33 / 44 px on the legs. So **1 texel ≈ 13–14 px** on the upper body and **≈ 11 px** on the legs (the legs are farther from the camera).
2. **Material masks.** Select pixels by colour rules (gold, belt, white fur, hoof, fur, muzzle) and take bounding boxes and row widths.
3. **Palettes.** Median-cut each material mask into 4–8 colours and sort dark to light.
4. **Undo the lighting.** Screenshot colours include Minecraft's face shading (top 100%, front/back 80%, sides 60%). Dividing by about 0.8 gives the texture colours.
5. **Check by rendering.** Render our model from the same angles with the same face shading, apply the same masks, and compare the mean colours and areas. Adjust until they match.

## 2. Model findings (in texels = model units)

| Part | Measured | Notes |
|---|---|---|
| Torso, belt top → shoulders | ≈ 24 | waist 7 + chest 17 |
| Belt | ≈ 20 wide, 4–5 tall | |
| Legs, below the belt | ≈ 24–26 tall | legs ≈ 42% of total height |
| Both legs together | ≈ 18–19 wide | each leg ≈ 8 |
| Hooves | ≈ 2–3 tall | same footprint as the leg |
| Silhouette width | ≈ 37 at the shoulders → ≈ 46 at the hands | the arms splay ≈ 10–12° each |
| Hands | end ≈ ⅓ of the height above the ground | |
| Bracers | ≈ 8–11 wide, ≈ 8 tall | just below the elbow |
| Pauldron | ≈ 10 wide, ≈ 5 tall | right shoulder only |
| Head above the torso top | ≈ 5–7 | small head, front-top of the chest |

**Construction lessons**
- Simple boxes, 1 texel per unit, about 30 cubes in total.
- Rotations are used only where they shape the silhouette: arm splay, horn tilt, tail swing.
- Gear sits flush on the body (bracer top flush with the elbow, pauldron 1 unit above the shoulder) so there are no gaps.

## 3. Texture findings

Mean colours seen in the screenshots, then the texture palette derived from them:

| Material | Seen in screenshot (dark → light) | Texture palette used |
|---|---|---|
| Fur | `#4B2810` `#522C12` `#5F371C` `#693D1F` | `#47240E` `#5D3214` `#72401B` `#864D22` `#975D2B` |
| Gold | `#C58709` `#D58507` `#C8A609` `#D8BD0A` `#DDD730` | `#964800` `#C46A04` `#E28E08` `#F0B00A` `#FACC0E` `#FFE01E` `#FFF040` `#FFFC78` |
| Muzzle | `#C9AB8D` `#CBBE88` `#DACC96` `#EBE0B5` | `#96805C` `#B29C72` `#C8B486` `#DAC898` `#ECDEB2` |
| White fur | `#A39C99` `#AAA19D` `#ADA4A0` `#D9CEBB` | `#8C827C` `#A89E96` `#C4BAB0` `#DCD2C4` `#F0E6D6` |
| Belt | `#240D18` `#29141E` `#341520` `#3E1E28` | `#260E12` `#341418` `#421C20` `#54282A` |
| Hoof | `#1E1211` `#231E1A` `#2F2825` | `#1E1614` `#2A201C` `#362C28` `#443A34` |

**What the palettes teach**
- **Fur is warm and orange-red** with very little blue (B ≈ 0.3 × R). A neutral brown looks wrong next to it.
- **Gold is saturated yellow**, almost no blue, and its highlights are lemon yellow, not cream white. Orange carries the shadows and rims.
- **The muzzle is pale beige**, not pink.
- **White fur is warm grey**; pure white appears only on the lit top of strands.
- **The belt is a dark wine colour**, closer to red-brown than purple.
- **Hooves are a warm near-black**, not neutral grey.
- **Contrast is high inside the fur**: dark patches cover about a third of the surface, in clusters of 2–4 texels.

## 4. Verification result

The back views were compared with the same masks and the same lighting:

| | Reference | Ours |
|---|---|---|
| Fur mean | (87, 48, 18) | (87, 49, 19) |
| Gold mean | (204, 164, 17) | (206, 173, 20) |
| Belt mean | (47, 21, 26) | (52, 22, 25) |
| Gold share of the body | ≈ 10% | ≈ 13% |

## 5. Limits

- The screenshots use a perspective camera and JPEG compression, so measurements are about ±1 texel.
- The exact pixel pattern of the original texture can't be recovered from a screenshot. Ours is painted by our own generator with the measured palette and cluster sizes.
