// The Laestrygonians: armoured giants of Telepylus who come out of the fog. Each weapon has its own move:
//   slash  (sword)        - a wide horizontal sweep
//   impale (glaive)       - a stab that lifts a man off his feet and flings him into the trees
//   crush  (mace)         - an overhead slam that shakes the ground (and ships)
//   cleave (curved blade) - a double sweep
//   smash  (any weapon)   - chops a ship to pieces
// Odysseus asks an armoured child for hospitality: the child laughs; asked again, the child screams and runs, and the
// giants emerge.
import { MOVES } from "../data/moves.js";
import {
  add, bearing, dirTo, dp, hurt, isBoat, isPlayer, isPrey, near, nearestPlayer, prop, push, ready, right, ringSpot,
  safe, scale, setDp, trigger, valid, wait, forward, later,
} from "../lib/util.js";
import { bar, burst, particle, say, sound } from "../lib/fx.js";
import { busy, perform } from "../lib/moves.js";
import { follow, hold, isHeld, release } from "../lib/holds.js";
import { creatures } from "../lib/registry.js";

export const TYPE = "studio:laestrygonian", CHILD = "studio:laestrygonian_child";
const isGiant = (t) => t.typeId === TYPE || t.typeId === CHILD;
const REACH = [5.4, 7.0, 5.4, 5.8];        // sword, glaive, mace, curved blade
const quarry = (g, t) => t.id !== g.id && !isGiant(t) && isPrey(t, isHeld);
const inArc = (g, radius, half) => near(g.dimension, g.location, radius).filter((t) => quarry(g, t) && Math.abs(bearing(g, t)) < half);

export function alarmGiants(dim, loc, r = 56) {
  let calm = false;
  for (const g of near(dim, loc, r, TYPE)) { if (!dp(g, "studio:alarmed", false)) calm = true; setDp(g, "studio:alarmed", true); trigger(g, "studio:alarm"); }
  if (calm) sound(dim, "odyssey.laestrygonian.war_cry", loc, 1, 1);
}

// ---------------------------------------------------------------- the weapon moves
function slash(g) {
  return perform(g, "slash", {
    hit: () => {
      for (const t of inArc(g, 5.6, 1.3)) {
        hurt(t, 10, g);
        push(t, add(scale(right(g), 0.8), dirTo(g.location, t.location)), 1.3, 0.4);
      }
      burst(g.dimension, "minecraft:critical_hit_emitter", add(g.location, scale(forward(g), 3)), 2, 5);
    },
  });
}
function impale(g) {
  const K = "laestrygonian.impale";
  let held;
  return perform(g, "impale", {
    hit: () => {
      const t = inArc(g, 7.2, 0.6).sort((a, b) => dist2(g, a) - dist2(g, b))[0];
      if (!t) return;
      held = t;
      hurt(t, 12, g);
      if (isPlayer(t)) bar(t, "odyssey.lae.impale");
      hold(t, g, {
        ticks: MOVES.laestrygonian.impale.len, at: follow(K, "point", MOVES.laestrygonian.impale.hit),
        onRelease: (v, h) => { if (h) push(v, add(forward(h), scale(right(h), 0.5)), 2.2, 1.2); },     // flung into the trees
      });
    },
    fling: () => { if (valid(held)) release(held); },
  });
}
const dist2 = (a, b) => (a.location.x - b.location.x) ** 2 + (a.location.z - b.location.z) ** 2;
function crush(g) {
  return perform(g, "crush", {
    hit: () => {
      const at = add(g.location, scale(forward(g), 3.2));
      for (const t of near(g.dimension, at, 4.6)) {
        if (isBoat(t)) { safe("boat", () => t.remove()); continue; }
        if (!quarry(g, t)) continue;
        hurt(t, 16, g);
        push(t, dirTo(at, t.location), 0.8, 0.9);
        if (isPlayer(t)) bar(t, "odyssey.lae.crush");
      }
      burst(g.dimension, "minecraft:huge_explosion_emitter", at, 2, 3);
    },
  });
}
function cleave(g) {
  return perform(g, "cleave", {
    hit: (c, i) => {
      for (const t of inArc(c, 5.8, 1.6)) {
        hurt(t, 8, c);
        push(t, add(scale(right(c), i === 0 ? -1 : 1), dirTo(c.location, t.location)), 1.2, 0.35);
      }
      burst(c.dimension, "minecraft:critical_hit_emitter", add(c.location, scale(forward(c), 3)), 2.2, 5);
    },
  });
}
export function smash(g, boat) {
  return perform(g, "smash", {
    hit: () => {
      if (!valid(boat)) return;
      const at = boat.location, dim = boat.dimension;
      safe("eject", () => boat.getComponent("minecraft:rideable")?.ejectRiders?.());
      particle(dim, "minecraft:water_splash_particle", at);
      burst(dim, "minecraft:huge_explosion_emitter", at, 1, 2);
      safe("boat", () => boat.remove());
    },
  });
}
const MOVE_FOR = [slash, impale, crush, cleave];

// ---------------------------------------------------------------- the thinking loop (every 10 ticks)
export function tickLaestrygonians() {
  for (const g of creatures(TYPE)) {
    safe("laestrygonian", () => {
      if (busy(g)) return;
      const boat = near(g.dimension, g.location, 4.8).find(isBoat);
      if (boat && ready(g, "studio:cd_smash")) { wait(g, "studio:cd_smash", 80); smash(g, boat); return; }
      const w = prop(g, "studio:weapon", 0);
      const prey = nearestPlayer(g, REACH[w]);
      if (prey && ready(g, "studio:cd_attack") && Math.abs(bearing(g, prey)) < 1.4) {
        wait(g, "studio:cd_attack", 50);
        MOVE_FOR[w] && MOVE_FOR[w](g);
      }
    });
  }
}

// ---------------------------------------------------------------- the armoured child
export function tickChildren() {
  for (const c of creatures(CHILD)) {
    safe("child", () => {
      const dim = c.dimension;
      if (!dp(c, "studio:init", false)) {
        setDp(c, "studio:init", true);
        if (!near(dim, c.location, 48, TYPE).length) {
          for (let i = 0; i < 3; i++) safe("giant", () => dim.spawnEntity(TYPE, ringSpot(c.location, 20 + i * 3, Math.random() * Math.PI * 2)));
        }
      }
      if (busy(c)) return;
      const phase = dp(c, "studio:phase", 0);
      if (phase === 0) {
        if (!nearestPlayer(c, 8)) return;
        setDp(c, "studio:phase", 1);
        wait(c, "studio:phase_at", 60);
        perform(c, "laugh");
        say(dim, c.location, 24, "odyssey.lae.child_laugh");
      } else if (phase === 1 && ready(c, "studio:phase_at")) {
        if (!nearestPlayer(c, 8)) { setDp(c, "studio:phase", 0); return; }        // nobody asked again
        setDp(c, "studio:phase", 2);
        wait(c, "studio:phase_at", 2400);
        perform(c, "scream", { done: (cc) => trigger(cc, "studio:flee") });
        say(dim, c.location, 48, "odyssey.lae.child_scream");
        later(30, () => say(dim, c.location, 56, "odyssey.lae.emerge"));
        alarmGiants(dim, c.location, 64);
      } else if (phase === 2 && ready(c, "studio:phase_at")) {
        setDp(c, "studio:phase", 0);
      }
    });
  }
}

// ---------------------------------------------------------------- events
export function onHit(g, victim) {
  if (g.typeId !== TYPE || busy(g) || !ready(g, "studio:cd_attack") || !quarry(g, victim)) return;
  wait(g, "studio:cd_attack", 50);
  const w = prop(g, "studio:weapon", 0);
  MOVE_FOR[w] && MOVE_FOR[w](g);
}
export function onHurt(v, src) {
  if (!isPlayer(src)) return;
  if (v.typeId === TYPE) alarmGiants(v.dimension, v.location);
  if (v.typeId === CHILD) { trigger(v, "studio:flee"); alarmGiants(v.dimension, v.location, 64); }
}
