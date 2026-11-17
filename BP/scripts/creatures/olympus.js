// The gods and the rest: the cattle of Apollo (graze, low), Zeus's storm, Calypso (offer, embrace), Athena (bless, appear,
// vanish) and the Trojan Horse (hatch, sally).
import { world, ItemStack } from "@minecraft/server";
import {
  add, dp, effect, isBoat, isNight, isPlayer, near, nearestPlayer, now, ready, ridingOn, riders, runCommand, safe,
  setDp, valid, wait, later, rand,
} from "../lib/util.js";
import { bar, say, sound, tell } from "../lib/fx.js";
import { busy, perform } from "../lib/moves.js";
import { creatures } from "../lib/registry.js";

export const CATTLE = "studio:sun_cattle", CALYPSO = "studio:calypso", ATHENA = "studio:athena", HORSE = "studio:trojan_horse";

// ---------------------------------------------------------------- the cattle of Apollo
export function tickCattle() {
  for (const c of creatures(CATTLE)) {
    safe("cattle", () => {
      if (busy(c) || !ready(c, "studio:cd_graze") || Math.random() > 0.5) return;
      wait(c, "studio:cd_graze", 200 + Math.floor(rand(0, 400)));
      perform(c, "graze", {}, { still: false });
    });
  }
}
export function onCattleHurt(c) { if (!busy(c)) perform(c, "low", {}, { still: false }); }

/** The starving men kill one of Apollo's cattle; Zeus sends a storm that sinks their ship. */
export function godsStorm(p) {
  const dim = p.dimension;
  say(dim, p.location, 64, "odyssey.zeus.storm");
  runCommand(dim, "weather thunder 6000");
  sound(dim, "odyssey.world.storm", p.location, 1, 1);
  for (let i = 1; i <= 10; i++) {
    later(i * 60, () => {
      if (!valid(p)) return;
      const a = Math.random() * Math.PI * 2, d = 3 + Math.random() * 6;
      const at = add(p.location, { x: Math.cos(a) * d, y: 0, z: Math.sin(a) * d });
      safe("lightning", () => p.dimension.spawnEntity("minecraft:lightning_bolt", at));
      const ride = ridingOn(p);
      for (const b of near(p.dimension, p.location, 24)) {
        if (isBoat(b) && (b.id === ride?.id || Math.hypot(b.location.x - at.x, b.location.z - at.z) < 8)) safe("boat", () => b.remove());
      }
    });
  }
}

// ---------------------------------------------------------------- Calypso: the lotus and the embrace
function giveItem(e, p, id) { safe("item", () => e.dimension.spawnItem(new ItemStack(id, 1), p.location)); }
export function offerLotus(c) {
  const p = nearestPlayer(c, 6);
  if (!p || !ready(p, "studio:next_lotus")) return;
  wait(p, "studio:next_lotus", 1200);
  perform(c, "offer", { give: () => { if (valid(p)) { giveItem(c, p, "studio:lotus_flower"); tell(p, "odyssey.calypso.lotus"); } } }, { still: false });
}
export function embrace(c) {
  const p = nearestPlayer(c, 6);
  if (!p) return;
  perform(c, "embrace", {
    hug: () => {
      if (!valid(p)) return;
      effect(p, "regeneration", 100, 1);
      effect(p, "instant_health", 1, 1);
      tell(p, "odyssey.calypso.embrace");
    },
  }, { still: false });
}

/** The lotus: a peaceful haze, and the memories (your levels) slip away. */
export function onLotus(p) {
  safe("lotus", () => p.addLevels(-p.level));
  effect(p, "regeneration", 600, 0);
  effect(p, "slowness", 600, 0);
  bar(p, "odyssey.calypso.eaten");
}

// ---------------------------------------------------------------- Athena
export function bless(a) {
  const p = nearestPlayer(a, 6);
  if (!p || !ready(p, "studio:next_blessing")) return;
  wait(p, "studio:next_blessing", 12000);
  perform(a, "bless", {
    give: () => { if (valid(p)) { effect(p, "resistance", 4800, 0); tell(p, "odyssey.athena.bless"); } },
  }, { still: false });
}
/** In an hour of crisis Athena appears to a man of the journey: "Return home." */
export function vision(p) {
  if (!dp(p, "studio:journey", false) || !ready(p, "studio:next_vision")) return;
  wait(p, "studio:next_vision", 24000);
  const at = add(p.location, { x: 3, y: 0, z: 0 });
  const a = safe("athena", () => p.dimension.spawnEntity(ATHENA, at));
  if (!a) return;
  perform(a, "appear", {
    done: () => {
      if (valid(p)) { effect(p, "resistance", 2400, 1); effect(p, "regeneration", 200, 1); tell(p, "odyssey.athena.vision"); }
      perform(a, "vanish", { done: () => safe("athena", () => a.remove()) }, { still: false, force: true });
    },
  }, { still: false });
}

// ---------------------------------------------------------------- the Trojan Horse: the Greeks hide inside
export function tickHorses() {
  for (const p of world.getAllPlayers()) {
    safe("rider", () => { if (ridingOn(p)?.typeId === HORSE) effect(p, "invisibility", 60); });
  }
  const day = Math.floor(now() / 24000);
  for (const h of creatures(HORSE)) {
    safe("horse", () => {
      const inside = riders(h).length;
      if (inside !== dp(h, "studio:inside", 0)) {
        if (!busy(h)) perform(h, "hatch", {}, { still: false });
        if (inside > dp(h, "studio:inside", 0)) say(h.dimension, h.location, 8, "odyssey.horse.hide");
        setDp(h, "studio:inside", inside);
      }
      if (inside > 0 && isNight() && dp(h, "studio:sally_day", -1) !== day && !busy(h)) {      // at night the Greeks pour out
        setDp(h, "studio:sally_day", day);
        perform(h, "sally", {
          eject: () => {
            const out = riders(h);
            safe("eject", () => h.getComponent("minecraft:rideable")?.ejectRiders?.());
            for (const r of out) { effect(r, "strength", 600, 1); effect(r, "speed", 600, 1); if (isPlayer(r)) tell(r, "odyssey.horse.sally"); }
            say(h.dimension, h.location, 24, "odyssey.horse.sally");
          },
        }, { still: false });
      }
    });
  }
}
