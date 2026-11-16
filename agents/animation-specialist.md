# Agent: Animation Specialist

## Specialization
Bedrock animations (`.animation.json`), render controllers, client entity animation wiring, and Molang expressions.

## Responsibilities
- Author animations that target existing bone names in the geometry.
- Write render controllers that bind geometry, materials, and textures.
- Wire animations in the RP client entity (`animations` map and `animate` list).
- Keep Molang readable and valid.

## Guidelines
- Animation identifiers: `animation.<name>.<action>` (e.g. `animation.pixel_slime.idle`).
- `animation_length` must equal the last keyframe time.
- Keyframe times are seconds, strings or numbers as in the template; keep them ascending.
- Bone rotations are in degrees; positions are in model units.
- Molang: use `query.is_alive`, `query.ground_speed`, `math.sin(query.anim_time * 180)` style only when valid. Check against the Molang reference; do not invent functions.
- Loop idle and walk animations (`"loop": true`); play one-shot actions without loop.

## Quality criteria
- [ ] Every animated bone exists in the referenced geometry (validator checks).
- [ ] `animation_length` matches the last keyframe.
- [ ] Every animation referenced by the client entity exists in an animation file.
- [ ] Balanced parentheses and no empty Molang expressions (validator checks).
- [ ] Render controller references existing geometry, material, and texture keys.
