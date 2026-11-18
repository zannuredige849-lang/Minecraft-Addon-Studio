# Installing and testing The Odyssey v3.0.0

## Install
1. Open **The_Odyssey_v3.0.0.mcworld** (double-click on Windows, Android or iOS, or *Import* in Minecraft). It
   includes both packs.
2. Requires Minecraft Bedrock **1.21.0 or newer**. The scripts use the stable `@minecraft/server` 1.11.0 and
   `@minecraft/server-ui` 1.2.0 modules, so **no experimental toggles** are needed.
3. Keep **cheats on** (the world ships with commands enabled). The camera, fade and input-lock features use commands
   internally.

## Play
- **Solo:** join the world, choose **Odysseus**, and the opening plays.
- **Multiplayer:** the host opens the world and friends join. Everyone gets the character screen. The host (★) can
  auto-assign everyone, start with the current picks, or allow shared roles.
- **Use the Odyssey Astrolabe** for your journal, scene replays, reward vault and (host only) pause, voting rule and
  character changes. Holding it shows the way to your current objective.

## Building the .mcworld from the repo
```sh
cd odyssey/world && zip -r ../The_Odyssey_v3.0.0.mcworld . -x '*.DS_Store'
```

## Developer checks
```sh
odyssey/tools/mocktest/run_all.sh                     # scenario tests (Node 18+)
python3 odyssey/tools/validate_assets.py odyssey/world # asset reference audit
python3 odyssey/tools/world_probe/spots.py odyssey/world/db '[{"name":"x","x":0,"z":3}]'
```

## Recovering a stuck player (should not be needed)
`/camera @s clear`, `/inputpermission set @s movement enabled`, `/inputpermission set @s camera enabled`
