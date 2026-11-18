// Global Multiplayer Menu System (Controlled via the Odyssey Astrolabe item).
// Supports:
//   1. Character Role Selection (Odysseus / Telemachus / Ithacan Companion)
//   2. Current Chapter & Quest Objective Briefing
//   3. Triggering / Voting on Story Branch Decisions
//   4. Replaying the Current Island's Cinematic Cutscene
//   5. Toggling Voting Rule (Majority >50% vs Unanimous 100%)
//   6. Toggling Controlled Global World Pause / Resume
import { dp, flat, setDp, valid } from "../lib/util.js";
import { bar, hear, tell } from "../lib/fx.js";
import { SITES } from "../data/sites.js";
import {
  STATE_VOTING, castVote, getActiveVote, getVotingRule,
  toggleGlobalPause, toggleVotingRule,
} from "./pause_vote.js";
import {
  CHAPTERS, STORY_DECISIONS, cyclePlayerRole, getChapter,
  getPlayerRole, triggerSiteDecisionVote,
} from "./story.js";
import { playSiteCutscene } from "./cinematics.js";
import { flushRewardVault, recoverLostQuestItems } from "./progression.js";

const MENU_ITEMS = [
  "odyssey.menu.opt.role",
  "odyssey.menu.opt.objective",
  "odyssey.menu.opt.vault",
  "odyssey.menu.opt.vote",
  "odyssey.menu.opt.cutscene",
  "odyssey.menu.opt.rule",
  "odyssey.menu.opt.pause",
];

function currentSiteNear(p) {
  let best = SITES[0], bd = Infinity;
  for (const s of SITES) {
    const d = flat(p.location, s);
    if (d < bd) { best = s; bd = d; }
  }
  return best;
}

/** Called when a player uses `studio:odyssey_astrolabe`. */
export function onUseAstrolabe(p) {
  if (!valid(p)) return;

  // If a multiplayer story vote is active:
  // Standing + Use cycles vote choices; Sneaking + Use casts the vote!
  const vote = getActiveVote();
  if (vote) {
    let cur = dp(p, "studio:menu_cursor", 0);
    if (p.isSneaking) {
      castVote(p, cur);
    } else {
      cur = (cur + 1) % vote.options.length;
      setDp(p, "studio:menu_cursor", cur);
      hear(p, "odyssey.athena.chime", undefined, 0.6, 1.2);
      tell(p, vote.options[cur].labelKey);
    }
    return;
  }

  // Normal Menu operation:
  // Standing + Use cycles the 6 Ancient Greek Astrolabe menu options;
  // Sneaking + Use activates the selected option!
  let idx = dp(p, "studio:astrolabe_idx", 0);
  if (!p.isSneaking) {
    idx = (idx + 1) % MENU_ITEMS.length;
    setDp(p, "studio:astrolabe_idx", idx);
    hear(p, "odyssey.athena.chime", undefined, 0.5, 1.15);
    bar(p, MENU_ITEMS[idx]);
    return;
  }

  // Sneak + Use: execute the highlighted menu command
  switch (idx) {
    case 0: // Cycle Role: Odysseus / Telemachus / Companion
      cyclePlayerRole(p);
      break;
    case 1: { // Show Current Chapter, Role & Objective
      const ch = getChapter(p);
      const role = getPlayerRole(p);
      const info = CHAPTERS.find((c) => c.id === ch) ?? CHAPTERS[0];
      tell(p, `odyssey.role.${role}`);
      tell(p, info.key);
      tell(p, info.hint);
      bar(p, info.hint);
      hear(p, "odyssey.athena.chime", undefined, 0.8, 1.0);
      break;
    }
    case 2: { // Claim Unclaimed Reward Vault & Recover Lost Quest Items
      flushRewardVault(p, { manual: true });
      recoverLostQuestItems(p, { notifyIfNone: true });
      break;
    }
    case 3: { // Open Story Decision Vote for nearest site (or Ogygia default)
      const site = currentSiteNear(p);
      const targetSite = STORY_DECISIONS[site.id] ? site.id : "ogygia";
      if (!triggerSiteDecisionVote(targetSite)) {
        const spec = STORY_DECISIONS[targetSite];
        if (spec) {
          try { p.dimension.runCommandAsync?.(`scriptevent odyssey:revote_${targetSite}`); } catch { }
        }
        tell(p, "odyssey.vote.already_decided");
      }
      break;
    }
    case 4: { // Replay Cinematic Cutscene for nearest site
      const site = currentSiteNear(p);
      playSiteCutscene(site.id, p, true);
      break;
    }
    case 5: // Toggle Voting Rule (Majority >50% vs Unanimous 100%)
      toggleVotingRule(p);
      break;
    case 6: // Toggle Controlled Global Pause / Resume
      toggleGlobalPause(p);
      break;
    default:
      break;
  }
}
