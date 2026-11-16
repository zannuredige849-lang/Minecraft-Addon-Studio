# Templates

Starting points for new content. Copy a template into the matching pack folder, then replace every placeholder:

| Placeholder | Replace with |
|---|---|
| `__NEW_UUID__` | a fresh v4 UUID (one per header and per module; never reuse) |
| `__NAMESPACE__` | the studio namespace (`studio`) from `studio/config/studio.json` |
| `__NAME__` | the entity/pack name in snake_case, e.g. `pixel_slime` |

Templates are not packs and are not validated. The validator only checks files inside `behavior_packs/` and `resource_packs/`, so a template left unedited can only break the build after it is copied there.

Format versions come from `studio/config/studio.json`.
