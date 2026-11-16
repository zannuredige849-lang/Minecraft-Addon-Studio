---
type: overview
status: existing
tags:
  - overview
  - requirements
updated: 2026-11-16
---

# Dependencies and Requirements

## Game
- Minecraft: Bedrock Edition. Both manifests set `min_engine_version` **1.21.0**.
- No experimental toggles are needed: the entity sets `is_experimental: false` and uses no beta APIs.

## Pack dependencies
- The behavior pack depends on the resource pack (UUID `…1a03`, version 1.0.0). See [[Pack Manifests]].
- No `@minecraft/server` or other script modules: there are no scripts yet.

## Vanilla assets the add-on relies on
- Material `slime` (client entity)
- Render controller `controller.render.default`

## Tools
- **Required:** none beyond a text editor and git.
- **Used so far:** Python 3 for JSON checks (`python3 -m json.tool`).
- **Useful later (planned):** Blockbench for models and animations, a Bedrock world for testing.
- **Docs:** Obsidian, no community plugins required.


---
Back to [[Home]] · [[Dashboard]]
