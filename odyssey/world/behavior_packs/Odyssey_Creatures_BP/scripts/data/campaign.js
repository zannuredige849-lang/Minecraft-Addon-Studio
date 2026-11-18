// The chronological campaign. Chapter order follows the 2026 film as far as its released material allows:
// it opens on Ithaca twenty years after the war (Telemachus, Mentor, the suitors) and on Ogygia (Odysseus and
// Calypso), then plays the voyage as Odysseus's remembered tale, and ends with the homecoming and the bow.
// See odyssey/docs/CAMPAIGN.md for the per-chapter breakdown and odyssey/docs/FILM_REFERENCE.md for sources.
//
// Objective fields:
//   id      unique id (also the lang key odyssey.q.<id>)
//   scope   "shared" (everyone), a role id ("odysseus", "telemachus") or "support" (companion + eumaeus)
//   done    event id that completes it. "reach:<point>" completes when the player stands within 5 blocks of POINTS[point].
//   dest    POINTS key shown in the journal / navigation (optional)
//   optional  not needed to finish the chapter
//   items   items the player needs for this step (shown in the journal)
//   npcAuto when the role has no player, the NPC stand-in completes it automatically (Telemachus in solo play)
//   anyone  the deed cannot be repeated once done (the Cyclops stays blind), so it counts whoever performs it
//   fallback if nobody holding the role is online, this objective completes when the fallback objective does
// Softlock rule (world/quests.js): a role objective can always be completed by another player while no player
// holding that role is online, so a player leaving never blocks the campaign.

export const CHAPTERS = [
  {
    id: 1, site: "ithaca", title: "odyssey.ch.1.title", story: "odyssey.ch.1.story",
    objectives: [
      { id: "t1_mentor",  scope: "telemachus", done: "talk_mentor", dest: "ithaca_mentor", npcAuto: true },
      { id: "t1_sparta",  scope: "telemachus", done: "site_sparta", dest: "sparta_temple", npcAuto: true },
      { id: "o1_calypso", scope: "odysseus",   done: "lotus_gifted", dest: "ogygia_calypso" },
      { id: "o1_athena",  scope: "odysseus",   done: "reach:ogygia_temple", dest: "ogygia_temple" },
      { id: "o1_ship",    scope: "odysseus",   done: "find_ship", dest: "ogygia_harbor", items: ["studio:odyssey_astrolabe"] },
      { id: "c1_ship",    scope: "companion",  done: "find_ship", dest: "ogygia_harbor" },
      { id: "e1_palace",  scope: "eumaeus",    done: "reach:ithaca_palace", dest: "ithaca_palace" },
      { id: "e1_mentor",  scope: "eumaeus",    done: "talk_mentor", dest: "ithaca_mentor", optional: true },
    ],
    // Chapter I ends when Odysseus has found the galley and Telemachus (player or NPC) has reached Sparta.
    complete: ["o1_ship", "t1_sparta"],
  },
  {
    id: 2, site: "troy", title: "odyssey.ch.2.title", story: "odyssey.ch.2.story",
    objectives: [
      { id: "s2_beach",   scope: "shared",     done: "reach:troy_beach", dest: "troy_beach" },
      { id: "o2_horse",   scope: "odysseus",   done: "horse_hidden", dest: "troy_horse" },
      { id: "t2_scout",   scope: "telemachus", done: "reach:troy_horse", dest: "troy_horse" },
      { id: "x2_horse",   scope: "support",    done: "horse_hidden", dest: "troy_horse" },
      { id: "s2_altar",   scope: "shared",     done: "vote:troy_altar", optional: true },
    ],
    complete: ["o2_horse"],
  },
  {
    id: 3, site: "cyclops", title: "odyssey.ch.3.title", story: "odyssey.ch.3.story",
    objectives: [
      { id: "s3_land",    scope: "shared",     done: "reach:cyclops_landing", dest: "cyclops_landing" },
      { id: "t3_cave",    scope: "telemachus", done: "reach:cyclops_cave", dest: "cyclops_cave" },
      { id: "o3_stake",   scope: "odysseus",   done: "cyclops_blinded", dest: "cyclops_cave", items: ["studio:burning_stake"], anyone: true },
      { id: "x3_cave",    scope: "support",    done: "reach:cyclops_cave", dest: "cyclops_cave" },
    ],
    complete: ["o3_stake"],
  },
  {
    id: 4, site: "telepylus", title: "odyssey.ch.4.title", story: "odyssey.ch.4.story",
    objectives: [
      { id: "s4_gate",    scope: "shared",     done: "reach:telepylus_gate", dest: "telepylus_gate" },
      { id: "t4_dock",    scope: "telemachus", done: "reach:telepylus_dock", dest: "telepylus_dock" },
      { id: "o4_giant",   scope: "odysseus",   done: "giant_slain", optional: true },
      { id: "s4_flee",    scope: "shared",     done: "site_aeaea", dest: "aeaea_shore" },
    ],
    complete: ["s4_flee"],
  },
  {
    id: 5, site: "aeaea", title: "odyssey.ch.5.title", story: "odyssey.ch.5.story",
    objectives: [
      { id: "t5_hall",    scope: "telemachus", done: "reach:aeaea_hall", dest: "aeaea_hall" },
      { id: "o5_circe",   scope: "odysseus",   done: "circe_yielded", dest: "aeaea_hall", items: ["studio:moly_herb"], anyone: true },
      { id: "x5_hall",    scope: "support",    done: "reach:aeaea_hall", dest: "aeaea_hall" },
      { id: "s5_pact",    scope: "shared",     done: "vote:circe_pact", optional: true },
    ],
    complete: ["o5_circe"],
  },
  {
    id: 6, site: "hades", title: "odyssey.ch.6.title", story: "odyssey.ch.6.story",
    objectives: [
      { id: "s6_shore",   scope: "shared",     done: "reach:hades_shore", dest: "hades_shore" },
      { id: "t6_altar",   scope: "telemachus", done: "reach:hades_altar", dest: "hades_altar" },
      { id: "o6_rite",    scope: "odysseus",   done: "hades_sacrifice", dest: "hades_altar", items: ["studio:sacrificial_copper_knife"] },
    ],
    complete: ["o6_rite"],
  },
  {
    id: 7, site: "sirens", title: "odyssey.ch.7.title", story: "odyssey.ch.7.story",
    objectives: [
      { id: "t7_wax",     scope: "telemachus", done: "wax_used", items: ["studio:beeswax"] },
      { id: "x7_wax",     scope: "support",    done: "wax_used", items: ["studio:beeswax"] },
      { id: "o7_listen",  scope: "odysseus",   done: "reach:sirens_rocks", dest: "sirens_rocks" },
      { id: "s7_pass",    scope: "shared",     done: "site_strait", dest: "strait_cliff" },
    ],
    complete: ["s7_pass"],
  },
  {
    id: 8, site: "strait", title: "odyssey.ch.8.title", story: "odyssey.ch.8.story",
    objectives: [
      { id: "s8_strait",  scope: "shared",     done: "reach:strait_cliff", dest: "strait_cliff" },
      { id: "s8_isle",    scope: "shared",     done: "site_thrinacia", dest: "thrinacia_shore" },
      { id: "o8_oath",    scope: "odysseus",   done: "vote:thrinacia_oath", dest: "thrinacia_temple" },
      { id: "t8_temple",  scope: "telemachus", done: "reach:thrinacia_temple", dest: "thrinacia_temple" },
      { id: "s8_home",    scope: "shared",     done: "site_ithaca", dest: "ithaca_harbor" },
    ],
    complete: ["s8_isle", "s8_home"],
  },
  {
    id: 9, site: "ithaca", title: "odyssey.ch.9.title", story: "odyssey.ch.9.story",
    objectives: [
      { id: "o9_eumaeus", scope: "odysseus",   done: "talk_eumaeus", dest: "ithaca_eumaeus" },
      { id: "t9_palace",  scope: "telemachus", done: "reach:ithaca_palace", dest: "ithaca_palace", npcAuto: true },
      { id: "e9_guide",   scope: "eumaeus",    done: "reach:ithaca_palace", dest: "ithaca_palace" },
      { id: "s9_athena",  scope: "shared",     done: "ithaca_blessed", dest: "ithaca_square" },
      { id: "o9_bow",     scope: "odysseus",   done: "bow_trial", dest: "ithaca_palace", items: ["studio:royal_bow_of_odysseus"], fallback: "s9_athena" },
    ],
    complete: ["o9_bow"],
  },
];

export const FINAL_CHAPTER = 9;
export const chapterById = (id) => CHAPTERS.find((c) => c.id === id) ?? CHAPTERS[0];
export const allObjectives = () => CHAPTERS.flatMap((c) => c.objectives.map((o) => ({ ...o, chapter: c.id })));

/** Does objective `o` belong to a player holding `role`? */
export function objectiveFor(o, role) {
  if (o.scope === "shared") return true;
  if (o.scope === "support") return role === "companion" || role === "eumaeus";
  return o.scope === role;
}
