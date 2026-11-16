---
type: rules
status: verified
---
# Animation rules

- Identifier: `animation.<entity>.<action>`.
- `animation_length` must equal the last keyframe time (validator error otherwise).
- Keyframe times ascend strictly (validator warning otherwise).
- Animated bones must exist in some geometry (validator error otherwise).
- Client entity wiring: `description.animations` maps a key to the animation; `scripts.animate` lists `{key: Molang}`.
- Format version for animations: 1.10.0 in this studio ([[Format Versions]]).

Related: [[Molang Basics]] · [[Pixel Slime]]
