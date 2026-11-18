// Centralised campaign configuration.
//
// Every coordinate below was read from the world's own LevelDB (the db/ folder of The_Odyssey_v2.2.0.mcworld) with
// odyssey/tools/world_probe.py: the block at y-1 is solid, safe ground and y / y+1 are air. Sparta is the exception:
// the shipped world has open sea there and architect.js raises the Spartan island when a player first arrives, so its
// points are re-checked at runtime (see `verified: "runtime"`). The runtime teleporter re-verifies every point anyway
// and falls back to the nearest safe spot, so a later edit to the map cannot strand a player inside a wall.

/** @typedef {{x:number,y:number,z:number,yaw?:number,label:string,verified:string}} Point */

export const POINTS = {
  // Ogygia: Calypso's island. World spawn (level.dat SpawnX/Y/Z = 0,65,3) sits on the stone-brick court.
  ogygia_court:     { x: 0.5,    y: 65, z: 3.5,    yaw: 180, label: "odyssey.dest.ogygia_court",   verified: "db:stone_bricks" },
  ogygia_calypso:   { x: 7.5,    y: 65, z: 5.5,    label: "odyssey.dest.ogygia_calypso",            verified: "db:grass_block" },
  ogygia_harbor:    { x: 1.5,    y: 65, z: -18.5,  yaw: 180, label: "odyssey.dest.ogygia_harbor",  verified: "db:grass_block" },
  ogygia_temple:    { x: -11.5,  y: 65, z: -3.5,   label: "odyssey.dest.ogygia_temple",             verified: "db:grass_block" },
  // Ithaca: the island square, the palace hall (inside the temple, floor smooth_quartz at y=64) and the harbour.
  ithaca_square:    { x: -419.5, y: 65, z: -199.5, yaw: 0,   label: "odyssey.dest.ithaca_square",  verified: "db:grass_block" },
  ithaca_palace:    { x: -419.5, y: 65, z: -211.5, label: "odyssey.dest.ithaca_palace",             verified: "db:smooth_quartz (interior)" },
  ithaca_harbor:    { x: -419.5, y: 65, z: -185.5, label: "odyssey.dest.ithaca_harbor",             verified: "db:grass_block" },
  ithaca_eumaeus:   { x: -403.5, y: 65, z: -195.5, yaw: 90,  label: "odyssey.dest.ithaca_eumaeus", verified: "db:grass_block" },
  ithaca_mentor:    { x: -423.5, y: 65, z: -197.5, label: "odyssey.dest.ithaca_mentor",             verified: "db:grass_block" },
  // Voyage sites.
  troy_beach:       { x: -149.5, y: 65, z: -243.5, label: "odyssey.dest.troy_beach",                verified: "db:sand" },
  troy_horse:       { x: -149.5, y: 65, z: -261.5, label: "odyssey.dest.troy_horse",                verified: "db:oak_planks" },
  sparta_temple:    { x: -259.5, y: 65, z: -89.5,  label: "odyssey.dest.sparta_temple",             verified: "runtime" },
  cyclops_landing:  { x: 370.5,  y: 66, z: -149.5, label: "odyssey.dest.cyclops_landing",           verified: "db:grass_block" },
  cyclops_cave:     { x: 318.5,  y: 67, z: -149.5, label: "odyssey.dest.cyclops_cave",              verified: "db:grass_block" },
  telepylus_dock:   { x: 560.5,  y: 65, z: 42.5,   label: "odyssey.dest.telepylus_dock",            verified: "db:podzol" },
  telepylus_gate:   { x: 560.5,  y: 65, z: 60.5,   label: "odyssey.dest.telepylus_gate",            verified: "db:mossy_stone_bricks" },
  aeaea_shore:      { x: 520.5,  y: 65, z: 344.5,  label: "odyssey.dest.aeaea_shore",               verified: "db:grass_block" },
  aeaea_hall:       { x: 520.5,  y: 65, z: 370.5,  label: "odyssey.dest.aeaea_hall",                verified: "db:grass_block" },
  hades_shore:      { x: 260.5,  y: 65, z: 504.5,  label: "odyssey.dest.hades_shore",               verified: "db:black_concrete_powder" },
  hades_altar:      { x: 260.5,  y: 65, z: 514.5,  label: "odyssey.dest.hades_altar",               verified: "db:black_concrete_powder" },
  sirens_rocks:     { x: -44.5,  y: 64, z: 471.5,  label: "odyssey.dest.sirens_rocks",              verified: "db:stone" },
  strait_cliff:     { x: -295.5, y: 93, z: 380.5,  label: "odyssey.dest.strait_cliff",              verified: "db:stone" },
  thrinacia_shore:  { x: -479.5, y: 65, z: 114.5,  label: "odyssey.dest.thrinacia_shore",           verified: "db:grass_block" },
  thrinacia_temple: { x: -479.5, y: 65, z: 140.5,  label: "odyssey.dest.thrinacia_temple",          verified: "db:grass_block" },
};

/** Respawn / checkpoint point for each campaign site. */
export const SITE_POINTS = {
  ogygia: "ogygia_court", troy: "troy_beach", sparta: "sparta_temple", cyclops: "cyclops_landing", telepylus: "telepylus_dock",
  aeaea: "aeaea_shore", hades: "hades_shore", sirens: "sirens_rocks", strait: "strait_cliff", thrinacia: "thrinacia_shore",
  ithaca: "ithaca_square",
};

/** Where each role begins the campaign. The film opens on Ithaca with Telemachus, then finds Odysseus on Ogygia. */
export const START_POSITIONS = {
  odysseus:   "ogygia_court",
  telemachus: "ithaca_square",
  companion:  "ogygia_harbor",
  eumaeus:    "ithaca_eumaeus",
};

/** Playable roles. `exclusive` roles can be held by one player at a time. */
export const ROLES = {
  odysseus:   { id: "odysseus",   exclusive: true,  primary: true,  portrait: "textures/ui/odyssey/portrait_odysseus",   group: "ogygia" },
  telemachus: { id: "telemachus", exclusive: true,  primary: true,  portrait: "textures/ui/odyssey/portrait_telemachus", group: "ithaca" },
  companion:  { id: "companion",  exclusive: false, primary: false, portrait: "textures/ui/odyssey/portrait_companion",  group: "ogygia" },
  eumaeus:    { id: "eumaeus",    exclusive: true,  primary: false, portrait: "textures/ui/odyssey/portrait_eumaeus",    group: "ithaca" },
};
export const ROLE_ORDER = ["odysseus", "telemachus", "companion", "eumaeus"];

/** Starting equipment per role (the rest is earned through the campaign; see world/progression.js). */
export const START_KITS = {
  // Every role carries a small boat: the galley is the main ship, but nobody can ever be stranded on an island.
  odysseus:   [["studio:odyssey_astrolabe", 1], ["studio:driftwood_club", 1], ["minecraft:bread", 3], ["minecraft:oak_boat", 1]],
  telemachus: [["studio:odyssey_astrolabe", 1], ["minecraft:wooden_sword", 1], ["minecraft:bread", 4], ["minecraft:leather_chestplate", 1], ["minecraft:oak_boat", 1]],
  companion:  [["studio:odyssey_astrolabe", 1], ["studio:driftwood_club", 1], ["studio:ship_repair_kit", 1], ["minecraft:bread", 3], ["minecraft:oak_boat", 1]],
  eumaeus:    [["studio:odyssey_astrolabe", 1], ["minecraft:wooden_sword", 1], ["minecraft:cooked_porkchop", 4], ["minecraft:oak_boat", 1]],
};

/** Timings (ticks). */
export const TIMING = {
  selectionTimeout: 20 * 120,  // a player who never answers is auto-assigned so nobody is locked out
  fadeIn: 1.0, fadeHold: 4.0, fadeOut: 1.2,   // seconds, /camera fade
  teleportAtTick: 26,          // > fadeIn: the screen is fully black before anyone moves
  verifyDelay: 8,
  maxTeleportTries: 5,
};
