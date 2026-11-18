// Global Controlled Pause & Synchronized Multiplayer Voting System.
// Maintains 5 distinct world states:
//   NORMAL_GAMEPLAY | MENU_SELECTION | STORY_VOTING | CINEMATIC_PLAYBACK | GLOBAL_PAUSE
// Freezes AI decisions, companion following, and story/cooldown timers cleanly without
// breaking server ticks or resetting entity positions, and resolves multiplayer votes
// via configurable Majority (>50%) or Unanimous (100%) rules with tie & disconnect handling.
import { world } from "@minecraft/server";
import { advancePauseOffset, clearEffect, dp, effect, rawNow, safe, setDp, valid } from "../lib/util.js";
import { bar, hear, tell, title } from "../lib/fx.js";
import { creatures } from "../lib/registry.js";

export const STATE_NORMAL    = "NORMAL_GAMEPLAY";
export const STATE_MENU      = "MENU_SELECTION";
export const STATE_VOTING    = "STORY_VOTING";
export const STATE_CINEMATIC = "CINEMATIC_PLAYBACK";
export const STATE_PAUSE     = "GLOBAL_PAUSE";

const PAUSABLE_TYPES = [
  "studio:cyclops", "studio:laestrygonian", "studio:laestrygonian_child", "studio:circe",
  "studio:siren", "studio:scylla", "studio:charybdis", "studio:shade", "studio:tiresias",
  "studio:sun_cattle", "studio:calypso", "studio:athena"
];

let worldState = STATE_NORMAL;
let activeVote = null; // { id, promptKey, options: [{labelKey, id}], votes: Map<playerId, int>, startedAt, timeoutTicks, onFinish }

export const getWorldState = () => worldState;
export const isWorldPaused = () => worldState === STATE_PAUSE || worldState === STATE_VOTING || worldState === STATE_MENU;
export const isCinematicActive = () => worldState === STATE_CINEMATIC;
export const getActiveVote = () => activeVote;

export function getVotingRule() {
  try { return world.getDynamicProperty("odyssey:vote_rule") ?? "majority"; } catch { return "majority"; }
}
export function toggleVotingRule(p) {
  const next = getVotingRule() === "majority" ? "unanimous" : "majority";
  try { world.setDynamicProperty("odyssey:vote_rule", next); } catch { }
  if (p) tell(p, next === "majority" ? "odyssey.vote.rule_majority" : "odyssey.vote.rule_unanimous");
  return next;
}

/** Enter controlled global pause without resetting entities or breaking animations. */
export function setWorldState(newState, initiator) {
  if (worldState === newState) return;
  const wasPaused = isWorldPaused();
  worldState = newState;
  const nowPaused = isWorldPaused();

  if (!wasPaused && nowPaused) {
    for (const p of world.getAllPlayers()) {
      hear(p, "odyssey.athena.shimmer", undefined, 0.6, 0.9);
      if (newState === STATE_PAUSE) {
        title(p, "odyssey.pause.title", "odyssey.pause.sub");
        tell(p, "odyssey.pause.on");
      }
    }
  } else if (wasPaused && !nowPaused) {
    // Restore entity movement cleanly
    for (const type of PAUSABLE_TYPES) {
      for (const e of creatures(type)) {
        if (valid(e)) clearEffect(e, "slowness");
      }
    }
    for (const p of world.getAllPlayers()) {
      clearEffect(p, "slowness");
      hear(p, "odyssey.athena.chime", undefined, 0.6, 1.1);
      if (initiator) tell(p, "odyssey.pause.off");
    }
  }
}

export function toggleGlobalPause(p) {
  if (worldState === STATE_VOTING || worldState === STATE_CINEMATIC) return;
  if (worldState === STATE_PAUSE || worldState === STATE_MENU) {
    setWorldState(STATE_NORMAL, p);
  } else {
    setWorldState(STATE_PAUSE, p);
  }
}

// ------------------------------------------------------------------ Multiplayer Voting Engine
export function startStoryVote({ id, promptKey, options, timeoutTicks = 900, onFinish }) {
  if (activeVote) return false;
  activeVote = {
    id,
    promptKey,
    options, // [{ id: "a", labelKey: "..." }, { id: "b", labelKey: "..." }]
    votes: new Map(),
    startedAt: rawNow(),
    timeoutTicks,
    onFinish,
  };
  setWorldState(STATE_VOTING);
  for (const p of world.getAllPlayers()) {
    setDp(p, "studio:menu_cursor", 0);
    title(p, "odyssey.vote.title", promptKey);
    tell(p, promptKey);
    options.forEach((opt, idx) => tell(p, opt.labelKey));
    tell(p, "odyssey.vote.howto");
    hear(p, "odyssey.athena.chime", undefined, 0.9, 1.0);
  }
  return true;
}

export function castVote(p, optionIndex) {
  if (!activeVote || !valid(p)) return false;
  const idx = Math.max(0, Math.min(activeVote.options.length - 1, optionIndex));
  activeVote.votes.set(p.id, idx);
  hear(p, "odyssey.calypso.lotus_chime", undefined, 0.8, 1.1);
  tell(p, activeVote.options[idx].labelKey);
  evaluateVoteResolution(false);
  return true;
}

export function onVotePlayerLeave(playerId) {
  if (!activeVote) return;
  activeVote.votes.delete(playerId);
  evaluateVoteResolution(false);
}

function tallyVotes() {
  const players = world.getAllPlayers().filter(valid);
  const eligible = Math.max(1, players.length);
  const counts = activeVote.options.map(() => 0);
  let votedCount = 0;
  for (const p of players) {
    const v = activeVote.votes.get(p.id);
    if (v !== undefined && counts[v] !== undefined) {
      counts[v]++;
      votedCount++;
    }
  }
  const maxVotes = Math.max(...counts);
  const leaders = counts.map((c, i) => (c === maxVotes ? i : -1)).filter((i) => i >= 0);
  const isTie = votedCount > 0 && leaders.length > 1;
  return { eligible, votedCount, remaining: eligible - votedCount, counts, maxVotes, leaders, isTie };
}

export function evaluateVoteResolution(timedOut = false) {
  if (!activeVote) return;
  const { eligible, votedCount, counts, maxVotes, leaders, isTie } = tallyVotes();
  const rule = getVotingRule();

  let resolvedIndex = -1;
  if (!isTie && votedCount > 0) {
    if (rule === "unanimous") {
      if (maxVotes >= eligible) resolvedIndex = leaders[0];
    } else {
      // Majority rule: > 50% of eligible players (for 2 players, > 1 means 2 votes unless timed out)
      if (maxVotes > eligible / 2 && (eligible === 1 || votedCount >= eligible || maxVotes > eligible / 2)) {
        resolvedIndex = leaders[0];
      }
    }
  }

  // If timed out (or all voted in a tie after timeout), break tie deterministically in favor of Option 0 (Odysseus's lead)
  if (resolvedIndex === -1 && timedOut) {
    resolvedIndex = leaders.length ? leaders[0] : 0;
  }

  if (resolvedIndex !== -1) {
    const winner = activeVote.options[resolvedIndex];
    const finishCb = activeVote.onFinish;
    const voteId = activeVote.id;
    activeVote = null;
    try { world.setDynamicProperty(`odyssey:choice_${voteId}`, winner.id); } catch { }
    for (const p of world.getAllPlayers()) {
      tell(p, "odyssey.vote.resolved");
      tell(p, winner.labelKey);
      hear(p, "odyssey.music.cinematic", undefined, 0.8, 1.0);
    }
    setWorldState(STATE_NORMAL);
    if (finishCb) safe("vote.finish", () => finishCb(winner.id, resolvedIndex));
  }
}

/** Runs every tick: advances pause offset when paused and updates live voting/pause HUD. */
export function tickPauseAndVote() {
  if (isWorldPaused()) {
    advancePauseOffset(1);
    if (rawNow() % 4 === 0) {
      for (const type of PAUSABLE_TYPES) {
        for (const e of creatures(type)) {
          if (valid(e)) {
            effect(e, "slowness", 10, 255);
            try { e.clearVelocity?.(); } catch { }
          }
        }
      }
    }
  }

  if (worldState === STATE_VOTING && activeVote) {
    const elapsed = rawNow() - activeVote.startedAt;
    if (elapsed >= activeVote.timeoutTicks) {
      evaluateVoteResolution(true);
      return;
    }
    if (rawNow() % 10 === 0) {
      const { eligible, votedCount, remaining, counts, isTie } = tallyVotes();
      const secsLeft = Math.max(1, Math.ceil((activeVote.timeoutTicks - elapsed) / 20));
      const distStr = counts.map((c, i) => `[${i + 1}: ${c}]`).join(" ");
      for (const p of world.getAllPlayers()) {
        const cur = dp(p, "studio:menu_cursor", 0) + 1;
        const status = isTie
          ? `§eTIE ${distStr} §7(${votedCount}/${eligible} voted, ${secsLeft}s) | §bSelect [${cur}] (Sneak+Use Astrolabe)`
          : `§6VOTE ${distStr} §7(Voted: ${votedCount}/${eligible}, Left: ${remaining}, ${secsLeft}s) | §bChoice [${cur}]`;
        try { p.onScreenDisplay.setActionBar(status); } catch { }
      }
    }
  } else if (worldState === STATE_PAUSE && rawNow() % 20 === 0) {
    for (const p of world.getAllPlayers()) {
      bar(p, "odyssey.pause.bar");
    }
  }
}
