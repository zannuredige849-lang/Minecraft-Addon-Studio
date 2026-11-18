// Companion AI System for Athena, Calypso, and yielded Circe.
// Implements: player following at comfortable distance (3.2 - 6.0 blocks), doorway/personal-space
// yielding (< 2.3 blocks), obstacle avoidance & step-up, stuck detection with safe ground teleport,
// combat assistance against nearby threats, and contextual story reactions.
import {
  add, block, byId, dirTo, dp, effect, flat, hurt, isAir, isWater, near, now, prop,
  ready, right, safe, scale, setDp, sub, valid, wait,
} from "../lib/util.js";
import { bar, burst, hear, tell } from "../lib/fx.js";
import { busy, perform } from "../lib/moves.js";
import { creatures } from "../lib/registry.js";

export const COMPANION_TYPES = ["studio:calypso", "studio:athena", "studio:circe"];
const HOSTILE_FAMILIES = new Set([
  "studio:cyclops", "studio:laestrygonian", "studio:shade", "studio:siren", "studio:scylla",
  "minecraft:zombie", "minecraft:skeleton", "minecraft:spider", "minecraft:creeper",
  "minecraft:drowned", "minecraft:phantom", "minecraft:pillager", "minecraft:vindicator",
]);

/** Find a safe solid ground spot with 2 blocks of air headroom near `center`. */
export function findSafeSpotNear(dim, center, radius = 3.5) {
  for (let k = 0; k < 10; k++) {
    const ang = (k / 10) * Math.PI * 2;
    const x = Math.floor(center.x + Math.cos(ang) * radius) + 0.5;
    const z = Math.floor(center.z + Math.sin(ang) * radius) + 0.5;
    for (let dy = 3; dy >= -4; dy--) {
      const y = Math.floor(center.y) + dy;
      const ground = block(dim, { x, y: y - 1, z });
      const feet = block(dim, { x, y, z });
      const head = block(dim, { x, y: y + 1, z });
      if (ground && !isAir(ground) && !isWater(ground) && isAir(feet) && isAir(head)) {
        return { x, y, z };
      }
    }
  }
  return undefined;
}

/** Bind or toggle an NPC as a player's active companion. */
export function bindCompanion(npc, player, toggle = false) {
  if (!valid(npc) || !valid(player)) return false;
  if (npc.typeId === "studio:circe" && !prop(npc, "studio:yielded", false)) return false;
  const currentOwner = dp(npc, "studio:companion_of", "");
  const isFollowing = dp(npc, "studio:following", false);

  if (currentOwner === player.id && toggle) {
    const nextState = !isFollowing;
    setDp(npc, "studio:following", nextState);
    setDp(npc, "studio:stuck_count", 0);
    bar(player, nextState ? "odyssey.comp.follow_on" : "odyssey.comp.follow_off");
    return nextState;
  }

  setDp(npc, "studio:companion_of", player.id);
  setDp(npc, "studio:following", true);
  setDp(npc, "studio:stuck_count", 0);
  setDp(npc, "studio:last_x", npc.location.x);
  setDp(npc, "studio:last_z", npc.location.z);
  return true;
}

/** Combat assistance & enemy warning when hostiles are near the companion or her player. */
function assistInCombat(npc, owner) {
  const dim = npc.dimension;
  const threats = near(dim, owner.location, 16).filter(
    (e) => valid(e) && e.id !== npc.id && e.id !== owner.id && HOSTILE_FAMILIES.has(e.typeId)
  );
  if (!threats.length) return false;

  const nearestThreat = threats.sort((a, b) => flat(a.location, owner.location) - flat(b.location, owner.location))[0];

  // Contextual enemy warning (cooldown 20 seconds)
  if (ready(npc, "studio:cd_warn")) {
    wait(npc, "studio:cd_warn", 400);
    if (npc.typeId === "studio:athena") tell(owner, "odyssey.comp.warn.athena");
    else if (npc.typeId === "studio:calypso") tell(owner, "odyssey.comp.warn.calypso");
    else if (npc.typeId === "studio:circe") tell(owner, "odyssey.comp.warn.circe");
  }

  // Active combat support ability (cooldown 8 seconds = 160 ticks)
  if (!busy(npc) && ready(npc, "studio:cd_assist")) {
    wait(npc, "studio:cd_assist", 160);
    if (npc.typeId === "studio:athena") {
      perform(npc, "bless", {
        give: () => {
          if (!valid(owner)) return;
          effect(owner, "resistance", 160, 0);
          effect(owner, "strength", 160, 0);
          for (const t of threats.slice(0, 3)) {
            if (flat(t.location, npc.location) < 8 && t.typeId !== "studio:scylla" && t.typeId !== "studio:cyclops") {
              hurt(t, 6, npc);
              burst(dim, "minecraft:critical_hit_emitter", t.location, 0.8, 5);
            }
          }
          bar(owner, "odyssey.comp.assist.athena");
        },
      }, { still: false });
    } else if (npc.typeId === "studio:calypso") {
      perform(npc, "offer", {
        give: () => {
          if (!valid(owner)) return;
          effect(owner, "regeneration", 140, 1);
          for (const t of threats.slice(0, 3)) {
            if (flat(t.location, npc.location) < 8) effect(t, "slowness", 100, 1);
          }
          bar(owner, "odyssey.comp.assist.calypso");
        },
      }, { still: false });
    } else if (npc.typeId === "studio:circe") {
      perform(npc, "counsel", {
        start: () => {
          for (const t of threats.slice(0, 4)) {
            if (flat(t.location, npc.location) < 10) {
              effect(t, "weakness", 160, 1);
              effect(t, "slowness", 160, 1);
            }
          }
          if (valid(owner)) bar(owner, "odyssey.comp.assist.circe");
        },
      }, { still: false });
    }
    return true;
  }
  return false;
}

/** Steer companion smoothly toward player while avoiding doorways, crowding, and obstacles. */
function steerCompanion(npc, owner) {
  const dim = npc.dimension;
  const nLoc = npc.location, pLoc = owner.location;
  const d = flat(nLoc, pLoc);

  // 1. Personal space & doorway yielding: never crowd or block the player (< 2.3 blocks)
  if (d < 2.3) {
    const away = dirTo(pLoc, nLoc);
    const side = right(owner);
    const stepOut = { x: away.x * 0.16 + side.x * 0.08, y: 0, z: away.z * 0.16 + side.z * 0.08 };
    const dest = add(nLoc, stepOut);
    if (isAir(block(dim, dest)) && !isWater(block(dim, add(dest, { x: 0, y: -1, z: 0 })))) {
      try { npc.applyImpulse(stepOut); } catch { }
    }
    setDp(npc, "studio:stuck_count", 0);
    return;
  }

  // 2. Comfortable companion range (2.3 to 5.6 blocks): hold position, face player or threats
  if (d <= 5.6) {
    setDp(npc, "studio:stuck_count", 0);
    setDp(npc, "studio:last_x", nLoc.x);
    setDp(npc, "studio:last_z", nLoc.z);
    return;
  }

  // 3. Long-distance teleport: only when genuinely far away (> 28 blocks) or in another area
  if (d > 28.0 || Math.abs(nLoc.y - pLoc.y) > 12) {
    const spot = findSafeSpotNear(dim, pLoc, 3.5);
    if (spot && ready(npc, "studio:cd_tp")) {
      wait(npc, "studio:cd_tp", 60);
      try {
        npc.teleport(spot, { keepVelocity: false });
        setDp(npc, "studio:stuck_count", 0);
        setDp(npc, "studio:last_x", spot.x);
        setDp(npc, "studio:last_z", spot.z);
      } catch { }
    }
    return;
  }

  // 4. Active following (5.6 < d <= 28.0 blocks): check progress to detect genuine stuck state
  const lx = dp(npc, "studio:last_x", nLoc.x);
  const lz = dp(npc, "studio:last_z", nLoc.z);
  const moved = Math.hypot(nLoc.x - lx, nLoc.z - lz);
  setDp(npc, "studio:last_x", nLoc.x);
  setDp(npc, "studio:last_z", nLoc.z);

  let stuck = dp(npc, "studio:stuck_count", 0);
  if (d > 7.5 && moved < 0.25) {
    stuck++;
  } else {
    stuck = Math.max(0, stuck - 1);
  }
  setDp(npc, "studio:stuck_count", stuck);

  // Teleport only if genuinely stuck behind an obstacle for >= 5 consecutive checks (2.5 seconds)
  if (stuck >= 5 && ready(npc, "studio:cd_tp")) {
    const spot = findSafeSpotNear(dim, pLoc, 3.5);
    if (spot) {
      wait(npc, "studio:cd_tp", 80);
      setDp(npc, "studio:stuck_count", 0);
      try { npc.teleport(spot, { keepVelocity: false }); } catch { }
      return;
    }
  }

  // Smooth obstacle-aware movement assistance
  const dir = dirTo(nLoc, pLoc);
  const ahead = add(nLoc, scale(dir, 1.1));
  const aheadBlock = block(dim, ahead);
  const aheadUp = block(dim, add(ahead, { x: 0, y: 1, z: 0 }));

  // Give speed effect when running to catch up (d > 10 blocks)
  if (d > 10.0) {
    effect(npc, "speed", 25, 1);
  }

  // If 1-block ledge ahead with clear headroom, step up smoothly; if 2-block wall, steer tangentially
  if (aheadBlock && !isAir(aheadBlock)) {
    if (isAir(aheadUp) && isAir(block(dim, add(ahead, { x: 0, y: 2, z: 0 })))) {
      try { npc.applyImpulse({ x: dir.x * 0.14, y: 0.36, z: dir.z * 0.14 }); } catch { }
    } else {
      const tangent = { x: -dir.z * 0.18, y: 0, z: dir.x * 0.18 };
      try { npc.applyImpulse(tangent); } catch { }
    }
  } else if (d > 7.0) {
    const speed = d > 12.0 ? 0.18 : 0.11;
    try { npc.applyImpulse({ x: dir.x * speed, y: 0, z: dir.z * speed }); } catch { }
  }
}

export function tickCompanions() {
  for (const type of COMPANION_TYPES) {
    for (const npc of creatures(type)) {
      safe("companion", () => {
        const ownerId = dp(npc, "studio:companion_of", "");
        if (!ownerId || !dp(npc, "studio:following", false)) return;
        const owner = byId(ownerId);
        if (!owner || owner.dimension.id !== npc.dimension.id) return;
        assistInCombat(npc, owner);
        if (!busy(npc)) steerCompanion(npc, owner);
      });
    }
  }
}
