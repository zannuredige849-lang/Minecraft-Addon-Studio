---
type: overview
status: existing
tags:
  - overview
  - structure
updated: 2026-11-16
---

# Repository Structure

Snapshot of the real tree (2026-11-16).

```text
Minecraft-Addon-Studio/
├── BP/                              behavior pack
│   ├── manifest.json
│   ├── entities/pixel_slime.json    server-side entity
│   └── texts/en_US.lang
├── RP/                              resource pack
│   ├── manifest.json
│   ├── entity/pixel_slime.entity.json   client entity
│   ├── models/entity/pixel_slime.geo.json
│   ├── textures/entity/pixel_slime.png
│   └── texts/en_US.lang
├── obsidian/                        this vault
├── .claude/settings.json            Claude Code permissions
├── CLAUDE.md                        working rules for Claude Code
├── README.md
└── .gitignore
```

## Folders that do not exist yet
`BP/scripts/`, `BP/items/`, `BP/blocks/`, `BP/loot_tables/`, `BP/spawn_rules/`, `BP/structures/`,
`RP/animations/`, `RP/animation_controllers/`, `RP/render_controllers/`, `RP/sounds/`.
Create them when the first file of that kind is added.

Related: [[Behavior Pack]] · [[Resource Pack]]


---
Back to [[Home]] · [[Dashboard]]
