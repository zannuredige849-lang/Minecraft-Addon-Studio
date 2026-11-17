# Minecraft-Addon-Studio

Bedrock add-ons. `BP/` is the behavior pack, `RP/` is the resource pack.

## The Odyssey (2026)

The creatures and mythic encounters of Christopher Nolan's *The Odyssey*, built only from what the film shows:
their look, their proportions and what they do on screen. Each one is a cube model with an HD texture
(up to 64 px per block) and its own animations.

![Every creature in the add-on](docs/odyssey-preview.png)

### Creatures

| Creature | In the film | In the game |
|---|---|---|
| **Polyphemus** `studio:cyclops` | A gangly, bald giant with pale, wrinkled elephantine skin, huge hands with broken nails, and one wide-open round eye with an amber iris, set crooked above a twisted nose and mouth. A shepherd who traps and devours men. | Stands **6.5 blocks** tall with a flock of 6 sheep. He grabs anyone within reach, lifts them to his mouth and bites, and tramples what is underfoot. At night he sleeps. Hit him with the **Burning Stake** while he sleeps and he is blinded for good: he cries *"Father Poseidon, they blinded me! Vengeance, father, vengeance for pain..."* and a storm rolls in. Blind, he passes over anyone standing among his sheep, and throws rocks at boats he hears. The rocks always miss, as in the film. |
| **Laestrygonians** `studio:laestrygonian` | 4 m giants of Telepylus, corpulent, with broad, slightly arched shoulders, in smooth silver plate: a domed helmet with a beak-like ridge and a dark Y-shaped face opening, one great dome on each shoulder, a rounded breastplate with a band across the belly, flared forearm guards, a skirt of hanging plates, and bare hands. Their weapons: a sword the size of a ship's prow, a glaive, an all-metal mace and a great curved blade. | **4 blocks** tall, each carrying one of the four weapons. The glaive launches people into the air. Blades do half damage against their armour; arrows do full damage. They are calm until alarmed, but hurting one alarms the whole group, and they smash any boat within reach. |
| **Laestrygonian child** `studio:laestrygonian_child` | Already the size of a grown man, in a quilted coat with plate. Asked for hospitality, the child laughs; asked again, the child screams and runs. | Laughs when you come close. If you stay, the child screams, runs and alarms every giant within 64 blocks. If no giants are near, three arrive. |
| **Circe** `studio:circe` | A witch on Aeaea with long dark hair going grey, living with her sister, whom she turned into a bird. The animals around her cottage were once sailors. She feeds the men stew if they leave their armour outside, then molds them into pigs with her hands. Odysseus grabs her sister and she stands down. | Spawns with her sister on her shoulder and three pigs. **Beg for Food**: she gives Circe's Stew only if you wear no armour. Eat it and come near her, and she molds you into a pig for 10 minutes. **Seize Her Sister** (use the bird): she yields, turns everyone back and tells you to cross the river Oceanus into Hades. |
| **Sirens** `studio:siren` | Mermaids, seen as pale bodies lying on the sea rocks in the mist. Their song lures one sailor to take out his wax and swim off the ship. The crew stop their ears with wax. Odysseus, tied to the mast, hears everything he could ever want, and why he could never have it. | Evil mermaids lying on the rocks in a haze of mist: ash-pale skin, black eyes, long black hair and a scaled tail. They cannot be harmed. Their song pulls in and sickens anyone within 32 blocks. **Wax** blocks it for 5 minutes. In a boat you are tied to the mast: you hear the song but are not pulled. |
| **Scylla** `studio:scylla` | A six-headed monster in the cliff that snatches six men from the deck and carries them off to her cave. | Fixed in place and cannot be harmed. Every 30 s her necks lunge and seize up to **six** creatures within 15 blocks, lift them high and bite them. |
| **Charybdis** `studio:charybdis` | The whirlpool that would take the whole ship. | Forms on water near Scylla. It drags everything within 28 blocks into a spiral and swallows boats and dropped items at its centre. |
| **Tiresias** and the **shades** `studio:tiresias`, `studio:shade` | In Hades, a sacrifice of sheep raises the dead. Sinon's shade reproaches Odysseus; Agamemnon's shade tells of his murder by Clytemnestra; blind Tiresias, shrouded and caked in black sand, prophesies. Then the unburied crew come for him. | Kill a **sheep** while standing on **soul sand, soul soil or black concrete powder**. Sinon, Agamemnon (black plumed helmet) and Tiresias rise from the ground and speak. Tiresias says *"The Whirlpool in the sea takes all of your lives, the monster in the cliff only six."* Then six crew shades rise and attack, and sink back after 90 s. |
| **Cattle of Apollo** `studio:sun_cattle` | On Thrinacia the starving men kill one of Apollo's cattle, and Zeus sends a storm that sinks the ship. | Long-horned cattle on the plains. Kill one and a thunderstorm brings ten lightning strikes around you; the boat you ride is destroyed. |
| **Calypso** `studio:calypso` | The nymph of Ogygia, whose lotus flowers make Odysseus forget. | **Accept a Lotus**: she gives a Lotus Flower. Eating it takes all your XP levels (your memories) and leaves you calm and slowed. |
| **Athena** `studio:athena` | The goddess who protects Odysseus and commands him to return home. | **Speak with Athena**: Resistance for 4 minutes, once every 10 minutes. |
| **Trojan Horse** `studio:trojan_horse` | Production designer Ruth De Jong's rearing 36 ft (11 m) horse. The Greeks hide inside it. | Stands **11 blocks** tall. **Hide Inside**: up to six players sit inside and turn invisible. |

### Items and recipes

| Item | How to get it | Use |
|---|---|---|
| Wax | 1 honeycomb gives 2 | Eat to stop the Sirens' song reaching you for 5 minutes |
| Burning Stake | flint over an oak log over coal (one column) | Strike Polyphemus with it while he sleeps |
| Circe's Stew | Circe gives it if you wear no armour | Filling food, but it leaves you pliable to Circe's hands |
| Lotus Flower | Calypso gives it | Eat to forget: removes your XP levels |

### Play the film in order

1. **The Cyclops:** let Polyphemus sleep at night, then strike with the burning stake. Hide among his flock and get to your boat.
2. **Telepylus:** in a taiga, do not linger near the armoured child.
3. **Aeaea:** take off your armour to eat Circe's stew (or don't), then seize her sister.
4. **Hades:** sacrifice a sheep on black sand to hear Tiresias, then run from the dead.
5. **The Sirens:** eat wax, or sail past bound to the mast.
6. **Scylla and Charybdis:** choose which one to pass.
7. **Thrinacia:** leave the cattle of Apollo alone.
8. **Ogygia:** Calypso's lotus, and Athena's command to go home.

Natural spawns: Laestrygonians (groups of 2–3) and their child in taigas, Sirens on stony shores, the cattle of Apollo on
plains. Everything else comes from spawn eggs or `/summon`. Charybdis also forms on its own near Scylla.

### Install and test

On a phone or PC, open the `.mcaddon` file (build it with `python3 -m tools.odyssey.package`) and Minecraft imports both
packs; then enable **Odyssey Creatures BP** on a world (it adds the resource pack itself). For development, copy `BP/` into
`development_behavior_packs` and `RP/` into `development_resource_packs` instead.
The script uses the stable `@minecraft/server` 1.11.0 API, so no experimental toggles are needed.

    /summon studio:cyclops
    /summon studio:laestrygonian_child
    /summon studio:circe
    /summon studio:siren
    /summon studio:scylla
    /summon studio:sun_cattle
    /summon studio:calypso
    /summon studio:athena
    /summon studio:trojan_horse
    /give @s studio:burning_stake
    /give @s studio:beeswax 4
    /time set night

### For developers

- `python3 -m tools.odyssey.build` regenerates every model, texture, animation and pack file from `tools/odyssey/`
  (one module per creature, plus shared materials, body parts and checks). Before writing anything it checks that no
  part floats, no joint gaps, no textures overlap and no face is left invisible.
- `python3 -m tools.odyssey.validate` checks the finished packs: every JSON parses, manifest UUIDs are unique, and every
  geometry, texture, animation bone, render controller, property, event, item and language key that the packs and the
  script refer to exists.
- `python3 -m tools.odyssey.package` zips both packs into `dist/Odyssey_Creatures_v<version>.mcaddon`.
- `node tools/preview_render.js` renders a model to PNG, optionally posed (`npm i three playwright` first).
- Mechanics live in `BP/scripts/main.js`.

Sources: the film's Wikipedia article (plot and production), film stills, the Villains Wiki and Odyssey fan-wiki
character pages, published reviews (including Collider's guide to the film's mythological figures), and viewers' accounts
of scenes the wikis do not describe.

## studio:pixel_slime

The original test entity: `/summon studio:pixel_slime`.
