---
type: reference
status: verified
---
# Format versions used by this studio

Source of truth: `studio/config/studio.json`. Checked with Creator Tools 0.21.0 `mct validate` on 2026-11-16.

| Item | Value | Check result |
|---|---|---|
| Manifest `format_version` | 2 | standard |
| Behavior entity | 1.26.60 | ENTITYTYPE120 satisfied |
| Client entity (resource) | 1.26.60 | FORMATVER300 satisfied |
| Animation | 1.10.0 | FORMATVER216/218 satisfied (exact value expected) |
| Geometry | 1.12.0 | no finding |
| Render controller | 1.8.0 | no finding |
| `@minecraft/server` | 2.11.0 | referenced by Creator Tools; not checked in game |

Open question: `min_engine_version` `[1,21,40]` is unverified. See [[Common Errors]].

Related: [[Behavior Packs/Index|Behavior Packs]] · [[Resource Packs/Index|Resource Packs]]
