// World Expansion & Ancient Greek Architectural Builder.
// Constructs detailed temples, palaces, ports/harbors, ruins, battlefield barricades,
// coastal beacon towers, and secret underground passages at each campaign site when loaded.
import { world } from "@minecraft/server";
import { runCommand, safe } from "../lib/util.js";
import { groundY, loaded } from "../lib/terrain.js";

const SITE_CENTER = {
  ogygia: [0, 0], troy: [-150, -260], sparta: [-260, -90], cyclops: [300, -150], telepylus: [560, 60], aeaea: [520, 360],
  hades: [260, 520], sirens: [-40, 480], strait: [-300, 380], thrinacia: [-480, 130], ithaca: [-420, -200],
};

function fill(dim, x1, y1, z1, x2, y2, z2, blockName) {
  runCommand(dim, `fill ${x1} ${y1} ${z1} ${x2} ${y2} ${z2} ${blockName}`);
}
function setb(dim, x, y, z, blockName) {
  runCommand(dim, `setblock ${x} ${y} ${z} ${blockName}`);
}

/** Build a classic Doric colonnade temple or pavilion at (cx, cy, cz). */
function buildDoricTemple(dim, cx, cy, cz, rx = 6, rz = 8, pillarBlock = "quartz_pillar", floorBlock = "smooth_quartz", roofBlock = "stone_bricks") {
  fill(dim, cx - rx, cy, cz - rz, cx + rx, cy, cz + rz, floorBlock);
  for (let x = cx - rx + 1; x <= cx + rx - 1; x += 3) {
    fill(dim, x, cy + 1, cz - rz + 1, x, cy + 5, cz - rz + 1, pillarBlock);
    fill(dim, x, cy + 1, cz + rz - 1, x, cy + 5, cz + rz - 1, pillarBlock);
  }
  for (let z = cz - rz + 1; z <= cz + rz - 1; z += 3) {
    fill(dim, cx - rx + 1, cy + 1, z, cx - rx + 1, cy + 5, z, pillarBlock);
    fill(dim, cx + rx - 1, cy + 1, z, cx + rx - 1, cy + 5, z, pillarBlock);
  }
  fill(dim, cx - rx, cy + 6, cz - rz, cx + rx, cy + 6, cz + rz, roofBlock);
  fill(dim, cx - rx + 2, cy + 7, cz - rz + 2, cx + rx - 2, cy + 7, cz + rz - 2, floorBlock);
  // Central altar & glowstone braziers
  setb(dim, cx, cy + 1, cz, "quartz_block");
  setb(dim, cx, cy + 2, cz, "glowstone");
  setb(dim, cx - rx + 1, cy + 5, cz - rz + 1, "glowstone");
  setb(dim, cx + rx - 1, cy + 5, cz - rz + 1, "glowstone");
  setb(dim, cx - rx + 1, cy + 5, cz + rz - 1, "glowstone");
  setb(dim, cx + rx - 1, cy + 5, cz + rz - 1, "glowstone");
}

/** Build a wooden harbor pier and coastal beacon extending toward the sea. */
function buildHarborPier(dim, x, y, z, dirX, dirZ, length = 14) {
  for (let i = 0; i <= length; i++) {
    const px = x + dirX * i, pz = z + dirZ * i;
    if (dirX !== 0) {
      fill(dim, px, y, pz - 1, px, y, pz + 1, "oak_planks");
      if (i % 4 === 0) {
        fill(dim, px, y - 3, pz - 1, px, y + 1, pz - 1, "oak_log");
        fill(dim, px, y - 3, pz + 1, px, y + 1, pz + 1, "oak_log");
      }
    } else {
      fill(dim, px - 1, y, pz, px + 1, y, pz, "oak_planks");
      if (i % 4 === 0) {
        fill(dim, px - 1, y - 3, pz, px - 1, y + 1, pz, "oak_log");
        fill(dim, px + 1, y - 3, pz, px + 1, y + 1, pz, "oak_log");
      }
    }
  }
  // Harbor pharos beacon at pier end
  const bx = x + dirX * length, bz = z + dirZ * length;
  fill(dim, bx, y + 1, bz, bx, y + 4, bz, "stone_bricks");
  setb(dim, bx, y + 5, bz, "glowstone");
}

export function ensureSiteArchitecture(siteId) {
  // v3.0: builds again once (new Ogygia and Cyclops piers, Strait beacon on the cliff), and only once the site's
  // chunks are loaded - /fill silently does nothing in unloaded chunks, which used to leave sites half built forever.
  const flag = `odyssey:arch_v30_${siteId}`;
  const dim = world.getDimension("minecraft:overworld");
  const c = SITE_CENTER[siteId];
  try {
    if (world.getDynamicProperty(flag) === true) return;
    if (c && !loaded(dim, { x: c[0], y: 64, z: c[1] })) return;
    world.setDynamicProperty(flag, true);
  } catch { return; }

  safe(`arch.${siteId}`, () => {
    switch (siteId) {
      case "ogygia":
        // Calypso's Sanctuary Pavilion, lotus pools, and harbor pier
        buildDoricTemple(dim, -12, 64, -10, 5, 5, "quartz_pillar", "smooth_quartz", "quartz_block");
        buildHarborPier(dim, 0, 64, -18, 0, -1, 21); // reaches open water (shore ends near z=-37)
        // Secret grotto passage beneath Ogygia
        fill(dim, -14, 60, -12, -10, 62, -8, "air");
        setb(dim, -12, 60, -10, "glowstone");
        break;

      case "troy":
        // Besieged Trojan Citadel Wall, Scaean Gate, Athena's Shrine, and Harbor
        fill(dim, -172, 64, -278, -128, 71, -278, "stone_bricks");
        fill(dim, -153, 64, -278, -147, 68, -278, "air"); // Breached Scaean Gate
        fill(dim, -174, 64, -280, -170, 74, -276, "stone_bricks"); // West Bastion Tower
        fill(dim, -130, 64, -280, -126, 74, -276, "stone_bricks"); // East Bastion Tower
        setb(dim, -172, 75, -278, "glowstone");
        setb(dim, -128, 75, -278, "glowstone");
        buildDoricTemple(dim, -150, 64, -290, 6, 6, "quartz_pillar", "stone_bricks", "smooth_stone");
        buildHarborPier(dim, -150, 64, -242, 0, 1, 14);
        break;

      case "sparta":
        // New Island: Sparta & Mycenae (Menelaus & Helen's Peloponnese Citadel where Telemachus seeks Odysseus)
        fill(dim, -282, 62, -112, -238, 64, -68, "stone");
        fill(dim, -278, 64, -108, -242, 64, -72, "grass_block");
        buildDoricTemple(dim, -260, 64, -90, 8, 9, "quartz_pillar", "smooth_quartz", "stone_bricks");
        buildHarborPier(dim, -260, 64, -72, 0, 1, 12);
        break;

      case "cyclops":
        // Expanded sheepfold fence, shepherd's hearth, and cliffside escape path
        buildHarborPier(dim, 373, 63, -150, 1, 0, 12); // east shore; the old west pier ran into the mountain
        fill(dim, 310, 66, -158, 326, 66, -142, "grass_block");
        setb(dim, 314, 67, -154, "glowstone");
        break;

      case "telepylus":
        // Laestrygonian Monolith Gate, Watchtowers, and fjord dock
        fill(dim, 542, 64, 42, 546, 74, 46, "cobblestone");
        fill(dim, 574, 64, 42, 578, 74, 46, "cobblestone");
        setb(dim, 544, 75, 44, "glowstone");
        setb(dim, 576, 75, 44, "glowstone");
        buildHarborPier(dim, 560, 64, 38, 0, -1, 14);
        break;

      case "aeaea":
        // Circe's Findlater Cliffside Stronghold, banquet colonnade, and secret herb cellar
        buildDoricTemple(dim, 520, 64, 374, 7, 7, "stone_bricks", "mossy_stone_bricks", "stone_bricks");
        buildHarborPier(dim, 520, 64, 340, 0, -1, 14);
        // Secret herb cellar beneath Circe's hall
        fill(dim, 517, 59, 371, 523, 62, 377, "air");
        setb(dim, 520, 59, 374, "glowstone");
        break;

      case "hades":
        // Necromanteion Black-Sand Altar & Oceanus Pier
        fill(dim, 250, 63, 510, 270, 64, 530, "black_concrete_powder");
        fill(dim, 252, 64, 512, 268, 64, 528, "soul_soil");
        fill(dim, 252, 65, 512, 252, 70, 512, "tuff");
        fill(dim, 268, 65, 512, 268, 70, 512, "tuff");
        fill(dim, 252, 65, 528, 252, 70, 528, "tuff");
        fill(dim, 268, 65, 528, 268, 70, 528, "tuff");
        setb(dim, 252, 71, 512, "glowstone");
        setb(dim, 268, 71, 512, "glowstone");
        buildHarborPier(dim, 260, 64, 502, 0, -1, 12);
        break;

      case "sirens":
        // Shipwrecked trireme ribs and sea stacks
        fill(dim, -48, 63, 472, -32, 64, 474, "dark_oak_log");
        for (let x = -46; x <= -34; x += 3) {
          fill(dim, x, 64, 470, x, 67, 470, "oak_fence");
          fill(dim, x, 64, 476, x, 67, 476, "oak_fence");
        }
        break;

      case "strait":
        // Strait navigation pharos beacons on either side of the channel
        {
          // West beacon stands on the Scylla cliff (ground ~y=110 here), not buried inside it.
          const gy = groundY(dim, -317, 366) ?? 63;
          fill(dim, -318, gy + 1, 365, -316, gy + 9, 367, "stone_bricks");
          setb(dim, -317, gy + 10, 366, "glowstone");
        }
        fill(dim, -284, 64, 395, -282, 72, 397, "stone_bricks");
        setb(dim, -283, 73, 396, "glowstone");
        break;

      case "thrinacia":
        // Temple of Helios/Apollo & sacred pasture
        buildDoricTemple(dim, -480, 64, 146, 6, 6, "quartz_pillar", "smooth_quartz", "hay_block");
        buildHarborPier(dim, -480, 64, 110, 0, -1, 14);
        break;

      case "ithaca":
        // Royal Palace of Odysseus, Great Hall of the Suitors, 12 Axe-Trial Pillars, and Royal Harbor
        buildDoricTemple(dim, -420, 64, -218, 9, 11, "quartz_pillar", "smooth_quartz", "stone_bricks");
        // 12 Axe-Trial Pillars along the Great Hall
        for (let i = 0; i < 6; i++) {
          setb(dim, -423, 65, -225 + i * 2, "oak_fence");
          setb(dim, -417, 65, -225 + i * 2, "oak_fence");
        }
        buildHarborPier(dim, -420, 64, -182, 0, 1, 16);
        break;

      default:
        break;
    }
    // Place physical Discovery Chest for this site
    const chests = {
      ogygia:    [0, 65, -20],
      troy:      [-150, 65, -288],
      sparta:    [-260, 65, -88],
      cyclops:   [314, 67, -153],
      telepylus: [544, 65, 45],
      aeaea:     [520, 60, 373],
      hades:     [260, 65, 514],
      sirens:    [-40, 65, 473],
      strait:    [-317, 65, 368],
      thrinacia: [-480, 65, 144],
      ithaca:    [-420, 65, -216],
    };
    const cpos = chests[siteId];
    if (cpos) {
      if (siteId === "strait") cpos[1] = (groundY(dim, cpos[0], cpos[2]) ?? 64) + 1;   // on the cliff top
      setb(dim, cpos[0], cpos[1], cpos[2], "chest");
    }
  });
}
