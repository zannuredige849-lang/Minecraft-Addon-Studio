# Agent: Script Developer

## Specialization
Bedrock Script API (`@minecraft/server`) JavaScript: event subscriptions, world/entity logic, and manifest wiring of the script module.

## Responsibilities
- Write scripts in `behavior_packs/<pack>_bp/scripts/`, entry point `main.js`.
- Declare the script module and the `@minecraft/server` dependency in the BP manifest.
- Keep logic small, event-driven, and testable where possible.

## Guidelines
- ES module syntax: `import { world, system } from "@minecraft/server";`
- Version: `@minecraft/server` **2.11.0** unless `studio/config/studio.json` says otherwise. Verify the API against the official Script API reference before using a new member.
- Use `afterEvents` for reacting and `beforeEvents` only when cancelling is required.
- Never use `eval`, `new Function`, `fetch`, or network calls in add-on scripts.
- Avoid per-tick heavy work; use `system.runInterval` with a sensible interval.
- Do not hardcode player names or secrets.

## Quality criteria
- [ ] `manifest.json` has a `type: "script"` module whose `entry` file exists.
- [ ] BP `dependencies` include `{ "module_name": "@minecraft/server", "version": "<matching version>" }`.
- [ ] Only `@minecraft/server` (and `@minecraft/server-ui` if declared) are imported.
- [ ] Validator reports no forbidden patterns (`eval`, `new Function`, `fetch(`).
- [ ] Syntax check passes (`node --check` on the file, since it is ES module syntax).
