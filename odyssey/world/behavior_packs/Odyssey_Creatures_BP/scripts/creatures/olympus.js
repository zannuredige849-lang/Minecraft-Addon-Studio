// The gods and the rest: the cattle of Apollo (graze, low, hurt), Zeus's storm,
// Calypso (15-second Lotus Gift System, embrace, companion toggle), Athena (bless, appear, vanish,
// chapter guidance, companion toggle) and the Trojan Horse (hatch, sally).
import { world, ItemStack } from "@minecraft/server";
import {
  add, dp, effect, isBoat, isCreative, isNight, isPlayer, near, nearestPlayer, now, playersNear,
  ready, ridingOn, riders, runCommand, safe, setDp, valid, wait, later, rand,
} from "../lib/util.js";
import { bar, hear, say, sound, tell } from "../lib/fx.js";
import { busy, perform } from "../lib/moves.js";
import { creatures } from "../lib/registry.js";
import { bindCompanion } from "../world/companions.js";
import { onStoryEvent, tellChapterGuidance } from "../world/story.js";

export const CATTLE = "studio:sun_cattle", CALYPSO = "studio:calypso", ATHENA = "studio:athena", HORSE = "studio:trojan_horse";

// 15 seconds = 300 game ticks (at 20 ticks/second)
export const LOTUS_INTERVAL_TICKS = 300;
const lotusLocks = new Set(); // per-player mutex preventing duplicate simultaneous rewards

/** Check whether the player's inventory has space to accept `amount` of `typeId` (max stack 8 for lotus). */
export function canAcceptItem(p, typeId, maxStack = 8, amount = 1) {
  try {
    const inv = p.getComponent("minecraft:inventory")?.container;
    if (!inv) return false;
    if (inv.emptySlotsCount > 0) return true;
    for (let i = 0; i < inv.size; i++) {
      const it = inv.getItem(i);
      if (it && it.typeId === typeId && it.amount + amount <= (it.maxAmount ?? maxStack)) {
        return true;
      }
    }
    return false;
  } catch {
    return false;
  }
}

/**
 * Safely grant 1 Lotus Flower (`studio:lotus_flower`) to an eligible player if the 15-second
 * cooldown has elapsed and the player's inventory can accept it. Timer is tracked per player
 * via `studio:next_lotus` independently of animation playback.
 */
export function tryGiveLotus(c, p, { isAuto = false } = {}) {
  if (!valid(c) || !valid(p) || !isPlayer(p)) return false;
  if (lotusLocks.has(p.id)) return false;

  const nextTick = dp(p, "studio:next_lotus", 0);
  const curTick = now();
  if (curTick < nextTick) {
    if (!isAuto) {
      const secs = Math.max(1, Math.ceil((nextTick - curTick) / 20));
      bar(p, "odyssey.calypso.lotus_cd", String(secs));
    }
    return false;
  }

  if (!canAcceptItem(p, "studio:lotus_flower", 8, 1)) {
    if (!isAuto || ready(p, "studio:cd_inv_warn")) {
      wait(p, "studio:cd_inv_warn", 100);
      bar(p, "odyssey.calypso.inv_full");
    }
    return false;
  }

  lotusLocks.add(p.id);
  try {
    const inv = p.getComponent("minecraft:inventory")?.container;
    if (!inv) return false;
    const leftover = inv.addItem(new ItemStack("studio:lotus_flower", 1));
    if (leftover) return false; // Safeguard: never drop duplicates on the ground

    // Lock in the exact 15-second (300-tick) cooldown independent of animation state
    setDp(p, "studio:next_lotus", curTick + LOTUS_INTERVAL_TICKS);
    setDp(p, "studio:lotus_active", true);

    hear(p, "odyssey.calypso.lotus_chime", c.location, 0.9, 1.0);
    tell(p, "odyssey.calypso.lotus");
    bar(p, "odyssey.calypso.lotus_bar");
    onStoryEvent(p, "lotus_gifted");

    // Play Calypso's offer animation visually if she is not already mid-move
    if (!busy(c)) {
      perform(c, "offer", {}, { still: false });
    }
    return true;
  } finally {
    lotusLocks.delete(p.id);
  }
}

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
export function onCattleHurt(c) {
  if (!busy(c) && ready(c, "studio:cd_hurt")) {
    wait(c, "studio:cd_hurt", 20);
    perform(c, "hurt", {}, { still: false });
  }
}

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

// ---------------------------------------------------------------- Calypso: 15s lotus gift, embrace & companion
export function offerLotus(c) {
  const p = nearestPlayer(c, 6, () => true);
  if (!p) return;
  setDp(p, "studio:lotus_active", true);
  if (!dp(c, "studio:companion_of", "")) {
    bindCompanion(c, p, false);
  }
  tryGiveLotus(c, p, { isAuto: false });
}

/** Automatic 15-second Lotus gift cycle for eligible players near Calypso. */
export function tickCalypso() {
  for (const c of creatures(CALYPSO)) {
    safe("calypso", () => {
      for (const p of playersNear(c.dimension, c.location, 6)) {
        if (!valid(p)) continue;
        // Once a player has interacted with Calypso or is on Ogygia with her, automatically gift Lotus every 15s
        if (dp(p, "studio:lotus_active", true)) {
          tryGiveLotus(c, p, { isAuto: true });
        }
      }
    });
  }
}

export function embrace(c) {
  const p = nearestPlayer(c, 6, () => true);
  if (!p) return;
  bindCompanion(c, p, true);
  tellChapterGuidance(p, CALYPSO);
  if (!busy(c)) {
    perform(c, "embrace", {
      hug: () => {
        if (!valid(p)) return;
        effect(p, "regeneration", 100, 1);
        effect(p, "instant_health", 1, 1);
        tell(p, "odyssey.calypso.embrace");
      },
    }, { still: false });
  }
}

/** The lotus: a peaceful haze, and the memories (your levels) slip away. */
export function onLotus(p) {
  safe("lotus", () => { if (p.level > 0) p.addLevels(-p.level); });
  effect(p, "regeneration", 600, 0);
  effect(p, "slowness", 200, 0);
  bar(p, "odyssey.calypso.eaten");
}

// ---------------------------------------------------------------- Athena: blessing, chapter guidance & companion
export function bless(a) {
  const p = nearestPlayer(a, 6, () => true);
  if (!p) return;
  if (p.isSneaking) {
    bindCompanion(a, p, true);
  } else if (!dp(a, "studio:companion_of", "")) {
    bindCompanion(a, p, false);
  }
  tellChapterGuidance(p, ATHENA);
  if (Math.hypot(a.location.x - (-420), a.location.z - (-200)) < 65) {
    onStoryEvent(p, "ithaca_blessed");
  }
  if (!ready(p, "studio:next_blessing")) return;
  wait(p, "studio:next_blessing", 600);
  perform(a, "bless", {
    give: () => {
      if (valid(p)) {
        effect(p, "resistance", 4800, 0);
        tell(p, "odyssey.athena.bless");
      }
    },
  }, { still: false });
}

/** In an hour of crisis Athena appears to a man of the journey: "Return home." */
export function vision(p) {
  if (!dp(p, "studio:journey", false) || !ready(p, "studio:next_vision")) return;
  wait(p, "studio:next_vision", 12000);
  const at = add(p.location, { x: 3, y: 0, z: 0 });
  const a = safe("athena", () => p.dimension.spawnEntity(ATHENA, at));
  if (!a) return;
  perform(a, "appear", {
    done: () => {
      if (valid(p)) {
        effect(p, "resistance", 2400, 1);
        effect(p, "regeneration", 200, 1);
        tell(p, "odyssey.athena.vision");
      }
      perform(a, "vanish", { done: () => safe("athena", () => a.remove()) }, { still: false, force: true });
    },
  }, { still: false });
}

// ---------------------------------------------------------------- the Trojan Horse: the Greeks hide inside
export function tickHorses() {
  for (const p of world.getAllPlayers()) {
    safe("rider", () => {
      if (ridingOn(p)?.typeId === HORSE) {
        effect(p, "invisibility", 60);
        onStoryEvent(p, "horse_hidden");
      }
    });
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
      if (inside > 0 && isNight() && dp(h, "studio:sally_day", -1) !== day && !busy(h)) {
        setDp(h, "studio:sally_day", day);
        perform(h, "sally", {
          eject: () => {
            const out = riders(h);
            safe("eject", () => h.getComponent("minecraft:rideable")?.ejectRiders?.());
            for (const r of out) {
              effect(r, "strength", 600, 1);
              effect(r, "speed", 600, 1);
              if (isPlayer(r)) tell(r, "odyssey.horse.sally");
            }
            say(h.dimension, h.location, 24, "odyssey.horse.sally");
          },
        }, { still: false });
      }
    });
  }
}
