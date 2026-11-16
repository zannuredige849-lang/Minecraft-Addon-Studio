// Knowledge base checks: categories exist, every wiki link resolves, Home links every
// category index, and no secret-like strings appear in knowledge or docs.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const kb = path.join(repo, "knowledge");

const CATEGORIES = [
  "Minecraft Bedrock Documentation", "Models & Geometry", "Textures & UVs", "Animations & Molang",
  "Script API", "Behavior Packs", "Resource Packs", "Mob Encyclopedia", "Boss Encyclopedia",
  "Add-on Research", "Errors & Solutions", "Development Journal",
];

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    if (e.name.startsWith(".")) return [];
    const p = path.join(dir, e.name);
    return e.isDirectory() ? walk(p) : [p];
  });
}
// Notes only: skip templates (they contain placeholders on purpose).
const notes = walk(kb).filter((f) => f.endsWith(".md") && !f.includes(`${path.sep}_templates${path.sep}`));
const noteNames = new Set(walk(kb).filter((f) => f.endsWith(".md")).map((f) => path.basename(f, ".md")));
const LINK = /\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]/g;

test("all 12 categories exist as folders with an index note", () => {
  for (const c of CATEGORIES) {
    assert.ok(fs.existsSync(path.join(kb, c, "Index.md")), `missing ${c}/Index.md`);
  }
});

test("every wiki link resolves to an existing note", () => {
  const broken = [];
  for (const f of notes) {
    for (const m of fs.readFileSync(f, "utf8").matchAll(LINK)) {
      const target = path.basename(m[1].trim());
      if (!noteNames.has(target)) broken.push(`${path.relative(kb, f)} -> [[${m[1]}]]`);
    }
  }
  assert.deepEqual(broken, []);
});

test("Home links every category index", () => {
  const home = fs.readFileSync(path.join(kb, "Home.md"), "utf8");
  for (const c of CATEGORIES) assert.ok(home.includes(`[[${c}/Index|`), `Home does not link ${c}`);
});

test("templates exist for mob, boss, model, animation, script, analysis and journal", () => {
  for (const t of ["Mob.md", "Boss.md", "Model.md", "Animation.md", "Script.md", "Add-on Analysis.md", "Journal Entry.md"]) {
    assert.ok(fs.existsSync(path.join(kb, "_templates", t)), `missing template ${t}`);
  }
});

test("no secret-like strings in knowledge, docs, or agent/config files", () => {
  const files = [
    ...walk(kb),
    ...walk(path.join(repo, "docs")),
    path.join(repo, ".mcp.json"),
    path.join(repo, "CLAUDE.md"),
  ].filter((f) => fs.existsSync(f) && fs.statSync(f).isFile());
  const patterns = [
    /ghp_[A-Za-z0-9]{20,}/,
    /github_pat_[A-Za-z0-9_]{20,}/,
    /gho_[A-Za-z0-9]{20,}/,
    /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
    /(password|passwd|api[_-]?key|secret|token)\s*[:=]\s*["']?[A-Za-z0-9_\-]{12,}/i,
  ];
  const hits = [];
  for (const f of files) {
    const text = fs.readFileSync(f, "utf8");
    for (const p of patterns) if (p.test(text)) hits.push(path.relative(repo, f));
  }
  assert.deepEqual(hits, []);
});
