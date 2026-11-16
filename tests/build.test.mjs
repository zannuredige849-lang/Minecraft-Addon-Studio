// Packaging test: the build must validate, then produce a .mcaddon zip with both pack folders.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const script = path.join(repo, "scripts", "build-mcaddon.mjs");

test("build produces a .mcaddon containing both packs", () => {
  const out = fs.mkdtempSync(path.join(os.tmpdir(), "studio-build-"));
  try {
    execFileSync(process.execPath, [script, "--out", out], { cwd: repo, stdio: "pipe" });
    const file = path.join(out, "studio_demo.mcaddon");
    assert.ok(fs.existsSync(file), "studio_demo.mcaddon not created");
    const listing = execFileSync("unzip", ["-Z1", file], { encoding: "utf8" }).split("\n").filter(Boolean);
    assert.ok(listing.some((p) => p.startsWith("studio_demo_bp/manifest.json")), "BP manifest missing from archive");
    assert.ok(listing.some((p) => p.startsWith("studio_demo_rp/manifest.json")), "RP manifest missing from archive");
    assert.ok(listing.some((p) => p.endsWith("pixel_slime.png")), "texture missing from archive");
    assert.ok(listing.some((p) => p.endsWith("scripts/main.js")), "script missing from archive");
    assert.ok(!listing.some((p) => p.includes("node_modules")), "node_modules leaked into archive");
  } finally {
    fs.rmSync(out, { recursive: true, force: true });
  }
});

test("build refuses to package an invalid project", () => {
  const work = fs.mkdtempSync(path.join(os.tmpdir(), "studio-badbuild-"));
  try {
    fs.cpSync(path.join(repo, "behavior_packs"), path.join(work, "behavior_packs"), { recursive: true });
    fs.cpSync(path.join(repo, "resource_packs"), path.join(work, "resource_packs"), { recursive: true });
    fs.cpSync(path.join(repo, "studio"), path.join(work, "studio"), { recursive: true });
    fs.writeFileSync(path.join(work, "resource_packs/studio_demo_rp/entity/pixel_slime.entity.json"), "{");
    assert.throws(
      () => execFileSync(process.execPath, [script, "--root", work, "--out", path.join(work, "dist")], { stdio: "pipe" }),
      (e) => e.status !== 0,
    );
    assert.ok(!fs.existsSync(path.join(work, "dist", "studio_demo.mcaddon")));
  } finally {
    fs.rmSync(work, { recursive: true, force: true });
  }
});
