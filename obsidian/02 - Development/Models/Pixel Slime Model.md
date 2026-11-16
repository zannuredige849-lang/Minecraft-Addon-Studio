---
type: model
status: existing
tags:
  - model
  - pixel-slime
updated: 2026-11-16
---

# Pixel Slime Model

File: `RP/models/entity/pixel_slime.geo.json`. Format 1.12.0. Status: **existing**.

| Field | Value |
|-------|-------|
| Identifier | `geometry.pixel_slime` |
| Declared texture size | 32 × 16 |
| Visible bounds | width 2, height 1.5, offset [0, 0.5, 0] |

## Bones
| Bone | Parent | Pivot | Cubes |
|------|--------|-------|-------|
| `body` | none | [0, 0, 0] | one 12×12×12 cube at origin [-6, 0, -6], UV [0, 0] |
| `eyes` | `body` | [0, 6, 0] | two 2×2×1 cubes at [-4, 7, -6.1] and [2, 7, -6.1], UV [24, 0] |

## Known issue: UV does not fit
With box UV, a 12×12×12 cube needs a **48 × 24** area, but the texture is 32 × 16.
The eye UV (24, 0 → 30, 3) also sits inside the body's UV area.
Fix: make the texture 64 × 32, set `texture_width` 64 / `texture_height` 32, and move the eye UV outside the body area (for example [48, 0]). Tracked in [[Backlog]].

Also: the eye cubes sit mostly inside the body (z −6.1 to −5.1). Only 0.1 sticks out. Check in game.

Texture: [[Pixel Slime Texture]] · Entity: [[Pixel Slime]]


---
Back to [[Home]] · [[Dashboard]]
