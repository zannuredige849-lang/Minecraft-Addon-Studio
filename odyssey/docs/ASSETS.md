# Assets: repaired, added, missing and incomplete

## Repaired

| Asset | Problem | Fix |
|---|---|---|
| 9 hand-item attachables (xiphos, dory, bow, spear, club, knife, cleaver, staff, hoplon) | Not bound to the hand bone, no first/third-person transforms. They box-mapped a 16×16 icon onto a 1×2×14 stick, so a garbled stick floated at the player's body | Removed. The items render as normal held items using their icons |
| copper_helm, copper_cuirass, aegis_copper_plate attachables | A 16×16 icon stretched over a box; no armour render controller or glint | Real armour: a Corinthian helmet with a red crest (custom geometry on the `head` bone) and a muscle cuirass / Aegis plate (own chest geometry). Painted armour textures, `controller.render.armor`, enchant glint |
| 16 move animation controllers | States only had transitions back through `none`, so chained moves (e.g. hurt during cheer) stuck on the wrong pose | Every move state can reach every other state, with an idle fallback |
| ship_crew texture | Horizontal colour bands that ignored the model's UV layout (the face got cloth colour) | UV-correct painted texture at 8× resolution (`tools/paint_humans.py`) |
| Sound IDs `odyssey.laestrygonian.clang`, `.impale`, `odyssey.tiresias.prophecy` | Played by scripts, never defined | Defined, reusing the matching recordings |
| Galley, Cyclops pier, Strait beacon and chest, creature spawns | Wrong coordinates (see START_POSITIONS.md) | Fixed |
| Site architecture | Flagged as built even when `/fill` ran in unloaded chunks, leaving sites half-built forever | Built only once the site's chunks are loaded (rebuilt once under a v3.0 flag) |
| Old "Ch. 8/9" lines and the "Nestor's Cave" / "silver-armored" text | Did not match the film or the new chapter order | Rewritten |

## Added

- `studio:odyssey_person`: Telemachus, Mentor, Eumaeus, three guide types (scout, fisherman, shepherd) and an
  Odysseus stand-in. It has walk, point and look animations, and a talk interaction.
- Character portraits (`textures/ui/odyssey/portrait_*.png`), rendered from the actual models.
- Armour geometry and textures (`models/entity/studio_armor.geo.json`, `textures/models/armor/*`).
- 246 new strings, each in English and Russian.

## Missing or not implemented (honest list)

- **Suitors, Penelope, Antinous, Argos, Menelaus and Helen:** no models. The suitor fight is not playable; the bow
  trial ends the campaign.
- **Mentor's death and the bandit ambush** (both in the film): not depicted.
- **Map building:** no new large regions were built in this pass. Work was limited to fixes (pier, ship, cliff
  structures) and the existing runtime builders. Settlements, palace interiors, roads, camps and forests at film-level
  detail remain to be built by hand in-game.
- **Custom 3D held weapons:** removed rather than rebuilt. Proper 3D held models need first-person tuning in a real
  client.
- **Calypso texture:** the lattice veil was reviewed and kept; it is a deliberate transparent net, not noise.
- **Music and voice:** the existing tracks are reused. There is no new audio.
