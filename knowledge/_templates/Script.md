---
type: script
name: <% tp.file.title %>
file: behavior_packs/<pack>_bp/scripts/<name>.js
api: "@minecraft/server 2.11.0"
status: draft
created: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.file.title %> (script)

Index: [[Script API/Index|Script API]] · Patterns: [[Script API 2.11.0 Notes]]

## Purpose
What the script reacts to and what it changes.

## Events subscribed
| Event | Handler | Cancels? | Why |
|---|---|---|---|
| `world.afterEvents.…` |  | no |  |

## Imports
- `@minecraft/server` only (add `@minecraft/server-ui` only if declared in the manifest)

## Forbidden in this studio
`eval`, `new Function`, `fetch`, network calls, hard-coded secrets. See [[Errors & Solutions/Index|Errors]].

## API members used (verify each)
| Member | Source checked | Status |
|---|---|---|
|  | official Script API reference | unverified |

## Checks
- [ ] Manifest declares the script module and dependency
- [ ] `npm run validate` passes (imports, forbidden patterns, syntax)

## Links
- Entity using it: 
- Journal: 
