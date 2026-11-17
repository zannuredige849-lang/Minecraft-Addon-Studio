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

// ---------------------------------------------------------------- the creatures of each place
// A place's creatures are spawned the first time a player comes near (the world remembers that), and one that is killed
// comes back ten minutes later (world time, so a restart does not forget it). Deaths are what is counted, not what is
// loaded: a creature that wanders off, or is not loaded, is never mistaken for a dead one.
const worldTime = () => { try { return typeof world.getAbsoluteTime === "function" ? world.getAbsoluteTime() : now(); } catch { return now(); } };
const readDeaths = () => { try { return JSON.parse(world.getDynamicProperty("odyssey:deaths") ?? "[]"); } catch { return []; } };
const writeDeaths = (list) => { try { world.setDynamicProperty("odyssey:deaths", JSON.stringify(list.slice(-64))); } catch { } };
const flagKey = (s, type) => `odyssey:site:${s.id}:${type}`;

/** A creature died: if it belongs to a place, that place will make a new one in ten minutes. */
export function onCreatureDied(e) {
  if (!mapActive()) return;
  const type = e.typeId, loc = e.location;
  const s = SITES.find((x) => x.creatures.some((c) => c[0] === type) && flat(loc, x) < x.r + 150);
  if (!s) return;
  const list = readDeaths();
  list.push([s.id, type, worldTime()]);
  writeDeaths(list);
}

function spawnSpot(dim, s, type, i, spots) {
  const [dx, dz] = spots[i % spots.length];
  const e = dim.spawnEntity(type, { x: s.x + dx, y: s.y + 1, z: s.z + dz });
  if (e) { try { e.setDynamicProperty("studio:site", s.id); } catch { } }
  return e;
}

/** Called every few seconds: keep every place populated while a player is near enough for it to be loaded. */
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
        const flag = flagKey(s, type);
        if (!world.getDynamicProperty(flag)) {                                      // first visit: everything is here
          for (let i = 0; i < spots.length; i++) spawnSpot(dim, s, type, i, spots);
          world.setDynamicProperty(flag, true);
          continue;
        }
        const deaths = readDeaths();
        const due = deaths.filter((d) => d[0] === s.id && d[1] === type && worldTime() - d[2] >= RESPAWN_TICKS);
        if (!due.length) continue;
        const have = near(dim, center, s.r + 150, type).filter(valid).length;
        let missing = Math.min(due.length, Math.max(0, spots.length - have));
        for (let i = 0; i < missing; i++) spawnSpot(dim, s, type, have + i, spots);
        writeDeaths(deaths.filter((d) => !due.includes(d)));                          // answered, whether or not one was needed
      }
    });
  }
}
