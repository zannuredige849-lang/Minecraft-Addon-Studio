// Minimal in-memory stand-in for @minecraft/server, enough to execute the add-on's scripts in Node.
// Terrain: flat solid ground with its top block at y=64 everywhere (so every spot is "safe").
export const log = { commands: [], messages: [], camera: [], teleports: [], titles: [], errors: [] };
const tasks = [];
export const system = {
  currentTick: 0,
  runInterval(fn, n = 1) { const t = { fn, at: this.currentTick + n, every: n }; tasks.push(t); return t; },
  runTimeout(fn, n = 1) { const t = { fn, at: this.currentTick + Math.max(1, n) }; tasks.push(t); return t; },
  clearRun(t) { const i = tasks.indexOf(t); if (i >= 0) tasks.splice(i, 1); },
};
export async function advance(n) {
  for (let i = 0; i < n; i++) {
    system.currentTick++;
    const due = tasks.filter((t) => t.at <= system.currentTick);
    for (const t of due) {
      try { t.fn(); } catch (e) { log.errors.push(String(e && e.stack || e)); }
      if (t.every) t.at = system.currentTick + t.every; else tasks.splice(tasks.indexOf(t), 1);
    }
    await Promise.resolve(); await Promise.resolve();
  }
}
export const EasingType = new Proxy({}, { get: (_, k) => k });
export class ItemStack { constructor(typeId, amount = 1) { this.typeId = typeId; this.amount = amount; this.maxAmount = 64; } }

class Signal { constructor() { this.h = []; } subscribe(f) { this.h.push(f); return f; } unsubscribe(f) { this.h = this.h.filter((x) => x !== f); } fire(ev) { for (const f of this.h) f(ev); } }
const afterEvents = new Proxy({}, { get: (o, k) => (o[k] ??= new Signal()) });
const beforeEvents = new Proxy({}, { get: (o, k) => (o[k] ??= new Signal()) });

const blockAt = (dim, l) => {
  const y = Math.floor(l.y);
  const typeId = dim.overrides.get(`${Math.floor(l.x)},${y},${Math.floor(l.z)}`) ?? (y <= 64 ? (y === 64 ? "minecraft:grass_block" : "minecraft:stone") : "minecraft:air");
  return { typeId, location: { x: Math.floor(l.x), y, z: Math.floor(l.z) }, isAir: typeId === "minecraft:air", isLiquid: typeId.includes("water") };
};
let nextId = 1;
class Container {
  constructor(size) { this.size = size; this.items = new Array(size).fill(undefined); }
  get emptySlotsCount() { return this.items.filter((x) => !x).length; }
  addItem(s) { const i = this.items.findIndex((x) => !x); if (i < 0) return s; this.items[i] = s; return undefined; }
  getItem(i) { return this.items[i]; }
  setItem(i, s) { this.items[i] = s; }
}
export class Entity {
  constructor(typeId, loc, dim) {
    this.typeId = typeId; this.id = String(nextId++); this.location = { ...loc }; this.dimension = dim; this.props = new Map();
    this.dyn = new Map(); this.tags = new Set(); this.effects = new Map(); this.nameTag = ""; this._valid = true; this.isOnGround = true;
  }
  isValid() { return this._valid; }
  getDynamicProperty(k) { return this.dyn.get(k); } setDynamicProperty(k, v) { if (v === undefined) this.dyn.delete(k); else this.dyn.set(k, v); }
  getProperty(k) { return this.props.get(k); } setProperty(k, v) { this.props.set(k, v); }
  addTag(t) { this.tags.add(t); return true; } hasTag(t) { return this.tags.has(t); } removeTag(t) { return this.tags.delete(t); } getTags() { return [...this.tags]; }
  addEffect(id, d, o) { this.effects.set(String(id), d); } removeEffect(id) { this.effects.delete(String(id)); } getEffect(id) { return this.effects.get(id); }
  teleport(l, o = {}) { this.location = { ...l }; if (o.dimension) this.dimension = o.dimension; log.teleports.push([this.name ?? this.typeId, { ...l }]); }
  remove() { this._valid = false; const i = this.dimension.entities.indexOf(this); if (i >= 0) this.dimension.entities.splice(i, 1); }
  triggerEvent(e) { } applyImpulse() { } applyKnockback() { } clearVelocity() { } applyDamage() { return true; }
  getVelocity() { return { x: 0, y: 0, z: 0 }; } getViewDirection() { return { x: 0, y: 0, z: 1 }; } getRotation() { return { x: 0, y: 0 }; }
  getComponent(id) {
    if (id === "minecraft:health" || id === "health") return { currentValue: 20, defaultValue: 20, setCurrentValue() { } };
    if (id === "minecraft:inventory" || id === "inventory") return (this._inv ??= { container: new Container(36) });
    return undefined;
  }
  matches() { return false; }
  runCommandAsync(c) { log.commands.push([this.name ?? this.typeId, c]); return Promise.resolve({ successCount: 1 }); }
  runCommand(c) { log.commands.push([this.name ?? this.typeId, c]); return { successCount: 1 }; }
}
export class Player extends Entity {
  constructor(name, dim) {
    super("minecraft:player", { x: 0.5, y: 65, z: 3.5 }, dim); this.name = name; this.level = 0; this.isSneaking = false; this.selectedSlotIndex = 0;
    const self = this;
    this.camera = {
      fade(o) { log.camera.push([self.name, "fade", o]); }, setCamera(p, o) { log.camera.push([self.name, "set", p, o?.location]); }, clear() { log.camera.push([self.name, "clear"]); },
    };
    this.onScreenDisplay = { setActionBar(m) { self.actionbar = m; }, setTitle(m, o) { log.titles.push([self.name, m]); } };
    this.inbox = [];
  }
  sendMessage(m) { this.inbox.push(m); log.messages.push([this.name, m]); }
  playSound() { } addLevels(n) { this.level += n; } getGameMode() { return "survival"; }
}
class Dimension {
  constructor(id) { this.id = id; this.entities = []; this.overrides = new Map(); }
  getBlock(l) { return blockAt(this, l); }
  getEntities(q = {}) {
    return this.entities.filter((e) => e.isValid() && (!q.type || e.typeId === q.type) && (!q.tags || q.tags.every((t) => e.hasTag(t)))
      && (!q.families) && (!q.location || Math.hypot(e.location.x - q.location.x, e.location.y - q.location.y, e.location.z - q.location.z) <= (q.maxDistance ?? 1e9)));
  }
  getPlayers(q = {}) { return world.getAllPlayers().filter((p) => p.dimension === this && (!q.location || Math.hypot(p.location.x - q.location.x, p.location.y - q.location.y, p.location.z - q.location.z) <= (q.maxDistance ?? 1e9))); }
  spawnEntity(t, l) { const e = new Entity(t, l, this); this.entities.push(e); afterEvents.entitySpawn.fire({ entity: e }); return e; }
  spawnParticle() { }
  runCommandAsync(c) { log.commands.push(["dim", c]); return Promise.resolve({ successCount: 1 }); }
  runCommand(c) { log.commands.push(["dim", c]); return { successCount: 1 }; }
}
const dims = new Map(["minecraft:overworld", "minecraft:nether", "minecraft:the_end"].map((d) => [d, new Dimension(d)]));
const players = [];
const wdyn = new Map();
export const world = {
  afterEvents, beforeEvents,
  getDimension: (id) => dims.get(id.startsWith("minecraft:") ? id : "minecraft:" + id),
  getAllPlayers: () => players.filter((p) => p.isValid()),
  getPlayers: () => players.filter((p) => p.isValid()),
  getEntity: (id) => [...dims.values()].flatMap((d) => d.entities).find((e) => e.id === id) ?? players.find((p) => p.id === id),
  getDynamicProperty: (k) => wdyn.get(k), setDynamicProperty: (k, v) => { if (v === undefined) wdyn.delete(k); else wdyn.set(k, v); },
  getTimeOfDay: () => 6000, getAbsoluteTime: () => system.currentTick, sendMessage: (m) => log.messages.push(["*", m]),
};
// ---- harness helpers
export function join(name) {
  const p = new Player(name, dims.get("minecraft:overworld")); players.push(p);
  afterEvents.playerJoin.fire({ playerId: p.id, playerName: name });
  afterEvents.playerSpawn.fire({ player: p, initialSpawn: true });
  return p;
}
export function leave(p) { p._valid = false; players.splice(players.indexOf(p), 1); afterEvents.playerLeave.fire({ playerId: p.id, playerName: p.name }); }
export function rejoin(p) { p._valid = true; players.push(p); afterEvents.playerSpawn.fire({ player: p, initialSpawn: true }); }
export const overworld = () => dims.get("minecraft:overworld");
export const fire = (name, ev) => afterEvents[name].fire(ev);
export const worldDyn = wdyn;
