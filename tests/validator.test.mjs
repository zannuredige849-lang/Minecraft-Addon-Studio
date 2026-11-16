// Validator test suite: real sample must pass; each rule must fail on a broken fixture.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";
import { validateProject, readPng, boxUvProblem, molangProblem } from "../validators/validate-addon.mjs";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

// Minimal valid RGBA PNG writer (filter 0, no compression tricks) for fixtures.
function writePng(file, w, h, pixel = [40, 110, 40, 255]) {
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 4 + 1)] = 0;
    for (let x = 0; x < w; x++) pixel.forEach((v, i) => (raw[y * (w * 4 + 1) + 1 + x * 4 + i] = v));
  }
  const crcTable = Array.from({ length: 256 }, (_, n) => {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    return c >>> 0;
  });
  const crc = (buf) => {
    let c = 0xffffffff;
    for (const b of buf) c = crcTable[(c ^ b) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  };
  const chunk = (type, data) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const td = Buffer.concat([Buffer.from(type, "latin1"), data]);
    const c = Buffer.alloc(4); c.writeUInt32BE(crc(td));
    return Buffer.concat([len, td, c]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  const png = Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
    chunk("IDAT", zlib.deflateSync(raw)),
    chunk("IEND", Buffer.alloc(0)),
  ]);
  fs.writeFileSync(file, png);
}

// Copy only the packs into a fresh temp project so each test can break one thing.
function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "studio-fixture-"));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  fs.cpSync(path.join(repo, "behavior_packs"), path.join(dir, "behavior_packs"), { recursive: true });
  fs.cpSync(path.join(repo, "resource_packs"), path.join(dir, "resource_packs"), { recursive: true });
  return dir;
}
const edit = (file, fn) => fs.writeFileSync(file, JSON.stringify(fn(JSON.parse(fs.readFileSync(file, "utf8"))), null, 2));
const BP = "behavior_packs/studio_demo_bp";
const RP = "resource_packs/studio_demo_rp";

test("sample project passes with zero errors", () => {
  const { errors } = validateProject(repo);
  assert.deepEqual(errors, []);
});

test("sample texture decodes as 16x16 RGBA with binary alpha", () => {
  const png = readPng(fs.readFileSync(path.join(repo, RP, "textures/entity/pixel_slime.png")));
  assert.equal(png.supported, true);
  assert.equal(png.width, 16);
  assert.equal(png.height, 16);
  assert.equal(png.nonBinaryAlpha, false);
  assert.ok(png.uniqueOpaqueColors <= 16);
});

test("invalid JSON is reported", (t) => {
  const dir = fixture(t);
  fs.writeFileSync(path.join(dir, RP, "entity/pixel_slime.entity.json"), "{ broken");
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("invalid JSON")));
});

test("duplicate UUID across packs is reported", (t) => {
  const dir = fixture(t);
  edit(path.join(dir, RP, "manifest.json"), (m) => ((m.modules[0].uuid = m.header.uuid), m));
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("duplicate UUID")), errors.join("\n"));
});

test("invalid UUID format is reported", (t) => {
  const dir = fixture(t);
  edit(path.join(dir, BP, "manifest.json"), (m) => ((m.header.uuid = "not-a-uuid"), m));
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("not a valid UUID")));
});

test("box UV outside texture bounds is reported", (t) => {
  const dir = fixture(t);
  edit(path.join(dir, RP, "models/entity/pixel_slime.geo.json"), (g) => {
    g["minecraft:geometry"][0].bones[1].cubes[0].uv = [14, 14];
    return g;
  });
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("box UV")), errors.join("\n"));
});

test("PNG size mismatch with geometry is reported", (t) => {
  const dir = fixture(t);
  writePng(path.join(dir, RP, "textures/entity/pixel_slime.png"), 32, 32);
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("expects 16x16")), errors.join("\n"));
});

test("missing texture is reported", (t) => {
  const dir = fixture(t);
  fs.rmSync(path.join(dir, RP, "textures/entity/pixel_slime.png"));
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("not found")));
});

test("animation bone missing from every geometry is reported", (t) => {
  const dir = fixture(t);
  edit(path.join(dir, RP, "animations/pixel_slime.animation.json"), (a) => {
    a.animations["animation.pixel_slime.idle"].bones.tail = a.animations["animation.pixel_slime.idle"].bones.body;
    return a;
  });
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes('bone "tail"')));
});

test("animation_length must match last keyframe", (t) => {
  const dir = fixture(t);
  edit(path.join(dir, RP, "animations/pixel_slime.animation.json"), (a) => {
    a.animations["animation.pixel_slime.idle"].animation_length = 3.0;
    return a;
  });
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("must equal animation_length")));
});

test("unbalanced Molang in client entity is reported", (t) => {
  const dir = fixture(t);
  edit(path.join(dir, RP, "entity/pixel_slime.entity.json"), (e) => {
    e["minecraft:client_entity"].description.scripts.animate[0].idle = "query.is_alive(";
    return e;
  });
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("unbalanced")));
});

test("BP entity without RP client entity is reported", (t) => {
  const dir = fixture(t);
  fs.rmSync(path.join(dir, RP, "entity/pixel_slime.entity.json"));
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("no matching resource pack client entity")));
});

test("forbidden script pattern is reported", (t) => {
  const dir = fixture(t);
  fs.writeFileSync(path.join(dir, BP, "scripts/main.js"), 'import { world } from "@minecraft/server";\neval("1+1");\n');
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("eval()")));
});

test("import of an unapproved module is reported", (t) => {
  const dir = fixture(t);
  fs.writeFileSync(path.join(dir, BP, "scripts/main.js"), 'import axios from "axios";\nconsole.log(axios);\n');
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes('"axios" is not an allowed module')));
});

test("script syntax error is reported", (t) => {
  const dir = fixture(t);
  fs.writeFileSync(path.join(dir, BP, "scripts/main.js"), 'import { world } from "@minecraft/server";\nconst = ;\n');
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("syntax check failed")));
});

test("missing script entry file is reported", (t) => {
  const dir = fixture(t);
  fs.rmSync(path.join(dir, BP, "scripts/main.js"));
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("script entry not found")));
});

test("unknown geometry reference is reported", (t) => {
  const dir = fixture(t);
  edit(path.join(dir, RP, "entity/pixel_slime.entity.json"), (e) => {
    e["minecraft:client_entity"].description.geometry.default = "geometry.missing";
    return e;
  });
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes('geometry "geometry.missing"')));
});

test("unknown animation reference is reported", (t) => {
  const dir = fixture(t);
  edit(path.join(dir, RP, "entity/pixel_slime.entity.json"), (e) => {
    e["minecraft:client_entity"].description.animations.idle = "animation.pixel_slime.nope";
    return e;
  });
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("animation.pixel_slime.nope")));
});

test("render controller geometry key mismatch is reported", (t) => {
  const dir = fixture(t);
  edit(path.join(dir, RP, "render_controllers/pixel_slime.render_controllers.json"), (r) => {
    r.render_controllers["controller.render.pixel_slime"].geometry = "Geometry.other";
    return r;
  });
  const { errors } = validateProject(dir);
  assert.ok(errors.some((e) => e.includes("no geometry key")));
});

test("helper: box UV math", () => {
  assert.equal(boxUvProblem({ size: [4, 4, 4], uv: [0, 0] }, 16, 16), null);
  assert.match(boxUvProblem({ size: [4, 4, 4], uv: [1, 0] }, 16, 16), /box UV/);
});

test("helper: Molang checks", () => {
  assert.equal(molangProblem("query.is_alive"), null);
  assert.equal(molangProblem("math.sin(query.anim_time * 180)"), null);
  assert.match(molangProblem("math.sin((1"), /unbalanced/);
  assert.match(molangProblem(""), /empty/);
  assert.match(molangProblem("query.a +"), /operator/);
});
