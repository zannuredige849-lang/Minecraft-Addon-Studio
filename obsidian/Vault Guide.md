---
type: guide
status: reference
tags:
  - meta
updated: 2026-11-16
---

# Vault Guide

How this vault works. The repository's `obsidian/` folder **is** the vault: open that folder in Obsidian.

## Rules
- One topic per note. Every folder has an index note with the same name as the section.
- Links use Obsidian wikilinks (`[[Note Name]]`). Note names are unique across the vault, so short links always resolve.
- Every note starts with YAML frontmatter: `type`, `status`, `tags`, `updated`.
- `status` values: `existing`, `planned`, `in-progress`, `deprecated`, `reference`.
- Images and other files go in `Attachments/`. Obsidian is configured to put pasted files there.
- New notes: use **Templates → Insert template** (core plugin, no install needed). See [[Templates Index]].

## Plugins
- **Required:** none. Only Obsidian core plugins are used.
- **Optional:** Obsidian Git (community plugin) for syncing from inside Obsidian. See [[GitHub Sync Guide]].

## Syncing
The vault is synced through the GitHub repository. Full steps for iPhone and computer: [[GitHub Sync Guide]].

## Why it is set up this way
See [[ADR-001 Vault Inside Repository]] and [[ADR-002 Wikilinks and Core Plugins Only]].


---
Back to [[Home]] · [[Dashboard]]
