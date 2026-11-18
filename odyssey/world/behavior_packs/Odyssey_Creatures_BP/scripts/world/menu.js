// The Odyssey Astrolabe: opens the in-game menu (Bedrock forms, works on touch, controller and keyboard).
//   Journal (individual objectives, destination, coordinates, navigation toggle)
//   Story decision vote (when one is open the astrolabe goes straight to the ballot)
//   Replay the nearest island's cinematic, claim the reward vault / recover lost quest items
//   Host controls: global pause, voting rule, role manager
import { ActionFormData } from "@minecraft/server-ui";
import { flat, valid } from "../lib/util.js";
import { msg, tell } from "../lib/fx.js";
import { SITES } from "../data/sites.js";
import { castVote, getActiveVote, getVotingRule, toggleGlobalPause, toggleVotingRule } from "./pause_vote.js";
import { playSiteCutscene, cutsceneActive } from "./cinematics.js";
import { flushRewardVault, recoverLostQuestItems } from "./progression.js";
import { openJournal } from "./quests.js";
import { campaignStarted, isHost, openRoleManager, showSelection } from "./selection.js";

function currentSiteNear(p) {
  let best = SITES[0], bd = Infinity;
  for (const s of SITES) {
    const d = flat(p.location, s);
    if (d < bd) { best = s; bd = d; }
  }
  return best;
}

export function openVote(p, vote) {
  const f = new ActionFormData().title(msg("odyssey.vote.title")).body(msg(vote.promptKey));
  vote.options.forEach((o) => f.button(msg(o.labelKey)));
  f.show(p).then((r) => { if (!r.canceled) castVote(p, r.selection); }).catch(() => { });
}

function openHost(p) {
  const f = new ActionFormData().title(msg("odyssey.host.title")).body(msg("odyssey.host.body"))
    .button(msg("odyssey.host.pause"), "textures/ui/pause")
    .button(msg(getVotingRule() === "majority" ? "odyssey.host.rule_majority" : "odyssey.host.rule_unanimous"), "textures/ui/vote")
    .button(msg("odyssey.host.roles"), "textures/ui/permissions_member_star")
    .button(msg("odyssey.ui.back"));
  f.show(p).then((r) => {
    if (r.canceled) return;
    if (r.selection === 0) toggleGlobalPause(p);
    else if (r.selection === 1) toggleVotingRule(p);
    else if (r.selection === 2) openRoleManager(p);
    else onUseAstrolabe(p);
  }).catch(() => { });
}

/** Called when a player uses `studio:odyssey_astrolabe`. */
export function onUseAstrolabe(p) {
  if (!valid(p)) return;
  if (!campaignStarted()) { showSelection(p); return; }
  if (cutsceneActive()) return;
  const vote = getActiveVote();
  if (vote) { openVote(p, vote); return; }

  const actions = [];
  const f = new ActionFormData().title(msg("odyssey.menu.title")).body(msg("odyssey.menu.body"));
  f.button(msg("odyssey.menu.journal"), "textures/items/book_writable"); actions.push(() => openJournal(p));
  f.button(msg("odyssey.menu.cutscene"), "textures/ui/camera-yo"); actions.push(() => playSiteCutscene(currentSiteNear(p).id, p, true));
  f.button(msg("odyssey.menu.vault"), "textures/ui/icon_recipe_item"); actions.push(() => {
    flushRewardVault(p, { manual: true });
    recoverLostQuestItems(p, { notifyIfNone: true });
  });
  if (isHost(p)) { f.button(msg("odyssey.menu.host"), "textures/ui/op"); actions.push(() => openHost(p)); }
  f.button(msg("odyssey.ui.close")); actions.push(() => { });
  f.show(p).then((r) => { if (!r.canceled) actions[r.selection]?.(); }).catch(() => tell(p, "odyssey.menu.busy"));
}
