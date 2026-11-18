// Polyphemus, the 11-block shepherd. Seven moves, each with its own animation, sound and server effect:
//   devour  - scoops a man up, lifts him to his mouth, two bites, tosses him aside
//   kick    - a swinging kick that sends a man flying ("kicked Elpenor, who died on the spot")
//   stomp   - raises a foot and brings it down on whatever is underfoot
//   throw   - blind, he hoists a rock overhead and hurls it at the ship he hears, and misses
//   cry     - blinded by the burning stake, he calls on Poseidon and a storm rolls in
//   tend    - the gentle shepherd strokes his flock
//   wake    - sits up out of sleep
// Blind, he passes over men hidden in his flock. At night he sleeps.
import { world } from "@minecraft/server";
import { MOVES } from "../data/moves.js";
import {
  add, bearing, block, dirTo, dp, effect, flat, forward, heldItem, hurt, isAir, isBoat, isCreative, isNight, isPlayer, isPrey, later,
  near, nearestPlayer, now, prop, push, ready, right, riders, ringSpot, runCommand, safe, scale, setDp, sub, trigger, valid, wait,
} from "../lib/util.js";
import { bar, burst, particle, say, sound } from "../lib/fx.js";
import { busy, perform } from "../lib/moves.js";
import { follow, hold, isHeld, pathAt, release, worldOffset } from "../lib/holds.js";
import { creatures } from "../lib/registry.js";
import { onStoryEvent } from "../world/story.js";

export const TYPE = "studio:cyclops";
const REACH = 6.0;          // blocks: he snatches men this close
const KICK_MAX = 6.5, FOOT = 4.6, STOMP_RADIUS = 4.5;
const flockOf = (cy) => near(cy.dimension, cy.location, 48, "minecraft:sheep").filter((s) => dp(s, "studio:shepherd", "") === cy.id);
const quarry = (cy, t) => t.id !== cy.id && isPrey(t, isHeld) && t.typeId !== "minecraft:sheep";

export function initCyclops(cy) {
  if (dp(cy, "studio:init", false)) return;
  setDp(cy, "studio:init", true);
  setDp(cy, "studio:hx", cy.location.x);
  setDp(cy, "studio:hy", cy.location.y);
  setDp(cy, "studio:hz", cy.location.z);
  for (let i = 0; i < 6; i++) {
    safe("flock", () => {
      const s = cy.dimension.spawnEntity("minecraft:sheep", ringSpot(cy.location, 5 + (i % 2) * 2.5, (i / 6) * Math.PI * 2));
      s.addTag("studio:flock");
      setDp(s, "studio:shepherd", cy.id);
    });
  }
}

// ---------------------------------------------------------------- devour: scoop, lift, bite, bite, toss
function devour(cy, victim) {
  if (!valid(victim) || isHeld(victim) || !ready(cy, "studio:cd_devour")) return false;
  const K = "cyclops.devour", spec = MOVES.cyclops.devour;
  const from = sub(victim.location, cy.location);
  const ok = perform(cy, "devour", {
    start: () => {
      wait(cy, "studio:cd_devour", 240);
      setDp(cy, "studio:last_combat", now());
      if (isPlayer(victim)) bar(victim, "odyssey.cy.devour");
      // the man is swept to the hand during the reach, then rides the hand up to the mouth
      hold(victim, cy, {
        ticks: spec.release,
        at: (h, t) => {
          const hand = worldOffset(h, pathAt(K, "hand", t));
          if (t >= spec.grab) return hand;
          const k = t / spec.grab, e = k * k * (3 - 2 * k), g = worldOffset(h, pathAt(K, "hand", spec.grab));
          return { x: from.x + (g.x - from.x) * e, y: from.y + (g.y - from.y) * e, z: from.z + (g.z - from.z) * e };
        },
        onRelease: (v, h) => {
          if (!h) return;
          push(v, add(scale(right(h), 1), scale(forward(h), 0.6)), 1.8, 0.7);      // tossed aside like a bone
        },
      });
    },
    bite: (c, i) => {
      if (!valid(victim)) return;
      hurt(victim, 7, c);
      burst(victim.dimension, "minecraft:critical_hit_emitter", victim.location, 0.6, 6);
    },
  });
  return ok;
}

// ---------------------------------------------------------------- kick: a swinging blow that sends men flying
function kick(cy) {
  if (!ready(cy, "studio:cd_kick")) return false;
  return perform(cy, "kick", {
    start: () => wait(cy, "studio:cd_kick", 140),
    hit: (c) => {
      const foot = add(c.location, scale(forward(c), FOOT));
      for (const t of near(c.dimension, foot, 3.4).filter((x) => quarry(c, x))) {
        hurt(t, 16, c);
        push(t, dirTo(c.location, t.location), 3.2, 1.0);
        if (isPlayer(t)) bar(t, "odyssey.cy.kick");
      }
      burst(c.dimension, "minecraft:huge_explosion_emitter", foot, 1.2, 2);
    },
  });
}

// ---------------------------------------------------------------- stomp: the foot comes down on whatever is underfoot
function stomp(cy) {
  if (!ready(cy, "studio:cd_stomp")) return false;
  return perform(cy, "stomp", {
    start: () => wait(cy, "studio:cd_stomp", 100),
    hit: (c) => {
      for (const t of near(c.dimension, c.location, STOMP_RADIUS).filter((x) => quarry(c, x))) {
        hurt(t, 14, c);
        push(t, dirTo(c.location, t.location), 1.4, 0.9);
        if (isPlayer(t)) bar(t, "odyssey.cy.stomp");
      }
      for (let k = 0; k < 8; k++) {
        const a = (k / 8) * Math.PI * 2;
        particle(c.dimension, "minecraft:huge_explosion_emitter", add(c.location, { x: Math.cos(a) * 3, y: 0.3, z: Math.sin(a) * 3 }));
      }
    },
  });
}

// ---------------------------------------------------------------- throw: hoist a rock overhead and hurl it at the ship
const boulders = new Map();
const GRAVITY = 0.045;
function launch(rock, owner, aim, damage) {
  const start = rock.location;
  const d = sub(aim, start);
  const T = Math.max(14, Math.min(48, Math.hypot(d.x, d.z)));
  const vel = { x: d.x / T, y: (d.y + 0.5 * GRAVITY * T * T) / T, z: d.z / T };
  boulders.set(rock.id, { e: rock, vel, owner, damage, life: 160 });
  sound(rock.dimension, "odyssey.boulder.whoosh", start, 1, 1);
}
function shatter(b, loc) {
  const dim = b.e.dimension;
  burst(dim, "minecraft:huge_explosion_emitter", loc, 1.5, 3);
  particle(dim, "minecraft:water_splash_particle", loc);
  sound(dim, "odyssey.boulder.impact", loc, 1, 1);
  for (const t of near(dim, loc, 4)) {
    if (t.id === b.e.id || t.typeId === "studio:boulder" || (valid(b.owner) && t.id === b.owner.id)) continue;
    if (isBoat(t)) { safe("boat", () => t.remove()); continue; }
    if (isPlayer(t) && isCreative(t)) continue;
    hurt(t, b.damage, b.owner);
  }
  safe("rock", () => b.e.remove());
}
export function tickBoulders() {
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
    safe("rock", () => b.e.teleport(next, { keepVelocity: false }));
  }
}
export const strayBoulder = (e) => !boulders.has(e.id) && !isHeld(e);

function throwRock(cy, boat) {
  if (!ready(cy, "studio:cd_throw")) return false;
  const spec = MOVES.cyclops.throw;
  const a = Math.random() * Math.PI * 2, miss = 5 + Math.random() * 4;        // beyond the 4-block blast: he always misses
  const aim = add(boat.location, { x: Math.cos(a) * miss, y: 0, z: Math.sin(a) * miss });
  let rock;
  return perform(cy, "throw", {
    start: () => wait(cy, "studio:cd_throw", 400),
    pick: (c) => {
      rock = safe("rock", () => c.dimension.spawnEntity("studio:boulder", add(c.location, worldOffset(c, pathAt("cyclops.throw", "hand", spec.pick)))));
      if (rock) hold(rock, c, { ticks: spec.len, at: follow("cyclops.throw", "hand", spec.pick) });
    },
    release: (c) => {
      if (!valid(rock)) return;
      release(rock);
      launch(rock, c, aim, 16);
    },
    done: () => { if (valid(rock) && !boulders.has(rock.id)) safe("rock", () => rock.remove()); },
  });
}

// ---------------------------------------------------------------- cry: "Father Poseidon, they blinded me!"
export function blindCyclops(cy) {
  trigger(cy, "studio:blinded");
  setDp(cy, "studio:last_combat", now());
  const dim = cy.dimension, at = cy.location;
  sound(dim, "odyssey.cyclops.stake_pierce", at, 1, 1);
  sound(dim, "odyssey.cyclops.pain_roar", at, 1.2, 1);
  perform(cy, "cry", {}, { force: true });
  later(14, () => say(dim, at, 128, "odyssey.cy.cry"));
  for (const p of near(dim, at, 64).filter(isPlayer)) bar(p, "odyssey.cy.blind_hint");
  later(80, () => {                                 // Poseidon answers: harsh sea conditions
    runCommand(dim, "weather thunder 6000");
    sound(dim, "odyssey.world.storm", at, 1, 1);
  });
}

// ---------------------------------------------------------------- tend the flock, wake
function tend(cy, sheep) {
  return perform(cy, "tend", {
    start: () => wait(cy, "studio:cd_tend", 700),
    stroke: () => { if (valid(sheep)) { effect(sheep, "regeneration", 100, 1); particle(sheep.dimension, "minecraft:heart_particle", add(sheep.location, { x: 0, y: 1.2, z: 0 })); } },
  });
}
function wake(cy) {
  const blind = prop(cy, "studio:blind", false);
  perform(cy, "wake", {
    start: (c) => trigger(c, "studio:wake"),
    done: (c) => trigger(c, blind ? "studio:blinded" : "studio:hunt"),
  });
}

// ---------------------------------------------------------------- the thinking loop (every 10 ticks)
let cyTick = 0;
function think(cy, hiddenNow) {
  initCyclops(cy);
  const dim = cy.dimension;
  const blind = prop(cy, "studio:blind", false), state = prop(cy, "studio:state", "awake");
  // once blind, men among his sheep go unnoticed
  if (blind && state !== "asleep") {
    const flock = flockOf(cy);
    for (const p of near(dim, cy.location, 48).filter(isPlayer)) {
      if (isCreative(p) || !flock.some((s) => flat(s.location, p.location) < 2.5)) continue;
      hiddenNow.add(p.id);
      safe("tag", () => p.addTag("studio:in_flock"));
      if (cyTick % 4 === 0 && flat(p.location, cy.location) < 16) bar(p, "odyssey.cy.hidden");
    }
  }
  if (busy(cy)) return;
  if (state === "asleep") {
    if (!isNight() || now() >= dp(cy, "studio:sleep_until", 0)) wake(cy);
    return;
  }
  if (isNight() && !blind && now() - dp(cy, "studio:last_combat", -9999) > 400) {
    trigger(cy, "studio:fall_asleep");
    setDp(cy, "studio:sleep_until", now() + 3600);
    return;
  }
  // Keep Polyphemus on flat ground near his cave meadow so his 11-block body never clips into steep cliff walls
  const hx = dp(cy, "studio:hx", 318), hy = dp(cy, "studio:hy", 67), hz = dp(cy, "studio:hz", -150);
  if (Math.hypot(cy.location.x - hx, cy.location.z - hz) > 16 || cy.location.y > hy + 2.5) {
    const back = dirTo(cy.location, { x: hx, y: hy, z: hz });
    try { cy.applyImpulse({ x: back.x * 0.22, y: 0, z: back.z * 0.22 }); } catch { }
  }
  const prey = nearestPlayer(cy, 7, (p) => !hiddenNow.has(p.id));
  if (prey) {
    const d = flat(prey.location, cy.location), ang = Math.abs(bearing(cy, prey));
    if (d < 3.6 && stomp(cy)) return;
    if (d >= 3.4 && d <= KICK_MAX && ang < 1.0 && Math.random() < 0.4 && kick(cy)) return;
    if (d <= REACH) devour(cy, prey);
    return;
  }
  if (blind && ready(cy, "studio:cd_throw")) {          // blind, he throws a rock at a boat he hears - and misses
    const boat = near(dim, cy.location, 48).find((b) => isBoat(b) && riders(b).length > 0);
    if (boat) throwRock(cy, boat);
    return;
  }
  if (!blind && !isNight() && ready(cy, "studio:cd_tend")) {
    const sheep = flockOf(cy).find((s) => flat(s.location, cy.location) < 10);
    if (sheep) tend(cy, sheep);
  }
}
export function tickCyclops() {
  cyTick++;
  const hiddenNow = new Set();
  for (const cy of creatures(TYPE)) safe("cyclops", () => think(cy, hiddenNow));
  for (const p of world.getAllPlayers()) {
    safe("tag", () => { if (!hiddenNow.has(p.id) && p.hasTag("studio:in_flock")) p.removeTag("studio:in_flock"); });
  }
}

// ---------------------------------------------------------------- events
export function onHit(cy, victim) {
  setDp(cy, "studio:last_combat", now());
  if (!busy(cy) && prop(cy, "studio:state", "awake") !== "asleep" && quarry(cy, victim)) devour(cy, victim);
}
export function onHurt(cy, src) {
  setDp(cy, "studio:last_combat", now());
  if (!isPlayer(src)) return;
  const state = prop(cy, "studio:state", "awake"), blind = prop(cy, "studio:blind", false);
  if (state === "asleep" && !blind && heldItem(src) === "studio:burning_stake") {
    blindCyclops(cy);
    onStoryEvent(src, "cyclops_blinded");
  } else if (state === "asleep" && !busy(cy)) {
    bar(src, "odyssey.prog.need_stake");
    wake(cy);
  } else if (!busy(cy) && ready(cy, "studio:cd_hurt")) {
    wait(cy, "studio:cd_hurt", 20);
    perform(cy, "hurt", {}, { still: false });
  }
}
