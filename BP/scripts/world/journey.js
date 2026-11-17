// The journey: only in the map (a lodestone at the marker position tells us). Gives the crew's supplies, shows the name of
// each place as a player arrives, wraps each place in its own fog for that player alone, and keeps each place's creatures
// alive: they are spawned when a player comes near and again, after ten minutes, if they were killed. All state is per
// player (dynamic properties and a map keyed by player id), so any number of players can be at any number of places.
import { world, ItemStack } from "@minecraft/server";
import { MARKER, SITES, FOGS, RESPAWN_TICKS } from "../data/sites.js";
import { block, dp, flat, near, now, playersNear, safe, setDp, valid } from "../lib/util.js";
import { fogOff, fogOn, hear, tell, title } from "../lib/fx.js";

let active = false, checked = -1e9;
const FOG_TAG = "odyssey_site";
const siteOf = new Map();            // player id -> site id they are in now
const lastSpawn = new Map();         // "site:type" -> tick of the last spawn
const gone = new Map();              // "site:type" -> tick at which it was found missing

/** Is this the map? (Checked now and then until it is.) */
export function mapActive(force = false) {
  if (active) return true;
  if (!MARKER || !SITES.length || (!force && now() - checked < 100)) return false;
  checked = now();
  try { active = world.getDimension("minecraft:overworld").getBlock({ x: MARKER.x, y: MARKER.y, z: MARKER.z })?.typeId === MARKER.block; }
  catch { active = false; }
  return active;
}

function giveKit(p) {
  if (dp(p, "studio:kit", false)) return;
  setDp(p, "studio:kit", true);
  const inv = p.getComponent("minecraft:inventory")?.container;
  for (const [id, n] of [["minecraft:oak_boat", 2], ["studio:beeswax", 6], ["studio:burning_stake", 1]]) {
    safe("kit", () => {
      const left = inv?.addItem(new ItemStack(id, n));
      if (left) p.dimension.spawnItem(left, p.location);
    });
  }
  tell(p, "odyssey.kit");
}

export function onPlayerSpawn(p, initialSpawn) {
  if (!mapActive(true)) return;
  setDp(p, "studio:journey", true);
  siteOf.delete(p.id);                    // re-apply this place's fog after a respawn
  if (initialSpawn || !dp(p, "studio:titled", false)) {
    setDp(p, "studio:titled", true);
    title(p, "odyssey.title", "odyssey.subtitle");
    giveKit(p);
  }
}
export function onPlayerLeave(id) { siteOf.delete(id); }

const siteAt = (p) => {
  let best, bd = Infinity;
  for (const s of SITES) {
    const d = flat(p.location, s);
    if (d < s.r && d < bd) { best = s; bd = d; }
  }
  return best;
};

export function tickJourney() {
  if (!mapActive()) return;
  for (const p of world.getAllPlayers()) {
    safe("journey", () => {
      const site = siteAt(p), was = siteOf.get(p.id);
      if ((site?.id) === was) return;
      if (was) { if (SITES.find((s) => s.id === was)?.fog) fogOff(p, FOG_TAG); siteOf.delete(p.id); }
      if (!site) return;
      siteOf.set(p.id, site.id);
      if (site.fog && FOGS[site.fog]) fogOn(p, `odyssey:${site.fog}`, FOG_TAG);
      if (now() - dp(p, `studio:seen_${site.id}`, -1e9) > 6000) {            // a new arrival, not someone pacing the shore
        setDp(p, `studio:seen_${site.id}`, now());
        title(p, `odyssey.site.${site.id}`, `odyssey.site.${site.id}.sub`);
        hear(p, "odyssey.world.arrive", undefined, 1, 1);
      }
    });
  }
}

/**
 * Keep every place's creatures alive while a player is near (close enough that the place is loaded): the missing ones
 * are spawned, and one that was killed comes back ten minutes later.
 */
export function tickSites() {
  if (!mapActive()) return;
  const dim = world.getDimension("minecraft:overworld");
  for (const s of SITES) {
    safe("site", () => {
      const center = { x: s.x, y: s.y, z: s.z };
      if (!playersNear(dim, center, 60).length) return;
      const wanted = new Map();
      for (const [type, dx, dz] of s.creatures) wanted.set(type, [...(wanted.get(type) ?? []), [dx, dz]]);
      for (const [type, spots] of wanted) {
        const have = near(dim, center, s.r + 15, type).filter(valid).length, key = `${s.id}:${type}`;
        if (have > 0) gone.delete(key);
        if (have >= spots.length) continue;
        if (have === 0 && lastSpawn.has(key)) {                      // it was here and now it is not: killed
          if (!gone.has(key)) gone.set(key, now());
          if (now() - gone.get(key) < RESPAWN_TICKS) continue;
          gone.delete(key);
        }
        for (let i = have; i < spots.length; i++) {
          const [dx, dz] = spots[i];
          const e = dim.spawnEntity(type, { x: s.x + dx, y: s.y + 1, z: s.z + dz });
          if (e) lastSpawn.set(key, now());
        }
      }
    });
  }
}
