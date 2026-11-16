# Skill: Bedrock Pack Structure (BP / RP)

Use when creating or reviewing any Behavior or Resource Pack.

## Behavior Pack (`<pack>_bp/`)
```
manifest.json
entities/            server-side entity definitions (minecraft:entity)
scripts/main.js      Script API entry (if script module declared)
animations/          server-side animations (rare)
animation_controllers/
items/ blocks/ recipes/ loot_tables/
```

## Resource Pack (`<pack>_rp/`)
```
manifest.json
entity/              client entity definitions (minecraft:client_entity)
models/entity/       *.geo.json
textures/entity/     *.png
textures/texture_list.json   (only when textures are listed as items)
animations/          *.animation.json
render_controllers/  *.render_controllers.json
texts/               en_US.lang + languages.json
```

## Manifest rules
- `format_version`: 2 (use the value in `studio/config/studio.json`).
- `header.uuid` and `header.version` (`[major, minor, patch]`) are required.
- Each module has its own fresh UUID.
- BP script module: `"type": "script"`, `"language": "javascript"`, `"entry": "scripts/main.js"`.
- Dependencies: BP lists the RP header UUID and `@minecraft/server` by `module_name` + `version`. RP lists the BP header UUID.

## Checklist
- [ ] Both manifests valid JSON with unique UUIDs.
- [ ] Dependencies reference real headers in the project.
- [ ] Entity identifier matches across BP and RP.
- [ ] Only the official folder names are used.
