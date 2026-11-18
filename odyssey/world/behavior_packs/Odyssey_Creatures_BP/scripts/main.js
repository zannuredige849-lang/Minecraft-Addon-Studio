// The Odyssey (2026) v2.0.0 — Complete World Expansion & Cinematic Overhaul.
import { world, system } from "@minecraft/server";
import { refresh, track } from "./lib/registry.js";
import { busy, cancel, perform, tickMoves } from "./lib/moves.js";
import { dropAllOf, tickHolds } from "./lib/holds.js";
import { add, block, isPlayer, ready, safe, valid, wait } from "./lib/util.js";
import { sound } from "./lib/fx.js";

import * as cyclops from "./creatures/cyclops.js";
import * as lae from "./creatures/laestrygonian.js";
import * as circe from "./creatures/circe.js";
import * as siren from "./creatures/siren.js";
import * as sea from "./creatures/scylla.js";
import * as hades from "./creatures/hades.js";
import * as gods from "./creatures/olympus.js";
import * as journey from "./world/journey.js";
import * as companions from "./world/companions.js";
import * as pauseVote from "./world/pause_vote.js";
import * as menu from "./world/menu.js";
import * as music from "./world/music.js";
import * as story from "./world/story.js";
import * as ship from "./world/ship.js";
import * as progression from "./world/progression.js";

const NPC_HURT_SOUNDS = {
  "studio:calypso": "odyssey.calypso.sigh",
  "studio:circe": "mob.witch.hurt",
  "studio:athena": "odyssey.athena.shimmer",
  "studio:shade": "odyssey.shade.hurt",
  "studio:tiresias": "odyssey.tiresias.voice",
  "studio:laestrygonian": "odyssey.laestrygonian.hurt",
  "studio:laestrygonian_child": "mob.villager.hurt",
};

function onNpcHurt(v) {
  if (!valid(v)) return;
  if (v.typeId === gods.CALYPSO || v.typeId === circe.TYPE || v.typeId === gods.ATHENA) {
    try { v.clearVelocity?.(); } catch { }
  }
  if (busy(v) || !ready(v, "studio:cd_hurt")) return;
  wait(v, "studio:cd_hurt", 20);
  perform(v, "hurt", {}, { still: false });
  const sfx = NPC_HURT_SOUNDS[v.typeId];
  if (sfx) sound(v.dimension, sfx, v.location, 0.85, 1.0);
}

// ------------------------------------------------------------------ events
world.afterEvents.entitySpawn.subscribe(({ entity }) => safe("spawn", () => track(entity)));

world.afterEvents.entityHitEntity.subscribe(({ damagingEntity: a, hitEntity: v }) => safe("hit", () => {
  if (pauseVote.isWorldPaused()) return;
  if (!valid(a) || !valid(v)) return;
  if (a.typeId === cyclops.TYPE) cyclops.onHit(a, v);
  else if (a.typeId === lae.TYPE) lae.onHit(a, v);
  else if (isPlayer(a)) progression.onPlayerWeaponHit(a, v);
}));

world.afterEvents.entityHurt.subscribe(({ hurtEntity: v, damageSource }) => safe("hurt", () => {
  const src = damageSource?.damagingEntity;
  if (!valid(v)) return;
  switch (v.typeId) {
    case cyclops.TYPE:
      cyclops.onHurt(v, src);
      break;
    case lae.TYPE:
    case lae.CHILD:
      lae.onHurt(v, src);
      onNpcHurt(v);
      break;
    case gods.CATTLE:
      gods.onCattleHurt(v);
      break;
    case ship.SHIP_TYPE:
      ship.onShipHurt(v, 25);
      break;
    case ship.CREW_TYPE:
      onNpcHurt(v);
      break;
    case gods.CALYPSO:
    case circe.TYPE:
    case gods.ATHENA:
    case hades.SHADE:
    case hades.TIRESIAS:
      onNpcHurt(v);
      break;
    case "minecraft:player": {
      const hp = v.getComponent("minecraft:health")?.currentValue;
      if (hp !== undefined && hp <= 6) gods.vision(v);
      break;
    }
    default:
      break;
  }
}));

world.afterEvents.entityDie.subscribe(({ deadEntity: e, damageSource }) => safe("die", () => {
  const killer = damageSource?.damagingEntity;
  if (e?.id) dropAllOf(e.id);
  if (e?.typeId && !isPlayer(e)) safe("site", () => journey.onCreatureDied(e));
  if (valid(e)) cancel(e);
  if (isPlayer(e)) {
    circe.endCurse(e, false);
    safe("tag", () => e.removeTag("studio:in_flock"));
    return;
  }
  if (!isPlayer(killer)) return;
  const type = e?.typeId;
  if (type === gods.CATTLE) {
    story.triggerSiteDecisionVote("thrinacia");
    gods.godsStorm(killer);
    return;
  }
  if (type === lae.TYPE) {
    progression.onProgressionStoryMilestone(killer, "giant_slain");
  }
  if (hades.SACRIFICE_VICTIMS.has(type)) {
    const under = block(killer.dimension, add(killer.location, { x: 0, y: -0.5, z: 0 }));
    if (hades.isBlackSand(under) && progression.canPerformHadesSacrifice(killer)) {
      hades.summonDead(killer);
    }
  }
}));

world.afterEvents.dataDrivenEntityTrigger.subscribe((ev) => safe("trigger", () => {
  const e = ev.entity, id = ev.eventId ?? ev.id;
  if (!valid(e)) return;
  if (e.typeId === circe.TYPE || e.typeId === circe.SISTER) circe.onTrigger(e, id);
  else if (e.typeId === gods.CALYPSO && id === "studio:offer_lotus") gods.offerLotus(e);
  else if (e.typeId === gods.CALYPSO && id === "studio:embrace") gods.embrace(e);
  else if (e.typeId === gods.ATHENA && id === "studio:bless") gods.bless(e);
  else if (e.typeId === ship.SHIP_TYPE && id === "studio:ship_interact") {
    const p = e.dimension.getPlayers({ location: e.location, maxDistance: 7 })[0];
    if (p) ship.onUseShipHorn(p);
  }
}));

function handleCustomItemUse(p, itemId) {
  if (!isPlayer(p) || !itemId) return;
  switch (itemId) {
    case "studio:beeswax":
      if (progression.checkItemPrerequisite(p, itemId)) siren.onWax(p);
      break;
    case "studio:circe_stew":
      if (progression.checkItemPrerequisite(p, itemId)) circe.onItemStew(p);
      break;
    case "studio:lotus_flower":
      gods.onLotus(p);
      break;
    case "studio:moly_herb":
      circe.endCurse(p, true);
      progression.onUseProgressionItem(p, itemId);
      break;
    case "studio:odyssey_astrolabe":
      menu.onUseAstrolabe(p);
      break;
    case "studio:ship_helm_horn":
      if (progression.checkItemPrerequisite(p, itemId)) ship.onUseShipHorn(p);
      break;
    case "studio:ship_repair_kit":
      if (progression.checkItemPrerequisite(p, itemId)) ship.onUseRepairKit(p);
      break;
    case "studio:copper_hoplon":
    case "studio:tiresias_staff":
    case "studio:apollo_sun_talisman":
    case "studio:royal_bow_of_odysseus":
    case "studio:spear_of_telemachus":
      progression.onUseProgressionItem(p, itemId);
      break;
    default:
      break;
  }
}

world.afterEvents.itemCompleteUse.subscribe(({ source: p, itemStack }) => safe("use", () => {
  handleCustomItemUse(p, itemStack?.typeId);
}));

try {
  world.afterEvents.itemUse?.subscribe(({ source: p, itemStack }) => safe("itemUse", () => {
    const id = itemStack?.typeId;
    if (id && [
      "studio:copper_hoplon",
      "studio:tiresias_staff",
      "studio:apollo_sun_talisman",
      "studio:royal_bow_of_odysseus",
      "studio:spear_of_telemachus",
    ].includes(id)) {
      handleCustomItemUse(p, id);
    }
  }));
} catch { }

world.afterEvents.playerSpawn.subscribe(({ player, initialSpawn }) => safe("playerSpawn", () => journey.onPlayerSpawn(player, initialSpawn)));
world.afterEvents.playerLeave.subscribe(({ playerId }) => safe("playerLeave", () => {
  journey.onPlayerLeave(playerId);
  pauseVote.onVotePlayerLeave(playerId);
  dropAllOf(playerId);
}));

// ------------------------------------------------------------------ loops
system.runInterval(() => {
  safe("pauseVote", pauseVote.tickPauseAndVote);
  if (pauseVote.isWorldPaused()) return;
  safe("moves", tickMoves);
  safe("holds", tickHolds);
  safe("boulders", cyclops.tickBoulders);
  safe("curses", circe.tickCurses);
  safe("circe", circe.tickCirce);
  safe("shipsFast", ship.tickShipsFast);
}, 1);

system.runInterval(() => {
  if (pauseVote.isWorldPaused()) return;
  safe("charybdis", sea.tickCharybdis);
}, 2);

system.runInterval(() => {
  safe("registry", refresh);
  if (pauseVote.isWorldPaused()) return;
  safe("cyclops", cyclops.tickCyclops);
  safe("giants", lae.tickLaestrygonians);
  safe("children", lae.tickChildren);
  safe("scylla", sea.tickScylla);
  safe("shades", hades.tickShades);
  safe("companions", companions.tickCompanions);
}, 10);

system.runInterval(() => {
  safe("music", () => music.tickMusic(pauseVote.isWorldPaused() || pauseVote.isCinematicActive()));
  if (pauseVote.isWorldPaused()) return;
  safe("roles", story.tickRoles);
  safe("sirens", siren.tickSirens);
  safe("horses", gods.tickHorses);
  safe("cattle", gods.tickCattle);
  safe("calypso", gods.tickCalypso);
  safe("shipsAmbient", ship.tickShipsAmbient);
  safe("progression", progression.tickProgression);
  safe("journey", journey.tickJourney);
  for (const b of world.getDimension("minecraft:overworld").getEntities({ type: "studio:boulder" })) {
    if (cyclops.strayBoulder(b)) safe("rock", () => b.remove());
  }
}, 20);

system.runInterval(() => {
  if (pauseVote.isWorldPaused()) return;
  safe("sites", journey.tickSites);
}, 80);
