// Mechanics tests for the add-on's script against a strict mock of @minecraft/server.
//   node --import ./tools/odyssey/jstest/register.mjs tools/odyssey/jstest/test.mjs
import { spawn, fire, runTicks, setTime, setBlock, ItemStack, all, clearAll, log, sounds, world } from "@minecraft/server";
import { MOVES, PATHS } from "../../../BP/scripts/data/moves.js";
await import("../../../BP/scripts/main.js");

let failed = 0, count = 0;
const ok = (c, m) => { count++; if (!c) { failed++; console.error("FAIL:", m); } else console.log("ok  ", m); };
const near = (a, b, tol = 0.6) => Math.abs(a - b) < tol;
const player = (x, z, name = "Odysseus", y = 64) => { const p = spawn("minecraft:player", { x, y, z }); p.name = name; return p; };
const key = (m) => (typeof m === "string" ? m : (m.bar ?? m).rawtext?.[0]?.translate);
const said = (p, k) => p.messages.some((m) => key(m) === k);
const cmds = (re) => log.filter((l) => re.test(l));
const reset = () => { clearAll(); log.length = 0; sounds.length = 0; setTime(6000); Math.random = () => 0.9; };
const hit = (a, v) => fire("entityHitEntity", { damagingEntity: a, hitEntity: v });
const hurtBy = (v, a, d = 2) => fire("entityHurt", { hurtEntity: v, damage: d, damageSource: { damagingEntity: a } });
const handAt = (cy, t, label = "hand", move = "cyclops.devour") => {          // where the path says the hand is at tick t
  const p = PATHS[move][label], x = Math.min(p.length - 1, t / 2), i = Math.floor(x), k = x - i, b = p[Math.min(p.length - 1, i + 1)];
  const lerp = (n) => p[i][n] + (b[n] - p[i][n]) * k;
  return { x: cy.location.x - lerp(2), y: cy.location.y + lerp(1), z: cy.location.z + lerp(0) };     // the cyclops faces +z
};

// ================================================================ the move runner and the data
reset();
{
  const cy = spawn("studio:cyclops", { x: 0, y: 64, z: 0 });
  ok(Object.keys(MOVES).every((e) => {
    const def = spawn("studio:" + e === "studio:boulder" ? "studio:boulder" : "studio:" + e, { x: 500, y: 64, z: 500 });
    const values = def.def.description.properties["studio:anim"].values;
    return Object.keys(MOVES[e]).every((m) => values.includes(m));
  }), "every move of every creature is a value of that creature's studio:anim property");
  ok(cy.props["studio:anim"] === "none", "creatures start with no move playing");
}

// ================================================================ Polyphemus
reset();
{
  const cy = spawn("studio:cyclops", { x: 0, y: 64, z: 0 });
  const P = player(0, 5);
  runTicks(10);
  const flock = all().filter((e) => e.hasTag("studio:flock"));
  ok(flock.length === 6 && flock.every((s) => s.dp["studio:shepherd"] === cy.id), "Polyphemus keeps a flock of 6 sheep");
  ok(cy.props["studio:anim"] === "devour", "a man within reach is devoured");
  const t0 = 10;
  runTicks(MOVES.cyclops.devour.grab + 6);
  let h = handAt(cy, MOVES.cyclops.devour.grab + 6);
  ok(near(P.location.y, h.y, 0.8) && near(P.location.z, h.z, 0.8), "he is swept up to the hand during the grab");
  runTicks(MOVES.cyclops.devour.bite[0] - (MOVES.cyclops.devour.grab + 6) + 3);
  h = handAt(cy, MOVES.cyclops.devour.bite[0] + 3);
  const mouth = { y: cy.location.y + PATHS["cyclops.devour"].mouth[Math.round((MOVES.cyclops.devour.bite[0] + 3) / 2)][1] };
  ok(near(P.location.y, mouth.y, 1.0), "at the first bite the man is at Polyphemus's mouth, " + P.location.y.toFixed(1));
  ok(P.health === 13, "the first bite takes 7");
  runTicks(MOVES.cyclops.devour.len - MOVES.cyclops.devour.bite[0] - 3 + 2);
  ok(P.health === 6 && cy.props["studio:anim"] === "none", "two bites in all, then the move is over");
  ok(P.hasEffect("slow_falling") && P.vel.y > 0, "he is tossed aside and set down gently");
  ok(sounds.length === 0 && cmds(/playsound/).length === 0, "the bite sounds belong to the animation, not the script");
}
reset();
{
  const cy = spawn("studio:cyclops", { x: 0, y: 64, z: 0 });
  const P = player(0, 2);
  runTicks(10);
  ok(cy.props["studio:anim"] === "stomp", "a man underfoot is stomped");
  runTicks(MOVES.cyclops.stomp.hit + 2);
  ok(P.health === 6 && P.vel.y > 0.5, "the foot comes down: 14 damage and a shove up");
}
reset();
{
  Math.random = () => 0.1;
  const cy = spawn("studio:cyclops", { x: 0, y: 64, z: 0 });
  const P = player(0, 5);
  runTicks(10);
  ok(cy.props["studio:anim"] === "kick", "a man at arm's length ahead may be kicked");
  runTicks(MOVES.cyclops.kick.hit + 2);
  ok(P.health === 4 && Math.hypot(P.vel.x, P.vel.z) > 2, "the kick sends him flying (16 damage)");
}
reset();
{
  const cy = spawn("studio:cyclops", { x: 0, y: 64, z: 0 });
  const P = player(0, 5);
  hit(cy, P);
  ok(cy.props["studio:anim"] === "devour", "a melee hit also starts the devour");
  const q = player(40, 40, "Elpenor");
  ok(cy.props["studio:anim"] === "devour" && !q.dp["studio:held"], "another man far away is left alone");
}
// sleep, wake, the burning stake
reset();
{
  const cy = spawn("studio:cyclops", { x: 0, y: 64, z: 0 });
  cy.dp["studio:cd_tend"] = 1e9;                       // (no stroking the flock in this test)
  setTime(18000); cy.dp["studio:last_combat"] = -9999;
  runTicks(10);
  ok(cy.props["studio:state"] === "asleep", "he falls asleep at night");
  setTime(6000); runTicks(10);
  ok(cy.props["studio:anim"] === "wake" && cy.props["studio:state"] === "awake", "he wakes at daybreak with the wake move");
  runTicks(MOVES.cyclops.wake.len + 2);
  ok(cy.events.includes("studio:hunt") && cy.props["studio:anim"] === "none", "and hunts again once he is up");
  const P = player(0, 30);
  setTime(18000); cy.dp["studio:last_combat"] = -9999; runTicks(10);
  hurtBy(cy, P);
  ok(cy.props["studio:state"] === "awake" && cy.props["studio:blind"] === false && cy.props["studio:anim"] === "wake", "an ordinary blow wakes him");
  runTicks(MOVES.cyclops.wake.len + 2);
  setTime(18000); cy.dp["studio:last_combat"] = -9999; runTicks(10);
  ok(cy.props["studio:state"] === "asleep", "asleep again");
  P.held = "studio:burning_stake";
  hurtBy(cy, P, 6);
  ok(cy.props["studio:blind"] === true && cy.props["studio:anim"] === "cry", "the burning stake blinds him and he cries out");
  runTicks(20);
  ok(said(P, "odyssey.cy.cry") && said(P, "odyssey.cy.blind_hint"), "the cry to Poseidon is spoken, and the player is told he is blind");
  ok(cmds(/playsound odyssey\.cyclops\.pain_roar/).length === 1 && cmds(/stake_pierce/).length === 1, "the stake and the roar are heard");
  runTicks(70);
  ok(cmds(/weather thunder/).length === 1 && cmds(/odyssey\.world\.storm/).length === 1, "Poseidon answers with a storm");
}
// blind: the flock hides men, rocks miss the boat
reset();
{
  const cy = spawn("studio:cyclops", { x: 0, y: 64, z: 0 });
  cy.triggerEvent("studio:blinded");
  runTicks(10);
  const flock = all().filter((e) => e.hasTag("studio:flock"));
  const P = player(flock[0].location.x, flock[0].location.z + 1);
  const Q = player(0, 6, "Open");
  runTicks(10);
  ok(P.hasTag("studio:in_flock") && !Q.hasTag("studio:in_flock"), "a man among the sheep is hidden, one in the open is not");
  ok(P.health === 20 && cy.props["studio:anim"] !== "none", "blind, he passes over the hidden man and goes for the other");
}
reset();
{
  const cy = spawn("studio:cyclops", { x: 0, y: 64, z: 0 });
  cy.triggerEvent("studio:blinded");
  const boat = spawn("minecraft:boat", { x: 30, y: 63, z: 10 });
  const R = player(30, 10, "Rower"); R.ridingEntity = boat;
  runTicks(10);
  ok(cy.props["studio:anim"] === "throw", "blind, he throws a rock at a boat he hears");
  runTicks(MOVES.cyclops.throw.pick + 2);
  const rock = all().find((e) => e.typeId === "studio:boulder");
  ok(!!rock, "he picks up a rock");
  const h = handAt(cy, MOVES.cyclops.throw.pick + 1, "hand", "cyclops.throw");
  runTicks(MOVES.cyclops.throw.release - MOVES.cyclops.throw.pick + 1);
  ok(cmds(/odyssey\.boulder\.whoosh/).length === 1, "the rock whistles through the air");
  runTicks(80);
  ok(cmds(/odyssey\.boulder\.impact/).length === 1 && boat.alive && R.health === 20, "it lands in the sea and misses the boat, as in the film");
  ok(!all().some((e) => e.typeId === "studio:boulder"), "the rock is gone");
}
reset();
{
  const cy = spawn("studio:cyclops", { x: 0, y: 64, z: 0 });
  runTicks(10);
  const sheep = all().find((e) => e.hasTag("studio:flock"));
  sheep.teleport({ x: 3, y: 64, z: 3 });
  runTicks(10);
  ok(cy.props["studio:anim"] === "tend" && !!sheep, "calm, he strokes his flock");
  runTicks(MOVES.cyclops.tend.stroke + 2);
  ok(sheep.hasEffect("regeneration"), "and the sheep are soothed");
}

// ================================================================ Laestrygonians
const giantTest = (weapon, setup, check, name) => {
  reset();
  const g = spawn("studio:laestrygonian", { x: 0, y: 64, z: 0 });
  g.props["studio:weapon"] = weapon;
  const P = player(0, 3.5);
  setup?.(g, P);
  runTicks(10);
  check(g, P, name);
};
giantTest(0, null, (g, P, n) => {
  ok(g.props["studio:anim"] === "slash", "a sword giant slashes");
  runTicks(MOVES.laestrygonian.slash.hit + 2);
  ok(P.health === 10 && Math.hypot(P.vel.x, P.vel.z) > 1, "the sweep hits for 10 and throws him aside");
}, "slash");
giantTest(1, null, (g, P) => {
  ok(g.props["studio:anim"] === "impale", "a glaive giant stabs");
  runTicks(MOVES.laestrygonian.impale.hit + 3);
  const tip = PATHS["laestrygonian.impale"].point;
  ok(P.health === 8 && P.location.y > 65, "the victim is lifted on the glaive: " + P.location.y.toFixed(1));
  runTicks(MOVES.laestrygonian.impale.fling - MOVES.laestrygonian.impale.hit + 2);
  ok(P.vel.y > 1 && Math.hypot(P.vel.x, P.vel.z) > 2, "and flung into the trees");
  ok(said(P, "odyssey.lae.impale"), "he is told what happened");
}, "impale");
giantTest(2, (g) => { spawn("minecraft:boat", { x: 0, y: 63, z: 5.4 }); }, (g, P) => {
  ok(g.props["studio:anim"] === "crush", "a mace giant slams the ground");
  runTicks(MOVES.laestrygonian.crush.hit + 2);
  ok(P.health === 4 && P.vel.y > 0.5, "the slam hits for 16 and shakes him up");
  ok(!all().some((e) => e.typeId === "minecraft:boat"), "and crushes the boat beside him");
}, "crush");
giantTest(3, null, (g, P) => {
  ok(g.props["studio:anim"] === "cleave", "a curved blade cleaves twice");
  runTicks(MOVES.laestrygonian.cleave.hit[1] + 2);
  ok(P.health === 4, "two sweeps of 8");
}, "cleave");
reset();
{
  const g = spawn("studio:laestrygonian", { x: 0, y: 64, z: 0 });
  const boat = spawn("minecraft:boat", { x: 0, y: 63, z: 4 });
  const R = player(0, 4, "Sailor"); R.mode = "creative";
  runTicks(10);
  ok(g.props["studio:anim"] === "smash", "a giant chops a ship to pieces");
  runTicks(MOVES.laestrygonian.smash.hit + 2);
  ok(!boat.alive, "the boat is gone");
}
reset();
{
  const a = spawn("studio:laestrygonian", { x: 0, y: 64, z: 0 }), b = spawn("studio:laestrygonian", { x: 30, y: 64, z: 0 });
  const P = player(60, 60);
  hurtBy(a, P);
  ok(a.props["studio:anim"] === "none" && b.dp["studio:alarmed"] === true && cmds(/laestrygonian\.war_cry/).length === 1, "hurting one alarms the group, who answer with a war cry");
}
reset();
{
  const c = spawn("studio:laestrygonian_child", { x: 0, y: 64, z: 0 });
  const P = player(0, 4);
  runTicks(10);
  ok(all().filter((e) => e.typeId === "studio:laestrygonian").length === 3, "the child's people are near");
  ok(c.props["studio:anim"] === "laugh" && said(P, "odyssey.lae.child_laugh"), "asked for hospitality, the child laughs");
  runTicks(65);
  ok(c.props["studio:anim"] === "scream" && said(P, "odyssey.lae.child_scream"), "asked again, the child screams");
  runTicks(MOVES.laestrygonian_child.scream.len + 2);
  ok(c.events.includes("studio:flee") && all().filter((e) => e.typeId === "studio:laestrygonian").every((g) => g.dp["studio:alarmed"]), "and runs; the giants emerge");
  ok(said(P, "odyssey.lae.emerge"), "from the fog");
}

// ================================================================ Circe
reset();
{
  const c = spawn("studio:circe", { x: 0, y: 64, z: 0 });
  const P = player(2, 2);
  runTicks(20);
  const sister = all().find((e) => e.typeId === "studio:circe_sister");
  ok(!!sister && all().filter((e) => e.typeId === "minecraft:pig").length === 3, "Circe has her sister and her three pigs");
  fire("dataDrivenEntityTrigger", { entity: c, eventId: "studio:offer_stew" });
  ok(c.props["studio:anim"] === "serve", "she ladles stew for a man without armour");
  runTicks(MOVES.circe.serve.give + 2);
  ok(cmds(/item studio:circe_stew/).length === 1 && said(P, "odyssey.circe.stew"), "and sets a bowl before him");
  runTicks(MOVES.circe.serve.len);
  P.armor.Chest = {};
  fire("dataDrivenEntityTrigger", { entity: c, eventId: "studio:offer_stew" });
  ok(c.props["studio:anim"] === "scream" && said(P, "odyssey.circe.no_armor") && cmds(/item studio:circe_stew/).length === 1, "for a man in armour she screams and gives nothing");
  P.armor = {};
  runTicks(MOVES.circe.scream.len + 5);
  fire("itemCompleteUse", { source: P, itemStack: new ItemStack("studio:circe_stew") });
  ok(said(P, "odyssey.circe.pliable"), "the stew makes him pliable");
  c.dp["studio:cd_mold"] = 0; c.dp["studio:cd_scream"] = 1e9;
  runTicks(30);
  ok(c.props["studio:anim"] === "mold", "within her reach she molds him like clay");
  runTicks(MOVES.circe.mold.finish + 2);
  ok(P.dp["studio:pig_until"] > 0 && P.hasEffect("slowness") && said(P, "odyssey.circe.molded"), "and he is a pig");
  runTicks(4);
  ok(all().some((e) => e.typeId === "minecraft:pig" && e.nameTag === "Odysseus" && e.hasTag("studio:curse_pig")), "a pig wears his name");
  fire("dataDrivenEntityTrigger", { entity: sister, eventId: "studio:seized" });
  ok(c.props["studio:yielded"] === true && !P.dp["studio:pig_until"] && said(P, "odyssey.circe.claims") && said(P, "odyssey.circe.hades"),
    "seizing her sister makes her yield: men are men again and she points to Hades");
  ok(sister.props["studio:anim"] === "flap" && c.props["studio:anim"] === "counsel", "the bird flaps and Circe gives her counsel");
  runTicks(110);
  ok(!all().some((e) => e.hasTag("studio:curse_pig")), "the pig is gone");
}

// ================================================================ the Sirens
reset();
{
  const s = spawn("studio:siren", { x: 0, y: 63, z: 0 });
  const A = player(20, 0, "Hearing"), B = player(22, 0, "Waxed");
  fire("itemCompleteUse", { source: B, itemStack: new ItemStack("studio:beeswax") });
  const C = player(0, 24, "Mast"); const boat = spawn("minecraft:boat", { x: 0, y: 63, z: 24 }); C.ridingEntity = boat;
  runTicks(20);
  ok(s.props["studio:anim"] === "sing", "the Siren sings when men are near");
  const heard = (n) => sounds.filter((x) => x.who === n).map((x) => x.id);
  ok(heard("Hearing")[0] === "odyssey.siren.song" && heard("Waxed")[0] === "odyssey.siren.song_muffled", "each listener hears their own mix: wax muffles the song");
  runTicks(21);
  ok(A.hasEffect("nausea") && A.vel.x < 0, "the song sickens and pulls the man toward the rocks");
  ok(!B.hasEffect("nausea") && said(B, "odyssey.siren.muffled") && B.vel.x === 0, "the waxed man hears a muffled hum");
  ok(C.hasEffect("slowness") && said(C, "odyssey.siren.mast"), "a man bound to the mast hears all of it and cannot go");
  runTicks(MOVES.siren.sing.len);
  runTicks(4);
  ok(s.props["studio:anim"] === "none" && !s.props["studio:anim"].includes("sing"), "the song ends and she lies still");
}
reset();
{
  const s = spawn("studio:siren", { x: 0, y: 63, z: 0 });
  const P = player(2, 1, "Reached");
  runTicks(20);
  ok(s.props["studio:anim"] === "drag" && said(P, "odyssey.siren.dragged"), "a man who reaches the rocks is dragged under");
  runTicks(MOVES.siren.drag.grab + 3);
  ok(P.location.y < 63, "down into the sea");
  runTicks(MOVES.siren.drag.len);
  ok(P.health <= 12 && P.vel.y > 0, "he is half drowned and cast out: " + P.health);
}

// ================================================================ Scylla and Charybdis
reset();
{
  const sc = spawn("studio:scylla", { x: 0, y: 64, z: 0 });
  const prey = [];
  for (let i = 0; i < 8; i++) prey.push(spawn("minecraft:pig", { x: 3 + i, y: 64, z: 5 }));
  runTicks(10);
  ok(sc.props["studio:anim"] === "lunge", "her necks lunge out when men come near");
  runTicks(MOVES.scylla.lunge.len + 1);
  ok(sc.props["studio:anim"] === "snatch", "then snatch");
  runTicks(MOVES.scylla.snatch.bite + 2);
  const taken = prey.filter((p) => p.health < 20);
  ok(taken.length === 6, "exactly six are taken, as Tiresias foretold: " + taken.length);
  runTicks(MOVES.scylla.snatch.len - MOVES.scylla.snatch.bite + 2);
  ok(sc.props["studio:anim"] === "devour" && taken.every((p) => p.location.y > 64 + 3), "the heads haul their victims up toward the cave");
  runTicks(MOVES.scylla.devour.len + 2);
  ok(taken.every((p) => p.health === 5), "three bites each: 3 + 12 = 15 damage");
  ok(sc.props["studio:anim"] === "recoil", "she recoils into the cave");
  ok(prey.filter((p) => p.health === 20).length === 2, "the other two are untouched");
}
reset();
{
  const sc = spawn("studio:scylla", { x: 0, y: 64, z: 0 });
  const boat = spawn("minecraft:boat", { x: 4, y: 63, z: 4 });
  runTicks(10);
  ok(sc.props["studio:anim"] === "rend", "an empty ship is torn apart");
  runTicks(MOVES.scylla.rend.hit + 2);
  ok(!boat.alive, "the ship is gone");
}
reset();
{
  const sc = spawn("studio:scylla", { x: 0, y: 64, z: 0 });
  runTicks(10);
  ok(all().some((e) => e.typeId === "studio:charybdis"), "Charybdis forms in the sea near Scylla");
}
reset();
{
  const ch = spawn("studio:charybdis", { x: 0, y: 62, z: 0 });
  const P = player(10, 0, "Swimmer"); P.mode = "survival";
  const boat = spawn("minecraft:boat", { x: -3, y: 62, z: 1 });
  const R = player(-3, 1, "Rower"); R.ridingEntity = boat;
  runTicks(4);
  ok(P.vel.x < 0, "the sea drains toward her throat and pulls the swimmer in");
  ok(ch.props["studio:anim"] === "surge" && said(P, "odyssey.charybdis.surge"), "now and then the whirlpool surges");
  runTicks(MOVES.charybdis.surge.len + 2);
  ok(!(ch.dp["studio:surge_until"] > 0) || ch.props["studio:anim"] !== "surge", "the surge passes");
}
reset();
{
  const ch = spawn("studio:charybdis", { x: 0, y: 62, z: 0 });
  ch.dp["studio:cd_surge"] = 1e9;
  const boat = spawn("minecraft:boat", { x: -3, y: 62, z: 1 });
  const R = player(-3, 1, "Rower"); R.ridingEntity = boat;
  runTicks(4);
  ok(ch.props["studio:anim"] === "gulp", "a ship at her throat is swallowed");
  runTicks(MOVES.charybdis.gulp.gulp + 2);
  ok(!boat.alive && R.health <= 14, "the ship is gone and the crew nearly drowned");
}

// ================================================================ Hades
reset();
{
  const P = player(0, 0, "Odysseus");
  setBlock(0, 63, 0, "minecraft:soul_sand");
  const sheep = spawn("minecraft:sheep", { x: 1, y: 64, z: 1 });
  fire("entityDie", { deadEntity: sheep, damageSource: { damagingEntity: P } });
  ok(said(P, "odyssey.hades.rise") && sounds.some((x) => x.id === "odyssey.shade.whispers"), "a sheep sacrificed on black sand raises the dead");
  const shades = () => all().filter((e) => e.typeId === "studio:shade");
  ok(shades().length === 2 && all().some((e) => e.typeId === "studio:tiresias"), "Sinon, Agamemnon and Tiresias rise");
  ok(shades().map((s) => s.props["studio:variant"]).sort().join() === "1,2", "as Sinon and Agamemnon");
  runTicks(62);
  ok(shades().some((s) => s.props["studio:anim"] === "speak_sinon") && said(P, "odyssey.hades.sinon"), "Sinon speaks first");
  runTicks(80);
  ok(shades().some((s) => s.props["studio:anim"] === "speak_agamemnon") && said(P, "odyssey.hades.agamemnon"), "then Agamemnon");
  runTicks(80);
  const tir = all().find((e) => e.typeId === "studio:tiresias");
  ok(tir.props["studio:anim"] === "speak" && said(P, "odyssey.hades.tiresias"), "then Tiresias prophesies");
  runTicks(130);
  ok(shades().filter((s) => s.props["studio:variant"] === 0).length === 6 && said(P, "odyssey.hades.crew"), "six shades of his crew come at a run");
  const crew = shades().find((s) => s.props["studio:variant"] === 0);
  crew.teleport({ x: 1, y: 64, z: 1 }); P.teleport({ x: 0, y: 64, z: 0 });
  runTicks(MOVES.shade.rise.len + 12);
  ok(crew.props["studio:anim"] === "grasp", "a crew shade grasps at him");
  runTicks(MOVES.shade.grasp.hit + 3);
  ok(P.health <= 15 && said(P, "odyssey.hades.grasp"), "the dead drag at him");
  runTicks(60);
  ok(!all().some((e) => e.typeId === "studio:tiresias"), "Tiresias sinks back into the sand");
}

// ================================================================ the gods and the rest
reset();
{
  const P = player(0, 0);
  const cow = spawn("studio:sun_cattle", { x: 3, y: 64, z: 3 });
  fire("entityDie", { deadEntity: cow, damageSource: { damagingEntity: P } });
  ok(said(P, "odyssey.zeus.storm") && cmds(/weather thunder/).length === 1, "killing Apollo's cattle brings Zeus's storm");
  runTicks(130);
  ok(cmds(/spawn minecraft:lightning_bolt/).length >= 2, "with lightning");
  const c = spawn("studio:sun_cattle", { x: 3, y: 64, z: 3 });
  hurtBy(c, P);
  ok(c.props["studio:anim"] === "low", "a hurt cow lows");
  c.dp["studio:cd_graze"] = 0;
  runTicks(MOVES.sun_cattle.low.len + 2);
  c.dp["studio:cd_graze"] = 0; Math.random = () => 0.1; runTicks(20);
  ok(c.props["studio:anim"] === "graze", "a calm one grazes");
}
reset();
{
  const P = player(0, 0), calypso = spawn("studio:calypso", { x: 2, y: 64, z: 0 });
  fire("dataDrivenEntityTrigger", { entity: calypso, eventId: "studio:offer_lotus" });
  ok(calypso.props["studio:anim"] === "offer", "Calypso offers the lotus");
  runTicks(MOVES.calypso.offer.give + 2);
  ok(cmds(/item studio:lotus_flower/).length === 1 && said(P, "odyssey.calypso.lotus"), "and gives it");
  P.level = 12;
  fire("itemCompleteUse", { source: P, itemStack: new ItemStack("studio:lotus_flower") });
  ok(P.level === 0 && said(P, "odyssey.calypso.eaten") && P.hasEffect("slowness"), "eating it takes the memories away");
  runTicks(MOVES.calypso.offer.len);
  fire("dataDrivenEntityTrigger", { entity: calypso, eventId: "studio:embrace" });
  runTicks(MOVES.calypso.embrace.hug + 2);
  ok(P.hasEffect("regeneration") && said(P, "odyssey.calypso.embrace"), "her embrace heals");
}
reset();
{
  const P = player(0, 0), a = spawn("studio:athena", { x: 2, y: 64, z: 0 });
  fire("dataDrivenEntityTrigger", { entity: a, eventId: "studio:bless" });
  runTicks(MOVES.athena.bless.give + 2);
  ok(P.hasEffect("resistance") && said(P, "odyssey.athena.bless"), "Athena commands him home and shields him");
  const Q = player(30, 30, "Journeyman"); Q.dp["studio:journey"] = true;
  Q.health = 5; hurtBy(Q, undefined, 0);
  ok(all().some((e) => e.typeId === "studio:athena" && e !== a), "in an hour of crisis she appears to a man of the journey");
  runTicks(MOVES.athena.appear.len + 2);
  ok(Q.hasEffect("resistance") && said(Q, "odyssey.athena.vision"), "and bids him return");
  runTicks(MOVES.athena.vanish.len + 2);
  ok(all().filter((e) => e.typeId === "studio:athena").length === 1, "then she is gone");
  const R = player(60, 60, "Stranger"); R.health = 5; hurtBy(R, undefined, 0);
  ok(all().filter((e) => e.typeId === "studio:athena").length === 1, "a man who is not on the journey gets no vision");
}
reset();
{
  const h = spawn("studio:trojan_horse", { x: 0, y: 64, z: 0 });
  const P = player(0, 0, "Greek"); P.ridingEntity = h;
  runTicks(20);
  ok(h.props["studio:anim"] === "hatch" && P.hasEffect("invisibility"), "a man climbs in through the hatch and is hidden");
  runTicks(MOVES.trojan_horse.hatch.len + 2);
  setTime(14000); runTicks(40);
  ok(h.props["studio:anim"] === "sally", "at night the Greeks pour out");
  runTicks(MOVES.trojan_horse.sally.eject + 2);
  ok(!P.ridingEntity && P.hasEffect("strength") && said(P, "odyssey.horse.sally"), "armed and strengthened");
}

// ================================================================ the journey (only in the map)
reset();
{
  const P = player(0, 3, "Early");
  runTicks(20);
  fire("playerSpawn", { player: P, initialSpawn: true });
  ok(P.inventory.length === 0 && P.titles.length === 0, "in an ordinary world there is no kit and no title");
  setBlock(0, 64, 0, "minecraft:lodestone");
  const Q = player(0, 3, "Crew");
  runTicks(20);
  fire("playerSpawn", { player: Q, initialSpawn: true });          // (the marker is looked for again when someone spawns)
  ok(Q.inventory.map((i) => i.typeId + "x" + i.amount).join() === "minecraft:oak_boatx2,studio:beeswaxx6,studio:burning_stakex1", "in the map he is given boats, wax and a burning stake");
  ok(Q.titles.length === 1 && said(Q, "odyssey.kit"), "and the title");
  fire("playerSpawn", { player: Q, initialSpawn: false });
  ok(Q.inventory.length === 3 && Q.titles.length === 1, "only once");
  runTicks(100);
  ok(all().some((e) => e.typeId === "studio:calypso"), "Calypso is on Ogygia");
  ok(Q.titles.length === 2 && Q.titles[1].title.rawtext[0].translate === "odyssey.site.ogygia", "arriving at Ogygia shows its name");
  ok(sounds.some((x) => x.who === "Crew" && x.id === "odyssey.world.arrive"), "with the arrival swell");
}
{
  // two crew members at two places: separate titles and separate fog
  const A = world.getAllPlayers().find((p) => p.name === "Crew");
  const B = player(-480, 130, "Herdsman");
  fire("playerSpawn", { player: B, initialSpawn: true });
  A.teleport({ x: 560, y: 64, z: 60 });
  runTicks(100);
  ok(cmds(/cmd@Crew fog @s push odyssey:telepylus odyssey_site/).length === 1 && cmds(/cmd@Herdsman fog/).length === 0, "the fog of Telepylus closes in on the one who is there, not on the other");
  ok(all().some((e) => e.typeId === "studio:laestrygonian_child"), "a Laestrygonian child waits in the fog");
  ok(all().filter((e) => e.typeId === "studio:sun_cattle").length === 6, "six cattle graze on Thrinacia");
  ok(B.titles.some((t) => t.title.rawtext[0].translate === "odyssey.site.thrinacia"), "and Thrinacia is named for its visitor");
  A.teleport({ x: 0, y: 64, z: 400 });
  runTicks(40);
  ok(cmds(/cmd@Crew fog @s remove odyssey_site/).length === 1, "leaving the place lifts its fog");
  const cows = all().filter((e) => e.typeId === "studio:sun_cattle");
  cows.forEach((c) => c.applyDamage(100, {}));
  runTicks(200);
  ok(all().filter((e) => e.typeId === "studio:sun_cattle").length === 0, "killed cattle do not return at once");
  runTicks(12100);
  ok(all().filter((e) => e.typeId === "studio:sun_cattle").length === 6, "but they do after ten minutes");
}

// ================================================================ several players at once
reset();
{
  setBlock(0, 64, 0, "minecraft:lodestone");
  const a = spawn("studio:cyclops", { x: 0, y: 64, z: 0 }), b = spawn("studio:cyclops", { x: 200, y: 64, z: 0 });
  const P = player(0, 5, "One"), Q = player(200, 5, "Two");
  runTicks(10);
  ok(a.props["studio:anim"] === "devour" && b.props["studio:anim"] === "devour", "two giants hold two men at once");
  runTicks(MOVES.cyclops.devour.bite[0] + 3);
  ok(P.location.x < 10 && Q.location.x > 190 && P.location.y > 70 && Q.location.y > 70, "each carries his own");
  runTicks(MOVES.cyclops.devour.len);
  ok(P.health === 6 && Q.health === 6, "each is bitten twice");
  const W = player(0, 20, "Waxed");
  fire("itemCompleteUse", { source: W, itemStack: new ItemStack("studio:beeswax") });
  const X = player(0, 22, "Open");
  ok(W.dp["studio:deaf_until"] > 0 && !X.dp["studio:deaf_until"], "wax affects only the one who used it");
}

console.log(`\n${count - failed} of ${count} checks passed`);
if (failed) { console.error(`${failed} FAILED`); process.exit(1); }
console.log("ALL MECHANICS TESTS PASSED");
