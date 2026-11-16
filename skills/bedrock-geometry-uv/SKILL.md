# Skill: Bedrock Geometry and Box UV

Use when writing or checking `models/entity/*.geo.json`.

## Structure
```json
{
  "format_version": "1.12.0",
  "minecraft:geometry": [{
    "description": { "identifier": "geometry.name", "texture_width": 16, "texture_height": 16 },
    "bones": [{ "name": "body", "pivot": [0, 8, 0], "cubes": [{ "origin": [-4, 0, -4], "size": [4, 4, 4], "uv": [0, 0] }] }]
  }]
}
```

## Units and pivots
- 1 block = 16 model units. Origins are the minimum corner.
- `pivot` is the joint for rotation. Child bones inherit the parent transform.

## Box UV unwrap size
For a cube `size = [sx, sy, sz]` with `uv = [u, v]`:
- Unwrap width = `2 * (sx + sz)`; unwrap height = `sz + sy`.
- Require `u + width ≤ texture_width` and `v + height ≤ texture_height`.

Example: size `[4,4,4]` at `uv [0,0]` needs 16×8, which fits a 16×16 texture.

## Checklist
- [ ] One root bone; all `parent` references exist.
- [ ] Sizes are positive.
- [ ] Every box UV passes the bounds rule.
- [ ] `texture_width`/`texture_height` equal the PNG size.
