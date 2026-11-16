---
type: mob
name: <% tp.file.title %>
identifier: studio:<name_snake_case>
status: draft
created: <% tp.date.now("YYYY-MM-DD") %>
pack_bp: studio_demo_bp
pack_rp: studio_demo_rp
---

# <% tp.file.title %>

Index: [[Mob Encyclopedia/Index|Mob Encyclopedia]] · Home: [[Home]]

## Summary
One or two sentences: what it is and what the player does with it.

## Identifiers
- Behavior entity: `studio:<name>` — file: `behavior_packs/studio_demo_bp/entities/<name>.json`
- Client entity: `studio:<name>` — file: `resource_packs/studio_demo_rp/entity/<name>.entity.json`
- Geometry: `geometry.<name>` — file: `models/entity/<name>.geo.json`
- Texture: `textures/entity/<name>` (16×16 / 32×32 / 64×64)
- Animations: `animation.<name>.idle` (+ others)

## Behavior (BP)
| Component | Value | Reason |
|---|---|---|
|  |  |  |

## Visuals (RP)
- Silhouette and bones: [[<Model note>]]
- Texture plan: [[Pixel Art Rules]]
- Animations: [[Animation Rules]]

## Script hooks
Describe any `@minecraft/server` behavior. Link [[Script API/Index|Script API]].

## Status checklist
- [ ] Behavior entity valid (`npm run validate`)
- [ ] Client entity references resolve
- [ ] Texture size matches geometry
- [ ] Tested in Minecraft (manual)

## Links
- Related mobs: 
- Related errors: [[Common Errors]]
- Journal: 
