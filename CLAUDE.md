# Minecraft-Addon-Studio — working rules

Project: Minecraft Bedrock add-ons. `BP/` = behavior pack, `RP/` = resource pack.
Developed from an iPhone via Claude Code Cloud, so keep work small and fast.

## Model and effort
- Simple edits, JSON fixes, renames: Haiku, low effort.
- Normal Minecraft development (entities, components, textures, lang): Sonnet, medium effort.
- Opus only for hard architecture or debugging that Sonnet has failed on.

## Work style
- One subagent at a time. No parallel agents unless the user asks.
- Do not scan the whole repo for small edits. Read only the files named in the task.
- Do not re-read files already in context. Do not repeat research.
- Ask before installing plugins, connectors, or MCP servers.
- Never commit to `main`. Work on the branch named in the session.

## Validation
- Small change: validate only the files touched.
  - JSON: `python3 -m json.tool <file> > /dev/null`
- Release build or large change: validate every `.json` under `BP/` and `RP/`, and check that every manifest UUID is unique.
- Do not run long test or build steps for a one-line change.

## Conventions
- Entity identifiers use the `namespace:name` form, e.g. `studio:pixel_slime`.
- Keep `format_version` values consistent with the engine version in each manifest.
- Keep manifest UUIDs stable once published. Generate new ones only for new packs.

## Documentation (Obsidian vault)
- Docs live in `obsidian/`. When BP/RP change, update the matching note (entity note, Balance, Dashboard, Changelog).
- Mark anything not built as `planned`. Never document features that are not in the repo.
- Keep `[[wikilinks]]` valid and note names unique.

## Git
- Commit messages: short imperative summary, then body if needed.
- Push only to the session's designated branch.
