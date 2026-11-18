// Scylla and Charybdis. Tiresias: "The Whirlpool in the sea takes all of your lives, the monster in the cliff only six."
// Scylla (five moves): lunge - her six necks stretch out of the cave; snatch - each head bites a man off the deck;
// devour - the heads haul their victims up toward the cave and chew; rend - the heads tear an empty ship apart;
// recoil - back into the cave, hissing. Charybdis (two moves): surge - the whirlpool gathers strength;
// gulp - she swallows a ship.
import { MOVES } from "../data/moves.js";
import {
  add, dp, forward, hurt, isBoat, isPlayer, isPrey, len, near, now, push, ready, riders, ringSpot, safe, scale, setDp,
  sub, valid, wait, waterSurfaceNear, flat, isCreative,
} from "../lib/util.js";
import { bar, particle, say } from "../lib/fx.js";
import { busy, perform } from "../lib/moves.js";
import { hold, isHeld, pathAt, release, worldOffset } from "../lib/holds.js";
import { creatures } from "../lib/registry.js";

export const SCYLLA = "studio:scylla", CHARYBDIS = "studio:charybdis";
const HEADS = 6;

// ---------------------------------------------------------------- Scylla
function spawnCharybdisNear(sc) {
  safe("charybdis", () => {
    if (near(sc.dimension, sc.location, 80, CHARYBDIS).length) return;
    for (let i = 0; i < 8; i++) {
      const spot = waterSurfaceNear(sc.dimension, ringSpot(sc.location, 30, (i / 8) * Math.PI * 2));
      if (spot) { sc.dimension.spawnEntity(CHARYBDIS, spot); return; }
    }
  });
}
const victimsOf = (sc) => near(sc.dimension, sc.location, 18)
  .filter((t) => t.id !== sc.id && isPrey(t, isHeld))
  .sort((a, b) => len(sub(a.location, sc.location)) - len(sub(b.location, sc.location)))
  .slice(0, HEADS);                                           // only six

function lunge(sc, picks) {
  wait(sc, "studio:cd_attack", 700);
  say(sc.dimension, sc.location, 40, "odyssey.scylla.snatch");
  return perform(sc, "lunge", { done: () => snatch(sc, picks) }, { still: false });
}
function snatch(sc, picks) {
  const sn = MOVES.scylla.snatch, dv = MOVES.scylla.devour, phase1 = sn.len - sn.bite;
  const live = [];
  return perform(sc, "snatch", {
    bite: () => {
      picks.filter((v) => valid(v) && !isHeld(v) && flat(v.location, sc.location) < 24).slice(0, HEADS).forEach((v, i) => {
        live.push(v);
        hurt(v, 3, sc);
        // the head that took him carries him: first along its snatch path, then up with the devour
        hold(v, sc, {
          ticks: phase1 + dv.len + 4,
          at: (h, t) => t < phase1
            ? worldOffset(h, pathAt("scylla.snatch", `head${i}`, sn.bite + t))
            : worldOffset(h, pathAt("scylla.devour", `head${i}`, t - phase1)),
          onRelease: (vv, h) => { if (h) safe("drop", () => vv.teleport(add(h.location, scale(forward(h), 4)), { keepVelocity: false })); },
        });
      });
    },
    done: () => devour(sc, live),
  }, { still: false });
}
function devour(sc, live) {
  return perform(sc, "devour", {
    bite: () => { for (const v of live) if (valid(v) && isHeld(v)) { hurt(v, 4, sc); if (isPlayer(v)) bar(v, "odyssey.scylla.devour"); } },
    done: () => { for (const v of live) if (valid(v)) release(v); perform(sc, "recoil", {}, { still: false }); },
  }, { still: false });
}
function rend(sc, boats) {
  wait(sc, "studio:cd_attack", 500);
  say(sc.dimension, sc.location, 40, "odyssey.scylla.rend");
  return perform(sc, "rend", {
    hit: () => {
      for (const b of boats) {
        if (!valid(b)) continue;
        for (const r of riders(b)) hurt(r, 6, sc);
        particle(b.dimension, "minecraft:water_splash_particle", b.location);
        safe("boat", () => b.remove());
      }
    },
  }, { still: false });
}

export function tickScylla() {
  for (const sc of creatures(SCYLLA)) {
    safe("scylla", () => {
      if (!dp(sc, "studio:init", false)) { setDp(sc, "studio:init", true); spawnCharybdisNear(sc); }
      if (busy(sc) || !ready(sc, "studio:cd_attack")) return;
      const picks = victimsOf(sc);
      if (picks.length) { lunge(sc, picks); return; }
      const boats = near(sc.dimension, sc.location, 16).filter(isBoat);
      if (boats.length) rend(sc, boats);
    });
  }
}

// ---------------------------------------------------------------- Charybdis
let chTick = 0;
const surging = (ch) => now() < dp(ch, "studio:surge_until", 0);
export function tickCharybdis() {
  chTick++;
  for (const ch of creatures(CHARYBDIS)) {
    safe("charybdis", () => {
      const dim = ch.dimension;
      if (!dp(ch, "studio:anchored", false)) {
        const spot = waterSurfaceNear(dim, ch.location) || ch.location;
        setDp(ch, "studio:anchored", true);
        setDp(ch, "studio:ax", spot.x); setDp(ch, "studio:ay", spot.y); setDp(ch, "studio:az", spot.z);
      }
      const c = { x: dp(ch, "studio:ax", ch.location.x), y: dp(ch, "studio:ay", ch.location.y), z: dp(ch, "studio:az", ch.location.z) };
      if (len(sub(ch.location, c)) > 0.4) safe("anchor", () => ch.teleport(c, { keepVelocity: false }));
      const strength = surging(ch) ? 2.4 : 1;
      if (chTick % 2 === 0) {
        for (let k = 0; k < 4; k++) {
          const a = chTick * 0.7 + k * 1.57, r = 3 + k * 5;
          particle(dim, "minecraft:bubble_column_up_particle", { x: c.x + Math.cos(a) * r, y: c.y - 0.2, z: c.z + Math.sin(a) * r });
        }
      }
      // the whirlpool gathers strength now and then
      if (!busy(ch) && ready(ch, "studio:cd_surge") && near(dim, c, 60).some((t) => isPlayer(t) && !isCreative(t))) {
        wait(ch, "studio:cd_surge", 1400);
        perform(ch, "surge", {
          start: () => { setDp(ch, "studio:surge_until", now() + MOVES.charybdis.surge.len); say(dim, c, 60, "odyssey.charybdis.surge"); },
        }, { still: false });
      }
      for (const t of near(dim, c, 28)) {
        if (t.id === ch.id || t.typeId === CHARYBDIS || t.typeId === SCYLLA || isHeld(t)) continue;
        if (isPlayer(t) && isCreative(t)) continue;
        const d = sub(c, t.location), r = Math.hypot(d.x, d.z) || 0.01;
        const radial = { x: d.x / r, z: d.z / r }, swirl = { x: -d.z / r, z: d.x / r };
        const pull = (0.035 + 0.13 * (1 - r / 28)) * strength;
        if (r < 5 && (isBoat(t) || t.typeId === "minecraft:item")) {
          if (isBoat(t) && !busy(ch) && ready(ch, "studio:cd_gulp")) {
            wait(ch, "studio:cd_gulp", 60);
            perform(ch, "gulp", {
              gulp: () => {
                for (const rd of riders(t)) hurt(rd, 6, undefined, "drowning");
                particle(dim, "minecraft:water_splash_particle", t.location);
                safe("boat", () => t.remove());
              },
            }, { still: false });
          } else if (t.typeId === "minecraft:item") {
            safe("item", () => t.remove());
          }
          continue;
        }
        if (isPlayer(t)) {
          if (chTick % 2 !== 0) continue;
          const v = { x: radial.x * pull + swirl.x * 0.08, z: radial.z * pull + swirl.z * 0.08 };
          const vl = Math.hypot(v.x, v.z) || 1;
          push(t, v, vl * 2.2, r < 5 ? -0.4 : 0);
          if (chTick % 20 === 0) bar(t, "odyssey.charybdis.drain");
        } else {
          safe("impulse", () => t.applyImpulse({ x: radial.x * pull + swirl.x * 0.08, y: r < 5 ? -0.08 : 0, z: radial.z * pull + swirl.z * 0.08 }));
        }
        if (r < 4 && chTick % 10 === 0) hurt(t, 3, undefined, "drowning");
      }
    });
  }
}
