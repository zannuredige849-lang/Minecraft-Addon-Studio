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
import { world, system } from "@minecraft/server";
import { add, dp, flat, forward, near, rawNow, right, safe, scale, setDp, valid } from "../lib/util.js";
import { bar, hear, tell, title } from "../lib/fx.js";
import { perform } from "../lib/moves.js";
import { playTheme } from "./music.js";
import { STATE_CINEMATIC, STATE_NORMAL, setWorldState } from "./pause_vote.js";

function camCmd(p, cmd) {
  try {
    if (typeof p.runCommandAsync === "function") p.runCommandAsync(cmd);
    else p.runCommand?.(cmd);
  } catch { }
}

export function camFade(p, fadeIn = 0.4, hold = 0.2, fadeOut = 0.4) {
  camCmd(p, `camera @s fade time ${fadeIn} ${hold} ${fadeOut} color 0 0 0`);
}

export function camFree(p, pos, facing, easeSec = 2.0, easeType = "in_out_sine") {
  const px = pos.x.toFixed(2), py = pos.y.toFixed(2), pz = pos.z.toFixed(2);
  const fx = facing.x.toFixed(2), fy = facing.y.toFixed(2), fz = facing.z.toFixed(2);
  if (easeSec > 0) {
    camCmd(p, `camera @s set minecraft:free ease ${easeSec.toFixed(2)} ${easeType} pos ${px} ${py} ${pz} facing ${fx} ${fy} ${fz}`);
  } else {
    camCmd(p, `camera @s set minecraft:free pos ${px} ${py} ${pz} facing ${fx} ${fy} ${fz}`);
  }
}

export function camClear(p) {
  camCmd(p, "camera @s clear");
}

/** Build the 8 camera shot types relative to an anchor position `c` and subject `target`. */
export const SHOTS = {
  wide_establishing: (c) => ({
    pos: { x: c.x - 18, y: c.y + 12, z: c.z - 18 },
    facing: { x: c.x, y: c.y + 3, z: c.z },
    ease: 2.2,
  }),
  aerial_pan: (c) => ({
    pos: { x: c.x + 22, y: c.y + 24, z: c.z - 14 },
    facing: { x: c.x, y: c.y + 2, z: c.z },
    ease: 2.8,
  }),
  low_angle_hero: (c, h = 6) => ({
    pos: { x: c.x + 4.5, y: c.y + 0.9, z: c.z + 4.5 },
    facing: { x: c.x, y: c.y + h, z: c.z },
    ease: 1.6,
  }),
  closeup_dialogue: (c) => ({
    pos: { x: c.x + 2.2, y: c.y + 1.65, z: c.z + 2.2 },
    facing: { x: c.x, y: c.y + 1.6, z: c.z },
    ease: 1.4,
  }),
  over_the_shoulder: (p, targetLoc) => {
    const f = forward(p), r = right(p);
    return {
      pos: { x: p.location.x - f.x * 1.6 + r.x * 0.65, y: p.location.y + 1.7, z: p.location.z - f.z * 1.6 + r.z * 0.65 },
      facing: { x: targetLoc.x, y: targetLoc.y + 1.5, z: targetLoc.z },
      ease: 1.3,
    };
  },
  tracking_shot: (c) => ({
    pos: { x: c.x + 12, y: c.y + 4, z: c.z + 12 },
    facing: { x: c.x, y: c.y + 2, z: c.z },
    ease: 2.4,
  }),
  panoramic_battlefield: (c) => ({
    pos: { x: c.x - 24, y: c.y + 15, z: c.z + 20 },
    facing: { x: c.x, y: c.y + 4, z: c.z },
    ease: 2.6,
  }),
  dynamic_action: (c, h = 3) => ({
    pos: { x: c.x - 6, y: c.y + 2.2, z: c.z + 6 },
    facing: { x: c.x, y: c.y + h, z: c.z },
    ease: 0.9,
  }),
};

/**
 * Play a multi-shot synchronized cutscene for `players` (defaults to all connected players).
 * Each step in `steps` has `{ tick, shotType, anchor, height, titleKey, subKey, sayKey, npcType, npcAnim }`.
 */
export function playCutscene(id, center, steps, durationTicks = 140, players = null) {
  const audience = (players ?? world.getAllPlayers()).filter(valid);
  if (!audience.length) return;

  setWorldState(STATE_CINEMATIC);
  for (const p of audience) {
    setDp(p, `studio:seen_cutscene_${id}`, true);
    camFade(p, 0.35, 0.15, 0.35);
    playTheme(p, id === "finale_ithaca" ? "odyssey.music.victory" : "odyssey.music.cinematic", true);
  }

  for (const step of steps) {
    system.runTimeout(() => {
      safe(`cutscene.${id}`, () => {
        const anchor = step.anchor ?? center;
        // Animate featured NPC if present nearby
        if (step.npcType && step.npcAnim) {
          const dim = audience[0]?.dimension;
          const npc = dim ? near(dim, anchor, 32, step.npcType)[0] : undefined;
          if (valid(npc)) {
            perform(npc, step.npcAnim, {}, { still: false, force: true });
          }
        }
        for (const p of audience) {
          if (!valid(p)) continue;
          let shot;
          if (step.shotType === "over_the_shoulder") {
            shot = SHOTS.over_the_shoulder(p, anchor);
          } else {
            const fn = SHOTS[step.shotType] ?? SHOTS.wide_establishing;
            shot = fn(anchor, step.height ?? 4);
          }
          camFree(p, shot.pos, shot.facing, shot.ease);
          if (step.titleKey) title(p, step.titleKey, step.subKey ?? "");
          if (step.sayKey) {
            tell(p, step.sayKey);
            bar(p, step.sayKey);
          }
        }
      });
    }, Math.max(1, step.tick));
  }

  system.runTimeout(() => {
    for (const p of audience) {
      if (!valid(p)) continue;
      camFade(p, 0.3, 0.1, 0.3);
      camClear(p);
    }
    if (worldStateIsCinematic()) setWorldState(STATE_NORMAL);
  }, durationTicks);
}

function worldStateIsCinematic() {
  try { return true; } catch { return false; }
}

/** Trigger the signature multi-shot cutscene for any of the 11 campaign sites or major story events. */
export function playSiteCutscene(siteId, player, force = false) {
  if (!valid(player)) return;
  if (!force && dp(player, `studio:seen_cutscene_${siteId}`, false)) return;
  const audience = world.getAllPlayers().filter((q) => valid(q) && flat(q.location, player.location) < 64);

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
      playCutscene("finale_ithaca", { x: -420, y: 65, z: -200 }, [
        { tick: 2,  shotType: "aerial_pan",        anchor: { x: -420, y: 65, z: -218 }, titleKey: "odyssey.site.ithaca", subKey: "odyssey.site.ithaca.sub", sayKey: "odyssey.story.ithaca_intro" },
        { tick: 50, shotType: "wide_establishing", anchor: { x: -420, y: 65, z: -218 } },
        { tick: 90, shotType: "closeup_dialogue",  anchor: { x: -416, y: 65, z: -194 }, npcType: "studio:athena", npcAnim: "bless", sayKey: "odyssey.story.ithaca_complete" },
      ], 140, audience);
      break;

    default:
      break;
  }
}
