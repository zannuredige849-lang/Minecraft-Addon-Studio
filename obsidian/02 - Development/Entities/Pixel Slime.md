---
type: entity
status: existing
identifier: studio:pixel_slime
tags:
  - entity
  - mob
  - pixel-slime
updated: 2026-11-16
---

# Pixel Slime (`studio:pixel_slime`)

Status: **existing**, not yet tested in game.

## Files
| Side | File |
|------|------|
| Behavior | `BP/entities/pixel_slime.json` (format 1.21.0) |
| Client | `RP/entity/pixel_slime.entity.json` (format 1.10.0) |
| Model | `RP/models/entity/pixel_slime.geo.json`, see [[Pixel Slime Model]] |
| Texture | `RP/textures/entity/pixel_slime.png`, see [[Pixel Slime Texture]] |
| Names | `texts/en_US.lang` in both packs: "Pixel Slime", "Pixel Slime Spawn Egg" |

## Description flags
- `is_spawnable: true`: gives it a spawn egg.
- `is_summonable: true`: `/summon studio:pixel_slime` works.
- `is_experimental: false`.
- No spawn rules file, so it does **not** spawn naturally.

## Stats
| Component | Value |
|-----------|-------|
| `health` | 8 (max 8) |
| `collision_box` | 0.8 × 0.8 |
| `movement` | 0.25 |
| `attack` | damage 1 |
| `fall_damage` | 0 (immune) |
| `type_family` | `pixel_slime`, `mob` |

## Movement
`navigation.walk` (avoids water), `movement.jump` with a 0.5–1.5 s jump delay, `jump.static`, `physics`, `pushable` (by entities and pistons).

## Behaviors (lower priority number runs first)
| Priority | Behavior | Detail |
|----------|----------|--------|
| 0 | `behavior.float` | swims up in water |
| 2 | `behavior.nearest_attackable_target` | targets players within 12 blocks |
| 3 | `behavior.melee_attack` | attacks its target |
| 6 | `behavior.random_stroll` | speed ×1.0 |
| 7 | `behavior.random_look_around` | idle looking |

## Client
Material `slime`, geometry `geometry.pixel_slime`, render controller `controller.render.default`,
spawn egg colours `#7BD94A` (base) and `#2E7D32` (overlay).

## Known issues
- Texture is 32×16 but the model's box UV needs 48×24. See [[Pixel Slime Texture]].
- Never loaded in game, so behavior and looks are unverified.

## Not implemented
Splitting on death, size variants, loot table, sounds, animations, natural spawning.

Design side: [[Creatures]] · Balance: [[Balance]]


---
Back to [[Home]] · [[Dashboard]]
