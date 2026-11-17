// The Sirens: evil mermaids lying on the sea rocks in the mist, known by their song. Three moves:
//   sing   - the song pulls and sickens everyone within 40 blocks; each listener hears their own mix (wax muffles it)
//   beckon - one listener is called by name: a stronger pull
//   drag   - anyone who reaches the rocks is dragged under
// The crew stop their ears with wax and the song dulls to a hum; Odysseus, bound to the mast, hears all of it and cannot go.
import { MOVES } from "../data/moves.js";
import {
  add, dirTo, dp, effect, flat, hurt, isCreative, now, playersNear, push, ready, ridingOn, safe, setDp, sub, wait,
  valid,
} from "../lib/util.js";
import { bar, hear, particle } from "../lib/fx.js";
import { busy, perform } from "../lib/moves.js";
import { hold, isHeld } from "../lib/holds.js";
import { creatures } from "../lib/registry.js";

export const TYPE = "studio:siren";
const RANGE = 40;

export function deaf(p) {
  const until = dp(p, "studio:deaf_until", 0);
  if (until && now() >= until) { setDp(p, "studio:deaf_until", 0); bar(p, "odyssey.siren.wax_off"); return false; }
  return until > now();
}
export function onWax(p) { setDp(p, "studio:deaf_until", now() + 6000); bar(p, "odyssey.siren.wax_on"); }

/** What the song does to one listener this second. */
function charm(s, p, strength = 1) {
  if (deaf(p)) { bar(p, "odyssey.siren.muffled"); return; }
  effect(p, "nausea", 160);
  if (ridingOn(p)) {                        // bound to the mast: he hears it all but cannot go to them
    effect(p, "slowness", 60, 3);
    bar(p, "odyssey.siren.mast");
    return;
  }
  const d = sub(s.location, p.location), l = Math.hypot(d.x, d.z) || 1;
  push(p, d, (0.35 + (RANGE - Math.min(l, RANGE)) / 60) * strength, 0.05);
  bar(p, "odyssey.siren.pull");
}

function sing(s) {
  const spec = MOVES.siren.sing;
  wait(s, "studio:cd_sing", spec.len + 200);
  return perform(s, "sing", {
    start: () => {
      for (const p of playersNear(s.dimension, s.location, RANGE)) {
        if (isCreative(p)) continue;
        hear(p, deaf(p) ? "odyssey.siren.song_muffled" : "odyssey.siren.song", s.location, 1, 1);   // each listener's own mix
      }
    },
    tick: (c, t) => {
      if (t % 20 !== 0) return;
      for (const p of playersNear(c.dimension, c.location, RANGE)) if (!isCreative(p) && !isHeld(p)) charm(c, p);
    },
  }, { still: false });
}
function beckon(s, target) {
  wait(s, "studio:cd_beckon", 500);
  return perform(s, "beckon", {
    tick: (c, t) => {
      if (t % 10 !== 0 || !valid(target) || deaf(target) || isHeld(target)) return;
      push(target, sub(c.location, target.location), 0.7, 0.08);
      particle(c.dimension, "minecraft:soul_particle", add(target.location, { x: 0, y: 1, z: 0 }));
    },
  }, { still: false });
}
function drag(s, victim) {
  const spec = MOVES.siren.drag;
  wait(s, "studio:cd_drag", 400);
  return perform(s, "drag", {
    start: () => bar(victim, "odyssey.siren.dragged"),
    grab: () => {
      if (!valid(victim)) return;
      hold(victim, s, {
        ticks: spec.len - spec.grab, every: 6,
        at: (h, t) => ({ x: 0, y: -1.2 - t * 0.04, z: 0 }),                      // down into the sea
        onTick: (v, h) => hurt(v, 3, h, "drowning"),
        onRelease: (v, h) => { if (h) push(v, dirTo(h.location, v.location), 1.2, 0.5); },
      });
    },
  }, { still: false });
}

let sirenTick = 0;
export function tickSirens() {
  sirenTick++;
  for (const s of creatures(TYPE)) {
    safe("siren", () => {
      const dim = s.dimension;
      for (let k = 0; k < 3; k++) {              // mist over the rocks
        const a = Math.random() * Math.PI * 2;
        particle(dim, "minecraft:campfire_smoke_particle", add(s.location, { x: Math.cos(a) * 2.5, y: 0.2, z: Math.sin(a) * 2.5 }));
      }
      const listeners = playersNear(dim, s.location, RANGE).filter((p) => !isCreative(p));
      if (!listeners.length || busy(s)) return;
      const reached = listeners.find((p) => flat(p.location, s.location) < 3.4 && !isHeld(p));
      if (reached && ready(s, "studio:cd_drag")) { drag(s, reached); return; }
      if (ready(s, "studio:cd_sing")) { sing(s); return; }
      const close = listeners.find((p) => flat(p.location, s.location) < 16 && !deaf(p));
      if (close && ready(s, "studio:cd_beckon")) beckon(s, close);
    });
  }
}
