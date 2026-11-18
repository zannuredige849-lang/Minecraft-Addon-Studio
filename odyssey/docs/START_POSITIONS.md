# Verified coordinates

Each point was read from the world's own LevelDB (`world/db`) with `tools/world_probe/spots.py` / `probe.py`. The
block below the point is solid, safe ground, and the point plus the block above it are air. World facts the probe
found:

- Superflat: bedrock at −64, stone to y = 39, water y = 40–61. The sea surface is y = 61.
- World spawn (level.dat): 0, 65, 3.

The configuration lives in `scripts/data/config.js` (`POINTS`, `START_POSITIONS`, `SITE_POINTS`). The teleporter
re-verifies each point at runtime and falls back to the nearest safe spot.

## Role starts

| Role | Point | x y z | Ground block |
|---|---|---|---|
| Odysseus | ogygia_court | 0.5 65 3.5 | stone_bricks (world spawn) |
| Telemachus | ithaca_square | −419.5 65 −199.5 | grass_block |
| Ithacan Companion | ogygia_harbor | 1.5 65 −18.5 | grass_block |
| Eumaeus | ithaca_eumaeus | −403.5 65 −195.5 | grass_block |

## Story points

| Point | x y z | Ground block |
|---|---|---|
| ogygia_calypso | 7.5 65 5.5 | grass_block |
| ogygia_temple | −11.5 65 −3.5 | grass_block |
| ithaca_palace (interior) | −419.5 65 −211.5 | smooth_quartz floor, roof at y = 70 |
| ithaca_harbor | −419.5 65 −185.5 | grass_block |
| ithaca_mentor | −423.5 65 −197.5 | grass_block |
| troy_beach | −149.5 65 −243.5 | sand |
| troy_horse | −149.5 65 −261.5 | oak_planks |
| sparta_temple | −259.5 65 −89.5 | **Runtime only.** The shipped world has open sea here (water to y = 61); `architect.js` raises the island when a player is within 140 blocks |
| cyclops_landing | 370.5 66 −149.5 | grass_block (east shore) |
| cyclops_cave | 318.5 67 −149.5 | grass_block |
| telepylus_dock | 560.5 65 42.5 | podzol |
| telepylus_gate | 560.5 65 60.5 | mossy_stone_bricks |
| aeaea_shore | 520.5 65 344.5 | grass_block |
| aeaea_hall | 520.5 65 370.5 | grass_block |
| hades_shore | 260.5 65 504.5 | black_concrete_powder |
| hades_altar | 260.5 65 514.5 | black_concrete_powder |
| sirens_rocks | −44.5 64 471.5 | stone |
| strait_cliff | −295.5 93 380.5 | stone |
| thrinacia_shore | −479.5 65 114.5 | grass_block |
| thrinacia_temple | −479.5 65 140.5 | grass_block |

## Coordinate errors found and fixed

| Was | Problem | Now |
|---|---|---|
| Galley at 0 64 −35 | Beach sand; the shore runs to z ≈ −37, so the ship sat stranded | 0 62 −44 (open water); pier extended to reach it |
| Cyclops pier from 275 64 −150 westward | Inside the mountain (surface y ≈ 111) | East shore, from 373 63 −150 eastward |
| Strait west beacon at y 64–73 | Buried in the Scylla cliff (surface y ≈ 110) | Built on the cliff top (runtime ground scan) |
| Strait discovery chest at −317 65 368 | Inside rock | y = 109 (cliff top) |
| Creature spawns at site y + 1 | Scylla spawned inside her cliff; others under hills | Terrain-aware spawn spots (`lib/terrain.js`) |
| Checkpoint respawn at site centre y + 1 | Same problem | Respawns at the verified site point |
