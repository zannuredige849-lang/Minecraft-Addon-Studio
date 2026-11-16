---
type: rules
status: verified
---
# Box UV math

For a cube with `size = [sx, sy, sz]` and `uv = [u, v]`:

- unwrap width `W = 2·(sx + sz)`
- unwrap height `H = sz + sy`
- must hold: `u + W ≤ texture_width` and `v + H ≤ texture_height`

Worked example (sample slime): body size `[4,4,4]`, uv `[0,0]` → W=16, H=8 → fits 16×16.
Head size `[4,2,4]`, uv `[0,8]` → W=16, H=6, v+H=14 ≤ 16 → fits.

Counter-example (test fixture): size `[4,4,4]`, uv `[14,14]` → fails (validator error "box UV").

Related: [[Geometry Rules]]
