#!/usr/bin/env node
// Validate the project, then package the packs into dist/<packName>.mcaddon.
// Usage: node scripts/build-mcaddon.mjs [--root <dir>] [--out <dir>]
// Refuses to package if the validator reports any error.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { validateProject } from "../validators/validate-addon.mjs";

const args = process.argv.slice(2);
const flag = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};
const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const root = path.resolve(flag("--root") || repo);
const outDir = path.resolve(flag("--out") || path.join(root, "dist"));

const config = JSON.parse(fs.readFileSync(path.join(root, "studio", "config", "studio.json"), "utf8"));
const packName = config.packName;

const { errors, warnings } = validateProject(root);
for (const w of warnings) console.log(`warn   ${w}`);
if (errors.length) {
  for (const e of errors) console.log(`error  ${e}`);
  console.error(`\nBuild stopped: ${errors.length} validation error(s). Nothing was packaged.`);
  process.exit(1);
}

const sources = [config.packs.behavior, config.packs.resource].map((p) => path.join(root, p));
const staging = fs.mkdtempSync(path.join(os.tmpdir(), "mcaddon-stage-"));
try {
  for (const src of sources) {
    fs.cpSync(src, path.join(staging, path.basename(src)), { recursive: true, filter: (f) => !f.includes("node_modules") });
  }
  fs.mkdirSync(outDir, { recursive: true });
  const target = path.join(outDir, `${packName}.mcaddon`);
  fs.rmSync(target, { force: true });
  try {
    execFileSync("zip", ["-r", "-X", "-q", target, "."], { cwd: staging, stdio: "pipe" });
  } catch {
    // zip CLI missing: fall back to Python's zipfile (always present with python3)
    execFileSync("python3", ["-c", `
import os, sys, zipfile
src, dst = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fs_ in os.walk(src):
        for f in fs_:
            full = os.path.join(dp, f)
            z.write(full, os.path.relpath(full, src))
`, staging, target], { stdio: "pipe" });
  }
  console.log(`\npackaged ${path.relative(root, target) || target}`);
  console.log(`contents:`);
  for (const line of fs.readdirSync(staging, { recursive: true })) console.log(`  ${line}`);
} finally {
  fs.rmSync(staging, { recursive: true, force: true });
}
