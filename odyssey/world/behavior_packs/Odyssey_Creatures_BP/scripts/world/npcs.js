// Story NPCs built on studio:odyssey_person: Mentor, Eumaeus and Telemachus (who is an NPC whenever no player plays
// him, e.g. in single-player). They are placed on verified points, re-checked against the terrain at runtime, and
// only spawned while a player is near enough for the chunk to be loaded.
import { world } from "@minecraft/server";
import { POINTS } from "../data/config.js";
import { dp, flat, nearestPlayer, playersNear, safe, setDp, setProp, valid } from "../lib/util.js";
import { hear, tell } from "../lib/fx.js";
import { perform, busy } from "../lib/moves.js";
import { safeSpotNear } from "../lib/terrain.js";
import { bindCompanion } from "./companions.js";
import { currentChapter, questEvent, roleOf } from "./quests.js";
import { onGuideTalk, isGuide } from "./guides.js";

export const PERSON = "studio:odyssey_person";
export const VARIANT = { telemachus: 0, mentor: 1, eumaeus: 2, guide_scout: 3, guide_fisher: 4, guide_shepherd: 5, odysseus: 6 };

const STORY_NPCS = [
  { key: "mentor",     name: "Mentor",     point: "ithaca_mentor",  when: (ch) => ch === 1,             replacedBy: null },
  { key: "eumaeus",    name: "Eumaeus",    point: "ithaca_eumaeus", when: () => true,                    replacedBy: "eumaeus" },
  { key: "telemachus", name: "Telemachus", point: "ithaca_square",  when: (ch) => ch === 1 || ch === 9, replacedBy: "telemachus" },
];
const tagOf = (key) => `odyssey_npc_${key}`;
const someoneIs = (role) => world.getAllPlayers().some((p) => valid(p) && roleOf(p) === role);

function findNpc(dim, key) {
  try { return dim.getEntities({ type: PERSON, tags: [tagOf(key)] }).filter(valid); } catch { return []; }
}

export function tickStoryNpcs() {
  if (world.getDynamicProperty("odyssey:campaign_started") !== true) return;
  const dim = world.getDimension("minecraft:overworld");
  const ch = currentChapter();
  for (const spec of STORY_NPCS) {
    safe(`npc.${spec.key}`, () => {
      const existing = findNpc(dim, spec.key);
      const wanted = spec.when(ch) && !(spec.replacedBy && someoneIs(spec.replacedBy));
      if (!wanted) { for (const e of existing) if (!dp(e, "studio:following", false)) e.remove(); return; }
      for (const extra of existing.slice(1)) extra.remove();
      if (existing.length) return;
      const pt = POINTS[spec.point];
      if (!playersNear(dim, pt, 48).length) return;          // chunk must be loaded
      const spot = safeSpotNear(dim, pt.x, pt.z, 6, Math.floor(pt.y) + 6);
      if (!spot) return;
      const e = dim.spawnEntity(PERSON, spot);
      e.addTag(tagOf(spec.key));
      setProp(e, "studio:variant", VARIANT[spec.key]);
      e.nameTag = spec.name;
      setDp(e, "studio:npc_key", spec.key);
    });
  }
  // Chapter IX: an NPC Telemachus joins his father for the homecoming.
  if (ch === 9 && !someoneIs("telemachus")) {
    const tel = findNpc(dim, "telemachus")[0];
    const ody = world.getAllPlayers().find((p) => roleOf(p) === "odysseus");
    if (tel && ody && !dp(tel, "studio:following", false) && flat(tel.location, ody.location) < 16) {
      bindCompanion(tel, ody, false);
      tell(ody, "odyssey.npc.telemachus.joins");
    }
  }
}

const LINES = {
  mentor:     (p, ch) => `odyssey.npc.mentor.${roleOf(p) === "telemachus" ? "telemachus" : "other"}`,
  eumaeus:    (p, ch) => (ch === 9 ? (roleOf(p) === "odysseus" ? "odyssey.npc.eumaeus.recognise" : "odyssey.npc.eumaeus.ch9") : "odyssey.npc.eumaeus.wait"),
  telemachus: (p, ch) => (ch === 9 ? "odyssey.npc.telemachus.ch9" : "odyssey.npc.telemachus.ch1"),
};

/** studio:talk fired by an odyssey_person (player interacted with it). */
export function onPersonTalk(npc) {
  if (!valid(npc)) return;
  const p = nearestPlayer(npc, 7, () => true);
  if (!p) return;
  if (isGuide(npc)) { onGuideTalk(npc, p); return; }
  const key = dp(npc, "studio:npc_key", "");
  const ch = currentChapter();
  const line = LINES[key]?.(p, ch);
  if (line) tell(p, line);
  hear(p, "odyssey.athena.chime", undefined, 0.4, 0.8);
  if (!busy(npc)) safe("npc.anim", () => perform(npc, key === "eumaeus" && ch === 9 ? "cheer" : "point", {}, { still: true }));
  if (key === "mentor") questEvent(p, "talk_mentor");
  if (key === "eumaeus" && ch === 9) questEvent(p, "talk_eumaeus");
  if (key === "telemachus" && ch === 9 && roleOf(p) === "odysseus") bindCompanion(npc, p, true);
}

/** A player playing Eumaeus counts as "found" when Odysseus stands next to him in Chapter IX. */
export function tickPlayerEumaeus() {
  if (currentChapter() !== 9) return;
  const eu = world.getAllPlayers().find((p) => roleOf(p) === "eumaeus");
  const od = world.getAllPlayers().find((p) => roleOf(p) === "odysseus");
  if (eu && od && eu.dimension.id === od.dimension.id && flat(eu.location, od.location) < 4) questEvent(od, "talk_eumaeus");
}
