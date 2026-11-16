#!/usr/bin/env node
// Minecraft-Addon-Studio project validator.
// Zero dependencies. Usage: node validators/validate-addon.mjs [projectRoot]
// Exports validateProject(root) -> { errors, warnings, info } for tests and the build script.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import zlib from "node:zlib";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ID_RE = /^[a-z0-9_]+:[a-z0-9_./-]+$/;
const MODULE_TYPES = new Set(["data", "resources", "script", "interface", "client_data", "world_template", "skin_pack"]);
const SCRIPT_ALLOWED_IMPORTS = new Set(["@minecraft/server", "@minecraft/server-ui"]);
const SCRIPT_FORBIDDEN = [
  [/\beval\s*\(/, "eval() is not allowed"],
  [/\bnew\s+Function\s*\(/, "new Function() is not allowed"],
  [/\bfetch\s*\(/, "fetch() network calls are not allowed in add-on scripts"],
  [/\bXMLHttpRequest\b/, "XMLHttpRequest is not allowed in add-on scripts"],
];
const PNG_SIG = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

// ---------- PNG reader (8-bit RGB/RGBA, non-interlaced) ----------
export function readPng(buf) {
  if (!buf.subarray(0, 8).equals(PNG_SIG)) throw new Error("not a PNG file");
  let pos = 8, width = 0, height = 0, bitDepth = 0, colorType = 0, interlace = 0;
  const idat = [];
  while (pos + 8 <= buf.length) {
    const len = buf.readUInt32BE(pos);
    const type = buf.toString("latin1", pos + 4, pos + 8);
    const data = buf.subarray(pos + 8, pos + 8 + len);
    if (type === "IHDR") {
      width = data.readUInt32BE(0); height = data.readUInt32BE(4);
      bitDepth = data[8]; colorType = data[9]; interlace = data[12];
    } else if (type === "IDAT") idat.push(data);
    else if (type === "IEND") break;
    pos += 12 + len;
  }
  if (bitDepth !== 8 || interlace !== 0 || (colorType !== 6 && colorType !== 2)) {
    return { width, height, colorType, supported: false };
  }
  const bpp = colorType === 6 ? 4 : 3;
  const stride = width * bpp;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const out = Buffer.alloc(stride * height);
  let prev = Buffer.alloc(stride);
  let p = 0;
  for (let y = 0; y < height; y++) {
    const filter = raw[p++];
    const line = raw.subarray(p, p + stride);
    p += stride;
    const cur = Buffer.alloc(stride);
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? cur[x - bpp] : 0;
      const b = prev[x];
      const c = x >= bpp ? prev[x - bpp] : 0;
      let pred;
      switch (filter) {
        case 0: pred = 0; break;
        case 1: pred = a; break;
        case 2: pred = b; break;
        case 3: pred = (a + b) >> 1; break;
        case 4: {
          const pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c);
          pred = pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
          break;
        }
        default: throw new Error(`unknown PNG filter ${filter}`);
      }
      cur[x] = (line[x] + pred) & 0xff;
    }
    cur.copy(out, y * stride);
    prev = cur;
  }
  let semiTransparent = 0, nonBinaryAlpha = false;
  const colors = new Set();
  for (let i = 0; i < width * height; i++) {
    const o = i * bpp;
    const alpha = colorType === 6 ? out[o + 3] : 255;
    if (alpha !== 0 && alpha !== 255) nonBinaryAlpha = true;
    if (alpha === 0) continue;
    if (alpha !== 255) semiTransparent++;
    colors.add((out[o] << 16) | (out[o + 1] << 8) | out[o + 2]);
  }
  return { width, height, colorType, supported: true, semiTransparent, nonBinaryAlpha, uniqueOpaqueColors: colors.size };
}

// ---------- helpers ----------
export function boxUvProblem(cube, tw, th) {
  if (!Array.isArray(cube.uv)) return null; // per-face UVs are checked as info only
  const [sx, sy, sz] = cube.size;
  const [u, v] = cube.uv;
  const w = 2 * (sx + sz), h = sz + sy;
  if (u < 0 || v < 0 || u + w > tw || v + h > th) {
    return `box UV [${u},${v}] needs ${w}x${h} starting at (${u},${v}) but texture is ${tw}x${th}`;
  }
  return null;
}

export function molangProblem(expr) {
  if (typeof expr !== "string") return null;
  if (expr.trim() === "") return "empty Molang expression";
  let depth = 0;
  for (const ch of expr) {
    if (ch === "(") depth++;
    else if (ch === ")") depth--;
    if (depth < 0) return `unbalanced ')' in "${expr}"`;
  }
  if (depth !== 0) return `unbalanced '(' in "${expr}"`;
  if (/[+\-*/&|=?:]\s*$/.test(expr.trim())) return `Molang ends with an operator: "${expr}"`;
  return null;
}

function walk(dir, suffix) {
  if (!fs.existsSync(dir)) return [];
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full, suffix));
    else if (!suffix || entry.name.endsWith(suffix)) out.push(full);
  }
  return out.sort();
}

function collectStrings(value, acc = []) {
  if (typeof value === "string") acc.push(value);
  else if (Array.isArray(value)) value.forEach((v) => collectStrings(v, acc));
  else if (value && typeof value === "object") Object.values(value).forEach((v) => collectStrings(v, acc));
  return acc;
}

// ---------- main validation ----------
export function validateProject(root) {
  const errors = [], warnings = [], info = [];
  const rel = (f) => path.relative(root, f) || ".";
  const err = (f, m) => errors.push(`${rel(f)}: ${m}`);
  const warn = (f, m) => warnings.push(`${rel(f)}: ${m}`);
  const note = (m) => info.push(m);

  const readJson = (file) => {
    try {
      return JSON.parse(fs.readFileSync(file, "utf8"));
    } catch (e) {
      err(file, `invalid JSON: ${e.message}`);
      return null;
    }
  };

  // 1. Discover packs
  const packs = [];
  for (const base of ["behavior_packs", "resource_packs"]) {
    const baseDir = path.join(root, base);
    if (!fs.existsSync(baseDir)) continue;
    for (const name of fs.readdirSync(baseDir).sort()) {
      const dir = path.join(baseDir, name);
      if (!fs.statSync(dir).isDirectory()) continue;
      const mf = path.join(dir, "manifest.json");
      if (!fs.existsSync(mf)) { err(dir, "pack folder has no manifest.json"); continue; }
      const manifest = readJson(mf);
      if (!manifest) continue;
      const role = (manifest.modules || []).some((m) => m.type === "resources") ? "rp" : "bp";
      packs.push({ dir, name, role, manifest, manifestFile: mf, scriptEntry: null, depModules: new Set() });
    }
  }
  if (packs.length === 0) err(root, "no packs found (expected behavior_packs/* and resource_packs/*)");
  const bps = packs.filter((p) => p.role === "bp");
  const rps = packs.filter((p) => p.role === "rp");
  if (bps.length === 0) warn(root, "no behavior pack found");
  if (rps.length === 0) warn(root, "no resource pack found");
  if (bps.length > 1 || rps.length > 1) warn(root, "more than one pack of a role; cross-checks use all packs together");

  // 2. Manifests: format, UUIDs, versions, modules
  const uuidSeen = new Map();
  const checkUuid = (u, where, label) => {
    if (typeof u !== "string" || !UUID_RE.test(u)) { err(where, `${label} is not a valid UUID: "${u}"`); return; }
    if (uuidSeen.has(u)) err(where, `duplicate UUID ${u} (also used in ${uuidSeen.get(u)})`);
    else uuidSeen.set(u, rel(where));
  };
  const isVersion = (v) => Array.isArray(v) && v.length === 3 && v.every((n) => Number.isInteger(n) && n >= 0);
  const headerUuids = new Set();
  for (const p of packs) {
    const m = p.manifest;
    if (m.format_version !== 2) err(p.manifestFile, `format_version should be 2, found ${JSON.stringify(m.format_version)}`);
    const h = m.header || {};
    if (!h.name) err(p.manifestFile, "header.name is missing");
    checkUuid(h.uuid, p.manifestFile, "header.uuid");
    if (h.uuid) headerUuids.add(h.uuid);
    if (!isVersion(h.version)) err(p.manifestFile, "header.version must be [major, minor, patch] integers");
    if (!Array.isArray(m.modules) || m.modules.length === 0) { err(p.manifestFile, "modules must be a non-empty array"); continue; }
    for (const mod of m.modules) {
      if (!MODULE_TYPES.has(mod.type)) err(p.manifestFile, `unknown module type "${mod.type}"`);
      checkUuid(mod.uuid, p.manifestFile, `module(${mod.type}).uuid`);
      if (!isVersion(mod.version)) err(p.manifestFile, `module(${mod.type}).version must be [major, minor, patch]`);
      if (mod.type === "script") {
        if (mod.language !== "javascript") err(p.manifestFile, `script module language must be "javascript"`);
        if (typeof mod.entry !== "string") err(p.manifestFile, "script module is missing entry");
        else {
          p.scriptEntry = mod.entry;
          if (!fs.existsSync(path.join(p.dir, mod.entry))) err(p.manifestFile, `script entry not found: ${mod.entry}`);
        }
      }
    }
  }
  // Dependencies (second pass: all header UUIDs known)
  for (const p of packs) {
    for (const dep of p.manifest.dependencies || []) {
      if (dep.uuid !== undefined) {
        if (!headerUuids.has(dep.uuid)) err(p.manifestFile, `dependency uuid ${dep.uuid} matches no header in this project`);
      } else if (dep.module_name !== undefined) {
        p.depModules.add(dep.module_name);
        if (typeof dep.version !== "string" && !isVersion(dep.version)) err(p.manifestFile, `dependency ${dep.module_name} has an invalid version`);
      } else err(p.manifestFile, "dependency needs either uuid or module_name");
    }
  }
  for (const bp of bps) for (const rp of rps) {
    const bpDeps = new Set((bp.manifest.dependencies || []).map((d) => d.uuid));
    const rpDeps = new Set((rp.manifest.dependencies || []).map((d) => d.uuid));
    if (!bpDeps.has(rp.manifest.header.uuid)) warn(bp.manifestFile, `does not depend on resource pack ${rp.name}`);
    if (!rpDeps.has(bp.manifest.header.uuid)) warn(rp.manifestFile, `does not depend on behavior pack ${bp.name}`);
  }

  // 3. Behavior entities
  const bpEntityIds = new Map(); // id -> file
  for (const bp of bps) {
    for (const file of walk(path.join(bp.dir, "entities"), ".json")) {
      const data = readJson(file);
      if (!data) continue;
      const desc = data["minecraft:entity"]?.description;
      if (!desc) { err(file, "missing minecraft:entity.description"); continue; }
      if (!ID_RE.test(desc.identifier || "")) err(file, `invalid identifier "${desc.identifier}" (expected namespace:name)`);
      if (!data.format_version) err(file, "format_version is missing");
      bpEntityIds.set(desc.identifier, file);
    }
  }

  // 4. Geometry
  const geoIndex = new Map(); // identifier -> { tw, th, bones:Set, file }
  for (const rp of rps) {
    for (const file of walk(path.join(rp.dir, "models"), ".geo.json")) {
      const data = readJson(file);
      if (!data) continue;
      if (!data.format_version) err(file, "format_version is missing");
      for (const g of data["minecraft:geometry"] || []) {
        const d = g.description || {};
        if (!/^geometry\.[a-z0-9_.-]+$/i.test(d.identifier || "")) err(file, `geometry identifier must start with "geometry.": "${d.identifier}"`);
        const tw = d.texture_width, th = d.texture_height;
        if (!Number.isInteger(tw) || !Number.isInteger(th) || tw <= 0 || th <= 0) err(file, `${d.identifier}: texture_width/height must be positive integers`);
        const bones = new Map();
        for (const b of g.bones || []) {
          if (bones.has(b.name)) err(file, `${d.identifier}: duplicate bone "${b.name}"`);
          bones.set(b.name, b);
        }
        for (const b of bones.values()) {
          if (b.parent !== undefined && !bones.has(b.parent)) err(file, `${d.identifier}: bone "${b.name}" has missing parent "${b.parent}"`);
          if (b.pivot && (!Array.isArray(b.pivot) || b.pivot.length !== 3)) err(file, `${d.identifier}: bone "${b.name}" pivot must have 3 numbers`);
          for (const c of b.cubes || []) {
            if (!Array.isArray(c.size) || c.size.length !== 3 || c.size.some((n) => !(n > 0))) {
              err(file, `${d.identifier}: bone "${b.name}" has a cube with non-positive size ${JSON.stringify(c.size)}`);
              continue;
            }
            if (!Array.isArray(c.origin) || c.origin.length !== 3) err(file, `${d.identifier}: bone "${b.name}" cube origin must have 3 numbers`);
            if (!Array.isArray(c.uv)) note(`${rel(file)}: ${d.identifier}/${b.name} uses per-face UVs (not bounds-checked)`);
            else if (Number.isInteger(tw) && Number.isInteger(th)) {
              const problem = boxUvProblem(c, tw, th);
              if (problem) err(file, `${d.identifier}: bone "${b.name}" ${problem}`);
            }
          }
        }
        geoIndex.set(d.identifier, { tw, th, bones: new Set(bones.keys()), file });
      }
    }
  }
  const allGeoBones = new Set([...geoIndex.values()].flatMap((g) => [...g.bones]));

  // 5. Animations
  const animIndex = new Map(); // name -> file
  for (const rp of rps) {
    for (const file of walk(path.join(rp.dir, "animations"), ".animation.json")) {
      const data = readJson(file);
      if (!data) continue;
      if (!data.format_version) err(file, "format_version is missing");
      for (const [name, anim] of Object.entries(data.animations || {})) {
        if (!name.startsWith("animation.")) err(file, `animation name must start with "animation.": ${name}`);
        animIndex.set(name, file);
        if (!(typeof anim.animation_length === "number" && anim.animation_length > 0)) err(file, `${name}: animation_length must be a positive number`);
        for (const [bone, channels] of Object.entries(anim.bones || {})) {
          if (!allGeoBones.has(bone)) err(file, `${name}: animates bone "${bone}" which exists in no geometry`);
          for (const [chan, frames] of Object.entries(channels)) {
            if (typeof frames !== "object" || frames === null) continue;
            const times = Object.keys(frames).map(Number);
            if (times.some((t) => Number.isNaN(t))) err(file, `${name}/${bone}/${chan}: keyframe times must be numbers`);
            const sorted = [...times].sort((a, b) => a - b);
            if (times.some((t, i) => i > 0 && t <= times[i - 1])) warn(file, `${name}/${bone}/${chan}: keyframes not in strictly ascending order`);
            if (typeof anim.animation_length === "number" && sorted.length && sorted.at(-1) !== anim.animation_length) {
              err(file, `${name}/${bone}/${chan}: last keyframe ${sorted.at(-1)} must equal animation_length ${anim.animation_length}`);
            }
          }
        }
        for (const s of collectStrings(anim)) {
          const p = molangProblem(s);
          if (p && /[()]|^\s*$/.test(s)) err(file, `${name}: ${p}`);
        }
      }
    }
  }

  // 6. Render controllers
  const rcIndex = new Map(); // key -> { data, file }
  for (const rp of rps) {
    for (const file of walk(path.join(rp.dir, "render_controllers"), ".json")) {
      const data = readJson(file);
      if (!data) continue;
      for (const [key, rc] of Object.entries(data.render_controllers || {})) {
        if (!key.startsWith("controller.render.")) err(file, `render controller key must start with "controller.render.": ${key}`);
        rcIndex.set(key, { data: rc, file });
      }
    }
  }

  // 7. Client entities + cross-references
  const clientEntities = new Map(); // id -> { file, desc }
  const textureRefs = []; // { file, path }
  for (const rp of rps) {
    for (const file of walk(path.join(rp.dir, "entity"), ".json")) {
      const data = readJson(file);
      if (!data) continue;
      const desc = data["minecraft:client_entity"]?.description;
      if (!desc) { err(file, "missing minecraft:client_entity.description"); continue; }
      if (!ID_RE.test(desc.identifier || "")) err(file, `invalid identifier "${desc.identifier}"`);
      clientEntities.set(desc.identifier, { file, desc });

      for (const [k, geo] of Object.entries(desc.geometry || {})) {
        if (!geoIndex.has(geo)) err(file, `geometry "${geo}" (${k}) is not defined in any models/*.geo.json`);
      }
      for (const [k, tex] of Object.entries(desc.textures || {})) {
        const texFile = path.join(rp.dir, `${tex}.png`);
        textureRefs.push({ file, path: texFile, key: k });
        if (!fs.existsSync(texFile)) err(file, `texture "${tex}" (${k}) not found at ${rel(texFile)}`);
      }
      for (const [k, anim] of Object.entries(desc.animations || {})) {
        if (!animIndex.has(anim)) err(file, `animation "${anim}" (${k}) is not defined in any animations file`);
      }
      for (const entries of [desc.scripts?.animate ?? []]) {
        for (const e of entries) {
          for (const [name, expr] of Object.entries(e)) {
            if (!(desc.animations && name in desc.animations)) err(file, `animate refers to "${name}" which is not in description.animations`);
            const p = molangProblem(expr);
            if (p) err(file, `animate "${name}": ${p}`);
          }
        }
      }
      for (const rcName of desc.render_controllers || []) {
        const rc = rcIndex.get(rcName);
        if (!rc) { err(file, `render controller "${rcName}" is not defined`); continue; }
        const g = rc.data.geometry;
        if (typeof g === "string" && g.startsWith("Geometry.") && !(g.slice(9) in (desc.geometry || {}))) {
          err(rc.file, `${rcName} uses ${g} but the entity has no geometry key "${g.slice(9)}"`);
        }
        for (const mat of rc.data.materials || []) {
          for (const v of Object.values(mat)) {
            if (typeof v === "string" && v.startsWith("Material.") && !(v.slice(9) in (desc.materials || {}))) {
              err(rc.file, `${rcName} uses ${v} but the entity has no material key "${v.slice(9)}"`);
            }
          }
        }
        for (const t of rc.data.textures || []) {
          if (typeof t === "string" && t.startsWith("Texture.") && !(t.slice(8) in (desc.textures || {}))) {
            err(rc.file, `${rcName} uses ${t} but the entity has no texture key "${t.slice(8)}"`);
          }
        }
      }
    }
  }
  for (const [id, file] of bpEntityIds) {
    if (!clientEntities.has(id)) err(file, `behavior entity "${id}" has no matching resource pack client entity`);
  }

  // 8. Textures (PNG dimensions, alpha, palette)
  const checkedTextures = new Set();
  for (const ref of textureRefs) {
    if (!fs.existsSync(ref.path) || checkedTextures.has(ref.path)) continue;
    checkedTextures.add(ref.path);
    let png;
    try { png = readPng(fs.readFileSync(ref.path)); }
    catch (e) { err(ref.path, `cannot read PNG: ${e.message}`); continue; }
    if (!png.supported) { warn(ref.path, `PNG type not checked (bit depth/colour type ${png.colorType}); use 8-bit RGBA`); continue; }
    if (png.colorType !== 6) warn(ref.path, "texture has no alpha channel; RGBA is recommended for entities");
    if (png.nonBinaryAlpha) warn(ref.path, "alpha contains values other than 0 and 255 (pixel art should be hard-edged)");
    if (png.uniqueOpaqueColors > 16) warn(ref.path, `${png.uniqueOpaqueColors} opaque colours (pixel-art guideline: at most 16 per entity)`);
    const geo = [...clientEntities.values()].find((c) => c.file === ref.file);
    const geometryId = geo && Object.values(geo.desc.geometry || {})[0];
    const g = geoIndex.get(geometryId);
    if (g && (png.width !== g.tw || png.height !== g.th)) {
      err(ref.path, `PNG is ${png.width}x${png.height} but ${geometryId} expects ${g.tw}x${g.th}`);
    }
  }
  for (const file of walk(path.join(root, "resource_packs"), ".png")) {
    if (path.basename(file) === "pack_icon.png" || checkedTextures.has(file)) continue;
    warn(file, "PNG is not referenced by any client entity");
  }

  // 9. Scripts (imports, forbidden patterns, syntax)
  for (const bp of bps) {
    const declaresServer = bp.depModules.has("@minecraft/server");
    for (const file of walk(path.join(bp.dir, "scripts"), ".js")) {
      const src = fs.readFileSync(file, "utf8");
      const specs = [...src.matchAll(/(?:from|import)\s+["']([^"']+)["']/g)].map((m) => m[1]);
      for (const spec of specs) {
        if (spec.startsWith(".")) continue;
        if (!SCRIPT_ALLOWED_IMPORTS.has(spec)) err(file, `import "${spec}" is not an allowed module`);
        else if (!declaresServer) err(file, `imports ${spec} but the behavior pack does not declare it as a dependency`);
      }
      for (const [re, msg] of SCRIPT_FORBIDDEN) if (re.test(src)) err(file, msg);
      const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "mcaddon-check-"));
      const tmp = path.join(tmpDir, "check.mjs");
      try {
        fs.writeFileSync(tmp, src);
        execFileSync(process.execPath, ["--check", tmp], { stdio: "pipe" });
      } catch (e) {
        err(file, `syntax check failed: ${String(e.stderr || e.message).split("\n").find((l) => /Error|SyntaxError/.test(l)) || "see node --check"}`);
      } finally {
        fs.rmSync(tmpDir, { recursive: true, force: true });
      }
    }
    if (bp.scriptEntry && !fs.existsSync(path.join(bp.dir, bp.scriptEntry))) err(bp.manifestFile, "script entry missing");
  }

  // 10. Language file
  for (const rp of rps) {
    const lang = path.join(rp.dir, "texts", "en_US.lang");
    if (!fs.existsSync(lang)) { warn(rp.dir, "texts/en_US.lang is missing"); continue; }
    const keys = new Set(fs.readFileSync(lang, "utf8").split("\n").filter((l) => l.trim() && !l.startsWith("#")).map((l) => l.split("=")[0]));
    for (const id of clientEntities.keys()) {
      if (!keys.has(`entity.${id}.name`)) warn(lang, `no display name for ${id} (entity.${id}.name)`);
    }
  }

  note(`packs: ${packs.length} (BP ${bps.length}, RP ${rps.length}); entities: ${bpEntityIds.size} BP / ${clientEntities.size} client; geometry: ${geoIndex.size}; animations: ${animIndex.size}; UUIDs checked: ${uuidSeen.size}`);
  return { errors, warnings, info };
}

// ---------- CLI ----------
const isMain = process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (isMain) {
  const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const root = path.resolve(process.argv[2] || repoRoot);
  const { errors, warnings, info } = validateProject(root);
  for (const m of info) console.log(`info   ${m}`);
  for (const m of warnings) console.log(`warn   ${m}`);
  for (const m of errors) console.log(`error  ${m}`);
  console.log(`\n${errors.length} error(s), ${warnings.length} warning(s)`);
  process.exit(errors.length ? 1 : 0);
}
