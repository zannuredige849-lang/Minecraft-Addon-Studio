// The Odyssey (2026) v2.2.0 — Progression-Based Item Unlocking, 5-Tier Copper Equipment,
// Role-Specific vs. Shared Rewards, Anti-Bypass Prerequisite Locks, Unclaimed Reward Vault,
// Discovery Chests, and Lost Quest-Item Recovery.
import { world, ItemStack } from "@minecraft/server";
import {
  add, dirTo, dp, effect, flat, forward, heldItem, hurt, isPlayer, near,
  now, playersNear, push, ready, runCommand, safe, scale, setDp, valid, wait,
} from "../lib/util.js";
import { bar, burst, hear, particle, sound, tell } from "../lib/fx.js";

// Complete 21-Item Progression Registry across 5 Equipment Tiers & 9 Chapters
export const PROGRESSION_ITEMS = {
  // ======================= TIER 1: STARTING & CASTAWAY GEAR (CH. I — OGYGIA) =======================
  "studio:odyssey_astrolabe": {
    id: "studio:odyssey_astrolabe",
    tier: 1,
    chapter: 1,
    category: "quest_tool",
    role: "both",
    unique: true,
    essential: true,
    maxStack: 1,
    unlockFlag: "studio:unlock_astrolabe",
    nameKey: "item.studio:odyssey_astrolabe.name",
  },
  "studio:driftwood_club": {
    id: "studio:driftwood_club",
    tier: 1,
    chapter: 1,
    category: "weapon",
    role: "both",
    unique: false,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_driftwood_club",
    nameKey: "item.studio:driftwood_club.name",
  },
  "studio:lotus_flower": {
    id: "studio:lotus_flower",
    tier: 1,
    chapter: 1,
    category: "consumable",
    role: "both",
    unique: false,
    essential: false,
    maxStack: 8,
    unlockFlag: "studio:unlock_lotus_flower",
    nameKey: "item.studio:lotus_flower.name",
  },
  "studio:ship_helm_horn": {
    id: "studio:ship_helm_horn",
    tier: 1,
    chapter: 1,
    category: "quest_tool",
    role: "both",
    unique: true,
    essential: true,
    maxStack: 1,
    unlockFlag: "studio:unlock_ship_horn",
    nameKey: "item.studio:ship_helm_horn.name",
  },
  "studio:ship_repair_kit": {
    id: "studio:ship_repair_kit",
    tier: 1,
    chapter: 1,
    category: "tool",
    role: "both",
    unique: false,
    essential: false,
    maxStack: 16,
    unlockFlag: "studio:unlock_ship_repair_kit",
    nameKey: "item.studio:ship_repair_kit.name",
  },

  // ======================= TIER 2: EARLY-GAME COPPER EQUIPMENT (CH. II — TROY & SPARTA) =======================
  "studio:copper_xiphos": {
    id: "studio:copper_xiphos",
    tier: 2,
    chapter: 2,
    category: "weapon",
    role: "odysseus",
    unique: true,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_copper_xiphos",
    nameKey: "item.studio:copper_xiphos.name",
  },
  "studio:copper_dory": {
    id: "studio:copper_dory",
    tier: 2,
    chapter: 2,
    category: "weapon",
    role: "telemachus",
    unique: true,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_copper_dory",
    nameKey: "item.studio:copper_dory.name",
  },
  "studio:copper_hoplon": {
    id: "studio:copper_hoplon",
    tier: 2,
    chapter: 2,
    category: "shield",
    role: "both",
    unique: true,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_copper_hoplon",
    nameKey: "item.studio:copper_hoplon.name",
  },
  "studio:copper_cuirass": {
    id: "studio:copper_cuirass",
    tier: 2,
    chapter: 2,
    category: "armor",
    role: "both",
    unique: true,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_copper_cuirass",
    nameKey: "item.studio:copper_cuirass.name",
  },

  // ======================= TIER 3: MID-GAME SPECIALIZED GEAR (CH. III–V — CYCLOPS, TELEPYLUS, AEAEA) =======================
  "studio:burning_stake": {
    id: "studio:burning_stake",
    tier: 3,
    chapter: 3,
    category: "quest_weapon",
    role: "both",
    unique: true,
    essential: true,
    maxStack: 1,
    unlockFlag: "studio:unlock_burning_stake",
    nameKey: "item.studio:burning_stake.name",
  },
  "studio:copper_helm": {
    id: "studio:copper_helm",
    tier: 3,
    chapter: 3,
    category: "armor",
    role: "both",
    unique: true,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_copper_helm",
    nameKey: "item.studio:copper_helm.name",
  },
  "studio:laestrygonian_cleaver": {
    id: "studio:laestrygonian_cleaver",
    tier: 3,
    chapter: 4,
    category: "weapon",
    role: "odysseus",
    unique: true,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_laestrygonian_cleaver",
    nameKey: "item.studio:laestrygonian_cleaver.name",
  },
  "studio:moly_herb": {
    id: "studio:moly_herb",
    tier: 3,
    chapter: 5,
    category: "quest_consumable",
    role: "both",
    unique: false,
    essential: true,
    maxStack: 4,
    unlockFlag: "studio:unlock_moly_herb",
    nameKey: "item.studio:moly_herb.name",
  },
  "studio:circe_stew": {
    id: "studio:circe_stew",
    tier: 3,
    chapter: 5,
    category: "consumable",
    role: "both",
    unique: false,
    essential: false,
    maxStack: 4,
    unlockFlag: "studio:unlock_circe_stew",
    nameKey: "item.studio:circe_stew.name",
  },

  // ======================= TIER 4: LATE-GAME MYTHIC & RITUAL GEAR (CH. VI–VIII — HADES, SIRENS, STRAIT, THRINACIA) =======================
  "studio:sacrificial_copper_knife": {
    id: "studio:sacrificial_copper_knife",
    tier: 4,
    chapter: 5,
    category: "quest_weapon",
    role: "both",
    unique: true,
    essential: true,
    maxStack: 1,
    unlockFlag: "studio:unlock_sacrificial_knife",
    nameKey: "item.studio:sacrificial_copper_knife.name",
  },
  "studio:tiresias_staff": {
    id: "studio:tiresias_staff",
    tier: 4,
    chapter: 6,
    category: "weapon",
    role: "telemachus",
    unique: true,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_tiresias_staff",
    nameKey: "item.studio:tiresias_staff.name",
  },
  "studio:beeswax": {
    id: "studio:beeswax",
    tier: 4,
    chapter: 6,
    category: "quest_consumable",
    role: "both",
    unique: false,
    essential: false,
    maxStack: 16,
    unlockFlag: "studio:unlock_beeswax",
    nameKey: "item.studio:beeswax.name",
  },
  "studio:aegis_copper_plate": {
    id: "studio:aegis_copper_plate",
    tier: 4,
    chapter: 8,
    category: "armor",
    role: "odysseus",
    unique: true,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_aegis_plate",
    nameKey: "item.studio:aegis_copper_plate.name",
  },
  "studio:apollo_sun_talisman": {
    id: "studio:apollo_sun_talisman",
    tier: 4,
    chapter: 8,
    category: "relic",
    role: "both",
    unique: true,
    essential: false,
    maxStack: 1,
    unlockFlag: "studio:unlock_apollo_talisman",
    nameKey: "item.studio:apollo_sun_talisman.name",
  },

  // ======================= TIER 5: FINAL CHAPTER MASTERWORKS (CH. IX — ITHACA) =======================
  "studio:royal_bow_of_odysseus": {
    id: "studio:royal_bow_of_odysseus",
    tier: 5,
    chapter: 9,
    category: "masterwork_weapon",
    role: "odysseus",
    unique: true,
    essential: true,
    maxStack: 1,
    unlockFlag: "studio:unlock_royal_bow",
    nameKey: "item.studio:royal_bow_of_odysseus.name",
  },
  "studio:spear_of_telemachus": {
    id: "studio:spear_of_telemachus",
    tier: 5,
    chapter: 9,
    category: "masterwork_weapon",
    role: "telemachus",
    unique: true,
    essential: true,
    maxStack: 1,
    unlockFlag: "studio:unlock_spear_telemachus",
    nameKey: "item.studio:spear_of_telemachus.name",
  },
};

// In-world Discovery Chests placed by architect.js across all 11 campaign locations
export const DISCOVERY_CHESTS = [
  {
    id: "chest_ogygia_harbor",
    site: "ogygia",
    x: 0, y: 65, z: -20,
    minChapter: 1,
    rewards: [
      { itemId: "studio:ship_helm_horn", amount: 1, role: "both", uniqueKey: "chest_horn" },
      { itemId: "minecraft:copper_ingot", amount: 4, role: "both", uniqueKey: "chest_ogygia_copper" },
    ],
    msgKey: "odyssey.prog.chest.ogygia",
  },
  {
    id: "chest_troy_athena",
    site: "troy",
    x: -150, y: 65, z: -288,
    minChapter: 2,
    rewards: [
      { itemId: "studio:copper_xiphos", amount: 1, role: "odysseus", uniqueKey: "troy_xiphos" },
      { itemId: "studio:copper_hoplon", amount: 1, role: "both", uniqueKey: "troy_hoplon" },
      { itemId: "minecraft:copper_ingot", amount: 6, role: "both", uniqueKey: "troy_copper" },
    ],
    msgKey: "odyssey.prog.chest.troy",
  },
  {
    id: "chest_sparta_menelaus",
    site: "sparta",
    x: -260, y: 65, z: -88,
    minChapter: 2,
    rewards: [
      { itemId: "studio:copper_dory", amount: 1, role: "telemachus", uniqueKey: "sparta_dory" },
      { itemId: "studio:copper_cuirass", amount: 1, role: "both", uniqueKey: "sparta_cuirass" },
      { itemId: "minecraft:copper_ingot", amount: 6, role: "both", uniqueKey: "sparta_copper" },
    ],
    msgKey: "odyssey.prog.chest.sparta",
  },
  {
    id: "chest_cyclops_hearth",
    site: "cyclops",
    x: 314, y: 67, z: -153,
    minChapter: 3,
    rewards: [
      { itemId: "studio:burning_stake", amount: 1, role: "both", uniqueKey: "cyclops_stake" },
      { itemId: "studio:copper_helm", amount: 1, role: "both", uniqueKey: "cyclops_helm" },
    ],
    msgKey: "odyssey.prog.chest.cyclops",
  },
  {
    id: "chest_telepylus_tower",
    site: "telepylus",
    x: 544, y: 65, z: 45,
    minChapter: 4,
    rewards: [
      { itemId: "studio:laestrygonian_cleaver", amount: 1, role: "odysseus", uniqueKey: "telepylus_cleaver" },
      { itemId: "studio:ship_repair_kit", amount: 2, role: "both", uniqueKey: "telepylus_repair" },
    ],
    msgKey: "odyssey.prog.chest.telepylus",
  },
  {
    id: "chest_aeaea_cellar",
    site: "aeaea",
    x: 520, y: 60, z: 373,
    minChapter: 5,
    rewards: [
      { itemId: "studio:moly_herb", amount: 2, role: "both", uniqueKey: "aeaea_moly" },
    ],
    msgKey: "odyssey.prog.chest.aeaea",
  },
  {
    id: "chest_hades_altar",
    site: "hades",
    x: 260, y: 65, z: 514,
    minChapter: 6,
    rewards: [
      { itemId: "studio:beeswax", amount: 6, role: "both", uniqueKey: "hades_beeswax" },
    ],
    msgKey: "odyssey.prog.chest.hades",
  },
  {
    id: "chest_sirens_wreck",
    site: "sirens",
    x: -40, y: 65, z: 473,
    minChapter: 7,
    rewards: [
      { itemId: "studio:beeswax", amount: 4, role: "both", uniqueKey: "sirens_beeswax" },
      { itemId: "studio:ship_repair_kit", amount: 2, role: "both", uniqueKey: "sirens_repair" },
    ],
    msgKey: "odyssey.prog.chest.sirens",
  },
  {
    id: "chest_strait_pharos",
    site: "strait",
    x: -317, y: 65, z: 368,
    minChapter: 8,
    rewards: [
      { itemId: "studio:aegis_copper_plate", amount: 1, role: "odysseus", uniqueKey: "strait_aegis" },
    ],
    msgKey: "odyssey.prog.chest.strait",
  },
  {
    id: "chest_thrinacia_helios",
    site: "thrinacia",
    x: -480, y: 65, z: 144,
    minChapter: 8,
    rewards: [
      { itemId: "studio:apollo_sun_talisman", amount: 1, role: "both", uniqueKey: "thrinacia_talisman" },
    ],
    msgKey: "odyssey.prog.chest.thrinacia",
  },
  {
    id: "chest_ithaca_great_hall",
    site: "ithaca",
    x: -420, y: 65, z: -216,
    minChapter: 9,
    rewards: [
      { itemId: "studio:royal_bow_of_odysseus", amount: 1, role: "odysseus", uniqueKey: "ithaca_bow" },
      { itemId: "studio:spear_of_telemachus", amount: 1, role: "telemachus", uniqueKey: "ithaca_spear" },
    ],
    msgKey: "odyssey.prog.chest.ithaca",
  },
];

// ------------------------------------------------------------------ Helpers: Inventory, Vault & Role Checks
export function getGlobalChapter(p) {
  try { return world.getDynamicProperty("odyssey:global_chapter") ?? dp(p, "studio:chapter", 1); }
  catch { return dp(p, "studio:chapter", 1); }
}

export function getRole(p) {
  const r = dp(p, "studio:role", "");
  return r || "odysseus";
}

export function hasItemInInventory(p, typeId) {
  try {
    const inv = p.getComponent("minecraft:inventory")?.container;
    if (!inv) return false;
    for (let i = 0; i < inv.size; i++) {
      const it = inv.getItem(i);
      if (it && it.typeId === typeId && it.amount > 0) return true;
    }
    return false;
  } catch {
    return false;
  }
}

export function canAcceptStack(p, typeId, amount = 1, maxStack = 1) {
  try {
    const inv = p.getComponent("minecraft:inventory")?.container;
    if (!inv) return false;
    if (inv.emptySlotsCount > 0) return true;
    for (let i = 0; i < inv.size; i++) {
      const it = inv.getItem(i);
      if (it && it.typeId === typeId && it.amount + amount <= (it.maxAmount ?? maxStack)) {
        return true;
      }
    }
    return false;
  } catch {
    return false;
  }
}

function readVault(p) {
  try { return JSON.parse(dp(p, "studio:reward_vault", "[]")); }
  catch { return []; }
}

function writeVault(p, list) {
  setDp(p, "studio:reward_vault", JSON.stringify(list.slice(0, 32)));
}

/** Check if an item is already queued in the player's Unclaimed Reward Vault. */
export function hasItemInVault(p, typeId) {
  return readVault(p).some((entry) => entry[0] === typeId);
}

/**
 * Safely grant a progression reward to a player:
 * - Filters by role ("odysseus", "telemachus", or "both") unless solo fallback applies.
 * - Prevents duplicate claims of unique rewards via `studio:claimed_<uniqueKey>`.
 * - Marks the item's `unlockFlag` on the player so prerequisite checks & lost-item recovery know it is unlocked.
 * - Checks available inventory space first; if full, stores the item in `studio:reward_vault` (never drops/deletes it).
 */
export function grantProgressionReward(p, itemId, amount = 1, {
  uniqueKey = "",
  role = "both",
  silent = false,
  bypassRoleIfSolo = true,
} = {}) {
  if (!valid(p) || !isPlayer(p)) return false;

  const spec = PROGRESSION_ITEMS[itemId];
  const targetRole = role !== "both" ? role : (spec?.role ?? "both");
  const playerRole = getRole(p);

  // Role isolation: In multiplayer, if another online player holds the targetRole, only that player receives this personal reward.
  // In solo play, if only 1 player is online and it's a personal item for the other role, we only grant if matches playerRole
  // (or if the player switches to that role later, they can claim it!).
  if (targetRole !== "both" && playerRole !== targetRole) {
    if (!bypassRoleIfSolo) return false;
    // Record that this role reward is ready whenever the player switches to that role
    setDp(p, `studio:pending_role_${targetRole}_${itemId}`, amount);
    return false;
  }

  const claimFlag = uniqueKey ? `studio:claimed_${uniqueKey}` : (spec?.unique ? `studio:claimed_${itemId}` : "");
  if (claimFlag && dp(p, claimFlag, false)) {
    return false; // Already claimed this unique reward
  }

  // Prevent duplicate unique equipment if player already holds one in inventory or vault
  if (spec?.unique && (hasItemInInventory(p, itemId) || hasItemInVault(p, itemId))) {
    if (claimFlag) setDp(p, claimFlag, true);
    if (spec.unlockFlag) setDp(p, spec.unlockFlag, true);
    return false;
  }

  if (claimFlag) setDp(p, claimFlag, true);
  if (spec?.unlockFlag) setDp(p, spec.unlockFlag, true);

  const maxStack = spec?.maxStack ?? 64;
  if (!canAcceptStack(p, itemId, amount, maxStack)) {
    const vault = readVault(p);
    vault.push([itemId, amount]);
    writeVault(p, vault);
    if (!silent) {
      tell(p, "odyssey.prog.vault_stored");
      bar(p, "odyssey.prog.vault_bar");
      hear(p, "odyssey.athena.chime", undefined, 0.8, 0.9);
    }
    return true;
  }

  try {
    const inv = p.getComponent("minecraft:inventory")?.container;
    const leftover = inv?.addItem(new ItemStack(itemId, amount));
    if (leftover && leftover.amount > 0) {
      const vault = readVault(p);
      vault.push([itemId, leftover.amount]);
      writeVault(p, vault);
      if (!silent) tell(p, "odyssey.prog.vault_stored");
    } else if (!silent) {
      hear(p, "odyssey.athena.chime", undefined, 0.9, 1.15);
      particle(p.dimension, "minecraft:villager_happy", add(p.location, { x: 0, y: 1.2, z: 0 }));
      bar(p, "odyssey.prog.reward_granted");
    }
    return true;
  } catch {
    return false;
  }
}

/** Distribute a milestone/quest reward across all eligible players in the world (synchronizing multiplayer). */
export function distributePartyReward(itemId, amount = 1, { uniqueKey = "", role = "both" } = {}) {
  for (const p of world.getAllPlayers().filter(valid)) {
    grantProgressionReward(p, itemId, amount, { uniqueKey, role, bypassRoleIfSolo: false });
  }
}

/** Deliver any pending items from the player's Unclaimed Reward Vault when inventory space opens. */
export function flushRewardVault(p, { manual = false } = {}) {
  if (!valid(p) || !isPlayer(p)) return 0;
  // Also check if player switched role and has pending role-specific rewards
  const role = getRole(p);
  for (const itemId of Object.keys(PROGRESSION_ITEMS)) {
    const pendKey = `studio:pending_role_${role}_${itemId}`;
    const pendAmt = dp(p, pendKey, 0);
    if (pendAmt > 0) {
      setDp(p, pendKey, 0);
      grantProgressionReward(p, itemId, pendAmt, { role, bypassRoleIfSolo: false });
    }
  }

  const vault = readVault(p);
  if (!vault.length) {
    if (manual) bar(p, "odyssey.prog.vault_empty");
    return 0;
  }
  const remaining = [];
  let delivered = 0;
  const inv = p.getComponent("minecraft:inventory")?.container;
  for (const [itemId, amount] of vault) {
    const spec = PROGRESSION_ITEMS[itemId];
    if (inv && canAcceptStack(p, itemId, amount, spec?.maxStack ?? 64)) {
      const left = inv.addItem(new ItemStack(itemId, amount));
      if (left && left.amount > 0) {
        remaining.push([itemId, left.amount]);
      } else {
        delivered++;
      }
    } else {
      remaining.push([itemId, amount]);
    }
  }
  writeVault(p, remaining);
  if (delivered > 0) {
    hear(p, "odyssey.athena.chime", undefined, 0.9, 1.2);
    tell(p, "odyssey.prog.vault_claimed");
    bar(p, "odyssey.prog.vault_claimed");
  } else if (manual && remaining.length > 0) {
    bar(p, "odyssey.calypso.inv_full");
  }
  return delivered;
}

/**
 * Lost Quest-Item Recovery:
 * Ensures that any essential quest item (`essential: true`) already unlocked by the player
 * can never be permanently lost. Restores missing essential items to inventory or vault.
 */
export function recoverLostQuestItems(p, { notifyIfNone = false } = {}) {
  if (!valid(p) || !isPlayer(p)) return 0;
  // Astrolabe is always unlocked from spawn
  setDp(p, "studio:unlock_astrolabe", true);
  const role = getRole(p);
  let restored = 0;

  for (const [itemId, spec] of Object.entries(PROGRESSION_ITEMS)) {
    if (!spec.essential) continue;
    if (spec.role !== "both" && spec.role !== role) continue;
    const isUnlocked = dp(p, spec.unlockFlag, false) || getGlobalChapter(p) > spec.chapter;
    if (!isUnlocked) continue;
    if (!hasItemInInventory(p, itemId) && !hasItemInVault(p, itemId)) {
      const inv = p.getComponent("minecraft:inventory")?.container;
      if (inv && canAcceptStack(p, itemId, 1, 1)) {
        inv.addItem(new ItemStack(itemId, 1));
      } else {
        const vault = readVault(p);
        vault.push([itemId, 1]);
        writeVault(p, vault);
      }
      restored++;
    }
  }
  if (restored > 0) {
    hear(p, "odyssey.athena.chime", undefined, 0.9, 1.1);
    tell(p, "odyssey.prog.recovered");
    bar(p, "odyssey.prog.recovered");
  } else if (notifyIfNone) {
    bar(p, "odyssey.prog.nothing_missing");
  }
  return restored;
}

// ------------------------------------------------------------------ Prerequisite & Anti-Bypass Enforcement
export function checkItemPrerequisite(p, itemId) {
  const spec = PROGRESSION_ITEMS[itemId];
  if (!spec) return true;
  const ch = getGlobalChapter(p);
  const unlocked = dp(p, spec.unlockFlag, false);
  if (ch < spec.chapter && !unlocked) {
    tell(p, "odyssey.prog.locked_ch");
    bar(p, "odyssey.prog.locked_ch_bar", String(spec.chapter));
    hear(p, "odyssey.calypso.sigh", undefined, 0.7, 0.8);
    return false;
  }
  const role = getRole(p);
  if (spec.role !== "both" && spec.role !== role) {
    tell(p, `odyssey.prog.wrong_role.${spec.role}`);
    bar(p, `odyssey.prog.wrong_role.${spec.role}`);
    return false;
  }
  return true;
}

/** Check if player has Moly protection against Circe's curse (either by holding Moly or having consumed it). */
export function hasMolyProtection(p) {
  if (!valid(p)) return false;
  if (dp(p, "studio:moly_immune_until", 0) > now()) return true;
  if (heldItem(p) === "studio:moly_herb" || hasItemInInventory(p, "studio:moly_herb")) {
    return true;
  }
  return false;
}

/** Check if player can perform the Hades Black-Sand Sacrifice (requires Chapter V+ or Sacrificial Copper Knife). */
export function canPerformHadesSacrifice(p) {
  if (!valid(p)) return false;
  const hasKnife = heldItem(p) === "studio:sacrificial_copper_knife" || hasItemInInventory(p, "studio:sacrificial_copper_knife");
  if (!hasKnife && getGlobalChapter(p) < 6 && !dp(p, "studio:unlock_sacrificial_knife", false)) {
    tell(p, "odyssey.prog.need_knife");
    bar(p, "odyssey.prog.need_knife");
    return false;
  }
  return true;
}

// ------------------------------------------------------------------ Active Combat & Relic Abilities (Item Use / Hit)
export function onUseProgressionItem(p, itemId) {
  if (!valid(p) || !isPlayer(p)) return;
  if (!checkItemPrerequisite(p, itemId)) return;

  switch (itemId) {
    case "studio:copper_hoplon": {
      if (!ready(p, "studio:cd_hoplon")) return;
      wait(p, "studio:cd_hoplon", 120);
      effect(p, "resistance", 160, 1);
      effect(p, "absorption", 160, 0);
      sound(p.dimension, "odyssey.laestrygonian.clang", p.location, 0.9, 1.2);
      bar(p, "odyssey.prog.use.hoplon");
      break;
    }
    case "studio:moly_herb": {
      setDp(p, "studio:moly_immune_until", now() + 12000);
      setDp(p, "studio:pliable_until", 0);
      effect(p, "resistance", 1200, 0);
      effect(p, "regeneration", 300, 1);
      hear(p, "odyssey.athena.shimmer", undefined, 0.9, 1.2);
      tell(p, "odyssey.prog.use.moly");
      bar(p, "odyssey.prog.use.moly");
      break;
    }
    case "studio:tiresias_staff": {
      if (!ready(p, "studio:cd_tiresias_staff")) return;
      wait(p, "studio:cd_tiresias_staff", 140);
      effect(p, "night_vision", 400, 0);
      effect(p, "regeneration", 120, 1);
      sound(p.dimension, "odyssey.tiresias.prophecy", p.location, 0.9, 1.1);
      for (const e of near(p.dimension, p.location, 10)) {
        if (e.id === p.id || isPlayer(e)) continue;
        effect(e, "weakness", 200, 1);
        effect(e, "slowness", 140, 1);
        particle(p.dimension, "minecraft:soul_particle", add(e.location, { x: 0, y: 1, z: 0 }));
      }
      bar(p, "odyssey.prog.use.tiresias_staff");
      break;
    }
    case "studio:apollo_sun_talisman": {
      if (!ready(p, "studio:cd_sun_talisman")) return;
      wait(p, "studio:cd_sun_talisman", 300);
      effect(p, "fire_resistance", 1200, 0);
      effect(p, "regeneration", 240, 1);
      effect(p, "absorption", 600, 1);
      burst(p.dimension, "minecraft:villager_happy", add(p.location, { x: 0, y: 1.2, z: 0 }), 1.2, 8);
      hear(p, "odyssey.athena.chime", undefined, 1.0, 1.3);
      bar(p, "odyssey.prog.use.sun_talisman");
      break;
    }
    case "studio:royal_bow_of_odysseus": {
      if (!ready(p, "studio:cd_royal_bow")) return;
      wait(p, "studio:cd_royal_bow", 35);
      const f = forward(p);
      sound(p.dimension, "random.bow", p.location, 1.0, 0.9);
      // Piercing line shot up to 22 blocks (inspired by the 12 Axe-Trial shot)
      for (let d = 1.5; d <= 22; d += 1.5) {
        const pt = add(p.location, { x: f.x * d, y: 1.3 + (f.y ?? 0) * d, z: f.z * d });
        particle(p.dimension, "minecraft:critical_hit_emitter", pt);
        for (const t of near(p.dimension, pt, 1.8)) {
          if (t.id === p.id || isPlayer(t)) continue;
          hurt(t, 14, p);
          push(t, f, 0.9, 0.25);
        }
      }
      bar(p, "odyssey.prog.use.royal_bow");
      break;
    }
    case "studio:spear_of_telemachus": {
      if (!ready(p, "studio:cd_royal_spear")) return;
      wait(p, "studio:cd_royal_spear", 50);
      const f = forward(p);
      push(p, f, 1.1, 0.2);
      sound(p.dimension, "odyssey.laestrygonian.impale", p.location, 0.95, 1.2);
      for (const t of near(p.dimension, add(p.location, scale(f, 3.2)), 3.2)) {
        if (t.id === p.id || isPlayer(t)) continue;
        hurt(t, 12, p);
        push(t, f, 1.3, 0.4);
        burst(p.dimension, "minecraft:critical_hit_emitter", t.location, 0.8, 6);
      }
      bar(p, "odyssey.prog.use.royal_spear");
      break;
    }
    default:
      break;
  }
}

/** Special melee weapon effects when a player strikes an entity with a Copper progression weapon. */
export function onPlayerWeaponHit(attacker, victim) {
  if (!valid(attacker) || !valid(victim) || !isPlayer(attacker)) return;
  const held = heldItem(attacker);
  if (!held || !PROGRESSION_ITEMS[held]) return;
  if (!checkItemPrerequisite(attacker, held)) return;

  if (held === "studio:copper_xiphos" && ready(attacker, "studio:cd_xiphos_cleave")) {
    wait(attacker, "studio:cd_xiphos_cleave", 40);
    for (const t of near(attacker.dimension, victim.location, 2.6)) {
      if (t.id === attacker.id || t.id === victim.id || isPlayer(t)) continue;
      hurt(t, 4, attacker);
    }
    particle(attacker.dimension, "minecraft:critical_hit_emitter", add(victim.location, { x: 0, y: 1, z: 0 }));
  } else if (held === "studio:copper_dory" && ready(attacker, "studio:cd_dory_lunge")) {
    wait(attacker, "studio:cd_dory_lunge", 45);
    push(victim, dirTo(attacker.location, victim.location), 0.9, 0.3);
    particle(attacker.dimension, "minecraft:critical_hit_emitter", add(victim.location, { x: 0, y: 1.1, z: 0 }));
  } else if (held === "studio:laestrygonian_cleaver" && ready(attacker, "studio:cd_cleaver_slam")) {
    wait(attacker, "studio:cd_cleaver_slam", 70);
    burst(attacker.dimension, "minecraft:huge_explosion_emitter", victim.location, 0.8, 1);
    for (const t of near(attacker.dimension, victim.location, 3.4)) {
      if (t.id === attacker.id || isPlayer(t)) continue;
      hurt(t, 5, attacker);
      push(t, dirTo(attacker.location, t.location), 1.1, 0.45);
    }
  } else if (held === "studio:spear_of_telemachus" && ready(attacker, "studio:cd_spear_spark")) {
    wait(attacker, "studio:cd_spear_spark", 60);
    hurt(victim, 5, attacker);
    hear(attacker, "odyssey.athena.shimmer", victim.location, 0.85, 1.2);
  }
}

// ------------------------------------------------------------------ Story Milestone & Discovery Chest Hooks
export function onProgressionStoryMilestone(p, eventId) {
  if (!valid(p) || !isPlayer(p)) return;

  switch (eventId) {
    case "lotus_gifted":
      setDp(p, "studio:unlock_lotus_flower", true);
      break;
    case "find_ship":
      grantProgressionReward(p, "studio:ship_helm_horn", 1, { uniqueKey: "milestone_ship_horn", role: "both" });
      break;
    case "gather_crew":
      grantProgressionReward(p, "studio:ship_repair_kit", 2, { uniqueKey: "milestone_crew_repair", role: "both" });
      break;
    case "site_troy":
      // Unlock Tier 2 Copper crafting & grant Copper Ingots for the siege
      setDp(p, "studio:unlock_copper_xiphos", true);
      setDp(p, "studio:unlock_copper_hoplon", true);
      setDp(p, "studio:unlock_copper_cuirass", true);
      break;
    case "horse_hidden":
      // Odysseus receives his signature Ithacan Copper Xiphos for leading the Trojan Horse infiltration
      grantProgressionReward(p, "studio:copper_xiphos", 1, { uniqueKey: "milestone_troy_xiphos", role: "odysseus" });
      grantProgressionReward(p, "studio:copper_hoplon", 1, { uniqueKey: "milestone_troy_hoplon", role: "both" });
      break;
    case "site_sparta":
      // Telemachus receives his Peloponnesian Copper Dory at Menelaus's Citadel in Sparta
      setDp(p, "studio:unlock_copper_dory", true);
      grantProgressionReward(p, "studio:copper_dory", 1, { uniqueKey: "milestone_sparta_dory", role: "telemachus" });
      grantProgressionReward(p, "studio:copper_cuirass", 1, { uniqueKey: "milestone_sparta_cuirass", role: "both" });
      break;
    case "site_cyclops":
      setDp(p, "studio:unlock_burning_stake", true);
      break;
    case "cyclops_blinded":
      grantProgressionReward(p, "studio:copper_helm", 1, { uniqueKey: "milestone_cyclops_helm", role: "both" });
      break;
    case "site_telepylus":
      setDp(p, "studio:unlock_laestrygonian_cleaver", true);
      break;
    case "giant_slain":
      grantProgressionReward(p, "studio:laestrygonian_cleaver", 1, { uniqueKey: "milestone_giant_cleaver", role: "odysseus" });
      break;
    case "site_aeaea":
      setDp(p, "studio:unlock_moly_herb", true);
      // Athena's warning on Aeaea grants 1 Moly root to resist Circe's spell
      grantProgressionReward(p, "studio:moly_herb", 1, { uniqueKey: "milestone_aeaea_moly", role: "both" });
      break;
    case "circe_yielded":
      // Circe yields and gifts the Ritual Copper Machaira required for Hades + Siren Beeswax
      grantProgressionReward(p, "studio:sacrificial_copper_knife", 1, { uniqueKey: "milestone_circe_knife", role: "both" });
      grantProgressionReward(p, "studio:beeswax", 4, { uniqueKey: "milestone_circe_wax", role: "both" });
      break;
    case "hades_sacrifice":
      // Tiresias bestows his Oracle Staff upon Telemachus (or vaults it for Telemachus)
      grantProgressionReward(p, "studio:tiresias_staff", 1, { uniqueKey: "milestone_hades_staff", role: "telemachus" });
      break;
    case "site_strait":
      grantProgressionReward(p, "studio:aegis_copper_plate", 1, { uniqueKey: "milestone_strait_aegis", role: "odysseus" });
      break;
    case "site_thrinacia":
      setDp(p, "studio:unlock_apollo_talisman", true);
      break;
    case "ithaca_blessed":
      // Final Chapter IX Masterworks for Odysseus and Telemachus
      grantProgressionReward(p, "studio:royal_bow_of_odysseus", 1, { uniqueKey: "milestone_ithaca_bow", role: "odysseus" });
      grantProgressionReward(p, "studio:spear_of_telemachus", 1, { uniqueKey: "milestone_ithaca_spear", role: "telemachus" });
      break;
    default:
      break;
  }
}

/** Periodic 1 Hz check: auto-flush Unclaimed Reward Vault & check proximity to Discovery Chests. */
export function tickProgression() {
  for (const p of world.getAllPlayers().filter(valid)) {
    safe("prog_tick", () => {
      flushRewardVault(p, { manual: false });
      const ch = getGlobalChapter(p);

      // Check proximity to in-world Discovery Chests (within 3.2 blocks)
      for (const chest of DISCOVERY_CHESTS) {
        if (flat(p.location, chest) > 3.2 || Math.abs(p.location.y - chest.y) > 3.0) continue;
        const seenFlag = `studio:chest_${chest.id}`;
        if (dp(p, seenFlag, false)) continue;
        if (ch < chest.minChapter) {
          if (ready(p, "studio:cd_chest_lock")) {
            wait(p, "studio:cd_chest_lock", 100);
            bar(p, "odyssey.prog.locked_ch_bar", String(chest.minChapter));
          }
          continue;
        }
        setDp(p, seenFlag, true);
        let anyGranted = false;
        for (const r of chest.rewards) {
          if (r.itemId.startsWith("minecraft:")) {
            if (canAcceptStack(p, r.itemId, r.amount, 64)) {
              p.getComponent("minecraft:inventory")?.container?.addItem(new ItemStack(r.itemId, r.amount));
              anyGranted = true;
            }
          } else {
            const ok = grantProgressionReward(p, r.itemId, r.amount, {
              uniqueKey: r.uniqueKey,
              role: r.role,
              silent: true,
            });
            if (ok) anyGranted = true;
          }
        }
        if (anyGranted) {
          sound(p.dimension, "random.chestopen", { x: chest.x, y: chest.y, z: chest.z }, 0.9, 1.0);
          hear(p, "odyssey.athena.chime", undefined, 0.9, 1.15);
          tell(p, chest.msgKey);
          bar(p, chest.msgKey);
        }
      }
    });
  }
}
