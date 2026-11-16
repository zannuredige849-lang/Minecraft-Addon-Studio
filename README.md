# Minecraft-Addon-Studio

An AI studio for building professional **Minecraft Bedrock Add-ons**: entity models, pixel-art textures, rigs, animations, Script API code, Behavior and Resource Packs, validation, and `.mcaddon` packaging.

Built to be driven from an iPhone through Claude Code on the web and GitHub.

## Quick start

```bash
npm run validate    # check every pack (JSON, UUIDs, UVs, references, Molang, scripts, PNGs)
npm test            # run the test suites
npm run build       # validate, then write dist/studio_demo.mcaddon
npm run mct:validate  # Creator Tools' own validation (needs the installed mct 0.21.0)
```

## What's inside

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Project rules, modes, workflow, definition of done |
| `agents/` | Seven agents: Project Manager, Minecraft Architect, Model Artist, Texture Artist, Animation Specialist, Script Developer, QA Engineer |
| `skills/` | How-to guides: pack structure, geometry/UV, animation/Molang, Script API, pixel art, QA/packaging, add-on analysis |
| `templates/` | Starter files with placeholders (`__NEW_UUID__`, `__NAMESPACE__`, `__NAME__`) |
| `behavior_packs/studio_demo_bp` | Sample Behavior Pack: pixel slime entity, join message script |
| `resource_packs/studio_demo_rp` | Sample Resource Pack: slime model, 16×16 pixel texture, idle animation, render controller, language file |
| `validators/validate-addon.mjs` | Zero-dependency validator (exit 1 on errors) |
| `tests/` | `node:test` suites: validator rules with broken fixtures, packaging, templates, MCP config |
| `scripts/` | `build-mcaddon.mjs` (validate → package), `generate_sample_texture.py` |
| `docs/` | Architecture, quality gates, MCP setup, iPhone workflow, teaching mode, manual actions, studio report |
| `studio/config/studio.json` | Mode (`development` by default), namespace, format versions |
| `.mcp.json` | Minecraft Creator Tools MCP server (`mct mcp`) |

## Modes

- **DEVELOPMENT** (default): short answers, change → validate → report.
- **TEACHING**: ask for it ("teaching mode"). Explains architecture, code and decisions. See `docs/TEACHING_MODE.md`.

## Important

- Targets current Bedrock and `@minecraft/server` 2.11.0. Verify new API members against the official docs.
- The Minecraft EULA and any store or account terms must be accepted by you, not by the studio.
- Generated `.mcaddon` files are for testing. Check them in Minecraft before sharing.

See `docs/IPHONE_WORKFLOW.md` for the phone-only process and `docs/MANUAL_ACTIONS.md` for steps only you can do.
