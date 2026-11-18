// Dynamic Music & Ambience Director.
// Transitions smoothly between Exploration, Sailing, Combat, Boss, Emotional, and Cutscene
// themes without overlapping tracks, and plays environmental ocean/battlefield ambience.
import { world } from "@minecraft/server";
import { dp, flat, isBoat, near, now, ridingOn, runCommand, safe, setDp, valid } from "../lib/util.js";
import { hear } from "../lib/fx.js";

const TRACK_DURATION_TICKS = {
  "odyssey.music.exploration": 240,
  "odyssey.music.combat": 200,
  "odyssey.music.boss": 200,
  "odyssey.music.emotional": 220,
  "odyssey.music.sailing": 200,
  "odyssey.music.cinematic": 120,
  "odyssey.music.victory": 140,
};

const BOSS_TYPES = new Set(["studio:cyclops", "studio:scylla", "studio:charybdis"]);
const COMBAT_TYPES = new Set(["studio:laestrygonian", "studio:shade", "studio:siren"]);

export function stopPlayerMusic(p) {
  for (const k of Object.keys(TRACK_DURATION_TICKS)) {
    try {
      if (typeof p.runCommandAsync === "function") p.runCommandAsync(`stopsound @s ${k}`);
      else p.runCommand?.(`stopsound @s ${k}`);
    } catch { }
  }
}

export function playTheme(p, themeId, force = false) {
  if (!valid(p)) return;
  const curTheme = dp(p, "studio:music_theme", "");
  const until = dp(p, "studio:music_until", 0);
  if (!force && curTheme === themeId && now() < until) return;
  if (curTheme && curTheme !== themeId) {
    stopPlayerMusic(p);
  }
  const dur = TRACK_DURATION_TICKS[themeId] ?? 200;
  setDp(p, "studio:music_theme", themeId);
  setDp(p, "studio:music_until", now() + dur);
  hear(p, themeId, undefined, 0.7, 1.0);
}

export function tickMusic(pausedOrCutscene = false) {
  if (pausedOrCutscene) return;
  for (const p of world.getAllPlayers()) {
    safe("music", () => {
      const dim = p.dimension, loc = p.location;
      const nearby = near(dim, loc, 32);

      // Determine situational theme priority: Boss > Combat > Sailing > Emotional (Ogygia/Ithaca) > Exploration
      let desired = "odyssey.music.exploration";
      if (nearby.some((e) => BOSS_TYPES.has(e.typeId))) {
        desired = "odyssey.music.boss";
      } else if (nearby.some((e) => COMBAT_TYPES.has(e.typeId))) {
        desired = "odyssey.music.combat";
      } else if (isBoat(ridingOn(p))) {
        desired = "odyssey.music.sailing";
        if (now() % 160 === 0) hear(p, "odyssey.ambience.ocean", undefined, 0.45, 1.0);
      } else if (flat(loc, { x: 0, z: 0 }) < 45 || flat(loc, { x: -420, z: -200 }) < 55) {
        desired = "odyssey.music.emotional";
      } else if (flat(loc, { x: -150, z: -260 }) < 45) {
        if (now() % 160 === 0) hear(p, "odyssey.ambience.battlefield", undefined, 0.5, 1.0);
      }

      playTheme(p, desired, false);
    });
  }
}
