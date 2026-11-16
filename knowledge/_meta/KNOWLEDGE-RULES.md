# Knowledge base rules (for Claude and humans)

Applies to everything under `knowledge/`. Read this before writing a note.

## Reading
1. Start at [[Home]]. Open the category index for the task (e.g. [[Models & Geometry/Index|Models & Geometry]]).
2. Before creating a mob, boss, model, animation or script, search for an existing note with `grep -ril` in `knowledge/` and extend it instead of duplicating.
3. Read [[Common Errors]] before debugging a validator or `mct` failure.

## Writing
- One topic per note. File names are human-readable (`Pixel Slime.md`); wiki links use the file name without `.md`, so names must be unique across the vault.
- Use the templates in `_templates/`. Fill the frontmatter fields; leave none empty without writing `unknown`.
- Frontmatter status values: `draft`, `verified` (checked in a validator, `mct`, or Minecraft), `unverified` (from memory or a guess).
- Facts about Minecraft versions, format versions, or Script API members must say how they were checked. If unchecked, mark `status: unverified` and put the source or "needs check" in the note.
- Every note links to at least one index and one related note. Related notes link both ways.
- Never record secrets: no tokens, passwords, API keys, personal data, or account details. Do not paste the contents of `.mcp.json` credentials or device settings.
- Do not copy copyrighted Minecraft assets or other add-ons' files into the vault. Describe structure and patterns in your own words.

## Updating after work
- Add a dated entry to `Development Journal/` for each session that changes the repo: what changed, what was verified, what was not.
- A failed check goes into `Errors & Solutions/` with: symptom, cause, fix, and the commit or file that fixed it.
- Mark superseded facts instead of deleting them: change the status and add a link to the replacement.
- Never delete or move existing notes without the user asking. Renames must update every link (the Obsidian setting `alwaysUpdateLinks` helps on the desktop).

## Structure rules
- Do not add files outside `knowledge/` for knowledge content.
- `_templates/` and `_meta/` hold templates and rules only; they are not content.
- `.obsidian/` holds only shared settings. Per-device files (`workspace*.json`, plugin data) are git-ignored.

## Checks
- `npm test` runs `tests/knowledge.test.mjs`: every wiki link must resolve to a note, the Home note must link every category index, and no secret-like string may appear in `knowledge/`.
