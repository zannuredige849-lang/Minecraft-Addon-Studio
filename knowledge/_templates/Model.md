---
type: model
name: <% tp.file.title %>
geometry: geometry.<name>
texture_size: 16x16
status: draft
created: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.file.title %> (model)

Index: [[Models & Geometry/Index|Models & Geometry]] · Rules: [[Geometry Rules]] · UVs: [[Box UV Math]]

## Bone hierarchy
```
root
└── body (pivot [0,4,0])
    └── head (pivot [0,8,0])
```

## Cubes
| Bone | origin | size | uv | UV unwrap needed | Fits texture? |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Unwrap = `2·(sx+sz)` × `sz+sy`. Confirm with the validator.

## Files
- `resource_packs/<pack>_rp/models/entity/<name>.geo.json`
- Used by: [[<Client entity note>]]

## Checks
- [ ] Single root, all parents exist
- [ ] Positive sizes
- [ ] Box UVs inside texture
- [ ] `npm run validate` passes

## Links
- Texture: [[Pixel Art Rules]]
- Animations: [[Animation Rules]]
