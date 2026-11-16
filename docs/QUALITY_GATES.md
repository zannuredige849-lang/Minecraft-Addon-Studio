# Quality gates

A change is "done" only when every applicable gate passes or is explicitly reported as not run.

| Gate | Command | Blocks build? | What it checks |
|---|---|---|---|
| Validator | `npm run validate` | Errors yes, warnings no | JSON syntax, manifests and UUIDs, dependencies, entity/geometry/texture/animation/render-controller references, box UV bounds, PNG size and alpha, Molang balance, script imports, forbidden APIs, script syntax, language keys |
| Tests | `npm test` | yes | Validator rules with broken fixtures; packaging; templates; MCP config |
| Build | `npm run build` | yes | Validates first; zip contains both packs; no `node_modules` |
| Creator Tools | `npm run mct:validate` | recorded | Creator Tools' checks (format versions, pack icons, script module registration, texture links) |
| MCP handshake | see `docs/MCP_SETUP.md` | recorded | `mct mcp` answers `initialize` and `tools/list` |
| Visual check | human review | recorded | Silhouette and texture readability in Minecraft |

## Rules for the QA Engineer
- Never weaken a rule to pass a pack. Fix the content.
- Every new rule needs a test that fails without it.
- Report skipped checks as "not run" with the reason.

## Known findings accepted
- `PATHLENGTH104` recommendations about non-lowercase names (`CLAUDE.md`, `README.md`, `SKILL.md`): conventional names, recommendation only.
- `UNLINK399` on `templates/resource/client_entity.json`: placeholder texture path in a template.
- `PRJINT101` / `UNKJSON101`: excluded via `npm run mct:validate` (see ARCHITECTURE.md).
