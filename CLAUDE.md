# Minecraft-Addon-Studio — Project Instructions

An AI studio for building professional **Minecraft Bedrock Add-ons**: entity models, pixel-art textures, rigs, animations, Script API code, Behavior Packs (BP), Resource Packs (RP), validation, and `.mcaddon` packaging.

Target platform: **current Minecraft Bedrock** (vanilla style, official BP/RP folder structure, `format_version` values as used by Creator Tools 0.21.0 and `@minecraft/server` 2.11.0). Verify against the official Bedrock docs when a value is uncertain and say so.

Work is done **from an iPhone** through Claude Code on the web and GitHub. Keep responses short, use checklists, and never assume the user can run a local terminal.

---

## Modes

| Mode | Default | Behavior |
|---|---|---|
| **DEVELOPMENT** | yes | Concise. Make the change, run validators/tests, report results. Explain only what the user needs to act on. |
| **TEACHING** | on request | Explain architecture, code, every change, and the reasoning behind each decision. Pause at decision points. |

- Current mode is stored in `studio/config/studio.json` (`"mode"`).
- Switch to TEACHING when the user asks ("teaching mode", "explain", "teach me"). Switch back on "development mode".
- In TEACHING mode, follow `docs/TEACHING_MODE.md`.

---

## Agents (see `agents/`)

| Agent | Owns |
|---|---|
| Project Manager | Scope, plan, task list, status reports, acceptance checks |
| Minecraft Architect | BP/RP structure, UUIDs, dependencies, file relationships, `format_version` decisions |
| Model Artist | `.geo.json` geometry, bones, UV layout, Bedrock model rules |
| Texture Artist | Pixel-art PNGs, palettes, texture size matching geometry |
| Animation Specialist | `.animation.json`, render controllers, Molang |
| Script Developer | `@minecraft/server` scripts, manifests, script module wiring |
| QA Engineer | Validators, tests, `mct validate`, packaging checks |

One agent is active per task; the Project Manager hands off between them. Agent definitions include quality criteria that must pass before work is called done.

---

## Repository layout

```
behavior_packs/<pack>_bp/     Behavior Pack (entities, scripts, animations, items)
resource_packs/<pack>_rp/     Resource Pack (client entities, models, textures, animations, render controllers, texts)
templates/                    Starter JSON/JS/manifest templates — copy, do not edit in place
validators/validate-addon.mjs Project validator (zero dependencies)
tests/                        node:test suites (validator + packaging)
scripts/                      build-mcaddon.mjs (validate → package), texture generator
skills/                       Reusable how-to guides for agents
agents/                       Agent role definitions
docs/                         Architecture, quality gates, MCP setup, iPhone workflow, manual actions
studio/config/studio.json     Studio settings (mode, namespace, versions)
.mcp.json                     Minecraft Creator Tools MCP server (mct mcp)
.claude/settings.json         Claude Code permissions
```

---

## Rules that always apply

1. **Official structure only.** BP: `manifest.json`, `entities/`, `scripts/`, `animations/`, `animation_controllers/`, `items/`, `blocks/`, `recipes/`. RP: `manifest.json`, `entity/`, `models/entity/`, `textures/entity/`, `animations/`, `render_controllers/`, `texts/`, `textures/texture_list.json` if textures are listed as items.
2. **Namespaces.** All identifiers use the studio namespace from `studio/config/studio.json` (`studio:`). Never use `minecraft:` for custom content.
3. **UUIDs.** Every header and module UUID is a fresh v4 UUID, unique across the project. Never reuse template UUIDs in a real pack. Never change a published pack's UUID.
4. **Versions.** `format_version` values come from `templates/` and `studio/config/studio.json`. Do not bump versions without a reason written in the commit.
5. **Pixel art.** Textures are PNG, RGBA, power-of-two-friendly sizes (16, 32, 64), hard alpha only (0 or 255), no anti-aliasing, limited palettes. Texture size must match `texture_width`/`texture_height` in the geometry.
6. **Geometry.** Bedrock units: 1 block = 16 model units. Every bone has a valid `parent` chain to a root. Box UVs must fit inside the texture.
7. **Molang.** Use `query.`, `variable.`, `math.`, `q.`, `v.`, `t.` correctly. Balance parentheses. Never invent functions; check against the official Molang reference.
8. **Script API.** Import only from `@minecraft/server` (and `@minecraft/server-ui` if used). The BP manifest must declare the dependency and the script module. Keep scripts deterministic and free of `eval`, network calls, or secrets.
9. **Never mark work done without a passing check.** Run `npm test` and `npm run validate`. If a check cannot run, say so explicitly in the report.
10. **Never overwrite unverified work.** Read a file before editing it. Do not delete files unless the user asks.
11. **Git.** Work on `feature/*` branches only. Never push to `main`. Never change GitHub settings. Commit messages describe the change; no model names in commits or PR text.
12. **Secrets.** Never print tokens, keys, passwords, or `.env` contents. Do not store them in the repo.
13. **EULA.** Never accept the Minecraft EULA or any terms on the user's behalf. Ask the user to do it.
14. **No paid services.** Do not create accounts, subscriptions, or purchases.

---

## Standard workflow

1. **Plan** (Project Manager): state the goal, the files to touch, and the acceptance checks.
2. **Design** (Architect): decide identifiers, UUIDs, relationships.
3. **Create** (Model / Texture / Animation / Script artist): use templates, respect the skills.
4. **Validate** (QA): `npm run validate`, `npm test`, optionally `mct validate`.
5. **Package**: `npm run build` produces `dist/<pack>.mcaddon` after validation passes.
6. **Report**: created files, test results, open issues, manual steps.

---

## Knowledge base (Obsidian)

The vault is the nested folder `knowledge/` (open it in Obsidian). Start at `knowledge/Home.md`.

- **Read first:** before a task, open the matching category index in `knowledge/` and search for an existing note (`grep -ril`). Extend it instead of duplicating.
- **Read before debugging:** `knowledge/Errors & Solutions/Common Errors.md`.
- **Write after work:** add a dated entry to `knowledge/Development Journal/` for each session that changes the repo. Record new validator or tool errors and their fixes in `Errors & Solutions/`.
- **Templates:** `knowledge/_templates/` (mob, boss, model, animation, script, add-on analysis, journal entry).
- **Full rules:** `knowledge/_meta/KNOWLEDGE-RULES.md`. Sync options and the iPhone setup: `docs/OBSIDIAN_SYNC.md`.
- Never put tokens or secrets in `knowledge/`. Never delete or move notes without the user asking.
- `npm test` checks wiki links, category coverage, and secret-like strings.

## Commands

| Command | Purpose |
|---|---|
| `npm run validate` | Validate all packs in the repo (JSON, manifests, UVs, references, Molang, scripts, PNG) |
| `npm test` | Run node:test suites (validator + packaging) |
| `npm run build` | Validate, then package every pack into `dist/*.mcaddon` |
| `npm run mct:validate` | Run Creator Tools `mct validate` on the project (optional, needs `mct`) |
| `npm run texture:sample` | Regenerate the sample pixel texture (needs Python + Pillow) |

## MCP

`.mcp.json` registers the **Minecraft Creator Tools** MCP server (`mct mcp`). The installed `mct` 0.21.0 is used as-is — do not reinstall. See `docs/MCP_SETUP.md` for the connection check and fallback. If MCP is unavailable, log the issue in `docs/STUDIO_REPORT.md` and continue with the zero-dependency validators.

## Definition of done

- Validators pass with zero errors (warnings listed).
- Tests pass.
- Packaging produces a `.mcaddon` that lists the expected folders.
- Report lists what was created, what was verified, what was not, and any manual step.
