---
type: decision
status: accepted
tags:
  - decisions
updated: 2026-11-16
---

# ADR-002: Wikilinks and Core Plugins Only

**Status:** accepted · **Date:** 2026-11-16

## Context
The vault should open on any device with no setup, and links should survive renames.

## Decision
- Use Obsidian wikilinks with vault-wide unique note names.
- Use only core plugins (Templates, Backlinks, Outline, Graph, Bookmarks, etc.). No Dataview. The dashboard is plain Markdown.
- Obsidian Git is optional, not required.

## Consequences
- Links resolve in Obsidian. On GitHub's web view, wikilinks show as plain text.
- The dashboard is updated by hand (or by Claude Code), not by queries.


---
Back to [[Home]] · [[Dashboard]]
