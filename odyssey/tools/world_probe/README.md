# world_probe

Reads the world's LevelDB directly (no Minecraft needed) to verify coordinates.

- `ldb.py` – minimal LevelDB SSTable/log reader (Bedrock raw-deflate blocks)
- `nbt.py` – little-endian NBT reader (block palettes, level.dat)
- `terrain.py <db> '<sites json>'` – surface summary per site
- `spots.py <db> '[{"name":..,"x":..,"z":..,"r":..}]'` – nearest safe standing spot (solid ground, 2 air above)
- `hmap.py <db> <x> <z> <radius> <step>` – ASCII height map (`~` = sea)
- `probe.py <db> '[[x,z],[x,z,[ys]]]'` – raw block column

Every point in `world/behavior_packs/Odyssey_Creatures_BP/scripts/data/config.js` was checked with `spots.py`/`probe.py`.
