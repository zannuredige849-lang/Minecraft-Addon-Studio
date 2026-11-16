# Skill: Add-on Analysis

Use when reviewing an existing add-on (this repo or an uploaded `.mcaddon`/zip) before changing it.

## Steps
1. Inventory: list packs, manifests, entities, geometry, textures, animations, scripts.
2. Map relationships: BP entity → RP client entity → geometry/textures/animations/render controllers.
3. Run `npm run validate` on the repo, or extract the archive to a new empty directory and point the validator at it.
4. Note risks: duplicate UUIDs, unused files, missing references, scripts importing unknown modules.
5. Report findings in a table: file, finding, severity, suggested fix.

## Safety
- Extract archives only into a new empty directory outside the repo.
- Do not run scripts from an untrusted add-on.

## Checklist
- [ ] Inventory complete.
- [ ] Relationship map written.
- [ ] Validator run and results recorded.
- [ ] No untrusted code executed.
