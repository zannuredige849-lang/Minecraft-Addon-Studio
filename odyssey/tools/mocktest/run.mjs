// Scenario tests for the campaign scripts against the in-memory mock (mock/@minecraft/*).
// Usage: node run.mjs <scenario>    (run_all.sh runs every scenario in a fresh process)
import * as mc from "@minecraft/server";
import { ui } from "@minecraft/server-ui";
const { advance, join, leave, rejoin, log, world } = mc;
const scenario = process.argv[2];
const warnings = [];
const _warn = console.warn;
console.warn = (...a) => { const m = a.join(" "); if (m.startsWith("[odyssey]")) warnings.push(m); else _warn(...a); };
await import(process.env.SCRIPTS + "/main.js");
mc.overworld().overrides.set("0,64,0", "minecraft:lodestone");     // the map marker journey.js looks for

let failures = 0;
const ok = (cond, what) => { console.log(`${cond ? "  PASS" : "  FAIL"} ${what}`); if (!cond) failures++; };
const btnKey = (b) => b?.t?.rawtext?.[0]?.translate ?? b?.t?.rawtext?.[0]?.text;
const roleOf = (p) => p.getDynamicProperty("studio:role");
const chapter = () => world.getDynamicProperty("odyssey:global_chapter") ?? 1;
const near = (p, x, z, r = 3) => Math.hypot(p.location.x - x, p.location.z - z) <= r;
/** Responder that picks `role` on the selection screen and confirms it on the detail screen. */
const chooser = (role) => (p, f) => {
  if (f.kind === "message") return { selection: 0 };
  const i = f.buttons.findIndex((b) => btnKey(b) === `odyssey.role.${role}.button`);
  return i >= 0 ? { selection: i } : { canceled: true };
};
/** A player who keeps the screen open: the form comes back as "busy" and is re-shown until the responder changes. */
const busy = () => ({ canceled: true, reason: "UserBusy" });
const hostButton = (key) => (p, f) => {
  const i = f.buttons.findIndex((b) => btnKey(b) === key);
  return i >= 0 ? { selection: i } : { canceled: true };
};
const shownTo = (name) => ui.shown.filter(([n]) => n === name).map(([, f]) => f);
const quests = await import(process.env.SCRIPTS + "/world/quests.js");
const pv = await import(process.env.SCRIPTS + "/world/pause_vote.js");
const ev = (p, id) => quests.questEvent(p, id);

async function finishCutscenes() { await advance(420); }

if (scenario === "solo") {
  console.log("Scenario: one player, full campaign");
  ui.responders.set("Hero", chooser("odysseus"));
  const p = join("Hero");
  await advance(5);
  ok(pv.getWorldState() === pv.STATE_MENU, "world is in controlled pause before selection");
  ok(!world.getDynamicProperty("odyssey:campaign_started"), "campaign has not started before selection");
  await advance(45);
  const sel = shownTo("Hero").find((f) => f.kind === "action");
  const roleButtons = sel.buttons.map(btnKey).filter((k) => k.startsWith("odyssey.role."));
  ok(roleButtons.join() === "odyssey.role.odysseus.button,odyssey.role.telemachus.button", "solo screen shows Odysseus and (NPC) Telemachus");
  ok(sel.buttons.some((b) => btnKey(b) === "odyssey.sel.host.auto"), "first player gets host controls");
  ok(sel.buttons.every((b) => !b.icon || b.icon.startsWith("textures/")), "buttons carry portrait icons");
  await advance(40);
  ok(roleOf(p) === "odysseus", "player is Odysseus");
  ok(near(p, 0.5, 3.5), "teleported to Ogygia court (verified start)");
  const fade = log.camera.find(([n, k, o]) => k === "fade" && o?.fadeTime?.holdTime >= 3);
  ok(!!fade, "long black fade covers the teleport");
  const tpTick = log.teleports.findIndex(([n]) => n === "Hero");
  ok(tpTick >= 0, "teleport happened");
  await finishCutscenes();
  ok(pv.getWorldState() === pv.STATE_NORMAL, "gameplay restored after opening cinematic");
  ok(!p.getDynamicProperty("studio:in_cutscene"), "player released from cutscene");
  ok(log.commands.some(([n, c]) => n === "Hero" && c.includes("inputpermission set @s movement enabled")), "input re-enabled");
  const inv = p.getComponent("minecraft:inventory").container.items.filter(Boolean).map((i) => i.typeId);
  ok(inv.includes("minecraft:bread"), "role kit given");
  ok(quests.isDone("t1_mentor") && quests.isDone("t1_sparta"), "NPC Telemachus objectives auto-complete in solo");
  const body = JSON.stringify(quests.journalBody(p));
  ok(body.includes("odyssey.q.o1_calypso") && !body.includes("odyssey.q.t1_mentor"), "Odysseus journal excludes Telemachus objectives");
  ok(body.includes("0 65 5") || body.includes("7 65 5"), "journal shows destination coordinates");
  // play the campaign through its events
  ev(p, "lotus_gifted"); await advance(20);
  p.location = { x: -11.5, y: 65, z: -3.5 }; await advance(25);
  ok(quests.isDone("o1_athena"), "reach-objective completes by proximity");
  ev(p, "find_ship"); await advance(5);
  ok(chapter() === 2, "chapter I -> II after Odysseus finds the galley");
  await finishCutscenes();
  const steps = [["reach:troy_beach", "horse_hidden"], ["cyclops_blinded"], ["site_aeaea"], ["circe_yielded"], ["hades_sacrifice"], ["site_strait"], ["site_thrinacia", "site_ithaca"]];
  for (const [i, s] of steps.entries()) {
    for (const e of s) ev(p, e);
    await advance(5);
    // votes may open on some events; resolve them
    if (pv.getActiveVote()) { pv.castVote(p, 0); await advance(5); }
    await finishCutscenes();
    ok(chapter() === i + 3, `chapter advances to ${i + 3}`);
  }
  ev(p, "talk_eumaeus"); ev(p, "ithaca_blessed"); ev(p, "bow_trial");
  await advance(10);
  ok(world.getDynamicProperty("odyssey:campaign_complete") === true, "campaign completes on the bow trial");
  await finishCutscenes();
  ok(pv.getWorldState() === pv.STATE_NORMAL, "control returned after the finale");
}

if (scenario === "duo") {
  console.log("Scenario: two players, exclusive primary roles, separate starts");
  ui.responders.set("A", busy);          // A's screen stays open while B chooses
  ui.responders.set("B", chooser("odysseus"));
  const a = join("A"); const b = join("B");
  await advance(60);
  ok(roleOf(b) === undefined, "nothing assigned before everyone has chosen");
  ui.responders.set("A", chooser("odysseus"));      // A tries the taken role
  const pvState = pv.getWorldState();
  ok(pvState === pv.STATE_MENU, "still paused while a player is choosing");
  // re-open A's screen
  const sel = await import(process.env.SCRIPTS + "/world/selection.js");
  const lobbyForm = () => shownTo("A").filter((f) => f.kind === "action").at(-1);
  // A's form never resolved; simulate it being closed and re-shown
  ui.responders.set("A", chooser("telemachus"));
  sel.showSelection(a); await advance(5);
  sel.showSelection(a); await advance(5);
  const last = shownTo("A").filter((f) => f.kind === "action").at(-1);
  const odyBtn = last?.buttons.find((b) => btnKey(b) === "odyssey.role.odysseus.button");
  ok(JSON.stringify(odyBtn?.t).includes("odyssey.sel.status.taken"), "Odysseus shown as taken by B on A's screen");
  await advance(40);
  ok(roleOf(a) === "telemachus" && roleOf(b) === "odysseus", "A = Telemachus, B = Odysseus");
  ok(near(a, -419.5, -199.5) && near(b, 0.5, 3.5), "each teleported to their own start (Ithaca / Ogygia)");
  await finishCutscenes();
  const ja = JSON.stringify(quests.journalBody(a)), jb = JSON.stringify(quests.journalBody(b));
  ok(ja.includes("t1_mentor") && !ja.includes("o1_calypso"), "Telemachus journal: own objectives only");
  ok(jb.includes("o1_calypso") && !jb.includes("t1_mentor"), "Odysseus journal: own objectives only");
  ok(!quests.isDone("t1_mentor"), "with a Telemachus player, his objectives are not auto-completed");
  ev(b, "talk_mentor"); ok(!quests.isDone("t1_mentor"), "Odysseus cannot complete Telemachus's objective");
  ev(a, "talk_mentor"); ok(quests.isDone("t1_mentor"), "Telemachus completes his objective");
  ev(b, "lotus_gifted"); ev(b, "find_ship"); b.location = { x: -11.5, y: 65, z: -3.5 }; await advance(25);
  ok(chapter() === 1, "chapter I waits for Telemachus to reach Sparta");
  ev(a, "site_sparta"); await advance(5);
  ok(chapter() === 2, "chapter II begins when both tracks are done");
  await finishCutscenes();
  ok(near(a, 1.5, -18.5, 4), "Telemachus regroups with Odysseus's party at Ogygia harbour for the voyage");
}

if (scenario === "four") {
  console.log("Scenario: four players, host auto-assign, primaries reserved");
  for (const n of ["H", "P2", "P3", "P4"]) ui.responders.set(n, busy);
  const ps = ["H", "P2", "P3", "P4"].map(join);
  await advance(45);
  ui.responders.set("P3", chooser("companion"));
  const sel = await import(process.env.SCRIPTS + "/world/selection.js");
  sel.showSelection(ps[2]); await advance(5);
  ok(roleOf(ps[2]) === undefined, "nothing saved before start");
  ui.responders.set("H", hostButton("odyssey.sel.host.auto"));
  sel.showSelection(ps[0]); await advance(60);
  const roles = ps.map(roleOf);
  console.log("   roles:", roles.join(", "));
  ok(roles.includes("odysseus") && roles.includes("telemachus"), "both primary roles filled");
  ok(roles[0] === "odysseus", "host gets Odysseus when undecided");
  ok(roles.filter((r) => r === "odysseus").length === 1 && roles.filter((r) => r === "telemachus").length === 1, "no duplicate exclusive roles");
  ok(roles.every(Boolean), "every player has a role");
  await finishCutscenes();
  ok(pv.getWorldState() === pv.STATE_NORMAL, "gameplay resumed");
}

if (scenario === "afk") {
  console.log("Scenario: a player never answers -> auto-assigned after the timeout (no permanent lock)");
  ui.responders.set("A", chooser("odysseus"));
  ui.responders.set("B", () => null);
  const a = join("A"); const b = join("B");
  await advance(200);
  ok(!world.getDynamicProperty("odyssey:campaign_started"), "waits for the second player at first");
  await advance(2500);
  ok(roleOf(b) === "telemachus", "AFK player auto-assigned Telemachus after the timeout");
  ok(world.getDynamicProperty("odyssey:campaign_started") === true, "campaign started");
}

if (scenario === "disconnect") {
  console.log("Scenario: disconnect during the opening cinematic, then rejoin");
  ui.responders.set("A", chooser("odysseus"));
  ui.responders.set("B", chooser("telemachus"));
  const a = join("A"); const b = join("B");
  await advance(100);
  ok(b.getDynamicProperty("studio:in_cutscene") === true, "B is in the opening cinematic");
  leave(b);
  await advance(400);
  ok(pv.getWorldState() === pv.STATE_NORMAL, "the remaining player's game resumes (no lock)");
  log.camera.length = 0;
  rejoin(b); await advance(5);
  ok(log.camera.some(([n, k]) => n === "B" && k === "clear"), "rejoining player's camera is cleared");
  ok(!b.getDynamicProperty("studio:in_cutscene"), "rejoining player is released");
  ok(roleOf(b) === "telemachus", "role kept after reconnect");
  // leave during selection
}

if (scenario === "leave_lobby") {
  console.log("Scenario: a player leaves during selection");
  ui.responders.set("A", chooser("odysseus"));
  ui.responders.set("B", () => null);
  const a = join("A"); const b = join("B");
  await advance(60);
  leave(b); await advance(60);
  ok(world.getDynamicProperty("odyssey:campaign_started") === true, "campaign starts for the remaining player");
  ok(roleOf(a) === "odysseus", "remaining player keeps Odysseus");
}

if (scenario === "late") {
  console.log("Scenario: late joiner after the start");
  ui.responders.set("A", chooser("odysseus"));
  const a = join("A"); await advance(500);
  ui.responders.set("L", (p, f) => ({ selection: 0 }));
  const l = join("L"); await advance(60);
  ok(!!roleOf(l), `late joiner got a role (${roleOf(l)})`);
  console.log("   state:", pv.getWorldState(), "vote:", !!pv.getActiveVote());
  ok(!pv.isWorldPaused(), "nobody else was paused (a late joiner's own arrival scene is not a pause)");
}

if (scenario === "guide") {
  console.log("Scenario: travel guide appears for a lost player, points the way, leaves");
  ui.responders.set("A", chooser("odysseus"));
  const a = join("A"); await advance(500);
  a.location = { x: 200.5, y: 65, z: 200.5 };              // far from Calypso (first objective), wandering
  await advance(60);
  const before = mc.overworld().getEntities({ type: "studio:odyssey_person", tags: ["odyssey_guide"] }).length;
  ok(before === 0, "no guide while the player is still making progress");
  await advance(1900);
  const g = mc.overworld().getEntities({ type: "studio:odyssey_person", tags: ["odyssey_guide"] });
  ok(g.length === 1, "exactly one guide appears after ~90 s without progress");
  const said = a.inbox.map((m) => JSON.stringify(m)).filter((m) => m.includes("odyssey.guide."));
  ok(said.some((m) => m.includes("odyssey.guide.dir") && m.includes("odyssey.dest.ogygia_calypso")), "guide gives directions to the player's own objective");
  ok(said.some((m) => /7 65 5/.test(m)), "directions include coordinates");
  await advance(1400);
  ok(mc.overworld().getEntities({ type: "studio:odyssey_person", tags: ["odyssey_guide"] }).length === 0, "guide leaves after its lifetime");
  await advance(400);
  ok(mc.overworld().getEntities({ type: "studio:odyssey_person", tags: ["odyssey_guide"] }).length === 0, "no immediate repeat (cooldown)");
}

if (scenario === "softlock") {
  console.log("Scenario: deeds done by the wrong role, and the Odysseus player leaving");
  ui.responders.set("A", chooser("odysseus")); ui.responders.set("B", chooser("telemachus"));
  const a = join("A"); const b = join("B"); await advance(500);
  quests.setGlobalChapter(3); await finishCutscenes();
  ev(b, "cyclops_blinded"); await advance(5);
  ok(quests.isDone("o3_stake"), "Telemachus blinding the Cyclops still completes the (irreversible) deed");
  ok(chapter() === 4, "chapter III ends");
  quests.setGlobalChapter(9); await finishCutscenes();
  leave(a); await advance(5);
  ev(b, "talk_eumaeus"); ok(quests.isDone("o9_eumaeus"), "with Odysseus gone, Telemachus can finish Odysseus's step");
  ev(b, "ithaca_blessed"); await advance(120);
  ok(quests.isDone("o9_bow"), "bow trial falls back to the blessing when no Odysseus is online");
  ok(world.getDynamicProperty("odyssey:campaign_complete") === true, "campaign can still be completed");
}

if (scenario === "mechanics") {
  console.log("Scenario: every island, creature loop, hit/hurt/death, interaction and item use");
  ui.responders.set("A", chooser("odysseus"));
  const a = join("A"); await advance(500);
  const { SITES } = await import(process.env.SCRIPTS + "/data/sites.js");
  const dim = mc.overworld();
  for (const site of SITES) {
    a.location = { x: site.x + 2.5, y: 65, z: site.z + 2.5 };
    await advance(200);
    if (pv.getActiveVote()) { pv.castVote(a, 0); await advance(5); }
    await advance(300);
  }
  const types = [...new Set(dim.entities.map((e) => e.typeId))].sort();
  console.log("   spawned:", types.join(" "));
  ok(["studio:cyclops", "studio:scylla", "studio:siren", "studio:circe", "studio:calypso", "studio:sun_cattle", "studio:laestrygonian"].every((t) => types.includes(t)), "every site creature spawned");
  // combat and interactions, with the player standing next to each creature
  for (const e of [...dim.entities]) {
    if (!e.isValid() || e.typeId === "minecraft:player") continue;
    a.location = { x: e.location.x + 1.5, y: e.location.y, z: e.location.z + 1.5 };
    mc.fire("entityHitEntity", { damagingEntity: a, hitEntity: e });
    mc.fire("entityHurt", { hurtEntity: e, damageSource: { damagingEntity: a, cause: "entityAttack" }, damage: 4 });
    mc.fire("entityHitEntity", { damagingEntity: e, hitEntity: a });
    for (const id of ["studio:offer_lotus", "studio:embrace", "studio:bless", "studio:talk", "studio:ship_interact", "studio:stew", "studio:counsel", "studio:seize", "studio:hide", "studio:serve"])
      mc.fire("dataDrivenEntityTrigger", { entity: e, eventId: id });
    await advance(40);
    if (pv.getActiveVote()) { pv.castVote(a, 0); await advance(5); }
  }
  await advance(200);
  // every custom item use
  const items = ["beeswax", "circe_stew", "lotus_flower", "moly_herb", "odyssey_astrolabe", "ship_helm_horn", "ship_repair_kit", "copper_hoplon", "tiresias_staff", "apollo_sun_talisman", "royal_bow_of_odysseus", "spear_of_telemachus"];
  ui.responders.set("A", () => ({ canceled: true }));
  for (const it of items) { mc.fire("itemCompleteUse", { source: a, itemStack: new mc.ItemStack("studio:" + it, 1) }); await advance(10); }
  // deaths
  for (const e of [...dim.entities]) {
    if (!e.isValid()) continue;
    mc.fire("entityDie", { deadEntity: e, damageSource: { damagingEntity: a, cause: "entityAttack" } });
    e.remove();
  }
  await advance(400);
  ok(true, "mechanics run completed");
}

ok(warnings.length === 0, `no caught script warnings (${warnings.length})`);
if (warnings.length) console.log([...new Set(warnings)].slice(0, 25).join("\n"));
const errs = log.errors.filter((e) => !e.includes("no move"));
ok(errs.length === 0, `no script errors (${errs.length})`);
if (errs.length) console.log(errs.slice(0, 5).join("\n"));
const warns = [];
process.exitCode = failures ? 1 : 0;
