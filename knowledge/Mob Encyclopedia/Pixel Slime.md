---
type: mob
identifier: studio:pixel_slime
status: verified
---
# Pixel Slime

Sample mob for the studio. A small green slime that wanders and looks around.

- Behavior: [[studio_demo_bp]] (`entities/pixel_slime.json`): health 8, movement 0.25, random stroll, random look.
- Visuals: [[Geometry Rules|geometry]] with root → body → head; 16×16 texture ([[Pixel Art Rules]]).
- Animation: `animation.pixel_slime.idle` ([[Animation Rules]]), played by `query.is_alive`.
- Join message: [[Script API 2.11.0 Notes]].

Checks: validator passes. Not yet tested in Minecraft.
Index: [[Mob Encyclopedia/Index|Mob Encyclopedia]]
