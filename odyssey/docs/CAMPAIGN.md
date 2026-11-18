# Campaign: nine chapters

Source of truth: `world/behavior_packs/Odyssey_Creatures_BP/scripts/data/campaign.js`.

**Scopes:** **O** = Odysseus, **T** = Telemachus, **C** = Companion, **E** = Eumaeus, **S** = shared (everyone),
**X** = support (C + E).

**How chapters advance:** a chapter ends when every objective in its `complete` list is done. Then a closing scene
plays, the next chapter's title is shown, and journals update. In solo play the NPC Telemachus finishes his own
objectives (`npcAuto`), with a line of narration.

**Coordinates:** every coordinate below is verified; see START_POSITIONS.md.

---

## Chapter I: Twenty Years
1. **Context:** Ithaca has waited twenty years. Antinous and the suitors hold the hall. Odysseus is held on Ogygia.
2. **Start:** O and C start at Ogygia (0.5 65 3.5 / 1.5 65 −18.5). T and E start at Ithaca (−419.5 65 −199.5 / −403.5 65 −195.5).
3. **Characters:** Odysseus, Calypso, Athena (guidance); Telemachus, Mentor, Eumaeus.
4. **Opening scene:** split by island. Ithaca players get an aerial shot of Ithaca, a low-angle shot of the palace, a
   close-up of Mentor and a tracking shot to the harbour. Ogygia players get an ocean panorama, the pavilion, a
   close-up of Calypso and an over-the-shoulder shot to the sea.
5. **Events in order:** T speaks with Mentor, then sails to Sparta. In parallel, O speaks with Calypso, answers the
   goddess at the pavilion and finds the galley.
6. **Player actions:** talk to NPCs, travel by boat (T gets a boat), reach places, use the galley horn.
7. **NPCs:** Mentor (`talk_mentor`), Calypso (lotus offer, then the lotus/resist vote), Eumaeus.
8. **Enemies:** none.
9. **Locations:** Ithaca square and harbour, Sparta (raised at runtime), Ogygia court, garden, pavilion and harbour.
10. **Items:** Astrolabe and role kits. At Sparta: copper dory (T) and cuirass. The galley horn is unlocked by the ship quest.
11. **Optional:** E tells Mentor what the suitors plan. Discovery chests on Ogygia and Sparta.
12. **Ending scene:** the galley on the beach ("the way home is open").
13. **Unlock:** `o1_ship` (O finds the galley) and `t1_sparta` (T reaches Sparta, or the NPC does it in solo play).
    After this, Ithaca players are faded and teleported to Ogygia harbour to join the voyage.

| Objective | Scope | Completes on | Destination |
|---|---|---|---|
| Speak with Mentor | T | talk to Mentor | ithaca_mentor |
| Sail to Sparta | T | arrive at Sparta | sparta_temple |
| Speak with Calypso | O | lotus offer | ogygia_calypso |
| Answer the goddess | O | stand at the pavilion | ogygia_temple |
| Find the galley | O, C | reach the ship | ogygia_harbor |
| Keep watch at the palace | E | stand in the hall | ithaca_palace |

## Chapter II: The Horse (the tale begins)
1. **Context:** Odysseus's account begins on the night of the wooden Horse.
2. **Start:** wherever the party sailed from. Troy beach is at −149.5 65 −243.5.
3. **Characters:** the party, the Trojan Horse.
4. **Opening scene:** site cutscene (battlefield panorama, low-angle Horse, tracking shot).
5. **Events:** land on the beach, then hide in the Horse. The altar vote follows.
6. **Actions:** sail, land, use the Horse's "Hide Inside" interaction, vote.
7. **NPCs:** none. Athena gives guidance at Sparta and Ithaca.
8. **Enemies:** none scripted.
9. **Locations:** Troy beach, the Horse, walls, Scaean gate, shrine and harbour.
10. **Items:** copper xiphos (O) and hoplon for hiding in the Horse; Tier-2 copper recipes unlock.
11. **Optional:** the altar vote (honour Athena or take the spoils); the Troy discovery chest.
12. **Ending scene:** a low-angle shot of the Horse ("Troy burns").
13. **Unlock:** `o2_horse`.

## Chapter III: The Shepherd's Cave
1. **Context:** the Cyclops' island.
2. **Start:** the east landing, 370.5 66 −149.5. A new pier is built there; the old one ran into the mountain.
3. **Characters:** Polyphemus.
4. **Opening scene:** wide shot of the island, then a low-angle shot of the Cyclops stomping.
5. **Events:** land, find the cave, wait for night, blind him with the burning stake. The escape vote follows.
6. **Actions:** craft the burning stake, sneak, strike at night.
7. **NPCs:** none.
8. **Enemies:** the Cyclops (boulders, kicks, devour).
9. **Locations:** landing and cave (318.5 67 −149.5).
10. **Items:** burning stake (crafted); copper helm when he is blinded.
11. **Optional:** the escape vote (silent flock or shout your name).
12. **Ending scene:** ocean panorama ("the giant's cry").
13. **Unlock:** `o3_stake`.

## Chapter IV: Telepylus
1. **Context:** a still harbour owned by giants.
2. **Start:** Telepylus dock, 560.5 65 42.5.
3. **Characters:** Laestrygonians and the giant child.
4. **Opening scene:** battlefield panorama, then a close-up of the child laughing.
5. **Events:** reach the gate, get the crew back to the harbour, flee to Aeaea.
6. **Actions:** fight or evade, sail away.
7. **NPCs:** none.
8. **Enemies:** four Laestrygonians (sword, glaive, mace, scimitar).
9. **Locations:** gate, watchtowers, fjord dock.
10. **Items:** Laestrygonian cleaver for slaying a giant (O).
11. **Optional:** bring down a giant (`o4_giant`).
12. **Ending scene:** aerial shot of Aeaea ("fewer ships leave").
13. **Unlock:** `s4_flee` (arrive at Aeaea).

## Chapter V: Circe
1. **Context:** smoke from a hall in the woods.
2. **Start:** Aeaea shore, 520.5 65 344.5.
3. **Characters:** Circe and her bird-sister.
4. **Opening scene:** wide shot of the hall, then a close-up of Circe serving.
5. **Events:** find the hall and face Circe with the moly herb. She yields, and the pact vote follows.
6. **Actions:** carry moly, avoid the pig curse, make her yield.
7. **NPCs:** Circe (guidance once she yields; can become a companion).
8. **Enemies:** Circe's curse.
9. **Locations:** hall (520.5 65 370.5) and herb cellar.
10. **Items:** moly on arrival; on her yielding, the sacrificial copper knife and beeswax ×4.
11. **Optional:** the pact vote.
12. **Ending scene:** wide shot of the hall ("down, to the dead").
13. **Unlock:** `o5_circe`.

## Chapter VI: The Land of the Dead
1. **Context:** only the dead know the way home.
2. **Start:** the black shore, 260.5 65 504.5.
3. **Characters:** the shades (including Sinon and Agamemnon) and Tiresias.
4. **Opening scene:** wide shot, then a tracking shot.
5. **Events:** land, guard the pit, perform the rite on the black sand. The dead rise.
6. **Actions:** sacrifice a sheep while standing on black sand, with the knife.
7. **NPCs:** Tiresias, Agamemnon, Sinon.
8. **Enemies:** grasping shades.
9. **Locations:** the shore and the pit of offerings (260.5 65 514.5).
10. **Items:** Tiresias's staff (T).
11. **Optional:** none.
12. **Ending scene:** reverse tracking shot ("the prophet has spoken").
13. **Unlock:** `o6_rite`.

## Chapter VII: The Sirens
1. **Context:** a song that drowns crews.
2. **Start:** at sea, heading for the Sirens' rocks (−44.5 64 471.5).
3. **Characters:** three Sirens.
4. **Opening scene:** aerial shot, then a dynamic shot of a Siren singing.
5. **Events:** T and the support roles seal their ears with wax, O hears the song, everyone gets past.
6. **Actions:** use beeswax, keep the ship on course.
7. **NPCs:** none.
8. **Enemies:** Sirens (beckon, drag).
9. **Locations:** the rocks and the wreck.
10. **Items:** beeswax.
11. **Optional:** none.
12. **Ending scene:** aerial shot of the strait ("the song fades").
13. **Unlock:** `s7_pass` (arrive at the Strait).

## Chapter VIII: The Strait and the Sun's Cattle
1. **Context:** between the cliff and the whirlpool, then hunger tests an oath.
2. **Start:** Scylla's cliff, −295.5 93 380.5.
3. **Characters:** Scylla, Charybdis, the sun cattle.
4. **Opening scene:** aerial shot, low-angle Scylla lunge, then the strait vote.
5. **Events:** pass the cliff, land on Thrinacia, decide the cattle's fate, reach Ithaca.
6. **Actions:** navigate, vote, resist (or not).
7. **NPCs:** none.
8. **Enemies:** Scylla's six heads, Charybdis, the god's storm if the cattle are killed.
9. **Locations:** strait (beacon and chest now on the cliff top), Thrinacia shore and temple.
10. **Items:** Aegis copper plate (O); Apollo sun talisman for keeping the oath.
11. **Optional:** the strait course vote.
12. **Ending scene:** aerial shot of Ithaca harbour.
13. **Unlock:** `s8_isle` and `s8_home`.

## Chapter IX: Homecoming
1. **Context:** home in rags, a hall full of suitors, a bow no one can string.
2. **Start:** Ithaca harbour, −419.5 65 −185.5.
3. **Characters:** Eumaeus, Telemachus (player or NPC companion), Athena.
4. **Opening scene:** arrival cutscene (aerial shot of the palace, low-angle shot).
5. **Events:** find Eumaeus, Telemachus waits in the hall, Athena's blessing, string the bow.
6. **Actions:** talk, receive the Royal Bow, use it inside the palace hall.
7. **NPCs:** Eumaeus (recognises Odysseus), NPC Telemachus (follows Odysseus in solo play), Athena.
8. **Enemies:** none scripted. The fight with the suitors is not implemented (see ASSETS.md).
9. **Locations:** square, palace hall (−419.5 65 −211.5), Eumaeus's yard.
10. **Items:** Royal Bow (O) and Spear of Telemachus (T) on the blessing.
11. **Optional:** none.
12. **Ending scene (finale):** the bow, the silent hall, the throne handed to Telemachus, sailing west. Then the end title.
13. **Unlock:** `o9_bow` completes the campaign.
