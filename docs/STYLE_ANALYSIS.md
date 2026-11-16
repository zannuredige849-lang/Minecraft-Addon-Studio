# Global analysis of 15 reference add-ons

Read-only study. Nothing was copied. Counts come from scanning manifests, entity/geometry/animation JSON, scripts, and PNGs.

## 1. Packs studied

| # | Pack | Type | Engine | Notable |
|---|---|---|---|---|
| a01 | Friday the 13th | BP+RP | 1.26.40 | 4 entities, 12 textures, mcfunction-driven |
| a02 | FantasyCraft 1.5 | BP+RP | 1.21.20 | 883 files, 23 scripts, 79 blocks, 71 entities, world gen |
| a03 | Structures from the Past | BP+RP | 1.21.130 | structures and loot, 1 script |
| a04 | Salt and Ships | BP+RP | 1.26.33 | 49 entities, 83 items, 58 lang files, pirate theme |
| a05 | ZhekAziz Fathylogy | BP+RP | 1.21.0 | 662 textures, 26 scripts, outposts, trolls, merfolk, warrior hiring |
| a06 | Pirate's Life | BP+RP | 1.26.0 | 12 entities, 18 items, 14 blocks |
| a07 | Nico's More Dungeon | BP+RP | 1.26.50 | 45 blocks, 208 loot tables, 15 scripts, ntk projectile helpers |
| a08 | The Forgotten Legends: Age of Renewal | BP+RP (nested zips) | — | orc "WAAAGH" theme, 28 entities, 81 items, 17 scripts, necromancer scythe |
| a09 | Mythological Craft | BP only | 1.21.80 | 73 entities, 177 items, 30 scripts, griffin and dragon, petrified player |
| a10 | Alylica's Dungeons | BP+RP | 1.26.20 | the largest: 224 entities, 592 items, 421 scripts, 3683 textures |
| a11 | Fantasy Adventure | BP+RP | 1.26.40 | 67 entities, 85 items, medusa, mythic weapons, 24 render controllers |
| a12 | Mythics and Magic | BP+RP | 1.21.131 | 271 geometry files, 154 recipes, griffin, wyvern, ice dragon, guidebook |
| a13 | Mowzie's Mobs | BP+RP | 1.21.40 | 43 entities, 52 scripts, custom jigsaw, gong, cave carver |
| a14 | Ranzie's Rise and Survive | 4 sub-packs | 1.21.90 | UI and visual effects, fullmoon script, 343 sounds |
| a15 | Dungeon Raiders | BP+RP | 1.21.90 | 94 blocks, 149 loot tables, coins, merchant, hanging leaves |
| a16 | Player Resizer | BP only | 1.21.132 | 1 script, changes player scale |

## 2. Entities and components (across 13 entity-heavy packs, 1,400+ entity files)

- **Format versions:** most entities use `1.16.0`, `1.17.0`, `1.20.70`, or `1.21.0`. There is no single standard.
- **Most used components:** `physics`, `collision_box`, `type_family`, `pushable`, `health`, `damage_sensor`, `knockback_resistance`, `jump.static`, `breathable`, `movement`, `navigation.walk`, `behavior.*`, `scale`, `loot`, `experience_reward`.
- **Component groups** are used heavily. The most common events are `entity_spawned`, `spawn_adult`, `entity_transformed`, and custom `*:despawn` events.
- **Geometry:** most files still use `format_version 1.12.0` (931 of about 1,100). Bone names are mostly generic (`body`, `head`, `rightLeg`, `leftLeg`, `rightArm`, `leftArm`, `waist`, `tail#`, `jaw`, `hat`, `layer_#`).

## 3. Textures

- **Sizes:** 16×16 is the most common (about 3,600), then 64×64 (886), 128×128 (423), 256×256 (309), 32×32 (264). Pack a05 uses 256×256 for its minotaur.
- **Mob sizes:** 64×64 is the standard for bipeds and beasts. 128 and 256 are used for bosses and mythic creatures.
- **Layout:** most packs use the vanilla UV layout. Only a few use custom UV maps.
- **Overlays:** emissive glow layers are common, using a second texture or a material with `glow`.

## 4. Animations and controllers

- **Animation keys:** `idle` (155), `walk` (153), `attack` (112), `death` (98), `run`, `fly`, and `first_person_hold` / `third_person_hold` for weapons.
- **Controllers:** animation controllers are used for states (idle, walk, attack, death). Render controllers handle material and texture selection.
- **Particles:** a few packs add particle files tied to animation events.

## 5. Scripts and code patterns

Counts are numbers of files that use each pattern:

| Pattern | Files | Use |
|---|---|---|
| `world.afterEvents.*` | 241 | `entityHurt`, `entitySpawn`, `entityDie`, `entityHitEntity`, `projectileHitBlock`, `itemUse`, `playerSpawn`, `dataDrivenEntityTrigger` |
| `world.beforeEvents.*` | 191 | cancel or change actions before they happen |
| `system.runInterval` | 201 | per-tick or per-second logic |
| `system.runTimeout` | 218 | delayed actions |
| `system.run` | 157 | run in the next tick |
| `getComponent(...)` | 335 | reading entity components |
| `setDynamicProperty` / `getDynamicProperty` | 213 | storing state on entities and players |
| `runCommand` / `runCommandAsync` | 150 | command calls |
| `registerCustomComponent` | 146 | custom components |
| `ActionFormData` / `ModalFormData` | 48 + 19 | UI menus (guidebook, shops, settings) |
| `try { }` | 96 | error handling |
| `Vec3` / `vector` helpers | 43 | math |

Modules imported most often: `@minecraft/server` (571), `@minecraft/server-ui` (13). Only one pack imports gametest. Helper modules are common (`util.js`, `i18n.js`, `ntk_functions.js`). Packs that use `i18n.js` support multiple languages through lang keys.

**Good habits we should adopt:**
- Put state in dynamic properties, not in global variables. This survives reloads.
- Use `afterEvents` for most logic and `beforeEvents` only when you need to cancel something.
- Keep one helper file for math and one for i18n.
- Name every entity `namespace:name`, and use one namespace per pack.

**Habits to avoid:**
- Running `runInterval` on every entity. Use one global tick loop that scans the entities it needs.
- Hard-coding text instead of lang keys.
- Using old format versions (`1.12.0`) on new models. Bump the version when you need newer features.

## 6. Themes and identity

| Theme | Packs |
|---|---|
| Dungeon and undead | a10, a05, a07, a15 |
| Orc and warband | a08, a14 |
| Mythic beasts (griffin, wyvern, dragon) | a09, a12, a02 |
| Pirate and sea | a04, a06 |
| Greek and mythic weapons (medusa, minotaur) | a11, a09, a05 |
| Structures and outposts | a03, a05, a13 |
| Visual and atmosphere | a14, a02 |

Minotaur appears in 3 packs (a05, a09, a11). Only a05 explicitly targets a "reference-accurate" model, so we should avoid copying its design.

## 7. Patterns that are common across the packs

1. Vanilla 16 px items, with 64-px mobs.
2. Mob groups: a family tag (`type_family`), then a damage sensor, then loot and experience.
3. Spawn rules in separate files (about 25% of packs).
4. Dungeon-style loot tables with many pools.
5. Custom crafting recipes, mostly shaped.
6. Sounds grouped by mob (`sounds/mob/*`), with a `sound_definitions.json` per pack.

## 8. Unique style for us: "Mythforge" (original)

**Core idea:** a vanilla+ look, with each faction built from simple shapes and one strong accent color. Every mob and item should be readable from far away.

**Visual rules**
- **Textures:** 16 px items. Mobs use 64×64 for small creatures and 128×128 for bosses. 1 texel per model unit.
- **Palette:** 3 shades per material (dark, base, light). Each faction gets one accent: ember for orcs, verdant for elves, frost for giants, bone for undead, gold for the Minotaur and relics.
- **Outline:** 1px darker edge on the lower and right sides of body parts. No outline on hard metal.
- **Silhouette:** head about 30–40% of body height on mobs. Weapons: head about 40% of total length.
- **Materials:** keep painterly noise on fur and bark, but use flat light/dark on metal.

**Model rules**
- Base rigs: humanoid, quadruped, winged, and large beast. Reuse them across factions.
- Mirror left and right parts with `mirror: true`.
- Keep base models unrotated so animation stays simple.

**Code rules**
- Namespace: `studio:` for all identifiers.
- Entities: `minecraft:type_family` for groups, `damage_sensor` for immunities, one loot table per mob.
- Scripts: `afterEvents` first. Dynamic properties for state. One `main.js`, plus `util.js` (math), `i18n.js` (lang keys), and `factions.js` (faction data).
- UI: one `ActionFormData` guidebook. No custom UI until the pack is stable.

**Format rules**
- Target engine: the latest stable engine. Set `min_engine_version` to match the version you test on.
- Geometry: `format_version 1.16.0` or newer. Do not use `1.12.0` for new models.
- Entities: current format version per pack.

## 9. What we take and what we don't

**Take**
- Component-based entity design and family tags.
- Dynamic properties for state.
- A single guidebook UI.
- Loot tables with several pools.
- Mob sounds grouped by mob.

**Don't take**
- Any model, texture, UV layout, entity file, or name from these packs.
- Their minotaur, medusa, or griffin designs.
- Old geometry format versions.
- Global tick loops per entity.

## 10. Next steps (proposed)

1. Adopt the "Mythforge" visual rules in `docs/STYLE.md`.
2. Define a faction table in `docs/FACTIONS.md`: name, accent color, base rig, example mobs.
3. Build the goblin or orc grunt as the first full mob (model, texture, behavior, spawn, loot, egg). Use the base humanoid rig.
4. Rebuild the minotaur on the humanoid rig with a bull head.
