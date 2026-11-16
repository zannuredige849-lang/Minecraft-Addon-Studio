# Skill: Bedrock Animation, Render Controllers, and Molang

Use when writing `*.animation.json`, `*.render_controllers.json`, or Molang expressions.

## Animation file
```json
{
  "format_version": "1.8.0",
  "animations": {
    "animation.pixel_slime.idle": {
      "loop": true,
      "animation_length": 2.0,
      "bones": {
        "body": {
          "rotation": { "0.0": [0, 0, 0], "1.0": [0, 0, 2], "2.0": [0, 0, 0] }
        }
      }
    }
  }
}
```
- `animation_length` equals the last keyframe time.
- Keyframes must be in ascending time order.
- Animated bone names must exist in the geometry.

## Client entity wiring
```json
"animations": { "idle": "animation.pixel_slime.idle" },
"scripts": { "animate": [ { "idle": "query.is_alive" } ] }
```
Put the `animate` list under `scripts` (client entity format), and check `query.is_alive` against the Molang reference before shipping.

## Render controller
```json
{
  "format_version": "1.8.0",
  "render_controllers": {
    "controller.render.pixel_slime": {
      "geometry": "Geometry.default",
      "materials": [ { "default": "Material.default" } ],
      "textures": [ "Texture.default" ]
    }
  }
}
```

## Molang rules
- Namespaces: `query.`, `variable.`, `math.`, `q.`, `v.`, `t.`, `c.`.
- Balance parentheses; no empty expressions.
- Never invent a function. Confirm with the official Molang reference.

## Checklist
- [ ] Animation names are `animation.<ns>.<name>`.
- [ ] `animation_length` matches the last keyframe.
- [ ] Every client-entity animation reference exists.
- [ ] Render controller keys match the client entity's geometry and textures.
