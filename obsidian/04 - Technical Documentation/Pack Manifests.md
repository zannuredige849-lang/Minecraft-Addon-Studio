---
type: technical
status: existing
tags:
  - technical
  - manifest
updated: 2026-11-16
---

# Pack Manifests

| Pack | Header UUID | Module UUID | Module type | Version |
|------|-------------|-------------|-------------|---------|
| BP | `3f0c1b7a-5d2e-4c1a-9a63-0b7d2f6e1a01` | `…1a02` | data | 1.0.0 |
| RP | `3f0c1b7a-5d2e-4c1a-9a63-0b7d2f6e1a03` | `…1a04` | resources | 1.0.0 |

- Both use `format_version` 2 and `min_engine_version` [1, 21, 0].
- The BP lists the RP header UUID as a dependency, so enabling the BP pulls in the RP.

## Rules
- Never change a published UUID. Bump `version` instead.
- New packs get new UUIDs.
- All four UUIDs must be unique. [[Validation and Testing]] checks this.


---
Back to [[Home]] · [[Dashboard]]
