# Working from an iPhone

## Everyday loop
1. Open the Claude app or claude.ai/code and pick the repository, branch `feature/studio-foundation` (or a new `feature/<task>`).
2. Describe the change in plain words, e.g. "add a second entity, a cow-like pixel mob, with a walk animation".
3. The Project Manager plans; the studio creates files and runs `npm run validate` and `npm test`.
4. Read the short report. Errors are listed with file and rule.
5. Ask for `npm run build` to produce `dist/studio_demo.mcaddon` (or a renamed pack).
6. Download the `.mcaddon` artifact from the session or GitHub, then open it on the iPhone.

## Opening the .mcaddon on iPhone
- Save the file to the Files app, then tap it. Minecraft Bedrock imports `.mcaddon` files.
- Enable the add-on in a world's Behavior Packs and Resource Packs settings.
- Test in a creative world with cheats enabled, and spawn the entity with `/summon studio:pixel_slime`.

## Teaching mode
Say "teaching mode". Say "development mode" to return. See `docs/TEACHING_MODE.md`.

## Rules for the phone
- Never accept the Minecraft EULA or any store terms for the studio. Do those yourself.
- Never merge to `main` from the studio. Review on GitHub and merge yourself.
- Keep changes small: one entity or one feature per branch.
