# Minecraft-Addon-Studio
Minecraft-Addon-Studio

## studio:pixel_slime

Bedrock add-on (`BP/` + `RP/`) adding the `studio:pixel_slime` entity.
Copy both folders into `development_behavior_packs` / `development_resource_packs`, enable them on a world, then run:

    /summon studio:pixel_slime

## Odyssey creatures

Creatures from Christopher Nolan's *The Odyssey* (2026), added to the same packs:

| Identifier | Character | Behavior |
|---|---|---|
| `studio:cyclops` | Cyclops Polyphemus (club, single eye) | Hostile to players, 120 HP, heavy hits |
| `studio:siren` | Siren (feathered wings and legs) | Hostile, hits slow the target |
| `studio:circe` | Circe (robe, hood, glowing staff) | Neutral, fights back when hit, hits weaken the target |
| `studio:scylla` | Scylla (six snapping heads) | Hostile, 250 HP |

Spawn any of them with `/summon studio:cyclops` (or siren, circe, scylla).
Models use 256x256 atlases, with walk and idle animations under `RP/animations/`.
