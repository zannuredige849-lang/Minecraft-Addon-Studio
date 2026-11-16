---
type: technical
status: existing
tags:
  - technical
  - testing
updated: 2026-11-16
---

# Validation and Testing

## Small change
Check only the files you touched:
```bash
python3 -m json.tool BP/entities/pixel_slime.json > /dev/null
```

## Release or large change
Check every JSON file and that manifest UUIDs are unique:
```bash
find BP RP -name '*.json' -exec python3 -m json.tool {} \; > /dev/null && echo "JSON ok"
python3 -c "import json; u=[x for f in ('BP/manifest.json','RP/manifest.json') for m in [json.load(open(f))] for x in [m['header']['uuid']]+[d['uuid'] for d in m['modules']]]; print('UUIDs ok' if len(u)==len(set(u)) else 'DUPLICATE UUID')"
```
The second command checks header and module UUIDs only. Dependency entries are meant to repeat another pack's UUID.

## In-game test (not done yet)
1. Copy `BP/` to `development_behavior_packs/` and `RP/` to `development_resource_packs/`.
2. Create a world and enable the behavior pack (the resource pack follows).
3. `/summon studio:pixel_slime`. Check the model, the texture, hopping and that it attacks you.
4. Record the result in [[Changelog]].

## Vault
After editing notes, check that every `[[link]]` resolves. Obsidian shows broken links in a lighter colour.


---
Back to [[Home]] · [[Dashboard]]
