// Story cinematics: the opening (split by where each character begins), chapter endings and the finale.
// All shots are framed on verified points from data/config.js; cinematics.js lifts anchors onto the real terrain.
import { world, system } from "@minecraft/server";
import { POINTS, ROLES } from "../data/config.js";
import { dp, near, safe, setDp, valid } from "../lib/util.js";
import { bar, tell, title } from "../lib/fx.js";
import { perform } from "../lib/moves.js";
import { groundY } from "../lib/terrain.js";
import { camClear, camFade, camFree, lockInput, playCutscene, SHOTS } from "./cinematics.js";
import { STATE_CINEMATIC, STATE_NORMAL, getWorldState, setWorldState } from "./pause_vote.js";
import { playTheme } from "./music.js";

const P = (k) => POINTS[k];
const groupOf = (p) => ROLES[dp(p, "studio:role", "")]?.group ?? "ogygia";

const OPENING = {
  ithaca: [
    { tick: 2,   shotType: "aerial_high",      anchor: P("ithaca_square"), titleKey: "odyssey.open.ithaca.title", subKey: "odyssey.open.ithaca.sub" },
    { tick: 70,  shotType: "low_angle_hero",   anchor: P("ithaca_palace"), height: 8, sayKey: "odyssey.open.ithaca.1", cut: true },
    { tick: 140, shotType: "closeup_dialogue", anchor: P("ithaca_mentor"), sayKey: "odyssey.open.ithaca.2", npcType: "studio:odyssey_person", npcAnim: "point" },
    { tick: 200, shotType: "tracking_shot",    anchor: P("ithaca_harbor"), sayKey: "odyssey.open.ithaca.3" },
  ],
  ogygia: [
    { tick: 2,   shotType: "ocean_panorama",   anchor: P("ogygia_harbor"), titleKey: "odyssey.open.ogygia.title", subKey: "odyssey.open.ogygia.sub" },
    { tick: 70,  shotType: "wide_establishing", anchor: P("ogygia_temple"), sayKey: "odyssey.open.ogygia.1", cut: true },
    { tick: 140, shotType: "closeup_dialogue", anchor: P("ogygia_calypso"), sayKey: "odyssey.open.ogygia.2", npcType: "studio:calypso", npcAnim: "offer" },
    { tick: 200, shotType: "over_the_shoulder", anchor: P("ogygia_harbor"), sayKey: "odyssey.open.ogygia.3" },
  ],
};

/** Opening cinematic. Players see the scene for the island they start on; both groups run in lockstep (same length). */
export function playOpening(players, onEnd) {
  const groups = { ithaca: [], ogygia: [] };
  for (const p of players.filter(valid)) groups[groupOf(p)].push(p);
  const order = Object.entries(groups).filter(([, list]) => list.length);
  if (!order.length) { onEnd?.(); return; }
  // Both groups are played as one scene with per-player shots, so nobody waits for the other group's cutscene.
  const audience = order.flatMap(([, list]) => list);
  const steps = [];
  for (const [g, list] of order) {
    for (const st of OPENING[g]) steps.push({ ...st, only: list.map((p) => p.id) });
  }
  playSplit("opening", steps, 270, audience, onEnd);
}

/** Like playCutscene, but each step is shown only to the players listed in `step.only`. */
function playSplit(id, steps, duration, audience, onEnd) {
  const byGroup = new Map();
  for (const st of steps) {
    const key = st.only.join(",");
    if (!byGroup.has(key)) byGroup.set(key, []);
    byGroup.get(key).push(st);
  }
  const groups = [...byGroup.entries()];
  let remaining = groups.length;
  const done = () => { if (--remaining === 0) onEnd?.(); };
  // The first group drives the global cutscene state; the others run alongside it.
  groups.forEach(([ids, st], i) => {
    const players = audience.filter((p) => ids.split(",").includes(p.id));
    playCutsceneParallel(`${id}_${i}`, st, duration, players, done);
  });
}

// playCutscene queues scenes one after another; the opening needs two scenes at once, so it has its own runner below.
let parallelRunning = 0;

function playCutsceneParallel(id, steps, duration, players, onEnd) {
  if (!players.length) { onEnd?.(); return; }
  parallelRunning++;
  setWorldState(STATE_CINEMATIC);
  const dim = players[0].dimension;
  for (const p of players) {
    setDp(p, "studio:in_cutscene", true);
    lockInput(p, true);
    playTheme(p, "odyssey.music.cinematic", true);
  }
  for (const step of steps) {
    system.runTimeout(() => safe(`cut.${id}`, () => {
      let a = step.anchor;
      const gy = groundY(dim, Math.floor(a.x), Math.floor(a.z), Math.floor(a.y) + 40, Math.floor(a.y) - 20);
      if (gy !== undefined && Math.abs(gy + 1 - a.y) > 2) a = { ...a, y: gy + 1 };
      if (step.npcType) {
        const npc = near(dim, a, 24, step.npcType)[0];
        if (npc) safe("npc", () => perform(npc, step.npcAnim, {}, { still: false, force: true }));
      }
      for (const p of players) {
        if (!p.isValid()) continue;
        const shot = step.shotType === "over_the_shoulder" ? SHOTS.over_the_shoulder(p, a) : (SHOTS[step.shotType] ?? SHOTS.wide_establishing)(a, step.height ?? 4);
        if (step.cut) camFade(p, 0.25, 0.1, 0.25);
        camFree(p, shot.pos, shot.facing, step.cut ? 0 : shot.ease);
        if (step.titleKey) title(p, step.titleKey, step.subKey ?? "");
        if (step.sayKey) { tell(p, step.sayKey); bar(p, step.sayKey); }
      }
    }), Math.max(1, step.tick));
  }
  system.runTimeout(() => {
    for (const p of players) {
      if (!p.isValid()) continue;
      camFade(p, 0.4, 0.2, 0.8);
      camClear(p);
      lockInput(p, false);
      setDp(p, "studio:in_cutscene", false);
    }
    if (--parallelRunning === 0 && getWorldState() === STATE_CINEMATIC) setWorldState(STATE_NORMAL);
    onEnd?.();
  }, duration);
}

/** Short closing scene for a finished chapter, shown to everyone. */
const CHAPTER_END = {
  1: { anchor: "ogygia_harbor", shot: "ocean_panorama", say: "odyssey.end.1" },
  2: { anchor: "troy_horse", shot: "low_angle_hero", say: "odyssey.end.2", height: 9 },
  3: { anchor: "cyclops_landing", shot: "ocean_panorama", say: "odyssey.end.3" },
  4: { anchor: "aeaea_shore", shot: "aerial_pan", say: "odyssey.end.4" },
  5: { anchor: "aeaea_hall", shot: "wide_establishing", say: "odyssey.end.5" },
  6: { anchor: "hades_altar", shot: "tracking_reverse", say: "odyssey.end.6" },
  7: { anchor: "strait_cliff", shot: "aerial_high", say: "odyssey.end.7" },
  8: { anchor: "ithaca_harbor", shot: "aerial_pan", say: "odyssey.end.8" },
};

export function playChapterEnd(chapter, onEnd) {
  const c = CHAPTER_END[chapter];
  const players = world.getAllPlayers().filter(valid);
  if (!c || !players.length) { onEnd?.(); return; }
  playCutscene(`chapter_end_${chapter}`, P(c.anchor), [
    { tick: 2, shotType: c.shot, anchor: P(c.anchor), height: c.height ?? 4, sayKey: c.say, titleKey: `odyssey.ch.${chapter}.title`, subKey: "odyssey.end.sub" },
  ], 100, players, onEnd);
}

/** The homecoming: the bow is strung, and (as in the film's ending) Odysseus cedes the throne to Telemachus. */
export function playFinale(onEnd) {
  const players = world.getAllPlayers().filter(valid);
  playCutscene("finale_ithaca", P("ithaca_palace"), [
    { tick: 2,   shotType: "low_angle_hero",   anchor: P("ithaca_palace"), height: 6, titleKey: "odyssey.finale.title", subKey: "odyssey.finale.sub" },
    { tick: 70,  shotType: "closeup_dialogue", anchor: P("ithaca_palace"), sayKey: "odyssey.finale.1", cut: true },
    { tick: 140, shotType: "wide_establishing", anchor: P("ithaca_square"), sayKey: "odyssey.finale.2", npcType: "studio:athena", npcAnim: "bless" },
    { tick: 210, shotType: "ocean_panorama",   anchor: P("ithaca_harbor"), sayKey: "odyssey.finale.3" },
  ], 300, players, onEnd);
}
