// A fake of the parts of @minecraft/server 1.11.0 that the add-on uses, strict where the real game is strict:
// property values are checked against the behaviour pack's entity definitions, events run the definitions' own
// set_property / component_groups, and a removed entity throws when it is touched.
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, dirname } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const DEFS = {};
for (const f of readdirSync(join(ROOT, "BP", "entities"))) {
  const d = JSON.parse(readFileSync(join(ROOT, "BP", "entities", f), "utf8"))["minecraft:entity"];
  DEFS[d.description.identifier] = d;
}

export const log = [];            // commands and notable calls, as text
export const sounds = [];         // { who, id, location, volume }
const subs = {};
const ev = (name) => ({ subscribe: (fn) => { (subs[name] ||= []).push(fn); return fn; }, unsubscribe() { } });
export const fire = (name, data) => (subs[name] || []).slice().forEach((fn) => fn(data));

// ------------------------------------------------------------------ time
let tick = 0, nextId = 1, timeOfDay = 6000;
export const setTime = (t) => { timeOfDay = t; };
const intervals = [], timeouts = [];
export const system = {
  get currentTick() { return tick; },
  runInterval: (fn, n) => { intervals.push({ fn, n, last: tick }); return intervals.length; },
  runTimeout: (fn, n) => { timeouts.push({ fn, at: tick + Math.max(1, n) }); return timeouts.length; },
};
export const runTicks = (n) => {
  for (let i = 0; i < n; i++) {
    tick++;
    for (const iv of intervals) if (tick - iv.last >= iv.n) { iv.last = tick; iv.fn(); }
    const due = timeouts.filter((t) => t.at <= tick);
    for (const t of due) timeouts.splice(timeouts.indexOf(t), 1);
    due.forEach((t) => t.fn());
  }
};
export const currentTick = () => tick;

export class ItemStack { constructor(typeId, amount = 1) { this.typeId = typeId; this.amount = amount; } }

// ------------------------------------------------------------------ entities
const entities = new Map();
const LIVING = new Set(["minecraft:player", "minecraft:pig", "minecraft:sheep", "minecraft:villager", "minecraft:cow", "minecraft:zombie"]);
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
const finite = (v) => Number.isFinite(v.x + v.y + v.z);

class Entity {
  constructor(typeId, loc, dim) {
    this.id = String(nextId++); this.typeId = typeId; this._loc = { ...loc }; this.dimension = dim;
    this.alive = true; this.dp = {}; this.props = {}; this.tags = new Set(); this.effects = {}; this.groups = new Set();
    this.nameTag = ""; this.events = []; this.vel = { x: 0, y: 0, z: 0 }; this.view = { x: 0, y: 0, z: 1 }; this.yaw = 0;
    const def = DEFS[typeId];
    this.def = def;
    const hp = def?.components?.["minecraft:health"]?.value;
    this.health = hp ?? 20;
    for (const [k, p] of Object.entries(def?.description?.properties ?? {})) this.props[k] = p.default;
    entities.set(this.id, this);
    if (typeId === "minecraft:player") {
      this.name = "Odysseus"; this.mode = "survival"; this.messages = []; this.level = 0; this.selectedSlotIndex = 0;
      this.held = undefined; this.armor = {}; this.inventory = []; this.ridingEntity = undefined; this.titles = [];
      this.onScreenDisplay = {
        setActionBar: (m) => this.messages.push({ bar: m }),
        setTitle: (t, o) => this.titles.push({ title: t, ...o }),
      };
    }
  }
  _chk() { if (!this.alive) throw new Error("Failed to access removed entity " + this.typeId); }
  get location() { this._chk(); return { ...this._loc }; }
  isValid() { return this.alive; }
  getDynamicProperty(k) { this._chk(); return this.dp[k]; }
  setDynamicProperty(k, v) { this._chk(); this.dp[k] = v; }
  getProperty(k) { this._chk(); return this.props[k]; }
  setProperty(k, v) {
    this._chk();
    const p = this.def?.description?.properties?.[k];
    if (!p) throw new Error(`unknown property ${k} on ${this.typeId}`);
    if (p.type === "enum" && !p.values.includes(v)) throw new Error(`${v} is not a value of ${k} on ${this.typeId}`);
    if (p.type === "bool" && typeof v !== "boolean") throw new Error(`${k} wants a bool`);
    if (p.type === "int" && !(Number.isInteger(v) && v >= p.range[0] && v <= p.range[1])) throw new Error(`${k}=${v} out of range`);
    this.props[k] = v;
  }
  triggerEvent(name) {
    this._chk();
    const def = this.def?.events?.[name];
    if (!def) throw new Error(`no event ${name} on ${this.typeId}`);
    this.events.push(name);
    this._apply(def);
  }
  _apply(def) {
    if (def.sequence) def.sequence.forEach((d) => this._apply(d));
    if (def.randomize) {
      const total = def.randomize.reduce((a, b) => a + b.weight, 0);
      let r = Math.random() * total;
      for (const o of def.randomize) { r -= o.weight; if (r <= 0) { this._apply(o); break; } }
    }
    for (const [k, v] of Object.entries(def.set_property ?? {})) this.setProperty(k, v);
    for (const g of def.add?.component_groups ?? []) this.groups.add(g);
    for (const g of def.remove?.component_groups ?? []) this.groups.delete(g);
  }
  addEffect(id, d, o) { this._chk(); this.effects[id] = { ticks: d, amp: o?.amplifier ?? 0, at: tick }; }
  removeEffect(id) { this._chk(); delete this.effects[id]; }
  hasEffect(id) { const e = this.effects[id]; return !!e && tick - e.at < e.ticks; }
  applyDamage(a, o) {
    this._chk();
    this.health -= a;
    log.push(`${this.typeId} took ${a} (${o?.cause})`);
    const damageSource = { cause: o?.cause, damagingEntity: o?.damagingEntity };
    fire("entityHurt", { hurtEntity: this, damage: a, damageSource });
    if (this.health <= 0 && this.alive) { fire("entityDie", { deadEntity: this, damageSource }); this.remove(); }
    return true;
  }
  applyKnockback(x, z, h, v) {
    this._chk();
    if (!Number.isFinite(x + z + h + v)) throw new Error("NaN knockback");
    this.vel = { x: x * h, y: v, z: z * h };
  }
  applyImpulse(v) { this._chk(); if (this.typeId === "minecraft:player") throw new Error("impulse on a player"); this.vel = { ...v }; }
  getVelocity() { this._chk(); return { ...this.vel }; }
  teleport(l) { this._chk(); if (!finite(l)) throw new Error("NaN teleport"); this._loc = { ...l }; }
  getViewDirection() { this._chk(); return { ...this.view }; }
  getRotation() { this._chk(); return { x: 0, y: this.yaw }; }
  remove() { this._chk(); this.alive = false; entities.delete(this.id); }
  hasTag(t) { this._chk(); return this.tags.has(t); }
  addTag(t) { this._chk(); this.tags.add(t); return true; }
  removeTag(t) { this._chk(); return this.tags.delete(t); }
  sendMessage(m) { this._chk(); this.messages.push(m); }
  runCommandAsync(c) { this._chk(); log.push(`cmd@${this.name ?? this.typeId} ${c}`); return Promise.resolve(); }
  playSound(id, o) { this._chk(); sounds.push({ who: this.name, id, location: o?.location, volume: o?.volume ?? 1 }); }
  getGameMode() { return this.mode; }
  addLevels(n) { this.level = Math.max(0, this.level + n); return this.level; }
  getComponent(c) {
    this._chk();
    const isPlayer = this.typeId === "minecraft:player";
    if (c === "minecraft:health") {
      const has = this.def ? !!this.def.components?.["minecraft:health"] : LIVING.has(this.typeId);
      return has ? { currentValue: this.health } : undefined;
    }
    if (c === "minecraft:inventory" && isPlayer) {
      return { container: {
        getItem: () => (this.held ? new ItemStack(this.held) : undefined),
        addItem: (s) => { this.inventory.push(s); return undefined; } } };
    }
    if (c === "minecraft:riding") return this.ridingEntity ? { entityRidingOn: this.ridingEntity } : undefined;
    if (c === "minecraft:rideable") {
      return { getRiders: () => [...entities.values()].filter((e) => e.ridingEntity === this),
               ejectRiders: () => { for (const e of entities.values()) if (e.ridingEntity === this) e.ridingEntity = undefined; } };
    }
    if (c === "minecraft:equippable" && isPlayer) return { getEquipment: (slot) => this.armor[slot] };
    return undefined;
  }
}

// ------------------------------------------------------------------ dimensions and the world
const blocks = new Map();
export const setBlock = (x, y, z, typeId) => blocks.set(`${x},${y},${z}`, typeId);
class Dimension {
  constructor(id) { this.id = id; }
  getEntities(o = {}) {
    return [...entities.values()].filter((e) => e.alive && e.dimension === this
      && (!o.type || e.typeId === o.type) && (!o.location || dist(e._loc, o.location) <= o.maxDistance)
      && (!o.tags || o.tags.every((t) => e.tags.has(t))));
  }
  getPlayers(o = {}) { return this.getEntities({ ...o, type: "minecraft:player" }); }
  spawnEntity(t, l) {
    if (!finite(l)) throw new Error("NaN spawn");
    if (!DEFS[t] && !LIVING.has(t) && !t.startsWith("minecraft:")) throw new Error(`unknown entity ${t}`);
    log.push(`spawn ${t}`);
    const e = new Entity(t, l, this);
    if (e.def?.events?.["minecraft:entity_spawned"]) e.triggerEvent("minecraft:entity_spawned");
    fire("entitySpawn", { entity: e });
    return e;
  }
  spawnItem(s) { log.push(`item ${s.typeId}`); }
  spawnParticle(id) { log.push(`particle ${id}`); }
  runCommandAsync(c) { log.push(`cmd ${c}`); return Promise.resolve(); }
  getBlock(l) {
    const k = `${Math.floor(l.x)},${Math.floor(l.y)},${Math.floor(l.z)}`;
    if (blocks.has(k)) return { typeId: blocks.get(k) };
    return { typeId: l.y < 62 ? "minecraft:water" : "minecraft:air" };
  }
}
const dims = { "minecraft:overworld": new Dimension("overworld"), "minecraft:nether": new Dimension("nether"), "minecraft:the_end": new Dimension("end") };
const worldDp = {};
export const world = {
  getDimension: (id) => dims[id],
  getAllPlayers: () => dims["minecraft:overworld"].getPlayers({}),
  getEntity: (id) => entities.get(id),
  getTimeOfDay: () => timeOfDay,
  getAbsoluteTime: () => tick,
  getDynamicProperty: (k) => worldDp[k],
  setDynamicProperty: (k, v) => { worldDp[k] = v; },
  afterEvents: { entitySpawn: ev("entitySpawn"), entityHitEntity: ev("entityHitEntity"), entityHurt: ev("entityHurt"),
    entityDie: ev("entityDie"), dataDrivenEntityTrigger: ev("dataDrivenEntityTrigger"), itemCompleteUse: ev("itemCompleteUse"),
    playerSpawn: ev("playerSpawn"), playerLeave: ev("playerLeave") },
};
export const spawn = (t, l, dimId = "minecraft:overworld") => dims[dimId].spawnEntity(t, l);
export const all = () => [...entities.values()];
export const clearAll = () => { for (const e of [...entities.values()]) e.alive = false; entities.clear(); };
export const forgetWorld = () => { for (const k of Object.keys(worldDp)) delete worldDp[k]; };
