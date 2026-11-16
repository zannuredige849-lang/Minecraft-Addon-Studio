---
type: animation
name: <% tp.file.title %>
identifier: animation.<entity>.<action>
loop: true
animation_length: 2.0
status: draft
created: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.file.title %>

Index: [[Animations & Molang/Index|Animations & Molang]] · Rules: [[Animation Rules]] · Molang: [[Molang Basics]]

## Purpose
Which entity, which state (idle, walk, attack), and when it plays.

## Bones animated
| Bone | Channels | Keyframes (time: value) |
|---|---|---|
|  | rotation / position |  |

## Client entity wiring
- Key in `animations`: 
- `scripts.animate` entry and condition (Molang):

## Checks
- [ ] Every bone exists in the geometry
- [ ] Last keyframe equals `animation_length`
- [ ] Molang parentheses balanced
- [ ] `npm run validate` passes

## Links
- Entity: [[Mob Encyclopedia/Index|Mob Encyclopedia]]
- Errors: [[Common Errors]]
