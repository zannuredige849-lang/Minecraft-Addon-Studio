---
type: process
status: verified
---
# Add-on analysis method

1. Extract the file into a new, empty folder **outside** the repo. Never run its scripts.
2. Inventory files by type (see the `addon-analysis` skill in the repo).
3. Map relationships: BP entity → RP client entity → geometry, textures, animations.
4. Run `npm run validate` on a copy of the structure if useful.
5. Record patterns and problems in an analysis note; link [[Common Errors]] for any failure.
