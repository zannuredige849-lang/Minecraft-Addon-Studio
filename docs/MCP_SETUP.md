# Minecraft Creator Tools MCP setup

## What is configured
`.mcp.json` registers the server `minecraft-creator-tools` as `mct mcp --input .`.

`mct` 0.21.0 is already installed globally on this machine. It is not reinstalled and the `/plugin` command is not used.

## Check the connection (no changes made)
```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"check","version":"0"}}}' \
  | timeout 20 mct mcp --input . --offline
```
A healthy server replies with `serverInfo` (name `minecraft`, version `1.0.0`) and the tool list follows with `tools/list`.

Last verified during the studio build: handshake succeeded and 22 tools were listed (`createProject`, `addItem`, `validateContent`, `validateFile`, `writeImageFile`, `writeImageFileFromPixelArt`, `getSkill`, and others).

## Use inside Claude Code
Project MCP servers in `.mcp.json` may need approval the first time the session loads them. If the `minecraft-creator-tools` tools do not appear:
1. Confirm the check above succeeds in the cloud shell.
2. Start a new session on the feature branch so `.mcp.json` is loaded.
3. Approve the project MCP server when prompted.

## If MCP is unavailable
Log it in `docs/STUDIO_REPORT.md` under "MCP issues" and continue with `npm run validate`, `npm test` and `npm run build`. Those do not need MCP.

## Creator Tools skills
`mct skills` lists guides for AI agents (create-block, create-item, create-mob, creator-tools-cli, debug-addon, design-model). Read them with `mct skills <name>` before tasks they cover.
