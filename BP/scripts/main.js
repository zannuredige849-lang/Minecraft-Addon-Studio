// The Odyssey (2026): the creatures of Christopher Nolan's film, their moves and the journey.
// @minecraft/server 1.11.0 (stable). One module per group of creatures (creatures/), shared helpers (lib/), the map (world/);
// data/moves.js is generated from the same table that builds the animations and their sound cues.
// Everything here is per creature or per player: nothing is global, so any number of players can play together.
import { world, system } from "@minecraft/server";
import { refresh, track } from "./lib/registry.js";
import { cancel, tickMoves } from "./lib/moves.js";
import { dropAllOf, tickHolds } from "./lib/holds.js";
import { add, block, isPlayer, safe, valid } from "./lib/util.js";

import * as cyclops from "./creatures/cyclops.js";
import * as lae from "./creatures/laestrygonian.js";
import * as circe from "./creatures/circe.js";
import * as siren from "./creatures/siren.js";
import * as sea from "./creatures/scylla.js";
import * as hades from "./creatures/hades.js";
import * as gods from "./creatures/olympus.js";
import * as journey from "./world/journey.js";

// ------------------------------------------------------------------ events
world.afterEvents.entitySpawn.subscribe(({ entity }) => safe("spawn", () => track(entity)));

world.afterEvents.entityHitEntity.subscribe(({ damagingEntity: a, hitEntity: v }) => safe("hit", () => {
  if (!valid(a) || !valid(v)) return;
  if (a.typeId === cyclops.TYPE) cyclops.onHit(a, v);
  else if (a.typeId === lae.TYPE) lae.onHit(a, v);
}));

world.afterEvents.entityHurt.subscribe(({ hurtEntity: v, damageSource }) => safe("hurt", () => {
  const src = damageSource?.damagingEntity;
  if (!valid(v)) return;
  switch (v.typeId) {
    case cyclops.TYPE: cyclops.onHurt(v, src); break;
    case lae.TYPE: case lae.CHILD: lae.onHurt(v, src); break;
    case gods.CATTLE: gods.onCattleHurt(v); break;
    case "minecraft:player": {
      const hp = v.getComponent("minecraft:health")?.currentValue;
      if (hp !== undefined && hp <= 6) gods.vision(v);
      break;
    }
    default:
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
  if (type === gods.CATTLE) { gods.godsStorm(killer); return; }
  if (hades.SACRIFICE_VICTIMS.has(type)) {
    const under = block(killer.dimension, add(killer.location, { x: 0, y: -0.5, z: 0 }));
    if (under && hades.SACRIFICE_BLOCKS.has(under.typeId)) hades.summonDead(killer);
  }
}));

world.afterEvents.dataDrivenEntityTrigger.subscribe((ev) => safe("trigger", () => {
  const e = ev.entity, id = ev.eventId ?? ev.id;
  if (!valid(e)) return;
  if (e.typeId === circe.TYPE || e.typeId === circe.SISTER) circe.onTrigger(e, id);
  else if (e.typeId === gods.CALYPSO && id === "studio:offer_lotus") gods.offerLotus(e);
  else if (e.typeId === gods.CALYPSO && id === "studio:embrace") gods.embrace(e);
  else if (e.typeId === gods.ATHENA && id === "studio:bless") gods.bless(e);
}));

world.afterEvents.itemCompleteUse.subscribe(({ source: p, itemStack }) => safe("use", () => {
  if (!isPlayer(p)) return;
  switch (itemStack?.typeId) {
    case "studio:beeswax": siren.onWax(p); break;
    case "studio:circe_stew": circe.onItemStew(p); break;
    case "studio:lotus_flower": gods.onLotus(p); break;
    default:
  }
}));

world.afterEvents.playerSpawn.subscribe(({ player, initialSpawn }) => safe("playerSpawn", () => journey.onPlayerSpawn(player, initialSpawn)));
world.afterEvents.playerLeave.subscribe(({ playerId }) => safe("playerLeave", () => { journey.onPlayerLeave(playerId); dropAllOf(playerId); }));

// ------------------------------------------------------------------ loops
system.runInterval(() => {
  safe("moves", tickMoves); safe("holds", tickHolds); safe("boulders", cyclops.tickBoulders); safe("curses", circe.tickCurses);
}, 1);
system.runInterval(() => { safe("circe", circe.tickCirce); safe("charybdis", sea.tickCharybdis); }, 2);
system.runInterval(() => {
  safe("registry", refresh);
  safe("cyclops", cyclops.tickCyclops); safe("giants", lae.tickLaestrygonians); safe("children", lae.tickChildren);
  safe("scylla", sea.tickScylla); safe("shades", hades.tickShades);
}, 10);
system.runInterval(() => {
  safe("sirens", siren.tickSirens); safe("horses", gods.tickHorses); safe("cattle", gods.tickCattle);
  safe("journey", journey.tickJourney);
  for (const b of world.getDimension("minecraft:overworld").getEntities({ type: "studio:boulder" })) {
    if (cyclops.strayBoulder(b)) safe("rock", () => b.remove());
  }
}, 20);
system.runInterval(() => safe("sites", journey.tickSites), 80);
