// Travel guides: occasional local people (a coastal scout, a fisherman, a shepherd) who appear when a party seems
// lost, point the way to each player's own current destination, walk a short stretch of the road with them, and
// leave. Rules that keep them subtle:
//   - at most one guide per party (players within 32 blocks of each other share one), never more than 2 in the world
//   - only on land, never during cutscenes, pauses or votes, never close to the destination
//   - a party is "lost" when its leader has not got 10 blocks closer to the objective for 90 seconds
//   - 5 minute cooldown per player after a guide appears, so encounters do not repeat
//   - every player hears directions to *their* objective, so one player's finished quest never misleads another
import { world, system } from "@minecraft/server";
import { POINTS } from "../data/config.js";
import { add, dirTo, dp, flat, isAir, isWater, block, near, now, ridingOn, safe, setDp, setProp, valid } from "../lib/util.js";
import { burst, hear } from "../lib/fx.js";
import { perform, busy } from "../lib/moves.js";
import { safeSpotNear } from "../lib/terrain.js";
import { getWorldState, STATE_NORMAL } from "./pause_vote.js";
import { cutsceneActive } from "./cinematics.js";
import { compass, mainObjective, roleOf } from "./quests.js";

const PERSON = "studio:odyssey_person";
const TAG = "odyssey_guide";
const VARIANTS = { scout: 3, fisher: 4, shepherd: 5 };
const LOST_TICKS = 1800, COOLDOWN = 6000, LIFETIME = 1200, LEAD_DISTANCE = 26, MIN_DEST_DIST = 70;
const DANGER = ["studio:cyclops", "studio:laestrygonian", "studio:scylla", "studio:siren", "studio:shade"];

export const isGuide = (e) => { try { return e.hasTag(TAG); } catch { return false; } };
const guides = () => { try { return world.getDimension("minecraft:overworld").getEntities({ type: PERSON, tags: [TAG] }).filter(valid); } catch { return []; } };

function destOf(p) {
  const o = mainObjective(p);
  return o?.dest ? { key: o.dest, pt: POINTS[o.dest] } : undefined;
}

function say(p, guide, key, ...withParts) {
  try {
    p.sendMessage({ rawtext: [{ text: "§7<" }, { translate: `odyssey.guide.name.${dp(guide, "studio:guide_kind", "scout")}` }, { text: "> §f" },
      withParts.length ? { translate: key, with: { rawtext: withParts } } : { translate: key }] });
  } catch { }
}

function directions(p, guide) {
  const d = destOf(p);
  if (!d) return;
  say(p, guide, "odyssey.guide.dir", { translate: d.pt.label }, { text: String(Math.round(flat(p.location, d.pt))) },
    { translate: `odyssey.compass.${compass(p.location, d.pt)}` }, { text: `${Math.floor(d.pt.x)} ${Math.floor(d.pt.y)} ${Math.floor(d.pt.z)}` });
}

/** Track progress toward the objective so we can tell when a player is going in circles. */
function updateLost(p) {
  const d = destOf(p);
  if (!d) return false;
  const dist = flat(p.location, d.pt);
  const key = dp(p, "studio:guide_dest", "");
  if (key !== d.key || dist < dp(p, "studio:guide_best", 1e9) - 10) {
    setDp(p, "studio:guide_dest", d.key);
    setDp(p, "studio:guide_best", dist);
    setDp(p, "studio:guide_best_t", now());
    return false;
  }
  return dist > MIN_DEST_DIST && now() - dp(p, "studio:guide_best_t", now()) > LOST_TICKS;
}

function kindFor(dim, loc) {
  for (let dx = -5; dx <= 5; dx += 5) for (let dz = -5; dz <= 5; dz += 5) {
    if (isWater(block(dim, { x: loc.x + dx, y: loc.y - 1, z: loc.z + dz }))) return "fisher";
  }
  const g = block(dim, { x: loc.x, y: loc.y - 1, z: loc.z });
  return g?.typeId === "minecraft:grass_block" ? "shepherd" : "scout";
}

function trySpawnFor(leader, party) {
  const d = destOf(leader);
  if (!d || ridingOn(leader)) return;
  const dim = leader.dimension;
  if (isWater(block(dim, leader.location)) || !leader.isOnGround) return;
  const dir = dirTo(leader.location, d.pt);
  const ahead = add(leader.location, { x: dir.x * 7, y: 0, z: dir.z * 7 });
  const spot = safeSpotNear(dim, ahead.x, ahead.z, 4, Math.floor(leader.location.y) + 4);
  if (!spot || Math.abs(spot.y - leader.location.y) > 3) return;
  const kind = kindFor(dim, spot);
  const g = dim.spawnEntity(PERSON, spot);
  g.addTag(TAG);
  setProp(g, "studio:variant", VARIANTS[kind]);
  setDp(g, "studio:guide_kind", kind);
  setDp(g, "studio:guide_leader", leader.id);
  setDp(g, "studio:guide_dest", d.key);
  setDp(g, "studio:guide_until", now() + LIFETIME);
  setDp(g, "studio:guide_start_x", spot.x);
  setDp(g, "studio:guide_start_z", spot.z);
  safe("g.face", () => g.teleport(spot, { facingLocation: { x: d.pt.x, y: spot.y + 1.5, z: d.pt.z } }));
  burst(dim, "minecraft:villager_happy", add(spot, { x: 0, y: 1, z: 0 }), 0.6, 4);
  system.runTimeout(() => safe("g.hello", () => {
    if (!valid(g)) return;
    perform(g, "point", {}, { still: true });
    const danger = DANGER.some((t) => near(dim, spot, 48, t).length);
    for (const p of party) {
      if (!valid(p)) continue;
      say(p, g, `odyssey.guide.hello.${kind}`);
      directions(p, g);
      if (danger) say(p, g, "odyssey.guide.danger");
      setDp(p, "studio:guide_next", now() + COOLDOWN);
      setDp(p, "studio:guide_best_t", now());
      hear(p, "odyssey.athena.chime", undefined, 0.3, 0.7);
    }
  }), 10);
}

function farewell(g, playersAround) {
  for (const p of playersAround) say(p, g, "odyssey.guide.bye");
  burst(g.dimension, "minecraft:villager_happy", add(g.location, { x: 0, y: 1, z: 0 }), 0.6, 4);
  system.runTimeout(() => { if (valid(g)) safe("g.rm", () => g.remove()); }, 30);
  setDp(g, "studio:guide_until", -1);
}

function steer(g) {
  const destKey = dp(g, "studio:guide_dest", "");
  const pt = POINTS[destKey];
  const leader = world.getAllPlayers().find((p) => p.id === dp(g, "studio:guide_leader", ""));
  const around = g.dimension.getPlayers({ location: g.location, maxDistance: 40 });
  if (dp(g, "studio:guide_until", 0) < 0) return;
  const finished = !pt || !leader || !around.length || now() > dp(g, "studio:guide_until", 0)
    || destOf(leader)?.key !== destKey || flat(leader.location, pt) < 30;
  if (finished) { farewell(g, around); return; }
  if (busy(g)) return;
  const traveled = Math.hypot(g.location.x - dp(g, "studio:guide_start_x", g.location.x), g.location.z - dp(g, "studio:guide_start_z", g.location.z));
  const close = g.dimension.getPlayers({ location: g.location, maxDistance: 9 }).length > 0;
  if (traveled >= LEAD_DISTANCE) {
    if (!dp(g, "studio:guide_waved", false)) {
      setDp(g, "studio:guide_waved", true);
      perform(g, "point", {}, { still: true });
      for (const p of around) say(p, g, "odyssey.guide.onward");
      setDp(g, "studio:guide_until", Math.min(dp(g, "studio:guide_until", 0), now() + 160));
    }
    return;
  }
  if (!close) return;                                    // wait for the players to follow
  const dir = dirTo(g.location, pt);
  const ahead = add(g.location, { x: dir.x * 1.2, y: 0, z: dir.z * 1.2 });
  const b0 = block(g.dimension, ahead), b1 = block(g.dimension, add(ahead, { x: 0, y: 1, z: 0 }));
  const below = block(g.dimension, add(ahead, { x: 0, y: -1, z: 0 })), below2 = block(g.dimension, add(ahead, { x: 0, y: -2, z: 0 }));
  if (isWater(b0) || isWater(below) || (isAir(below) && isAir(below2))) {   // never lead into the sea or off a ledge
    setDp(g, "studio:guide_start_x", g.location.x - dir.x * LEAD_DISTANCE);  // stop leading here
    return;
  }
  try {
    g.teleport(g.location, { facingLocation: { x: pt.x, y: g.location.y + 1.5, z: pt.z } });
    if (b0 && !isAir(b0) && isAir(b1)) g.applyImpulse({ x: dir.x * 0.12, y: 0.38, z: dir.z * 0.12 });
    else g.applyImpulse({ x: dir.x * 0.1, y: 0, z: dir.z * 0.1 });
  } catch { }
}

/** Every 10 ticks: move active guides. */
export function tickGuidesFast() {
  for (const g of guides()) safe("guide.steer", () => steer(g));
}

/** Every 2 seconds: decide whether a lost party should meet a guide. */
export function tickGuides() {
  if (getWorldState() !== STATE_NORMAL || cutsceneActive()) return;
  const players = world.getAllPlayers().filter((p) => valid(p) && roleOf(p));
  const lost = new Map(players.map((p) => [p.id, updateLost(p)]));
  const active = guides();
  if (active.length >= 2) return;
  const seen = new Set();
  for (const leader of players) {
    if (seen.has(leader.id)) continue;
    const party = players.filter((q) => q.dimension.id === leader.dimension.id && flat(q.location, leader.location) < 32);
    party.forEach((q) => seen.add(q.id));
    if (active.some((g) => flat(g.location, leader.location) < 64)) continue;
    if (party.some((q) => now() < dp(q, "studio:guide_next", 0))) continue;
    if (!lost.get(leader.id)) continue;
    safe("guide.spawn", () => trySpawnFor(leader, party));
  }
}

export function onGuideTalk(g, p) {
  directions(p, g);
  if (!busy(g)) safe("g.point", () => perform(g, "point", {}, { still: true }));
}

/** Guides never persist across sessions (their timers are session ticks): remove any left in the world. */
export function clearStaleGuides() {
  for (const g of guides()) safe("g.rm", () => g.remove());
}

/** Session ticks restart at 0 on every load, so per-player guide timers are reset when a player joins. */
export function resetGuideTimers(p) {
  setDp(p, "studio:guide_next", 0);
  setDp(p, "studio:guide_best_t", now());
  setDp(p, "studio:guide_best", 1e9);
}
