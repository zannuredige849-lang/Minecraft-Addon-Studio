---
type: boss
name: <% tp.file.title %>
identifier: studio:<name_snake_case>
status: draft
phases: 1
created: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.file.title %>

Index: [[Boss Encyclopedia/Index|Boss Encyclopedia]] · Home: [[Home]]

## Summary
What the boss is, where it appears, and what it asks of the player.

## Identifiers
- Behavior entity: `studio:<name>`
- Geometry / texture / animations: same naming as [[Mob Encyclopedia/Index|mobs]]

## Stats
| Stat | Value | Notes |
|---|---|---|
| Health |  |  |
| Movement |  |  |
| Damage |  |  |

## Phases
### Phase 1
- Trigger:
- Attacks:
- Animation(s):

### Phase 2 (if any)
- Trigger:
- Attacks:

## Script hooks
Link [[Script API/Index|Script API]] and list every event the boss subscribes to. Bosses must not run unbounded per-tick work.

## Fight checklist
- [ ] Phase transitions tested
- [ ] Health bar / feedback defined
- [ ] Performance: no per-tick entity scans
- [ ] Tested in Minecraft (manual)

## Links
- Related mobs: [[Mob Encyclopedia/Index|Mob Encyclopedia]]
- Related errors: [[Common Errors]]
