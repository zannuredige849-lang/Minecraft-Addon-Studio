---
type: errors
status: verified
---
# Common errors

## CPACKICON101 — pack_icon missing
- Symptom: Creator Tools "pack_icon image file not found … must use the .png extension".
- Cause: no `pack_icon.png` in the pack folder.
- Fix: add a PNG icon (sample: 128×128) to each pack. Done for [[studio_demo_bp]] and [[studio_demo_rp]].

## SCRIPTMODULE110 — @minecraft/server not registered
- Symptom: "Could not find an package.json registration for @minecraft/server".
- Fix: declare `@minecraft/server` in root `package.json` (2.11.0). See [[Script API 2.11.0 Notes]].

## FORMATVER216 / 218 — animation format
- Symptom: animation `1.8.0` below expected; then `1.12.0` above expected.
- Fix: use exactly `1.10.0` for animations ([[Format Versions]]).

## FORMATVER300 / ENTITYTYPE120 — entity format
- Symptom: entity `1.21.40` lower than expected.
- Fix: use `1.26.60` for behavior and client entities ([[Format Versions]]).

## PRJINT101 / UNKJSON101 — extraneous files and unknown JSON
- Symptom: Creator Tools flags `scripts/`, `tests/`, `.mcp.json`, `templates/`.
- Cause: repo-level files sit beside the packs.
- Fix: accepted. `npm run mct:validate` excludes `PRJINT` and `UNKJSON`. See `docs/ARCHITECTURE.md`.

## UNLINK399 — template texture link
- Symptom: warning on `templates/resource/client_entity.json`.
- Cause: placeholder path in a template. Accepted.

## Validator bug: pack_icon flagged as unreferenced PNG
- Fixed in `validators/validate-addon.mjs` (skip `pack_icon.png`).

## `node --test tests/` fails on Node 22
- Symptom: "Cannot find module … tests".
- Fix: pass files explicitly (`npm test` does this).

## Sync: obsidian-git on iOS
- Symptom: documented as experimental/unstable on mobile.
- Mitigation: see `docs/OBSIDIAN_SYNC.md`.
