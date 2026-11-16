---
type: process
status: verified
updated: 2026-11-16
---
# AI model routing

Home: [[Home]] · Rules: [[KNOWLEDGE-RULES]] · Efficiency: `docs/PROMPT_EFFICIENCY.md` · Agents: `agents/` and `.claude/agents/`

## 1. Two separate decisions

| Decision | Where it is set | Verified? |
|---|---|---|
| **Main session model** (the model you talk to) | `/model` in the session, or `--model` at launch | Set by you. Delegating to subagents does **not** change it |
| **Subagent model** (a delegated task) | `model:` in `.claude/agents/<name>.md` (default), or the `model` parameter on each Agent call (override) | Frontmatter and the Agent `model` enum (`sonnet`, `opus`, `haiku`) confirmed in the tool schema. Runtime behaviour not yet exercised |

Subagents draw from the same Claude Pro usage limit as the main session. A cheaper model saves limit; it does not create a separate budget.

Model IDs in this environment: `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`. Use aliases (`haiku`, `sonnet`, `opus`) in agent files and calls.

## 2. Assess every task before routing

| Factor | Low | Medium | High |
|---|---|---|---|
| Complexity | rename, typo, format, run a command | one feature in one pack | cross-pack design, subtle bug, new mechanic |
| Risk | no effect on packs | changes entity or script behaviour | UUIDs, dependencies, format versions, release |
| Files affected | 1 | 2–5 | many, or unknown |
| Analysis depth | read one file | read 2–3 files and a note | must reason across the whole add-on |

Rule: use the **cheapest model that meets every factor**. Any single "high" in risk or depth raises the level.

## 3. Routing diagram

```
                     task arrives
                          │
              ┌───────────┴────────────┐
       simple & repetitive?        complex / risky / deep?
              │                         │
           HAIKU  ──fails──►  SONNET ──fails twice──► OPUS
        (simple, local)     (primary dev)           (architecture,
                                                     hard bugs)
  Escalate only after a failure with NO new information or context fix.
  Hand over: brief report + affected files + check output. Not the chat history.
```

## 4. Default model per agent

| Agent | Default (frontmatter) | Haiku for | Sonnet for | Opus for |
|---|---|---|---|---|
| Project Manager | **haiku** | status, hand-offs, task lists | multi-pack planning | (rarely) cross-cutting plan with risk |
| Minecraft Architect | sonnet | notes, small manifest edits | structure, UUIDs, deps | complex architecture decisions |
| Model Artist | sonnet | rename bone, fix one size | new geometry, UV layout | (no) |
| Texture Artist | sonnet | resize check, palette count | new texture, shading | (no) |
| Animation Specialist | sonnet | fix a keyframe time | new animation, render controller | complex multi-bone Molang that failed twice |
| Script Developer | sonnet | typo, import, log text | new handler, logic | complex logic, repeated failure |
| QA Engineer | **haiku** | run checks, summarise output | failure analysis | critical release case only |

To use a different model for one call, pass `model` to the Agent tool (`haiku`, `sonnet` or `opus`). The frontmatter default is used when no override is given.

## 5. Escalation rules

1. **Start at the cheapest allowed level** for the task (table above).
2. **First failure:** fix the context before escalating. Add the missing file, the exact error, or the knowledge note. Re-run on the same model.
3. **Still failing with full context:** escalate one level (Haiku → Sonnet → Opus). Never skip a level.
4. **Each escalation** carries only: the brief report, the affected file paths, and the check output tail (last ~40 lines).
5. **Stop** after Opus fails once. Report to the user with what was tried; do not loop.

## 6. Promotion and demotion criteria

Promote a task **up** one level when any is true:
- The same task failed on the current model twice with full context.
- Risk is high (UUIDs, format versions, dependencies, a release build).
- The change needs reasoning across three or more packs or files, with interacting rules.
- A bug has no clear cause after one focused investigation.

Demote a task **down** when:
- It is a repeated, mechanical change (same edit in many files, rename, format fix).
- The output is a checklist or a short report from known facts.
- The change is covered by an existing template or skill and only needs filling in.

Do **not** promote for: missing information (ask or read the note), a typo, or a style preference.

## 7. Examples for each level

**Haiku**
- "Rename bone `leg_l` to `leg_left` in `pixel_slime.geo.json` and the animation." (1–2 files, mechanical)
- "Run `npm run validate` and `npm test`; summarise failing rule codes." (QA initial check)
- "Add a dated entry to `Development Journal` from this session's report." (note writing)

**Sonnet**
- "Add a new mob with geometry, 16×16 texture and an idle animation, following the templates." (several files, one feature)
- "Fix the `CPACKICON101` error on the new pack." (diagnose and fix one error)
- "Write a `@minecraft/server` handler that counts player spawns." (logic, one file)

**Opus**
- "Design how two packs share a custom entity family without breaking UUIDs or dependency order." (architecture, high risk)
- "A boss animation loops incorrectly only in phase 2; the bone transforms look right in the file." (hard bug after Sonnet failed twice)
- "Review a release candidate's validator and build output for hidden risks before publishing." (critical case)

## 8. Handoff report format (keep it short)

```
TASK: <one line>
MODEL: <haiku|sonnet|opus>, attempt <n>
FILES: <paths only>
CHECKS: <command → pass/fail, last ~40 lines on fail>
CONTEXT ADDED: <what new info was supplied, or "none">
NEXT: <one line>
```

## 9. Efficiency rules tied to routing

- One agent per task. Do not run several agents on one simple task.
- Parallelise only independent tasks (different files, no shared outputs). Never run all agents at once.
- Don't re-run the full validator, tests, and build after every minor edit. Batch edits, then check once.
- Don't reread the whole repository. Open the note and the files the task names.
- Save verified answers to `knowledge/` so the next task reads a note instead of re-deriving it.

## 10. Verification status

- Frontmatter `model:` and per-call `model` override: confirmed in this environment's tool schema.
- Actual model served by each subagent at runtime: **not yet measured**. Measure with one low-cost test call before relying on savings (see `docs/PROMPT_EFFICIENCY.md`).
