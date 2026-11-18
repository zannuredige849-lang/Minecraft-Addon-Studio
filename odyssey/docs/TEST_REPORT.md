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

### Scenario tests (`tools/mocktest/run_all.sh`): 72 assertions, all pass

| Scenario | Verifies |
|---|---|
| solo | World paused before selection. Solo screen offers Odysseus, with Telemachus shown as an NPC. Host controls and portraits present. Long black fade covers the teleport, to the verified Ogygia start. Input re-enabled and normal play restored after the opening. Kit given. NPC Telemachus objectives auto-complete. The journal lists only Odysseus's objectives, with coordinates. Proximity objectives work. Every chapter I→IX advances in order from story events (votes resolved). The bow trial completes the campaign and control returns after the finale. No script errors. |
| duo | Nothing assigned until both have chosen. A taken role shows "Taken by …". Exclusive roles are enforced. Separate Ithaca and Ogygia starts. Each journal shows only its own role. Odysseus cannot complete Telemachus's objective. Chapter I waits for both tracks. Telemachus regroups at Ogygia harbour for Chapter II. |
| four | Host auto-assign gives Odysseus (host), Telemachus, Companion, Eumaeus. No duplicate exclusive roles. Gameplay resumes. |
| afk | A player who never answers is auto-assigned after 120 s and the campaign starts (no permanent lock). |
| disconnect | A player leaving mid-opening does not lock the other. On rejoin their camera is cleared, input released and role kept. |
| leave_lobby | A player leaving during selection lets the others start. |
| late | A late joiner picks a free role without pausing others. |
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
