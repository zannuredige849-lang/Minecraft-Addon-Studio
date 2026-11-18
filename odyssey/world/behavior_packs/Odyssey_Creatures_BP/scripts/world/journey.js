// The journey: gives the crew's supplies + Odyssey Astrolabe, assigns Odysseus/Telemachus roles,
// builds Ancient Greek site architecture, triggers multi-shot location cutscenes & fogs,
// and manages site creature spawning & checkpoint respawns.
import { world, ItemStack } from "@minecraft/server";
import { MARKER, SITES, FOGS, RESPAWN_TICKS } from "../data/sites.js";
import { dp, flat, near, now, playersNear, safe, setDp, valid } from "../lib/util.js";
import { fogOff, fogOn, hear, tell, title } from "../lib/fx.js";
import { getPlayerRole, onStoryEvent, respawnAtCheckpoint } from "./story.js";
import { ensureSiteArchitecture } from "./architect.js";
import { ensureHarborShip } from "./ship.js";
import { flushRewardVault, grantProgressionReward, recoverLostQuestItems } from "./progression.js";

let active = false, checked = -1e9;
const FOG_TAG = "odyssey_site";
const siteOf = new Map();

export function mapActive(force = false) {
  if (active) return true;
  try {
    if (world.getDynamicProperty("odyssey:is_map") === true) { active = true; return true; }
  } catch { }
  if (!MARKER || !SITES.length || (!force && now() - checked < 100)) return false;
  checked = now();
  try {
    active = world.getDimension("minecraft:overworld").getBlock({ x: MARKER.x, y: MARKER.y, z: MARKER.z })?.typeId === MARKER.block;
    if (active) world.setDynamicProperty("odyssey:is_map", true);
  } catch { active = false; }
  return active;
}

function giveKit(p) {
  if (dp(p, "studio:kit", false)) return;
  setDp(p, "studio:kit", true);
  setDp(p, "studio:unlock_astrolabe", true);
  setDp(p, "studio:unlock_driftwood_club", true);
  // Tier 1 Starting Equipment Only (Castaway Gear on Ogygia — later items unlock progressively!)
  grantProgressionReward(p, "studio:odyssey_astrolabe", 1, { uniqueKey: "start_astrolabe", role: "both", silent: true });
  grantProgressionReward(p, "studio:driftwood_club", 1, { uniqueKey: "start_club", role: "both", silent: true });
  const inv = p.getComponent("minecraft:inventory")?.container;
  for (const [id, n] of [["minecraft:leather_chestplate", 1], ["minecraft:bread", 3]]) {
    safe("kit", () => inv?.addItem(new ItemStack(id, n)));
  }
  tell(p, "odyssey.kit");
  const role = getPlayerRole(p);
  tell(p, `odyssey.role.${role}`);
}

export function onPlayerSpawn(p, initialSpawn) {
  if (!mapActive(true)) return;
  setDp(p, "studio:journey", true);
  siteOf.delete(p.id);
  if (initialSpawn || !dp(p, "studio:titled", false)) {
    setDp(p, "studio:titled", true);
    title(p, "odyssey.title", "odyssey.subtitle");
    giveKit(p);
    ensureSiteArchitecture("ogygia");
    ensureHarborShip(p.dimension, 0, 64, -35);
    onStoryEvent(p, "site_ogygia");
  } else {
    respawnAtCheckpoint(p);
    recoverLostQuestItems(p, { notifyIfNone: false });
    flushRewardVault(p, { manual: false });
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
      ensureSiteArchitecture(site.id);
      if (site.fog && FOGS[site.fog]) fogOn(p, `odyssey:${site.fog}`, FOG_TAG);
      if (now() - dp(p, `studio:seen_${site.id}`, -1e9) > 6000) {
        setDp(p, `studio:seen_${site.id}`, now());
        title(p, `odyssey.site.${site.id}`, `odyssey.site.${site.id}.sub`);
        hear(p, "odyssey.world.arrive", undefined, 1, 1);
        onStoryEvent(p, `site_${site.id}`);
      }
    });
  }
}

const worldTime = () => { try { return typeof world.getAbsoluteTime === "function" ? world.getAbsoluteTime() : now(); } catch { return now(); } };
const readDeaths = () => { try { return JSON.parse(world.getDynamicProperty("odyssey:deaths") ?? "[]"); } catch { return []; } };
const writeDeaths = (list) => { try { world.setDynamicProperty("odyssey:deaths", JSON.stringify(list.slice(-64))); } catch { } };
const flagKey = (s, type) => `odyssey:site:${s.id}:${type}`;

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

export function tickSites() {
  if (!mapActive()) return;
  const dim = world.getDimension("minecraft:overworld");
  for (const s of SITES) {
    safe("site", () => {
      const center = { x: s.x, y: s.y, z: s.z };
      if (!playersNear(dim, center, 65).length) return;
      ensureSiteArchitecture(s.id);
      const wanted = new Map();
      for (const [type, dx, dz] of s.creatures) wanted.set(type, [...(wanted.get(type) ?? []), [dx, dz]]);
      for (const [type, spots] of wanted) {
        const flag = flagKey(s, type);
        if (!world.getDynamicProperty(flag)) {
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
        writeDeaths(deaths.filter((d) => !due.includes(d)));
      }
    });
  }
}
