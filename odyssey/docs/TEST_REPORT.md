# Technical test report: v3.0.0

## What was tested and how

**Not tested in Minecraft.** No Bedrock client or server is available in the build environment. Everything below
was checked by static validation or by running the real add-on scripts in Node against an in-memory mock of
`@minecraft/server` and `@minecraft/server-ui` (`tools/mocktest/`). The mock models the API surface the scripts use,
not engine behaviour: rendering, pathfinding, physics, real form UI, camera easing and the input-permission commands
are not exercised. Multiplayer was simulated with several mock players in one process, not real clients.

### Static checks: all pass

| Check | Result |
|---|---|
| Every `.json` in BP and RP parses (`python3 -m json.tool`) | 0 errors |
| Manifest UUIDs unique, and unchanged from v2.2.0 | OK (the RP UUID also appears as the BP's dependency, as intended) |
| `node --check` on every script | 0 errors |
| Asset audit (`tools/validate_assets.py`): geometry/texture/animation/controller/render-controller references, UV bounds, bone names, controller transitions, sound files, item icons | 0 issues (was 18 in v2.2.0) |
| Lang coverage: every translate key used in scripts and config exists in en_US and ru_RU | OK (identical key sets) |
| Visual check of every entity model and texture with a three.js renderer (`tools` in the session scratchpad) | Done. Defects found are listed in ASSETS.md |

### Mechanics audit (second pass)

API check: every method and event the scripts use exists in `@minecraft/server` 1.11.0 / `@minecraft/server-ui` 1.2.0
typings. Bugs found and fixed:

| Bug | Effect in game | Fix |
|---|---|---|
| Astrolabe, galley horn, Royal Bow, Spear, Staff, Hoplon and Sun Talisman were `minecraft:food` with no `using_converts_to` | **Each one was eaten (deleted) on use.** The Astrolabe, the only way to open the menu, vanished on first use. The bow needed to finish the campaign vanished too | `using_converts_to` set to the item itself |
| Repair kit used with no ship nearby | Kit lost for nothing | Refunded |
| The five relics were handled on both `itemUse` and `itemCompleteUse` | Every handler ran twice (hidden by cooldowns) | Handled once |
| Cooldowns and "until" times measured in session ticks, which restart at 0 on every load | After reloading a long session, abilities could stay locked for hours, and a pig curse or wax could last far too long | Persistent game clock (`lib/util.js`, saved every 5 s) |
| Sun Cattle natural spawn rule for the plains biome (the whole superflat world is plains) | Cattle on every island. Killing one anywhere started the Thrinacia vote and the god's storm | Natural spawn rule removed (Thrinacia spawns its own herd). The vote and storm only trigger near Thrinacia |
| Copper helm and cuirass recipes identical to vanilla copper armor (Copper Age update) | Ambiguous crafting result | Helm needs red dye (crest), cuirass needs leather (lining) |
| Cyclops blinded by a non-Odysseus player | Cyclops blind forever, objective never completes: **softlock** | Irreversible deeds (`anyone`) count for the party |
| Circe yields while Odysseus is over 64 blocks away | Same softlock | Same fix |
| Odysseus (or any role) leaves for good | Role objectives could never be completed | Any player may complete a role's objective while no holder is online. The bow trial falls back to Athena's blessing. Re-checked every 5 s |
| Story vote opened at the same moment as an arrival cutscene | Ballot and pause over a locked camera | Votes wait until the cutscene ends |
| Site builds started 65 blocks away, with only the centre chunk checked | Far side of large builds skipped by `/fill` (half-built sites) | All footprint corners must be loaded |
| Hades sheep respawn 10 min | A strayed sheep stalled the rite | 1 min for sacrifice sheep |
| Galley is the only transport for Odysseus and the Companion | Any galley problem strands them | Every role kit includes a boat. NPC Telemachus can board the galley |

### Scenario tests (`tools/mocktest/run_all.sh`): 91 assertions, all pass

| Scenario | Verifies |
|---|---|
| solo | World paused before selection. Solo screen offers Odysseus, with Telemachus shown as an NPC. Host controls and portraits present. Long black fade covers the teleport, to the verified Ogygia start. Input re-enabled and normal play restored after the opening. Kit given. NPC Telemachus objectives auto-complete. The journal lists only Odysseus's objectives, with coordinates. Proximity objectives work. Every chapter I→IX advances in order from story events (votes resolved). The bow trial completes the campaign and control returns after the finale. No script errors. |
| duo | Nothing assigned until both have chosen. A taken role shows "Taken by …". Exclusive roles are enforced. Separate Ithaca and Ogygia starts. Each journal shows only its own role. Odysseus cannot complete Telemachus's objective. Chapter I waits for both tracks. Telemachus regroups at Ogygia harbour for Chapter II. |
| four | Host auto-assign gives Odysseus (host), Telemachus, Companion, Eumaeus. No duplicate exclusive roles. Gameplay resumes. |
| afk | A player who never answers is auto-assigned after 120 s and the campaign starts (no permanent lock). |
| disconnect | A player leaving mid-opening does not lock the other. On rejoin their camera is cleared, input released and role kept. |
| leave_lobby | A player leaving during selection lets the others start. |
| late | A late joiner picks a free role without pausing others. |
| mechanics | Visits all 11 islands. Every site creature spawns and runs its AI loop. Hit, hurt and death events plus every NPC interaction fire on every creature, and every custom item is used. No script errors or caught warnings. |
| softlock | Telemachus blinding the Cyclops completes the chapter. With the Odysseus player gone, Telemachus can finish Chapter IX and the campaign completes. |
| guide | No guide while the player is progressing. Exactly one guide after ~90 s without progress, giving directions to that player's own objective with coordinates. It leaves after its lifetime and does not repeat immediately (cooldown). |

Run with: `odyssey/tools/mocktest/run_all.sh` (needs Node 18+).

## Not verified: please test in game

1. Form appearance on phone, controller and PC (button text length, portrait icons).
2. `/inputpermission` behaviour during selection and cutscenes. If a player is stuck, `/inputpermission set @s movement enabled` and `/camera @s clear` recover them; rejoining does this automatically.
3. Camera framing of the opening and finale shots on the real terrain, and the ease timings.
4. Guide NPC walking: it uses impulses, not pathfinding, so check slopes and doors.
5. Sparta island build timing as a boat approaches (built within 140 blocks).
6. The new Ogygia pier and galley position, and the east Cyclops pier.
7. Armour attachables on Steve/Alex and custom skins (helmet crest, arm guards).
8. The Chapter IX bow trial range (within 12 blocks of the palace point).
9. Old saves: v2.x worlds without roles show the selection screen on next join. Earlier chapter progress is kept, but
   the new objective list starts empty.
