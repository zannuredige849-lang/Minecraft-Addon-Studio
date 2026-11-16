// Template: Behavior Pack script entry (scripts/main.js).
// Declare "@minecraft/server" 2.11.0 in the BP manifest dependencies before using this.
import { world } from "@minecraft/server";

world.afterEvents.playerSpawn.subscribe((event) => {
  if (event.initialSpawn) {
    world.sendMessage(`Welcome, ${event.player.name}!`);
  }
});
