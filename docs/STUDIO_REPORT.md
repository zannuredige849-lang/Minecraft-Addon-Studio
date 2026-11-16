# Studio report — studio-foundation build

Branch: `feature/studio-foundation` (created from `claude/lucid-planck-c7i3ac`). Nothing was pushed to `main`.

## 1. Created components

| Area | Files |
|---|---|
| Instructions | `CLAUDE.md`, `README.md` |
| Agents (7) | `agents/project-manager.md`, `minecraft-architect.md`, `model-artist.md`, `texture-artist.md`, `animation-specialist.md`, `script-developer.md`, `qa-engineer.md` |
| Skills (7) | `skills/bedrock-pack-structure`, `bedrock-geometry-uv`, `bedrock-animation-molang`, `bedrock-script-api`, `pixel-art-textures`, `addon-qa-packaging`, `addon-analysis` |
| Templates | `templates/` — manifests (BP/RP), behavior entity, client entity, geometry, animation, render controller, script; `templates/README.md` |
| Sample BP | `behavior_packs/studio_demo_bp/` — manifest, `entities/pixel_slime.json`, `scripts/main.js`, `pack_icon.png` |
| Sample RP | `resource_packs/studio_demo_rp/` — manifest, `entity/pixel_slime.entity.json`, `models/entity/pixel_slime.geo.json`, `textures/entity/pixel_slime.png` (16×16 RGBA), `animations/pixel_slime.animation.json`, `render_controllers/…`, `texts/en_US.lang`, `texts/languages.json`, `pack_icon.png` |
| Validator | `validators/validate-addon.mjs` (zero dependencies; also exports `validateProject`, `readPng`) |
| Tests | `tests/validator.test.mjs` (21 tests), `tests/build.test.mjs` (2 tests), `tests/templates-config.test.mjs` (4 tests) |
| Packaging | `scripts/build-mcaddon.mjs` (validates, then zips), `scripts/generate_sample_texture.py` |
| Config | `.mcp.json`, `studio/config/studio.json`, `package.json` |
| Docs | `docs/ARCHITECTURE.md`, `QUALITY_GATES.md`, `MCP_SETUP.md`, `IPHONE_WORKFLOW.md`, `TEACHING_MODE.md`, `MANUAL_ACTIONS.md`, `STUDIO_REPORT.md` |

Modes: DEVELOPMENT is the default (`studio/config/studio.json`). TEACHING is switched on by request, as described in `CLAUDE.md` and `docs/TEACHING_MODE.md`.

## 2. Working tools

| Tool | Result |
|---|---|
| Node.js | v22.23.4 (meets the 22+ requirement) |
| `npm run validate` | **0 errors, 0 warnings** |
| `npm test` | **27 / 27 passing** (21 validator, 2 build, 4 templates/config) |
| `npm run build` | Passes; produces `dist/studio_demo.mcaddon` (git-ignored) with `studio_demo_bp/` and `studio_demo_rp/` |
| `mct validate main PRJINT,UNKJSON` (Creator Tools 0.21.0) | **Exit 0, no errors.** One warning on the template (see §4) |
| `mct mcp` handshake | **Works.** `serverInfo` = `minecraft` 1.0.0; 22 tools listed |

No packages were installed or reinstalled. `@minecraft/creator-tools` 0.21.0 was used as already installed globally.

## 3. Test results

- Validator tests (21): sample passes; each rule fails on a broken fixture. Covered: invalid JSON, duplicate and malformed UUIDs, box-UV out of bounds, PNG size mismatch, missing texture, animation bone not in any geometry, `animation_length` vs last keyframe, unbalanced Molang, BP entity without RP entity, forbidden `eval`, unapproved import, script syntax error, missing script entry, unknown geometry/animation reference, render-controller key mismatch; plus helper unit tests for UV and Molang.
- Build tests: the `.mcaddon` lists both packs and their files, excludes `node_modules`; an invalid project is refused and nothing is written.
- Template/config tests: templates parse, carry no concrete UUIDs, the config has the required keys, and `.mcp.json` registers `mct mcp`.

## 4. Findings during the build (and how they were resolved)

| Finding (source) | Resolution |
|---|---|
| Missing `pack_icon.png` in both packs (CPACKICON101) | Generated 128×128 nearest-neighbour icons |
| `@minecraft/server` not registered in package.json (SCRIPTMODULE110) | Added `"@minecraft/server": "2.11.0"` to `devDependencies` (declared only; not installed) |
| Entity format `1.21.40` below expected (ENTITYTYPE120, FORMATVER300) | Set BP and RP entity to `1.26.60` |
| Animation format `1.8.0` below expected (FORMATVER216) | Set to `1.10.0`; the next check wanted exactly `1.10.0` (FORMATVER218) |
| Scripts/tests/config flagged as extraneous (PRJINT101) and unknown JSON (UNKJSON101) | Accepted and excluded in `npm run mct:validate`. These are repo-level files, not pack content. Documented in `docs/ARCHITECTURE.md` |
| Texture link not found in template (UNLINK399) | Accepted. Placeholder path in a template, which is not a pack |
| Non-lowercase file names (PATHLENGTH104) | Accepted. Conventional names (`CLAUDE.md`, `README.md`, `SKILL.md`); recommendation only |
| Validator bug: `pack_icon.png` flagged as unreferenced texture | Fixed in `validators/validate-addon.mjs` |
| Validator bug: keyframe-order check was convoluted | Replaced with a strict ascending check |
| `node --test tests/` fails on Node 22 (directory argument) | `npm test` lists the test files explicitly |

## 5. Known issues and blocked items

- **`.claude/settings.json` was NOT created.** The write was denied by the auto-mode permission classifier. The reason given was that a change to Claude's own permission settings falls under "undermining oversight". I did not work around the denial. Consequence: no project-level allow or deny list exists yet. The Git and build commands still run through the normal permission prompts. If you want that file, approve it explicitly.
- **MCP session loading:** the handshake succeeds from the shell, but the current session loaded its MCP servers before `.mcp.json` existed. You may need to start a new session on this branch and approve the project MCP server. Until then the `minecraft-creator-tools` tools may not appear in this session.
- **In-game behavior is not verified.** Creator Tools' validation passes, but nothing has been loaded in Minecraft Bedrock. Format versions were chosen from Creator Tools' own validator, which does not guarantee the game accepts them.
- **`min_engine_version` `[1, 21, 40]` is unverified** against the Minecraft version you will test on.
- **Script API 2.11.0** is the version Creator Tools references. Member-level API use has not been checked against the official reference.
- **The Minecraft EULA was not accepted** and must be accepted by you.
- **Commit attribution:** the session instructions ask for a `Co-Authored-By` line naming the model. The system rules forbid model identifiers in commit messages. I followed the system rule and left the model name out.
- **The sample pixel slime has not been visually reviewed** in Minecraft. The texture validator checks dimensions, alpha and palette count only.

## 6. Manual actions (you)

1. Accept the Minecraft EULA and any store terms yourself.
2. Install and open Minecraft Bedrock on the iPhone.
3. Review the branch on GitHub and open/merge a PR yourself, if you want one. Nothing was merged to `main`.
4. Approve the project MCP server when Claude Code asks (new session).
5. Decide whether to approve `.claude/settings.json`.
6. Test `studio_demo.mcaddon` in Minecraft and report back what you see.

## 7. Using the studio from iPhone

1. Open Claude Code on the web and select the repository, branch `feature/studio-foundation`.
2. Describe the change in plain words. The studio plans it, creates the files, runs `npm run validate` and `npm test`, then reports.
3. Ask for `npm run build`. Download `dist/studio_demo.mcaddon` from the session.
4. Save it to Files on the iPhone and open it. Minecraft imports it.
5. In a creative world, enable the Behavior and Resource Packs, then `/summon studio:pixel_slime`.
6. For a walkthrough of every decision, say "teaching mode".

## 8. Suggested next steps

1. Approve `.claude/settings.json` and a new session so MCP loads.
2. Test the sample in Minecraft; report the result.
3. Add the first real entity from the templates, then the first texture from the pixel-art skill.
