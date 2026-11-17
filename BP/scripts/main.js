// The Odyssey (2026): the creatures' mechanics as shown in Christopher Nolan's film.
// @minecraft/server 1.11.0 (stable). Every risky API call is guarded so one failure never stops the loops.
import { world, system, ItemStack } from "@minecraft/server";

const DIMENSIONS = ["minecraft:overworld", "minecraft:nether", "minecraft:the_end"];
const SACRIFICE_BLOCKS = new Set(["minecraft:soul_sand", "minecraft:soul_soil", "minecraft:black_concrete_powder"]);
const SACRIFICE_VICTIMS = new Set(["minecraft:sheep"]);           // the film: "they sacrifice some sheep"
const NOT_PREY = new Set(["studio:scylla", "studio:charybdis", "studio:boulder", "studio:cyclops", "studio:circe_sister",
  "studio:trojan_horse", "studio:siren", "studio:tiresias", "studio:athena", "minecraft:item", "minecraft:xp_orb",
  "minecraft:arrow", "minecraft:armor_stand", "minecraft:painting", "minecraft:boat", "minecraft:chest_boat"]);

// ------------------------------------------------------------------ helpers
const now = () => system.currentTick;
const valid = (e) => { try { return !!e && (typeof e.isValid === "function" ? e.isValid() : e.isValid); } catch { return false; } };
const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z });
const sub = (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z });
const scale = (a, k) => ({ x: a.x * k, y: a.y * k, z: a.z * k });
const len = (a) => Math.hypot(a.x, a.y, a.z);
const flat = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);
const dp = (e, k, d) => { try { const v = e.getDynamicProperty(k); return v === undefined ? d : v; } catch { return d; } };
const setDp = (e, k, v) => { try { e.setDynamicProperty(k, v); } catch { } };
const prop = (e, k, d) => { try { const v = e.getProperty(k); return v === undefined ? d : v; } catch { return d; } };
const setProp = (e, k, v) => { try { e.setProperty(k, v); } catch { } };
const trigger = (e, ev) => { try { e.triggerEvent(ev); } catch { } };
const effect = (e, id, ticks, amp = 0) => { try { e.addEffect(id, ticks, { amplifier: amp, showParticles: false }); } catch { } };
const clearEffect = (e, id) => { try { e.removeEffect(id); } catch { } };
const byId = (id) => { if (!id) return undefined; try { const e = world.getEntity(id); return valid(e) ? e : undefined; } catch { return undefined; } };
const hurt = (v, amount, src, cause = "entityAttack") => {
  try { v.applyDamage(amount, src && valid(src) ? { cause, damagingEntity: src } : { cause }); } catch { }
};
const actionbar = (p, msg) => { try { p.onScreenDisplay.setActionBar(msg); } catch { } };
const tell = (p, msg) => { try { p.sendMessage(msg); } catch { } };
const isPlayer = (e) => e?.typeId === "minecraft:player";
const isLiving = (e) => { try { return !!e.getComponent("minecraft:health"); } catch { return false; } };
const isCreative = (p) => {
  try {
    if (typeof p.getGameMode === "function") { const gm = String(p.getGameMode()).toLowerCase(); return gm === "creative" || gm === "spectator"; }
    return !!(p.matches?.({ gameMode: "creative" }) || p.matches?.({ gameMode: "spectator" }));
  } catch { return false; }
};
const forward = (e) => {
  try { const v = e.getViewDirection(); const l = Math.hypot(v.x, v.z) || 1; return { x: v.x / l, y: 0, z: v.z / l }; }
  catch { return { x: 0, y: 0, z: 1 }; }
};
const right = (e) => { const f = forward(e); return { x: -f.z, y: 0, z: f.x }; };
const heldItem = (p) => {
  try {
    const slot = p.selectedSlotIndex ?? p.selectedSlot;
    return p.getComponent("minecraft:inventory")?.container?.getItem(slot)?.typeId;
  } catch { return undefined; }
};
const ridingOn = (p) => { try { return p.getComponent("minecraft:riding")?.entityRidingOn; } catch { return undefined; } };
const riders = (e) => { try { return e.getComponent("minecraft:rideable")?.getRiders?.() ?? []; } catch { return []; } };
const playersNear = (dim, loc, r) => { try { return dim.getPlayers({ location: loc, maxDistance: r }); } catch { return []; } };
const near = (dim, loc, r, type) => {
  try { return dim.getEntities(type ? { location: loc, maxDistance: r, type } : { location: loc, maxDistance: r }); } catch { return []; }
};
const entitiesOf = (type) => {
  const out = [];
  for (const id of DIMENSIONS) { try { out.push(...world.getDimension(id).getEntities({ type })); } catch { } }
  return out;
};
const sound = (dim, id, loc, pitch = 1, volume = 1) => {
  try { dim.runCommandAsync(`playsound ${id} @a ${loc.x.toFixed(1)} ${loc.y.toFixed(1)} ${loc.z.toFixed(1)} ${volume} ${pitch}`); } catch { }
};
const badParticles = new Set();
const particle = (dim, id, loc) => {
  if (badParticles.has(id)) return;
  try { dim.spawnParticle(id, loc); } catch { badParticles.add(id); }
};
const animate = (e, value, ticks) => {
  setProp(e, "studio:anim", value);
  if (ticks) system.runTimeout(() => { if (valid(e) && prop(e, "studio:anim") === value) setProp(e, "studio:anim", "none"); }, ticks);
};
const ready = (e, key) => now() >= dp(e, key, 0);
const wait = (e, key, ticks) => setDp(e, key, now() + ticks);
const later = (ticks, fn) => system.runTimeout(fn, ticks);
const block = (dim, loc) => { try { return dim.getBlock({ x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) }); } catch { return undefined; } };
const isWater = (b) => !!b && (b.typeId === "minecraft:water" || b.typeId === "minecraft:flowing_water");
const isAir = (b) => !b || b.typeId === "minecraft:air";
const isBoat = (e) => e?.typeId === "minecraft:boat" || e?.typeId === "minecraft:chest_boat";
const say = (dim, loc, r, msg) => { for (const p of playersNear(dim, loc, r)) tell(p, msg); };
const timeOfDay = () => { try { return world.getTimeOfDay(); } catch { return 6000; } };
const isNight = () => { const t = timeOfDay(); return t >= 13000 && t < 23000; };
const ringSpot = (center, r, a) => ({ x: center.x + Math.cos(a) * r, y: center.y, z: center.z + Math.sin(a) * r });
const nearestPlayer = (e, maxR, filter = () => true) => {
  let best, bd = Infinity;
  for (const p of playersNear(e.dimension, e.location, maxR)) {
    if (isCreative(p) || !filter(p)) continue;
    const d = flat(p.location, e.location);
    if (d < bd) { best = p; bd = d; }
  }
  return best;
};
const runCommand = (dim, cmd) => { try { dim.runCommandAsync(cmd); } catch { } };

// ------------------------------------------------------------------ holds: a victim pinned relative to its holder
const holds = new Map();
function startHold(victim, holder, ticks, offsetFn, opts = {}) {
  if (!valid(victim) || holds.has(victim.id)) return false;
  holds.set(victim.id, { victim, holder, until: now() + ticks, offsetFn, start: now(), ...opts });
  return true;
}
function tickHolds() {
  for (const [id, h] of holds) {
    const { victim, holder } = h;
    if (!valid(victim) || !valid(holder) || now() >= h.until) {
      holds.delete(id);
      if (valid(victim)) h.onRelease?.(victim, valid(holder) ? holder : undefined);
      continue;
    }
    try { victim.teleport(add(holder.location, h.offsetFn(holder, now() - h.start)), { keepVelocity: false }); } catch { }
    if (h.every && now() > h.start && (now() - h.start) % h.every === 0) h.onTick?.(victim, holder);
  }
}
const isHeld = (e) => holds.has(e.id);

// ------------------------------------------------------------------ the rock Polyphemus throws at the ship
const boulders = new Map();
const GRAVITY = 0.045;
function hurlBoulder(thrower, targetLoc, damage, height) {
  const start = add(thrower.location, add(scale(forward(thrower), 1.2), { x: 0, y: height, z: 0 }));
  const d = sub(targetLoc, start);
  const T = Math.max(14, Math.min(48, Math.hypot(d.x, d.z)));
  const vel = { x: d.x / T, y: (d.y + 0.5 * GRAVITY * T * T) / T, z: d.z / T };
  let e;
  try { e = thrower.dimension.spawnEntity("studio:boulder", start); } catch { return; }
  boulders.set(e.id, { e, vel, owner: thrower, damage, life: 140 });
}
function shatter(b, loc) {
  const dim = b.e.dimension;
  particle(dim, "minecraft:huge_explosion_emitter", loc);
  particle(dim, "minecraft:water_splash_particle", loc);
  sound(dim, "random.explode", loc, 0.7, 2);
  sound(dim, "random.splash", loc, 0.6, 2);
  for (const t of near(dim, loc, 4)) {
    if (t.id === b.e.id || (valid(b.owner) && t.id === b.owner.id) || t.typeId === "studio:boulder") continue;
    if (isBoat(t)) { try { t.remove(); } catch { } continue; }
    if (isPlayer(t) && isCreative(t)) continue;
    hurt(t, b.damage, b.owner);
  }
  try { b.e.remove(); } catch { }
}
function tickBoulders() {
  for (const [id, b] of boulders) {
    if (!valid(b.e)) { boulders.delete(id); continue; }
    b.vel.y -= GRAVITY;
    const next = add(b.e.location, b.vel);
    b.life--;
    let hit = b.life <= 0 || !isAir(block(b.e.dimension, next));
    if (!hit) {
      for (const t of near(b.e.dimension, next, 1.8)) {
        if (t.id !== b.e.id && !(valid(b.owner) && t.id === b.owner.id) && t.typeId !== "studio:boulder") { hit = true; break; }
      }
    }
    if (hit) { boulders.delete(id); shatter(b, next); continue; }
    try { b.e.teleport(next, { keepVelocity: false }); } catch { }
  }
}

// ================================================================== Polyphemus
// The film's 60 ft puppet, 6.5 blocks tall here. A shepherd with a flock; he traps and devours men, kicks and tramples them, and falls asleep;
// he is blinded in his sleep with a sharp fiery log and cries out to Poseidon. Blind, he feels his sheep's wool as they
// leave and the men slip out camouflaged in the flock. He plunges into the sea and throws a rock at the ship - and misses.
const CY_MOUTH_UP = 4.7, CY_MOUTH_FWD = 1.3, CY_REACH = 3.5, CY_STEP = 1.7;   // blocks, for a 6.5-block giant
const flockOf = (cy) => near(cy.dimension, cy.location, 48, "minecraft:sheep").filter((s) => dp(s, "studio:shepherd", "") === cy.id);
function initCyclops(cy) {
  if (dp(cy, "studio:init", false)) return;
  setDp(cy, "studio:init", true);
  for (let i = 0; i < 6; i++) {
    try {
      const s = cy.dimension.spawnEntity("minecraft:sheep", ringSpot(cy.location, 4 + (i % 2) * 2, (i / 6) * Math.PI * 2));
      s.addTag("studio:flock");
      setDp(s, "studio:shepherd", cy.id);
    } catch { }
  }
}
function wakeCyclops(cy) {
  trigger(cy, "studio:wake");
  trigger(cy, prop(cy, "studio:blind", false) ? "studio:blinded" : "studio:hunt");
}
function blindCyclops(cy) {
  trigger(cy, "studio:blinded");
  setDp(cy, "studio:last_combat", now());
  animate(cy, "cry", 100);
  sound(cy.dimension, "mob.ravager.roar", cy.location, 0.4, 4);
  sound(cy.dimension, "mob.warden.roar", cy.location, 0.5, 4);
  say(cy.dimension, cy.location, 128, "§bPolyphemus: §f\"Father Poseidon, they blinded me! Vengeance, father, vengeance for pain... Poseidon, vengeance for pain!\"");
  for (const p of playersNear(cy.dimension, cy.location, 64)) actionbar(p, "§7He is blind. He counts his sheep by feeling their wool — hide among the flock.");
  runCommand(cy.dimension, "weather thunder 6000");      // Poseidon answers: harsh sea conditions
}
function cyclopsGrab(cy, victim) {
  if (!ready(cy, "studio:next_grab") || isHeld(victim) || (isPlayer(victim) && isCreative(victim))) return;
  if (NOT_PREY.has(victim.typeId) || victim.typeId === "minecraft:sheep" || !isLiving(victim)) return;
  wait(cy, "studio:next_grab", 200);
  setDp(cy, "studio:last_combat", now());
  animate(cy, "grab", 60);
  effect(cy, "weakness", 62, 3);          // while he feeds, the bite is the damage
  if (isPlayer(victim)) actionbar(victim, "§4Polyphemus snatches you up and lifts you to his mouth...");
  startHold(victim, cy, 56, (h) => add(scale(forward(h), CY_MOUTH_FWD), { x: 0, y: CY_MOUTH_UP, z: 0 }), {
    onRelease: (v, h) => {
      sound(v.dimension, "mob.ravager.bite", v.location, 0.5, 3);
      if (h) { try { v.teleport(add(h.location, scale(forward(h), 1.6)), { keepVelocity: false }); } catch { } }
      hurt(v, 14, h);
    },
  });
}
let cyTick = 0;
function tickCyclops() {
  cyTick++;
  const hiddenNow = new Set();
  for (const cy of entitiesOf("studio:cyclops")) {
    initCyclops(cy);
    const dim = cy.dimension;
    const blind = prop(cy, "studio:blind", false);
    const state = prop(cy, "studio:state", "awake");
    if (state === "asleep") {
      if (cyTick % 4 === 0) sound(dim, "mob.ravager.ambient", cy.location, 0.25, 1.5);
      if (!isNight() || now() >= dp(cy, "studio:sleep_until", 0)) wakeCyclops(cy);
      continue;
    }
    if (isNight() && !blind && now() - dp(cy, "studio:last_combat", -9999) > 400) {
      trigger(cy, "studio:fall_asleep");
      setDp(cy, "studio:sleep_until", now() + 3600);
      continue;
    }
    // kicking and trampling underfoot
    let moving = false;
    try { const v = cy.getVelocity(); moving = Math.hypot(v.x, v.z) > 0.02; } catch { }
    if (moving) {
      for (const t of near(dim, cy.location, CY_STEP)) {
        if (t.id === cy.id || NOT_PREY.has(t.typeId) || !isLiving(t) || isHeld(t) || (isPlayer(t) && isCreative(t))) continue;
        if (t.typeId === "minecraft:sheep" || Math.abs(t.location.y - cy.location.y) > 1.5 || !ready(t, "studio:trampled")) continue;
        wait(t, "studio:trampled", 30);
        hurt(t, 8, cy);
      }
    }
    // camouflaged in the flock: once he is blind, men among his sheep go unnoticed
    if (blind) {
      const flock = flockOf(cy);
      for (const p of playersNear(dim, cy.location, 48)) {
        if (!flock.some((s) => flat(s.location, p.location) < 2.5)) continue;
        hiddenNow.add(p.id);
        try { p.addTag("studio:in_flock"); } catch { }
        if (cyTick % 4 === 0 && flat(p.location, cy.location) < 16) actionbar(p, "§7Polyphemus runs his hands over the wool of his sheep... he does not find you.");
      }
    }
    // he snatches men within reach
    const prey = nearestPlayer(cy, CY_REACH, (p) => !hiddenNow.has(p.id));
    if (prey) cyclopsGrab(cy, prey);
    // blind, he throws a rock at a boat he hears - and misses
    if (blind && ready(cy, "studio:next_throw")) {
      const boat = near(dim, cy.location, 48).find((b) => isBoat(b) && riders(b).length > 0);
      if (boat) {
        wait(cy, "studio:next_throw", 400);
        animate(cy, "throw", 18);
        const a = Math.random() * Math.PI * 2, miss = 5 + Math.random() * 4;     // beyond the 4-block blast
        const aim = add(boat.location, { x: Math.cos(a) * miss, y: 0, z: Math.sin(a) * miss });
        later(10, () => { if (valid(cy)) hurlBoulder(cy, aim, 16, 5.5); });
      }
    }
  }
  for (const p of world.getAllPlayers()) {
    try { if (!hiddenNow.has(p.id) && p.hasTag("studio:in_flock")) p.removeTag("studio:in_flock"); } catch { }
  }
}

// ================================================================== Laestrygonians
// Armoured giants of Telepylus. Odysseus asks an armoured child (already the size of a grown man) for hospitality and the
// child only laughs; asked again, the child screams and runs. The giants emerge from the fog in a coordinated attack:
// a glaive launches men into the trees and the air, maces crush men and ships, and they sink the smaller ships.
function alarmGiants(dim, loc, r = 56) { for (const g of near(dim, loc, r, "studio:laestrygonian")) trigger(g, "studio:alarm"); }
function tickLaestrygonians() {
  for (const g of entitiesOf("studio:laestrygonian")) {
    if (!ready(g, "studio:next_smash")) continue;
    const boat = near(g.dimension, g.location, 4.2).find(isBoat);
    if (!boat) continue;
    wait(g, "studio:next_smash", 40);
    animate(g, "smash", 20);
    later(10, () => {
      if (!valid(boat)) return;
      sound(boat.dimension, "random.break", boat.location, 0.6, 2);
      sound(boat.dimension, "random.splash", boat.location, 0.7, 2);
      particle(boat.dimension, "minecraft:water_splash_particle", boat.location);
      try { boat.remove(); } catch { }
    });
  }
}
function tickChildren() {
  for (const c of entitiesOf("studio:laestrygonian_child")) {
    const dim = c.dimension;
    if (!dp(c, "studio:init", false)) {
      setDp(c, "studio:init", true);
      if (!near(dim, c.location, 48, "studio:laestrygonian").length) {
        for (let i = 0; i < 3; i++) { try { dim.spawnEntity("studio:laestrygonian", ringSpot(c.location, 20 + i * 3, Math.random() * Math.PI * 2)); } catch { } }
      }
    }
    const phase = dp(c, "studio:phase", 0);
    if (phase === 0) {
      if (!nearestPlayer(c, 8)) continue;
      setDp(c, "studio:phase", 1);
      wait(c, "studio:phase_at", 60);
      animate(c, "laugh", 45);
      sound(dim, "mob.witch.celebrate", c.location, 1.7, 1.5);
      say(dim, c.location, 24, "§7You ask the armoured child for hospitality. The child only laughs at you.");
    } else if (phase === 1 && ready(c, "studio:phase_at")) {
      if (!nearestPlayer(c, 8)) { setDp(c, "studio:phase", 0); continue; }     // nobody asked again
      setDp(c, "studio:phase", 2);
      wait(c, "studio:phase_at", 2400);
      animate(c, "scream", 60);
      sound(dim, "mob.ghast.scream", c.location, 1.8, 3);
      say(dim, c.location, 48, "§7You ask again, more seriously. §cThe child screams and runs. Something enormous moves in the fog...");
      trigger(c, "studio:flee");
      alarmGiants(dim, c.location, 64);
    } else if (phase === 2 && ready(c, "studio:phase_at")) {
      setDp(c, "studio:phase", 0);
    }
  }
}

// ================================================================== Circe
// An aged witch in a cottage on Aeaea; her sister, whom she turned into a bird, lives with her, and the animals around
// the cottage were sailors. She feeds the starving men stew on condition that they leave their armour outside; pliable
// to her will, they are molded by her hands like clay into squealing pigs. Odysseus sees through her deception and grabs
// her sister; Circe stands down, claims she only made the men what they really are, turns them back, and tells him he
// must cross the river Oceanus into Hades to reach Ithaca.
function initCirce(c) {
  if (dp(c, "studio:init", false)) return;
  setDp(c, "studio:init", true);
  try {
    const bird = c.dimension.spawnEntity("studio:circe_sister", add(c.location, { x: 0, y: 1.6, z: 0 }));
    setDp(bird, "studio:owner", c.id);
    setDp(c, "studio:sister", bird.id);
  } catch { }
  for (let i = 0; i < 3; i++) {
    try { const pig = c.dimension.spawnEntity("minecraft:pig", ringSpot(c.location, 3 + i, i * 2.1)); pig.addTag("studio:island_animal"); } catch { }
  }
}
const wearsArmor = (p) => {
  try {
    const eq = p.getComponent("minecraft:equippable");
    return ["Head", "Chest", "Legs", "Feet"].some((slot) => !!eq?.getEquipment(slot));
  } catch { return false; }
};
const pliable = (p) => dp(p, "studio:pliable_until", 0) > now();
const CURSE_EFFECTS = [["invisibility", 0], ["slowness", 1], ["weakness", 1], ["mining_fatigue", 0]];
function curse(p) {
  setDp(p, "studio:pig_until", now() + 12000);
  for (const [id, amp] of CURSE_EFFECTS) effect(p, id, 12000, amp);
  tell(p, "§5Circe works your flesh and bones as a potter works clay. Your scream becomes a squeal.");
  sound(p.dimension, "mob.pig.death", p.location, 0.7, 2);
}
function endCurse(p, msg = true) {
  if (!dp(p, "studio:pig_until", 0)) return;
  setDp(p, "studio:pig_until", 0);
  for (const [id] of CURSE_EFFECTS) clearEffect(p, id);
  const pig = byId(dp(p, "studio:curse_pig", ""));
  if (pig) { try { pig.remove(); } catch { } }
  setDp(p, "studio:curse_pig", "");
  if (msg) actionbar(p, "§aYou are human again.");
}
function circeYield(c) {
  if (prop(c, "studio:yielded", false)) return;
  trigger(c, "studio:yield");
  setProp(c, "studio:yielded", true);
  for (const p of playersNear(c.dimension, c.location, 64)) endCurse(p);
  say(c.dimension, c.location, 32, "§5You grab Circe's sister. Circe stands down.");
  say(c.dimension, c.location, 32, "§5Circe: she only made your men what they really are — brutal and savage. Reluctantly, she turns them back.");
  say(c.dimension, c.location, 32, "§5To reach Ithaca, she tells you, you must cross the river Oceanus into Hades.");
  sound(c.dimension, "mob.witch.ambient", c.location, 0.8, 1.5);
}
let circeTick = 0;
function tickCirce() {
  circeTick++;
  for (const c of entitiesOf("studio:circe")) {
    initCirce(c);
    const bird = byId(dp(c, "studio:sister", ""));
    if (bird) {
      const r = right(c);
      let yaw = 0;
      try { yaw = c.getRotation().y; } catch { }
      try { bird.teleport(add(c.location, { x: r.x * 0.3, y: 1.62, z: r.z * 0.3 }), { keepVelocity: false, rotation: { x: 0, y: yaw } }); } catch { }
    }
    if (prop(c, "studio:yielded", false) || circeTick % 10 !== 0 || !ready(c, "studio:next_mold")) continue;
    const victim = nearestPlayer(c, 4, (p) => pliable(p) && !dp(p, "studio:pig_until", 0) && !isHeld(p));
    if (!victim) continue;
    wait(c, "studio:next_mold", 100);
    animate(c, "mold", 44);
    effect(victim, "darkness", 60);
    startHold(victim, c, 40, (h) => add(scale(forward(h), 1.2), { x: 0, y: 0.05, z: 0 }), {
      onRelease: (v) => { setDp(v, "studio:pliable_until", 0); curse(v); },
    });
  }
}
function tickCurses() {
  for (const p of world.getAllPlayers()) {
    const until = dp(p, "studio:pig_until", 0);
    if (!until) continue;
    if (now() >= until) { endCurse(p); continue; }
    let pig = byId(dp(p, "studio:curse_pig", ""));
    if (!pig) {
      try {
        pig = p.dimension.spawnEntity("minecraft:pig", p.location);
        pig.nameTag = p.name;
        pig.addTag("studio:curse_pig");
        setDp(pig, "studio:owner", p.id);
        setDp(p, "studio:curse_pig", pig.id);
      } catch { continue; }
    }
    let yaw = 0;
    try { yaw = p.getRotation().y; } catch { }
    try { pig.teleport(p.location, { keepVelocity: false, rotation: { x: 0, y: yaw } }); } catch { }
  }
  if (now() % 100 === 0) {
    for (const pig of entitiesOf("minecraft:pig")) {
      let tagged = false;
      try { tagged = pig.hasTag("studio:curse_pig"); } catch { }
      if (!tagged) continue;
      const owner = byId(dp(pig, "studio:owner", ""));
      if (!owner || !dp(owner, "studio:pig_until", 0)) { try { pig.remove(); } catch { } }
    }
  }
}

// ================================================================== the Sirens
// Barely seen: human silhouettes, distant and shrouded in mist, known by their song. The crew stop their ears with wax
// and the sound dulls away; Odysseus, tied to the mast, hears everything he could ever want and why he could never have it.
const SCALE = [0.5, 0.56, 0.63, 0.67, 0.75, 0.67, 0.56, 0.6];
function deaf(p) {
  const until = dp(p, "studio:deaf_until", 0);
  if (until && now() >= until) { setDp(p, "studio:deaf_until", 0); actionbar(p, "§eThe wax has worked loose. You can hear again."); return false; }
  return until > now();
}
let sirenTick = 0;
function tickSirens() {
  sirenTick++;
  for (const s of entitiesOf("studio:siren")) {
    const dim = s.dimension;
    for (let k = 0; k < 3; k++) {
      const a = Math.random() * Math.PI * 2;
      particle(dim, "minecraft:campfire_smoke_particle", add(s.location, { x: Math.cos(a) * 2.5, y: 0.2, z: Math.sin(a) * 2.5 }));
    }
    const listeners = playersNear(dim, s.location, 32).filter((p) => !isCreative(p));
    if (!listeners.length) continue;
    sound(dim, "note.flute", s.location, SCALE[(sirenTick + s.id.length) % SCALE.length], 3);
    for (const p of listeners) {
      if (deaf(p)) { actionbar(p, "§7Wax in your ears: the song is only a muffled hum."); continue; }
      effect(p, "nausea", 160);
      if (ridingOn(p)) {         // bound to the mast: he hears it all but cannot go to them
        effect(p, "slowness", 60, 3);
        actionbar(p, "§5Bound to the mast, you hear it all: everything you could ever want — and why you can never have it.");
        continue;
      }
      const d = sub(s.location, p.location); const l = Math.hypot(d.x, d.z) || 1;
      try { p.applyKnockback(d.x / l, d.z / l, 0.35 + (32 - l) / 60, 0.05); } catch { }
      actionbar(p, "§d♪ The Sirens' song draws you toward the rocks... ♪");
    }
  }
}

// ================================================================== Scylla and Charybdis
// Tiresias: "The Whirlpool in the sea takes all of your lives, the monster in the cliff only six." Scylla emerges from her
// cave, snatches six men from the deck and carries them off to devour them; Charybdis would swallow the ship whole.
function tickScylla() {
  for (const sc of entitiesOf("studio:scylla")) {
    if (!dp(sc, "studio:init", false)) { setDp(sc, "studio:init", true); spawnCharybdisNear(sc); }
    if (!ready(sc, "studio:next_snatch")) continue;
    const dim = sc.dimension;
    const prey = near(dim, sc.location, 15)
      .filter((t) => t.id !== sc.id && !NOT_PREY.has(t.typeId) && isLiving(t) && !isHeld(t) && !(isPlayer(t) && isCreative(t)))
      .sort((a, b) => len(sub(a.location, sc.location)) - len(sub(b.location, sc.location)))
      .slice(0, 6);
    if (!prey.length) continue;
    wait(sc, "studio:next_snatch", 600);
    animate(sc, "snatch", 90);
    sound(dim, "mob.ravager.roar", sc.location, 0.4, 4);
    say(dim, sc.location, 40, "§4Scylla's heads lunge out of the cliff and snatch their victims from the deck.");
    const f = forward(sc), r = right(sc);
    prey.forEach((v, i) => {
      sound(dim, "mob.ravager.bite", v.location, 0.6, 2);
      const side = (i - 2.5) * 1.6;
      startHold(v, sc, 90, (h, t) => {
        const k = Math.min(1, t / 30);
        const reach = 8 - 4 * k, up = 6 + 4 * k + Math.sin(t * 0.3 + i) * 0.5;
        return { x: f.x * reach + r.x * side, y: up, z: f.z * reach + r.z * side };
      }, {
        every: 20,
        onTick: (vv, h) => hurt(vv, 4, h),
        onRelease: (vv, h) => { if (h) { try { vv.teleport(add(h.location, scale(forward(h), 3)), { keepVelocity: false }); } catch { } } },
      });
    });
  }
}
function waterSurfaceNear(dim, loc) {
  for (let dy = 8; dy >= -12; dy--) {
    const p = { x: loc.x, y: Math.floor(loc.y) + dy, z: loc.z };
    if (isWater(block(dim, p)) && isAir(block(dim, add(p, { x: 0, y: 1, z: 0 })))) return { x: p.x, y: p.y + 0.9, z: p.z };
  }
  return undefined;
}
function spawnCharybdisNear(sc) {
  try {
    if (near(sc.dimension, sc.location, 80, "studio:charybdis").length) return;
    for (let i = 0; i < 8; i++) {
      const spot = waterSurfaceNear(sc.dimension, ringSpot(sc.location, 30, (i / 8) * Math.PI * 2));
      if (spot) { sc.dimension.spawnEntity("studio:charybdis", spot); return; }
    }
  } catch { }
}
let chTick = 0;
function tickCharybdis() {
  chTick++;
  for (const ch of entitiesOf("studio:charybdis")) {
    const dim = ch.dimension;
    if (!dp(ch, "studio:anchored", false)) {
      const spot = waterSurfaceNear(dim, ch.location) || ch.location;
      setDp(ch, "studio:anchored", true);
      setDp(ch, "studio:ax", spot.x); setDp(ch, "studio:ay", spot.y); setDp(ch, "studio:az", spot.z);
    }
    const c = { x: dp(ch, "studio:ax", ch.location.x), y: dp(ch, "studio:ay", ch.location.y), z: dp(ch, "studio:az", ch.location.z) };
    if (len(sub(ch.location, c)) > 0.4) { try { ch.teleport(c, { keepVelocity: false }); } catch { } }
    if (chTick % 2 === 0) {
      for (let k = 0; k < 4; k++) {
        const a = chTick * 0.7 + k * 1.57, r = 3 + k * 5;
        particle(dim, "minecraft:bubble_column_up_particle", { x: c.x + Math.cos(a) * r, y: c.y - 0.2, z: c.z + Math.sin(a) * r });
      }
    }
    for (const t of near(dim, c, 28)) {
      if (t.id === ch.id || t.typeId === "studio:charybdis" || t.typeId === "studio:scylla" || isHeld(t)) continue;
      if (isPlayer(t) && isCreative(t)) continue;
      const d = sub(c, t.location); const r = Math.hypot(d.x, d.z) || 0.01;
      const radial = { x: d.x / r, z: d.z / r }, swirl = { x: -d.z / r, z: d.x / r };
      const pull = 0.035 + 0.13 * (1 - r / 28);
      if (r < 5 && (isBoat(t) || t.typeId === "minecraft:item")) {
        particle(dim, "minecraft:water_splash_particle", t.location);
        sound(dim, "random.splash", t.location, 0.5, 2);
        try { t.remove(); } catch { }
        continue;
      }
      if (isPlayer(t)) {
        if (chTick % 2 !== 0) continue;
        const v = { x: radial.x * pull + swirl.x * 0.08, z: radial.z * pull + swirl.z * 0.08 };
        const vl = Math.hypot(v.x, v.z) || 1;
        try { t.applyKnockback(v.x / vl, v.z / vl, vl * 2.2, r < 5 ? -0.4 : 0); } catch { }
        if (chTick % 20 === 0) actionbar(t, "§3The sea is draining into Charybdis's throat!");
      } else {
        try { t.applyImpulse({ x: radial.x * pull + swirl.x * 0.08, y: r < 5 ? -0.08 : 0, z: radial.z * pull + swirl.z * 0.08 }); } catch { }
      }
      if (r < 4 && chTick % 10 === 0) hurt(t, 3, undefined, "drowning");
    }
  }
}

// ================================================================== Hades: the blood sacrifice
// Across the river Oceanus the dead rise from the black sand. Sinon's shade reproaches Odysseus; Agamemnon's shade tells of
// his murder; Tiresias rises and prophesies. Then the shades rapidly approaching are his unburied crew, who want him to
// join them in their shame - and they chase him out of the underworld.
function rise(e, ticks = 36) {
  trigger(e, "studio:rise");
  setProp(e, "studio:anim", "rise");
  later(ticks, () => { if (valid(e)) { setProp(e, "studio:anim", "none"); trigger(e, "studio:risen"); } });
}
function sinkAway(e, ticks = 40) {
  if (!valid(e)) return;
  setProp(e, "studio:anim", "sink");
  later(ticks, () => { if (valid(e)) { try { e.remove(); } catch { } } });
}
function summonDead(p) {
  if (!ready(p, "studio:next_sacrifice")) return;
  wait(p, "studio:next_sacrifice", 3600);
  const dim = p.dimension, here = p.location, f = forward(p), r = right(p);
  const spawn = (type, off, ev) => {
    try { const e = dim.spawnEntity(type, add(here, off)); if (ev) trigger(e, ev); rise(e); return e; } catch { return undefined; }
  };
  say(dim, here, 48, "§7The blood soaks into the black sand. The dead begin to rise.");
  const sinon = spawn("studio:shade", add(scale(f, 3), scale(r, -4)), "studio:as_sinon");
  const aga = spawn("studio:shade", add(scale(f, 3), scale(r, 4)), "studio:as_agamemnon");
  const tir = spawn("studio:tiresias", scale(f, 4));
  later(60, () => say(dim, here, 48, "§7Sinon's shade reproaches you for deceiving him — and reveals that Antinous manipulated him into taking his place in the Greek army."));
  later(140, () => say(dim, here, 48, "§7Agamemnon's shade reveals that Clytemnestra murdered him on his return, in revenge for sacrificing their daughter Iphigenia to Artemis for fair seas."));
  later(220, () => {
    if (valid(tir)) setProp(tir, "studio:anim", "speak");
    say(dim, here, 48, "§fTiresias: \"The Whirlpool in the sea takes all of your lives, the monster in the cliff only six.\"");
  });
  later(290, () => say(dim, here, 48, "§7Tiresias foretells that, by divine will, only you will return home — and that your men will die if they kill the cattle of Apollo."));
  later(350, () => {
    say(dim, here, 48, "§cThe shades rapidly approaching are your unburied crew. They want you to join them in their shame.");
    for (let i = 0; i < 6; i++) {
      const a = Math.atan2(-f.z, -f.x) + (i - 2.5) * 0.45;
      try {
        const s = dim.spawnEntity("studio:shade", ringSpot(here, 10 + (i % 2) * 2, a));
        trigger(s, "studio:as_crew");
        rise(s);
        later(1800, () => sinkAway(s));
      } catch { }
    }
  });
  later(400, () => { sinkAway(tir); sinkAway(sinon); sinkAway(aga); });
}

// ================================================================== Thrinacia: the cattle of Apollo
// The starving men kill one of Apollo's cattle; Zeus sends a storm that sinks their ship.
function godsStorm(p) {
  const dim = p.dimension;
  say(dim, p.location, 64, "§6You have killed one of the cattle of Apollo. Zeus sends a storm.");
  runCommand(dim, "weather thunder 6000");
  for (let i = 1; i <= 10; i++) {
    later(i * 60, () => {
      if (!valid(p)) return;
      const a = Math.random() * Math.PI * 2, d = 3 + Math.random() * 6;
      const at = add(p.location, { x: Math.cos(a) * d, y: 0, z: Math.sin(a) * d });
      try { p.dimension.spawnEntity("minecraft:lightning_bolt", at); } catch { }
      const ride = ridingOn(p);
      for (const b of near(p.dimension, p.location, 24)) {
        if (isBoat(b) && (b.id === ride?.id || flat(b.location, at) < 8)) { try { b.remove(); } catch { } }
      }
    });
  }
}

// ================================================================== the Trojan Horse: the Greeks hide inside
function tickHorses() {
  for (const p of world.getAllPlayers()) {
    if (ridingOn(p)?.typeId === "studio:trojan_horse") effect(p, "invisibility", 60);
  }
}

// ================================================================== events
world.afterEvents.entityHitEntity.subscribe(({ damagingEntity: a, hitEntity: v }) => {
  if (!valid(a) || !valid(v)) return;
  if (a.typeId === "studio:cyclops") { setDp(a, "studio:last_combat", now()); cyclopsGrab(a, v); return; }
  if (a.typeId === "studio:laestrygonian") {
    animate(a, "swing", 16);
    if (prop(a, "studio:weapon", 0) === 1) {   // the glaive launches men into the trees and the air
      const d = sub(v.location, a.location); const l = Math.hypot(d.x, d.z) || 1;
      try { v.applyKnockback(d.x / l, d.z / l, 2.2, 1.2); } catch { }
    }
  }
});

world.afterEvents.entityHurt.subscribe(({ hurtEntity: v, damageSource }) => {
  const src = damageSource?.damagingEntity;
  if (!valid(v)) return;
  if (v.typeId === "studio:cyclops") {
    setDp(v, "studio:last_combat", now());
    if (!isPlayer(src)) return;
    const state = prop(v, "studio:state", "awake"), blind = prop(v, "studio:blind", false);
    if (state === "asleep" && !blind && heldItem(src) === "studio:burning_stake") blindCyclops(v);
    else if (state === "asleep") wakeCyclops(v);
    return;
  }
  if (v.typeId === "studio:laestrygonian" && isPlayer(src)) alarmGiants(v.dimension, v.location);
  if (v.typeId === "studio:laestrygonian_child" && isPlayer(src)) { trigger(v, "studio:flee"); alarmGiants(v.dimension, v.location, 64); }
});

world.afterEvents.entityDie.subscribe(({ deadEntity: e, damageSource }) => {
  const killer = damageSource?.damagingEntity;
  if (isPlayer(e)) { endCurse(e, false); try { e.removeTag("studio:in_flock"); } catch { } return; }
  if (!isPlayer(killer)) return;
  const type = e?.typeId;
  if (type === "studio:sun_cattle") { godsStorm(killer); return; }
  if (SACRIFICE_VICTIMS.has(type)) {
    const under = block(killer.dimension, add(killer.location, { x: 0, y: -0.5, z: 0 }));
    if (under && SACRIFICE_BLOCKS.has(under.typeId)) summonDead(killer);
  }
});

world.afterEvents.dataDrivenEntityTrigger.subscribe((ev) => {
  const e = ev.entity, id = ev.eventId ?? ev.id;
  if (!valid(e)) return;
  if (e.typeId === "studio:circe" && id === "studio:offer_stew") {
    const p = nearestPlayer(e, 6);
    if (!p) return;
    if (wearsArmor(p)) { tell(p, "§5Circe will feed you — on condition that you leave your armour outside."); return; }
    try { e.dimension.spawnItem(new ItemStack("studio:circe_stew", 1), p.location); } catch { }
    tell(p, "§5Circe sets a bowl of stew before you.");
  } else if (e.typeId === "studio:circe" && id === "studio:counsel") {
    const p = nearestPlayer(e, 6);
    if (p) tell(p, "§5Circe: to reach Ithaca, you must cross the river Oceanus into Hades.");
  } else if (e.typeId === "studio:circe_sister" && id === "studio:seized") {
    const c = byId(dp(e, "studio:owner", ""));
    if (c) circeYield(c);
  } else if (e.typeId === "studio:calypso" && id === "studio:offer_lotus") {
    const p = nearestPlayer(e, 6);
    if (!p || !ready(p, "studio:next_lotus")) return;
    wait(p, "studio:next_lotus", 1200);
    try { e.dimension.spawnItem(new ItemStack("studio:lotus_flower", 1), p.location); } catch { }
    tell(p, "§bCalypso offers you a lotus flower.");
  } else if (e.typeId === "studio:athena" && id === "studio:bless") {
    later(40, () => { if (valid(e)) setProp(e, "studio:anim", "none"); });
    const p = nearestPlayer(e, 6);
    if (!p || !ready(p, "studio:next_blessing")) return;
    wait(p, "studio:next_blessing", 12000);
    effect(p, "resistance", 4800, 0);
    tell(p, "§fAthena commands you to return home. You feel her protection settle over you.");
  }
});

world.afterEvents.itemCompleteUse.subscribe(({ source: p, itemStack }) => {
  const id = itemStack?.typeId;
  if (!isPlayer(p)) return;
  if (id === "studio:beeswax") {
    setDp(p, "studio:deaf_until", now() + 6000);
    actionbar(p, "§eYou press soft wax into your ears. The sound dulls away.");
  } else if (id === "studio:circe_stew") {
    setDp(p, "studio:pliable_until", now() + 2400);
    actionbar(p, "§dYou devour the stew with a grotesque hunger... and feel strangely pliable.");
  } else if (id === "studio:lotus_flower") {
    try { p.addLevels(-p.level); } catch { }
    effect(p, "regeneration", 600, 0);
    effect(p, "slowness", 600, 0);
    actionbar(p, "§bA peaceful haze settles over you. Your memories slip away.");
  }
});

// ------------------------------------------------------------------ loops
system.runInterval(() => { tickHolds(); tickBoulders(); tickCurses(); }, 1);
system.runInterval(() => { tickCirce(); tickCharybdis(); }, 2);
system.runInterval(() => { tickCyclops(); tickLaestrygonians(); tickChildren(); tickScylla(); }, 10);
system.runInterval(() => { tickSirens(); }, 40);
system.runInterval(() => {
  tickHorses();
  for (const b of entitiesOf("studio:boulder")) if (!boulders.has(b.id)) { try { b.remove(); } catch { } }
}, 20);
