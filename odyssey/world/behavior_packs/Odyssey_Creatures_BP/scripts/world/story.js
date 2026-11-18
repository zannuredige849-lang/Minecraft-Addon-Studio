// The Odyssey (2026) — Multiplayer Campaign, Odysseus & Telemachus Co-op Roles,
// Checkpoints, and 6 Branching Story Decisions with Real Gameplay Consequences.
import { world, ItemStack } from "@minecraft/server";
import { dp, effect, flat, now, ready, safe, setDp, valid, wait } from "../lib/util.js";
import { bar, hear, tell, title } from "../lib/fx.js";
import { startStoryVote } from "./pause_vote.js";
import { playSiteCutscene } from "./cinematics.js";
import { SITE_POINTS } from "../data/config.js";
import { CHAPTERS as CAMPAIGN } from "../data/campaign.js";
import {
  flushRewardVault, grantProgressionReward,
  onProgressionStoryMilestone, recoverLostQuestItems,
} from "./progression.js";
import { currentChapter, mainObjective, questEvent, setGlobalChapter } from "./quests.js";
import { teleportVerified } from "./selection.js";

// Chapter definitions live in data/campaign.js; this alias keeps older imports working.
export const CHAPTERS = CAMPAIGN.map((c) => ({ id: c.id, site: c.site, key: c.title, hint: c.story }));

// 6 Major Branching Decisions of the Campaign
export const STORY_DECISIONS = {
  ogygia: {
    id: "ogygia_lotus",
    promptKey: "odyssey.branch.ogygia.prompt",
    options: [
      { id: "resist", labelKey: "odyssey.branch.ogygia.a" },
      { id: "embrace_lotus", labelKey: "odyssey.branch.ogygia.b" },
    ],
  },
  troy: {
    id: "troy_altar",
    promptKey: "odyssey.branch.troy.prompt",
    options: [
      { id: "honor_athena", labelKey: "odyssey.branch.troy.a" },
      { id: "spoils_of_war", labelKey: "odyssey.branch.troy.b" },
    ],
  },
  cyclops: {
    id: "cyclops_escape",
    promptKey: "odyssey.branch.cyclops.prompt",
    options: [
      { id: "silent_flock", labelKey: "odyssey.branch.cyclops.a" },
      { id: "shout_name", labelKey: "odyssey.branch.cyclops.b" },
    ],
  },
  aeaea: {
    id: "circe_pact",
    promptKey: "odyssey.branch.aeaea.prompt",
    options: [
      { id: "swear_alliance", labelKey: "odyssey.branch.aeaea.a" },
      { id: "seize_spoils", labelKey: "odyssey.branch.aeaea.b" },
    ],
  },
  strait: {
    id: "strait_course",
    promptKey: "odyssey.branch.strait.prompt",
    options: [
      { id: "hug_scylla", labelKey: "odyssey.branch.strait.a" },
      { id: "skirt_charybdis", labelKey: "odyssey.branch.strait.b" },
    ],
  },
  thrinacia: {
    id: "thrinacia_oath",
    promptKey: "odyssey.branch.thrinacia.prompt",
    options: [
      { id: "keep_oath", labelKey: "odyssey.branch.thrinacia.a" },
      { id: "feast_cattle", labelKey: "odyssey.branch.thrinacia.b" },
    ],
  },
};

export const getChapter = () => currentChapter();

/** Chapter changes are driven by quest objectives (world/quests.js); this only moves forward. */
export function setChapter(p, ch) { setGlobalChapter(ch); }

// ------------------------------------------------------------------ 2-Player Roles: Odysseus, Telemachus & Companion
/** Role chosen on the selection screen (data/config.js ROLES). Unassigned players read as "companion". */
export function getPlayerRole(p) {
  return dp(p, "studio:role", "") || "companion";
}

export function cyclePlayerRole(p) {
  const order = ["odysseus", "telemachus", "companion", "eumaeus"];
  const cur = getPlayerRole(p);
  const next = order[(order.indexOf(cur) + 1) % order.length];
  setDp(p, "studio:role", next);
  tell(p, `odyssey.role.${next}`);
  bar(p, `odyssey.role.${next}`);
  hear(p, "odyssey.athena.chime", undefined, 0.8, 1.1);
  flushRewardVault(p, { manual: false });
  recoverLostQuestItems(p, { notifyIfNone: false });
  return next;
}

/** Tick role abilities & Odysseus + Telemachus cooperative proximity synergy. */
export function tickRoles() {
  const players = world.getAllPlayers().filter(valid);
  const ody = players.find((p) => getPlayerRole(p) === "odysseus");
  const tel = players.find((p) => getPlayerRole(p) === "telemachus");
  const coopNear = ody && tel && ody.dimension.id === tel.dimension.id && flat(ody.location, tel.location) <= 18;
  if (!players.some((p) => dp(p, "studio:role", ""))) return;   // nobody has chosen yet (selection screen)

  for (const p of players) {
    const role = getPlayerRole(p);
    if (role === "odysseus") {
      effect(p, "resistance", 60, 0);
    } else if (role === "telemachus") {
      effect(p, "speed", 60, 0);
    } else if (role === "companion") {
      effect(p, "haste", 60, 0);
    } else if (role === "eumaeus") {
      effect(p, "night_vision", 260, 0);
    }
    if (coopNear) {
      effect(p, "strength", 60, 0);
      effect(p, "regeneration", 60, 0);
    }
    // Apply persistent story branch perks
    if (getBranchChoice("ogygia_lotus") === "resist") effect(p, "strength", 60, 0);
    if (getBranchChoice("ogygia_lotus") === "embrace_lotus") effect(p, "regeneration", 60, 0);
    if (getBranchChoice("thrinacia_oath") === "keep_oath") effect(p, "fire_resistance", 60, 0);
  }
}

export function getBranchChoice(decisionId) {
  try { return world.getDynamicProperty(`odyssey:choice_${decisionId}`); } catch { return undefined; }
}

/** Apply real gameplay consequences when a multiplayer story branch vote resolves. */
export function applyBranchConsequence(decisionId, choiceId) {
  const players = world.getAllPlayers().filter(valid);
  for (const p of players) {
    const inv = p.getComponent("minecraft:inventory")?.container;
    if (decisionId === "ogygia_lotus") {
      if (choiceId === "resist") {
        effect(p, "strength", 2400, 0);
        effect(p, "speed", 2400, 0);
        tell(p, "odyssey.branch.ogygia.res_a");
      } else {
        safe("lotus_bonus", () => inv?.addItem(new ItemStack("studio:lotus_flower", 3)));
        effect(p, "regeneration", 3600, 1);
        tell(p, "odyssey.branch.ogygia.res_b");
      }
    } else if (decisionId === "troy_altar") {
      if (choiceId === "honor_athena") {
        grantProgressionReward(p, "studio:copper_hoplon", 1, { uniqueKey: "branch_troy_hoplon", role: "both", silent: true });
        effect(p, "absorption", 3600, 1);
        effect(p, "resistance", 3600, 0);
        tell(p, "odyssey.branch.troy.res_a");
      } else {
        grantProgressionReward(p, "studio:copper_cuirass", 1, { uniqueKey: "branch_troy_cuirass", role: "both", silent: true });
        safe("troy_spoils", () => inv?.addItem(new ItemStack("minecraft:copper_ingot", 6)));
        tell(p, "odyssey.branch.troy.res_b");
      }
    } else if (decisionId === "cyclops_escape") {
      if (choiceId === "silent_flock") {
        effect(p, "invisibility", 1200, 0);
        effect(p, "speed", 1200, 1);
        tell(p, "odyssey.branch.cyclops.res_a");
      } else {
        safe("xp", () => p.addLevels(5));
        effect(p, "strength", 2400, 1);
        try { p.dimension.runCommandAsync?.("weather thunder 4800"); } catch { }
        tell(p, "odyssey.branch.cyclops.res_b");
      }
    } else if (decisionId === "circe_pact") {
      if (choiceId === "swear_alliance") {
        safe("stew_gift", () => inv?.addItem(new ItemStack("studio:circe_stew", 1)));
        effect(p, "regeneration", 2400, 0);
        tell(p, "odyssey.branch.aeaea.res_a");
      } else {
        safe("wax_gift", () => inv?.addItem(new ItemStack("studio:beeswax", 4)));
        tell(p, "odyssey.branch.aeaea.res_b");
      }
    } else if (decisionId === "strait_course") {
      if (choiceId === "hug_scylla") {
        effect(p, "resistance", 2400, 1);
        tell(p, "odyssey.branch.strait.res_a");
      } else {
        effect(p, "speed", 2400, 1);
        tell(p, "odyssey.branch.strait.res_b");
      }
    } else if (decisionId === "thrinacia_oath") {
      if (choiceId === "keep_oath") {
        grantProgressionReward(p, "studio:apollo_sun_talisman", 1, { uniqueKey: "branch_thrinacia_talisman", role: "both", silent: true });
        effect(p, "fire_resistance", 6000, 0);
        effect(p, "regeneration", 2400, 0);
        try { p.dimension.runCommandAsync?.("weather clear 6000"); } catch { }
        tell(p, "odyssey.branch.thrinacia.res_a");
      } else {
        safe("beef", () => inv?.addItem(new ItemStack("minecraft:cooked_beef", 8)));
        effect(p, "strength", 1800, 1);
        tell(p, "odyssey.branch.thrinacia.res_b");
      }
    }
  }
}

export function triggerSiteDecisionVote(siteId) {
  const spec = STORY_DECISIONS[siteId];
  if (!spec) return false;
  if (getBranchChoice(spec.id)) return false;
  return startStoryVote({
    id: spec.id,
    promptKey: spec.promptKey,
    options: spec.options,
    timeoutTicks: 900,
    onFinish: (winnerId) => { applyBranchConsequence(spec.id, winnerId); questEvent(null, `vote:${spec.id}`); },
  });
}

// ------------------------------------------------------------------ Checkpoints & Story Events
export function setCheckpoint(p, siteId) {
  if (!valid(p)) return;
  setDp(p, "studio:checkpoint", siteId);
}

export function respawnAtCheckpoint(p) {
  const cid = dp(p, "studio:checkpoint", "");
  const point = SITE_POINTS[cid] ?? dp(p, "studio:checkpoint_point", "");
  if (!point) return;
  teleportVerified(p, point, () => bar(p, `odyssey.site.${cid || "ogygia"}`));
}

export function onStoryEvent(p, eventId) {
  if (!valid(p)) return;
  onProgressionStoryMilestone(p, eventId);
  const flag = `studio:story_${eventId}`;
  const firstTime = !dp(p, flag, false);
  if (firstTime) setDp(p, flag, true);

  if (eventId.startsWith("site_")) {
    const siteId = eventId.replace("site_", "");
    setCheckpoint(p, siteId);
    if (firstTime) {
      playSiteCutscene(siteId, p, false);
    }
  }

  switch (eventId) {
    case "site_ogygia":
      if (firstTime) tell(p, "odyssey.story.ogygia_intro");
      break;
    case "lotus_gifted":
      triggerSiteDecisionVote("ogygia");
      break;
    case "site_troy":
      if (firstTime) tell(p, "odyssey.story.troy_intro");
      break;
    case "site_sparta":
      if (firstTime) tell(p, "odyssey.story.sparta_intro");
      break;
    case "horse_hidden":
      if (firstTime) tell(p, "odyssey.story.horse_memory");
      triggerSiteDecisionVote("troy");
      break;
    case "site_cyclops":
      if (firstTime) tell(p, "odyssey.story.cyclops_intro");
      break;
    case "cyclops_blinded":
      if (firstTime) tell(p, "odyssey.story.cyclops_done");
      triggerSiteDecisionVote("cyclops");
      break;
    case "site_telepylus":
      if (firstTime) tell(p, "odyssey.story.telepylus_intro");
      break;
    case "site_aeaea":
      if (firstTime) tell(p, "odyssey.story.aeaea_intro");
      break;
    case "circe_yielded":
      if (firstTime) tell(p, "odyssey.story.circe_done");
      triggerSiteDecisionVote("aeaea");
      break;
    case "site_hades":
      if (firstTime) tell(p, "odyssey.story.hades_intro");
      break;
    case "hades_sacrifice":
      if (firstTime) tell(p, "odyssey.story.hades_done");
      break;
    case "site_sirens":
      if (firstTime) tell(p, "odyssey.story.sirens_intro");
      break;
    case "site_strait":
      if (firstTime) tell(p, "odyssey.story.strait_intro");
      triggerSiteDecisionVote("strait");
      break;
    case "site_thrinacia":
      if (firstTime) tell(p, "odyssey.story.thrinacia_intro");
      triggerSiteDecisionVote("thrinacia");
      break;
    case "site_ithaca":
      if (firstTime) tell(p, "odyssey.story.ithaca_intro");
      break;
    case "ithaca_blessed":
      if (firstTime) tell(p, "odyssey.story.ithaca_complete");
      break;
    default:
      break;
  }
  questEvent(p, eventId);
}

export function tellChapterGuidance(p, npcType) {
  if (!valid(p) || !ready(p, "studio:cd_guidance")) return;
  wait(p, "studio:cd_guidance", 60);
  const ch = getChapter();
  if (npcType === "studio:athena") {
    tell(p, `odyssey.athena.guide.${ch}`);
  } else if (npcType === "studio:calypso") {
    tell(p, ch <= 2 ? "odyssey.calypso.guide.early" : "odyssey.calypso.guide.late");
  } else if (npcType === "studio:circe") {
    tell(p, ch <= 6 ? "odyssey.circe.guide.hades" : "odyssey.circe.guide.strait");
  }
  const o = mainObjective(p);
  if (o) bar(p, `odyssey.q.${o.id}`);
}
