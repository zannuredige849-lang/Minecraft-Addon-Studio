---
type: reference
status: unverified
---
# Script API 2.11.0 notes

- Dependency in BP manifest: `{ "module_name": "@minecraft/server", "version": "2.11.0" }`.
- Script module entry: `scripts/main.js`, `language: javascript`.
- Allowed imports: `@minecraft/server`, `@minecraft/server-ui` (only if declared).
- Forbidden (validator errors): `eval(`, `new Function(`, `fetch(`, `XMLHttpRequest`.
- Sample uses `world.afterEvents.playerSpawn` — **unverified** member, check the official reference.
- `package.json` lists `@minecraft/server` 2.11.0 as a devDependency (declared, not installed).

Related: [[Common Errors]] (SCRIPTMODULE110) · [[studio_demo_bp]]
