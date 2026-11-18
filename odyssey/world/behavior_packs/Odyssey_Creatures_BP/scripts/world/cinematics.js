// Complete Cinematic Cutscene System (8 Camera Shot Types & 12 Story Sequences).
// Shot types implemented via Bedrock's native /camera API:
//   1. wide_establishing      - Elevated wide angle framing the island & Greek architecture
//   2. aerial_pan             - High-altitude sweeping camera across harbors & seas
//   3. low_angle_hero         - Low camera looking up at Polyphemus, Scylla, Trojan Horse, or Athena
//   4. closeup_dialogue       - Eye-level portrait shot on speaking character
//   5. over_the_shoulder      - Framed over the player's shoulder toward the speaker
//   6. tracking_shot          - Lateral moving camera tracking across the scene
//   7. panoramic_battlefield  - Wide sweeping arc across Troy or Telepylus
//   8. dynamic_action         - Fast-ease combat/reveal shot
import { world, system, EasingType } from "@minecraft/server";
import { add, dp, flat, forward, near, rawNow, right, safe, scale, setDp, valid } from "../lib/util.js";
import { bar, hear, tell, title } from "../lib/fx.js";
import { perform } from "../lib/moves.js";
import { groundY } from "../lib/terrain.js";
import { playTheme } from "./music.js";
import { STATE_CINEMATIC, STATE_NORMAL, getWorldState, setWorldState } from "./pause_vote.js";

function camCmd(p, cmd) {
  try {
    if (typeof p.runCommandAsync === "function") p.runCommandAsync(cmd);
    else p.runCommand?.(cmd);
  } catch { }
}

const EASE = { in_out_sine: "InOutSine", linear: "Linear", in_out_cubic: "InOutCubic", out_quad: "OutQuad", in_out_quad: "InOutQuad" };

/** Full-screen fade (seconds). Uses the Camera API, falls back to /camera. */
export function camFade(p, fadeIn = 0.4, hold = 0.2, fadeOut = 0.4) {
  try {
    p.camera.fade({ fadeTime: { fadeInTime: fadeIn, holdTime: hold, fadeOutTime: fadeOut }, fadeColor: { red: 0, green: 0, blue: 0 } });
  } catch {
    camCmd(p, `camera @s fade time ${fadeIn} ${hold} ${fadeOut} color 0 0 0`);
  }
}

export function camFree(p, pos, facing, easeSec = 2.0, easeType = "in_out_sine") {
  try {
    const opts = { location: pos, facingLocation: facing };
    if (easeSec > 0) opts.easeOptions = { easeTime: easeSec, easeType: EasingType[EASE[easeType] ?? "InOutSine"] ?? "InOutSine" };
    p.camera.setCamera("minecraft:free", opts);
    return;
  } catch { }
  const px = pos.x.toFixed(2), py = pos.y.toFixed(2), pz = pos.z.toFixed(2);
  const fx = facing.x.toFixed(2), fy = facing.y.toFixed(2), fz = facing.z.toFixed(2);
  if (easeSec > 0) camCmd(p, `camera @s set minecraft:free ease ${easeSec.toFixed(2)} ${easeType} pos ${px} ${py} ${pz} facing ${fx} ${fy} ${fz}`);
  else camCmd(p, `camera @s set minecraft:free pos ${px} ${py} ${pz} facing ${fx} ${fy} ${fz}`);
}

export function camClear(p) {
  try { p.camera.clear(); } catch { camCmd(p, "camera @s clear"); }
}

/** Freeze or release a player's own movement and look input (the world keeps running). */
export function lockInput(p, locked) {
  const v = locked ? "disabled" : "enabled";
  camCmd(p, `inputpermission set @s movement ${v}`);
  camCmd(p, `inputpermission set @s camera ${v}`);
}

/** A player joining (or rejoining after a disconnect mid-cutscene) must never be left on a cinematic camera. */
export function recoverPlayerCamera(p) {
  if (!valid(p)) return;
  if (dp(p, "studio:in_cutscene", false) || dp(p, "studio:locked", false)) {
    camClear(p);
    lockInput(p, false);
    setDp(p, "studio:in_cutscene", false);
    setDp(p, "studio:locked", false);
  }
  if (!active && getWorldState() === STATE_CINEMATIC) setWorldState(STATE_NORMAL);
}

/** Lift a hard-coded anchor onto the real terrain when it would sit inside or far above the ground. */
function onTerrain(dim, a) {
  const gy = groundY(dim, Math.floor(a.x), Math.floor(a.z), Math.floor(a.y) + 60, Math.floor(a.y) - 20);
  if (gy === undefined) return a;
  return Math.abs(gy + 1 - a.y) > 2 ? { x: a.x, y: gy + 1, z: a.z } : a;
}

/** Build the camera shot types relative to an anchor position `c`. */
export const SHOTS = {
  wide_establishing: (c) => ({ pos: { x: c.x - 18, y: c.y + 12, z: c.z - 18 }, facing: { x: c.x, y: c.y + 3, z: c.z }, ease: 2.2 }),
  aerial_pan: (c) => ({ pos: { x: c.x + 22, y: c.y + 24, z: c.z - 14 }, facing: { x: c.x, y: c.y + 2, z: c.z }, ease: 2.8 }),
  aerial_high: (c) => ({ pos: { x: c.x - 30, y: c.y + 40, z: c.z + 30 }, facing: { x: c.x, y: c.y, z: c.z }, ease: 3.5 }),
  ocean_panorama: (c) => ({ pos: { x: c.x + 40, y: c.y + 8, z: c.z + 10 }, facing: { x: c.x, y: c.y + 2, z: c.z }, ease: 3.0 }),
  low_angle_hero: (c, h = 6) => ({ pos: { x: c.x + 4.5, y: c.y + 0.9, z: c.z + 4.5 }, facing: { x: c.x, y: c.y + h, z: c.z }, ease: 1.6 }),
  closeup_dialogue: (c) => ({ pos: { x: c.x + 2.2, y: c.y + 1.65, z: c.z + 2.2 }, facing: { x: c.x, y: c.y + 1.6, z: c.z }, ease: 1.4 }),
  over_the_shoulder: (p, targetLoc) => {
    const f = forward(p), r = right(p);
    return {
      pos: { x: p.location.x - f.x * 1.6 + r.x * 0.65, y: p.location.y + 1.7, z: p.location.z - f.z * 1.6 + r.z * 0.65 },
      facing: { x: targetLoc.x, y: targetLoc.y + 1.5, z: targetLoc.z }, ease: 1.3,
    };
  },
  tracking_shot: (c) => ({ pos: { x: c.x + 12, y: c.y + 4, z: c.z + 12 }, facing: { x: c.x, y: c.y + 2, z: c.z }, ease: 2.4 }),
  tracking_reverse: (c) => ({ pos: { x: c.x - 12, y: c.y + 4, z: c.z + 12 }, facing: { x: c.x, y: c.y + 2, z: c.z }, ease: 2.4 }),
  panoramic_battlefield: (c) => ({ pos: { x: c.x - 24, y: c.y + 15, z: c.z + 20 }, facing: { x: c.x, y: c.y + 4, z: c.z }, ease: 2.6 }),
  dynamic_action: (c, h = 3) => ({ pos: { x: c.x - 6, y: c.y + 2.2, z: c.z + 6 }, facing: { x: c.x, y: c.y + h, z: c.z }, ease: 0.9 }),
};

// One cutscene runs at a time; later requests queue behind it instead of fighting over the camera.
let active = null;
const queue = [];
export const cutsceneActive = () => !!active;

/**
 * Play a multi-shot synchronized cutscene for `players` (defaults to all connected players).
 * Each step: { tick, shotType, anchor, height, titleKey, subKey, sayKey, npcType, npcAnim, sound }.
 * Every audience member sees the same shots on the same tick, has movement/look input locked, and gets control back
 * at the end (or on rejoin, see recoverPlayerCamera). `onEnd` runs once when the scene finishes.
 */
export function playCutscene(id, center, steps, durationTicks = 140, players = null, onEnd = undefined) {
  const audience = (players ?? world.getAllPlayers()).filter(valid);
  if (!audience.length) { if (onEnd) safe("cutscene.end", onEnd); return; }
  if (active) { queue.push([id, center, steps, durationTicks, players, onEnd]); return; }
  active = { id, audience: audience.map((p) => p.id) };

  setWorldState(STATE_CINEMATIC);
  const dim = audience[0].dimension;
  for (const p of audience) {
    setDp(p, `studio:seen_cutscene_${id}`, true);
    setDp(p, "studio:in_cutscene", true);
    lockInput(p, true);
    camFade(p, 0.35, 0.15, 0.35);
    playTheme(p, id.startsWith("finale") ? "odyssey.music.victory" : "odyssey.music.cinematic", true);
  }

  for (const step of steps) {
    system.runTimeout(() => {
      safe(`cutscene.${id}`, () => {
        const anchor = onTerrain(dim, step.anchor ?? center);
        if (step.npcType && step.npcAnim) {
          const npc = near(dim, anchor, 32, step.npcType)[0];
          if (valid(npc)) safe("cutscene.npc", () => perform(npc, step.npcAnim, {}, { still: false, force: true }));
        }
        for (const p of audience) {
          if (!valid(p)) continue;
          const shot = step.shotType === "over_the_shoulder"
            ? SHOTS.over_the_shoulder(p, anchor)
            : (SHOTS[step.shotType] ?? SHOTS.wide_establishing)(anchor, step.height ?? 4);
          if (step.cut) camFade(p, 0.25, 0.1, 0.25);
          camFree(p, shot.pos, shot.facing, step.cut ? 0 : shot.ease);
          if (step.titleKey) title(p, step.titleKey, step.subKey ?? "");
          if (step.sayKey) { tell(p, step.sayKey); bar(p, step.sayKey); }
          if (step.sound) hear(p, step.sound, undefined, 0.9, 1.0);
        }
      });
    }, Math.max(1, step.tick));
  }

  system.runTimeout(() => {
    for (const p of audience) {
      if (!valid(p)) continue;
      camFade(p, 0.3, 0.1, 0.3);
      camClear(p);
      lockInput(p, false);
      setDp(p, "studio:in_cutscene", false);
    }
    active = null;
    if (getWorldState() === STATE_CINEMATIC) setWorldState(STATE_NORMAL);
    if (onEnd) safe("cutscene.end", onEnd);
    const next = queue.shift();
    if (next) system.runTimeout(() => playCutscene(...next), 10);
  }, durationTicks);
}

/** Trigger the signature multi-shot cutscene for any of the 11 campaign sites or major story events. */
export function playSiteCutscene(siteId, player, force = false) {
  if (!valid(player)) return;
  if (!force && dp(player, `studio:seen_cutscene_${siteId}`, false)) return;
  // A replay from the menu is shown only to the player who asked. A first visit is shown to everyone nearby who
  // has not seen this site's scene yet, so players who already saw it are never pulled back into it.
  const audience = force ? [player] : world.getAllPlayers().filter((q) => valid(q) && flat(q.location, player.location) < 64
    && (q.id === player.id || !dp(q, `studio:seen_cutscene_${siteId}`, false)));

  switch (siteId) {
    case "ogygia":
      playCutscene("ogygia", { x: 0, y: 65, z: 0 }, [
        { tick: 2,  shotType: "aerial_pan",         anchor: { x: 0, y: 65, z: 0 }, titleKey: "odyssey.site.ogygia", subKey: "odyssey.site.ogygia.sub", sayKey: "odyssey.story.ogygia_intro" },
        { tick: 45, shotType: "wide_establishing",  anchor: { x: -12, y: 65, z: -10 } },
        { tick: 85, shotType: "closeup_dialogue",   anchor: { x: 7, y: 65, z: 5 }, npcType: "studio:calypso", npcAnim: "offer", sayKey: "odyssey.calypso.guide.early" },
      ], 130, audience);
      break;

    case "troy":
      playCutscene("troy", { x: -150, y: 65, z: -260 }, [
        { tick: 2,  shotType: "panoramic_battlefield", anchor: { x: -150, y: 65, z: -275 }, titleKey: "odyssey.site.troy", subKey: "odyssey.site.troy.sub", sayKey: "odyssey.story.troy_intro" },
        { tick: 50, shotType: "low_angle_hero",        anchor: { x: -150, y: 65, z: -260 }, height: 8, npcType: "studio:trojan_horse", npcAnim: "hatch" },
        { tick: 90, shotType: "tracking_shot",         anchor: { x: -150, y: 65, z: -260 } },
      ], 130, audience);
      break;

    case "sparta":
      playCutscene("sparta", { x: -260, y: 65, z: -90 }, [
        { tick: 2,  shotType: "wide_establishing",  anchor: { x: -260, y: 65, z: -90 }, titleKey: "odyssey.site.sparta", subKey: "odyssey.site.sparta.sub", sayKey: "odyssey.story.sparta_intro" },
        { tick: 50, shotType: "over_the_shoulder",  anchor: { x: -260, y: 65, z: -87 }, npcType: "studio:athena", npcAnim: "bless", sayKey: "odyssey.athena.guide.2" },
      ], 100, audience);
      break;

    case "cyclops":
      playCutscene("cyclops", { x: 318, y: 67, z: -150 }, [
        { tick: 2,  shotType: "wide_establishing", anchor: { x: 300, y: 67, z: -150 }, titleKey: "odyssey.site.cyclops", subKey: "odyssey.site.cyclops.sub", sayKey: "odyssey.story.cyclops_intro" },
        { tick: 50, shotType: "low_angle_hero",    anchor: { x: 318, y: 67, z: -150 }, height: 9, npcType: "studio:cyclops", npcAnim: "stomp" },
      ], 105, audience);
      break;

    case "telepylus":
      playCutscene("telepylus", { x: 560, y: 65, z: 60 }, [
        { tick: 2,  shotType: "panoramic_battlefield", anchor: { x: 560, y: 65, z: 60 }, titleKey: "odyssey.site.telepylus", subKey: "odyssey.site.telepylus.sub", sayKey: "odyssey.story.telepylus_intro" },
        { tick: 50, shotType: "closeup_dialogue",      anchor: { x: 560, y: 65, z: 60 }, npcType: "studio:laestrygonian_child", npcAnim: "laugh" },
      ], 100, audience);
      break;

    case "aeaea":
      playCutscene("aeaea", { x: 520, y: 65, z: 364 }, [
        { tick: 2,  shotType: "wide_establishing", anchor: { x: 520, y: 65, z: 374 }, titleKey: "odyssey.site.aeaea", subKey: "odyssey.site.aeaea.sub", sayKey: "odyssey.story.aeaea_intro" },
        { tick: 50, shotType: "closeup_dialogue",  anchor: { x: 520, y: 65, z: 364 }, npcType: "studio:circe", npcAnim: "serve" },
      ], 100, audience);
      break;

    case "hades":
      playCutscene("hades", { x: 260, y: 65, z: 520 }, [
        { tick: 2,  shotType: "wide_establishing", anchor: { x: 260, y: 65, z: 520 }, titleKey: "odyssey.site.hades", subKey: "odyssey.site.hades.sub", sayKey: "odyssey.story.hades_intro" },
        { tick: 50, shotType: "tracking_shot",     anchor: { x: 260, y: 65, z: 520 } },
      ], 95, audience);
      break;

    case "sirens":
      playCutscene("sirens", { x: -40, y: 64, z: 480 }, [
        { tick: 2,  shotType: "aerial_pan",     anchor: { x: -40, y: 64, z: 480 }, titleKey: "odyssey.site.sirens", subKey: "odyssey.site.sirens.sub", sayKey: "odyssey.story.sirens_intro" },
        { tick: 50, shotType: "dynamic_action", anchor: { x: -54, y: 64, z: 474 }, height: 2, npcType: "studio:siren", npcAnim: "sing" },
      ], 100, audience);
      break;

    case "strait":
      playCutscene("strait", { x: -300, y: 65, z: 380 }, [
        { tick: 2,  shotType: "aerial_pan",     anchor: { x: -300, y: 65, z: 380 }, titleKey: "odyssey.site.strait", subKey: "odyssey.site.strait.sub", sayKey: "odyssey.story.strait_intro" },
        { tick: 50, shotType: "low_angle_hero", anchor: { x: -300, y: 65, z: 380 }, height: 9, npcType: "studio:scylla", npcAnim: "lunge" },
      ], 105, audience);
      break;

    case "thrinacia":
      playCutscene("thrinacia", { x: -480, y: 65, z: 130 }, [
        { tick: 2,  shotType: "wide_establishing", anchor: { x: -480, y: 65, z: 146 }, titleKey: "odyssey.site.thrinacia", subKey: "odyssey.site.thrinacia.sub", sayKey: "odyssey.story.thrinacia_intro" },
        { tick: 50, shotType: "tracking_shot",     anchor: { x: -480, y: 65, z: 130 }, npcType: "studio:sun_cattle", npcAnim: "graze" },
      ], 95, audience);
      break;

    case "ithaca":
      // Arrival only: the homecoming finale has its own scene (story_cinematics.js).
      playCutscene("ithaca", { x: -420, y: 65, z: -200 }, [
        { tick: 2,  shotType: "aerial_pan",        anchor: { x: -420, y: 65, z: -218 }, titleKey: "odyssey.site.ithaca", subKey: "odyssey.site.ithaca.sub", sayKey: "odyssey.story.ithaca_intro" },
        { tick: 55, shotType: "low_angle_hero",    anchor: { x: -420, y: 65, z: -212 }, height: 7 },
      ], 110, audience);
      break;

    default:
      break;
  }
}
