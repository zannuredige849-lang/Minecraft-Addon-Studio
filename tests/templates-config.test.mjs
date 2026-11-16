// Templates and configuration: every template parses, carries placeholders (never real UUIDs),
// and the studio config and MCP config are well formed.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const walk = (dir) =>
  fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)],
  );
const UUID_RE = /[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i;

test("every template JSON parses", () => {
  const files = walk(path.join(repo, "templates")).filter((f) => f.endsWith(".json"));
  assert.ok(files.length >= 6, "expected at least 6 JSON templates");
  for (const f of files) assert.doesNotThrow(() => JSON.parse(fs.readFileSync(f, "utf8")), path.relative(repo, f));
});

test("templates contain no real UUIDs (placeholders only)", () => {
  for (const f of walk(path.join(repo, "templates")).filter((x) => x.endsWith(".json"))) {
    assert.equal(UUID_RE.test(fs.readFileSync(f, "utf8")), false, `${path.relative(repo, f)} contains a concrete UUID`);
  }
});

test("studio config declares mode, namespace and format versions", () => {
  const cfg = JSON.parse(fs.readFileSync(path.join(repo, "studio/config/studio.json"), "utf8"));
  assert.ok(["development", "teaching"].includes(cfg.mode));
  assert.equal(cfg.namespace, "studio");
  assert.equal(cfg.versions.creatorTools, "0.21.0");
  assert.equal(cfg.versions.minecraftServerScript, "2.11.0");
  for (const k of ["entity", "geometry", "animation", "renderController"]) {
    assert.ok(cfg.versions.formats[k], `missing format version for ${k}`);
  }
});

test("MCP config registers the Creator Tools server via mct mcp", () => {
  const mcp = JSON.parse(fs.readFileSync(path.join(repo, ".mcp.json"), "utf8"));
  const server = mcp.mcpServers["minecraft-creator-tools"];
  assert.ok(server, "minecraft-creator-tools server missing");
  assert.equal(server.command, "mct");
  assert.deepEqual(server.args.slice(0, 1), ["mcp"]);
});
