// Circe, the witch of Aeaea, and her sister the bird. Four moves:
//   serve   - ladles stew for the unarmoured
//   scream  - armoured strangers: the sensible thing to do is scream
//   mold    - works a man's flesh like clay until he is a squealing pig
//   counsel - points the way to Hades (once Odysseus has seized her sister and she stands down)
// The stew is only for those who leave their armour outside; eating it makes a man pliable.
import { world, ItemStack } from "@minecraft/server";
import { MOVES } from "../data/moves.js";
import {
  add, byId, clearEffect, dp, effect, forward, near, nearestPlayer, now, prop, ready, right, ringSpot, safe, scale, setDp,
  setProp, trigger, wait, wearsArmor, playersNear, valid,
} from "../lib/util.js";
import { bar, say, sound, tell } from "../lib/fx.js";
import { busy, perform } from "../lib/moves.js";
import { hold, isHeld as held } from "../lib/holds.js";
import { creatures } from "../lib/registry.js";

export const TYPE = "studio:circe", SISTER = "studio:circe_sister";
const CURSE_EFFECTS = [["invisibility", 0], ["slowness", 1], ["weakness", 1], ["mining_fatigue", 0]];
const pliable = (p) => dp(p, "studio:pliable_until", 0) > now();

function initCirce(c) {
  if (dp(c, "studio:init", false)) return;
  setDp(c, "studio:init", true);
  safe("sister", () => {
    const bird = c.dimension.spawnEntity(SISTER, add(c.location, { x: 0, y: 1.6, z: 0 }));
    setDp(bird, "studio:owner", c.id);
    setDp(c, "studio:sister", bird.id);
  });
  for (let i = 0; i < 3; i++) safe("pig", () => c.dimension.spawnEntity("minecraft:pig", ringSpot(c.location, 3 + i, i * 2.1)).addTag("studio:island_animal"));
}

// ---------------------------------------------------------------- the curse (per player)
function curse(p) {
  setDp(p, "studio:pig_until", now() + 12000);
  for (const [id, amp] of CURSE_EFFECTS) effect(p, id, 12000, amp);
  tell(p, "odyssey.circe.molded");
  sound(p.dimension, "mob.pig.death", p.location, 1, 0.7);
}
export function endCurse(p, message = true) {
  if (!dp(p, "studio:pig_until", 0)) return;
  setDp(p, "studio:pig_until", 0);
  for (const [id] of CURSE_EFFECTS) clearEffect(p, id);
  const pig = byId(dp(p, "studio:curse_pig", ""));
  if (pig) safe("pig", () => pig.remove());
  setDp(p, "studio:curse_pig", "");
  if (message) bar(p, "odyssey.circe.human");
}
export function tickCurses() {
  for (const p of world.getAllPlayers()) {
    safe("curse", () => {
      const until = dp(p, "studio:pig_until", 0);
      if (!until) return;
      if (now() >= until) { endCurse(p); return; }
      let pig = byId(dp(p, "studio:curse_pig", ""));
      if (!pig) {
        pig = p.dimension.spawnEntity("minecraft:pig", p.location);
        pig.nameTag = p.name;
        pig.addTag("studio:curse_pig");
        setDp(pig, "studio:owner", p.id);
        setDp(p, "studio:curse_pig", pig.id);
      }
      let yaw = 0;
      try { yaw = p.getRotation().y; } catch { }
      pig.teleport(p.location, { keepVelocity: false, rotation: { x: 0, y: yaw } });
    });
  }
  if (now() % 100 === 0) {                  // pigs of players who left or were cured
    for (const dim of ["minecraft:overworld", "minecraft:nether", "minecraft:the_end"]) {
      safe("pigs", () => {
        for (const pig of world.getDimension(dim).getEntities({ type: "minecraft:pig", tags: ["studio:curse_pig"] })) {
          const owner = byId(dp(pig, "studio:owner", ""));
          if (!owner || !dp(owner, "studio:pig_until", 0)) pig.remove();
        }
      });
    }
  }
}

// ---------------------------------------------------------------- her moves
function mold(c, victim) {
  const spec = MOVES.circe.mold;
  return perform(c, "mold", {
    start: () => {
      wait(c, "studio:cd_mold", 160);
      effect(victim, "darkness", 70);
      hold(victim, c, { ticks: spec.finish, at: (h) => add(scale(forward(h), 1.2), { x: 0, y: 0.05, z: 0 }) });
    },
    finish: () => { if (valid(victim)) { setDp(victim, "studio:pliable_until", 0); curse(victim); } },
  });
}
function serve(c, p) {
  if (wearsArmor(p)) { scream(c); tell(p, "odyssey.circe.no_armor"); return; }
  perform(c, "serve", {
    give: () => {
      if (!valid(p)) return;
      safe("stew", () => c.dimension.spawnItem(new ItemStack("studio:circe_stew", 1), p.location));
      tell(p, "odyssey.circe.stew");
    },
  });
}
function scream(c) {
  return perform(c, "scream", {
    start: () => {
      wait(c, "studio:cd_scream", 600);
      say(c.dimension, c.location, 24, "odyssey.circe.scream");
      for (const pig of near(c.dimension, c.location, 14, "minecraft:pig")) effect(pig, "speed", 80, 2);      // the pigs bolt
    },
  });
}
function counsel(c, p) {
  perform(c, "counsel", { start: () => tell(p, "odyssey.circe.counsel") });
}
export function circeYield(c) {
  if (prop(c, "studio:yielded", false)) return;
  trigger(c, "studio:yield");
  setProp(c, "studio:yielded", true);
  for (const p of playersNear(c.dimension, c.location, 64)) endCurse(p);
  say(c.dimension, c.location, 32, "odyssey.circe.seized");
  say(c.dimension, c.location, 32, "odyssey.circe.claims");
  say(c.dimension, c.location, 32, "odyssey.circe.hades");
  const bird = byId(dp(c, "studio:sister", ""));
  if (bird) perform(bird, "flap", {}, { still: false });
  perform(c, "counsel", {}, { force: true });
}

// ---------------------------------------------------------------- loops and events
let circeTick = 0;
export function tickCirce() {
  circeTick++;
  for (const c of creatures(TYPE)) {
    safe("circe", () => {
      initCirce(c);
      const bird = byId(dp(c, "studio:sister", ""));
      if (bird) {                           // the sister rides her shoulder
        const r = right(c);
        let yaw = 0;
        try { yaw = c.getRotation().y; } catch { }
        try { bird.teleport(add(c.location, { x: r.x * 0.3, y: 1.62, z: r.z * 0.3 }), { keepVelocity: false, rotation: { x: 0, y: yaw } }); } catch { }
      }
      if (circeTick % 10 !== 0 || busy(c) || prop(c, "studio:yielded", false)) return;
      const armoured = nearestPlayer(c, 9, wearsArmor);
      if (armoured && ready(c, "studio:cd_scream")) { scream(c); return; }
      const victim = nearestPlayer(c, 4, (p) => pliable(p) && !dp(p, "studio:pig_until", 0) && !held(p));
      if (victim && ready(c, "studio:cd_mold")) mold(c, victim);
    });
  }
}
/** Interactions: the entity's events name what the player asked for. */
export function onTrigger(e, id) {
  if (e.typeId === TYPE) {
    const p = nearestPlayer(e, 6);
    if (!p) return;
    if (id === "studio:offer_stew") serve(e, p);
    else if (id === "studio:counsel") counsel(e, p);
  } else if (e.typeId === SISTER && id === "studio:seized") {
    const c = byId(dp(e, "studio:owner", ""));
    if (c) circeYield(c);
  }
}
export const onItemStew = (p) => { setDp(p, "studio:pliable_until", now() + 2400); bar(p, "odyssey.circe.pliable"); };
