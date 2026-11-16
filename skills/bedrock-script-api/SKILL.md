# Skill: Bedrock Script API (`@minecraft/server`)

Use when writing or reviewing `behavior_packs/<pack>_bp/scripts/*.js`.

## Setup
- BP manifest: script module with `entry: "scripts/main.js"`.
- BP dependency: `{ "module_name": "@minecraft/server", "version": "2.11.0" }`.
- Import only what you use:
```js
import { world, system } from "@minecraft/server";
```

## Patterns
- React to events with `world.afterEvents.<event>.subscribe(handler)`.
- Cancel only with `world.beforeEvents.<event>` and document why.
- Repeat work with `system.runInterval(fn, ticks)`; keep it cheap.
- Log with `console.warn` / `world.sendMessage` for player-visible output.

## Forbidden
- `eval`, `new Function`, `fetch(`, `XMLHttpRequest`, hard-coded tokens or URLs.
- Unbounded loops inside tick handlers.

## Verify before use
Check every API member against the official Script API reference for the version in `studio/config/studio.json`. If unsure, mark the code "unverified" in the report.

## Checklist
- [ ] Entry file exists; manifest declares the module.
- [ ] Imports are limited to `@minecraft/server` (and `@minecraft/server-ui` if declared).
- [ ] No forbidden patterns.
- [ ] `node --check` passes on the file.
