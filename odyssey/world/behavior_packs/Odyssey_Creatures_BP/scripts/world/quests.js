// Quest progress, individual journals and subtle navigation.
//
// Progress is stored once for the party (world dynamic property), keyed by objective id. Objectives are role-scoped,
// so each player's journal lists only the objectives of the character they play: Odysseus never sees Telemachus's
// list and vice versa. Exclusive roles make this exact; supporting roles share their objectives.
import { world, system } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { CHAPTERS, FINAL_CHAPTER, chapterById, objectiveFor } from "../data/campaign.js";
import { POINTS } from "../data/config.js";
import { dp, flat, heldItem, now, safe, setDp, valid } from "../lib/util.js";
import { hear, msg, tell, title } from "../lib/fx.js";

const KEY_DONE = "odyssey:q_done";
const KEY_CHAPTER = "odyssey:global_chapter";
const listeners = [];   // (event, payload) => void, registered by the campaign / cinematics layer

let doneCache;
function doneSet() {
  if (!doneCache) {
    try { doneCache = new Set(JSON.parse(world.getDynamicProperty(KEY_DONE) ?? "[]")); } catch { doneCache = new Set(); }
  }
  return doneCache;
}
function saveDone() { try { world.setDynamicProperty(KEY_DONE, JSON.stringify([...doneSet()])); } catch { } }

export const onQuestSignal = (fn) => listeners.push(fn);
const signal = (ev, payload) => { for (const fn of listeners) safe(`quest.${ev}`, () => fn(ev, payload)); };

export function currentChapter() {
  try { return world.getDynamicProperty(KEY_CHAPTER) ?? 1; } catch { return 1; }
}
export const roleOf = (p) => dp(p, "studio:role", "");
export const isDone = (id) => doneSet().has(id);
export const playersWithRole = (role) => world.getAllPlayers().filter((p) => valid(p) && roleOf(p) === role);

/** The objectives a player sees for a chapter, in journal order. */
export function objectivesFor(p, chapterId = currentChapter()) {
  const role = roleOf(p);
  return chapterById(chapterId).objectives.filter((o) => objectiveFor(o, role));
}
/** First unfinished non-optional objective of this player (their "main objective"), else first optional. */
export function mainObjective(p) {
  const list = objectivesFor(p);
  return list.find((o) => !isDone(o.id) && !o.optional) ?? list.find((o) => !isDone(o.id));
}

function announce(o) {
  for (const p of world.getAllPlayers()) {
    if (!valid(p) || !objectiveFor(o, roleOf(p))) continue;
    try { p.sendMessage({ rawtext: [{ translate: "odyssey.q.complete", with: { rawtext: [{ translate: `odyssey.q.${o.id}` }] } }] }); } catch { }
    hear(p, "odyssey.athena.chime", undefined, 0.7, 1.25);
    setDp(p, "studio:nav_until", now() + 200);      // show the next destination briefly
  }
}

export function markDone(id, { silent = false } = {}) {
  if (isDone(id)) return false;
  doneSet().add(id); saveDone();
  const o = CHAPTERS.flatMap((c) => c.objectives).find((x) => x.id === id);
  if (o && !silent) announce(o);
  return true;
}

/**
 * A story event happened. `p` is the player who caused it, or null for party-wide events (votes).
 * Completes every matching objective of the current or an earlier chapter that belongs to that player's role.
 */
export function questEvent(p, eventId) {
  const ch = currentChapter();
  const role = p ? roleOf(p) : "";
  let changed = false;
  for (const c of CHAPTERS) {
    if (c.id > ch) break;
    for (const o of c.objectives) {
      if (o.done !== eventId || isDone(o.id)) continue;
      if (p && o.scope !== "shared" && !objectiveFor(o, role) && !o.anyone && !noHolderOnline(o.scope)) continue;
      changed = markDone(o.id) || changed;
    }
  }
  if (changed) checkChapter();
  return changed;
}

/** Is nobody who could do this objective online? (then anyone may do it, so a player leaving never blocks the story) */
export function noHolderOnline(scope) {
  if (scope === "shared") return false;
  const roles = scope === "support" ? ["companion", "eumaeus"] : [scope];
  return !world.getAllPlayers().some((p) => valid(p) && roles.includes(roleOf(p)));
}

/** NPC stand-ins (solo Telemachus) finish their objectives automatically, with a line of narration. */
function autoCompleteNpcObjectives(c) {
  for (const o of c.objectives) {
    if (!o.npcAuto || isDone(o.id) || o.scope === "shared") continue;
    if (playersWithRole(o.scope).length) continue;
    markDone(o.id, { silent: true });
    for (const p of world.getAllPlayers()) tell(p, `odyssey.npc_auto.${o.id}`);
  }
}

export function checkChapter() {
  const ch = currentChapter();
  const c = chapterById(ch);
  autoCompleteNpcObjectives(c);
  for (const o of c.objectives) {
    if (o.fallback && !isDone(o.id) && isDone(o.fallback) && noHolderOnline(o.scope)) markDone(o.id);
  }
  if (!c.complete.every((id) => isDone(id))) return false;
  if (ch >= FINAL_CHAPTER) {
    if (!world.getDynamicProperty("odyssey:campaign_complete")) {
      world.setDynamicProperty("odyssey:campaign_complete", true);
      signal("campaign_complete", { chapter: ch });
    }
    return true;
  }
  setGlobalChapter(ch + 1);
  return true;
}

export function setGlobalChapter(next) {
  const prev = currentChapter();
  if (next <= prev) return;
  try { world.setDynamicProperty(KEY_CHAPTER, next); } catch { }
  for (const p of world.getAllPlayers()) setDp(p, "studio:chapter", next);
  signal("chapter_end", { chapter: prev, next });
  for (const p of world.getAllPlayers()) {
    if (!valid(p)) continue;
    title(p, chapterById(next).title, chapterById(next).story);
    tell(p, chapterById(next).story);
    setDp(p, "studio:nav_until", now() + 300);
  }
  autoCompleteNpcObjectives(chapterById(next));
  signal("chapter_start", { chapter: next, prev });
}

// ------------------------------------------------------------------ proximity objectives + navigation HUD
const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
export function compass(from, to) {
  // Minecraft: north is -Z, east is +X
  const ang = Math.atan2(to.x - from.x, -(to.z - from.z));
  return COMPASS[((Math.round(ang / (Math.PI / 4)) % 8) + 8) % 8];
}

let tickCount = 0;
export function tickQuests() {
  // Every ~5 s re-check the chapter, so fallbacks also apply when a player leaves (no event fires then).
  if (++tickCount % 5 === 0 && world.getDynamicProperty("odyssey:campaign_started") === true) safe("quest.check", checkChapter);
  const ch = currentChapter();
  for (const p of world.getAllPlayers()) {
    if (!valid(p) || !roleOf(p)) continue;
    safe("quest.tick", () => {
      for (const o of objectivesFor(p, ch)) {
        if (isDone(o.id) || !o.done.startsWith("reach:")) continue;
        const pt = POINTS[o.done.slice(6)];
        if (pt && Math.abs(p.location.y - pt.y) < 12 && flat(p.location, pt) <= 5) questEvent(p, o.done);
      }
      showNavigation(p);
    });
  }
}

function showNavigation(p) {
  if (!dp(p, "studio:nav_enabled", true) || dp(p, "studio:in_cutscene", false)) return;
  const holding = heldItem(p) === "studio:odyssey_astrolabe";
  if (!holding && now() > dp(p, "studio:nav_until", 0)) return;
  const o = mainObjective(p);
  const pt = o?.dest && POINTS[o.dest];
  if (!pt) return;
  const d = Math.round(flat(p.location, pt));
  if (d < 6) return;
  try {
    p.onScreenDisplay.setActionBar({ rawtext: [{ translate: "odyssey.nav.line", with: { rawtext: [
      { translate: pt.label }, { text: String(d) }, { text: compass(p.location, pt) },
      { text: `${Math.floor(pt.x)} ${Math.floor(pt.y)} ${Math.floor(pt.z)}` }] } }] });
  } catch { }
}

// ------------------------------------------------------------------ the journal
const mark = (o) => (isDone(o.id) ? "§a✔ §7" : (o.optional ? "§8◦ §7" : "§e• §f"));

export function journalBody(p) {
  const ch = currentChapter();
  const c = chapterById(ch);
  const role = roleOf(p) || "unassigned";
  const mine = objectivesFor(p, ch);
  const lines = [];
  const T = (key, ...w) => lines.push(w.length ? { translate: key, with: { rawtext: w } } : { translate: key }, { text: "\n" });
  T("odyssey.journal.character", { rawtext: [{ translate: `odyssey.role.${role}.name` }] });
  T("odyssey.journal.role", { rawtext: [{ translate: `odyssey.role.${role}.duty` }] });
  T("odyssey.journal.chapter", { rawtext: [{ text: String(ch) }] }, { rawtext: [{ translate: c.title }] });
  lines.push({ text: "\n" });
  const main = mainObjective(p);
  if (main) {
    T("odyssey.journal.main", { rawtext: [{ translate: `odyssey.q.${main.id}` }] });
    const pt = main.dest && POINTS[main.dest];
    if (pt) {
      T("odyssey.journal.dest", { rawtext: [{ translate: pt.label }] },
        { rawtext: [{ text: `${Math.floor(pt.x)} ${Math.floor(pt.y)} ${Math.floor(pt.z)}` }] },
        { rawtext: [{ text: String(Math.round(flat(p.location, pt))) }] });
    }
    if (main.items?.length) {
      T("odyssey.journal.items", { rawtext: main.items.flatMap((id, i) => [...(i ? [{ text: ", " }] : []), { translate: `item.${id}.name` }]) });
    }
  } else {
    T("odyssey.journal.none");
  }
  const section = (key, list) => {
    if (!list.length) return;
    lines.push({ text: "\n" }); T(key);
    for (const o of list) lines.push({ text: mark(o) }, { translate: `odyssey.q.${o.id}` }, { text: "\n" });
  };
  section("odyssey.journal.personal", mine.filter((o) => o.scope !== "shared" && !o.optional));
  section("odyssey.journal.shared", mine.filter((o) => o.scope === "shared" && !o.optional));
  section("odyssey.journal.optional", mine.filter((o) => o.optional));
  const done = CHAPTERS.filter((x) => x.id < ch).flatMap((x) => x.objectives.filter((o) => objectiveFor(o, role) && isDone(o.id)));
  if (done.length) {
    lines.push({ text: "\n" }); T("odyssey.journal.completed", { rawtext: [{ text: String(done.length) }] });
  }
  return { rawtext: lines };
}

export function openJournal(p) {
  const nav = dp(p, "studio:nav_enabled", true);
  const form = new ActionFormData()
    .title(msg("odyssey.journal.title"))
    .body(journalBody(p))
    .button(msg(nav ? "odyssey.journal.nav_off" : "odyssey.journal.nav_on"), "textures/items/compass_item")
    .button(msg("odyssey.ui.close"));
  form.show(p).then((r) => {
    if (r.canceled) return;
    if (r.selection === 0) {
      setDp(p, "studio:nav_enabled", !nav);
      tell(p, nav ? "odyssey.nav.off" : "odyssey.nav.on");
    }
  }).catch(() => { });
}

/** Reset quest progress (used only by the host "restart campaign" control). */
export function resetQuests() {
  doneCache = new Set(); saveDone();
  try { world.setDynamicProperty(KEY_CHAPTER, 1); world.setDynamicProperty("odyssey:campaign_complete", false); } catch { }
}
