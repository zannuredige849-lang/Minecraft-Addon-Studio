# Film reference and authenticity notes: *The Odyssey* (2026)

Written for The Odyssey add-on v3.0.0. It separates what the released film is **confirmed** to contain from what
this map **interprets**. Research was done on 18 Nov 2026, four months after the film's release (17 Jul 2026).

## Sources and their limits

| Source | Status | Used for |
|---|---|---|
| Wikipedia, *The Odyssey (2026 film)* | Read. The plot and cast sections were read verbatim. Production and costume sections came only as an automated summary. | Plot order, cast, filming |
| NBC Insider, Variety, Britannica, TMDB cast lists (search results) | Headlines and snippets only. Britannica pages returned HTTP 403. | Cast cross-check |
| Official trailers, stills, production images | **Not reviewed** in this session (no video or image access) | — |

Because stills and trailers were not studied, no texture claims to copy a specific costume. Visual choices below are
labelled *interpretation*. Nothing here uses film footage, stills, music or dialogue: all in-game dialogue is original.

## Confirmed (from the verbatim plot and cast text)

- **Opening:** the film begins on Ithaca 20 years after the Trojan War. Telemachus sails to **Sparta** with **Mentor**
  for news of his father; Menelaus and Helen do not know Odysseus's fate. **Athena** appears to Odysseus on **Ogygia**,
  where **Calypso** holds him.
- **Telemachus's danger:** **Antinous**, the leading suitor, learns of the trip and plots to kill him on his return.
  Mentor is killed by bandits sent by the suitors.
- **The voyage (told in flashback):** Troy and the **Trojan Horse**; the **Cyclops**; **Telepylus** and the
  Laestrygonians (two of three ships lost); **Circe** (crew turned to pigs); the underworld (**Sinon's** shade,
  **Agamemnon**, **Tiresias**); the **Sirens**; **Charybdis and Scylla**; **Thrinacia** and the **cattle of Apollo**,
  then a storm, with Odysseus the only survivor; Calypso's lotus and his lost memory.
- **Homecoming:** Odysseus returns to Ithaca. Then come **Eumaeus**, the dog **Argos**, the suitors' feast,
  **Penelope**, the **bow contest** and the fight with the suitors. In the ending Odysseus **hands the throne to
  Telemachus** and sails west with Penelope.
- **Cast (verbatim):** Matt Damon (Odysseus), Tom Holland (Telemachus), Anne Hathaway (Penelope), Robert Pattinson
  (Antinous), Lupita Nyong'o (Helen / Clytemnestra), Samantha Morton (Circe), John Leguizamo (Eumaeus), Zendaya (Athena).
- **Format:** the film was shot entirely on IMAX 70 mm.

## Reported but not verified verbatim (summary text only)

Treat these as leads, not facts:

- **Cast:** Charlize Theron (Calypso), Jon Bernthal (Menelaus), Himesh Patel (Eurylochus), Elliot Page (Sinon),
  Benny Safdie (Agamemnon), Ryan Hurst (Mentor), James Remar (Tiresias), Mia Goth (Melantho).
- **Costume and armour:** "tactile" design (Ellen Mirojnick). Agamemnon wears blackened bronze. Odysseus wears a
  **Corinthian helmet with a red plume**.
- **Locations:** Aït Benhaddou (Troy), Voidokilia beach near Pylos (Cyclops), Favignana (Ithaca), the Aeolian
  islands, Icelandic black beaches (the underworld), Malta and Scotland.
- **Effects:** practical creatures (the Cyclops by animatronics and performance, Circe's pigs), forced perspective
  for the Laestrygonians, a mostly digital six-headed Scylla, and gods suggested through natural phenomena.
- **Ships:** a Viking-style replica longship stood in for a Greek warship.
- **Tone:** cited inspirations are *Andrei Rublev* and *Ran*, with an emphasis on "tactile realism".

## How the map uses this

| Element | Status | Implementation |
|---|---|---|
| Opening on Ithaca (Telemachus, Mentor) and Ogygia (Odysseus, Calypso) | Confirmed | Chapter I has separate starts and tracks per role (`data/campaign.js`, `data/config.js`) |
| Telemachus sails to Sparta | Confirmed | Objective `t1_sparta`. The Spartan island is raised at runtime by `architect.js` |
| Voyage as a remembered tale | Confirmed (flashback) | Chapters II–VIII. Telemachus's player joins it "at his father's side" (**interpretation**: a gameplay device so co-op players travel together) |
| Episode order Troy → Cyclops → Telepylus → Circe → Underworld → Sirens → Strait → Thrinacia → Ithaca | Confirmed episodes; on-screen order **partly inferred** (the plot text is not strictly chronological) | Chapter order |
| Cattle of Apollo, not Helios | Confirmed | Existing sun-cattle content kept |
| Eumaeus as a loyal ally at the homecoming | Confirmed | Playable support role and NPC (`npcs.js`) |
| Bow contest | Confirmed | Objective `o9_bow`: use the Royal Bow in the palace hall |
| Throne handed to Telemachus | Confirmed | Finale scene (`story_cinematics.js`), in original wording |
| Fight with the suitors, Penelope, Argos, Antinous on screen | Confirmed in film | **Not implemented** (no suitor/Penelope models; see ASSETS.md) |
| Mentor's death | Confirmed | **Not depicted.** Mentor is present only in Chapter I |
| Corinthian helmet with red crest | Summary only | Copper helm attachable, an **interpretation** (copper replaces bronze by project rule) |
| Muscle cuirass, chitons, cloaks | Not verified | **Interpretation** in muted, natural-dye palettes, to match the reported "tactile" style |
| Guides (scout, fisherman, shepherd) | Invented | Gameplay helpers, not film characters, and never presented as such |
| Story decision votes (lotus, altar, Circe pact, etc.) | Invented (from v2.x) | Kept as optional branches. They are game content, not film events |
| Circe "yielding" when her bird-sister is seized | Invented (v2.x mechanic) | Kept |

## Visual direction (interpretation)

The film's material, as far as it could be checked here, points to real locations (Mediterranean stone, black
volcanic beaches, northern cliffs) and practical, worn craft. The map follows that: natural stone and sand palettes,
undyed and earth-dyed cloth, copper and leather, smooth shading in textures with no random per-pixel noise, and fog
for the dangerous islands. No logos, stills or likenesses of the cast are used.
