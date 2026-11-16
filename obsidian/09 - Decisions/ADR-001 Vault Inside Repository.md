---
type: decision
status: accepted
tags:
  - decisions
updated: 2026-11-16
---

# ADR-001: Vault Inside Repository

**Status:** accepted · **Date:** 2026-11-16

## Context
Documentation should stay next to the add-on code, sync between iPhone and computer, and stay private.

## Decision
Keep the vault in `obsidian/` in the existing private GitHub repository. Use git (Working Copy on iPhone, git or Obsidian Git on computer) for sync.

## Consequences
- Docs and code change in the same commits and branches.
- No extra sync service or subscription needed.
- Device-specific Obsidian files must be git-ignored to avoid conflicts.
- On iPhone, Working Copy links the whole repository, so `BP/` and `RP/` are visible in the vault too.


---
Back to [[Home]] · [[Dashboard]]
