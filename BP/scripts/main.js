// The Odyssey (2026) creatures: signature mechanics.
// @minecraft/server 1.11.0 (stable). Every risky API call is guarded so one failure never stops the loop.
import { world, system, ItemStack } from "@minecraft/server";

const DIMENSIONS = ["minecraft:overworld", "minecraft:nether", "minecraft:the_end"];
const HUMANOIDS = new Set([
  "minecraft:villager", "minecraft:villager_v2", "minecraft:wandering_trader", "minecraft:pillager",
  "minecraft:vindicator", "minecraft:evocation_illager", "minecraft:witch", "minecraft:zombie_villager",
  "minecraft:zombie_villager_v2", "minecraft:zombie", "minecraft:husk", "minecraft:drowned", "minecraft:piglin",
]);
const NOT_PREY = new Set(["studio:scylla", "studio:charybdis", "studio:boulder", "minecraft:item", "minecraft:xp_orb",
  "minecraft:arrow", "minecraft:boat", "minecraft:chest_boat", "minecraft:painting", "minecraft:armor_stand"]);

// ------------------------------------------------------------------ helpers
const now = () => system.currentTick;
const valid = (e) => { try { return !!e && (typeof e.isValid === "function" ? e.isValid() : e.isValid); } catch { return false; } };
const sub = (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z });
const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z });
const scale = (a, k) => ({ x: a.x * k, y: a.y * k, z: a.z * k });
const len = (a) => Math.hypot(a.x, a.y, a.z);
const flatDist = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);
const dp = (e, k, d) => { try { const v = e.getDynamicProperty(k); return v === undefined ? d : v; } catch { return d; } };
const setDp = (e, k, v) => { try { e.setDynamicProperty(k, v); } catch { } };
const prop = (e, k, d) => { try { return e.getProperty(k); } catch { return d; } };
const setProp = (e, k, v) => { try { e.setProperty(k, v); } catch { } };
const trigger = (e, ev) => { try { e.triggerEvent(ev); } catch { } };
const effect = (e, id, ticks, amp = 0) => { try { e.addEffect(id, ticks, { amplifier: amp, showParticles: false }); } catch { } };
const clearEffect = (e, id) => { try { e.removeEffect(id); } catch { } };
const hurt = (victim, amount, source, cause = "entityAttack") => {
  try { victim.applyDamage(amount, source && valid(source) ? { cause, damagingEntity: source } : { cause }); } catch { }
};
const actionbar = (p, msg) => { try { p.onScreenDisplay.setActionBar(msg); } catch { } };
const tell = (p, msg) => { try { p.sendMessage(msg); } catch { } };
const forward = (e) => { try { const v = e.getViewDirection(); const l = Math.hypot(v.x, v.z) || 1; return { x: v.x / l, y: 0, z: v.z / l }; } catch { return { x: 0, y: 0, z: 1 }; } };
const isPlayer = (e) => e?.typeId === "minecraft:player";
const isLiving = (e) => { try { return !!e.getComponent("minecraft:health"); } catch { return false; } };
const isCreative = (p) => {
  try {
    if (typeof p.getGameMode === "function") { const gm = String(p.getGameMode()).toLowerCase(); return gm === "creative" || gm === "spectator"; }
    return !!(p.matches?.({ gameMode: "creative" }) || p.matches?.({ gameMode: "spectator" }));
  } catch { return false; }
};
const heldItem = (p) => {
  try {
    const slot = p.selectedSlotIndex ?? p.selectedSlot;
    return p.getComponent("minecraft:inventory")?.container?.getItem(slot)?.typeId;
  } catch { return undefined; }
};
const isRiding = (p) => { try { return !!p.getComponent("minecraft:riding")?.entityRidingOn; } catch { return false; } };
const playersNear = (dim, loc, r) => { try { return dim.getPlayers({ location: loc, maxDistance: r }); } catch { return []; } };
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
const timerReady = (e, key) => now() >= dp(e, key, 0);
const setTimer = (e, key, ticks) => setDp(e, key, now() + ticks);
const block = (dim, loc) => { try { return dim.getBlock({ x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) }); } catch { return undefined; } };
const isWater = (b) => !!b && (b.typeId === "minecraft:water" || b.typeId === "minecraft:flowing_water");
const isAir = (b) => !b || b.typeId === "minecraft:air";
const nearestPlayer = (e, maxR, minR = 0, filter = () => true) => {
  let best, bd = Infinity;
  for (const p of playersNear(e.dimension, e.location, maxR)) {
    if (isCreative(p) || !filter(p)) continue;
    const d = len(sub(p.location, e.location));
    if (d >= minR && d < bd) { best = p; bd = d; }
  }
  return best;
};

// ------------------------------------------------------------------ holds (grab, snatch, mold)
// A hold pins a victim to a point relative to its holder every tick, then releases it.
const holds = new Map(); // victimId -> hold
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
    if (h.every && (now() - h.start) % h.every === 0 && now() > h.start) h.onTick?.(victim, holder);
  }
}
const isHeld = (e) => holds.has(e.id);

// ------------------------------------------------------------------ boulders (Polyphemus & Laestrygonians)
const boulders = new Map(); // id -> { e, vel, owner, damage, life }
const GRAVITY = 0.045;
function hurlBoulder(thrower, targetLoc, damage) {
  const start = add(thrower.location, add(scale(forward(thrower), 1.5), { x: 0, y: 3.4, z: 0 }));
  const d = sub(targetLoc, start);
  const flat = Math.hypot(d.x, d.z);
  const T = Math.max(12, Math.min(40, flat / 0.9));
  const vel = { x: d.x / T, y: (d.y + 0.5 * GRAVITY * T * T) / T, z: d.z / T };
  let e;
  try { e = thrower.dimension.spawnEntity("studio:boulder", start); } catch { return; }
  boulders.set(e.id, { e, vel, owner: thrower, damage, life: 120 });
  sound(thrower.dimension, "mob.ravager.roar", thrower.location, 0.6, 1.5);
}
function shatter(b, loc) {
  const dim = b.e.dimension;
  particle(dim, "minecraft:huge_explosion_emitter", loc);
  sound(dim, "random.explode", loc, 0.7, 1.2);
  for (const t of dim.getEntities({ location: loc, maxDistance: 3.2 })) {
    if (t.id === b.e.id || (valid(b.owner) && t.id === b.owner.id)) continue;
    if (t.typeId === "minecraft:boat" || t.typeId === "minecraft:chest_boat") {
      // The Laestrygonians sank Odysseus's ships with thrown rocks.
      particle(dim, "minecraft:water_splash_particle", t.location);
      sound(dim, "random.splash", t.location, 0.8, 1.5);
      try { t.remove(); } catch { }
      continue;
    }
    if (t.typeId === "studio:boulder" || (isPlayer(t) && isCreative(t))) continue;
    hurt(t, b.damage, b.owner, "entityAttack");
    try { const k = sub(t.location, loc); const l = Math.hypot(k.x, k.z) || 1; t.applyKnockback(k.x / l, k.z / l, 1.1, 0.45); } catch { }
  }
  try { b.e.remove(); } catch { }
}
function tickBoulders() {
  for (const [id, b] of boulders) {
    if (!valid(b.e)) { boulders.delete(id); continue; }
    b.vel.y -= GRAVITY;
    const next = add(b.e.location, b.vel);
    b.life--;
    const blk = block(b.e.dimension, next);
    let hit = b.life <= 0 || (!isAir(blk) && !isWater(blk));
    if (!hit && isWater(blk)) hit = true;
    if (!hit) {
      for (const t of b.e.dimension.getEntities({ location: next, maxDistance: 1.8 })) {
        if (t.id === b.e.id || (valid(b.owner) && t.id === b.owner.id) || t.typeId === "studio:boulder") continue;
        hit = true; break;
      }
    }
    if (hit) { boulders.delete(id); shatter(b, next); continue; }
    try { b.e.teleport(next, { keepVelocity: false }); } catch { }
  }
}

// ------------------------------------------------------------------ Polyphemus
function initCyclops(cy) {
  if (dp(cy, "studio:init", false)) return;
  setDp(cy, "studio:init", true);
  // The shepherd and his flock.
  for (let i = 0; i < 4; i++) {
    const a = (i / 4) * Math.PI * 2;
    try {
      const sheep = cy.dimension.spawnEntity("minecraft:sheep", add(cy.location, { x: Math.cos(a) * 3, y: 0.5, z: Math.sin(a) * 3 }));
      sheep.addTag("studio:flock");
      setDp(sheep, "studio:shepherd", cy.id);
    } catch { }
  }
}
function angerCyclops(cy) {
  if (!valid(cy) || prop(cy, "studio:blind", false)) return;
  setDp(cy, "studio:angry", true);
  if (prop(cy, "studio:state", "awake") === "awake") trigger(cy, "studio:anger");
}
function wakeCyclops(cy) {
  trigger(cy, "studio:wake");
  if (prop(cy, "studio:blind", false)) trigger(cy, "studio:blinded");
  else if (dp(cy, "studio:angry", false)) trigger(cy, "studio:anger");
}
function blindCyclops(cy, player) {
  trigger(cy, "studio:blinded");
  setDp(cy, "studio:angry", true);
  animate(cy, "cry", 80);
  const dim = cy.dimension, loc = cy.location;
  sound(dim, "mob.warden.roar", loc, 0.6, 3);
  sound(dim, "mob.ravager.roar", loc, 0.5, 3);
  for (const p of playersNear(dim, loc, 64)) {
    tell(p, "§b\"Nobody has blinded me! Nobody is killing me!\"§7 — Polyphemus screams to his father, Poseidon.");
    actionbar(p, "§7He is blind now. He hunts by sound — §fsneak§7 to slip past him.");
  }
  // Poseidon answers his son.
  try { dim.runCommandAsync("weather thunder 3600"); } catch { }
  system.runTimeout(() => {
    if (!valid(player)) return;
    for (let i = 0; i < 2; i++) {
      const off = { x: (Math.random() - 0.5) * 10, y: 0, z: (Math.random() - 0.5) * 10 };
      try { player.dimension.spawnEntity("minecraft:lightning_bolt", add(player.location, off)); } catch { }
    }
  }, 40);
}
function cyclopsGrab(cy, victim) {
  if (!timerReady(cy, "studio:next_grab") || isHeld(victim) || (isPlayer(victim) && isCreative(victim))) return;
  setTimer(cy, "studio:next_grab", 220);
  animate(cy, "grab", 50);
  effect(cy, "weakness", 52, 2); // his fists stop landing while he holds a victim: the bite is the damage
  if (isPlayer(victim)) actionbar(victim, "§4Polyphemus lifts you towards his mouth...");
  startHold(victim, cy, 50, (h) => add(scale(forward(h), 2.4), { x: 0, y: 3.2, z: 0 }), {
    onRelease: (v, h) => {
      sound(v.dimension, "mob.ravager.bite", v.location, 0.6, 2);
      if (!isPlayer(v) && !v.typeId.startsWith("studio:")) {
        particle(v.dimension, "minecraft:critical_hit_emitter", v.location);
        try { v.kill(); } catch { }
        return;
      }
      hurt(v, prop(h, "studio:blind", false) ? 7 : 10, h);
      try { const f = forward(h); v.applyKnockback(f.x, f.z, 1.3, 0.5); } catch { }
    },
  });
}
let cyTick = 0;
function tickCyclops() {
  cyTick++;
  for (const cy of entitiesOf("studio:cyclops")) {
    initCyclops(cy);
    const state = prop(cy, "studio:state", "awake");
    if (state === "asleep") {
      if (cyTick % 4 === 0) particle(cy.dimension, "minecraft:basic_smoke_particle", add(cy.location, { x: 0, y: 1.5, z: 0 }));
      if (now() >= dp(cy, "studio:sleep_until", 0)) wakeCyclops(cy);
      continue;
    }
    if (state === "drunk" && now() >= dp(cy, "studio:drunk_until", 0)) { setDp(cy, "studio:drinks", 0); wakeCyclops(cy); }
    // Hurl boulders at distant prey (not while drunk or blind).
    if (state === "awake" && !prop(cy, "studio:blind", false) && dp(cy, "studio:angry", false) && timerReady(cy, "studio:next_throw")) {
      const t = nearestPlayer(cy, 30, 9);
      if (t) {
        setTimer(cy, "studio:next_throw", 140);
        animate(cy, "throw", 15);
        system.runTimeout(() => { if (valid(cy) && valid(t)) hurlBoulder(cy, add(t.location, { x: 0, y: 0.8, z: 0 }), 9); }, 9);
      }
    }
  }
}

// ------------------------------------------------------------------ Sirens
const SONG = ["§d♪ ...come closer, glorious Odysseus... ♪", "§d♪ ...no man has sailed past us unheard... ♪",
  "§d♪ ...we know all that happened at Troy... ♪", "§d♪ ...rest here, and grow wise... ♪"];
const SCALE = [0.5, 0.59, 0.67, 0.75, 0.84, 0.67, 0.59];
function deaf(p) {
  const until = dp(p, "studio:deaf_until", 0);
  if (until && now() >= until) { setDp(p, "studio:deaf_until", 0); actionbar(p, "§eThe beeswax has fallen out. You can hear again."); return false; }
  return until > now();
}
function tickSirens() {
  for (const s of entitiesOf("studio:siren")) {
    const listeners = playersNear(s.dimension, s.location, 24).filter((p) => !isCreative(p));
    if (!listeners.length) continue;
    animate(s, "sing", 30);
    const step = (Math.floor(now() / 40) + s.id.length) % SCALE.length;
    sound(s.dimension, "note.flute", s.location, SCALE[step], 2.5);
    sound(s.dimension, "mob.allay.idle", s.location, 0.55, 1.5);
    for (const p of listeners) {
      if (deaf(p)) { actionbar(p, "§7The beeswax holds. You hear only the sea."); continue; }
      effect(p, "nausea", 160);
      if (isRiding(p)) { actionbar(p, "§5You strain against the ropes... the song is unbearable."); continue; }
      const d = sub(s.location, p.location); const l = Math.hypot(d.x, d.z) || 1;
      try { p.applyKnockback(d.x / l, d.z / l, 0.35 + (24 - l) / 45, 0.06); } catch { }
      actionbar(p, SONG[step % SONG.length]);
    }
  }
}

// ------------------------------------------------------------------ Circe
const CIRCE_COUNSEL = [
  "§5Circe: §f\"The Sirens sit in a meadow piled with bones. Soften beeswax for your men's ears; if you must hear, have them bind you to the mast.\"",
  "§5Circe: §f\"Scylla takes six men, one for each head. Charybdis takes the whole ship. Choose Scylla, and row hard.\"",
  "§5Circe: §f\"Do not wake the shepherd's anger. Wine dulls a giant; a stake ends his sight.\"",
];
function initCirce(c) {
  if (dp(c, "studio:init", false)) return;
  setDp(c, "studio:init", true);
  for (let i = 0; i < 3; i++) {
    try {
      const pig = c.dimension.spawnEntity("minecraft:pig", add(c.location, { x: (i - 1) * 2, y: 0.5, z: 2.5 }));
      pig.nameTag = "§dTransformed Sailor";
      pig.addTag("studio:transformed");
      setDp(pig, "studio:orig", "minecraft:villager_v2");
    } catch { }
  }
}
const molyActive = (p) => dp(p, "studio:moly_until", 0) > now();
function transformToPig(victim, circe) {
  const dim = victim.dimension, loc = victim.location, orig = victim.typeId;
  particle(dim, "minecraft:knockback_roar_particle", loc);
  sound(dim, "mob.pig.death", loc, 0.7, 1.5);
  sound(dim, "mob.evocation_illager.cast_spell", loc, 0.8, 1.5);
  try {
    const pig = dim.spawnEntity("minecraft:pig", loc);
    pig.nameTag = "§dTransformed " + (orig.includes("villager") ? "Sailor" : orig.replace("minecraft:", "").replace(/_/g, " "));
    pig.addTag("studio:transformed");
    setDp(pig, "studio:orig", orig === "minecraft:villager" ? "minecraft:villager_v2" : orig);
    victim.remove();
  } catch { }
}
function cursePlayer(p, circe) {
  const ticks = dp(p, "studio:pliable_until", 0) > now() ? 1200 : 600;
  setDp(p, "studio:pig_until", now() + ticks);
  for (const [id, amp] of [["invisibility", 0], ["slowness", 1], ["weakness", 1], ["hunger", 1], ["mining_fatigue", 0]]) effect(p, id, ticks, amp);
  tell(p, "§5Circe's hands work your flesh like clay. Bones bend. Your scream becomes a squeal.");
  sound(p.dimension, "mob.pig.say", p.location, 0.6, 2);
}
function endCurse(p, msg = true) {
  setDp(p, "studio:pig_until", 0);
  for (const id of ["invisibility", "slowness", "weakness", "hunger", "mining_fatigue"]) clearEffect(p, id);
  const pig = world.getEntity(dp(p, "studio:curse_pig", "") || "_");
  if (valid(pig)) { try { pig.remove(); } catch { } }
  setDp(p, "studio:curse_pig", "");
  if (msg) actionbar(p, "§aYour body returns to human form.");
}
function circeMold(circe, victim) {
  if (isHeld(victim) || !timerReady(circe, "studio:next_mold")) return;
  if (isPlayer(victim)) {
    if (isCreative(victim)) return;
    if (molyActive(victim)) {
      actionbar(victim, "§aThe moly in your blood turns her magic aside!");
      sound(circe.dimension, "random.anvil_land", victim.location, 1.6, 0.6);
      return;
    }
  } else if (!HUMANOIDS.has(victim.typeId)) return;
  setTimer(circe, "studio:next_mold", 100);
  animate(circe, "mold", 40);
  if (isPlayer(victim)) effect(victim, "darkness", 60);
  startHold(victim, circe, 34, (h) => add(scale(forward(h), 1.3), { x: 0, y: 0.1, z: 0 }), {
    onRelease: (v, h) => {
      if (isPlayer(v)) { if (!molyActive(v)) cursePlayer(v, h); }
      else transformToPig(v, h);
    },
  });
}
function circeYield(circe, player) {
  trigger(circe, "studio:yield");
  setProp(circe, "studio:anim", "none");
  const dim = circe.dimension;
  let restored = 0;
  for (const pig of dim.getEntities({ location: circe.location, maxDistance: 64, tags: ["studio:transformed"] })) {
    try {
      const orig = dp(pig, "studio:orig", "minecraft:villager_v2");
      particle(dim, "minecraft:totem_particle", pig.location);
      dim.spawnEntity(orig, pig.location);
      pig.remove();
      restored++;
    } catch { }
  }
  for (const p of playersNear(dim, circe.location, 32)) {
    if (dp(p, "studio:pig_until", 0)) endCurse(p);
    tell(p, `§5Circe: §f"Hermes warned me of you, man of many turns. Your men are restored${restored ? ` (${restored})` : ""}. When you leave my island, cross the river Oceanus to the house of Hades."`);
  }
  sound(dim, "random.levelup", circe.location, 0.7, 1.5);
}
function tickCurses() {
  for (const p of world.getAllPlayers()) {
    const until = dp(p, "studio:pig_until", 0);
    if (!until) continue;
    if (now() >= until) { endCurse(p); continue; }
    let pig = world.getEntity(dp(p, "studio:curse_pig", "") || "_");
    if (!valid(pig)) {
      try {
        pig = p.dimension.spawnEntity("minecraft:pig", p.location);
        pig.nameTag = p.name;
        pig.addTag("studio:curse_pig");
        setDp(pig, "studio:owner", p.id);
        setDp(p, "studio:curse_pig", pig.id);
      } catch { continue; }
    }
    try { pig.teleport(p.location, { keepVelocity: false, rotation: { x: 0, y: p.getRotation().y } }); } catch { }
    if (now() % 20 === 0) actionbar(p, `§dYou are a pig. §7(${Math.ceil((until - now()) / 20)}s)`);
  }
  // Clean up orphaned disguise pigs (owner left or reloaded).
  if (now() % 100 === 0) {
    for (const pig of entitiesOf("minecraft:pig")) {
      if (!pig.hasTag("studio:curse_pig")) continue;
      const owner = world.getEntity(dp(pig, "studio:owner", "") || "_");
      if (!valid(owner) || !dp(owner, "studio:pig_until", 0)) { try { pig.remove(); } catch { } }
    }
  }
}

// ------------------------------------------------------------------ Scylla & Charybdis
function tickScylla() {
  for (const sc of entitiesOf("studio:scylla")) {
    if (!dp(sc, "studio:init", false)) {
      setDp(sc, "studio:init", true);
      spawnCharybdisNear(sc);
    }
    if (!timerReady(sc, "studio:next_snatch")) continue;
    const prey = sc.dimension.getEntities({ location: sc.location, maxDistance: 9 })
      .filter((t) => t.id !== sc.id && !NOT_PREY.has(t.typeId) && !isHeld(t) && !(isPlayer(t) && isCreative(t))
        && isLiving(t) && (isPlayer(t) || t.typeId.startsWith("minecraft:")))
      .sort((a, b) => len(sub(a.location, sc.location)) - len(sub(b.location, sc.location)))
      .slice(0, 6); // one victim per head
    if (!prey.length) continue;
    setTimer(sc, "studio:next_snatch", 180);
    animate(sc, "snatch", 70);
    sound(sc.dimension, "mob.ravager.roar", sc.location, 0.45, 3);
    prey.forEach((v, i) => {
      if (isPlayer(v)) actionbar(v, "§4A head snaps down — you are hauled into the air!");
      sound(sc.dimension, "mob.ravager.bite", v.location, 0.7, 1.5);
      startHold(v, sc, 70, (h, t) => {
        const a = (i / 6) * Math.PI * 2 + t * 0.05;
        return { x: Math.cos(a) * 2.6, y: 5.6 + (i % 2) * 1.2 + Math.sin(t * 0.3 + i) * 0.4, z: Math.sin(a) * 2.6 };
      }, {
        every: 20,
        onTick: (vv, h) => hurt(vv, 3, h),
        onRelease: (vv, h) => {
          if (!h) return;
          const k = sub(vv.location, h.location); const l = Math.hypot(k.x, k.z) || 1;
          try { vv.applyKnockback(k.x / l, k.z / l, 1.6, 0.4); } catch { }
        },
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
    if (sc.dimension.getEntities({ type: "studio:charybdis", location: sc.location, maxDistance: 64 }).length) return;
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      const spot = waterSurfaceNear(sc.dimension, add(sc.location, { x: Math.cos(a) * 18, y: 0, z: Math.sin(a) * 18 }));
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
      const a = chTick * 0.8;
      for (let k = 0; k < 3; k++) {
        const r = 2 + k * 2.5;
        particle(dim, "minecraft:bubble_column_up_particle", { x: c.x + Math.cos(a + k * 2) * r, y: c.y - 0.2, z: c.z + Math.sin(a + k * 2) * r });
      }
    }
    for (const t of dim.getEntities({ location: c, maxDistance: 14 })) {
      if (t.id === ch.id || t.typeId === "studio:charybdis" || t.typeId === "studio:scylla" || isHeld(t)) continue;
      if (isPlayer(t) && isCreative(t)) continue;
      const d = sub(c, t.location); const r = Math.hypot(d.x, d.z) || 0.01;
      const radial = { x: d.x / r, z: d.z / r }, swirl = { x: -d.z / r, z: d.x / r };
      const pull = 0.035 + 0.12 * (1 - r / 14);
      const isBoat = t.typeId === "minecraft:boat" || t.typeId === "minecraft:chest_boat";
      if (r < 2.4 && (isBoat || t.typeId === "minecraft:item")) {
        particle(dim, "minecraft:water_splash_particle", t.location);
        sound(dim, "random.splash", t.location, 0.6, 1.5);
        try { t.remove(); } catch { }
        continue;
      }
      if (isPlayer(t)) {
        if (chTick % 2 !== 0) continue;
        const v = { x: radial.x * pull + swirl.x * 0.08, z: radial.z * pull + swirl.z * 0.08 };
        const vl = Math.hypot(v.x, v.z) || 1;
        try { t.applyKnockback(v.x / vl, v.z / vl, vl * 2.2, r < 3 ? -0.4 : 0); } catch { }
        if (chTick % 20 === 0) actionbar(t, "§3The sea itself is draining into Charybdis!");
      } else {
        try { t.applyImpulse({ x: radial.x * pull + swirl.x * 0.08, y: r < 3 ? -0.08 : 0, z: radial.z * pull + swirl.z * 0.08 }); } catch { }
      }
      if (r < 2.5 && chTick % 10 === 0) hurt(t, 3, undefined, "drowning");
    }
  }
}

// ------------------------------------------------------------------ Laestrygonians
function tickLaestrygonians() {
  for (const g of entitiesOf("studio:laestrygonian")) {
    const dim = g.dimension;
    // Rocks for ships first: boats in range are the favourite target.
    if (timerReady(g, "studio:next_throw")) {
      let tgt;
      try {
        tgt = dim.getEntities({ location: g.location, maxDistance: 34, type: "minecraft:boat" })[0]
          || dim.getEntities({ location: g.location, maxDistance: 34, type: "minecraft:chest_boat" })[0];
      } catch { }
      tgt = tgt || nearestPlayer(g, 30, 12);
      if (tgt) {
        setTimer(g, "studio:next_throw", 110);
        animate(g, "throw", 15);
        system.runTimeout(() => { if (valid(g) && valid(tgt)) hurlBoulder(g, tgt.location, 10); }, 9);
        continue;
      }
    }
    // Spear charge.
    const charging = dp(g, "studio:charge_until", 0) > now();
    if (!charging && timerReady(g, "studio:next_charge")) {
      const t = nearestPlayer(g, 12, 5);
      if (t) {
        setTimer(g, "studio:next_charge", 160);
        setDp(g, "studio:charge_until", now() + 14);
        setDp(g, "studio:charge_target", t.id);
        setDp(g, "studio:charge_hit", false);
        animate(g, "charge", 22);
        sound(dim, "mob.ravager.roar", g.location, 0.8, 1.5);
      }
    } else if (charging) {
      const t = world.getEntity(dp(g, "studio:charge_target", "") || "_");
      if (!valid(t)) continue;
      const d = sub(t.location, g.location); const l = Math.hypot(d.x, d.z) || 1;
      try { g.applyImpulse({ x: (d.x / l) * 0.32, y: 0, z: (d.z / l) * 0.32 }); } catch { }
      if (l < 2.6 && !dp(g, "studio:charge_hit", false)) {
        setDp(g, "studio:charge_hit", true);
        hurt(t, 10, g);
        try { t.applyKnockback(d.x / l, d.z / l, 1.7, 0.5); } catch { }
        sound(dim, "mob.irongolem.hit", t.location, 0.7, 1.5);
      }
    }
  }
}

// ------------------------------------------------------------------ events
world.afterEvents.entityHitEntity.subscribe((ev) => {
  const { damagingEntity: a, hitEntity: v } = ev;
  if (!valid(a) || !valid(v)) return;
  if (a.typeId === "studio:cyclops") cyclopsGrab(a, v);
  else if (a.typeId === "studio:circe") circeMold(a, v);
});

world.afterEvents.entityHurt.subscribe((ev) => {
  const v = ev.hurtEntity, src = ev.damageSource?.damagingEntity;
  if (!valid(v)) return;
  if (v.typeId === "minecraft:sheep" && isPlayer(src) && v.hasTag("studio:flock")) {
    let cy = world.getEntity(dp(v, "studio:shepherd", "") || "_");
    if (!valid(cy)) cy = v.dimension.getEntities({ type: "studio:cyclops", location: v.location, maxDistance: 40 })[0];
    if (valid(cy)) {
      angerCyclops(cy);
      actionbar(src, "§cA furious bellow echoes from the cave. You have harmed the shepherd's flock.");
    }
    return;
  }
  if (v.typeId === "studio:cyclops" && isPlayer(src)) {
    const state = prop(v, "studio:state", "awake");
    const blind = prop(v, "studio:blind", false);
    if (!blind && heldItem(src) === "studio:olive_stake" && (state === "asleep" || state === "drunk")) {
      blindCyclops(v, src);
    } else {
      if (state === "asleep") wakeCyclops(v);
      angerCyclops(v);
      if (blind && timerReady(v, "studio:next_shout")) {
        setTimer(v, "studio:next_shout", 200);
        for (const p of playersNear(v.dimension, v.location, 48)) tell(p, "§b\"Nobody is killing me!\"");
      }
    }
    return;
  }
  if (v.typeId === "studio:circe" && isPlayer(src) && molyActive(src) && !prop(v, "studio:yielded", false)) {
    circeYield(v, src);
  }
});

world.afterEvents.dataDrivenEntityTrigger.subscribe((ev) => {
  const e = ev.entity, id = ev.eventId ?? ev.id;
  if (!valid(e)) return;
  if (e.typeId === "studio:cyclops" && id === "studio:drink_wine") {
    const drinks = dp(e, "studio:drinks", 0) + 1;
    setDp(e, "studio:drinks", drinks);
    setDp(e, "studio:drunk_until", now() + 600);
    sound(e.dimension, "random.drink", e.location, 0.5, 2);
    const lines = ["§6Polyphemus gulps the dark Maronian wine. §7\"More!\" (1/3)",
      "§6He drains it again and laughs. §7\"For that, Nobody, I will eat you last.\" (2/3)",
      "§6The giant sways... and crashes to the cave floor, snoring. §7Now — the stake. (3/3)"];
    for (const p of playersNear(e.dimension, e.location, 16)) tell(p, lines[Math.min(drinks, 3) - 1]);
    if (drinks >= 3) {
      setDp(e, "studio:drinks", 0);
      setDp(e, "studio:sleep_until", now() + 1200);
      trigger(e, "studio:fall_asleep");
    }
  } else if (e.typeId === "studio:circe" && id === "studio:offer_feast") {
    const p = nearestPlayer(e, 8);
    if (!p) return;
    try { e.dimension.spawnItem(new ItemStack("studio:circe_feast", 1), p.location); } catch { }
    tell(p, "§5Circe: §f\"You look starved, sailor. Eat. Rest. Stay a while...\"");
  } else if (e.typeId === "studio:circe" && id === "studio:counsel") {
    const p = nearestPlayer(e, 8);
    if (p) tell(p, CIRCE_COUNSEL[Math.floor(Math.random() * CIRCE_COUNSEL.length)]);
  }
});

world.afterEvents.itemCompleteUse.subscribe((ev) => {
  const p = ev.source, id = ev.itemStack?.typeId;
  if (!isPlayer(p)) return;
  if (id === "studio:beeswax") {
    setDp(p, "studio:deaf_until", now() + 6000);
    actionbar(p, "§eYou press soft beeswax into your ears. The world goes quiet.");
  } else if (id === "studio:moly") {
    setDp(p, "studio:moly_until", now() + 6000);
    tell(p, "§aThe bitter black root of moly burns in your chest. Her magic cannot touch you now.");
  } else if (id === "studio:circe_feast") {
    setDp(p, "studio:pliable_until", now() + 2400);
    effect(p, "saturation", 2, 4);
    effect(p, "slowness", 600, 0);
    actionbar(p, "§dWarmth floods you... you feel strangely soft. Pliable.");
  } else if (id === "studio:maronian_wine") {
    effect(p, "nausea", 300, 0);
    actionbar(p, "§6Strong enough for a giant. Your head spins.");
  }
});

world.afterEvents.projectileHitEntity.subscribe((ev) => {
  let hit;
  try { hit = ev.getEntityHit()?.entity; } catch { return; }
  if (hit?.typeId !== "studio:laestrygonian") return;
  sound(hit.dimension, "item.shield.block", hit.location, 0.8, 1.5);
  if (isPlayer(ev.source)) actionbar(ev.source, "§7Your shot glances off the bronze shield.");
});

world.afterEvents.entityDie.subscribe((ev) => {
  const e = ev.deadEntity;
  if (e?.typeId === "studio:cyclops") {
    try { e.dimension.runCommandAsync("weather thunder 2400"); } catch { }
    for (const p of playersNear(e.dimension, e.location, 64)) tell(p, "§bPolyphemus falls. Far below, the sea begins to churn — Poseidon will remember this.");
  }
  if (isPlayer(e) && dp(e, "studio:pig_until", 0)) endCurse(e, false);
});

// ------------------------------------------------------------------ loops
system.runInterval(() => { tickHolds(); tickBoulders(); tickCurses(); }, 1);
system.runInterval(() => { tickCharybdis(); }, 2);
system.runInterval(() => { tickCyclops(); tickLaestrygonians(); for (const c of entitiesOf("studio:circe")) initCirce(c); }, 10);
system.runInterval(() => { tickScylla(); }, 10);
system.runInterval(() => { tickSirens(); }, 40);
system.runInterval(() => {
  // Orphaned boulders (e.g. after a world reload) have no flight state: remove them.
  for (const b of entitiesOf("studio:boulder")) if (!boulders.has(b.id)) { try { b.remove(); } catch { } }
}, 100);
