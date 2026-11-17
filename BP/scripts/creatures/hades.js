// Hades: the blood sacrifice. Across the river Oceanus the dead rise from the black sand. A sheep sacrificed on black sand
// raises Sinon's shade (he reproaches Odysseus), Agamemnon's shade (he tells of his murder) and Tiresias, who prophesies.
// Then six shades come at a run: Odysseus's unburied crew, who want him to join them in their shame.
// Moves: shade rise / sink / speak_sinon / speak_agamemnon / grasp; Tiresias rise / speak / sink.
import {
  add, effect, forward, hurt, prop, push, ready, right, ringSpot, safe, scale, trigger, valid, wait, later,
  nearestPlayer, dirTo,
} from "../lib/util.js";
import { bar, hear, say } from "../lib/fx.js";
import { busy, perform } from "../lib/moves.js";
import { creatures } from "../lib/registry.js";

export const SHADE = "studio:shade", TIRESIAS = "studio:tiresias";
export const SACRIFICE_BLOCKS = new Set(["minecraft:soul_sand", "minecraft:soul_soil", "minecraft:black_concrete_powder"]);
/** Black sand: soul sand, soul soil or black concrete powder (older game versions name it concrete_powder + a colour). */
export function isBlackSand(b) {
  if (!b) return false;
  if (SACRIFICE_BLOCKS.has(b.typeId)) return true;
  try { return b.typeId === "minecraft:concrete_powder" && b.permutation?.getState?.("color") === "black"; } catch { return false; }
}
export const SACRIFICE_VICTIMS = new Set(["minecraft:sheep"]);            // the film: "they sacrifice some sheep"

const rise = (e) => perform(e, "rise", { start: () => trigger(e, "studio:rise"), done: () => trigger(e, "studio:risen") }, { still: false, force: true });
const sinkAway = (e) => { if (valid(e)) perform(e, "sink", { done: () => safe("shade", () => e.remove()) }, { still: false, force: true }); };

export function summonDead(p) {
  if (!ready(p, "studio:next_sacrifice")) return;
  wait(p, "studio:next_sacrifice", 3600);
  const dim = p.dimension, here = p.location, f = forward(p), r = right(p);
  const spawn = (type, off, ev) => {
    const e = safe("spawn", () => dim.spawnEntity(type, add(here, off)));
    if (!e) return undefined;
    if (ev) trigger(e, ev);
    rise(e);
    return e;
  };
  say(dim, here, 48, "odyssey.hades.rise");
  for (const q of dim.getPlayers({ location: here, maxDistance: 48 })) hear(q, "odyssey.shade.whispers", here, 1, 1);
  const sinon = spawn(SHADE, add(scale(f, 3), scale(r, -4)), "studio:as_sinon");
  const aga = spawn(SHADE, add(scale(f, 3), scale(r, 4)), "studio:as_agamemnon");
  const tir = spawn(TIRESIAS, scale(f, 4));
  later(60, () => { if (valid(sinon)) perform(sinon, "speak_sinon", {}, { still: false }); say(dim, here, 48, "odyssey.hades.sinon"); });
  later(140, () => { if (valid(aga)) perform(aga, "speak_agamemnon", {}, { still: false }); say(dim, here, 48, "odyssey.hades.agamemnon"); });
  later(220, () => { if (valid(tir)) perform(tir, "speak", {}, { still: false }); say(dim, here, 48, "odyssey.hades.tiresias"); });
  later(290, () => say(dim, here, 48, "odyssey.hades.fate"));
  later(350, () => {
    say(dim, here, 48, "odyssey.hades.crew");
    for (let i = 0; i < 6; i++) {
      const a = Math.atan2(-f.z, -f.x) + (i - 2.5) * 0.45;
      safe("crew", () => {
        const s = dim.spawnEntity(SHADE, ringSpot(here, 10 + (i % 2) * 2, a));
        trigger(s, "studio:as_crew");
        rise(s);
        later(1800, () => sinkAway(s));
      });
    }
  });
  later(400, () => { sinkAway(tir); sinkAway(sinon); sinkAway(aga); });
}

/** The crew shades grasp at whoever they reach: the dead want him to join them. */
export function tickShades() {
  for (const sh of creatures(SHADE)) {
    safe("shade", () => {
      if (prop(sh, "studio:variant", 0) !== 0 || busy(sh) || !ready(sh, "studio:cd_grasp")) return;
      const p = nearestPlayer(sh, 2.8);
      if (!p) return;
      wait(sh, "studio:cd_grasp", 70);
      perform(sh, "grasp", {
        hit: () => {
          if (!valid(p)) return;
          hurt(p, 5, sh);
          effect(p, "slowness", 60, 1);
          push(p, dirTo(p.location, sh.location), 0.4, 0.05);
          bar(p, "odyssey.hades.grasp");
        },
      });
    });
  }
}
