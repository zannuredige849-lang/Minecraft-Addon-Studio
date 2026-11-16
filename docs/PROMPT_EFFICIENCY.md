# Prompt efficiency and context caching policy

Goal: less repeated context, fewer agent calls, fewer escalations, same development quality.

## Policy

1. **Stable instructions live in files that rarely change.** Project rules: `CLAUDE.md`. Specialist rules: `agents/*.md` and `.claude/agents/*.md`. Routing: `knowledge/AI Model Routing.md`.
2. **Dynamic details stay out of stable files.** Task specifics go in the task message or a short handoff report, not into `CLAUDE.md`.
3. **Do not inject whole documentation files into every task.** Link to the note; load the section needed.
4. **Load only relevant knowledge and source files.** Start at the category index in `knowledge/`, then open the named files.
5. **Reuse verified summaries.** A note with `status: verified` is read instead of re-researched. Re-verify only if its source changed.
6. **No trivial agents or sessions.** A typo fix is a direct edit, not a subagent.
7. **One focused task per agent call.** Use parallel agents only for independent work with separate files and outputs.
8. **Do not assume prompt-cache hits.** Identical `CLAUDE.md` content does not guarantee cache reads in Claude Code Cloud. Nothing in this studio depends on cache hits.
9. **No custom API harness and no API billing** without explicit user approval. This studio runs on the Claude Pro workflow only.
10. **If an API-based execution layer is ever proposed**, evaluate Anthropic Prompt Caching first: a stable system prefix, identical tool definitions, explicit cache breakpoints, and the default five-minute TTL. Keep the Claude Pro workflow separate from any API workflow.
11. **Measure before claiming savings.** Track actual cache reads, cache writes, token usage and cost. Until measured, savings are estimates only.
12. **Keep the two workflows separate.** Claude Pro (interactive, this repo) and any API workflow (future, not approved) do not share config or cost assumptions.

## What to measure (once, cheaply)

| Measure | How | Recorded in |
|---|---|---|
| Model actually served by a subagent | one low-cost test delegation, check the transcript model field | `knowledge/AI Model Routing.md` §10 |
| Context size of a typical task | count the files the task opened | Development Journal |
| Escalations per week | count handoff reports with `attempt > 1` | Development Journal |
| Cache behaviour | only if an API workflow is approved | not applicable now |

Do not spend limit on measurement beyond one test call.

## Anti-patterns

- Re-running the full validator, tests and build after every line edit.
- Opus reviewing every file.
- Repeating a full project review after a minor change.
- Several agents researching the same question.
- Pasting the whole chat history into a subagent.
