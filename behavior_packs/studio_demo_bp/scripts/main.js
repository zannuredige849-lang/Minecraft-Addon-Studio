// Studio Demo — Behavior Pack script entry point.
// API: @minecraft/server 2.11.0 (see studio/config/studio.json).
import { world } from "@minecraft/server";

const TAG = "[studio_demo]";

world.afterEvents.playerSpawn.subscribe((event) => {
  if (event.initialSpawn) {
    world.sendMessage(`${TAG} Welcome, ${event.player.name}!`);
  }
});
