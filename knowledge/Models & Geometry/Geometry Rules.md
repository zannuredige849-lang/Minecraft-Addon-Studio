---
type: rules
status: verified
---
# Geometry rules

- 1 block = 16 model units. Cube `origin` is the minimum corner; `size` must be positive.
- One root bone; every `parent` must name an existing bone (checked by `validate-addon`).
- `pivot` is the joint for rotation; children inherit it.
- `texture_width` and `texture_height` must equal the PNG size (checked).
- Bone names: lowercase snake_case. Animations refer to these names, so renaming a bone breaks animations ([[Animation Rules]]).

Verified by: `npm run validate` and the sample in [[studio_demo_rp]].
Related: [[Box UV Math]] · [[Pixel Slime]]
