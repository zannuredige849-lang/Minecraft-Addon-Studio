# Skill: Add-on QA, Validation, and Packaging

Use before any add-on is called finished or packaged.

## Run order
1. `npm run validate` — zero errors required.
2. `npm test` — all suites pass.
3. `npm run build` — validates again, then writes `dist/<pack>.mcaddon`.
4. Optional: `npm run mct:validate` (Creator Tools). Record result.

## What the validator checks
- JSON parses in every pack file.
- Manifest format, UUID format, unique UUIDs, dependency targets exist.
- BP entity identifiers have matching RP client entities.
- RP entity textures, geometry, animations, and render controllers exist.
- Geometry: parent chains, positive sizes, box UV bounds.
- PNG dimensions equal geometry texture size; alpha is binary (warning otherwise).
- Animations: bones exist, `animation_length` matches last keyframe, Molang balanced.
- Script module entry exists, dependency declared, forbidden patterns absent.

## Packaging
- `.mcaddon` is a zip containing one folder per pack (`<pack>_bp/`, `<pack>_rp/`).
- The build never packages a project that fails validation.
- Output goes to `dist/` (git-ignored). Copy to the iPhone from the artifact or download link.

## Checklist
- [ ] Validator: 0 errors.
- [ ] Tests: all pass.
- [ ] Build: `.mcaddon` created and listed.
- [ ] Report written with results and manual steps.
