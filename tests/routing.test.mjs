// Routing configuration checks: subagent files use supported frontmatter and model aliases,
// each wrapper points to a real role file, and the routing policy note exists with its sections.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const agentsDir = path.join(repo, ".claude", "agents");
const MODELS = new Set(["haiku", "sonnet", "opus"]);
const ALLOWED_KEYS = new Set(["name", "description", "model"]); // only fields we rely on

function frontmatter(file) {
  const text = fs.readFileSync(file, "utf8");
  const m = text.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  assert.ok(m, `${path.basename(file)} has no frontmatter`);
  const fields = {};
  for (const line of m[1].split("\n")) {
    const kv = line.match(/^([a-z_]+):\s*(.*)$/);
    assert.ok(kv, `${path.basename(file)}: unsupported frontmatter line "${line}"`);
    fields[kv[1]] = kv[2].trim();
  }
  return { fields, body: m[2] };
}

const files = fs.readdirSync(agentsDir).filter((f) => f.endsWith(".md"));

test("seven subagent wrappers exist", () => {
  assert.equal(files.length, 7);
});

for (const f of files) {
  test(`${f}: valid frontmatter, alias model, real role file`, () => {
    const { fields, body } = frontmatter(path.join(agentsDir, f));
    const name = f.replace(/\.md$/, "");
    assert.equal(fields.name, name, "name must match filename");
    assert.ok(fields.description && fields.description.length > 20, "description required");
    assert.ok(MODELS.has(fields.model), `model must be haiku, sonnet or opus, got "${fields.model}"`);
    for (const k of Object.keys(fields)) assert.ok(ALLOWED_KEYS.has(k), `unexpected frontmatter key "${k}"`);
    const role = body.match(/`agents\/([a-z-]+\.md)`/);
    assert.ok(role, "wrapper must reference its role file under agents/");
    assert.ok(fs.existsSync(path.join(repo, "agents", role[1])), `role file ${role[1]} missing`);
  });
}

test("Project Manager and QA default to haiku, all others to sonnet", () => {
  const expect = { "project-manager": "haiku", "qa-engineer": "haiku" };
  for (const f of files) {
    const name = f.replace(/\.md$/, "");
    const { fields } = frontmatter(path.join(agentsDir, f));
    assert.equal(fields.model, expect[name] ?? "sonnet", name);
  }
});

test("routing policy note exists with required sections", () => {
  const note = fs.readFileSync(path.join(repo, "knowledge", "AI Model Routing.md"), "utf8");
  for (const h of ["Two separate decisions", "Routing diagram", "Default model per agent", "Escalation rules", "Promotion and demotion", "Examples for each level", "Handoff report format"]) {
    assert.ok(note.includes(h), `missing section: ${h}`);
  }
});

test("CLAUDE.md states the routing rules", () => {
  const claude = fs.readFileSync(path.join(repo, "CLAUDE.md"), "utf8");
  assert.ok(claude.includes("## Model routing"));
  assert.ok(claude.includes("knowledge/AI Model Routing.md"));
});
