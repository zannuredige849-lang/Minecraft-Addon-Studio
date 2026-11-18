// Fully Functional Ancient Greek Ship System (studio:greek_ship & studio:ship_crew).
// Inspired by Odysseus's crimson-sailed wooden galley in Christopher Nolan's The Odyssey (2026).
// Implements:
//   - Walkable deck & stern quarterdeck floor collision + port/starboard railing bounds + anti-hull-trap guard
//   - Single Helmsman steering control with smooth yaw interpolation & safe helm transfer
//   - 4 Speed Gears: 0 = Anchored, 1 = Half Speed (Oars), 2 = Full Speed (Crimson Sail + Oars), 3 = Reverse (Back Oars)
//   - 4 Synchronized Ithacan Oarsmen (studio:ship_crew) pinned to rowing benches
//   - Controlled water buoyancy, bow wake/oar splash particles, and automatic pier docking stop
//   - 3-Tier Hull & Sail Damage + Shipwright Repair Kit system (never despawns on damage)
//   - 7-Step Action-Driven Ship Quest Chain & 4 Multi-Shot Ship Cutscenes
import { questEvent } from "./quests.js";
import { world } from "@minecraft/server";
import {
  add, block, byId, dp, flat, heldItem, isAir, isPlayer, isWater, near, nearestPlayer,
  now, playersNear, prop, ready, riders, ridingOn, safe, setDp, setProp, valid, wait, waterSurfaceNear,
} from "../lib/util.js";
import { bar, burst, hear, particle, say, sound, tell } from "../lib/fx.js";
import { perform } from "../lib/moves.js";
import { creatures } from "../lib/registry.js";
import { SITES } from "../data/sites.js";
import { playCutscene } from "./cinematics.js";
import { onProgressionStoryMilestone } from "./progression.js";

export const SHIP_TYPE = "studio:greek_ship";
export const CREW_TYPE = "studio:ship_crew";
export const HORN_ITEM = "studio:ship_helm_horn";
export const REPAIR_ITEM = "studio:ship_repair_kit";

const SPEED_VALUES = [0.0, 0.22, 0.38, -0.12]; // Stop, Oar Cruise, Full Sail + Oars, Reverse
const DAMAGE_SPEED_MULT = [1.0, 0.80, 0.50];   // Intact, Weathered/Damaged, Critical
const CREW_OFFSETS = [
  [-0.95, 1.18, -1.1],
  [ 0.95, 1.18, -1.1],
  [-0.95, 1.18,  0.9],
  [ 0.95, 1.18,  0.9],
];

function degToRad(d) { return (d * Math.PI) / 180; }
function normalizeAngle(deg) {
  let a = ((deg + 180) % 360 + 360) % 360 - 180;
  return a;
}

/** Unit forward vector (along ship prow) and right vector (starboard) from yaw in degrees. */
export function shipVectors(ship) {
  let yaw = dp(ship, "studio:yaw", undefined);
  if (yaw === undefined) {
    try { yaw = ship.getRotation().y; } catch { yaw = 0; }
    setDp(ship, "studio:yaw", yaw);
  }
  const rad = degToRad(yaw);
  const fx = -Math.sin(rad), fz = Math.cos(rad);
  const rx = Math.cos(rad),  rz = Math.sin(rad);
  return { yaw, F: { x: fx, y: 0, z: fz }, R: { x: rx, y: 0, z: rz } };
}

/** Convert world offset (wx, wz) relative to ship center into local [forward, right] coordinates. */
function worldToShipLocal(ship, loc) {
  const { F, R } = shipVectors(ship);
  const dx = loc.x - ship.location.x;
  const dz = loc.z - ship.location.z;
  return {
    localF: dx * F.x + dz * F.z,
    localR: dx * R.x + dz * R.z,
    dy: loc.y - ship.location.y,
  };
}

function shipLocalToWorld(ship, localF, localUp, localR) {
  const { F, R } = shipVectors(ship);
  return {
    x: ship.location.x + F.x * localF + R.x * localR,
    y: ship.location.y + localUp,
    z: ship.location.z + F.z * localF + R.z * localR,
  };
}

// ------------------------------------------------------------------ 7-Step Interactive Ship Quest Chain
export function advanceShipQuest(p, stepId) {
  if (!valid(p) || !isPlayer(p)) return;
  safe("ship.quest", () => questEvent(p, stepId));
  const flag = `studio:ship_q_${stepId}`;
  if (dp(p, flag, false)) return;
  setDp(p, flag, true);
  onProgressionStoryMilestone(p, stepId);

  switch (stepId) {
    case "find_ship":
      tell(p, "odyssey.ship.q.find_done");
      bar(p, "odyssey.ship.q.next_crew");
      playShipCutscene("ship_intro", p);
      break;
    case "gather_crew":
      tell(p, "odyssey.ship.q.crew_done");
      bar(p, "odyssey.ship.q.next_prep");
      break;
    case "prepare_vessel":
      tell(p, "odyssey.ship.q.prep_done");
      bar(p, "odyssey.ship.q.next_board");
      break;
    case "board_ship":
      tell(p, "odyssey.ship.q.board_done");
      bar(p, "odyssey.ship.q.next_sails");
      break;
    case "raise_sails":
      tell(p, "odyssey.ship.q.sails_done");
      bar(p, "odyssey.ship.q.next_depart");
      playShipCutscene("ship_departure", p);
      break;
    case "leave_harbor":
      tell(p, "odyssey.ship.q.depart_done");
      bar(p, "odyssey.ship.q.next_dock");
      break;
    case "dock_safely":
      tell(p, "odyssey.ship.q.dock_done");
      bar(p, "odyssey.ship.q.complete");
      playShipCutscene("ship_arrival_dock", p);
      break;
    default:
      break;
  }
}

export function playShipCutscene(kind, player) {
  if (!valid(player)) return;
  const c = player.location;
  if (kind === "ship_intro") {
    playCutscene("ship_intro", c, [
      { tick: 2,  shotType: "wide_establishing", anchor: c, titleKey: "odyssey.ship.title", subKey: "odyssey.ship.sub.intro", sayKey: "odyssey.ship.cin.intro" },
      { tick: 45, shotType: "tracking_shot",     anchor: c },
    ], 85, [player]);
  } else if (kind === "ship_departure") {
    playCutscene("ship_departure", c, [
      { tick: 2,  shotType: "aerial_pan",     anchor: c, titleKey: "odyssey.ship.title.depart", subKey: "odyssey.ship.sub.depart", sayKey: "odyssey.ship.cin.depart" },
      { tick: 40, shotType: "dynamic_action", anchor: c, height: 3 },
    ], 80, [player]);
  } else if (kind === "ship_arrival_dock") {
    playCutscene("ship_arrival_dock", c, [
      { tick: 2,  shotType: "wide_establishing", anchor: c, titleKey: "odyssey.ship.title.dock", subKey: "odyssey.ship.sub.dock", sayKey: "odyssey.ship.cin.dock" },
    ], 65, [player]);
  }
}

// ------------------------------------------------------------------ Spawn & Crew Initialization
export function ensureHarborShip(dim, x = 0, y = 62, z = -44) {
  if (near(dim, { x, y, z }, 45, SHIP_TYPE).length > 0) return;
  safe("spawn_ship", () => {
    const s = dim.spawnEntity(SHIP_TYPE, { x, y: y + 0.2, z });
    if (s) {
      setDp(s, "studio:yaw", 180);
      setDp(s, "studio:hull_hp", 300);
      initShipCrew(s);
    }
  });
}

export function initShipCrew(ship) {
  if (!valid(ship) || dp(ship, "studio:crew_init", false)) return;
  setDp(ship, "studio:crew_init", true);
  if (dp(ship, "studio:hull_hp", undefined) === undefined) setDp(ship, "studio:hull_hp", 300);
  const crewIds = [];
  for (let i = 0; i < CREW_OFFSETS.length; i++) {
    const [rx, up, fz] = CREW_OFFSETS[i];
    const pos = shipLocalToWorld(ship, fz, up, rx);
    const c = safe("crew", () => ship.dimension.spawnEntity(CREW_TYPE, pos));
    if (c) {
      setDp(c, "studio:ship_id", ship.id);
      setDp(c, "studio:seat_idx", i);
      crewIds.push(c.id);
    }
  }
  setDp(ship, "studio:crew_ids", JSON.stringify(crewIds));
}

function getShipCrew(ship) {
  let ids = [];
  try { ids = JSON.parse(dp(ship, "studio:crew_ids", "[]")); } catch { ids = []; }
  const list = ids.map(byId).filter(valid);
  return list;
}

// ------------------------------------------------------------------ Helmsman, Speed Gears & Commands
function resolveHelmsman(ship) {
  const rds = riders(ship).filter(isPlayer);
  const deckPlayers = playersNear(ship.dimension, ship.location, 5.5).filter((p) => {
    const loc = worldToShipLocal(ship, p.location);
    return Math.abs(loc.localF) <= 4.4 && Math.abs(loc.localR) <= 1.7 && Math.abs(loc.dy) <= 2.5;
  });
  const candidates = [...new Set([...rds, ...deckPlayers])];
  if (!candidates.length) {
    setDp(ship, "studio:helmsman", "");
    return undefined;
  }
  const curId = dp(ship, "studio:helmsman", "");
  const cur = candidates.find((p) => p.id === curId);
  if (cur) return cur;
  const next = candidates[0];
  setDp(ship, "studio:helmsman", next.id);
  advanceShipQuest(next, "board_ship");
  bar(next, "odyssey.ship.helm_taken");
  return next;
}

export function onUseShipHorn(p) {
  if (!valid(p)) return;
  const ship = near(p.dimension, p.location, 9, SHIP_TYPE)[0];
  if (!ship) {
    bar(p, "odyssey.ship.no_ship_near");
    return;
  }
  initShipCrew(ship);
  advanceShipQuest(p, "gather_crew");

  // Ensure player is Helmsman if no one else holds the helm
  const helm = resolveHelmsman(ship) ?? p;
  if (helm.id !== p.id && !p.isSneaking) {
    bar(p, "odyssey.ship.other_helmsman");
    return;
  }
  setDp(ship, "studio:helmsman", p.id);
  advanceShipQuest(p, "board_ship");

  if (p.isSneaking) {
    // Sneak + Horn: Rally Crew & Safe Disembark / Mooring Command
    sound(ship.dimension, "odyssey.ship.crew_command", ship.location, 0.9, 1.0);
    for (const c of getShipCrew(ship)) {
      perform(c, "cheer", {}, { still: false, force: true });
    }
    setProp(ship, "studio:speed_state", 0);
    setProp(ship, "studio:sail_deployed", false);
    setProp(ship, "studio:turn_state", 0);
    bar(p, "odyssey.ship.cmd.anchored");
    return;
  }

  // Standing + Horn: Cycle Speed Gear (0: Stop -> 1: Half Oars -> 2: Full Sail + Oars -> 3: Reverse)
  const curSpeed = prop(ship, "studio:speed_state", 0);
  const nextSpeed = (curSpeed + 1) % 4;
  setProp(ship, "studio:speed_state", nextSpeed);
  const sailOn = nextSpeed === 2;
  setProp(ship, "studio:sail_deployed", sailOn);

  if (nextSpeed === 0) {
    sound(ship.dimension, "odyssey.ship.dock_thud", ship.location, 0.85, 1.0);
    bar(p, "odyssey.ship.gear.0");
  } else if (nextSpeed === 1) {
    sound(ship.dimension, "odyssey.ship.crew_command", ship.location, 0.85, 1.0);
    sound(ship.dimension, "odyssey.ship.oar_row", ship.location, 0.85, 1.0);
    bar(p, "odyssey.ship.gear.1");
  } else if (nextSpeed === 2) {
    sound(ship.dimension, "odyssey.ship.sail_unfurl", ship.location, 0.95, 1.0);
    sound(ship.dimension, "odyssey.ship.sail_wind", ship.location, 0.75, 1.0);
    bar(p, "odyssey.ship.gear.2");
    advanceShipQuest(p, "raise_sails");
  } else if (nextSpeed === 3) {
    sound(ship.dimension, "odyssey.ship.oar_row", ship.location, 0.8, 0.85);
    bar(p, "odyssey.ship.gear.3");
  }
}

export function onUseRepairKit(p) {
  if (!valid(p)) return;
  const ship = near(p.dimension, p.location, 8, SHIP_TYPE)[0];
  if (!ship) {
    bar(p, "odyssey.ship.no_ship_near");
    return;
  }
  const hp = dp(ship, "studio:hull_hp", 300);
  const newHp = Math.min(300, hp + 100);
  setDp(ship, "studio:hull_hp", newHp);
  updateShipDamageState(ship, newHp);
  sound(ship.dimension, "odyssey.ship.repair_hammer", ship.location, 0.95, 1.0);
  burst(ship.dimension, "minecraft:villager_happy", add(ship.location, { x: 0, y: 1.5, z: 0 }), 1.8, 8);
  advanceShipQuest(p, "prepare_vessel");
  bar(p, "odyssey.ship.repaired", String(Math.round((newHp / 300) * 100)));
}

function updateShipDamageState(ship, hp) {
  const state = hp > 180 ? 0 : (hp > 75 ? 1 : 2);
  setProp(ship, "studio:damage_state", state);
}

export function onShipHurt(ship, amount = 25) {
  if (!valid(ship)) return;
  const curHp = dp(ship, "studio:hull_hp", 300);
  // Clamp at 15 HP so the ship never vanishes in the ocean
  const nextHp = Math.max(15, curHp - Math.max(8, amount));
  setDp(ship, "studio:hull_hp", nextHp);
  updateShipDamageState(ship, nextHp);
  try {
    const hComp = ship.getComponent("minecraft:health");
    if (hComp && hComp.currentValue < 100) hComp.resetToMaxValue?.();
  } catch { }
  if (ready(ship, "studio:cd_ship_hurt")) {
    wait(ship, "studio:cd_ship_hurt", 16);
    perform(ship, "hurt", {}, { still: false, force: true });
    sound(ship.dimension, "odyssey.ship.damage_crack", ship.location, 0.95, 1.0);
    for (const p of playersNear(ship.dimension, ship.location, 12)) {
      bar(p, "odyssey.ship.damaged_warn", String(Math.round((nextHp / 300) * 100)));
    }
  }
}

// ------------------------------------------------------------------ 20 Hz Fast Loop: Movement, Steering & Walkable Deck Collision
export function tickShipsFast() {
  for (const ship of creatures(SHIP_TYPE)) {
    safe("ship_fast", () => {
      initShipCrew(ship);
      const dim = ship.dimension;
      const loc = ship.location;
      const speedState = prop(ship, "studio:speed_state", 0);
      const dmgState = prop(ship, "studio:damage_state", 0);
      const helm = resolveHelmsman(ship);

      // If no helmsman is aboard and ship was moving, bring to safe idle stop
      if (!helm && speedState !== 0) {
        setProp(ship, "studio:speed_state", 0);
        setProp(ship, "studio:turn_state", 0);
        return;
      }

      let { yaw, F, R } = shipVectors(ship);
      let turnState = 0;

      // Smooth steering toward Helmsman's view direction when moving
      if (helm && speedState !== 0) {
        try {
          const rot = helm.getRotation();
          const diff = normalizeAngle(rot.y - yaw);
          if (Math.abs(diff) > 4.0) {
            const step = Math.max(-2.6, Math.min(2.6, diff * 0.18));
            yaw = normalizeAngle(yaw + step);
            setDp(ship, "studio:yaw", yaw);
            turnState = step < -0.4 ? -1 : (step > 0.4 ? 1 : 0);
            if (ready(ship, "studio:cd_rudder_sfx") && Math.abs(diff) > 18) {
              wait(ship, "studio:cd_rudder_sfx", 45);
              sound(dim, "odyssey.ship.steer_rudder", loc, 0.7, 1.0);
            }
          }
        } catch { }
      }
      if (prop(ship, "studio:turn_state", 0) !== turnState) {
        setProp(ship, "studio:turn_state", turnState);
      }

      const rad = degToRad(yaw);
      F = { x: -Math.sin(rad), y: 0, z: Math.cos(rad) };
      R = { x: Math.cos(rad),  y: 0, z: Math.sin(rad) };

      // Calculate velocity vector with damage multiplier
      const baseSpeed = SPEED_VALUES[speedState] ?? 0.0;
      const mult = DAMAGE_SPEED_MULT[dmgState] ?? 1.0;
      const vMag = baseSpeed * mult;
      let dx = F.x * vMag, dz = F.z * vMag;

      // Check water ahead at bow (+4.5 blocks) and stern (-4.5 blocks)
      if (Math.abs(vMag) > 0.001) {
        const probeDist = vMag > 0 ? 4.8 : -4.8;
        const probePos = { x: loc.x + F.x * probeDist, y: Math.floor(loc.y), z: loc.z + F.z * probeDist };
        const aheadBlock = block(dim, probePos);
        const waterUnderAhead = block(dim, { x: probePos.x, y: Math.floor(loc.y) - 1, z: probePos.z });
        if ((aheadBlock && !isAir(aheadBlock) && !isWater(aheadBlock)) || (waterUnderAhead && !isWater(waterUnderAhead) && !isAir(waterUnderAhead))) {
          // Gently dock/stop at pier or shoreline without clipping into land
          dx = 0; dz = 0;
          setProp(ship, "studio:speed_state", 0);
          setProp(ship, "studio:turn_state", 0);
          sound(dim, "odyssey.ship.dock_thud", loc, 0.9, 1.0);
          if (helm) {
            bar(helm, "odyssey.ship.docked_stop");
            // Check if docked near any non-Ogygia island harbor to complete dock_safely quest
            if (SITES.some((s) => s.id !== "ogygia" && flat(loc, s) < s.r + 25)) {
              advanceShipQuest(helm, "dock_safely");
            }
          }
        }
      }

      // Controlled water surface buoyancy
      const surf = waterSurfaceNear(dim, loc);
      const targetY = surf ? surf.y - 0.1 : loc.y;
      const nextShipPos = { x: loc.x + dx, y: targetY, z: loc.z + dz };

      try {
        ship.teleport(nextShipPos, { keepVelocity: false, rotation: { x: 0, y: yaw } });
      } catch { }

      // Pin 4 Crew Oarsmen to their rowing thwarts & sync their animations
      const crewList = getShipCrew(ship);
      const isStorm = prop(ship, "studio:storm", false);
      const desiredCrewAnim = isStorm ? "brace" : (speedState !== 0 ? "row" : "none");
      crewList.forEach((c, idx) => {
        const [rx, up, fz] = CREW_OFFSETS[idx % CREW_OFFSETS.length];
        const cPos = {
          x: nextShipPos.x + F.x * fz + R.x * rx,
          y: nextShipPos.y + up,
          z: nextShipPos.z + F.z * fz + R.z * rx,
        };
        try {
          c.teleport(cPos, { keepVelocity: false, rotation: { x: 0, y: normalizeAngle(yaw + 180) } });
          if (prop(c, "studio:anim", "none") !== "cheer" && prop(c, "studio:anim", "none") !== "hurt") {
            if (prop(c, "studio:anim", "none") !== desiredCrewAnim) {
              setProp(c, "studio:anim", desiredCrewAnim);
            }
          }
        } catch { }
      });

      // Walkable Deck Support, Railing Bounds & Anti-Hull-Trap for all players on deck
      for (const p of playersNear(dim, nextShipPos, 6.0)) {
        if (!valid(p)) continue;
        if (flat(p.location, nextShipPos) < 8.0) {
          advanceShipQuest(p, "find_ship");
        }
        if (ridingOn(p)?.id === ship.id) continue; // Seated riders are already carried by rideable
        const rel = worldToShipLocal(ship, p.location);
        if (Math.abs(rel.localF) <= 4.35 && Math.abs(rel.localR) <= 1.68 && rel.dy >= -0.8 && rel.dy <= 2.4) {
          const deckFloorY = nextShipPos.y + (rel.localF < -2.1 ? 1.50 : 1.22);
          let clampedF = rel.localF;
          let clampedR = rel.localR;
          // If player is below railing jump height, keep them inside the bulwark railings
          if (p.location.y < deckFloorY + 0.38) {
            clampedR = Math.max(-1.42, Math.min(1.42, clampedR));
            clampedF = Math.max(-4.05, Math.min(4.05, clampedF));
          }
          // Lift player onto deck if they sank below deckFloorY (anti-hull-trap + deck floor support)
          if (p.location.y < deckFloorY - 0.02 || Math.abs(dx) > 0.001 || Math.abs(dz) > 0.001 || clampedR !== rel.localR || clampedF !== rel.localF) {
            const newP = {
              x: nextShipPos.x + F.x * clampedF + R.x * clampedR,
              y: Math.max(p.location.y, deckFloorY),
              z: nextShipPos.z + F.z * clampedF + R.z * clampedR,
            };
            try { p.teleport(newP, { keepVelocity: true }); } catch { }
          }
        }
      }
    });
  }
}

// ------------------------------------------------------------------ 1 Hz Ambient & Ocean Effects Loop
let shipSec = 0;
export function tickShipsAmbient() {
  shipSec++;
  for (const ship of creatures(SHIP_TYPE)) {
    safe("ship_amb", () => {
      const dim = ship.dimension, loc = ship.location;
      const speedState = prop(ship, "studio:speed_state", 0);
      const { F, R } = shipVectors(ship);

      // Quest check: left Ogygia harbor (> 35 blocks from (0, -35))
      if (speedState !== 0 && flat(loc, { x: 0, z: -35 }) > 35) {
        for (const p of playersNear(dim, loc, 8)) advanceShipQuest(p, "leave_harbor");
      }

      if (speedState !== 0) {
        // Bow wake & oar splash particles
        const bow = add(loc, { x: F.x * 4.4, y: 0.2, z: F.z * 4.4 });
        particle(dim, "minecraft:water_splash_particle", bow);
        particle(dim, "minecraft:bubble_column_up_particle", add(loc, { x: -F.x * 4.2, y: 0.1, z: -F.z * 4.2 }));
        for (const side of [-2.4, 2.4]) {
          particle(dim, "minecraft:water_splash_particle", add(loc, { x: R.x * side, y: 0.15, z: R.z * side }));
        }
        // Rhythmic oar & water sounds (non-overlapping)
        if (shipSec % 2 === 0) {
          sound(dim, "odyssey.ship.oar_row", loc, 0.7, 1.0);
          sound(dim, "odyssey.ship.water_splash", bow, 0.65, 1.0);
        }
        if (speedState === 2 && shipSec % 4 === 0) {
          sound(dim, "odyssey.ship.sail_wind", loc, 0.6, 1.0);
        }
      } else if (shipSec % 6 === 0) {
        sound(dim, "odyssey.ship.hull_creak", loc, 0.55, 1.0);
      }
    });
  }
}
