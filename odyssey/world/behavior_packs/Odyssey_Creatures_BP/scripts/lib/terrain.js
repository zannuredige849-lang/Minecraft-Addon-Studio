// Terrain queries at runtime. Every position the campaign uses for spawning, teleporting or framing a camera is
// checked against the real blocks first, because sites sit on terrain of very different heights (the Strait cliff
// tops out near y=114 while most beaches are at y=64).
import { block, isAir, isWater } from "./util.js";

const PASSABLE = new Set(["minecraft:air", "minecraft:short_grass", "minecraft:tall_grass", "minecraft:grass", "minecraft:dandelion",
  "minecraft:poppy", "minecraft:fern", "minecraft:light_block", "minecraft:snow_layer", "minecraft:seagrass"]);
const UNSAFE_GROUND = new Set(["minecraft:lava", "minecraft:flowing_lava", "minecraft:fire", "minecraft:magma", "minecraft:cactus",
  "minecraft:oak_leaves", "minecraft:spruce_leaves", "minecraft:dark_oak_leaves", "minecraft:glowstone", "minecraft:oak_fence",
  "minecraft:campfire", "minecraft:sweet_berry_bush", "minecraft:powder_snow"]);

const passable = (b) => !!b && (PASSABLE.has(b.typeId) || isAir(b));
/** Is this block loaded at all? `getBlock` returns undefined in unloaded chunks. */
export const loaded = (dim, loc) => !!block(dim, loc);

/** Topmost solid, non-liquid block in a column (scanning down from `fromY`). Returns its y, or undefined. */
export function groundY(dim, x, z, fromY = 130, toY = 40) {
  for (let y = fromY; y >= toY; y--) {
    const b = block(dim, { x, y, z });
    if (b === undefined) return undefined;          // chunk not loaded
    if (!passable(b) && !isWater(b)) return y;
  }
  return undefined;
}

/** Highest water surface in a column, if the column ends in water. */
export function waterY(dim, x, z, fromY = 90, toY = 40) {
  for (let y = fromY; y >= toY; y--) {
    const b = block(dim, { x, y, z });
    if (b === undefined) return undefined;
    if (isWater(b)) return y;
    if (!passable(b)) return undefined;
  }
  return undefined;
}

/** A standing spot (feet position) at x,z: solid safe ground with two blocks of headroom. */
export function standAt(dim, x, z, fromY = 130) {
  const fx = Math.floor(x), fz = Math.floor(z);
  const y = groundY(dim, fx, fz, fromY);
  if (y === undefined) return undefined;
  const g = block(dim, { x: fx, y, z: fz });
  if (!g || UNSAFE_GROUND.has(g.typeId)) return undefined;
  if (!passable(block(dim, { x: fx, y: y + 1, z: fz })) || !passable(block(dim, { x: fx, y: y + 2, z: fz }))) return undefined;
  return { x: fx + 0.5, y: y + 1, z: fz + 0.5 };
}

/** Nearest standing spot to (x,z), searching outward in rings up to `maxR` blocks. */
export function safeSpotNear(dim, x, z, maxR = 10, fromY = 130) {
  for (let r = 0; r <= maxR; r++) {
    for (let dx = -r; dx <= r; dx++) {
      for (let dz = -r; dz <= r; dz++) {
        if (Math.max(Math.abs(dx), Math.abs(dz)) !== r) continue;
        const s = standAt(dim, x + dx, z + dz, fromY);
        if (s) return s;
      }
    }
  }
  return undefined;
}

/** Where a creature should appear: Charybdis on open water, everything else (Sirens on their rocks, Scylla on her cliff) on safe ground. */
export function spawnSpotFor(dim, type, x, z) {
  if (type === "studio:charybdis") {
    for (let r = 0; r <= 24; r += 2) {
      for (let a = 0; a < 8; a++) {
        const px = Math.floor(x + Math.cos(a * Math.PI / 4) * r), pz = Math.floor(z + Math.sin(a * Math.PI / 4) * r);
        const w = waterY(dim, px, pz);
        if (w !== undefined) return { x: px + 0.5, y: w, z: pz + 0.5 };
      }
    }
  }
  return safeSpotNear(dim, x, z, 12);
}
