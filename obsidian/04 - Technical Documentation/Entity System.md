---
type: technical
status: existing
tags:
  - technical
  - entities
updated: 2026-11-16
---

# Entity System

How one custom entity is wired up, using [[Pixel Slime]] as the real example.

```text
BP/entities/pixel_slime.json          identifier studio:pixel_slime
        │  same identifier
RP/entity/pixel_slime.entity.json     client entity
        ├── geometry.default  → geometry.pixel_slime   (RP/models/entity/pixel_slime.geo.json)
        ├── textures.default  → textures/entity/pixel_slime  (RP/textures/entity/pixel_slime.png)
        ├── materials.default → slime                  (vanilla)
        └── render_controllers → controller.render.default (vanilla)
texts/en_US.lang                      entity.studio:pixel_slime.name
```

## Rules
- The identifier must match exactly in BP and RP.
- The client entity's short names (`default`) are what the render controller uses.
- `controller.render.default` uses `geometry.default`, `material.default` and `texture.default`, so those keys must exist.
- Texture paths have no `.png` extension.

## Adding a new entity (checklist)
1. `BP/entities/<name>.json` with identifier `studio:<name>`.
2. `RP/entity/<name>.entity.json` with the same identifier.
3. Geometry in `RP/models/entity/`, texture in `RP/textures/entity/`. Make the texture size match the box UV.
4. Lang lines in both `en_US.lang` files.
5. Optional: spawn rules, loot table, animations.
6. Run [[Validation and Testing]].
7. Add a note from **Template - Creature** under [[Entities]].


---
Back to [[Home]] · [[Dashboard]]
