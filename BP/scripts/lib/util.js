// Shared helpers. Every call into the game is guarded: one failing entity or API call must never stop a loop.
import { world, system } from "@minecraft/server";

export const DIMENSIONS = ["minecraft:overworld", "minecraft:nether", "minecraft:the_end"];

// things that are never prey: the add-on's own creatures, bystanders and objects
export const NOT_PREY = new Set(["studio:scylla", "studio:charybdis", "studio:boulder", "studio:cyclops", "studio:circe_sister",
  "studio:trojan_horse", "studio:siren", "studio:tiresias", "studio:athena", "minecraft:item", "minecraft:xp_orb",
  "minecraft:arrow", "minecraft:armor_stand", "minecraft:painting", "minecraft:boat", "minecraft:chest_boat"]);

export const now = () => system.currentTick;
export const valid = (e) => { try { return !!e && (typeof e.isValid === "function" ? e.isValid() : e.isValid); } catch { return false; } };
export const warn = (where, err) => { try { console.warn(`[odyssey] ${where}: ${err && err.message ? err.message : err}`); } catch { } };
/** Run fn, report (never throw) any error. */
export const safe = (where, fn) => { try { return fn(); } catch (err) { warn(where, err); return undefined; } };
export const later = (ticks, fn) => system.runTimeout(() => safe("later", fn), Math.max(1, Math.round(ticks)));

// ---- vectors
export const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z });
export const sub = (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z });
export const scale = (a, k) => ({ x: a.x * k, y: a.y * k, z: a.z * k });
export const len = (a) => Math.hypot(a.x, a.y, a.z);
export const flat = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);
export const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
export const rand = (lo, hi) => lo + Math.random() * (hi - lo);
export const pick = (list) => list[Math.floor(Math.random() * list.length)];
export const forward = (e) => {
  try { const v = e.getViewDirection(); const l = Math.hypot(v.x, v.z) || 1; return { x: v.x / l, y: 0, z: v.z / l }; }
  catch { return { x: 0, y: 0, z: 1 }; }
};
export const right = (e) => { const f = forward(e); return { x: -f.z, y: 0, z: f.x }; };
/** Unit horizontal vector from a to b. */
export const dirTo = (a, b) => { const d = sub(b, a); const l = Math.hypot(d.x, d.z) || 1; return { x: d.x / l, y: 0, z: d.z / l }; };
export const ringSpot = (center, r, a) => ({ x: center.x + Math.cos(a) * r, y: center.y, z: center.z + Math.sin(a) * r });
/** Horizontal angle (radians, 0 = dead ahead, sign = to the right) of `target` as seen from `e`. */
export function bearing(e, target) {
  const f = forward(e), d = dirTo(e.location, target.location ?? target);
  return Math.atan2(f.x * d.z - f.z * d.x, f.x * d.x + f.z * d.z);
}

// ---- properties and state
export const dp = (e, k, d) => { try { const v = e.getDynamicProperty(k); return v === undefined ? d : v; } catch { return d; } };
export const setDp = (e, k, v) => { try { e.setDynamicProperty(k, v); } catch { } };
export const prop = (e, k, d) => { try { const v = e.getProperty(k); return v === undefined ? d : v; } catch { return d; } };
export const setProp = (e, k, v) => { try { e.setProperty(k, v); } catch (err) { warn(`setProperty ${k}=${v}`, err); } };
export const trigger = (e, ev) => { try { e.triggerEvent(ev); } catch { } };
export const ready = (e, key) => now() >= dp(e, key, 0);
export const wait = (e, key, ticks) => setDp(e, key, now() + ticks);

// ---- entities
export const effect = (e, id, ticks, amp = 0) => { try { e.addEffect(id, Math.round(ticks), { amplifier: amp, showParticles: false }); } catch { } };
export const clearEffect = (e, id) => { try { e.removeEffect(id); } catch { } };
export const byId = (id) => { if (!id) return undefined; try { const e = world.getEntity(id); return valid(e) ? e : undefined; } catch { return undefined; } };
export const hurt = (v, amount, src, cause = "entityAttack") => {
  try { v.applyDamage(amount, src && valid(src) ? { cause, damagingEntity: src } : { cause }); } catch { }
};
export const push = (v, dir, strength, up) => {
  const l = Math.hypot(dir.x, dir.z) || 1;
  try { v.applyKnockback(dir.x / l, dir.z / l, strength, up); } catch { }
};
export const isPlayer = (e) => e?.typeId === "minecraft:player";
export const isLiving = (e) => { try { return !!e.getComponent("minecraft:health"); } catch { return false; } };
export const isCreative = (p) => {
  try {
    if (typeof p.getGameMode === "function") { const gm = String(p.getGameMode()).toLowerCase(); return gm === "creative" || gm === "spectator"; }
    return !!(p.matches?.({ gameMode: "creative" }) || p.matches?.({ gameMode: "spectator" }));
  } catch { return false; }
};
export const heldItem = (p) => {
  try {
    const slot = p.selectedSlotIndex ?? p.selectedSlot;
    return p.getComponent("minecraft:inventory")?.container?.getItem(slot)?.typeId;
  } catch { return undefined; }
};
export const wearsArmor = (p) => {
  try {
    const eq = p.getComponent("minecraft:equippable");
    return ["Head", "Chest", "Legs", "Feet"].some((slot) => !!eq?.getEquipment(slot));
  } catch { return false; }
};
export const ridingOn = (p) => { try { return p.getComponent("minecraft:riding")?.entityRidingOn; } catch { return undefined; } };
export const riders = (e) => { try { return e.getComponent("minecraft:rideable")?.getRiders?.() ?? []; } catch { return []; } };
export const isBoat = (e) => e?.typeId === "minecraft:boat" || e?.typeId === "minecraft:chest_boat";
/** A living thing a creature may hunt: not one of the add-on's own, not a bystander, not a creative player. */
export const isPrey = (e, holds) => valid(e) && !NOT_PREY.has(e.typeId) && isLiving(e) && !(isPlayer(e) && isCreative(e)) && !holds?.(e);

export const playersNear = (dim, loc, r) => { try { return dim.getPlayers({ location: loc, maxDistance: r }); } catch { return []; } };
export const near = (dim, loc, r, type) => {
  try { return dim.getEntities(type ? { location: loc, maxDistance: r, type } : { location: loc, maxDistance: r }); } catch { return []; }
};
export const nearestPlayer = (e, maxR, filter = () => true) => {
  let best, bd = Infinity;
  for (const p of playersNear(e.dimension, e.location, maxR)) {
    if (isCreative(p) || !filter(p)) continue;
    const d = flat(p.location, e.location);
    if (d < bd) { best = p; bd = d; }
  }
  return best;
};

// ---- world
export const block = (dim, loc) => { try { return dim.getBlock({ x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) }); } catch { return undefined; } };
export const isWater = (b) => !!b && (b.typeId === "minecraft:water" || b.typeId === "minecraft:flowing_water");
export const isAir = (b) => !b || b.typeId === "minecraft:air";
export const timeOfDay = () => { try { return world.getTimeOfDay(); } catch { return 6000; } };
export const isNight = () => { const t = timeOfDay(); return t >= 13000 && t < 23000; };
export const runCommand = (dim, cmd) => { try { dim.runCommandAsync(cmd); } catch { } };
export function waterSurfaceNear(dim, loc) {
  for (let dy = 8; dy >= -12; dy--) {
    const p = { x: loc.x, y: Math.floor(loc.y) + dy, z: loc.z };
    if (isWater(block(dim, p)) && isAir(block(dim, add(p, { x: 0, y: 1, z: 0 })))) return { x: p.x, y: p.y + 0.9, z: p.z };
  }
  return undefined;
}
