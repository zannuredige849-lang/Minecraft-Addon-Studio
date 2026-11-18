// Character selection, role assignment, black-screen transition and role-specific teleportation.
//
// Opening sequence (first players into a fresh world):
//   1. Controlled global pause (STATE_MENU): creature AI, companions, story timers and votes stop; players' movement
//      and look input are locked and the camera holds an establishing shot of the sea.
//   2. Every player gets the selection screen. Roles offered depend on how many players are connected:
//        1 player  -> Odysseus (Telemachus is an NPC);  2 -> Odysseus + Telemachus;
//        3+        -> the two primary roles are reserved first, then supporting roles (Ithacan Companion, Eumaeus).
//      Exclusive roles can be held once unless the host enables shared roles.
//   3. The host (first player in) can auto-assign everyone, start with the current picks, or allow shared roles.
//      A player who never answers is auto-assigned after TIMING.selectionTimeout so nobody is locked out.
//   4. When everyone has a role: fade to black, wait until fully black, teleport each player to their role's start
//      (verified point, re-checked at runtime, retried, safe fallback), equip them, start their quests, play the
//      opening cinematic for the island they start on, fade back in and restore normal play.
// Late joiners pick from the roles still free and are faded and teleported to the party without pausing anyone else.
import { world, system, ItemStack } from "@minecraft/server";
import { ActionFormData, MessageFormData, FormCancelationReason } from "@minecraft/server-ui";
import { POINTS, ROLES, ROLE_ORDER, START_KITS, START_POSITIONS, TIMING } from "../data/config.js";
import { dp, flat, now, rawNow, safe, setDp, valid } from "../lib/util.js";
import { bar, hear, msg, tell, title } from "../lib/fx.js";
import { safeSpotNear, standAt } from "../lib/terrain.js";
import { STATE_MENU, STATE_NORMAL, getWorldState, setWorldState } from "./pause_vote.js";
import { camClear, camFade, camFree, lockInput } from "./cinematics.js";
import { playOpening } from "./story_cinematics.js";
import { currentChapter, checkChapter, roleOf } from "./quests.js";
import { grantProgressionReward } from "./progression.js";
import { ensureSiteArchitecture } from "./architect.js";

const lobby = new Map();          // playerId -> { joinedAt, role, showing }
let transitioning = false;

export const campaignStarted = () => { try { return world.getDynamicProperty("odyssey:campaign_started") === true; } catch { return false; } };
const sharedRoles = () => { try { return world.getDynamicProperty("odyssey:shared_roles") === true; } catch { return false; } };
const byId = (id) => world.getAllPlayers().find((p) => p.id === id);
const lobbyPlayers = () => [...lobby.keys()].map(byId).filter(valid);
export const hostId = () => [...lobby.entries()].sort((a, b) => a[1].joinedAt - b[1].joinedAt)[0]?.[0]
  ?? (() => { try { return world.getDynamicProperty("odyssey:host"); } catch { return undefined; } })();
export const isHost = (p) => p.id === hostId() || (() => { try { return world.getDynamicProperty("odyssey:host") === p.id; } catch { return false; } })();

// ------------------------------------------------------------------ role rules
/** Roles shown for the current player count. */
function rolesOffered(n) {
  if (n <= 1) return ["odysseus"];
  if (n === 2) return ["odysseus", "telemachus"];
  return ROLE_ORDER;
}
/** Who holds a role right now (lobby picks before start, saved roles after). */
function holders(role) {
  const out = [];
  for (const p of world.getAllPlayers()) {
    if (!valid(p)) continue;
    const r = campaignStarted() ? roleOf(p) : lobby.get(p.id)?.role;
    if (r === role) out.push(p);
  }
  return out;
}
/** Why `p` cannot take `role` (lang key), or undefined if allowed. */
function blockReason(p, role, n) {
  if (!rolesOffered(n).includes(role)) return n <= 1 && role === "telemachus" ? "odyssey.sel.solo_npc" : "odyssey.sel.not_offered";
  const others = holders(role).filter((q) => q.id !== p.id);
  if (ROLES[role].exclusive && others.length && !sharedRoles()) return "odyssey.sel.taken";
  if (!ROLES[role].primary && !campaignStarted()) {
    // Primary roles are reserved: a supporting pick must leave enough undecided players to fill them.
    const unclaimed = ["odysseus", "telemachus"].filter((r) => rolesOffered(n).includes(r) && !holders(r).length).length;
    const undecided = lobbyPlayers().filter((q) => q.id !== p.id && !lobby.get(q.id)?.role).length;
    if (undecided < unclaimed) return "odyssey.sel.reserved";
  }
  return undefined;
}

// ------------------------------------------------------------------ lobby lifecycle
export function onSelectionJoin(p) {
  if (campaignStarted()) { lateJoin(p); return; }
  if (!lobby.has(p.id)) lobby.set(p.id, { joinedAt: rawNow(), role: undefined, showing: false });
  try { if (!world.getDynamicProperty("odyssey:host")) world.setDynamicProperty("odyssey:host", p.id); } catch { }
  setWorldState(STATE_MENU);
  holdLobbyCamera(p);
  system.runTimeout(() => showSelection(p), 40);   // give the client time to finish loading
}

export function onSelectionLeave(playerId) {
  lobby.delete(playerId);
  try { if (world.getDynamicProperty("odyssey:host") === playerId) world.setDynamicProperty("odyssey:host", hostId() ?? ""); } catch { }
  if (!campaignStarted() && !transitioning) {
    if (!lobby.size) setWorldState(STATE_NORMAL);
    else maybeBegin();
  }
}

function holdLobbyCamera(p) {
  setDp(p, "studio:locked", true);
  lockInput(p, true);
  const h = POINTS.ogygia_harbor;
  camFree(p, { x: h.x + 34, y: h.y + 18, z: h.z - 26 }, { x: 0, y: 64, z: 0 }, 0);
}

/** Runs every second while the lobby is open: status line, timeouts, retries of forms that failed to open. */
export function tickSelection() {
  if (campaignStarted() || transitioning || !lobby.size) return;
  const n = lobbyPlayers().length;
  const chosen = lobbyPlayers().filter((p) => lobby.get(p.id)?.role).length;
  for (const p of lobbyPlayers()) {
    const e = lobby.get(p.id);
    if (getWorldState() !== STATE_MENU) setWorldState(STATE_MENU);
    if (e.role) bar(p, "odyssey.sel.waiting", String(chosen), String(n));
    if (!e.role && rawNow() - e.joinedAt > TIMING.selectionTimeout) {
      autoAssign([p]);
      tell(p, "odyssey.sel.timeout");
      maybeBegin();
    }
  }
}

// ------------------------------------------------------------------ forms
const roleName = (r) => ({ rawtext: [{ translate: `odyssey.role.${r}.name` }] });

function rosterText() {
  const lines = [];
  for (const q of lobbyPlayers()) {
    const r = lobby.get(q.id)?.role;
    lines.push({ text: `\n §7• §f${q.name}${isHost(q) ? " §6★" : ""} §8— ` }, r ? { translate: `odyssey.role.${r}.name` } : { translate: "odyssey.sel.choosing" });
  }
  return lines;
}

export function showSelection(p) {
  if (!valid(p) || campaignStarted() || transitioning) return;
  const e = lobby.get(p.id);
  if (!e || e.showing) return;
  const n = lobbyPlayers().length;
  const roles = ROLE_ORDER.filter((r) => rolesOffered(n).includes(r) || (n === 1 && r === "telemachus"));
  const form = new ActionFormData()
    .title(msg("odyssey.sel.title"))
    .body({ rawtext: [{ translate: "odyssey.sel.body", with: [String(n)] }, { translate: `odyssey.sel.rule.${Math.min(n, 3)}` }, { text: "\n" }, ...rosterText()] });
  const actions = [];
  for (const r of roles) {
    const why = blockReason(p, r, n);
    const holder = holders(r).filter((q) => q.id !== p.id)[0];
    const status = why === "odyssey.sel.solo_npc" ? { translate: "odyssey.sel.status.npc" }
      : holder ? { translate: "odyssey.sel.status.taken", with: [holder.name] }
      : why ? { translate: "odyssey.sel.status.locked" } : { translate: "odyssey.sel.status.free" };
    form.button({ rawtext: [{ translate: `odyssey.role.${r}.button` }, { text: "\n" }, status] }, ROLES[r].portrait);
    actions.push(["role", r]);
  }
  if (isHost(p)) {
    form.button(msg("odyssey.sel.host.auto"), "textures/ui/refresh_light");
    actions.push(["auto"]);
    form.button(msg("odyssey.sel.host.start"), "textures/ui/realms_slot_check");
    actions.push(["start"]);
    form.button(msg(sharedRoles() ? "odyssey.sel.host.shared_on" : "odyssey.sel.host.shared_off"), "textures/ui/multiplayer_glyph_color");
    actions.push(["shared"]);
  }
  e.showing = true;
  form.show(p).then((res) => {
    e.showing = false;
    if (campaignStarted() || transitioning) return;
    if (res.canceled) {
      // Busy (loading, chat open) or closed: ask again shortly - a role is required to play.
      const delay = res.cancelationReason === FormCancelationReason.UserBusy ? 20 : 30;
      if (!lobby.get(p.id)?.role) system.runTimeout(() => showSelection(p), delay);
      return;
    }
    const [kind, role] = actions[res.selection] ?? [];
    if (kind === "role") showRoleDetail(p, role);
    else if (kind === "auto") { autoAssign(lobbyPlayers()); maybeBegin(true); }
    else if (kind === "start") { autoAssign(lobbyPlayers().filter((q) => !lobby.get(q.id)?.role)); maybeBegin(true); }
    else if (kind === "shared") {
      try { world.setDynamicProperty("odyssey:shared_roles", !sharedRoles()); } catch { }
      system.runTimeout(() => showSelection(p), 2);
    }
  }).catch(() => { e.showing = false; system.runTimeout(() => showSelection(p), 40); });
}

function showRoleDetail(p, role) {
  const n = lobbyPlayers().length;
  const why = blockReason(p, role, n);
  const R = (k) => ({ translate: `odyssey.role.${role}.${k}` });
  const H = (k) => ({ translate: `odyssey.sel.h.${k}` });
  const body = { rawtext: [
    H("bio"), R("bio"), { text: "\n\n" }, H("importance"), R("importance"), { text: "\n\n" },
    H("abilities"), R("abilities"), { text: "\n\n" }, H("equipment"), R("equipment"), { text: "\n\n" },
    H("duty"), R("duty"), { text: "\n\n" }, H("status"), why ? { translate: why } : { translate: "odyssey.sel.status.free" },
  ] };
  new MessageFormData()
    .title(roleName(role))
    .body(body)
    .button1(why ? msg("odyssey.ui.back") : { rawtext: [{ translate: "odyssey.sel.confirm", with: { rawtext: [{ translate: `odyssey.role.${role}.name` }] } }] })
    .button2(msg("odyssey.ui.back"))
    .show(p).then((res) => {
      if (campaignStarted() || transitioning) return;
      if (!res.canceled && res.selection === 0 && !why) {
        if (blockReason(p, role, lobbyPlayers().length)) { tell(p, "odyssey.sel.taken"); showSelection(p); return; }
        pick(p, role);
      } else {
        showSelection(p);
      }
    }).catch(() => system.runTimeout(() => showSelection(p), 40));
}

function pick(p, role) {
  const e = lobby.get(p.id);
  if (!e) return;
  e.role = role;
  for (const q of lobbyPlayers()) {
    try { q.sendMessage({ rawtext: [{ translate: "odyssey.sel.picked", with: { rawtext: [{ text: p.name }, { translate: `odyssey.role.${role}.name` }] } }] }); } catch { }
    hear(q, "odyssey.athena.chime", undefined, 0.6, 1.2);
  }
  maybeBegin();
}

/** Fill roles for `players` who have none: primaries first (host gets Odysseus), then supporting roles. */
export function autoAssign(players) {
  const n = lobbyPlayers().length || players.length;
  const host = hostId();
  const order = [...players].filter((p) => !lobby.get(p.id)?.role).sort((a, b) => (a.id === host ? -1 : b.id === host ? 1 : 0));
  for (const p of order) {
    // Primary roles first (in order), then the supporting role with the fewest players.
    const open = rolesOffered(n).filter((r) => !blockReason(p, r, n) && (ROLES[r].exclusive ? !holders(r).length : true));
    const role = open.find((r) => ROLES[r].primary)
      ?? open.sort((x, y) => holders(x).length - holders(y).length)[0]
      ?? (rolesOffered(n).includes("companion") ? "companion" : "odysseus");
    lobby.get(p.id).role = role;
    try { p.sendMessage({ rawtext: [{ translate: "odyssey.sel.auto", with: { rawtext: [{ translate: `odyssey.role.${role}.name` }] } }] }); } catch { }
  }
}

function maybeBegin(force = false) {
  if (campaignStarted() || transitioning) return;
  const players = lobbyPlayers();
  if (!players.length) return;
  if (!force && !players.every((p) => lobby.get(p.id)?.role)) return;
  if (force) autoAssign(players);
  // Odysseus must be played by someone (the story is his); if nobody took him, the host is moved onto him.
  if (!players.some((p) => lobby.get(p.id).role === "odysseus")) {
    const h = byId(hostId()) ?? players[0];
    lobby.get(h.id).role = "odysseus";
  }
  beginTransition(players);
}

// ------------------------------------------------------------------ transition + teleport
function beginTransition(players) {
  transitioning = true;
  try { world.setDynamicProperty("odyssey:campaign_started", true); } catch { }
  for (const p of players) {
    try { world.setDynamicProperty("odyssey:host", hostId() ?? p.id); } catch { }
    camFade(p, TIMING.fadeIn, TIMING.fadeHold, TIMING.fadeOut);
    hear(p, "odyssey.world.storm", undefined, 0.5, 0.8);
  }
  // Teleport only once the screen is fully black.
  system.runTimeout(() => {
    for (const p of players) {
      if (!valid(p)) continue;
      const role = lobby.get(p.id)?.role ?? "odysseus";
      setDp(p, "studio:role", role);
      setDp(p, "studio:chapter", currentChapter());
      teleportVerified(p, START_POSITIONS[role], () => equip(p, role));
    }
    ensureSiteArchitecture("ogygia");
    ensureSiteArchitecture("ithaca");
  }, TIMING.teleportAtTick);
  // Start the opening while the screen is still black so its first shot is already framed when the fade lifts.
  system.runTimeout(() => {
    const ps = players.filter(valid);
    for (const p of ps) { camClear(p); setDp(p, "studio:locked", false); }
    playOpening(ps, () => {
      transitioning = false;
      lobby.clear();
      setWorldState(STATE_NORMAL);
      for (const p of ps.filter(valid)) {
        lockInput(p, false);
        tell(p, "odyssey.ch.1.story");
        tell(p, "odyssey.journal.hint");
        setDp(p, "studio:nav_until", now() + 400);
      }
      checkChapter();
    });
  }, TIMING.teleportAtTick + TIMING.verifyDelay * 3);
}

/**
 * Teleport to a configured point and verify it. Retries up to TIMING.maxTeleportTries; if the point is no longer
 * safe ground (map edited, island not built yet), uses the nearest safe spot; last resort is the verified world spawn.
 */
export function teleportVerified(p, pointKey, onArrive, attempt = 1) {
  const pt = POINTS[pointKey] ?? POINTS.ogygia_court;
  let target = { x: pt.x, y: pt.y, z: pt.z };
  if (attempt > 1) {
    const s = standAt(p.dimension, pt.x, pt.z, Math.floor(pt.y) + 8) ?? safeSpotNear(p.dimension, pt.x, pt.z, 10, Math.floor(pt.y) + 8);
    if (s) target = s;
  }
  if (attempt > TIMING.maxTeleportTries) target = POINTS.ogygia_court;
  safe("tp", () => p.teleport(target, { dimension: world.getDimension("minecraft:overworld"), rotation: { x: 0, y: pt.yaw ?? 0 }, keepVelocity: false }));
  system.runTimeout(() => {
    if (!valid(p)) return;
    const ok = flat(p.location, target) < 2.5 && Math.abs(p.location.y - target.y) < 3;
    const ground = standAt(p.dimension, target.x, target.z, Math.floor(target.y) + 3);
    if ((ok && ground) || attempt > TIMING.maxTeleportTries) {
      setDp(p, "studio:checkpoint_point", pointKey);
      onArrive?.();
    } else {
      teleportVerified(p, pointKey, onArrive, attempt + 1);
    }
  }, TIMING.verifyDelay);
}

function equip(p, role) {
  if (dp(p, `studio:kit_${role}`, false)) return;
  setDp(p, `studio:kit_${role}`, true);
  setDp(p, "studio:kit", true);
  setDp(p, "studio:unlock_astrolabe", true);
  for (const [id, n] of START_KITS[role] ?? []) {
    if (id === "studio:odyssey_astrolabe" || id === "studio:driftwood_club") {
      setDp(p, id === "studio:driftwood_club" ? "studio:unlock_driftwood_club" : "studio:unlock_astrolabe", true);
      grantProgressionReward(p, id, n, { uniqueKey: `start_${id}`, role: "both", silent: true });
    } else {
      safe("kit", () => p.getComponent("minecraft:inventory")?.container?.addItem(new ItemStack(id, n)));
    }
  }
}

// ------------------------------------------------------------------ late join / reassignment
function lateJoin(p) {
  if (roleOf(p)) return;    // returning player: keeps role, quests and position
  const n = world.getAllPlayers().length;
  const free = ROLE_ORDER.filter((r) => rolesOffered(Math.max(n, 3)).includes(r) && !blockReason(p, r, Math.max(n, 3)));
  const form = new ActionFormData().title(msg("odyssey.sel.late_title")).body(msg("odyssey.sel.late_body"));
  for (const r of free) form.button({ rawtext: [{ translate: `odyssey.role.${r}.button` }] }, ROLES[r].portrait);
  form.show(p).then((res) => {
    if (res.canceled) { system.runTimeout(() => lateJoin(p), res.cancelationReason === FormCancelationReason.UserBusy ? 20 : 60); return; }
    const role = free[res.selection] ?? "companion";
    setDp(p, "studio:role", role);
    camFade(p, 0.8, 1.5, 1.0);
    system.runTimeout(() => {
      const leader = world.getAllPlayers().find((q) => q.id !== p.id && roleOf(q) === "odysseus") ?? world.getAllPlayers().find((q) => q.id !== p.id);
      const join = currentChapter() === 1 || !leader ? START_POSITIONS[role] : undefined;
      if (join) teleportVerified(p, join, () => equip(p, role));
      else {
        const s = safeSpotNear(leader.dimension, leader.location.x + 2, leader.location.z + 2, 6, Math.floor(leader.location.y) + 4);
        safe("tp", () => p.teleport(s ?? leader.location, { dimension: leader.dimension }));
        equip(p, role);
      }
      try { world.sendMessage({ rawtext: [{ translate: "odyssey.sel.picked", with: { rawtext: [{ text: p.name }, { translate: `odyssey.role.${role}.name` }] } }] }); } catch { }
    }, 18);
  }).catch(() => system.runTimeout(() => lateJoin(p), 60));
}

/** Host control after the start: move a player to another role (exclusive roles are swapped, never duplicated). */
export function openRoleManager(host) {
  if (!isHost(host)) { tell(host, "odyssey.host.only"); return; }
  const ps = world.getAllPlayers().filter(valid);
  const f = new ActionFormData().title(msg("odyssey.host.roles_title")).body(msg("odyssey.host.roles_body"));
  for (const q of ps) f.button({ rawtext: [{ text: `${q.name}\n` }, { translate: `odyssey.role.${roleOf(q) || "unassigned"}.name` }] });
  f.show(host).then((r) => {
    if (r.canceled) return;
    const target = ps[r.selection];
    const g = new ActionFormData().title({ rawtext: [{ text: target.name }] });
    for (const role of ROLE_ORDER) g.button(roleName(role), ROLES[role].portrait);
    g.show(host).then((r2) => {
      if (r2.canceled || !valid(target)) return;
      const role = ROLE_ORDER[r2.selection];
      if (ROLES[role].exclusive && !sharedRoles()) {
        for (const q of holders(role)) if (q.id !== target.id) setDp(q, "studio:role", roleOf(target) || "companion");
      }
      setDp(target, "studio:role", role);
      equip(target, role);
      for (const q of world.getAllPlayers()) {
        try { q.sendMessage({ rawtext: [{ translate: "odyssey.sel.picked", with: { rawtext: [{ text: target.name }, { translate: `odyssey.role.${role}.name` }] } }] }); } catch { }
      }
    }).catch(() => { });
  }).catch(() => { });
}
