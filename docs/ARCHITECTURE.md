# Architecture

## Layers
1. **Instructions**: `CLAUDE.md` (rules, modes, workflow), `agents/` (roles and quality criteria), `skills/` (how-to guides).
2. **Templates**: `templates/` holds starting points with placeholders. They are never validated as packs.
3. **Content**: `behavior_packs/<pack>_bp` and `resource_packs/<pack>_rp`, using official Bedrock folder names.
4. **Quality gates**: `validators/validate-addon.mjs` (zero-dependency) and `mct validate` (Creator Tools 0.21.0).
5. **Packaging**: `scripts/build-mcaddon.mjs` validates first, then zips both packs into `dist/<packName>.mcaddon`.

## Cross-file relationships checked
| From | To | Rule |
|---|---|---|
| BP entity identifier | RP client entity identifier | must match |
| RP client entity `geometry` | `models/**/*.geo.json` `description.identifier` | must exist |
| RP client entity `textures` | `textures/**/*.png` | file must exist; size must equal geometry texture size |
| RP client entity `animations` / `scripts.animate` | `animations/*.animation.json` | must exist |
| RP client entity `render_controllers` | `render_controllers/*.json` | must exist; `Geometry.x`, `Material.x`, `Texture.x` keys must exist in the entity |
| Animation `bones` | any geometry bone | must exist |
| Geometry `parent` | bone `name` in same geometry | must exist |
| Manifest `dependencies.uuid` | a header UUID in the project | must exist |
| Script import | BP manifest dependency | `@minecraft/server` must be declared |
| Script module `entry` | file | must exist |

## Versions (see `studio/config/studio.json`)
| Item | Value | Why |
|---|---|---|
| Manifest `format_version` | 2 | Standard for current packs |
| BP / RP entity `format_version` | 1.26.60 | `mct validate` expects this for entity resources (FORMATVER300) and a minor ≥ 26 for BP entities (ENTITYTYPE120) |
| Animation `format_version` | 1.10.0 | `mct validate` expects exactly this (FORMATVER216/218) |
| Geometry `format_version` | 1.12.0 | Standard geometry format |
| Render controller `format_version` | 1.8.0 | Standard |
| `@minecraft/server` | 2.11.0 | Version Creator Tools 0.21.0 references |
| `min_engine_version` | [1, 21, 40] | **Unverified**: confirm against the Bedrock version you test on |

## Decisions and tradeoffs
- The validator has no npm dependencies so it runs on a phone-only workflow without `npm install`.
- Creator Tools is referenced, not vendored. It is already installed globally at 0.21.0 and is not reinstalled.
- The project's own scripts and tests sit beside the packs. Creator Tools reports them as "extraneous" (PRJINT101), so `npm run mct:validate` excludes the PRJINT and UNKJSON checks. Those checks are about the pack layout, which the studio's own validator covers.
- Templates are plain `.json` files. Creator Tools flags them as unknown JSON and reports an unlinked texture (UNLINK399). Both are accepted; the templates are documented as non-packs.
- Pixel art limits (16 opaque colours, binary alpha) are warnings, not errors, so an artist can override deliberately.
